import {Composition} from 'remotion';
import type {FC} from 'react';
import {MonkeySocietyVideo} from './MonkeySocietyVideo';
import {MonkeyIntroVideo} from './videos/MonkeyIntroVideo';
import {
  ROLLER_COASTER_CHAT_DURATION,
  ROLLER_COASTER_CHAT_FPS,
  RollerCoasterChatVideo,
} from './videos/RollerCoasterChatVideo';
import introScript from './scripts/intro.en.json';
import {makeLyricsVideo, type Song} from './videos/LyricsVideo';
import oneBreath from './songs/one-breath.json';
import rejoice from './songs/rejoice.json';
import {
  ROLLER_COASTER_M2_DURATION,
  ROLLER_COASTER_M2_FPS,
  RollerCoasterMilestone2Video,
} from './videos/RollerCoasterMilestone2Video';
import {
  ROLLER_COASTER_SHORT_DURATION,
  ROLLER_COASTER_SHORT_FPS,
  RollerCoasterMilestonesShortVideo,
} from './videos/RollerCoasterMilestonesShortVideo';
import {
  ROLLER_COASTER_M3_BUILD_DURATION,
  ROLLER_COASTER_M3_BUILD_FPS,
  RollerCoasterMilestone3BuildVideo,
} from './videos/RollerCoasterMilestone3BuildVideo';
import {
  ROLLER_COASTER_M3_BUILD_VERTICAL_DURATION,
  ROLLER_COASTER_M3_BUILD_VERTICAL_FPS,
  RollerCoasterMilestone3BuildVerticalVideo,
} from './videos/RollerCoasterMilestone3BuildVerticalVideo';

const OneBreathVideo = makeLyricsVideo(oneBreath as Song);
const CHORUS_FROM = 84;
const CHORUS_SECONDS = 46;
const OneBreathChorus = makeLyricsVideo(oneBreath as Song, {offsetSeconds: CHORUS_FROM});

const RejoiceVideo = makeLyricsVideo(rejoice as Song);
/** Three cuts of the same film: lyrics low, lyrics centred, and pictures alone. */
const RejoiceCenter = makeLyricsVideo(rejoice as Song, {anchor: 'center'});
const RejoiceClean = makeLyricsVideo(rejoice as Song, {hideLyrics: true});
/** The cross section into the first chorus -- the part with the most to get wrong. */
const REJOICE_WINDOW_FROM = 41;
const REJOICE_WINDOW_SECONDS = 62;
const RejoiceWindow = makeLyricsVideo(rejoice as Song, {offsetSeconds: REJOICE_WINDOW_FROM});
/** The nail -> cross -> three crosses -> milky way run, on stills and stock only. */
const REJOICE_CROSS_FROM = 30;
const REJOICE_CROSS_SECONDS = 18;
const RejoiceCross = makeLyricsVideo(rejoice as Song, {offsetSeconds: REJOICE_CROSS_FROM});
/** First chorus: the silhouette, the clouds, the bubbles and the (Rejoice) echo. */
const REJOICE_C1_FROM = 66;
const REJOICE_C1_SECONDS = 38;
const RejoiceChorus1 = makeLyricsVideo(rejoice as Song, {offsetSeconds: REJOICE_C1_FROM});
/** A movable window for checking one stretch without paying for the whole film. */
const REJOICE_PROBE_FROM = 140;
const REJOICE_PROBE_SECONDS = 28;
// Centred, to match the version being delivered -- a probe is only useful for
// confirming a change if it is cut the same way as the film it stands in for.
const RejoiceProbe = makeLyricsVideo(rejoice as Song, {
  offsetSeconds: REJOICE_PROBE_FROM,
  anchor: 'center',
});
/** The last chorus: the only place the golden-light clip appears. */
const REJOICE_FINALE_FROM = 250;
const REJOICE_FINALE_SECONDS = 57;
const RejoiceFinale = makeLyricsVideo(rejoice as Song, {offsetSeconds: REJOICE_FINALE_FROM});

export const Root: FC = () => {
  return (
    <>
      <Composition
        id="Rejoice"
        component={RejoiceVideo}
        durationInFrames={Math.ceil(rejoice.durationSeconds * rejoice.fps)}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceCenter"
        component={RejoiceCenter}
        durationInFrames={Math.ceil(rejoice.durationSeconds * rejoice.fps)}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceClean"
        component={RejoiceClean}
        durationInFrames={Math.ceil(rejoice.durationSeconds * rejoice.fps)}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceWindow"
        component={RejoiceWindow}
        durationInFrames={REJOICE_WINDOW_SECONDS * rejoice.fps}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceCross"
        component={RejoiceCross}
        durationInFrames={REJOICE_CROSS_SECONDS * rejoice.fps}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceChorus1"
        component={RejoiceChorus1}
        durationInFrames={REJOICE_C1_SECONDS * rejoice.fps}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceProbe"
        component={RejoiceProbe}
        durationInFrames={REJOICE_PROBE_SECONDS * rejoice.fps}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RejoiceFinale"
        component={RejoiceFinale}
        durationInFrames={REJOICE_FINALE_SECONDS * rejoice.fps}
        fps={rejoice.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="OneBreathChorus"
        component={OneBreathChorus}
        durationInFrames={CHORUS_SECONDS * oneBreath.fps}
        fps={oneBreath.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="OneBreath"
        component={OneBreathVideo}
        durationInFrames={Math.ceil(oneBreath.durationSeconds * oneBreath.fps)}
        fps={oneBreath.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="RollerCoasterMilestone1"
        component={RollerCoasterChatVideo}
        durationInFrames={ROLLER_COASTER_CHAT_DURATION}
        fps={ROLLER_COASTER_CHAT_FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="RollerCoasterMilestone2"
        component={RollerCoasterMilestone2Video}
        durationInFrames={ROLLER_COASTER_M2_DURATION}
        fps={ROLLER_COASTER_M2_FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="RollerCoasterMilestonesShort"
        component={RollerCoasterMilestonesShortVideo}
        durationInFrames={ROLLER_COASTER_SHORT_DURATION}
        fps={ROLLER_COASTER_SHORT_FPS}
        width={1080}
        height={1920}
      />
      <Composition
        id="RollerCoasterMilestone3Build"
        component={RollerCoasterMilestone3BuildVideo}
        durationInFrames={ROLLER_COASTER_M3_BUILD_DURATION}
        fps={ROLLER_COASTER_M3_BUILD_FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="RollerCoasterMilestone3BuildVertical"
        component={RollerCoasterMilestone3BuildVerticalVideo}
        durationInFrames={ROLLER_COASTER_M3_BUILD_VERTICAL_DURATION}
        fps={ROLLER_COASTER_M3_BUILD_VERTICAL_FPS}
        width={1080}
        height={1920}
      />
      <Composition
        id="MonkeyIntro"
        component={MonkeyIntroVideo}
        durationInFrames={introScript.durationSeconds * introScript.fps}
        fps={introScript.fps}
        width={1920}
        height={1080}
      />
      <Composition
        id="MonkeySociety"
        component={MonkeySocietyVideo}
        durationInFrames={432}
        fps={24}
        width={1920}
        height={1080}
      />
    </>
  );
};
