import type {FC, ReactNode} from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import timeline from '../../data/vg-why-paint-them.json';
import {ART, LESSONS, SHOTS, type ArtId, type Cam, type Label, type Shot, type Tile} from './shots';

/**
 * "Why Did Van Gogh Paint Them?" — lucas-academy-media#3.
 *
 * One picture edit; `audio` picks the narration track. Captions are not burned
 * in: YouTube carries zh-Hans.srt and en.srt, and a second audio track, so the
 * delivered picture is rendered once without audio ('none') and muxed.
 * Every picture is a real work (see shots.ts); nothing is generated.
 */

export type VgWhyProps = {audio: 'zh' | 'en' | 'none'};

export const VG_WHY_FPS = timeline.fps;
export const VG_WHY_DURATION = Math.ceil(timeline.durationSeconds * timeline.fps);

const FADE = 18; // frames of cross-dissolve between shots
const PIC = {top: 40, bottom: 1040, width: 1840}; // the player draws captions over the picture
const PIC_H = PIC.bottom - PIC.top;
const PIC_CY = (PIC.top + PIC.bottom) / 2;

const ZH_FONT = '"PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif';
const EN_FONT = '"Avenir Next", "Helvetica Neue", Arial, sans-serif';
const SERIF = 'Georgia, "Songti SC", serif';
const INK = '#f6efe0';
const GOLD = '#e9b93a';
const BG = '#14110d';

const cueById = new Map(timeline.cues.map((c) => [c.id, c]));
const ease = Easing.bezier(0.42, 0, 0.58, 1);
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const artSrc = (id: ArtId) => staticFile(`vg-why-paint-them/art/${id}.jpg`);
/** ≤800 px copies for rows and walls, so a frame never decodes a dozen full-size scans. */
const tileSrc = (id: ArtId) => staticFile(`vg-why-paint-them/art/tiles/${id}.jpg`);
const aspect = (id: ArtId) => ART[id].w / ART[id].h;

function camAt(keys: Cam[], p: number): Cam {
  if (keys.length === 1 || p <= keys[0].t) return keys[0];
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1];
    const b = keys[i];
    if (p <= b.t) {
      const k = ease((p - a.t) / Math.max(1e-6, b.t - a.t));
      return {t: p, x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, z: a.z + (b.z - a.z) * k};
    }
  }
  return keys[keys.length - 1];
}

/** A painting, never cropped at z = 1, never stretched, with a camera on it. */
const Painting: FC<{art: ArtId; cam: Cam; dim?: number}> = ({art, cam, dim = 0}) => {
  const {w, h} = ART[art];
  const fit = Math.min(PIC.width / w, PIC_H / h);
  const s = fit * cam.z;
  const left = 960 - cam.x * w * s;
  const top = PIC_CY - cam.y * h * s;
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Img
        src={tileSrc(art)}
        style={{
          position: 'absolute', inset: -80, width: 2080, height: 1240, objectFit: 'cover',
          filter: 'blur(48px) brightness(0.32) saturate(0.8)',
        }}
      />
      <Img
        src={artSrc(art)}
        style={{
          position: 'absolute', left, top, width: w * s, height: h * s,
          boxShadow: cam.z <= 1.05 ? '0 18px 60px rgba(0,0,0,0.55)' : undefined,
        }}
      />
      {dim > 0 && <AbsoluteFill style={{background: `rgba(10,8,6,${dim})`}} />}
    </AbsoluteFill>
  );
};

const Chip: FC<{label: Label; meta?: string; opacity: number; right?: boolean}> = ({label, meta, opacity, right}) => (
  <div
    style={{
      position: 'absolute', top: 48, ...(right ? {right: 56} : {left: 56}), opacity, padding: '14px 22px', borderRadius: 10,
      background: 'rgba(12,10,8,0.62)', color: INK, borderLeft: `4px solid ${GOLD}`, maxWidth: 820,
    }}
  >
    <div style={{fontFamily: ZH_FONT, fontSize: 30, fontWeight: 600}}>{label.zh}</div>
    <div style={{fontFamily: EN_FONT, fontSize: 24, marginTop: 2, fontStyle: 'italic'}}>{label.en}</div>
    {meta && <div style={{fontFamily: EN_FONT, fontSize: 18, marginTop: 6, opacity: 0.75}}>{meta}</div>}
  </div>
);

