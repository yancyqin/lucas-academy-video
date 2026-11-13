import type {CSSProperties, FC, ReactNode} from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import timeline from '../../data/impressionism-secret.json';
import {ChapterBar, type Chapter} from '../middle-income-trap/ChapterBar';
import strokesData from '../../data/impressionism-strokes.json';
import {CLIPS, IMG, type ClipId, type ImgId} from './assets.generated';
import {CAMILLE, FACES, RECAP, SHOTS, type Beat, type Cam, type CamKey, type Mark, type Name, type Shot} from './shots';

/**
 * 你知道印象派的秘密吗？ / Do You Know the Secret of Impressionism?
 * By Eunice Yue, Yancy Qin | Lucas Academy.
 *
 * One picture edit carries the Chinese track and the English dub (the cue
 * timeline uses max(zh, en) per line), so the picture carries almost no words:
 * names, years, MANET/MONET and the chapter bar (English over Chinese). Captions are YouTube SRTs. Paintings are real
 * works; the moving scenes are the owner's AI clips (Muse; one MiniMax), said in the description, not on screen.
 * v10 (owner 2026-11-04): no Codex picture any more; every circle follows the owner's own hand-drawn stroke.
 */

export type ImpressionismProps = {audio: 'zh' | 'en' | 'none'};
export const IMP_FPS = timeline.fps;
export const IMP_DURATION = Math.ceil(timeline.durationSeconds * timeline.fps);

const FADE = 18;
const PIC = {top: 40, bottom: 1040, width: 1840};
const PIC_H = PIC.bottom - PIC.top;
const PIC_CY = (PIC.top + PIC.bottom) / 2;
const ZH_FONT = '"PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif';
const EN_FONT = '"Avenir Next", "Helvetica Neue", Arial, sans-serif';
const SERIF = 'Didot, Georgia, "Songti SC", serif';
const INK = '#f6efe0';
const GOLD = '#e9b93a';
const BG = '#140f0c';

const cueById = new Map(timeline.cues.map((c) => [c.id, c]));
const ease = Easing.bezier(0.42, 0, 0.58, 1);
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const src = (id: ImgId) => staticFile(`impressionism-secret/img/${id}${IMG[id].ext}`);
const tile = (id: ImgId) => staticFile(`impressionism-secret/tiles/${id}.jpg`);

type Placed = {left: number; top: number; w: number; h: number};
type Frame = {x: number; y: number; w: number; h: number};
const FULL: Frame = {x: 960 - PIC.width / 2, y: PIC.top, w: PIC.width, h: PIC_H};

/**
 * The camera at p: one smooth curve through every key (monotone cubic, still at the
 * first and last key), so a move through a middle key keeps going instead of
 * stopping there and starting again.
 */
function camAt(keys: Cam[], p: number): Cam {
  if (keys.length === 1 || p <= keys[0].t) return keys[0];
  const n = keys.length - 1;
  if (p >= keys[n].t) return keys[n];
  let i = 0;
  while (p > keys[i + 1].t) i++;
  const a = keys[i];
  const b = keys[i + 1];
  const h = Math.max(1e-6, b.t - a.t);
  const s = (p - a.t) / h;
  const slope = (j: number, c: 'x' | 'y' | 'z') => (keys[j + 1][c] - keys[j][c]) / Math.max(1e-6, keys[j + 1].t - keys[j].t);
  const tangent = (j: number, c: 'x' | 'y' | 'z') => {
    if (j === 0 || j === n) return 0;
    const d0 = slope(j - 1, c);
    const d1 = slope(j, c);
    return d0 * d1 > 0 ? 2 / (1 / d0 + 1 / d1) : 0;
  };
  const curve = (c: 'x' | 'y' | 'z') => {
    const s2 = s * s;
    const s3 = s2 * s;
    return (2 * s3 - 3 * s2 + 1) * a[c] + (s3 - 2 * s2 + s) * h * tangent(i, c) + (-2 * s3 + 3 * s2) * b[c] + (s3 - s2) * h * tangent(i + 1, c);
  };
  return {t: p, x: curve('x'), y: curve('y'), z: curve('z')};
}

/**
 * v kept between the edges a and b, slowing into an edge over the last `ease` px
 * (exponential approach, same speed as v where it meets the free middle), so a camera
 * that asks to go past an edge glides to a stop there.
 */
const EDGE_EASE = 0.1; // of the picture's size on screen in that direction
/** How far a picture must outgrow the frame (a fraction of the frame) before the camera's aim fully applies. */
const AIM_IN = 0.35;
const smoothstep = (u: number) => {
  const k = Math.max(0, Math.min(1, u));
  return k * k * (3 - 2 * k);
};
function soften(v: number, a: number, b: number, ease: number): number {
  const lo = Math.min(a, b);
  const hi = Math.max(a, b);
  const m = Math.min(ease, (hi - lo) / 2);
  if (m <= 1e-6) return lo;
  if (v > hi - m) return hi - m * Math.exp(-(v - (hi - m)) / m);
  if (v < lo + m) return lo + m * Math.exp((v - (lo + m)) / m);
  return v;
}

