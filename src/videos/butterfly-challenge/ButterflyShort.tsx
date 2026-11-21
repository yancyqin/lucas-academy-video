/**
 * The vertical shorts of 「Challenge: Which Butterflies Are Real?」 (docs/butterfly-challenge/shorts.md), 1080x1920,
 * timed by scripts/butterfly-challenge/build_short.py (public/butterfly-challenge/shorts/<name>.json).
 * v2 (Yancy 2026-11-16: 「节奏要紧凑很多很多！不要那么多废话，就是猜，猜完展示结果（视频）」): no voice, two rounds.
 * Each round: the two pictures stacked (A above, B below) under the question, a 3-2-1 badge between them; the reveal
 * marks the real one with a green ✓ and the AI one with a red ✗ and puts each model's robot on the picture it picked;
 * then the real butterfly's video plays in a band over its own blurred copy, its name underneath. It opens on the first
 * pair's pictures (no fade from black) and ends on the last video, so the loop goes straight back into a guess.
 * Same look as the film (ButterflyChallengeVideo.tsx): icons, few words, English large / Chinese small, no byline.
 */
import type { FC } from "react";
import { AbsoluteFill, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig,
  type CalculateMetadataFunction } from "remotion";
import { BG, Chip, GOLD, INK, MUTED, Mark, REAL, SANS, SHADOW, SOFT, WRONG, fadeIn } from "./ButterflyChallengeVideo";

const file = (p: string) => staticFile(`butterfly-challenge/${p}`);

type Pair = { n: number; real: "A" | "B"; astra: "A" | "B"; fable: "A" | "B"; photo: string; clipCredit: string;
  name: { zh: string; en: string } };
type Round = { pair: Pair; start: number; reveal: number; clip: number; end: number; video: { src: string; from: number; rate: number } };
type ShortTl = { fps: number; durationSeconds: number; rounds: Round[] };
export type ShortProps = { name: string; tl?: ShortTl | null };

export const calculateShortMetadata: CalculateMetadataFunction<ShortProps> = async ({ props, abortSignal }) => {
  const r = await fetch(file(`shorts/${props.name}.json`), { signal: abortSignal });
  if (!r.ok) throw Error("Run scripts/butterfly-challenge/build_short.py first");
  const tl = (await r.json()) as ShortTl;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.round(tl.durationSeconds * tl.fps) };
};

const PW = 1000, PH = 562, PX = 40, AY = 392, BY = 1004;
const XFADE = 0.3; // picture view → video, and video → the next round's pictures

const Question: FC<{ rounds: number; at: number }> = ({ rounds, at }) => (
  <div style={{ position: "absolute", top: 110, left: 0, right: 0, textAlign: "center", fontFamily: SANS, color: INK, textShadow: SHADOW }}>
    <div style={{ fontSize: 92, fontWeight: 800, letterSpacing: -1 }}>Which One Is <span style={{ color: REAL }}>Real</span>?</div>
    <div style={{ fontSize: 50, fontWeight: 500, color: SOFT, marginTop: 4 }}>哪只是真的？</div>
    <div style={{ display: "flex", justifyContent: "center", gap: 16, marginTop: 22 }}>
      {Array.from({ length: rounds }, (_, k) => (
        <div key={k} style={{ width: 18, height: 18, borderRadius: 9, background: k === at ? GOLD : "rgba(255,255,255,.28)" }} />
      ))}
    </div>
  </div>
);

