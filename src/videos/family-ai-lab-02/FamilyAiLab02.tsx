import type {FC, ReactNode} from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame, type CalculateMetadataFunction} from 'remotion';

type Language='en'|'zh';
type Cue={id:string;scene:number;visual:string;zh:string;en:string;from:number;duration:number};
type Timeline={fps:number;durationInFrames:number;narrated:boolean;lines:Cue[];scenes:string[]};
type Facts={codes:Record<string,{number:number;bits:string}>;message:string;messageBits:string;weights:number[];boxPath:{threshold:number;answer:boolean;remaining:number[]}[]};
export type Family02Props={tl:Timeline|null;facts:Facts|null;captureFrames?:number};
const C={ink:'#173c3b',deep:'#154c48',teal:'#2d8a81',mint:'#a4d5ba',paper:'#fff4dc',sky:'#d3e9d7',gold:'#f6bd52',blue:'#83cdd2',coral:'#d8704a',wood:'#bc8255',line:'#31534b',muted:'#607a6a'};
const FONT="'Avenir Next', 'Arial', sans-serif";
const MONO="'SFMono-Regular', 'Menlo', monospace";
const file=(name:string)=>staticFile('family-ai-lab-02/'+name);
const clamp=(n:number)=>Math.min(1,Math.max(0,n));
const ease=(n:number)=>{const p=clamp(n);return p*p*(3-2*p);};
const lerp=(a:number,b:number,p:number)=>a+(b-a)*p;

export const calculateFamily02Metadata:CalculateMetadataFunction<Family02Props>=async({abortSignal})=>{
 const read=async(name:string)=>{const r=await fetch(file(name),{signal:abortSignal});if(!r.ok)throw Error('Missing Family 02 '+name);return r.json();};
 const [tl,facts,capture]=await Promise.all([read('timeline.json'),read('facts.json'),read('capture.json')]);
 return {durationInFrames:tl.durationInFrames,fps:tl.fps,props:{tl,facts,captureFrames:capture.frames}};
};

const Text:FC<{x:number;y:number;size?:number;fill?:string;anchor?:'middle'|'start'|'end';children:ReactNode;weight?:number;mono?:boolean;opacity?:number}>=({x,y,size=36,fill=C.ink,anchor='start',children,weight=650,mono=false,opacity=1})=><text x={x} y={y} fontSize={size} fontFamily={mono?MONO:FONT} fontWeight={weight} fill={fill} textAnchor={anchor} opacity={opacity}>{children}</text>;
const Card:FC<{x:number;y:number;w:number;h:number;fill?:string;children?:ReactNode}>=({x,y,w,h,fill=C.paper,children})=><g><rect x={x+2} y={y+11} width={w} height={h} rx={32} fill={C.ink} opacity={.12}/><rect x={x} y={y} width={w} height={h} rx={32} fill={fill} stroke={C.ink+'22'} strokeWidth={2}/>{children}</g>;
const Bead:FC<{x:number;y:number;value:number;r?:number;opacity?:number}>=({x,y,value,r=30,opacity=1})=><g opacity={opacity}><circle cx={x+1} cy={y+4} r={r} fill={C.ink} opacity={.15}/><circle cx={x} cy={y} r={r} fill={value?C.gold:C.blue} stroke={C.ink} strokeWidth={2.5}/><ellipse cx={x-r*.2} cy={y-r*.34} rx={r*.36} ry={r*.16} fill="white" opacity={.45}/><Text x={x} y={y+r*.38} size={r*1.12} mono anchor="middle">{value}</Text></g>;

