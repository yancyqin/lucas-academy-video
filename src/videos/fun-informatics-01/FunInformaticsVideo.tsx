import {rampAt} from '../../lib/timeRamps';
import type {CSSProperties, FC, ReactNode} from 'react';
import {
  type CalculateMetadataFunction,
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
} from 'remotion';
import {ADDER, ADDER_ROWS, CARDS, FRACTAL_PIXEL, INTRO, RULER, RULER_MILLIONS_EN, VISUALS, type Card, type Label, type RampKey, type Span, type Visual} from './shots';

/**
 * 「计算机怎么算 1+1=？ / How Does a Computer Add 1 + 1=?」 — 趣味信息学1, filmed in the Pixel Science
 * Room of Inception Space. Two films, one per language (Louise in both), each paced by its own
 * narration; nothing is burned in, captions ship as SRT. FUN-INFORMATICS-01.md is the plan.
 */

export type Lang = 'zh' | 'en';

type Cue = {id: string; section: string; zh: string; en: string; start: number; end: number; speech: {start: number; end: number}};

/** Written by scripts/fun-informatics-01/build_timeline.py into public/fun-informatics-01/ — generated, never committed. */
export type Timeline = {
  fps: number;
  leadIn: number;
  lang: Lang;
  title: Label;
  footage: string[];
  images: string[];
  footageSeconds: Record<string, number>;
  durationSeconds: number;
  endCardStart: number;
  cues: Cue[];
};

export type FunInformaticsProps = {lang: Lang; tl?: Timeline | null};

export const FI_FPS = 30;
const DIR = 'fun-informatics-01';

export const calculateFunInformaticsMetadata: CalculateMetadataFunction<FunInformaticsProps> = async ({props, abortSignal}) => {
  const file = `${DIR}/timeline.${props.lang}.json`;
  const response = await fetch(staticFile(file), {signal: abortSignal});
  if (!response.ok) throw new Error(`${file} is missing — run npm run fi01:timeline first`);
  const tl = (await response.json()) as Timeline;
  return {durationInFrames: Math.ceil(tl.durationSeconds * tl.fps), fps: tl.fps, props: {...props, tl}};
};

const FADE = 18; // frames of cross-dissolve
const SAFE_BOTTOM = 150; // keep cards clear of where YouTube draws captions
const ZH_FONT = '"PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif';
const EN_FONT = '"Avenir Next", "Helvetica Neue", Arial, sans-serif';
const MONO = '"SF Mono", Menlo, monospace';
const WHITE = '#f4f8ff';
const SOFT = 'rgba(230,240,255,0.78)';
const CYAN = '#7fe3ff';
const MINT = '#a7f59b';
const GOLD = '#ffd27a';
const BG = '#070b14';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const glass = (extra: CSSProperties = {}): CSSProperties => ({
  background: 'linear-gradient(135deg, rgba(20,34,58,0.62), rgba(10,18,34,0.48))',
  backdropFilter: 'blur(16px) saturate(140%)',
  WebkitBackdropFilter: 'blur(16px) saturate(140%)',
  border: '1px solid rgba(127,227,255,0.38)',
  boxShadow: '0 0 0 1px rgba(255,255,255,0.05) inset, 0 0 26px rgba(127,227,255,0.16), 0 18px 50px rgba(0,0,0,0.35)',
  borderRadius: 18,
  color: WHITE,
  ...extra,
});
const glow = '0 0 18px rgba(127,227,255,0.35), 0 2px 12px rgba(0,0,0,0.6)';

type Ctx = {tl: Timeline; lang: Lang; cue: (id: string) => Cue};
const pick = (ctx: Ctx, l: Label) => (ctx.lang === 'zh' ? l.zh : l.en);
const other = (ctx: Ctx, l: Label) => (ctx.lang === 'zh' ? l.en : l.zh);
const font = (ctx: Ctx) => (ctx.lang === 'zh' ? ZH_FONT : EN_FONT);

const Missing: FC<{name: string}> = ({name}) => (
  <AbsoluteFill style={{background: '#101828', alignItems: 'center', justifyContent: 'center'}}>
    <div style={{border: '2px dashed #4b6385', borderRadius: 16, padding: '24px 40px', color: '#9fb3d1', fontFamily: MONO, fontSize: 26}}>{name}</div>
  </AbsoluteFill>
);

const Tag: FC<{children: ReactNode; style?: CSSProperties}> = ({children, style}) => (
  <div style={glass({padding: '10px 22px', borderRadius: 999, fontFamily: EN_FONT, fontSize: 26, ...style})}>{children}</div>
);

const Kicker: FC<{children: ReactNode}> = ({children}) => (
  <div style={{fontFamily: MONO, fontSize: 22, letterSpacing: 4, color: CYAN, textShadow: glow, marginBottom: 14}}>{children}</div>
);

/** Primary language large, the other smaller beneath it. */
const Pair: FC<{ctx: Ctx; text: Label; size: number; color?: string}> = ({ctx, text, size, color}) => (
  <>
    <div style={{fontFamily: font(ctx), fontSize: size, fontWeight: 700, lineHeight: 1.35, textShadow: glow, color}}>{pick(ctx, text)}</div>
    <div style={{fontFamily: ctx.lang === 'zh' ? EN_FONT : ZH_FONT, fontSize: Math.round(size * 0.55), color: SOFT, marginTop: 10, lineHeight: 1.4}}>
      {other(ctx, text)}
    </div>
  </>
);

const FadeIn: FC<{frames: number; children: ReactNode}> = ({frames, children}) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{opacity: interpolate(frame, [0, Math.max(1, frames)], [0, 1], {extrapolateRight: 'clamp'})}}>{children}</AbsoluteFill>;
};

// ---------------------------------------------------------------- visuals

const zoomText = (z: number) => {
  if (z < 10) return `×${z.toFixed(1)}`;
  if (z < 1e6) return `×${Math.round(z).toLocaleString('en-US')}`;
  const e = Math.floor(Math.log10(z));
  const sup = String(e).split('').map((d) => '⁰¹²³⁴⁵⁶⁷⁸⁹'[Number(d)]).join('');
  return `×${(z / 10 ** e).toFixed(1)} × 10${sup}`;
};

/**
 * A recording from second `a`, played so that it reaches `b` when the visual's main length ends
 * (`a == b` freezes). Past the end of the file it holds the last good frame instead of failing.
 */
