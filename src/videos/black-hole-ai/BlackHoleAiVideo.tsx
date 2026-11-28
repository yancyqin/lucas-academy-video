// "We Build A BlackHole with AI" (BLACK-HOLE-AI.md). One picture, English first, with a Chinese audio track (the
// render mutes the picture and muxes both mixes; `track` only chooses what the studio preview plays).
// Everything is laid out by scripts/black-hole-ai/build_timeline.py in public/black-hole-ai/timeline.json:
//   shots     picture layers on an integer frame map (footage plays at 1x from `fromFrame`; no slow motion, no
//             repeated frames), stills with a slow push-in, and full-frame cards; each fades in over the one before
//   overlays  the title, the three reference cards, the outcome legend, the CPU-check card and the end card
// On screen English leads and Chinese follows in small type; nothing important sits in the bottom caption band
// (captions are separate SRTs, never burned in) except the thin chapter bar, segmented like the YouTube chapters.
import type { CSSProperties, FC, ReactNode } from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  type CalculateMetadataFunction,
} from "remotion";
import { QR_ROWS, SITE } from "./qr";

type Lang = "en" | "zh";
type Span = { start: number; end: number };
type Cue = { id: string; section: string; en: string; zh: string; start: number; end: number; speech: Span; speeches: Record<Lang, Span> };
type Section = { id: string; en: string; zh: string; start: number; end: number };
type Shot = {
  id: string;
  kind: "footage" | "still" | "card";
  clip?: string;
  image?: string;
  card?: string;
  startFrame: number;
  endFrame: number;
  fromFrame?: number;
  fadeIn?: number;
  gain?: number;
  dim?: number;
  push?: number;
  focus?: [number, number];
  label?: string;
  steps?: number[];
};
type Overlay = { kind: string; start: number; end: number };
export type BlackHoleTimeline = {
  fps: number;
  durationSeconds: number;
  durationInFrames: number;
  draft: boolean;
  title: string;
  byline: string;
  sections: Section[];
  cues: Cue[];
  shots: Shot[];
  overlays: Overlay[];
  fadeOut: number;
  d3Gain: number;
  marks: Record<string, number>;
};
export type BlackHoleProps = { tl?: BlackHoleTimeline | null; track?: Lang };

const DIR = "black-hole-ai";
const file = (p: string) => staticFile(`${DIR}/${p}`);

// The space palette: near-black, white type, a warm amber accent.
export const NIGHT = "#05060a",
  INK = "#f6f3ec",
  MUTED = "#aaa59b",
  AMBER = "#f2b45a",
  AMBER_SOFT = "rgba(242, 180, 90, 0.85)",
  LINE = "rgba(242, 222, 190, 0.18)",
  PANEL = "rgba(7, 8, 13, 0.80)";
export const EN = '"Avenir Next", "Helvetica Neue", sans-serif';
export const ZH = '"PingFang SC", "Hiragino Sans GB", sans-serif';
export const MONO = '"SF Mono", Menlo, monospace';
const SAFE_BOTTOM = 160; // the captions' band: nothing important below this (but the chapter bar)

const ease = (x: number) => {
  const t = Math.max(0, Math.min(1, x));
  return t * t * (3 - 2 * t);
};
const rise = (t: number, a: number, b: number) => ease((t - a) / Math.max(0.001, b - a));
/** In over `inn` s from a, out over `out` s before b. */
const window_ = (t: number, a: number, b: number, inn = 0.5, out = 0.4) => Math.min(rise(t, a, a + inn), 1 - rise(t, b - out, b));

export const calculateBlackHoleMetadata: CalculateMetadataFunction<BlackHoleProps> = async ({ props, abortSignal }) => {
  const response = await fetch(file("timeline.json"), { signal: abortSignal });
  if (!response.ok) throw Error("Run scripts/black-hole-ai/build_timeline.py first");
  const tl = (await response.json()) as BlackHoleTimeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: tl.durationInFrames };
};

// ------------------------------------------------------------------ type

