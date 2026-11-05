import type {CSSProperties, FC, ReactNode} from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, type CalculateMetadataFunction} from 'remotion';
import xResult from '../../../scripts/perceptron-race/results/perceptron-js.json';
import claudeResult from '../../../scripts/perceptron-race/results/claude-fable.json';
import astraResult from '../../../scripts/perceptron-race/results/astra-low.json';
import qwenResult from '../../../scripts/perceptron-race/results/qwen-fast.json';
import recording from '../../../docs/family-ai-lab-01/capture.json';

type Lang = 'en' | 'zh';
type Line = {id:string; scene:number; visual:string; text:Record<Lang,string>; from:number; duration:number; captionFrames:number};
type Timeline = {fps:number; durationInFrames:number; lines:Line[]; titles:string[]; values:Record<string,string|number>};
type VisualData = {pixels:number[]; points:number[]; rounds:number};
export type FamilyProps = {tl?:Timeline|null; data?:VisualData|null; captions?:Lang|null};
const file=(p:string)=>staticFile(`family-ai-lab-01/${p}`);
const PAPER='#f1ecdf', INK='#172a2c', TEAL='#103e42', GOLD='#efba63', CYAN='#8be0dc', BLUE='#4779d7', ORANGE='#dc8352';
const FONT="'Avenir Next', 'Arial', 'Hiragino Sans GB', sans-serif";
const MONO="'SFMono-Regular', 'Menlo', monospace";
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const mix=(f:number,a:number,b:number)=>interpolate(f,[a,b],[0,1],clamp);
const at=(tl:Timeline,v:string)=>tl.lines.find(l=>l.visual===v)!.from;
const sceneAt=(tl:Timeline,s:number)=>tl.lines.find(l=>l.scene===s)!.from;
const vtime=(name:string)=>recording.events.find(e=>e.name===name)!.seconds;

export const calculateFamilyMetadata:CalculateMetadataFunction<FamilyProps>=async({props,abortSignal})=>{
 const read=async(name:string)=>{const r=await fetch(file(name),{signal:abortSignal});if(!r.ok)throw Error(`Missing ${name}: run npm run fal01:prepare`);return r.json();};
 const [tl,picture,model]=await Promise.all([read('timeline.json'),read('picture.json'),read('trained-model.json')]);
 return {props:{...props,tl,data:{pixels:picture.pixels,points:model.points,rounds:model.rounds}},fps:tl.fps,durationInFrames:tl.durationInFrames};
};

const Box:FC<{children:ReactNode;style?:CSSProperties}>=({children,style})=><div style={{position:'absolute',borderRadius:22,background:'#fffaf0',border:'1px solid #203d3e22',boxShadow:'0 12px 40px #173b3012',...style}}>{children}</div>;
const Label:FC<{children:ReactNode;style?:CSSProperties}>=({children,style})=><div style={{fontSize:30,fontWeight:650,letterSpacing:1,...style}}>{children}</div>;
const Big:FC<{children:ReactNode;style?:CSSProperties}>=({children,style})=><div style={{fontSize:76,fontWeight:750,lineHeight:1.13,letterSpacing:-2,...style}}>{children}</div>;
const Credit:FC<{children:ReactNode}>=({children})=><div style={{position:'absolute',right:76,top:886,fontSize:20,color:'#576567',background:'#f6f0e8ed',padding:'7px 15px',borderRadius:4}}>{children}</div>;

/** One unbroken source take followed by its final frame; no video loops. */
const Take:FC<{name:string;from:number;poster:string;frames?:number;start?:number;rate?:number;fit?:'cover'|'contain';style?:CSSProperties}>=({name,from,poster,frames=300,start=0,rate=1,fit='cover',style})=><AbsoluteFill style={{overflow:'hidden',...style}}>
 <Img src={file(poster)} style={{position:'absolute',left:0,top:0,width:'100%',height:'100%',objectFit:fit}}/>
 <Sequence from={from} durationInFrames={Math.ceil(frames/rate)} layout="none">
  <OffthreadVideo src={file(name)} muted startFrom={start} playbackRate={rate} style={{position:'absolute',left:0,top:0,width:'100%',height:'100%',objectFit:fit}}/>
 </Sequence>
</AbsoluteFill>;