const ClipSpan: FC<{ctx: Ctx; file: string; span: Span; main: number; len: number; dim?: number; push?: number; boost?: number; overlay?: 'fractal' | 'overdrive'}> = ({
  ctx, file, span, main, len, dim = 0, push = 0, boost = 1, overlay,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (!ctx.tl.footage.includes(file)) return <Missing name={`footage/${file}`} />;
  const src = staticFile(`${DIR}/footage/${file}`);
  const [a, b] = span;
  const rate = b > a ? Math.min(4, Math.max(0.2, (b - a) / (main / fps))) : 0;
  const style: CSSProperties = {position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover',
    transform: `scale(${1 + push * (frame / Math.max(1, len))})`, filter: boost !== 1 ? `brightness(${boost}) saturate(1.15)` : undefined};
  const trim = Math.round(a * fps);
  const end = (ctx.tl.footageSeconds[file] ?? 0) - 0.12;
  const good = rate > 0 ? Math.max(1, Math.floor(((end - a) / rate) * fps)) : 0;
  let video: ReactNode;
  if (rate === 0) {
    video = <Freeze frame={0}><OffthreadVideo src={src} trimBefore={trim} muted style={style} /></Freeze>;
  } else if (good >= len) {
    video = <OffthreadVideo src={src} trimBefore={trim} playbackRate={rate} muted style={style} />;
  } else {
    video = (
      <>
        <Sequence durationInFrames={good}><OffthreadVideo src={src} trimBefore={trim} playbackRate={rate} muted style={style} /></Sequence>
        <Sequence from={good}><Freeze frame={0}><OffthreadVideo src={src} trimBefore={Math.round(end * fps) - 1} muted style={style} /></Freeze></Sequence>
      </>
    );
  }
  const t = a + (rate * Math.min(frame, main)) / fps;
  return (
    <AbsoluteFill style={{background: BG, overflow: 'hidden'}}>
      {video}
      {dim > 0 && <AbsoluteFill style={{background: `rgba(7,11,20,${dim})`}} />}
      {overlay && (
        <div style={{position: 'absolute', left: 44, top: 40}}>
          <Tag style={{fontFamily: MONO, fontSize: 28, color: CYAN}}>
            z → z² + c <span style={{color: WHITE, marginLeft: 22}}>{zoomText((overlay === 'overdrive' ? 8 : 2) ** t)}</span>
          </Tag>
        </div>
      )}
    </AbsoluteFill>
  );
};

export {rampAt} from '../../lib/timeRamps';

/** One unbroken recording played along a speed curve: every frame is looked up on the curve, never cut. */
const RampClip: FC<{ctx: Ctx; file: string; keys: RampKey[]; dim?: number}> = ({ctx, file, keys, dim = 0}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (!ctx.tl.footage.includes(file)) return <Missing name={`footage/${file}`} />;
  const end = (ctx.tl.footageSeconds[file] ?? 0) - 0.12;
  const s = Math.min(end, rampAt(keys, frame / fps));
  return (
    <AbsoluteFill style={{background: BG, overflow: 'hidden'}}>
      <Freeze frame={0}>
        <OffthreadVideo src={staticFile(`${DIR}/footage/${file}`)} trimBefore={Math.round(s * fps)} muted
          style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}} />
      </Freeze>
      {dim > 0 && <AbsoluteFill style={{background: `rgba(7,11,20,${dim})`}} />}
    </AbsoluteFill>
  );
};

const Pip: FC<{ctx: Ctx; file: string; span: Span; main: number; len: number}> = ({ctx, file, span, main, len}) => (
  <div style={glass({position: 'absolute', right: 44, top: 40, width: 576, height: 324, padding: 8, borderRadius: 14})}>
    <div style={{position: 'relative', width: '100%', height: '100%', borderRadius: 8, overflow: 'hidden'}}>
      <ClipSpan ctx={ctx} file={file} span={span} main={main} len={len} />
    </div>
  </div>
);

const ImageView: FC<{ctx: Ctx; file: string; fit?: 'cover' | 'contain'; push?: number; dim?: number; len: number}> = ({ctx, file, fit = 'cover', push = 0, dim = 0, len}) => {
  const frame = useCurrentFrame();
  if (!ctx.tl.images.includes(file)) return <Missing name={`images/${file}`} />;
  return (
    <AbsoluteFill style={{background: BG, overflow: 'hidden', alignItems: 'center', justifyContent: 'center'}}>
      <Img src={staticFile(`${DIR}/images/${file}`)} style={{
        width: fit === 'contain' ? '86%' : '100%', height: fit === 'contain' ? '82%' : '100%', objectFit: fit,
        transform: `scale(${1 + push * (frame / Math.max(1, len))})`,
      }} />
      {dim > 0 && <AbsoluteFill style={{background: `rgba(7,11,20,${dim})`}} />}
    </AbsoluteFill>
  );
};

/** The room's own glass: the Go-board points and lines of mr-yancy-black.svg. */
const GridView: FC<{ctx: Ctx}> = ({ctx}) => {
  const frame = useCurrentFrame();
  const ok = ctx.tl.images.includes('mr-yancy-black.svg');
  return (
    <AbsoluteFill style={{background: BG}}>
      {ok && (
        <AbsoluteFill style={{
          backgroundImage: `url(${staticFile(`${DIR}/images/mr-yancy-black.svg`)})`, backgroundSize: '512px 512px',
          backgroundPosition: `${-frame * 0.15}px ${-frame * 0.08}px`, opacity: 0.95,
        }} />
      )}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(7,11,20,0) 30%, rgba(7,11,20,0.75) 100%)'}} />
    </AbsoluteFill>
  );
};

