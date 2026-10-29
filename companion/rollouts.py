"""Read Codex JSONL lifecycle records locally; never forward conversation content."""
from pathlib import Path
from datetime import datetime
import json
import re
import os
import time
from .hook import identity

MAX_RECORD = 2 * 1024 * 1024
THREAD = re.compile(r'([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})\.jsonl$')
INPUT_TOOLS = {'request_user_input', 'request_user_input_async'}


class Cursor:
    def __init__(self, path, *, existing=False):
        self.path = path
        match = THREAD.search(path.name)
        self.session = identity(match.group(1)) if match else identity(str(path))
        self.turn = ''
        self.pending = {}
        self.offset = 0
        self.dropping = False
        self.record_ns = 0
        if existing:
            size = path.stat().st_size
            if time.time()-path.stat().st_mtime > 300:
                self.offset = size
                return
            # Recover identifiers only. Old activity and alerts are never replayed.
            with path.open('rb') as stream:
                stream.seek(max(0, size-MAX_RECORD))
                if stream.tell():
                    stream.readline()
                for raw in stream:
                    try:
                        record = json.loads(raw)
                        value = record.get('payload', {}).get('turn_id')
                        if isinstance(value, str) and value:
                            self.turn = value
                    except (ValueError, AttributeError):
                        pass
            self.offset = size

    def event(self, kind, *, turn=None, request=None):
        value = turn or self.turn
        if not value:
            return []
        event = dict(session=self.session, turn=identity(value), kind=kind,
                     observed_at_ns=self.record_ns or time.monotonic_ns())
        if self.record_ns:self.record_ns += 1
        if request:
            event['request_id'] = identity(request)
        return [event]

    def parse(self, record):
        if not isinstance(record, dict) or not isinstance(record.get('payload'), dict):
            return []
        self.record_ns = 0
        stamp=record.get('timestamp')
        if isinstance(stamp,str):
            try:
                delta=datetime.fromisoformat(stamp.replace('Z','+00:00')).timestamp()-time.time()
                self.record_ns=max(1,time.monotonic_ns()+int(min(0,delta)*1_000_000_000))
            except ValueError:pass
        outer, payload = record.get('type'), record['payload']
        kind = payload.get('type')
        explicit = payload.get('turn_id')
        if not self.turn and isinstance(explicit, str):
            self.turn = explicit
        if outer == 'event_msg':
            if kind == 'task_started' and isinstance(explicit, str) and explicit:
                self.turn = explicit
                self.pending.clear()
                return self.event('start')
            if kind == 'task_complete':
                if self.pending:
                    return []  # An outstanding structured question still needs an answer.
                return self.event('finished', turn=explicit)
            if kind == 'turn_aborted':
                self.pending.clear()
                return self.event('interrupt', turn=explicit)
            if kind == 'error' and payload.get('will_retry') is False:
                return self.event('error', turn=explicit)
            if kind == 'item_completed' and isinstance(payload.get('item'), dict):
                item = payload['item']
                item_type = item.get('type')
                if item_type == 'AgentMessage' and item.get('phase') == 'commentary':
                    return self.event('message', turn=explicit)
                if item_type == 'SubAgentActivity' and item.get('kind') in ('interacted', 'completed'):
                    return self.event('message', turn=explicit)
                if item_type in ('CommandExecution', 'McpToolCall', 'FileChange'):
                    return self.event('activity', turn=explicit)
        if outer == 'response_item':
            name = payload.get('name', '')
            tool = name.rsplit('.', 1)[-1].rsplit('__', 1)[-1] if isinstance(name, str) else ''
            if kind == 'function_call' and tool in INPUT_TOOLS:
                call = payload.get('call_id')
                if isinstance(call, str) and call and self.turn:
                    self.pending[call] = (self.turn, tool.endswith('_async'))
                    return self.event('needs_input', request=call)
            if kind == 'function_call_output':
                call = payload.get('call_id')
                if call in self.pending and not self.pending[call][1]:
                    turn, _ = self.pending.pop(call)
                    return self.event('resolved', turn=turn, request=call)
            if kind == 'message' and payload.get('role') == 'user':
                result = []
                content = payload.get('content')
                for part in content if isinstance(content, list) else []:
                    if not isinstance(part, dict):
                        continue
                    text = part.get('text', '')
                    if not isinstance(text, str):
                        continue
                    begin, end = '<send_user_message_question_reply>', '</send_user_message_question_reply>'
                    if begin not in text or end not in text:
                        continue
                    try:
                        replies = json.loads(text.split(begin, 1)[1].split(end, 1)[0])
                        for reply in replies if isinstance(replies, list) else []:
                            ref = json.loads(reply['questionItemId'])
                            call = ref[1]
                            if call in self.pending:
                                turn, _ = self.pending.pop(call)
                                result.extend(self.event('resolved', turn=turn, request=call))
                    except (ValueError, KeyError, TypeError, IndexError):
                        continue
                return result
        return []

    def read(self, size=None):
        result = []
        if size is None:size = self.path.stat().st_size
        if size < self.offset:
            # A replaced/truncated history must not replay old alarms.
            self.offset = size
            self.pending.clear()
            return self.event('end')
        if size == self.offset:
            return result
        with self.path.open('rb') as stream:
            stream.seek(self.offset)
            budget = 4*MAX_RECORD
            while budget > 0:
                start = stream.tell()
                raw = stream.readline(MAX_RECORD+1)
                if not raw:
                    break
                budget -= len(raw)
                if not raw.endswith(b'\n'):
                    if len(raw) > MAX_RECORD or self.dropping:
                        self.dropping = True
                        self.offset = stream.tell()
                        continue
                    self.offset = start  # Wait for a complete JSON record.
                    break
                self.offset = stream.tell()
                if self.dropping:
                    self.dropping = False
                    continue
                if len(raw) > MAX_RECORD:
                    continue
                try:
                    result.extend(self.parse(json.loads(raw)))
                except (ValueError, TypeError, AttributeError):
                    continue
        return result


class RolloutWatcher:
    def __init__(self, root, *, thread=None):
        self.root = Path(root)
        self.thread = thread
        self.cursors = {}
        self.started = False
        self.scan_at = 0.0
        self.read_at = 0.0
        self.events = 0

    def poll(self, now):
        if now < self.scan_at:
            return []
        self.scan_at = now + .5
        result = []
        # DirEntry metadata is cached by Windows directory enumeration. Read only
        # changed files, rather than issuing a stat for every history file at 50 Hz.
        folders = [self.root]
        while folders:
            try:
                with os.scandir(folders.pop()) as entries:
                    for entry in entries:
                        if entry.is_dir(follow_symlinks=False):
                            folders.append(Path(entry.path))
                            continue
                        if not entry.name.startswith('rollout-') or not entry.name.endswith('.jsonl'):
                            continue
                        if self.thread and self.thread not in entry.name:
                            continue
                        path=Path(entry.path)
                        try:
                            size=entry.stat(follow_symlinks=False).st_size
                            if path not in self.cursors:
                                self.cursors[path]=Cursor(path,existing=not self.started)
                            cursor=self.cursors[path]
                            if size!=cursor.offset:
                                result.extend(cursor.read(size))
                        except OSError:
                            continue
            except OSError:
                continue
        self.started=True
        self.events+=len(result)
        return result