function Character({x,y,frame,mia=false,scale=1,pose='happy'}:{x:number;y:number;frame:number;mia?:boolean;scale?:number;pose?:string}){
 const phase=frame+(mia?0:47),blink=phase%131<5,arm=pose==='wave'?-45+Math.sin(phase/6)*14:pose==='push'?-30+Math.sin(phase/9)*11:Math.sin(phase/18)*5;
 const hair='#3b3026',skin=mia?'#d8996c':'#a96f4e',shirt=mia?C.gold:C.blue;
 return <g transform={`translate(${x} ${y+Math.sin(phase/22)*2}) scale(${scale})`} stroke={C.ink} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
  <ellipse cx={0} cy={49} rx={70} ry={12} fill={C.ink} opacity={.13} stroke="none"/>
  <path d="M-31 -18 L-38 37 L-5 39 L1 -14 M12 -16 L17 40 L50 37 L45 -19" fill={C.deep}/>
  <path d="M-43 33 Q-76 31 -75 48 L-5 48 L-5 35 M16 34 L16 48 L80 48 Q80 31 46 32" fill={mia?C.coral:C.wood}/>
  <path d="M-50 -151 Q-70 -127 -65 -36 Q0 -4 65 -36 Q69 -123 48 -151 Z" fill={shirt}/>
  <path d="M-40 -108 L-41 -34 Q0 -16 44 -34 L40 -108 L25 -108 L25 -147 L6 -150 L6 -101 L-7 -101 L-7 -150 L-26 -148 L-25 -107 Z" fill={mia?C.coral:C.teal}/>
  <rect x={-19} y={-81} width={40} height={29} rx={7} fill={shirt} stroke="none"/>
  <g transform={`translate(-48 -137) rotate(${-arm*.3})`}><path d="M0 0 Q-49 16 -54 72" fill="none" stroke={shirt} strokeWidth={34}/><circle cx={-55} cy={73} r={17} fill={skin}/></g>
  <g transform={`translate(48 -137) rotate(${arm})`}><path d="M0 0 Q43 13 58 -20" fill="none" stroke={shirt} strokeWidth={34}/><circle cx={58} cy={-23} r={17} fill={skin}/><path d="M61 -26 L66 -40" stroke={skin} strokeWidth={10}/></g>
  <rect x={-17} y={-181} width={34} height={39} rx={12} fill={skin}/>
  {mia?<><circle cx={-61} cy={-260} r={31} fill={hair}/><circle cx={59} cy={-260} r={31} fill={hair}/><circle cx={-61} cy={-272} r={10} fill={C.coral} stroke="none"/></>:Array.from({length:7},(_,i)=><circle key={i} cx={-53+i*18} cy={-263-(i%3)*6} r={24} fill={hair}/>)}
  <ellipse cx={0} cy={-223} rx={67} ry={73} fill={skin}/>
  <circle cx={-66} cy={-215} r={13} fill={skin}/><circle cx={66} cy={-215} r={13} fill={skin}/>
  <path d={mia?'M-65 -239 Q-72 -299 -13 -299 Q60 -309 66 -239 Q32 -257 12 -278 Q-20 -244 -65 -239':'M-65 -251 Q-73 -303 -22 -295 Q38 -317 67 -254 Q26 -261 12 -278 Q-24 -253 -65 -251'} fill={hair}/>
  <path d="M-38 -236 Q-28 -242 -17 -237 M18 -237 Q28 -242 40 -236" fill="none" stroke={hair} strokeWidth={4}/>
  {blink?<path d="M-35 -220 L-20 -220 M21 -220 L36 -220" fill="none" strokeWidth={5}/>:<><ellipse cx={-27} cy={-219} rx={5} ry={8} fill={hair} stroke="none"/><ellipse cx={29} cy={-219} rx={5} ry={8} fill={hair} stroke="none"/></>}
  <circle cx={-43} cy={-202} r={11} fill={C.coral} opacity={.45} stroke="none"/><circle cx={45} cy={-202} r={11} fill={C.coral} opacity={.45} stroke="none"/>
  <path d="M3 -214 L-2 -201 L7 -199" fill="none" stroke={C.ink+'66'} strokeWidth={2}/>
  {pose==='think'?<path d="M-9 -183 Q5 -188 15 -182" fill="none" strokeWidth={3}/>:<path d="M-20 -187 Q1 -163 24 -187 Q3 -177 -20 -187" fill={C.paper} strokeWidth={2.5}/>}
 </g>;
}

function Forest({frame,night=false}:{frame:number;night?:boolean}){
 return <>
  <defs>
   <linearGradient id="sky" x2="0" y2="1"><stop stopColor={night?'#123f44':'#b7d9c7'}/><stop offset="1" stopColor={night?'#417c6d':'#f3edcd'}/></linearGradient>
   <linearGradient id="trunk" x2="1" y2="0"><stop stopColor="#765542"/><stop offset=".48" stopColor="#9b7251"/><stop offset="1" stopColor="#624f3b"/></linearGradient>
   <pattern id="paper-grain" width="33" height="31" patternUnits="userSpaceOnUse"><circle cx="5" cy="9" r="1" fill={C.deep} opacity=".055"/><path d="M19 21l4 -2" stroke={C.deep} opacity=".035"/></pattern>
  </defs>
  <rect width={1920} height={1080} fill="url(#sky)"/>
  <circle cx={1470} cy={180} r={95} fill={night?C.paper:'#fff6d1'} opacity={.75}/>
  {[[-80,160,1.2],[700,160,.9],[1720,330,.8]].map(([x,y,s],i)=><g key={i} transform={`translate(${x+Math.sin(frame/380+i)*24} ${y}) scale(${s})`} fill="#fff9e6" opacity={.48}><ellipse cx={0} cy={0} rx={130} ry={30}/><ellipse cx={-30} cy={-25} rx={50} ry={40}/><ellipse cx={45} cy={-15} rx={70} ry={35}/></g>)}
  <path d="M0 730 Q320 560 640 720 T1280 730 T1920 620 V1080 H0Z" fill="#9dc4a4" opacity={.6}/>
  <path d="M0 840 Q300 700 730 850 T1540 790 T1920 850 V1080 H0Z" fill="#7ca987" opacity={.58}/>
  {[80,690,1190,1860].map((x,i)=><g key={i} opacity={i%2?.15:.35}><path d={`M${x} 980 L${x+25} 20`} stroke="#447764" strokeWidth={40}/><ellipse cx={x} cy={160} rx={200} ry={240} fill="#67977b"/></g>)}
  {[75,1850].map((x,i)=><g key={i}><path d={`M${x-75} 1120 Q${x+2} 510 ${x-25} -40 L${x+45} -40 Q${x+140} 620 ${x+110} 1120 Z`} fill="url(#trunk)"/><path d={`M${x+22} 740 Q${x+65} 400 ${x+18} 70 M${x+57} 1010 Q${x+92} 630 ${x+55} 260`} stroke="#493e33" strokeWidth={5} fill="none" opacity={.3}/></g>)}
  <path d="M0 1000 Q550 920 1010 1010 T1920 970 V1080 H0Z" fill={C.deep}/>
  {Array.from({length:24},(_,i)=><g key={i} transform={`translate(${i*87-20} ${1045-(i%4)*12}) rotate(${Math.sin(frame/45+i)*4})`}><path d="M0 55 Q-23 -20 -49 -33 Q-10 -46 0 4 Q18 -45 43 -45 Q52 -9 0 15" fill={i%3?'#438b6a':'#649f74'}/>{i%4===0&&<circle cx={0} cy={-16} r={9} fill={C.gold}/>}</g>)}
  {Array.from({length:12},(_,i)=><circle key={i} cx={220+(i*149)%1480+Math.sin(frame/75+i)*20} cy={100+(i*177)%800+Math.cos(frame/90+i)*18} r={2.3+(i%2)} fill={C.paper} opacity={.15+.3*(1+Math.sin(frame/32+i))/2}/>)}
  <rect width={1920} height={1080} fill="url(#paper-grain)"/>
 </>;
}

