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

function position(shot:Shot,frame:number,portrait:boolean){if(!portrait)return '50% 50%';const x=shot.visual==='paper'?88-66*ease((frame-shot.from)/(shot.duration*.55)):shot.visual==='friends'?22:shot.visual==='world'?100:shot.visual==='code'?6+94*ease((frame-shot.from)/(shot.duration*.57)):shot.visual==='reply'?52:shot.visual==='cargo'?51:shot.visual==='snack'||shot.visual==='invite'||shot.visual==='online'?50:49;return `${x}% 50%`;}

function NetworkGlobe({x,y,r,frame}:{x:number;y:number;r:number;frame:number}){
 const nodes=[[-.72,-.23],[-.48,-.57],[-.15,-.72],[.25,-.62],[.65,-.35],[.78,.07],[.46,.46],[.08,.7],[-.35,.5],[-.7,.22],[.08,-.14],[-.12,.25]];
 const links=[[0,2],[1,3],[2,4],[3,5],[4,6],[5,7],[6,8],[7,9],[8,0],[9,1],[0,10],[3,10],[6,11],[9,11],[10,11]];
 return <g transform={`translate(${x} ${y})`}>
  <defs><radialGradient id="short-earth"><stop stopColor="#123a54"/><stop offset=".72" stopColor="#071e35"/><stop offset="1" stopColor="#020d1d"/></radialGradient><clipPath id="short-globe-clip"><circle r={r}/></clipPath></defs>
  <circle r={r+9} fill="#082c4077" stroke={blue} strokeOpacity=".3" strokeWidth={2}/><circle r={r} fill="url(#short-earth)" stroke={blue} strokeWidth={3}/>
  <g clipPath="url(#short-globe-clip)">
   {[.2,.45,.7].map(n=><ellipse key={n} rx={r*n} ry={r} fill="none" stroke={blue} strokeOpacity=".25" strokeWidth={2} transform={`rotate(${Math.sin(frame/130)*10})`}/>)}
   {[-.6,-.3,0,.3,.6].map(n=><ellipse key={n} cy={r*n} rx={r*Math.sqrt(1-n*n)} ry={r*.13} fill="none" stroke={blue} strokeOpacity=".22" strokeWidth={2}/>)}
   {links.map(([a,b],i)=>{const A=nodes[a].map(v=>v*r),B=nodes[b].map(v=>v*r),C=[(A[0]+B[0])*.3,(A[1]+B[1])*.3],p=((frame/62+i*.17)%1+1)%1,X=(1-p)**2*A[0]+2*(1-p)*p*C[0]+p*p*B[0],Y=(1-p)**2*A[1]+2*(1-p)*p*C[1]+p*p*B[1],color=i%2?gold:blue;return <g key={i} opacity={ease((frame-i*2)/14)}><path d={`M${A[0]} ${A[1]}Q${C[0]} ${C[1]} ${B[0]} ${B[1]}`} fill="none" stroke={color} strokeOpacity=".65" strokeWidth={2}/><circle cx={X} cy={Y} r={4} fill={color}/>{i%3===0&&<text x={X+8} y={Y-6} fill={color} fontSize={r*.075} fontFamily="Menlo,monospace">{i%2}</text>}</g>;})}
   {nodes.map(([a,b],i)=><g key={i}><circle cx={a*r} cy={b*r} r={12} fill={i%2?gold:blue} opacity=".2"/><circle cx={a*r} cy={b*r} r={5} fill={white}/></g>)}
  </g>
 </g>;
}

function OnlineCards({W,H,frame}:{W:number;H:number;frame:number}){const portrait=H>W,w=portrait?270:330,h=portrait?235:220,gap=portrait?40:95,left=(W-3*w-2*gap)/2,y=H*.74;
 return <g>{['Video','Message','AI'].map((label,i)=>{const x=left+i*(w+gap),cx=x+w/2,cy=y+85;return <g key={label} opacity={ease((frame-i*6)/14)}>
  <rect x={x} y={y} width={w} height={h} rx={24} fill="#041723ed" stroke={i===2?gold:blue} strokeWidth={3}/>
  {i===0?<><rect x={cx-66} y={cy-42} width={132} height={86} rx={10} fill="none" stroke={blue} strokeWidth={4}/><path d={`M${cx-15} ${cy-23}L${cx+25} ${cy}L${cx-15} ${cy+23}Z`} fill={gold}/></>:i===1?<path d={`M${cx-65} ${cy-42}H${cx+65}V${cy+30}H${cx-25}L${cx-55} ${cy+54}V${cy+30}H${cx-65}Z`} fill="#0b3248" stroke={blue} strokeWidth={4}/>:<><path d={`M${cx-72} ${cy-48}H${cx+72}V${cy+39}H${cx-28}L${cx-57} ${cy+60}V${cy+39}H${cx-72}Z`} fill="#3b2e13" stroke={gold} strokeWidth={4}/><text x={cx} y={cy+17} textAnchor="middle" fill={gold} fontSize={58}>AI</text></>}
  <text x={cx} y={y+h-28} textAnchor="middle" fill={white} fontSize={portrait?38:36}>{label}</text>
 </g>;})}</g>;}

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
   {v==='friends'&&<><path d={`M${W*.25} ${H*.79}H${W*.75}`} stroke={blue} strokeWidth={4}/>{[0,1].map((n,i)=><g key={n} transform={`translate(${W*(.25+i*.5)} ${H*.79})`}><circle r={portrait?84:70} fill="#061827e6" stroke={i?gold:blue} strokeWidth={3}/><circle cy={-20} r={23} fill={i?gold:blue}/><path d="M-42 42Q-40 -5 0 -3Q40 -5 42 42Z" fill={i?gold:blue}/></g>)}<circle cx={W*(.25+.5*clamp(local/Math.max(1,cue.duration-12)))} cy={H*.79} r={11} fill={gold}/></>}
   {v==='world'&&<><rect width={W} height={H} fill="#020b1444"/><text x={W/2} y={H*.16} textAnchor="middle" fontSize={portrait?84:76} fill={white} stroke="#04111d" strokeWidth={3} paintOrder="stroke">The internet</text><NetworkGlobe x={W/2} y={H*.52} r={portrait?365:320} frame={local}/></>}
   {v==='online'&&<><text x={W/2} y={H*.13} textAnchor="middle" fontSize={portrait?72:70} fill={white} stroke="#04111d" strokeWidth={3} paintOrder="stroke">All connected</text><NetworkGlobe x={portrait?W*.8:W/2} y={H*.48} r={portrait?172:190} frame={local}/><OnlineCards W={W} H={H} frame={local}/></>}
   {v==='invite'&&<text x={portrait?75:110} y={portrait?180:200} fontSize={portrait?65:74} fill={white} stroke="#04111d" strokeWidth={2} paintOrder="stroke"><tspan>What will you</tspan><tspan x={portrait?75:110} dy={portrait?90:100}>share today?</tspan></text>}
  </svg>
  {v==='invite'&&<div style={{position:'absolute',right:portrait?40:100,top:portrait?100:100,width:portrait?250:260,padding:15,background:'#fbffff',border:'2px solid #7be8ff',borderRadius:12,textAlign:'center',boxShadow:'0 0 30px #62dfff44'}}><Img src={asset('qr.png')} style={{width:'100%',display:'block'}}/><div style={{color:'#132d3b',fontSize:portrait?25:24,fontWeight:800,marginTop:8}}>Lucas Academy</div></div>}
 </AbsoluteFill>;
};
