import type {CSSProperties, FC, ReactNode} from 'react';
import {
  type CalculateMetadataFunction,
  AbsoluteFill,
  Audio,
  Img,
  Loop,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {EDUCATOR, INTRO, QUESTION, SECTION_BG, SHOTS, type BigQuestion, type Card, type Clip, type Label, type Shot} from './shots';

/**
 * "全人教育的五个理念 / Five Principles of Whole-Person Education" —
 * lucas-academy-media#5, told to parents, following the parents deck.
 *
 * Two films, one per language (zh = Yancy, en = Louise), each paced by its own
 * narration. Nothing is burned in: captions ship as zh-Hans.srt + en.srt.
 * Cards and labels are translucent "glass" over the app recordings.
 */

export type Lang = 'zh' | 'en';

type Cue = {
  id: string;
  section: string;
  zh: string;
  en: string;
  start: number;
  end: number;
  speech: {start: number; end: number};
};

/** Written by scripts/whole-person-01/build_timeline.py into public/whole-person-01/ — generated, never committed. */
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

export type WholePersonProps = {lang: Lang; tl?: Timeline | null};

export const WP_FPS = 30;

/** Load the film's timeline (and so its length) before rendering. Run `npm run wp01:timeline` first. */
export const calculateWholePersonMetadata: CalculateMetadataFunction<WholePersonProps> = async ({props, abortSignal}) => {
  const file = `whole-person-01/timeline.${props.lang}.json`;
  const response = await fetch(staticFile(file), {signal: abortSignal});
  if (!response.ok) throw new Error(`${file} is missing — run npm run wp01:timeline first`);
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
const BG = '#070b14';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** Translucent tech panel: frosted backdrop, hairline cyan edge, faint glow. */
const glass = (extra: CSSProperties = {}): CSSProperties => ({
  background: 'linear-gradient(135deg, rgba(20,34,58,0.50), rgba(10,18,34,0.34))',
  backdropFilter: 'blur(16px) saturate(140%)',
  WebkitBackdropFilter: 'blur(16px) saturate(140%)',
  border: '1px solid rgba(127,227,255,0.38)',
  boxShadow: '0 0 0 1px rgba(255,255,255,0.05) inset, 0 0 26px rgba(127,227,255,0.16), 0 18px 50px rgba(0,0,0,0.35)',
  borderRadius: 18,
  color: WHITE,
  ...extra,
});

const glow = '0 0 18px rgba(127,227,255,0.35), 0 2px 12px rgba(0,0,0,0.6)';

type Ctx = {tl: Timeline; lang: Lang; cue: (id: string) => Timeline['cues'][number]};

const Missing: FC<{name: string}> = ({name}) => (
  <AbsoluteFill style={{background: '#101828', alignItems: 'center', justifyContent: 'center'}}>
    <div style={{border: '2px dashed #4b6385', borderRadius: 16, padding: '24px 40px', color: '#9fb3d1', fontFamily: MONO, fontSize: 26}}>{name}</div>
  </AbsoluteFill>
);

/**
 * A recording, looped if shorter than its slot; 'contain' sits on a blurred copy.
 * OffthreadVideo extracts exact frames with ffmpeg (the HTML5 <Video> froze and
 * jumped back when rendering), and <Loop> repeats it from `from`.
 */
const ClipView: FC<{ctx: Ctx; clip: Clip; dim?: number; blur?: number; push?: number}> = ({ctx, clip, dim = 0, blur = 0, push = 0}) => {
  const {fps} = useVideoConfig();
  if (!ctx.tl.footage.includes(clip.file)) return <Missing name={`footage/${clip.file}`} />;
  const src = staticFile(`whole-person-01/footage/${clip.file}`);
  const trimBefore = Math.round((clip.from ?? 0) * fps);
  const total = Math.floor((ctx.tl.footageSeconds as Record<string, number>)[clip.file] * fps);
  const loopLen = Math.max(1, total - trimBefore - 1);
  const cover: CSSProperties = {position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'};
  const layer = (style: CSSProperties) => (
    <Loop durationInFrames={loopLen}>
      <OffthreadVideo src={src} trimBefore={trimBefore} muted style={style} />
    </Loop>
  );
  return (
    <AbsoluteFill style={{background: BG, overflow: 'hidden'}}>
      {clip.fit === 'contain' && layer({...cover, filter: 'blur(36px) brightness(0.55)', transform: 'scale(1.15)'})}
      {layer({
        ...cover,
        objectFit: clip.fit === 'contain' ? 'contain' : 'cover',
        filter: blur ? `blur(${blur}px)` : undefined,
        transform: `scale(${1 + push + (blur ? 0.03 : 0)})`,
      })}
      {dim > 0 && <AbsoluteFill style={{background: `radial-gradient(ellipse at center, rgba(7,11,20,${dim * 0.7}), rgba(7,11,20,${dim * 1.5}))`}} />}
    </AbsoluteFill>
  );
};

const Tag: FC<{children: ReactNode; style?: CSSProperties}> = ({children, style}) => (
  <div style={glass({padding: '9px 20px', borderRadius: 999, fontFamily: EN_FONT, fontSize: 24, ...style})}>{children}</div>
);

const Kicker: FC<{children: ReactNode}> = ({children}) => (
  <div style={{fontFamily: MONO, fontSize: 22, letterSpacing: 4, color: CYAN, textShadow: glow, marginBottom: 14}}>{children}</div>
);

/** Who is speaking, on the card: the team's name in the film's own type, not the mono code style. */
const TeamLabel: FC<{ctx: Ctx; label: Label}> = ({ctx, label}) => (
  <div style={{fontFamily: ctx.lang === 'zh' ? ZH_FONT : EN_FONT, fontSize: 24, letterSpacing: 1, color: CYAN, textShadow: glow, marginBottom: 12}}>
    {ctx.lang === 'zh' ? label.zh : label.en}
  </div>
);

const Centre: FC<{children: ReactNode; opacity: number; y: number}> = ({children, opacity, y}) => (
  <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', paddingBottom: SAFE_BOTTOM, opacity}}>
    <div style={{transform: `translateY(${y}px)`}}>{children}</div>
  </AbsoluteFill>
);

const Reveal: FC<{at: number; frame: number; children: ReactNode; dx?: number}> = ({at, frame, children, dx = 0}) => {
  const o = interpolate(frame, [at, at + 14], [0, 1], clamp);
  const d = interpolate(frame, [at, at + 14], [1, 0], clamp);
  return <div style={{opacity: o, transform: `translate(${dx * d}px, ${dx ? 0 : 18 * d}px)`}}>{children}</div>;
};

/** Primary language large, the other smaller beneath it. */
const Pair: FC<{ctx: Ctx; text: Label; size: number}> = ({ctx, text, size}) => {
  const first = ctx.lang === 'zh' ? text.zh : text.en;
  const second = ctx.lang === 'zh' ? text.en : text.zh;
  return (
    <>
      <div style={{fontFamily: ctx.lang === 'zh' ? ZH_FONT : EN_FONT, fontSize: size, fontWeight: 700, lineHeight: 1.35, textShadow: glow}}>{first}</div>
      <div style={{fontFamily: ctx.lang === 'zh' ? EN_FONT : ZH_FONT, fontSize: Math.round(size * 0.55), color: SOFT, marginTop: 10, lineHeight: 1.4}}>{second}</div>
    </>
  );
};

/** A question in the cover's big type: line one white with its key word in gold, line two cyan. */
const BigQuestionText: FC<{lang: Lang; question: BigQuestion}> = ({lang, question}) => {
  const zh = lang === 'zh';
  const font = zh ? ZH_FONT : EN_FONT;
  const [before, highlight, after] = question.first[lang];
  return (
    <>
      <div style={{fontFamily: font, fontSize: zh ? 200 : question.second ? 128 : 150, fontWeight: 800, lineHeight: 1.12, textShadow: glow}}>
        {before}<span style={{color: '#ffc94d'}}>{highlight}</span>{after}
      </div>
      {question.second && (
        <div style={{fontFamily: font, fontSize: zh ? 200 : 168, fontWeight: 800, lineHeight: 1.12, color: CYAN, textShadow: glow}}>
          {question.second[lang]}
        </div>
      )}
    </>
  );
};

/** Darkens the middle of the picture so big type reads on any footage. */
const Scrim: FC = () => (
  <AbsoluteFill style={{background: 'radial-gradient(ellipse 62% 58% at 50% 50%, rgba(7,11,20,0.62), rgba(7,11,20,0) 100%)'}} />
);

const CardView: FC<{ctx: Ctx; card: Card; frame: number; len: number; shotStart: number}> = ({ctx, card, frame, len, shotStart}) => {
  const {fps} = useVideoConfig();
  const cueFrame = (id: string) => Math.round(ctx.cue(id).speech.start * fps) - shotStart;
  const o = interpolate(frame, [6, 22, len - 16, len], [0, 1, 1, 0], clamp);
  const y = interpolate(frame, [6, 22], [18, 0], clamp);
  const out = interpolate(frame, [len - 16, len], [1, 0], clamp);
  switch (card.kind) {
    case 'question':
      return (
        <AbsoluteFill style={{opacity: o}}>
          <Scrim />
          <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: WHITE, transform: `translateY(${y}px)`}}>
            <BigQuestionText lang={ctx.lang} question={card.question} />
          </AbsoluteFill>
        </AbsoluteFill>
      );
    case 'principle':
      return (
        <Centre opacity={o} y={y}>
          <div style={glass({padding: '44px 90px', textAlign: 'center', minWidth: 760})}>
            <Kicker>{`PRINCIPLE 0${card.n}  //  理念 ${card.n}`}</Kicker>
            <Pair ctx={ctx} text={card.title} size={ctx.lang === 'zh' ? 110 : 84} />
            {card.subtitle && (
              <div style={{marginTop: 18, paddingTop: 16, borderTop: '1px solid rgba(127,227,255,0.3)'}}>
                <Pair ctx={ctx} text={card.subtitle} size={ctx.lang === 'zh' ? 40 : 34} />
              </div>
            )}
          </div>
        </Centre>
      );
    case 'words':
      return (
        <Centre opacity={o} y={y}>
          <div style={glass({padding: '42px 70px', textAlign: 'center', maxWidth: 1460, textWrap: 'balance'})}>
            {card.kicker && <TeamLabel ctx={ctx} label={card.kicker} />}
            <Pair ctx={ctx} text={card.text} size={ctx.lang === 'zh' ? 58 : 50} />
            {card.small && (
              <div style={{marginTop: 26, paddingTop: 22, borderTop: '1px solid rgba(127,227,255,0.3)'}}>
                <Pair ctx={ctx} text={card.small} size={ctx.lang === 'zh' ? 36 : 32} />
              </div>
            )}
          </div>
        </Centre>
      );
    case 'quote':
    case 'scripture':
      return (
        <Centre opacity={o} y={y}>
          <div style={glass({padding: '40px 70px', textAlign: 'center', maxWidth: 1560, textWrap: 'balance'})}>
            <Kicker>{card.kind === 'scripture' ? 'SCRIPTURE  //  经文' : 'QUOTE  //  引文'}</Kicker>
            <Pair ctx={ctx} text={{zh: `“${card.text.zh}”`, en: card.text.en.startsWith('“') ? card.text.en : `“${card.text.en}”`}} size={ctx.lang === 'zh' ? 46 : 40} />
            <div style={{fontFamily: MONO, fontSize: 22, marginTop: 22, color: CYAN, letterSpacing: 1}}>
              {ctx.lang === 'zh' ? `${card.source.zh}  ·  ${card.source.en}` : `${card.source.en}  ·  ${card.source.zh}`}
            </div>
          </div>
        </Centre>
      );
    case 'list':
      return (
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', paddingBottom: SAFE_BOTTOM, opacity: out}}>
          {card.heading && (
            <Reveal at={4} frame={frame}>
              <div style={{textAlign: 'center', marginBottom: 30, color: WHITE}}>
                <Pair ctx={ctx} text={card.heading} size={ctx.lang === 'zh' ? 52 : 44} />
              </div>
            </Reveal>
          )}
          <div style={{display: 'flex', flexWrap: 'wrap', gap: 18, justifyContent: 'center', maxWidth: 1640}}>
            {card.items.map((item, i) => {
              const k = card.reveal.slice(0, i).filter((r) => r === card.reveal[i]).length;
              return (
                <Reveal key={item.zh} at={Math.max(6, cueFrame(card.reveal[i])) + k * 12} frame={frame}>
                  <div style={glass({padding: '18px 30px', textAlign: 'center', minWidth: 220, borderTop: `2px solid ${CYAN}`})}>
                    <Pair ctx={ctx} text={item} size={ctx.lang === 'zh' ? 40 : 34} />
                  </div>
                </Reveal>
              );
            })}
          </div>
        </AbsoluteFill>
      );
    case 'steps': {
      const steps: {big: string; tag: string; text: Label}[] = [
        {big: '1', tag: '1 STEP  //  1 步', text: {zh: '我们只比孩子领先一步，让探索的旅程充满乐趣。', en: 'We stay just one step ahead of the kids, so the journey of discovery is fun.'}},
        {big: '1000', tag: '1,000 STEPS  //  1000 步', text: {zh: '我们也领先一千步，让这段旅程安全。', en: 'We stay a thousand steps ahead, so the journey is safe.'}},
      ];
      return (
        <AbsoluteFill style={{flexDirection: 'row', gap: 44, alignItems: 'center', justifyContent: 'center', paddingBottom: SAFE_BOTTOM, opacity: out}}>
          {steps.map((s, i) => (
            <Reveal key={s.big} at={Math.max(6, cueFrame(card.reveal[i]))} frame={frame}>
              <div style={glass({width: 640, padding: '38px 44px', textAlign: 'center', textWrap: 'balance'})}>
                <div style={{fontFamily: EN_FONT, fontSize: 112, fontWeight: 800, lineHeight: 1, color: i ? CYAN : '#ffd27a', textShadow: glow}}>{s.big}</div>
                <div style={{fontFamily: MONO, fontSize: 22, letterSpacing: 3, color: CYAN, margin: '10px 0 20px'}}>{s.tag}</div>
                <Pair ctx={ctx} text={s.text} size={ctx.lang === 'zh' ? 34 : 30} />
              </div>
            </Reveal>
          ))}
        </AbsoluteFill>
      );
    }
    case 'drawing': {
      // The original pencil sketch, then the prepared drawing, then the child's finished
      // artwork (a photo of the real page, only the tabletop cropped away).
      const steps: {file: string; label: Label}[] = [
        {file: card.sketch, label: {zh: '原始铅笔草稿', en: 'Pencil sketch'}},
        {file: card.final, label: {zh: '准备稿', en: 'Prepared drawing'}},
        ...(card.finished ? [{file: card.finished, label: {zh: '最终作品', en: 'Finished artwork'}}] : []),
      ];
      const h = steps.length === 3 ? 560 : 620;
      const one = (file: string, label: Label, last: boolean) => (
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16}}>
          <div style={glass({padding: 10, borderRadius: 14, ...(last ? {border: `1px solid ${CYAN}`} : {})})}>
            {ctx.tl.images.includes(file) ? (
              <Img src={staticFile(`whole-person-01/images/${file}`)} style={{height: h, borderRadius: 8, display: 'block'}} />
            ) : (
              <div style={{width: Math.round(h * 0.75), height: h}}><Missing name={`images/${file}`} /></div>
            )}
          </div>
          <Tag style={last ? {color: CYAN} : undefined}>{ctx.lang === 'zh' ? `${label.zh}  ·  ${label.en}` : `${label.en}  ·  ${label.zh}`}</Tag>
        </div>
      );
      return (
        <AbsoluteFill style={{opacity: interpolate(frame, [0, 14, len - 16, len], [0, 1, 1, 0], clamp)}}>
          {/* The clearer gallery background competes with the children's drawings; quiet it here. */}
          <AbsoluteFill style={{background: 'rgba(7,11,20,0.55)', backdropFilter: 'blur(6px)'}} />
          <div style={{position: 'absolute', left: 60, top: 44}}>
            <Tag style={{fontSize: 30, fontFamily: MONO, color: CYAN}}>{`// ${card.who.en.toUpperCase()}`}</Tag>
          </div>
          <AbsoluteFill style={{flexDirection: 'row', gap: steps.length === 3 ? 44 : 70, alignItems: 'center', justifyContent: 'center', paddingBottom: 60}}>
            {steps.map((step, i) => (
              <Reveal key={step.file} at={i === 0 ? 8 : Math.round(len * (i === 1 ? 0.3 : 0.58))} frame={frame} dx={i ? 40 : 0}>
                {one(step.file, step.label, i === steps.length - 1 && steps.length === 3)}
              </Reveal>
            ))}
          </AbsoluteFill>
        </AbsoluteFill>
      );
    }
    case 'contrast': {
      const side = (s: {term: Label; gloss: Label}, good: boolean, at: number) => (
        <Reveal at={at} frame={frame}>
          <div style={glass({width: 560, padding: '34px 40px', textAlign: 'center', opacity: good ? 1 : 0.62,
            border: good ? `1px solid ${CYAN}` : '1px solid rgba(255,255,255,0.25)'})}>
            <div style={{fontFamily: MONO, fontSize: 22, letterSpacing: 3, color: good ? CYAN : SOFT, marginBottom: 12}}>{good ? '✓' : '✕'}</div>
            <div style={{fontFamily: EN_FONT, fontSize: 56, fontWeight: 700, textShadow: good ? glow : undefined,
              textDecoration: good ? undefined : 'line-through', textDecorationColor: 'rgba(255,255,255,0.5)'}}>{s.term.en}</div>
            <div style={{fontFamily: ctx.lang === 'zh' ? ZH_FONT : EN_FONT, fontSize: 32, color: SOFT, marginTop: 10}}>
              {ctx.lang === 'zh' ? s.gloss.zh : s.gloss.en}
            </div>
          </div>
        </Reveal>
      );
      const start = 10; // the card covers one line (wp01-19): reveal shortly after it begins
      return (
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', paddingBottom: SAFE_BOTTOM, opacity: out}}>
          <AbsoluteFill style={{background: 'rgba(7,11,20,0.5)', backdropFilter: 'blur(6px)', opacity: interpolate(frame, [0, 14], [0, 1], clamp)}} />
          <Reveal at={4} frame={frame}>
            <div style={{textAlign: 'center', marginBottom: 30, color: WHITE}}>
              {card.kicker && <TeamLabel ctx={ctx} label={card.kicker} />}
              <Pair ctx={ctx} text={card.heading} size={ctx.lang === 'zh' ? 48 : 42} />
            </div>
          </Reveal>
          <div style={{display: 'flex', gap: 40, alignItems: 'center'}}>
            {side(card.yes, true, start + 6)}
            <div style={{fontFamily: ctx.lang === 'zh' ? ZH_FONT : EN_FONT, fontSize: 30, color: SOFT}}>
              {ctx.lang === 'zh' ? '而不是' : 'rather than'}
            </div>
            {side(card.no, false, start + 30)}
          </div>
        </AbsoluteFill>
      );
    }
    case 'image':
      return ctx.tl.images.includes(card.file) ? (
        <Img src={staticFile(`whole-person-01/images/${card.file}`)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}} />
      ) : (
        <Missing name={`images/${card.file}`} />
      );
  }
};