const Tag: FC<{label: Label; opacity: number}> = ({label, opacity}) => (
  <div
    style={{
      position: 'absolute', right: 56, top: 48, opacity, padding: '8px 16px', borderRadius: 999,
      background: 'rgba(20,17,13,0.72)', color: INK, fontFamily: EN_FONT, fontSize: 22,
      border: '1px solid rgba(246,239,224,0.35)',
    }}
  >
    <span style={{fontFamily: ZH_FONT}}>{label.zh}</span> · {label.en}
  </div>
);

/** A shot's title chip: the work's own title and collection, or a custom label. */
const ArtChip: FC<{art: ArtId; chip?: boolean | Label; opacity: number}> = ({art, chip, opacity}) =>
  chip === true ? <Chip label={ART[art].title} meta={ART[art].meta} opacity={opacity} />
    : chip ? <Chip label={chip} opacity={opacity} /> : null;

const TileLabel: FC<{label: Label; size?: number}> = ({label, size = 1}) => (
  <div style={{color: INK, textAlign: 'center', lineHeight: 1.25}}>
    <div style={{fontFamily: ZH_FONT, fontSize: 28 * size, fontWeight: 600}}>{label.zh}</div>
    <div style={{fontFamily: EN_FONT, fontSize: 21 * size, fontStyle: 'italic', opacity: 0.85}}>{label.en}</div>
  </div>
);

/**
 * Justified rows: tiles keep their proportions and order, each row spans the
 * width, and the row count is the one that shows the paintings largest once
 * the whole layout is scaled to fit the box.
 */
function justify(tiles: Tile[], width: number, height: number, gap: number, labelH: number) {
  let best: {rows: Tile[][]; heights: number[]; total: number; area: number} | null = null;
  for (let r = 1; r <= tiles.length; r++) {
    const target = tiles.reduce((a, tl) => a + aspect(tl.art), 0) / r;
    const rows: Tile[][] = [[]];
    let acc = 0;
    for (const tl of tiles) {
      if (acc >= target * 0.999 && rows.length < r) {
        rows.push([]);
        acc = 0;
      }
      rows[rows.length - 1].push(tl);
      acc += aspect(tl.art);
    }
    const heights = rows.map((row) => (width - gap * (row.length - 1)) / row.reduce((a, tl) => a + aspect(tl.art), 0));
    const total = heights.reduce((a, h) => a + h + labelH, 0) + gap * (rows.length - 1);
    const k = Math.min(1, height / total);
    const area = rows.reduce((a, row, ri) => a + (heights[ri] * k) ** 2 * row.reduce((b, tl) => b + aspect(tl.art), 0), 0);
    if (!best || area > best.area) {
      best = {rows, heights, total, area};
    }
  }
  const b = best!;
  const scale = Math.min(1, height / b.total);
  const placed: {tile: Tile; x: number; y: number; w: number; h: number; i: number}[] = [];
  let y = (height - b.total * scale) / 2;
  let i = 0;
  b.rows.forEach((row, ri) => {
    const h = b.heights[ri] * scale;
    const rowW = row.reduce((a, tl) => a + aspect(tl.art) * h, 0) + gap * scale * (row.length - 1);
    let x = (width - rowW) / 2;
    for (const tl of row) {
      placed.push({tile: tl, x, y, w: aspect(tl.art) * h, h, i: i++});
      x += aspect(tl.art) * h + gap * scale;
    }
    y += h + labelH * scale + gap * scale;
  });
  return placed;
}