const Grid:FC<{pixels:number[];n:number;size?:number;color?:string;paper?:string;reveal?:number;weights?:boolean}>=({pixels,n,size=440,color=INK,paper='#fffaf0',reveal=1,weights=false})=>{
 const gap=n>8?1.4:3,cell=size/n;
 const max=Math.max(1,...pixels.map(Math.abs));
 return <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
  {pixels.map((p,i)=>{const visible=i<pixels.length*reveal;const fill=weights?(p>0?BLUE:p<0?ORANGE:paper):(p?color:paper);return <rect key={i} x={i%n*cell+gap/2} y={Math.floor(i/n)*cell+gap/2} width={cell-gap} height={cell-gap} rx={n>8?1:3} fill={visible?fill:paper} opacity={weights&&p!==0?0.2+0.8*Math.abs(p)/max:1} stroke={weights?'none':'#b9c2b8'} strokeWidth={0.6}/>;})}
 </svg>;
};
const CAT=[129,195,255,153,255,231,126,60];
const HEART=[102,255,255,255,126,60,24,0];
const bytes=(values:number[])=>values.flatMap(b=>Array.from({length:8},(_,i)=>(b>>(7-i))&1));

function Race({tl,data,frame,line}:{tl:Timeline;data:VisualData;frame:number;line:Line}){
 const elapsed=Math.max(0,(frame-at(tl,'race-run'))/30-0.5);
 const go=frame>=at(tl,'race-run')+15;
 const systems=[
  {name:'GPT-6-Astra',seconds:astraResult.median_model,answer:astraResult.rows[0].said,color:'#afa3d8'},
  {name:'Claude Fable 5.1',seconds:claudeResult.median_model,answer:claudeResult.rows[0].said,color:GOLD},
  {name:'Qwen · local',seconds:qwenResult.median_model,answer:qwenResult.rows[0].said,color:'#7cbcaf'},
  {name:'X',seconds:xResult.median_seconds,answer:xResult.rows[0].said,color:CYAN},
 ];
 const ascii=Array.from({length:20},(_,r)=>data.pixels.slice(r*20,r*20+20).map(p=>p?'#':'.').join('')).join('\n');
 return <>
  <div style={{position:'absolute',inset:0,background:'radial-gradient(ellipse at 20% 15%,#225d5d,#0b2429 65%)'}}/>
  <Big style={{position:'absolute',left:80,top:165,color:PAPER,fontSize:68}}>Is this a 7?</Big>
  <Box style={{left:80,top:275,width:500,height:560,background:'#092326',borderColor:'#93c9c533'}}>
   <pre style={{margin:'30px 0 0',textAlign:'center',fontFamily:MONO,fontSize:24,lineHeight:'24px',letterSpacing:2,color:CYAN}}>{ascii}</pre>
  </Box>
  {systems.map((s,i)=>{
   const done=go&&elapsed>=s.seconds;
   const progress=go?Math.min(elapsed/s.seconds,1):0;
   return <div key={s.name} style={{position:'absolute',left:665,top:264+i*143,width:1165,height:126,color:PAPER}}>
    <Label style={{fontSize:29,color:s.color}}>{s.name}</Label>
    <div style={{position:'absolute',left:0,top:60,width:750,height:24,borderRadius:12,background:'#ffffff14',overflow:'hidden'}}><div style={{height:'100%',width:`${progress*100}%`,background:s.color,borderRadius:12}}/></div>
    <div style={{position:'absolute',left:775,top:35,fontFamily:MONO,fontSize:s.name==='X'?28:39,color:s.color}}>{done?(s.name==='X'?s.seconds.toFixed(8):s.seconds.toFixed(2)):(go?Math.min(elapsed,s.seconds).toFixed(2):'0.00')}<span style={{fontSize:23}}> s</span></div>
    {done&&<div style={{position:'absolute',right:0,top:35,fontSize:30,fontWeight:700,color:s.answer?'#c6f1db':'#f5a985'}}>{s.answer?'YES ✓':'NO ×'}</div>}
   </div>;
  })}
  <div style={{position:'absolute',left:82,top:863,fontSize:19,color:'#bbd0c9'}}>2026-11-04 · MacBook Pro · same 20×20 input · medians · warmed JS / reported model times</div>
  <Credit>Original experiment · Author</Credit>
  {line.visual==='mystery'&&<div style={{position:'absolute',right:210,top:340,fontSize:390,fontWeight:700,color:'#b5e6e8',textShadow:'0 0 70px #73dedb55'}}>X<span style={{color:GOLD}}>?</span></div>}
 </>;
}

