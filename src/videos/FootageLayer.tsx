import React from 'react';
import {AbsoluteFill, Loop, OffthreadVideo, Sequence, interpolate, staticFile, useVideoConfig} from 'remotion';
import {clamp01, easeOut} from './lyrics-theme';

export type CameraMove = 'in' | 'out' | 'left' | 'right' | 'up' | 'none';

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
  /**
   * Whether the clip may wrap when the shot outruns it.
   *
   * Off unless asked for. Looping only hides itself on a boomerang clip, where the
   * turnaround is already a reversal -- and a reversal is exactly what a song about
   * moving from shadow into light cannot have, because the light would drain back
   * out. Rejoice therefore pre-renders every shot to its own length and leaves this
   * alone; One Breath's shots pass loopSeconds and keep the old behaviour.
   */
  loop?: boolean;
  /** Overrides the camera move's zoom range, for shots that need a restrained one. */
  zoom?: number[];
  /**
   * Ramps the shot from cool shadow into full golden light across its length.
   *
   * The plan wants the last chorus to be the world slowly filling with light, and
   * the model will not do it: these clips carry almost no subject motion, so the
   * development has to be graded on rather than generated. Forward only -- the
   * ramp never returns to shadow, which is the whole point of the shot.
   */
  lightRamp?: boolean;
  /**
   * Defocus that eases off across the shot, as [from%, to%].
   *
   * The face is the film's "we could not understand": it starts behind a heavy
   * blur and resolves as the song moves toward being fully known. Given as a ramp
   * rather than a fixed value per shot so the change reads as one continuous pull
   * into focus instead of a stack of discrete steps.
   */
  blurRamp?: number[];
  /**
   * Opacity ramp at the head of the shot, as [starting opacity, seconds].
   *
   * Not the same as fading up from black: the image is on screen from the first
   * frame, only very transparent, so the nebula is faintly there before it firms up.
   */
  fadeIn?: number[];
  /**
   * Seconds of opacity fade to nothing at the tail of the shot. The picture keeps
   * moving while it goes -- it dissolves away rather than being cut away.
   */
  fadeOut?: number;
  /**
   * Pulls back over the last `seconds` of the shot, continuing from wherever the
   * shot's own move had reached.
   *
   * For a clip that finishes before its slot does: rather than freezing on the
   * final frame -- which reads as a stall next to shots that are all still
   * drifting -- the frame stays and the camera keeps easing back off it.
   */
  tailZoom?: {seconds: number; to: number};
  /**
   * Overrides the song's crossfade length for this shot's own dissolve.
   *
   * The crossfade is as long as DISSOLVE, not as long as the overlap, so making a
   * single transition softer than the rest takes saying so here -- the galaxy
   * easing into the crosses wants a longer one than a cut between two skies.
   */
  dissolve?: number;
};

/**
 * Shots overlap by this much, and the dissolve runs across the overlap.
 *
 * A dissolve longer than the overlap starts fading a shot out before its
 * successor is fully in, so it has to be given per song rather than fixed: One
 * Breath overlaps its shots generously, Rejoice cuts 30 shots to measured lyric
 * timings and overlaps them by 0.6s.
 */
const DEFAULT_DISSOLVE = 1.4;
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
const transformFor = (
  move: CameraMove | undefined,
  p: number,
  zoom?: number[],
): string => {
  const k = easeOut(p);
  if (zoom && zoom.length === 2) return `scale(${interpolate(k, [0, 1], zoom)})`;
  switch (move) {
    // 'none' is for shots that already carry their movement, such as a still whose
    // push was rendered at twice the frame size -- scaling it again here would only
    // soften what was sharpened on purpose.
    case 'none':  return 'scale(1)';
    case 'out':   return `scale(${interpolate(k, [0, 1], [1.20, 1.04])})`;
    case 'left':  return `scale(1.16) translateX(${interpolate(k, [0, 1], [2.2, -2.2])}%)`;
    case 'right': return `scale(1.16) translateX(${interpolate(k, [0, 1], [-2.2, 2.2])}%)`;
    case 'up':    return `scale(1.16) translateY(${interpolate(k, [0, 1], [2.0, -2.0])}%)`;
    case 'in':
    default:      return `scale(${interpolate(k, [0, 1], [1.04, 1.20])})`;
  }
};

