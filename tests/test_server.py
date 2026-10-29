import json
import threading
import unittest
import urllib.request
import urllib.error
from companion.main import make_server
from companion.state import Reducer
from companion.hook import normalize_hook


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.reducer = Reducer()
        self.server = make_server('test-token', self.reducer, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}/event'

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()

    def send(self, body, token='test-token', origin=None):
        headers = {'Authorization': 'Bearer '+token, 'Content-Type': 'application/json'}
        if origin: headers['Origin'] = origin
        req = urllib.request.Request(self.url, json.dumps(body).encode(), headers)
        try:
            with urllib.request.urlopen(req, timeout=2) as r:
                return r.status
        except urllib.error.HTTPError as e:
            code = e.code
            e.close()
            return code

    def test_authenticated_event_reaches_reducer(self):
        self.assertEqual(self.send(dict(session='a', turn='t', kind='start')), 200)
        self.assertEqual(self.reducer.snapshot.state, 'working')

    def test_unauthorized_or_browser_origin_cannot_change_state(self):
        body = dict(session='a', turn='t', kind='start')
        self.assertEqual(self.send(body, token='wrong'), 401)
        self.assertEqual(self.send(body, origin='https://example.com'), 403)
        self.assertEqual(self.reducer.snapshot.state, 'idle')

    def test_oversize_unknown_or_secret_fields_rejected(self):
        self.assertEqual(self.send(dict(session='a', turn='t', kind='start', prompt='secret')), 400)
        self.assertEqual(self.send(dict(session='a', turn='t', kind='magic')), 400)
        self.assertEqual(self.send({'large': 'x'*5000}), 413)

    def test_structured_kind_is_rejected_without_breaking_server(self):
        self.assertEqual(self.send(dict(session='a', turn='t', kind=[])), 400)
        self.assertEqual(self.send(dict(session='a', turn='t', kind='start')), 200)

    def test_duplicate_delivery_does_not_resurrect_acknowledged_wait(self):
        body=dict(session='a', turn='t', kind='needs_input', event_id='same', observed_at_ns=10)
        self.assertEqual(self.send(body), 200)
        self.reducer.acknowledge()
        self.assertEqual(self.send(body), 200)
        self.assertFalse(self.reducer.snapshot.notify)

    def test_source_timestamp_rejects_delayed_older_start(self):
        self.assertEqual(self.send(dict(session='a', turn='new', kind='start', observed_at_ns=20)), 200)
        self.assertEqual(self.send(dict(session='a', turn='new', kind='needs_input', observed_at_ns=21)), 200)
        self.assertEqual(self.send(dict(session='a', turn='old', kind='start', observed_at_ns=10)), 200)
        self.assertEqual(self.reducer.snapshot.state, 'needs_input')

    def test_stop_after_resumed_activity_can_finish_same_turn(self):
        for name in ('UserPromptSubmit','Stop','PreToolUse','Stop'):
            event=normalize_hook(dict(hook_event_name=name,session_id='s',turn_id='t'))
            self.assertEqual(self.send(event),200)
        self.assertEqual(self.reducer.snapshot.state,'finished')


if __name__ == '__main__':
    unittest.main()
