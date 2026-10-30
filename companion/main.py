"""Run the local Codex observer and the explicitly selected USB device."""
import argparse
from dataclasses import asdict
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from collections import OrderedDict, deque
from .rollouts import RolloutWatcher
from .hook import DEFAULT_CONFIG, forward_hook
from .state import Event, Reducer, KINDS
from .transport import SerialLink


def make_server(token: str, reducer: Reducer, *, port: int = 52341) -> HTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def reply(self, code, body=None):
            data = json.dumps(body or {}).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            if self.headers.get('Origin') or not hmac.compare_digest(self.headers.get('Authorization', '').encode(), ('Bearer '+token).encode()):
                return self.reply(401)
            if self.path != '/status':
                return self.reply(404)
            return self.reply(200, self.server.health())

        def discard_small_body(self):
            try:
                size=int(self.headers.get('Content-Length','0'))
                if 0<size<=4096:self.rfile.read(size)
            except (ValueError,OSError):pass

        def do_POST(self):
            if self.headers.get('Origin'):
                self.discard_small_body()
                return self.reply(403)
            if not hmac.compare_digest(self.headers.get('Authorization', '').encode('utf-8'), ('Bearer ' + token).encode('utf-8')):
                self.discard_small_body()
                return self.reply(401)
            if self.path not in ('/event', '/ack'):
                return self.reply(404)
            try:
                size = int(self.headers.get('Content-Length', '-1'))
            except ValueError:
                return self.reply(400)
            if size < 0 or size > 4096:
                return self.reply(413)
            try:
                body = json.loads(self.rfile.read(size))
            except (ValueError, OSError):
                return self.reply(400)
            if self.path == '/ack':
                if body != {}:
                    return self.reply(400)
                reducer.acknowledge()
            else:
                if not isinstance(body, dict) or set(body) - {'session', 'turn', 'kind', 'request_id', 'event_id', 'observed_at_ns'}:
                    return self.reply(400)
                if not isinstance(body.get('kind'), str) or body['kind'] not in KINDS:
                    return self.reply(400)
                for key in ('session', 'turn'):
                    value = body.get(key)
                    if not isinstance(value, str) or not 0 < len(value) <= 64 or not value.isalnum():
                        return self.reply(400)
                req = body.get('request_id')
                if req is not None and (not isinstance(req, str) or not 0 < len(req) <= 64 or not req.isalnum()):
                    return self.reply(400)
                event_id = body.pop('event_id', None)
                if event_id is not None and (not isinstance(event_id, str) or not event_id.isalnum() or len(event_id)>64):
                    return self.reply(400)
                observed = body.get('observed_at_ns', 0)
                if type(observed) is not int or observed < 0 or observed > time.monotonic_ns()+5_000_000_000:
                    return self.reply(400)
                key = (body['session'], event_id)
                if event_id and key in self.server.seen:
                    return self.reply(200, asdict(reducer.snapshot))
                if event_id:
                    self.server.seen[key]=None
                    if len(self.server.seen)>4096:
                        self.server.seen.popitem(last=False)
                if body['kind'] == 'end' and body['session'] in reducer.sessions:
                    body['turn'] = reducer.sessions[body['session']].turn
                self.server.counter += 1
                self.server.evidence.append(dict(source='hook',kind=body['kind'],session=body['session'],turn=body['turn'],at_ns=time.monotonic_ns()))
                reducer.apply(Event(seq=self.server.counter, **body))
            self.reply(200, asdict(reducer.snapshot))

    class LocalServer(HTTPServer):
        def get_request(self):
            sock, addr = super().get_request()
            sock.settimeout(0.25)
            return sock, addr

    server = LocalServer(('127.0.0.1', port), Handler)
    server.evidence = deque(maxlen=24)
    server.health = lambda: dict(state=reducer.snapshot.state)
    server.counter = 0
    server.seen = OrderedDict()
    server.timeout = 0.02
    return server


