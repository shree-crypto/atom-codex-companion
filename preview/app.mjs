import {Animator,sample,svg,definitions} from './face.mjs';
import {SoundPreview,voicePlan,voiceStyles,voiceOptions} from './audio.mjs';
const $=id=>document.getElementById(id);
const sound=new SoundPreview(),face=new Animator('idle',0);
sound.onError=message=>{$('audio-status').textContent=message;};
for(const style of voiceStyles){const option=document.createElement('option');option.value=style.id;option.textContent=style.label;$('voice-style').append(option);}
sound.setStyle('naruto');$('voice-style').value='naruto';
sound.onClip=plan=>{
  $('playing-phrase').textContent=plan.text;
  $('clip-source').hidden=!plan.source;
  if(plan.source)$('clip-source').href=plan.source;
};
function syncPhrases(){
  const options=voiceOptions(face.id,sound.style);
  $('phrase').replaceChildren(new Option('Rotate through phrases','auto'),...options.map((p,i)=>new Option(p.text,String(i))));
  $('phrase').disabled=!options.length;
  $('next-phrase').disabled=!options.length;
  sound.variation=null;
  $('playing-phrase').textContent=options.length?options.length+' character clips available for this state.':'';
  $('clip-source').hidden=true;
}
$('phrase').addEventListener('change',async()=>{
  sound.variation=$('phrase').value==='auto'?null:Number($('phrase').value);
  try{await sound.enable();sound.play(face.id,{once:true});syncSound();}catch(error){$('audio-status').textContent=error.message;}
});
$('next-phrase').addEventListener('click',async()=>{
  try{await sound.enable();sound.variation=null;$('phrase').value='auto';sound.play(face.id,{once:true});syncSound();}catch(error){$('audio-status').textContent=error.message;}
});
let now=0,previous=performance.now(),paused=false,demo=false,demoIndex=0,demoAt=0;
const reduced=matchMedia('(prefers-reduced-motion: reduce)');$('reduced').checked=reduced.matches;
const states=new Map(definitions.states.map(s=>[s.id,s]));
for(const s of definitions.states){
  const button=document.createElement('button');button.className='state';button.dataset.id=s.id;
  button.setAttribute('aria-pressed',String(s.id==='idle'));
  const mini=document.createElement('span');mini.className='mini';mini.setAttribute('aria-hidden','true');mini.innerHTML=svg(sample(s.id,0,{reduced:true}));
  const label=document.createElement('span');label.className='state-label';label.textContent=s.label;
  button.append(mini,label);button.addEventListener('click',()=>{stopDemo();choose(s.id,true);});$('states').append(button);
}
function syncSound(){
  $('sound').textContent=sound.enabled?'Sound on':'Sound off';$('sound').setAttribute('aria-pressed',String(sound.enabled));
  $('replay').disabled=!sound.enabled||!voicePlan(face.id).text;
}
function draw(){
  const f=face.frame(now,{reduced:$('reduced').checked});
  $('face').innerHTML=svg(f,{muted:!sound.enabled,color:$('eye-color').value});
  $('face').setAttribute('aria-label',states.get(face.id).label+' expression');
}
function choose(id,play=true){
  face.setState(id,now,{immediate:paused||$('reduced').checked,restart:true});
  const state=states.get(id);$('current-name').textContent=state.label;$('description').textContent=state.description;
  for(const button of $('states').children)button.setAttribute('aria-pressed',String(button.dataset.id===id));
  syncPhrases();
  const cue=voicePlan(id,sound.style);$('cue-description').textContent=cue.text?cue.text+' · '+(cue.repeats===Infinity?'repeats until state changes or muted':cue.repeats===1?'plays once':'repeats 3 times'):'This state stays quiet.';
  if(play)sound.play(id);syncSound();draw();
}
function stopDemo(){demo=false;$('stop-demo').disabled=true;$('demo').textContent='Play demo + sound';}
$('sound').addEventListener('click',async()=>{
  try{if(sound.enabled)sound.mute();else{await sound.enable();sound.play(face.id);}
    $('audio-status').textContent=sound.enabled?'Sound enabled. State buttons play their matching recording.':'Muted. Expressions still show every state.';
  }catch(error){$('audio-status').textContent=error.message;}syncSound();draw();
});
$('volume').addEventListener('input',event=>{sound.volume=Number(event.target.value)/100;$('volume-value').value=event.target.value+'%';});
$('replay').addEventListener('click',()=>sound.play(face.id));
$('voice-style').addEventListener('change',event=>{sound.setStyle(event.target.value);choose(face.id,sound.enabled);});
$('audition').addEventListener('click',async()=>{
  try{await sound.enable();stopDemo();choose('needs_input',false);sound.play('needs_input',{once:true});syncSound();$('audio-status').textContent='One attention sample. Choose another voice to compare; Sound off stops playback.';}
  catch(error){$('audio-status').textContent=error.message;}
});
$('pause').addEventListener('click',()=>{
  paused=!paused;$('pause').setAttribute('aria-pressed',String(paused));$('pause').textContent=paused?'Resume animation':'Pause animation';
  if(paused)sound.stop();
});
$('actual-size').addEventListener('change',event=>document.querySelector('.robot').classList.toggle('actual',event.target.checked));
$('eye-color').addEventListener('change',()=>{
  for(const button of $('states').children)button.querySelector('.mini').innerHTML=svg(sample(button.dataset.id,0,{reduced:true}),{color:$('eye-color').value});
  draw();
});
$('reduced').addEventListener('change',draw);
reduced.addEventListener('change',event=>{$('reduced').checked=event.matches;draw();});
$('demo').addEventListener('click',async()=>{
  try{await sound.enable();syncSound();paused=false;$('pause').textContent='Pause animation';$('pause').setAttribute('aria-pressed','false');
    demo=true;demoIndex=0;demoAt=now;$('stop-demo').disabled=false;$('demo').textContent='Demo running...';choose(definitions.states[0].id);
    $('audio-status').textContent='Demo: each state runs for 10 seconds, with its matching sound.';
  }catch(error){$('audio-status').textContent=error.message;}
});
$('stop-demo').addEventListener('click',()=>{stopDemo();sound.stop();});
document.addEventListener('visibilitychange',()=>{previous=performance.now();if(document.hidden)sound.stop();});
function tick(time){
  const delta=Math.min(100,time-previous);previous=time;
  if(!paused&&!document.hidden)now+=delta;
  if(demo&&!paused&&now-demoAt>=10000){
    demoAt=now;demoIndex++;
    if(demoIndex>=definitions.states.length){stopDemo();choose('idle',false);}else choose(definitions.states[demoIndex].id);
  }
  if(!document.hidden&&!paused)draw();
  requestAnimationFrame(tick);
}
choose('idle',false);requestAnimationFrame(tick);