function House({x,name,right=false}:{x:number;name:string;right?:boolean}){
 return <g transform={`translate(${x} 0)`} stroke={C.ink} strokeWidth={4} strokeLinejoin="round">
  <path d="M70 727 L50 976 M470 727 L490 977" stroke="#725c43" strokeWidth={22}/>
  <rect x={16} y={380} width={520} height={355} rx={12} fill={right?'#7baba0':'#d0a171'}/>
  {Array.from({length:7},(_,i)=><path key={i} d={`M23 ${414+i*46} H529`} stroke="#173c3b" strokeOpacity={.13} strokeWidth={2}/>)}
  <path d="M-26 386 L266 207 L575 386 Z" fill={right?C.deep:C.coral}/>
  <path d="M0 389 L268 231 L548 389" fill="none" stroke="#ffffff44" strokeWidth={9}/>
  <rect x={85} y={413} width={350} height={286} rx={24} fill={right?'#324e43':'#805b41'} strokeWidth={9}/>
  <path d="M105 437 Q268 420 413 437 V697 H105 Z" fill={C.paper} opacity={.16} stroke="none"/>
  <rect x={-4} y={710} width={565} height={39} rx={9} fill={right?'#bb9e6b':'#e0bb7c'}/>
  <rect x={183} y={764} width={178} height={59} rx={12} fill={C.paper}/><Text x={272} y={805} anchor="middle" size={31}>{name}</Text>
  <path d="M145 955 L145 753 M215 955 L215 753 M145 798 H215 M145 851 H215 M145 904 H215" fill="none" stroke="#a17d56" strokeWidth={10}/>
 </g>;
}

const pipePoint=(p:number)=>({x:lerp(620,1300,p),y:635+95*Math.sin(Math.PI*p)**2});
function Pipe({frame,values=[],progress=0,reverse=false}:{frame:number;values?:number[];progress?:number;reverse?:boolean}){
 return <g>
  <path d="M615 635 C810 635 805 730 960 730 S1140 635 1305 635" fill="none" stroke={C.ink} strokeWidth={79} strokeLinecap="round"/>
  <path d="M615 635 C810 635 805 730 960 730 S1140 635 1305 635" fill="none" stroke="#8cbcab" strokeWidth={64} strokeLinecap="round"/>
  <path d="M615 617 C810 617 805 712 960 712 S1140 617 1305 617" fill="none" stroke="#e2f6cf" strokeWidth={5} strokeLinecap="round" opacity={.5}/>
  {[620,1300].map(x=><g key={x}><rect x={x-17} y={581} width={34} height={109} rx={9} fill={C.wood} stroke={C.ink} strokeWidth={3}/><circle cx={x} cy={593} r={4} fill={C.paper}/><circle cx={x} cy={678} r={4} fill={C.paper}/></g>)}
  {values.map((value,i)=>{let p=(progress*1.8-i*.11);if(p<0||p>1)return null;if(reverse)p=1-p;const q=pipePoint(p);return <Bead key={i} x={q.x} y={q.y} value={value} r={23}/>;})}
  <path d="M944 781 L972 781 M965 774 L974 781 L965 788" stroke={C.deep} strokeWidth={3} fill="none" opacity={.55+.2*Math.sin(frame/20)}/>
 </g>;
}

function World({frame,cue,local,children}:{frame:number;cue:Cue;local:number;children?:ReactNode}){
 const card=['card','challenge'].includes(cue.visual),picnic=cue.visual==='picnic',p=clamp(local/cue.duration);
 const zoom=cue.visual==='card'?1.22:1+Math.sin(p*Math.PI)*.025;
 return <g transform={`translate(${960-960*zoom} ${540-540*zoom}) scale(${zoom})`}>
  <House x={65} name="Mia"/><House x={1293} name="Leo" right/>
  <Character x={345} y={688} frame={frame} mia scale={.82} pose={cue.visual==='world'?'wave':picnic?'happy':'push'}/>
  <Character x={1569} y={688} frame={frame} scale={.82} pose={picnic?'wave':cue.visual==='challenge'?'think':'happy'}/>
  {card&&<g transform={`translate(${440+(cue.visual==='card'?120*ease(local/45):0)+Math.sin(local/5)*4} ${490+(cue.visual==='card'?130*ease(local/45):0)+Math.sin(local/11)*3}) rotate(${-10+Math.sin(local/8)*5})`}><rect x={-70} y={-44} width={140} height={91} rx={8} fill={C.paper} stroke={C.ink} strokeWidth={3}/><Text x={0} y={9} size={36} anchor="middle">PLAY</Text></g>}
  {cue.visual==='card'&&local>50&&<Text x={960} y={480} anchor="middle" size={43} fill={C.deep}>It will not fit!</Text>}
  <Pipe frame={frame} values={cue.visual==='rules'?[0,1]:picnic?[1]:[]} progress={(local%90)/90} reverse={picnic}/>
  {picnic&&<><g transform="translate(1558 567) rotate(-14)"><Watermelon scale={.35}/></g><g transform="translate(380 555) rotate(8)"><Watermelon scale={.25}/></g></>}
  {children}
 </g>;
}