def init_config(path: Path, port: int):
    if path.exists():
        raise FileExistsError('Configuration exists; reuse it rather than rotate the token')
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    config = dict(endpoint=f'http://127.0.0.1:{port}/event', token=secrets.token_hex(32))
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(config, stream)
    if os.name == 'nt':
        # Replace inherited ACLs on this new token file, not on its parent folder.
        account = os.environ.get('USERDOMAIN', '') + '\\' + os.environ['USERNAME']
        result = subprocess.run(['icacls', str(path), '/inheritance:r', '/grant:r', account+':(F)'],
                                capture_output=True)
        if result.returncode:
            path.unlink()
            raise OSError('Could not restrict token-file permissions')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', help='Explicit serial port, e.g. COM5 or /dev/cu.usbmodem...')
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--listen-port', type=int, default=52341)
    parser.add_argument('--init-config', action='store_true')
    parser.add_argument('--dry-run', action='store_true', help='Observe without serial hardware')
    parser.add_argument('--codex-events', action='store_true', help='Observe new local Codex lifecycle records')
    parser.add_argument('--codex-home', type=Path, default=Path(os.environ.get('CODEX_HOME',Path.home()/'.codex')))
    parser.add_argument('--log-file', type=Path, help='Local state-only background log')
    parser.add_argument('--thread', help='Optional single thread UUID; default observes all local chats')
    parser.add_argument('--emit', choices=sorted(KINDS), help='Send a manual test event and exit')
    args = parser.parse_args(argv)
    if args.log_file:
        args.log_file.parent.mkdir(parents=True,exist_ok=True)
        sys.stdout = args.log_file.open('a',encoding='utf-8',buffering=1)
        sys.stderr = sys.stdout
    if args.init_config:
        init_config(args.config, args.listen_port)
        print('Created private observer configuration at', args.config)
        return 0
    config = json.loads(args.config.read_text(encoding='utf-8'))
    if args.emit:
        # This is explicitly a manual demonstration, not a Codex observation.
        forward_hook(dict(session='manual', turn='manual', kind=args.emit), config['endpoint'], config['token'])
        return 0
    if not args.port and not args.dry_run:
        parser.error('--port is required unless --dry-run is selected')
    expected = f'http://127.0.0.1:{args.listen_port}/event'
    if config.get('endpoint') != expected or not isinstance(config.get('token'), str) or len(config['token']) < 32:
        parser.error('Configuration endpoint/token does not match this observer')
    reducer = Reducer()
    server = make_server(config['token'], reducer, port=args.listen_port)
    link = None if args.dry_run else SerialLink(args.port, acknowledge=reducer.acknowledge)
    watcher = RolloutWatcher(args.codex_home/'sessions', thread=args.thread) if args.codex_events else None
    evidence = server.evidence
    server.health = lambda: dict(pid=os.getpid(), state=reducer.snapshot.state, seq=reducer.snapshot.seq,
        device_connected=bool(link and link.ready), firmware=link.firmware if link else None, muted=link.muted if link else None, port=args.port,
        source='codex_rollouts' if watcher else 'hooks',
        events_seen=watcher.events if watcher else server.counter,
        recent_events=list(evidence))
    last = None
    print('Observer running on loopback; hardware:', 'disabled' if link is None else args.port)
    try:
        while True:
            server.handle_request()
            now = time.monotonic()
            if watcher:
                for event in watcher.poll(now):
                    server.counter += 1
                    reducer.apply(Event(seq=server.counter, **event))
                    evidence.append(dict(source='rollout',kind=event['kind'], session=event['session'],
                                         turn=event['turn'], at_ns=event['observed_at_ns']))
            snapshot = reducer.tick(now)
            if link:
                link.tick(now, snapshot)
            if (snapshot.state, snapshot.seq) != last:
                print(snapshot.state, flush=True)
                last = (snapshot.state, snapshot.seq)
    except KeyboardInterrupt:
        pass
    finally:
        if link:
            link.disconnect()
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
