import React from 'react';
import {AbsoluteFill,Composition,Img,OffthreadVideo,Sequence,interpolate,registerRoot,staticFile,useCurrentFrame} from 'remotion';

const C={ink:'#111a1e',paper:'#f8f6ef',teal:'#85c6b6',gold:'#ddb481',muted:'#aebbbd'};
const FONT='"Hiragino Sans GB", "PingFang SC", Arial, sans-serif';
const ease=(v:number)=>{v=Math.min(1,Math.max(0,v));return v*v*(3-2*v)};
const appear=(f:number,at=0,d=18)=>ease((f-at)/d);
type Scene={id:string;kind:string;frames:number;local_start:number;voice_seconds:number;text:string};
type Props={piece:'intro'|'outro';scenes:Scene[];frames:number;assets:Record<string,{frames:number}>};

const Text:React.FC<{children:React.ReactNode;x?:number;y?:number;size?:number;color?:string;style?:React.CSSProperties}>=({children,x=120,y=100,size=64,color=C.paper,style={}})=><div style={{position:'absolute',left:x,top:y,fontSize:size,color,fontFamily:FONT,fontWeight:400,lineHeight:1.45,letterSpacing:1,...style}}>{children}</div>;
const Shade=()=> <AbsoluteFill style={{background:'linear-gradient(90deg,rgba(7,16,19,.68),rgba(7,16,19,0) 75%),linear-gradient(0deg,rgba(7,16,19,.6),transparent 38%)'}}/>;
const Footage:React.FC<{id:string;assets:Props['assets'];offset?:number;opacity?:number}>=({id,assets,offset=0,opacity=1})=>{
 const f=useCurrentFrame();const max=(assets[id]?.frames||300)-1;const at=f+offset;
 return <AbsoluteFill style={{opacity}}>{at<=max?<OffthreadVideo src={staticFile(id+'.mp4')} startFrom={offset} muted style={{width:'100%',height:'100%',objectFit:'cover'}}/>:<Img src={staticFile(id+'-last.jpg')} style={{width:'100%',height:'100%',objectFit:'cover'}}/>}</AbsoluteFill>;
};

