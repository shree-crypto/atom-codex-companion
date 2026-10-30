"""Exercise the flashed robot over an explicitly selected USB port; retain levels, not audio."""
import argparse
import json
from pathlib import Path
import secrets
import time
import serial

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--port',required=True)
parser.add_argument('--output',type=Path)
args=parser.parse_args()
result={'port':args.port}


def read_kind(link,kind,seconds=8):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        raw=link.readline(1024)
        try:msg=json.loads(raw)
        except (ValueError,UnicodeDecodeError):continue
        if isinstance(msg,dict) and msg.get('v')==1 and msg.get('kind')==kind:return msg
    raise TimeoutError('No '+kind+' response from the robot')


link=serial.Serial(port=None,baudrate=115200,timeout=.2)
link.dtr=False;link.rts=False;link.port=args.port
with link:
    ready=read_kind(link,'ready')
    assert ready.get('device')=='atom-companion' and ready.get('firmware')=='2.6-s3r-lofi',ready
    assert ready.get('audio') is True, 'Echo Base speaker did not initialize'
    assert ready.get('psram_bytes',0)>=8*1024*1024, 'S3R PSRAM profile did not initialize'
    result['ready']=ready
    link.write(b'MIC_TEST\n');link.flush()
    mic=read_kind(link,'mic_test')
    assert mic.get('recorded') and mic.get('speaker_restored'),mic
    assert mic.get('peak',0)>0, 'Microphone returned a flat signal; check the base or try speaking near it.'
    result['microphone']=mic
    epoch=secrets.token_hex(12)
    result['states']=[]
    for seq,state in enumerate(['idle','working','needs_input','message','finished'],1):
        payload=dict(v=1,epoch=epoch,seq=seq,state=state,session='hardwarecheck',notify=state!='idle')
        frame=(json.dumps(payload)+'\n').encode()
        link.write(frame);link.flush();time.sleep(.1)
        link.write(b'STATUS\n');link.flush()
        status=read_kind(link,'status')
        assert status.get('state')==state,status
        if state=='needs_input' and not status.get('muted'):
            assert status.get('audio_playing') is True, 'Recorded attention audio was not queued'
        result['states'].append(status)
        deadline=time.monotonic()+{'idle':1,'working':3,'needs_input':5,'message':4,'finished':5}[state]
        while time.monotonic()<deadline:
            link.write(frame);link.flush();time.sleep(.4)
    payload.update(seq=6,state='idle',notify=False)
    link.write((json.dumps(payload)+'\n').encode());link.flush()
result['limits']=['Display pixels, audible sound and physical button feel require user confirmation.',
                  'Microphone samples were discarded; no speech was stored or transmitted.']
if args.output:
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
