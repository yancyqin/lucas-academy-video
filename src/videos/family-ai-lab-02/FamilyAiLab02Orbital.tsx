import type {FC, ReactNode} from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame, type CalculateMetadataFunction} from 'remotion';
import type {Family02Props} from './FamilyAiLab02';

type Timeline=NonNullable<Family02Props['tl']>;
type Cue=Timeline['lines'][number];
type Facts=NonNullable<Family02Props['facts']>;
export type OrbitalProps=Family02Props & {view?:'study'|'full'};
const P={white:'#e9faff',muted:'#9fc3ce',cyan:'#68ddff',gold:'#ffbd55',glass:'#05131fe8',edge:'#39728b',steel:'#253745'};
const FONT="'Avenir Next','Arial',sans-serif",MONO="'SFMono-Regular','Menlo',monospace";
const f=(n:string)=>staticFile('family-ai-lab-02/'+n);
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const ease=(n:number)=>{const p=clamp(n);return p*p*(3-2*p);};

export const calculateOrbitalMetadata:CalculateMetadataFunction<OrbitalProps>=async({props,abortSignal})=>{
 const read=async(n:string)=>{const r=await fetch(f(n),{signal:abortSignal});if(!r.ok)throw Error('Missing orbital input '+n);return r.json();};
 const [source,facts,capture]=await Promise.all([read('timeline.json'),read('facts.json'),read('capture.json')]);
 let tl=source as Timeline;
 if(props.view!=='full'){
  let from=0;
  const selected:[string,number][]=[['byte',150],['letter-a',150],['send-play',210],['guess-4',150],['tree-four',150],['fruit-seeds',150],['lab',180],['worksheet',120]];
  const lines=selected.map(([visual,duration])=>{const original=tl.lines.find(l=>l.visual===visual);if(!original)throw Error('Missing study cue '+visual);const row={...original,from,duration};from+=duration;return row;});
  tl={...tl,narrated:false,lines,durationInFrames:from};
 }
 return {durationInFrames:tl.durationInFrames,fps:30,props:{...props,view:props.view??'study',tl,facts,captureFrames:capture.frames}};
};

const T:FC<{x:number;y:number;size?:number;fill?:string;anchor?:'start'|'middle'|'end';mono?:boolean;children:ReactNode;opacity?:number}>=({x,y,size=36,fill=P.white,anchor='start',mono=false,children,opacity=1})=><text x={x} y={y} fontSize={size} fontFamily={mono?MONO:FONT} fontWeight={650} textAnchor={anchor} fill={fill} opacity={opacity}>{children}</text>;
function Defs(){return <defs>
 <radialGradient id="o-gold" cx="32%" cy="25%"><stop stopColor="#fff9c6"/><stop offset=".3" stopColor="#ffd273"/><stop offset=".75" stopColor="#f59022"/><stop offset="1" stopColor="#8f4d12"/></radialGradient>
 <radialGradient id="o-blue" cx="32%" cy="25%"><stop stopColor="#e5ffff"/><stop offset=".3" stopColor="#91f5ff"/><stop offset=".75" stopColor="#24a8d9"/><stop offset="1" stopColor="#154268"/></radialGradient>
 <linearGradient id="o-metal" x2=".6" y2="1"><stop stopColor="#667c8c"/><stop offset=".45" stopColor="#2b3e4c"/><stop offset="1" stopColor="#142431"/></linearGradient>
 <linearGradient id="o-beam" x2="0" y2="1"><stop stopColor={P.cyan} stopOpacity="0"/><stop offset="1" stopColor={P.cyan} stopOpacity=".16"/></linearGradient>
 <filter id="o-glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="10"/></filter>
 </defs>;}
function Pane({x,y,w,h,children}:{x:number;y:number;w:number;h:number;children?:ReactNode}){return <g>
 <path d={`M${x+18} ${y}H${x+w-18}L${x+w} ${y+18}V${y+h-18}L${x+w-18} ${y+h}H${x+18}L${x} ${y+h-18}V${y+18}Z`} fill={P.glass} stroke={P.edge} strokeWidth={2}/>
 <path d={`M${x+20} ${y}H${x+95}M${x+w-95} ${y+h}H${x+w-20}`} stroke={P.cyan} strokeWidth={4}/>{children}
 </g>;}
