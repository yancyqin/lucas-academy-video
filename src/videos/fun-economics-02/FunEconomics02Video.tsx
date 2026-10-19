/**
 * 「都学了三年，放弃就白学了吗？」 · 教育经济学 2 / Education Economics 2 (FUN-ECONOMICS-02.md).
 *
 * Two films, one per language (owner, 2026-10-19), from one shot list: the picture carries no words in either
 * language, and each film is paced to its own voice. Mary's story is comic stills; the LEGO, the homework and the
 * research are realistic footage and photos; the idea itself is paper diagrams (a sunk weight on both pans of a
 * balance); Paul is oil paintings. Only the title card and the end card have words, in the film's language.
 * A picture event fires when the voice reaches its words (markers in timeline.<lang>.json, from Whisper's word times).
 * Same look as episode 1: warm and solid for what is there, a cool dashed ghost for what is gone.
 */
import { useEffect, useState, type CSSProperties, type FC, type ReactNode } from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  OffthreadVideo,
  Sequence,
  continueRender,
  delayRender,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  type CalculateMetadataFunction,
} from "remotion";
import { C, NUM, Paper, ZH, rise, shadow, useT } from "../fun-economics-01/FunEconomics01Video";

const DIR = "fun-economics-02";
const file = (p: string) => staticFile(`${DIR}/${p}`);
type Lang = "zh" | "en";

type Cue = {
  id: string;
  section: string;
  speaker: "narrator" | "mary";
  start: number;
  end: number;
  text: string;
  trim: number;
  speech: { start: number; end: number };
};
export type Fe02Timeline = {
  lang: Lang;
  fps: number;
  durationSeconds: number;
  endCardStart: number;
  draft: boolean;
  title: Record<Lang, string>;
  images: string[];
  art: string[];
  footage: string[];
  footageSeconds: Record<string, number>;
  cues: Cue[];
  markers: Record<string, number>;
};
export type Fe02Props = { tl?: Fe02Timeline | null; lang?: Lang };

export const calculateFe02Metadata: CalculateMetadataFunction<Fe02Props> = async ({ props, abortSignal }) => {
  const response = await fetch(file(`timeline.${props.lang ?? "zh"}.json`), { signal: abortSignal });
  if (!response.ok) throw Error("Run scripts/fun-economics-02/build_timeline.py [--lang en] first");
  const tl = (await response.json()) as Fe02Timeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

const FONTS: [string, string, string][] = [
  ["MaShanZheng", "fonts/mashanzheng-MaShanZheng-Regular.ttf", "400"],
  ["Andika", "fonts/andika-Andika-Regular.ttf", "400"],
  ["Andika", "fonts/andika-Andika-Bold.ttf", "700"],
];
const useFonts = () => {
  const [handle] = useState(() => delayRender("fonts"));
  useEffect(() => {
    Promise.all(FONTS.map(([family, path, weight]) => new FontFace(family, `url(${file(path)})`, { weight }).load()))
      .then((faces) => { faces.forEach((f) => document.fonts.add(f)); continueRender(handle); })
      .catch((e) => { console.error(e); continueRender(handle); });
  }, [handle]);
};

// ---- time: seconds local to the enclosing Sequence ----
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = Easing.bezier(0.3, 0.7, 0.2, 1);
// A line's speech; at(f) is that share of the way through it.
type Speech = { dur: number; end: number; at: (f: number) => number };
const speechOf = (cue: Cue): Speech => {
  const s0 = cue.speech.start - cue.start, s1 = cue.speech.end - cue.start;
  return { dur: cue.end - cue.start, end: s1, at: (f) => s0 + f * (s1 - s0) };
};
// A marked word, in film seconds.
const mark = (tl: Fe02Timeline, key: string) => {
  const m = tl.markers[key];
  if (m === undefined) throw Error(`no marker ${key}`);
  return m;
};

// ---- pictures ----
type Push = { from?: number; to?: number; ox?: number; oy?: number; fit?: "cover" | "contain" };
const Still: FC<{ src: string; dur: number; push?: Push; children?: ReactNode }> = ({ src, dur, push = {}, children }) => {
  const t = useT();
  const s = interpolate(t, [0, Math.max(dur, 0.1)], [push.from ?? 1, push.to ?? 1.06], clamp);
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: C.paper }}>
      <AbsoluteFill style={{ transform: `scale(${s})`, transformOrigin: `${push.ox ?? 50}% ${push.oy ?? 50}%` }}>
        <Img src={file(src)} style={{ width: "100%", height: "100%", objectFit: push.fit ?? "cover" }} />
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// An oil painting on a dark ground of its own colours, pushed in slowly.
const Painting: FC<{ src: string; dur: number; push?: Push }> = ({ src, dur, push = {} }) => {
  const t = useT();
  const s = interpolate(t, [0, Math.max(dur, 0.1)], [push.from ?? 1, push.to ?? 1.08], { ...clamp, easing: Easing.inOut(Easing.sin) });
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#17120e" }}>
      <Img src={file(`art/${src}`)} style={{ position: "absolute", left: -80, top: -80, width: 2080, height: 1240, objectFit: "cover", filter: "blur(46px) brightness(.38) saturate(.8)" }} />
      <AbsoluteFill style={{ transform: `scale(${s})`, transformOrigin: `${push.ox ?? 50}% ${push.oy ?? 40}%` }}>
        <Img src={file(`art/${src}`)} style={{ width: "100%", height: "100%", objectFit: push.fit ?? "contain", filter: "drop-shadow(0 24px 50px rgba(0,0,0,.65))" }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Placeholder: FC<{ label: string }> = ({ label }) => (
  <AbsoluteFill>
    <Paper />
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ fontFamily: NUM, fontSize: 80, color: C.ghost, border: `8px dashed ${C.ghost}`, borderRadius: 40, padding: "40px 80px" }}>{label}</div>
    </AbsoluteFill>
  </AbsoluteFill>
);

