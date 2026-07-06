import {Composition} from 'remotion';
import type {FC} from 'react';
import {MonkeySocietyVideo} from './MonkeySocietyVideo';

export const Root: FC = () => {
  return (
    <Composition
      id="MonkeySociety"
      component={MonkeySocietyVideo}
      durationInFrames={432}
      fps={24}
      width={1920}
      height={1080}
    />
  );
};
