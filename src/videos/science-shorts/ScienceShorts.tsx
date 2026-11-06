import type {CSSProperties, FC, ReactNode} from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, type CalculateMetadataFunction} from 'remotion';

type Film='perceptron'|'optogenetics';
type Line={id:string;visual:string;from:number;duration:number;text:Record<'en'|'zh',string>};
type Shot={asset:string;from:number;duration:number;in:number;out:number;rate:number;layout:'portrait'|'wide'|'square';focus:number};
export type Timeline={film:Film;fps:number;durationInFrames:number;narrated:boolean;lines:Line[];shots:Shot[]};
type Data={pixels:number[];weights:number[];training:{d:string;yes:boolean}[];values:Record<string,string|number>;assets:Record<string,{path:string}>;metrics:Record<string,any>};
export type Props={film:Film;tl?:Timeline|null;data?:Data|null};
const file=(name:string)=>staticFile(`science-shorts-20261105/${name}`);
const C={cream:'#f6ebd1',gold:'#edbf70',mint:'#b7dfc0',green:'#0e3229',amber:'#ffbf57',blue:'#86c5fc'};
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const progress=(frame:number,start:number,frames:number)=>interpolate(frame,[start,start+frames],[0,1],clamp);
const FONT="'Avenir Next', 'Arial', sans-serif", SERIF="'Georgia', 'Times New Roman', serif";
const mono="'Menlo', 'Courier New', monospace";

export const calculateShortMetadata:CalculateMetadataFunction<Props>=async({props,abortSignal})=>{
 const read=async(name:string)=>{const r=await fetch(file(name),{signal:abortSignal});if(!r.ok)throw Error(`Missing short input ${name}`);return r.json();};
 const [tl,data]=await Promise.all([read(`timeline.${props.film}.json`),read('data.json')]);
 return {props:{...props,tl,data},fps:tl.fps,durationInFrames:tl.durationInFrames};
};

const Title:FC<{children:ReactNode;top?:number;size?:number;style?:CSSProperties}>=({children,top=210,size=92,style})=><div style={{position:'absolute',left:78,right:100,top,fontFamily:SERIF,fontSize:size,lineHeight:1.12,fontWeight:700,letterSpacing:-2,color:C.cream,textShadow:'0 3px 20px #00190d',...style}}>{children}</div>;
const Key:FC<{children:ReactNode;top:number;size?:number;color?:string;style?:CSSProperties}>=({children,top,size=50,color=C.cream,style})=><div style={{position:'absolute',left:82,right:100,top,fontSize:size,fontWeight:650,lineHeight:1.28,color,...style}}>{children}</div>;
const Panel:FC<{children:ReactNode;style?:CSSProperties}>=({children,style})=><div style={{position:'absolute',left:62,width:940,padding:36,boxSizing:'border-box',border:'1px solid #ebc78a55',borderRadius:12,background:'#071e1bdb',...style}}>{children}</div>;

/** Keep one continuous take for each story beat. Never loop or freeze a clip. */
function Footage({shot,data}:{shot:Shot;data:Data}){
 const src=file(data.assets[shot.asset].path);
 const videoStyle:CSSProperties={width:'100%',height:'100%',objectFit:'cover',objectPosition:`${shot.focus*100}% 50%`};
 return <Sequence from={shot.from} durationInFrames={shot.duration} layout="none">
  <AbsoluteFill style={{overflow:'hidden'}}>
   <OffthreadVideo src={src} muted startFrom={Math.round(shot.in*30)} playbackRate={shot.rate} style={{...videoStyle,filter:shot.layout==='portrait'?'saturate(.84)':'blur(36px) brightness(.38) saturate(.75)',transform:shot.layout==='portrait'?undefined:'scale(1.07)'}}/>
   <AbsoluteFill style={{background:'linear-gradient(180deg,#001b1be8 0%,#001b1b60 28%,transparent 48%,#001b1b88 78%,#001b1bf2 100%)'}}/>
   {shot.layout!=='portrait'&&<div style={{position:'absolute',left:42,top:shot.layout==='wide'?530:450,width:996,height:shot.layout==='wide'?860:1020,borderRadius:14,overflow:'hidden',boxShadow:'0 25px 80px #0008',border:'2px solid #edd3a455',background:'#17251c'}}>
    <OffthreadVideo src={src} muted startFrom={Math.round(shot.in*30)} playbackRate={shot.rate} style={{...videoStyle,objectFit:'cover',background:'#17251c'}}/>
   </div>}
  </AbsoluteFill>
 </Sequence>;
}

