import type {CSSProperties,FC,ReactNode} from 'react';
import {AbsoluteFill,Img,staticFile,useVideoConfig,type CalculateMetadataFunction} from 'remotion';

type Props={film:'perceptron'|'optogenetics';lang:'en'|'zh';values:Record<string,string|number>|null;pixels:number[]};
const C={cream:'#fff4d9',gold:'#ffcd72',mint:'#b5f0d7',ink:'#072723'};
const EN="'Avenir Next',Arial,sans-serif",ZH="'PingFang SC','Hiragino Sans GB',sans-serif";
const file=(name:string)=>staticFile(`science-shorts-20261105/cover/${name}`);
export const calculateCoverMetadata:CalculateMetadataFunction<Props>=async({props,abortSignal})=>{
 const response=await fetch(staticFile('science-shorts-20261105/data.json'),{signal:abortSignal});
 if(!response.ok)throw Error('Missing original-round cover data');
 const data=await response.json();return {props:{...props,values:data.values,pixels:data.pixels}};
};

const Copy:FC<{x:number;y:number;size:number;color?:string;children:ReactNode;style?:CSSProperties}>=({x,y,size,color=C.cream,children,style})=><div style={{position:'absolute',left:x,top:y,fontSize:size,fontWeight:800,lineHeight:1.12,letterSpacing:-1.4,color,textShadow:'0 4px 24px #001c17b0',whiteSpace:'nowrap',...style}}>{children}</div>;

function Seven({pixels,x,y,size}:{pixels:number[];x:number;y:number;size:number}){
 const n=Math.sqrt(pixels.length);if(n!==20)throw Error('Expected original 20×20 held-out picture');
 const path=pixels.map((p,i)=>p?`M${i%n*20+2} ${Math.floor(i/n)*20+2}h16v16h-16z`:'').join(' ');
 return <div style={{position:'absolute',left:x,top:y,width:size,height:size,border:'2px solid #f7d49a80',borderRadius:20,padding:18,boxSizing:'border-box',background:'#072b28e8',boxShadow:'0 15px 70px #001a14c0,inset 0 0 40px #c6e6d012',transform:'rotate(-4deg)'}}>
  <svg width="100%" height="100%" viewBox="0 0 400 400"><path d={path} fill={C.cream}/></svg>
 </div>;
}

