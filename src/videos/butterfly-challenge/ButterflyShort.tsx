/**
 * The vertical shorts of 「Challenge: Which Butterflies Are Real?」 (docs/butterfly-challenge/shorts.md): one round of
 * the film each, 1080x1920, timed by scripts/butterfly-challenge/build_short.py (public/butterfly-challenge/shorts/<name>.json).
 * The question stays on top (English large, Chinese small); the two pictures stack (A above, B below) with a 5-4-3-2-1
 * badge between them; the reveal marks the real one with a green ✓ and the AI one with a red ✗, each model's robot sits
 * on the picture it picked; then the real video plays in a band over its own blurred copy, its name underneath.
 * Same look as the film (ButterflyChallengeVideo.tsx): icons, few words, no byline, no burned captions.
 */
import type { FC } from "react";
import { AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig,
  type CalculateMetadataFunction } from "remotion";
import { BG, Chip, GOLD, INK, MUTED, Mark, REAL, SANS, SHADOW, SOFT, WRONG, fadeIn, fadeOut } from "./ButterflyChallengeVideo";

const file = (p: string) => staticFile(`butterfly-challenge/${p}`);

type ShortTl = {
  fps: number; durationSeconds: number; count: number; reveal: number; clip: number; end: number;
  pair: { n: number; real: "A" | "B"; astra: "A" | "B"; fable: "A" | "B"; photo: string; clipCredit: string;
    name: { zh: string; en: string } };
  video: { src: string; from: number; rate: number; hold: number | null; last: string; still: string | null };
};
export type ShortProps = { name: string; tl?: ShortTl | null };

export const calculateShortMetadata: CalculateMetadataFunction<ShortProps> = async ({ props, abortSignal }) => {
  const r = await fetch(file(`shorts/${props.name}.json`), { signal: abortSignal });
  if (!r.ok) throw Error("Run scripts/butterfly-challenge/build_short.py first");
  const tl = (await r.json()) as ShortTl;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

const PW = 1000, PH = 562, PX = 40, AY = 392, BY = 1004;

const Question: FC = () => (
  <div style={{ position: "absolute", top: 120, left: 0, right: 0, textAlign: "center", fontFamily: SANS, color: INK, textShadow: SHADOW }}>
    <div style={{ fontSize: 92, fontWeight: 800, letterSpacing: -1 }}>Which One Is <span style={{ color: REAL }}>Real</span>?</div>
    <div style={{ fontSize: 50, fontWeight: 500, color: SOFT, marginTop: 6 }}>哪只是真的？</div>
  </div>
);

const Pictures: FC<{ tl: ShortTl; t: number }> = ({ tl, t }) => {
  const p = tl.pair;
  const revealed = t >= tl.reveal;
  const r = fadeIn(t, tl.reveal, 0.45);
  const inCount = t >= tl.count && t < tl.reveal;
  const count = Math.max(1, Math.min(5, 5 - Math.floor(t - tl.count)));
  const tick = (t - tl.count) % 1;
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
              boxShadow: revealed ? `0 0 0 ${5 + 4 * r}px ${ring}` : `0 0 0 2px ${ring}`,
              filter: revealed && !real ? `saturate(${1 - 0.15 * r}) brightness(${1 - 0.12 * r})` : undefined }}>
              <Img src={file(`pairs/${String(p.n).padStart(2, "0")}-${side}.jpg`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </div>
            {revealed && <div style={{ position: "absolute", left: PX + PW - 170, top: y + 24 }}><Mark real={real} size={140} pop={fadeIn(t, tl.reveal, 0.4)} /></div>}
            {revealed && (
              <div style={{ position: "absolute", left: PX + 22, top: y + PH - 82, display: "flex", gap: 16, fontFamily: SANS }}>
                {picks.map((who, k) => (
                  <Chip key={who} who={who} style={{ background: "rgba(10,12,13,.78)", opacity: fadeIn(t, tl.reveal + 0.25 + 0.2 * k, 0.4) }} />
                ))}
              </div>
            )}
            {revealed && real && (
              <div style={{ position: "absolute", left: PX, top: y + PH + 10, width: PW, textAlign: "right", fontFamily: SANS, fontSize: 24,
                color: MUTED, opacity: r }}>{p.photo}</div>
            )}
          </div>
        );
      })}
      {inCount && (
        <div style={{ position: "absolute", left: 540 - 95, top: (AY + PH + BY) / 2 - 95, width: 190, height: 190, borderRadius: 95,
          display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(13,16,18,.92)",
          boxShadow: `0 0 0 6px rgba(233,196,106,${0.9 - 0.6 * tick})`, fontFamily: SANS, fontSize: 116, fontWeight: 800, color: GOLD,
          transform: `scale(${1 + 0.12 * (1 - Math.min(1, tick * 4))})` }}>{count}</div>
      )}
    </>
  );
};

