// "How Do You Solve a 2×2 Cube?" / 「二阶魔方怎么还原？」 (CUBE-2X2.md §4), v0.2: one picture, English first, with a
// Chinese audio track. Every picture is the cube page itself (inception-space-ui /cube/, "Solve it for me"),
// recorded frame by frame by scripts/cube-2x2/capture.mjs. On screen, English leads and Chinese follows in small
// type; the cube sits small on the left, and the right-hand column carries the cards: what each move means (every
// time one is used), the step's moves with the turning one lit, the algorithm's name, and the two big parts —
// the first layer, then the top layer.
import type { CSSProperties, FC, ReactNode } from "react";
import {
  AbsoluteFill,
  Audio,
  Freeze,
  Img,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  type CalculateMetadataFunction,
} from "remotion";
import { CUBE_URL, QR_ROWS } from "./qr";

type Lang = "zh" | "en";
type Span = { start: number; end: number };
type Cue = { id: string; section: string; zh: string; en: string; start: number; end: number; speech: Span; speeches: Record<Lang, Span> };
/** `keys`: [film seconds, source seconds] points to follow instead of the eased curve (the letters, timed to the words). */
type Shot = { take: string; cues: [string, string]; start: number; end: number; from: number; to: number; keys?: [number, number][] };
type CubeMove = { axis: number; lo: number; hi: number; quarter: number };
type TakeMove = { stage?: number; step?: number; index?: number; move?: CubeMove; label?: string; start: number; end: number };
type Take = {
  fps: number;
  take: string;
  frames: number;
  moves: TakeMove[];
  stages: { stage: number; key: string; frame: number }[];
  steps: { stage: number; step: number; frame: number }[];
  marks: { name: string; frame: number }[];
};
type PlanStage = { key: string; title: string; steps: { text: string; alg: string | null; moves: CubeMove[] }[] };
export type CubeTimeline = {
  fps: number;
  durationSeconds: number;
  endCardStart: number;
  leadIn: number;
  cues: Cue[];
  shots: Shot[];
  takes: Record<string, Take>;
  plan: PlanStage[];
  footageSeconds: Record<string, number>;
  draft: boolean;
};
/** `track`: which narration plays (the render mutes it and muxes both tracks; the studio preview plays one). */
export type CubeProps = { tl?: CubeTimeline | null; track?: Lang };

const DIR = "cube-2x2";
const file = (p: string) => staticFile(`${DIR}/${p}`);
// The cube page's own palette (inception-space-ui cube/styles/cube.css), so the film and the page look alike.
const NIGHT = "#04070d",
  INK = "#f6f8fb",
  MUTED = "#a9b7c8",
  LINE = "rgba(193, 220, 241, 0.22)",
  MINT = "#9ed7bd",
  AMBER = "#f3c46b",
  PANEL = "rgba(10, 18, 30, 0.84)";
/** R L U D F B: red, orange, white, yellow, green, blue (cube/src/view.js). */
const STICKER = ["#d4202f", "#ff7f11", "#f4f6f8", "#ffd60a", "#13a453", "#1565e0"];
const ZH = '"PingFang SC", "Hiragino Sans GB", sans-serif';
const EN = '"Avenir Next", "Helvetica Neue", sans-serif';
const MONO = '"SF Mono", Menlo, monospace';
const XFADE = 0.35;
/** Captions sit in YouTube's bottom band; nothing important goes below this. */
const SAFE_BOTTOM = 150;
/** The right-hand column beside the cube. */
const COLUMN = { right: 70, width: 820 };

const ease = (x: number) => {
  const t = Math.max(0, Math.min(1, x));
  return t * t * (3 - 2 * t);
};
/** 0 → 1 between a and b, eased. */
const rise = (t: number, a: number, b: number) => ease((t - a) / Math.max(0.001, b - a));
/** In over `inn` seconds from a, out over `out` seconds before b. */
const window_ = (t: number, a: number, b: number, inn = 0.4, out = 0.3) => Math.min(rise(t, a, a + inn), 1 - rise(t, b - out, b));

