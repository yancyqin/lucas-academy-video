// 语言的桥 · Language Bridge (lucas-academy-media issue #4) -- two films, one per language.
//
// The Chinese video and the English video play the same scenes, each on its own
// timeline (scripts/reciprocal-doors-prep.mjs): scenes key every beat off line
// start times, never off one voice's pacing. On-screen words follow the film:
// Chinese with small English in the Chinese video, English only in the English
// video; the product screens switch to the product's English interface too.
import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import timelineZh from '../scripts/reciprocal-doors.timeline.zh.json';
import timelineEn from '../scripts/reciprocal-doors.timeline.en.json';
import product from '../../public/images/reciprocal-doors/product/regions.json';

export type Lang = 'zh' | 'en';
type Part = {id: string; file: string | null; lang: string; demo: boolean; offset: number; seconds: number};
type Chunk = {id: string; zh: string; en: string; start: number; slot: number; spoken: Record<Lang, number>; tracks: Partial<Record<Lang, Part[]>>};
type Segment = {id: string; start: number; end: number; chunks: Chunk[]};
type Timeline = {fps: number; titleSeconds: number; endCardSeconds: number; durationSeconds: number; images: string[]; segments: Segment[]};

const TIMELINES: Record<Lang, Timeline> = {zh: timelineZh as unknown as Timeline, en: timelineEn as unknown as Timeline};
export const RD_FPS = 30;
export const filmDuration = (lang: Lang) => Math.ceil(TIMELINES[lang].durationSeconds * RD_FPS);

export type LanguageBridgeProps = {lang: Lang; audio: boolean; subtitles: boolean};

const available = new Set(TIMELINES.zh.images);
/** Which film is rendering: its language and its timeline. */
const Film = React.createContext<{lang: Lang; segments: Segment[]}>({lang: 'zh', segments: TIMELINES.zh.segments});
const useLang = () => React.useContext(Film).lang;

const C = {
  cream: '#fffaf0',
  paper: '#fffdf8',
  ink: '#3b2f2a',
  soft: '#7a6a5e',
  coral: '#e36f55', // Mary (the girl in the coral hoodie)
  teal: '#2c8c86', // Jacob (the boy in the teal hoodie)
  gold: '#f5a623',
  shadow: '0 10px 30px rgba(59, 47, 42, 0.18)',
};
const ZH = '"PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif';
const EN = '"Avenir Next", "Avenir", "Helvetica Neue", sans-serif';