function Heading({title,tag}:{title:string;tag?:string}){return <><Text x={108} y={157} size={61} weight={780}>{title}</Text>{tag&&<Text x={110} y={213} size={29} fill={C.muted} weight={500}>{tag}</Text>}</>;}
function Presenters({frame}:{frame:number}){return <><Character x={108} y={975} frame={frame} mia scale={.56} pose="think"/><Character x={1800} y={975} frame={frame} scale={.56} pose="happy"/></>;}

function Bits({cue,local,frame}:{cue:Cue;local:number;frame:number}){
 const v=cue.visual;
 return <><Heading title={v==='one-bit'?'Two possibilities.':v==='two-bits'?'Order makes a difference.':v==='bit-name'?'One place. One bit.':'8 bits = 1 byte'} tag={v==='byte'?'256 different patterns':undefined}/>
  {v==='one-bit'?<>{[0,1].map((b,i)=><g key={b} transform={`translate(${520+i*820} ${535+Math.sin(local/19+i)*12})`}><Card x={-245} y={-225} w={490} h={430}/><Bead x={0} y={-30} value={b} r={112}/><Text x={0} y={158} anchor="middle" size={44}>{b?'YES':'NO'}</Text></g>)}</>:
   v==='two-bits'?<>{['00','01','10','11'].map((s,i)=><g key={s} transform={`translate(${115+i*438} ${320+22*(1-ease((local-i*8)/25))})`} opacity={ease((local-i*8)/24)}><Card x={0} y={0} w={385} h={390}/>{s.split('').map((b,j)=><Bead key={j} x={112+j*154} y={174} value={Number(b)} r={56}/>)}<Text x={193} y={320} anchor="middle" mono size={55}>{s}</Text></g>)}</>:
   <><Card x={190} y={295} w={1540} h={480}/>{[0,1,0,0,0,0,0,1].map((b,i)=><g key={i} transform={`translate(${335+i*178} ${450+Math.sin(local/20+i)*4})`}><Bead x={0} y={0} value={b} r={57}/>{v==='bit-name'&&<Text x={0} y={125} anchor="middle" size={31}>bit</Text>}</g>)}<path d="M280 565 V600 H1642 V565" stroke={C.teal} strokeWidth={5} fill="none"/><Text x={960} y={682} anchor="middle" size={54}>{v==='byte'?'1 byte · 256 patterns':'8 bits together'}</Text></>}
  <Presenters frame={frame}/>
 </>;
}

function OpenBook({x,y,scale=1,accent=C.teal}:{x:number;y:number;scale?:number;accent?:string}){
 return <g transform={`translate(${x} ${y}) scale(${scale})`}>
  <path d="M-220 -145 Q-100 -190 0 -147 Q100 -190 220 -145 V190 Q100 147 0 190 Q-100 147 -220 190 Z" fill={accent} stroke={C.ink} strokeWidth={4}/>
  <path d="M-207 -150 Q-105 -190 -4 -150 V169 Q-107 129 -207 168 Z M4 -150 Q106 -190 207 -150 V168 Q107 129 4 169 Z" fill={C.paper} stroke={C.ink+'44'} strokeWidth={2}/>
  <Text x={-106} y={-90} anchor="middle" size={29}>ASCII</Text>
  {['A','B','C','L','P','Y'].map((s,i)=><g key={s}><Text x={i<3?-173:39} y={-24+(i%3)*59} size={40}>{s}</Text><Text x={i<3?-100:110} y={-24+(i%3)*59} size={29} mono>{s.charCodeAt(0)}</Text></g>)}
  <path d="M0 -145 V184" stroke={C.wood} strokeWidth={3}/>
 </g>;
}

function Codes({cue,local,frame,facts}:{cue:Cue;local:number;frame:number;facts:Facts}){
 const v=cue.visual,arr=facts.codes.A.bits.split('').map(Number),progress=clamp(local/Math.max(1,cue.duration-25)),count=Math.min(8,Math.floor(progress*9)),active=7-Math.min(7,Math.floor(progress*8));
 if(v==='codebooks')return <><Heading title="The same code at both ends."/><OpenBook x={555} y={557} scale={1.38} accent={C.coral}/><OpenBook x={1370} y={557} scale={1.38}/><path d="M895 553 H1024 M997 531 L1027 553 L997 575" fill="none" stroke={C.teal} strokeWidth={7}/><Presenters frame={frame}/></>;
 if(v==='ascii')return <><Heading title="A shared code: ASCII" tag="Seven-bit ASCII, written here with a leading 0."/><OpenBook x={675} y={566} scale={1.7}/><Card x={1195} y={340} w={490} h={420}/><Text x={1440} y={455} anchor="middle" size={126}>A</Text><Text x={1440} y={555} anchor="middle" size={60} mono>65</Text><Text x={1440} y={671} anchor="middle" size={40} mono>01000001</Text><Presenters frame={frame}/></>;
 return <><Heading title={v==='weights'?'Each place doubles.':v==='padding'?'Wait for all 8.':'64 + 1 = 65 → A'} tag={v==='padding'?'The leading zeros are part of the message.':undefined}/>
  <Card x={178} y={290} w={1564} h={470}/>
  {facts.weights.map((weight,i)=><g key={weight} transform={`translate(${335+i*178} 0)`}>
   <Text x={0} y={387} size={37} anchor="middle" fill={v==='weights'&&i===active?C.coral:C.muted} mono>{weight}</Text>
   {v!=='padding'||i<count?<Bead x={0} y={497+Math.sin(local/20+i)*3} value={v==='weights'?(i===active?1:0):arr[i]} r={57}/>:<circle cx={0} cy={497} r={57} fill="none" stroke={C.teal} strokeDasharray="6 7" opacity={.3}/>}
   {v==='letter-a'&&arr[i]===1&&<path d="M-55 582 H55" stroke={C.coral} strokeWidth={7} strokeLinecap="round"/>}
  </g>)}
  <Text x={960} y={683} size={54} anchor="middle" fill={C.deep}>{v==='weights'?'1  →  2  →  4  →  8  →  …':v==='padding'?`${count} / 8 balls${count===8?'   →   A':''}`:'01000001'}</Text>
  <Presenters frame={frame}/>
 </>;
}