const Clip: FC<{ tl: ShortTl; t: number; fps: number }> = ({ tl, t, fps }) => {
  const local = t - tl.clip;
  const v = tl.video;
  const holding = v.hold !== null && local >= v.hold;
  const push = holding ? interpolate(local - v.hold!, [0, tl.durationSeconds - tl.clip - v.hold!], [1, 1.08], { extrapolateRight: "clamp" }) : 1;
  const card = fadeIn(local, 0.6, 0.5);
  const band = { position: "absolute" as const, left: 0, top: 620, width: 1080, height: 608, overflow: "hidden" as const };
  const video = (blurred: boolean) => (
    <Sequence from={Math.round(tl.clip * fps)} layout="none">
      <OffthreadVideo src={file(v.src)} muted playbackRate={v.rate} startFrom={Math.round(v.from * fps)}
        style={{ width: "100%", height: "100%", objectFit: "cover", ...(blurred ? { filter: "blur(40px) brightness(.55)", transform: "scale(1.2)" } : {}) }} />
    </Sequence>
  );
  const still = (src: string, blurred: boolean) => (
    <Img src={file(src)} style={{ width: "100%", height: "100%", objectFit: "cover",
      ...(blurred ? { filter: "blur(40px) brightness(.55)", transform: "scale(1.2)" } : { transform: `scale(${push})` }) }} />
  );
  const shown = holding ? (v.still ?? v.last) : null;
  return (
    <AbsoluteFill style={{ background: "#000", opacity: fadeIn(local, 0, 0.5) }}>
      <AbsoluteFill>{shown ? still(shown, true) : video(true)}</AbsoluteFill>
      <div style={band}>{shown ? still(shown, false) : video(false)}</div>
      <Question />
      <div style={{ position: "absolute", left: 0, right: 0, top: 1290, textAlign: "center", fontFamily: SANS, color: INK, textShadow: SHADOW,
        opacity: card, transform: `translateY(${(1 - card) * 18}px)` }}>
        <div style={{ fontSize: 96, fontWeight: 800 }}>{tl.pair.name.en}</div>
        <div style={{ fontSize: 54, color: SOFT, marginTop: 6 }}>{tl.pair.name.zh}</div>
      </div>
      {tl.pair.clipCredit && (
        <div style={{ position: "absolute", left: 0, right: 0, top: 1240, textAlign: "center", fontFamily: SANS, fontSize: 24, color: SOFT, opacity: card }}>{tl.pair.clipCredit}</div>
      )}
    </AbsoluteFill>
  );
};

export const ButterflyShort: FC<ShortProps> = ({ tl }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  if (!tl) return <AbsoluteFill style={{ background: BG }} />;
  return (
    <AbsoluteFill style={{ background: BG, opacity: fadeIn(t, 0, 0.3) * fadeOut(t, tl.durationSeconds, 0.6) }}>
      {t < tl.clip + 0.5 && (
        <AbsoluteFill>
          <Question />
          <Pictures tl={tl} t={t} />
        </AbsoluteFill>
      )}
      {t >= tl.clip && <Clip tl={tl} t={t} fps={fps} />}
    </AbsoluteFill>
  );
};