const Bi: FC<{ en: ReactNode; zh?: ReactNode; size: number; color?: string; zhColor?: string; weight?: number; align?: CSSProperties["textAlign"]; style?: CSSProperties }> = ({
  en,
  zh,
  size,
  color = INK,
  zhColor = MUTED,
  weight = 700,
  align = "left",
  style,
}) => (
  <div style={{ textAlign: align, ...style }}>
    <div style={{ fontFamily: EN, fontSize: size, fontWeight: weight, color, lineHeight: 1.18 }}>{en}</div>
    {zh && <div style={{ fontFamily: ZH, fontSize: Math.round(size * 0.58), fontWeight: 500, color: zhColor, marginTop: size * 0.16, lineHeight: 1.3 }}>{zh}</div>}
  </div>
);

const Panel: FC<{ children: ReactNode; style?: CSSProperties }> = ({ children, style }) => (
  <div style={{ background: PANEL, border: `1px solid ${LINE}`, borderRadius: 22, padding: "26px 34px", boxShadow: "0 18px 60px rgba(0,0,0,.45)", ...style }}>{children}</div>
);

// ------------------------------------------------------------------ backgrounds

/** A quiet star field for the cards: fixed stars drifting very slowly, so a card is never a frozen frame. */
const STARS = (() => {
  let s = 1126;
  const rnd = () => {
    s = (s * 16807) % 2147483647;
    return s / 2147483647;
  };
  return Array.from({ length: 260 }, () => ({ x: rnd() * 2100 - 90, y: rnd() * 1080, r: 0.6 + rnd() * rnd() * 2.2, a: 0.25 + rnd() * 0.6, d: 0.4 + rnd() }));
})();
const StarField: FC<{ t: number }> = ({ t }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse at 70% 40%, #121420 0%, ${NIGHT} 70%)` }}>
    <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
      {STARS.map((st, i) => (
        <circle key={i} cx={((st.x - t * 7 * st.d) % 2100 + 2100) % 2100 - 90} cy={st.y} r={st.r} fill="#fff" opacity={st.a} />
      ))}
    </svg>
  </AbsoluteFill>
);

// ------------------------------------------------------------------ shots

const ShotLayer: FC<{ shot: Shot; tl: BlackHoleTimeline }> = ({ shot, tl }) => {
  const frame = useCurrentFrame(); // relative to the shot's Sequence
  const t = frame / tl.fps;
  const length = (shot.endFrame - shot.startFrame) / tl.fps;
  const opacity = shot.fadeIn ? ease(t / shot.fadeIn) : 1;
  let body: ReactNode = null;
  if (shot.kind === "footage") {
    body = (
      <>
        <OffthreadVideo
          src={file(`footage/${shot.clip}.mp4`)}
          muted
          trimBefore={shot.fromFrame ?? 0}
          style={{ width: "100%", height: "100%", filter: shot.gain && shot.gain !== 1 ? `brightness(${shot.gain})` : undefined }}
        />
        {shot.dim ? <AbsoluteFill style={{ background: NIGHT, opacity: shot.dim }} /> : null}
      </>
    );
  } else if (shot.kind === "still") {
    const [fx, fy] = shot.focus ?? [960, 540];
    const scale = 1 + (shot.push ?? 0) * (t / length);
    body = (
      <AbsoluteFill style={{ transform: `scale(${scale})`, transformOrigin: `${fx}px ${fy}px` }}>
        <Img src={file(`stills/${shot.image}.png`)} style={{ width: 1920, height: 1080 }} />
      </AbsoluteFill>
    );
  } else if (shot.card === "plan") {
    body = <PlanCard t={t} steps={(shot.steps ?? []).map((s) => s - shot.startFrame / tl.fps)} />;
  } else if (shot.card === "code") {
    body = <CodeCard t={t} />;
  } else if (shot.card === "shadow-edge") {
    body = <ShadowEdgeCard t={t} />;
  }
  return <AbsoluteFill style={{ opacity }}>{body}</AbsoluteFill>;
};

