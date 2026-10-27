/**
 * 「跨越中等收入陷阱」 · 从新闻看教育 / Lessons from the Headlines (MIDDLE-INCOME-TRAP.md, docs/middle-income-trap/video-plan.md).
 * The series is never numbered.
 *
 * Chinese first (Yancy, 2026-10-25): Yancy's cloned voice, Li Lu's own voice in two clips, captions in a separate SRT,
 * so the words on screen are only the key words, numbers and the chapter bar. Every one of them is in Chinese and
 * English, the English a little smaller underneath (Yancy, 2026-10-26: 应该改成中英文，英文比中文稍小一点); in
 * edit.json a string is written 「中文|English」. The shot list is
 * scripts/middle-income-trap/edit.json, timed by build_timeline.py; each shot fades into the next. Pictures: Codex
 * illustrations (one style, each tagged 「AI 插图」), Li Lu's talk, one public-domain photo, and graphics drawn here.
 * Real people and events are never drawn by AI (the series' rule). The chapter bar along the bottom follows the cube
 * film's (ChapterBar.tsx).
 */
import { useEffect, useState, type CSSProperties, type FC, type ReactNode } from "react";
import {
  AbsoluteFill,
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
import { ChapterBar, type Chapter, type Skip } from "./ChapterBar";

const DIR = "middle-income-trap";
const file = (p: string) => staticFile(`${DIR}/${p}`);

type Shot = {
  k: string; start: number; end: number; src?: string; push?: [number, number, number, number]; label?: string;
  items?: string[] | [string, string][]; itemsAt?: number[]; lines?: [string, string][]; linesAt?: number[];
  big?: string; bigAt?: number; line?: string; lineBy?: string; lineAt?: number; num?: string; sub?: string; numAt?: number;
  groups?: { items: string[]; tone: "gold" | "grey" }[]; notes?: string[]; notesAt?: number[]; dropAt?: number;
  splitAt?: number; noteAt?: number; head?: string; skip?: boolean; compound?: boolean; by?: string; cite?: string;
  promo?: string; promoAt?: number[]; notesFirst?: boolean; barHintAt?: number[];
};
export type MitTimeline = {
  fps: number; durationSeconds: number; shots: Shot[]; chapters: Chapter[];
  lines: Record<string, { start: number; end: number; text: string }>;
};
export type MitProps = { tl?: MitTimeline | null };

export const calculateMitMetadata: CalculateMetadataFunction<MitProps> = async ({ props, abortSignal }) => {
  const r = await fetch(file("timeline.json"), { signal: abortSignal });
  if (!r.ok) throw Error("Run scripts/middle-income-trap/build_timeline.py first");
  const tl = (await r.json()) as MitTimeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

// ---- look (the series') ----
const INK = "#0f1317";
const EMBER = "#e2733c";
const GOLD = "#c9a45a";
const PAPER = "#ece3d2";
const SOFT = "#d9d3c7";
const MUTED = "#8f989f";
const GREY = "#5d666e";
const SERIF = "'NotoSerifSC', 'Songti SC', serif";
const FADE = 0.8; // seconds of cross-fade between shots
const CARD = 2.9; // seconds a chapter card stays up
const LIFT = 150; // words on a picture stay above the chapter bar
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = Easing.bezier(0.3, 0.7, 0.2, 1);
const SHADOW = "0 4px 30px rgba(0,0,0,.75), 0 1px 3px rgba(0,0,0,.8)";
const LILU = "李录 · 哥伦比亚商学院 · 2026-10-05|Li Lu · Columbia Business School · Oct 5, 2026";
const AI_TAG = "AI 插图|AI illustration";

/** 「中文|English」 → the two halves; English is drawn a little smaller, light, under the Chinese. */
const bi = (s: string) => { const [zh, en] = s.split("|"); return [zh, en ?? ""] as const; };
const enSize = (zh: number) => Math.round(zh >= 100 ? zh * 0.45 : zh * 0.62);
const Bi: FC<{ s: string; size: number; color?: string; enColor?: string; zh?: CSSProperties; en?: CSSProperties }> = ({ s, size, color, enColor, zh, en }) => {
  const [a, b] = bi(s);
  return (
    <>
      <div style={{ fontSize: size, color, ...zh }}>{a}</div>
      {b ? <div style={{ fontSize: enSize(size), fontWeight: 300, color: enColor ?? color, letterSpacing: 0.5, lineHeight: 1.25,
        marginTop: Math.round(size * 0.12), ...en }}>{b}</div> : null}
    </>
  );
};

const FONTS: [string, string, string][] = [
  ["NotoSerifSC", "fonts/NotoSerifSC-Regular.otf", "400"],
  ["NotoSerifSC", "fonts/NotoSerifSC-Light.otf", "300"],
];
const useFonts = () => {
  const [handle] = useState(() => delayRender("fonts"));
  useEffect(() => {
    Promise.all(FONTS.map(([family, path, weight]) => new FontFace(family, `url(${file(path)})`, { weight }).load()))
      .then((faces) => { faces.forEach((f) => document.fonts.add(f)); continueRender(handle); })
      .catch((e) => { console.error(e); continueRender(handle); });
  }, [handle]);
};

/** Seconds since the enclosing Sequence began. */
const useT = () => useCurrentFrame() / useVideoConfig().fps;
const appear = (t: number, at: number, d = 0.8) => interpolate(t, [at, at + d], [0, 1], { ...clamp, easing: ease });
const rise = (o: number): CSSProperties => ({ opacity: o, transform: `translateY(${(1 - o) * 18}px)` });

const Dark: FC<{ children?: ReactNode; style?: CSSProperties }> = ({ children, style }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 40%, #1b2128 0%, ${INK} 70%)`, ...style }}>{children}</AbsoluteFill>
);

/** A small line of provenance above the chapter bar, bottom left. */
const Label: FC<{ text: string; right?: boolean }> = ({ text, right }) => (
  <div style={{ position: "absolute", [right ? "right" : "left"]: 40, bottom: 118, fontFamily: SERIF, fontWeight: 300,
    letterSpacing: 1, color: "rgba(255,255,255,.72)", textShadow: "0 1px 6px rgba(0,0,0,.9)", textAlign: right ? "right" : "left" }}>
    <Bi s={text} size={right ? 18 : 22} en={{ marginTop: 2 }} />
  </div>
);

// ---- icons (simple strokes, no words) ----
const Icon: FC<{ name: string; size?: number; color?: string }> = ({ name, size = 120, color = SOFT }) => {
  const st = { fill: "none", stroke: color, strokeWidth: 5, strokeLinecap: "round", strokeLinejoin: "round" } as const;
  const shapes: Record<string, ReactNode> = {
    school: <><path d="M14 98V48L60 22l46 26v50Z" {...st} /><path d="M46 98V70h28v28M60 22V6l18 6-18 6" {...st} /></>,
    student: <><circle cx="60" cy="34" r="16" {...st} /><path d="M28 104c2-26 14-40 32-40s30 14 32 40" {...st} /><path d="M38 20l22-10 22 10-22 10Z" {...st} /></>,
    teacher: <><circle cx="48" cy="32" r="15" {...st} /><path d="M18 104c2-26 12-40 30-40 10 0 18 4 24 12" {...st} /><path d="M70 30h40v34H70" {...st} /><path d="M66 76l28-20" {...st} /></>,
    crowd: <><circle cx="34" cy="40" r="11" {...st} /><circle cx="60" cy="32" r="12" {...st} /><circle cx="86" cy="40" r="11" {...st} /><path d="M14 100c2-22 10-34 20-34M106 100c-2-22-10-34-20-34M38 104c2-26 10-40 22-40s20 14 22 40" {...st} /></>,
    sun: <><circle cx="60" cy="60" r="20" {...st} />{[...Array(8)].map((_, i) => { const a = (i * Math.PI) / 4; return <path key={i} d={`M${60 + 30 * Math.cos(a)} ${60 + 30 * Math.sin(a)}L${60 + 44 * Math.cos(a)} ${60 + 44 * Math.sin(a)}`} {...st} />; })}</>,
    ship: <><path d="M14 74h92l-12 22H26Z" {...st} /><path d="M34 74V46h40v28M54 46V24h14v22" {...st} /><path d="M10 104c10-6 20-6 30 0s20 6 30 0 20-6 30 0" {...st} /></>,
    wheat: <><path d="M60 108V18" {...st} />{[30, 48, 66].map((y) => <g key={y}><path d={`M60 ${y}c-14-2-20-10-20-18 10 0 18 6 20 18Z`} {...st} /><path d={`M60 ${y}c14-2 20-10 20-18-10 0-18 6-20 18Z`} {...st} /></g>)}</>,
    lock: <><rect x="26" y="54" width="68" height="52" rx="8" {...st} /><path d="M40 54V40c0-12 8-22 20-22s20 10 20 22v14" {...st} /><circle cx="60" cy="78" r="6" {...st} /></>,
    bulb: <><path d="M42 74c-10-8-14-18-14-28a32 32 0 0 1 64 0c0 10-4 20-14 28v12H42Z" {...st} /><path d="M44 98h32M50 108h20" {...st} /></>,
  };
  return <svg width={size} height={size} viewBox="0 0 120 120">{shapes[name]}</svg>;
};

// ---- pictures ----
const Art: FC<{ s: Shot; dur: number; tag?: boolean }> = ({ s, dur, tag = true }) => {
  const t = useT();
  const [p0, p1, ox, oy] = s.push ?? [1.0, 1.08, 50, 45];
  const sc = interpolate(t, [0, Math.max(dur + FADE, 0.1)], [p0, p1], { ...clamp, easing: Easing.inOut(Easing.sin) });
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: INK }}>
      <AbsoluteFill style={{ transform: `scale(${sc})`, transformOrigin: `${ox}% ${oy}%` }}>
        <Img src={file(`art/${s.src}.jpg`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      {tag ? <Label text={AI_TAG} right /> : null}
    </AbsoluteFill>
  );
};

const Still: FC<{ s: Shot; dur: number }> = ({ s, dur }) => {
  const t = useT();
  const sc = interpolate(t, [0, dur + FADE], [1.0, 1.06], clamp);
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: INK }}>
      <Img src={file(`stills/${s.src}.jpg`)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${sc})`,
        filter: s.items ? "brightness(.55) saturate(.8)" : "brightness(.9)" }} />
      <Label text={LILU} />
    </AbsoluteFill>
  );
};

/** A Li Lu clip with its own sound in the mix; the picture is 16:9 inside 960×720, so the letterbox is cropped. */
const Clip: FC<{ s: Shot }> = ({ s }) => (
  <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
    <OffthreadVideo src={file(`clips/${s.src}`)} muted style={{ position: "absolute", left: 0, top: -180, width: 1920, height: 1440 }} />
    <Label text={LILU} />
  </AbsoluteFill>
);

const Photo: FC<{ s: Shot; dur: number }> = ({ s, dur }) => {
  const t = useT();
  const sc = interpolate(t, [0, dur + FADE], [1.0, 1.05], clamp);
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#120f0c" }}>
      <Img src={file(`art/${s.src}`)} style={{ position: "absolute", left: -90, top: -90, width: 2100, height: 1260, objectFit: "cover",
        filter: "blur(46px) brightness(.35) saturate(.6)" }} />
      <AbsoluteFill style={{ transform: `scale(${sc})`, padding: "40px 0 150px" }}>
        <Img src={file(`art/${s.src}`)} style={{ width: "100%", height: "100%", objectFit: "contain", filter: "drop-shadow(0 24px 50px rgba(0,0,0,.6))" }} />
      </AbsoluteFill>
      {s.label ? <Label text={s.label} /> : null}
    </AbsoluteFill>
  );
};

// ---- words over a picture ----
const Chips: FC<{ items: string[]; at: number[]; big?: boolean }> = ({ items, at, big }) => {
  const t = useT();
  return (
    <div style={{ position: "absolute", left: 80, right: 80, bottom: LIFT, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 22 }}>
      {items.map((w, i) => {
        const o = appear(t, at[i] ?? 0, 0.6);
        return (
          <div key={w} style={{ ...rise(o), fontFamily: SERIF, color: PAPER, textAlign: "center",
            background: "rgba(10,12,15,.62)", borderRadius: 12, padding: big ? "10px 34px" : "8px 26px", textShadow: SHADOW,
            border: `1px solid rgba(201,164,90,.35)` }}><Bi s={w} size={big ? 60 : 44} zh={{ letterSpacing: 3 }} en={{ color: SOFT }} /></div>
        );
      })}
    </div>
  );
};

const Big: FC<{ text: string; at: number }> = ({ text, at }) => {
  const t = useT();
  const o = appear(t, at, 0.5);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ fontFamily: SERIF, fontSize: 420, color: EMBER, opacity: o, transform: `scale(${1.25 - 0.25 * o})`,
        textShadow: "0 10px 60px rgba(0,0,0,.85)", lineHeight: 1 }}>{bi(text)[0]}</div>
      {bi(text)[1] ? <div style={{ fontFamily: SERIF, fontSize: 64, fontWeight: 300, color: PAPER, opacity: o, marginTop: 18,
        textShadow: SHADOW, letterSpacing: 1 }}>{bi(text)[1]}</div> : null}
    </AbsoluteFill>
  );
};

const QuoteLine: FC<{ text: string; by?: string; at: number }> = ({ text, by, at }) => {
  const t = useT();
  const o = appear(t, at, 1.0);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: LIFT, textAlign: "center", fontFamily: SERIF, ...rise(o) }}>
      <span style={{ display: "inline-block", background: "rgba(10,12,15,.6)", borderRadius: 14, padding: "16px 44px" }}>
        <Bi s={text} size={54} color={PAPER} zh={{ letterSpacing: 4, textShadow: SHADOW }} en={{ color: SOFT, textShadow: SHADOW }} />
        {by ? <div style={{ marginTop: 10, color: GOLD }}><Bi s={by} size={26} zh={{ fontWeight: 300, letterSpacing: 2 }} en={{ marginTop: 2 }} /></div> : null}
      </span>
    </div>
  );
};

const Num: FC<{ value: string; sub?: string; at: number }> = ({ value, sub, at }) => {
  const t = useT();
  const o = appear(t, at, 1.0);
  return (
    <div style={{ position: "absolute", left: 110, bottom: LIFT, fontFamily: SERIF, color: "#fff", textShadow: SHADOW, ...rise(o) }}>
      <div style={{ fontSize: 132, fontWeight: 300, letterSpacing: 2, lineHeight: 1 }}>{value}</div>
      {sub ? <div style={{ marginTop: 14, opacity: 0.9 }}><Bi s={sub} size={40} zh={{ fontWeight: 300, letterSpacing: 4 }} /></div> : null}
    </div>
  );
};

// ---- cards and graphics ----
const Title: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  return (
    <AbsoluteFill>
      <Art s={{ ...s, push: [1.04, 1.0, 50, 30] }} dur={4} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(10,12,15,.15) 0%, rgba(10,12,15,.55) 45%, rgba(10,12,15,.85) 100%)" }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, color: "#fff", textAlign: "center", paddingBottom: 120 }}>
        <div style={{ fontSize: 34, fontWeight: 300, letterSpacing: 8, color: GOLD, opacity: appear(t, 0.2) }}>从新闻看教育 · LESSONS FROM THE HEADLINES</div>
        <div style={{ fontSize: 120, fontWeight: 400, marginTop: 34, opacity: appear(t, 0.5), letterSpacing: 10, textShadow: SHADOW }}>跨越中等收入陷阱</div>
        <div style={{ fontSize: 56, fontWeight: 300, marginTop: 22, opacity: appear(t, 0.8), color: SOFT, textShadow: SHADOW }}>Crossing the Middle-Income Trap</div>
        <div style={{ fontSize: 30, fontWeight: 300, marginTop: 44, opacity: appear(t, 1.0), color: SOFT, letterSpacing: 3 }}>Yancy Qin | Lucas Academy</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Quote: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const at = s.linesAt ?? [];
  const look = (kind: string): [number, CSSProperties, CSSProperties] =>
    kind === "lead" ? [50, { fontWeight: 300, color: SOFT, letterSpacing: 6 }, { color: MUTED }]
      : kind === "key2" ? [64, { color: GOLD, letterSpacing: 4 }, { color: SOFT }]
        : kind === "cite" ? [50, { color: PAPER, letterSpacing: 2, lineHeight: 1.5, maxWidth: 1760 }, { color: SOFT, maxWidth: 1500, fontStyle: "italic" }]
          : [120, { color: GOLD, letterSpacing: 10 }, { color: SOFT }];
  const last = at.length ? at[at.length - 1] : 0;
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, textAlign: "center", paddingBottom: 90 }}>
        {(s.lines ?? []).map(([text, kind], i) => {
          const [size, zh, en] = look(kind);
          return (
            <div key={i} style={{ marginTop: i ? (kind === "key" ? 30 : 40) : 0, display: "flex", flexDirection: "column", alignItems: "center",
              ...rise(appear(t, at[i] ?? 0, 0.9)) }}><Bi s={text} size={size} zh={zh} en={en} /></div>
          );
        })}
        {s.by ? <div style={{ marginTop: 46, color: GOLD, ...rise(appear(t, last + 0.8, 0.9)) }}><Bi s={s.by} size={30} zh={{ fontWeight: 300, letterSpacing: 2 }} /></div> : null}
        {s.compound ? <Compound at={last + 0.4} /> : null}
      </AbsoluteFill>
    </Dark>
  );
};

/** A line that grows slowly, then faster: knowledge compounding. */
const Compound: FC<{ at: number }> = ({ at }) => {
  const t = useT();
  const p = interpolate(t, [at, at + 3], [0, 1], { ...clamp, easing: ease });
  const pts = [...Array(61)].map((_, i) => { const x = i / 60; return [200 + x * 600, 200 - (Math.pow(1.9, x * 4) - 1) / (Math.pow(1.9, 4) - 1) * 170] as const; });
  const n = Math.max(2, Math.round(p * pts.length));
  return (
    <svg width={1000} height={230} viewBox="0 0 1000 230" style={{ marginTop: 40, opacity: Math.min(1, p * 3) }}>
      <path d={"M" + pts.slice(0, n).map(([x, y]) => `${x} ${y}`).join("L")} fill="none" stroke={EMBER} strokeWidth={6} strokeLinecap="round" />
      <path d="M200 205H820" stroke={GREY} strokeWidth={2} />
    </svg>
  );
};

/** Income over time: three countries climb out of poverty and flatten under a dashed ceiling. */
const Curve: FC<{ dur: number }> = ({ dur }) => {
  const t = useT();
  const X0 = 300, X1 = 1640, Y0 = 860, CEIL = 430;
  const curve = (k: number) => [...Array(81)].map((_, i) => {
    const x = i / 80;
    const y = Y0 - (Y0 - CEIL - 26 - k * 22) * (1 - Math.exp(-5.5 * x));
    return [X0 + x * (X1 - X0), y] as const;
  });
  const draw = (k: number) => {
    const p = interpolate(t, [0.6 + k * 0.5, 3.6 + k * 0.5], [0, 1], { ...clamp, easing: ease });
    const pts = curve(k).slice(0, Math.max(2, Math.round(p * 81)));
    return "M" + pts.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join("L");
  };
  const ceil = appear(t, 2.6, 1.0);
  const label = (x: number, y: number, text: string, o: number, color = MUTED) => (
    <g opacity={o} fontFamily={SERIF} fill={color}>
      <text x={x} y={y} fontSize={34} letterSpacing={3}>{bi(text)[0]}</text>
      <text x={x} y={y + 30} fontSize={21} fontWeight={300}>{bi(text)[1]}</text>
    </g>
  );
  const pulse = 0.6 + 0.4 * Math.sin(t * 2.4);
  return (
    <Dark>
      <svg width={1920} height={1080} viewBox="0 0 1920 1080">
        <path d={`M${X0} ${Y0}H${X1}M${X0} ${Y0}V300`} stroke={GREY} strokeWidth={2} />
        {label(X0 - 160, Y0 - 6, "贫穷|Poor", appear(t, 0.2))}
        {label(X0 - 210, CEIL + 120, "中等收入|Middle income", appear(t, 1.6))}
        {label(X1 - 70, Y0 + 56, "时间|Time", appear(t, 0.2))}
        {[2, 1, 0].map((k) => <path key={k} d={draw(k)} fill="none" stroke={k === 0 ? EMBER : SOFT} strokeOpacity={k === 0 ? 1 : 0.55} strokeWidth={5} strokeLinecap="round" />)}
        <path d={`M${X0} ${CEIL}H${X1}`} stroke={GOLD} strokeWidth={4} strokeDasharray="18 14" opacity={ceil * (dur > 6 ? pulse : 1)} />
        {label(X1 - 300, CEIL - 54, "看不见的天花板|the invisible ceiling", ceil, GOLD)}
      </svg>
    </Dark>
  );
};

const Words: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const at = s.itemsAt ?? [];
  return (
    <Dark>
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 120, paddingBottom: 80 }}>
        {(s.items as string[]).map((w, i) => (
          <div key={w} style={{ fontFamily: SERIF, textAlign: "center", ...rise(appear(t, at[i] ?? 0, 0.6)) }}>
            <Bi s={w} size={130} color={i === (s.items as string[]).length - 1 ? GOLD : PAPER} zh={{ letterSpacing: 8 }} en={{ color: SOFT }} />
          </div>
        ))}
      </AbsoluteFill>
    </Dark>
  );
};

const Nums: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const at = s.itemsAt ?? [];
  const items = s.items as [string, string][];
  return (
    <Dark>
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: items.length > 2 ? 130 : 200, paddingBottom: 90 }}>
        {items.map(([v, sub], i) => (
          <div key={v} style={{ display: "flex", flexDirection: "column", alignItems: "center", fontFamily: SERIF, ...rise(appear(t, at[i] ?? 0, 0.9)) }}>
            <Bi s={v} size={bi(v)[0].length > 5 ? 100 : 150} color={i === items.length - 1 ? GOLD : "#fff"} zh={{ fontWeight: 300, letterSpacing: 2, lineHeight: 1.1 }} en={{ color: SOFT, marginTop: 4 }} />
            <div style={{ marginTop: 22, color: SOFT, maxWidth: items.length > 1 ? 720 : 1500, textAlign: "center" }}>
              <Bi s={sub} size={38} zh={{ fontWeight: 300, letterSpacing: 3 }} en={{ color: MUTED }} />
            </div>
          </div>
        ))}
      </AbsoluteFill>
    </Dark>
  );
};

const ChipGroups: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const notesAt = s.notesAt ?? [];
  const many = (s.groups ?? []).reduce((n, g) => n + g.items.length, 0) > 4;
  const chips = (
    <div key="chips" style={{ display: "flex", gap: many ? 60 : 90, alignItems: "center" }}>
      {(s.groups ?? []).map((g, gi) => (
        <div key={gi} style={{ display: "flex", gap: 26, ...rise(appear(t, 0.3 + gi * 0.8, 0.8)) }}>
          {g.items.map((c) => (
            <div key={c} style={{ padding: many ? "14px 34px" : "18px 44px", borderRadius: 16, textAlign: "center",
              color: g.tone === "gold" ? "#16120d" : PAPER, background: g.tone === "gold" ? GOLD : "rgba(93,102,110,.55)" }}>
              <Bi s={c} size={many ? 56 : 66} zh={{ letterSpacing: 6 }} en={{ marginTop: 4 }} />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
  const notes = (s.notes ?? []).map((n, i) => (
    <div key={`n${i}`} style={{ color: i === 0 ? SOFT : GOLD, marginTop: s.notesFirst ? 0 : i === 0 ? 70 : 26, marginBottom: s.notesFirst ? 60 : 0,
      textAlign: "center", ...rise(appear(t, notesAt[i] ?? 0, 0.9)) }}>
      <Bi s={n} size={44} zh={{ fontWeight: 300, letterSpacing: 3 }} en={{ color: i === 0 ? MUTED : SOFT }} />
    </div>
  ));
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, paddingBottom: 90 }}>
        {s.notesFirst ? [...notes, chips] : [chips, ...notes]}
      </AbsoluteFill>
    </Dark>
  );
};

/** Hanushek & Woessmann, as a sketch: years in school look alike; what was learned does not. Not to scale. */
const Bars: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const drop = interpolate(t, [s.dropAt ?? 4, (s.dropAt ?? 4) + 1.4], [0, 1], { ...clamp, easing: ease });
  const groups: [string, number, number, number][] = [["上了几年学|Years in school", 0.82, 0.76, 0.6], ["学会了多少|What was learned", 0.8, 0.8 - 0.42 * drop, 2.2]];
  const H = 420, BASE = 820;
  return (
    <Dark>
      <svg width={1920} height={1080} viewBox="0 0 1920 1080">
        {groups.map(([name, a, b, at], gi) => {
          const o = appear(t, at, 0.9);
          const x = 560 + gi * 560;
          return (
            <g key={name} opacity={o}>
              <rect x={x} y={BASE - H * a * o} width={130} height={H * a * o} fill={GOLD} rx={6} />
              <rect x={x + 160} y={BASE - H * b * o} width={130} height={H * b * o} fill={GREY} rx={6} />
              <text x={x + 145} y={BASE + 70} textAnchor="middle" fill={PAPER} fontFamily={SERIF} fontSize={42} letterSpacing={3}>{bi(name)[0]}</text>
              <text x={x + 145} y={BASE + 110} textAnchor="middle" fill={SOFT} fontFamily={SERIF} fontSize={27} fontWeight={300}>{bi(name)[1]}</text>
            </g>
          );
        })}
        <path d={`M470 ${BASE}H1450`} stroke={GREY} strokeWidth={2} />
        <g opacity={appear(t, 1.2)} fontFamily={SERIF} fontSize={30} letterSpacing={2}>
          <rect x={1520} y={360} width={30} height={30} fill={GOLD} rx={4} /><text x={1566} y={386} fill={SOFT}>东亚 <tspan fontSize={21} fontWeight={300}>East Asia</tspan></text>
          <rect x={1520} y={420} width={30} height={30} fill={GREY} rx={4} /><text x={1566} y={446} fill={SOFT}>拉美 <tspan fontSize={21} fontWeight={300}>Latin America</tspan></text>
          <text x={1520} y={520} fill={MUTED} fontSize={24}>示意图 <tspan fontSize={18} fontWeight={300}>sketch, not to scale</tspan></text>
        </g>
      </svg>
    </Dark>
  );
};

/** The incubation experiment, as a sketch: the easy, mind-wandering break gives more ideas afterwards. */
const Ideas: FC = () => {
  const t = useT();
  const col = (x: number, title: string, bulbs: number, gold: boolean, at: number) => (
    <div style={{ position: "absolute", left: x, top: 220, width: 620, textAlign: "center", fontFamily: SERIF, ...rise(appear(t, at, 0.8)) }}>
      <Bi s={title} size={46} color={gold ? GOLD : SOFT} zh={{ letterSpacing: 4 }} />
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 18, marginTop: 70, width: 620 }}>
        {[...Array(bulbs)].map((_, i) => (
          <div key={i} style={{ opacity: appear(t, at + 3.5 + i * 0.35, 0.4) }}><Icon name="bulb" size={96} color={gold ? GOLD : MUTED} /></div>
        ))}
      </div>
    </div>
  );
  return (
    <Dark>
      {col(280, "休息时：轻松、容易走神|Break: something easy, mind wandering", 7, true, 0.4)}
      {col(1020, "休息时：费脑子的事|Break: something demanding", 3, false, 1.2)}
      <div style={{ position: "absolute", left: 0, right: 0, top: 790, textAlign: "center", fontFamily: SERIF, color: MUTED, opacity: appear(t, 4) }}>
        <Bi s="回来再做创造性的题目，想出的点子 · 示意图|Ideas on the creative task afterwards · a sketch" size={26} zh={{ letterSpacing: 2 }} />
      </div>
    </Dark>
  );
};

const Icons: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const at = s.itemsAt ?? [];
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, paddingBottom: 90 }}>
        <div style={{ textAlign: "center", ...rise(appear(t, 0.2)) }}><Bi s={s.head ?? ""} size={48} color={GOLD} zh={{ letterSpacing: 8 }} /></div>
        <div style={{ display: "flex", gap: 110, marginTop: 80 }}>
          {(s.items as [string, string][]).map(([icon, text], i) => (
            <div key={text} style={{ display: "flex", flexDirection: "column", alignItems: "center", ...rise(appear(t, at[i] ?? 0, 0.8)) }}>
              <Icon name={icon} size={140} color={i === 0 ? EMBER : SOFT} />
              <div style={{ marginTop: 26, textAlign: "center", maxWidth: 330 }}><Bi s={text} size={38} color={PAPER} zh={{ fontWeight: 300, letterSpacing: 3 }} en={{ color: SOFT }} /></div>
            </div>
          ))}
        </div>
      </AbsoluteFill>
    </Dark>
  );
};

/** 1914, Buenos Aires and Chicago (Campante & Glaeser 2009): one road for the same trade, then two. A sketch, not data. */
const Cities: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const split = interpolate(t, [s.splitAt ?? 5, (s.splitAt ?? 5) + 2.5], [0, 1], { ...clamp, easing: ease });
  const road = interpolate(t, [0.8, 2.6], [0, 1], { ...clamp, easing: ease });
  const X0 = 360, XS = 980, X1 = 1500, Y = 640;
  const branch = (dy: number) => `M${XS} ${Y} C ${XS + 200} ${Y}, ${XS + 260} ${Y + dy * 0.6}, ${XS + (X1 - XS) * split} ${Y + dy * split}`;
  return (
    <Dark>
      <svg width={1920} height={1080} viewBox="0 0 1920 1080">
        <text x={960} y={190} textAnchor="middle" fill={GOLD} fontFamily={SERIF} fontSize={46} letterSpacing={8} opacity={appear(t, 0.2)}>1914</text>
        <path d={`M${X0} ${Y}H${X0 + (XS - X0) * road}`} stroke={SOFT} strokeWidth={8} strokeLinecap="round" />
        <foreignObject x={X0 + 60} y={Y - 200} width={520} height={150} opacity={appear(t, 1.0)}>
          <div style={{ display: "flex", justifyContent: "center", gap: 36 }}>
            <Icon name="wheat" size={110} color={SOFT} /><Icon name="ship" size={110} color={SOFT} />
          </div>
        </foreignObject>
        <g opacity={appear(t, 1.4)} fontFamily={SERIF} fill={MUTED} textAnchor="middle">
          <text x={(X0 + XS) / 2} y={Y + 70} fontSize={30} letterSpacing={3}>同一门生意：把内陆的肉和粮食运出去</text>
          <text x={(X0 + XS) / 2} y={Y + 104} fontSize={21} fontWeight={300}>The same trade: shipping meat and grain from the interior</text>
        </g>
        <path d={branch(-260)} fill="none" stroke={GOLD} strokeWidth={8} strokeLinecap="round" opacity={split} />
        <path d={branch(60)} fill="none" stroke={GREY} strokeWidth={8} strokeLinecap="round" opacity={split} />
        <g opacity={appear(t, (s.splitAt ?? 5) + 1.5)} fontFamily={SERIF}>
          <text x={X1 + 30} y={Y - 250} fill={GOLD} fontSize={48} letterSpacing={4}>芝加哥</text>
          <text x={X1 + 30} y={Y - 214} fill={GOLD} fontSize={28} fontWeight={300}>Chicago</text>
          <text x={X1 + 30} y={Y + 76} fill={SOFT} fontSize={48} letterSpacing={4}>布宜诺斯艾利斯</text>
          <text x={X1 + 30} y={Y + 112} fill={SOFT} fontSize={28} fontWeight={300}>Buenos Aires</text>
        </g>
        <g opacity={appear(t, s.noteAt ?? 9, 1)} fontFamily={SERIF} fill={GOLD} textAnchor="middle">
          <text x={960} y={880} fontSize={48} letterSpacing={4}>最大的差别：人的教育</text>
          <text x={960} y={918} fontSize={29} fontWeight={300} fill={SOFT}>The biggest difference: people's education</text>
        </g>
      </svg>
    </Dark>
  );
};

/** sc07-01～05, the recap (v0.5): each chapter with what it found, lit in turn as the narration walks through them. */
const Recap: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const at = s.itemsAt ?? [];
  const rows = s.items as [string, string][];
  const now = at.filter((a) => t >= a).length - 1;
  return (
    <Dark>
      <div style={{ position: "absolute", left: 200, right: 160, top: 70, fontFamily: SERIF, opacity: appear(t, CARD - 0.3, 0.8) }}>
        {rows.map(([name, said], i) => {
          const o = appear(t, at[i] ?? 0, 0.7);
          const on = i === now;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", height: 118, opacity: 0.25 + 0.75 * o * (on ? 1 : 0.62),
              transform: `translateX(${(1 - o) * 24}px)` }}>
              <div style={{ width: 420, color: on ? GOLD : MUTED }}><Bi s={name} size={34} zh={{ letterSpacing: 3 }} /></div>
              <div style={{ width: 4, height: 70, background: on ? EMBER : GREY, marginRight: 40, borderRadius: 2 }} />
              <div style={{ color: on ? PAPER : SOFT }}><Bi s={said} size={40} zh={{ letterSpacing: 2 }} en={{ color: on ? SOFT : MUTED }} /></div>
            </div>
          );
        })}
      </div>
    </Dark>
  );
};

/** sc02-07 「可以点击右上角，看我们另一个视频」: YouTube's card teaser opens in the top-right corner, so the arrow points
 * at the corner and the other episode's cover sits a little inside it, never under the teaser. */
const Promo: FC<{ title: string; at: number[] }> = ({ title, at }) => {
  const t = useT();
  const [a, b] = at;
  const o = interpolate(t, [a, a + 0.6, b - 0.5, b], [0, 1, 1, 0], clamp);
  const nudge = Math.sin(t * 5) * 6;
  return (
    <div style={{ position: "absolute", inset: 0, opacity: o, pointerEvents: "none" }}>
      <div style={{ position: "absolute", right: 250, top: 190, width: 400, background: "rgba(10,12,15,.78)", borderRadius: 16, padding: 16,
        boxShadow: "0 20px 50px rgba(0,0,0,.6)", border: "1px solid rgba(201,164,90,.45)", fontFamily: SERIF, textAlign: "center" }}>
        <Img src={file("art/promo-icepop.jpg")} style={{ width: 368, borderRadius: 8, display: "block" }} />
        <div style={{ marginTop: 12, color: PAPER }}><Bi s={title} size={30} zh={{ letterSpacing: 2 }} en={{ color: SOFT }} /></div>
        <div style={{ marginTop: 10, color: GOLD }}><Bi s="点右上角，看这一集|Tap the top-right corner to watch" size={24} /></div>
      </div>
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
        <g transform={`translate(${nudge} ${-nudge})`}>
          <path d="M 1680 200 C 1760 170, 1810 120, 1840 64" fill="none" stroke="rgba(0,0,0,.55)" strokeWidth={14} strokeLinecap="round" />
          <path d="M 1680 200 C 1760 170, 1810 120, 1840 64" fill="none" stroke={GOLD} strokeWidth={8} strokeLinecap="round" />
          <path d="M 1812 70 L 1852 44 L 1858 92 Z" fill={GOLD} stroke="rgba(0,0,0,.55)" strokeWidth={3} strokeLinejoin="round" />
        </g>
      </svg>
    </div>
  );
};

const End: FC = () => {
  const t = useT();
  const credit: CSSProperties = { fontSize: 20, fontWeight: 300, color: MUTED, lineHeight: 1.8, letterSpacing: 0.3 };
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, color: "#fff", textAlign: "center", paddingBottom: 60 }}>
        <div style={{ fontSize: 60, fontWeight: 400, opacity: appear(t, 0.3), letterSpacing: 8 }}>从新闻看教育</div>
        <div style={{ fontSize: 34, fontWeight: 300, opacity: appear(t, 0.5), color: SOFT, marginTop: 8 }}>Lessons from the Headlines</div>
        <div style={{ fontSize: 32, fontWeight: 300, marginTop: 20, opacity: appear(t, 0.7), color: SOFT, letterSpacing: 3 }}>Yancy Qin | Lucas Academy</div>
        <div style={{ marginTop: 64, opacity: appear(t, 1.4), maxWidth: 1800, ...credit }}>
          李录对谈 Li Lu talk：Columbia Business School, 36th Annual Graham &amp; Dodd Event with Li Lu ’96, 2026-10-05<br />
          中文字幕用哥大官方中文翻译 · Chinese subtitles: CBS's official translation<br />
          马丁·路德·金照片 Photo of Martin Luther King Jr.：O. Fernandez, New York World-Telegram and the Sun，美国国会图书馆藏 Library of Congress，公有领域 public domain<br />
          插图：AI 生成（Codex），不是照片，也不是任何人的原作 · Illustrations: AI-generated (Codex), not photos or anyone's original work<br />
          音乐 Music：Satie, Gymnopédie No. 1 · Kevin MacLeod (incompetech.com), CC BY 3.0；Bach, Air · U.S. Air Force Strings，公有领域 public domain；<br />
          Bach, Jesu, Joy of Man’s Desiring · Gli Armonici, CC0<br />
          配音：Yancy 本人的克隆声音 · Voice: Yancy's own voice, synthesized
        </div>
      </AbsoluteFill>
    </Dark>
  );
};

/** Every chapter opens with its card, briefly (Yancy, 2026-10-26: 章节卡可以简短一下，要中英文): part number, the
 * Chinese name, the English name under it, about 2.5 s over whatever the chapter opens on. Text cards that open a
 * chapter (sc03-01, sc04-01, sc05-01, the recap) bring their own words in after it. `p` is seconds since the card. */
const ChapterCard: FC<{ index: number; name: string; en?: string; p: number }> = ({ index, name, en, p }) => {
  const o = interpolate(p, [0.15, 0.55, CARD - 0.5, CARD], [0, 1, 1, 0], clamp);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", pointerEvents: "none", opacity: o, paddingBottom: 60 }}>
      <div style={{ background: "rgba(10,12,15,.72)", borderRadius: 18, padding: "20px 64px 24px", textAlign: "center", fontFamily: SERIF,
        border: "1px solid rgba(201,164,90,.35)", transform: `translateY(${(1 - o) * 12}px)` }}>
        <div style={{ fontSize: 26, fontWeight: 300, color: GOLD, letterSpacing: 4 }}>第 {index + 1} 段 · Part {index + 1}</div>
        <div style={{ fontSize: 68, color: PAPER, letterSpacing: 8, marginTop: 8 }}>{name}</div>
        {en ? <div style={{ fontSize: 38, fontWeight: 300, color: SOFT, marginTop: 4 }}>{en}</div> : null}
      </div>
    </AbsoluteFill>
  );
};

const ShotView: FC<{ s: Shot; dur: number }> = ({ s, dur }) => {
  switch (s.k) {
    case "title": return <Title s={s} />;
    case "art": return <Art s={s} dur={dur} />;
    case "still": return <Still s={s} dur={dur} />;
    case "clip": return <Clip s={s} />;
    case "photo": return <Photo s={s} dur={dur} />;
    case "quote": return <Quote s={s} />;
    case "curve": return <Curve dur={dur} />;
    case "words": return <Words s={s} />;
    case "nums": return <Nums s={s} />;
    case "chips": return <ChipGroups s={s} />;
    case "bars": return <Bars s={s} />;
    case "ideas": return <Ideas />;
    case "icons": return <Icons s={s} />;
    case "cities": return <Cities s={s} />;
    case "recap": return <Recap s={s} />;
    case "end": return <End />;
    default: return <Dark><div style={{ color: "#fff", fontSize: 60, margin: "auto" }}>{s.k}</div></Dark>;
  }
};

/** Words laid over a picture shot (art or still). */
const Overlays: FC<{ s: Shot }> = ({ s }) => (
  <>
    {s.items && !["words", "nums", "icons", "recap"].includes(s.k) ? <Chips items={s.items as string[]} at={s.itemsAt ?? []} big={s.k === "still"} /> : null}
    {s.big ? <Big text={s.big} at={s.bigAt ?? 0} /> : null}
    {s.line ? <QuoteLine text={s.line} by={s.lineBy} at={s.lineAt ?? 0} /> : null}
    {s.num ? <Num value={s.num} sub={s.sub} at={s.numAt ?? 0} /> : null}
    {s.label && s.k === "art" ? <Label text={s.label} /> : null}
    {s.cite ? <Label text={s.cite} /> : null}
    {s.promo ? <Promo title={s.promo} at={s.promoAt ?? [0, 5]} /> : null}
  </>
);

const Faded: FC<{ first: boolean; children: ReactNode }> = ({ first, children }) => {
  const t = useT();
  const o = first ? interpolate(t, [0, 1.2], [0, 1], clamp) : interpolate(t, [0, FADE], [0, 1], clamp);
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};

export const MiddleIncomeTrapVideo: FC<MitProps> = ({ tl }) => {
  useFonts();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!tl) return <AbsoluteFill style={{ background: INK }} />;
  const t = frame / fps;
  const title = tl.shots[0];
  const skip = tl.shots.find((s) => s.skip);
  const onSkip = skip && t >= skip.start + 0.2 && t < skip.end;
  const skipO = skip ? interpolate(t, [skip.start + 0.2, skip.start + 0.8, skip.end - 0.6, skip.end], [0, 1, 1, 0], clamp) : 0;
  const arc: Skip | null = onSkip && skip
    ? { from: 1, to: 2, opacity: skipO, draw: interpolate(t, [skip.start + 0.5, skip.start + 2.3], [0, 1], { ...clamp, easing: ease }) } : null;
  // the bar's "jump to any part" hint: at the title, and again where Yancy says so (sc00-02, v0.6)
  const again = tl.shots.find((s) => s.barHintAt);
  const [ha, hb] = again ? again.barHintAt!.map((x) => again.start + x) : [-10, -9];
  const hint = Math.max(interpolate(t, [0.4, 1.2, title.end + 2.0, title.end + 2.8], [0, 1, 1, 0], clamp),
    interpolate(t, [ha, ha + 0.6, hb - 0.6, hb], [0, 1, 1, 0], clamp));
  // the first chapter's card comes after the title card
  const cardAt = tl.chapters.map((c, i) => (i === 0 ? tl.shots[1].start : c.start));
  const card = cardAt.findIndex((a) => t >= a && t < a + CARD);
  return (
    <AbsoluteFill style={{ background: INK }}>
      {tl.shots.map((s, i) => {
        const from = Math.round(s.start * fps);
        const dur = s.end - s.start;
        const len = Math.max(1, Math.round((dur + (i + 1 < tl.shots.length ? FADE : 0)) * fps));
        return (
          <Sequence key={i} from={from} durationInFrames={len}>
            <Faded first={i === 0}>
              <ShotView s={s} dur={dur} />
              <Overlays s={s} />
            </Faded>
          </Sequence>
        );
      })}
      {card >= 0 ? <ChapterCard index={card} name={tl.chapters[card].name} en={tl.chapters[card].en} p={t - cardAt[card]} /> : null}
      {/* sc00-09: the picture steps back so the arc over the bar is the thing to look at */}
      <AbsoluteFill style={{ background: "rgba(8,10,13,.5)", opacity: skipO, pointerEvents: "none" }} />
      {t < tl.durationSeconds - 9 ? (
        <ChapterBar chapters={tl.chapters} duration={tl.durationSeconds} t={t} hint={hint} skip={arc} />
      ) : null}
    </AbsoluteFill>
  );
};