function PixelGrid({pixels,size=600,n=20,fill=C.cream,active=-1}:{pixels:number[];size?:number;n?:number;fill?:string;active?:number}){
 const cell=size/n;
 const shape=pixels.map((p,i)=>p?`M${i%n*cell+1},${Math.floor(i/n)*cell+1}h${cell-2}v${cell-2}h-${cell-2}z`:'').join(' ');
 return <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
  <rect width={size} height={size} fill="#0d3329"/>
  <path d={shape} fill={fill}/>
  {Array.from({length:n+1},(_,i)=><path key={i} d={`M0 ${i*cell}H${size}M${i*cell} 0V${size}`} stroke="#a3c2a43a" strokeWidth={1}/>)}
  {active>=0&&<rect x={active%n*cell} y={Math.floor(active/n)*cell} width={cell} height={cell} fill={C.gold}/>}
 </svg>;
}

function Race({tl,data,frame}:{tl:Timeline;data:Data;frame:number}){
 const cue=tl.lines.find(line=>line.id==='p02')!;
 const elapsed=Math.max(0,(frame-cue.from)/30-.5);
 const rows=[['GPT-6-Astra',data.metrics.astra.median_model,C.blue],['Claude Fable 5.1',data.metrics.claude.median_model,C.gold],['Qwen · local',data.metrics.qwen.median_model,'#afd4aa'],['X',data.metrics.x.median_seconds,C.mint]] as const;
 return <>
  <AbsoluteFill style={{background:'#00160b6b'}}/>
  <Title size={88}>The same 7.<br/>Four programs.</Title>
  <div style={{position:'absolute',left:700,top:420,padding:10,background:'#052d27cc',border:'1px solid #abcfac55'}}><PixelGrid pixels={data.pixels} size={230}/></div>
  <div style={{position:'absolute',left:78,right:120,top:735}}>
   {rows.map(([name,seconds,color],i)=>{
    const done=elapsed>=seconds,yes=i!==2;
    return <div key={name} style={{height:205,color:C.cream}}>
     <div style={{fontSize:42,fontWeight:650,color}}>{name}</div>
     <div style={{marginTop:25,width:760,height:17,background:'#cee9cd22',borderRadius:10,overflow:'hidden'}}><div style={{width:`${Math.min(1,elapsed/seconds)*100}%`,height:'100%',background:color}}/></div>
     <div style={{display:'flex',justifyContent:'space-between',marginTop:18,width:760,fontFamily:mono,fontSize:34}}><span>{done?(i===3?seconds.toFixed(8):seconds.toFixed(2)):elapsed.toFixed(2)} s</span><span style={{color:done?(yes?C.mint:'#f5aa8c'):'#bac6bf'}}>{done?(yes?'YES ✓':'NO ×'):'…'}</span></div>
    </div>;
   })}
  </div>
 </>;
}

