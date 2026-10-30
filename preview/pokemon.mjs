// Vector faces for the 128px expression preview; no downloaded wallpaper assets.
export const pokemonThemes=Object.freeze([
 {id:'pikachu',name:'Pikachu',bg:'#ffda32',iris:'#272526',cheeks:true},
 {id:'charmander',name:'Charmander',bg:'#fa8c28',iris:'#237e9c',fangs:true,nostrils:true},
 {id:'squirtle',name:'Squirtle',bg:'#83bdcf',iris:'#a43965',nostrils:true},
 {id:'bulbasaur',name:'Bulbasaur',bg:'#82c6a6',iris:'#ac3453',fangs:true,spots:true},
 {id:'eevee',name:'Eevee',bg:'#ad743e',iris:'#593e31',fluff:true},
 {id:'psyduck',name:'Psyduck',bg:'#f7cc39',iris:'#171f25',bill:true},
 {id:'jigglypuff',name:'Jigglypuff',bg:'#f5bed6',iris:'#258aa8',curl:true},
 {id:'snorlax',name:'Snorlax',bg:'#217b7d',iris:'#3c3432',sleepy:true,fangs:true}
]);
const themes=new Map(pokemonThemes.map(t=>[t.id,t]));
const states=new Set(['idle','working','needs_input','finished','error','paused','disconnected']);
const n=x=>Number(x.toFixed(3));
export function pokemonFrame(state,time,{reduced=false}={}){
 if(!states.has(state))throw new RangeError('Unknown Pokemon expression');
 const t=reduced?0:Math.max(0,time),phase=t/1000;
 const blinkPhase=t%4300;
 const blink=reduced?1:blinkPhase<4000?1:Math.max(.06,Math.abs(blinkPhase-4150)/150);
 return {state,gaze:reduced?0:state==='working'?3.2*Math.sin(phase*1.8):1.1*Math.sin(phase*.65),
  bob:reduced?0:(state==='finished'?1.5:.7)*Math.sin(phase*(state==='working'?2.2:1.5)),
  blink:state==='needs_input'?1:blink,question:reduced?0:1.5*Math.sin(phase*3),
  phase,wide:state==='needs_input'?1.14:state==='paused'?.55:1};
}
function ornaments(t){
 return (t.cheeks?'<circle cx="20" cy="79" r="9" fill="#ed4c49"/><circle cx="108" cy="79" r="9" fill="#ed4c49"/>':'')+
 (t.spots?'<g fill="#388d76"><path d="m57 14 15 2-7 14zM44 27l9 3-5 8zM78 28l7 7-12 1z"/></g>':'')+
 (t.fluff?'<path d="M0 108 18 104l8 9 13-7 12 12 13-6 14 6 12-12 13 7 8-9 17 4v20H0" fill="#f2daa9"/>':'')+
 (t.curl?'<path d="M58 23c-20-15 21-25 17-7-3 11-21 5-11-3" fill="none" stroke="#d68db7" stroke-width="3" stroke-linecap="round"/>':'')+
 (t.sleepy?'<path d="M0 43 19 29 43 38Q64 44 85 38L109 29 128 43V128H0Z" fill="#f5e5bc"/>':'');
}
function mouthPath(t,state){
 const open=state==='finished'||state==='needs_input';
 let path=state==='error'?'M49 95Q64 87 79 95':state==='disconnected'?'M54 94H74':open?'M43 87Q64 96 85 87Q81 111 64 112Q47 109 43 87Z':t.cheeks?'M51 90q6 7 13 0q7 7 13 0':'M43 91Q64 105 85 91';
 if(t.bill)path=state==='needs_input'?'M56 94Q64 89 72 94':'M48 92Q64 97 80 92';
 return path;
}
export function pokemonSvg(id,state='idle',time=0,options={}){
 const t=themes.get(id);if(!t)throw new RangeError('Unknown Pokemon theme');
 if(!states.has(state))throw new RangeError('Unknown Pokemon expression');
 const eye=(x,i)=>`<g data-eye="${i}" transform="translate(${x} 61)">${t.bill?'<ellipse rx="14" ry="15" fill="#fff9e9" stroke="#413c31" stroke-width="1.3"/><circle data-pupil r="2.7" fill="#171f25"/>':t.sleepy?'<path d="M-12 0Q0-4 12 0" fill="none" stroke="#483c34" stroke-width="2.5" stroke-linecap="round"/>':`<ellipse rx="${t.cheeks?8:12}" ry="${t.cheeks?10:18}" fill="#fffbed" stroke="#353436" stroke-width="1"/><g data-pupil><ellipse cy="3" rx="${t.cheeks?7:9}" ry="${t.cheeks?8:14}" fill="${t.iris}"/><ellipse cy="0" rx="${t.cheeks?6:8}" ry="${t.cheeks?8:12}" fill="#20232b"/><ellipse cx="-3" cy="-8" rx="3.5" ry="5.5" fill="white"/><circle cx="4" cy="8" r="1.8" fill="white" opacity=".65"/></g>`}<path data-happy d="M-11 2Q0-12 11 2" fill="none" stroke="#383031" stroke-width="2.8" stroke-linecap="round" visibility="hidden"/></g>`;
 const result=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="${t.name} ${state}"><rect width="128" height="128" fill="${t.bg}"/><g data-head>${ornaments(t)}${eye(39,0)}${eye(89,1)}<g data-brows fill="none" stroke="#4c3837" stroke-width="2" stroke-linecap="round" visibility="hidden"><path d="m26 36 22 7m32 0 22-7"/></g>${t.bill?'<path d="M40 78Q64 68 88 78L96 91Q64 106 32 91Z" fill="#f6e4a0" stroke="#544b32" stroke-width="1.5"/><path d="m57 80 2 2m10-2-2 2" stroke="#544b32" stroke-width="1.5"/>':t.nostrils?'<g fill="#61413b"><ellipse cx="60" cy="78" rx="1" ry=".7"/><ellipse cx="68" cy="78" rx="1" ry=".7"/></g>':'<path d="m61 77 3 2 3-2z" fill="#383031"/>'}<path data-mouth d="${mouthPath(t,state)}" fill="${(state==='finished'||state==='needs_input')&&!t.bill?'#79334f':'none'}" stroke="#513a3b" stroke-width="1.5" stroke-linecap="round"/><path data-tongue fill="#ee8c9c"/><g data-fangs fill="#fff9e8" visibility="hidden"><path d="m43 88 3 6 3-6m30 0 3 6 3-6"/></g></g><g data-question fill="#343e49" font-family="Arial,sans-serif" font-weight="bold" font-size="21" text-anchor="middle" visibility="hidden"><text x="64" y="22">?</text></g><g data-work fill="#323b43" visibility="hidden">${[0,1,2].map(i=>`<circle data-dot="${i}" cx="${54+i*10}" cy="115" r="2"/>`).join('')}</g><g data-sleep fill="#42444b" font-family="Arial,sans-serif" font-size="12" visibility="hidden"><text x="96" y="23">zZ</text></g><g data-mute stroke="#343e49" stroke-width="1.4" visibility="hidden"><path d="m115 113 7 7m0-7-7 7"/></g></svg>`;
 return result;
}
export function renderPokemon(container,id,state,time,options={}){
 const t=themes.get(id);if(!t)throw new RangeError('Unknown Pokemon theme');
 if(container.dataset.pokemon!==id||!container.querySelector('[data-head]')){
  container.innerHTML=pokemonSvg(id,state,time,options);container.dataset.pokemon=id;
 }
 const f=pokemonFrame(state,time,options),q=s=>container.querySelector(s),visible=(s,on)=>q(s).setAttribute('visibility',on?'visible':'hidden');
 q('svg').setAttribute('aria-label',`${t.name}: ${state.replaceAll('_',' ')}`);
 q('[data-head]').setAttribute('transform',`translate(0 ${n(f.bob)})`);
 for(let i=0;i<2;i++){
  const e=q(`[data-eye="${i}"]`);e.setAttribute('transform',`translate(${39+i*50} 61) scale(1 ${n(f.blink*f.wide)})`);
  const p=e.querySelector('[data-pupil]');if(p)p.setAttribute('transform',`translate(${n(f.gaze)} 0)`);
 }
 const mouth=q('[data-mouth]');
 const open=state==='finished'||state==='needs_input';
 const path=mouthPath(t,state);
 mouth.setAttribute('d',path);mouth.setAttribute('fill',open&&!t.bill?'#79334f':'none');
 q('[data-tongue]').setAttribute('d',open&&!t.bill?'M52 105Q64 98 77 105Q64 117 52 105Z':'');
 visible('[data-fangs]',t.fangs&&open);visible('[data-brows]',state==='error');
 visible('[data-question]',state==='needs_input');q('[data-question]').setAttribute('transform',`translate(0 ${n(f.question)})`);
 visible('[data-work]',state==='working');for(let i=0;i<3;i++)q(`[data-dot="${i}"]`).setAttribute('r',n(1.8+.8*Math.sin(f.phase*3-i)));
 visible('[data-sleep]',state==='paused');visible('[data-mute]',!!options.muted);
 // Happy closed eyes: retain DOM nodes so animation never rebuilds the SVG per frame.
 for(const e of container.querySelectorAll('[data-eye]')){
  for(const child of e.children)child.setAttribute('visibility',child.hasAttribute('data-happy')?(state==='finished'?'visible':'hidden'):(state==='finished'?'hidden':'visible'));
 }
}
