import test from 'node:test';import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {voicePlan,voiceStyles,SoundPreview} from '../preview/audio.mjs';
globalThis.Audio=function(){};
function harness(t){
 t.mock.timers.enable({apis:['setTimeout']});
 const players=[];let plays=0,pauses=0;
 t.mock.method(globalThis,'Audio',function(src){this.src=src;this.play=()=>{plays++;return Promise.resolve();};this.pause=()=>{pauses++;};players.push(this);});
 const sound=new SoundPreview();sound.enabled=true;t.after(()=>sound.stop());
 return {sound,players,plays:()=>plays,pauses:()=>pauses};
}
test('starts disabled; quiet states have no recording',()=>{
 const sound=new SoundPreview();sound.play('needs_input');assert.equal(sound.player,null);
 for(const id of ['idle','interrupted','disconnected'])assert.equal(voicePlan(id).src,'');
});
test('five styles map every voiced state to a bundled WAV or OGG',()=>{
 assert.equal(voiceStyles.filter(s=>!s.online&&!s.fixed).length,5);
 for(const style of voiceStyles.filter(s=>!s.online))for(const id of ['working','needs_input','message','finished','error']){
  const plan=voicePlan(id,style.id),data=readFileSync(new URL('../preview/'+plan.src,import.meta.url));
  assert.ok(['RIFF','OggS'].includes(data.subarray(0,4).toString()));assert.ok(data.length>100);
 }
 assert.equal(voicePlan('needs_input','bright').rate,1.18);
 assert.throws(()=>voicePlan('needs_input','missing'),RangeError);
});
test('play uses recorded audio with explicit volume and bright pitch variation',t=>{
 const {sound,players}=harness(t);sound.setStyle('bright');sound.play('needs_input');
 assert.equal(players[0].src,'voices/cute/needs_input.wav');assert.equal(players[0].playbackRate,1.18);
 assert.equal(players[0].preservesPitch,false);assert.equal(players[0].volume,.65);
 sound.volume=.4;assert.equal(players[0].volume,.4);
});
test('attention waits for recording end before repeating',t=>{
 const {sound,players,plays}=harness(t);sound.play('needs_input');t.mock.timers.tick(20000);assert.equal(plays(),1);
 for(let i=0;i<4;i++){players[0].onended();t.mock.timers.tick(3000);}
 assert.equal(plays(),5);
});
test('message repeats three times; working and audition play once',t=>{
 const {sound,players,plays}=harness(t);sound.play('message');
 for(let i=0;i<3;i++){players[0].onended();t.mock.timers.tick(1200);}
 assert.equal(plays(),3);assert.equal(sound.timer,null);
 sound.play('working');players[1].onended();t.mock.timers.tick(10000);assert.equal(plays(),4);
 sound.play('needs_input',{once:true});players[2].onended();t.mock.timers.tick(10000);assert.equal(plays(),5);
});
test('mute cancels audio and stale callbacks cannot restart it',t=>{
 const {sound,players,plays,pauses}=harness(t);sound.play('error');const stale=players[0].onended;
 sound.mute();stale();t.mock.timers.tick(10000);assert.equal(plays(),1);assert.equal(pauses(),1);assert.equal(sound.timer,null);
});
test('switching styles cancels a pending repeat; next cue uses new files',t=>{
 const {sound,players,plays}=harness(t);sound.play('needs_input');players[0].onended();
 sound.setStyle('warm');t.mock.timers.tick(10000);assert.equal(plays(),1);
 sound.play('needs_input');assert.equal(players[1].src,'voices/warm/needs_input.wav');
});
test('quiet state cancels repeats and media errors report without looping',t=>{
 const {sound,players,plays}=harness(t);sound.play('needs_input');players[0].onended();sound.play('idle');
 t.mock.timers.tick(10000);assert.equal(plays(),1);
 let message='';sound.onError=text=>{message=text;};sound.play('message');players[1].onerror();
 t.mock.timers.tick(10000);assert.equal(plays(),2);assert.match(message,/could not play/);
});
test('rejected playback stops and surfaces a useful error',async t=>{
 const {sound,players}=harness(t);let reported=false;sound.onError=()=>{reported=true;};
 sound.play('needs_input');players[0].play=()=>Promise.reject(new Error('blocked'));
 players[0].onended();t.mock.timers.tick(3000);await Promise.resolve();
 assert.equal(reported,true);assert.equal(sound.player,null);assert.equal(sound.timer,null);
});


test('anime packs provide distinct online variations and preserve source links',()=>{
 for(const style of voiceStyles.filter(s=>s.online)){
  const seen=new Set();
  for(let i=0;i<3;i++){const p=voicePlan('needs_input',style.id,i);assert.match(p.src,/^https:\/\/sounds\.myinstantplay\.com\//);assert.match(p.source,/^https:/);seen.add(p.src);}
  assert.equal(seen.size,3);
  assert.equal(voicePlan('idle',style.id).src,'');
 }
});
test('automatic anime rotation changes repeated lines; explicit choice stays fixed',t=>{
 const {sound,players}=harness(t);sound.setStyle('naruto');sound.play('needs_input');
 const first=players[0].src;players[0].onended();t.mock.timers.tick(3000);assert.notEqual(players[0].src,first);
 sound.stop();sound.variation=1;sound.play('needs_input');const chosen=players[1].src;
 players[1].onended();t.mock.timers.tick(3000);assert.equal(players[1].src,chosen);
 sound.mute();t.mock.timers.tick(3000);assert.equal(sound.player,null);
});


test('device crew uses one fixed phrase per state and five different characters',()=>{
 const expected={working:'Shikamaru',needs_input:'Hinata',message:'Kakashi',finished:'Naruto',error:'Killer Bee'};
 const sources=new Set();
 for(const [state,character] of Object.entries(expected)){
  const plan=voicePlan(state,'naruto-device');assert.ok(plan.text.startsWith(character+' — '));
  assert.deepEqual(voicePlan(state,'naruto-device',7),plan);sources.add(plan.src);
  const data=readFileSync(new URL('../preview/'+plan.src,import.meta.url));assert.equal(data.subarray(0,4).toString(),'RIFF');
 }
 assert.equal(sources.size,5);
 for(const state of ['idle','interrupted','disconnected'])assert.equal(voicePlan(state,'naruto-device').src,'');
});