export const calculateCubeMetadata: CalculateMetadataFunction<CubeProps> = async ({ props, abortSignal }) => {
  const response = await fetch(file("timeline.json"), { signal: abortSignal });
  if (!response.ok) throw Error("Run c2:timeline first");
  const tl = (await response.json()) as CubeTimeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

// ------------------------------------------------------------------ the footage on its curve

/**
 * Where a shot's footage is at film time t. A take plays at its own speed with a short start and stop
 * (RAMP) and then rests on its last frame while the line finishes; a take longer than its lines is sped up
 * over the whole shot instead, still starting and stopping smoothly. The two slow camera turns (hero,
 * meet) always fill their shot.
 */
const RAMP = 0.3;
const profile = (u: number, r: number) => {
  const x = Math.max(0, Math.min(1, u));
  if (r <= 0) return x;
  const v = 1 / (1 - r);
  if (x < r) return (0.5 * v * x * x) / r;
  if (x > 1 - r) return 1 - (0.5 * v * (1 - x) * (1 - x)) / r;
  return 0.5 * v * r + v * (x - r);
};
const sourceAt = (shot: Shot, t: number) => {
  if (shot.keys) {
    const k = shot.keys;
    if (t <= k[0][0]) return k[0][1];
    for (let i = 1; i < k.length; i += 1) {
      if (t <= k[i][0]) return k[i - 1][1] + ((k[i][1] - k[i - 1][1]) * (t - k[i - 1][0])) / (k[i][0] - k[i - 1][0]);
    }
    return k[k.length - 1][1];
  }
  const length = shot.to - shot.from;
  const span = shot.end - shot.start;
  if (length <= 0.02) return shot.from;
  const stretch = shot.take === "hero" || shot.take === "meet";
  let from = shot.start;
  let run = span;
  if (!stretch && length + RAMP < span) {
    run = length + RAMP;
    from = shot.start + Math.min(0.35, (span - run) / 2);
  }
  return shot.from + length * profile((t - from) / run, Math.min(0.45, RAMP / run));
};

type Layout = { x: number; y: number; s: number };
/** The cube in the middle (title, closing question, end card) or small on the left, beside the cards. */
const CENTRE: Layout = { x: 0, y: 0, s: 1 };
const LEFT: Layout = { x: -400, y: 10, s: 0.62 };
const CENTRED = new Set(["cb00-03", "cb06-02"]);
/** The real page (take "page") sits in a browser window on the left, its address bar above it. */
const PAGE: Layout = { x: -330, y: 40, s: 0.6 };
const layoutAt = (cues: Cue[], t: number): Layout => {
  const i = Math.max(0, cues.findIndex((c) => c.start <= t && t < c.end));
  const target = (k: number) => (k < 0 ? LEFT : CENTRED.has(cues[k].id) ? CENTRE : LEFT);
  const now = target(i);
  const before = target(i - 1);
  const w = i === 0 ? 1 : rise(t, cues[i].start, cues[i].start + 0.9);
  return { x: before.x + (now.x - before.x) * w, y: before.y + (now.y - before.y) * w, s: before.s + (now.s - before.s) * w };
};

const Footage: FC<{ tl: CubeTimeline; shot: Shot; t: number; dim?: number; layout: Layout }> = ({ tl, shot, t, dim = 0, layout }) => {
  const seconds = tl.footageSeconds[`${shot.take}.mp4`] ?? 1;
  const src = Math.max(0, Math.min(seconds - 0.07, sourceAt(shot, t)));
  // A shot that holds one picture (the cards explain it) drifts slowly closer and back, so the frame never
  // stands dead still and the next shot starts from the same framing.
  const still = shot.to - shot.from <= 0.05;
  const u = Math.max(0, Math.min(1, (t - shot.start) / Math.max(1, shot.end - shot.start)));
  const drift = still ? 1 + (0.04 * (1 - Math.cos(2 * Math.PI * u))) / 2 : 1;
  return (
    <AbsoluteFill>
      {shot.take === "page" ? <BrowserFrame /> : null}
      <AbsoluteFill style={{ transform: `translate(${layout.x}px, ${layout.y}px) scale(${layout.s * drift})` }}>
        <Freeze frame={0}>
          <OffthreadVideo src={file(`footage/${shot.take}.mp4`)} muted trimBefore={Math.round(src * tl.fps)} style={{ width: "100%", height: "100%" }} />
        </Freeze>
      </AbsoluteFill>
      {dim > 0 && <AbsoluteFill style={{ background: NIGHT, opacity: dim }} />}
    </AbsoluteFill>
  );
};

/** The window around the page take: a rounded frame and an address bar reading the page's address. */
const BrowserFrame: FC = () => {
  const width = 1920 * PAGE.s;
  const height = 1080 * PAGE.s;
  const left = 960 + PAGE.x - width / 2;
  const top = 540 + PAGE.y - height / 2;
  return (
    <div
      style={{
        position: "absolute",
        left: left - 10,
        top: top - 58,
        width: width + 20,
        height: height + 68,
        borderRadius: 22,
        background: "#1b2533",
        border: `1px solid ${LINE}`,
        boxShadow: "0 30px 80px rgba(0,0,0,.55)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10, height: 48, padding: "0 18px" }}>
        {["#ff5f57", "#febc2e", "#28c840"].map((colour) => (
          <span key={colour} style={{ width: 14, height: 14, borderRadius: 7, background: colour }} />
        ))}
        <div style={{ marginLeft: 16, flex: 1, height: 30, borderRadius: 15, background: "rgba(255,255,255,.08)", display: "flex", alignItems: "center", padding: "0 16px", fontFamily: MONO, fontSize: 20, color: INK }}>
          🔒 {CUBE_URL}
        </div>
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ notation (cube.js formatMove, home frame)

const faceSign = (face: number) => (face & 1 ? -1 : 1);
/** A move's name as the cube page writes it in its own frame (R = +x), with a real prime. */
const moveName = (m: CubeMove, n = 2) => {
  const outer = n - 1;
  const index = m.axis;
  const near = [0, 2, 4][index];
  const far = near ^ 1;
  const suffix = (face: number) => (m.quarter === (faceSign(face) > 0 ? 3 : 1) ? "" : m.quarter === 2 ? "2" : "′");
  if (m.lo <= -outer && m.hi >= outer) return "xyz"[index] + suffix(near);
  if (m.lo === 0 && m.hi === 0) return "MES"[index] + suffix(index === 2 ? near : far);
  const depth = (face: number, c: number) => (outer - faceSign(face) * c) / 2 + 1;
  const face = depth(near, m.lo) <= depth(far, m.lo) ? near : far;
  const layer = depth(face, m.lo);
  return `${layer > 1 ? layer : ""}${(face === near ? "RUF" : "LDB")[index]}${suffix(face)}`;
};
const prime = (label: string) => label.replace(/'/g, "′");

// ------------------------------------------------------------------ building blocks

const Panel: FC<{ children: ReactNode; style?: CSSProperties }> = ({ children, style }) => (
  <div
    style={{
      background: PANEL,
      border: `1px solid ${LINE}`,
      borderRadius: 28,
      padding: "24px 32px",
      boxShadow: "0 24px 60px rgba(0,0,0,.45)",
      ...style,
    }}
  >
    {children}
  </div>
);

/** English first, Chinese under it, smaller (owner, 2026-10-25). */
const Bi: FC<{ en: ReactNode; zh: ReactNode; size?: number; color?: string; weight?: number; align?: CSSProperties["textAlign"]; style?: CSSProperties }> = ({
  en,
  zh,
  size = 40,
  color = INK,
  weight = 650,
  align,
  style,
}) => (
  <div style={{ textAlign: align, ...style }}>
    <div style={{ fontFamily: EN, fontSize: size, color, fontWeight: weight, lineHeight: 1.25 }}>{en}</div>
    <div style={{ fontFamily: ZH, fontSize: Math.round(size * 0.66), color: MUTED, fontWeight: 500, lineHeight: 1.4, marginTop: Math.round(size * 0.1) }}>{zh}</div>
  </div>
);

const Chip: FC<{ children: ReactNode; state?: "done" | "now" | "next"; size?: number }> = ({ children, state = "next", size = 46 }) => (
  <span
    style={{
      display: "inline-block",
      minWidth: size * 1.25,
      padding: `${size * 0.12}px ${size * 0.28}px`,
      margin: size * 0.08,
      borderRadius: size * 0.28,
      textAlign: "center",
      fontFamily: MONO,
      fontWeight: 700,
      fontSize: size,
      lineHeight: 1.15,
      color: state === "now" ? "#06120c" : INK,
      background: state === "now" ? MINT : "rgba(255,255,255,.08)",
      opacity: state === "done" ? 0.38 : 1,
      transform: state === "now" ? "scale(1.08)" : undefined,
      boxShadow: state === "now" ? "0 0 26px rgba(158,215,189,.55)" : undefined,
    }}
  >
    {children}
  </span>
);

const Sticker: FC<{ colour: number; size?: number; glow?: boolean; style?: CSSProperties }> = ({ colour, size = 64, glow, style }) => (
  <span
    style={{
      display: "inline-block",
      width: size,
      height: size,
      borderRadius: size * 0.18,
      background: STICKER[colour],
      boxShadow: glow ? `0 0 ${size * 0.5}px ${STICKER[colour]}, inset 0 0 0 3px rgba(0,0,0,.25)` : "inset 0 0 0 3px rgba(0,0,0,.25)",
      verticalAlign: "middle",
      flexShrink: 0,
      ...style,
    }}
  />
);

/** A card in the right-hand column; `top` places it, it fades in and out with its lines. */
const Side: FC<{ children: ReactNode; t: number; from: number; to: number; top: number }> = ({ children, t, from, to, top }) => (
  <div
    style={{
      position: "absolute",
      top,
      right: COLUMN.right,
      width: COLUMN.width,
      display: "flex",
      justifyContent: "center",
      opacity: window_(t, from, to),
      transform: `translateY(${(1 - rise(t, from, from + 0.5)) * 18}px)`,
    }}
  >
    {children}
  </div>
);

const Note: FC<{ t: number; from: number; to: number; title?: [ReactNode, ReactNode]; children: [ReactNode, ReactNode]; top?: number; width?: number }> = ({
  t,
  from,
  to,
  title,
  children,
  top = 150,
  width = 760,
}) => (
  <Side t={t} from={from} to={to} top={top}>
    <Panel style={{ width }}>
      {title && <Bi en={title[0]} zh={title[1]} size={30} color={AMBER} weight={800} style={{ marginBottom: 12 }} />}
      <Bi en={children[0]} zh={children[1]} size={36} weight={600} />
    </Panel>
  </Side>
);

// ------------------------------------------------------------------ the move card

/** What each move means, in both languages (the page's notation, cube/README.md). */
const MEANING: Record<string, [string, string]> = {
  R: ["Right face", "右面"],
  L: ["Left face", "左面"],
  U: ["Top face (Up)", "上面"],
  D: ["Bottom face (Down)", "下面"],
  F: ["Front face", "前面"],
  B: ["Back face", "后面"],
  y: ["The whole cube", "整个魔方"],
};
const meaning = (label: string): [string, string] => {
  const face = label[0];
  const turn = label.slice(1);
  const [en, zh] = MEANING[face] ?? [face, face];
  if (face === "y") {
    return turn === "′" ? [`${en}, turned like U′`, `${zh}，像 U′ 一样转`] : turn === "2" ? [`${en}, a half turn`, `${zh}，转半圈`] : [`${en}, turned like U`, `${zh}，像 U 一样转`];
  }
  const seen = face === "B" ? [" (seen from behind)", "（从后面看）"] : face === "L" ? [" (seen from the left)", "（从左边看）"] : face === "D" ? [" (seen from below)", "（从下面看）"] : ["", ""];
  if (turn === "2") return [`${en} · a half turn`, `${zh} · 转半圈`];
  if (turn === "′") return [`${en} · counterclockwise${seen[0]}`, `${zh} · 逆时针${seen[1]}`];
  return [`${en} · clockwise${seen[0]}`, `${zh} · 顺时针${seen[1]}`];
};

/**
 * A little 2×2 drawn from above-front-right (top white, front green, right red): the turning layer lit, the
 * rest dimmed, and an arrow showing which way the front (or top) stickers travel.
 */
const MoveIcon: FC<{ label: string; size?: number }> = ({ label, size = 230 }) => {
  const face = label[0];
  const turn = label.slice(1);
  const k = size / 4.4;
  const P = (x: number, y: number, z: number) => [size / 2 + (x - z) * 0.866 * k, size / 2 + ((x + z) * 0.5 - y) * k];
  const poly = (pts: number[][]) => pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const inLayer = (x: number, y: number, z: number) =>
    face === "y" || (face === "R" && x > 0) || (face === "L" && x < 0) || (face === "U" && y > 0) || (face === "D" && y < 0) || (face === "F" && z > 0) || (face === "B" && z < 0);
  const stickers: { pts: number[][]; colour: number; lit: boolean }[] = [];
  const g = 0.08;
  for (const a of [-1, 0]) {
    for (const b of [-1, 0]) {
      // top (y = 1): x across, z along
      stickers.push({ pts: [P(a + g, 1, b + g), P(a + 1 - g, 1, b + g), P(a + 1 - g, 1, b + 1 - g), P(a + g, 1, b + 1 - g)], colour: 2, lit: inLayer(a + 0.5, 1, b + 0.5) });
      // front (z = 1): x across, y up
      stickers.push({ pts: [P(a + g, b + g, 1), P(a + 1 - g, b + g, 1), P(a + 1 - g, b + 1 - g, 1), P(a + g, b + 1 - g, 1)], colour: 4, lit: inLayer(a + 0.5, b + 0.5, 1) });
      // right (x = 1): z across, y up
      stickers.push({ pts: [P(1, b + g, a + g), P(1, b + g, a + 1 - g), P(1, b + 1 - g, a + 1 - g), P(1, b + 1 - g, a + g)], colour: 0, lit: inLayer(1, b + 0.5, a + 0.5) });
    }
  }
  // The arrow: where the stickers on a visible face go when the layer turns clockwise (seen from that face).
  const arrows: Record<string, [number[], number[]]> = {
    R: [[0.5, -0.75, 1.02], [0.5, 0.75, 1.02]],
    L: [[-0.5, 0.75, 1.02], [-0.5, -0.75, 1.02]],
    U: [[0.75, 0.5, 1.02], [-0.75, 0.5, 1.02]],
    D: [[-0.75, -0.5, 1.02], [0.75, -0.5, 1.02]],
    F: [[-0.75, 1.02, 0.5], [0.75, 1.02, 0.5]],
    B: [[0.75, 1.02, -0.5], [-0.75, 1.02, -0.5]],
    y: [[0.75, 0, 1.02], [-0.75, 0, 1.02]],
  };
  let [from, to] = arrows[face] ?? arrows.R;
  if (turn === "′") [from, to] = [to, from];
  const [x0, y0] = P(from[0], from[1], from[2]);
  const [x1, y1] = P(to[0], to[1], to[2]);
  const angle = Math.atan2(y1 - y0, x1 - x0);
  const head = k * 0.42;
  const tip = (da: number) => [x1 - head * Math.cos(angle + da), y1 - head * Math.sin(angle + da)];
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {stickers.map((s, i) => (
        <polygon key={i} points={poly(s.pts)} fill={STICKER[s.colour]} opacity={s.lit ? 1 : 0.22} stroke="#0b0e13" strokeWidth={2} />
      ))}
      <line x1={x0} y1={y0} x2={x1} y2={y1} stroke={AMBER} strokeWidth={k * 0.2} strokeLinecap="round" />
      <polygon points={poly([[x1, y1], tip(0.55), tip(-0.55)])} fill={AMBER} stroke={AMBER} strokeWidth={4} strokeLinejoin="round" />
      {turn === "2" && (
        <text x={x1 + 8} y={y1 - 14} fill={AMBER} fontFamily={MONO} fontWeight={800} fontSize={k * 0.62}>
          ×2
        </text>
      )}
    </svg>
  );
};

/** The move card: the letter, what it means in both languages, and the little cube. */
const MoveCard: FC<{ label: string; opacity: number; top: number; big?: boolean }> = ({ label, opacity, top, big }) => {
  const [en, zh] = meaning(label);
  return (
    <div style={{ position: "absolute", top, right: COLUMN.right, width: COLUMN.width, display: "flex", justifyContent: "center", opacity }}>
      <Panel style={{ width: COLUMN.width - 60, display: "flex", alignItems: "center", gap: 28, padding: "18px 28px" }}>
        <MoveIcon label={label} size={big ? 230 : 180} />
        <div>
          <div style={{ fontFamily: MONO, fontSize: big ? 130 : 96, fontWeight: 800, color: AMBER, lineHeight: 1 }}>{label}</div>
          <Bi en={en} zh={zh} size={big ? 36 : 30} weight={650} style={{ marginTop: 10 }} />
        </div>
      </Panel>
    </div>
  );
};

/** The move of a take turning at frame f, or (for `linger` frames after) the one that just turned. */
const moveAt = (take: Take, frame: number, linger: number) => [...take.moves].reverse().find((m) => m.start < frame && frame < m.end + linger) ?? null;

// ------------------------------------------------------------------ the solve's overlays

const ALG: Record<string, [string, string]> = {
  "R U R' U'": ["The little move", "小动作"],
  "R U R' U R U2 R'": ["Sune", "小鱼公式"],
  "R' F R' B2 R F' R' B2 R2": ["The corner algorithm", "换角公式"],
};

/** What the solve take shows at a source time: the stage, the step and how far into it. */
const solveAt = (take: Take, plan: PlanStage[], src: number) => {
  const frame = Math.round(src * take.fps);
  // A move whose first frame this is has not visibly begun: it is still the next one.
  const turning = take.moves.find((m) => m.start < frame && frame < m.end);
  const next = turning ?? take.moves.find((m) => m.start >= frame);
  const lastDone = [...take.moves].reverse().find((m) => m.end <= frame);
  // Between steps, the step just finished stays on screen through its rest; once the cube has moved on (a new
  // stage's camera move, a held picture), the next step is shown, still to come.
  const sameStep = lastDone && next && lastDone.step === next.step && lastDone.stage === next.stage;
  const resting = lastDone && frame - lastDone.end <= 18;
  const ref = turning ?? (sameStep ? next : resting ? lastDone : next ?? lastDone);
  if (!ref || ref.stage === undefined || ref.step === undefined) return null;
  const stage = ref.stage;
  const step = plan[stage].steps[ref.step];
  const labels = step.moves.map((m) => moveName(m));
  const doneCount = take.moves.filter((m) => m.stage === stage && m.step === ref.step && m.end <= frame).length;
  return { stage, stepIndex: ref.step, step, labels, turning: turning ? turning.index ?? -1 : -1, done: doneCount };
};

/** Which time round the little move is on, in a step that repeats it. */
const repetition = (labels: string[], done: number, turning: number) => {
  const first = labels.findIndex((_, i) => labels.slice(i, i + 4).join(" ") === "R U R′ U′");
  if (first < 0) return null;
  const count = Math.floor((labels.length - first) / 4);
  const at = turning >= 0 ? turning : done;
  if (at < first) return { now: 0, count };
  return { now: Math.min(count, Math.floor((at - first) / 4) + 1), count };
};

/** A step with no algorithm is either holding the cube a new way or lining up the top. */
const plainStep = (labels: string[]): [string, string] | null =>
  labels.every((l) => /^[xyz]/.test(l)) ? ["Turn the whole cube", "转动整个魔方"] : labels.every((l) => /^U/.test(l)) ? ["Turn the top", "转动顶层"] : null;

/** The film's chapters, as YouTube shows them (package.py writes the same starts into the description). */
const CHAPTER_NAMES: Record<string, [string, string]> = {
  cb00: ["The challenge", "挑战"],
  cb01: ["Letters", "字母"],
  cb02: ["Part 1 · First layer", "第一部分 · 第一层"],
  cb03: ["Part 2 · Yellow top", "第二部分 · 顶面全黄"],
  cb04: ["Part 2 · Corners", "第二部分 · 换好四个角"],
  cb05: ["Replay", "再看一遍"],
  cb06: ["Try online", "网上练"],
};
const chaptersOf = (tl: CubeTimeline) => {
  const starts: [string, number][] = [];
  for (const c of tl.cues) if (!starts.some(([s]) => s === c.section)) starts.push([c.section, starts.length ? c.start : 0]);
  return starts.map(([section, start], i) => ({ section, start, end: i + 1 < starts.length ? starts[i + 1][1] : tl.durationSeconds }));
};

/**
 * The chapter bar along the bottom, segmented exactly as YouTube segments its own bar from the description's
 * chapters (same starts, same proportions, the same small gaps), so a viewer can see where each part is and jump
 * there with YouTube's bar just below. A ▼ rides above the playing point; at the start, ↓ arrows over every
 * chapter say "jump to any part".
 */
const ChapterTrack: FC<{ tl: CubeTimeline; t: number; hint: number }> = ({ tl, t, hint }) => {
  const chapters = chaptersOf(tl);
  const inset = 18;
  const width = 1920 - inset * 2;
  const x = (time: number) => inset + (time / tl.durationSeconds) * width;
  const gap = 4;
  const current = chapters.findIndex((ch) => t >= ch.start && t < ch.end);
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {hint > 0 && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 176, textAlign: "center", opacity: hint }}>
          <Bi en="Jump to any part with the progress bar ↓" zh="点下面的进度条，跳到任意部分" size={34} color={AMBER} weight={800} align="center" />
        </div>
      )}
      {chapters.map((ch, i) => {
        const left = x(ch.start) + (i ? gap / 2 : 0);
        const right = x(ch.end) - (i < chapters.length - 1 ? gap / 2 : 0);
        const w = right - left;
        const on = i === current;
        const played = Math.max(0, Math.min(1, (t - ch.start) / (ch.end - ch.start)));
        const [en, zh] = CHAPTER_NAMES[ch.section] ?? [ch.section, ""];
        return (
          <div key={ch.section}>
            {hint > 0 && (
              <div style={{ position: "absolute", left, width: w, bottom: 100, textAlign: "center", opacity: hint, fontSize: 40, color: AMBER, transform: `translateY(${Math.sin(t * 5 + i) * 4}px)` }}>↓</div>
            )}
            <div style={{ position: "absolute", left, width: w, bottom: 38, textAlign: "center", overflow: "hidden", whiteSpace: "nowrap" }}>
              <div style={{ fontFamily: EN, fontSize: w < 130 ? 19 : 22, fontWeight: on ? 800 : 600, color: on ? INK : MUTED, opacity: on ? 1 : 0.8 }}>{en}</div>
              {w >= 90 && <div style={{ fontFamily: ZH, fontSize: 15, color: on ? MINT : MUTED, opacity: on ? 1 : 0.7 }}>{zh}</div>}
            </div>
            <div style={{ position: "absolute", left, width: w, bottom: 12, height: 8, borderRadius: 4, background: "rgba(255,255,255,.22)", overflow: "hidden" }}>
              <div style={{ width: `${played * 100}%`, height: "100%", background: on ? MINT : "rgba(158,215,189,.75)" }} />
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

const StepStrip: FC<{ at: NonNullable<ReturnType<typeof solveAt>>; opacity: number }> = ({ at, opacity }) => {
  const name = at.step.alg ? ALG[at.step.alg] ?? null : plainStep(at.labels);
  const rep = repetition(at.labels, at.done, at.turning);
  const size = at.labels.length > 16 ? 34 : at.labels.length > 8 ? 40 : 48;
  return (
    <div style={{ position: "absolute", right: COLUMN.right, width: COLUMN.width, bottom: SAFE_BOTTOM + 20, display: "flex", justifyContent: "center", opacity }}>
      <Panel style={{ width: COLUMN.width - 60, padding: "16px 24px", textAlign: "center" }}>
        {(name || rep) && (
          <div style={{ display: "flex", justifyContent: "center", alignItems: "flex-end", gap: 26, marginBottom: 6 }}>
            {name && <Bi en={name[0]} zh={name[1]} size={30} color={AMBER} weight={800} />}
            {rep && rep.now > 0 && <Bi en={`× ${rep.now}`} zh={`第 ${rep.now} 次`} size={30} color={MINT} weight={800} />}
          </div>
        )}
        <div>
          {at.labels.map((label, i) => (
            <Chip key={i} size={size} state={i < at.done ? "done" : i === at.turning ? "now" : "next"}>
              {label}
            </Chip>
          ))}
        </div>
      </Panel>
    </div>
  );
};

// ------------------------------------------------------------------ cards

const QR: FC<{ size: number }> = ({ size }) => {
  const n = QR_ROWS.length;
  const quiet = 3;
  const cell = size / (n + quiet * 2);
  return (
    <svg width={size} height={size} viewBox={`0 0 ${n + quiet * 2} ${n + quiet * 2}`} shapeRendering="crispEdges" style={{ borderRadius: cell * 2, display: "block", flexShrink: 0 }}>
      <rect width={n + quiet * 2} height={n + quiet * 2} fill="#ffffff" />
      {QR_ROWS.flatMap((row, y) => [...row].map((bit, x) => (bit === "1" ? <rect key={`${x}-${y}`} x={x + quiet} y={y + quiet} width={1} height={1} fill="#04070d" /> : null)))}
    </svg>
  );
};

/** The cube page's address and QR code, beside the page itself: try it online, right now. */
const LinkCard: FC<{ t: number; from: number; to: number; end?: boolean }> = ({ t, from, to, end }) => (
  <div style={{ position: "absolute", top: 200, right: 60, width: 620, opacity: window_(t, from, to), transform: `translateY(${(1 - rise(t, from, from + 0.5)) * 18}px)` }}>
    <Panel style={{ padding: "28px 32px", textAlign: "center" }}>
      <Bi en={end ? "No cube yet? Practise online." : "Try it online, right now."} zh={end ? "还没有魔方？在网上练。" : "现在就能在网上试。"} size={44} weight={800} />
      <div style={{ display: "flex", justifyContent: "center", margin: "22px 0 18px" }}>
        <QR size={250} />
      </div>
      <div style={{ fontFamily: MONO, fontSize: 36, color: MINT, fontWeight: 700 }}>{CUBE_URL}</div>
      <Bi en="Free · press “Step by step” and it walks you through every move" zh="免费 · 点 Step by step，一步一步带你还原" size={26} color={MUTED} weight={500} style={{ marginTop: 14 }} />
    </Panel>
  </div>
);

const Title: FC<{ t: number; from: number; qr?: boolean }> = ({ t, from, qr }) => (
  <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: rise(t, from, from + 0.7) }}>
    <div style={{ textAlign: "center", transform: `translateY(${(1 - rise(t, from, from + 0.9)) * 24}px)` }}>
      <div style={{ fontFamily: EN, fontSize: 30, letterSpacing: "0.32em", color: MINT, fontWeight: 700, marginBottom: 28 }}>LUCAS ACADEMY</div>
      <div style={{ fontFamily: EN, fontSize: 112, fontWeight: 800, color: INK, lineHeight: 1.1 }}>
        How Do You Solve a <span style={{ color: AMBER }}>2×2 Cube</span>?
      </div>
      <div style={{ fontFamily: ZH, fontSize: 58, fontWeight: 600, color: MUTED, marginTop: 18 }}>二阶魔方怎么还原？</div>
      <div style={{ display: "flex", justifyContent: "center", gap: 14, margin: "36px 0 30px" }}>
        {[2, 4, 0, 3, 5, 1].map((c) => (
          <Sticker key={c} colour={c} size={30} />
        ))}
      </div>
      <div style={{ fontFamily: EN, fontSize: 32, color: MUTED }}>By Lucas Academy Team</div>
      {qr && (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 24, marginTop: 40 }}>
          <QR size={170} />
          <div style={{ textAlign: "left" }}>
            <div style={{ fontFamily: MONO, fontSize: 30, color: MINT, fontWeight: 700 }}>{CUBE_URL}</div>
            <Bi en="Practise online" zh="在网上练" size={26} color={MUTED} weight={500} style={{ marginTop: 6 }} />
          </div>
        </div>
      )}
    </div>
  </AbsoluteFill>
);

/** A big part begins: its name fills the screen for a moment, then settles into the bar at the top. */
const ChapterCard: FC<{ t: number; from: number; number: string; en: string; zh: string }> = ({ t, from, number, en, zh }) => {
  const opacity = Math.min(rise(t, from, from + 0.5), 1 - rise(t, from + 2.6, from + 3.2));
  if (opacity <= 0) return null;
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", background: `rgba(4,7,13,${0.82 * opacity})`, opacity }}>
      <div style={{ textAlign: "center", transform: `scale(${0.96 + 0.04 * rise(t, from, from + 0.8)})` }}>
        <div style={{ fontFamily: EN, fontSize: 40, letterSpacing: "0.3em", color: MINT, fontWeight: 800 }}>{number}</div>
        <div style={{ fontFamily: EN, fontSize: 120, fontWeight: 800, color: INK, marginTop: 10 }}>{en}</div>
        <div style={{ fontFamily: ZH, fontSize: 60, color: MUTED, fontWeight: 600, marginTop: 10 }}>{zh}</div>
      </div>
    </AbsoluteFill>
  );
};

const CountUp: FC<{ t: number; c: Cue }> = ({ t, c }) => {
  const k = rise(t, c.speech.start + 1.0, c.speech.end - 0.4);
  const value = Math.round(3674160 * k * k);
  return (
    <Side t={t} from={c.speech.start + 0.6} to={c.end} top={330}>
      <Panel style={{ textAlign: "center", width: 640 }}>
        <div style={{ fontFamily: MONO, fontSize: 104, fontWeight: 800, color: AMBER }}>{value.toLocaleString("en-US")}</div>
        <Bi en="ways to scramble it" zh="种打乱的样子" size={40} color={INK} />
        <div style={{ opacity: rise(t, c.speech.start + (c.speech.end - c.speech.start) * 0.45, c.speech.start + (c.speech.end - c.speech.start) * 0.55), marginTop: 22 }}>
          <Bi en="Most people never solve one." zh="大多数人一次都没还原过。" size={36} color={AMBER} weight={800} />
        </div>
      </Panel>
    </Side>
  );
};

/** A 2×2 seen from above: four top stickers, a corner's side sticker drawn as a bar at its edge. */
const TopView: FC<{ yellow: boolean[]; sides?: Record<number, "left" | "front">; mark?: number; size?: number }> = ({ yellow, sides = {}, mark, size = 200 }) => {
  const cell = size / 2;
  const at = [
    [0, 0],
    [1, 0],
    [0, 1],
    [1, 1],
  ]; // back-left, back-right, front-left, front-right
  return (
    <svg width={size + 60} height={size + 70} viewBox={`-30 -30 ${size + 60} ${size + 70}`} style={{ flexShrink: 0 }}>
      {at.map(([x, y], i) => (
        <rect key={i} x={x * cell + 6} y={y * cell + 6} width={cell - 12} height={cell - 12} rx={12} fill={yellow[i] ? STICKER[3] : "#3a4352"} stroke={i === mark ? MINT : "none"} strokeWidth={8} />
      ))}
      {Object.entries(sides).map(([i, where]) => {
        const [x, y] = at[Number(i)];
        return where === "left" ? (
          <rect key={`s${i}`} x={-24} y={y * cell + 14} width={14} height={cell - 28} rx={6} fill={STICKER[3]} />
        ) : (
          <rect key={`s${i}`} x={x * cell + 14} y={size + 10} width={cell - 28} height={14} rx={6} fill={STICKER[3]} />
        );
      })}
      <text x={size / 2} y={size + 34} textAnchor="middle" fill={MUTED} fontSize={22} fontFamily={EN}>
        front · 前
      </text>
    </svg>
  );
};

const Headlights: FC<{ t: number; c: Cue }> = ({ t, c }) => (
  <Side t={t} from={c.speech.start + 0.8} to={c.end} top={150}>
    <Panel style={{ textAlign: "center", width: 640 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 96px)", gap: 10, justifyContent: "center" }}>
        <Sticker colour={0} size={96} glow />
        <Sticker colour={0} size={96} glow />
        <Sticker colour={4} size={96} style={{ opacity: 0.55 }} />
        <Sticker colour={5} size={96} style={{ opacity: 0.55 }} />
      </div>
      <Bi en="Two matching top corners = headlights" zh="上面两个角一样 = 车头灯" size={34} style={{ marginTop: 18 }} />
    </Panel>
  </Side>
);

// ------------------------------------------------------------------ the film

export const Cube2x2Video: FC<CubeProps> = ({ tl, track = "en" }) => {
  const frame = useCurrentFrame(),
    { fps } = useVideoConfig();
  if (!tl) return null;
  const t = frame / fps;
  const byId = Object.fromEntries(tl.cues.map((c) => [c.id, c]));
  const c = tl.cues.find((x) => x.start <= t && t < x.end) ?? (t < tl.cues[0].start ? tl.cues[0] : tl.cues[tl.cues.length - 1]);
  const shotIndex = Math.max(
    0,
    tl.shots.findIndex((s) => s.start <= t && t < s.end),
  );
  const shot = t >= tl.endCardStart ? tl.shots[tl.shots.length - 1] : t < tl.shots[0].start ? tl.shots[0] : tl.shots[shotIndex];
  const previous = shotIndex > 0 ? tl.shots[shotIndex - 1] : null;
  const crossing = previous && previous.take !== shot.take && t < shot.start + XFADE;
  const src = sourceAt(shot, t);
  const solve = tl.takes.solve;
  const inSolve = shot.take === "solve" && t < tl.endCardStart;
  const recap = c.section === "cb05";
  const at = inSolve ? solveAt(solve, tl.plan, src) : null;
  const firstSolve = byId["cb02-01"];
  const ending = c.id === "cb06-02" || t >= tl.endCardStart;
  const layout = t >= tl.endCardStart ? CENTRE : shot.take === "page" ? PAGE : layoutAt(tl.cues, t);
  // The move card: whenever a take is turning a move (and for a moment after), in the letters and in the solve.
  const take = tl.takes[shot.take];
  const notationPart = shot.take === "letters";
  const srcFrame = Math.round(src * (take?.fps ?? 30));
  // Not in the opening's fast replay (cb00) or the recap: there the moves fly past too quickly to read.
  const turningNow = take && (notationPart || (inSolve && !recap && c.section !== "cb00")) ? moveAt(take, srcFrame, notationPart ? 40 : 14) : null;
  const cardLabel = turningNow ? (turningNow.label ? prime(turningNow.label) : turningNow.move ? moveName(turningNow.move) : null) : null;

  return (
    <AbsoluteFill style={{ background: NIGHT, color: INK, fontFamily: EN }}>
      <Audio src={file(`audio/${track}.mix.wav`)} />
      {crossing && previous && <Footage tl={tl} shot={previous} t={previous.end - 0.01} layout={previous.take === "page" ? PAGE : layoutAt(tl.cues, previous.end - 0.01)} />}
      <AbsoluteFill style={{ opacity: crossing ? rise(t, shot.start, shot.start + XFADE) : 1 }}>
        <Footage
          tl={tl}
          shot={shot}
          t={t}
          layout={layout}
          dim={c.id === "cb00-03" ? 0.72 * rise(t, c.start, c.start + 0.6) : ending ? 0.78 * rise(t, c.start, c.start + 0.8) : 0}
        />
      </AbsoluteFill>

      {/* Opening: the payoff and the challenge, the page and its guide, the title */}
      {c.id === "cb00-01" && <CountUp t={t} c={c} />}
      {c.id === "cb00-02" && <LinkCard t={t} from={c.start + 0.2} to={c.end} />}
      {c.id === "cb00-03" && <Title t={t} from={c.start + 0.2} />}

      {/* The letters: one line, a card for each move as it turns */}
      {c.id === "cb01-01" && (
        <Note t={t} from={c.speech.start + 0.5} to={c.end} top={130} title={["Every move gets its card", "每个转动都有卡片"]}>
          {["No need to memorise: it shows up every time.", "不用背：每次用到都会出现。"]}
        </Note>
      )}

      {/* The two big parts */}
      {c.id === "cb02-01" && <ChapterCard t={t} from={c.start} number="PART 1" en="The First Layer" zh="第一部分 · 拼第一层" />}
      {c.id === "cb03-01" && <ChapterCard t={t} from={c.start} number="PART 2" en="The Top Layer" zh="第二部分 · 拼顶层" />}
      {inSolve && !recap && at && !["cb02-03", "cb02-09", "cb03-02", "cb03-03", "cb03-04"].includes(c.id) && (
        <StepStrip at={at} opacity={rise(t, firstSolve.start + 1, firstSolve.start + 1.5)} />
      )}
      {cardLabel && (
        <MoveCard label={cardLabel} top={notationPart ? 400 : 380} big={notationPart} opacity={notationPart ? window_(t, byId["cb01-01"].start, byId["cb01-01"].end) : 1} />
      )}
      {c.id === "cb02-03" && (
        <Note t={t} from={c.speech.start + 1.2} to={c.end} title={["The first corner decides", "第一块角定下颜色"]}>
          {[
            <div key="en" style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 6 }}>
              <span>
                <Sticker colour={4} size={44} /> Front: green
              </span>
              <span>
                <Sticker colour={1} size={44} /> Right: orange
              </span>
            </div>,
            "前面：绿色 · 右边：橙色",
          ]}
        </Note>
      )}
      {c.id === "cb02-09" && (
        <Note t={t} from={c.start + 0.3} to={c.end} title={["A tip", "小提示"]}>
          {["A white corner stuck in the wrong bottom spot? Turn it to the front right and do R U R′ once to lift it out.", "白色角卡在下面不对的位置？转到右前方，先做一次 R U R′ 把它请出来。"]}
        </Note>
      )}
      {c.id === "cb03-02" && (
        <Side t={t} from={c.speech.start} to={c.end} top={250}>
          <Panel style={{ textAlign: "center", width: COLUMN.width - 60 }}>
            <Bi en="Sune" zh="小鱼公式" size={40} color={AMBER} weight={800} />
            <div style={{ marginTop: 12 }}>
              {"R U R′ U R U2 R′".split(" ").map((m, i) => (
                <Chip key={i} size={54}>
                  {m}
                </Chip>
              ))}
            </div>
          </Panel>
        </Side>
      )}
      {c.id === "cb03-03" && (
        <Note t={t} from={c.speech.start} to={c.end} title={["Exactly one yellow on top", "顶上只有一块黄色"]} top={200}>
          {[
            <div key="en" style={{ display: "flex", alignItems: "center", gap: 24 }}>
              <TopView yellow={[false, false, true, false]} mark={2} size={180} />
              <span>Put it at the front left.</span>
            </div>,
            "把它转到左前方",
          ]}
        </Note>
      )}
      {c.id === "cb03-04" && (
        <Note t={t} from={c.speech.start} to={c.end} title={["None, or two", "没有，或者有两块"]} top={200}>
          {[
            <div key="en" style={{ display: "flex", alignItems: "center", gap: 24 }}>
              <TopView yellow={[false, false, false, false]} sides={{ 2: "left" }} mark={2} size={180} />
              <span>The front-left corner&apos;s yellow faces left.</span>
            </div>,
            "左前角的黄色朝左",
          ]}
        </Note>
      )}
      {c.id === "cb04-02" && <Headlights t={t} c={c} />}
      {c.id === "cb04-04" && (
        <Note t={t} from={c.speech.start} to={c.end} title={["No headlights?", "没有车头灯？"]}>
          {["Do the corner algorithm once from anywhere, and they appear.", "先在随便哪一面做一次换角公式，车头灯就出来了。"]}
        </Note>
      )}

      {/* Once more */}
      {recap && inSolve && (
        <>
          <div style={{ position: "absolute", right: 80, top: 56, opacity: rise(t, byId["cb05-01"].start, byId["cb05-01"].start + 0.5) }}>
            <Bi en={`Fast replay ×${((shot.to - shot.from) / (shot.end - shot.start)).toFixed(1)}`} zh="快放" size={34} color={MUTED} align="right" />
          </div>
        </>
      )}
      {c.id === "cb05-02" && (
        <Side t={t} from={c.speech.start} to={c.end} top={250}>
          <Panel style={{ width: COLUMN.width - 60 }}>
            {(
              [
                ["The little move", "小动作", "R U R′ U′"],
                ["Sune", "小鱼公式", "R U R′ U R U2 R′"],
                ["The corner algorithm", "换角公式", "R′ F R′ B2 R F′ R′ B2 R2"],
              ] as const
            ).map(([en, zh, alg]) => (
              <div key={en} style={{ margin: "10px 0 18px" }}>
                <Bi en={en} zh={zh} size={28} color={AMBER} weight={800} />
                <div style={{ fontFamily: MONO, fontSize: 40, fontWeight: 700, marginTop: 4 }}>{alg}</div>
              </div>
            ))}
          </Panel>
        </Side>
      )}

      {/* The chapter bar along the bottom, all film long; at the title, a pointer to it */}
      {t < tl.endCardStart && (
        <ChapterTrack tl={tl} t={t} hint={c.id === "cb00-03" ? window_(t, c.start + 0.4, c.end, 0.5, 0.5) : 0} />
      )}

      {/* Ending: the link again, the question, the end card */}
      {c.id === "cb06-01" && <LinkCard t={t} from={c.start + 0.2} to={c.end} end />}
      {c.id === "cb06-02" && t < tl.endCardStart && (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 260px", opacity: window_(t, c.speech.start, tl.endCardStart, 0.8, 0.5) }}>
          <Bi en={c.en} zh={c.zh} size={52} weight={700} align="center" style={{ textShadow: "0 4px 24px rgba(0,0,0,.8)" }} />
        </AbsoluteFill>
      )}
      {t >= tl.endCardStart && (
        <AbsoluteFill style={{ opacity: rise(t, tl.endCardStart, tl.endCardStart + 0.6) }}>
          <AbsoluteFill style={{ background: NIGHT, opacity: 0.75 }} />
          <Title t={t} from={tl.endCardStart} qr />
        </AbsoluteFill>
      )}
      {/* The film opens on a dim cube rather than black (the delivery check allows no black frames). */}
      {t < tl.leadIn && <AbsoluteFill style={{ background: NIGHT, opacity: 0.8 * (1 - rise(t, 0, tl.leadIn)) }} />}
      {tl.draft && (
        <div style={{ position: "absolute", right: 24, bottom: 16, fontFamily: MONO, fontSize: 22, color: AMBER, opacity: 0.8 }}>DRAFT timeline</div>
      )}
    </AbsoluteFill>
  );
};

/** The YouTube cover: the question, English first with the Chinese small under it, a scrambled cube, and (owner,
 * 2026-10-25) a badge saying the free online cube comes with it. */
export const Cube2x2Cover: FC = () => (
  <AbsoluteFill style={{ background: NIGHT }}>
    <AbsoluteFill style={{ transform: "translateX(430px) scale(1.08)" }}>
      <Img src={file("footage/hero.jpg")} style={{ width: 1920, height: 1080 }} />
    </AbsoluteFill>
    <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(4,7,13,1) 0%, rgba(4,7,13,.92) 40%, rgba(4,7,13,0) 60%)" }} />
    <AbsoluteFill style={{ justifyContent: "center", paddingLeft: 120 }}>
      <div style={{ fontFamily: EN, fontSize: 122, fontWeight: 800, color: INK, lineHeight: 1.08, maxWidth: 900 }}>
        How Do You Solve a <span style={{ color: AMBER }}>2×2 Cube</span>?
      </div>
      <div style={{ fontFamily: ZH, fontSize: 64, fontWeight: 600, color: MUTED, marginTop: 30 }}>二阶魔方怎么还原？</div>
      {/* The owner's one addition to the question (2026-10-25): the film comes with the free web cube. */}
      <div style={{ alignSelf: "flex-start", marginTop: 44, padding: "16px 34px 18px", borderRadius: 30, background: MINT, color: "#06120c" }}>
        <div style={{ fontFamily: EN, fontSize: 46, fontWeight: 800 }}>✓ Free online cube included</div>
        <div style={{ fontFamily: ZH, fontSize: 30, fontWeight: 700, opacity: 0.8, marginTop: 2 }}>附免费网页魔方</div>
      </div>
    </AbsoluteFill>
  </AbsoluteFill>
);
