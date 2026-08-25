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

export const Root: FC = () => {
  return (
    <>
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