// Stock footage, muted. A clip too short for its shot slows down to fit (one take on a gentle curve, never a freeze).
const Clip: FC<{ tl: Fe02Timeline; name: string; dur: number; from?: number; rate?: number; push?: Push }> = ({ tl, name, dur, from = 0, rate = 1, push }) => {
  const { fps } = useVideoConfig();
  const t = useT();
  if (!tl.footage.includes(name)) return <Placeholder label={name} />;
  const r = Math.min(rate, (tl.footageSeconds[name] - from - 0.15) / Math.max(dur, 0.1));
  const s = push ? interpolate(t, [0, dur], [push.from ?? 1, push.to ?? 1.05], clamp) : 1;
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <OffthreadVideo src={file(`footage/${name}`)} startFrom={Math.round(from * fps)} playbackRate={r} muted
        style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${s})`, transformOrigin: `${push?.ox ?? 50}% ${push?.oy ?? 50}%` }} />
    </AbsoluteFill>
  );
};

// ---- the sunk weight: three years of fees (coins) and time (an hourglass) ----
const Weight: FC<{ x: number; y: number; scale?: number; ghost?: number; sand?: number }> = ({ x, y, scale = 1, ghost = 0, sand = 1 }) => {
  const solid = ghost < 0.5;
  const fill = (c: string) => (solid ? c : "rgba(255,255,255,.35)");
  const stroke = solid ? C.goldDeep : C.ghost;
  const dash = solid ? undefined : "18 12";
  const coins = Array.from({ length: 6 }, (_, i) => 200 - i * 26);
  return (
    <svg width={400} height={260} viewBox="0 0 400 260"
      style={{ position: "absolute", left: x - 200 * scale, top: y - 260 * scale, width: 400 * scale, height: 260 * scale, overflow: "visible", opacity: 1 - 0.35 * ghost }}>
      {coins.map((cy, i) => (
        <g key={i}>
          <rect x={30} y={cy} width={150} height={26} fill={fill(C.goldDeep)} stroke={stroke} strokeWidth={5} strokeDasharray={dash} />
          <ellipse cx={105} cy={cy} rx={75} ry={22} fill={fill(C.gold)} stroke={stroke} strokeWidth={6} strokeDasharray={dash} />
        </g>
      ))}
      <g stroke={solid ? C.ink : C.ghost} strokeWidth={8} strokeDasharray={dash} strokeLinejoin="round">
        <rect x={232} y={18} width={140} height={20} rx={8} fill={fill(C.card)} />
        <rect x={232} y={208} width={140} height={20} rx={8} fill={fill(C.card)} />
        <path d="M246 38 C246 98, 296 108, 296 123 C296 138, 246 148, 246 208 L358 208 C358 148, 308 138, 308 123 C308 108, 358 98, 358 38 Z" fill={fill("#FFFDF5")} />
      </g>
      <path d={`M${258 + 34 * (1 - sand)} 54 L${346 - 34 * (1 - sand)} 54 L302 ${54 + 60 * sand} Z`} fill={solid ? C.gold : "transparent"} opacity={sand > 0.02 ? 1 : 0} />
      <path d={`M262 200 L342 200 C330 ${200 - 52 * (1.1 - sand)}, 274 ${200 - 52 * (1.1 - sand)}, 262 200 Z`} fill={solid ? C.gold : "transparent"} stroke={solid ? "none" : C.ghost} strokeWidth={4} strokeDasharray={dash} />
    </svg>
  );
};

const Water: FC<{ top: number; front?: boolean }> = ({ top, front }) => {
  const t = useT();
  const wave = (k: number) => Array.from({ length: 25 }, (_, i) => `${i === 0 ? "M" : "L"}${i * 80} ${top + Math.sin(i * 0.9 + t * 1.6 + k) * 9}`).join(" ");
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <linearGradient id={front ? "fe02-water-front" : "fe02-water"} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={C.water} stopOpacity={front ? 0.5 : 1} />
          <stop offset="1" stopColor="#2F6E93" stopOpacity={front ? 0.72 : 1} />
        </linearGradient>
      </defs>
      <path d={`${wave(0)} L1920 1080 L0 1080 Z`} fill={`url(#${front ? "fe02-water-front" : "fe02-water"})`} />
      <path d={wave(1.3)} fill="none" stroke="#FFFFFF" strokeOpacity={0.55} strokeWidth={6} />
    </svg>
  );
};

// sc03-01: the weight, and the question.
const WeightQuestion: FC<{ s: Speech }> = ({ s }) => {
  const t = useT();
  const k = rise(t, s.at(0.1), 0.6);
  const q = rise(t, s.at(0.75), 0.5);
  const wobble = Math.sin(t * 3) * 2 * k;
  return (
    <AbsoluteFill>
      <Paper />
      <div style={{ position: "absolute", inset: 0, opacity: k, transform: `translateY(${(1 - k) * 40}px) rotate(${wobble}deg)`, transformOrigin: "960px 760px" }}>
        <Weight x={900} y={760} scale={1.7} />
      </div>
      <div style={{ position: "absolute", left: 1330, top: 260, fontFamily: NUM, fontWeight: 700, fontSize: 400, color: C.orangeText, opacity: q, transform: `scale(${0.6 + 0.4 * q})` }}>?</div>
    </AbsoluteFill>
  );
};