const Demo: FC<{ctx: Ctx; demo: NonNullable<Shot['demo']>; len: number}> = ({ctx, demo, len}) => {
  const frame = useCurrentFrame();
  const chip = interpolate(frame, [14, 30, len - 16, len], [0, 1, 1, 0], clamp);
  const fadeOut = interpolate(frame, [len - FADE, len], [1, 0], clamp);
  return (
    <AbsoluteFill style={{opacity: fadeOut}}>
      <ClipView ctx={ctx} clip={demo} push={0.03 * (frame / Math.max(1, len))} />
      {demo.caption && (
        <div style={{position: 'absolute', left: 44, top: 40, opacity: chip}}>
          <Tag style={{fontSize: 26}}>
            <span style={{fontFamily: MONO, color: CYAN, marginRight: 12}}>● DEMO</span>
            {ctx.lang === 'zh' ? demo.caption.zh : demo.caption.en}
          </Tag>
        </div>
      )}
      {demo.url && (
        <div style={{position: 'absolute', right: 44, top: 40, opacity: chip}}>
          <Tag style={{fontFamily: MONO, fontSize: 24, color: CYAN}}>{demo.url}</Tag>
        </div>
      )}
    </AbsoluteFill>
  );
};

/** Inception Space's own loading screen (index.html #entry-loading, at 1.5x). */
/**
 * The opening (see INTRO): the first frame is the cover — the question, big — plus Lucas Academy, the
 * film's name and the byline, on the transit chamber. It gives way to 「谁是教育者？」 in the same type,
 * which leaves as the answer begins.
 */
