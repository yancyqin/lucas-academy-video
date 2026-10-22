/**
 * 好奇新世界 / Curious Worlds · the weekly film of Curious Worlds Weekly (WEEKLY-DEMO-PLAN.md, WEEKLY-VIDEO.md).
 *
 * Two films per episode, Chinese and English (owner, 2026-10-20): each is paced to its own voice, shows the products
 * in its own language and puts only its own language on the cards. scripts/weekly/build_timeline.py lays each one out
 * in public/weekly/<ep>/timeline.<lang>.json; this file only draws it. The look is the Weekly page's own: paper, ink,
 * rust. The series ribbon belongs to the cover (WeeklyCover), never to the film.
 *
 * Recordings play along a smooth source-time curve (one unbroken take, faster between the moments the narration
 * names), looked up frame by frame, never cut.
 */
import type {CSSProperties, FC, ReactNode} from 'react';
import {
  AbsoluteFill,
  Audio,
  Freeze,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  type CalculateMetadataFunction,
} from 'remotion';

type Lang = 'zh' | 'en';
type Shot = {
  kind: 'title' | 'chapter' | 'page' | 'image' | 'clip' | 'film' | 'question' | 'end';
  start: number;
  end: number;
  src?: string;
  keys?: [number, number][];
  crop?: [number, number, number, number];
  label?: string;
  tag?: string;
  film?: string;
  source?: string;
  n?: string;
  zh?: string;
  en?: string;
};
type Cue = {id: string; start: number; end: number; zh: string; en: string; audio?: string};
export type WeeklyTimeline = {
  episode: string;
  lang: Lang;
  fps: number;
  durationSeconds: number;
  draft: boolean;
  series: {zh: string; en: string};
  shots: Shot[];
  cues: Cue[];
  chapters: {t: number; n: string; zh: string; en: string}[];
};
/** `voice: false` renders the picture alone (the delivery muxes the mixed track onto it). */
export type WeeklyProps = {episode: string; lang: Lang; voice?: boolean; tl?: WeeklyTimeline | null};

export const calculateWeeklyMetadata: CalculateMetadataFunction<WeeklyProps> = async ({props, abortSignal}) => {
  const response = await fetch(staticFile(`weekly/${props.episode}/timeline.${props.lang}.json`), {signal: abortSignal});
  if (!response.ok) throw Error(`Run python3 scripts/weekly/build_timeline.py ${props.episode} ${props.lang} first`);
  const tl = (await response.json()) as WeeklyTimeline;
  return {props: {...props, tl}, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps)};
};

// The Weekly page's palette (lucasgame-academy/weekly/weekly.css).
const C = {paper: '#f5f2eb', ink: '#253a36', muted: '#64716a', line: '#cbd0c5', rust: '#ad482c', dark: '#0a1720', cream: '#f5ead4'};
const SERIF_ZH = '"Songti SC", "STSong", serif';
const SERIF = 'Georgia, "Times New Roman", serif';
const SANS = '-apple-system, "PingFang SC", "Helvetica Neue", sans-serif';
const FADE = 8; // frames of cross-fade into each shot
const T = {
  zh: {kicker: 'LUCAS ACADEMY · 每周项目展示', episode: (n: number) => `第 ${n} 期 · Weekly 001–003 回顾`, by: 'By Lucas Academy Team',
    film: '完整影片 · 在 Lucas Academy 频道', source: '来源', fridays: '每周五下午 4–5 点 · 欢迎来听，也欢迎带一个想法来讲', draft: 'DRAFT · 时长为估算'},
  en: {kicker: 'LUCAS ACADEMY · WEEKLY SHOW AND TELL', episode: (n: number) => `Episode ${n} · catching up on Weekly 001–003`, by: 'By Lucas Academy Team',
    film: 'FULL FILM ON OUR CHANNEL', source: 'Source', fridays: 'Fridays 4–5 pm · come to listen, or bring an idea to share', draft: 'DRAFT · estimated timing'},
};

const ease = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