// sc03-02: a ship carrying the weight sinks: gone, whatever we choose next.
const Ship: FC<{ tl: Fe02Timeline; seqStart: number }> = ({ tl, seqStart }) => {
  const t = useT();
  const at = mark(tl, "sc03-02:ship") - seqStart;
  const k = interpolate(t, [at, at + 3.2], [0, 1], { ...clamp, easing: Easing.in(Easing.quad) });
  const bob = Math.sin(t * 1.4) * 8 * (1 - k);
  const y = 560 + bob + k * 400, rot = -2 + k * -7;
  const bubbles = [0, 1, 2, 3, 4, 5];
  return (
    <AbsoluteFill>
      <Paper />
      <Water top={600} />
      <div style={{ position: "absolute", left: 960 - 330, top: y - 260, width: 660, height: 360, transform: `rotate(${rot}deg)`, transformOrigin: "50% 80%" }}>
        <Weight x={330} y={225} scale={1.1} />
        <svg width={660} height={360} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
          <path d="M10 220 L650 220 L560 330 L100 330 Z" fill="#B5643C" stroke={C.ink} strokeWidth={9} strokeLinejoin="round" />
          <path d="M60 262 L600 262" stroke={C.ink} strokeWidth={5} opacity={0.5} />
        </svg>
      </div>
      <Water top={600} front />
      {bubbles.map((i) => {
        const b0 = at + 0.8 + i * 0.35;
        const p = interpolate(t, [b0, b0 + 1.6], [0, 1], clamp);
        return p > 0 && p < 1 ? (
          <div key={i} style={{ position: "absolute", left: 880 + (i % 3) * 70 + Math.sin(i * 2 + t * 3) * 14, top: 960 - p * 330, width: 26 + (i % 2) * 14, height: 26 + (i % 2) * 14, borderRadius: 30, border: "5px solid rgba(255,255,255,.85)", opacity: 1 - p * 0.6 }} />
        ) : null;
      })}
    </AbsoluteFill>
  );
};

// sc03-03/04: the same weight on both paths (keep going: grit.png; stop: pause.png). The beam stays level.
const Balance: FC<{ tl: Fe02Timeline; s: Speech; seqStart: number; ghosted?: boolean }> = ({ tl, s, seqStart, ghosted }) => {
  const t = useT();
  const k = rise(t, 0, 0.6);
  const drop = (key: string) => (ghosted ? 1 : interpolate(t, [mark(tl, key) - seqStart, mark(tl, key) - seqStart + 0.7], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.4)) }));
  const left = drop("sc03-03:keep"), right = drop("sc03-03:stop");
  // a damped nudge as each weight lands, then still: equal weights cancel
  const wob = (key: string) => { const t0 = mark(tl, key) - seqStart + 0.5; return t > t0 ? 2.6 * Math.sin((t - t0) * 6) * Math.exp(-(t - t0) * 2.2) : 0; };
  const nudge = ghosted ? 0 : wob("sc03-03:stop") - wob("sc03-03:keep");
  const ghost = ghosted ? rise(t, s.at(0.15), 1.2) : 0;
  const pan = (x: number, a: number, src: string) => (
    <div style={{ position: "absolute", left: x - 300, top: 0, width: 600, height: 1080 }}>
      <Img src={file(`images/${src}`)} style={{ position: "absolute", left: 60, top: 70, width: 480, height: 270, objectFit: "cover", borderRadius: 28, border: `8px solid ${C.ink}`, boxShadow: shadow }} />
      <svg width={600} height={1080} style={{ position: "absolute", inset: 0 }}>
        <path d="M300 470 L80 640 M300 470 L520 640" stroke={C.ink} strokeWidth={6} />
        <path d="M40 640 L560 640 C540 760, 60 760, 40 640 Z" fill={C.card} stroke={C.ink} strokeWidth={8} />
      </svg>
      <div style={{ position: "absolute", left: 0, top: 0, opacity: a, transform: `translateY(${(1 - a) * -260}px)` }}>
        <Weight x={300} y={652} scale={0.95} ghost={ghost} />
      </div>
    </div>
  );
  return (
    <AbsoluteFill style={{ opacity: k }}>
      <Paper />
      <svg width={1920} height={1080} style={{ position: "absolute" }}>
        <path d="M960 470 L860 1000 L1060 1000 Z" fill={C.card} stroke={C.ink} strokeWidth={8} strokeLinejoin="round" />
      </svg>
      <AbsoluteFill style={{ transform: `rotate(${nudge}deg)`, transformOrigin: "960px 470px" }}>
        <svg width={1920} height={1080} style={{ position: "absolute" }}>
          <rect x={420} y={458} width={1080} height={24} rx={12} fill={C.ink} />
        </svg>
        {pan(480, left, "grit.png")}
        {pan(1440, right, "pause.png")}
      </AbsoluteFill>
      <svg width={1920} height={1080} style={{ position: "absolute" }}>
        <circle cx={960} cy={470} r={28} fill={C.hl} stroke={C.ink} strokeWidth={6} />
      </svg>
    </AbsoluteFill>
  );
};

// sc02-01 / sc02-05: three reasons ahead (the next three pictures), the paid fee left behind as a ghost.
const REASONS = ["grit.png", "music-loves.png", "pause.png"];
const Ahead: FC<{ s: Speech; filled?: boolean }> = ({ s, filled }) => {
  const t = useT();
  const arrow = rise(t, s.at(0.05), 0.9);
  const behind = filled ? rise(t, s.at(0.55), 0.8) : 0;
  return (
    <AbsoluteFill>
      <Paper />
      <svg width={1920} height={1080} style={{ position: "absolute" }}>
        <path d={`M150 760 L${150 + 1600 * arrow} 760`} stroke={C.green} strokeWidth={18} strokeLinecap="round" />
        {arrow > 0.97 && <path d="M1700 712 L1764 760 L1700 808" fill="none" stroke={C.green} strokeWidth={18} strokeLinecap="round" strokeLinejoin="round" />}
      </svg>
      {REASONS.map((src, i) => {
        const a = filled ? rise(t, s.at(0.05 + 0.08 * i), 0.5) : rise(t, s.at(0.3 + 0.12 * i), 0.5);
        const x = 130 + i * 570, y = 250;
        return (
          <div key={src} style={{ position: "absolute", left: x, top: y, width: 520, height: 320, opacity: a, transform: `translateY(${(1 - a) * 30}px)` }}>
            {filled
              ? <Img src={file(`images/${src}`)} style={{ width: 520, height: 320, objectFit: "cover", borderRadius: 30, border: `8px solid ${C.ink}`, boxShadow: shadow, boxSizing: "border-box" }} />
              : <div style={{ width: 520, height: 320, borderRadius: 30, border: `8px dashed ${C.ghost}`, boxSizing: "border-box", background: "rgba(255,255,255,.5)" }} />}
          </div>
        );
      })}
      <div style={{ position: "absolute", left: 0, top: 0, opacity: behind }}>
        <Weight x={260} y={1010} scale={0.8} ghost={1} />
      </div>
    </AbsoluteFill>
  );
};

