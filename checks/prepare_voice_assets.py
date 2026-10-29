"""Prepare locally downloaded CC0 recordings; no remote runtime dependency."""
from pathlib import Path
import io
import json
import wave
import zipfile
import struct
import argparse
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'preview/voices'
OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--archives',type=Path,default=ROOT/'.runtime/voice-research')
research=parser.parse_args().archives
mapping={'working':['jump1.wav'],'needs_input':['jump2.wav','jump1.wav'],
         'message':['jump3.wav'],'finished':['healed1.wav'],'error':['damaged1.wav']}
manifest=[]


def read_clip(data):
    assert data[:4]==b'RIFF' and data[8:12]==b'WAVE'
    chunks={};offset=12
    while offset+8<=len(data):
        name=data[offset:offset+4];size=struct.unpack_from('<I',data,offset+4)[0]
        chunks[name]=data[offset+8:offset+8+size];offset+=8+size+(size%2)
    tag,channels,rate,_,_,bits=struct.unpack_from('<HHIIHH',chunks[b'fmt '])
    width=bits//8;raw=chunks[b'data']
    if tag==3 and width==4:
        a=np.frombuffer(raw,dtype='<f4').astype(float)
    elif tag==1 and width==2:
        a=np.frombuffer(raw,dtype='<i2').astype(float)/32768
    elif tag==1 and width==3:
        b=np.frombuffer(raw,dtype=np.uint8).reshape(-1,3).astype(np.int32)
        a=b[:,0]+(b[:,1]<<8)+(b[:,2]<<16)
        a=((a+8388608)%16777216-8388608).astype(float)/8388608
    else:
        raise ValueError(f'Unsupported PCM sample width {width}')
    a=a.reshape(-1,channels).mean(axis=1)
    audible=np.flatnonzero(np.abs(a)>.008)
    if len(audible):a=a[max(0,audible[0]-int(rate*.03)):min(len(a),audible[-1]+int(rate*.07))]
    a=np.interp(np.arange(int(len(a)*22050/rate))*rate/22050,np.arange(len(a)),a)
    return a


with zipfile.ZipFile(research/'rpg.zip') as z:
    (OUT/'character-pack-readme.txt').write_bytes(z.read('RPG Voice Starter Pack/readme.txt'))
    for num,folder in enumerate(['cute','warm','mature'],1):
        (OUT/folder).mkdir(exist_ok=True)
        for state,names in mapping.items():
            chunks=[read_clip(z.read(f'RPG Voice Starter Pack/Type {num}/{name}')) for name in names]
            a=chunks[0]
            for chunk in chunks[1:]:a=np.concatenate([a,np.zeros(4410),chunk])
            a=a*.8/max(.01,np.max(np.abs(a)))
            edge=min(110,len(a)//2);a[:edge]*=np.linspace(0,1,edge);a[-edge:]*=np.linspace(1,0,edge)
            p=OUT/folder/(state+'.wav')
            with wave.open(str(p),'wb') as f:
                f.setparams((1,2,22050,0,'NONE','not compressed'));f.writeframes((a*32767).astype('<i2').tobytes())
            manifest.append({'file':f'{folder}/{state}.wav','source':'cicifyre / Female RPG Voice Starter Pack',
                             'originals':[f'Type {num}/{name}' for name in names], 'duration':round(len(a)/22050,3)})
with zipfile.ZipFile(research/'kenney-oga.zip') as z:
    (OUT/'kenney-license.txt').write_bytes(z.read('License.txt'))
    (OUT/'spoken').mkdir(exist_ok=True)
    for state,name in {'working':'go','needs_input':'ready','message':'ready','finished':'mission_completed','error':'war_hold'}.items():
        (OUT/'spoken'/(state+'.ogg')).write_bytes(z.read(f'Female/{name}.ogg'))
        manifest.append({'file':f'spoken/{state}.ogg','source':'Kenney / Voiceover Pack','originals':[f'Female/{name}.ogg']})
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,indent=2))