/** Where a picture lands for a camera, fitted (z = 1) inside a frame box. */
function place(id: ImgId, cam: Cam, box: Frame = FULL): Placed {
  const {w, h} = IMG[id];
  const s = Math.min(box.w / w, box.h / h) * cam.z;
  // While the picture is no wider (taller) than the frame it stays centred that way; the
  // camera's aim comes in smoothly as the picture outgrows the frame. Aiming off-centre
  // right as the picture reached the frame's size pinned it to an edge for a moment and
  // then let it rush on: the shake in the Salon chapter's zooms.
  const gx = smoothstep((w * s / box.w - 1) / AIM_IN);
  const gy = smoothstep((h * s / box.h - 1) / AIM_IN);
  let left = box.x + box.w / 2 - (0.5 + (cam.x - 0.5) * gx) * w * s;
  let top = box.y + box.h / 2 - (0.5 + (cam.y - 0.5) * gy) * h * s;
  // Keep the picture between the frame's edges: inside the frame while it is smaller,
  // covering it once larger. Both limits meet as the picture outgrows the frame, so
  // nothing jumps there; and the camera eases into an edge instead of hitting it,
  // which used to stop or bounce a pan mid-move (the Salon chapter's "shake").
  left = soften(left, box.x, box.x + box.w - w * s, EDGE_EASE * w * s);
  top = soften(top, box.y, box.y + box.h - h * s, EDGE_EASE * h * s);
  return {left, top, w: w * s, h: h * s};
}

/**
 * Camera keys with `at` (a cue) become progress through [s, e] (frames of the shot); keys keep their order.
 */
function resolveCam(keys: CamKey[], clock: Clock, s: number, e: number): Cam[] {
  const span = Math.max(1, e - s);
  let last = 0;
  return keys.map((k) => {
    const t = k.at ? (clock.at(k.at, k.delay) - s) / span : k.t ?? 0;
    last = Math.max(last, Math.min(1, Math.max(0, t)));
    return {t: last, x: k.x, y: k.y, z: k.z};
  });
}

/** Cue times as frames relative to the start of the current shot. */
type Clock = {at: (id: string, delay?: number) => number; end: (id: string) => number};
const makeClock = (start: number, fps: number): Clock => ({
  at: (id, delay = 0) => {
    const c = cueById.get(id)!;
    return Math.round((c.start + 0.2 + delay * (c.end - c.start)) * fps) - start;
  },
  end: (id) => Math.round(cueById.get(id)!.end * fps) - start,
});

const Backdrop: FC<{id: ImgId; dim?: number}> = ({id, dim = 0.32}) => (
  <Img src={tile(id)} style={{position: 'absolute', inset: -80, width: 2080, height: 1240, objectFit: 'cover',
    filter: `blur(48px) brightness(${dim}) saturate(0.8)`}} />
);

/**
 * A picture at its intrinsic size, moved and scaled with a transform: slow camera
 * moves then glide by sub-pixels instead of snapping a re-laid-out box every frame.
 */
const Pic: FC<{id: ImgId; at: Placed; style?: CSSProperties; shadow?: boolean}> = ({id, at, style, shadow}) => {
  const {w, h} = IMG[id];
  return (
    <Img src={src(id)} style={{position: 'absolute', left: 0, top: 0, width: w, height: h, transformOrigin: '0 0',
      transform: `translate(${at.left}px, ${at.top}px) scale(${at.w / w}, ${at.h / h})`,
      boxShadow: shadow ? `0 ${18 * w / at.w}px ${60 * w / at.w}px rgba(0,0,0,0.55)` : undefined, ...style}} />
  );
};

/** A painting under a moving camera, with the blurred copy filling the frame. */
const Painting: FC<{id: ImgId; cam: Cam; dim?: number; blur?: number}> = ({id, cam, dim = 0, blur = 0}) => (
  <AbsoluteFill style={{overflow: 'hidden'}}>
    <Backdrop id={id} />
    <Pic id={id} at={place(id, cam)} shadow style={blur ? {filter: `blur(${(blur * IMG[id].w) / place(id, cam).w}px)`} : undefined} />
    {dim > 0 && <AbsoluteFill style={{background: `rgba(10,8,6,${dim})`}} />}
  </AbsoluteFill>
);

const YearChip: FC<{year: string; opacity: number}> = ({year, opacity}) => (
  <div style={{position: 'absolute', left: 56, top: 40, opacity, fontFamily: SERIF, fontSize: 64, color: INK,
    textShadow: '0 2px 16px rgba(0,0,0,0.7)'}}>{year}</div>
);

type StrokeSet = {img: string; drawn: boolean; strokes: number[][][]};
const STROKES = strokesData as Record<string, StrokeSet>;
// Slow enough to watch the pen go round (owner 2026-11-04: "视频是要画出来，不是直接出现个圈").
const DRAW = 36; // frames to draw one loop

/** The point a fraction p of the way along a polyline (by length): where the pen is. */
function pointAlong(pts: [number, number][], p: number): [number, number] {
  const seg = pts.slice(1).map((q, i) => Math.hypot(q[0] - pts[i][0], q[1] - pts[i][1]));
  let left = p * seg.reduce((a, b) => a + b, 0);
  for (let i = 0; i < seg.length; i++) {
    if (left <= seg[i]) {
      const k = seg[i] ? left / seg[i] : 0;
      return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k];
    }
    left -= seg[i];
  }
  return pts[pts.length - 1];
}