// sc06-04: "don't waste" looks after the sand still on top; what has run through is already sunk.
const Hourglass: FC<{ tl: Fe02Timeline; s: Speech; seqStart: number }> = ({ tl, s, seqStart }) => {
  const t = useT();
  const k = rise(t, s.at(0.02), 0.6);
  const top = rise(t, mark(tl, "sc06-04:not-yet") - seqStart, 0.8);
  const sunk = rise(t, mark(tl, "sc06-04:sunk") - seqStart, 1.0);
  const fall = Math.min(1, t * 0.03);
  return (
    <AbsoluteFill style={{ opacity: k }}>
      <Paper />
      <svg width={1920} height={1080} style={{ position: "absolute" }}>
        <defs>
          <clipPath id="fe02-glass-top"><path d="M760 170 C760 380, 930 440, 930 540 L990 540 C990 440, 1160 380, 1160 170 Z" /></clipPath>
          <clipPath id="fe02-glass-bottom"><path d="M930 540 C930 640, 760 700, 760 910 L1160 910 C1160 700, 990 640, 990 540 Z" /></clipPath>
        </defs>
        <g clipPath="url(#fe02-glass-top)">
          <rect x={700} y={250 + 60 * fall} width={520} height={400} fill={C.gold} />
        </g>
        {top > 0 && <ellipse cx={960} cy={330} rx={260} ry={230} fill={C.gold} opacity={0.22 * top} />}
        <path d={`M960 540 L960 ${540 + 250}`} stroke={C.gold} strokeWidth={8} strokeDasharray="10 14" strokeDashoffset={-t * 60} />
        <g clipPath="url(#fe02-glass-bottom)">
          <path d="M700 910 L700 800 C800 720, 1120 720, 1220 800 L1220 910 Z" fill={sunk > 0.5 ? "rgba(141,153,174,.25)" : C.gold} stroke={sunk > 0.5 ? C.ghost : "none"} strokeWidth={8} strokeDasharray="20 14" />
        </g>
        <g fill="none" stroke={C.ink} strokeWidth={10} strokeLinejoin="round">
          <path d="M760 170 C760 380, 930 440, 930 540 C930 640, 760 700, 760 910" />
          <path d="M1160 170 C1160 380, 990 440, 990 540 C990 640, 1160 700, 1160 910" />
        </g>
        <rect x={700} y={130} width={520} height={44} rx={16} fill={C.card} stroke={C.ink} strokeWidth={9} />
        <rect x={700} y={906} width={520} height={44} rx={16} fill={C.card} stroke={C.ink} strokeWidth={9} />
      </svg>
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, bottom: 0, opacity: sunk }}>
        <Water top={980} />
      </div>
    </AbsoluteFill>
  );
};

// sc07-04: the past sunk (left, under water), the future not here yet (right, a dashed road into mist), now (centre).
const Now: FC<{ tl: Fe02Timeline; s: Speech; seqStart: number }> = ({ tl, s, seqStart }) => {
  const t = useT();
  const past = rise(t, s.at(0.02), 0.8);
  const sinkK = interpolate(t, [s.at(0.04), s.at(0.04) + 2.5], [0, 1], { ...clamp, easing: Easing.inOut(Easing.quad) });
  const future = rise(t, mark(tl, "sc07-04:future") - seqStart, 1.0);
  const now = rise(t, mark(tl, "sc07-04:now") - seqStart, 0.8);
  const glow = rise(t, mark(tl, "sc07-04:cherish") - seqStart, 1.2);
  return (
    <AbsoluteFill>
      <Paper />
      <div style={{ position: "absolute", inset: 0, opacity: past }}>
        <Weight x={330} y={640 + sinkK * 260} scale={0.9} ghost={sinkK} />
      </div>
      <div style={{ position: "absolute", left: 0, top: 0, width: 760, height: 1080, overflow: "hidden", opacity: past, WebkitMaskImage: "linear-gradient(90deg, #000 62%, transparent 100%)" }}>
        <Water top={760} front />
      </div>
      <svg width={1920} height={1080} style={{ position: "absolute", opacity: future }}>
        <defs>
          <linearGradient id="fe02-mist" x1="0" x2="1">
            <stop offset="0" stopColor={C.ghost} stopOpacity={1} />
            <stop offset="1" stopColor={C.ghost} stopOpacity={0} />
          </linearGradient>
        </defs>
        <path d="M1240 860 C1420 760, 1520 600, 1820 520" fill="none" stroke="url(#fe02-mist)" strokeWidth={22} strokeDasharray="34 26" strokeLinecap="round" />
        <path d="M1240 940 C1460 860, 1600 700, 1880 640" fill="none" stroke="url(#fe02-mist)" strokeWidth={22} strokeDasharray="34 26" strokeLinecap="round" />
      </svg>
      <div style={{
        position: "absolute", left: 960 - 260, top: 540 - 300, width: 520, height: 520, borderRadius: 260, overflow: "hidden",
        border: `12px solid ${C.goldDeep}`, opacity: now, transform: `scale(${0.85 + 0.15 * now})`,
        boxShadow: `0 0 ${30 + 90 * glow}px ${10 + 40 * glow}px rgba(246,195,67,${0.35 + 0.4 * glow})`,
      }}>
        <Img src={file("images/skills-stay.png")} style={{ position: "absolute", left: -208, top: -91, width: 1300, height: 731, objectFit: "cover" }} />
      </div>
    </AbsoluteFill>
  );
};

