/**
 * 「一根冰棍，要花多少钱？」 · Fun Economics 1 (FUN-ECONOMICS-01.md).
 *
 * Two layers over one narration mix. Backgrounds run in segments that can span several cues (a picture-book image
 * with a slow push, the hand footage, the arithmetic page recording, an old print), so a picture does not jump when a
 * new line starts. Cards sit on top, one set per cue, timed against that cue's speech. The film's one visual rule:
 * what you can see is warm and solid, what you can't see is a cool dashed ghost.
 * Text is never small: 64 px is the floor on a 1080p frame.
 */
import { createContext, useContext, useEffect, useState, type CSSProperties, type FC, type ReactNode } from "react";
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

const DIR = "fun-economics-01";
const file = (p: string) => staticFile(`${DIR}/${p}`);

// One film per language (owner's rule): the English film draws every card in English, with dollars instead of yuan.
export type Lang = "zh" | "en";
export const LangCtx = createContext<Lang>("zh");
const useLang = () => useContext(LangCtx);
export const tx = (lang: Lang, zh: ReactNode, en: ReactNode) => (lang === "en" ? en : zh);
const MONEY = {
  zh: { price: "¥5", chore: "¥2", total: "¥7", zero: "¥0" },
  en: { price: "$2", chore: "$1", total: "$3", zero: "$0" },
};

type Cue = {
  id: string;
  section: string;
  speaker: "narrator" | "mary";
  text: string;
  start: number;
  end: number;
  speech: { start: number; end: number };
};
export type EconTimeline = {
  lang: Lang;
  fps: number;
  durationSeconds: number;
  endCardStart: number;
  draft: boolean;
  images: string[];
  art: string[];
  footage: string[];
  footageSeconds: Record<string, number>;
  cues: Cue[];
  markers?: Record<string, number>;
};
export type EconProps = { tl?: EconTimeline | null; lang?: Lang };

export const calculateEconMetadata: CalculateMetadataFunction<EconProps> = async ({ props, abortSignal }) => {
  const response = await fetch(file(`timeline.${props.lang ?? "zh"}.json`), { signal: abortSignal });
  if (!response.ok) throw Error("Run scripts/fun-economics-01/build_timeline.py first");
  const tl = (await response.json()) as EconTimeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

// ---- look (the arithmetic page's palette) ----
export const C = {
  paper: "#F7F9F2", grid: "#DAE6D3", ink: "#20322C", card: "#FFFFFF",
  red: "#E04A3A", redText: "#C93A2B", orange: "#F39B23", orangeText: "#B86603",
  green: "#11865B", ghost: "#8D99AE", hl: "#FFEC9E", gold: "#F6C343", goldDeep: "#C9921A", water: "#7FB7D8",
};
export const ZH = '"MaShanZheng", "Kaiti SC", serif';
export const NUM = '"Andika", "Avenir Next", sans-serif';
const FONTS: [string, string, string][] = [
  ["MaShanZheng", "fonts/mashanzheng-MaShanZheng-Regular.ttf", "400"],
  ["Andika", "fonts/andika-Andika-Regular.ttf", "400"],
  ["Andika", "fonts/andika-Andika-Bold.ttf", "700"],
];

export const useFonts = () => {
  const [handle] = useState(() => delayRender("fonts"));
  useEffect(() => {
    Promise.all(FONTS.map(([family, path, weight]) => new FontFace(family, `url(${file(path)})`, { weight }).load()))
      .then((faces) => { faces.forEach((f) => document.fonts.add(f)); continueRender(handle); })
      .catch((e) => { console.error(e); continueRender(handle); });
  }, [handle]);
};

// ---- time helpers (seconds, local to the enclosing Sequence) ----
export const useT = () => useCurrentFrame() / useVideoConfig().fps;
const ease = Easing.bezier(0.3, 0.7, 0.2, 1);
export const rise = (t: number, at: number, d = 0.45) =>
  interpolate(t, [at, at + d], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
export type Speech = { s0: number; s1: number; at: (f: number) => number; dur: number };
const speechOf = (cue: Cue): Speech => {
  const s0 = cue.speech.start - cue.start, s1 = cue.speech.end - cue.start;
  return { s0, s1, at: (f) => s0 + f * (s1 - s0), dur: cue.end - cue.start };
};

// ---- backgrounds ----
export const Paper: FC = () => (
  <AbsoluteFill style={{ background: C.paper }}>
    <svg width="1920" height="1080" style={{ position: "absolute", inset: 0 }}>
      <defs>
        <pattern id="econ-grid" width="60" height="60" patternUnits="userSpaceOnUse">
          <path d="M60 0H0V60" fill="none" stroke={C.grid} strokeWidth="2" />
        </pattern>
      </defs>
      <rect width="1920" height="1080" fill="url(#econ-grid)" />
    </svg>
  </AbsoluteFill>
);

type Push = { from?: number; to?: number; ox?: number; oy?: number; fit?: "cover" | "contain" };
const Still: FC<{ src: string; dur: number; push?: Push; ghost?: number; style?: CSSProperties }> = ({ src, dur, push = {}, ghost = 0, style }) => {
  const t = useT();
  const s = interpolate(t, [0, Math.max(dur, 0.1)], [push.from ?? 1, push.to ?? 1.07], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ overflow: "hidden", ...style }}>
      {push.fit === "contain" && <Paper />}
      <Img src={file(src)} style={{
        width: "100%", height: "100%", objectFit: push.fit ?? "cover",
        transform: `scale(${s})`, transformOrigin: `${push.ox ?? 50}% ${push.oy ?? 50}%`,
        filter: ghost ? `grayscale(${ghost}) brightness(${1 + 0.12 * ghost}) contrast(${1 - 0.25 * ghost})` : undefined,
      }} />
    </AbsoluteFill>
  );
};

const Placeholder: FC<{ label: string }> = ({ label }) => (
  <AbsoluteFill>
    <Paper />
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ fontFamily: ZH, fontSize: 96, color: C.ghost, border: `8px dashed ${C.ghost}`, borderRadius: 40, padding: "40px 80px" }}>{label}</div>
    </AbsoluteFill>
  </AbsoluteFill>
);

const Clip: FC<{ tl: EconTimeline; name: string; startFrom?: number; label: string; style?: CSSProperties }> = ({ tl, name, startFrom = 0, label, style }) => {
  const { fps } = useVideoConfig();
  if (!tl.footage.includes(name)) return <Placeholder label={label} />;
  return (
    <AbsoluteFill style={{ background: C.paper, ...style }}>
      <OffthreadVideo src={file(`footage/${name}`)} startFrom={Math.max(0, Math.round(startFrom * fps))} muted
        style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    </AbsoluteFill>
  );
};