function Message({cue,local,frame,facts}:{cue:Cue;local:number;frame:number;facts:Facts}){
 const first=cue.visual==='send-p',complete=cue.visual==='received';
 const all=facts.messageBits.split('').map(Number),chunk=first?all.slice(0,8):all.slice(8),progress=clamp(local/Math.max(1,cue.duration-35)),ticks=progress*(chunk.length+2),base=first?0:8;
 const delivered=complete?32:base+Math.max(0,Math.min(chunk.length,Math.floor(ticks-2)+1));
 const started=complete?32:base+Math.max(0,Math.min(chunk.length,Math.floor(ticks)+1));
 return <>
  <World frame={frame} cue={cue} local={local}>
   <Pipe frame={frame}/>
   {!complete&&chunk.map((value,i)=>{
    const relative=clamp((local/(Math.max(1,cue.duration-35))*(chunk.length+2)-i)/2);
    if(relative<=0||relative>=1)return null;
    const pt=pipePoint(relative);return <Bead key={i} x={pt.x} y={pt.y} value={value} r={23}/>;
   })}
  </World>
  <Card x={515} y={198} w={890} h={307} fill={complete?'#fff6cf':C.paper}/>
  <Text x={960} y={254} anchor="middle" size={29} fill={C.muted}>{complete?'Message received':'8 balls per letter'}</Text>
  {facts.message.split('').map((letter,i)=><g key={i} transform={`translate(${665+i*197} 0)`}>
   <Text x={0} y={361+(!complete&&delivered>=8*(i+1)?Math.sin(local/10+i)*2:0)} anchor="middle" size={87} fill={delivered>=8*(i+1)?C.deep:'#bccab6'}>{delivered>=8*(i+1)?letter:'·'}</Text>
   <Text x={0} y={421} anchor="middle" size={23} mono fill={C.muted}>{complete||started>i*8?facts.codes[letter].bits:'········'}</Text>
  </g>)}
  {!complete&&<Text x={960} y={890} anchor="middle" size={42}>{delivered} / 32 balls</Text>}
  {complete&&Array.from({length:22},(_,i)=><g key={i} transform={`translate(${400+i*55} ${540+(local*(i%3+1)*2+i*70)%390}) rotate(${local*2+i*31})`}><rect width={8} height={18} rx={3} fill={[C.gold,C.coral,C.blue][i%3]}/></g>)}
 </>;
}

function Box({x,y,n,active=true,chosen=false,frame=0}:{x:number;y:number;n:number;active?:boolean;chosen?:boolean;frame?:number}){
 const lift=chosen?ease(frame/25):0;
 return <g transform={`translate(${x} ${y+(active?Math.sin(frame/28+n)*2:16)}) scale(${active?1:.93})`} opacity={active?1:.24}>
  <ellipse cx={116} cy={165} rx={123} ry={17} fill={C.ink} opacity={.13}/>
  <path d="M6 25 H229 L218 163 H20 Z" fill={chosen?'#f6c865':'#ca9e68'} stroke={C.ink} strokeWidth={3}/>
  <rect x={102} y={28} width={27} height={135} fill={C.coral}/>
  <g transform={`translate(0 ${-68*lift}) rotate(${-9*lift} 116 25)`}><rect x={-1} y={13} width={238} height={36} rx={7} fill={chosen?C.gold:'#e4ba7a'} stroke={C.ink} strokeWidth={3}/><rect x={99} y={13} width={33} height={36} fill={C.coral}/></g>
  <circle cx={118} cy={105} r={37} fill={C.paper} stroke={C.ink+'44'} strokeWidth={2}/><Text x={118} y={121} anchor="middle" size={41}>{n}</Text>
  {chosen&&<g transform={`translate(118 ${30-60*lift})`} opacity={lift}><rect x={-43} y={-40} width={86} height={67} rx={6} fill={C.blue} stroke={C.ink} strokeWidth={2}/><path d="M0 -41 V27 M-43 -12 H43" stroke={C.paper} strokeWidth={10}/><path d="M0 -40 C-40 -85 -48 -32 0 -40 C38 -83 50 -33 0 -40" fill={C.coral} stroke={C.ink} strokeWidth={2}/></g>}
 </g>;
}