/** Source seconds at shot-local time t: straight between two points, a monotone Hermite curve through more. */
const sourceAt = (keys: [number, number][], t: number): number => {
  if (t <= keys[0][0]) return keys[0][1];
  const n = keys.length;
  if (t >= keys[n - 1][0]) return keys[n - 1][1];
  const slope = (i: number) => (keys[i + 1][1] - keys[i][1]) / (keys[i + 1][0] - keys[i][0]);
  const tangent = (i: number) => (i === 0 ? slope(0) : i === n - 1 ? slope(n - 2) : Math.min(slope(i - 1), slope(i)));
  let i = 0;
  while (t > keys[i + 1][0]) i++;
  const [t0, s0] = keys[i];
  const [t1, s1] = keys[i + 1];
  if (n === 2) return s0 + ((s1 - s0) * (t - t0)) / (t1 - t0);
  const h = t1 - t0;
  const u = (t - t0) / h;
  return (2 * u ** 3 - 3 * u ** 2 + 1) * s0 + (u ** 3 - 2 * u ** 2 + u) * h * tangent(i)
    + (3 * u ** 2 - 2 * u ** 3) * s1 + (u ** 3 - u ** 2) * h * tangent(i + 1);
};

const file = (ep: string, p: string) => staticFile(`weekly/${ep}/${p}`);

/** The series name on a diagonal band across the top-right corner: the cover's, not the film's. */
const Ribbon: FC<{text: string; lang: Lang}> = ({text, lang}) => {
  // The band's centre sits on the corner's diagonal, D px in from the corner, so the text is centred where the
  // band crosses the frame (about 2·D px of it shows).
  const zh = lang === 'zh';
  const BOX = 720, D = zh ? 250 : 270, W = 1000, H = 132;  // owner 2026-10-20: a wide band, big letters
  const cx = BOX - D / Math.SQRT2, cy = D / Math.SQRT2;
  return (
    <div style={{position: 'absolute', top: 0, right: 0, width: BOX, height: BOX, overflow: 'hidden', pointerEvents: 'none', zIndex: 50}}>
      <div style={{
        position: 'absolute', left: cx - W / 2, top: cy - H / 2, width: W, height: H, transform: 'rotate(45deg)',
        background: C.rust, color: C.cream, display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: zh ? SERIF_ZH : SERIF, fontWeight: 700, fontStyle: zh ? 'normal' : 'italic',
        fontSize: zh ? 68 : 58, letterSpacing: zh ? 12 : 1, textIndent: zh ? 12 : 0,
        boxShadow: '0 6px 18px rgba(0,0,0,.28)', borderTop: '2px solid rgba(245,234,212,.6)', borderBottom: '2px solid rgba(245,234,212,.6)',
      }}>{text}</div>
    </div>
  );
};

/** A product's name in the lower-left corner for the first seconds of a shot. */
const Label: FC<{text: string; hold?: number}> = ({text, hold = 4.2}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const o = interpolate(frame, [6, 16, hold * fps, hold * fps + 12], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const x = interpolate(frame, [6, 18], [-24, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', left: 56, bottom: 56, opacity: o, transform: `translateX(${x}px)`,
      background: 'rgba(10,23,32,.84)', color: C.cream, padding: '16px 28px 16px 22px', borderLeft: `6px solid ${C.rust}`,
      boxShadow: '0 8px 24px rgba(0,0,0,.25)', fontFamily: SANS, fontWeight: 600, fontSize: 40, lineHeight: 1.2}}>{text}</div>
  );
};

const Pill: FC<{children: ReactNode; style?: CSSProperties}> = ({children, style}) => (
  <div style={{position: 'absolute', left: 56, top: 48, background: 'rgba(10,23,32,.78)', color: C.cream, fontFamily: SANS,
    fontSize: 26, letterSpacing: 2, padding: '9px 18px', borderRadius: 30, ...style}}>{children}</div>
);

// ---------------------------------------------------------------- shots