function Ratios({which}:{which:'claude'|'astra'}){
 const ratio=(which==='claude'?claudeResult.median_model:astraResult.median_model)/xResult.median_seconds;
 const count=which==='claude'?Math.round(ratio/1e6):Math.floor(ratio/1e7)*10;
 return <>
  <AbsoluteFill style={{background:TEAL}}/>
  <div style={{position:'absolute',left:105,top:200,color:PAPER}}>
   <Label style={{color:CYAN,fontSize:35}}>In this picture task</Label>
   <Big style={{fontSize:210,color:GOLD,marginTop:40}}>{which==='claude'?'≈':'>'}{count}<span style={{fontSize:80,letterSpacing:-2}}> million</span></Big>
   <Big style={{fontSize:68,marginTop:15}}>times faster than<br/>{which==='claude'?'Claude Fable 5.1':'GPT-6-Astra'}</Big>
  </div>
  <Credit>Original experiment · median model times · Author</Credit>
 </>;
}

function Pictures({line,frame,tl}:{line:Line;frame:number;tl:Timeline}){
 const cat=line.visual.startsWith('cat')||line.visual==='worksheet-cat';
 const stage=line.visual.includes('photo')?0:line.visual.includes('mosaic')?1:2;
 const worksheet=line.visual.startsWith('worksheet');
 const b=cat?CAT:HEART;
 const src=`curriculum/${cat?'cat':'heart'}_${['photo','mosaic','bits'][stage]}.png`;
 return <>
  <Box style={{left:85,top:180,width:900,height:660,padding:28,display:'flex',alignItems:'center',justifyContent:'center'}}>
   <Img src={file(worksheet?'curriculum/worksheet-heart-cat.png':src)} style={{width:'100%',height:'100%',objectFit:'contain',transform:worksheet?'scale(1.12)':'scale(0.95)',imageRendering:stage===1?'pixelated':'auto'}}/>
  </Box>
  <div style={{position:'absolute',left:1080,top:194}}>
   <Label style={{fontSize:31,color:TEAL,marginBottom:30}}>{worksheet?'Try it on paper':stage===0?'Start with a picture':stage===1?'16 × 16':'8 × 8'}</Label>
   <Grid n={8} pixels={bytes(b)} size={425} reveal={stage===2?mix(frame-line.from,0,65):1}/>
   {line.visual==='cat-bytes'?<div style={{marginTop:24,fontFamily:MONO,fontSize:25,color:TEAL}}>129 195 255 153<br/>255 231 126 60<br/><b style={{fontSize:38,lineHeight:1.8}}>8 bytes</b></div>:
    <Label style={{marginTop:27,color:TEAL,fontSize:29}}>{stage===2?'Black = 1   White = 0':worksheet?'Read a row. Color a row.':'A picture becomes numbers.'}</Label>}
  </div>
  <Credit>Lucas Academy · {worksheet?'worksheet':'lesson images'}</Credit>
 </>;
}

function Neuron({line,frame,tl}:{line:Line;frame:number;tl:Timeline}){
 const f=frame-sceneAt(tl,4), strong=line.visual==='hebb';
 const fire=line.visual==='neuron-fire'||strong;
 return <>
  <svg width={1920} height={900} style={{position:'absolute',top:0}}>
   {Array.from({length:7},(_,i)=>{const y=235+i*77,w=strong?12:3+(i%3)*3;const p=((f/95+i*.18)%1),q=1-p;const px=q*q*q*250+3*q*q*p*580+3*q*p*p*570+p*p*p*860,py=q*q*q*y+3*q*q*p*y+3*q*p*p*490+p*p*p*490;return <g key={i}>
    <path d={`M 250 ${y} C 580 ${y}, 570 490, 860 490`} fill="none" stroke={i%3===0?ORANGE:BLUE} strokeWidth={w} opacity={0.5}/>
    <circle cx={250} cy={y} r={27} fill={i%3===0?ORANGE:BLUE}/>
    <circle cx={px} cy={py} r={9} fill={TEAL} opacity={0.8}/>
   </g>;})}
   <circle cx={940} cy={490} r={112} fill={TEAL}/>
   <circle cx={940} cy={490} r={96} fill="none" stroke={CYAN} strokeWidth={2}/>
   <text x={940} y={510} textAnchor="middle" fontSize={65} fill={PAPER}>Σ</text>
   <path d="M 1052 490 L 1510 490" stroke={TEAL} strokeWidth={7}/>
   <circle cx={1580} cy={490} r={70} fill={fire?GOLD:'#d1d7cd'} stroke={TEAL} strokeWidth={4}/>
   {fire&&<circle cx={1580} cy={490} r={80+(f%50)*1.7} stroke={GOLD} fill="none" strokeWidth={4} opacity={1-(f%50)/50}/>}
  </svg>
  <Label style={{position:'absolute',left:170,top:150}}>Signals</Label>
  <Label style={{position:'absolute',left:830,top:665}}>Add them up</Label>
  <Label style={{position:'absolute',left:1460,top:665}}>{fire?'Fire!':'Enough?'}</Label>
  {line.visual==='neuron-many'&&<Box style={{left:610,top:300,width:1000,height:400,padding:50}}><Big style={{color:TEAL,fontSize:90}}>≈86 billion</Big><Label style={{marginTop:25,fontSize:42}}>neurons in a human brain</Label><Label style={{fontSize:25,marginTop:30,color:'#64716a'}}>We will start with one very simple model.</Label></Box>}
  {strong&&<Box style={{left:590,top:700,width:840,height:105,padding:25,textAlign:'center'}}><Label>Hebb · 1949 · stronger connections</Label></Box>}
  <Credit>Diagram · Author · simplified neuron</Credit>
 </>;
}