const clamp = (v: number, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
/** 0 → 1 over `dur` seconds from `at`, eased. */
const rise = (t: number, at: number, dur = 0.6) =>
  interpolate(t, [at, at + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
const seg = (segments: Segment[], id: string) => segments.find((s) => s.id === id)!;
/** Start time of chunk n (1-based) in a scene, optionally a fraction into its slot. */
const beat = (s: Segment, n: number, into = 0) => s.chunks[n - 1].start + s.chunks[n - 1].slot * into;

// ─── Audio ────────────────────────────────────────────────────────────────

const Narration: React.FC<{track: Lang; segments: Segment[]}> = ({track, segments}) => (
  <>
    {segments.flatMap((s) =>
      s.chunks.flatMap((chunk) =>
        (chunk.tracks[track] ?? [])
          .filter((part) => part.file)
          .map((part) => (
            <Sequence key={`${track}-${part.id}`} from={Math.round((chunk.start + part.offset) * RD_FPS)}>
              <Audio src={staticFile(part.file!)} />
            </Sequence>
          )),
      ),
    )}
  </>
);

// ─── Building blocks ──────────────────────────────────────────────────────

/** A concept illustration with a slow push-in; a labelled stand-in until the art exists. */
const Picture: React.FC<{name: string; t: number; from: number; to: number; zoom?: [number, number]; origin?: string; dim?: number}> = ({
  name,
  t,
  from,
  to,
  zoom = [1.02, 1.1],
  origin = '50% 40%',
  dim = 0,
}) => {
  const p = clamp((t - from) / Math.max(1, to - from));
  const scale = interpolate(p, [0, 1], zoom);
  const file = `${name}.png`;
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#f3e6d2'}}>
      {available.has(file) ? (
        <Img
          src={staticFile(`images/reciprocal-doors/${file}`)}
          style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${scale})`, transformOrigin: origin}}
        />
      ) : (
        <AbsoluteFill
          style={{
            background: 'linear-gradient(160deg, #fbe9cf 0%, #f4d9b8 55%, #e9c9a6 100%)',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div style={{border: `4px dashed ${C.soft}`, borderRadius: 24, padding: '28px 48px', color: C.soft, fontFamily: EN, fontSize: 40, marginTop: -160}}>
            image pending · {file}
          </div>
        </AbsoluteFill>
      )}
      {dim > 0 && <AbsoluteFill style={{background: C.cream, opacity: dim}} />}
    </AbsoluteFill>
  );
};

const Card: React.FC<{zh: string; en?: string; x: number; y: number; show: number; color?: string; w?: number; size?: number; anchor?: 'center' | 'left'}> = ({
  zh,
  en,
  x,
  y,
  show,
  color = C.ink,
  w,
  size = 50,
  anchor = 'center',
}) => {
  const english = useLang() === 'en';
  return (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y,
      width: w,
      transform: `translate(${anchor === 'center' ? '-50%' : '0'}, ${(1 - show) * 24}px) scale(${0.94 + 0.06 * show})`,
      opacity: show,
      background: 'rgba(255, 253, 248, 0.94)',
      borderRadius: 26,
      padding: '20px 34px',
      boxShadow: C.shadow,
      borderTop: `8px solid ${color}`,
      textAlign: 'center',
    }}
  >
    {english ? (
      <div style={{fontFamily: EN, fontSize: size * 0.84, fontWeight: 700, color, lineHeight: 1.25}}>{en ?? zh}</div>
    ) : (
      <>
        <div style={{fontFamily: ZH, fontSize: size, fontWeight: 700, color, lineHeight: 1.25}}>{zh}</div>
        {en && <div style={{fontFamily: EN, fontSize: size * 0.56, fontWeight: 600, color: C.soft, marginTop: 6}}>{en}</div>}
      </>
    )}
  </div>
  );
};

const Bubble: React.FC<{text: string; x: number; y: number; show: number; color: string; tail?: 'left' | 'right'; font?: string}> = ({
  text,
  x,
  y,
  show,
  color,
  tail = 'left',
  font = ZH,
}) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y,
      opacity: show,
      transform: `translate(-50%, -50%) scale(${0.7 + 0.3 * show})`,
      transformOrigin: tail === 'left' ? '20% 100%' : '80% 100%',
      background: C.paper,
      border: `6px solid ${color}`,
      borderRadius: 40,
      padding: '18px 38px',
      fontFamily: font,
      fontSize: 56,
      fontWeight: 700,
      color: C.ink,
      whiteSpace: 'nowrap',
      boxShadow: C.shadow,
    }}
  >
    {text}
    <div
      style={{
        position: 'absolute',
        bottom: -30,
        [tail === 'left' ? 'left' : 'right']: 50,
        width: 0,
        height: 0,
        borderLeft: '18px solid transparent',
        borderRight: '18px solid transparent',
        borderTop: `30px solid ${color}`,
      }}
    />
  </div>
);

/** A soft pulsing ring marking who is speaking. */
const Glow: React.FC<{x: number; y: number; r: number; color: string; show: number; t: number}> = ({x, y, r, color, show, t}) => {
  const pulse = 1 + 0.05 * Math.sin(t * Math.PI * 2 * 0.8);
  return (
    <div
      style={{
        position: 'absolute',
        left: x - r,
        top: y - r,
        width: r * 2,
        height: r * 2,
        borderRadius: '50%',
        border: `8px solid ${color}`,
        boxShadow: `0 0 40px ${color}`,
        opacity: show * 0.85,
        transform: `scale(${pulse})`,
      }}
    />
  );
};

/** An arrow that draws itself along a quadratic curve. */
const Arrow: React.FC<{from: [number, number]; to: [number, number]; bend: number; color: string; draw: number; label?: string; labelFont?: string}> = ({
  from,
  to,
  bend,
  color,
  draw,
  label,
  labelFont = ZH,
}) => {
  const mx = (from[0] + to[0]) / 2;
  const my = (from[1] + to[1]) / 2 + bend;
  const d = `M ${from[0]} ${from[1]} Q ${mx} ${my} ${to[0]} ${to[1]}`;
  const length = 2000;
  const angle = Math.atan2(to[1] - my, to[0] - mx);
  const head = 34;
  const tip = (a: number) => `${to[0] - head * Math.cos(angle - a)},${to[1] - head * Math.sin(angle - a)}`;
  const lx = (from[0] + 2 * mx + to[0]) / 4;
  const ly = (from[1] + 2 * my + to[1]) / 4;
  return (
    <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
      <path d={d} fill="none" stroke={C.paper} strokeWidth={22} strokeLinecap="round" strokeDasharray={length} strokeDashoffset={length * (1 - draw)} opacity={0.9} />
      <path d={d} fill="none" stroke={color} strokeWidth={12} strokeLinecap="round" strokeDasharray={length} strokeDashoffset={length * (1 - draw)} />
      {draw > 0.97 && <polygon points={`${to[0]},${to[1]} ${tip(0.5)} ${tip(-0.5)}`} fill={color} />}
      {label && draw > 0.4 && (
        <g opacity={clamp((draw - 0.4) / 0.3)}>
          <rect x={lx - 105} y={ly - 42} width={210} height={84} rx={42} fill={C.paper} stroke={color} strokeWidth={6} />
          <text x={lx} y={ly + 15} textAnchor="middle" fontFamily={labelFont} fontSize={44} fontWeight={700} fill={color}>
            {label}
          </text>
        </g>
      )}
    </svg>
  );
};

type IconKind = 'book' | 'ear' | 'picture' | 'talk' | 'sound' | 'pencil' | 'check';
const Icon: React.FC<{kind: IconKind; size?: number; color?: string}> = ({kind, size = 64, color = C.ink}) => {
  const s = {fill: 'none', stroke: color, strokeWidth: 5, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
  const shapes: Record<IconKind, React.ReactNode> = {
    book: (
      <>
        <path d="M32 16 C24 10 12 10 6 14 V52 C12 48 24 48 32 54 C40 48 52 48 58 52 V14 C52 10 40 10 32 16 Z" {...s} />
        <path d="M32 16 V54" {...s} />
      </>
    ),
    ear: (
      <>
        <path d="M20 26 C20 12 44 10 46 26 C47 36 38 38 36 46 C34 54 24 56 22 48" {...s} />
        <path d="M28 28 C28 22 38 22 38 28 C38 32 33 33 33 37" {...s} />
      </>
    ),
    picture: (
      <>
        <rect x={8} y={12} width={48} height={40} rx={6} {...s} />
        <circle cx={22} cy={25} r={5} {...s} />
        <path d="M10 48 L26 34 L36 42 L44 34 L54 44" {...s} />
      </>
    ),
    talk: (
      <>
        <path d="M10 14 H54 V40 H30 L18 52 V40 H10 Z" {...s} />
        <path d="M20 24 H44 M20 31 H36" {...s} />
      </>
    ),
    sound: (
      <>
        <path d="M10 26 H20 L32 14 V50 L20 38 H10 Z" {...s} />
        <path d="M40 22 C45 27 45 37 40 42 M46 16 C55 25 55 39 46 48" {...s} />
      </>
    ),
    pencil: (
      <>
        <path d="M14 50 L18 38 L44 12 L52 20 L26 46 Z" {...s} />
        <path d="M40 16 L48 24" {...s} />
      </>
    ),
    check: <path d="M12 34 L26 48 L52 18" {...s} strokeWidth={7} />,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 64 64">
      {shapes[kind]}
    </svg>
  );
};

/** A small round chip: icon + bilingual label. */
const Chip: React.FC<{kind: IconKind; zh: string; en: string; show: number; lit?: number; color?: string}> = ({kind, zh, en, show, lit = 0, color = C.gold}) => {
  const english = useLang() === 'en';
  return (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      gap: 16,
      opacity: show,
      transform: `translateY(${(1 - show) * 18}px)`,
      background: lit > 0 ? `color-mix(in srgb, ${color} ${Math.round(18 * lit)}%, ${C.paper})` : C.paper,
      border: `5px solid ${lit > 0 ? color : 'rgba(122,106,94,0.25)'}`,
      borderRadius: 60,
      padding: '12px 30px 12px 18px',
      boxShadow: C.shadow,
    }}
  >
    <Icon kind={kind} size={62} color={lit > 0 ? color : C.soft} />
    {english ? (
      <div style={{fontFamily: EN, fontSize: 34, fontWeight: 700, color: C.ink, lineHeight: 1.15}}>{en}</div>
    ) : (
      <div>
        <div style={{fontFamily: ZH, fontSize: 40, fontWeight: 700, color: C.ink, lineHeight: 1.1}}>{zh}</div>
        <div style={{fontFamily: EN, fontSize: 24, fontWeight: 600, color: C.soft}}>{en}</div>
      </div>
    )}
  </div>
  );
};

const Row: React.FC<{x: number; y: number; children: React.ReactNode; gap?: number; anchor?: 'center' | 'left'}> = ({x, y, children, gap = 26, anchor = 'center'}) => (
  <div style={{position: 'absolute', left: x, top: y, display: 'flex', gap, transform: anchor === 'center' ? 'translateX(-50%)' : undefined}}>{children}</div>
);

const ConceptTag: React.FC = () => {
  const english = useLang() === 'en';
  return (
  <div
    style={{
      position: 'absolute',
      top: 34,
      right: 40,
      fontFamily: `${ZH}`,
      fontSize: 24,
      color: C.ink,
      background: 'rgba(255, 253, 248, 0.82)',
      borderRadius: 30,
      padding: '8px 22px',
      letterSpacing: 1,
    }}
  >
    {english ? <span style={{fontFamily: EN}}>Concept illustration</span> : <>概念示意 · <span style={{fontFamily: EN}}>Concept illustration</span></>}
  </div>
  );
};

// ─── The real product (lang.lucasacademy.org) ─────────────────────────────
// Screens captured by scripts/reciprocal-doors-capture-product.mjs at 1440x900
// CSS px (2x pixels), with the on-screen rects of the parts the film points at.

type Rect = {x: number; y: number; w: number; h: number};
const PAGE = product.viewport;
const FULL: Rect = {x: 0, y: 0, w: PAGE.width, h: PAGE.height};
// Screens captured in both interface languages ('en-' prefix = English first,
// which also turns the product's interface English). A state written 'en:home'
// or 'zh:home' pins the language; a bare name follows the film.
const EN_SCREENS = new Set(['home', 'tools', 'word', 'pinyin', 'study', 'study-switch']);
const screenFor = (lang: Lang, state: string) => {
  const [pinned, name] = state.includes(':') ? (state.split(':') as [Lang, string]) : [lang, state];
  return pinned === 'en' && EN_SCREENS.has(name) ? `en-${name}` : name;
};
const region = (state: string, name: string): Rect => {
  const found = (product.regions as Record<string, Record<string, Rect>>)[state]?.[name];
  if (!found) throw new Error(`No region ${name} in product screen ${state}`);
  return found;
};
const union = (...rects: Rect[]): Rect => {
  const x = Math.min(...rects.map((r) => r.x));
  const y = Math.min(...rects.map((r) => r.y));
  return {x, y, w: Math.max(...rects.map((r) => r.x + r.w)) - x, h: Math.max(...rects.map((r) => r.y + r.h)) - y};
};
const pad = (r: Rect, p: number): Rect => ({x: r.x - p, y: r.y - p, w: r.w + 2 * p, h: r.h + 2 * p});
const mix = (a: number, b: number, k: number) => a + (b - a) * k;

/** One camera position on the product: which screen, which part of it, what to point at. */
type Ring = {name: string; at: number; state?: string; color?: string};
type Shot = {at: number; state: string; focus: Rect; rings?: Ring[]};

/** Fit a focus rect into the window, never showing past the edge of the page. */
const camera = (focus: Rect, W: number, H: number) => {
  const s = Math.max(Math.min(W / focus.w, H / focus.h), W / PAGE.width, H / PAGE.height);
  const x = Math.min(0, Math.max(W - s * PAGE.width, W / 2 - s * (focus.x + focus.w / 2)));
  const y = Math.min(0, Math.max(H - s * PAGE.height, H / 2 - s * (focus.y + focus.h / 2)));
  return {s, x, y};
};

const BAR = 46;

/** A browser window showing the product; the camera eases from shot to shot. */
const ProductWindow: React.FC<{t: number; shots: Shot[]; x: number; y: number; w: number; opacity?: number}> = ({t, shots, x, y, w, opacity = 1}) => {
  const lang = useLang();
  const H = (w * PAGE.height) / PAGE.width;
  let index = 0;
  shots.forEach((shot, i) => {
    if (shot.at <= t) index = i;
  });
  const current = shots[index];
  const previous = shots[Math.max(0, index - 1)];
  const k = index === 0 ? 1 : interpolate(t, [current.at, current.at + 0.8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const focus: Rect = {
    x: mix(previous.focus.x, current.focus.x, k),
    y: mix(previous.focus.y, current.focus.y, k),
    w: mix(previous.focus.w, current.focus.w, k),
    h: mix(previous.focus.h, current.focus.h, k),
  };
  const cam = camera(focus, w, H);
  const next = shots[index + 1]?.at ?? Infinity;
  const screen = (state: string, alpha: number) => (
    <Img
      key={state}
      src={staticFile(`images/reciprocal-doors/product/${screenFor(lang, state)}.png`)}
      style={{position: 'absolute', left: cam.x, top: cam.y, width: cam.s * PAGE.width, height: cam.s * PAGE.height, opacity: alpha}}
    />
  );
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: H + BAR, opacity, borderRadius: 22, overflow: 'hidden', boxShadow: '0 24px 60px rgba(59, 47, 42, 0.28)', background: C.paper}}>
      <div style={{height: BAR, background: '#f1ebe1', display: 'flex', alignItems: 'center', padding: '0 18px', gap: 9, borderBottom: '1px solid #e2d8c9'}}>
        {['#ec6a5e', '#f4bf4f', '#61c554'].map((dot) => (
          <div key={dot} style={{width: 14, height: 14, borderRadius: 7, background: dot}} />
        ))}
        <div style={{marginLeft: 18, flex: 1, maxWidth: 520, height: 28, borderRadius: 14, background: C.paper, display: 'flex', alignItems: 'center', padding: '0 16px', fontFamily: EN, fontSize: 18, color: C.soft}}>
          lang.lucasacademy.org
        </div>
        <div style={{marginLeft: 'auto', fontFamily: ZH, fontSize: 18, color: C.soft}}>
          {lang === 'en' ? <span style={{fontFamily: EN}}>Product screen</span> : <>产品画面 · <span style={{fontFamily: EN}}>Product screen</span></>}
        </div>
      </div>
      <div style={{position: 'relative', width: w, height: H, overflow: 'hidden'}}>
        {screenFor(lang, previous.state) !== screenFor(lang, current.state) && k < 1 && screen(previous.state, 1)}
        {screen(current.state, screenFor(lang, previous.state) !== screenFor(lang, current.state) ? k : 1)}
        {(current.rings ?? []).map((ring) => {
          const r = region(screenFor(lang, ring.state ?? current.state), ring.name);
          // Rings leave just before the next shot; the last shot's stay until the window goes.
          const show = rise(t, ring.at, 0.35) * (Number.isFinite(next) ? 1 - rise(t, next - 0.25, 0.25) : 1);
          const grow = 1 + 0.04 * Math.sin((t - ring.at) * Math.PI * 1.6);
          const color = ring.color ?? C.gold;
          return (
            <div
              key={`${ring.name}-${ring.at}`}
              style={{
                position: 'absolute',
                left: cam.x + cam.s * (r.x - 8),
                top: cam.y + cam.s * (r.y - 8),
                width: cam.s * (r.w + 16),
                height: cam.s * (r.h + 16),
                borderRadius: 14 * cam.s,
                border: `${Math.max(4, 3 * cam.s)}px solid ${color}`,
                boxShadow: `0 0 26px ${color}`,
                opacity: show,
                transform: `scale(${grow})`,
              }}
            />
          );
        })}
      </div>
    </div>
  );
};

/** Product screens on view (0..1): the concept-illustration tag steps aside for them. */
const productOnScreen = (t: number, segments: Segment[]) => {
  const rd08 = seg(segments, 'rd08');
  const rd10 = seg(segments, 'rd10');
  return Math.max(
    rise(t, beat(rd08, 2) - 0.5, 0.6) * (1 - rise(t, beat(rd08, 4) - 0.4, 0.6)),
    rise(t, beat(rd10, 2) - 0.5, 0.6) * (1 - rise(t, beat(rd10, 3) - 0.45, 0.6)),
  );
};

// ─── Scenes ───────────────────────────────────────────────────────────────

type SceneProps = {t: number; s: Segment};

const RD01: React.FC<SceneProps> = ({t, s}) => {
  const swap = rise(t, beat(s, 3) - 0.4, 0.8);
  return (
    <>
      <Picture name="rd01-listen" t={t} from={s.start} to={beat(s, 3)} />
      <AbsoluteFill style={{opacity: swap}}>
        <Picture name="rd01-read-alone" t={t} from={beat(s, 3)} to={s.end} zoom={[1.04, 1.12]} origin="45% 45%" />
      </AbsoluteFill>
      <Row x={960} y={70}>
        <Chip kind="book" zh="认字·拼写" en="Word reading · spelling" show={rise(t, beat(s, 5))} lit={rise(t, beat(s, 5), 0.4)} color={C.gold} />
        <Chip kind="ear" zh="听懂" en="Understanding" show={rise(t, beat(s, 6, 0.35))} />
        <Chip kind="talk" zh="表达" en="Telling" show={rise(t, beat(s, 6, 0.55))} />
      </Row>
    </>
  );
};

const RD02: React.FC<SceneProps> = ({t, s}) => {
  const understand = beat(s, 2);
  const word = beat(s, 3);
  const step = s.chunks[1].slot / 3;
  return (
    <>
      <Picture name="rd02-support" t={t} from={s.start} to={s.end} dim={0.12} />
      <Card zh="这个孩子需要什么帮助？" en="What help does this child need?" x={960} y={60} show={rise(t, beat(s, 1)) * (1 - rise(t, understand - 0.3, 0.4))} />
      <div style={{position: 'absolute', left: 90, top: 70, opacity: rise(t, understand - 0.2)}}>
        <TaskCard zh="理解故事" en="Understand a story" color={C.teal}>
          <Chip kind="ear" zh="听" en="Listen" show={1} lit={rise(t, understand + 0.2)} color={C.teal} />
          <Chip kind="picture" zh="看图" en="Look" show={1} lit={rise(t, understand + step)} color={C.teal} />
          <Chip kind="talk" zh="聊一聊" en="Talk" show={1} lit={rise(t, understand + 2 * step)} color={C.teal} />
        </TaskCard>
      </div>
      <div style={{position: 'absolute', right: 90, top: 70, opacity: rise(t, word - 0.2)}}>
        <TaskCard zh="练认字" en="Practise word reading" color={C.coral}>
          <Chip kind="book" zh="读" en="Read" show={1} lit={rise(t, word + 0.3)} color={C.coral} />
          <Chip kind="check" zh="合适的帮助" en="Suitable support" show={1} lit={rise(t, word + s.chunks[2].slot * 0.6)} color={C.coral} />
        </TaskCard>
      </div>
    </>
  );
};

const TaskCard: React.FC<{zh: string; en: string; color: string; children: React.ReactNode}> = ({zh, en, color, children}) => {
  const english = useLang() === 'en';
  return (
    <div style={{background: 'rgba(255,253,248,0.93)', borderRadius: 28, padding: '22px 28px 28px', boxShadow: C.shadow, borderTop: `8px solid ${color}`}}>
      {english ? (
        <div style={{fontFamily: EN, fontSize: 40, fontWeight: 800, color, marginBottom: 18}}>{en}</div>
      ) : (
        <>
          <div style={{fontFamily: ZH, fontSize: 46, fontWeight: 800, color}}>{zh}</div>
          <div style={{fontFamily: EN, fontSize: 26, fontWeight: 600, color: C.soft, marginBottom: 18}}>{en}</div>
        </>
      )}
      <div style={{display: 'flex', flexDirection: 'column', gap: 14}}>{children}</div>
    </div>
  );
};

const RD03: React.FC<SceneProps> = ({t, s}) => (
  <>
    <Picture name="rd03-classroom" t={t} from={s.start} to={s.end} dim={0.45} />
    <Card zh="能听懂中文" en="Understands spoken Chinese" x={560} y={120} w={640} show={rise(t, beat(s, 2))} color={C.teal} size={46} />
    <Card zh="还在学汉字" en="Still learning characters" x={560} y={330} w={640} show={rise(t, beat(s, 2, 0.5))} color={C.gold} size={46} />
    <Card zh="读中文比较顺" en="Reads Chinese more easily" x={1360} y={120} w={640} show={rise(t, beat(s, 3))} color={C.teal} size={46} />
    <Card zh="讲英文需要帮助" en="Needs help speaking English" x={1360} y={330} w={640} show={rise(t, beat(s, 3, 0.5))} color={C.gold} size={46} />
    <Card zh="原因不同" en="Different causes from dyslexia" x={960} y={560} show={rise(t, beat(s, 4)) * (1 - rise(t, beat(s, 5) - 0.3, 0.4))} color={C.soft} size={40} />
    <Card zh="哪一步难？ 还能从哪里开始？" en="Which step is difficult? Where else can we begin?" x={960} y={540} show={rise(t, beat(s, 5))} color={C.coral} size={52} />
  </>
);

/** Where the two children stand in rd04-two-doors / rd10-together (tune to the art). */
const DOORS = {mary: [300, 610] as [number, number], jacob: [1560, 610] as [number, number]};

const RD04: React.FC<SceneProps> = ({t, s}) => {
  const english = useLang() === 'en';
  const zhArrow = rise(t, beat(s, 3, 0.05), 1.1);
  const enArrow = rise(t, beat(s, 3, 0.5), 1.1);
  return (
    <>
      <Picture name="rd04-two-doors" t={t} from={s.start} to={s.end} zoom={[1.0, 1.06]} />
      <NameTag name="Mary" color={C.coral} x={DOORS.mary[0]} y={DOORS.mary[1] + 150} show={rise(t, beat(s, 2, 0.5))} />
      <NameTag name="Jacob" color={C.teal} x={DOORS.jacob[0]} y={DOORS.jacob[1] + 150} show={rise(t, beat(s, 2))} />
      <Arrow from={[DOORS.jacob[0] - 90, 360]} to={[DOORS.mary[0] + 90, 360]} bend={-120} color={C.teal} draw={zhArrow} label={english ? 'Chinese' : '中文'} labelFont={english ? EN : ZH} />
      <Arrow from={[DOORS.mary[0] + 90, 470]} to={[DOORS.jacob[0] - 90, 470]} bend={110} color={C.coral} draw={enArrow} label="English" labelFont={EN} />
      <Card zh="互惠" en="Reciprocity" x={960} y={40} show={rise(t, beat(s, 4)) * (1 - rise(t, beat(s, 5) - 0.3, 0.4))} color={C.gold} size={54} />
      <Card zh="都教，也都学" en="Both teach · both learn" x={960} y={40} show={rise(t, beat(s, 5))} color={C.gold} size={54} />
    </>
  );
};

const NameTag: React.FC<{name: string; color: string; x: number; y: number; show: number}> = ({name, color, x, y, show}) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y,
      transform: `translate(-50%, ${(1 - show) * 20}px)`,
      opacity: show,
      background: color,
      color: 'white',
      borderRadius: 40,
      padding: '10px 34px',
      boxShadow: C.shadow,
      whiteSpace: 'nowrap',
      fontFamily: EN,
      fontSize: 44,
      fontWeight: 700,
    }}
  >
    {name}
  </div>
);

const RD05: React.FC<SceneProps> = ({t, s}) => {
  const english = useLang() === 'en';
  return (
  <>
    <Picture name="rd05-shared-paper" t={t} from={s.start} to={s.end} zoom={[1.08, 1.0]} origin="50% 60%" />
    <Card zh="共同的渠道" en="A channel they share" x={960} y={50} show={rise(t, beat(s, 5)) * (1 - rise(t, beat(s, 6) - 0.3, 0.4))} color={C.gold} size={54} />
    {english ? (
      <Bubble text="Is this what you meant?" x={560} y={150} show={rise(t, beat(s, 6, 0.3), 0.4)} color={C.coral} tail="right" font={EN} />
    ) : (
      <Bubble text="是这个意思吗？" x={420} y={150} show={rise(t, beat(s, 6, 0.3), 0.4)} color={C.coral} tail="right" />
    )}
  </>
  );
};

/** Faces in rd06-pointing: Mary left, Jacob right. Bubbles sit beside, not above, the heads. */
const TABLE = {mary: [660, 300] as [number, number], jacob: [1410, 290] as [number, number]};
const BUBBLE = {mary: [330, 170] as [number, number], jacob: [1600, 170] as [number, number]};

const RD06: React.FC<SceneProps> = ({t, s}) => {
  const panels = s.chunks[0];
  const toPointing = rise(t, beat(s, 2) - 0.4, 0.7);
  const toTeacher = rise(t, beat(s, 8) - 0.4, 0.7);
  // Who is speaking right now: [speaker, text, font] -- one language at a time.
  const lines: {at: number; to: number; who: 'jacob' | 'mary'; text: string; font: string}[] = [
    {at: beat(s, 2, 0.35), to: beat(s, 3), who: 'jacob', text: '我来帮你。', font: ZH},
    {at: beat(s, 3, 0.45), to: beat(s, 4), who: 'mary', text: 'Let me help you.', font: EN},
    {at: beat(s, 5, 0.05), to: beat(s, 5, 0.55), who: 'mary', text: '我来帮你。', font: ZH},
    {at: beat(s, 5, 0.55), to: beat(s, 6), who: 'jacob', text: 'Let me help you.', font: EN},
  ];
  return (
    <>
      <Picture name="rd06-story-panels" t={t} from={s.start} to={beat(s, 2)} zoom={[1.0, 1.04]} />
      {/* Reveal the three drawn panels one after another, left to right. */}
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: (1920 / 3) * i,
            top: 0,
            width: 1920 / 3 + 1,
            height: 1080,
            background: '#f7efe2',
            opacity: 1 - rise(t, panels.start + panels.slot * (0.12 + i * 0.28), 0.6),
          }}
        />
      ))}
      <AbsoluteFill style={{opacity: toPointing}}>
        <Picture name="rd06-pointing" t={t} from={beat(s, 2)} to={beat(s, 8)} zoom={[1.02, 1.07]} />
        {lines.map((line) => {
          const on = rise(t, line.at, 0.35) * (1 - rise(t, line.to - 0.2, 0.3));
          const [x, y] = TABLE[line.who];
          return (
            <React.Fragment key={`${line.at}`}>
              <Glow x={x} y={y} r={150} color={line.who === 'jacob' ? C.teal : C.coral} show={on} t={t} />
              <Bubble text={line.text} x={BUBBLE[line.who][0]} y={BUBBLE[line.who][1]} show={on} color={line.who === 'jacob' ? C.teal : C.coral} tail={line.who === 'jacob' ? 'left' : 'right'} font={line.font} />
            </React.Fragment>
          );
        })}
        <Card zh="交换" en="Switch" x={960} y={60} show={rise(t, beat(s, 4)) * (1 - rise(t, beat(s, 5, 0.1), 0.4))} color={C.gold} />
        <Row x={960} y={70}>
          <Chip kind="sound" zh="听一听，再试一次" en="Listen, try again" show={rise(t, beat(s, 6)) * (1 - rise(t, beat(s, 7) - 0.2, 0.4))} lit={1} color={C.teal} />
        </Row>
        <WordCard show={rise(t, beat(s, 7, 0.3)) * (1 - toTeacher)} />
      </AbsoluteFill>
      <AbsoluteFill style={{opacity: toTeacher}}>
        <Picture name="rd06-teacher" t={t} from={beat(s, 8)} to={s.end} />
        <Row x={960} y={70}>
          <Chip kind="check" zh="确认意思" en="Check the meaning" show={rise(t, beat(s, 8, 0.3))} lit={1} color={C.gold} />
        </Row>
      </AbsoluteFill>
    </>
  );
};

/** The unfamiliar written word, found and learned together. */
const WordCard: React.FC<{show: number}> = ({show}) => (
  <div
    style={{
      position: 'absolute',
      left: 960,
      top: 60,
      transform: `translateX(-50%) scale(${0.85 + 0.15 * show})`,
      opacity: show,
      background: C.paper,
      borderRadius: 28,
      padding: '18px 48px',
      boxShadow: C.shadow,
      borderTop: `8px solid ${C.gold}`,
      textAlign: 'center',
    }}
  >
    <div style={{fontFamily: EN, fontSize: 34, color: C.soft}}>bāng</div>
    <div style={{fontFamily: ZH, fontSize: 130, fontWeight: 800, color: C.ink, lineHeight: 1.05}}>帮</div>
    <div style={{fontFamily: EN, fontSize: 30, color: C.soft}}>help</div>
  </div>
);

/** The real product: the words are always there; sound and pictures come in when they help. */
const RD07: React.FC<SceneProps> = ({t, s}) => {
  const text = rise(t, beat(s, 1));
  const sound = rise(t, beat(s, 2));
  const pic = rise(t, beat(s, 3));
  const flowA = rise(t, beat(s, 5));
  const flowB = rise(t, beat(s, 6));
  const lang = useLang();
  const at = (state: string, name: string) => region(screenFor(lang, state), name);
  const verse = (state: string) => pad(union(at(state, 'verseZh'), at(state, 'verseEn')), 36);
  // The film's language is read first on screen, so it is pointed at first.
  const [firstLine, secondLine] = lang === 'en' ? ['verseEn', 'verseZh'] : ['verseZh', 'verseEn'];
  const [firstPlay, secondPlay] = lang === 'en' ? ['playEn', 'playZh'] : ['playZh', 'playEn'];
  const controls: Rect = {x: 380, y: 250, w: 960, h: 600}; // play buttons, toolbar and the speed menu
  const picture: Rect = {x: 1043, y: 430, w: 430, h: 380};
  const shots: Shot[] = [
    {at: s.start, state: 'home', focus: FULL},
    // 文字，让我们学着自己读。
    {at: beat(s, 1) - 0.2, state: 'home', focus: verse('home'), rings: [{name: firstLine, at: beat(s, 1, 0.15)}, {name: secondLine, at: beat(s, 1, 0.55)}]},
    // 声音，可以示范怎么说。 -- the play buttons, then the slower reading speeds.
    {at: beat(s, 2) - 0.2, state: 'home', focus: controls, rings: [{name: firstPlay, at: beat(s, 2, 0.05), color: C.teal}, {name: secondPlay, at: beat(s, 2, 0.25), color: C.teal}]},
    {at: beat(s, 2, 0.55), state: 'tools', focus: controls, rings: [{name: 'toolsPopover', at: beat(s, 2, 0.62), color: C.teal}]},
    // 图画，帮我们一起谈故事。
    {at: beat(s, 3) - 0.2, state: 'word', focus: picture, rings: [{name: 'wordPicture', at: beat(s, 3, 0.15), color: C.coral}]},
    // 什么时候用哪一种，要看这次想学什么。
    {at: beat(s, 4) - 0.2, state: 'home', focus: FULL, rings: [{name: 'toolbar', at: beat(s, 4, 0.15)}]},
    // 理解故事时，可以先看图、听故事。
    {at: beat(s, 5) - 0.2, state: 'word', focus: FULL, rings: [{name: 'wordPicture', at: beat(s, 5, 0.1), color: C.coral}, {name: 'listenButton', at: beat(s, 5, 0.5), color: C.teal}]},
    // 练认字时，可以先试着读，需要时再用声音和图画帮忙。 -- pinyin on demand, then a tapped word.
    {at: beat(s, 6) - 0.2, state: 'pinyin', focus: {x: 380, y: 250, w: 960, h: 420}, rings: [{name: 'verseZh', at: beat(s, 6, 0.05)}, {name: 'pinyinToggle', at: beat(s, 6, 0.35)}]},
    {at: beat(s, 6, 0.62), state: 'word', focus: {x: 1060, y: 150, w: 400, h: 580}, rings: [{name: 'wordListen', at: beat(s, 6, 0.68), color: C.teal}, {name: 'wordPicture', at: beat(s, 6, 0.8), color: C.coral}]},
  ];
  return (
    <AbsoluteFill style={{background: 'linear-gradient(170deg, #fff6e6, #f6e3c8)'}}>
      {/* Kept above the burned-in subtitles. */}
      <ProductWindow t={t} shots={shots} x={60} y={96} w={1180} />
      <div style={{position: 'absolute', left: 1290, top: 110, display: 'flex', flexDirection: 'column', gap: 22}}>
        <Chip kind="book" zh="文字：自己读" en="Words: read for ourselves" show={text} lit={t < beat(s, 4) ? text : 0} color={C.gold} />
        <Chip kind="sound" zh="声音：示范怎么说" en="Sound: how it is spoken" show={sound} lit={t < beat(s, 4) && t >= beat(s, 2) ? 1 : 0} color={C.teal} />
        <Chip kind="picture" zh="图画：一起谈" en="Pictures: talk together" show={pic} lit={t < beat(s, 4) && t >= beat(s, 3) ? 1 : 0} color={C.coral} />
      </div>
      <Flow
        x={1290}
        y={490}
        show={flowA}
        zh="理解故事"
        en="Understand a story"
        color={C.teal}
        steps={[
          {kind: 'picture', optional: false},
          {kind: 'ear', optional: false},
          {kind: 'book', optional: false},
        ]}
      />
      <Flow
        x={1290}
        y={670}
        show={flowB}
        zh="练认字"
        en="Practise word reading"
        color={C.coral}
        steps={[
          {kind: 'book', optional: false},
          {kind: 'sound', optional: true},
          {kind: 'picture', optional: true},
        ]}
      />
    </AbsoluteFill>
  );
};

const Flow: React.FC<{x?: number; y: number; show: number; zh: string; en: string; color: string; steps: {kind: IconKind; optional: boolean}[]}> = ({x = 1160, y, show, zh, en, color, steps}) => {
  const english = useLang() === 'en';
  return (
  <div style={{position: 'absolute', left: x, top: y, opacity: show, transform: `translateX(${(1 - show) * 30}px)`}}>
    {english ? (
      <div style={{fontFamily: EN, fontSize: 34, fontWeight: 800, color}}>{en}</div>
    ) : (
      <div style={{fontFamily: ZH, fontSize: 38, fontWeight: 800, color}}>
        {zh} <span style={{fontFamily: EN, fontSize: 24, fontWeight: 600, color: C.soft}}>{en}</span>
      </div>
    )}
    <div style={{display: 'flex', alignItems: 'center', gap: 14, marginTop: 10}}>
      {steps.map((step, i) => (
        <React.Fragment key={i}>
          {i > 0 && <div style={{fontFamily: EN, fontSize: 40, color: C.soft}}>→</div>}
          <div
            style={{
              width: 92,
              height: 92,
              borderRadius: 22,
              background: C.paper,
              border: `5px ${step.optional ? 'dashed' : 'solid'} ${color}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: step.optional ? 0.75 : 1,
            }}
          >
            <Icon kind={step.kind} size={58} color={color} />
          </div>
        </React.Fragment>
      ))}
      {steps.some((step) => step.optional) && (
        <div style={{fontFamily: english ? EN : ZH, fontSize: 28, color: C.soft, marginLeft: 8}}>{english ? 'when needed' : '需要时'}</div>
      )}
    </div>
  </div>
  );
};

