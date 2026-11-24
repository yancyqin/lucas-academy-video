import React from 'react';
import {AbsoluteFill,Composition,Img,OffthreadVideo,Sequence,registerRoot,staticFile,useCurrentFrame} from 'remotion';
import labelData from './labels.json';
const L:Readonly<Record<string,readonly string[]>>=labelData;
const C={ink:'#080b0d',paper:'#f8f6ef',teal:'#a2d4c7',gold:'#e3c39b',muted:'#bac8c8',graphite:'#25292c'};
const FONT='"Hiragino Sans GB", "PingFang SC", Arial, sans-serif';
const ease=(v:number)=>{v=Math.min(1,Math.max(0,v));return v*v*(3-2*v)};
const appear=(f:number,at=0,d=18)=>ease((f-at)/d);
type Scene={id:string;kind:string;frames:number;local_start:number;voice_seconds:number;text:string;piece:string};
type Props={piece:'intro';scenes:Scene[];frames:number;assets:Record<string,{frames:number}>};

// Both language lines inherit one shared font size and appear in this order.
const Pair:React.FC<{id:string;size:number;color?:string;style?:React.CSSProperties}>=({id,size,color=C.paper,style={}})=>
 <div data-bilingual-label={id} style={{fontSize:size,fontFamily:FONT,fontWeight:400,lineHeight:1.24,letterSpacing:.35,color,...style}}>
  <div data-lang="zh">{L[id][0]}</div><div data-lang="en" style={{marginTop:8}}>{L[id][1]}</div>
 </div>;
const Dual:React.FC<{id:string;x?:number;y?:number;size?:number;color?:string;style?:React.CSSProperties}>=({id,x=120,y=90,size=54,color=C.paper,style={}})=>
 <Pair id={id} size={size} color={color} style={{position:'absolute',left:x,top:y,...style}}/>;
const PaperWash=()=> <AbsoluteFill style={{background:'linear-gradient(90deg,rgba(255,255,255,.9),rgba(255,255,255,0) 76%),linear-gradient(0deg,rgba(255,255,255,.6),transparent 38%)'}}/>;
const Footage:React.FC<{id:string;assets:Props['assets'];offset?:number}>=({id,assets,offset=0})=>{
 const f=useCurrentFrame()+offset;const max=(assets[id]?.frames||300)-1;
 return <AbsoluteFill>{f<=max?<OffthreadVideo src={staticFile(id+'.mp4')} startFrom={offset} muted style={{width:'100%',height:'100%',objectFit:'cover'}}/>:<Img src={staticFile(id+'-last.jpg')} style={{width:'100%',height:'100%',objectFit:'cover'}}/>}</AbsoluteFill>;
};
function Pyramid(){
 const keys=['self','esteem','belonging','safety','physical'];
 const tops=[268,410,544,678,814];
 return <AbsoluteFill style={{background:'#191a19'}}>
  <Img src={staticFile('needs-pyramid-v03.png')} style={{width:1920,height:1080,objectFit:'fill'}}/>
  {keys.map((key,i)=><Dual key={key} id={key} x={1380} y={tops[i]} size={34}
    color={i===1?'#ddc490':i===2?'#b8c3a4':C.paper} style={{opacity:i===1||i===2?1:.78}}/>)}
  <Dual id="needTitle" y={49} size={48}/><Dual id="needsNote" y={207} size={20} color="#b4c2c3"/>
 </AbsoluteFill>
}
function Prop({kind,t}:{kind:number;t:number}){
 const common={fill:'none',stroke:'#f3f4ef',strokeWidth:3.5,strokeLinecap:'round' as const,strokeLinejoin:'round' as const};
 return <svg viewBox="0 0 260 280" width="270" height="290"><g {...common}>
  {kind===0&&<><path d="M84 49 H176 V115 Q176 163 130 179 Q84 163 84 115 Z M84 66 H55 V99 Q55 139 90 139 M176 66 H205 V99 Q205 139 170 139 M130 179 V222 M93 238 H167 M103 222 H157"/><path d="M113 89 L130 73 L147 89 L140 115 L120 115 Z" stroke={C.gold}/><path d={`M55 ${203+Math.sin(t*1.4)*4} L210 ${203+Math.sin(t*1.4)*4}`} opacity=".3"/></>}
  {kind===1&&<g transform={`rotate(${Math.sin(t*.7)*2},130,150)`}><path d="M50 213 Q124 232 219 205 M43 231 Q125 251 226 223 M76 53 L158 222 M148 48 L206 211 M64 59 L87 48 M135 54 L159 45"/><path d="M53 268 L225 260" opacity=".4"/></g>}
  {kind===2&&<g transform={`rotate(${Math.sin(t*1.1)*3},130,160)`}><ellipse cx="130" cy="92" rx="60" ry="78"/><path d="M105 162 L114 244 H146 L155 162 M114 244 L146 244"/>{[98,114,130,146,162].map(x=><path key={x} d={`M${x} 27 V157 M79 ${x-58} H181`} strokeWidth="1" opacity=".6"/>)}</g>}
  {kind===3&&<><path d="M125 33 H141 V102 C180 83 195 118 163 141 C208 155 205 215 164 229 Q132 246 100 229 C57 211 63 161 102 141 C70 119 84 84 123 102 Z M128 31 V218 M137 31 V218 M126 230 L124 265 M117 33 H150 M117 49 H150"/><path d={`M${60+Math.sin(t)*15} 88 L${203+Math.sin(t)*15} 195`} stroke={C.gold}/><path d="M102 165 Q113 172 101 184 M163 165 Q151 173 164 184"/></>}
  {kind===4&&<><path d="M68 109 Q130 87 192 109 L224 189 Q229 217 208 223 Q192 226 171 196 H88 Q66 225 48 221 Q31 217 37 191 Z"/><path d="M79 130 V171 M58 150 H101 M176 137 H177 M193 153 H194" strokeWidth="7"/><path d="M106 48 L130 24 L154 48 L130 78 Z M106 48 H154 M130 24 V78" stroke={C.gold} opacity={.55+.4*Math.sin(t*2)**2}/></>}
 </g></svg>
}


