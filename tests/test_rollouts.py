import json,tempfile,unittest
from pathlib import Path
from companion.rollouts import Cursor,RolloutWatcher,MAX_RECORD
from companion.state import Reducer,Event


def record(kind,**fields):
    return dict(type='event_msg',payload=dict(type=kind,**fields))
def response(kind,**fields):
    return dict(type='response_item',payload=dict(type=kind,**fields))

class RolloutTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'rollout-2026-10-30T00-00-00-11111111-1111-1111-1111-111111111111.jsonl'
        self.path.touch();self.cursor=Cursor(self.path)
    def test_real_lifecycle_and_message_without_content_leaking(self):
        events=self.cursor.parse(record('task_started',turn_id='t'))
        events+=self.cursor.parse(record('item_completed',turn_id='t',item=dict(type='AgentMessage',phase='commentary',content='secret prompt')))
        events+=self.cursor.parse(record('task_complete',turn_id='t',last_agent_message='secret output'))
        self.assertEqual([e['kind'] for e in events],['start','message','finished'])
        self.assertNotIn('secret',json.dumps(events))
    def test_pending_async_question_survives_stop_and_tool_activity(self):
        self.cursor.parse(record('task_started',turn_id='t'))
        question=self.cursor.parse(response('function_call',name='request_user_input_async',call_id='call_q'))
        self.assertEqual(question[0]['kind'],'needs_input')
        self.assertEqual(self.cursor.parse(response('function_call_output',call_id='call_q',output='pending')),[])
        self.assertEqual(self.cursor.parse(record('task_complete',turn_id='t')),[])
        reply=json.dumps([dict(questionItemId=json.dumps(['request_user_input_async','call_q',0]),answer='secret')])
        resolved=self.cursor.parse(response('message',role='user',content=[dict(type='input_text',text='<send_user_message_question_reply>'+reply+'</send_user_message_question_reply>')]))
        self.assertEqual(resolved[0]['kind'],'resolved');self.assertEqual(resolved[0]['request_id'],question[0]['request_id'])
    def test_sync_answer_resolves_only_its_request(self):
        self.cursor.parse(record('task_started',turn_id='t'))
        self.cursor.parse(response('function_call',name='request_user_input',call_id='q'))
        self.assertEqual(self.cursor.parse(response('function_call_output',call_id='other')),[])
        self.assertEqual(self.cursor.parse(response('function_call_output',call_id='q'))[0]['kind'],'resolved')
    def test_final_message_is_not_an_incoming_message(self):
        self.cursor.parse(record('task_started',turn_id='t'))
        self.assertEqual(self.cursor.parse(record('item_completed',turn_id='t',item=dict(type='AgentMessage',phase='final'))),[])
    def test_child_completion_is_only_message(self):
        self.cursor.parse(record('task_started',turn_id='t'))
        events=self.cursor.parse(record('item_completed',turn_id='t',item=dict(type='SubAgentActivity',kind='completed')))
        self.assertEqual(events[0]['kind'],'message')
    def test_partial_lines_wait_and_oversize_records_do_not_poison_next_event(self):
        raw=json.dumps(record('task_started',turn_id='t')).encode()
        self.path.write_bytes(raw[:12]);self.assertEqual(self.cursor.read(),[])
        with self.path.open('ab') as f:f.write(raw[12:]+b'\n'+b'x'*(MAX_RECORD+20)+b'\n'+json.dumps(record('task_complete',turn_id='t')).encode()+b'\n')
        self.assertEqual([e['kind'] for e in self.cursor.read()],['start','finished'])
    def test_existing_history_is_not_replayed_but_append_is_observed(self):
        self.path.write_text(json.dumps(record('task_complete',turn_id='old'))+'\n',encoding='utf-8')
        watcher=RolloutWatcher(self.path.parent);self.assertEqual(watcher.poll(0),[])
        with self.path.open('a') as f:f.write(json.dumps(record('task_started',turn_id='new'))+'\n')
        self.assertEqual([e['kind'] for e in watcher.poll(1)],['start'])
    def test_delayed_history_cannot_override_a_newer_native_hook(self):
        from datetime import datetime,timezone,timedelta
        import time
        reducer=Reducer()
        self.cursor.parse(record('task_started',turn_id='t'))
        request=self.cursor.event('needs_input',request='q')[0]
        reducer.apply(Event(seq=1,**request))
        old=record('item_completed',turn_id='t',item=dict(type='CommandExecution'))
        old['timestamp']=(datetime.now(timezone.utc)-timedelta(seconds=10)).isoformat()
        delayed=self.cursor.parse(old)[0]
        self.assertLess(delayed['observed_at_ns'],request['observed_at_ns'])
        self.assertEqual(reducer.apply(Event(seq=2,**delayed)).state,'needs_input')

    def test_routine_activity_does_not_cut_off_message_overlay(self):
        reducer=Reducer();reducer.apply(Event('s','t',1,'start'),now=0)
        reducer.apply(Event('s','t',2,'message'),now=1)
        self.assertEqual(reducer.apply(Event('s','t',3,'activity'),now=1.2).state,'message')
        self.assertEqual(reducer.tick(5).state,'working')
    def test_working_has_an_audible_entry_cue(self):
        reducer=Reducer();self.assertTrue(reducer.apply(Event('s','t',1,'start')).notify)
        first=reducer.snapshot
        self.assertEqual(reducer.apply(Event('s','t',2,'activity')),first)

if __name__=='__main__':unittest.main()
