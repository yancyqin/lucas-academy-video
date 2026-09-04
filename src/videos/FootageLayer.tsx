import React from 'react';
import {AbsoluteFill, Loop, OffthreadVideo, Sequence, interpolate, staticFile, useVideoConfig} from 'remotion';
import {clamp01, easeOut} from './lyrics-theme';

export type CameraMove = 'in' | 'out' | 'left' | 'right' | 'up';

export type Shot = {
  /** path under public/, e.g. "footage/sh09-underwater-loop.mp4" */
  src: string;
  /** seconds in the song */
  start: number;
  end: number;
  move?: CameraMove;
  /**
   * Source length. Wan clips are built as 12.2s boomerangs and loop invisibly;
   * real footage is not, so its shots are kept shorter than the clip instead.
   */
  loopSeconds?: number;
};

/** Shots overlap by this much, and the dissolve runs across the overlap. */
const DISSOLVE = 1.4;
/**
 * Every clip is built as a boomerang of the same length, so a shot can outrun its
 * source and simply loop -- the turnaround is where the motion already reverses,
 * and the seam is invisible.
 */
const CLIP_SECONDS = 12.2;

/**
 * The clips carry almost no subject motion -- the model does not produce it. So the
 * camera move lives here, which is also how the reference lyric videos work: slow
 * pushes and drifts over near-still plates.
 */
const transformFor = (move: CameraMove | undefined, p: number): string => {
  const k = easeOut(p);
  switch (move) {
    case 'out':   return `scale(${interpolate(k, [0, 1], [1.20, 1.04])})`;
    case 'left':  return `scale(1.16) translateX(${interpolate(k, [0, 1], [2.2, -2.2])}%)`;
    case 'right': return `scale(1.16) translateX(${interpolate(k, [0, 1], [-2.2, 2.2])}%)`;
    case 'up':    return `scale(1.16) translateY(${interpolate(k, [0, 1], [2.0, -2.0])}%)`;
    case 'in':
    default:      return `scale(${interpolate(k, [0, 1], [1.04, 1.20])})`;
  }
};

export const FootageLayer: React.FC<{shots: Shot[]; now: number; offset: number}> = ({
  shots, now, offset,
}) => {
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={styles.plate}>
      {shots.map((shot, i) => {
        const from = Math.round((shot.start - offset) * fps);
        const frames = Math.round((shot.end - shot.start) * fps);
        if (from + frames < 0) return null;
        const p = clamp01((now - shot.start) / (shot.end - shot.start));
        // Dissolve in and out; the first shot has nothing to dissolve from.
        const fadeIn = i === 0 ? 1 : easeOut((now - shot.start) / DISSOLVE);
        const fadeOut = easeOut((shot.end - now) / DISSOLVE);
        return (
          <Sequence key={i} from={Math.max(0, from)} durationInFrames={frames + Math.round(DISSOLVE * fps)}>
            <AbsoluteFill style={{opacity: Math.min(fadeIn, fadeOut)}}>
              <Loop durationInFrames={Math.round((shot.loopSeconds ?? CLIP_SECONDS) * fps)}>
                <OffthreadVideo
                  src={staticFile(shot.src)}
                  muted
                  style={{...styles.video, transform: transformFor(shot.move, p)}}
                />
              </Loop>
            </AbsoluteFill>
          </Sequence>
        );
      })}
      <Grade />
    </AbsoluteFill>
  );
};

/**
 * One grade over everything. Clips come from different sources -- a local diffusion
 * model at 832x480 and 4K stock -- and this layer is what makes them read as one film.
 */
const Grade: React.FC = () => (
  <>
    <AbsoluteFill style={styles.shadowTint} />
    <AbsoluteFill style={styles.highlightTint} />
    <AbsoluteFill style={styles.lift} />
    <AbsoluteFill style={styles.vignette} />
  </>
);

const styles: Record<string, React.CSSProperties> = {
  plate: {overflow: 'hidden', background: '#05070a'},
  video: {
    width: '100%', height: '100%', objectFit: 'cover',
    // Pull saturation back before the tint goes on, so the tint is what colours it.
    filter: 'saturate(.82) contrast(1.07) brightness(.94)',
  },
  shadowTint: {
    background: 'linear-gradient(180deg, rgba(28,52,74,.34), rgba(20,34,52,.20))',
    mixBlendMode: 'soft-light', pointerEvents: 'none',
  },
  highlightTint: {
    background: 'radial-gradient(ellipse at 52% 40%, rgba(255,196,120,.26), rgba(255,170,80,0) 62%)',
    mixBlendMode: 'soft-light', pointerEvents: 'none',
  },
  // Lifted blacks -- nothing in the frame reaches pure black, which is what reads
  // as film rather than as a screenshot.
  lift: {background: 'rgba(38,44,58,.13)', mixBlendMode: 'screen', pointerEvents: 'none'},
  vignette: {
    background: 'radial-gradient(ellipse at 50% 46%, rgba(0,0,0,0) 40%, rgba(0,0,0,.62) 100%)',
    pointerEvents: 'none',
  },
};