/** Two languages growing side by side -- neither replaces the other. */
const RD08: React.FC<SceneProps> = ({t, s}) => {
  const zhGrow = rise(t, beat(s, 2), s.chunks[1].slot + s.chunks[2].slot + 3);
  const enGrow = rise(t, beat(s, 2, 0.4), s.chunks[1].slot + s.chunks[2].slot + 3);
  const english = useLang() === 'en';
  const product08 = rise(t, beat(s, 2) - 0.5, 0.6) * (1 - rise(t, beat(s, 4) - 0.4, 0.6));
  // Start in the film's own language, then flip the order: both languages stay.
  const [first, second] = english ? ['en:home', 'zh:home'] : ['zh:home', 'en:home'];
  const shots: Shot[] = [
    {at: beat(s, 2) - 0.5, state: first, focus: FULL, rings: [{name: 'langToggle', at: beat(s, 2, 0.3)}]},
    {at: beat(s, 3) - 0.2, state: second, focus: FULL, rings: [{name: 'langToggle', at: beat(s, 3, 0.1)}]},
  ];
  return (
    <>
      <div style={{position: 'absolute', left: 0, top: 0, width: 1180, height: 1080, overflow: 'hidden'}}>
        <Picture name="rd08-growing" t={t} from={s.start} to={s.end} origin="40% 40%" />
        {/* 学英文时，中文也可以继续用；学中文时，英文也有用 -- the product keeps both, in either order. */}
        <AbsoluteFill style={{background: 'linear-gradient(170deg, #fff6e6, #f6e3c8)', opacity: product08}} />
        <ProductWindow t={t} shots={shots} x={60} y={150} w={1060} opacity={product08} />
      </div>
      <div style={{position: 'absolute', left: 1180, top: 0, width: 740, height: 1080, background: 'linear-gradient(180deg, #fff8ea, #f7e8cf)'}}>
        {english ? (
          <>
            <Vine x={200} grow={zhGrow} color={C.teal} zh="Chinese" latinFirst />
            <Vine x={520} grow={enGrow} color={C.coral} zh="English" latinFirst />
          </>
        ) : (
          <>
            <Vine x={200} grow={zhGrow} color={C.teal} zh="中文" en="Chinese" />
            <Vine x={520} grow={enGrow} color={C.coral} zh="English" en="英文" latinFirst />
          </>
        )}
        <div style={{position: 'absolute', left: 0, right: 0, top: 120, opacity: rise(t, beat(s, 4)), display: 'flex', justifyContent: 'center'}}>
          <Chip kind="pencil" zh="画画，帮大家学" en="Drawing helps the group" show={1} lit={1} color={C.gold} />
        </div>
      </div>
    </>
  );
};