// ---- the homework notebook (notebook-page.png: left page x 200–900, right page 910–1590, y 90–990) ----
const GRAPHITE = "#3A3E45";
const Pencil: FC<{ x: number; y: number; at: number; children: ReactNode; size?: number; rot?: number; color?: string; d?: number }> = ({ x, y, at, children, size = 92, rot = -1.5, color = GRAPHITE, d }) => {
  const t = useT();
  const len = typeof children === "string" ? children.length : 6;
  const k = interpolate(t, [at, at + (d ?? Math.min(1.6, 0.18 * len + 0.3))], [0, 1], clamp);
  if (k <= 0) return null;
  return (
    <div style={{
      position: "absolute", left: x, top: y, fontFamily: NUM, fontWeight: 400, fontSize: size, color, whiteSpace: "nowrap",
      transform: `rotate(${rot}deg)`, clipPath: `inset(-20% ${100 - 100 * k}% -20% -5%)`, opacity: 0.9, letterSpacing: 2,
    }}>{children}</div>
  );
};
const Ring: FC<{ x: number; y: number; w: number; h: number; at: number; color: string }> = ({ x, y, w, h, at, color }) => {
  const t = useT();
  const k = interpolate(t, [at, at + 0.7], [0, 1], { ...clamp, easing: ease });
  const L = Math.PI * (w + h) * 0.55;
  return (
    <svg width={w + 40} height={h + 40} style={{ position: "absolute", left: x - 20, top: y - 20, overflow: "visible" }}>
      <ellipse cx={(w + 40) / 2} cy={(h + 40) / 2} rx={w / 2} ry={h / 2} fill="none" stroke={color} strokeWidth={9} strokeLinecap="round"
        strokeDasharray={L} strokeDashoffset={L * (1 - k)} transform={`rotate(-8 ${(w + 40) / 2} ${(h + 40) / 2})`} />
    </svg>
  );
};
const Box: FC<{ x: number; y: number; at: number }> = ({ x, y, at }) => {
  const t = useT();
  const k = rise(t, at, 0.5);
  return (
    <svg width={220} height={200} style={{ position: "absolute", left: x, top: y, opacity: k, overflow: "visible" }}>
      {Array.from({ length: 8 }, (_, i) => (
        <g key={i} transform={`translate(${26 + i * 22} 0)`}>
          <rect x={0} y={20 + (i % 3) * 8} width={15} height={90} fill="#F3C64A" stroke={GRAPHITE} strokeWidth={3} />
          <path d={`M0 ${20 + (i % 3) * 8} L7.5 ${(i % 3) * 8} L15 ${20 + (i % 3) * 8} Z`} fill="#F1D9B5" stroke={GRAPHITE} strokeWidth={3} />
        </g>
      ))}
      <rect x={10} y={84} width={200} height={100} rx={8} fill="#E9EEF7" stroke={GRAPHITE} strokeWidth={5} />
    </svg>
  );
};
const Kid: FC<{ x: number; y: number; k: number }> = ({ x, y, k }) => (
  <svg width={60} height={92} style={{ position: "absolute", left: x, top: y, opacity: k, transform: `translateY(${(1 - k) * 12}px)` }}>
    <circle cx={30} cy={20} r={16} fill="none" stroke={GRAPHITE} strokeWidth={5} />
    <path d="M8 88 C8 52, 52 52, 52 88" fill="none" stroke={GRAPHITE} strokeWidth={5} strokeLinecap="round" />
  </svg>
);
// The left page: one box of 8 pencils, × 7, shared by 14 children: how many each?
const Problem: FC<{ tl: Fe02Timeline; seqStart: number; still?: boolean }> = ({ tl, seqStart, still }) => {
  const t = useT();
  const at = (key: string) => (still ? -10 : mark(tl, key) - seqStart);
  return (
    <>
      <div style={{ position: "absolute", left: 250, top: 100, transform: "scale(1.45)", transformOrigin: "0 0" }}><Box x={0} y={0} at={at("sc05-01:problem")} /></div>
      <Pencil x={600} y={190} at={at("sc05-01:boxes")} size={130}>× 7</Pencil>
      {Array.from({ length: 14 }, (_, i) => (
        <Kid key={i} x={250 + (i % 7) * 86} y={460 + Math.floor(i / 7) * 120} k={rise(t, at("sc05-01:kids") + i * 0.06, 0.3)} />
      ))}
      <Pencil x={500} y={720} at={at("sc05-01:ask")} size={150} rot={-3}>?</Pencil>
    </>
  );
};
const Notebook: FC<{ tl: Fe02Timeline; seqStart: number; stage: "wrong" | "right" }> = ({ tl, seqStart, stage }) => {
  const t = useT();
  const at = (key: string, plus = 0) => mark(tl, key) - seqStart + plus;
  const mess = stage === "wrong" ? at("sc05-03:mess") : 0;
  return (
    <AbsoluteFill>
      <Still src="images/notebook-page.png" dur={1} push={{ from: 1, to: 1 }} />
      <Problem tl={tl} seqStart={seqStart} still={stage === "right"} />
      {stage === "wrong" ? <>
        <Pencil x={960} y={110} at={at("sc05-02:plus")} size={84}>7 + 8 = 15</Pencil>
        <Pencil x={960} y={240} at={at("sc05-02:fifteen")} size={76}>15 ÷ 14 = 1</Pencil>
        <Pencil x={1400} y={240} at={at("sc05-02:left")} size={76}>… 1</Pencil>
        <svg width={480} height={90} style={{ position: "absolute", left: 960, top: 395, overflow: "visible", opacity: rise(t, at("sc05-02:cut"), 0.4) }}>
          <path d="M0 45 L40 20 L440 20 L440 70 L40 70 Z" fill="#F3C64A" stroke={GRAPHITE} strokeWidth={5} strokeLinejoin="round" />
          <path d="M0 45 L40 20 L40 70 Z" fill="#F1D9B5" stroke={GRAPHITE} strokeWidth={5} />
          {Array.from({ length: 13 }, (_, i) => {
            const k = rise(t, at("sc05-02:cut", 0.5 + i * 0.07), 0.2);
            return <path key={i} d={`M${40 + (i + 1) * (400 / 14)} 8 L${40 + (i + 1) * (400 / 14)} 82`} stroke={C.red} strokeWidth={4} strokeDasharray="7 6" opacity={k} />;
          })}
        </svg>
        <Pencil x={1460} y={360} at={at("sc05-02:cut", 1.4)} size={100} rot={6}>?</Pencil>
        <Pencil x={965} y={545} at={mess} size={60} rot={-2.5}>1 ÷ 14 = 0.0714…</Pencil>
        <Pencil x={985} y={640} at={mess + 1.1} size={58} rot={1.5}>0.0714 × 7 = 0.4998</Pencil>
        <Pencil x={955} y={735} at={mess + 2.2} size={58} rot={-4}>15.07 ÷ 8 = 1.88…</Pencil>
        <Pencil x={990} y={835} at={mess + 3.3} size={56} rot={3}>1.88 × 14 = 26.32 ?</Pencil>
      </> : <>
        <Pencil x={980} y={130} at={at("sc05-04:times")}>7 × 8 = 56</Pencil>
        <Pencil x={980} y={300} at={at("sc05-04:share")}>56 ÷ 14 = 4</Pencil>
        <Ring x={1398} y={310} w={110} h={130} at={at("sc05-04:four")} color={C.green} />
      </>}
    </AbsoluteFill>
  );
};