function AppleGame({line,frame}:{line:Line;frame:number}){
 const tomato=line.visual==='tomato';
 const lit=['apple-light','tomato','apple-clue'].includes(line.visual);
 const clues=line.visual==='apple-clue';
 return <>
  <Box style={{left:90,top:185,width:750,height:650,padding:40}}>
   <Label style={{color:TEAL,fontSize:42}}>Be a Neuron!</Label>
   <Img src={file(`curriculum/${tomato?'tomato_3d':'red_apple_3d'}.png`)} style={{position:'absolute',left:90,top:120,width:550,height:440,objectFit:'contain'}}/>
   <Label style={{position:'absolute',bottom:35,left:0,width:'100%',textAlign:'center',fontSize:36}}>{tomato?'Tomato':'Apple?'}</Label>
  </Box>
  <div style={{position:'absolute',left:970,top:205,width:820}}>
   <Big style={{fontSize:58,color:TEAL}}>Give each clue points.</Big>
   {['Red  +1','Round  +1',...(clues?['Sweet?  +?']:[])].map((c,i)=><Box key={c} style={{position:'relative',marginTop:22,padding:'22px 35px',fontSize:43,color:i===2?BLUE:INK}}>{c}</Box>)}
   <div style={{display:'flex',alignItems:'center',gap:30,marginTop:42}}><div style={{width:96,height:96,borderRadius:60,background:lit?GOLD:'#d0d8cf',border:`4px solid ${TEAL}`,boxShadow:lit?'0 0 55px #e9ad5177':'none'}}/><Label style={{fontSize:38}}>{tomato?'It gets 2 points, too.':clues?'Choose a new clue.':'2 points → light on'}</Label></div>
  </div>
  <Credit>Classroom game · Lucas Academy</Credit>
 </>;
}

function Code({both=false,train=false}:{both?:boolean;train?:boolean}){
 const predict=['function predict(picture, points) {','  let total = 0;','  for (let i = 0; i < picture.length; i++) {','    if (picture[i] === 1) total += points[i];','  }','  return total > 0;','}'];
 const training=['function train(picture, answer, points) {','  if (predict(picture, points) === answer) return;','  const change = answer ? 1 : -1;','  for (let i = 0; i < picture.length; i++) {','    if (picture[i] === 1) points[i] += change;','  }','}'];
 const parts=both?[['Predict',predict],['Learn',training]] as const:[[train?'Learn':'Predict',train?training:predict]] as const;
 return <>{parts.map(([name,code],i)=><Box key={name} style={{left:80+i*900,top:210,width:both?860:1760,height:570,padding:32,background:'#0e2c30',color:PAPER}}>
  <Label style={{color:GOLD,marginBottom:35,fontSize:36}}>{name}</Label>
  {code.map((row,j)=><div key={j} style={{whiteSpace:'pre',fontFamily:MONO,fontSize:both?21:35,lineHeight:both?'48px':'57px',color:row.includes('if (picture')?CYAN:row.includes('return')?GOLD:PAPER}}>{row}</div>)}
 </Box>)}<Credit>JavaScript rule · Author · same predict / train logic</Credit></>;
}