function Perceptron({line,tl,data,frame}:{line:Line;tl:Timeline;data:Data;frame:number}){
 const f=frame-line.from,visual=line.visual;
 if(visual==='portal')return <><Title size={154} top={225} style={{color:C.gold}}>1957</Title><Key top={420} size={54}>Claude Fable 5.1<br/>+ GPT-6-Astra</Key><Key top={1450} size={82}>Let’s race.</Key></>;
 if(visual==='race')return <Race tl={tl} data={data} frame={frame}/>;
 if(visual==='speed')return <><Title size={140} top={260} style={{color:C.gold}}>{data.values.x_us}<br/><span style={{fontSize:75}}>microseconds</span></Title><Key top={770} size={70}>per picture</Key><Panel style={{top:1180,textAlign:'center'}}><div style={{fontFamily:SERIF,fontSize:150,color:C.mint}}>{data.metrics.x.right}/{data.metrics.x.n}</div><div style={{fontSize:44}}>test pictures correct</div></Panel></>;
 if(visual==='ratios')return <>
  <Panel style={{top:300}}><div style={{fontFamily:SERIF,fontSize:116,color:C.gold}}>{data.values.claude_million_en} MILLION ×</div><div style={{fontSize:43,marginTop:20}}>faster than<br/>Claude Fable 5.1</div></Panel>
  <Panel style={{top:1020}}><div style={{fontFamily:SERIF,fontSize:108,color:C.mint}}>{data.values.astra_ten_million_en} MILLION ×</div><div style={{fontSize:43,marginTop:20}}>faster than<br/>GPT-6-Astra</div></Panel>
 </>;
 if(visual==='reveal')return <><Title size={102}>Perceptron</Title><Key top={370} size={68} color={C.gold}>1957</Key><div style={{position:'absolute',left:230,top:620}}><PixelGrid pixels={data.pixels} size={600}/></div><Key top={1400} size={90}>{data.values.pixel_n} points</Key></>;
 if(visual==='add'){
  const indices=data.pixels.flatMap((p,i)=>p?[i]:[]);const count=Math.min(indices.length,Math.floor(progress(f,0,line.duration-20)*indices.length));
  const sum=indices.slice(0,count).reduce((total,i)=>total+data.weights[i],0);
  return <><Title>Add.<br/>Then decide.</Title><div style={{position:'absolute',left:230,top:600}}><PixelGrid pixels={data.pixels} active={indices[Math.min(count,indices.length-1)]} size={600}/></div><Key top={1350} size={70}>Score: {sum}</Key><Key top={1490} size={85} color={C.mint}>{count===indices.length?'YES ✓':'…'}</Key></>;
 }
 if(visual==='train')return <>
  <Title size={154} style={{color:C.gold}}>{data.values.train_n}</Title><Key top={420} size={68}>examples</Key>
  <svg width={1080} height={1150} style={{position:'absolute',top:580}}>
   {data.training.map((_,i)=>{const tile=data.training[i*197%data.training.length];const age=((f/165+i*.037)%1);const x=55+(i*83%940),y=age*1050;return <path key={i} d={tile.d} transform={`translate(${x} ${y}) scale(${2.1+i%3*.6})`} fill={tile.yes?C.gold:C.mint} opacity={Math.sin(age*Math.PI)*.28}/>;})}
  </svg>
 </>;
 if(visual==='scope')return <><Title top={260} size={112} style={{color:C.gold}}>ONE TASK</Title><Key top={690} size={82}>Fast here ≠<br/>smarter overall.</Key><div style={{position:'absolute',left:380,top:1180}}><PixelGrid pixels={data.pixels} size={300}/></div></>;
 if(visual==='family')return <><Title size={95}>You can<br/>train one.</Title><Key top={1490} size={49}>Paper. Pencils. Examples.</Key></>;
 return <>
  <AbsoluteFill style={{background:'linear-gradient(#001b1bb8,#001b1b33,#001b1bb8)'}}/>
  <Title size={100}>What would<br/>you teach it?</Title>
  <div style={{position:'absolute',left:260,top:960,width:520,height:520,padding:30,boxSizing:'border-box',background:'#fffef4',borderRadius:4}}><Img src={file('ai-lab-qr.png')} style={{width:460,height:460,imageRendering:'pixelated'}}/></div>
  <Key top={1560} size={43} style={{textAlign:'center',left:40,right:80}}>ai.lucasacademy.org</Key>
 </>;
}

