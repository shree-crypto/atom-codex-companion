import definitions from './definitions.mjs';
export function voicePlan(id){
  const state=definitions.states.find(s=>s.id===id);
  if(!state)throw new RangeError('Unknown expression');
  return {text:state.voice||'',repeats:id==='needs_input'||id==='error'?Infinity:id==='working'?1:3};
}
export class SoundPreview {
  constructor(){this.enabled=false;this.volume=.65;this.timer=null;this.generation=0;this.utterance=null;}
  async enable(){
    if(!globalThis.speechSynthesis||!globalThis.SpeechSynthesisUtterance)throw new Error('Voice playback is unavailable in this browser. Try Chrome, Edge or Safari.');
    this.enabled=true;
  }
  stop(){
    this.generation++;clearTimeout(this.timer);this.timer=null;
    if(this.utterance){this.utterance.onend=null;this.utterance.onerror=null;globalThis.speechSynthesis?.cancel();this.utterance=null;}
  }
  mute(){this.enabled=false;this.stop();}
  play(id){
    this.stop();if(!this.enabled)return;
    const plan=voicePlan(id);if(!plan.text)return;
    const generation=this.generation;let remaining=plan.repeats;
    const cycle=()=>{
      if(generation!==this.generation||!this.enabled)return;
      this.timer=null;
      const line=new SpeechSynthesisUtterance(plan.text);
      const voices=speechSynthesis.getVoices().filter(v=>/^en(?:-|$)/i.test(v.lang));
      line.voice=voices.find(v=>/Samantha|Aria|Jenny|Google US English/i.test(v.name))||voices[0]||null;
      line.lang=line.voice?.lang||'en-US';line.pitch=1.55;line.rate=1.05;line.volume=this.volume;
      line.onend=()=>{
        if(generation!==this.generation)return;
        this.utterance=null;remaining--;
        if(remaining>0)this.timer=setTimeout(cycle,plan.repeats===Infinity?3000:1200);
      };
      line.onerror=()=>{if(generation===this.generation){this.utterance=null;this.stop();}};
      this.utterance=line;speechSynthesis.speak(line);
    };
    cycle();
  }
}