const Vine: React.FC<{x: number; grow: number; color: string; zh: string; en?: string; latinFirst?: boolean}> = ({x, grow, color, zh, en, latinFirst}) => {
  const height = 440 * grow;
  const base = 680;
  const leaves = [0.18, 0.34, 0.5, 0.66, 0.82];
  return (
    <>
      <svg width={740} height={1080} style={{position: 'absolute', inset: 0}}>
        <path d={`M ${x} ${base} C ${x - 40} ${base - height * 0.33} ${x + 40} ${base - height * 0.66} ${x} ${base - height}`} stroke={color} strokeWidth={14} fill="none" strokeLinecap="round" />
        {leaves.map((at, i) =>
          grow > at ? (
            <ellipse
              key={i}
              cx={x + (i % 2 ? 36 : -36)}
              cy={base - 440 * at}
              rx={34 * clamp((grow - at) * 6)}
              ry={16 * clamp((grow - at) * 6)}
              fill={color}
              opacity={0.85}
              transform={`rotate(${i % 2 ? -30 : 30} ${x + (i % 2 ? 36 : -36)} ${base - 440 * at})`}
            />
          ) : null,
        )}
        <ellipse cx={x} cy={base + 10} rx={90} ry={22} fill="#c9a77c" opacity={0.6} />
      </svg>
      <div style={{position: 'absolute', left: x - 120, width: 240, top: base + 40, textAlign: 'center'}}>
        <div style={{fontFamily: latinFirst ? EN : ZH, fontSize: 44, fontWeight: 800, color}}>{zh}</div>
        {en && <div style={{fontFamily: latinFirst ? ZH : EN, fontSize: 26, color: C.soft}}>{en}</div>}
      </div>
    </>
  );
};

