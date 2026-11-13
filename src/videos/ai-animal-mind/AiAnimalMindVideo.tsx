/**
 * 「动物想什么？AI 知道吗？」 / "What Are Animals Thinking? Does AI Know?" (AI-ANIMAL-TALK.md, docs/ai-animal-mind/).
 *
 * One picture for an English and a Chinese voice track (Yancy 2026-11-10), so nothing is written on screen: no title,
 * no labels, no chapter bar, no end card. Only animal footage (Pexels), Yancy's Muse clips (or their Codex first frames
 * while a clip is not in yet), Yancy's own sunset photos, two Commons pictures (Clever Hans in 1904, Monet's water-lily
 * bridge) and the climax of the Jesu, Joy of Man's Desiring film. Shots come from scripts/ai-animal-mind/edit.json,
 * timed by build_timeline.py, and cross-fade into each other.
 */
import type { FC } from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
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
const FADE = 0.6;
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

type Shot = {
  k: "clip" | "still"; start: number; end: number; clip?: string; rate?: number; in?: number; plain?: boolean;
  img?: string; zoom?: [number, number]; focus?: [number, number]; fit?: "cover" | "contain";
};
export type AiAnimalTimeline = { fps: number; durationSeconds: number; shots: Shot[] };
export type AiAnimalProps = { tl?: AiAnimalTimeline | null };

export const calculateAiAnimalMetadata: CalculateMetadataFunction<AiAnimalProps> = async ({ props, abortSignal }) => {
  const r = await fetch(file("timeline.json"), { signal: abortSignal });
  if (!r.ok) throw Error("Run scripts/ai-animal-mind/assets.py and build_timeline.py first");
  const tl = (await r.json()) as AiAnimalTimeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

const useT = () => useCurrentFrame() / useVideoConfig().fps;

/** Footage: fills the frame, drifting in very slightly so cuts between clips feel alive; the Jesu film plays as it is. */
const Clip: FC<{ s: Shot; dur: number }> = ({ s, dur }) => {
  const t = useT();
  const { fps } = useVideoConfig();
  const sc = s.plain ? 1 : interpolate(t, [0, dur + FADE], [1.0, 1.04], clamp);
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <AbsoluteFill style={{ transform: `scale(${sc})` }}>
        <OffthreadVideo src={file(`clips/${s.clip}.mp4`)} muted playbackRate={s.rate ?? 1}
          startFrom={Math.round((s.in ?? 0) * fps)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** A picture with a slow zoom toward its focus; a picture that is not 16:9 sits whole over a blurred copy of itself. */
const Still: FC<{ s: Shot; dur: number }> = ({ s, dur }) => {
  const t = useT();
  const [z0, z1] = s.zoom ?? [1.0, 1.06];
  const [fx, fy] = s.focus ?? [0.5, 0.5];
  const z = interpolate(t, [0, dur + FADE], [z0, z1], { ...clamp, easing: Easing.inOut(Easing.sin) });
  const src = file(`stills/${s.img}`);
  const origin = `${fx * 100}% ${fy * 100}%`;
  if (s.fit === "contain") {
    return (
      <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
        <Img src={src} style={{ position: "absolute", inset: -60, width: "calc(100% + 120px)", height: "calc(100% + 120px)",
          objectFit: "cover", filter: "blur(40px) brightness(.45) saturate(1.1)" }} />
        <AbsoluteFill style={{ transform: `scale(${z})`, transformOrigin: origin }}>
          <Img src={src} style={{ width: "100%", height: "100%", objectFit: "contain",
            filter: "drop-shadow(0 20px 60px rgba(0,0,0,.6))" }} />
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <AbsoluteFill style={{ transform: `scale(${z})`, transformOrigin: origin }}>
        <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Faded: FC<{ first: boolean; last: boolean; dur: number; children: React.ReactNode }> = ({ first, last, dur, children }) => {
  const t = useT();
  const fin = first ? interpolate(t, [0, 1.5], [0, 1], clamp) : interpolate(t, [0, FADE], [0, 1], clamp);
  const fout = last ? interpolate(t, [dur - 2.5, dur], [1, 0], clamp) : 1;
  return <AbsoluteFill style={{ opacity: fin * fout }}>{children}</AbsoluteFill>;
};

export const AiAnimalMindVideo: FC<AiAnimalProps> = ({ tl }) => {
  const { fps } = useVideoConfig();
  if (!tl) return <AbsoluteFill style={{ background: "#000" }} />;
  const n = tl.shots.length;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {tl.shots.map((s, i) => {
        const from = Math.round(s.start * fps);
        const dur = s.end - s.start;
        const len = Math.max(1, Math.round((dur + (i + 1 < n ? FADE : 0)) * fps));
        return (
          <Sequence key={i} from={from} durationInFrames={len}>
            <Faded first={i === 0} last={i + 1 === n} dur={dur}>
              {s.k === "clip" ? <Clip s={s} dur={dur} /> : <Still s={s} dur={dur} />}
            </Faded>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