// ---- title and end cards: the only words, in the film's language. The series is 教育经济学 / Education Economics. ----
const ZhTitle: FC<{ size: number }> = ({ size }) => (
  <div style={{ fontFamily: ZH, fontSize: size, lineHeight: 1.22, color: C.ink, textAlign: "center" }}>
    都学了<span style={{ color: C.orangeText }}>三年</span>，<br />放弃就<span style={{ color: C.green }}>白学</span>了吗？
  </div>
);
const EnTitle: FC<{ size: number; style?: CSSProperties }> = ({ size, style }) => (
  <div style={{ fontFamily: NUM, fontWeight: 700, fontSize: size, lineHeight: 1.15, color: C.ink, textAlign: "center", ...style }}>
    Is Quitting After<br /><span style={{ color: C.orangeText }}>Three Years</span> a <span style={{ color: C.green }}>Waste</span>?
  </div>
);
const Line: FC<{ zh?: boolean; size?: number; color?: string; children: ReactNode }> = ({ zh, size = 64, color = C.ink, children }) => (
  <div style={{ fontFamily: zh ? ZH : NUM, fontWeight: zh ? 400 : 700, fontSize: size, color, textAlign: "center", whiteSpace: "nowrap" }}>{children}</div>
);
const AI = ({ size }: { size: number }) => <span style={{ fontFamily: NUM, fontWeight: 700, fontSize: size * 0.9 }}>AI</span>;
const Two = ({ size }: { size: number }) => <span style={{ fontFamily: NUM, fontWeight: 700, fontSize: size * 0.9 }}>2</span>;
const TitleCard: FC<{ lang: Lang; at: number; out: number }> = ({ lang, at, out }) => {
  const t = useT();
  const k = rise(t, at, 0.6) * (1 - rise(t, out, 0.3));
  return (
    <AbsoluteFill style={{ opacity: k }}>
      <Paper />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 30, transform: `translateY(${(1 - k) * 30}px)` }}>
        {lang === "zh" ? <>
          <ZhTitle size={160} />
          <Line zh size={84}>教育经济学 <Two size={84} /></Line>
          <Line size={64}><span style={{ fontFamily: ZH, fontWeight: 400, fontSize: 70 }}>作者</span> Yancy Qin | Lucas Academy</Line>
          <Line zh size={64} color={C.ghost}>部分画面由 <AI size={64} /> 生成</Line>
        </> : <>
          <EnTitle size={124} />
          <Line size={80}>Education Economics 2</Line>
          <Line size={64}>By Yancy Qin | Lucas Academy</Line>
          <Line size={64} color={C.ghost}>Some pictures are AI-generated</Line>
        </>}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
const EndCard: FC<{ lang: Lang }> = ({ lang }) => {
  const t = useT();
  const k = rise(t, 0.2, 0.8);
  return (
    <AbsoluteFill style={{ opacity: k }}>
      <Paper />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 36 }}>
        <Line size={150}>Lucas Academy</Line>
        {lang === "zh" ? <>
          <Line zh size={84}>教育经济学 <Two size={84} /> · 都学了三年，放弃就白学了吗？</Line>
          <Line size={64}><span style={{ fontFamily: ZH, fontWeight: 400, fontSize: 70 }}>作者</span> Yancy Qin</Line>
          <Line zh size={64} color={C.ghost}>部分画面由 <AI size={64} /> 生成 · 配音为 <AI size={64} /> 合成</Line>
        </> : <>
          <Line size={80}>Education Economics 2</Line>
          <Line size={72}>Is Quitting After Three Years a Waste?</Line>
          <Line size={64}>By Yancy Qin</Line>
          <Line size={64} color={C.ghost}>Some pictures AI-generated · Narration AI-voiced</Line>
        </>}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---- the shot list: backgrounds start at a cue (or a marked word in it) and run until the next one ----