/** Parent and child positions in rd09-family (tune to the art). */
const FAMILY = {parent: [560, 330] as [number, number], child: [1100, 330] as [number, number]};

const RD09: React.FC<SceneProps> = ({t, s}) => {
  const english = useLang() === 'en';
  return (
  <>
    <Picture name="rd09-family" t={t} from={s.start} to={s.end} />
    <Arrow from={[FAMILY.parent[0] + 180, 560]} to={[FAMILY.child[0] + 220, 560]} bend={-90} color={C.teal} draw={rise(t, beat(s, 3), 1.0)} label={english ? 'Meaning' : '意思'} labelFont={english ? EN : ZH} />
    <Arrow from={[FAMILY.child[0] + 220, 660]} to={[FAMILY.parent[0] + 180, 660]} bend={80} color={C.coral} draw={rise(t, beat(s, 3, 0.4), 1.0)} label="English" labelFont={EN} />
    <Row x={960} y={60}>
      <Chip kind="check" zh="一起确认" en="Check it together" show={rise(t, beat(s, 3, 0.75)) * (1 - rise(t, beat(s, 4) - 0.3, 0.3))} lit={1} color={C.gold} />
    </Row>
    <Card zh="两代人，都分享，也都学习" en="Both generations share · both learn" x={960} y={60} show={rise(t, beat(s, 4))} color={C.gold} size={48} />
  </>
  );
};

