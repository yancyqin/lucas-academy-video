import React from 'react';
import {AbsoluteFill, Composition, registerRoot, useCurrentFrame, interpolate, Easing, OffthreadVideo, Img, staticFile} from 'remotion';
import plan from '../../../scripts/curiosity-builds-v10/plan.json';

const INK='#080e19', WHITE='#f5f1e6', GOLD='#f5bc68', BLUE='#70d7e8';
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
const mix=(x:number,a:number,b:number)=>interpolate(x,[0,1],[a,b],clamp);
function Geometry({id,t,progress}:{id:string;t:number;progress:number}){
 if(id==='cube'){const enter=interpolate(t,[0,.8],[0,1],clamp);return <div style={{width:720,height:720,opacity:enter,transform:`translateY(${(1-enter)*16}px) scale(${.94+progress*.06})`}}><Img src={staticFile('cube-draft.png')} style={{width:'100%',height:'100%',objectFit:'contain',maskImage:'radial-gradient(ellipse at center, #000 75%, transparent 95%)'}}/></div>;}
 if(id==='vangogh'||id==='journey'){return <div style={{width:900,height:720,transform:`scale(${.97+progress*.03})`}}><Img src={staticFile(id+'-gallery-concept.png')} style={{width:'100%',height:'100%',objectFit:'contain',maskImage:'radial-gradient(ellipse at center, #000 87%, transparent 100%)'}}/></div>;}
 const P=(x:number,y:number,z:number)=>{const a=t*.12-.5;const X=x*Math.cos(a)+z*Math.sin(a),Z=-x*Math.sin(a)+z*Math.cos(a);return [X*1.05, y*.9+Z*.35]};
 const line=(pts:number[][])=>pts.map((p,i)=>`${i?'L':'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
 let content:React.ReactNode;
 if(id==='roller'){
  const path=line(Array.from({length:440},(_,i)=>{const u=i/439*7*Math.PI;const r=250*(1-i/520);return P(Math.cos(u)*r, -210+i/439*390,Math.sin(u)*r)}));
  content=<><path d={path} stroke={BLUE} strokeWidth="1.5" opacity=".25"/><path d={path} stroke={BLUE} strokeWidth="9" pathLength="1" strokeDasharray="1" strokeDashoffset={1-progress}/>{Array.from({length:16},(_,i)=><path key={i} d={line([P(-280,-220+i*30,0),P(280,-220+i*30,0)])} stroke={BLUE} opacity=".09"/>)}</>;
 }else if(id==='chess'){
  content=<>{Array.from({length:64},(_,i)=>{const x=i%8,y=Math.floor(i/8),cx=(x-y)*39,cy=(x+y)*21-150;return <path key={i} d={`M${cx},${cy}l39,21 -39,21 -39,-21Z`} fill={(x+y)%2?'#123245':'#314f57'} stroke={BLUE} strokeWidth="1" opacity={Math.min(1,progress*3-i/64)}/>})}{Array.from({length:8},(_,i)=><g key={i} transform={`translate(${(i-6)*39},${(i+6)*21-166})`} opacity={mix(progress,.1,1)}><ellipse cy="24" rx="15" ry="7" fill={GOLD}/><path d="M-12,20 L-7,-3 Q-15,-15 0,-20 Q15,-15 7,-3 L12,20Z" fill={GOLD}/></g>)}</>;
 }else if(id==='sky'){
  content=<>{Array.from({length:65},(_,i)=>{const a=i*2.399,r=35+Math.sqrt(i)*33;return <circle key={i} cx={Math.cos(a)*r} cy={Math.sin(a)*r*.7} r={i%7?2:5} fill={i%3?BLUE:GOLD} opacity={Math.max(0,progress*2-i/65)} />})}{Array.from({length:9},(_,i)=><ellipse key={i} cy={150+i*12} rx={270-i*14} ry={32+i*2} stroke={BLUE} strokeWidth="1" opacity=".3" />)}<ellipse rx="290" ry="220" stroke={BLUE} opacity=".16"/></>;
 }else if(id==='chameleon'){
  content=<><path d="M-120,35 Q-180,-110 -50,-100 Q40,-130 100,-60 L182,-40 130,10 Q40,50 -100,45 Q-190,170 -230,95 Q-260,10 -170,0 Q-100,10 -155,60" fill="#183947" stroke={GOLD} strokeWidth="7" pathLength="1" strokeDasharray="1" strokeDashoffset={1-progress}/><circle cx="115" cy="-45" r="13" fill={BLUE}/>{Array.from({length:25},(_,i)=><path key={i} d={`M${-130+(i%7)*45},${-150+Math.floor(i/7)*70}q25,-24 50,0`} stroke={i%2?BLUE:GOLD} opacity={.12+progress*.3} strokeWidth="13"/>)}</>;
 }else if(id==='coder'){
  content=<>{Array.from({length:12},(_,i)=><path key={i} d={`M-270,${-225+i*43}H270 M${-250+i*43},-230V250`} stroke={BLUE} opacity=".16"/>)}<path d="M-230,180H-100V40H50V-100H230" stroke={GOLD} strokeWidth="30" strokeLinejoin="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1-progress}/><circle cx="230" cy="-180" r="14" fill={BLUE}/></>;
 }else{
  const words=['Your','word','is','a','lamp','to','my','feet.'];
  content=<>{words.map((w,i)=>{const x=(i%3-1)*185,y=(Math.floor(i/3)-1)*100;return <g key={w+i} transform={`translate(${x+Math.sin(i*4)*100*(1-progress)},${y+Math.cos(i*3)*160*(1-progress)})`}><rect x="-84" y="-37" width="168" height="74" rx="10" fill="#17303b" stroke={i<progress*8?GOLD:BLUE} strokeWidth="2"/><text y="10" fill={WHITE} fontSize="48" textAnchor="middle" fontFamily="Georgia">{w}</text></g>})}</>;
 }
 return <svg width="720" height="720" viewBox="-360 -360 720 720" fill="none">{content}</svg>;
}
function Background(){return <><OffthreadVideo src={staticFile('jesus-background.mp4')} muted style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',opacity:.42}}/><AbsoluteFill style={{background:'rgba(8,14,25,.56)'}}/></>}
function Film({project=0,kind='project'}:{project?:number;kind?:string}){
 const f=useCurrentFrame(),t=f/30,item=plan.projects[project];
 if(kind==='ending'){
  const i=Math.min(2,Math.floor(t/6)),local=t-i*6;
  const a=interpolate(local,[0,.65,5.45,6],[0,1,1,0],clamp);
  return <AbsoluteFill style={{background:INK,color:WHITE,justifyContent:'center',alignItems:'center',padding:'110px 140px'}}>
   <Background/>
   <div style={{position:'relative',fontFamily:'Georgia',fontSize:118,lineHeight:1.18,textAlign:'center',maxWidth:1650,opacity:a,transform:`translateY(${(1-a)*12}px)`}}>{plan.ending_questions[i]}</div>
  </AbsoluteFill>;
 }
 const titleAlpha=interpolate(f,[0,14,75,90],[0,1,1,0],clamp);
 const titleZoom=interpolate(f,[30,54],[0,1],{...clamp,easing:Easing.inOut(Easing.cubic)});
 const promptAlpha=interpolate(f,[96,110,202,216],[0,1,1,0],clamp);
 const drawingAlpha=interpolate(f,[42,60],[0,1],clamp);
 const progress=interpolate(f,[0,75,96,210],[.5,.5,.5,1],clamp);
 const gallery=item.id==='vangogh'||item.id==='journey';
 const previewAlpha=item.id==='journey'?interpolate(f,[96,112],[0,1],clamp):0;
 // Native sweet-home-v3-model-only.mp4 frames: all 105 source frames across 120 output frames.
 const modelFrame=Math.min(105,1+Math.floor(Math.max(0,f-96)*.875));
 return <AbsoluteFill style={{background:INK,color:WHITE,fontFamily:'Helvetica Neue, Arial'}}>
  <Background/>
  <div data-title-motion="standalone-to-layout" data-intro-layout="title-and-illustration" style={{position:'absolute',top:mix(titleZoom,320,300),left:mix(titleZoom,339,100),width:900,transform:`scale(${mix(titleZoom,1.38,1)})`,transformOrigin:'top left',opacity:titleAlpha}}>
   <div style={{fontFamily:'Georgia',fontSize:item.question.length>43?86:100,lineHeight:1.12,maxWidth:890}}>{item.question}</div>
  </div>
  <div data-process-prompt="after-title" style={{position:'absolute',top:370,left:100,width:830,fontSize:48,lineHeight:1.36,color:'#dce4eb',opacity:promptAlpha}}>“{item.prompt}”</div>
  <div data-process-picture="fixed-right" style={{position:'absolute',left:gallery?940:1110,top:220,width:gallery?900:720,height:720,opacity:drawingAlpha}}>
   <div style={{opacity:1-previewAlpha}}><Geometry id={item.id} t={t} progress={progress}/></div>
   {item.id==='journey'&&f>=96&&<Img src={staticFile('sweet-home-model-frames/frame-'+String(modelFrame).padStart(3,'0')+'.jpg')} style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'contain',opacity:previewAlpha}}/>}
  </div>
 </AbsoluteFill>;
}
registerRoot(()=> <Composition id="CuriosityBuild" component={Film} width={1920} height={1080} fps={30} durationInFrames={216} defaultProps={{project:0,kind:'project'}} calculateMetadata={({props})=>({durationInFrames:props.kind==='ending'?540:216})}/>);