function LightGate({frame,line}:{frame:number;line:Line}){
 const f=frame-line.from,open=(f%95)>26;
 return <>
  <AbsoluteFill style={{background:'#071b26bd',backdropFilter:'blur(14px)'}}/>
  <Title size={88}>Light opens<br/>a tiny door.</Title>
  <svg width={1080} height={1260} style={{position:'absolute',top:500}}>
   <path d="M90 510H990" stroke="#a0caa1" strokeWidth={65}/>
   <rect x={445} y={410} width={190} height={205} rx={28} fill="#143247" stroke={C.blue} strokeWidth={9}/>
   <path d={open?'M460 450L405 400 M620 450L675 400':'M458 450H622'} stroke={C.gold} strokeWidth={15} fill="none"/>
   <path d="M280 120L520 360" stroke={C.blue} strokeWidth={45} strokeLinecap="round" opacity={.45+.2*Math.sin(f/9)}/>
   <path d="M480 330L540 380L525 295" fill={C.blue}/>
   {Array.from({length:8},(_,i)=>{const p=((f/90+i/8)%1);return <circle key={i} cx={510+Math.sin(i)*36} cy={open?280+p*700:240+i*22} r={14} fill={C.gold} opacity={.8}/>;})}
   <path d="M540 755V1010" stroke={C.gold} strokeWidth={9} strokeDasharray="20 18"/>
   <path d="M495 970L540 1030L585 970" fill="none" stroke={C.gold} strokeWidth={9}/>
   <text x={540} y={1180} textAnchor="middle" fontFamily={FONT} fontSize={60} fill={C.cream}>Electrical signal</text>
  </svg>
 </>;
}

function Optogenetics({line,frame}:{line:Line;frame:number}){
 const v=line.visual;
 if(v==='notebook-hook')return <><Title size={90}>How did light<br/>help him find it?</Title><Key top={1430} size={60}>A notebook.<br/>A clue from algae.</Key></>;
 if(v==='algae')return <><Title size={88}>A clue in<br/>tiny algae.</Title><Key top={1550} size={66}>Light → Signal</Key></>;
 if(v==='gate')return <LightGate line={line} frame={frame}/>;
 if(v==='camera')return <><Title size={82}>Light sensors fail.<br/>Signal cells remain.</Title><Key top={1390} size={50}>Like a camera:<br/>sensor ×<br/>signal path ✓</Key></>;
 if(v==='amber')return <><Title size={88}>A new switch.<br/>Amber light.</Title><Key top={1430} size={58} color={C.amber}>A different light switch</Key></>;
 if(v==='encode')return <><Title size={125} style={{color:C.amber}}>ENCODE</Title><Key top={420} size={55}>Scene → light pulses</Key><Key top={1450} size={58}>Glasses send<br/>a new signal.</Key></>;
 if(v==='decode')return <><Title size={124} style={{color:C.amber}}>DECODE</Title><Key top={1310} size={78}>Signals → objects</Key><Key top={1480} size={52}>The brain learns.</Key></>;
 if(v==='touch')return <><Title size={84}>After months<br/>of training…</Title><Key top={1450} size={60}>Locate. Reach. Touch.</Key></>;
 if(v==='limits')return <><Title size={108} style={{color:C.amber}}>PARTIAL<br/>RECOVERY</Title><Panel style={{top:1070,padding:44}}><div style={{fontSize:53,lineHeight:1.8,color:C.cream}}>One patient.<br/>Glasses still needed.<br/>Not normal vision.</div></Panel></>;
 return <><Title size={94} top={270}>How would you<br/>send a picture?</Title><Key top={1360} size={55}>Picture → Code<br/>→ Message</Key></>;
}

export const ScienceShort:FC<Props>=({film,tl,data})=>{
 const frame=useCurrentFrame();if(!tl||!data)throw Error('Short metadata missing');
 const line=tl.lines.find(item=>frame>=item.from&&frame<item.from+item.duration)??tl.lines[tl.lines.length-1];
 const shot=tl.shots.find(item=>frame>=item.from&&frame<item.from+item.duration)!;
 return <AbsoluteFill style={{background:'#09251f',fontFamily:FONT,color:C.cream,overflow:'hidden'}}>
  <Footage shot={shot} data={data}/>
  {film==='perceptron'?<Perceptron line={line} tl={tl} data={data} frame={frame}/>:<Optogenetics line={line} frame={frame}/>}
  {film==='perceptron'&&<AbsoluteFill style={{pointerEvents:'none',boxShadow:'inset 0 0 0 10px #b28a4d55,inset 0 0 120px #0005'}}/>}
 </AbsoluteFill>;
};
