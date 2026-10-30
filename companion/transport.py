"""Bounded JSON-lines transport. Never talks until the selected device identifies itself."""
import json
import uuid
from .state import Snapshot, STATES

MAX_FRAME = 512


def valid_snapshot(frame: dict) -> bool:
    return (type(frame.get('v')) is int and frame['v'] == 1
            and isinstance(frame.get('epoch'), str) and 0 < len(frame['epoch']) <= 40
            and type(frame.get('seq')) is int and 0 <= frame['seq'] <= 0xFFFFFFFF
            and frame.get('state') in STATES
            and isinstance(frame.get('session'), str) and len(frame['session']) <= 64
            and type(frame.get('notify')) is bool)


def encode_snapshot(snapshot: Snapshot, epoch: str, *, notify: bool | None = None) -> bytes:
    frame = dict(v=1, epoch=epoch, seq=snapshot.seq, state=snapshot.state,
                 session=snapshot.session, notify=snapshot.notify if notify is None else notify)
    if not valid_snapshot(frame):
        raise ValueError('Invalid snapshot')
    raw = json.dumps(frame, separators=(',', ':'), ensure_ascii=True).encode('ascii') + b'\n'
    if len(raw) - 1 > MAX_FRAME:
        raise ValueError('Frame too large')
    return raw


class FrameDecoder:
    def __init__(self):
        self.buffer = bytearray()
        self.dropping = False

    def feed(self, chunk: bytes) -> list[dict]:
        result = []
        for byte in chunk:
            if byte == 10:
                if not self.dropping and self.buffer:
                    try:
                        frame = json.loads(self.buffer)
                        if isinstance(frame, dict) and self._valid(frame):
                            result.append(frame)
                    except (ValueError, UnicodeDecodeError, TypeError):
                        pass
                self.buffer.clear()
                self.dropping = False
            elif not self.dropping:
                if len(self.buffer) >= MAX_FRAME:
                    self.buffer.clear()
                    self.dropping = True
                else:
                    self.buffer.append(byte)
        return result

    @staticmethod
    def _valid(frame):
        if type(frame.get('v')) is not int or frame['v'] != 1:
            return False
        if frame.get('kind') == 'ready':
            return frame.get('device') == 'atom-companion'
        if frame.get('kind') == 'ack':
            return (type(frame.get('seq')) is int and 0 <= frame['seq'] <= 0xFFFFFFFF
                    and isinstance(frame.get('epoch'), str) and 0 < len(frame['epoch']) <= 40)
        return valid_snapshot(frame)


class SerialLink:
    def __init__(self, port: str, *, opener=None, acknowledge=None):
        self.port = port
        self.opener = opener or self._open
        self.acknowledge = acknowledge or (lambda: None)
        self.epoch = uuid.uuid4().hex
        self.wire = None
        self.decoder = FrameDecoder()
        self.ready = False
        self.firmware = None
        self.retry_at = 0.0
        self.opened_at = 0.0
        self.sent_at = -1.0
        self.last_snapshot = None
        self.first_send = True

    def _open(self):
        import serial
        return serial.Serial(self.port, 115200, timeout=0, write_timeout=0.25)

    def disconnect(self):
        if self.wire:
            try:
                self.wire.close()
            except OSError:
                pass
        self.wire = None
        self.ready = False
        self.firmware = None
        self.first_send = True
        self.last_snapshot = None
        self.decoder = FrameDecoder()

    def tick(self, now: float, snapshot: Snapshot) -> None:
        if not self.wire:
            if now < self.retry_at:
                return
            try:
                self.wire = self.opener()
                self.opened_at = now
            except (OSError, ImportError):
                self.retry_at = now + 2
                return
        try:
            for frame in self.decoder.feed(self.wire.read(min(self.wire.in_waiting, 4096))):
                if frame.get('kind') == 'ready':
                    self.ready = True
                    version=frame.get('firmware')
                    self.firmware=version if isinstance(version,str) and len(version)<=64 else None
                elif self.ready and frame.get('kind') == 'ack':
                    if frame['epoch'] == self.epoch and frame['seq'] == snapshot.seq:
                        self.acknowledge()
            if not self.ready:
                if now - self.opened_at >= 5:
                    self.disconnect()
                    self.retry_at = now + 2
                return
            if snapshot != self.last_snapshot or now - self.sent_at >= 1:
                frame = encode_snapshot(snapshot, self.epoch,
                                        notify=False if self.first_send else snapshot.notify)
                if self.wire.write(frame) != len(frame):
                    raise OSError('Incomplete serial write')
                self.first_send = False
                self.last_snapshot = snapshot
                self.sent_at = now
        except OSError:
            self.disconnect()
            self.retry_at = now + 2