type Render = (tl: Fe02Timeline, dur: number, seqStart: number) => ReactNode;
type Bg = { from: string; mark?: string; render: Render };
const img = (src: string, push?: Push, children?: ReactNode): Render => (_tl, dur) => <Still src={`images/${src}`} dur={dur} push={push}>{children}</Still>;
const clip = (name: string, from = 0, rate = 1, push?: Push): Render => (tl, dur) => <Clip tl={tl} name={name} dur={dur} from={from} rate={rate} push={push} />;
const paint = (src: string, push?: Push): Render => (_tl, dur) => <Painting src={src} dur={dur} push={push} />;
const cueOf = (tl: Fe02Timeline, id: string) => tl.cues.find((c) => c.id === id)!;
const diagram = (node: (tl: Fe02Timeline, cue: Cue, s: Speech, seqStart: number) => ReactNode, id: string): Render =>
  (tl, _dur, seqStart) => { const cue = cueOf(tl, id); const s = speechOf(cue); return node(tl, cue, { ...s, at: (f) => s.at(f) + cue.start - seqStart }, seqStart); };

// The wrong brick in lego-wrong-brick.png (frame pixels at scale 1).
const WRONG_BRICK = { x: 590, y: 548, w: 110, h: 84 };
const WrongBrickRing: FC<{ at: number }> = ({ at }) => <Ring x={WRONG_BRICK.x} y={WRONG_BRICK.y} w={WRONG_BRICK.w} h={WRONG_BRICK.h} at={at} color={C.orange} />;

const BGS: Bg[] = [
  { from: "sc00-01", render: img("first-piece.png", { from: 1.0, to: 1.08, ox: 30, oy: 45 }) },
  { from: "sc00-02", render: img("practice-chore.png", { from: 1.0, to: 1.08, ox: 45, oy: 40 }) },
  { from: "sc00-03", render: img("dont-want.png", { from: 1.0, to: 1.06, ox: 45, oy: 45 }) },
  { from: "sc00-04", render: img("parents-think.png", { from: 1.0, to: 1.06, ox: 40, oy: 45 }) },
  { from: "sc01-01", render: img("three-years.png", { from: 1.0, to: 1.08, ox: 70, oy: 50 }) },
  { from: "sc01-02", render: img("stick-with-it.png", { from: 1.0, to: 1.06, ox: 40, oy: 45 }) },
  { from: "sc02-01", render: diagram((_tl, _c, s) => <Ahead s={s} />, "sc02-01") },
  { from: "sc02-02", render: img("grit.png", { from: 1.0, to: 1.08, ox: 30, oy: 45 }) },
  { from: "sc02-03", render: img("music-loves.png", { from: 1.0, to: 1.06, ox: 45, oy: 50 }) },
  { from: "sc02-04", render: img("pause.png", { from: 1.0, to: 1.06, ox: 50, oy: 45 }) },
  { from: "sc02-05", render: diagram((_tl, _c, s) => <Ahead s={s} filled />, "sc02-05") },
  { from: "sc03-01", render: diagram((_tl, _c, s) => <WeightQuestion s={s} />, "sc03-01") },
  { from: "sc03-02", render: (tl, _d, seqStart) => <Ship tl={tl} seqStart={seqStart} /> },
  { from: "sc03-03", render: diagram((tl, _c, s, seqStart) => <Balance tl={tl} s={s} seqStart={seqStart} />, "sc03-03") },
  { from: "sc03-04", render: diagram((tl, _c, s, seqStart) => <Balance tl={tl} s={s} seqStart={seqStart} ghosted />, "sc03-04") },
  { from: "sc04-01", render: clip("sc04-7230999.mp4", 0) },
  { from: "sc04-01", mark: "sc04-01:wrong", render: (tl, dur, seqStart) => (
    <Still src="images/lego-wrong-brick.png" dur={dur} push={{ from: 1.0, to: 1.07, ox: 30, oy: 55 }}>
      <WrongBrickRing at={mark(tl, "sc04-01:wrong") - seqStart + 0.6} />
    </Still>) },
  { from: "sc04-02", render: clip("sc04-6666287.mp4", 0) },
  { from: "sc04-02", mark: "sc04-02:patch", render: img("lego-patched.png", { from: 1.0, to: 1.07, ox: 55, oy: 50 }) },
  { from: "sc04-03", render: clip("sc04-6663997.mp4", 2) },
  { from: "sc04-04", render: clip("sc04-7313178.mp4", 0) },
  { from: "sc04-04", mark: "sc04-04:second", render: img("lego-rebuilt.png", { from: 1.0, to: 1.06, ox: 30, oy: 55 }) },
  { from: "sc05-01", render: clip("sc05-6996523.mp4", 0) },
  { from: "sc05-01", mark: "sc05-01:problem", render: (tl, _d, seqStart) => <Notebook tl={tl} seqStart={seqStart} stage="wrong" /> },
  { from: "sc05-04", render: clip("sc05-853819.mp4", 6) },
  { from: "sc05-04", mark: "sc05-04:boxes", render: (tl, _d, seqStart) => <Notebook tl={tl} seqStart={seqStart} stage="right" /> },
  { from: "sc05-05", render: clip("sc05-7015925.mp4", 10) },
  { from: "sc05-05", mark: "sc05-05:look", render: clip("sc05-3981943.mp4", 0) },
  { from: "sc05-06", render: clip("sc05-5182684.mp4", 1) },
  { from: "sc06-01", render: clip("sc06-7117367.mp4", 0) },
  { from: "sc06-02", render: clip("sc06-7311978.mp4", 9) },
  { from: "sc06-02", mark: "sc06-02:apart", render: img("robot-apart.png", { from: 1.0, to: 1.07, ox: 45, oy: 45 }) },
  { from: "sc06-03", render: clip("sc06-8799077.mp4", 0) },
  { from: "sc06-04", render: diagram((tl, _c, s, seqStart) => <Hourglass tl={tl} s={s} seqStart={seqStart} />, "sc06-04") },
  { from: "sc07-01", render: img("skills-stay.png", { from: 1.0, to: 1.08, ox: 30, oy: 45 }) },
  { from: "sc07-02", render: img("tired-day.png", { from: 1.0, to: 1.06, ox: 55, oy: 60 }) },
  { from: "sc07-03", render: img("road-ahead.png", { from: 1.0, to: 1.1, ox: 70, oy: 45 }) },
  { from: "sc07-04", render: diagram((tl, _c, s, seqStart) => <Now tl={tl} s={s} seqStart={seqStart} />, "sc07-04") },
  { from: "sc08-01", render: paint("paul-nga.jpg", { from: 1.0, to: 1.14, ox: 50, oy: 28 }) },
  { from: "sc08-02", render: paint("paul-valentin.jpg", { from: 1.0, to: 1.08, ox: 45, oy: 40, fit: "cover" }) },
  { from: "sc08-03", render: paint("paul-prison.jpg", { from: 1.0, to: 1.12, ox: 45, oy: 35 }) },
  { from: "sc08-04", render: paint("paul-selfportrait.jpg", { from: 1.0, to: 1.08, ox: 50, oy: 30 }) },
  { from: "sc09-01", render: clip("sc09-6296878.mp4", 0) },
  { from: "sc09-01", mark: "sc09-01:or", render: clip("sc09-7123932.mp4", 10) },
  { from: "sc09-01", mark: "sc09-01:road", render: clip("sc09-38413453.mp4", 0, 0.5) },
];

