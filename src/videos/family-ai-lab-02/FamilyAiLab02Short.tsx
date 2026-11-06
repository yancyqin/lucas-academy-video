import type {FC} from 'react';
import {AbsoluteFill,Img,OffthreadVideo,Sequence,staticFile,useCurrentFrame,useVideoConfig,type CalculateMetadataFunction} from 'remotion';

type Cue={id:string;visual:string;en:string;zh:string;from:number;duration:number;speechOffsetFrames:number;voiceSeconds:Record<string,number>};
type Shot={id:string;visual:string;from:number;duration:number;frames:number;src:string};
type ShortTimeline={aspect:'portrait'|'landscape';durationInFrames:number;lines:Cue[];storyClips:Shot[]};
type Facts={message:string;codes:Record<string,{bits:string}>;boxPath:{threshold:number;answer:boolean;remaining:number[]}[]};
export type ShortProps={tl:ShortTimeline|null;facts:Facts|null};
const asset=(s:string)=>staticFile('family-ai-lab-02/'+s),clamp=(x:number)=>Math.max(0,Math.min(1,x)),ease=(x:number)=>{const v=clamp(x);return v*v*(3-2*v);};
const gold='#ffc558',blue='#6bddff',white='#fff8e8',font="'Avenir Next','Arial',sans-serif";

export const calculateShortMetadata:CalculateMetadataFunction<ShortProps>=async({props,abortSignal})=>{
 const read=async(s:string)=>{const r=await fetch(asset(s),{signal:abortSignal});if(!r.ok)throw Error('Missing short input '+s);return r.json();};
 const [tl,facts]=await Promise.all([read('orbital-v2/short/timeline.json'),read('facts.json')]);
 return {fps:30,width:tl.aspect==='portrait'?1080:1920,height:tl.aspect==='portrait'?1920:1080,durationInFrames:tl.durationInFrames,props:{...props,tl,facts}};
};

function position(shot:Shot,frame:number,portrait:boolean){if(!portrait)return '50% 50%';const x=shot.visual==='paper'?88-66*ease((frame-shot.from)/(shot.duration*.55)):shot.visual==='code'?6+94*ease((frame-shot.from)/(shot.duration*.57)):shot.visual==='reply'?52:shot.visual==='cargo'?51:shot.visual==='snack'||shot.visual==='invite'?50:49;return `${x}% 50%`;}

function Crate({x,y,w,h,n,active,selected}:{x:number;y:number;w:number;h:number;n:number;active:boolean;selected:boolean}){return <g transform={`translate(${x} ${y})`} opacity={active?1:.17}>
 <ellipse cx={w*.5} cy={h} rx={w*.55} ry={18} fill="#0009"/>
 <path d={`M0 28L25 0H${w-25}L${w} 28V${h}H0Z`} fill="url(#short-metal)" stroke={selected?gold:'#718d9d'} strokeWidth={3}/>
 <path d={`M0 28H${w}M20 44V${h-15}M${w-20} 44V${h-15}`} stroke="#9cc6d2" strokeOpacity=".4" strokeWidth={5}/>
 <rect x={w*.28} y={h*.3} width={w*.44} height={h*.5} rx={9} fill="#051622" stroke={selected?gold:blue} strokeWidth={2}/>
 <text x={w*.5} y={h*.68} fontSize={h*.39} fontWeight={800} textAnchor="middle" fill={selected?gold:white}>{n}</text>
 {selected&&<path d={`M20 33H${w-20}`} stroke={gold} strokeWidth={10}/>}
 </g>;}