function Signal({x,y,b,r=40,label=true,frame=0}:{x:number;y:number;b:number;r?:number;label?:boolean;frame?:number}){const c=b?P.gold:P.cyan;return <g>
 <circle cx={x} cy={y} r={r*1.13} fill={c} opacity={.18+.04*Math.sin(frame/13)} filter="url(#o-glow)"/>
 <circle cx={x} cy={y} r={r} fill={`url(#o-${b?'gold':'blue'})`} stroke={c} strokeWidth={2}/>
 <ellipse cx={x-r*.2} cy={y-r*.38} rx={r*.32} ry={r*.1} fill="white" opacity=".7"/>
 {label&&<T x={x} y={y+r*.35} size={r*1.03} fill="#09222e" anchor="middle" mono>{b}</T>}
 </g>;}
function Slot({x,y,b,frame,active=true}:{x:number;y:number;b:number;frame:number;active?:boolean}){return <g>
 <ellipse cx={x} cy={y+82} rx={69} ry={15} fill="#000a"/>
 <path d={`M${x-67} ${y+59}L${x-44} ${y+42}H${x+45}L${x+67} ${y+59}V${y+82}H${x-67}Z`} fill="url(#o-metal)" stroke={P.edge} strokeWidth={2}/>
 <ellipse cx={x} cy={y+55} rx={49} ry={10} fill="none" stroke={active?(b?P.gold:P.cyan):P.edge} strokeWidth={3}/>
 {active?<Signal x={x} y={y} b={b} r={44} frame={frame}/>:<circle cx={x} cy={y} r={44} fill="none" stroke={P.edge} strokeDasharray="4 8"/>}
 </g>;}
function Title({name,note}:{name:string;note?:string}){return <><T x={140} y={160} size={66}>{name}</T>{note&&<T x={144} y={216} size={29} fill={P.muted}>{note}</T>}</>;}
function Platform(){return <><path d="M220 820L550 330H1370L1700 820Z" fill="url(#o-beam)"/><ellipse cx={960} cy={820} rx={740} ry={42} fill="#041624bb" stroke={P.edge} strokeWidth={2}/><ellipse cx={960} cy={820} rx={665} ry={20} fill="none" stroke={P.cyan} strokeOpacity=".35"/></>;}

function Bits({cue,local,frame}:{cue:Cue;local:number;frame:number}){const v=cue.visual;return <>
 <Title name={v==='one-bit'?'Two signals.':v==='two-bits'?'Four patterns.':v==='bit-name'?'One place. One bit.':'8 bits = 1 byte'} note={v==='byte'?'256 possible patterns':undefined}/><Platform/>
 {v==='one-bit'?[0,1].map((b,i)=><g key={b}><Slot x={620+i*680} y={550} b={b} frame={frame}/><T x={620+i*680} y={747} size={45} anchor="middle">{b?'YES':'NO'}</T></g>):v==='two-bits'?['00','01','10','11'].map((s,i)=><g key={s} opacity={ease((local-i*10)/22)}>{s.split('').map((b,j)=><Signal key={j} x={380+i*405+j*120} y={520} b={Number(b)} r={43} frame={frame}/>)}<T x={440+i*405} y={700} anchor="middle" mono size={44}>{s}</T></g>):<>
  {'01000001'.split('').map((b,i)=><g key={i} opacity={ease((local-i*5)/20)}><Slot x={330+i*180} y={500} b={Number(b)} frame={frame}/></g>)}
  <path d="M260 675V705H1660V675" fill="none" stroke={P.cyan} strokeWidth={3}/><T x={960} y={773} anchor="middle" size={48}>{v==='byte'?'1 byte':'8 bits together'}</T>
 </>}
 </>;}