const Intro: FC<{ctx: Ctx; len: number}> = ({ctx, len}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const at = (id: string) => Math.round(ctx.cue(id).speech.start * fps);
  const coverOut = at(INTRO.coverUntil);
  const coverOpacity = interpolate(frame, [coverOut - 14, coverOut + 4], [1, 0], clamp);
  const educatorIn = coverOut;
  const educatorOut = at(INTRO.educatorUntil);
  const educatorOpacity = interpolate(frame, [educatorIn, educatorIn + 16, educatorOut - 4, educatorOut + 14], [0, 1, 1, 0], clamp);
  const lift = interpolate(frame, [educatorIn, educatorIn + 16], [16, 0], clamp);
  const out = interpolate(frame, [len - FADE, len], [1, 0], clamp);
  const zh = ctx.lang === 'zh';
  return (
    <AbsoluteFill style={{opacity: out}}>
      <ClipView ctx={ctx} clip={INTRO.chamber} push={0.04 * (frame / Math.max(1, len))} />
      <AbsoluteFill style={{opacity: Math.max(coverOpacity, educatorOpacity)}}>
        <Scrim />
      </AbsoluteFill>
      <AbsoluteFill style={{opacity: coverOpacity, alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: WHITE}}>
        <Kicker>LUCAS ACADEMY  //  BRINGER OF LIGHT</Kicker>
        <div style={{marginTop: 18}}><BigQuestionText lang={ctx.lang} question={QUESTION} /></div>
        <div style={{fontFamily: zh ? ZH_FONT : EN_FONT, fontSize: 46, color: SOFT, marginTop: 44}}>{INTRO.name[ctx.lang]}</div>
        <div style={{fontFamily: EN_FONT, fontSize: 34, color: WHITE, marginTop: 14, letterSpacing: 1.5}}>{INTRO.byline[ctx.lang]}</div>
      </AbsoluteFill>
      <AbsoluteFill style={{opacity: educatorOpacity, alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: WHITE,
        transform: `translateY(${lift}px)`}}>
        <BigQuestionText lang={ctx.lang} question={EDUCATOR} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const EndCard: FC<{ctx: Ctx}> = ({ctx}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 24], [0, 1], {extrapolateRight: 'clamp'});
  const t = ctx.tl.title;
  const zh = ctx.lang === 'zh';
  return (
    <AbsoluteFill style={{background: BG, alignItems: 'center', justifyContent: 'center', opacity: o, color: WHITE, textAlign: 'center'}}>
      <Pair ctx={ctx} text={{zh: t.zh, en: t.en}} size={zh ? 60 : 50} />
      <div style={{width: 120, height: 2, background: CYAN, margin: '30px 0', boxShadow: glow}} />
      <div style={{fontFamily: MONO, fontSize: 34, color: CYAN, textShadow: glow}}>lucasacademy.org</div>
      <div style={{fontFamily: MONO, fontSize: 24, marginTop: 14, color: SOFT}}>is.lucasacademy.org · lang.lucasacademy.org · lucasacademy.org/challenge</div>
      <div style={{fontFamily: EN_FONT, fontSize: 20, marginTop: 50, color: SOFT, maxWidth: 1600, lineHeight: 1.6}}>
        {zh ? (
          <span style={{fontFamily: ZH_FONT}}>经文：马太福音 13:52；以弗所书 2:10；希伯来书 10:24；诗篇 119:105；创世记 1:28。中文经文：和合本。</span>
        ) : (
          <>Scripture: Matthew 13:52; Ephesians 2:10; Hebrews 10:24; Psalm 119:105; Genesis 1:28.</>
        )}
        <br />
        Scripture quotations marked NIV are taken from The Holy Bible, New International Version® NIV® Copyright © 1973, 1978, 1984, 2011 by
        Biblica, Inc.® Used by permission. All rights reserved worldwide.
        <br />
        Ephesians 2:10 is taken from the Holy Bible, New Living Translation, copyright © 1996, 2004, 2015 by Tyndale House Foundation.
        Used by permission of Tyndale House Publishers, Carol Stream, Illinois 60188. All rights reserved.
        <br />
        {zh ? <span style={{fontFamily: ZH_FONT}}>Lucas 与 Matthew 的画经家长同意使用。</span> : <>Lucas’s and Matthew’s drawings are shared with their parent’s permission.</>}
      </div>
      <div style={{fontFamily: MONO, fontSize: 26, marginTop: 44, letterSpacing: 8, color: CYAN}}>LUCAS ACADEMY</div>
    </AbsoluteFill>
  );
};