/** A polyline through points, smoothed with quadratic curves through the midpoints. */
function smoothPath(pts: [number, number][]): string {
  if (pts.length < 3) return pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`).join(' ');
  let d = `M${pts[0][0].toFixed(1)} ${pts[0][1].toFixed(1)}`;
  for (let i = 1; i < pts.length - 1; i++) {
    const mx = (pts[i][0] + pts[i + 1][0]) / 2;
    const my = (pts[i][1] + pts[i + 1][1]) / 2;
    d += ` Q${pts[i][0].toFixed(1)} ${pts[i][1].toFixed(1)} ${mx.toFixed(1)} ${my.toFixed(1)}`;
  }
  const l = pts[pts.length - 1];
  return `${d} L${l[0].toFixed(1)} ${l[1].toFixed(1)}`;
}

/**
 * Hand-drawn gold loops, drawn on from the mark's cue with the pen visible as it goes round (owner 2026-11-04:
 * "视频是要画出来，不是直接出现个圈"); closed, no overlap. The loops are mine; the owner's drawing only placed
 * Titian's two (circle_pack.py, marks.json). Several strokes for one mark are drawn one after another. They ride
 * the picture at sub-pixel positions, as the picture itself moves.
 */
const Marks: FC<{marks?: Mark[]; at: Placed; clock: Clock; frame: number; len: number}> = ({marks, at, clock, frame, len}) => {
  const shown = (marks ?? []).map((m) => {
    const t0 = clock.at(m.at, m.delay);
    const t1 = m.until ? clock.end(m.until) : len;
    return {m, t0, o: interpolate(frame, [t0, t0 + 2, t1 - 10, t1], [0, 1, 1, 0], clamp)};
  }).filter(({o}) => o > 0);
  if (!shown.length) return null;
  return (
    <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
      <defs>
        <filter id="imp-gold-glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="7" /></filter>
      </defs>
      {shown.map(({m, t0, o}, i) => {
        const set = STROKES[m.id];
        if (!set) return null;
        return (
          <g key={i} opacity={o}>
            {set.strokes.map((st, j) => {
              const p = interpolate(frame, [t0 + j * DRAW, t0 + (j + 1) * DRAW], [0, 1], {...clamp, easing: Easing.inOut(Easing.sin)});
              if (p <= 0) return null;
              const pts = st.map(([x, y]) => [at.left + x * at.w, at.top + y * at.h] as [number, number]);
              const d = smoothPath(pts);
              const dash = {pathLength: 1, strokeDasharray: '1 1', strokeDashoffset: 1 - p, fill: 'none', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
              const [tx, ty] = pointAlong(pts, p);
              const pen = p < 1 ? interpolate(p, [0, 0.06, 0.9, 1], [0, 1, 1, 0], clamp) : 0;
              return (
                <g key={j}>
                  <path d={d} stroke={GOLD} strokeWidth={13} opacity={0.55} filter="url(#imp-gold-glow)" {...dash} />
                  <path d={d} stroke={GOLD} strokeWidth={6} {...dash} />
                  {pen > 0 && (
                    <>
                      <circle cx={tx} cy={ty} r={16} fill="#fff3c4" opacity={0.5 * pen} filter="url(#imp-gold-glow)" />
                      <circle cx={tx} cy={ty} r={5} fill="#fff8e0" opacity={pen} />
                    </>
                  )}
                </g>
              );
            })}
          </g>
        );
      })}
    </svg>
  );
};

const NameTag: FC<{name: Name; opacity: number}> = ({name, opacity}) => (
  <div style={{position: 'absolute', left: 64, bottom: 150, opacity, color: INK, padding: '16px 26px', borderRadius: 12,
    background: 'rgba(20,15,12,0.66)', borderLeft: `4px solid ${GOLD}`}}>
    <div style={{fontFamily: SERIF, fontSize: 46, fontStyle: 'italic'}}>{name.en}</div>
    <div style={{fontFamily: ZH_FONT, fontSize: 27, fontWeight: 500, marginTop: 4}}>{name.zh}</div>
    <div style={{fontFamily: EN_FONT, fontSize: 24, marginTop: 6, letterSpacing: 2, opacity: 0.85}}>{name.years}</div>
  </div>
);

/** Chapter opener: the painter's real portrait with the name tag; optionally dissolving into the chapter's first painting. */
const Intro: FC<{shot: Extract<Shot, {kind: 'intro'}>; frame: number; len: number; clock: Clock}> = ({shot, frame, len, clock}) => {
  const box: Frame = {x: 360, y: 40, w: 1200, h: 1000};
  const t1 = shot.then ? clock.at(shot.then.at, shot.then.delay) : len;
  const toThen = shot.then ? interpolate(frame, [t1, t1 + 22], [0, 1], clamp) : 0;
  const p = interpolate(frame, [0, t1 + 22], [0, 1], clamp);
  return (
    <AbsoluteFill style={{background: BG}}>
      <AbsoluteFill style={{opacity: 1 - toThen}}>
        <Backdrop id={shot.img} dim={0.28} />
        <Pic id={shot.img} at={place(shot.img, {t: 0, x: 0.5, y: 0.45, z: 1 + 0.06 * p}, box)} shadow />
      </AbsoluteFill>
      {shot.then && toThen > 0 && (
        <AbsoluteFill style={{opacity: toThen}}>
          <Painting id={shot.then.img} cam={camAt(resolveCam(shot.then.cam ?? [{t: 0, x: 0.5, y: 0.5, z: 1}, {t: 1, x: 0.5, y: 0.5, z: 1.05}], clock, t1, len),
            interpolate(frame, [t1, len], [0, 1], clamp))} />
        </AbsoluteFill>
      )}
      <NameTag name={shot.name} opacity={interpolate(frame, [16, 34, Math.min(t1, len) - 10, Math.min(t1, len) + 8], [0, 1, 1, 0], clamp)} />
    </AbsoluteFill>
  );
};

/** The painters as themselves, their real portraits in a row, coming in one by one. */
const Faces: FC<{frame: number; len: number}> = ({frame, len}) => {
  const h = 380;
  const widths = FACES.map((f) => (IMG[f.img].w / IMG[f.img].h) * h);
  const gap = 26;
  const total = widths.reduce((a, b) => a + b, 0) + gap * (FACES.length - 1);
  const k = Math.min(1, 1800 / total);
  let x = 960 - (total * k) / 2;
  const step = Math.min(14, (len * 0.5) / FACES.length);
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, #2a211a 0%, #140f0c 70%)'}}>
      {FACES.map((f, i) => {
        const w = widths[i] * k;
        const at: Placed = {left: x, top: 270 - (h * k - h) / 2, w, h: h * k};
        x += w + gap * k;
        const o = interpolate(frame, [8 + i * step, 22 + i * step], [0, 1], clamp);
        return (
          <div key={f.img} style={{opacity: o}}>
            <div style={{position: 'absolute', left: at.left - 8, top: at.top - 8, width: at.w + 16, height: at.h + 16, background: '#a8843c',
              boxShadow: '0 16px 40px rgba(0,0,0,0.6)'}} />
            <Pic id={f.img} at={at} />
            <div style={{position: 'absolute', left: at.left, width: at.w, top: at.top + at.h + 26, textAlign: 'center', color: INK}}>
              <div style={{fontFamily: SERIF, fontSize: 36, fontStyle: 'italic'}}>{f.en}</div>
              <div style={{fontFamily: ZH_FONT, fontSize: 24, marginTop: 4, opacity: 0.85}}>{f.zh}</div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const Title: FC<{opacity: number}> = ({opacity}) => (
  <AbsoluteFill style={{opacity, alignItems: 'center', justifyContent: 'center',
    background: 'radial-gradient(ellipse at 50% 55%, rgba(20,15,12,0.82) 0%, rgba(20,15,12,0.55) 55%, rgba(20,15,12,0.2) 100%)'}}>
    <div style={{fontFamily: SERIF, fontSize: 84, fontStyle: 'italic', color: INK, textShadow: '0 6px 30px rgba(0,0,0,0.6)'}}>
      Do You Know the <span style={{color: GOLD}}>Secret</span> of Impressionism?
    </div>
    <div style={{fontFamily: ZH_FONT, fontSize: 50, fontWeight: 700, color: INK, marginTop: 20}}>
      你知道印象派的<span style={{color: GOLD}}>秘密</span>吗？
    </div>
    <div style={{width: 140, height: 3, background: GOLD, margin: '34px 0 20px'}} />
    <div style={{fontFamily: EN_FONT, fontSize: 30, color: INK, letterSpacing: 1}}>Eunice Yue, Yancy Qin ｜ Lucas Academy</div>
  </AbsoluteFill>
);

/** INK → GOLD. */
const mix = (k: number) => `rgb(${Math.round(246 - 13 * k)},${Math.round(239 - 54 * k)},${Math.round(224 - 166 * k)})`;

const Letters: FC<{frame: number; clock: Clock}> = ({frame, clock}) => {
  const on = interpolate(frame, [clock.at('im05-01', 0.3), clock.at('im05-01', 0.3) + 18], [0, 1], clamp);
  const gold = interpolate(frame, [clock.at('im05-03'), clock.at('im05-03') + 12], [0, 1], clamp);
  const manet = interpolate(frame, [clock.at('im05-02'), clock.at('im05-02') + 14], [0, 1], clamp);
  const row = (word: string, odd: string) => (
    <div style={{display: 'flex', gap: 34}}>
      {word.split('').map((ch, i) => (
        <span key={i} style={{color: ch === odd ? mix(gold) : INK, opacity: ch === odd ? 1 : 1 - 0.3 * gold}}>{ch}</span>
      ))}
    </div>
  );
  const cut: CSSProperties = {position: 'absolute', right: 70, bottom: 0, height: 900, opacity: manet};
  return (
    <AbsoluteFill>
      <Painting id="manet-monet-studio-boat" cam={{t: 0, x: 0.5, y: 0.5, z: 1.05}} dim={0.55} blur={2} />
      <div style={{position: 'absolute', left: 170, top: 250, opacity: on, fontFamily: SERIF, fontSize: 190, lineHeight: 1.15,
        textShadow: '0 6px 30px rgba(0,0,0,0.6)'}}>
        {row('MANET', 'A')}
        {row('MONET', 'O')}
      </div>
      <Img src={staticFile('impressionism-secret/img/manet-cutout.png')} style={{...cut, opacity: manet}} />
    </AbsoluteFill>
  );
};

const museClip = (name: string) => staticFile(`impressionism-secret/video/${name}.mp4`);
const MUSE_FRAMES = 300; // every Muse clip is 10 s; a longer slot plays it slower
/** The 60 fps copy of a clip (frames interpolated), so it can be slowed to half speed and still move smoothly. */
const smoothClip = (name: string) => museClip(`${name}.i60`);
/** The opening Salon clip, m1 reversed and slowed with interpolated frames to 26.3 s (owner: at least 25 s). */
const OPEN_FRAMES = 788;
/** The closing clip, m2 slowed the same way to 29.8 s (then a 1-2-1 three-frame blend, where minterpolate stepped), so it pulls back through the hall to the end. */
const CLOSE_FRAMES = 893;

/**
 * Paintings and the owner's clips taking turns (v6 opening; v10 throughout, owner 2026-11-04: "油画 muse 视频切换"):
 * each beat from its cue with its own camera, a short dissolve between beats. A clip registered to the painting
 * (CLIPS[clip].art) sits exactly on it, cropped to the part it covers with the painting around it, so painting
 * and clip line up through the dissolve; any other clip fills the painting's place (or the frame, `fit`).
 * A clip moves only while on screen, carrying on where it last stopped, at `rate` or just slow enough to last.
 */
const CUT = 8;
/** Show only the part of a registered clip that it covers, with soft edges into the painting around it. */
const FEATHER = 3; // percent of the picture
function feathered([x0, y0, x1, y1]: number[]): CSSProperties {
  const ramp = (dir: string, a: number, b: number) => `linear-gradient(${dir}, transparent ${a * 100}%, black ${a * 100 + FEATHER}%, black ${b * 100 - FEATHER}%, transparent ${b * 100}%)`;
  const mask = `${ramp('to right', x0, x1)}, ${ramp('to bottom', y0, y1)}`;
  return {WebkitMaskImage: mask, maskImage: mask, WebkitMaskComposite: 'source-in', maskComposite: 'intersect'};
}
const YearScene: FC<{frame: number; len: number; bg: ImgId; year: string}> = ({frame, len, bg, year}) => {
  const p = interpolate(frame, [0, len], [0, 1], clamp);
  return (
    <AbsoluteFill style={{background: BG}}>
      <Painting id={bg} cam={{t: 0, x: 0.5, y: 0.45, z: 1.1 + 0.05 * p}} dim={0.58} blur={5} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div style={{fontFamily: SERIF, fontSize: 240, color: GOLD, opacity: interpolate(frame, [8, 26], [0, 1], clamp),
          textShadow: '0 8px 40px rgba(0,0,0,0.7)'}}>{year}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Seq: FC<{shot: Extract<Shot, {kind: 'seq'}>; frame: number; len: number; clock: Clock}> = ({shot, frame, len, clock}) => {
  const starts = shot.beats.map((b, i) => (i === 0 ? 0 : b.sec !== undefined ? clock.at(b.at!) + Math.round(b.sec * IMP_FPS) : clock.at(b.at!, b.delay)));
  const used: Record<string, number> = {};
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: BG}}>
      {shot.beats.map((b: Beat, i) => {
        const s = starts[i];
        const e = i + 1 < starts.length ? starts[i + 1] + CUT : len;
        const o = i === 0 ? 1 : interpolate(frame, [s, s + CUT], [0, 1], clamp);
        const art = b.art ?? shot.art;
        if (b.show === 'year') return (
          <Sequence key={i} from={s} durationInFrames={Math.max(1, e - s)} layout="none">
            <AbsoluteFill style={{opacity: o}}>
              <YearScene frame={frame - s} len={e - s} bg={art} year={b.year ?? ''} />
            </AbsoluteFill>
          </Sequence>
        );
        const at = place(art, camAt(resolveCam(b.cam, clock, s, e), interpolate(frame, [s, e], [0, 1], clamp)));
        let video = null;
        if (b.show === 'clip') {
          const name = (b.clip ?? shot.clip)! as ClipId;
          const meta = CLIPS[name];
          const left = (meta.frames60 / 60) * IMP_FPS - 2 - (used[name] ?? 0); // frames of clip time still unplayed
          const rate = b.rate ?? Math.max(0.45, Math.min(1, left / Math.max(1, e - s)));
          const from = used[name] ?? 0;
          used[name] = from + (e - s) * rate;
          const aligned = meta.art === art && meta.inner;
          const box: CSSProperties = b.fit === 'frame'
            ? {position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}
            : {position: 'absolute', left: at.left, top: at.top, width: at.w, height: at.h, objectFit: aligned ? 'fill' : 'cover',
               ...(aligned ? feathered(meta.inner!) : {boxShadow: '0 18px 60px rgba(0,0,0,0.55)'})};
          video = (
            <>
              {aligned && <Pic id={art} at={at} shadow />}
              <OffthreadVideo src={smoothClip(name)} muted trimBefore={Math.round(from)} playbackRate={rate} style={box} />
            </>
          );
        }
        return (
          <Sequence key={i} from={s} durationInFrames={Math.max(1, e - s)} layout="none">
            <AbsoluteFill style={{opacity: o}}>
              <Backdrop id={art} />
              {video ?? (
                <>
                  <Pic id={art} at={at} shadow />
                  <Marks marks={b.marks} at={at} clock={clock} frame={frame} len={len} />
                </>
              )}
              {b.year && <YearChip year={b.year} opacity={interpolate(frame, [s + 6, s + 20, e - 14, e], [0, 1, 1, 0], clamp)} />}
            </AbsoluteFill>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const Pair: FC<{shot: Extract<Shot, {kind: 'pair'}>; frame: number; len: number; clock: Clock}> = ({shot, frame, len, clock}) => {
  const left: Frame = {x: 50, y: 110, w: 890, h: 860};
  const right: Frame = {x: 980, y: 110, w: 890, h: 860};
  const p = frame / Math.max(1, len);
  const a = place(shot.a, {t: 0, x: 0.5, y: 0.5, z: 1 + 0.03 * p}, left);
  const b = place(shot.b, {t: 0, x: 0.5, y: 0.5, z: 1 + 0.03 * p}, right);
  return (
    <AbsoluteFill style={{background: BG}}>
      <Backdrop id={shot.b} dim={0.22} />
      <Pic id={shot.a} at={a} shadow />
      <Pic id={shot.b} at={b} shadow />
      <Marks marks={shot.marksA} at={a} clock={clock} frame={frame} len={len} />
      <Marks marks={shot.marksB} at={b} clock={clock} frame={frame} len={len} />
    </AbsoluteFill>
  );
};


/** The Salon itself (Muse clip m3): from the painters into the walls full of the Salon's paintings. */
const SalonClip: FC<{len: number}> = ({len}) => (
  <AbsoluteFill style={{background: BG}}>
    <OffthreadVideo src={smoothClip('muse-m3')} muted playbackRate={Math.max(0.45, Math.min(1, MUSE_FRAMES / len))}
      style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}} />
  </AbsoluteFill>
);

const Camille: FC<{frame: number; len: number}> = ({frame, len}) => {
  const each = len / CAMILLE.length;
  return (
    <AbsoluteFill style={{background: BG}}>
      {CAMILLE.map((c, i) => {
        const s = i * each;
        const o = interpolate(frame, [s - 8, s + 10, s + each, s + each + 16], [0, 1, 1, 0], clamp);
        if (o <= 0) return null;
        const p = interpolate(frame, [s, s + each + 16], [0, 1], clamp);
        return (
          <AbsoluteFill key={c.img + i} style={{opacity: i === CAMILLE.length - 1 ? interpolate(frame, [s - 8, s + 10], [0, 1], clamp) : o}}>
            <Painting id={c.img} cam={{t: 0, x: 0.5, y: 0.45, z: 1 + 0.06 * p}} />
            <YearChip year={c.year} opacity={interpolate(frame, [s + 4, s + 12, s + each - 4, s + each + 4], [0, 1, 1, i === CAMILLE.length - 1 ? 1 : 0], clamp)} />
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};

/** The recap wall: each painter's painting lights up as their own words are said. */
const Recap: FC<{frame: number; clock: Clock}> = ({frame, clock}) => {
  const h = 300;
  const rows = [RECAP.slice(0, 3), RECAP.slice(3)];
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, #2a211a 0%, #140f0c 70%)'}}>
      {rows.map((row, r) => {
        const widths = row.map((x) => (IMG[x.img].w / IMG[x.img].h) * h);
        const gap = 40;
        let x = 960 - (widths.reduce((a, b) => a + b, 0) + gap * (row.length - 1)) / 2;
        return row.map((item, i) => {
          const at: Placed = {left: x, top: 150 + r * (h + 80), w: widths[i], h};
          x += widths[i] + gap;
          const t = clock.at(item.at, item.delay);
          const lit = interpolate(frame, [t, t + 14], [0, 1], clamp);
          const o = interpolate(frame, [4 + (r * 3 + i) * 4, 18 + (r * 3 + i) * 4], [0, 1], clamp);
          return (
            <div key={item.img} style={{opacity: o * (0.42 + 0.58 * lit)}}>
              <div style={{position: 'absolute', left: at.left - 10, top: at.top - 10, width: at.w + 20, height: at.h + 20,
                background: lit > 0.5 ? GOLD : '#a8843c', boxShadow: `0 16px 40px rgba(0,0,0,0.6), 0 0 ${40 * lit}px rgba(233,185,58,${0.6 * lit})`}} />
              <Pic id={item.img} at={at} />
            </div>
          );
        });
      })}
    </AbsoluteFill>
  );
};

/**
 * Shannon's test, played once (owner 2026-11-04, im13-05..07): the title loses some letters (Chinese: two
 * characters), the viewer fills them in, then they come back in gold.
 */
const GAME_EN = 'Do you know the secret of Impressionism?';
const GAME_ZH = '你知道印象派的秘密吗？';
const GAME_ZH_OUT = new Set([4, 8]); // 象, 密
const Game: FC<{frame: number; clock: Clock}> = ({frame, clock}) => {
  const drop = interpolate(frame, [clock.at('im13-05', 0.45), clock.at('im13-05', 0.75)], [0, 1], clamp);
  const back = interpolate(frame, [clock.at('im13-07'), clock.at('im13-07') + 24], [0, 1], clamp);
  const on = 1; // the shot's own fade brings it in over the recap; a second fade here let the recap vanish first
  const vowels = [...GAME_EN].map((ch, i) => ({ch, i, out: /[aeiouAEIOU]/.test(ch) && i > 0}));
  const nOut = vowels.filter((v) => v.out).length;
  let k = 0;
  const glyph = (ch: string, out: boolean, rank: number, n: number) => {
    const gone = out ? interpolate(drop, [rank / n, (rank + 1) / n], [0, 1], clamp) * (1 - back) : 0;
    return (
      <span style={{position: 'relative', display: 'inline-block'}}>
        <span style={{opacity: 1 - gone, color: out && back > 0 ? mix(back) : undefined}}>{ch === ' ' ? '\u00a0' : ch}</span>
        {out && <span style={{position: 'absolute', left: '8%', right: '8%', bottom: '0.08em', height: 4, background: GOLD, opacity: gone}} />}
      </span>
    );
  };
  return (
    <AbsoluteFill style={{opacity: on}}>
      <Painting id="monet-impression-sunrise" cam={{t: 0, x: 0.5, y: 0.5, z: 1.05}} dim={0.62} blur={4} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', color: INK, textShadow: '0 6px 30px rgba(0,0,0,0.6)'}}>
        <div style={{fontFamily: SERIF, fontSize: 92, fontStyle: 'italic'}}>
          {vowels.map(({ch, i, out}) => <span key={i}>{glyph(ch, out, out ? k++ : 0, nOut)}</span>)}
        </div>
        <div style={{fontFamily: ZH_FONT, fontSize: 56, fontWeight: 700, marginTop: 34, letterSpacing: 4}}>
          {[...GAME_ZH].map((ch, i) => <span key={i}>{glyph(ch, GAME_ZH_OUT.has(i), i === 4 ? 0 : 1, 2)}</span>)}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Skip: FC<{frame: number; bg: ImgId}> = ({frame, bg}) => {
  const t = Math.ceil((timeline.chapters as Record<string, number>).im05);
  const label = `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`;
  const o = interpolate(frame, [8, 24], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <Painting id={bg} cam={{t: 0, x: 0.5, y: 0.5, z: 1.2}} dim={0.65} blur={14} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: o, color: INK}}>
        <svg width="220" height="140" viewBox="0 0 220 140">
          <polygon points="10,10 100,70 10,130" fill={GOLD} />
          <polygon points="110,10 200,70 110,130" fill={GOLD} />
        </svg>
        <div style={{fontFamily: EN_FONT, fontSize: 92, fontWeight: 600, marginTop: 20, letterSpacing: 4}}>{label}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Inset: FC<{id: ImgId; side: 'left' | 'right'; o: number}> = ({id, side, o}) => {
  const h = 560;
  const w = (IMG[id].w / IMG[id].h) * h;
  return (
    <div style={{position: 'absolute', [side]: 70 - (1 - o) * 60, top: 260, width: w, height: h, opacity: o,
      border: '10px solid #a8843c', boxShadow: '0 20px 60px rgba(0,0,0,0.65)'}}>
      <Img src={src(id)} style={{width: '100%', height: '100%'}} />
    </div>
  );
};

const ShotView: FC<{shot: Shot; len: number; start: number}> = ({shot, len, start}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const clock = makeClock(start, fps);
  const p = Math.min(1, frame / Math.max(1, len));
  switch (shot.kind) {
    case 'opening': {
      const title = interpolate(frame, [clock.at(shot.title) - 6, clock.at(shot.title) + 14], [0, 1], clamp);
      // m1 reversed and slowed (26.3 s): from the whole Salon in to the painters; a longer slot plays it a little slower
      const rate = Math.max(0.6, Math.min(1, OPEN_FRAMES / Math.max(1, len)));
      return (
        <AbsoluteFill style={{background: BG}}>
          <OffthreadVideo src={museClip('muse-m1-reverse-slow')} muted playbackRate={rate}
            style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}} />
          <Title opacity={title} />
        </AbsoluteFill>
      );
    }
    case 'art': {
      const at = place(shot.img, camAt(resolveCam(shot.cam, clock, 0, len), p));
      const inset = shot.inset ? interpolate(frame, [clock.at(shot.inset.at), clock.at(shot.inset.at) + 24], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)}) : 0;
      return (
        <AbsoluteFill style={{overflow: 'hidden'}}>
          <Backdrop id={shot.img} />
          <Pic id={shot.img} at={at} shadow />
          {shot.dim ? <AbsoluteFill style={{background: `rgba(10,8,6,${shot.dim})`}} /> : null}
          <Marks marks={shot.marks} at={at} clock={clock} frame={frame} len={len} />
          {shot.inset && <Inset id={shot.inset.img} side={shot.inset.side} o={inset} />}
          {shot.year && <YearChip year={shot.year} opacity={interpolate(frame, [10, 28], [0, 1], clamp)} />}
        </AbsoluteFill>
      );
    }
    case 'pair':
      return <Pair shot={shot} frame={frame} len={len} clock={clock} />;
    case 'seq':
      return <Seq shot={shot} frame={frame} len={len} clock={clock} />;
    case 'intro':
      return <Intro shot={shot} frame={frame} len={len} clock={clock} />;
    case 'faces':
      return <Faces frame={frame} len={len} />;
    case 'salon':
      return <SalonClip len={len} />;
    case 'letters':
      return <Letters frame={frame} clock={clock} />;
    case 'year':
      return <YearScene frame={frame} len={len} bg={shot.bg} year={shot.year} />;
    case 'skip':
      return <Skip frame={frame} bg={shot.bg} />;
    case 'camille':
      return <Camille frame={frame} len={len} />;
    case 'recap':
      return <Recap frame={frame} clock={clock} />;
    case 'game':
      return <Game frame={frame} clock={clock} />;
    case 'closing': {
      // m2 (slowed) pulls back through the hall to the end, its speed fitted to the slot
      const rate = Math.max(0.5, Math.min(1.15, CLOSE_FRAMES / Math.max(1, len)));
      return (
        <AbsoluteFill style={{background: BG}}>
          <OffthreadVideo src={museClip('muse-m2-slow')} muted playbackRate={rate}
            style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}} />
        </AbsoluteFill>
      );
    }
  }
};

const EndCard: FC = () => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 24], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: BG, alignItems: 'center', justifyContent: 'center', opacity: o, color: INK}}>
      <div style={{fontFamily: SERIF, fontSize: 66, fontStyle: 'italic'}}>Do You Know the <span style={{color: GOLD}}>Secret</span> of Impressionism?</div>
      <div style={{fontFamily: ZH_FONT, fontSize: 40, fontWeight: 700, marginTop: 14}}>你知道印象派的<span style={{color: GOLD}}>秘密</span>吗？</div>
      <div style={{width: 140, height: 3, background: GOLD, margin: '40px 0'}} />
      <div style={{fontFamily: EN_FONT, fontSize: 36}}>Eunice Yue, Yancy Qin</div>
      <div style={{fontFamily: EN_FONT, fontSize: 30, marginTop: 50, letterSpacing: 6}}>LUCAS ACADEMY</div>
    </AbsoluteFill>
  );
};

const FadeIn: FC<{frames: number; children: ReactNode}> = ({frames, children}) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{opacity: interpolate(frame, [0, frames], [0, 1], {extrapolateRight: 'clamp'})}}>{children}</AbsoluteFill>;
};

/**
 * Chapter names on the progress bar (owner, 2026-11-01: the news series' bar, simple
 * labels, Chinese with a short English name under it). Same names and starts as the
 * YouTube chapters (scripts/impressionism-secret/youtube.py CHAPTERS); the one-line
 * review (im01) belongs to the opening.
 */
const CHAPTER_NAMES: [string, string, string][] = [
  ['im00', '开场', 'Opening'], ['im02', '沙龙', 'Salon'], ['im03', '马奈', 'Manet'], ['im04', '奥林匹亚', 'Olympia'],
  ['im05', '马奈莫奈', 'Manet & Monet'], ['im06', '1874', '1874'], ['im07', '莫奈', 'Monet'], ['im08', '德加', 'Degas'],
  ['im09', '莫里索', 'Morisot'], ['im10', '雷诺阿', 'Renoir'], ['im11', '塞尚', 'Cézanne'],
  ['im13', '秘密', 'Secret'], ['im14', '结尾', 'End'],
];
const CHAPTERS: Chapter[] = CHAPTER_NAMES.map(([id, name, enShort], i) => {
  const at = (k: string) => (k === 'im00' ? 0 : (timeline.chapters as Record<string, number>)[k]);
  const next = CHAPTER_NAMES[i + 1];
  return {id, name, enShort, start: at(id), end: next ? at(next[0]) : timeline.durationSeconds};
});

/** The progress bar over everything; its hint ("use the bar to jump") rides the line that lists what's coming. */
const Progress: FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const c = cueById.get('im00-09')!;
  const hint = interpolate(t, [c.start, c.start + 0.5, c.end + 1.5, c.end + 2], [0, 1, 1, 0], clamp);
  const o = interpolate(t, [timeline.endCardStart - 1, timeline.endCardStart], [1, 0], clamp);
  return (
    <AbsoluteFill style={{opacity: o}}>
      <ChapterBar chapters={CHAPTERS} duration={timeline.durationSeconds} t={t} hint={hint} enFirst />
    </AbsoluteFill>
  );
};

export const ImpressionismVideo: FC<ImpressionismProps> = ({audio}) => {
  const {fps} = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);
  const shots = SHOTS.map((shot, i) => ({
    shot,
    start: i === 0 ? 0 : f(cueById.get(shot.from)!.start),
    end: f(cueById.get(shot.to)!.end),
  }));
  const endStart = f(timeline.endCardStart);
  return (
    <AbsoluteFill style={{background: BG}}>
      {shots.map(({shot, start, end}, i) => {
        const len = end - start + FADE; // the last shot stays under the end card until the card is fully in
        return (
          <Sequence key={shot.from} from={start} durationInFrames={len}>
            <FadeIn frames={i === 0 ? 1 : FADE}>
              <ShotView shot={shot} len={len} start={start} />
            </FadeIn>
          </Sequence>
        );
      })}
      <Sequence from={endStart - FADE}>
        <EndCard />
      </Sequence>
      <Progress />
      {audio !== 'none' && <Audio src={staticFile(`impressionism-secret/audio/${audio}.wav`)} />}
    </AbsoluteFill>
  );
};

/**
 * YouTube cover (owner 2026-11-01, design B2 of five Codex designs): Berthe Morisot,
 * finger to her lips, while the painter in the top hat whispers in her ear — an edit of
 * the film's AI Salon portrait (codex/cover-morisot-secret.png). Title only:
 * set in the dark left 40%. v6 (owner 2026-11-02, when the English video became the
 * upload): "This painter cut off the dancers' heads." with "cut off" and "heads" in gold, and
 * the same in Chinese, 这位画家 / 切掉了 / 舞者的 / 头, with 切掉 and 头 in gold (before v6:
 * 印象派的秘密 / The Secret of Impressionism). v10 (owner 2026-11-04: "封面标题还是换为 印象派的秘密吧"): back to
 * 印象派的 / 秘密 (秘密 gold) and The / Secret (gold) / of Impressionism. The film's title card and YouTube title stay
 * as they are. Later the same day ("封面背景用虚化的沙龙背景（可以codex重新制作）标题和主体两个人物没问题", then, on a
 * pasted-in pair, "人物有点不自然 让codex 用参考图重新生成吧 … 主要是左边肩膀被切掉了"): Codex repainted the pair inside the
 * Salon hall, his left shoulder whole: 'salon' pulled back to the waist, 'salon-close' the B2 framing (prep_assets.py cover
 * blurs the hall behind them a little more; 'salon' is enlarged from the top left so his coat clears the title). 'b2' is the
 * red-wall original.
 */
const COVER_PIC = {salon: ['img/cover-salon-b.jpg', 1.07], 'salon-close': ['img/cover-salon-a.jpg', 1], b2: ['codex/cover-morisot-secret.png', 1]} as const;

export const ImpressionismCover: FC<{lang?: 'zh' | 'en'; bg?: keyof typeof COVER_PIC | 'degas'}> = ({lang = 'zh', bg = 'salon'}) => {
  const ink = '#FFF1D2';
  const lift = '0 6px 22px rgba(8,5,3,0.85), 0 0 3px rgba(8,5,3,0.9)';
  const stroke = {WebkitTextStroke: '4px rgba(20,12,6,0.9)', paintOrder: 'stroke fill'} as CSSProperties;
  return (
    <AbsoluteFill style={{background: BG}}>
      {bg !== 'degas' ? (
        <>
          <Img src={staticFile(`impressionism-secret/${COVER_PIC[bg][0]}`)}
            style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover',
              transform: `scale(${COVER_PIC[bg][1]})`, transformOrigin: 'left top'}} />
          {bg !== 'b2' && <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(16,9,6,0.55) 0%, rgba(16,9,6,0.35) 34%, rgba(16,9,6,0) 52%)'}} />}
        </>
      ) : (
        // v10 alternative: the painting itself, its top edge cutting the dancers off at the frame's top (B2 stays the default:
        // owner 2026-11-04, Codex pictures that no Muse clip repeats can stay)
        <>
          <Pic id="degas-orchestra-opera" at={{left: 700, top: -40, w: 1220, h: (1220 * IMG['degas-orchestra-opera'].h) / IMG['degas-orchestra-opera'].w}} />
          <AbsoluteFill style={{background: 'linear-gradient(90deg, #140f0c 0%, #140f0c 36%, rgba(20,15,12,0.75) 44%, rgba(20,15,12,0) 58%)'}} />
        </>
      )}
      {lang === 'zh' ? (
        <div style={{position: 'absolute', left: 78, top: 250, fontFamily: '"Songti SC", "STSong", serif', fontWeight: 900,
          lineHeight: 1.12, letterSpacing: 8, color: ink, textShadow: lift, ...stroke}}>
          <div style={{fontSize: 150}}>印象派的</div>
          <div style={{fontSize: 300, color: GOLD}}>秘密</div>
        </div>
      ) : (
        <div style={{position: 'absolute', left: 72, top: 230, fontFamily: 'Baskerville, "Baskerville Old Face", Georgia, serif',
          fontWeight: 700, color: ink, textShadow: lift, lineHeight: 1.0, ...stroke}}>
          <div style={{fontSize: 120}}>The</div>
          <div style={{fontSize: 250, color: GOLD, margin: '-6px 0 10px -6px'}}>Secret</div>
          <div style={{fontSize: 92}}>of Impressionism</div>
        </div>
      )}
    </AbsoluteFill>
  );
};