// A ghost image laid over another in the same composition (piano over football): cool, faded, still visible.
const GhostOver: FC<{ src: string; at: number; amount?: number }> = ({ src, at, amount = 0.55 }) => {
  const t = useT();
  const k = rise(t, at, 1.2);
  return (
    <AbsoluteFill style={{ opacity: k * amount }}>
      <Img src={file(src)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1) sepia(0.2) hue-rotate(180deg) saturate(1.6) brightness(1.15)" }} />
    </AbsoluteFill>
  );
};

// ---- cards ----
export const shadow = "0 18px 40px -16px rgba(32,50,44,.45)";
export const Big: FC<{ children: ReactNode; size?: number; color?: string; style?: CSSProperties }> = ({ children, size = 120, color = C.ink, style }) => {
  const en = useLang() === "en";
  return <div style={{ fontFamily: en ? NUM : ZH, fontWeight: en ? 700 : 400, fontSize: size, lineHeight: en ? 1.15 : 1.25, color, textAlign: "center", ...style }}>{children}</div>;
};
export const Num: FC<{ children: ReactNode; size?: number; color?: string; style?: CSSProperties }> = ({ children, size = 120, color = C.ink, style }) => (
  <span style={{ fontFamily: NUM, fontWeight: 700, fontSize: size, color, ...style }}>{children}</span>
);

export const Card: FC<{ at: number; children: ReactNode; style?: CSSProperties; out?: number }> = ({ at, children, style, out }) => {
  const t = useT();
  const k = rise(t, at) * (out === undefined ? 1 : 1 - rise(t, out, 0.3));
  return (
    <div style={{ position: "absolute", opacity: k, transform: `translateY(${(1 - k) * 30}px)`, ...style }}>{children}</div>
  );
};

export const BigText: FC<{ at: number; lines: ReactNode[]; size?: number; out?: number; onPaper?: boolean; y?: number }> = ({ at, lines, size = 130, out, onPaper, y }) => {
  const t = useT();
  const k = rise(t, at) * (out === undefined ? 1 : 1 - rise(t, out, 0.3));
  const place: CSSProperties = y === undefined ? { justifyContent: "center" } : { justifyContent: "flex-start", paddingTop: y };
  return (
    <AbsoluteFill style={{ alignItems: "center", opacity: k, ...place }}>
      {onPaper && <Paper />}
      <div style={{
        background: onPaper ? "transparent" : "rgba(255,255,255,.94)", borderRadius: 48, padding: "48px 90px",
        boxShadow: onPaper ? "none" : shadow, transform: `scale(${0.92 + 0.08 * k})`, position: "relative",
      }}>
        {lines.map((l, i) => <Big key={i} size={size}>{l}</Big>)}
      </div>
    </AbsoluteFill>
  );
};

const Bubble: FC<{ at: number; who: string; text: ReactNode; x: number; y: number; tail?: "left" | "right"; out?: number }> = ({ at, who, text, x, y, tail = "left", out }) => {
  const en = useLang() === "en";
  return (
  <Card at={at} out={out} style={{ left: x, top: y, whiteSpace: "nowrap" }}>
    <div style={{ position: "relative", background: C.card, borderRadius: 44, padding: "34px 52px 40px", boxShadow: shadow, border: `6px solid ${C.ink}` }}>
      <div style={{ fontFamily: /[一-龥]/.test(who) ? ZH : NUM, fontWeight: 700, fontSize: 64, color: C.orangeText, lineHeight: 1 }}>{who}</div>
      <div style={{ fontFamily: en ? NUM : ZH, fontWeight: en ? 700 : 400, fontSize: en ? 76 : 84, lineHeight: en ? 1.2 : 1.3, color: C.ink, marginTop: 14 }}>{text}</div>
      <div style={{
        position: "absolute", bottom: -40, [tail]: 90, width: 0, height: 0,
        borderLeft: "34px solid transparent", borderRight: "34px solid transparent", borderTop: `44px solid ${C.ink}`,
      }} />
    </div>
  </Card>
  );
};

type TagItem = { text: string; kind: "solid" | "ghost" | "answer" | "struck"; at: number; strikeAt?: number };
const PriceTag: FC<{ items: TagItem[]; x: number; y: number; scale?: number; at?: number }> = ({ items, x, y, scale = 1, at = 0 }) => {
  const t = useT();
  const k = rise(t, at);
  return (
    <div style={{ position: "absolute", left: x, top: y, transform: `scale(${scale * (0.9 + 0.1 * k)}) rotate(-3deg)`, transformOrigin: "left top", opacity: k }}>
      <svg width="120" height="140" style={{ position: "absolute", left: 40, top: -120 }}>
        <path d="M60 140 C 40 80, 90 50, 70 0" fill="none" stroke={C.ink} strokeWidth="6" strokeLinecap="round" />
      </svg>
      <div style={{ display: "flex", alignItems: "center", gap: 26, background: C.card, border: `8px solid ${C.ink}`, borderRadius: 40, padding: "34px 50px 34px 96px", boxShadow: shadow, position: "relative" }}>
        <div style={{ position: "absolute", left: 30, top: "50%", width: 34, height: 34, marginTop: -17, borderRadius: 17, border: `6px solid ${C.ink}`, background: C.paper }} />
        {items.map((it, i) => {
          const a = rise(t, it.at);
          if (a <= 0) return null;
          const ghost = it.kind === "ghost";
          return (
            <div key={i} style={{
              fontFamily: /[一-龥]/.test(it.text) ? ZH : NUM, fontWeight: 700, fontSize: 112, lineHeight: 1.1, whiteSpace: "nowrap",
              color: ghost ? C.ghost : it.kind === "answer" ? C.green : C.ink,
              border: ghost ? `7px dashed ${C.ghost}` : "7px solid transparent", borderRadius: 26, padding: "0 22px",
              opacity: a, transform: `scale(${0.7 + 0.3 * a})`,
              textDecoration: it.kind === "struck" || (it.strikeAt !== undefined && t >= it.strikeAt) ? `line-through 10px ${C.red}` : undefined,
            }}>{it.text}</div>
          );
        })}
      </div>
    </div>
  );
};