function Guess({cue,local,frame,facts}:{cue:Cue;local:number;frame:number;facts:Facts}){
 const v=cue.visual,index=v.startsWith('guess-')?Number(v.slice(6))-1:-1;
 const answered=local>cue.duration*.38;
 const step=index>=0?facts.boxPath[index]:null;
 const remaining=step?(answered?step.remaining:index?facts.boxPath[index-1].remaining:Array.from({length:10},(_,i)=>i+1)):v==='bad-question'?Array.from({length:10},(_,i)=>i+1).filter(n=>n>(local>cue.duration*.55?2:local>cue.duration*.28?1:0)):Array.from({length:10},(_,i)=>i+1);
 const question=step?`Greater than ${step.threshold}?`:v==='questions-rule'?'A shared question tree':v==='bad-question'?'Box 1?   Box 2?':'One hidden gift. Ten boxes.';
 return <>
  <Heading title={question} tag={v==='questions-rule'?'Agree on the questions before the game.':step?`${answered?step.remaining.length:remaining.length} ${remaining.length===1?'box':'boxes'} left`:v==='bad-question'?'One guess removes only one box.':undefined}/>
  {step&&<g opacity={ease(local/15)}><rect x={1200} y={100} width={540} height={150} rx={32} fill={C.paper}/><Bead x={1285} y={174} value={step.answer?1:0} r={44}/><Text x={1390} y={192} size={49}>{answered?(step.answer?'YES':'NO'):'…'}</Text><Text x={1655} y={184} size={29} anchor="end" fill={C.muted}>{index+1} / 4</Text></g>}
  {Array.from({length:10},(_,i)=><Box key={i} x={236+(i%5)*295} y={365+Math.floor(i/5)*290} n={i+1} active={remaining.includes(i+1)} chosen={index===3&&answered&&i===6} frame={local}/>)}
  <Presenters frame={frame}/>
 </>;
}

function QuestionTree({levels,frame}:{levels:number;frame:number}){
 const top=287,dy=levels===3?139:112,left=270,width=1380;
 return <g>
  {Array.from({length:levels+1},(_,level)=>Array.from({length:2**level},(_,j)=>{
   const n=2**level,x=left+width*(j+.5)/n,y=top+level*dy;
   return <g key={`${level}-${j}`} opacity={ease((frame-level*10)/22)}>
    {level<levels&&[0,1].map(b=><path key={b} d={`M${x} ${y+12} L${left+width*(j*2+b+.5)/(n*2)} ${y+dy}`} stroke={C.teal} strokeWidth={level<2?5:3} opacity={.55}/>)}
    {level===levels?<rect x={x-29} y={y-25} width={58} height={50} rx={12} fill={j<10?C.gold:C.blue} stroke={C.ink} strokeWidth={2}/>:<circle cx={x} cy={y} r={level===0?27:18} fill={C.deep}/>}
    {level===levels&&<Text x={x} y={y+9} size={25} anchor="middle">{j+1}</Text>}
   </g>;
  }))}
 </g>;
}

function Counts({cue,local,frame}:{cue:Cue;local:number;frame:number}){
 if(cue.visual==='thousand')return <><Heading title="1,000 possibilities. 10 answers." tag="Keep splitting the remaining choices."/>
  <Card x={170} y={300} w={620} h={530}/><Text x={480} y={445} size={86} anchor="middle">2¹⁰ = 1,024</Text><Text x={480} y={546} size={39} anchor="middle" fill={C.muted}>Enough patterns for 1,000</Text><Text x={480} y={674} size={37} anchor="middle">1,000 → 500 → 250 → … → 1</Text>
  {Array.from({length:1024},(_,i)=><rect key={i} x={1000+(i%32)*19} y={262+Math.floor(i/32)*19} width={14} height={14} rx={3} fill={i<1000?C.teal:C.paper} opacity={i<Math.floor(clamp(local/55)*1024)?1:.17}/>)}<Presenters frame={frame}/></>;
 const levels=cue.visual==='tree-three'?3:4;
 return <><Heading title={levels===3?'3 answers → at most 8 outcomes':'4 answers → at most 16 outcomes'} tag={levels===3?'Ten possibilities need more room.':'Suitable questions guarantee a result within four.'}/><QuestionTree levels={levels} frame={local}/>
  {levels===3?<><Box x={732} y={835} n={9} frame={frame}/><Box x={1030} y={835} n={10} frame={frame}/><Text x={625} y={932} size={37} anchor="end" fill={C.coral}>No room for</Text></>:<Text x={960} y={897} anchor="middle" size={45}>10 boxes fit. 6 patterns spare.</Text>}
  <Presenters frame={frame}/>
 </>;
}

function Watermelon({scale=1}:{scale?:number}){return <g transform={`scale(${scale})`} stroke={C.ink} strokeWidth={3}><path d="M-150 -30 Q0 210 150 -30Z" fill="#559866"/><path d="M-134 -29 Q0 177 134 -29Z" fill="#e7efb8" stroke="none"/><path d="M-119 -29 Q0 149 119 -29Z" fill="#e3745e" stroke="none"/>{[-70,-28,20,62].map((x,i)=><ellipse key={x} cx={x} cy={10+(i%2)*22} rx={5} ry={9} fill={C.ink} stroke="none" transform={`rotate(${x/5} ${x} ${10+(i%2)*22})`}/>)}</g>;}

