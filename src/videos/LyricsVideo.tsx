import React from 'react';
import {
  AbsoluteFill,
  Audio,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {LYRIC_FONT, PALETTES, easeOut, type LyricSection, type Palette} from './lyrics-theme';
import {FootageLayer, type Shot} from './FootageLayer';

export type LyricLine = {
  t: number;
  section: LyricSection;
  text: string;
  /**
   * Measured end of the sung line. When present it replaces MAX_HOLD, which is a
   * guess that cannot know the difference between a held note and an instrumental
   * break: this song's aligner reported ends of 22.4s and 24.5s on the two lines
   * that precede its long breaks.
   */
  end?: number;
  /** A parenthesised answer, e.g. "(Rejoice)" -- set lighter and smaller. */
  echo?: boolean;
};

export type Song = {
  title: string;
  subtitle?: string;
  audio: string;
  fps: number;
  durationSeconds: number;
  lines: LyricLine[];
  shots?: Shot[];
  /**
   * Where the text sits. 'lower' keeps it out of the middle of the frame, which is
   * where this film puts the things it must not cover -- a face, the cross, the
   * figure in the fog.
   */
  lyricAnchor?: 'center' | 'lower';
  /** Crossfade length between shots; must not exceed how much they overlap. */
  dissolveSeconds?: number;
  /**
   * When the title card is up, as [fade-in start, fade-out end]. A plain array
   * rather than a tuple: these songs are imported from JSON, and TypeScript widens
   * a JSON array to number[], which will not satisfy a tuple type.
   */
  titleSeconds?: number[];
  /**
   * Seconds of fade up from black at the very start. Zero means the first frame is
   * already the picture, for openings that fade in by opacity instead.
   */
  openFadeSeconds?: number;
  /** A closing card, e.g. a benediction, held after the last sung line. */
  endCard?: {lines: string[]; seconds: number[]};
  /**
   * Whether to ghost the previous and next line above and below the current one.
   * Over 30 shots of real footage the ghosts read as smudge under the live line
   * rather than as context, so this film turns them off.
   */
  showNeighbours?: boolean;
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
  opts: {
    offsetSeconds?: number;
    /** Overrides the song's own placement, for cutting alternate versions. */
    anchor?: 'center' | 'lower';
    /** Renders the pictures alone -- no lyrics, no title. */
    hideLyrics?: boolean;
  } = {},
): React.FC => {
  const lines = song.lines;
  const shots = song.shots ?? [];
  const offset = opts.offsetSeconds ?? 0;
  const anchor = opts.anchor ?? song.lyricAnchor;
  const hideLyrics = opts.hideLyrics ?? false;

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

    // A measured end wins; MAX_HOLD is only the fallback for songs without one.
    const holdUntil = current
      ? current.end !== undefined
        ? current.end
        : Math.min(current.t + MAX_HOLD, next ? next.t : current.t + MAX_HOLD)
      : 0;
    const singing = Boolean(current) && now < holdUntil;
    const gapToNext = next ? next.t - now : Infinity;

    const section: LyricSection = current?.section ?? 'verse';
    const palette = PALETTES[section];

    const lineIn = current ? easeOut((now - current.t) / 0.55) : 0;
    const lineOut = current ? easeOut((holdUntil - now) / 0.5) : 0;
    const lineOpacity = singing ? Math.min(lineIn, lineOut) : 0;

    // The title sits centred over the opening image; the lyrics run in the lower
    // safe area underneath it, so the two do not collide.
    const firstLine = lines.length ? lines[0].t : Infinity;
    const win = song.titleSeconds;
    const openTitle = !win && offset > 0
      ? 0
      : win
        ? (() => {
            // Short windows need a short fade, or the card never reaches full.
            const f = Math.min(0.6, (win[1] - win[0]) / 3);
            return interpolate(now, [win[0], win[0] + f, win[1] - f, win[1]], [0, 1, 1, 0],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          })()
        : firstLine < 6
          ? 0
          : interpolate(now, [0.8, 2.6, Math.min(11.5, firstLine - 1.4), Math.min(14, firstLine - 0.6)],
              [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    const openFade = song.openFadeSeconds ?? 1.2;
    const edgeFade = Math.min(
      openFade > 0 ? interpolate(frame, [0, fps * openFade], [0, 1], {extrapolateRight: 'clamp'}) : 1,
      interpolate(frame, [durationInFrames - fps * 1.6, durationInFrames - 1], [1, 0],
        {extrapolateLeft: 'clamp'}),
    );

    return (
      <AbsoluteFill style={{...styles.canvas, background: palette.base, opacity: edgeFade}}>
        <Audio src={staticFile(song.audio)} startFrom={Math.round(offset * fps)} />

        {shots.length ? (
          <FootageLayer
            shots={shots}
            now={now}
            offset={offset}
            dissolveSeconds={song.dissolveSeconds}
          />
        ) : (
          <>
            <Backdrop palette={palette} now={now} />
            <AbsoluteFill style={styles.vignette} />
          </>
        )}

        {(() => {
          const ec = song.endCard;
          if (!ec || hideLyrics) return null;
          const [a, b] = ec.seconds;
          const f = Math.min(0.8, (b - a) / 3);
          const o = interpolate(now, [a, a + f, b - f, b], [0, 1, 1, 0],
            {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          if (o < 0.01) return null;
          return (
            <AbsoluteFill style={{...styles.stage, opacity: o}}>
              <div style={styles.endCard}>
                {ec.lines.map((l, k) => <div key={k}>{l}</div>)}
              </div>
            </AbsoluteFill>
          );
        })()}

        {openTitle > 0.01 && !hideLyrics ? (
          <AbsoluteFill style={{...styles.stage, opacity: openTitle}}>
            <div style={styles.title}>{song.title}</div>
            {song.subtitle ? <div style={styles.subtitle}>{song.subtitle}</div> : null}
          </AbsoluteFill>
        ) : null}

        {hideLyrics ? null : (
        <AbsoluteFill style={anchor === 'lower' ? styles.stageLower : styles.stage}>
          <div style={styles.rail}>
            {song.showNeighbours === false ? null : (
              <div style={{...styles.neighbour, opacity: singing && previous ? 0.2 : 0}}>
                {previous?.text ?? ''}
              </div>
            )}

            <div
              style={{
                ...styles.line,
                color: palette.ink,
                fontSize: current?.echo ? palette.size * 0.52 : palette.size,
                fontWeight: current?.echo ? 300 : palette.weight,
                letterSpacing: current?.echo ? '.10em' : palette.tracking,
                // Lighter than the line it answers, but a lyric video still has to
                // be readable: 0.72 disappeared into a lit bubble.
                opacity: current?.echo ? lineOpacity * 0.88 : lineOpacity,
                transform: `translateY(${interpolate(lineIn, [0, 1], [22, 0])}px)`,
                // Over footage a glow fights the picture; a dark drop is what keeps
                // the text legible against a bright frame.
                // The V1 look: a warm halo behind the ivory, over a dark drop that
                // keeps the hairlines of a Didone readable on a bright frame.
                textShadow: current?.echo
                  ? '0 0 40px rgba(255,206,138,.30), 0 2px 26px rgba(0,0,0,.95), 0 0 8px rgba(0,0,0,.85)'
                  : '0 0 64px rgba(255,198,120,.38), 0 0 26px rgba(255,222,170,.22), '
                    + '0 2px 40px rgba(0,0,0,.88), 0 0 12px rgba(0,0,0,.72)',
              }}
            >
              {current?.text ?? ''}
            </div>

            {song.showNeighbours === false ? null : (
              <div style={{...styles.neighbour, opacity: singing && next && gapToNext < 9 ? 0.16 : 0}}>
                {next?.text ?? ''}
              </div>
            )}
          </div>
        </AbsoluteFill>
        )}
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

const font = LYRIC_FONT;

const styles: Record<string, React.CSSProperties> = {
  canvas: {fontFamily: font, overflow: 'hidden'},
  stage: {alignItems: 'center', justifyContent: 'center', display: 'flex'},
  stageLower: {
    alignItems: 'center', justifyContent: 'flex-end', display: 'flex', paddingBottom: 96,
  },
  rail: {width: 1500, textAlign: 'center'},
  line: {lineHeight: 1.18, minHeight: 130, display: 'flex', alignItems: 'center', justifyContent: 'center'},
  neighbour: {
    color: '#ffffff', fontSize: 40, fontWeight: 300, letterSpacing: '.06em',
    lineHeight: 1.4, height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
    textShadow: '0 2px 30px rgba(0,0,0,.85)',
  },
  title: {
    color: '#f7edd6', fontSize: 96, fontWeight: 400, letterSpacing: '.10em',
    lineHeight: 1.22, maxWidth: 1400, textAlign: 'center', textWrap: 'balance',
    textShadow: '0 0 90px rgba(255,198,120,.42), 0 0 34px rgba(255,222,170,.26), '
      + '0 2px 44px rgba(0,0,0,.9)',
  },
  /** Its own size so the benediction sits on one line, not broken mid-phrase. */
  endCard: {
    color: '#f7edd6', fontSize: 72, fontWeight: 400, letterSpacing: '.07em',
    lineHeight: 1.3, maxWidth: 1720, textAlign: 'center', whiteSpace: 'nowrap',
    textShadow: '0 0 90px rgba(255,198,120,.42), 0 0 34px rgba(255,222,170,.26), '
      + '0 2px 44px rgba(0,0,0,.9)',
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