function Pyramid({clock}:{clock:number}){
 const names=['自我实现','尊重与自我价值','爱与归属','安全','身体需要'];
 const t=clock/30;const focus=ease((t-4.6)/2.2);
 return <AbsoluteFill style={{background:'radial-gradient(ellipse at 37% 47%,#263b40,#10191d 72%)'}}>
  <svg width="1920" height="1080" viewBox="0 0 1920 1080">
   <defs><linearGradient id="layer" x2="1" y2="1"><stop stopColor="#f4f4e7" stopOpacity=".14"/><stop offset="1" stopColor="#6c8c91" stopOpacity=".05"/></linearGradient></defs>
   {names.map((name,i)=>{const y=205+i*137;const next=y+125;const mid=775;const w0=i*111,w1=(i+1)*111;const op=appear(clock,i*13,24);const active=i===1||i===2;const fill=i===1?C.gold:C.teal;
    return <g key={name} opacity={op*(active?1:1-focus*.64)} transform={`translate(0,${(1-op)*22})`}>
     <path d={`M${mid-w0},${y} L${mid+w0},${y} L${mid+w1},${next} L${mid-w1},${next} Z`} fill={active?fill:'url(#layer)'} fillOpacity={active?.09+focus*.40:1} stroke={active?fill:'#90a6a7'} strokeWidth={active?2.6:1.6}/>
     <path d={`M${mid+w1-12},${y+66} H${1375+i*12}`} fill="none" stroke={active?fill:'#829698'} strokeWidth="1.5" opacity=".65"/>
     <text x="1440" y={y+82} fontSize={active?49:42} fontFamily={FONT} fill={active?fill:C.paper}>{name}</text>
    </g>})}
   <line x1="1430" y1="430" x2="1430" y2="504" stroke={C.paper} strokeWidth="2" opacity={focus*.65}/>
   <path d="M1423 438 L1430 429 L1437 438 M1423 495 L1430 504 L1437 495" fill="none" stroke={C.paper} strokeWidth="2" opacity={focus*.65}/>
  </svg>
  <Text y={72} size={56}>孩子最需要什么？</Text>
  <Text x={125} y={956} size={23} color="#b4c2c3">需求层次示意</Text>
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

function Recognition(){const f=useCurrentFrame();const t=f/30;const labels=['竞赛','滑雪','网球','大提琴','稀有装备'];return <AbsoluteFill style={{background:'#070b0d'}}>
 <Text y={91} size={54}>被认可</Text>
 <div style={{position:'absolute',top:315,left:140,display:'flex',gap:69}}>{labels.map((label,i)=>{const p=appear(f,i*14,22);return <div key={label} style={{opacity:p,transform:`translateY(${(1-p)*22}px)`,width:270,textAlign:'center'}}><Prop kind={i} t={t}/><div style={{marginTop:28,fontFamily:FONT,fontSize:34,color:C.paper}}>{label}</div></div>})}</div>
 <Text y={802} size={66} style={{width:1680,textAlign:'center',opacity:appear(f,220,36)}}>我值得被看见吗？</Text>
 </AbsoluteFill>}

function ContentStream(){const f=useCurrentFrame();return <AbsoluteFill style={{background:'linear-gradient(125deg,#0d181c,#233b42)'}}>
 <svg width="1920" height="1080"><defs><linearGradient id="streamFade" x2="0" y2="1"><stop stopColor="#122126"/><stop offset=".3" stopColor="#122126" stopOpacity="0"/><stop offset=".7" stopColor="#122126" stopOpacity="0"/><stop offset="1" stopColor="#122126"/></linearGradient></defs>
  {[0,1,2,3].map(col=><g key={col} transform={`translate(${730+col*305},${-260+(f*(col%2?1:-1)*1.8)%300})`}>{Array.from({length:6},(_,i)=><g key={i} transform={`translate(0,${i*250})`}><rect width="265" height="214" rx="9" fill={['#789688','#947d69','#6d8897'][(i+col)%3]} fillOpacity=".28" stroke="#b1c2bd" strokeOpacity=".6"/><path d="M24 175 L84 97 L133 137 L190 54 L241 175 Z" fill="none" stroke="#d2dbd7" strokeOpacity=".7" strokeWidth="2"/><circle cx="67" cy="53" r="15" fill="none" stroke="#d2dbd7" strokeOpacity=".7"/></g>)}</g>)}
  <rect width="1920" height="1080" fill="url(#streamFade)"/>
 </svg>
 <div style={{position:'absolute',left:0,top:0,width:1050,height:1080,background:'linear-gradient(90deg,#111f24 50%,transparent)'}}/>
 <Text x={110} y={350} size={76}>要多少<br/>有多少</Text>
 <Text x={115} y={640} size={40} color={C.teal} style={{opacity:appear(f,150,28)}}>能给孩子带来什么？</Text>
 </AbsoluteFill>}

function IdeaDrawing(){const f=useCurrentFrame()-240;const p=appear(f,8,100);return <AbsoluteFill style={{background:'#0b1114'}}>
 <svg width="1920" height="1080"><path d="M230 690 C390 690 390 368 550 368 C760 368 700 790 950 790 C1120 790 1040 294 1290 294 C1480 294 1420 657 1670 657" fill="none" stroke={C.paper} strokeWidth="5" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1-p}/><path d="M230 705 C390 705 390 383 550 383 C760 383 700 805 950 805 C1120 805 1040 309 1290 309 C1480 309 1420 672 1670 672" fill="none" stroke="#8ac7b8" strokeWidth="2" pathLength="1" strokeDasharray="1" strokeDashoffset={1-p}/>{[400,590,800,1020,1260,1490].map((x,i)=><path key={x} d={`M${x} ${[540,400,670,700,330,530][i]} V920`} fill="none" stroke="#81999c" strokeWidth="2" opacity={appear(f,50+i*11,20)*.35}/>)}</svg>
 <Text y={102} size={53}>一点一点，把想法做出来</Text>
 <div style={{position:'absolute',left:125,top:940,display:'flex',gap:110}}>{['判断','负责','带领与合作'].map((v,i)=><div key={v} style={{color:i===1?C.gold:C.teal,fontFamily:FONT,fontSize:35,opacity:appear(f,80+i*33,24)}}>{v}</div>)}</div>
 </AbsoluteFill>}

function SharedIdea(){const f=useCurrentFrame();const p=appear(f,10,80);return <AbsoluteFill style={{background:'#000'}}>
 <Img src={staticFile('family-grid.png')} style={{position:'absolute',top:90,left:120,width:1680,height:945,objectFit:'contain'}}/>
 <svg width="1920" height="1080" style={{position:'absolute',inset:0}}><path d="M690 791 C830 620 1000 850 1170 688" stroke={C.paper} strokeWidth="4" fill="none" pathLength="1" strokeDasharray="1" strokeDashoffset={1-p}/></svg>
 <Text x={140} y={80} size={56}>成为同伴</Text>
 </AbsoluteFill>}