const CARDS: Record<string, (s: Speech, tl: Fe02Timeline) => ReactNode> = {
  "sc00-04": (s, tl) => <TitleCard lang={tl.lang} at={s.end + 0.4} out={s.dur - 0.3} />,
};

const FADE = 0.3;
export const FunEconomics02Video: FC<Fe02Props> = ({ tl }) => {
  useFonts();
  const { fps } = useVideoConfig();
  if (!tl) return null;
  const F = (s: number) => Math.round(s * fps);
  const starts = BGS.map((bg, i) => (i === 0 ? 0 : bg.mark ? mark(tl, bg.mark) - 0.15 : cueOf(tl, bg.from).start));
  return (
    <AbsoluteFill style={{ background: C.paper }}>
      {BGS.map((bg, i) => {
        const a = i === 0 ? 0 : starts[i] - FADE;
        const b = i + 1 < BGS.length ? starts[i + 1] : tl.endCardStart + 1;
        return (
          <Sequence key={`${bg.from}-${bg.mark ?? ""}`} from={F(a)} durationInFrames={Math.max(1, F(b) - F(a))}>
            <Fade d={i === 0 ? 0 : FADE}>{bg.render(tl, b - a, a)}</Fade>
          </Sequence>
        );
      })}
      {tl.cues.map((cue) => {
        const card = CARDS[cue.id];
        if (!card) return null;
        return (
          <Sequence key={cue.id} from={F(cue.start)} durationInFrames={Math.max(1, F(cue.end) - F(cue.start))}>
            {card(speechOf(cue), tl)}
          </Sequence>
        );
      })}
      <Sequence from={F(tl.endCardStart)}><EndCard lang={tl.lang} /></Sequence>
      <Audio src={file(`audio/${tl.lang}.mix.wav`)} />
      {tl.draft && <div style={{ position: "absolute", right: 30, bottom: 24, fontFamily: NUM, fontWeight: 700, fontSize: 64, color: C.red, opacity: 0.7 }}>DRAFT</div>}
    </AbsoluteFill>
  );
};

const Fade: FC<{ d: number; children: ReactNode }> = ({ d, children }) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  return <AbsoluteFill style={{ opacity: d ? interpolate(t, [0, d], [0, 1], { extrapolateRight: "clamp" }) : 1 }}>{children}</AbsoluteFill>;
};

// YouTube cover (README "YouTube covers"): one question, one realistic picture, for parents and educators first.
// Both languages on each cover; the film's own language leads.
const CoverFrame: FC<{ lead: Lang }> = ({ lead }) => {
  useFonts();
  const zh = <div style={{ fontFamily: ZH, fontSize: lead === "zh" ? 140 : 84, lineHeight: 1.16, color: C.ink, whiteSpace: "nowrap", textShadow: "0 4px 0 rgba(255,255,255,.9)" }}>
    都学了<span style={{ color: C.orangeText }}>三年</span>，<br />放弃就<span style={{ color: C.green }}>白学</span>了吗？</div>;
  const en = <div style={{ fontFamily: NUM, fontWeight: 700, fontSize: lead === "en" ? 120 : 70, lineHeight: 1.08, color: C.ink, whiteSpace: "nowrap", textShadow: "0 4px 0 rgba(255,255,255,.9)" }}>
    {lead === "en" ? <>Is Quitting<br />After <span style={{ color: C.orangeText }}>Three Years</span><br />a <span style={{ color: C.green }}>Waste</span>?</>
      : <>Is Quitting After <span style={{ color: C.orangeText }}>Three Years</span><br />a <span style={{ color: C.green }}>Waste</span>?</>}</div>;
  const zhSmall = <div style={{ fontFamily: ZH, fontSize: 84, lineHeight: 1.2, color: C.ink, whiteSpace: "nowrap", textShadow: "0 4px 0 rgba(255,255,255,.9)" }}>
    都学了<span style={{ color: C.orangeText }}>三年</span>，放弃就<span style={{ color: C.green }}>白学</span>了吗？</div>;
  return (
    <AbsoluteFill style={{ background: C.paper }}>
      <Img src={file("images/cover.png")} style={{ position: "absolute", left: -150, top: -42, width: 2070, height: 1164, objectFit: "cover" }} />
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(247,249,242,0) 30%, rgba(247,249,242,.8) 42%, rgba(247,249,242,.88) 100%)" }} />
      <div style={{ position: "absolute", left: 720, top: 272, width: 1170, display: "flex", flexDirection: "column", gap: 40 }}>
        {lead === "zh" ? <>{zh}{en}</> : <>{en}{zhSmall}</>}
      </div>
    </AbsoluteFill>
  );
};
export const FunEconomics02Cover: FC = () => <CoverFrame lead="zh" />;
export const FunEconomics02CoverEn: FC = () => <CoverFrame lead="en" />;