function Codes({cue,local,frame,facts}:{cue:Cue;local:number;frame:number;facts:Facts}){
 const v=cue.visual,arr=facts.codes.A.bits.split('').map(Number),progress=clamp(local/Math.max(1,cue.duration-30)),count=Math.min(8,Math.floor(progress*9));
 if(v==='codebooks')return <><Title name="The same code." note="Agree before the game."/>{[230,1040].map((x,j)=><Pane key={x} x={x} y={295} w={650} h={510}><T x={x+45} y={360} size={34} fill={j?P.cyan:P.gold}>{j?'Leo':'Mia'} · ASCII</T>{['A','L','P','Y'].map((s,i)=><g key={s}><T x={x+50} y={445+i*95} size={47}>{s}</T><T x={x+170} y={445+i*95} size={32} mono>{facts.codes[s].number}</T><T x={x+298} y={445+i*95} size={32} mono fill={P.cyan}>{facts.codes[s].bits}</T></g>)}</Pane>)}</>;
 return <><Title name={v==='weights'?'Each place doubles.':v==='padding'?'Wait for all 8.':v==='ascii'?'A shared code: ASCII':'64 + 1 = 65 → A'} note={v==='ascii'?'Seven-bit ASCII, with a leading 0 here.':v==='padding'?'Leading zeros travel too.':undefined}/><Platform/>
 {facts.weights.map((w,i)=><g key={w}><T x={330+i*180} y={369} anchor="middle" size={39} fill={arr[i]?P.gold:P.muted} mono>{w}</T><Slot x={330+i*180} y={520} b={v==='weights'?(i===7-Math.min(7,Math.floor(progress*8))?1:0):arr[i]} frame={frame} active={v!=='padding'||i<count}/>{arr[i]===1&&v!=='weights'&&<path d={`M${282+i*180} 665H${378+i*180}`} stroke={P.gold} strokeWidth={4}/>}</g>)}
 <T x={960} y={773} anchor="middle" size={52} mono>{v==='padding'?`${count} / 8${count===8?'  →  A':''}`:v==='weights'?'1 → 2 → 4 → 8 → …':facts.codes.A.bits}</T>
 </>;
}

export function orbitalMessageState(cue:Cue,local:number,facts:Facts,study=false){
 const first=cue.visual==='send-p',complete=cue.visual==='received',all=facts.messageBits.split('').map(Number);
 const base=study?0:first?0:8,chunk=study?all:first?all.slice(0,8):all.slice(8),clock=clamp(local/Math.max(1,cue.duration-30))*(chunk.length+2);
 const delivered=complete?32:base+Math.max(0,Math.min(chunk.length,Math.floor(clock-2)+1));
 return {base,chunk,clock,delivered};
}
function Message({cue,local,frame,facts,study}:{cue:Cue;local:number;frame:number;facts:Facts;study:boolean}){const {chunk,clock,delivered}=orbitalMessageState(cue,local,facts,study);return <>
 <Title name={cue.visual==='received'?'Invitation received.':'Send the invitation.'} note="8 signals per letter"/>
 {cue.visual!=='received'&&chunk.map((b,i)=>{const p=(clock-i)/2;return p>0&&p<1?<g key={i}><path d={`M${160+1600*p-70} 630H${160+1600*p}`} stroke={b?P.gold:P.cyan} strokeWidth={5} opacity=".6"/><Signal x={160+1600*p} y={630} b={b} r={34} frame={frame}/></g>:null;})}
 {facts.message.split('').map((letter,i)=><Pane key={i} x={530+i*225} y={780} w={195} h={165}><T x={628+i*225} y={868} size={70} anchor="middle" fill={delivered>=8*(i+1)?P.white:P.edge}>{delivered>=8*(i+1)?letter:'·'}</T><T x={628+i*225} y={918} size={23} mono anchor="middle" fill={delivered>=8*(i+1)?P.cyan:P.edge}>{facts.codes[letter].bits}</T></Pane>)}
 <T x={1720} y={332} anchor="end" size={37} mono fill={P.cyan}>{delivered} / 32</T>
 </>;}
