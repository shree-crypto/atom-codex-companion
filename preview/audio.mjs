import definitions from './definitions.mjs';
import {animeClips} from './anime.mjs';
export const voiceStyles=[
  {id:'naruto',label:'Naruto · character lines',online:true,rate:1},
  {id:'jjk',label:'Jujutsu Kaisen · character lines',online:true,rate:1},
  {id:'mha',label:'My Hero Academia · character lines',online:true,rate:1},
  {id:'cute',label:'Cute character',folder:'cute',rate:1},
  {id:'bright',label:'Bright / anime-like',folder:'cute',rate:1.18},
  {id:'warm',label:'Warm character',folder:'warm',rate:1},
  {id:'mature',label:'Mature character',folder:'mature',rate:1},
  {id:'spoken',label:'Spoken announcer',folder:'spoken',rate:1,ext:'ogg'}
];
const reactions={working:'Little effort call',needs_input:'Attention call',message:'Surprised call',finished:'Happy reaction',error:'Concerned reaction'};
const voiced=['working','needs_input','message','finished','error'];
export function voiceOptions(id,style){
  const clips=animeClips[style];
  if(!clips||!voiced.includes(id))return [];
  // Start each state at a different line; every clip remains available to audition.
  const offset=voiced.indexOf(id)*2%clips.length;
  return [...clips.slice(offset),...clips.slice(0,offset)];
}
export function voicePlan(id,style='cute',variation=0){
  if(!definitions.states.some(s=>s.id===id))throw new RangeError('Unknown expression');
  const profile=voiceStyles.find(s=>s.id===style);if(!profile)throw new RangeError('Unknown voice style');
  const options=voiceOptions(id,style);
  if(profile.online){
    const clip=options[((variation%options.length)+options.length)%options.length];
    return {text:clip?.text||'',src:clip?.src||'',source:clip?.source||'',rate:1,
      repeats:id==='needs_input'||id==='error'?Infinity:id==='working'?1:3};
  }
  const spoken={working:'Go!',needs_input:'Ready?',message:'Ready?',finished:'Mission completed',error:'Hold!'};
  return {text:reactions[id]?(style==='spoken'?spoken[id]:reactions[id]):'',src:reactions[id]?`voices/${profile.folder}/${id}.${profile.ext||'wav'}`:'',rate:profile.rate,
    repeats:id==='needs_input'||id==='error'?Infinity:id==='working'?1:3};
}
export class SoundPreview {
  constructor(){this.enabled=false;this._volume=.65;this.style='cute';this.timer=null;this.generation=0;this.player=null;this.onError=null;this.onClip=null;this.variation=null;this.rotations=new Map();}
  get volume(){return this._volume;}
  set volume(value){this._volume=Math.max(0,Math.min(1,Number(value)||0));if(this.player)this.player.volume=this._volume;}
  async enable(){if(!globalThis.Audio)throw new Error('Recorded audio is unavailable in this browser.');this.enabled=true;}
  setStyle(id){if(!voiceStyles.some(s=>s.id===id))throw new RangeError('Unknown voice style');this.stop();this.style=id;}
  stop(){
    this.generation++;clearTimeout(this.timer);this.timer=null;
    if(this.player){this.player.onended=null;this.player.onerror=null;this.player.pause();this.player=null;}
  }
  mute(){this.enabled=false;this.stop();}
  play(id,{once=false}={}){
    this.stop();if(!this.enabled)return;
    const key=this.style+':'+id;
    const nextPlan=()=>{const index=this.variation??(this.rotations.get(key)||0);if(this.variation===null)this.rotations.set(key,index+1);return voicePlan(id,this.style,index);};
    let plan=nextPlan();if(!plan.src)return;
    const generation=this.generation;let remaining=once?1:plan.repeats;
    const player=new Audio(plan.src);this.player=player;
    player.volume=this.volume;player.playbackRate=plan.rate;player.preservesPitch=false;
    const fail=()=>{if(generation!==this.generation)return;this.stop();this.onError?.('Recording could not play. Check your browser audio settings and try Hear sample.');};
    const cycle=()=>{
      if(generation!==this.generation||!this.enabled)return;
      this.timer=null;player.src=plan.src;player.currentTime=0;this.onClip?.(plan);player.play().catch(fail);
    };
    player.onended=()=>{
      if(generation!==this.generation)return;
      remaining--;
      if(remaining>0){plan=nextPlan();this.timer=setTimeout(cycle,plan.repeats===Infinity?3000:1200);}
    };
    player.onerror=fail;cycle();
  }
}