const TitleShot: FC<{tl: WeeklyTimeline}> = ({tl}) => {
  const frame = useCurrentFrame();
  const a = interpolate(frame, [0, 22], [0, 1], {extrapolateRight: 'clamp'});
  const b = interpolate(frame, [14, 36], [0, 1], {extrapolateRight: 'clamp'});
  const t = T[tl.lang];
  const zh = tl.lang === 'zh';
  return (
    <AbsoluteFill style={{background: C.paper, padding: '0 180px', justifyContent: 'center'}}>
      <div style={{fontFamily: SANS, fontSize: 26, letterSpacing: 6, color: C.rust, opacity: b}}>{t.kicker}</div>
      {zh
        ? <div style={{fontFamily: SERIF_ZH, fontSize: 210, lineHeight: 1.08, letterSpacing: 12, color: C.ink, marginTop: 26, opacity: a,
            transform: `translateY(${(1 - a) * 24}px)`}}>好奇<span style={{color: C.rust}}>新世界</span></div>
        : <div style={{fontFamily: SERIF, fontSize: 190, lineHeight: 1.0, letterSpacing: -6, color: C.ink, marginTop: 26, opacity: a,
            transform: `translateY(${(1 - a) * 24}px)`}}>Curious <em style={{color: C.rust}}>Worlds</em></div>}
      <div style={{height: 2, background: C.ink, width: 900, margin: '48px 0 30px', opacity: b}} />
      <div style={{fontFamily: zh ? SANS : SERIF, fontSize: 40, color: C.ink, opacity: b}}>{t.episode(Number(tl.episode))}</div>
      <div style={{fontFamily: SANS, fontSize: 28, color: C.muted, marginTop: 26, opacity: b}}>{t.by}</div>
    </AbsoluteFill>
  );
};