export const FamilyAiLab02Short:FC<ShortProps>=({tl,facts})=>{
 const frame=useCurrentFrame(),{width:W,height:H}=useVideoConfig();if(!tl||!facts)return null;
 const cue=tl.lines.find(r=>frame>=r.from&&frame<r.from+r.duration)??tl.lines.at(-1)!,local=frame-cue.from,portrait=H>W;
 const shot=tl.storyClips.find(s=>frame>=s.from&&frame<s.from+s.duration),v=cue.visual;
 const arrival=Math.min(32,Math.floor(clamp(local/36)*32));
 const question=Math.min(3,Math.floor(clamp(local/Math.max(1,cue.duration-12))*4)),part=local/Math.max(1,cue.duration-12)*4-question,step=facts.boxPath[question],answered=part>.3;
 const remaining=answered?step.remaining:question?facts.boxPath[question-1].remaining:Array.from({length:10},(_,i)=>i+1);
 const replyProgress=clamp((local-72)/27);
 return <AbsoluteFill style={{background:'#030c14',fontFamily:font,overflow:'hidden'}}>
  {shot?<Sequence from={shot.from} durationInFrames={shot.duration} layout="none"><OffthreadVideo src={asset(shot.src)} muted style={{position:'absolute',width:'100%',height:'100%',objectFit:'cover',objectPosition:position(shot,frame,portrait)}}/></Sequence>:<Img src={asset(`orbital-v2/art/${v==='questions'||v==='snack'?'cargo-bay':'signal-conduit'}.png`)} style={{width:'100%',height:'100%',objectFit:'cover'}}/>}
  <AbsoluteFill style={{background:'linear-gradient(180deg,#02091422,transparent 30%,transparent 75%,#02091433)'}}/>
  <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position:'absolute',inset:0,fontFamily:font,fontWeight:750}}>
   <defs><linearGradient id="short-metal" x2="0.3" y2="1"><stop stopColor="#708895"/><stop offset=".5" stopColor="#2c4353"/><stop offset="1" stopColor="#102331"/></linearGradient><radialGradient id="short-gold" cx="30%" cy="25%"><stop stopColor="#fff5b5"/><stop offset="1" stopColor="#d8810d"/></radialGradient></defs>
   {v==='code'&&<>{[0,1].map((b,i)=><g key={b} transform={`translate(${W*(.28+i*.44)} ${H*.77})`}><circle r={portrait?88:72} fill="#061827e6" stroke={b?gold:blue} strokeWidth={4}/><text y={portrait?31:27} fontSize={portrait?96:80} fill={b?gold:blue} textAnchor="middle">{b}</text></g>)}</>}
   {v==='arrival'&&facts.message.split('').map((letter,i)=>{const w=portrait?220:260,x=(W-w*4-36*3)/2+i*(w+36),y=H*.76;return <g key={letter}><rect x={x} y={y} width={w} height={portrait?200:180} rx={16} fill="#04131de3" stroke={arrival>=8*(i+1)?gold:blue} strokeWidth={2}/><text x={x+w/2} y={y+105} textAnchor="middle" fontSize={92} fill={arrival>=8*(i+1)?white:'#47738a'}>{arrival>=8*(i+1)?letter:'·'}</text><text x={x+w/2} y={y+155} textAnchor="middle" fontFamily="Menlo,monospace" fontSize={portrait?24:29} fill={blue}>{facts.codes[letter].bits}</text></g>;})}
   {v==='questions'&&<><rect width={W} height={H} fill="#020b1466"/><text x={W*.5} y={portrait?155:130} textAnchor="middle" fontSize={portrait?76:70} fill={white}>4 questions</text><text x={W*.5} y={portrait?285:245} textAnchor="middle" fontSize={portrait?72:64} fill={step.answer?gold:blue}>{`Above ${step.threshold}?  ${answered?(step.answer?'YES':'NO'):'…'}`}</text>
    {Array.from({length:10},(_,i)=>{const cols=portrait?2:5,w=portrait?300:250,h=portrait?165:185,x=portrait?180+(i%2)*420:230+(i%5)*290,y=portrait?420+Math.floor(i/2)*240:350+Math.floor(i/5)*285;return <Crate key={i} x={x} y={y} w={w} h={h} n={i+1} active={remaining.includes(i+1)} selected={question===3&&answered&&i===6}/>;})}
    <text x={W*.5} y={H-120} textAnchor="middle" fontSize={portrait?52:40} fill={gold}>{question===3&&answered?'Box 7':`${question+1} / 4`}</text></>}
   {v==='snack'&&!shot&&<Crate x={W/2-180} y={H*.4} w={360} h={250} n={7} active selected/>}
   {v==='reply'&&local>=72&&<><path d={`M${W*.08} ${H*.82}H${W*.92}`} stroke={blue} strokeOpacity=".45" strokeWidth={3}/>{replyProgress<.98?<circle cx={W*(.86-.72*replyProgress)} cy={H*.82} r={portrait?48:38} fill="url(#short-gold)" stroke={gold} strokeWidth={3}/>:<text x={W/2} y={H*.82-28} textAnchor="middle" fontSize={portrait?76:66} fill={white} stroke="#05131b" strokeWidth={3} paintOrder="stroke">Got it!</text>}</>}
   {v==='invite'&&<text x={portrait?75:110} y={portrait?180:200} fontSize={portrait?65:74} fill={white} stroke="#04111d" strokeWidth={2} paintOrder="stroke"><tspan>What would</tspan><tspan x={portrait?75:110} dy={portrait?90:100}>you send?</tspan></text>}
  </svg>
  {v==='invite'&&<div style={{position:'absolute',right:portrait?40:100,top:portrait?100:100,width:portrait?250:260,padding:15,background:'#fbffff',border:'2px solid #7be8ff',borderRadius:12,textAlign:'center',boxShadow:'0 0 30px #62dfff44'}}><Img src={asset('qr.png')} style={{width:'100%',display:'block'}}/><div style={{color:'#132d3b',fontSize:portrait?25:24,fontWeight:800,marginTop:8}}>Lucas Academy</div></div>}
 </AbsoluteFill>;
};