const fruits=[{name:'Banana',file:'banana_3d',red:false,seeds:false},{name:'Apple',file:'red_apple_3d',red:true,seeds:false},{name:'Grapes',file:'grapes_3d',red:false,seeds:false},{name:'Watermelon',file:'watermelon_3d',red:true,seeds:true}];
function Fruit({cue,local,frame}:{cue:Cue;local:number;frame:number}){
 const v=cue.visual,filter=v==='fruit-red'?1:v==='fruit-seeds'||v==='fruit-tree'?2:0;
 if(v==='fruit-tree')return <>
  <Heading title="Choose the next question." tag="Two questions can separate all four pictures."/>
  <path d="M960 338 L535 470 M960 338 L1385 470 M535 520 L295 680 M535 520 L725 680 M1385 520 L1175 680 M1385 520 L1605 680" fill="none" stroke={C.teal} strokeWidth={5} opacity={.5}/>
  <path d="M960 338 L535 470 L535 520 L725 680" fill="none" stroke={C.gold} strokeWidth={8} strokeDasharray="14 8" strokeDashoffset={-local*2}/>
  <Card x={810} y={280} w={300} h={85}/><Text x={960} y={338} size={40} anchor="middle">Red?</Text>
  <Text x={730} y={408} size={28} anchor="middle">YES</Text><Text x={1190} y={408} size={28} anchor="middle">NO</Text>
  <Card x={325} y={450} w={420} h={85}/><Text x={535} y={508} size={38} anchor="middle">Seeds visible?</Text>
  <Card x={1200} y={450} w={370} h={85}/><Text x={1385} y={508} size={38} anchor="middle">Yellow?</Text>
  {[['NO',390],['YES',650],['YES',1260],['NO',1515]].map(([t,x])=><Text key={String(x)} x={Number(x)} y={594} size={27} anchor="middle">{t}</Text>)}
  {[fruits[1],fruits[3],fruits[0],fruits[2]].map((fruit,i)=><g key={fruit.name} opacity={ease((local-i*8)/25)}>
   <image href={file('curriculum/'+fruit.file+'.png')} x={185+i*435} y={650} width={220} height={180} preserveAspectRatio="xMidYMid meet"/>
   <Text x={295+i*435} y={887} size={35} anchor="middle">{fruit.name}</Text>
  </g>)}
  <Presenters frame={frame}/>
 </>;
 return <>
  <Heading title={filter===0?'What is the snack?':filter===1?'Red in these pictures?':'Can you see seeds?'} tag={v==='fruit-tree'?'The pictures matter. Choose questions that separate the choices.':undefined}/>
  {fruits.map((fruit,i)=>{
   const yes=filter===0||filter===1&&fruit.red||filter===2&&fruit.seeds,revealed=v==='fruit-tree'||local>cue.duration*.35,dim=filter>0&&!yes&&revealed;
   return <g key={fruit.name} opacity={dim?.22:1} transform={`translate(${118+i*445} ${350+(yes?Math.sin(local/19+i)*5:12)})`}>
    <Card x={0} y={0} w={396} h={440} fill={filter===2&&fruit.seeds?'#fff2c6':C.paper}/>
    <image href={file('curriculum/'+fruit.file+'.png')} x={28} y={30} width={340} height={275} preserveAspectRatio="xMidYMid meet"/>
    <Text x={198} y={373} size={38} anchor="middle">{fruit.name}</Text>
    {filter>0&&yes&&revealed&&<circle cx={350} cy={45} r={20} fill={C.gold} stroke={C.ink} strokeWidth={2}/>}
   </g>;
  })}
  {filter>0&&(v==='fruit-tree'||local>cue.duration*.35)&&<g transform="translate(960 898)"><Bead x={-85} y={-13} value={1} r={32}/><Text x={-25} y={0} size={38}>YES</Text></g>}
  <Presenters frame={frame}/>
 </>;
}

function ClosingArt({cue,local,frame}:{cue:Cue;local:number;frame:number}){
 if(cue.visual==='picnic')return <World frame={frame} cue={cue} local={local}/>;
 if(cue.visual==='lights')return <><Heading title="Two states. The same idea."/><Card x={240} y={300} w={1440} h={490}/>{[0,1].map((b,i)=><g key={b} transform={`translate(${580+i*760} 510)`}><path d="M-40 74 V110 H40 V74" fill={C.wood} stroke={C.ink} strokeWidth={4}/><circle cx={0} cy={-15} r={100} fill={b?C.gold:'#b5c0b2'} stroke={C.ink} strokeWidth={5}/>{b&&Array.from({length:10},(_,n)=>{const a=n*Math.PI/5;return <path key={n} d={`M${Math.cos(a)*120} ${-15+Math.sin(a)*120} L${Math.cos(a)*(136+Math.sin(local/12)*6)} ${-15+Math.sin(a)*(136+Math.sin(local/12)*6)}`} stroke={C.gold} strokeWidth={7} strokeLinecap="round"/>;})}<Text x={0} y={209} anchor="middle" size={50}>{b?'ON = 1':'OFF = 0'}</Text></g>)}<Presenters frame={frame}/></>;
 if(cue.visual==='scope')return <><Heading title="A byte is not always a character."/><Card x={280} y={320} w={620} h={450}/><Text x={590} y={494} size={132} anchor="middle">A</Text><Text x={590} y={655} size={44} anchor="middle">8 bits in this example</Text><Card x={1015} y={320} w={620} h={450}/><Text x={1325} y={480} size={95} anchor="middle">文  字</Text><Text x={1325} y={625} size={37} anchor="middle">Other encodings can need</Text><Text x={1325} y={684} size={44} anchor="middle">more than one byte.</Text><Presenters frame={frame}/></>;
 return null;
}