/** Works appearing one after another: a few large (row) or many small (wall). */
const Gallery: FC<{
  tiles: Tile[]; frame: number; len: number; box: {x: number; y: number; w: number; h: number};
  gap: number; spread: number; labelSize?: number;
}> = ({tiles, frame, len, box, gap, spread, labelSize = 1}) => {
  const labelH = tiles.some((tl) => tl.label) ? 100 * labelSize : 0;
  const placed = justify(tiles, box.w, box.h, gap, labelH);
  const step = Math.min(24, (len * spread) / tiles.length);
  const z = 1 + 0.025 * Math.min(1, frame / Math.max(1, len));
  return (
    <AbsoluteFill style={{background: BG}}>
      <AbsoluteFill style={{transform: `scale(${z})`}}>
        {placed.map(({tile, x, y, w, h, i}) => {
          const k = interpolate(frame, [8 + i * step, 8 + i * step + 14], [0, 1], clamp);
          return (
            <div key={`${tile.art}-${i}`} style={{position: 'absolute', left: box.x + x, top: box.y + y, width: w, opacity: k, transform: `translateY(${(1 - k) * 18}px)`}}>
              <Img src={tileSrc(tile.art)} style={{width: w, height: h, display: 'block', boxShadow: '0 10px 30px rgba(0,0,0,0.5)'}} />
              {tile.label && <div style={{marginTop: 10}}><TileLabel label={tile.label} size={labelSize} /></div>}
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Two works side by side, each whole, at a common height. */
const Pair: FC<{left: Tile; right: Tile; p: number; frame: number}> = ({left, right, p, frame}) => {
  const z = 1 + 0.03 * p;
  const capOpacity = interpolate(frame, [20, 40], [0, 1], clamp);
  const labelled = !!(left.label || right.label);
  const height = Math.min(labelled ? 820 : 900, 1700 / (aspect(left.art) + aspect(right.art))) * z;
  const one = (tile: Tile) => (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16}}>
      <Img src={artSrc(tile.art)} style={{height, width: aspect(tile.art) * height, boxShadow: '0 18px 60px rgba(0,0,0,0.55)'}} />
      {tile.label && <div style={{opacity: capOpacity}}><TileLabel label={tile.label} size={0.9} /></div>}
    </div>
  );
  return (
    <AbsoluteFill style={{background: BG, flexDirection: 'row', gap: 72, alignItems: 'center', justifyContent: 'center'}}>
      {one(left)}
      {one(right)}
    </AbsoluteFill>
  );
};

const QuoteCard: FC<{quote: Label; source: string; opacity: number}> = ({quote, source, opacity}) => (
  <AbsoluteFill style={{alignItems: 'center', justifyContent: 'flex-end', paddingBottom: 170, opacity}}>
    <div
      style={{
        maxWidth: 1400, padding: '56px 80px', borderRadius: 18, background: 'rgba(244,236,216,0.94)',
        color: '#2a2217', textAlign: 'center', boxShadow: '0 20px 70px rgba(0,0,0,0.5)',
      }}
    >
      <div style={{fontFamily: ZH_FONT, fontSize: 60, fontWeight: 600, lineHeight: 1.35}}>{quote.zh}</div>
      <div style={{fontFamily: SERIF, fontSize: 44, fontStyle: 'italic', marginTop: 18}}>{quote.en}</div>
      <div style={{fontFamily: EN_FONT, fontSize: 24, marginTop: 28, color: '#7a6644', letterSpacing: 1}}>
        Vincent van Gogh · {source}
      </div>
    </div>
  </AbsoluteFill>
);

const LetterCard: FC<{source: Label; opacity: number}> = ({source, opacity}) => (
  <AbsoluteFill style={{alignItems: 'center', justifyContent: 'flex-end', paddingBottom: 170, opacity}}>
    <div
      style={{
        display: 'flex', alignItems: 'center', gap: 36, padding: '36px 56px', borderRadius: 16,
        background: 'rgba(244,236,216,0.94)', color: '#2a2217', boxShadow: '0 20px 70px rgba(0,0,0,0.5)',
      }}
    >
      <svg width="120" height="88" viewBox="0 0 120 88">
        <rect x="4" y="4" width="112" height="80" rx="6" fill="#fffaf0" stroke="#2a2217" strokeWidth="4" />
        <path d="M6 8 L60 50 L114 8" fill="none" stroke="#2a2217" strokeWidth="4" />
      </svg>
      <div>
        <div style={{fontFamily: ZH_FONT, fontSize: 40, fontWeight: 600}}>{source.zh}</div>
        <div style={{fontFamily: EN_FONT, fontSize: 28, marginTop: 8}}>{source.en}</div>
      </div>
    </div>
  </AbsoluteFill>
);

/** Thin marks over The Starry Night: the turning sky and the quiet village. */
const StarryLines: FC<{art: ArtId; frame: number; len: number}> = ({art, frame, len}) => {
  const {w, h} = ART[art];
  const s = Math.min(PIC.width / w, PIC_H / h);
  const W = w * s;
  const H = h * s;
  const draw = interpolate(frame, [15, 75], [1, 0], clamp);
  const fade = interpolate(frame, [len - 40, len - 10], [1, 0], clamp);
  const village = interpolate(frame, [70, 100], [0, 1], clamp);
  const line = {
    fill: 'none', stroke: '#fff7d6', strokeWidth: 3.5, strokeLinecap: 'round' as const,
    vectorEffect: 'non-scaling-stroke' as const, pathLength: 1, strokeDasharray: 1, strokeDashoffset: draw,
  };
  // Painting coordinates (0–1 each way); the SVG is stretched onto the picture.
  return (
    <svg
      width={W} height={H} viewBox="0 0 1 1" preserveAspectRatio="none"
      style={{position: 'absolute', left: 960 - W / 2, top: PIC_CY - H / 2, opacity: fade * 0.8}}
    >
      <path {...line} d="M0.03 0.46 C0.16 0.30 0.32 0.22 0.44 0.30 C0.54 0.37 0.62 0.34 0.61 0.26 C0.60 0.18 0.48 0.18 0.47 0.27 C0.46 0.35 0.55 0.42 0.62 0.38" />
      <path {...line} d="M0.34 0.56 C0.46 0.60 0.60 0.60 0.68 0.52 C0.74 0.46 0.73 0.38 0.67 0.40 C0.62 0.42 0.63 0.50 0.70 0.50 C0.80 0.50 0.90 0.42 0.99 0.38" />
      <ellipse
        cx={0.6} cy={0.82} rx={0.21} ry={0.1} fill="none" stroke="#fff7d6" strokeWidth={4}
        vectorEffect="non-scaling-stroke" strokeDasharray="14 10" opacity={village}
      />
    </svg>
  );
};

const LessonTitle: FC<{frame: number}> = ({frame}) => {
  const o = interpolate(frame, [0, 24], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: '#f4ecd8', alignItems: 'center', justifyContent: 'center'}}>
      <div style={{textAlign: 'center', color: '#1f2f6b', opacity: o}}>
        <div style={{fontFamily: EN_FONT, fontSize: 28, letterSpacing: 6, color: '#8a7650'}}>LUCAS ACADEMY · 美术课 · ART LESSONS</div>
        <div style={{fontFamily: ZH_FONT, fontSize: 110, fontWeight: 700, marginTop: 24}}>爱是永恒</div>
        <div style={{fontFamily: SERIF, fontSize: 62, fontStyle: 'italic', marginTop: 8}}>Love Is What Lasts</div>
        <div style={{width: 120, height: 4, background: GOLD, margin: '44px auto 0'}} />
      </div>
      <div style={{position: 'absolute', right: 56, top: 48, fontFamily: EN_FONT, fontSize: 20, color: '#8a7650'}}>
        <span style={{fontFamily: ZH_FONT}}>课程：Lucas Academy 的理解</span> · Our lesson reading
      </div>
    </AbsoluteFill>
  );
};

/** One lesson, shown with one of his works (the work, not a lesson product). */
const LessonCard: FC<{n: number; p: number; frame: number}> = ({n, p, frame}) => {
  const {art, title, more} = LESSONS[n];
  const o = interpolate(frame, [10, 30], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <Painting art={art} cam={{t: 0, x: 0.5, y: 0.5, z: 1 + 0.05 * p}} />
      <div
        style={{
          position: 'absolute', left: 56, top: 48, opacity: o, padding: '14px 24px', borderRadius: 12,
          background: 'rgba(31,47,107,0.92)', color: INK, display: 'flex', alignItems: 'center', gap: 20,
        }}
      >
        <div style={{fontFamily: EN_FONT, fontSize: 44, fontWeight: 700, color: GOLD}}>{more ? '+' : n + 1}</div>
        <div>
          <div style={{fontFamily: ZH_FONT, fontSize: 34, fontWeight: 600}}>{title.zh}</div>
          <div style={{fontFamily: EN_FONT, fontSize: 24}}>{title.en}</div>
        </div>
      </div>
      <div
        style={{
          position: 'absolute', right: 56, top: 48, opacity: o * 0.9, color: INK, textAlign: 'right', fontFamily: EN_FONT,
          fontSize: 18, padding: '8px 14px', borderRadius: 8, background: 'rgba(12,10,8,0.55)',
        }}
      >
        <div style={{fontFamily: ZH_FONT, fontSize: 22}}>{ART[art].title.zh}</div>
        <div style={{fontStyle: 'italic'}}>{ART[art].title.en} · {ART[art].meta.split(' · ')[0]}</div>
      </div>
    </AbsoluteFill>
  );
};

const NameCard: FC<{p: number; frame: number}> = ({p, frame}) => {
  const o = interpolate(frame, [14, 34], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <Painting art="selfportrait" cam={{t: 0, x: 0.38, y: 0.5, z: 1 + 0.04 * p}} />
      <div style={{position: 'absolute', left: 96, top: 330, opacity: o, color: INK}}>
        <div style={{fontFamily: SERIF, fontSize: 64}}>Vincent van Gogh</div>
        <div style={{fontFamily: ZH_FONT, fontSize: 52, marginTop: 8}}>文森特·梵高</div>
        <div style={{width: 120, height: 4, background: GOLD, margin: '22px 0'}} />
        <div style={{fontFamily: EN_FONT, fontSize: 40, letterSpacing: 2}}>1853–1890</div>
      </div>
    </AbsoluteFill>
  );
};

const ShotView: FC<{shot: Shot; len: number}> = ({shot, len}) => {
  const frame = useCurrentFrame();
  const p = Math.min(1, frame / Math.max(1, len));
  const inOut = interpolate(frame, [12, 32, len - 20, len], [0, 1, 1, 0], clamp);
  switch (shot.kind) {
    case 'art':
      return (
        <AbsoluteFill>
          <Painting art={shot.art} cam={camAt(shot.cam, p)} />
          {shot.overlay === 'starry-lines' && <StarryLines art={shot.art} frame={frame} len={len} />}
          <ArtChip art={shot.art} chip={shot.chip} opacity={inOut} />
        </AbsoluteFill>
      );
    case 'pair':
      return <Pair left={shot.left} right={shot.right} p={p} frame={frame} />;
    case 'namecard':
      return <NameCard p={p} frame={frame} />;
    case 'quote':
      return (
        <AbsoluteFill>
          <Painting art={shot.art} cam={shot.cam} dim={0.45} />
          <QuoteCard quote={shot.quote} source={shot.source} opacity={inOut} />
        </AbsoluteFill>
      );
    case 'letter':
      return (
        <AbsoluteFill>
          <Painting art={shot.art} cam={shot.cam} dim={0.4} />
          <LetterCard source={shot.source} opacity={inOut} />
        </AbsoluteFill>
      );
    case 'row':
      return <Gallery tiles={shot.tiles} frame={frame} len={len} box={{x: 60, y: 60, w: 1800, h: 960}} gap={40} spread={0.6} labelSize={1.1} />;
    case 'wall':
      return (
        <AbsoluteFill>
          <Gallery tiles={shot.tiles} frame={frame} len={len} box={{x: 60, y: 150, w: 1800, h: 880}} gap={18} spread={0.5} />
          {shot.caption && <Chip label={shot.caption} opacity={inOut} />}
        </AbsoluteFill>
      );
    case 'dissolve': {
      const mix = interpolate(p, [0.42, 0.58], [0, 1], clamp);
      return (
        <AbsoluteFill>
          <Painting art={shot.a} cam={camAt(shot.camA, p)} />
          <AbsoluteFill style={{opacity: ease(mix)}}>
            <Painting art={shot.b} cam={camAt(shot.camB, p)} />
          </AbsoluteFill>
          <ArtChip art={shot.a} chip opacity={inOut * (1 - mix)} />
          <ArtChip art={shot.b} chip opacity={inOut * mix} />
          {shot.tag && <Tag label={shot.tag} opacity={inOut} />}
        </AbsoluteFill>
      );
    }
    case 'lesson':
      return <LessonCard n={shot.n} p={p} frame={frame} />;
    case 'lessons-title':
      return <LessonTitle frame={frame} />;
    case 'lessons-grid':
      return (
        <Gallery
          tiles={LESSONS.map((l, i) => ({art: l.art, label: {zh: `${l.more ? '+' : i + 1} · ${l.title.zh}`, en: l.title.en}}))}
          frame={frame} len={len} box={{x: 60, y: 60, w: 1800, h: 960}} gap={40} spread={0.35} labelSize={0.95}
        />
      );
  }
};

const EndCard: FC = () => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 24], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: BG, alignItems: 'center', justifyContent: 'center', opacity: o, color: INK}}>
      <div style={{fontFamily: ZH_FONT, fontSize: 64, fontWeight: 700}}>梵高为什么画他们？</div>
      <div style={{fontFamily: SERIF, fontSize: 46, fontStyle: 'italic', marginTop: 10}}>Why Did Van Gogh Paint Them?</div>
      <div style={{width: 120, height: 4, background: GOLD, margin: '36px 0'}} />
      <div style={{fontFamily: ZH_FONT, fontSize: 32}}>课案《爱是永恒》 · Lessons: Love Is What Lasts</div>
      <div style={{fontFamily: 'Menlo, monospace', fontSize: 28, marginTop: 14, color: GOLD}}>is.lucasacademy.org/docs/van-gogh-love-lessons.html</div>
      <div style={{fontFamily: EN_FONT, fontSize: 22, marginTop: 70, opacity: 0.75, maxWidth: 1500, textAlign: 'center', lineHeight: 1.5}}>
        Paintings, drawings and letter sketches by Vincent van Gogh; Giotto's Lamentation, Scrovegni Chapel. Public-domain photographs via
        Wikimedia Commons — collections are named on screen and in the description. Letters: vangoghletters.org (Van Gogh Museum / Huygens ING).
        <br />
        <span style={{fontFamily: ZH_FONT}}>课程联系与信仰理解为 Lucas Academy 的解释</span> · Lesson links and faith reading are Lucas Academy's own.
      </div>
      <div style={{fontFamily: EN_FONT, fontSize: 30, marginTop: 48, letterSpacing: 6}}>LUCAS ACADEMY</div>
    </AbsoluteFill>
  );
};