const Pictures: FC<{ r: Round; t: number }> = ({ r, t }) => {
  const p = r.pair;
  const revealed = t >= r.reveal;
  const pop = fadeIn(t, r.reveal, 0.35);
  const step = (r.reveal - r.start) / 3;
  const into = (t - r.start) / step;
  const count = Math.max(1, Math.min(3, 3 - Math.floor(into)));
  const tick = into % 1;
  return (
    <>
      {(["A", "B"] as const).map((side) => {
        const real = p.real === side;
        const y = side === "A" ? AY : BY;
        const ring = revealed ? (real ? REAL : WRONG) : "rgba(255,255,255,.14)";
        const picks = [p.astra === side ? "Astra" : null, p.fable === side ? "Fable" : null].filter(Boolean) as string[];
        return (
          <div key={side}>
            <div style={{ position: "absolute", left: PX, top: y, width: PW, height: PH, borderRadius: 18, overflow: "hidden",
              boxShadow: revealed ? `0 0 0 ${5 + 4 * pop}px ${ring}` : `0 0 0 2px ${ring}`,
              filter: revealed && !real ? `saturate(${1 - 0.2 * pop}) brightness(${1 - 0.18 * pop})` : undefined }}>
              <Img src={file(`pairs/${String(p.n).padStart(2, "0")}-${side}.jpg`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </div>
            {/* mark and robots along the top-left: the Shorts buttons cover the right edge and the title text the bottom
                of the lower picture */}
            {revealed && <div style={{ position: "absolute", left: PX + 24, top: y + 24 }}><Mark real={real} size={130} pop={pop} /></div>}
            {revealed && (
              <div style={{ position: "absolute", left: PX + 24 + 130 + 16, top: y + 24 + 37, display: "flex", gap: 14, fontFamily: SANS }}>
                {picks.map((who, k) => (
                  <Chip key={who} who={who} style={{ background: "rgba(10,12,13,.78)", opacity: fadeIn(t, r.reveal + 0.15 + 0.15 * k, 0.3) }} />
                ))}
              </div>
            )}
            {revealed && real && (
              <div style={{ position: "absolute", left: PX + 4, top: y + PH + 8, fontFamily: SANS, fontSize: 22, color: MUTED, opacity: pop }}>{p.photo}</div>
            )}
          </div>
        );
      })}
      {!revealed && (
        <div style={{ position: "absolute", left: 540 - 85, top: (AY + PH + BY) / 2 - 85, width: 170, height: 170, borderRadius: 85,
          display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(13,16,18,.92)",
          boxShadow: `0 0 0 6px rgba(233,196,106,${0.9 - 0.6 * tick})`, fontFamily: SANS, fontSize: 104, fontWeight: 800, color: GOLD,
          transform: `scale(${1 + 0.14 * (1 - Math.min(1, tick * 4))})` }}>{count}</div>
      )}
    </>
  );
};

const Clip: FC<{ r: Round; t: number; fps: number }> = ({ r, t, fps }) => {
  const local = t - r.clip;
  const card = fadeIn(local, 0.1, 0.3);
  // the Sequence starts the video at the round's clip time; frames inside it count from there
  const video = (blurred: boolean) => (
    <Sequence from={Math.round(r.clip * fps)} durationInFrames={Math.round((r.end + XFADE - r.clip) * fps) + 1} layout="none">
      <OffthreadVideo src={file(r.video.src)} muted playbackRate={r.video.rate} startFrom={Math.round(r.video.from * fps)}
        style={{ width: "100%", height: "100%", objectFit: "cover", ...(blurred ? { filter: "blur(40px) brightness(.55)", transform: "scale(1.2)" } : {}) }} />
    </Sequence>
  );
  return (
    <AbsoluteFill style={{ background: "#000", opacity: fadeIn(local, 0, XFADE) }}>
      <AbsoluteFill>{video(true)}</AbsoluteFill>
      <div style={{ position: "absolute", left: 0, top: 620, width: 1080, height: 608, overflow: "hidden" }}>{video(false)}</div>
      <div style={{ position: "absolute", left: 28, top: 646, opacity: card }}><Mark real size={96} pop={card} /></div>
      {r.pair.clipCredit && (
        <div style={{ position: "absolute", left: 0, right: 0, top: 1240, textAlign: "center", fontFamily: SANS, fontSize: 24, color: SOFT, opacity: card }}>{r.pair.clipCredit}</div>
      )}
      <div style={{ position: "absolute", left: 0, right: 0, top: 1290, textAlign: "center", fontFamily: SANS, color: INK, textShadow: SHADOW,
        opacity: card, transform: `translateY(${(1 - card) * 14}px)` }}>
        <div style={{ fontSize: 96, fontWeight: 800 }}>{r.pair.name.en}</div>
        <div style={{ fontSize: 54, color: SOFT, marginTop: 6 }}>{r.pair.name.zh}</div>
      </div>
    </AbsoluteFill>
  );
};

export const ButterflyShort: FC<ShortProps> = ({ tl }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  if (!tl) return <AbsoluteFill style={{ background: BG }} />;
  const at = Math.max(0, tl.rounds.findIndex((r, k) => t >= r.start && (k === tl.rounds.length - 1 || t < tl.rounds[k + 1].start)));
  return (
    <AbsoluteFill style={{ background: BG }}>
      {tl.rounds.map((r, k) => {
        const shown = t >= r.start && t < r.end + XFADE;
        if (!shown) return null;
        // every round after the first fades its pictures in over the previous round's video
        const pics = k === 0 ? 1 : fadeIn(t, r.start, XFADE);
        return (
          <AbsoluteFill key={r.pair.n}>
            {t < r.clip + XFADE && <AbsoluteFill style={{ background: BG, opacity: pics }}><Pictures r={r} t={t} /></AbsoluteFill>}
            {t >= r.clip && <Clip r={r} t={t} fps={fps} />}
          </AbsoluteFill>
        );
      })}
      <Question rounds={tl.rounds.length} at={at} />
    </AbsoluteFill>
  );
};