function Lab({line,tl,frame}:{line:Line;tl:Timeline;frame:number}){
 const twenty=line.visual==='lab-20';
 const start=twenty?at(tl,'lab-20'):at(tl,'lab-round');
 const sourceStart=twenty?Math.ceil(vtime('twenty-trained')*30):0;
 const frames=twenty?125:Math.floor(vtime('twenty-trained')*30)-4;
 const poster=twenty?'twenty-trained':frame<start?'three-zero':'three-trained';
 // Keep the real action continuous, slowing it for reading; then hold the last frame.
 return <>
  <div style={{position:'absolute',left:70,top:160,width:1780,height:705,borderRadius:18,overflow:'hidden',border:'2px solid #9fada0',background:'#f4f5fa'}}>
   <Take name="capture/lab.mp4" poster={`capture/${poster}.png`} from={start} start={sourceStart} frames={frames} rate={twenty?0.6:0.55} style={{width:1056,height:704,top:0}}/>
  </div>
  <Box style={{left:twenty?1090:1190,top:twenty?260:190,width:twenty?665:585,height:twenty?520:650,padding:30,background:'#f6f0e8f7'}}>
   <Label style={{fontSize:34,color:TEAL,marginBottom:25}}>{twenty?'The learned points':'Points · enlarged'}</Label>
   {twenty?<Img src={file('capture/twenty-points.png')} style={{width:410,height:410,objectFit:'contain',marginLeft:90,imageRendering:'pixelated'}}/>:
    <><div style={{position:'relative',width:430,height:380,overflow:'hidden',marginLeft:55}}>
     <Take name="capture/lab.mp4" poster={`capture/${poster}.png`} from={start} start={sourceStart} frames={frames} rate={0.55} style={{width:1920,height:1280,left:-649,top:-263}}/>
    </div><div style={{position:'absolute',left:40,top:485,width:500,height:125,overflow:'hidden'}}>
     <Take name="capture/lab.mp4" poster={`capture/${poster}.png`} from={start} start={sourceStart} frames={frames} rate={0.55} style={{width:2688,height:1792,left:-910,top:-1027.6}}/>
    </div></>}
  </Box>
  <Credit>Browser recording · Lucas Academy · {twenty?'trained model restored':'3×3 activity'}</Credit>
 </>;
}

function MarkI({line,data,frame,tl}:{line:Line;data:VisualData;frame:number;tl:Timeline}){
 const motors=line.visual==='mark-motors',output=line.visual==='mark-output';
 const f=frame-sceneAt(tl,6),rotation=motors?mix(frame-line.from,0,130)*95:70;
 return <>
  <Label style={{position:'absolute',left:80,top:160,color:TEAL,fontSize:40}}>Mark I · 1960</Label>
  <Box style={{left:85,top:245,width:500,height:550,padding:40,background:'#ded5bd'}}>
   <Grid n={20} pixels={data.pixels} size={420} color={TEAL} paper="#eee6d2"/>
   <Label style={{position:'absolute',left:0,bottom:25,width:'100%',textAlign:'center',fontSize:30}}>20 × 20 light sensors</Label>
  </Box>
  <svg width={1920} height={900} style={{position:'absolute',top:0}}>
   {[0,1,2,3,4,5].map(i=><path key={i} d={`M 585 ${330+i*55} C 750 ${330+i*55}, 695 ${370+i*48}, 840 ${370+i*48}`} fill="none" stroke={i%2?BLUE:ORANGE} strokeWidth={5} opacity={0.7}/>)}
   <path d="M 1350 500 L 1540 500" stroke={TEAL} strokeWidth={7}/>
  </svg>
  <Box style={{left:840,top:270,width:510,height:470,background:'#314843'}}>
   {Array.from({length:6},(_,i)=><div key={i} style={{position:'absolute',left:55+(i%3)*155,top:60+Math.floor(i/3)*190,width:92,height:92,borderRadius:50,background:'radial-gradient(circle at 30% 25%,#e9c990,#a1743d)',border:'6px solid #152c27',transform:`rotate(${rotation+(i%2)*20}deg)`}}><div style={{position:'absolute',left:41,top:8,width:5,height:35,background:'#273c31'}}/></div>)}
   <Label style={{position:'absolute',left:0,bottom:25,width:'100%',textAlign:'center',fontSize:26,color:PAPER}}>Motor → adjustable weight</Label>
  </Box>
  <div style={{position:'absolute',left:1570,top:410,width:170,height:170,borderRadius:90,border:`7px solid ${TEAL}`,background:output?GOLD:'#cbcdbb',boxShadow:output?'0 0 70px #eabb6377':'none'}}/>
  <Label style={{position:'absolute',left:1560,top:630,fontSize:40}}>Output</Label>
  <Credit>Author diagram · simplified Mark I, not a wiring plan</Credit>
 </>;
}

function Report({newspaper=false}:{newspaper?:boolean}){
 return <>
  <Box style={{left:230,top:200,width:1460,height:600,padding:75,background:'#faf3df',borderColor:'#c2b293'}}>
   <Label style={{fontFamily:MONO,color:'#637066',fontSize:27}}>{newspaper?'THE NEW YORK TIMES · JULY 8, 1958':'CORNELL AERONAUTICAL LABORATORY · JANUARY 1957'}</Label>
   <div style={{height:2,background:'#b0a388',margin:'32px 0'}}/>
   <Big style={{fontFamily:"'Georgia', serif",fontSize:newspaper?91:95,color:INK}}>{newspaper?<>New Navy Device<br/>Learns By Doing</>:<>The Perceptron</>}</Big>
   {!newspaper&&<Label style={{fontFamily:"'Georgia', serif",fontSize:44,lineHeight:1.35,marginTop:35}}>A Perceiving and Recognizing Automaton<br/><span style={{fontSize:31}}>Frank Rosenblatt · Report 85-460-1</span></Label>}
  </Box>
  <Credit>{newspaper?'Headline · The New York Times · typeset recreation':'Title · Rosenblatt 1957 report · typeset recreation'}</Credit>
 </>;
}

