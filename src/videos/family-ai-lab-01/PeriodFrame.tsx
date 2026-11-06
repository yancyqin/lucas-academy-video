import type {FC, ReactNode} from 'react';
import {AbsoluteFill, Img, interpolate, staticFile} from 'remotion';

export type PeriodSurface = 'instrument' | 'projection';

// Measured against the generated originals (1672 × 941). The authored lesson
// stays inside the glass/paper aperture; the brass and wood remain in front.
const PLATES = {
 instrument: {image:'instrument-screen-v3.png', x:130, y:67, width:1414, height:687, radius:43},
 projection: {image:'projection-screen-v3.png', x:158, y:65, width:1363, height:790, radius:13},
} as const;

/** A photographed period set, with moving light and a restrained optical finish. */
export const PeriodFrame:FC<{surface:PeriodSurface;frame:number;from:number;children:ReactNode;footage?:boolean}>=({surface,frame,from,children,footage=false})=>{
 const plate=PLATES[surface], sx=1920/1672, sy=1080/941;
 const x=plate.x*sx,y=plate.y*sy,width=plate.width*sx,height=plate.height*sy;
 const canvasHeight=footage?1080:930,scale=Math.min(width/1920,height/canvasHeight);
 const reveal=interpolate(frame-from,[0,9],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 const pulse=.15+.08*Math.sin(frame/43);
 return <AbsoluteFill data-period-set={surface} style={{background:'#1a2016'}}>
  <Img src={staticFile(`family-ai-lab-01/art/${plate.image}`)} style={{position:'absolute',inset:0,width:1920,height:1080}}/>
  <div style={{position:'absolute',left:x,top:y,width,height,borderRadius:plate.radius*sx,overflow:'hidden',isolation:'isolate'}}>
   <AbsoluteFill style={{background:footage?'#15251a':surface==='instrument'?'#e0dfb9':'#e8d3a7',opacity:surface==='projection'&&!footage?.3:1}}/>
   <div style={{position:'absolute',left:(width-1920*scale)/2,top:(height-canvasHeight*scale)/2,width:1920,height:canvasHeight,transform:`scale(${scale})`,transformOrigin:'top left',overflow:'hidden',opacity:reveal,color:'#23372b',filter:footage?'sepia(0.24) saturate(0.72)':'sepia(0.13) saturate(0.78)'}}>
    {children}
   </div>
   <AbsoluteFill style={{pointerEvents:'none',background:surface==='instrument'?'repeating-linear-gradient(0deg,#173b230c 0px,#173b230c 1px,transparent 1px,transparent 4px)':'linear-gradient(112deg,#f3d69a16,transparent 47%,#563e1510)',boxShadow:'inset 0 0 45px #251b1c3b',mixBlendMode:'multiply'}}/>
   <svg width="100%" height="100%" style={{position:'absolute',inset:0,opacity:.035,pointerEvents:'none',mixBlendMode:'multiply'}}>
    <filter id="period-grain"><feTurbulence type="fractalNoise" baseFrequency=".83" numOctaves={2} stitchTiles="stitch"/></filter>
    <rect width="100%" height="100%" filter="url(#period-grain)"/>
   </svg>
   <AbsoluteFill style={{pointerEvents:'none',background:'linear-gradient(135deg,#fff8c408,transparent 25%,transparent 75%,#fff8c406)'}}/>
  </div>
  {surface==='instrument'&&[657,1012].map(cx=><div key={cx} style={{position:'absolute',left:cx*sx-37,top:843*sy-37,width:74,height:74,borderRadius:'50%',background:'radial-gradient(circle,#ffce61,transparent 68%)',opacity:pulse,mixBlendMode:'screen'}}/>)}
 </AbsoluteFill>;
};