function Crate({x,y,n,active,chosen,local}:{x:number;y:number;n:number;active:boolean;chosen:boolean;local:number}){const lift=chosen?ease(local/24):0;return <g transform={`translate(${x} ${y})`} opacity={active?1:.17}>
 <ellipse cx={111} cy={179} rx={122} ry={20} fill="#000a"/>
 <path d="M0 35L32 5H201L225 35V166H0Z" fill="url(#o-metal)" stroke="#648399" strokeWidth={2}/><path d="M17 59V149M206 59V149" stroke="#a2b3bb" strokeWidth={6} opacity=".5"/>
 {chosen&&<rect x={15} y={23} width={195} height={25} fill={P.gold} opacity={lift}/>}
 <g transform={`translate(0 ${-44*lift}) rotate(${-5*lift} 112 24)`}><path d="M0 35L32 5H201L225 35L206 51H17Z" fill="#8396a1" stroke="#a0c1d0" strokeWidth={2}/><path d="M30 25H195" stroke="#142c38" strokeWidth={5}/></g>
 <rect x={76} y={66} width={75} height={69} rx={5} fill="#081824" stroke={chosen?P.gold:P.edge} strokeWidth={2}/><T x={114} y={119} size={43} mono anchor="middle" fill={chosen?P.gold:P.white}>{n}</T>
 <path d="M52 149H173" stroke={chosen?P.gold:P.cyan} strokeWidth={4}/><circle cx={34} cy={68} r={4} fill={P.muted}/><circle cx={191} cy={68} r={4} fill={P.muted}/>
 </g>;}
