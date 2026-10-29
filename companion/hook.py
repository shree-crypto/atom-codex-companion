"""Silent, fail-open Codex observer. Never emits hook control output."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request
import urllib.error

DEFAULT_CONFIG = Path.home() / '.atom-companion' / 'config.json'


def identity(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:24]


def normalize_hook(payload: dict) -> dict | None:
    if not isinstance(payload, dict):
        return None
    mapping = {'UserPromptSubmit': 'start', 'PreToolUse': 'activity',
               'PermissionRequest': 'needs_input', 'PostToolUse': 'resolved',
               'PostToolUseFailure': 'resolved', 'Stop': 'finished', 'Interrupt': 'interrupt', 'SessionEnd': 'end'}
    hook_name = payload.get('hook_event_name')
    kind = mapping.get(hook_name) if isinstance(hook_name, str) else None
    tool = payload.get('tool_name', '')
    if hook_name == 'PostToolUse' and isinstance(tool, str) and tool.endswith('request_user_input_async'):
        return None  # The tool returned a handle; only its later answer resolves the wait.
    session = payload.get('session_id', payload.get('thread_id'))
    turn = payload.get('turn_id')
    if not kind or not isinstance(session, str) or not session:
        return None
    if not isinstance(turn, str) or not turn:
        if kind != 'end':
            return None
        turn = 'session-end'
    if len(session) > 512 or len(turn) > 512:
        return None
    event = dict(session=identity(session), turn=identity(turn), kind=kind)
    request = payload.get('request_id', payload.get('tool_use_id'))
    if isinstance(request, str) and request:
        event['request_id'] = identity(request)
    event['observed_at_ns'] = time.monotonic_ns()
    source_id=payload.get('event_id')
    # Preserve a provided source event's identity. Otherwise identify this hook
    # invocation, not every Stop in a turn: another Stop may follow continued work.
    event['event_id'] = identity(source_id if isinstance(source_id,str) and source_id
                                 else '|'.join((event['session'],event['turn'],kind,str(event['observed_at_ns']))))
    return event


def forward_hook(payload: dict, endpoint: str, token: str) -> None:
    # Never follow a supplied configuration to another host.
    from urllib.parse import urlparse
    parsed = urlparse(endpoint)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.path != '/event':
        return
    request = urllib.request.Request(endpoint, json.dumps(payload).encode('utf-8'),
                                     {'Authorization': 'Bearer ' + token,
                                      'Content-Type': 'application/json'})
    try:
        # Ignore proxy environment variables for this local observer.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        with opener.open(request, timeout=0.2) as response:
            response.read(128)
    except (OSError, ValueError, urllib.error.URLError):
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.buffer.read(65537)
        if len(raw) > 65536:
            return 0
        event = normalize_hook(json.loads(raw))
        config = json.loads(args.config.read_text(encoding='utf-8'))
        if event:
            forward_hook(event, config['endpoint'], config['token'])
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