export const FamilyAiLab02:FC<Family02Props>=({tl,facts,captureFrames=180})=>{
 const frame=useCurrentFrame();
 if(!tl||!facts)return null;
 const cue=tl.lines.find(l=>frame>=l.from&&frame<l.from+l.duration)??tl.lines.at(-1)!;
 const local=frame-cue.from,v=cue.visual;
 const teaching=cue.scene>=2&&cue.scene<=3||cue.scene===5||cue.scene===6||cue.scene===7||['lights','scope','lab','worksheet'].includes(v);
 const isLab=v==='lab',isWorksheet=v==='worksheet',isInvite=v==='invite';
 return <AbsoluteFill style={{background:C.sky,fontFamily:FONT,color:C.ink}}>
  <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{position:'absolute',inset:0}}>
   <Forest frame={frame}/>
   {teaching&&<rect x={65} y={60} width={1790} height={950} rx={48} fill={C.paper} opacity={.92}/>}
   {cue.scene===1&&<>
    <World frame={frame} cue={cue} local={local}/>
    {v==='world'&&<><Text x={960} y={135} anchor="middle" size={62} weight={780}>How Can 0 and 1 Send a Message?</Text><Text x={960} y={191} anchor="middle" size={27} fill={C.muted}>By Lucas Academy Team</Text></>}
    {v==='rules'&&<><Card x={647} y={280} w={626} h={240}/><Bead x={787} y={384} value={0} r={56}/><Text x={787} y={477} anchor="middle" size={30}>NO</Text><Bead x={1132} y={384} value={1} r={56}/><Text x={1132} y={477} anchor="middle" size={30}>YES</Text></>}
    {v==='challenge'&&<Text x={960} y={174} anchor="middle" size={62} weight={780}>Only 0 and 1. Can you do it?</Text>}
   </>}
   {cue.scene===2&&<Bits cue={cue} local={local} frame={frame}/>}
   {cue.scene===3&&<Codes cue={cue} local={local} frame={frame} facts={facts}/>}
   {cue.scene===4&&<Message cue={cue} local={local} frame={frame} facts={facts}/>}
   {cue.scene===5&&<Guess cue={cue} local={local} frame={frame} facts={facts}/>}
   {cue.scene===6&&<Counts cue={cue} local={local} frame={frame}/>}
   {cue.scene===7&&<Fruit cue={cue} local={local} frame={frame}/>}
   {cue.scene===8&&<ClosingArt cue={cue} local={local} frame={frame}/>}
   {(isLab||isWorksheet)&&<Heading title={isLab?'Try the real lab.':'Make a message for someone.'}/>}
   {isInvite&&<><World frame={frame} cue={cue} local={local}/><Card x={450} y={115} w={1020} h={295}/><Text x={960} y={214} anchor="middle" size={52} weight={780}>What would you tell your friend?</Text><Text x={960} y={293} anchor="middle" size={37} fill={C.teal}>Lucas Academy · Try it together.</Text></>}
   <Text x={1809} y={1045} size={19} fill={C.paper} anchor="end" weight={500}>{cue.scene===7?'Story & animation · Lucas Academy | Fruit · Fluent Emoji (MIT)':isLab?'Real browser recording · Lucas Academy':isWorksheet?'Original worksheet · Lucas Academy':'Story & animation · Lucas Academy'}</Text>
  </svg>
  {isLab&&<div style={{position:'absolute',left:120,top:265,width:1296,height:729,borderRadius:24,overflow:'hidden',boxShadow:'0 14px 25px #183e3b22',background:'white'}}>
   <Sequence from={cue.from} durationInFrames={Math.min(captureFrames,cue.duration)} layout="none"><OffthreadVideo src={file('capture/lab.mp4')} muted style={{width:'100%',height:'100%',objectFit:'contain'}}/></Sequence>
   {local>=captureFrames&&<Img src={file('capture/lab-a.png')} style={{width:'100%',height:'100%',objectFit:'contain'}}/>}
  </div>}
  {isWorksheet&&<Img src={file('curriculum/worksheet-front.jpg')} style={{position:'absolute',left:230,top:245,width:1030,height:735,objectFit:'contain',transform:`rotate(${-2+Math.sin(local/50)*.5}deg)`,filter:'drop-shadow(5px 12px 12px #173c3b33)'}}/>}
  {(isLab||isWorksheet||isInvite)&&<div style={{position:'absolute',right:isInvite?770:125,top:isInvite?780:405,width:isInvite?380:315,background:C.paper,borderRadius:25,padding:'21px 18px 20px',boxSizing:'border-box',boxShadow:'0 10px 32px #173c3b22',textAlign:'center'}}>
   <Img src={file('qr.png')} style={{width:isInvite?210:230,height:isInvite?210:230,display:isInvite?'inline-block':'block',margin:'auto'}}/>
   <div style={{fontSize:isInvite?20:23,fontWeight:700,marginTop:8}}>ai.lucasacademy.org</div>
   {!isInvite&&<div style={{fontSize:19,marginTop:10,color:C.muted}}>0 and 1 · lesson + worksheets</div>}
  </div>}
 </AbsoluteFill>;
};