function Scale({data,zoom,frame,line}:{data:VisualData;zoom:boolean;frame:number;line:Line}){
 const p=mix(frame-line.from,0,100);
 const billion=8e9, side=610, little=side/Math.sqrt(billion/data.points.length);
 return <>
  <Big style={{position:'absolute',left:100,top:175,fontSize:62,color:TEAL}}>{zoom?'How many numbers?':'Only the black squares add points.'}</Big>
  <Box style={{left:95,top:300,width:620,height:500,padding:35}}>
   <div style={{display:'flex',justifyContent:'center'}}><Grid n={20} pixels={zoom?data.points:data.pixels} weights={zoom} size={340}/></div>
   <Label style={{fontSize:35,textAlign:'center',marginTop:22}}>{data.points.length} points{zoom?' · enlarged inset':''}</Label>
  </Box>
  {zoom?<>
   <div style={{position:'absolute',left:1060,top:205,width:side,height:side,background:TEAL,borderRadius:4,boxShadow:'inset 0 0 0 1px #8ccac633'}}/>
   <div style={{position:'absolute',left:825,top:510,width:little,height:little,background:BLUE}}/>
   <div style={{position:'absolute',left:775,top:550,fontSize:25}}>400<br/><span style={{fontSize:21}}>at this scale</span></div>
   <div style={{position:'absolute',left:1105,top:370,color:PAPER}}><Big style={{fontSize:99,color:GOLD}}>≈8 billion</Big><Label style={{fontSize:34,marginTop:15}}>parameters · Qwen3 8B</Label><Label style={{fontSize:24,marginTop:75,color:CYAN}}>Same area scale</Label></div>
  </>:<div style={{position:'absolute',left:850,top:370}}><Big style={{fontSize:130,color:TEAL}}>≤{data.points.length}</Big><Label style={{fontSize:48,marginTop:25}}>additions per picture</Label><Label style={{fontSize:30,marginTop:35,color:'#647168'}}>Read the points. Add. Decide.</Label></div>}
  <Credit>{zoom?'Author diagram · Qwen model card · rounded parameter count':'JavaScript predict() · Author'}</Credit>
 </>;
}

const HISTORY=[['1957','Perceptron','One simple neuron'],['1969','Limits','What one layer cannot do'],['1986','Backpropagation','Learning in layers'],['2012','ImageNet','Deep networks see better'],['2017','Transformer','Attention'],['Now','Chat AI','Many kinds of questions']];
function History({line}:{line:Line}){
 const key=line.visual.split('-')[1];const selected=Math.max(0,HISTORY.findIndex(h=>h[0]===key));
 return <>
  <Big style={{position:'absolute',left:100,top:190,color:TEAL}}>How AI grew</Big>
  <div style={{position:'absolute',left:125,top:530,width:1650,height:5,background:'#a0b5a8'}}/>
  {HISTORY.map((h,i)=><div key={h[0]} style={{position:'absolute',left:90+i*295,top:380,width:270,textAlign:'center'}}>
   <div style={{fontFamily:MONO,fontSize:58,fontWeight:700,color:i===selected?TEAL:'#7b8d82'}}>{h[0]}</div>
   <div style={{width:28,height:28,borderRadius:20,background:i===selected?GOLD:TEAL,margin:'80px auto 35px',boxShadow:i===selected?'0 0 0 13px #efba6333':'none'}}/>
   <Label style={{fontSize:29,minHeight:80,color:TEAL}}>{h[1]}</Label>
   <Label style={{fontSize:25,color:'#65736a',fontWeight:400}}>{h[2]}</Label>
  </div>)}
  <Credit>Historical timeline · Author · references in production notes</Credit>
 </>;
}

