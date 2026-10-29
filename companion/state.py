"""Observable session state; no inference from message text or hidden reasoning."""
from dataclasses import dataclass, field
import time

STATES = frozenset(('idle', 'working', 'needs_input', 'message', 'finished',
                    'error', 'interrupted', 'disconnected'))
KINDS = frozenset(('start', 'activity', 'needs_input', 'resolved', 'message',
                   'finished', 'error', 'interrupt', 'end'))


@dataclass(frozen=True)
class Event:
    session: str
    turn: str
    seq: int
    kind: str
    request_id: str | None = None
    observed_at_ns: int = 0


@dataclass(frozen=True)
class Snapshot:
    state: str = 'idle'
    session: str = ''
    seq: int = 0
    notify: bool = False


@dataclass
class Session:
    turn: str
    seq: int = -1
    state: str = 'idle'
    requests: set[str] = field(default_factory=set)
    retired: set[str] = field(default_factory=set)
    acknowledged: bool = False
    changed: int = 0
    message_until: float = 0
    observed_at_ns: int = 0


class Reducer:
    def __init__(self):
        self.sessions: dict[str, Session] = {}
        self.snapshot = Snapshot()
        self.order = 0

    def apply(self, event: Event, now: float | None = None) -> Snapshot:
        now = time.monotonic() if now is None else now
        if event.kind not in KINDS or not event.session or not event.turn:
            return self.snapshot
        s = self.sessions.get(event.session)
        if s is None:
            if len(self.sessions) >= 32:
                removable = [k for k, v in self.sessions.items()
                             if v.state in ('idle', 'finished', 'interrupted') and not v.requests]
                if not removable:
                    return self.snapshot
                del self.sessions[removable[0]]
            s = self.sessions[event.session] = Session(event.turn)
        if event.seq <= s.seq or event.turn in s.retired:
            return self.snapshot
        if event.observed_at_ns and event.observed_at_ns <= s.observed_at_ns:
            return self.snapshot
        if event.turn != s.turn:
            # Only an observed new submission starts another turn. A late completion
            # from an unknown turn must not retire the current one.
            if event.kind != 'start':
                return self.snapshot
            s.retired.add(s.turn)
            if len(s.retired) > 128:
                # Session history is bounded; old non-start events still cannot switch turns.
                s.retired.pop()
            s.turn = event.turn
            s.requests.clear()
            s.state = 'idle'
        s.seq = event.seq
        if event.observed_at_ns:
            s.observed_at_ns = event.observed_at_ns
        if s.state == 'error' and not s.acknowledged and event.kind in ('activity', 'resolved'):
            return self._select(now)
        if s.state == 'finished' and event.kind == 'finished':
            return self._select(now)
        self.order += 1
        s.changed = self.order
        if event.kind == 'end':
            del self.sessions[event.session]
        elif event.kind == 'message':
            s.message_until = now + 3
        else:
            s.message_until = 0
            keep_acknowledgement = bool(s.requests) and event.kind in ('activity', 'resolved')
            duplicate_request = event.kind == 'needs_input' and (event.request_id or 'approval') in s.requests
            if event.kind == 'needs_input':
                s.requests.add(event.request_id or 'approval')
            elif event.kind == 'resolved':
                s.requests.discard(event.request_id or 'approval')
                s.state = 'working'
            else:
                s.state = {'start': 'working', 'activity': 'working',
                           'finished': 'finished', 'error': 'error',
                           'interrupt': 'interrupted'}[event.kind]
                if event.kind in ('start', 'finished', 'error', 'interrupt'):
                    s.requests.clear()
            if not keep_acknowledgement and not duplicate_request:
                s.acknowledged = False
        return self._select(now)

    def _select(self, now: float) -> Snapshot:
        choices = []
        rank = {'idle': 0, 'interrupted': 1, 'finished': 2, 'working': 3,
                'message': 4, 'error': 5, 'needs_input': 6}
        for key, s in self.sessions.items():
            state = 'needs_input' if s.requests else s.state
            if s.acknowledged and state in ('error', 'finished'):
                state = 'idle'
            if s.message_until > now and state not in ('needs_input', 'error'):
                state = 'message'
            notify = state in ('needs_input', 'message', 'error', 'finished') and not s.acknowledged
            choices.append((rank[state], s.changed, key, state, notify))
        if choices:
            _, _, key, state, notify = max(choices)
        else:
            key, state, notify = '', 'idle', False
        identity = (state, key, notify)
        old = self.snapshot
        if identity != (old.state, old.session, old.notify):
            self.snapshot = Snapshot(state, key, old.seq + 1, notify)
        return self.snapshot

    def acknowledge(self) -> Snapshot:
        if self.snapshot.session in self.sessions:
            s = self.sessions[self.snapshot.session]
            s.acknowledged = True
            s.message_until = 0
        return self._select(time.monotonic())

    def tick(self, now: float) -> Snapshot:
        return self._select(now)