function PerceptronCover({lang,values,pixels}:{lang:Props['lang'];values:NonNullable<Props['values']>;pixels:number[]}){
 const {width,height}=useVideoConfig();const portrait=height>width;
 const cn=lang==='zh',three=Number(values.claude_million_en),ten=Number(values.astra_ten_million_en);
 if(three<=0||ten<=0)throw Error('Cover numbers must come from the selected experiment');
 return <>
  <Img src={file('perceptron.png')} style={{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover',objectPosition:'57% 50%'}}/>
  <AbsoluteFill style={{background:portrait?'linear-gradient(180deg,#021d1bd9 0%,#03201eae 47%,#03201e08 74%,#021d1bb8 100%)':'linear-gradient(90deg,#021d1bed 0%,#021d1bc4 53%,#021d1b15 100%)'}}/>
  {portrait?<>
   {cn?<>
    <Copy x={76} y={155} size={54}>比 Claude Fable 5.1</Copy>
    <Copy x={66} y={238} size={158} color={C.gold}>快{three*100}万倍</Copy>
    <Copy x={76} y={487} size={54}>比 GPT-6-Astra</Copy>
    <Copy x={66} y={570} size={147} color={C.mint}>快{ten*100}万倍！</Copy>
   </>:<>
    <Copy x={74} y={155} size={134} color={C.gold}>{three} MILLION ×</Copy>
    <Copy x={80} y={324} size={39} color={C.gold}>FASTER THAN</Copy>
    <Copy x={76} y={383} size={61}>Claude Fable 5.1</Copy>
    <Copy x={74} y={552} size={119} color={C.mint}>{ten} MILLION ×</Copy>
    <Copy x={80} y={707} size={39} color={C.mint}>FASTER THAN</Copy>
    <Copy x={76} y={766} size={61}>GPT-6-Astra</Copy>
   </>}
   <Seven pixels={pixels} x={305} y={1120} size={485}/>
  </>:<>
   {cn?<>
    <Copy x={62} y={68} size={39}>比 Claude Fable 5.1</Copy>
    <Copy x={52} y={127} size={109} color={C.gold}>快{three*100}万倍</Copy>
    <Copy x={62} y={334} size={39}>比 GPT-6-Astra</Copy>
    <Copy x={52} y={393} size={101} color={C.mint}>快{ten*100}万倍！</Copy>
   </>:<>
    <Copy x={60} y={66} size={91} color={C.gold}>{three} MILLION ×</Copy>
    <Copy x={64} y={178} size={26} color={C.gold}>FASTER THAN</Copy>
    <Copy x={62} y={221} size={43}>Claude Fable 5.1</Copy>
    <Copy x={60} y={345} size={82} color={C.mint}>{ten} MILLION ×</Copy>
    <Copy x={64} y={451} size={26} color={C.mint}>FASTER THAN</Copy>
    <Copy x={62} y={494} size={43}>GPT-6-Astra</Copy>
   </>}
   <Seven pixels={pixels} x={858} y={278} size={306}/>
  </>}
 </>;
}

function OptogeneticsCover({lang}:{lang:Props['lang']}){
 const {width,height}=useVideoConfig();const portrait=height>width,cn=lang==='zh';
 return <>
  <AbsoluteFill style={{background:'#092a25'}}/>
  <Img src={file('optogenetics.png')} style={portrait?{position:'absolute',left:0,top:760,width:1080,height:608,objectFit:'contain'}:{position:'absolute',inset:0,width:'100%',height:'100%',objectFit:'cover'}}/>
  <AbsoluteFill style={{background:portrait?'linear-gradient(180deg,transparent 40%,#092a2500 49%,#092a2500 63%,#092a25 76%)':'linear-gradient(90deg,#082a25f8 0%,#082a25ea 38%,#082a2510 68%)'}}/>
  {portrait?<>
   {cn?<>
    <Copy x={78} y={165} size={94} color={C.gold}>1分钟了解</Copy>
    <Copy x={68} y={316} size={223} color={C.gold} style={{letterSpacing:-8}}>2026</Copy>
    <Copy x={75} y={597} size={132}>诺贝尔奖</Copy>
    <Copy x={82} y={1450} size={100} color={C.gold}>光遗传学</Copy>
    <Copy x={84} y={1580} size={43}>生理学或医学奖</Copy>
   </>:<>
    <Copy x={78} y={157} size={64} color={C.gold}>IN 1 MINUTE</Copy>
    <Copy x={68} y={278} size={223} color={C.gold} style={{letterSpacing:-8}}>2026</Copy>
    <Copy x={76} y={554} size={109}>NOBEL PRIZE</Copy>
    <Copy x={80} y={1450} size={83} color={C.gold}>Optogenetics</Copy>
    <Copy x={84} y={1570} size={36}>Physiology or Medicine</Copy>
   </>}
  </>:<>
   {cn?<>
    <Copy x={61} y={77} size={50} color={C.gold}>1分钟了解</Copy>
    <Copy x={54} y={157} size={153} color={C.gold} style={{letterSpacing:-5}}>2026</Copy>
    <Copy x={58} y={342} size={83}>诺贝尔奖</Copy>
    <Copy x={62} y={505} size={62} color={C.gold}>光遗传学</Copy>
    <Copy x={64} y={589} size={28}>生理学或医学奖</Copy>
   </>:<>
    <Copy x={60} y={67} size={38} color={C.gold}>IN 1 MINUTE</Copy>
    <Copy x={52} y={135} size={151} color={C.gold} style={{letterSpacing:-5}}>2026</Copy>
    <Copy x={58} y={323} size={69}>NOBEL PRIZE</Copy>
    <Copy x={61} y={507} size={47} color={C.gold}>Optogenetics</Copy>
    <Copy x={64} y={581} size={25}>Physiology or Medicine</Copy>
   </>}
  </>}
 </>;
}

export const ScienceShortCover:FC<Props>=({film,lang,values,pixels})=>{
 if(!values)throw Error('Load selected original-round metadata before rendering covers');
 return <AbsoluteFill style={{background:C.ink,fontFamily:lang==='zh'?ZH:EN,overflow:'hidden'}}>
  {film==='perceptron'?<PerceptronCover lang={lang} values={values} pixels={pixels}/>:<OptogeneticsCover lang={lang}/>}
 </AbsoluteFill>;
};