function Recognition(){const f=useCurrentFrame();const t=f/30;const keys=['competitions','skiing','tennis','cello','gear'];return <AbsoluteFill style={{background:'#07090a'}}>
 <Dual id="recognized" y={65} size={48}/>
 <div style={{position:'absolute',top:290,left:140,display:'flex',gap:69}}>{keys.map((key,i)=>{const p=appear(f,i*14,22);return <div key={key} style={{opacity:p,transform:`translateY(${(1-p)*22}px)`,width:270,textAlign:'center'}}><Prop kind={i} t={t}/><Pair id={key} size={30} style={{marginTop:24}}/></div>})}</div>
 <Dual id="worth" y={780} size={56} style={{width:1680,textAlign:'center',opacity:appear(f,220,36)}}/>
 </AbsoluteFill>}
function ContentStream(){const f=useCurrentFrame();return <AbsoluteFill style={{background:'#0b1012'}}>
 <svg width="1920" height="1080"><defs><linearGradient id="streamFade" x2="0" y2="1"><stop stopColor="#0b1012"/><stop offset=".3" stopColor="#0b1012" stopOpacity="0"/><stop offset=".7" stopColor="#0b1012" stopOpacity="0"/><stop offset="1" stopColor="#0b1012"/></linearGradient></defs>
  {[0,1,2,3].map(col=><g key={col} transform={`translate(${730+col*305},${-260+(f*(col%2?1:-1)*1.8)%300})`}>{Array.from({length:6},(_,i)=><g key={i} transform={`translate(0,${i*250})`}><rect width="265" height="214" rx="9" fill="#cbd5d4" fillOpacity=".07" stroke="#c9d2d1" strokeOpacity=".5"/><path d="M24 175 L84 97 L133 137 L190 54 L241 175 Z" fill="none" stroke="#e9eeeb" strokeOpacity=".65" strokeWidth="2"/><circle cx="67" cy="53" r="15" fill="none" stroke="#e9eeeb" strokeOpacity=".65"/></g>)}</g>)}
  <rect width="1920" height="1080" fill="url(#streamFade)"/>
 </svg>
 <div style={{position:'absolute',left:0,top:0,width:1050,height:1080,background:'linear-gradient(90deg,#0b1012 58%,transparent)'}}/>
 <Dual id="endless" x={110} y={340} size={72}/>
 <Dual id="contentQuestion" x={115} y={620} size={39} color={C.teal} style={{width:650,opacity:appear(f,105,23)}}/>
 </AbsoluteFill>}