/** The title callback; the product as it is today; the shared story and the last line. */
const RD10: React.FC<SceneProps> = ({t, s}) => {
  const lang = useLang();
  const at = (state: string, name: string) => region(screenFor(lang, state), name);
  const productShown = rise(t, beat(s, 2) - 0.5, 0.6) * (1 - rise(t, beat(s, 3) - 0.45, 0.6));
  const shots: Shot[] = [
    {at: beat(s, 2) - 0.5, state: 'home', focus: FULL},
    {at: beat(s, 2, 0.33), state: 'study', focus: pad(at('study', 'dialog'), 10)},
    {at: beat(s, 2, 0.66), state: 'study-switch', focus: pad(union(at('study-switch', 'talkCard'), at('study-switch', 'switchButton')), 30), rings: [{name: 'switchButton', at: beat(s, 2, 0.72)}]},
  ];
  return (
    <>
      <Picture name="rd10-together" t={t} from={s.start} to={s.end + TIMELINES[lang].endCardSeconds} zoom={[1.08, 1.0]} />
      <Card zh="语言的桥" en="Language Bridge" x={960} y={60} show={rise(t, beat(s, 1)) * (1 - rise(t, beat(s, 2) - 0.6, 0.4))} color={C.gold} size={60} />
      {/* 我们……正在设计中英双语的多媒体学习方式 -- and here it is: 语言的桥. */}
      <AbsoluteFill style={{background: 'linear-gradient(170deg, #fff6e6, #f6e3c8)', opacity: productShown * 0.92}} />
      <ProductWindow t={t} shots={shots} x={320} y={34} w={1280} opacity={productShown} />
      <Card zh="你教我，我教你" en="You teach me, I teach you" x={960} y={60} show={rise(t, beat(s, 4))} color={C.gold} size={64} />
    </>
  );
};

