/**
 * Vertical shorts from 「动物想什么？AI 知道吗？」 (Yancy 2026-11-11: 「出2个短视频吧，多用动物。一个用海洋动物，开场用G10；一个用
 * 其他动物」). 1080×1920: the film's 16:9 shots in a band across the middle (sides trimmed a little), over a blurred, darkened copy of the
 * same shot; the title on top (bold white, "AI" in the cover's yellow). Each short is the English video with a separate
 * Chinese track (Yancy 11-11), so build_short.py writes no captions and the SRTs go alongside; the caption layer under
 * the band (kept left of the Shorts buttons) only draws when a timeline has captions.
 * Timeline from scripts/ai-animal-mind/build_short.py: public/ai-animal-mind/shorts/<short>.json.
 */
import type { FC } from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  type CalculateMetadataFunction,
} from "remotion";

const DIR = "ai-animal-mind";
const file = (p: string) => staticFile(`${DIR}/${p}`);
const FADE = 0.3;
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const BAND = { top: 640, height: 700 };  // a 16:9 shot scaled to 700 high, its sides trimmed 7 % each: bigger animals
const YELLOW = "#ffc83d";

type Shot = { k: "clip"; clip: string; in: number; rate: number; start: number; end: number };
type Caption = { start: number; end: number; text: string };
export type AiAnimalShortTimeline = {
  fps: number; durationSeconds: number; lang: "en" | "zh"; title: string[]; shots: Shot[]; captions: Caption[];
};
export type AiAnimalShortProps = { short: string; tl?: AiAnimalShortTimeline | null };

export const calculateAiAnimalShortMetadata: CalculateMetadataFunction<AiAnimalShortProps> = async ({ props, abortSignal }) => {
  const r = await fetch(file(`shorts/${props.short}.json`), { signal: abortSignal });
  if (!r.ok) throw Error(`Run scripts/ai-animal-mind/build_short.py first (${props.short})`);
  const tl = (await r.json()) as AiAnimalShortTimeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

const ShotLayer: FC<{ s: Shot; dur: number; first: boolean }> = ({ s, dur, first }) => {
  const { fps } = useVideoConfig();
  const t = useCurrentFrame() / fps;
  const op = first ? 1 : interpolate(t, [0, FADE], [0, 1], clamp);
  const sc = interpolate(t, [0, dur + FADE], [1.0, 1.04], clamp);
  const video = (style: React.CSSProperties) => (
    <OffthreadVideo src={file(`clips/${s.clip}.mp4`)} muted playbackRate={s.rate}
      startFrom={Math.round(s.in * fps)} style={style} />
  );
  return (
    <AbsoluteFill style={{ opacity: op }}>
      <AbsoluteFill style={{ overflow: "hidden" }}>
        {video({ position: "absolute", inset: -80, width: "calc(100% + 160px)", height: "calc(100% + 160px)",
          objectFit: "cover", filter: "blur(36px) brightness(.42) saturate(1.15)" })}
      </AbsoluteFill>
      <div style={{ position: "absolute", left: 0, top: BAND.top, width: 1080, height: BAND.height, overflow: "hidden",
        boxShadow: "0 18px 60px rgba(0,0,0,.55)" }}>
        <div style={{ width: "100%", height: "100%", transform: `scale(${sc})` }}>
          {video({ width: "100%", height: "100%", objectFit: "cover" })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Title: FC<{ lines: string[]; lang: "en" | "zh" }> = ({ lines, lang }) => {
  const zh = lang === "zh";
  const paint = (line: string) =>
    line.split(/(AI)/).map((part, i) => (part === "AI" ? <span key={i} style={{ color: YELLOW }}>AI</span> : part));
  return (
    <div style={{ position: "absolute", left: 40, right: 40, top: zh ? 330 : 350, textAlign: "center", color: "#fff",
      fontFamily: zh ? '"PingFang SC", sans-serif' : '"SF Pro Display", -apple-system, "Helvetica Neue", sans-serif',
      fontWeight: zh ? 600 : 800, fontSize: zh ? 100 : 70, lineHeight: zh ? 1.22 : 1.18, letterSpacing: zh ? 4 : 0,
      textShadow: "0 0 2px rgba(0,0,0,.55), 0 4px 14px rgba(0,0,0,.5), 0 10px 40px rgba(0,0,0,.45)" }}>
      {lines.map((l, i) => <div key={i}>{paint(l)}</div>)}
    </div>
  );
};

const Captions: FC<{ caps: Caption[]; lang: "en" | "zh" }> = ({ caps, lang }) => {
  const { fps } = useVideoConfig();
  const t = useCurrentFrame() / fps;
  const c = caps.find((x) => t >= x.start && t < x.end + 0.15);
  if (!c) return null;
  const zh = lang === "zh";
  return (
    <div style={{ position: "absolute", left: 60, width: 880, top: BAND.top + BAND.height + 56, textAlign: "center",
      color: "#fff", whiteSpace: "pre-line",
      fontFamily: zh ? '"PingFang SC", sans-serif' : '"SF Pro Text", -apple-system, "Helvetica Neue", sans-serif',
      fontWeight: 600, fontSize: zh ? 54 : 48, lineHeight: 1.32,
      textShadow: "0 0 2px rgba(0,0,0,.7), 0 3px 12px rgba(0,0,0,.6)" }}>
      {c.text}
    </div>
  );
};

export const AiAnimalShort: FC<AiAnimalShortProps> = ({ tl }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  if (!tl) return <AbsoluteFill style={{ background: "#000" }} />;
  const n = tl.shots.length;
  const out = interpolate(frame / fps, [tl.durationSeconds - 0.8, tl.durationSeconds], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ background: "#071318" }}>
      <AbsoluteFill style={{ opacity: out }}>
        {tl.shots.map((s, i) => {
          const dur = s.end - s.start;
          return (
            <Sequence key={i} from={Math.round(s.start * fps)}
              durationInFrames={Math.max(1, Math.round((dur + (i + 1 < n ? FADE : 0)) * fps))}>
              <ShotLayer s={s} dur={dur} first={i === 0} />
            </Sequence>
          );
        })}
        <Title lines={tl.title} lang={tl.lang} />
        <Captions caps={tl.captions} lang={tl.lang} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