function Guess({cue,local,frame,facts}:{cue:Cue;local:number;frame:number;facts:Facts}){const index=cue.visual.startsWith('guess-')?Number(cue.visual.slice(6))-1:-1,answered=local>cue.duration*.42,step=index>=0?facts.boxPath[index]:null;
 const all=Array.from({length:10},(_,i)=>i+1),before=index>0?facts.boxPath[index-1].remaining:all,remaining=step?(answered?step.remaining:before):all;
 return <><Title name={step?`Greater than ${step.threshold}?`:cue.visual==='bad-question'?'Box 1? Box 2?':cue.visual==='questions-rule'?'Agree on the questions.':'Find the hidden gift.'} note={step?`${remaining.length} ${remaining.length===1?'box':'boxes'} left`:'One gift. Ten boxes.'}/>
 {step&&<g><Signal x={1530} y={182} b={step.answer?1:0} r={34} frame={frame}/><T x={1605} y={198} size={39} fill={step.answer?P.gold:P.cyan}>{answered?(step.answer?'YES':'NO'):'…'}</T><T x={1760} y={253} size={26} anchor="end" fill={P.muted}>{index+1} / 4</T></g>}
 {all.map((n,i)=><Crate key={n} x={248+i%5*300} y={390+Math.floor(i/5)*300} n={n} active={remaining.includes(n)} chosen={index===3&&answered&&n===7} local={Math.max(0,local-cue.duration*.42)}/>)}
 </>;
}
function Counts({cue,local}:{cue:Cue;local:number}){const thousand=cue.visual==='thousand',levels=cue.visual==='tree-three'?3:4;if(thousand){const step=Math.min(10,Math.floor(local/Math.max(1,cue.duration-25)*11)),remaining=Math.ceil(1000/2**step);return <>
 <Title name="1,000 possibilities." note="Keep splitting the remaining choices."/><Pane x={160} y={320} w={680} h={460}><T x={500} y={455} anchor="middle" size={70} mono>2¹⁰ = 1,024</T><T x={500} y={575} anchor="middle" size={52} fill={P.gold}>{remaining} left</T><T x={500} y={694} anchor="middle" size={32}>10 answers are enough.</T></Pane>
 {Array.from({length:1024},(_,i)=><circle key={i} cx={1000+i%32*21} cy={290+Math.floor(i/32)*20} r={5} fill={i<1000?P.gold:P.cyan} opacity={i<remaining?1:.1}/>)}
 </>;}
 return <><Title name={`${levels} answers. ${2**levels} outcomes.`} note={levels===3?'Ten boxes need more room.':'Ten boxes fit. Six patterns remain.'}/>
 {Array.from({length:levels+1},(_,level)=>Array.from({length:2**level},(_,j)=>{const count=2**level,x=180+1560*(j+.5)/count,y=300+level*(levels===3?150:125),leaf=level===levels,chosen=leaf&&j===6;return <g key={`${level}-${j}`} opacity={ease((local-level*12)/22)}>
  {!leaf&&[0,1].map(b=><path key={b} d={`M${x} ${y}L${180+1560*(j*2+b+.5)/(count*2)} ${y+(levels===3?150:125)}`} stroke={P.cyan} strokeOpacity=".4" strokeWidth={3}/>)}
  {leaf?<rect x={x-31} y={y-25} width={62} height={52} rx={8} fill={j<10?'#3c2c18':'#0a2735'} stroke={j<10?P.gold:P.edge} strokeWidth={chosen?4:2}/>:<circle cx={x} cy={y} r={18} fill="#0a293a" stroke={P.cyan} strokeWidth={2}/>}
  {leaf&&<T x={x} y={y+9} anchor="middle" size={24} mono fill={j<10?P.gold:P.muted}>{j+1}</T>}
 </g>;}))}
 <T x={960} y={947} anchor="middle" size={38} fill={P.muted}>{levels===3?'8 outcomes cannot cover 10 boxes.':'Suitable questions guarantee at most 4 answers.'}</T>
 </>;
}
const fruits=[{name:'Banana',file:'banana_3d',red:false,seeds:false},{name:'Apple',file:'red_apple_3d',red:true,seeds:false},{name:'Grapes',file:'grapes_3d',red:false,seeds:false},{name:'Watermelon',file:'watermelon_3d',red:true,seeds:true}];
function Fruit({cue,local}:{cue:Cue;local:number}){const filter=cue.visual==='fruit-red'?1:cue.visual==='fruit-seeds'?2:0,revealed=local>cue.duration*.38;return <>
 <Title name={filter===1?'Red in the picture?':filter===2?'Can you see seeds?':'Which snack?'} note="Choose questions that separate the pictures."/>
 {fruits.map((fruit,i)=>{const keep=filter===0||filter===1&&fruit.red||filter===2&&fruit.seeds,x=155+i*425;return <g key={fruit.name} opacity={!keep&&revealed?.16:1}>
  <Pane x={x} y={335} w={365} h={455}/><image href={f('curriculum/'+fruit.file+'.png')} x={x+25} y={370+Math.sin(local/24+i)*4} width={315} height={295} preserveAspectRatio="xMidYMid meet"/>
  <T x={x+183} y={738} anchor="middle" size={34} fill={keep&&revealed?P.gold:P.white}>{fruit.name}</T>
 </g>;})}
 {filter>0&&revealed&&<T x={960} y={925} anchor="middle" size={46} fill={P.gold}>YES</T>}
 </>;}