function IdeaDrawing({clock}:{clock:number}){const f=clock;const p=appear(f,42,210);return <AbsoluteFill style={{background:'#080b0d'}}>
 <svg width="1920" height="1080"><path d="M230 610 C390 610 390 348 550 348 C760 348 700 700 950 700 C1120 700 1040 294 1290 294 C1480 294 1420 617 1670 617" fill="none" stroke={C.paper} strokeWidth="5" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1-p}/><path d="M230 625 C390 625 390 363 550 363 C760 363 700 715 950 715 C1120 715 1040 309 1290 309 C1480 309 1420 632 1670 632" fill="none" stroke={C.teal} strokeWidth="2" pathLength="1" strokeDasharray="1" strokeDashoffset={1-p}/>{[400,590,800,1020,1260,1490].map((x,i)=><path key={x} d={`M${x} ${[480,370,610,620,330,500][i]} V790`} fill="none" stroke="#a6b5b6" strokeWidth="2" opacity={appear(f,50+i*11,20)*.35}/>)}</svg>
 <Dual id={f<100?"curiosity":"buildStep"} y={73} size={48} style={{opacity:f<100?appear(100-f,0,10):appear(f,100,12)}}/>
 <div style={{position:'absolute',left:125,top:830,display:'flex',gap:100}}>{['judgment','responsibility','leadTeam'].map((key,i)=><Pair id={key} key={key} size={32} color={i===1?C.gold:C.teal} style={{opacity:appear(f,120+i*45,24),width:[285,380,620][i]}}/>)}</div>
 </AbsoluteFill>}
const SceneView:React.FC<{scene:Scene;assets:Props['assets'];buildingLead:number}>=({scene,assets,buildingLead})=>{
 const f=useCurrentFrame();const id=scene.id;const drawingStart=Math.max(0,(assets.G06?.frames||300)-buildingLead);
 if(id==='n003'||id==='n004')return <Pyramid/>;
 if(id==='n006')return <Recognition/>;
 if(id==='n008')return <ContentStream/>;
 if(id==='n011'&&f>=drawingStart)return <IdeaDrawing clock={f-drawingStart}/>;
 if(id==='n012')return <AbsoluteFill style={{background:C.ink}}><Dual id="bridge" y={270} size={76} style={{width:1680,textAlign:'center'}}/><Dual id="projects" y={580} size={44} color={C.teal} style={{width:1680,textAlign:'center'}}/></AbsoluteFill>;
 const footage=id==='n001'?'G01':id==='n002'?'G02':id==='n005'?'G03':id==='n009'?'G04':id==='n010'||id==='n011'?'G06':'G05';
 return <AbsoluteFill style={{background:'white'}}>
  <Footage id={footage} assets={assets} offset={id==='n011'?buildingLead:0}/><PaperWash/>
  {id==='n001'&&<><Dual id="travel" y={83} size={35} color={C.graphite}/><Dual id="people" y={680} size={80} color={C.graphite} style={{opacity:appear(f,160,25)}}/></>}
  {id==='n002'&&<><Dual id="meal" y={73} size={34} color={C.graphite}/><Dual id="budget" y={226} size={78} color={C.graphite} style={{opacity:appear(f,8,22)}}/><Dual id="budgetNote" y={867} size={23} color={C.graphite}/></>}
  {id==='n005'&&<Dual id="belong" y={745} size={62} color={C.graphite}/>}
  {id==='n007'&&<><div style={{position:'absolute',left:120,top:485,fontFamily:FONT,fontSize:78,color:C.graphite}}>Lucas Academy</div>
   <div style={{position:'absolute',top:630,left:120,display:'flex',gap:50}}>{['languages','art','software'].map((key,i)=><Pair key={key} id={key} size={30} color={C.graphite} style={{width:[410,230,690][i]}}/>)}</div>
   <Dual id="byline" y={867} size={24} color={C.graphite}/></>}
  {id==='n009'&&<Dual id="more" y={365} size={104} color={C.graphite} style={{width:1680,textAlign:'center'}}/>}
  {(id==='n010'||id==='n011')&&<Dual id="ownIdeas" y={80} size={52} color={C.graphite}/>}
 </AbsoluteFill>
};
const Film:React.FC<Props>=({scenes,assets})=>{
 const lead=scenes.find(s=>s.id==='n010')?.frames||258;
 return <AbsoluteFill style={{background:C.ink}}>{scenes.map(scene=><Sequence key={scene.id} from={scene.local_start} durationInFrames={scene.frames}><SceneView scene={scene} assets={assets} buildingLead={lead}/></Sequence>)}</AbsoluteFill>
};
const Root=()=> <Composition id="WhyBuildTogetherV03" component={Film} width={1920} height={1080} fps={30} durationInFrames={30} defaultProps={{piece:'intro',scenes:[],frames:30,assets:{}}} calculateMetadata={({props})=>({durationInFrames:props.frames})}/>;
registerRoot(Root);