/** The transistor drawn as a switch, flipping on and off; optionally a still for the first 45%. */
const SwitchView: FC<{ctx: Ctx; first?: string; main: number; len: number}> = ({ctx, first, main, len}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const firstLen = first ? Math.round(main * 0.45) : 0;
  const on = Math.floor((frame - firstLen) / (fps * 0.7)) % 2 === 1;
  return (
    <AbsoluteFill style={{background: BG}}>
      {first && frame < firstLen + 12 && (
        <AbsoluteFill style={{opacity: interpolate(frame, [firstLen - 4, firstLen + 12], [1, 0], clamp)}}>
          <ImageView ctx={ctx} file={first} push={0.06} len={firstLen} />
        </AbsoluteFill>
      )}
      {frame >= firstLen - 4 && (
        <AbsoluteFill style={{opacity: interpolate(frame, [firstLen - 4, firstLen + 12], [0, 1], clamp)}}>
          <ImageView ctx={ctx} file={on ? 'transistor-switch-closed.png' : 'transistor-switch-open.png'} len={len} />
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

/** Zoom into a picture with its pixels drawn as squares (nearest neighbour), keeping `focus` centred. */
const PixelZoom: FC<{ctx: Ctx; file: string; focus: [number, number]; from: number; to: number; main: number; w?: number; h?: number}> = ({
  ctx, file, focus, from, to, main, w = 1920, h = 1080,
}) => {
  const frame = useCurrentFrame();
  if (!ctx.tl.images.includes(file)) return <Missing name={`images/${file}`} />;
  const p = interpolate(frame, [8, Math.max(9, main * 0.8)], [0, 1], clamp);
  const eased = p * p * (3 - 2 * p);
  const s = from * (to / from) ** eased;
  const k = w / 1920; // stills are 1920 x 1080
  return (
    <AbsoluteFill style={{background: BG, overflow: 'hidden'}}>
      <Img src={staticFile(`${DIR}/images/${file}`)} style={{
        position: 'absolute', width: 1920 * k * s, height: 1080 * k * s, maxWidth: 'none',
        left: w / 2 - focus[0] * k * s, top: h / 2 - focus[1] * k * s, imageRendering: 'pixelated',
      }} />
      {s > 2 && (
        <div style={{position: 'absolute', left: 44, top: 40}}>
          <Tag style={{fontFamily: MONO, fontSize: 28, color: CYAN}}>{`×${Math.round(s)}`}</Tag>
        </div>
      )}
    </AbsoluteFill>
  );
};

const WallView: FC<{ctx: Ctx; items: {file: string; label: Label}[]}> = ({ctx, items}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: BG, alignItems: 'center', justifyContent: 'center', paddingBottom: SAFE_BOTTOM}}>
      <div style={{display: 'flex', gap: 22}}>
        {items.map((it, i) => (
          <div key={it.file} style={{opacity: interpolate(frame, [6 + i * 10, 20 + i * 10], [0, 1], clamp), textAlign: 'center'}}>
            <div style={glass({padding: 8, borderRadius: 12})}>
              {ctx.tl.images.includes(it.file)
                ? <Img src={staticFile(`${DIR}/images/${it.file}`)} style={{width: 344, height: 260, objectFit: 'cover', borderRadius: 6, display: 'block'}} />
                : <div style={{width: 344, height: 260, position: 'relative'}}><Missing name={it.file} /></div>}
            </div>
            <div style={{fontFamily: font(ctx), fontSize: 34, fontWeight: 700, marginTop: 14, color: WHITE, textShadow: glow}}>{pick(ctx, it.label)}</div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const VisualView: FC<{ctx: Ctx; v: Visual; main: number; len: number; w?: number; h?: number}> = ({ctx, v, main, len, w, h}) => {
  switch (v.kind) {
    case 'clip':
      return (
        <AbsoluteFill>
          <ClipSpan ctx={ctx} file={v.file} span={v.span} main={main} len={len} dim={v.dim} push={v.push} boost={v.boost} overlay={v.overlay} />
          {v.pip && <Pip ctx={ctx} file={v.pip.file} span={v.pip.span} main={main} len={len} />}
        </AbsoluteFill>
      );
    case 'montage': {
      const share = Math.floor(main / v.spans.length);
      return (
        <AbsoluteFill style={{background: BG}}>
          {v.spans.map((span, i) => (
            <Sequence key={i} from={i * share} durationInFrames={i === v.spans.length - 1 ? len - i * share : share + 6}>
              <FadeIn frames={i ? 6 : 1}>
                <ClipSpan ctx={ctx} file={v.file} span={span} main={i === v.spans.length - 1 ? main - i * share : share} len={share} dim={v.dim} />
              </FadeIn>
            </Sequence>
          ))}
        </AbsoluteFill>
      );
    }
    case 'ramp':
      return <RampClip ctx={ctx} file={v.file} keys={v.keys[ctx.lang]} dim={v.dim} />;
    case 'image':
      return <ImageView ctx={ctx} file={v.file} fit={v.fit} push={v.push} dim={v.dim} len={len} />;
    case 'grid':
      return (
        <AbsoluteFill>
          <GridView ctx={ctx} />
          {v.pip && <Pip ctx={ctx} file={v.pip.file} span={v.pip.span} main={main} len={len} />}
        </AbsoluteFill>
      );
    case 'switch':
      return (
        <AbsoluteFill>
          <SwitchView ctx={ctx} first={v.first} main={main} len={len} />
          {v.pip && <Pip ctx={ctx} file={v.pip.file} span={v.pip.span} main={main} len={len} />}
        </AbsoluteFill>
      );
    case 'pixelzoom':
      return <PixelZoom ctx={ctx} file={v.file} focus={v.focus} from={v.from} to={v.to} main={main} w={w} h={h} />;
    case 'split':
      return (
        <AbsoluteFill style={{background: BG, flexDirection: 'row', gap: 36, alignItems: 'center', justifyContent: 'center', paddingBottom: 60}}>
          {[v.left, v.right].map((side, i) => (
            <div key={i} style={glass({padding: 8, borderRadius: 14})}>
              <div style={{position: 'relative', width: 880, height: 495, borderRadius: 8, overflow: 'hidden'}}>
                <VisualView ctx={ctx} v={side} main={main} len={len} w={880} h={495} />
              </div>
            </div>
          ))}
        </AbsoluteFill>
      );
    case 'wall':
      return <WallView ctx={ctx} items={v.items} />;
  }
};

// ---------------------------------------------------------------- cards

const Centre: FC<{children: ReactNode; opacity: number; y: number}> = ({children, opacity, y}) => (
  <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', paddingBottom: SAFE_BOTTOM, opacity}}>
    <div style={{transform: `translateY(${y}px)`}}>{children}</div>
  </AbsoluteFill>
);

type CardProps = {ctx: Ctx; frame: number; len: number; start: number};

/** Frame (within the card) at which a cue's speech starts. */
const at = (p: CardProps, id: string) => Math.round(p.ctx.cue(id).speech.start * p.ctx.tl.fps) - p.start;
/** The last of `ids` whose speech has started by now. */
const current = (p: CardProps, ids: string[]) => ids.filter((id) => p.frame >= at(p, id) - 3).pop() ?? ids[0];
const pop = (frame: number, a: number) => ({
  opacity: interpolate(frame, [a, a + 12], [0, 1], clamp),
  transform: `translateY(${interpolate(frame, [a, a + 12], [16, 0], clamp)}px)`,
});

const CarryCard: FC<CardProps> = (p) => {
  const {ctx, frame} = p;
  const binary = at(p, 'it03-03');
  const col = (title: Label, rows: string[], a: number, accent: string) => (
    <div style={{...pop(frame, a), ...glass({padding: '30px 54px', textAlign: 'center', minWidth: 520})}}>
      <Pair ctx={ctx} text={title} size={ctx.lang === 'zh' ? 38 : 32} />
      <div style={{marginTop: 18}}>
        {rows.map((r, i) => (
          <div key={r} style={{...pop(frame, a + 14 + i * 16), fontFamily: MONO, fontSize: 76, fontWeight: 700, lineHeight: 1.25,
            color: i === rows.length - 1 ? accent : WHITE, textShadow: glow}}>{r}</div>
        ))}
      </div>
      <div style={{...pop(frame, a + 14 + rows.length * 16), fontFamily: font(ctx), fontSize: 28, color: accent, marginTop: 8}}>
        {pick(ctx, {zh: '进位！', en: 'carry!'})}
      </div>
    </div>
  );
  return (
    <AbsoluteFill style={{flexDirection: 'row', gap: 60, alignItems: 'center', justifyContent: 'center', paddingBottom: SAFE_BOTTOM, color: WHITE}}>
      {col({zh: '我们的数：十个数字', en: 'Our numbers: ten digits'}, ['8', '9', '10'], 6, GOLD)}
      {col({zh: '计算机的数：两个数字', en: 'A computer’s numbers: two digits'}, ['0', '1', '10'], Math.max(20, binary), CYAN)}
    </AbsoluteFill>
  );
};

/** Two switches, two lamps: SUM lights when exactly one is on, CARRY when both are. The cue decides the state (shots.ts ADDER). */
const AdderCard: FC<CardProps> = (p) => {
  const {ctx, frame, len} = p;
  const {fps} = useVideoConfig();
  // Only the cues that fall inside this card: the adder appears twice (04 and 07).
  const ids = Object.keys(ADDER).filter((id) => at(p, id) > -90 && at(p, id) < len);
  const id = current(p, ids);
  const state = ADDER[id];
  if ('view' in state) return <AdderTiles {...p} view={state.view} begin={at(p, id)} />;
  const c = ctx.cue(id);
  const speech = (c.speech.end - c.speech.start) * fps;
  const [A, B] = state.then && frame >= at(p, id) + Math.round(speech * 0.55) ? state.then : [state.a, state.b];
  const sum = A !== B;
  const carry = A && B;
  const flow = Boolean(state.flow);
  const readout = Boolean(state.readout) && frame >= at(p, id) + Math.round(speech * 0.45);
  const wire = (live: boolean) => ({stroke: live ? CYAN : 'rgba(127,227,255,0.28)', strokeWidth: live ? 7 : 5, fill: 'none',
    strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, filter: live ? 'url(#glow)' : undefined,
    strokeDasharray: flow && live ? '14 18' : undefined, strokeDashoffset: flow && live ? -frame * 3 : undefined});
  const sw = (y: number, on: boolean, label: Label) => (
    <g>
      <path d={`M 40 ${y} H 150`} {...wire(on)} />
      <circle cx={150} cy={y} r={11} fill={on ? CYAN : '#24405a'} />
      <path d={on ? `M 150 ${y} L 262 ${y}` : `M 150 ${y} L 248 ${y - 62}`} stroke={on ? CYAN : '#9fb3d1'} strokeWidth={9} strokeLinecap="round" />
      <circle cx={268} cy={y} r={11} fill={on ? CYAN : '#24405a'} />
      <text x={150} y={y + 62} fill={on ? CYAN : SOFT} fontFamily={font(ctx)} fontSize={30} textAnchor="middle">
        {`${pick(ctx, label)}  ${on ? pick(ctx, {zh: '开', en: 'ON'}) : pick(ctx, {zh: '关', en: 'OFF'})}`}
      </text>
    </g>
  );
  const lamp = (y: number, lit: boolean, label: Label, color: string) => (
    <g>
      <circle cx={1210} cy={y} r={56} fill={lit ? color : '#0d1b2c'} stroke={lit ? color : '#3d5c78'} strokeWidth={4} filter={lit ? 'url(#bigglow)' : undefined} opacity={lit ? 0.95 : 1} />
      {readout && <text x={1210} y={y + 22} fill={lit ? '#0b1626' : WHITE} fontFamily={MONO} fontSize={62} fontWeight={700} textAnchor="middle">{lit ? '1' : '0'}</text>}
      <text x={1300} y={y + 12} fill={lit ? color : SOFT} fontFamily={font(ctx)} fontSize={38} fontWeight={700}>{pick(ctx, label)}</text>
    </g>
  );
  const box = (y: number, label: Label, hot: boolean) => (
    <g>
      <rect x={560} y={y - 52} width={330} height={104} rx={18} fill="rgba(20,34,58,0.85)" stroke={hot ? GOLD : 'rgba(127,227,255,0.5)'} strokeWidth={hot ? 4 : 2} />
      <text x={725} y={y + 12} fill={hot ? GOLD : WHITE} fontFamily={font(ctx)} fontSize={32} textAnchor="middle">{pick(ctx, label)}</text>
    </g>
  );
  const rows = [['0', '0', '0'], ['0', '1', '1'], ['1', '0', '1'], ['1', '1', '10']];
  const rowAt = (i: number) => Math.max(0, at(p, ADDER_ROWS[i]) + (i === 2 ? 20 : 0));
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', paddingBottom: SAFE_BOTTOM - 40, opacity: interpolate(frame, [0, 14], [0, 1], clamp)}}>
      <div style={glass({padding: '26px 40px 30px', borderRadius: 22})}>
        <svg width={1560} height={560} viewBox="0 0 1560 560">
          <defs>
            <filter id="glow"><feGaussianBlur stdDeviation="4" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
            <filter id="bigglow"><feGaussianBlur stdDeviation="14" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
          </defs>
          <path d="M 268 150 H 420 V 128 H 560" {...wire(A)} />
          <path d="M 420 150 V 392 H 560" {...wire(A)} />
          <path d="M 268 430 H 480 V 168 H 560" {...wire(B)} />
          <path d="M 480 430 V 448 H 560" {...wire(B)} />
          <path d="M 890 148 H 1154" {...wire(sum)} />
          <path d="M 890 420 H 1154" {...wire(carry)} />
          {sw(150, A, {zh: '开关 A', en: 'Switch A'})}
          {sw(430, B, {zh: '开关 B', en: 'Switch B'})}
          {box(148, {zh: '只有一个开着', en: 'exactly one on'}, state.hot === 'sum')}
          {box(420, {zh: '两个都开着', en: 'both on'}, state.hot === 'carry')}
          {lamp(148, sum, {zh: '和', en: 'SUM'}, MINT)}
          {lamp(420, carry, {zh: '进位', en: 'CARRY'}, GOLD)}
          {readout && (
            <g>
              <text x={1450} y={322} fontFamily={MONO} fontSize={120} fontWeight={800} textAnchor="middle">
                <tspan fill={GOLD}>1</tspan><tspan fill={MINT}>0</tspan>
              </text>
              <text x={1450} y={362} fill={SOFT} fontFamily={font(ctx)} fontSize={24} textAnchor="middle">{pick(ctx, {zh: '进位 · 和', en: 'CARRY · SUM'})}</text>
            </g>
          )}
        </svg>
        <div style={{display: 'flex', gap: 22, justifyContent: 'center', marginTop: 6, minHeight: 92}}>
          {rows.slice(0, state.rows).map(([a, b, r], i) => (
            <div key={i} style={{...pop(frame, rowAt(i)),
              ...glass({padding: '14px 30px', borderRadius: 14, border: i === 3 ? `2px solid ${GOLD}` : undefined}),
              fontFamily: MONO, fontSize: 44, fontWeight: 700, color: i === 3 ? GOLD : WHITE}}>
              {`${a} + ${b} = ${r}`}
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** More adders: a row of four for bigger numbers, a screen full of them, and every pixel of the fractal. */
const AdderTiles: FC<CardProps & {view: 'chain' | 'tiles' | 'pixels'; begin: number}> = (p) => {
  const {ctx, frame, view, begin} = p;
  if (view === 'chain') {
    return (
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', paddingBottom: SAFE_BOTTOM, gap: 34, color: WHITE}}>
        <div style={{display: 'flex', gap: 26, alignItems: 'center'}}>
          {[0, 1, 2, 3].map((i) => (
            <div key={i} style={{...pop(frame, begin + i * 8), display: 'flex', alignItems: 'center', gap: 26}}>
              <div style={glass({width: 250, height: 150, borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 18})}>
                <div style={{width: 34, height: 34, borderRadius: '50%', background: MINT, boxShadow: `0 0 20px ${MINT}`}} />
                <div style={{width: 34, height: 34, borderRadius: '50%', background: GOLD, boxShadow: `0 0 20px ${GOLD}`}} />
              </div>
              {i < 3 && <div style={{fontFamily: MONO, fontSize: 40, color: GOLD}}>←</div>}
            </div>
          ))}
        </div>
        <div style={{...pop(frame, begin + 30), ...glass({padding: '20px 44px', textAlign: 'center'})}}>
          <Pair ctx={ctx} text={{zh: '更大的数：多排几组开关 · 乘法：把加法做很多次', en: 'Bigger numbers: more groups of switches · multiplication: addition, many times'}} size={ctx.lang === 'zh' ? 40 : 34} />
        </div>
      </AbsoluteFill>
    );
  }
  const a = view === 'tiles' ? begin : begin - 90;
  const n = Math.round(interpolate(frame, [a, a + 90], [24, 640], clamp));
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', paddingBottom: SAFE_BOTTOM}}>
      <div style={{position: 'absolute', inset: 0, display: 'flex', flexWrap: 'wrap', gap: 6, padding: 30, alignContent: 'flex-start',
        opacity: view === 'pixels' ? 0.35 : 0.9}}>
        {Array.from({length: n}, (_, i) => (
          <div key={i} style={{width: 52, height: 30, borderRadius: 6, border: '1px solid rgba(127,227,255,0.45)', background: 'rgba(20,34,58,0.6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6}}>
            <div style={{width: 8, height: 8, borderRadius: '50%', background: (i * 7 + Math.floor(frame / 4)) % 3 === 0 ? MINT : '#1d3b52'}} />
            <div style={{width: 8, height: 8, borderRadius: '50%', background: (i * 5 + Math.floor(frame / 5)) % 4 === 0 ? GOLD : '#1d3b52'}} />
          </div>
        ))}
      </div>
      <div style={{...pop(frame, begin + 8), ...glass({padding: '22px 46px', textAlign: 'center'})}}>
        <Pair ctx={ctx} text={view === 'pixels'
          ? {zh: '每一个像素：几百次 z² + c，每一次都是许多个 1 + 1', en: 'Every pixel: hundreds of z² + c, each one many 1 + 1s'}
          : {zh: '几十亿个开关，一秒钟开关几十亿次', en: 'Billions of switches, flipping billions of times a second'}} size={ctx.lang === 'zh' ? 44 : 36} />
      </div>
    </AbsoluteFill>
  );
};

/** Guess a number from 1 to 8 with three yes-or-no questions. */
const GuessCard: FC<CardProps> = (p) => {
  const {ctx, frame} = p;
  const {fps} = useVideoConfig();
  const q = ctx.cue('it10-03');
  const qa = at(p, 'it10-03');
  const qlen = (q.speech.end - q.speech.start) * fps;
  const steps = [qa + qlen * 0.16, qa + qlen * 0.33, qa + qlen * 0.5].map(Math.round);
  const asked = steps.filter((s) => frame >= s).length;
  const alive = (n: number) => (asked === 0 ? true : asked === 1 ? n > 4 : asked === 2 ? n > 6 : n === 7);
  const questions: Label[] = [{zh: '比 4 大吗？ 是', en: 'Bigger than 4? Yes'}, {zh: '比 6 大吗？ 是', en: 'Bigger than 6? Yes'}, {zh: '是 7 吗？ 是！', en: 'Is it 7? Yes!'}];
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', paddingBottom: SAFE_BOTTOM, gap: 40, color: WHITE, opacity: interpolate(frame, [0, 14], [0, 1], clamp)}}>
      <div style={{textAlign: 'center'}}>
        <Pair ctx={ctx} text={{zh: '我心里想了 1 到 8 里的一个数', en: 'I’m thinking of a number from 1 to 8'}} size={ctx.lang === 'zh' ? 46 : 40} />
      </div>
      <div style={{display: 'flex', gap: 18}}>
        {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
          <div key={n} style={glass({width: 150, height: 150, borderRadius: 18, display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: MONO, fontSize: 72, fontWeight: 700, opacity: alive(n) ? 1 : 0.16,
            border: asked === 3 && n === 7 ? `3px solid ${GOLD}` : undefined, color: asked === 3 && n === 7 ? GOLD : WHITE})}>{n}</div>
        ))}
      </div>
      <div style={{display: 'flex', gap: 22, minHeight: 74}}>
        {questions.slice(0, asked).map((qq, i) => (
          <div key={i} style={{...pop(frame, steps[i]), ...glass({padding: '14px 30px', borderRadius: 999}), fontFamily: font(ctx), fontSize: 34}}>
            <span style={{fontFamily: MONO, color: CYAN, marginRight: 14}}>{`Q${i + 1}`}</span>{pick(ctx, qq)}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

/** Shannon's ruler: information = how many yes-or-no questions you still have to ask. */
const RulerCard: FC<CardProps> = (p) => {
  const {ctx, frame} = p;
  const final = p.ctx.cue('it10-11').start * p.ctx.tl.fps - p.start <= frame + 1;
  const shown = RULER.map((r) => ({...r, a: Math.max(8, at(p, r.at))})).filter((r) => r.a <= frame + 8 || final);
  const title: Label = final
    ? {zh: '信息 = 你还得问多少', en: 'Information = how much you still have to ask'}
    : {zh: '香农的尺子：要问几个“是不是”', en: 'Shannon’s ruler: how many yes-or-no questions?'};
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', paddingBottom: SAFE_BOTTOM, color: WHITE, opacity: interpolate(frame, [0, 14], [0, 1], clamp)}}>
      <div style={{textAlign: 'center', marginBottom: 50}}>
        <Kicker>CLAUDE SHANNON  ·  1948</Kicker>
        <Pair ctx={ctx} text={title} size={ctx.lang === 'zh' ? 58 : 46} />
      </div>
      <div style={{position: 'relative', width: 1700, height: 300}}>
        <div style={{position: 'absolute', left: 0, right: 0, top: 118, height: 10, borderRadius: 5,
          background: `linear-gradient(90deg, ${CYAN}, ${MINT}, ${GOLD})`, boxShadow: glow}} />
        {RULER.map((r, i) => {
          const x = (i / (RULER.length - 1)) * 1640 + 30;
          const s = shown.find((m) => m.value === r.value);
          const a = s ? (final ? Math.max(8, at(p, 'it10-11')) + i * 6 : s.a) : 1e9;
          const value = ctx.lang === 'en' && r.value === '几百万' ? RULER_MILLIONS_EN : r.value;
          return (
            <div key={r.value} style={{position: 'absolute', left: x - 136, width: 272, textAlign: 'center', top: 0}}>
              <div style={{...pop(frame, a), fontFamily: MONO, fontSize: value.length > 4 ? 40 : 56, fontWeight: 700, color: i >= 4 ? GOLD : WHITE, textShadow: glow, height: 90}}>{value}</div>
              <div style={{width: 4, height: 54, margin: '0 auto', background: s ? WHITE : 'rgba(255,255,255,0.25)'}} />
              <div style={{...pop(frame, a + 6), fontFamily: font(ctx), fontSize: 26, color: SOFT, marginTop: 18, lineHeight: 1.3}}>{pick(ctx, r.label)}</div>
            </div>
          );
        })}
      </div>
      <div style={{fontFamily: font(ctx), fontSize: 26, color: SOFT, marginTop: 10}}>
        {pick(ctx, {zh: '单位：比特 = 一个“是不是”的问题', en: 'Unit: the bit = one yes-or-no question'})}
      </div>
    </AbsoluteFill>
  );
};

/** One pixel of the fractal: its position goes into the formula, a few hundred times, and out comes its colour. */
const FractalPixelCard: FC<CardProps> = (p) => {
  const {ctx, frame, len} = p;
  const [x, y] = FRACTAL_PIXEL.at;
  const runEnd = Math.round(len * 0.72);
  const n = Math.round(interpolate(frame, [16, runEnd], [0, FRACTAL_PIXEL.iterations], clamp));
  const done = frame >= runEnd;
  const [r, g, b] = FRACTAL_PIXEL.rgb;
  const ring = 18 + 6 * Math.sin(frame / 5);
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: x - ring, top: y - ring, width: ring * 2, height: ring * 2, borderRadius: '50%',
        border: `5px solid ${GOLD}`, boxShadow: `0 0 0 4px rgba(7,11,20,0.85), 0 0 26px ${GOLD}`}} />
      <div style={{position: 'absolute', left: x + 24, top: y + 2, width: 300, height: 2, background: GOLD, opacity: 0.8}} />
      <div style={{position: 'absolute', left: 1140, top: 300, ...glass({padding: '30px 40px', width: 660})}}>
        <Kicker>{pick(ctx, {zh: '一个像素', en: 'ONE PIXEL'})}</Kicker>
        <div style={{fontFamily: MONO, fontSize: 30, color: WHITE}}>c = {FRACTAL_PIXEL.c}</div>
        <div style={{fontFamily: font(ctx), fontSize: 26, color: SOFT, marginTop: 6}}>{pick(ctx, {zh: '它在画面上的位置', en: 'its position in the picture'})}</div>
        <div style={{fontFamily: MONO, fontSize: 40, color: CYAN, marginTop: 22, textShadow: glow}}>z → z² + c</div>
        <div style={{fontFamily: font(ctx), fontSize: 34, marginTop: 18}}>
          {pick(ctx, {zh: '第', en: 'step'})} <span style={{fontFamily: MONO, fontSize: 52, color: GOLD}}>{n}</span> {pick(ctx, {zh: '次', en: ''})}
        </div>
        <div style={{display: 'flex', alignItems: 'center', gap: 20, marginTop: 18, opacity: done ? 1 : 0.25}}>
          <div style={{width: 64, height: 64, borderRadius: 10, background: `rgb(${r},${g},${b})`, boxShadow: `0 0 20px rgb(${r},${g},${b})`}} />
          <div style={{fontFamily: font(ctx), fontSize: 30}}>{pick(ctx, {zh: '跑出去了 → 就是这个颜色', en: 'escaped → this is its colour'})}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const CardView: FC<CardProps & {card: Card}> = ({card, ...p}) => {
  const {ctx, frame, len} = p;
  const o = interpolate(frame, [6, 22, len - 16, len], [0, 1, 1, 0], clamp);
  const y = interpolate(frame, [6, 22], [18, 0], clamp);
  const out = interpolate(frame, [len - 16, len], [1, 0], clamp);
  switch (card.kind) {
    case 'words':
      return (
        <Centre opacity={o} y={y}>
          <div style={glass({padding: '42px 70px', textAlign: 'center', maxWidth: 1500, textWrap: 'balance'})}>
            {card.kicker && <div style={{fontFamily: font(ctx), fontSize: 26, color: CYAN, textShadow: glow, marginBottom: 14}}>{pick(ctx, card.kicker)}</div>}
            <Pair ctx={ctx} text={card.text} size={ctx.lang === 'zh' ? 62 : 52} />
            {card.small && (
              <div style={{marginTop: 26, paddingTop: 22, borderTop: '1px solid rgba(127,227,255,0.3)'}}>
                <Pair ctx={ctx} text={card.small} size={ctx.lang === 'zh' ? 36 : 32} />
              </div>
            )}
          </div>
        </Centre>
      );
    case 'big':
      return (
        <Centre opacity={o} y={y}>
          <div style={glass({padding: '40px 90px', textAlign: 'center'})}>
            <div style={{fontFamily: MONO, fontSize: 150, fontWeight: 700, color: WHITE, textShadow: glow, whiteSpace: 'nowrap'}}>{card.text}</div>
            {card.small && <div style={{marginTop: 14}}><Pair ctx={ctx} text={card.small} size={ctx.lang === 'zh' ? 40 : 34} /></div>}
          </div>
        </Centre>
      );
    case 'note':
      return (
        <div style={{position: 'absolute', left: 44, bottom: SAFE_BOTTOM + 10, opacity: o, transform: `translateY(${y}px)`, maxWidth: 1500}}>
          <div style={glass({padding: '18px 30px', borderRadius: 16})}>
            <div style={{fontFamily: font(ctx), fontSize: 38, fontWeight: 700, textShadow: glow}}>{pick(ctx, card.text)}</div>
            <div style={{fontFamily: ctx.lang === 'zh' ? EN_FONT : ZH_FONT, fontSize: 24, color: SOFT, marginTop: 6}}>{other(ctx, card.text)}</div>
          </div>
        </div>
      );
    case 'carry':
      return <AbsoluteFill style={{opacity: out}}><CarryCard {...p} /></AbsoluteFill>;
    case 'adder':
      return <AbsoluteFill style={{opacity: out}}><AdderCard {...p} /></AbsoluteFill>;
    case 'guess':
      return <AbsoluteFill style={{opacity: out}}><GuessCard {...p} /></AbsoluteFill>;
    case 'ruler':
      return <AbsoluteFill style={{opacity: out}}><RulerCard {...p} /></AbsoluteFill>;
    case 'fractal-pixel':
      return <AbsoluteFill style={{opacity: out}}><FractalPixelCard {...p} /></AbsoluteFill>;
  }
};

const ShotCard: FC<{ctx: Ctx; card: Card; len: number; start: number}> = ({ctx, card, len, start}) => {
  const frame = useCurrentFrame();
  return <CardView ctx={ctx} card={card} frame={frame} len={len} start={start} />;
};

// ---------------------------------------------------------------- opening and end

/** Inception Space's own loading screen (index.html #entry-loading, at 1.5x). */
const LoadingScreen: FC<{frame: number; fps: number}> = ({frame, fps}) => {
  const turn = ((frame / fps) * 1000) / 850;
  return (
    <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 42%, rgba(52, 105, 117, 0.28), transparent 38%), rgba(4, 7, 13, 0.97)',
      alignItems: 'center', justifyContent: 'center'}}>
      <div style={{display: 'grid', justifyItems: 'center', gap: 21, color: '#f6f8fb', textAlign: 'center', fontFamily: '-apple-system, "SF Pro Text", system-ui, sans-serif'}}>
        <div style={{width: 69, height: 69, borderRadius: '50%', border: '4.5px solid rgba(158, 215, 189, 0.2)', borderTopColor: '#9ed7bd',
          transform: `rotate(${turn * 360}deg)`, boxSizing: 'border-box'}} />
        <div style={{fontSize: 27, fontWeight: 750}}>Opening Space Museum...</div>
        <div style={{fontSize: 19.5, color: '#a9b7c8'}}>Preparing the world and its living paintings</div>
      </div>
    </AbsoluteFill>
  );
};

const Intro: FC<{ctx: Ctx; len: number}> = ({ctx, len}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const load = Math.round(INTRO.loadingSeconds * fps);
  const loadingOpacity = interpolate(frame, [load - 12, load + 12], [1, 0], clamp);
  const titleIn = load + 6;
  const titleOut = Math.round(ctx.cue(INTRO.titleUntil).speech.start * fps) - 14;
  const titleOpacity = interpolate(frame, [titleIn, titleIn + 20, titleOut - 16, titleOut], [0, 1, 1, 0], clamp);
  const lift = interpolate(frame, [titleIn, titleIn + 20], [16, 0], clamp);
  const zh = ctx.lang === 'zh';
  return (
    <AbsoluteFill>
      <ClipSpan ctx={ctx} file={INTRO.chamber.file} span={INTRO.chamber.span} main={len - FADE} len={len} push={0.04} />
      <AbsoluteFill style={{opacity: titleOpacity, alignItems: 'center', justifyContent: 'center', paddingBottom: SAFE_BOTTOM}}>
        <div style={glass({padding: '46px 96px', textAlign: 'center', transform: `translateY(${lift}px)`})}>
          <Kicker>LUCAS ACADEMY  //  FUN INFORMATICS 01</Kicker>
          <div style={{fontFamily: zh ? ZH_FONT : EN_FONT, fontSize: zh ? 96 : 72, fontWeight: 800, textShadow: glow}}>{pick(ctx, ctx.tl.title)}</div>
          <div style={{fontFamily: zh ? EN_FONT : ZH_FONT, fontSize: 30, color: SOFT, marginTop: 10}}>{other(ctx, ctx.tl.title)}</div>
          <div style={{fontFamily: zh ? ZH_FONT : EN_FONT, fontSize: 34, color: CYAN, marginTop: 22, textShadow: glow}}>{pick(ctx, INTRO.series)}</div>
          <div style={{fontFamily: zh ? ZH_FONT : EN_FONT, fontSize: 28, color: WHITE, marginTop: 18, letterSpacing: 1.5}}>{pick(ctx, INTRO.byline)}</div>
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{opacity: loadingOpacity}}>
        <LoadingScreen frame={frame} fps={fps} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const EndCard: FC<{ctx: Ctx}> = ({ctx}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 24], [0, 1], {extrapolateRight: 'clamp'});
  const zh = ctx.lang === 'zh';
  const credits: Label[] = [
    {zh: '画面：Inception Space 太空博物馆 · 像素科学室（The Pixel Science Room）', en: 'Filmed in Inception Space · The Pixel Science Room'},
    {zh: '分形：用 z → z² + c 一帧一帧算出来的', en: 'Fractal: computed frame by frame from z → z² + c'},
    {zh: '电路画面：AI 生成', en: 'Circuit pictures: AI-generated'},
    {zh: '“你最喜欢的游戏”：Printables 上 Link 透光浮雕（CC0）的像素重制；Link © Nintendo', en: '“Your favorite game”: a pixel remake of a CC0 Link lithophane on Printables; Link © Nintendo'},
    {zh: '音乐：Echoes in the Void（Yancy，用 Suno 制作）', en: 'Music: Echoes in the Void (Yancy, made with Suno)'},
  ];
  return (
    <AbsoluteFill style={{background: BG, alignItems: 'center', justifyContent: 'center', opacity: o, color: WHITE, textAlign: 'center'}}>
      <Pair ctx={ctx} text={ctx.tl.title} size={zh ? 64 : 54} />
      <div style={{fontFamily: zh ? ZH_FONT : EN_FONT, fontSize: 30, color: CYAN, marginTop: 14}}>{pick(ctx, INTRO.series)}</div>
      <div style={{width: 120, height: 2, background: CYAN, margin: '30px 0', boxShadow: glow}} />
      <div style={{fontFamily: MONO, fontSize: 34, color: CYAN, textShadow: glow}}>is.lucasacademy.org</div>
      <div style={{fontFamily: zh ? ZH_FONT : EN_FONT, fontSize: 26, marginTop: 12, color: SOFT}}>
        {pick(ctx, {zh: '走进像素科学室，按 R，慢慢看', en: 'Walk into the Pixel Science Room, press R, and look slowly'})}
      </div>
      <div style={{fontFamily: zh ? ZH_FONT : EN_FONT, fontSize: 21, marginTop: 46, color: SOFT, lineHeight: 1.75}}>
        {credits.map((c) => <div key={c.en}>{pick(ctx, c)}</div>)}
      </div>
      <div style={{fontFamily: zh ? ZH_FONT : EN_FONT, fontSize: 26, marginTop: 36, color: WHITE, letterSpacing: 1.5}}>{pick(ctx, INTRO.byline)}</div>
      <div style={{fontFamily: MONO, fontSize: 24, marginTop: 16, letterSpacing: 8, color: CYAN}}>LUCAS ACADEMY</div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- the film

export const FunInformaticsVideo: FC<FunInformaticsProps> = ({lang, tl}) => {
  const {fps} = useVideoConfig();
  if (!tl) return <Missing name="npm run fi01:timeline" />;
  const byId = new Map(tl.cues.map((c) => [c.id, c]));
  const ctx: Ctx = {tl, lang, cue: (id) => {
    const c = byId.get(id);
    if (!c) throw new Error(`no cue ${id}`);
    return c;
  }};
  const f = (s: number) => Math.round(s * fps);
  const introLen = f(ctx.cue(INTRO.last).end) + FADE;
  const visuals = VISUALS.map((v) => ({...v, start: f(ctx.cue(v.from).start), end: f(ctx.cue(v.to).end)}));
  const cards = CARDS.map((c) => ({...c, start: f(ctx.cue(c.from).start), end: f(ctx.cue(c.to).end)}));
  const endStart = f(tl.endCardStart);
  return (
    <AbsoluteFill style={{background: BG}}>
      <Sequence from={0} durationInFrames={introLen}>
        <Intro ctx={ctx} len={introLen} />
      </Sequence>
      {visuals.map(({from, visual, start, end}) => {
        const main = end - start;
        const len = main + FADE;
        return (
          <Sequence key={`v-${from}`} from={start} durationInFrames={len}>
            <FadeIn frames={FADE}>
              <VisualView ctx={ctx} v={visual} main={main} len={len} />
            </FadeIn>
          </Sequence>
        );
      })}
      {cards.map(({from, card, start, end}) => (
        <Sequence key={`c-${from}`} from={start} durationInFrames={end - start + FADE}>
          <ShotCard ctx={ctx} card={card} len={end - start + FADE} start={start} />
        </Sequence>
      ))}
      <Sequence from={endStart - FADE}>
        <EndCard ctx={ctx} />
      </Sequence>
      <Audio src={staticFile(`${DIR}/audio/${lang}.mix.wav`)} />
    </AbsoluteFill>
  );
};

/** YouTube cover: only the question, big in the film's language, small in the other, over the fractal. */
export const FunInformaticsCover: FC<{lang: Lang}> = ({lang}) => {
  const zh = lang === 'zh';
  return (
    <AbsoluteFill style={{background: BG}}>
      <Img src={staticFile(`${DIR}/images/stills/fractal-main-20.png`)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse 70% 65% at 50% 50%, rgba(7,11,20,0.82), rgba(7,11,20,0.35) 100%)'}} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: WHITE}}>
        <div style={{fontFamily: zh ? ZH_FONT : EN_FONT, fontSize: zh ? 190 : 150, fontWeight: 800, lineHeight: 1.1, textShadow: glow}}>
          {zh ? '计算机怎么算' : 'How Does a Computer'}
        </div>
        <div style={{fontSize: zh ? 230 : 200, fontWeight: 800, lineHeight: 1.1, textShadow: glow, marginTop: 10}}>
          {!zh && <span style={{fontFamily: EN_FONT, fontSize: 170}}>Add </span>}
          <span style={{fontFamily: MONO, color: GOLD}}>{zh ? '1+1=？' : '1+1=?'}</span>
        </div>
        <div style={{fontFamily: zh ? EN_FONT : ZH_FONT, fontSize: 56, color: SOFT, marginTop: 34}}>
          {zh ? 'How Does a Computer Add 1 + 1=?' : '计算机怎么算 1+1=？'}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
