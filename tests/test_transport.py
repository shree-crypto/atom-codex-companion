import json
import unittest
from companion.state import Snapshot
from companion.transport import FrameDecoder, encode_snapshot, SerialLink


class Wire:
    def __init__(self):
        self.incoming = bytearray()
        self.outgoing = bytearray()
        self.closed = False
    @property
    def in_waiting(self):
        return len(self.incoming)
    def read(self, n):
        data = bytes(self.incoming[:n]); del self.incoming[:n]; return data
    def write(self, data):
        self.outgoing.extend(data); return len(data)
    def close(self):
        self.closed = True


class TransportTests(unittest.TestCase):
    def test_fragmented_frames_and_overflow_recovery(self):
        d = FrameDecoder()
        frame = encode_snapshot(Snapshot('working', 's', 2, False), 'boot')
        self.assertEqual(d.feed(frame[:9]), [])
        self.assertEqual(d.feed(frame[9:])[0]['state'], 'working')
        self.assertEqual(d.feed(b'x' * 513 + b'\n' + frame)[0]['seq'], 2)

    def test_schema_rejects_invalid_states_versions_and_types(self):
        base = dict(v=1, epoch='boot', seq=1, state='working', session='s', notify=False)
        for key, bad in [('v', 2), ('state', 'approve'), ('seq', True), ('notify', 1), ('epoch', ''), ('session', 'x'*100)]:
            frame = dict(base); frame[key] = bad
            self.assertEqual(FrameDecoder().feed(json.dumps(frame).encode()+b'\n'), [], (key, bad))

    def test_no_commands_until_device_identifies_itself(self):
        wire = Wire()
        link = SerialLink('unused', opener=lambda: wire)
        snap = Snapshot('finished', 's', 1, True)
        link.tick(0, snap)
        self.assertEqual(wire.outgoing, b'')
        wire.incoming.extend(b'{"v":1,"device":"atom-companion","kind":"ready"}\n')
        link.tick(1, snap)
        self.assertFalse(json.loads(wire.outgoing.splitlines()[0])['notify'])

    def test_reconnect_does_not_replay_chime(self):
        wires = [Wire(), Wire()]
        link = SerialLink('unused', opener=lambda: wires.pop(0))
        a, b = wires[:]
        snap = Snapshot('finished', 's', 1, True)
        link.tick(0, snap)
        a.incoming.extend(b'{"v":1,"device":"atom-companion","kind":"ready"}\n')
        link.tick(1, snap)
        link.disconnect()
        link.tick(3, snap)
        b.incoming.extend(b'{"v":1,"device":"atom-companion","kind":"ready"}\n')
        link.tick(4, snap)
        self.assertFalse(json.loads(b.outgoing.splitlines()[0])['notify'])

    def test_stale_button_press_cannot_acknowledge_new_snapshot(self):
        wire = Wire(); acks = []
        link = SerialLink('unused', opener=lambda: wire, acknowledge=lambda: acks.append(True))
        old = Snapshot('finished', 's', 1, True)
        link.tick(0, old)
        wire.incoming.extend(b'{"v":1,"device":"atom-companion","kind":"ready"}\n')
        link.tick(1, old)
        wire.incoming.extend(json.dumps(dict(v=1, kind='ack', epoch=link.epoch, seq=1)).encode()+b'\n')
        link.tick(2, Snapshot('needs_input', 's', 2, True))
        self.assertEqual(acks, [])


if __name__ == '__main__':
    unittest.main()