const SceneView:React.FC<{scene:Scene;assets:Props['assets'];pyramidLead:number}>=({scene,assets,pyramidLead})=>{
 const f=useCurrentFrame();const t=f/30;const id=scene.id;
 if(id==='n003'||id==='n004')return <Pyramid clock={f+(id==='n004'?pyramidLead:0)}/>;
 if(id==='n006')return <Recognition/>;
 if(id==='n008')return <ContentStream/>;
 if(id==='n014')return <SharedIdea/>;
 if(id==='n011'&&t>8)return <IdeaDrawing/>;
 if(id==='n012')return <AbsoluteFill style={{background:C.ink}}><Text y={335} size={90} style={{width:1680,textAlign:'center'}}>好奇心能创造什么？</Text><Text y={535} size={44} color={C.teal} style={{width:1680,textAlign:'center'}}>9 个创作项目</Text></AbsoluteFill>;
 let footage=id==='n001'?'G01':id==='n002'?'G02':id==='n005'?'G03':id==='n009'?'G04':id==='n013'?'G06':id==='n010'?'G05-bw':'G05';
 return <AbsoluteFill style={{background:C.ink}}>
  <Footage id={footage} assets={assets}/><Shade/>
  {id==='n001'&&<><Text y={95} size={35} color={C.paper} style={{opacity:.9}}>2026 → 两千年前</Text><Text y={690} size={94} style={{opacity:appear(f,160,25)}}>5,000 个人</Text></>}
  {id==='n002'&&<><Text y={95} size={34}>一顿简单的饭</Text><Text y={205} size={92} style={{opacity:appear(f,8,22)}}>$2,000–3,000</Text><Text y={906} size={23} color="#e0e2da">简餐食材预算假设</Text></>}
  {id==='n005'&&<Text y={763} size={72}>我属于这里吗？</Text>}
  {id==='n007'&&<><Text y={560} size={80}>Lucas Academy</Text><Text y={690} size={38} color={C.teal}>中英文　·　艺术　·　网络项目共建</Text><Text y={906} size={23}>By Lucas Academy Team</Text></>}
  {id==='n009'&&<Text y={390} size={140} style={{width:1680,textAlign:'center',textShadow:'0 3px 30px #000'}}>多 ≠ 好</Text>}
  {id==='n010'&&<Text y={100} size={60}>孩子自己的想法，在哪里？</Text>}
  {id==='n011'&&<Text y={788} size={60}>从兴趣出发</Text>}
  {id==='n013'&&<div style={{position:'absolute',left:125,top:800,display:'flex',gap:100}}>{['带领','负责','合作'].map((s,i)=><div key={s} style={{fontFamily:FONT,color:C.paper,fontSize:55,opacity:appear(f,85+i*55,25)}}>{s}</div>)}</div>}
  {id==='n015'&&<><AbsoluteFill style={{background:'rgba(9,18,22,.42)'}}/><Text x={180} y={265} size={64} style={{opacity:appear(f,4,25),lineHeight:1.7}}>从你和孩子的一个小兴趣开始，<br/>你们想一起创造什么，<br/>给别人带来一点帮助或快乐？</Text><Text x={180} y={871} size={25} color={C.teal} style={{opacity:appear(f,scene.voice_seconds*30+10,30)}}>By Lucas Academy Team</Text></>}
 </AbsoluteFill>
};

const Film:React.FC<Props>=({piece,scenes,assets})=>{
 const filtered=scenes.filter(s=>(s as any).piece===piece);const lead=scenes.find(s=>s.id==='n003')?.frames||150;
 return <AbsoluteFill style={{background:C.ink}}>{filtered.map(scene=><Sequence key={scene.id} from={scene.local_start} durationInFrames={scene.frames}><SceneView scene={scene} assets={assets} pyramidLead={lead}/></Sequence>)}</AbsoluteFill>
};

const Root=()=> <Composition id="WhyBuildTogether" component={Film} width={1920} height={1080} fps={30} durationInFrames={30} defaultProps={{piece:'intro',scenes:[],frames:30,assets:{}}} calculateMetadata={({props})=>({durationInFrames:props.frames})}/>;
registerRoot(Root);
