import React from 'react';
import {
  AbsoluteFill,
  Audio,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {PALETTES, easeOut, type LyricSection, type Palette} from './lyrics-theme';
import {FootageLayer, type Shot} from './FootageLayer';

export type LyricLine = {t: number; section: LyricSection; text: string};

export type Song = {
  title: string;
  subtitle?: string;
  audio: string;
  fps: number;
  durationSeconds: number;
  lines: LyricLine[];
  shots?: Shot[];
};

/**
 * A line holds until the next one starts, but never longer than this -- otherwise
 * the last line of a section would hang across an instrumental break.
 *
 * 6.5s was too short: the chorus leaves 8.8-9.5s between "You and me -- together,
 * one breath" and "Not dust, not grass", so the line vanished two to three seconds
 * before the next arrived, in all three choruses. 10s covers every sung gap and
 * still clears for the real instrumental breaks (the 12.6s verse gap and the 17s
 * guitar solo).
 */
const MAX_HOLD = 10.0;

/**
 * `offsetSeconds` renders a window out of the middle of the song, audio included, so
 * a section can be judged without paying for a five-minute render.
 */
export const makeLyricsVideo = (
  song: Song,
  opts: {offsetSeconds?: number} = {},
): React.FC => {
  const lines = song.lines;
  const shots = song.shots ?? [];
  const offset = opts.offsetSeconds ?? 0;

  const LyricsVideo: React.FC = () => {
    const frame = useCurrentFrame();
    const {fps, durationInFrames} = useVideoConfig();
    const now = offset + frame / fps;

    let index = -1;
    for (let i = 0; i < lines.length; i += 1) {
      if (lines[i].t <= now) index = i;
      else break;
    }

    const current = index >= 0 ? lines[index] : undefined;
    const next = lines[index + 1];
    const previous = index > 0 ? lines[index - 1] : undefined;

    const holdUntil = current
      ? Math.min(current.t + MAX_HOLD, next ? next.t : current.t + MAX_HOLD)
      : 0;
    const singing = Boolean(current) && now < holdUntil;
    const gapToNext = next ? next.t - now : Infinity;

    const section: LyricSection = current?.section ?? 'verse';
    const palette = PALETTES[section];

    const lineIn = current ? easeOut((now - current.t) / 0.55) : 0;
    const lineOut = current ? easeOut((holdUntil - now) / 0.5) : 0;
    const lineOpacity = singing ? Math.min(lineIn, lineOut) : 0;

    const openTitle = offset > 0 ? 0 : interpolate(now, [0.8, 2.6, 11.5, 14], [0, 1, 1, 0], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    });
    const edgeFade = Math.min(
      interpolate(frame, [0, fps * 1.2], [0, 1], {extrapolateRight: 'clamp'}),
      interpolate(frame, [durationInFrames - fps * 1.6, durationInFrames - 1], [1, 0],
        {extrapolateLeft: 'clamp'}),
    );

    return (
      <AbsoluteFill style={{...styles.canvas, background: palette.base, opacity: edgeFade}}>
        <Audio src={staticFile(song.audio)} startFrom={Math.round(offset * fps)} />

        {shots.length ? (
          <FootageLayer shots={shots} now={now} offset={offset} />
        ) : (
          <>
            <Backdrop palette={palette} now={now} />
            <AbsoluteFill style={styles.vignette} />
          </>
        )}

        {openTitle > 0.01 ? (
          <AbsoluteFill style={{...styles.stage, opacity: openTitle}}>
            <div style={styles.title}>{song.title}</div>
            {song.subtitle ? <div style={styles.subtitle}>{song.subtitle}</div> : null}
          </AbsoluteFill>
        ) : null}

        <AbsoluteFill style={styles.stage}>
          <div style={styles.rail}>
            <div style={{...styles.neighbour, opacity: singing && previous ? 0.2 : 0}}>
              {previous?.text ?? ''}
            </div>

            <div
              style={{
                ...styles.line,
                color: palette.ink,
                fontSize: palette.size,
                fontWeight: palette.weight,
                letterSpacing: palette.tracking,
                opacity: lineOpacity,
                transform: `translateY(${interpolate(lineIn, [0, 1], [22, 0])}px)`,
                // Over footage a glow fights the picture; a dark drop is what keeps
                // the text legible against a bright frame.
                textShadow: shots.length
                  ? '0 2px 44px rgba(0,0,0,.9), 0 0 14px rgba(0,0,0,.7)'
                  : section === 'chorus'
                    ? '0 0 70px rgba(255,186,96,.5), 0 0 26px rgba(255,214,150,.34)'
                    : '0 0 46px rgba(0,0,0,.65)',
              }}
            >
              {current?.text ?? ''}
            </div>

            <div style={{...styles.neighbour, opacity: singing && next && gapToNext < 9 ? 0.16 : 0}}>
              {next?.text ?? ''}
            </div>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  };

  return LyricsVideo;
};

/** Fallback plate for songs with no footage: two slow-orbiting glows. */
const Backdrop: React.FC<{palette: Palette; now: number}> = ({palette, now}) => {
  const drift = now * 0.055;
  return (
    <AbsoluteFill>
      <div style={{...styles.orb,
        left: 470 + Math.sin(drift) * 240, top: 210 + Math.cos(drift * 0.8) * 150,
        background: `radial-gradient(circle, ${palette.glow}, rgba(0,0,0,0) 68%)`}} />
      <div style={{...styles.orb, width: 1500, height: 1500,
        left: 1010 + Math.cos(drift * 0.6) * 260, top: 400 + Math.sin(drift * 1.1) * 180,
        background: `radial-gradient(circle, ${palette.glowAlt}, rgba(0,0,0,0) 70%)`}} />
    </AbsoluteFill>
  );
};

const font = '"Avenir Next", Inter, "Helvetica Neue", Arial, sans-serif';

const styles: Record<string, React.CSSProperties> = {
  canvas: {fontFamily: font, overflow: 'hidden'},
  stage: {alignItems: 'center', justifyContent: 'center', display: 'flex'},
  rail: {width: 1500, textAlign: 'center'},
  line: {lineHeight: 1.18, minHeight: 130, display: 'flex', alignItems: 'center', justifyContent: 'center'},
  neighbour: {
    color: '#ffffff', fontSize: 40, fontWeight: 300, letterSpacing: '.06em',
    lineHeight: 1.4, height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
    textShadow: '0 2px 30px rgba(0,0,0,.85)',
  },
  title: {
    color: '#f4ece0', fontSize: 128, fontWeight: 200, letterSpacing: '.16em',
    textTransform: 'uppercase', textShadow: '0 0 80px rgba(255,196,120,.35)',
  },
  subtitle: {
    color: '#9aa2b2', fontSize: 24, fontWeight: 400, letterSpacing: '.30em',
    marginTop: 34, textTransform: 'uppercase',
  },
  orb: {position: 'absolute', width: 1700, height: 1700, borderRadius: '50%', transform: 'translate(-50%,-50%)'},
  vignette: {
    background: 'radial-gradient(ellipse at 50% 48%, rgba(0,0,0,0) 42%, rgba(0,0,0,.72) 100%)',
    pointerEvents: 'none',
  },
};