function Limits({chat=false}:{chat?:boolean}){
 return <>
  <Big style={{position:'absolute',left:100,top:190,color:TEAL,fontSize:72}}>{chat?'Many kinds of questions':'A confident answer can still be wrong.'}</Big>
  {chat?<div style={{position:'absolute',left:120,top:355,width:1640,display:'flex',gap:35}}>{['Explain a story','Help with code','Translate a sentence'].map((c,i)=><Box key={c} style={{position:'relative',width:520,height:325,padding:45,background:i===1?TEAL:'#fffaf0',color:i===1?PAPER:INK}}><div style={{fontSize:75,color:i===1?GOLD:BLUE,marginBottom:55}}>{['“ ”','{ }','A ↔ B'][i]}</div><Label style={{fontSize:37}}>{c}</Label></Box>)}</div>:
   <><Label style={{position:'absolute',left:115,top:330,fontSize:40}}>Qwen · local · original experiment</Label><div style={{position:'absolute',left:110,top:425,display:'flex',gap:18}}>{qwenResult.rows.map((r,i)=><Box key={i} style={{position:'relative',width:150,height:160,background:r.right?'#dbe8d8':'#f2d8c1',borderRadius:14,padding:23,textAlign:'center'}}><Label style={{fontSize:29}}>NO</Label><div style={{fontSize:55,color:r.right?TEAL:'#ae552a',marginTop:14}}>{r.right?'✓':'×'}</div></Box>)}</div><Big style={{position:'absolute',left:115,top:660,fontSize:92,color:TEAL}}>{qwenResult.right} / {qwenResult.n}<span style={{fontSize:39,marginLeft:35}}>correct</span></Big></>}
  <Credit>{chat?'Illustration · Author':'Original experiment · Author'}</Credit>
 </>;
}

function Closing({line,tl}:{line:Line;tl:Timeline}){
 if(line.visual==='family') return <><Take name="muse/G3.mp4" poster="muse/G3-last.png" from={at(tl,'family')} style={{height:930}}/><Credit>AI generated · Muse · illustration</Credit></>;
 if(line.visual==='invite')return <><AbsoluteFill style={{background:TEAL}}/><Label style={{position:'absolute',left:110,top:220,color:CYAN,fontSize:37}}>Lucas Academy</Label><Big style={{position:'absolute',left:110,top:345,fontSize:120,color:PAPER}}>What would you<br/>teach it?</Big><div style={{position:'absolute',right:150,top:280,width:400,height:400,opacity:.85}}><Grid n={8} pixels={bytes(HEART)} color={GOLD} paper={TEAL} size={380}/></div><Credit>Illustration · Author</Credit></>;
 return <>
  <div style={{position:'absolute',left:95,top:220,display:'flex',gap:35}}>{['Print','Color','Teach'].map((s,i)=><Box key={s} style={{position:'relative',width:550,height:535,padding:30}}><Label style={{fontSize:48,color:TEAL,marginBottom:25}}>{s}</Label><Img src={file(i===0?'curriculum/worksheet-heart-cat.png':i===1?'curriculum/cat_bits.png':'capture/twenty-trained.png')} style={{width:'100%',height:370,objectFit:'contain'}}/></Box>)}</div>
  <Label style={{position:'absolute',left:100,top:795,fontSize:38,color:TEAL}}>{line.visual==='url'?'Website coming soon':'Try it together.'}</Label><Credit>Lucas Academy · worksheets and browser lab</Credit>
 </>;
}

