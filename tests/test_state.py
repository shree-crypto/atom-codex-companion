import unittest
from companion.state import Event, Reducer


class StateTests(unittest.TestCase):
    def test_other_completion_cannot_hide_input(self):
        r = Reducer()
        r.apply(Event('a', 't1', 1, 'start'))
        r.apply(Event('a', 't1', 2, 'needs_input', 'p1'))
        r.apply(Event('b', 't2', 1, 'start'))
        self.assertEqual(r.apply(Event('b', 't2', 2, 'finished')).state, 'needs_input')

    def test_duplicate_and_stale_events_do_not_replay(self):
        r = Reducer()
        r.apply(Event('a', 't', 1, 'start'))
        snap = r.apply(Event('a', 't', 3, 'finished'))
        self.assertEqual(r.apply(Event('a', 't', 3, 'finished')), snap)
        self.assertEqual(r.apply(Event('a', 't', 2, 'activity')), snap)

    def test_retired_turn_cannot_clear_new_wait(self):
        r = Reducer()
        r.apply(Event('a', 'old', 1, 'start'))
        r.apply(Event('a', 'new', 2, 'start'))
        r.apply(Event('a', 'new', 3, 'needs_input', 'q'))
        self.assertEqual(r.apply(Event('a', 'old', 4, 'finished')).state, 'needs_input')

    def test_acknowledgement_does_not_resolve_wait(self):
        r = Reducer()
        r.apply(Event('a', 't', 1, 'needs_input', 'q'))
        snap = r.acknowledge()
        self.assertEqual(snap.state, 'needs_input')
        self.assertFalse(snap.notify)

    def test_only_matching_request_clears_wait(self):
        r = Reducer()
        r.apply(Event('a', 't', 1, 'needs_input', 'q'))
        self.assertEqual(r.apply(Event('a', 't', 2, 'resolved', 'wrong')).state, 'needs_input')
        self.assertEqual(r.apply(Event('a', 't', 3, 'resolved', 'q')).state, 'working')

    def test_child_completion_leaves_parent_working(self):
        r = Reducer()
        r.apply(Event('parent', 't', 1, 'start'))
        r.apply(Event('child', 'c', 1, 'start'))
        self.assertEqual(r.apply(Event('child', 'c', 2, 'finished')).state, 'working')

    def test_error_and_interrupt_never_become_finished(self):
        for kind, expected in [('error', 'error'), ('interrupt', 'interrupted')]:
            with self.subTest(kind=kind):
                r = Reducer()
                self.assertEqual(r.apply(Event('a', 't', 1, kind)).state, expected)

    def test_message_overlay_expires_and_restores_work(self):
        r = Reducer()
        r.apply(Event('a', 't', 1, 'start'), now=0)
        self.assertEqual(r.apply(Event('a', 't', 2, 'message'), now=1).state, 'message')
        self.assertEqual(r.tick(5).state, 'working')

    def test_message_does_not_hide_wait(self):
        r = Reducer()
        r.apply(Event('a', 't', 1, 'needs_input', 'q'))
        self.assertEqual(r.apply(Event('a', 't', 2, 'message')).state, 'needs_input')

    def test_unrelated_activity_does_not_rearm_acknowledged_request(self):
        r = Reducer()
        r.apply(Event('a', 't', 1, 'needs_input', 'q'))
        r.acknowledge()
        self.assertFalse(r.apply(Event('a', 't', 2, 'activity')).notify)

    def test_error_survives_routine_activity(self):
        r=Reducer()
        r.apply(Event('a', 't', 1, 'error'))
        self.assertEqual(r.apply(Event('a', 't', 2, 'activity')).state, 'error')

    def test_repeated_finished_without_activity_stays_acknowledged(self):
        r=Reducer(); r.apply(Event('a','t',1,'finished')); r.acknowledge()
        self.assertFalse(r.apply(Event('a','t',2,'finished')).notify)


if __name__ == '__main__':
    unittest.main()