export const VgWhyVideo: FC<VgWhyProps> = ({audio}) => {
  const {fps} = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);
  const shots: {shot: Shot; start: number; end: number}[] = SHOTS.map((shot, i) => ({
    shot,
    start: i === 0 ? 0 : f(cueById.get(shot.from)!.start),
    end: f(cueById.get(shot.to)!.end),
  }));
  const endStart = f(timeline.endCardStart);
  return (
    <AbsoluteFill style={{background: BG}}>
      {shots.map(({shot, start, end}, i) => {
        const len = end - start + (i + 1 < shots.length ? FADE : 0);
        return (
          <Sequence key={shot.from} from={start} durationInFrames={len}>
            <FadeIn frames={i === 0 ? 1 : FADE}>
              <ShotView shot={shot} len={len} />
            </FadeIn>
          </Sequence>
        );
      })}
      <Sequence from={endStart - FADE}>
        <EndCard />
      </Sequence>
      {audio !== 'none' && <Audio src={staticFile(`vg-why-paint-them/audio/${audio}.wav`)} />}
    </AbsoluteFill>
  );
};

const FadeIn: FC<{frames: number; children: ReactNode}> = ({frames, children}) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{opacity: interpolate(frame, [0, frames], [0, 1], {extrapolateRight: 'clamp'})}}>{children}</AbsoluteFill>;
};
