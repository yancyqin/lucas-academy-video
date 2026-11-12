import {Composition,registerRoot} from 'remotion';
import {ScienceShort,calculateShortMetadata} from './videos/science-shorts/ScienceShorts';

const ShortsRoot=()=> <>
 <Composition id="PerceptronShort" component={ScienceShort} width={1080} height={1920} fps={30} durationInFrames={2700} defaultProps={{film:'perceptron' as const,tl:null,data:null}} calculateMetadata={calculateShortMetadata}/>
 <Composition id="OptogeneticsShort" component={ScienceShort} width={1080} height={1920} fps={30} durationInFrames={2700} defaultProps={{film:'optogenetics' as const,tl:null,data:null}} calculateMetadata={calculateShortMetadata}/>
</>;

registerRoot(ShortsRoot);