const FadeIn: FC<{frames: number; children: ReactNode}> = ({frames, children}) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{opacity: interpolate(frame, [0, frames], [0, 1], {extrapolateRight: 'clamp'})}}>{children}</AbsoluteFill>;
};

const ShotCard: FC<{ctx: Ctx; card: Card; len: number; start: number}> = ({ctx, card, len, start}) => {
  const frame = useCurrentFrame();
  return <CardView ctx={ctx} card={card} frame={frame} len={len} shotStart={start} />;
};

export const WholePersonVideo: FC<WholePersonProps> = ({lang, tl}) => {
  const {fps} = useVideoConfig();
  if (!tl) return <Missing name="npm run wp01:timeline" />;
  const byId = new Map(tl.cues.map((c) => [c.id, c]));
  const ctx: Ctx = {tl, lang, cue: (id) => byId.get(id)!};
  const f = (s: number) => Math.round(s * fps);
  const endStart = f(tl.endCardStart);

  const sections = Object.keys(SECTION_BG).map((key, i) => {
    const cues = tl.cues.filter((c) => c.section === key);
    return {key, start: i === 0 ? 0 : f(cues[0].start), end: f(cues[cues.length - 1].end)};
  });
  // A line the film's timeline does not have (zh wp01-09a: the zh film was not re-made with it) has no shot.
  const shots = SHOTS.filter((shot) => byId.has(shot.from) && byId.has(shot.to))
    .map((shot) => ({shot, start: f(ctx.cue(shot.from).start), end: f(ctx.cue(shot.to).end)}));

  return (
    <AbsoluteFill style={{background: BG}}>
      {sections.map(({key, start, end}) => (
        <Sequence key={key} from={start} durationInFrames={end - start + FADE}>
          <FadeIn frames={start === 0 ? 1 : FADE}>
            <ClipView ctx={ctx} clip={SECTION_BG[key]} dim={0.22} blur={2} />
          </FadeIn>
        </Sequence>
      ))}
      <Sequence from={0} durationInFrames={f(ctx.cue(INTRO.last).end) + FADE}>
        <Intro ctx={ctx} len={f(ctx.cue(INTRO.last).end) + FADE} />
      </Sequence>
      {shots.map(({shot, start, end}) => {
        const len = end - start + FADE;
        return (
          <Sequence key={shot.from} from={start} durationInFrames={len}>
            {shot.demo ? (
              <FadeIn frames={FADE}>
                <Demo ctx={ctx} demo={shot.demo} len={len} />
              </FadeIn>
            ) : shot.card ? (
              <ShotCard ctx={ctx} card={shot.card} len={len} start={start} />
            ) : null}
          </Sequence>
        );
      })}
      <Sequence from={endStart - FADE}>
        <EndCard ctx={ctx} />
      </Sequence>
      <Audio src={staticFile(`whole-person-01/audio/${lang}.mix.wav`)} />
    </AbsoluteFill>
  );
};

/**
 * The YouTube cover: the opening card without what the cover rule keeps off it — only the question,
 * on the title frame's background (the transit chamber 5 s in).
 */
export const WholePersonCover: FC<{lang: Lang}> = ({lang}) => (
  <AbsoluteFill style={{background: BG}}>
    <OffthreadVideo src={staticFile(`whole-person-01/footage/${INTRO.chamber.file}`)} startFrom={150} muted
      style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    <Scrim />
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: WHITE}}>
      <BigQuestionText lang={lang} question={QUESTION} />
    </AbsoluteFill>
  </AbsoluteFill>
);
