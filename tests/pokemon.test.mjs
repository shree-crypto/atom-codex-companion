import definitions from '../preview/definitions.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {pokemonThemes,pokemonSvg,pokemonFrame} from '../preview/pokemon.mjs';
test('eight distinct faces render all active states at 128px',()=>{
 assert.equal(new Set(pokemonThemes.map(t=>t.id)).size,8);
 for(const t of pokemonThemes)for(const {id:state} of definitions.states.filter(s=>s.id!=='message')){
  const s=pokemonSvg(t.id,state);assert.ok(Number.isFinite(pokemonFrame(state,100).gaze));assert.ok(s.includes('viewBox="0 0 128 128"'));assert.ok(s.includes(t.name));assert.ok(/data-mouth d="M/.test(s));assert.ok(!/undefined|NaN/.test(s));
 }
});
test('working moves continuously; reduced motion is deterministic',()=>{
 assert.notEqual(pokemonFrame('working',100).gaze,pokemonFrame('working',700).gaze);
 assert.deepEqual(pokemonFrame('working',100,{reduced:true}),pokemonFrame('working',3000,{reduced:true}));
 for(let time=0;time<9000;time+=43){const f=pokemonFrame('idle',time);assert.ok(f.blink>=.06&&f.blink<=1);}
 assert.equal(pokemonFrame('needs_input',4150).blink,1);
});
test('unknown characters and states are rejected',()=>{
 assert.throws(()=>pokemonSvg('unknown'),RangeError);assert.throws(()=>pokemonFrame('message',0),RangeError);
});
