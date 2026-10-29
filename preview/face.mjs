import definitions from './definitions.mjs';
export { definitions };
const byId=new Map(definitions.states.map(s=>[s.id,s]));
const clamp=x=>Math.max(0,Math.min(1,x));
export const ease=x=>{x=clamp(x);return x*x*(3-2*x);};
const mix=(a,b,t)=>a+(b-a)*t;

function blinkAt(age){
  const b=definitions.blink,total=b.closeMs+b.holdMs+b.openMs;
  const phase=((age%b.periodMs)+b.periodMs)%b.periodMs-(b.periodMs-total);
  if(phase<0)return 1;
  if(phase<b.closeMs)return 1-.92*ease(phase/b.closeMs);
  if(phase<b.closeMs+b.holdMs)return .08;
  return .08+.92*ease((phase-b.closeMs-b.holdMs)/b.openMs);
}
function gazeAt(age){
  const p=((age%10000)+10000)%10000;
  if(p<2400)return 0;if(p<2800)return ease((p-2400)/400);
  if(p<3800)return 1;if(p<4200)return 1-ease((p-3800)/400);
  if(p<6200)return 0;if(p<6600)return -ease((p-6200)/400);
  if(p<7400)return -1;if(p<7800)return -(1-ease((p-7400)/400));return 0;
}
export function sample(id,age,{reduced=false}={}){
  const s=byId.get(id);if(!s)throw new RangeError('Unknown expression');
  const phase=reduced?0:age*2*Math.PI/1800;
  const gaze=reduced?0:id==='working'?9*Math.sin(phase):s.gaze*gazeAt(age);
  const breath=reduced?0:s.breathe*Math.sin(age*2*Math.PI/3800);
  const open=reduced||!s.blink?1:blinkAt(age);
  const shift=id==='message'?3*Math.sin(phase):0;
  const eyes=[40,88].map((x,i)=>({x:x+gaze+shift,y:64+breath+(id==='error'?(i?2:-1):id==='working'?3*Math.cos(phase+i*Math.PI):0),
    w:s.w,h:Math.max(3,(s.h-(id==='error'&&i?5:0)+(id==='needs_input'?2*Math.sin(phase):id==='message'?(i?-7:3)*Math.cos(phase):0))*open),bend:s.bend}));
  return {eyes,mouth:s.mouth,brow:s.brow,icon:id==='working'?6:s.icon,iconAlpha:1,
    activity:phase,attention:id==='needs_input'?1+.12*Math.sin(phase):1,notification:id==='message'?-3*Math.abs(Math.sin(phase)):0};
}
function blend(a,b,t){
  return {eyes:b.eyes.map((eye,i)=>Object.fromEntries(Object.keys(eye).map(k=>[k,mix(a.eyes[i][k],eye[k],t)]))),
    mouth:mix(a.mouth,b.mouth,t),brow:mix(a.brow,b.brow,t),
    activity:b.activity,attention:mix(a.attention,b.attention,t),notification:mix(a.notification,b.notification,t),
    icon:t<.5?a.icon:b.icon,iconAlpha:t<.5?a.iconAlpha*(1-t*2):b.iconAlpha*(t*2-1)};
}
export class Animator {
  constructor(id='idle',now=0){this.id=id;this.entered=now;this.previous=sample(id,0);this.immediate=true;}
  setState(id,now,{immediate=false,restart=false}={}){
    if(!byId.has(id))throw new RangeError('Unknown expression');
    if(id===this.id&&!restart)return;
    this.previous=this.frame(now);this.id=id;this.entered=now;this.immediate=immediate;
  }
  frame(now,{reduced=false}={}){
    const age=Math.max(0,now-this.entered), target=sample(this.id,age,{reduced});
    if(reduced||this.immediate||age>=definitions.transitionMs)return target;
    if(age===0)return this.previous;
    return blend(this.previous,target,ease(age/definitions.transitionMs));
  }
}
const n=x=>Number(x.toFixed(3));
export function eyePath(eye){
  const points=[],r=Math.min(eye.w/2,eye.h/2);
  for(const sign of [-1,1]){
    for(let i=0;i<=40;i++){
      const dx=(sign<0?i/40:1-i/40)*eye.w-eye.w/2;
      const edge=Math.max(0,Math.abs(dx)-(eye.w/2-r));
      const half=eye.h/2-r+Math.sqrt(Math.max(0,r*r-edge*edge));
      const bend=eye.bend*(4*dx*dx/(eye.w*eye.w)-.5);
      points.push([n(eye.x+dx),n(eye.y+bend+sign*half)]);
    }
  }
  return 'M'+points.map(p=>p.join(',')).join('L')+'Z';
}
function iconShape(icon){
  if(icon===1)return '<path d="M64 15v10M44 24l-5-4m45 4 5-4"/><circle cx="64" cy="32" r="2" fill="currentColor"/>';
  if(icon===2)return '<path d="M64 99v9"/><circle cx="64" cy="114" r="1.4" fill="currentColor"/>';
  if(icon===3)return '<rect x="50" y="15" width="28" height="19" rx="4"/><path d="m51 17 13 10 13-10"/><circle cx="80" cy="14" r="4" fill="currentColor" stroke="none"/>';
  if(icon===4)return '<path d="M59 103h10"/>';
  if(icon===5)return '<path d="M53 106l7-7q3-3 6 0m9 5-7 7q-3 3-6 0m-1-7 6 3M52 96l-3-3m27 20 3 3"/>';
  return '';
}
export const eyeColors=Object.freeze({blue:'#397dcc',green:'#2eab79',orange:'#ed8b35'});
export function svg(frame,{size=128,muted=false,color='blue'}={}){
  const p={...definitions.palette,eye:eyeColors[color]??eyeColors.blue};
  const eyes=frame.eyes.map(e=>`<path d="${eyePath(e)}"/>`).join('');
  const mouth=`<path d="M57 92q7 8 14 0" opacity="${n(frame.mouth)}" fill="none" stroke="${p.eye}" stroke-width="2.4" stroke-linecap="round"/>`;
  const brows=`<g opacity="${n(frame.brow)}" stroke="${p.eye}" stroke-width="2.5" stroke-linecap="round"><path d="M27 39l25 6m24-1 25-7"/></g>`;
  const activity=frame.icon===6?[0,1,2,3,4].map(i=>`<circle cx="${44+i*10}" cy="101" r="${n(2+1.1*Math.sin(frame.activity-i*.8))}" fill="currentColor" stroke="none"/>`).join(''):'';
  const icon=`<g transform="translate(64 24) scale(${n(frame.attention)}) translate(-64 ${n(-24+frame.notification)})" color="${p.accent}" opacity="${n(frame.iconAlpha)}" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round">${iconShape(frame.icon)}${activity}</g>`;
  const mute=muted?`<g stroke="${p.eye}" fill="none" stroke-width="1.5"><path d="M109 112h3l4-3v11l-4-3h-3zM119 112l5 5m0-5-5 5"/></g>`:'';
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 128 128" role="img" aria-label="Robot expression"><rect width="128" height="128" fill="${p.background}"/><g fill="${p.eye}">${eyes}</g>${mouth}${brows}${icon}${mute}</svg>`;
}
