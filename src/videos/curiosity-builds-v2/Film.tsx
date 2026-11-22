import React from 'react';
import {AbsoluteFill, Composition, registerRoot, useCurrentFrame, interpolate, Easing, OffthreadVideo, staticFile} from 'remotion';
import plan from '../../../scripts/curiosity-builds-v2/plan.json';

const INK='#080e19', WHITE='#f5f1e6', GOLD='#f5bc68', BLUE='#70d7e8';
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const mix=(x:number,a:number,b:number)=>interpolate(x,[0,1],[a,b],clamp);
function Geometry({id,t,progress}:{id:string;t:number;progress:number}){
 const P=(x:number,y:number,z:number)=>{const a=t*.12-.5;const X=x*Math.cos(a)+z*Math.sin(a),Z=-x*Math.sin(a)+z*Math.cos(a);return [X*1.05, y*.9+Z*.35]};
 const line=(pts:number[][])=>pts.map((p,i)=>`${i?'L':'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
 let content:React.ReactNode;
 if(id==='roller'){
  const path=line(Array.from({length:440},(_,i)=>{const u=i/439*7*Math.PI;const r=250*(1-i/520);return P(Math.cos(u)*r, -210+i/439*390,Math.sin(u)*r)}));
  content=<><path d={path} stroke={BLUE} strokeWidth="1.5" opacity=".25"/><path d={path} stroke={GOLD} strokeWidth="9" pathLength="1" strokeDasharray="1" strokeDashoffset={1-progress}/>{Array.from({length:16},(_,i)=><path key={i} d={line([P(-280,-220+i*30,0),P(280,-220+i*30,0)])} stroke={BLUE} opacity=".09"/>)}</>;
 }else if(id==='chess'){
  content=<>{Array.from({length:64},(_,i)=>{const x=i%8,y=Math.floor(i/8),cx=(x-y)*39,cy=(x+y)*21-150;return <path key={i} d={`M${cx},${cy}l39,21 -39,21 -39,-21Z`} fill={(x+y)%2?'#123245':'#314f57'} stroke={BLUE} strokeWidth="1" opacity={Math.min(1,progress*3-i/64)}/>})}{Array.from({length:8},(_,i)=><g key={i} transform={`translate(${(i-6)*39},${(i+6)*21-166})`} opacity={mix(progress,.1,1)}><ellipse cy="24" rx="15" ry="7" fill={GOLD}/><path d="M-12,20 L-7,-3 Q-15,-15 0,-20 Q15,-15 7,-3 L12,20Z" fill={GOLD}/></g>)}</>;
 }else if(id==='cube'){
  content=<>{[0,1,2].flatMap(face=>Array.from({length:49},(_,i)=>{const x=i%7,y=Math.floor(i/7),s=33;const pts=face===0?[[0,0],[s,s*.5],[0,s],[-s,s*.5]]:face===1?[[0,0],[s,s*.5],[s,s*1.6],[0,s*1.1]]:[[0,0],[-s,s*.5],[-s,s*1.6],[0,s*1.1]];const X=face===0?(x-y)*s:face===1?-231+x*s:231-x*s;const Y=face===0?-225+(x+y)*s*.5:face===1?-109+x*s*.5+y*s*1.1:-109+x*s*.5+y*s*1.1;return <path key={face+'-'+i} d={line(pts.map(p=>[p[0]+X,p[1]+Y]))+'Z'} fill={[GOLD,BLUE,'#d58168'][face]} stroke={INK} strokeWidth="3" opacity={mix(progress,.08,1)}/>;}))}</>;
 }else if(id==='vangogh'||id==='journey'){
  content=<>{Array.from({length:7},(_,i)=>{const x=(i-3)*80,y=Math.abs(i-3)*20-60;return <g key={i} transform={`translate(${x},${y})`} opacity={Math.max(0,progress*2-i*.13)}><rect x="-45" y="-150" width="88" height="230" fill="#142433" stroke={GOLD} strokeWidth="3"/>{Array.from({length:10},(_,j)=><path key={j} d={`M-35,${-130+j*20}q30,${Math.sin(j+i)*30} 68,0`} stroke={j%2?GOLD:BLUE} strokeWidth="5"/>)}</g>})}<path d="M-300,160L0,40 300,160M-300,250L0,40 300,250" stroke={BLUE} opacity=".5"/></>;
 }else if(id==='sky'){
  content=<>{Array.from({length:65},(_,i)=>{const a=i*2.399,r=35+Math.sqrt(i)*33;return <circle key={i} cx={Math.cos(a)*r} cy={Math.sin(a)*r*.7} r={i%7?2:5} fill={i%3?BLUE:GOLD} opacity={Math.max(0,progress*2-i/65)} />})}{Array.from({length:9},(_,i)=><ellipse key={i} cy={150+i*12} rx={270-i*14} ry={32+i*2} stroke={BLUE} strokeWidth="1" opacity=".3" />)}<ellipse rx="290" ry="220" stroke={BLUE} opacity=".16"/></>;
 }else if(id==='chameleon'){
  content=<><path d="M-120,35 Q-180,-110 -50,-100 Q40,-130 100,-60 L182,-40 130,10 Q40,50 -100,45 Q-190,170 -230,95 Q-260,10 -170,0 Q-100,10 -155,60" fill="#183947" stroke={GOLD} strokeWidth="7" pathLength="1" strokeDasharray="1" strokeDashoffset={1-progress}/><circle cx="115" cy="-45" r="13" fill={BLUE}/>{Array.from({length:25},(_,i)=><path key={i} d={`M${-130+(i%7)*45},${-150+Math.floor(i/7)*70}q25,-24 50,0`} stroke={i%2?BLUE:GOLD} opacity={.12+progress*.3} strokeWidth="13"/>)}</>;
 }else if(id==='coder'){
  content=<>{Array.from({length:12},(_,i)=><path key={i} d={`M-270,${-225+i*43}H270 M${-250+i*43},-230V250`} stroke={BLUE} opacity=".16"/>)}<path d="M-230,180H-100V40H50V-100H230" stroke={GOLD} strokeWidth="30" strokeLinejoin="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1-progress}/><circle cx="230" cy="-180" r="14" fill={BLUE}/></>;
 }else{
  const words=['Your','word','is','a','lamp','to','my','feet.'];
  content=<>{words.map((w,i)=>{const x=(i%3-1)*185,y=(Math.floor(i/3)-1)*100;return <g key={w+i} transform={`translate(${x+Math.sin(i*4)*100*(1-progress)},${y+Math.cos(i*3)*160*(1-progress)})`}><rect x="-84" y="-37" width="168" height="74" rx="10" fill="#17303b" stroke={i<progress*8?GOLD:BLUE} strokeWidth="2"/><text y="10" fill={WHITE} fontSize="31" textAnchor="middle" fontFamily="Georgia">{w}</text></g>})}</>;
 }
 return <svg width="720" height="720" viewBox="-360 -360 720 720" fill="none">{content}</svg>;
}
function Film({project=0,kind='project'}:{project?:number;kind?:string}){
 const f=useCurrentFrame(),t=f/30;
 const item=plan.projects[project];
 const isBuild=t>=3.7;const trans=interpolate(t,[3.55,4.15],[0,1],clamp);
 const progress=interpolate(t,[.3,3.4,3.7,6.8],[.1,.5,.5,1],clamp);
 const opacity=interpolate(t,[0,.25,7,7.2],[0,1,1,0],clamp);
 if(kind==='ending'){
  const starts=[0,3.2,6.4,9.6,13.6];let i=starts.findLastIndex(s=>t>=s);const local=t-starts[i];const end=i===4?4.4:starts[i+1]-starts[i];
  const a=interpolate(local,[0,.45,end-.4,end],[0,1,1,i===4?1:0],clamp);
  return <AbsoluteFill style={{background:INK,color:WHITE,fontFamily:'Helvetica Neue, Arial',padding:'100px 145px',justifyContent:'center'}}>
   <div style={{position:'absolute',top:90,color:GOLD,fontSize:23,letterSpacing:5}}>LUCAS ACADEMY · LET'S BEGIN</div>
   <div style={{fontFamily:'Georgia',fontSize:i===3?90:108,lineHeight:1.15,maxWidth:1580,opacity:a,transform:`translateY(${(1-a)*20}px)`}}>{plan.ending_questions[i]}</div>
   <div style={{position:'absolute',bottom:90,fontSize:28,color:BLUE}}>lucasacademy.org</div>
   <div style={{position:'absolute',bottom:32,fontSize:19,color:'#8798aa'}}>Music: Mozart · Bach · Chopin · Debussy. Clair de lune: Laurens Goedhart, CC BY 3.0, edited excerpt. Full sources accompany this film.</div>
  </AbsoluteFill>;
 }
 if(kind!=='project')return <AbsoluteFill style={{background:INK,color:WHITE,justifyContent:'center',padding:'110px 150px',fontFamily:'Helvetica Neue, Arial'}}>
  <OffthreadVideo src={staticFile('sky-transition.mp4')} muted style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',opacity:.32}}/>
  <div style={{position:'absolute',inset:0,background:'linear-gradient(90deg,rgba(8,14,25,.9),rgba(8,14,25,.15))'}}/>
  <div style={{position:'relative'}}>
  <div style={{fontSize:23,letterSpacing:6,color:GOLD,marginBottom:46}}>LUCAS ACADEMY</div>
  <div style={{fontFamily:'Georgia',fontSize:118,lineHeight:1.1,maxWidth:1350}}>{kind==='opening'?<>What can<br/>curiosity build?</>:<>What will you<br/>build next?</>}</div>
  <div style={{fontSize:29,color:BLUE,marginTop:48}}>{kind==='opening'?'Ideas become places, games, and things to explore.':'Explore the projects at lucasacademy.org'}</div>
  </div><div style={{position:'absolute',bottom:70,fontSize:22,color:'#93a3b3'}}>By Lucas Academy Team</div>
 </AbsoluteFill>;
 return <AbsoluteFill style={{background:INK,color:WHITE,fontFamily:'Helvetica Neue, Arial',opacity}}>
  <div style={{position:'absolute',inset:0,backgroundImage:'linear-gradient(#15233266 1px,transparent 1px),linear-gradient(90deg,#15233266 1px,transparent 1px)',backgroundSize:'80px 80px',maskImage:'linear-gradient(to right,transparent,black)'}}/>
  <div style={{position:'absolute',top:80,left:100,color:GOLD,fontSize:24,letterSpacing:4}}>{String(project+1).padStart(2,'0')} / {item.name.toUpperCase()}</div>
  <div style={{position:'absolute',top:268,left:100,width:900,opacity:1-trans,transform:`translateY(${-trans*20}px)`}}>
   <div style={{fontFamily:'Georgia',fontSize:item.question.length>43?76:88,lineHeight:1.08,maxWidth:890,marginBottom:48}}>{item.question}</div>
   <div style={{fontSize:18,letterSpacing:4,color:BLUE,marginBottom:16}}>IDEA · CONDENSED PROMPT</div>
   <div style={{fontSize:34,lineHeight:1.45,color:'#d3d9de',maxWidth:800}}>“{item.prompt}”</div>
  </div>
  <div style={{position:'absolute',left:mix(trans,1110,600),top:mix(trans,220,150),transform:`scale(${mix(trans,1,1.08)})`}}><Geometry id={item.id} t={t} progress={progress}/></div>
  <div style={{position:'absolute',left:100,bottom:95,display:'flex',gap:24,alignItems:'center',opacity:trans}}>{item.steps.map((s,i)=><React.Fragment key={s}>{i>0&&<span style={{color:'#415368',fontSize:28}}>→</span>}<span style={{fontSize:32,color:t>4.05+i*.8?WHITE:'#506073'}}>{s}</span></React.Fragment>)}</div>
  <div style={{position:'absolute',right:90,bottom:55,color:'#6b8295',fontSize:18,letterSpacing:2}}>{isBuild?'BUILD VISUALIZATION':'LUCAS ACADEMY'}</div>
  <div style={{position:'absolute',left:100,right:100,bottom:30,height:2,background:'#243342'}}><div style={{width:`${t/7.2*100}%`,height:2,background:GOLD}}/></div>
 </AbsoluteFill>;
}
registerRoot(()=> <Composition id="CuriosityBuild" component={Film} width={1920} height={1080} fps={30} durationInFrames={216} defaultProps={{project:0,kind:'project'}} calculateMetadata={({props})=>({durationInFrames:props.kind==='opening'?90:props.kind==='ending'?540:216})}/>);
