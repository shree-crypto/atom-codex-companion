import test from 'node:test';import assert from 'node:assert/strict';
import {voicePlan,SoundPreview} from '../preview/audio.mjs';
function harness(t){
 t.mock.timers.enable({apis:['setTimeout']});
 const lines=[];let cancels=0;
 t.mock.method(globalThis,'SpeechSynthesisUtterance',function(text){this.text=text;});
 t.mock.method(speechSynthesis,'getVoices',()=>[{name:'Samantha',lang:'en-US'}]);
 t.mock.method(speechSynthesis,'speak',line=>lines.push(line));
 t.mock.method(speechSynthesis,'cancel',()=>{cancels++;});
 const sound=new SoundPreview();sound.enabled=true;t.after(()=>sound.stop());
 return {sound,lines,cancels:()=>cancels};
}
// Node has no speech platform; expose just its browser boundary for controlled tests.
globalThis.SpeechSynthesisUtterance=function(){};
globalThis.speechSynthesis={getVoices(){},speak(){},cancel(){}};
test('speech starts disabled and silent states have no phrases',()=>{
 const sound=new SoundPreview();sound.play('needs_input');assert.equal(sound.utterance,null);
 for(const id of ['idle','interrupted','disconnected'])assert.equal(voicePlan(id).text,'');
});
test('voice uses a cute high pitch and clear input prompt',t=>{
 const {sound,lines}=harness(t);sound.play('needs_input');
 assert.match(lines[0].text,/need you/i);assert.equal(lines[0].pitch,1.55);assert.equal(lines[0].volume,.65);
});
test('attention waits for speech to finish before repeating',t=>{
 const {sound,lines}=harness(t);sound.play('needs_input');t.mock.timers.tick(20000);assert.equal(lines.length,1);
 for(let i=0;i<4;i++){lines.at(-1).onend();t.mock.timers.tick(3000);}
 assert.equal(lines.length,5);
});
test('new message repeats three times, working speaks once',t=>{
 const {sound,lines}=harness(t);sound.play('message');
 for(let i=0;i<3;i++){lines.at(-1).onend();t.mock.timers.tick(1200);}
 assert.equal(lines.length,3);assert.equal(sound.timer,null);
 sound.play('working');lines.at(-1).onend();t.mock.timers.tick(10000);assert.equal(lines.length,4);
});
test('mute cancels current speech and stale callbacks cannot restart it',t=>{
 const {sound,lines,cancels}=harness(t);sound.play('error');const stale=lines[0].onend;sound.mute();stale();t.mock.timers.tick(10000);
 assert.equal(lines.length,1);assert.equal(cancels(),1);assert.equal(sound.timer,null);
});
test('state changes cancel pending repeats and speech errors do not loop',t=>{
 const {sound,lines}=harness(t);sound.play('needs_input');lines[0].onend();sound.play('idle');t.mock.timers.tick(10000);assert.equal(lines.length,1);
 sound.play('message');lines[1].onerror();t.mock.timers.tick(10000);assert.equal(lines.length,2);
});
