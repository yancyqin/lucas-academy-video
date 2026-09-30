import type {FC, ReactNode} from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  Sequence,
  Video,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import timeline from '../../data/whole-person-01.json';
import {SHOTS, TITLE_IMAGE, type Card, type Drift, type Label, type Picture, type Shot} from './shots';

/**
 * "全人教育①：老师的权柄从哪里来？" — lucas-academy-media#5.
 *
 * One picture edit; `audio` picks the narration track (zh = Yancy, en = Louise)
 * and `subtitles` burns in the bilingual captions, spoken language on top.
 * The clean master is audio 'none' + no subtitles, for YouTube multi-audio.
 */

export type WholePersonProps = {audio: 'zh' | 'en' | 'none'; subtitles: boolean};

type Cue = (typeof timeline.cues)[number];

export const WP_FPS = timeline.fps;
export const WP_DURATION = Math.ceil(timeline.durationSeconds * timeline.fps);

const FADE = 18; // frames of cross-dissolve between shots
const CAPTION_TOP = 846; // cards stay above the caption band

const ZH_FONT = '"PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif';
const EN_FONT = '"Avenir Next", "Helvetica Neue", Arial, sans-serif';
const SERIF = 'Georgia, "Songti SC", serif';
const PAPER = '#f5eedf';
const INK = '#2b2418';
const WARM = '#c9704f';
const BLUE = '#2f4a6d';
const CREAM = '#fffaf0';
const BG = '#1b1712';

const cueById = new Map(timeline.cues.map((c) => [c.id, c]));
const concepts = new Set<string>(timeline.concepts);
const footage = new Set<string>(timeline.footage);
const ease = Easing.bezier(0.42, 0, 0.58, 1);
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const Placeholder: FC<{name: string; what: string}> = ({name, what}) => (
  <AbsoluteFill style={{background: '#ece2cc', alignItems: 'center', justifyContent: 'center'}}>
    <div
      style={{
        border: '4px dashed #b9a57c', borderRadius: 24, padding: '40px 64px', color: '#6b5a37',
        fontFamily: EN_FONT, fontSize: 38, textAlign: 'center', marginBottom: 200,
      }}
    >
      {what}
      <div style={{fontSize: 30, marginTop: 12, fontFamily: 'Menlo, monospace'}}>{name}</div>
    </div>
  </AbsoluteFill>
);

const ConceptImage: FC<{name: string; drift?: Drift; p: number}> = ({name, drift, p}) => {
  if (!concepts.has(name)) return <Placeholder name={`concept/${name}`} what="Codex concept image" />;
  const d = drift ?? {z0: 1, z1: 1.04, x: 0.5, y: 0.5};
  const z = d.z0 + (d.z1 - d.z0) * ease(p);
  return (
    <AbsoluteFill style={{background: PAPER, overflow: 'hidden'}}>
      <Img
        src={staticFile(`whole-person-01/concept/${name}`)}
        style={{
          width: 1920, height: 1080, objectFit: 'cover',
          transform: `scale(${z})`, transformOrigin: `${d.x * 100}% ${d.y * 100}%`,
        }}
      />
    </AbsoluteFill>
  );
};

/** Muted stock footage, looped if shorter than the shot, with a gentle push. */
const Footage: FC<{file: string; fallback: string; p: number}> = ({file, fallback, p}) =>
  footage.has(file) ? (
    <AbsoluteFill style={{background: BG, overflow: 'hidden'}}>
      <Video
        src={staticFile(`whole-person-01/footage/${file}`)}
        muted
        loop
        style={{width: 1920, height: 1080, objectFit: 'cover', transform: `scale(${1 + 0.04 * p})`}}
      />
    </AbsoluteFill>
  ) : concepts.has(fallback) ? (
    <ConceptImage name={fallback} p={p} />
  ) : (
    <Placeholder name={`footage/${file}  ·  or concept/${fallback}`} what="Stock footage" />
  );

