"""Generate an original quiet 66-BPM lo-fi keys-and-brushes loop for Working."""
from pathlib import Path
import hashlib,json,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RATE=16000;BPM=66;BEAT=60/BPM;N=round(RATE*BEAT*16)
rng=np.random.default_rng(314159);mix=np.zeros(N,dtype=np.float64)
def add(beat,tone,gain):
    start=round(beat*BEAT*RATE)
    np.add.at(mix,(start+np.arange(len(tone)))%N,tone*gain)
def keys(note,duration=3.7):
    t=np.arange(round(duration*RATE))/RATE;f=440*2**((note-69)/12)
    env=(1-np.exp(-t/.025))*np.exp(-t/1.45)
    return env*(np.sin(2*np.pi*f*t+.35*np.sin(4*np.pi*f*t)*np.exp(-t*1.5))+.12*np.sin(2*np.pi*(f*2.001)*t)*np.exp(-t*2))
chords=[([60,63,67,70],48),([56,60,63,67],41),([55,60,63,67],44),([53,58,62,69],43)]
for bar,(notes,bass) in enumerate(chords):
    for i,note in enumerate(notes):
        add(bar*4+i*.018,keys(note),.10)
        add(bar*4+2.6+i*.014,keys(note,2.1),.045)
    for beat in [0,2.5]:
        t=np.arange(round(.9*RATE))/RATE;freq=440*2**((bass-69)/12)
        add(bar*4+beat,np.sin(2*np.pi*freq*t)*(1-np.exp(-t/.015))*np.exp(-t*4),.11)
    for beat in [0,2]:
        t=np.arange(round(.24*RATE))/RATE
        kick=np.sin(2*np.pi*(45*t+20*.035*(1-np.exp(-t/.035))))*(1-np.exp(-t/.002))*np.exp(-t*24)
        add(bar*4+beat,kick,.11)
    for beat in [1,3]:
        t=np.arange(round(.18*RATE))/RATE;noise=rng.normal(0,1,len(t))
        brushed=np.convolve(noise,np.ones(5)/5,mode='same')*np.exp(-t*32)*(1-np.exp(-t/.004))
        add(bar*4+beat,brushed,.04)
    for step in range(8):
        t=np.arange(round(.07*RATE))/RATE;noise=rng.normal(0,1,len(t))
        hat=(noise-np.convolve(noise,np.ones(7)/7,mode='same'))*np.exp(-t*70)
        add(bar*4+step*.5+(.06 if step%2 else 0),hat,.004)
for beat,note in [(1.5,75),(3.25,74),(6.5,72),(9.5,70),(11.25,72),(14.5,69)]:add(beat,keys(note,1.4),.025)
mix+=.08*np.roll(mix,round(.18*RATE))+.035*np.roll(mix,round(.36*RATE))
mix=np.tanh(mix*1.1);mix-=mix.mean();mix*=(.035*10**(12/20))/np.sqrt(np.mean(mix*mix))
assert np.max(np.abs(mix))<.9
path=ROOT/'preview/voices/naruto-device/working.wav'
with wave.open(str(path),'wb') as stream:
    stream.setparams((1,2,RATE,0,'NONE','not compressed'));stream.writeframes(np.round(mix*32767).astype('<i2').tobytes())
manifest=ROOT/'expressions/device_voice_pack.json';pack=json.loads(manifest.read_text(encoding='utf-8'))
pack['name']='Naruto alerts + slow lo-fi working music'
pack['states']['working']=dict(character='Ambient',phrase='Slow lo-fi — 66 BPM',src=None,source=None,duration=round(N/RATE,3),file='naruto-device/working.wav',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),loop=True,generated='Original 66 BPM instrumental; soft electric keys, bass and brushed drums; quiet RMS -17.1 dBFS (+12 dB from the original working loop); seamless four-bar loop')
manifest.write_text(json.dumps(pack,indent=2)+'\n',encoding='utf-8')
print('Generated original 66-BPM lo-fi loop:',round(N/RATE,3),'seconds')