const ChapterShot: FC<{shot: Shot; lang: Lang}> = ({shot, lang}) => {
  const frame = useCurrentFrame();
  const a = interpolate(frame, [0, 18], [0, 1], {extrapolateRight: 'clamp'});
  const w = interpolate(frame, [6, 40], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const zh = lang === 'zh';
  const n = zh ? shot.n : String('一二三四五六七八九'.indexOf(shot.n ?? '') + 1);
  return (
    <AbsoluteFill style={{background: C.paper, alignItems: 'center', justifyContent: 'center'}}>
      <div style={{width: 128, height: 128, borderRadius: 64, border: `3px solid ${C.rust}`, display: 'grid', placeItems: 'center',
        fontFamily: zh ? SERIF_ZH : SERIF, fontSize: 64, color: C.rust, opacity: a}}>{n}</div>
      <div style={{fontFamily: zh ? SERIF_ZH : SERIF, fontSize: zh ? 112 : 100, color: C.ink, marginTop: 40, letterSpacing: zh ? 6 : -1,
        opacity: a, transform: `translateY(${(1 - a) * 18}px)`}}>{zh ? shot.zh : shot.en}</div>
      <div style={{height: 2, background: C.line, width: 760 * ease(w), marginTop: 36}} />
    </AbsoluteFill>
  );
};

/** A still: a Weekly page as it reads, or a picture, on a slow push. */
const StillShot: FC<{ep: string; shot: Shot; len: number; lang: Lang}> = ({ep, shot, len, lang}) => {
  const frame = useCurrentFrame();
  const page = shot.kind === 'page';
  const z = interpolate(frame, [0, len], page ? [1.0, 1.035] : [1.02, 1.1]);
  return (
    <AbsoluteFill style={{background: page ? C.paper : C.dark, overflow: 'hidden'}}>
      <Img src={file(ep, shot.src!)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${z})`,
        transformOrigin: page ? '50% 30%' : '50% 50%'}} />
      {shot.tag && <Pill>{shot.tag}</Pill>}
      {shot.source && <Pill style={{top: 'auto', bottom: 48}}>{T[lang].source} · {shot.source}</Pill>}
      {shot.film && <FilmBadge title={shot.film} lang={lang} />}
      {shot.label && <Label text={shot.label} />}
    </AbsoluteFill>
  );
};

/** A recording: one take along its source-time curve, a crop shown whole on the dark ground. */
const ClipShot: FC<{ep: string; shot: Shot; lang: Lang}> = ({ep, shot, lang}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const s = sourceAt(shot.keys!, frame / fps);
  const [cx, cy, cw, ch] = shot.crop ?? [0, 0, 1920, 1080];
  const k = Math.min(width / cw, height / ch);
  const ox = (width - cw * k) / 2, oy = (height - ch * k) / 2;
  return (
    <AbsoluteFill style={{background: C.dark, overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: ox, top: oy, width: cw * k, height: ch * k, overflow: 'hidden'}}>
        <Freeze frame={0}>
          <OffthreadVideo src={file(ep, shot.src!)} trimBefore={Math.max(0, Math.round(s * fps))} muted
            style={{position: 'absolute', left: -cx * k, top: -cy * k, width: 1920 * k, height: 1080 * k}} />
        </Freeze>
      </div>
      {shot.film && <FilmBadge title={shot.film} lang={lang} />}
      {shot.label && <Label text={shot.label} />}
    </AbsoluteFill>
  );
};

/** One of our films: the whole of it is on the channel. */
const FilmBadge: FC<{title: string; lang: Lang}> = ({title, lang}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [8, 20], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', left: 56, bottom: 56, opacity: o, background: 'rgba(245,242,235,.95)', color: C.ink,
      padding: '18px 28px', borderLeft: `6px solid ${C.rust}`, boxShadow: '0 8px 24px rgba(0,0,0,.3)'}}>
      <div style={{fontFamily: SANS, fontSize: 22, letterSpacing: 3, color: C.rust}}>{T[lang].film}</div>
      <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 40, marginTop: 6}}>{title}</div>
    </div>
  );
};

const QuestionShot: FC<{shot: Shot; lang: Lang}> = ({shot, lang}) => {
  const frame = useCurrentFrame();
  const a = interpolate(frame, [0, 24], [0, 1], {extrapolateRight: 'clamp'});
  const zh = lang === 'zh';
  return (
    <AbsoluteFill style={{background: C.paper, alignItems: 'center', justifyContent: 'center', textAlign: 'center'}}>
      <div style={{fontFamily: SERIF, fontSize: 150, color: C.rust, lineHeight: 0.6, opacity: a}}>?</div>
      <div style={{fontFamily: zh ? SERIF_ZH : SERIF, fontSize: zh ? 84 : 76, lineHeight: 1.4, color: C.ink, marginTop: 50,
        whiteSpace: 'pre-line', opacity: a, transform: `translateY(${(1 - a) * 16}px)`}}>{zh ? shot.zh : shot.en}</div>
    </AbsoluteFill>
  );
};

const EndShot: FC<{lang: Lang}> = ({lang}) => {
  const frame = useCurrentFrame();
  const a = interpolate(frame, [0, 20], [0, 1], {extrapolateRight: 'clamp'});
  const zh = lang === 'zh';
  return (
    <AbsoluteFill style={{background: C.dark, color: C.cream, alignItems: 'center', justifyContent: 'center', textAlign: 'center', opacity: a}}>
      {zh
        ? <div style={{fontFamily: SERIF_ZH, fontSize: 120, letterSpacing: 10}}>好奇<span style={{color: '#e08a63'}}>新世界</span></div>
        : <div style={{fontFamily: SERIF, fontSize: 120, letterSpacing: -4}}>Curious <em style={{color: '#e08a63'}}>Worlds</em></div>}
      <div style={{height: 2, background: 'rgba(245,234,212,.35)', width: 760, margin: '46px 0 36px'}} />
      <div style={{fontFamily: zh ? SANS : SERIF, fontSize: 42}}>{T[lang].fridays}</div>
      <div style={{fontFamily: SANS, fontSize: 36, marginTop: 50, letterSpacing: 1}}>lucasacademy.org/weekly</div>
      <div style={{fontFamily: SANS, fontSize: 26, marginTop: 16, letterSpacing: 6, opacity: 0.7}}>LUCAS ACADEMY</div>
    </AbsoluteFill>
  );
};

const ShotView: FC<{tl: WeeklyTimeline; shot: Shot; len: number}> = ({tl, shot, len}) => {
  switch (shot.kind) {
    case 'title': return <TitleShot tl={tl} />;
    case 'chapter': return <ChapterShot shot={shot} lang={tl.lang} />;
    case 'page': case 'image': return <StillShot ep={tl.episode} shot={shot} len={len} lang={tl.lang} />;
    case 'clip': case 'film': return <ClipShot ep={tl.episode} shot={shot} lang={tl.lang} />;
    case 'question': return <QuestionShot shot={shot} lang={tl.lang} />;
    case 'end': return <EndShot lang={tl.lang} />;
  }
};

const Fade: FC<{children: ReactNode; first: boolean}> = ({children, first}) => {
  const frame = useCurrentFrame();
  const o = first ? 1 : interpolate(frame, [0, FADE], [0, 1], {extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{opacity: o}}>{children}</AbsoluteFill>;
};

export const WeeklyEpisode: FC<WeeklyProps> = ({tl, voice = true}) => {
  const {fps} = useVideoConfig();
  if (!tl) return <AbsoluteFill style={{background: C.paper}} />;
  const f = (s: number) => Math.round(s * fps);
  return (
    <AbsoluteFill style={{background: C.paper}}>
      {tl.shots.map((shot, i) => {
        const from = f(shot.start);
        const len = Math.max(1, f(shot.end) - from) + (i < tl.shots.length - 1 ? FADE : 0);
        return (
          <Sequence key={i} from={from} durationInFrames={len} name={`${shot.kind} ${shot.src ?? shot.zh ?? ''}`}>
            <Fade first={i === 0}><ShotView tl={tl} shot={shot} len={len} /></Fade>
          </Sequence>
        );
      })}
      {voice && tl.cues.map((c) => c.audio
        ? <Sequence key={c.id} from={f(c.start)} name={c.id}><Audio src={staticFile(c.audio)} /></Sequence>
        : null)}
      {tl.draft && <div style={{position: 'absolute', right: 40, bottom: 30, fontFamily: SANS, fontSize: 26, color: C.rust, opacity: 0.75,
        background: 'rgba(245,242,235,.8)', padding: '4px 12px', zIndex: 60}}>{T[tl.lang].draft}</div>}
    </AbsoluteFill>
  );
};

/**
 * The YouTube cover: the episode's question, big in the film's language with the other language small under it, and
 * the series name on a diagonal ribbon in the top-right corner (owner, 2026-10-20). Nothing else: brand and byline
 * are inside the film. The background is a frame of the film itself.
 */
export type WeeklyCoverProps = {episode: string; lang: Lang; zh: string; en: string; bg: string; at?: number; focus?: string};
export const WeeklyCover: FC<WeeklyCoverProps> = ({episode, lang, zh, en, bg, at = 0, focus = '50% 50%'}) => {
  const {fps} = useVideoConfig();
  const video = bg.endsWith('.mp4');
  const media: CSSProperties = {position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', objectPosition: focus};
  const big = lang === 'zh' ? zh : en;
  const small = lang === 'zh' ? en : zh;
  return (
    <AbsoluteFill style={{background: C.dark}}>
      {video
        ? <Freeze frame={0}><OffthreadVideo src={file(episode, bg)} trimBefore={Math.round(at * fps)} muted style={media} /></Freeze>
        : <Img src={file(episode, bg)} style={media} />}
      <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(10,23,32,.88) 0%, rgba(10,23,32,.66) 55%, rgba(10,23,32,.1) 92%)'}} />
      <AbsoluteFill style={{justifyContent: 'center', padding: '120px 90px 0'}}>
        <div style={{fontFamily: lang === 'zh' ? SERIF_ZH : SERIF, fontWeight: 700, fontSize: lang === 'zh' ? 176 : 150, lineHeight: 1.16,
          color: C.cream, whiteSpace: 'pre-line', textShadow: '0 6px 30px rgba(0,0,0,.5)', maxWidth: 1700}}>{big}</div>
        <div style={{fontFamily: lang === 'zh' ? SERIF : SERIF_ZH, fontStyle: lang === 'zh' ? 'italic' : 'normal', fontSize: 64,
          color: '#e8d8b8', marginTop: 34, whiteSpace: 'pre-line', textShadow: '0 4px 18px rgba(0,0,0,.5)'}}>{small}</div>
      </AbsoluteFill>
      <Ribbon text={lang === 'zh' ? '好奇新世界' : 'Curious Worlds'} lang={lang} />
    </AbsoluteFill>
  );
};