const TitleCard: FC<{ at: number }> = ({ at }) => {
  const t = useT();
  const lang = useLang();
  const k = rise(t, at, 0.6);
  return (
    <AbsoluteFill style={{ opacity: k }}>
      <Paper />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 30 }}>
        <Big size={lang === "en" ? 150 : 170} style={{ transform: `translateY(${(1 - k) * 30}px)` }}>
          {tx(lang, <>一根<span style={{ color: C.orangeText }}>冰棍</span>，<br />要花<span style={{ color: C.green }}>多少钱</span>？</>,
            <>How Much Does an<br /><span style={{ color: C.orangeText }}>Ice Pop</span> <span style={{ color: C.green }}>Cost</span>?</>)}
        </Big>
        <Big size={76} color={C.ink}>{tx(lang, "趣味经济学", "Fun Economics")} <Num size={76}>1</Num></Big>
        <div style={{ fontFamily: NUM, fontWeight: 700, fontSize: 64, color: C.ink }}>{tx(lang, "作者", "By")} Yancy Qin, Louise Yang | Lucas Academy</div>
        <Big size={64} color={C.ghost}>{tx(lang, "插图由 AI 生成", "Illustrations are AI-generated")}</Big>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const EndCard: FC = () => {
  const t = useT();
  const lang = useLang();
  const k = rise(t, 0.2, 0.8);
  return (
    <AbsoluteFill style={{ opacity: k }}>
      <Paper />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 36 }}>
        <div style={{ fontFamily: NUM, fontWeight: 700, fontSize: 150, color: C.ink }}>Lucas Academy</div>
        <Big size={lang === "en" ? 76 : 84}>{tx(lang, "趣味经济学", "Fun Economics")} <Num size={lang === "en" ? 76 : 84}>1</Num> · {tx(lang, "一根冰棍，要花多少钱？", "How Much Does an Ice Pop Cost?")}</Big>
        <div style={{ fontFamily: NUM, fontWeight: 700, fontSize: 64, color: C.ink }}>{tx(lang, "作者", "By")} Yancy Qin, Louise Yang</div>
        <Big size={64} color={C.ghost}>{tx(lang, "插图由 AI 生成 · 配音为 AI 合成", "Illustrations AI-generated · Narration AI-voiced")}</Big>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Clock: FC<{ at: number; x: number; y: number }> = ({ at, x, y }) => {
  const t = useT();
  const lang = useLang();
  const k = rise(t, at);
  const sweep = interpolate(t, [at, at + 2.4], [0, 180], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  const a = (sweep - 90) * (Math.PI / 180);
  const arc = (deg: number) => { const r = (deg - 90) * Math.PI / 180; return `${130 + 110 * Math.cos(r)} ${130 + 110 * Math.sin(r)}`; };
  return (
    <div style={{ position: "absolute", left: x, top: y, opacity: k, display: "flex", alignItems: "center", gap: 30 }}>
      <svg width="260" height="260">
        <circle cx="130" cy="130" r="120" fill={C.card} stroke={C.ink} strokeWidth="10" />
        {sweep > 1 && <path d={`M130 130 L${arc(0)} A110 110 0 ${sweep > 180 ? 1 : 0} 1 ${arc(sweep)} Z`} fill={C.hl} />}
        <line x1="130" y1="130" x2={130 + 92 * Math.cos(a)} y2={130 + 92 * Math.sin(a)} stroke={C.ink} strokeWidth="12" strokeLinecap="round" />
        <circle cx="130" cy="130" r="12" fill={C.ink} />
      </svg>
      <div style={{ background: C.card, borderRadius: 30, padding: "16px 34px", boxShadow: shadow }}>
        <Num size={110}>30</Num><Big size={90} style={{ display: "inline" }}>{tx(lang, " 分钟", " min")}</Big>
      </div>
    </div>
  );
};

export const Chip: FC<{ at: number; x: number; y: number; children: ReactNode; ghost?: boolean; out?: number; size?: number }> = ({ at, x, y, children, ghost, out, size }) => {
  const en = useLang() === "en";
  return (
    <Card at={at} out={out} style={{ left: x, top: y }}>
      <div style={{
        background: ghost ? "rgba(255,255,255,.75)" : C.card, borderRadius: 32, padding: "18px 40px", boxShadow: shadow,
        border: ghost ? `7px dashed ${C.ghost}` : `6px solid ${C.ink}`, fontFamily: en ? NUM : ZH, fontWeight: en ? 700 : 400,
        fontSize: size ?? (en ? 76 : 84), color: ghost ? C.ghost : C.ink, whiteSpace: "nowrap",
      }}>{children}</div>
    </Card>
  );
};

// Three things that could fill 30 minutes; only one fits the slot.
const ChoiceSlot: FC<{ s: Speech }> = ({ s }) => {
  const t = useT();
  const lang = useLang();
  const cards = lang === "en"
    ? [["choice-reading.png", "Read"], ["choice-nap.png", "Nap"], ["choice-soccer.png", "Soccer"]]
    : [["choice-reading.png", "看书"], ["choice-nap.png", "睡午觉"], ["choice-soccer.png", "踢球"]];
  const pick = s.at(0.62);
  const k = rise(t, pick, 0.8);
  return (
    <AbsoluteFill>
      <Paper />
      <div style={{ position: "absolute", left: 660, top: 90, width: 600, height: 380, border: `10px dashed ${C.ink}`, borderRadius: 40, display: "flex", alignItems: "flex-end", justifyContent: "center" }}>
        <div style={{ marginBottom: -90, background: C.paper, padding: "0 20px" }}><Num size={80}>30</Num><Big size={72} style={{ display: "inline" }}>{tx(lang, " 分钟", " min")}</Big></div>
      </div>
      {cards.map(([src, label], i) => {
        const appear = rise(t, s.at(0.08 + 0.1 * i));
        const chosen = i === 0;
        const x0 = 180 + i * 560, y0 = 600;
        const x = chosen ? interpolate(k, [0, 1], [x0, 700]) : x0;
        const y = chosen ? interpolate(k, [0, 1], [y0, 115]) : y0;
        const ghost = chosen ? 0 : k;
        return (
          <div key={src} style={{ position: "absolute", left: x, top: y, width: 520, opacity: appear * (1 - 0.5 * ghost), transform: `scale(${chosen ? 1 - 0.0 * k : 1})` }}>
            <Img src={file(`images/${src}`)} style={{ width: 520, height: chosen ? interpolate(k, [0, 1], [380, 330]) : 380, objectFit: "cover", borderRadius: 30, border: ghost ? `8px dashed ${C.ghost}` : `8px solid ${C.ink}`, filter: `grayscale(${ghost})` }} />
            <Big size={72} color={ghost ? C.ghost : C.ink} style={{ opacity: chosen ? 1 - k : 1 }}>{label}</Big>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// 24 time coins in four clusters: sleep, school, meals and the road take most; the few left glow.
const COIN_GROUPS = [
  { n: 10, cols: 5, label: { zh: "睡觉", en: "Sleep" }, key: 0.42 },
  { n: 8, cols: 4, label: { zh: "上学", en: "School" }, key: 0.5 },
  { n: 3, cols: 3, label: { zh: "吃饭 · 路上", en: "Meals · trips" }, key: 0.58 },
  { n: 3, cols: 3, label: { zh: "自己选", en: "Yours" }, key: -1 },
];
const TimeCoins: FC<{ s: Speech; sink?: boolean }> = ({ s, sink }) => {
  const t = useT();
  const lang = useLang();
  const glow = rise(t, s.at(0.72), 0.6);
  const sinkK = sink ? rise(t, s.at(0.1), 2.2) : 0;
  const D = 92, STEP = 104, GAP = 70;
  let x = (1920 - (COIN_GROUPS.reduce((w, g) => w + g.cols * STEP, 0) + GAP * 3)) / 2;
  const nodes: ReactNode[] = [];
  COIN_GROUPS.forEach((g, gi) => {
    const free = g.key < 0;
    const used = free ? 0 : rise(t, s.at(g.key), 0.7);
    for (let i = 0; i < g.n; i++) {
      const cx = x + (i % g.cols) * STEP, cy = 400 + Math.floor(i / g.cols) * STEP;
      const sinking = sink && free && i === g.n - 1;
      nodes.push(<div key={`${gi}-${i}`} style={{
        position: "absolute", left: cx, top: cy + (sinking ? sinkK * 470 : 0), width: D, height: D, borderRadius: D / 2,
        background: used || (sink && !free) ? "transparent" : C.gold, border: used || (sink && !free) ? `6px dashed ${C.ghost}` : `6px solid ${C.goldDeep}`,
        transform: `scale(${free && !sink ? 1 + 0.18 * glow : 1})`, boxShadow: free && !sink && glow > 0 ? `0 0 ${40 * glow}px ${C.gold}` : undefined,
      }} />);
    }
    const k = free ? glow : rise(t, s.at(g.key));
    if (!sink) nodes.push(<Big key={`l${gi}`} size={72} color={free ? C.goldDeep : C.ghost} style={{ position: "absolute", left: x - 40, width: g.cols * STEP + 80, top: 640, opacity: k, whiteSpace: "nowrap" }}>{g.label[lang]}</Big>);
    x += g.cols * STEP + GAP;
  });
  return (
    <AbsoluteFill>
      <Paper />
      {sink && <div style={{ position: "absolute", left: 0, right: 0, top: 760, bottom: 0, background: `linear-gradient(${C.water}, #3E7FA6)`, opacity: 0.85 }} />}
      {nodes}
      {!sink && <Card at={s.at(0.05)} style={{ left: 0, right: 0, top: 150, display: "flex", justifyContent: "center" }}><Big size={96}>{tx(lang, <>一天 <Num size={110}>24</Num> 个小时 = <Num size={110}>24</Num> 枚时间币</>, <>A day: <Num size={110}>24</Num> hours = <Num size={110}>24</Num> time coins</>)}</Big></Card>}
    </AbsoluteFill>
  );
};

type View = { x: number; y: number; w: number };
// A big scan, moved from one view of it to another (in the scan's own pixels); paper shows round its edges.
const Focus: FC<{ src: string; W: number; H: number; from: View; to: View; dur: number }> = ({ src, W, H, from, to, dur }) => {
  const t = useT();
  const k = interpolate(t, [0.3, Math.max(0.4, dur - 0.6)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const v = { x: from.x + (to.x - from.x) * k, y: from.y + (to.y - from.y) * k, w: from.w * Math.pow(to.w / from.w, k) };
  const scale = 1920 / v.w;
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Paper />
      <Img src={file(src)} style={{ position: "absolute", left: -v.x * scale, top: -v.y * scale, width: W * scale, height: H * scale }} />
    </AbsoluteFill>
  );
};

const Balance: FC<{ s: Speech; lit?: boolean }> = ({ s, lit }) => {
  const t = useT();
  const lang = useLang();
  const k = rise(t, s.at(0.05), 0.8);
  const right = lit ? 1 : rise(t, s.at(0.55), 0.8);
  const ghostRight = lit ? rise(t, 0.2, 1) : 0;
  const pan = (x: number, children: ReactNode, ghost: boolean, a: number) => (
    <div style={{ position: "absolute", left: x - 330, top: 470, width: 660, opacity: a }}>
      <svg width="660" height="80" style={{ display: "block" }}><path d="M330 0 L60 80 M330 0 L600 80" stroke={C.ink} strokeWidth="6" /></svg>
      <div style={{ minHeight: 330, borderRadius: "0 0 200px 200px", border: ghost ? `8px dashed ${C.ghost}` : `8px solid ${C.ink}`, background: ghost ? "rgba(255,255,255,.6)" : C.card, display: "flex", gap: 24, alignItems: "center", justifyContent: "center", padding: 24 }}>{children}</div>
    </div>
  );
  const thumb = (src: string, label: string, ghost: number) => (
    <div style={{ textAlign: "center" }}>
      <Img src={file(`images/${src}`)} style={{ width: 270, height: 170, objectFit: "cover", borderRadius: 20, filter: `grayscale(${ghost})`, opacity: 1 - 0.45 * ghost }} />
      <Big size={64} color={ghost > 0.5 ? C.ghost : C.ink}>{label}</Big>
    </div>
  );
  return (
    <AbsoluteFill style={{ opacity: k }}>
      <Paper />
      <svg width="1920" height="1080" style={{ position: "absolute" }}>
        <path d="M960 250 L880 980 L1040 980 Z" fill={C.card} stroke={C.ink} strokeWidth="8" />
        <rect x="430" y="440" width="1060" height="24" rx="12" fill={C.ink} />
        <circle cx="960" cy="452" r="26" fill={C.hl} stroke={C.ink} strokeWidth="6" />
      </svg>
      {pan(530, lang === "en" ? <Big size={84}>Fee + skill</Big> : <><Big size={84}>学费</Big><Big size={84}>本领</Big></>, false, 1)}
      {pan(1390, <>{thumb("free-play.png", tx(lang, "自由地玩", "Free play") as string, 1 - ghostRight)}{thumb("family-dinner.png", tx(lang, "全家吃饭", "Family dinner") as string, 1 - ghostRight)}</>, !lit || ghostRight < 0.5, right)}
      <Big size={84} style={{ position: "absolute", left: 230, top: 120, width: 600 }}>{tx(lang, "看得见", "Seen")}</Big>
      <Big size={84} color={lit ? C.ink : C.ghost} style={{ position: "absolute", left: 1090, top: 120, width: 600, opacity: right }}>{tx(lang, "看不见", "Unseen")}</Big>
    </AbsoluteFill>
  );
};

const TwoCosts: FC<{ s: Speech; lit?: boolean }> = ({ s, lit }) => {
  const t = useT();
  const lang = useLang();
  const glow = lit ? rise(t, s.at(0.1), 1.2) : 0;
  const ghostColor = interpolate(glow, [0, 1], [0, 1]);
  const col = (x: number, title: string, body: ReactNode, icon: ReactNode, at: number) => (
    <Card at={at} style={{ left: x, top: 110, width: 760 }}>
      <div style={{ background: C.card, borderRadius: 44, padding: "44px 50px", boxShadow: shadow, border: `6px solid ${C.ink}`, boxSizing: "border-box", display: "flex", flexDirection: "column", alignItems: "center", gap: 26 }}>
        <Big size={lang === "en" ? 72 : 88} style={{ whiteSpace: "nowrap" }}>{title}</Big>
        <div style={{ height: 300, display: "flex", alignItems: "center" }}>{icon}</div>
        <Big size={lang === "en" ? 68 : 80} color={ghostColor > 0.5 ? C.ink : C.ghost}>{body}</Big>
      </div>
    </Card>
  );
  const dash = ghostColor > 0.5 ? "none" : "26 20";
  const stroke = ghostColor > 0.5 ? C.green : C.ghost;
  return (
    <AbsoluteFill>
      <Paper />
      {col(160, tx(lang, "选择的时候", "When you choose") as string, tx(lang, <>放下的<br />那件事</>, <>the thing<br />you put down</>), (
        <div style={{ width: 240, height: 240, borderRadius: 120, border: `10px ${ghostColor > 0.5 ? "solid" : "dashed"} ${ghostColor > 0.5 ? C.goldDeep : C.ghost}`, background: ghostColor > 0.5 ? C.gold : "transparent", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Num size={120} color={ghostColor > 0.5 ? C.ink : C.ghost}>{MONEY[lang].chore}</Num>
        </div>), s.at(0.25))}
      {col(1000, tx(lang, "学习的时候", "When you learn") as string, tx(lang, <>直接拿答案，<br />放下的想法</>, <>ideas you skip<br />for the answer</>), (
        <svg width="560" height="300">
          {[0, 1, 2, 3].map((i) => <path key={i} d={`M20 ${40 + i * 70} C 240 ${40 + i * 70}, 320 150, 520 150`} fill="none" stroke={stroke} strokeWidth="16" strokeDasharray={dash} strokeLinecap="round" />)}
          <circle cx="520" cy="150" r="34" fill={C.ink} />
        </svg>), s.at(0.62))}
    </AbsoluteFill>
  );
};

const Scripture: FC<{ s: Speech }> = ({ s }) => {
  const t = useT();
  const lang = useLang();
  const split = s.at(lang === "en" ? 0.55 : 0.48);
  const a = rise(t, s.at(0.02)) * (1 - rise(t, split, 0.3));
  const b = rise(t, split + 0.2);
  const box = (k: number, lines: string[], ref?: string) => (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: k }}>
      <div style={{ background: "rgba(255,255,255,.95)", borderRadius: 48, padding: "56px 90px", boxShadow: shadow, maxWidth: 1600 }}>
        {lines.map((l) => <Big key={l} size={lang === "en" ? 84 : 92}>{l}</Big>)}
        {ref && <Big size={64} color={C.orangeText} style={{ marginTop: 24 }}>{ref}</Big>}
      </div>
    </AbsoluteFill>
  );
  return (
    <>
      {lang === "en" ? <>
        {box(a, ["“Martha, Martha,", "you are anxious and troubled", "about many things,", "but one thing is needed."])}
        {box(b, ["Mary has chosen the good part,", "which will not be taken", "away from her.”"], "Luke 10:41–42 (WEB)")}
      </> : <>
        {box(a, ["「马大！马大！", "你为许多的事思虑烦扰，", "但是不可少的只有一件；"])}
        {box(b, ["马利亚已经选择那上好的福分，", "是不能夺去的。」"], "路加福音 10:41–42")}
      </>}
    </>
  );
};

// ---- the shot list: backgrounds (may span cues) and per-cue cards ----
type Bg = { from: string; to: string; render: (tl: EconTimeline, dur: number, segStart: number) => ReactNode };
const img = (src: string, push?: Push, ghost?: number) => (_tl: EconTimeline, dur: number) => <Still src={`images/${src}`} dur={dur} push={push} ghost={ghost} />;
const art = (src: string, push?: Push) => (_tl: EconTimeline, dur: number) => <Still src={`art/${src}`} dur={dur} push={push} />;
const paper = () => () => <Paper />;
// roads.<lang>.mp4 (record-roads.cjs) starts FADE before oc04-05, like the segment that shows it, so its clock is the film's.
const ROADS_FROM = "oc04-05";
const page = (label: string) => (tl: EconTimeline, _dur: number, segStart: number) => {
  const rec = tl.cues.find((c) => c.id === ROADS_FROM)!;
  return <Clip tl={tl} name={`roads.${tl.lang}.mp4`} startFrom={segStart - rec.start} label={label} />;
};

const BGS: Bg[] = [
  { from: "oc00-01", to: "oc00-02", render: img("shop.png", { from: 1.0, to: 1.08, ox: 35, oy: 55 }) },
  { from: "oc00-03", to: "oc00-03", render: img("walk.png", { from: 1.1, to: 1.0, ox: 40, oy: 60 }) },
  { from: "oc00-04", to: "oc00-04", render: img("chores.png", { from: 1.0, to: 1.06, ox: 60, oy: 55 }) },
  { from: "oc00-05", to: "oc00-05", render: paper() },
  { from: "oc00-06", to: "oc00-07", render: img("icepop-hand.png", { from: 1.0, to: 1.05, ox: 30, oy: 45 }) },
  { from: "oc01-01", to: "oc01-01", render: img("chores.png", { from: 1.06, to: 1.12, ox: 62, oy: 75 }) },
  { from: "oc01-02", to: "oc01-04", render: paper() },
  { from: "oc01-05", to: "oc01-05", render: img("town.png", { from: 1.0, to: 1.1, ox: 40, oy: 60 }) },
  { from: "oc02-01", to: "oc02-01", render: img("piano-hour.png", { from: 1.0, to: 1.06, ox: 30, oy: 50 }) },
  { from: "oc02-02", to: "oc02-02", render: img("recital.png", { from: 1.0, to: 1.06, ox: 50, oy: 50 }) },
  { from: "oc02-03", to: "oc02-03", render: art("bastiat-portrait.jpg", { from: 1.55, to: 1.7, ox: 50, oy: 46, fit: "contain" }) },
  { from: "oc02-04", to: "oc02-07", render: paper() },
  { from: "oc03-01", to: "oc03-01", render: img("piano-hour.png", { from: 1.06, to: 1.1, ox: 30, oy: 50 }, 0.6) },
  { from: "oc03-02", to: "oc03-03", render: img("desk-thinking.png", { from: 1.0, to: 1.1, ox: 45, oy: 70 }) },
  { from: "oc03-04", to: "oc03-04", render: paper() },
  { from: "oc04-01", to: "oc04-01", render: img("times-chart.png", { from: 1.0, to: 1.06, ox: 40, oy: 45 }) },
  { from: "oc04-02", to: "oc04-04", render: img("classroom.png", { from: 1.0, to: 1.08, ox: 45, oy: 45 }) },
  { from: "oc04-05", to: "oc04-07", render: page("网页录屏 s0–s2") },
  { from: "oc04-08", to: "oc04-08", render: (tl) => <Clip tl={tl} name={`hands.${tl.lang}.mp4`} startFrom={0} label="手指实拍" /> },
  { from: "oc04-15", to: "oc04-15", render: (_tl, dur) => <Focus src="art/rhind-papyrus.jpg" W={6271} H={1864} from={{ x: 0, y: -830, w: 6271 }} to={{ x: 3300, y: 980, w: 1800 }} dur={dur} /> },
  { from: "oc04-16", to: "oc04-24", render: page("网页录屏 s4–s5") },
  { from: "oc05-01", to: "oc05-01", render: paper() },
  { from: "oc05-02", to: "oc05-02", render: page("网页录屏 s5") },
  { from: "oc05-03", to: "oc05-05", render: paper() },
  { from: "oc06-01", to: "oc06-01", render: img("icepop-hand.png", { from: 1.05, to: 1.1, ox: 30, oy: 45 }) },
  { from: "oc06-02", to: "oc06-04", render: art("martha-mary.jpg", { from: 1.0, to: 1.12, ox: 40, oy: 55, fit: "cover" }) },
  { from: "oc07-01", to: "oc07-01", render: paper() },
];

const CARDS: Record<string, (s: Speech, tl: EconTimeline) => ReactNode> = {
  "oc00-01": (s, tl) => <PriceTag x={1220} y={300} at={s.at(0.25)} items={[{ text: MONEY[tl.lang].price, kind: "solid", at: s.at(0.25) }]} />,
  "oc00-02": (_s, tl) => (<>
    <PriceTag x={1220} y={300} items={[{ text: MONEY[tl.lang].price, kind: "solid", at: 0 }]} />
    <Bubble at={0.1} who="Mary" text={tx(tl.lang, <>姐姐，这还用问吗？<br />当然是五块钱呀！</>, <>That's easy!<br />$2, of course!</>)} x={120} y={90} tail="left" />
  </>),
  "oc00-03": (s) => <Clock at={s.at(0.35)} x={1080} y={110} />,
  "oc00-04": (s, tl) => <Chip at={s.at(0.55)} x={760} y={800}>{tx(tl.lang, "做家务", "Chores")} <Num size={92}>30</Num>{tx(tl.lang, " 分钟", " min")} → <Num size={92} color={C.orangeText}>{MONEY[tl.lang].chore}</Num></Chip>,
  "oc00-05": (s, tl) => <PriceTag x={420} y={380} scale={1.5} items={[{ text: MONEY[tl.lang].price, kind: "solid", at: 0 }, { text: `+ ${MONEY[tl.lang].chore}`, kind: "ghost", at: s.at(0.4) }, { text: "= ?", kind: "ghost", at: s.at(0.85) }]} />,
  "oc00-06": (s, tl) => (<>
    <PriceTag x={1180} y={620} scale={0.9} items={[{ text: MONEY[tl.lang].price, kind: "solid", at: 0 }, { text: `+ ${MONEY[tl.lang].chore}`, kind: "ghost", at: s.at(0.55) }]} />
    <Bubble at={0.1} who="Mary" text={tx(tl.lang, <>嗯……五块钱，再加上……<br />没拿到的那两块钱？</>, <>Umm... $2, plus...<br />the dollar I didn't get?</>)} x={640} y={50} tail="left" />
  </>),
  "oc00-07": (s, tl) => (<>
    <PriceTag x={1050} y={620} scale={0.9} items={[{ text: MONEY[tl.lang].price, kind: "solid", at: 0 }, { text: `+ ${MONEY[tl.lang].chore}`, kind: "ghost", at: 0 }, { text: `= ${MONEY[tl.lang].total}`, kind: "answer", at: s.at(0.1) }]} />
    <TitleCard at={s.s1 + 0.2} />
  </>),
  "oc01-01": (s, tl) => <BigText at={s.at(tl.lang === "en" ? 0.8 : 0.72)} lines={[tx(tl.lang, "机会成本", "Opportunity cost")]} size={tl.lang === "en" ? 150 : 170} />,
  "oc01-02": (s, tl) => <PriceTag x={300} y={400} scale={1.5} items={[{ text: MONEY[tl.lang].price, kind: "solid", at: 0.2 }, { text: `+ ${MONEY[tl.lang].chore}`, kind: "ghost", at: s.at(0.35) }, { text: `= ${MONEY[tl.lang].total}`, kind: "answer", at: s.at(0.75) }]} />,
  "oc01-03": (s) => <ChoiceSlot s={s} />,
  "oc01-04": (s, tl) => (<>
    <PriceTag x={360} y={260} scale={1.3} items={[{ text: MONEY[tl.lang].price, kind: "solid", at: 0, strikeAt: s.at(0.18) }, { text: MONEY[tl.lang].zero, kind: "solid", at: s.at(0.22) }, { text: `+ ${MONEY[tl.lang].chore}`, kind: "ghost", at: 0.2 }]} />
    <BigText at={s.at(0.62)} lines={tx(tl.lang, ["天下没有免费的午餐"], ["There's no such thing", "as a free lunch"]) as ReactNode[]} size={tl.lang === "en" ? 100 : 120} y={tl.lang === "en" ? 610 : 680} />
  </>),
  "oc01-05": (s, tl) => (<>
    <Chip at={s.at(0.3)} x={300} y={640}>{tx(tl.lang, "隔壁：", "Next door: ")}<Num size={92}>2</Num>{tx(tl.lang, " 分钟", " min")}</Chip>
    <Chip at={s.at(0.68)} x={1150} y={160}>{tx(tl.lang, "住得远：", "Far away: ")}<Num size={92}>30</Num>{tx(tl.lang, " 分钟", " min")}</Chip>
  </>),
  "oc02-01": (s, tl) => <PriceTag x={1050} y={200} items={[{ text: tx(tl.lang, "学费", "Fee") as string, kind: "solid", at: s.at(0.45) }, { text: tx(tl.lang, "+ ？", "+ ?") as string, kind: "ghost", at: s.at(0.7) }]} />,
  "oc02-02": (s, tl) => (<>
    <Card at={s.at(0.5)} style={{ inset: 0 }}><AbsoluteFill><Still src="images/piano-hour.png" dur={s.dur} push={{ from: 1.0, to: 1.04 }} /></AbsoluteFill></Card>
    <Sequence from={0}><GhostOver src="images/soccer-hour.png" at={s.at(0.6)} /></Sequence>
    <BigText at={s.at(0.8)} lines={[tx(tl.lang, "没有做的事，谁也看不见", "What she didn't do, nobody sees")]} size={96} />
  </>),
  "oc02-03": (s, tl) => (<>
    <Chip at={s.at(0.1)} x={1180} y={140}>{tx(tl.lang, "巴斯夏", "Bastiat")} · <Num size={92}>1850</Num></Chip>
    <Card at={s.at(0.3)} style={{ left: tl.lang === "en" ? 1040 : 1100, top: 330 }}><div style={{ background: C.card, borderRadius: 36, padding: "26px 44px", boxShadow: shadow }}>
      <Big size={tl.lang === "en" ? 70 : 88}>{tx(tl.lang, <>《看得见的<br />与看不见的》</>, <>“That Which Is Seen,<br />and That Which<br />Is Not Seen”</>)}</Big></div></Card>
    <Card at={s.at(0.55)} style={{ inset: 0 }}><AbsoluteFill><Paper /><AbsoluteFill style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 70 }}>
      <div style={{ background: C.card, border: `6px solid ${C.ink}`, borderRadius: 40, padding: "50px 50px", whiteSpace: "nowrap" }}><Big size={76}>{tx(tl.lang, "不好的经济学家", "A bad economist")}</Big><Big size={tl.lang === "en" ? 76 : 88} style={{ marginTop: 20 }}>{tx(tl.lang, "只看见看得见的", <>sees only<br />what is seen</>)}</Big></div>
      <div style={{ background: C.card, border: `6px solid ${C.green}`, borderRadius: 40, padding: "50px 50px", whiteSpace: "nowrap" }}><Big size={76}>{tx(tl.lang, "好的经济学家", "A good economist")}</Big><Big size={tl.lang === "en" ? 76 : 88} color={C.green} style={{ marginTop: 20 }}>{tx(tl.lang, "还会去想看不见的", <>also thinks of<br />what is not seen</>)}</Big></div>
    </AbsoluteFill></AbsoluteFill></Card>
  </>),
  "oc02-04": (s) => <TimeCoins s={s} />,
  "oc02-05": (s, tl) => <BigText at={s.at(tl.lang === "en" ? 0.75 : 0.55)} lines={[tx(tl.lang, "稀缺", "Scarcity")]} size={200} onPaper />,
  "oc02-06": (s) => <Balance s={s} />,
  "oc02-07": (s) => <Balance s={s} lit />,
  "oc03-03": (s) => <Card at={s.at(0.3)} style={{ inset: 0 }}><AbsoluteFill style={{ background: "rgba(247,249,242,.55)", backdropFilter: "grayscale(1)" }} /></Card>,
  "oc03-04": (s) => <BigText at={s.at(0.6)} lines={[<Num key="n" size={260}><span style={{ color: C.redText }}>7</span> × <span style={{ color: C.orangeText }}>8</span></Num>]} onPaper />,
  "oc04-02": (_s, tl) => <Bubble at={0.05} who="Mary" text={tx(tl.lang, "七八五十六！", "Seven eights are fifty-six!")} x={160} y={110} />,
  "oc04-03": (_s, tl) => <Bubble at={0.05} who={tx(tl.lang, "老师", "Teacher") as string} text={tx(tl.lang, "你是怎么算出来的？", <>How did you<br />work it out?</>)} x={tl.lang === "en" ? 1150 : 1000} y={110} tail="right" />,
  "oc04-04": (_s, tl) => <Bubble at={0.05} who="Mary" text={tx(tl.lang, "口诀里就是这么说的呀！", <>That's what the<br />times table says!</>)} x={160} y={110} />,
  // The finger path is one line since v0.8; its explanation is its own video. The chip sits on the empty wall above the hands.
  "oc04-08": (s, tl) => (
    <Chip at={s.at(0.62)} x={70} y={60} size={tl.lang === "en" ? 68 : 76}>
      {tx(tl.lang, <>另一个视频：你会算 <Num size={84}>7 × 8</Num> 吗？</>, <>Its own video: Can You Work Out <Num size={76}>7 × 8</Num>?</>)}
    </Chip>
  ),
  "oc04-15": (s, tl) => <Chip at={s.at(0.3)} x={160} y={880} size={tl.lang === "en" ? 64 : undefined}>{tx(tl.lang, "古埃及 · 莱因德数学纸草书（现代誊写）", "Ancient Egypt · the Rhind Papyrus (modern copy)")}</Chip>,
  "oc04-24": (s, tl) => <PriceTag x={tl.lang === "en" ? 1200 : 1300} y={880} scale={0.75} at={s.at(0.6)} items={[{ text: "56", kind: "answer", at: s.at(0.6) }, { text: tx(tl.lang, "+ 四条路", "+ 4 paths") as string, kind: "ghost", at: s.at(0.75) }]} />,
  "oc05-01": (s, tl) => <BigText at={s.at(0.15)} lines={[tx(tl.lang, "口诀背得熟，是好事", "Knowing the table well is good")]} size={tl.lang === "en" ? 100 : 120} onPaper />,
  "oc05-03": (s) => <TwoCosts s={s} />,
  "oc05-04": (s, tl) => (<><TwoCosts s={s} lit /><BigText at={s.at(0.5)} lines={[tx(tl.lang, "看见看不见的", "See what can't be seen")]} size={110} y={860} /></>),
  "oc05-05": (s, tl) => (<><TimeCoins s={s} sink /><BigText at={s.at(0.7)} lines={[tx(tl.lang, "沉没成本 · 下一集", "Sunk cost · next time")]} size={110} y={90} /></>),
  "oc06-01": (s) => <Card at={s.at(0.05)} style={{ left: 1150, top: 380 }}><Num size={220} color={C.orangeText}>Mary</Num></Card>,
  "oc06-03": (s) => <Scripture s={s} />,
  "oc07-01": (s, tl) => <Ending s={s} tl={tl} />,
};

// Where each part of the closing line starts, as a share of its speech (the two languages order it the same way).
const ENDING = {
  zh: { q1: 0.17, words: 0.18, formula: 0.27, ai: 0.36, homework: 0.46, q2: [0.47, 0.74], last: 0.76 },
  en: { q1: 0.21, words: 0.23, formula: 0.32, ai: 0.4, homework: 0.52, q2: [0.53, 0.65], last: 0.66 },  // from the take's word times
};
const Ending: FC<{ s: Speech; tl: EconTimeline }> = ({ s, tl }) => {
  const { fps } = useVideoConfig();
  const E = ENDING[tl.lang];
  const shots: [number, number, ReactNode][] = [
    [0, s.at(E.words), <PriceTag key="p" x={500} y={420} scale={1.4} items={[{ text: MONEY[tl.lang].price, kind: "solid", at: 0 }, { text: `+ ${MONEY[tl.lang].chore}`, kind: "ghost", at: 0.3 }]} />],
    [s.at(E.words), s.at(E.formula), <Still key="w" src="images/ending-words.png" dur={2} />],
    [s.at(E.formula), s.at(E.ai), <Still key="f" src="images/ending-formula.png" dur={2} />],
    [s.at(E.ai), s.at(E.homework), <Still key="a" src="images/ending-ai.png" dur={2} />],
    [s.at(E.homework), s.dur, <Clip key="h" tl={tl} name="homework.mp4" label="编程作业录屏" />],
  ];
  return (
    <AbsoluteFill>
      {shots.map(([a, b, node], i) => (
        <Sequence key={i} from={Math.round(a * fps)} durationInFrames={Math.max(1, Math.round((b - a) * fps))}>{node}</Sequence>
      ))}
      <BigText at={s.at(0.02)} out={s.at(E.q1)} lines={tx(tl.lang, ["下一次花掉三十分钟，", "你会看见被放下的选项吗？"], ["Next time you spend 30 minutes,", "will you see the choice you put down?"]) as ReactNode[]} size={tl.lang === "en" ? 80 : 96} y={90} />
      <BigText at={s.at(E.q2[0])} out={s.at(E.q2[1])} lines={tx(tl.lang, ["你知道自己放下了", "什么样的机会吗？"], ["Do you know what chance", "you're giving up?"]) as ReactNode[]} size={tl.lang === "en" ? 88 : 96} y={700} />
      <BigText at={s.at(E.last)} lines={tx(tl.lang, ["学会了什么，", "更要在过程里学会思考"], ["What you learn, and even more:", "learning how to think"]) as ReactNode[]} size={tl.lang === "en" ? 88 : 96} y={700} />
    </AbsoluteFill>
  );
};

export const FunEconomics01Video: FC<EconProps> = ({ tl }) => {
  useFonts();
  const { fps } = useVideoConfig();
  if (!tl) return null;
  const F = (s: number) => Math.round(s * fps);
  const at = (id: string) => tl.cues.find((c) => c.id === id)!;
  const FADE = 0.3;
  return (
    <LangCtx.Provider value={tl.lang}>
    <AbsoluteFill style={{ background: C.paper }}>
      {BGS.map((bg, i) => {
        const a = i === 0 ? 0 : at(bg.from).start - FADE, b = at(bg.to).end;
        const segStart = at(bg.from).start;
        return (
          <Sequence key={bg.from} from={F(a)} durationInFrames={Math.max(1, F(b) - F(a))}>
            <FadeIn d={i === 0 ? 0 : FADE}>{bg.render(tl, b - a, segStart)}</FadeIn>
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
      <Sequence from={F(tl.endCardStart)}><EndCard /></Sequence>
      <Audio src={file(`audio/${tl.lang}.mix.wav`)} />
      {tl.draft && <div style={{ position: "absolute", right: 30, bottom: 24, fontFamily: NUM, fontWeight: 700, fontSize: 64, color: C.red, opacity: 0.7 }}>DRAFT</div>}
    </AbsoluteFill>
    </LangCtx.Provider>
  );
};

export const FadeIn: FC<{ d: number; children: ReactNode }> = ({ d, children }) => {
  const t = useT();
  return <AbsoluteFill style={{ opacity: d ? interpolate(t, [0, d], [0, 1], { extrapolateRight: "clamp" }) : 1 }}>{children}</AbsoluteFill>;
};

// YouTube cover: one question, one picture (README "YouTube covers"). zh: big Chinese, small English; en flipped.
const CoverFrame: FC<{ lang: Lang }> = ({ lang }) => {
  useFonts();
  const zh = (
    <LangCtx.Provider value="zh">
      <Big size={lang === "zh" ? 168 : 80} style={{ textAlign: "left", lineHeight: 1.12, whiteSpace: "nowrap", textShadow: "0 4px 0 rgba(255,255,255,.9)" }}>
        一根<span style={{ color: C.orangeText }}>冰棍</span>，<br />要花<span style={{ color: C.green }}>多少钱</span>？
      </Big>
    </LangCtx.Provider>
  );
  const en = (
    <div style={{ fontFamily: NUM, fontWeight: 700, fontSize: lang === "en" ? 118 : 64, lineHeight: 1.05, color: C.ink, whiteSpace: "nowrap", textShadow: "0 4px 0 rgba(255,255,255,.9)" }}>
      {lang === "en" ? <>How Much<br />Does an <span style={{ color: C.orangeText }}>Ice Pop</span><br /><span style={{ color: C.green }}>Cost</span>?</>
        : <>How Much Does an<br /><span style={{ color: C.orangeText }}>Ice Pop</span> <span style={{ color: C.green }}>Cost</span>?</>}
    </div>
  );
  return (
    <AbsoluteFill>
      <Img src={file("images/icepop-hand.png")} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "20% 50%" }} />
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(247,249,242,0) 30%, rgba(247,249,242,.88) 52%, rgba(247,249,242,.95) 100%)" }} />
      <div style={{ position: "absolute", left: 930, top: 110, width: 960, display: "flex", flexDirection: "column", gap: 30 }}>
        {lang === "zh" ? <>{zh}{en}</> : <>{en}{zh}</>}
      </div>
      <PriceTag x={1010} y={790} scale={1.0} at={-1} items={[{ text: MONEY[lang].price, kind: "solid", at: -1 }, { text: `+ ${MONEY[lang].chore}`, kind: "ghost", at: -1 }]} />
    </AbsoluteFill>
  );
};
export const FunEconomics01Cover: FC = () => <CoverFrame lang="zh" />;
export const FunEconomics01CoverEn: FC = () => <CoverFrame lang="en" />;