export const FamilyAiLab02Orbital:FC<OrbitalProps>=({tl,facts,captureFrames=180,view='study'})=>{
 const frame=useCurrentFrame();if(!tl||!facts)return null;
 const cue=tl.lines.find(l=>frame>=l.from&&frame<l.from+l.duration)??tl.lines.at(-1)!,local=frame-cue.from,v=cue.visual;
 const story=cue.scene===1||v==='received'||v==='picnic'||v==='invite',lab=v==='lab',worksheet=v==='worksheet';
 const art=cue.scene===1?'../../design-v2/01-orbital':v==='received'?'story-arrival':v==='picnic'||v==='invite'?'story-arrival':cue.scene===4?'signal-conduit':cue.scene===5||cue.scene===6?'cargo-bay':'lab-workbench';
 const src=cue.scene===1?f('design-v2/01-orbital.png'):f('orbital-v2/art/'+art+'.png');
 return <AbsoluteFill style={{background:'#020b12',fontFamily:FONT}}>
  <Img src={src} style={{position:'absolute',width:'100%',height:'100%',objectFit:'cover'}}/>
  <AbsoluteFill style={{background:story?'linear-gradient(180deg,#020a12aa,transparent 45%,#020a1233)':'linear-gradient(180deg,#020a12df,#020a1266 38%,#020a1226 75%,#020a1288)'}}/>
  <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{position:'absolute',inset:0}}><Defs/>
   {cue.scene===1&&<><T x={140} y={145} size={48}>Only 0 and 1.</T>{v==='rules'&&<Pane x={1200} y={290} w={560} h={320}><Signal x={1350} y={440} b={0} r={60} frame={frame}/><Signal x={1610} y={440} b={1} r={60} frame={frame}/></Pane>}</>}
   {cue.scene===2&&<Bits cue={cue} local={local} frame={frame}/>}
   {cue.scene===3&&<Codes cue={cue} local={local} frame={frame} facts={facts}/>}
   {cue.scene===4&&<Message cue={cue} local={local} frame={frame} facts={facts} study={view==='study'}/>}
   {cue.scene===5&&<Guess cue={cue} local={local} frame={frame} facts={facts}/>}
   {cue.scene===6&&<Counts cue={cue} local={local}/>}
   {cue.scene===7&&<Fruit cue={cue} local={local}/>}
   {lab&&<Title name="Try the real lab."/>}{worksheet&&<Title name="Send your own message."/>}
   {v==='lights'&&<><Title name="Two states. The same idea."/>{[0,1].map((b,i)=><g key={b}><Signal x={620+i*680} y={540} b={b} r={100} frame={frame}/><T x={620+i*680} y={770} anchor="middle" size={50}>{b?'ON = 1':'OFF = 0'}</T></g>)}</>}
   {v==='scope'&&<><Title name="A byte is not always a character."/><Pane x={230} y={345} w={650} h={410}><T x={555} y={510} anchor="middle" size={120}>A</T><T x={555} y={670} anchor="middle" size={35}>8 bits in this example</T></Pane><Pane x={1040} y={345} w={650} h={410}><T x={1365} y={510} anchor="middle" size={90}>文 字</T><T x={1365} y={670} anchor="middle" size={32}>Some encodings need more bytes.</T></Pane></>}
   {v==='invite'&&<Title name="What would you tell your friend?"/>}
   <T x={1820} y={1045} size={18} anchor="end" fill={P.muted}>{cue.scene===7?'AI artwork + animation · Lucas Academy | Fruit · Fluent Emoji (MIT)':lab?'Real browser capture · Lucas Academy':worksheet?'Original worksheet · Lucas Academy':'AI artwork + code animation · Lucas Academy'}</T>
  </svg>
  {lab&&<div style={{position:'absolute',left:135,top:285,width:1265,height:712,background:'#061620',border:'3px solid #68ddff66',borderRadius:12,overflow:'hidden',boxShadow:'0 0 45px #68ddff22'}}>
   <Sequence from={cue.from} durationInFrames={Math.min(captureFrames,cue.duration)} layout="none"><OffthreadVideo src={f('capture/lab.mp4')} muted style={{width:'100%',height:'100%',objectFit:'contain'}}/></Sequence>
   {local>=captureFrames&&<Img src={f('capture/lab-a.png')} style={{width:'100%',height:'100%',objectFit:'contain'}}/>}
  </div>}
  {worksheet&&<Img src={f('curriculum/worksheet-front.jpg')} style={{position:'absolute',left:210,top:270,width:1050,height:730,objectFit:'contain',filter:'drop-shadow(0 0 14px #68ddff44)'}}/>}
  {(lab||worksheet||v==='invite')&&<div style={{position:'absolute',right:125,top:405,width:310,background:'#f7fdff',border:'3px solid #68ddff',padding:22,boxSizing:'border-box',borderRadius:12,textAlign:'center',boxShadow:'0 0 40px #68ddff33'}}><Img src={f('qr.png')} style={{width:250,height:250}}/><div style={{fontSize:21,fontWeight:750,marginTop:14,color:'#102833'}}>ai.lucasacademy.org</div></div>}
 </AbsoluteFill>;
};