function Visual({line,tl,data,frame}:{line:Line;tl:Timeline;data:VisualData;frame:number}){
 const v=line.visual;
 if(v.startsWith('ratio-'))return <Ratios which={v==='ratio-claude'?'claude':'astra'}/>;
 if(v==='terminal')return <><div style={{position:'absolute',left:90,top:190,width:1740,height:650,overflow:'hidden',background:'#000',borderRadius:18}}><Take name="capture/terminal-view.mp4" poster="capture/terminal-view.png" from={line.from} frames={90} fit="contain" style={{height:'100%',width:'100%'}}/></div><Credit>Real terminal recording · saved original results · Author</Credit></>;
 if(line.scene===1)return <Race tl={tl} data={data} frame={frame} line={line}/>;
 if(v==='title')return <><Take name="muse/G1.mp4" poster="muse/G1-last.png" from={line.from} style={{height:930}}/><div style={{position:'absolute',inset:0,height:930,background:'#0c2d2ee6'}}/><Label style={{position:'absolute',left:100,top:220,color:CYAN,fontSize:35}}>Family AI Lab · Lucas Academy</Label><Big style={{position:'absolute',left:100,top:330,color:PAPER,fontSize:94}}>A 1957 AI model is faster<br/>than ChatGPT Astra<br/>and Claude Fable?</Big><Credit>AI generated background · Muse · illustration</Credit></>;
 if(v==='time-travel')return <><Take name="muse/G1.mp4" poster="muse/G1-last.png" from={at(tl,'title')} style={{height:930}}/><Big style={{position:'absolute',left:100,top:225,fontFamily:"'Georgia', serif",fontSize:180,color:'#fff3d8',textShadow:'0 3px 25px #18201a'}}>1957</Big><Credit>AI generated · Muse · illustration</Credit></>;
 if(line.scene===3)return <Pictures line={line} tl={tl} frame={frame}/>;
 if(v.startsWith('apple-')||v==='tomato')return <AppleGame line={line} frame={frame}/>;
 if(line.scene===4)return <Neuron line={line} tl={tl} frame={frame}/>;
 if(v.startsWith('lab-'))return <Lab line={line} tl={tl} frame={frame}/>;
 if(v.startsWith('code-')||v==='reveal-code')return <Code both={v==='code-both'||v==='reveal-code'} train={v==='code-train'}/>;
 if(v==='reveal'||v==='reveal-trained')return <><AbsoluteFill style={{background:TEAL}}/><Label style={{position:'absolute',left:110,top:215,fontSize:48,color:CYAN}}>X =</Label><Big style={{position:'absolute',left:110,top:330,fontSize:170,color:GOLD}}>Perceptron</Big><Label style={{position:'absolute',left:125,top:600,fontSize:47,color:PAPER}}>{v==='reveal-trained'?`${xResult.training.pictures} training pictures · ${xResult.right}/${xResult.n} test answers correct`:'Frank Rosenblatt · 1957'}</Label><Credit>Original experiment and Rosenblatt 1957 · Author</Credit></>;
 if(v==='report'||v==='newspaper')return <Report newspaper={v==='newspaper'}/>;
 if(v.startsWith('mark-'))return <MarkI line={line} tl={tl} data={data} frame={frame}/>;
 if(v==='vintage-lab')return <><Take name="muse/G2.mp4" poster="muse/G2-last.png" from={line.from} rate={1} style={{height:930}}/><Credit>AI generated · Muse · imagined computer room</Credit></>;
 if(v==='scale'||v==='scale-zoom')return <Scale data={data} zoom={v==='scale-zoom'} frame={frame} line={line}/>;
 if(v.startsWith('timeline-'))return <History line={line}/>;
 if(v==='chat'||v==='limits')return <Limits chat={v==='chat'}/>;
 if(line.scene===8)return <Closing line={line} tl={tl}/>;
 throw Error(`No shot for ${v}`);
}

export const FamilyAiLab01:FC<FamilyProps>=({tl,data,captions=null})=>{
 const frame=useCurrentFrame();
 if(!tl||!data)throw Error('Family AI Lab metadata not loaded');
 const line=tl.lines.find(l=>frame>=l.from&&frame<l.from+l.duration)??tl.lines[tl.lines.length-1];
 const footage=['time-travel','vintage-lab','family'].includes(line.visual);
 const dark=(line.scene===1&&line.visual!=='terminal')||footage||['title','reveal','reveal-trained','invite'].includes(line.visual);
 return <AbsoluteFill style={{fontFamily:FONT,background:PAPER,color:INK}}>
  <AbsoluteFill style={{height:930,backgroundImage:'linear-gradient(#35665108 1px,transparent 1px),linear-gradient(90deg,#35665108 1px,transparent 1px)',backgroundSize:'40px 40px'}}/>
  <Visual line={line} tl={tl} data={data} frame={frame}/>
  {footage&&<div style={{position:'absolute',top:0,left:0,right:0,height:140,background:'linear-gradient(#092b2dcc,transparent)'}}/>}
  <div style={{position:'absolute',left:80,top:56,color:dark?CYAN:TEAL,fontSize:24,fontWeight:650,letterSpacing:4,textTransform:'uppercase'}}>Family AI Lab</div>
  <div style={{position:'absolute',right:80,top:52,color:dark?'#d4dfd4':TEAL,fontSize:31,fontWeight:650}}>{tl.titles[line.scene-1]}</div>
  <div style={{position:'absolute',left:0,right:0,top:931,height:149,background:'#0a2025',borderTop:'2px solid #4d777055'}}/>
  {captions&&frame<line.from+line.captionFrames&&<div style={{position:'absolute',bottom:35,left:100,right:100,textAlign:'center',color:'#fff9e9',fontSize:captions==='en'?40:43,lineHeight:1.23,fontWeight:500,textShadow:'0 2px 3px #000',maxHeight:110}}>{line.text[captions]}</div>}
  <div style={{position:'absolute',left:0,bottom:0,height:4,width:`${(frame+1)/tl.durationInFrames*100}%`,background:GOLD}}/>
 </AbsoluteFill>;
};
