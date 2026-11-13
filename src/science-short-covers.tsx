import {Composition,registerRoot} from 'remotion';
import {ScienceShortCover,calculateCoverMetadata} from './videos/science-shorts/ScienceShortCover';

const defaults={film:'perceptron' as const,lang:'en' as const,values:null,pixels:[]};
const CoverRoot=()=> <>
 <Composition id="ShortCoverPortrait" component={ScienceShortCover} width={1080} height={1920} durationInFrames={1} fps={30} defaultProps={defaults} calculateMetadata={calculateCoverMetadata}/>
 <Composition id="ShortCoverLandscape" component={ScienceShortCover} width={1280} height={720} durationInFrames={1} fps={30} defaultProps={defaults} calculateMetadata={calculateCoverMetadata}/>
</>;
registerRoot(CoverRoot);