export const FootageLayer: React.FC<{
  shots: Shot[];
  now: number;
  offset: number;
  dissolveSeconds?: number;
}> = ({shots, now, offset, dissolveSeconds}) => {
  const {fps} = useVideoConfig();
  const DISSOLVE = dissolveSeconds ?? DEFAULT_DISSOLVE;
  return (
    <AbsoluteFill style={styles.plate}>
      {shots.map((shot, i) => {
        const from = Math.round((shot.start - offset) * fps);
        const frames = Math.round((shot.end - shot.start) * fps);
        if (from + frames < 0) return null;
        const p = clamp01((now - shot.start) / (shot.end - shot.start));
        // Dissolve in and out; the first shot has nothing to dissolve from.
        const d = shot.dissolve ?? DISSOLVE;
        const dNext = shots[i + 1]?.dissolve ?? DISSOLVE;
        // A long crossfade has to be linear on both sides or it is not a
        // crossfade: eased in, the incoming shot is already 87% opaque at the
        // midpoint and the outgoing one is invisible long before it should be.
        const curve = (v: number, len: number) => (len > 2 ? clamp01(v) : easeOut(v));
        const openRamp = shot.fadeIn?.length === 2
          ? interpolate(now - shot.start, [0, shot.fadeIn[1]], [shot.fadeIn[0], 1],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
          : 1;
        const closeRamp = shot.fadeOut
          ? interpolate(now, [shot.end - shot.fadeOut, shot.end], [1, 0],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
          : 1;
        const fadeIn = (i === 0 ? 1 : curve((now - shot.start) / d, d)) * openRamp * closeRamp;
        const fadeOut = curve((shot.end - now) / dNext, dNext);
        const k = easeOut(p);
        // 100% maps to 26px, which is heavy enough to hide the features but still
        // reads as a face rather than a smudge.
        const blur = shot.blurRamp?.length === 2
          ? `blur(${(interpolate(k, [0, 1], shot.blurRamp) / 100 * 26).toFixed(2)}px)`
          : '';
        const ramp = shot.lightRamp
          ? {
              filter:
                `saturate(${interpolate(k, [0, 1], [0.52, 1.08])}) ` +
                `contrast(${interpolate(k, [0, 1], [1.12, 1.04])}) ` +
                `brightness(${interpolate(k, [0, 1], [0.66, 1.08])}) ` +
                `hue-rotate(${interpolate(k, [0, 1], [-10, 10])}deg)`,
            }
          : undefined;
        // Where the shot's own move has reached when the pull-back takes over, so
        // the two join without a jump.
        let transform = transformFor(shot.move, p, shot.zoom);
        const tz = shot.tailZoom;
        if (tz && now >= shot.end - tz.seconds) {
          const tStart = shot.end - tz.seconds;
          const pAt = clamp01((tStart - shot.start) / (shot.end - shot.start));
          const from = shot.zoom && shot.zoom.length === 2
            ? interpolate(easeOut(pAt), [0, 1], shot.zoom)
            : shot.move === 'out'
              ? interpolate(easeOut(pAt), [0, 1], [1.20, 1.04])
              : interpolate(easeOut(pAt), [0, 1], [1.04, 1.20]);
          // Linear: the point is a constant rate that matches the push-in, and
          // an eased tail would spend most of its travel in the first second.
          const k = clamp01((now - tStart) / tz.seconds);
          transform = `scale(${interpolate(k, [0, 1], [from, tz.to])})`;
        }
        const video = (
          <OffthreadVideo
            src={staticFile(shot.src)}
            muted
            style={{
              ...styles.video,
              ...ramp,
              filter: [ramp?.filter ?? styles.video.filter, blur].filter(Boolean).join(' '),
              // Blurring samples past the frame edge, so scale up a touch to keep
              // the softened border outside the picture.
              transform: `${transform}${shot.blurRamp?.length ? ' scale(1.06)' : ''}`,
            }}
          />
        );
        // Legacy shots signalled looping by carrying a source length; new ones have
        // to ask for it, so a clip is never silently wrapped back to its first frame.
        const wraps = shot.loop ?? shot.loopSeconds !== undefined;
        return (
          <Sequence key={i} from={Math.max(0, from)} durationInFrames={frames + Math.round(DISSOLVE * fps)}>
            <AbsoluteFill style={{opacity: Math.min(fadeIn, fadeOut)}}>
              {wraps ? (
                <Loop durationInFrames={Math.round((shot.loopSeconds ?? CLIP_SECONDS) * fps)}>
                  {video}
                </Loop>
              ) : (
                video
              )}
              {shot.lightRamp ? (
                <>
                  <AbsoluteFill
                    style={{
                      background:
                        'radial-gradient(ellipse at 50% 62%, rgba(255,196,104,.92), rgba(255,150,52,.34) 46%, rgba(255,120,30,0) 74%)',
                      mixBlendMode: 'soft-light',
                      opacity: interpolate(k, [0, 1], [0.05, 0.95]),
                      pointerEvents: 'none',
                    }}
                  />
                  <AbsoluteFill
                    style={{
                      background:
                        'linear-gradient(180deg, rgba(255,214,140,.30), rgba(255,176,74,.10) 52%, rgba(30,48,78,.28))',
                      mixBlendMode: 'screen',
                      opacity: interpolate(k, [0, 1], [0.12, 0.62]),
                      pointerEvents: 'none',
                    }}
                  />
                </>
              ) : null}
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