// ------------------------------------------------------------------ cards

const PLAN: [string, string][] = [
  ["the shape of space (Kerr metric)", "空间的形状（克尔度规）"],
  ["a step-by-step solver for each ray (Dormand–Prince)", "每一束光的逐步求解器（Dormand-Prince）"],
  ["a camera that can fall", "一台能掉进去的相机"],
  ["glowing gas, colour and Doppler shift", "发光的气体、颜色和多普勒频移"],
  ["the same code on the GPU, one ray per pixel", "同一份代码放到显卡上，每个像素一束光"],
  ["checks against an exact CPU version", "和精确的 CPU 版本对照检查"],
];

const PlanCard: FC<{ t: number; steps: number[] }> = ({ t, steps }) => (
  <AbsoluteFill>
    <StarField t={t} />
    <AbsoluteFill style={{ padding: "92px 0 0 190px" }}>
      <Bi en="The plan, in plain words" zh="用大白话写的计划" size={64} color={AMBER} weight={800} />
      <div style={{ marginTop: 46 }}>
        {PLAN.map(([en, zh], i) => {
          const at = steps[i] ?? 0.4 + i * 0.8;
          const o = rise(t, at, at + 0.6);
          return (
            <div key={en} style={{ display: "flex", alignItems: "baseline", gap: 30, marginBottom: 22, opacity: o, transform: `translateY(${(1 - o) * 14}px)` }}>
              <div style={{ fontFamily: MONO, fontSize: 34, color: AMBER, width: 44, textAlign: "right" }}>{i + 1}</div>
              <Bi en={en} zh={zh} size={42} weight={600} />
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  </AbsoluteFill>
);

// inception-space-ui src/inception/world/blackHole/kerr.js, condensed (the card says so).
const CODE = `export function kerrSchild(x, y, z, a) {
  const r = kerrRadius(x, y, z, a);
  const s = r ** 4 + a * a * z * z;
  const f = (2 * r ** 3) / s;
  const lx = (r * x + a * y) / (r * r + a * a);
  const ly = (r * y - a * x) / (r * r + a * a);
  const lz = z / r;
  return { r, f, lx, ly, lz };
}`;
const KEYWORDS = new Set(["export", "function", "const", "return"]);
const CodeLine: FC<{ line: string }> = ({ line }) => {
  const parts = line.split(/(\b[A-Za-z_]\w*\b|\d+|\*\*|[(){};,=+\-*/])/).filter((p) => p !== "");
  return (
    <div style={{ whiteSpace: "pre" }}>
      {parts.map((p, i) => {
        const color = KEYWORDS.has(p) ? AMBER : /^\d+$/.test(p) ? "#9fc7ff" : p === "kerrSchild" || p === "kerrRadius" ? "#ffd9a0" : /^[A-Za-z_]/.test(p) ? INK : MUTED;
        return (
          <span key={i} style={{ color, fontWeight: KEYWORDS.has(p) ? 700 : 500 }}>
            {p}
          </span>
        );
      })}
    </div>
  );
};
const CodeCard: FC<{ t: number }> = ({ t }) => {
  const lines = CODE.split("\n");
  return (
    <AbsoluteFill>
      <StarField t={t} />
      <AbsoluteFill style={{ padding: "84px 0 0 170px" }}>
        <Bi en="Kerr metric · adaptive Dormand–Prince solver" zh="克尔度规 · 自适应 Dormand-Prince 求解器" size={54} color={AMBER} weight={800} />
        <Panel style={{ marginTop: 44, width: 1480, padding: "34px 44px" }}>
          <div style={{ fontFamily: MONO, fontSize: 36, lineHeight: 1.55 }}>
            {lines.map((line, i) => {
              const o = rise(t, 0.5 + i * 0.32, 0.9 + i * 0.32);
              return (
                <div key={i} style={{ opacity: o }}>
                  <CodeLine line={line} />
                </div>
              );
            })}
          </div>
        </Panel>
        <div style={{ marginTop: 22, opacity: rise(t, 3.6, 4.4) }}>
          <span style={{ fontFamily: EN, fontSize: 28, color: MUTED }}>simplified from </span>
          <span style={{ fontFamily: MONO, fontSize: 26, color: INK }}>kerr.js</span>
          <span style={{ fontFamily: EN, fontSize: 24, color: MUTED }}> · inception-space-ui/src/inception/world/blackHole/</span>
          <div style={{ fontFamily: ZH, fontSize: 22, color: MUTED, marginTop: 6 }}>由 kerr.js 简化而来</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** The shadow test, as a diagram: the ray-traced edge sits on the theory's ring (the critical impact parameter). */
const ShadowEdgeCard: FC<{ t: number }> = ({ t }) => {
  const cx = 470,
    cy = 520,
    R = 230;
  const ring = rise(t, 0.4, 2.0);
  const dots = 36;
  return (
    <AbsoluteFill>
      <StarField t={t} />
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        <circle cx={cx} cy={cy} r={R + 160} fill="#1d2027" opacity={0.9} />
        <circle cx={cx} cy={cy} r={R} fill="#000" />
        <circle cx={cx} cy={cy} r={R} fill="none" stroke={AMBER} strokeWidth={5} strokeDasharray={`${2 * Math.PI * R * ring} ${2 * Math.PI * R}`} transform={`rotate(-90 ${cx} ${cy})`} />
        {Array.from({ length: dots }, (_, i) => {
          const a = (i / dots) * Math.PI * 2;
          const o = rise(t, 1.6 + i * 0.06, 1.9 + i * 0.06);
          return <circle key={i} cx={cx + R * Math.cos(a)} cy={cy + R * Math.sin(a)} r={7} fill="#ffffff" opacity={o} />;
        })}
      </svg>
      <div style={{ position: "absolute", left: 960, top: 230, width: 860 }}>
        <Bi en="Tested against the math" zh="用数学来检验" size={60} color={AMBER} weight={800} />
        <div style={{ marginTop: 44, opacity: rise(t, 1.0, 1.6), display: "flex", gap: 18, alignItems: "center" }}>
          <svg width={40} height={40}>
            <circle cx={20} cy={20} r={8} fill="#fff" />
          </svg>
          <Bi en="the shadow's edge, ray-traced" zh="光线追踪出来的阴影边缘" size={36} weight={600} />
        </div>
        <div style={{ marginTop: 22, opacity: rise(t, 0.4, 1.0), display: "flex", gap: 18, alignItems: "center" }}>
          <svg width={40} height={40}>
            <circle cx={20} cy={20} r={14} fill="none" stroke={AMBER} strokeWidth={5} />
          </svg>
          <Bi en="theory: the critical impact parameter" zh="理论：临界碰撞参数" size={36} weight={600} />
        </div>
        <div style={{ marginTop: 50, opacity: rise(t, 2.8, 3.6) }}>
          <Bi en={<>they agree to 1 part in 10<sup style={{ fontSize: "0.6em" }}>9</sup></>} zh="误差不到十亿分之一" size={56} weight={800} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ overlays

const REFS: Record<string, { en: ReactNode; zh: string }> = {
  "ref-svs13326": {
    en: <>NASA Goddard Scientific Visualization Studio — SVS 13326 (J. Schnittman): the colours of our gas</>,
    zh: "NASA 戈达德科学可视化工作室 SVS 13326：我们气体的颜色",
  },
  "ref-james2015": {
    en: (
      <>
        O. James, E. von Tunzelmann, P. Franklin, K. S. Thorne (2015), <i>Gravitational lensing by spinning black holes in astrophysics, and in the movie Interstellar</i>, Class.
        Quantum Grav. 32, 065001
      </>
    ),
    zh: "光怎么弯：基普·索恩与《星际穿越》特效团队的论文（2015）",
  },
  "ref-svs14576": {
    en: <>NASA Goddard visualization, 2024 — a plunge into a black hole (SVS 14576)</>,
    zh: "NASA 戈达德 2024 年的可视化：坠入黑洞（SVS 14576）",
  },
};
const RefCard: FC<{ t: number; o: Overlay }> = ({ t, o }) => {
  const ref = REFS[o.kind];
  const v = window_(t, o.start, o.end, 0.6, 0.45);
  return (
    <div style={{ position: "absolute", left: 64, top: 56, width: 900, opacity: v, transform: `translateY(${(1 - v) * -10}px)` }}>
      <Panel style={{ padding: "24px 32px" }}>
        <div style={{ fontFamily: EN, fontSize: 22, fontWeight: 800, letterSpacing: 3, color: AMBER }}>
          REFERENCE <span style={{ fontFamily: ZH, letterSpacing: 1, fontWeight: 600 }}>· 参考</span>
        </div>
        <div style={{ fontFamily: EN, fontSize: 31, fontWeight: 600, color: INK, lineHeight: 1.3, marginTop: 10 }}>{ref.en}</div>
        <div style={{ fontFamily: ZH, fontSize: 22, color: MUTED, marginTop: 10 }}>{ref.zh}</div>
      </Panel>
    </div>
  );
};

const TitleCard: FC<{ t: number; o: Overlay; tl: BlackHoleTimeline }> = ({ t, o, tl }) => {
  const v = window_(t, o.start, o.end, 0.7, 0.6);
  return (
    <AbsoluteFill style={{ opacity: v }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 30%, rgba(5,6,10,.72) 0%, rgba(5,6,10,.35) 45%, rgba(5,6,10,0) 75%)" }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: 170, textAlign: "center", transform: `scale(${0.98 + 0.02 * v})` }}>
        <div style={{ fontFamily: EN, fontSize: 104, fontWeight: 800, color: INK, letterSpacing: 1, textShadow: "0 6px 40px rgba(0,0,0,.8)" }}>
          We Build A <span style={{ color: AMBER }}>BlackHole</span> with AI
        </div>
        <div style={{ fontFamily: EN, fontSize: 38, fontWeight: 600, color: INK, opacity: 0.9, marginTop: 18, textShadow: "0 4px 24px rgba(0,0,0,.8)" }}>{tl.byline}</div>
      </div>
    </AbsoluteFill>
  );
};

const LEGEND: [string, string, string, string?][] = [
  ["#2e5fc8", "blue: escaped to the sky", "蓝：飞向了天空"],
  ["#000000", "black: fell into the horizon", "黑：掉进了视界"],
  ["#d3542a", "gold / orange-red: stopped in the gas", "金 / 橙红：停在了气体里"],
  ["#d23cd2", "magenta: out of budget — none", "品红：超出步数——没有", "none"],
];
const Legend: FC<{ t: number; o: Overlay }> = ({ t, o }) => {
  const v = window_(t, o.start, o.end, 0.5, 0.35);
  return (
    // Right side: on the page still the left is the study page's own control panel; on d2 the right is open sky.
    <div style={{ position: "absolute", right: 64, bottom: SAFE_BOTTOM + 30, opacity: v }}>
      <Panel style={{ padding: "20px 28px" }}>
        {LEGEND.map(([color, en, zh, none], i) => (
          <div key={en} style={{ display: "flex", alignItems: "center", gap: 18, marginTop: i ? 12 : 0, opacity: none ? 0.75 : 1 }}>
            <div style={{ width: 34, height: 34, borderRadius: 8, background: color, border: "2px solid rgba(255,255,255,.55)" }} />
            <div>
              <div style={{ fontFamily: EN, fontSize: 28, fontWeight: 600, color: INK }}>{en}</div>
              <div style={{ fontFamily: ZH, fontSize: 19, color: MUTED }}>{zh}</div>
            </div>
          </div>
        ))}
      </Panel>
    </div>
  );
};

const CpuCard: FC<{ t: number; o: Overlay }> = ({ t, o }) => {
  const v = window_(t, o.start, o.end, 0.6, 0.45);
  const rows: [string, string, string?][] = [
    ["outcome agrees on 100.00% of 2304 rays", "2304 束光的去向 100.00% 一致", "sky, horizon or gas · 天空、视界或气体"],
    ["frequency shift: mean Δ 4.31e-4", "频移：平均相差 4.31e-4"],
    ["no GPU ray ran out of budget", "没有一束显卡光线超出步数"],
  ];
  return (
    <div style={{ position: "absolute", right: 64, top: 150, width: 860, opacity: v, transform: `translateX(${(1 - v) * 20}px)` }}>
      <Panel style={{ padding: "30px 36px" }}>
        <Bi en="Checked against an exact CPU version" zh="和又慢又精确的 CPU 版本对照" size={36} color={AMBER} weight={800} />
        {rows.map(([en, zh, sub], i) => {
          const r = rise(t, o.start + 0.8 + i * 0.7, o.start + 1.3 + i * 0.7);
          return (
            <div key={en} style={{ display: "flex", gap: 20, marginTop: 26, opacity: r }}>
              <div style={{ fontFamily: EN, fontSize: 36, color: AMBER, fontWeight: 800 }}>✓</div>
              <div>
                <div style={{ fontFamily: EN, fontSize: 34, fontWeight: 600, color: INK }}>{en}</div>
                <div style={{ fontFamily: ZH, fontSize: 22, color: MUTED, marginTop: 4 }}>{zh}</div>
                {sub && <div style={{ fontFamily: EN, fontSize: 20, color: MUTED, marginTop: 4 }}>{sub}</div>}
              </div>
            </div>
          );
        })}
        <div style={{ fontFamily: EN, fontSize: 19, color: MUTED, marginTop: 26 }}>as the study page printed it · a* 0.382 · 48 × 48 rays · 2026-11-26</div>
      </Panel>
    </div>
  );
};

/** The debug views' names, top left: English big, Chinese small. Shots with the same label share one. */
const LABELS: Record<string, [string, string, string?]> = {
  page: ["Our debug page", "我们的调试页面"],
  picture: ["The picture", "画面"],
  outcome: ["What each ray did", "每一束光的去向"],
  cost: ["What each ray cost: steps per ray", "每束光的代价：走了多少步"],   // d3 is shown 8× brighter (BLACK-HOLE-AI.md)
  shift: ["Frequency shift", "颜色偏移（频移）"],
  compare: ["Checking the GPU", "检查显卡"],
  landmark: ["One landmark, no gas", "一个路标，没有气体"],
};
const LABEL_OF: Record<string, string> = {
  page: "page",
  picture: "picture",
  "outcome-page": "outcome",
  outcome: "outcome",
  "cost-page": "cost",
  cost: "cost",
  "shift-page": "shift",
  shift: "shift",
  "compare-page": "compare",
  landmark: "landmark",
};
const labelSpans = (tl: BlackHoleTimeline) => {
  const spans: { key: string; start: number; end: number }[] = [];
  for (const s of tl.shots) {
    if (!s.label) continue;
    const key = LABEL_OF[s.label];
    const a = s.startFrame / tl.fps + (s.fadeIn ?? 0) * 0.5;
    const b = s.endFrame / tl.fps;
    const last = spans[spans.length - 1];
    if (last && last.key === key && a <= last.end + 0.05) last.end = b;
    else spans.push({ key, start: a, end: b });
  }
  return spans;
};
const ViewLabel: FC<{ t: number; span: { key: string; start: number; end: number } }> = ({ t, span }) => {
  const [en, zh, note] = LABELS[span.key];
  const v = window_(t, span.start, span.end - 0.15, 0.45, 0.35);
  return (
    // Right of the study page's own control panel (the stills show it at the left, 0-390 px)
    <div style={{ position: "absolute", left: 430, top: 52, opacity: v }}>
      <div style={{ display: "inline-block", background: "rgba(5,6,10,.62)", borderRadius: 16, padding: "14px 26px 16px", borderLeft: `6px solid ${AMBER}` }}>
        <Bi en={en} zh={zh} size={46} weight={800} />
        {note && <div style={{ fontFamily: EN, fontSize: 20, color: AMBER_SOFT, marginTop: 6 }}>{note}</div>}
      </div>
    </div>
  );
};

export const QR: FC<{ size: number }> = ({ size }) => {
  const n = QR_ROWS.length;
  const quiet = 4;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${n + quiet * 2} ${n + quiet * 2}`} shapeRendering="crispEdges" style={{ display: "block", borderRadius: 14 }}>
      <rect width={n + quiet * 2} height={n + quiet * 2} fill="#ffffff" />
      {QR_ROWS.flatMap((row, y) => [...row].map((bit, x) => (bit === "1" ? <rect key={`${x}-${y}`} x={x + quiet} y={y + quiet} width={1} height={1} fill="#05060a" /> : null)))}
    </svg>
  );
};

const EndCard: FC<{ t: number; o: Overlay; tl: BlackHoleTimeline }> = ({ t, o, tl }) => {
  const v = rise(t, o.start, o.start + 0.9);
  const step = (k: number) => rise(t, o.start + 0.4 + k * 0.35, o.start + 1.0 + k * 0.35);
  return (
    <AbsoluteFill style={{ opacity: v }}>
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(5,6,10,.88) 0%, rgba(5,6,10,.7) 55%, rgba(5,6,10,.35) 100%)" }} />
      <div style={{ position: "absolute", left: 150, top: 150, width: 1060 }}>
        <div style={{ opacity: step(0) }}>
          <Bi en="Fly it yourself" zh="你自己来飞" size={70} weight={800} />
        </div>
        <div style={{ fontFamily: EN, fontSize: 88, fontWeight: 800, color: AMBER, marginTop: 34, opacity: step(1), letterSpacing: 0.5 }}>{SITE}</div>
        <div style={{ marginTop: 40, opacity: step(2) }}>
          <Bi en="The Manifold → Teleport Orb → Black Hole Journey" zh="Manifold 房间 → 传送球 → Black Hole Journey" size={38} weight={600} />
        </div>
        <div style={{ marginTop: 70, opacity: step(3) }}>
          <div style={{ fontFamily: EN, fontSize: 30, fontWeight: 700, color: INK }}>{tl.title}</div>
          <div style={{ fontFamily: EN, fontSize: 26, color: MUTED, marginTop: 6 }}>{tl.byline}</div>
        </div>
      </div>
      <div style={{ position: "absolute", right: 170, top: 210, opacity: step(1), textAlign: "center" }}>
        <QR size={430} />
        <div style={{ fontFamily: EN, fontSize: 26, color: INK, marginTop: 18 }}>Scan to fly</div>
        <div style={{ fontFamily: ZH, fontSize: 20, color: MUTED, marginTop: 4 }}>扫码去飞</div>
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ the chapter bar

/** The chapters as YouTube segments its bar from the description (same starts, same proportions, small gaps),
 * with a ▼ riding above the playing point (the cube films' convention). */
/** The bar's own short names (the YouTube description carries the full chapter titles). */
const BAR: Record<string, [string, string]> = {
  BH00: ["Flying around", "绕着黑洞飞"],
  BH01: ["A real black hole", "真实的黑洞"],
  BH02: ["How we built it with AI", "我们怎么和 AI 一起做的"],
  BH03: ["Falling in", "掉进去"],
  BH04: ["Fly it yourself", "你自己来飞"],
};
const ChapterBar: FC<{ tl: BlackHoleTimeline; t: number }> = ({ tl, t }) => {
  const inset = 18;
  const width = 1920 - inset * 2;
  const x = (time: number) => inset + (time / tl.durationSeconds) * width;
  const gap = 4;
  const current = tl.sections.findIndex((s) => t >= s.start && t < s.end);
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {tl.sections.map((s, i) => {
        const left = x(s.start) + (i ? gap / 2 : 0);
        const right = x(s.end) - (i < tl.sections.length - 1 ? gap / 2 : 0);
        const w = right - left;
        const on = i === current;
        const played = Math.max(0, Math.min(1, (t - s.start) / (s.end - s.start)));
        return (
          <div key={s.id}>
            <div style={{ position: "absolute", left, width: w, bottom: 38, textAlign: "center", overflow: "hidden", whiteSpace: "nowrap" }}>
              <div style={{ fontFamily: EN, fontSize: w < 200 ? 18 : 21, fontWeight: on ? 800 : 600, color: on ? INK : MUTED, opacity: on ? 1 : 0.8 }}>{(BAR[s.id] ?? [s.en])[0]}</div>
              {w >= 110 && <div style={{ fontFamily: ZH, fontSize: 14, color: on ? AMBER : MUTED, opacity: on ? 1 : 0.7 }}>{(BAR[s.id] ?? [s.en, s.zh])[1]}</div>}
            </div>
            <div style={{ position: "absolute", left, width: w, bottom: 12, height: 8, borderRadius: 4, background: "rgba(255,255,255,.22)", overflow: "hidden" }}>
              <div style={{ width: `${played * 100}%`, height: "100%", background: on ? AMBER : "rgba(242,180,90,.7)" }} />
            </div>
          </div>
        );
      })}
      {current >= 0 && (
        <div style={{ position: "absolute", left: x(t) - 11, bottom: 19, width: 0, height: 0, borderLeft: "11px solid transparent", borderRight: "11px solid transparent", borderTop: `14px solid ${AMBER}` }} />
      )}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ the film

export const BlackHoleAiVideo: FC<BlackHoleProps> = ({ tl, track = "en" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!tl) return <AbsoluteFill style={{ background: NIGHT }} />;
  const t = frame / fps;
  const at = (kind: string) => tl.overlays.filter((o) => o.kind === kind && t >= o.start - 0.05 && t < o.end + 0.05);
  const fade = 1 - rise(t, tl.durationSeconds - tl.fadeOut, tl.durationSeconds);
  return (
    <AbsoluteFill style={{ background: NIGHT }}>
      {tl.shots.map((s) => (
        <Sequence key={s.id} from={s.startFrame} durationInFrames={s.endFrame - s.startFrame} layout="none">
          <AbsoluteFill>
            <ShotLayer shot={s} tl={tl} />
          </AbsoluteFill>
        </Sequence>
      ))}
      {labelSpans(tl)
        .filter((sp) => t >= sp.start && t < sp.end)
        .map((sp) => (
          <ViewLabel key={`${sp.key}-${sp.start}`} t={t} span={sp} />
        ))}
      {at("title").map((o) => (
        <TitleCard key="title" t={t} o={o} tl={tl} />
      ))}
      {tl.overlays
        .filter((o) => o.kind.startsWith("ref-") && t >= o.start && t < o.end)
        .map((o) => (
          <RefCard key={o.kind} t={t} o={o} />
        ))}
      {at("legend").map((o) => (
        <Legend key="legend" t={t} o={o} />
      ))}
      {at("cpu-check").map((o) => (
        <CpuCard key="cpu" t={t} o={o} />
      ))}
      {at("end-card").map((o) => (
        <EndCard key="end" t={t} o={o} tl={tl} />
      ))}
      <ChapterBar tl={tl} t={t} />
      {fade < 1 && <AbsoluteFill style={{ background: "#000", opacity: 1 - fade }} />}
      {tl.draft && <div style={{ position: "absolute", right: 24, top: 16, fontFamily: MONO, fontSize: 22, color: AMBER, opacity: 0.8 }}>DRAFT timeline (placeholder takes)</div>}
      {/* The studio preview plays one track; the render is muted and muxes both mixes. */}
      <Audio src={file(`audio/${track}.mix.wav`)} />
    </AbsoluteFill>
  );
};
