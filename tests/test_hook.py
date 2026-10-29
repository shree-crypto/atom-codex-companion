import io
import json
import subprocess
import sys
import unittest
from companion.hook import normalize_hook, forward_hook


class HookTests(unittest.TestCase):
    def test_unknown_and_child_stop_are_ignored(self):
        for kind in ('MadeUp', 'SubagentStop'):
            self.assertIsNone(normalize_hook({'hook_event_name': kind, 'session_id': 's', 'turn_id': 't'}))

    def test_only_metadata_leaves_hook(self):
        event = normalize_hook(dict(hook_event_name='PermissionRequest', session_id='s',
                                   turn_id='t', prompt='secret', tool_input={'command': 'secret'}))
        self.assertEqual(event['kind'], 'needs_input')
        self.assertNotIn('secret', json.dumps(event))
        self.assertNotIn('decision', event)
        self.assertNotEqual(event['session'], 's')

    def test_finished_does_not_infer_question(self):
        event = normalize_hook(dict(hook_event_name='Stop', session_id='s', turn_id='t',
                                   last_assistant_message='What do you want?'))
        self.assertEqual(event['kind'], 'finished')

    def test_missing_identity_is_ignored(self):
        self.assertIsNone(normalize_hook({'hook_event_name': 'Stop'}))

    def test_absent_companion_does_not_fail_hook(self):
        self.assertIsNone(forward_hook({'kind': 'finished'}, 'http://127.0.0.1:1/event', 'x'))

    def test_hook_is_silent_and_successful_without_config(self):
        result = subprocess.run([sys.executable, '-m', 'companion.hook', '--config', 'does-not-exist.json'],
                                input='{}', capture_output=True, text=True, timeout=3)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