/** Side-by-side panels that appear one by one on their cues. */
const Panels: FC<{images: string[]; reveal: string[]; shotStart: number; frame: number}> = ({
  images, reveal, shotStart, frame,
}) => {
  const {fps} = useVideoConfig();
  const w = images.length === 3 ? 580 : 860;
  return (
    <AbsoluteFill style={{background: PAPER, flexDirection: 'row', gap: 28, alignItems: 'center', justifyContent: 'center', paddingBottom: 1080 - CAPTION_TOP}}>
      {images.map((img, i) => {
        const cue = cueById.get(reveal[i])!;
        // Panels sharing one reveal cue step in across that cue's speech.
        const same = reveal.filter((r) => r === reveal[i]);
        const k = reveal.slice(0, i).filter((r) => r === reveal[i]).length;
        const speech = cue.speech.zh.end - cue.speech.zh.start;
        const at = Math.round((cue.speech.zh.start + (same.length > 1 ? (k * speech) / same.length : 0)) * fps) - shotStart;
        const o = interpolate(frame, [at, at + 14], [0, 1], clamp);
        const y = interpolate(frame, [at, at + 14], [24, 0], clamp);
        return (
          <div key={img} style={{opacity: o, transform: `translateY(${y}px)`, width: w, height: (w * 9) / 16, borderRadius: 14, overflow: 'hidden', boxShadow: '0 10px 30px rgba(0,0,0,0.18)', position: 'relative'}}>
            {concepts.has(img) ? (
              <Img src={staticFile(`whole-person-01/concept/${img}`)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
            ) : (
              <div style={{width: '100%', height: '100%', background: '#e2d6ba', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Menlo, monospace', fontSize: 22, color: '#6b5a37'}}>{img}</div>
            )}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const PictureView: FC<{picture: Picture; p: number; frame: number; shotStart: number}> = ({picture, p, frame, shotStart}) => {
  switch (picture.kind) {
    case 'concept': {
      const mix = picture.next ? ease(interpolate(p, [0.35, 0.6], [0, 1], clamp)) : 0;
      return (
        <AbsoluteFill>
          <ConceptImage name={picture.image} drift={picture.drift} p={p} />
          {picture.next && (
            <AbsoluteFill style={{opacity: mix}}>
              <ConceptImage name={picture.next} drift={picture.drift} p={p} />
            </AbsoluteFill>
          )}
        </AbsoluteFill>
      );
    }
    case 'footage':
      return <Footage file={picture.file} fallback={picture.fallback} p={p} />;
    case 'panels':
      return <Panels images={picture.images} reveal={picture.reveal} shotStart={shotStart} frame={frame} />;
  }
};

const Chip: FC<{side: 'left' | 'right'; opacity: number; children: ReactNode}> = ({side, opacity, children}) => (
  <div
    style={{
      position: 'absolute', [side]: 48, top: 40, opacity, padding: '8px 18px', borderRadius: 999,
      background: 'rgba(27,23,18,0.66)', color: CREAM, fontFamily: EN_FONT, fontSize: 22,
      border: '1px solid rgba(255,250,240,0.3)',
    }}
  >
    {children}
  </div>
);

const Panel: FC<{children: ReactNode; opacity: number; y?: number}> = ({children, opacity, y = 0}) => (
  <AbsoluteFill style={{alignItems: 'center', justifyContent: 'flex-end', paddingBottom: 1080 - CAPTION_TOP + 44, opacity}}>
    <div
      style={{
        maxWidth: 1440, padding: '44px 72px', borderRadius: 18, background: 'rgba(255,250,240,0.95)',
        color: INK, textAlign: 'center', boxShadow: '0 18px 60px rgba(0,0,0,0.35)', transform: `translateY(${y}px)`,
      }}
    >
      {children}
    </div>
  </AbsoluteFill>
);

const CardView: FC<{card: Card; frame: number; len: number; cardStart: number; shotStart: number}> = ({
  card, frame, len, cardStart, shotStart,
}) => {
  const {fps} = useVideoConfig();
  const o = interpolate(frame, [cardStart, cardStart + 16, len - 20, len - 4], [0, 1, 1, 0], clamp);
  const y = interpolate(frame, [cardStart, cardStart + 16], [16, 0], clamp);
  switch (card.kind) {
    case 'scripture':
      return (
        <Panel opacity={o} y={y}>
          <div style={{fontFamily: ZH_FONT, fontSize: 50, fontWeight: 600, lineHeight: 1.4, whiteSpace: "nowrap"}}>{card.text.zh}</div>
          <div style={{fontFamily: SERIF, fontSize: 40, fontStyle: 'italic', marginTop: 16}}>{card.text.en}</div>
          <div style={{fontFamily: EN_FONT, fontSize: 24, marginTop: 24, color: '#7a6644', letterSpacing: 1}}>
            <span style={{fontFamily: ZH_FONT}}>{card.source.zh}</span> · {card.source.en}
          </div>
        </Panel>
      );
    case 'words':
      return (
        <Panel opacity={o} y={y}>
          <div style={{fontFamily: ZH_FONT, fontSize: 68, fontWeight: 700, color: BLUE}}>{card.text.zh}</div>
          <div style={{fontFamily: SERIF, fontSize: 42, fontStyle: 'italic', marginTop: 10}}>{card.text.en}</div>
        </Panel>
      );
    case 'questions':
      return (
        <AbsoluteFill style={{alignItems: 'flex-end', justifyContent: 'center', paddingRight: 72, paddingBottom: 1080 - CAPTION_TOP}}>
          <div style={{display: 'flex', flexDirection: 'column', gap: 20, opacity: interpolate(frame, [len - 20, len - 4], [1, 0], clamp)}}>
            {card.items.map((q, i) => {
              const at = Math.round(cueById.get(card.reveal[i])!.speech.zh.start * fps) - shotStart;
              const qo = interpolate(frame, [at, at + 14], [0, 1], clamp);
              const qx = interpolate(frame, [at, at + 14], [30, 0], clamp);
              return (
                <div key={q.zh} style={{opacity: qo, transform: `translateX(${qx}px)`, padding: '18px 30px', borderRadius: 14, background: 'rgba(255,250,240,0.95)', borderLeft: `6px solid ${WARM}`, boxShadow: '0 10px 30px rgba(0,0,0,0.25)', maxWidth: 760}}>
                  <div style={{fontFamily: ZH_FONT, fontSize: 40, fontWeight: 600, color: INK}}>{q.zh}</div>
                  <div style={{fontFamily: EN_FONT, fontSize: 26, color: '#5b4d36', marginTop: 4}}>{q.en}</div>
                </div>
              );
            })}
          </div>
        </AbsoluteFill>
      );
    case 'math':
      return (
        <AbsoluteFill style={{alignItems: 'flex-end', justifyContent: 'center', paddingRight: 120, paddingBottom: 1080 - CAPTION_TOP, opacity: o}}>
          <div style={{padding: '36px 64px', borderRadius: 16, background: '#2f3b33', color: CREAM, border: '10px solid #8a6a43', boxShadow: '0 16px 40px rgba(0,0,0,0.35)', fontFamily: '"Chalkboard SE", "Comic Sans MS", sans-serif', fontSize: 110, letterSpacing: 8}}>
            2 + 3 = <span style={{color: '#f0c75e'}}>5</span>
          </div>
        </AbsoluteFill>
      );
  }
};

const ShotView: FC<{shot: Shot; len: number; start: number}> = ({shot, len, start}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = Math.min(1, frame / Math.max(1, len));
  const chip = interpolate(frame, [12, 30, len - 20, len], [0, 1, 1, 0], clamp);
  const cardStart = shot.cardFrom ? Math.round(cueById.get(shot.cardFrom)!.speech.zh.start * fps) - start : 14;
  return (
    <AbsoluteFill>
      <PictureView picture={shot.picture} p={p} frame={frame} shotStart={start} />
      {shot.concept && (
        <Chip side="left" opacity={chip}>
          <span style={{fontFamily: ZH_FONT}}>概念示意</span> · Concept illustration
        </Chip>
      )}
      {shot.ref && (
        <Chip side="right" opacity={chip}>
          <span style={{fontFamily: ZH_FONT}}>{shot.ref.zh}</span> · {shot.ref.en}
        </Chip>
      )}
      {shot.card && <CardView card={shot.card} frame={frame} len={len} cardStart={cardStart} shotStart={start} />}
    </AbsoluteFill>
  );
};

const TitleCard: FC<{len: number}> = ({len}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 18, len - 18, len], [0, 1, 1, 0], clamp);
  return (
    <AbsoluteFill>
      <ConceptImage name={TITLE_IMAGE} p={0} drift={{z0: 1.02, z1: 1.02, x: 0.5, y: 0.5}} />
      <AbsoluteFill style={{background: 'rgba(27,23,18,0.55)', alignItems: 'center', justifyContent: 'center', opacity: o, color: CREAM, textAlign: 'center'}}>
        <div style={{fontFamily: EN_FONT, fontSize: 26, letterSpacing: 8, opacity: 0.8}}>LUCAS ACADEMY · 全人教育 · WHOLE-PERSON EDUCATION</div>
        <div style={{fontFamily: ZH_FONT, fontSize: 84, fontWeight: 700, marginTop: 28}}>{timeline.title.zh}</div>
        <div style={{fontFamily: SERIF, fontSize: 48, fontStyle: 'italic', marginTop: 14, maxWidth: 1500}}>{timeline.title.en}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Subtitle: FC<{cue: Cue; primary: 'zh' | 'en'}> = ({cue, primary}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 6], [0, 1], {extrapolateRight: 'clamp'});
  const zh = <div key="zh" style={{fontFamily: ZH_FONT, fontSize: primary === 'zh' ? 42 : 30, fontWeight: primary === 'zh' ? 600 : 400}}>{cue.zh}</div>;
  const en = <div key="en" style={{fontFamily: EN_FONT, fontSize: primary === 'en' ? 38 : 28, fontWeight: primary === 'en' ? 600 : 400}}>{cue.en}</div>;
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 30, opacity: o}}>
      <div
        style={{
          maxWidth: 1780, padding: '12px 30px', borderRadius: 12, background: 'rgba(20,16,12,0.74)',
          color: CREAM, textAlign: 'center', lineHeight: 1.32, display: 'flex', flexDirection: 'column', gap: 6,
        }}
      >
        {primary === 'zh' ? [zh, en] : [en, zh]}
      </div>
    </AbsoluteFill>
  );
};

const EndCard: FC = () => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 24], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: BG, alignItems: 'center', justifyContent: 'center', opacity: o, color: CREAM, textAlign: 'center'}}>
      <div style={{fontFamily: ZH_FONT, fontSize: 60, fontWeight: 700}}>{timeline.title.zh}</div>
      <div style={{fontFamily: SERIF, fontSize: 40, fontStyle: 'italic', marginTop: 10}}>{timeline.title.en}</div>
      <div style={{width: 120, height: 4, background: WARM, margin: '34px 0'}} />
      <div style={{fontFamily: ZH_FONT, fontSize: 30}}>全文 · Read the essay</div>
      <div style={{fontFamily: 'Menlo, monospace', fontSize: 28, marginTop: 12, color: '#f0c75e'}}>lucasacademy.org/research/whole-person-education</div>
      <div style={{fontFamily: EN_FONT, fontSize: 21, marginTop: 56, opacity: 0.78, maxWidth: 1560, lineHeight: 1.55}}>
        <span style={{fontFamily: ZH_FONT}}>经文：马太福音 6:13、28:18–20、13:52、11:25；使徒行传 17:11；路加福音 11:52；约翰福音 13:13–14。中文引文：和合本。</span>
        <br />
        English Scripture: Matthew 6:13 doxology from the NIV footnote. Scripture quotations taken from The Holy Bible, New International Version® NIV®
        Copyright © 1973, 1978, 1984, 2011 by Biblica, Inc.® Used by permission of Biblica, Inc.® All rights reserved worldwide.
        <br />
        <span style={{fontFamily: ZH_FONT}}>课堂情景均为虚构的概念示意；课堂应用是 Lucas Academy 的解释</span> · Classroom scenes are invented concept illustrations; classroom applications are Lucas Academy's reading.
      </div>
      <div style={{fontFamily: EN_FONT, fontSize: 30, marginTop: 48, letterSpacing: 6}}>LUCAS ACADEMY</div>
    </AbsoluteFill>
  );
};