const SCENES: Record<string, React.FC<SceneProps>> = {rd01: RD01, rd02: RD02, rd03: RD03, rd04: RD04, rd05: RD05, rd06: RD06, rd07: RD07, rd08: RD08, rd09: RD09, rd10: RD10};

// Scenes that show illustrations of people carry the concept label.
const LABELLED = new Set(['rd01', 'rd02', 'rd03', 'rd04', 'rd05', 'rd06', 'rd08', 'rd09', 'rd10']);

const TitleCard: React.FC<{t: number}> = ({t}) => {
  const lang = useLang();
  const english = lang === 'en';
  return (
    <>
      <Picture name="rd04-two-doors" t={t} from={0} to={TIMELINES[lang].titleSeconds} zoom={[1.1, 1.05]} dim={0.55} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: rise(t, 0.3, 0.9)}}>
        <div style={{fontFamily: EN, fontSize: 32, letterSpacing: 6, color: C.soft, marginBottom: 18}}>LUCAS ACADEMY</div>
        {english ? (
          <>
            <div style={{fontFamily: EN, fontSize: 112, fontWeight: 800, color: C.ink}}>Language Bridge</div>
            <div style={{fontFamily: EN, fontSize: 56, fontWeight: 600, color: C.teal, marginTop: 14}}>You teach me, I teach you</div>
          </>
        ) : (
          <>
            <div style={{fontFamily: ZH, fontSize: 104, fontWeight: 800, color: C.ink}}>语言的桥：你教我，我教你</div>
            <div style={{fontFamily: EN, fontSize: 40, fontWeight: 600, color: C.teal, marginTop: 18}}>Language Bridge · You teach me, I teach you</div>
          </>
        )}
      </AbsoluteFill>
    </>
  );
};

