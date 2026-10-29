import test from 'node:test';
import assert from 'node:assert/strict';
import { sample, Animator, svg, definitions } from '../preview/face.mjs';

test('idle starts open and a blink closes then reopens',()=>{
  assert.equal(sample('idle',0).eyes[0].h,34);
  assert.ok(sample('idle',5100).eyes[0].h<=4);
  assert.equal(sample('idle',5200).eyes[0].h,34);
});
test('input request keeps wide eyes and does not blink',()=>{
  assert.ok(sample('needs_input',5100).eyes[0].h>=40);
  assert.equal(sample('needs_input',5100).icon,1);
});
test('state morph begins at the current face without jumping',()=>{
  const face=new Animator('idle',0);
  const before=face.frame(1000);
  face.setState('working',1000);
  assert.deepEqual(face.frame(1000),before);
  assert.ok(face.frame(1240).eyes[0].h<20);
});
test('interrupted morph starts from the visible intermediate frame',()=>{
  const face=new Animator('idle',0); face.setState('working',500);
  const before=face.frame(600); face.setState('finished',600);
  assert.deepEqual(face.frame(600),before);
});
test('reduced motion is still expressive but stays still',()=>{
  assert.deepEqual(sample('working',100,{reduced:true}),sample('working',5000,{reduced:true}));
});
test('every state stays within the 128 pixel face',()=>{
  for(const state of definitions.states) for(let t=0;t<11000;t+=71){
    const f=sample(state.id,t);
    for(const eye of f.eyes){
      assert.ok(eye.w>0 && eye.h>=3);
      assert.ok(eye.x-eye.w/2>=0 && eye.x+eye.w/2<=128);
      assert.ok(eye.y-eye.h/2-Math.abs(eye.bend)>=0);
      assert.ok(eye.y+eye.h/2+Math.abs(eye.bend)<=128);
    }
    assert.ok(!svg(f).includes('NaN'));
  }
});
test('sounds are reserved for attention transitions',()=>{
  for(const id of ['idle','working','interrupted','disconnected'])
    assert.deepEqual(definitions.states.find(s=>s.id===id).cue,[]);
  assert.equal(definitions.states.find(s=>s.id==='needs_input').cue.length,2);
  assert.equal(definitions.states.find(s=>s.id==='finished').cue.length,3);
});

test('working keeps moving throughout its cycle and shows activity',()=>{
 for(let t=0;t<5000;t+=150)assert.notDeepEqual(sample('working',t),sample('working',t+100));
 assert.equal(sample('working',0).icon,6);
});
test('attention pulses and message envelope bounces',()=>{
 assert.notEqual(sample('needs_input',0).attention,sample('needs_input',450).attention);
 assert.notEqual(sample('message',0).notification,sample('message',450).notification);
});