export const WholePersonVideo: FC<WholePersonProps> = ({audio, subtitles}) => {
  const {fps} = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);
  const primary = audio === 'en' ? 'en' : 'zh';
  const lead = f(timeline.leadIn);
  const shots = SHOTS.map((shot, i) => ({
    shot,
    start: i === 0 ? lead - FADE : f(cueById.get(shot.from)!.start),
    end: f(cueById.get(shot.to)!.end),
  }));
  const endStart = f(timeline.endCardStart);
  return (
    <AbsoluteFill style={{background: BG}}>
      <Sequence from={0} durationInFrames={lead}>
        <TitleCard len={lead} />
      </Sequence>
      {shots.map(({shot, start, end}, i) => {
        const len = end - start + (i + 1 < shots.length ? FADE : 0);
        return (
          <Sequence key={shot.from} from={start} durationInFrames={len}>
            <FadeIn frames={FADE}>
              <ShotView shot={shot} len={len} start={start} />
            </FadeIn>
          </Sequence>
        );
      })}
      <Sequence from={endStart - FADE}>
        <EndCard />
      </Sequence>
      {subtitles &&
        timeline.cues.map((cue) => {
          const start = f(cue.speech[primary].start);
          return (
            <Sequence key={cue.id} from={start} durationInFrames={f(cue.end) - start - 3}>
              <Subtitle cue={cue} primary={primary} />
            </Sequence>
          );
        })}
      {audio !== 'none' && <Audio src={staticFile(`whole-person-01/audio/${audio}.wav`)} />}
    </AbsoluteFill>
  );
};

const FadeIn: FC<{frames: number; children: ReactNode}> = ({frames, children}) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{opacity: interpolate(frame, [0, frames], [0, 1], {extrapolateRight: 'clamp'})}}>{children}</AbsoluteFill>;
};