const NIV =
  'English Scripture in the product screens: The Holy Bible, New International Version® NIV® Copyright © 1973, 1978, 1984, 2011 by Biblica, Inc.®';
const NIV_2 = 'Used by permission of Biblica, Inc.® All rights reserved worldwide.';

const EndCard: React.FC<{t: number; from: number}> = ({t, from}) => {
  const english = useLang() === 'en';
  return (
    <AbsoluteFill style={{background: C.cream, opacity: rise(t, from, 1.0), alignItems: 'center', justifyContent: 'center'}}>
      {english ? (
        <div style={{fontFamily: EN, fontSize: 88, fontWeight: 800, color: C.ink}}>You teach me, I teach you</div>
      ) : (
        <>
          <div style={{fontFamily: ZH, fontSize: 92, fontWeight: 800, color: C.ink}}>你教我，我教你</div>
          <div style={{fontFamily: EN, fontSize: 40, fontWeight: 600, color: C.teal, marginTop: 10}}>You teach me, I teach you</div>
        </>
      )}
      <div style={{marginTop: 64, display: 'flex', alignItems: 'baseline', gap: 22}}>
        <span style={{fontFamily: english ? EN : ZH, fontSize: 36, fontWeight: 700, color: C.ink}}>{english ? 'Language Bridge' : '语言的桥'}</span>
        <span style={{fontFamily: EN, fontSize: 40, fontWeight: 700, color: C.teal}}>lang.lucasacademy.org</span>
      </div>
      <div style={{fontFamily: EN, fontSize: 28, color: C.soft, marginTop: 14}}>lucasacademy.org/weekly</div>
      <div style={{fontFamily: english ? EN : ZH, fontSize: 24, color: C.soft, marginTop: 44, textAlign: 'center', lineHeight: 1.6}}>
        {english ? (
          'A teaching idea with fictional examples and concept illustrations.'
        ) : (
          <>
            教学构想与概念示例；人物为虚构，插画为概念示意。
            <br />
            <span style={{fontFamily: EN}}>A teaching idea with fictional examples and concept illustrations.</span>
          </>
        )}
      </div>
      <div style={{fontFamily: EN, fontSize: 18, color: C.soft, marginTop: 26, textAlign: 'center', lineHeight: 1.5, maxWidth: 1300, opacity: 0.9}}>
        {NIV}
        <br />
        {NIV_2} · {english ? 'Chinese Scripture source: YouVersion' : <span style={{fontFamily: ZH}}>中文经文来源：YouVersion</span>}
      </div>
    </AbsoluteFill>
  );
};

// ─── Subtitles (burned in: the owner wants them in the picture) ────────────

const Subtitles: React.FC<{t: number; segments: Segment[]; lang: Lang}> = ({t, segments, lang}) => {
  const chunks = segments.flatMap((s) => s.chunks);
  const index = chunks.findIndex((c) => t >= c.start - 0.1 && t < c.start + c.slot + 0.35);
  if (index < 0) return null;
  const chunk = chunks[index];
  // Same cue times as the SRT: linger a little, never into the next line.
  const until = Math.min(chunk.start + chunk.slot + 0.35, (chunks[index + 1]?.start ?? Infinity) - 0.05);
  if (t >= until) return null;
  const opacity = Math.min(rise(t, chunk.start - 0.1, 0.2), 1 - rise(t, until - 0.2, 0.2));
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 40, display: 'flex', justifyContent: 'center', opacity}}>
      <div style={{maxWidth: 1640, background: 'rgba(40, 30, 26, 0.74)', borderRadius: 22, padding: '14px 40px 16px', textAlign: 'center'}}>
        {lang === 'en' ? (
          <div style={{fontFamily: EN, fontSize: 44, fontWeight: 600, color: 'white', lineHeight: 1.3}}>{chunk.en}</div>
        ) : (
          <>
            <div style={{fontFamily: ZH, fontSize: 48, fontWeight: 600, color: 'white', lineHeight: 1.35}}>{chunk.zh}</div>
            <div style={{fontFamily: EN, fontSize: 28, fontWeight: 500, color: '#f6e7cf', lineHeight: 1.3, marginTop: 4}}>{chunk.en}</div>
          </>
        )}
      </div>
    </div>
  );
};

// ─── Film ─────────────────────────────────────────────────────────────────

const FADE = 0.5;

export const LanguageBridgeVideo: React.FC<LanguageBridgeProps> = ({lang, audio, subtitles}) => {
  const frame = useCurrentFrame();
  const t = frame / RD_FPS;
  const timeline = TIMELINES[lang];
  const segments = timeline.segments;
  const last = segments.at(-1)!;
  return (
    <Film.Provider value={{lang, segments}}>
      <AbsoluteFill style={{background: C.cream}}>
        {audio && <Narration track={lang} segments={segments} />}
        {t < timeline.titleSeconds + FADE && (
          <AbsoluteFill style={{opacity: 1 - rise(t, timeline.titleSeconds - FADE / 2, FADE)}}>
            <TitleCard t={t} />
          </AbsoluteFill>
        )}
        {segments.map((s, i) => {
          const Scene = SCENES[s.id];
          const end = i === segments.length - 1 ? timeline.durationSeconds : s.end;
          if (t < s.start - FADE || t > end + FADE) return null;
          const opacity = rise(t, s.start - FADE / 2, FADE) * (i === segments.length - 1 ? 1 : 1 - rise(t, s.end - FADE / 2, FADE));
          return (
            <AbsoluteFill key={s.id} style={{opacity}}>
              <Scene t={t} s={s} />
              {LABELLED.has(s.id) && <div style={{opacity: 1 - productOnScreen(t, segments)}}><ConceptTag /></div>}
            </AbsoluteFill>
          );
        })}
        <EndCard t={t} from={last.end} />
        {subtitles && <Subtitles t={t} segments={segments} lang={lang} />}
      </AbsoluteFill>
    </Film.Provider>
  );
};
