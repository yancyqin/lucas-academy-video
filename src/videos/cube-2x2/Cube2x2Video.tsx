// 「二阶魔方怎么还原？」 / "How Do You Solve a 2×2 Cube?" (CUBE-2X2.md §4).
// Every picture is the cube page itself (inception-space-ui /cube/, "Solve it for me"), recorded frame by
// frame by scripts/cube-2x2/capture.mjs: one continuous solve and three short takes. The film runs each take
// on an eased curve under its lines (build_timeline.py's shots) and draws on top what a learner needs: the
// three stages, the step's moves with the turning one lit, the algorithm's name, how many times round.
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

type Lang = "zh" | "en";
type Cue = { id: string; section: string; zh: string; en: string; start: number; end: number; speech: { start: number; end: number } };
type Shot = { take: string; cues: [string, string]; start: number; end: number; from: number; to: number };
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
  lang: Lang;
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
export type CubeProps = { tl?: CubeTimeline | null; lang?: Lang };

const DIR = "cube-2x2";
const file = (p: string) => staticFile(`${DIR}/${p}`);
// The cube page's own palette (inception-space-ui cube/styles/cube.css), so the film and the page look alike.
const NIGHT = "#04070d",
  INK = "#f6f8fb",
  MUTED = "#a9b7c8",
  LINE = "rgba(193, 220, 241, 0.22)",
  MINT = "#9ed7bd",
  AMBER = "#f3c46b",
  PANEL = "rgba(10, 18, 30, 0.82)";
/** R L U D F B: red, orange, white, yellow, green, blue (cube/src/view.js). */
const STICKER = ["#d4202f", "#ff7f11", "#f4f6f8", "#ffd60a", "#13a453", "#1565e0"];
const ZH = '"PingFang SC", "Hiragino Sans GB", sans-serif';
const EN = '"Avenir Next", "Helvetica Neue", sans-serif';
const MONO = '"SF Mono", Menlo, monospace';
const XFADE = 0.35;
/** Captions sit in YouTube's bottom band; nothing important goes below this. */
const SAFE_BOTTOM = 150;
/** The right-hand column beside the cube: cards on top, the step's moves below. */
const COLUMN = { right: 80, width: 640 };

const ease = (x: number) => {
  const t = Math.max(0, Math.min(1, x));
  return t * t * (3 - 2 * t);
};
/** 0 → 1 between a and b, eased. */
const rise = (t: number, a: number, b: number) => ease((t - a) / Math.max(0.001, b - a));
/** In over `inn` seconds from a, out over `out` seconds before b. */
const window_ = (t: number, a: number, b: number, inn = 0.4, out = 0.3) => Math.min(rise(t, a, a + inn), 1 - rise(t, b - out, b));

export const calculateCubeMetadata: CalculateMetadataFunction<CubeProps> = async ({ props, abortSignal }) => {
  const response = await fetch(file(`timeline.${props.lang ?? "zh"}.json`), { signal: abortSignal });
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
/** The cube in the middle (title, closing question) or to the left, leaving the right for cards and moves. */
const CENTRE: Layout = { x: 0, y: 0, s: 1 };
const LEFT: Layout = { x: -270, y: -30, s: 0.82 };
const CENTRED = new Set(["cb00-03", "cb06-01"]);
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
  const drift = still ? 1 + 0.04 * (1 - Math.cos(2 * Math.PI * u)) / 2 : 1;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ transform: `translate(${layout.x}px, ${layout.y}px) scale(${layout.s * drift})` }}>
        <Freeze frame={0}>
          <OffthreadVideo src={file(`footage/${shot.take}.mp4`)} muted trimBefore={Math.round(src * tl.fps)} style={{ width: "100%", height: "100%" }} />
        </Freeze>
      </AbsoluteFill>
      {dim > 0 && <AbsoluteFill style={{ background: NIGHT, opacity: dim }} />}
    </AbsoluteFill>
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
      padding: "28px 36px",
      boxShadow: "0 24px 60px rgba(0,0,0,.45)",
      backdropFilter: "blur(6px)",
      ...style,
    }}
  >
    {children}
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
      ...style,
    }}
  />
);

const Words: FC<{ lang: Lang; size?: number; color?: string; weight?: number; style?: CSSProperties; children: ReactNode }> = ({
  lang,
  size = 44,
  color = INK,
  weight = 600,
  style,
  children,
}) => <div style={{ fontFamily: lang === "zh" ? ZH : EN, fontSize: size, color, fontWeight: weight, lineHeight: 1.35, ...style }}>{children}</div>;

const say = (lang: Lang, zh: ReactNode, en: ReactNode) => (lang === "zh" ? zh : en);

// ------------------------------------------------------------------ the solve's overlays

const STAGES = {
  zh: ["白色的一层", "顶面全黄", "换好四个角"],
  en: ["The white layer", "A yellow top", "The last corners"],
};
const ALG = {
  "R U R' U'": { zh: "小动作", en: "The little move" },
  "R U R' U R U2 R'": { zh: "小鱼公式 · Sune", en: "Sune" },
  "R' F R' B2 R F' R' B2 R2": { zh: "换角公式", en: "The corner algorithm" },
} as Record<string, { zh: string; en: string }>;

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

const StageBar: FC<{ lang: Lang; stage: number; t: number; from: number }> = ({ lang, stage, t, from }) => (
  <div style={{ position: "absolute", left: 60, top: 54, display: "flex", gap: 14, opacity: rise(t, from, from + 0.5) }}>
    {STAGES[lang].map((name, i) => (
      <div
        key={name}
        style={{
          padding: "10px 22px",
          borderRadius: 999,
          border: `2px solid ${i === stage ? MINT : LINE}`,
          background: i < stage ? "rgba(158,215,189,.14)" : i === stage ? "rgba(158,215,189,.22)" : "rgba(10,18,30,.6)",
          color: i === stage ? INK : i < stage ? MINT : MUTED,
          fontFamily: lang === "zh" ? ZH : EN,
          fontWeight: 700,
          fontSize: 30,
        }}
      >
        {i + 1} · {name}
        {i < stage ? " ✓" : ""}
      </div>
    ))}
  </div>
);

/** A step with no algorithm is either holding the cube a new way or lining up the top. */
const plainStep = (labels: string[], lang: Lang) =>
  labels.every((l) => /^[xyz]/.test(l))
    ? { zh: "转动整个魔方", en: "Turn the whole cube" }[lang]
    : labels.every((l) => /^U/.test(l))
      ? { zh: "转动顶层", en: "Turn the top" }[lang]
      : null;

const StepStrip: FC<{ lang: Lang; at: NonNullable<ReturnType<typeof solveAt>>; opacity: number }> = ({ lang, at, opacity }) => {
  const name = at.step.alg ? ALG[at.step.alg]?.[lang] : plainStep(at.labels, lang);
  const rep = repetition(at.labels, at.done, at.turning);
  const size = at.labels.length > 16 ? 36 : at.labels.length > 8 ? 40 : 50;
  return (
    <div style={{ position: "absolute", right: COLUMN.right, width: COLUMN.width, bottom: SAFE_BOTTOM + 30, display: "flex", justifyContent: "center", opacity }}>
      <Panel style={{ width: "100%", padding: "18px 24px", textAlign: "center" }}>
        {(name || rep) && (
          <div style={{ display: "flex", justifyContent: "center", gap: 24, marginBottom: 6 }}>
            {name && <Words lang={lang} size={30} color={AMBER} weight={700}>{name}</Words>}
            {rep && rep.now > 0 && (
              <Words lang={lang} size={30} color={MINT} weight={800}>
                {lang === "zh" ? `第 ${rep.now} 次` : `× ${rep.now}`}
              </Words>
            )}
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

const Title: FC<{ lang: Lang; t: number; from: number }> = ({ lang, t, from }) => (
  <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: rise(t, from, from + 0.7) }}>
    <div style={{ textAlign: "center", transform: `translateY(${(1 - rise(t, from, from + 0.9)) * 24}px)` }}>
      <div style={{ fontFamily: EN, fontSize: 30, letterSpacing: "0.32em", color: MINT, fontWeight: 700, marginBottom: 28 }}>LUCAS ACADEMY</div>
      <Words lang={lang} size={lang === "zh" ? 136 : 108} weight={800}>
        {say(
          lang,
          <>
            <span style={{ color: AMBER }}>二阶魔方</span>怎么还原？
          </>,
          <>
            How Do You Solve a <span style={{ color: AMBER }}>2×2 Cube</span>?
          </>,
        )}
      </Words>
      <div style={{ display: "flex", justifyContent: "center", gap: 14, margin: "40px 0 36px" }}>
        {[2, 4, 0, 3, 5, 1].map((c) => (
          <Sticker key={c} colour={c} size={34} />
        ))}
      </div>
      <Words lang={lang} size={34} color={MUTED} weight={500}>
        {say(lang, "作者 Lucas Academy Team", "By Lucas Academy Team")}
      </Words>
    </div>
  </AbsoluteFill>
);

const Side: FC<{ children: ReactNode; t: number; from: number; to: number; top?: number }> = ({ children, t, from, to, top = 200 }) => (
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

const CountUp: FC<{ lang: Lang; t: number; c: Cue }> = ({ lang, t, c }) => {
  const k = rise(t, c.speech.start + 1.0, c.speech.end - 0.4);
  const value = Math.round(3674160 * k * k);
  return (
    <Side t={t} from={c.speech.start + 0.6} to={c.end} top={360}>
      <Panel style={{ textAlign: "right" }}>
        <div style={{ fontFamily: MONO, fontSize: 96, fontWeight: 800, color: AMBER }}>{value.toLocaleString("en-US")}</div>
        <Words lang={lang} size={38} color={MUTED}>
          {say(lang, "种打乱的样子", "ways to be scrambled")}
        </Words>
      </Panel>
    </Side>
  );
};

const Pairs: FC<{ lang: Lang; t: number; c: Cue }> = ({ lang, t, c }) => {
  const names = { zh: ["白", "黄", "绿", "蓝", "红", "橙"], en: ["white", "yellow", "green", "blue", "red", "orange"] }[lang];
  return (
    <Side t={t} from={c.speech.start} to={c.end} top={300}>
      <Panel>
        {[
          [2, 3],
          [4, 5],
          [0, 1],
        ].map(([a, b], i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 18, margin: "14px 0", opacity: rise(t, c.speech.start + 0.6 + i * 0.9, c.speech.start + 1.1 + i * 0.9) }}>
            <Sticker colour={a} />
            <Words lang={lang} size={34} style={{ width: 110 }}>
              {names[[2, 3, 4, 5, 0, 1].indexOf(a)]}
            </Words>
            <Words lang={lang} size={40} color={MUTED}>
              ⟷
            </Words>
            <Sticker colour={b} />
            <Words lang={lang} size={34} style={{ width: 120 }}>
              {names[[2, 3, 4, 5, 0, 1].indexOf(b)]}
            </Words>
          </div>
        ))}
      </Panel>
    </Side>
  );
};

const NOTATION: Record<string, { zh: string; en: string }> = {
  R: { zh: "右边这一层 · 顺时针", en: "the right layer · clockwise" },
  "R'": { zh: "反着转回来", en: "back the other way" },
  U: { zh: "上面这一层", en: "the top layer" },
  "U'": { zh: "反着转", en: "turned back" },
  R2: { zh: "转半圈", en: "a half turn" },
  y: { zh: "整个魔方一起转", en: "the whole cube turns" },
  "y'": { zh: "整个魔方转回来", en: "and back" },
};

const Letter: FC<{ lang: Lang; take: Take; src: number; t: number; c: Cue }> = ({ lang, take, src, t, c }) => {
  const frame = Math.round(src * take.fps);
  // The move turning now, or the last one turned (it stays up while it rests).
  const move = [...take.moves].reverse().find((m) => m.start < frame) ?? null;
  if (!move?.label) return null;
  const info = NOTATION[move.label];
  return (
    <Side t={t} from={c.start} to={c.end} top={320}>
      <Panel style={{ textAlign: "center", minWidth: 380 }}>
        <div style={{ fontFamily: MONO, fontSize: 170, fontWeight: 800, color: AMBER, lineHeight: 1 }}>{prime(move.label)}</div>
        <Words lang={lang} size={36} color={INK} style={{ marginTop: 14 }}>
          {info?.[lang]}
        </Words>
      </Panel>
    </Side>
  );
};

const Note: FC<{ lang: Lang; t: number; from: number; to: number; title?: ReactNode; children: ReactNode; top?: number; width?: number }> = ({
  lang,
  t,
  from,
  to,
  title,
  children,
  top = 200,
  width = 600,
}) => (
  <Side t={t} from={from} to={to} top={top}>
    <Panel style={{ width }}>
      {title && (
        <Words lang={lang} size={30} color={AMBER} weight={800} style={{ marginBottom: 10 }}>
          {title}
        </Words>
      )}
      <Words lang={lang} size={38}>
        {children}
      </Words>
    </Panel>
  </Side>
);

/** A 2×2 seen from above: four top stickers, each corner's side stickers drawn as bars at its edges. */
const TopView: FC<{ yellow: boolean[]; sides?: Record<number, "left" | "front">; mark?: number; size?: number }> = ({ yellow, sides = {}, mark, size = 200 }) => {
  const cell = size / 2;
  const at = [
    [0, 0],
    [1, 0],
    [0, 1],
    [1, 1],
  ]; // back-left, back-right, front-left, front-right
  return (
    <svg width={size + 60} height={size + 60} viewBox={`-30 -30 ${size + 60} ${size + 60}`}>
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
      <text x={size / 2} y={size + 52} textAnchor="middle" fill={MUTED} fontSize={22} fontFamily={EN}>
        front
      </text>
    </svg>
  );
};

const Headlights: FC<{ lang: Lang; t: number; c: Cue }> = ({ lang, t, c }) => (
  <Side t={t} from={c.speech.start + 0.8} to={c.end} top={150}>
    <Panel style={{ textAlign: "center" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 96px)", gap: 10, justifyContent: "center" }}>
        <Sticker colour={0} size={96} glow />
        <Sticker colour={0} size={96} glow />
        <Sticker colour={4} size={96} style={{ opacity: 0.55 }} />
        <Sticker colour={5} size={96} style={{ opacity: 0.55 }} />
      </div>
      <Words lang={lang} size={36} style={{ marginTop: 18 }}>
        {say(lang, "上面两个角一样 = 车头灯", "Two matching top corners = headlights")}
      </Words>
    </Panel>
  </Side>
);

// ------------------------------------------------------------------ the film

export const Cube2x2Video: FC<CubeProps> = ({ tl }) => {
  const frame = useCurrentFrame(),
    { fps } = useVideoConfig();
  if (!tl) return null;
  const t = frame / fps;
  const lang = tl.lang;
  const byId = Object.fromEntries(tl.cues.map((c) => [c.id, c]));
  const cue = tl.cues.find((c) => c.start <= t && t < c.end) ?? (t < tl.cues[0].start ? tl.cues[0] : tl.cues[tl.cues.length - 1]);
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
  const recap = cue.section === "cb05";
  const at = inSolve ? solveAt(solve, tl.plan, src) : null;
  const firstSolve = byId["cb02-01"];
  const c = cue;
  const card = (id: string) => byId[id];
  const ending = cue.section === "cb06" || t >= tl.endCardStart;
  const layout = t >= tl.endCardStart ? CENTRE : layoutAt(tl.cues, t);

  return (
    <AbsoluteFill style={{ background: NIGHT, color: INK, fontFamily: lang === "zh" ? ZH : EN }}>
      <Audio src={file(`audio/${lang}.mix.wav`)} />
      {crossing && previous && <Footage tl={tl} shot={previous} t={previous.end - 0.01} layout={layout} />}
      <AbsoluteFill style={{ opacity: crossing ? rise(t, shot.start, shot.start + XFADE) : 1 }}>
        <Footage tl={tl} shot={shot} t={t} layout={layout} dim={c.id === "cb00-03" ? 0.72 * rise(t, c.start, c.start + 0.6) : ending ? 0.78 * rise(t, c.start, c.start + 0.8) : 0} />
      </AbsoluteFill>

      {/* Opening */}
      {c.id === "cb00-01" && <CountUp lang={lang} t={t} c={c} />}
      {c.id === "cb00-03" && <Title lang={lang} t={t} from={c.start + 0.3} />}

      {/* Meet the cube */}
      {c.id === "cb01-01" && (
        <Note lang={lang} t={t} from={c.speech.start + 1.5} to={c.end}>
          {say(lang, "没有中心块：8 个角块，每块 3 种颜色", "No centres: 8 corners, 3 colours each")}
        </Note>
      )}
      {c.id === "cb01-02" && <Pairs lang={lang} t={t} c={c} />}
      {shot.take === "notation" && <Letter lang={lang} take={tl.takes.notation} src={src} t={t} c={{ ...c, start: card("cb01-03").start, end: card("cb01-05").end }} />}

      {/* The solve */}
      {inSolve && !recap && at && (
        <>
          <StageBar lang={lang} stage={{ cb02: 0, cb03: 1, cb04: 2 }[c.section] ?? at.stage} t={t} from={firstSolve.start} />
          {!["cb02-03", "cb02-09", "cb03-02", "cb03-03", "cb03-04"].includes(c.id) && <StepStrip lang={lang} at={at} opacity={rise(t, firstSolve.start + 1, firstSolve.start + 1.5)} />}
        </>
      )}
      {inSolve && !recap && !at && c.id === "cb02-01" && <StageBar lang={lang} stage={0} t={t} from={firstSolve.start} />}
      {c.id === "cb02-03" && (
        <Note lang={lang} t={t} from={c.speech.start + 1.2} to={c.end} title={say(lang, "第一块角定下颜色", "The first corner decides")}>
          <div style={{ display: "flex", flexDirection: "column", gap: 14, marginTop: 8 }}>
            <span>
              <Sticker colour={4} size={46} /> {say(lang, "前面：绿色", "Front: green")}
            </span>
            <span>
              <Sticker colour={1} size={46} /> {say(lang, "右边：橙色", "Right: orange")}
            </span>
          </div>
        </Note>
      )}
      {c.id === "cb02-09" && (
        <Note lang={lang} t={t} from={c.start + 0.3} to={c.end} title={say(lang, "小提示", "A tip")} width={700}>
          {say(lang, "白色角卡在下面不对的位置？转到右前方，先做一次 R U R′ 把它请出来。", "A white corner stuck in the wrong bottom spot? Turn it to the front right and do R U R′ once to lift it out.")}
        </Note>
      )}
      {c.id === "cb03-02" && (
        <div style={{ position: "absolute", right: COLUMN.right, width: COLUMN.width, top: 360, display: "flex", justifyContent: "center", opacity: window_(t, c.speech.start, c.end) }}>
          <Panel style={{ textAlign: "center", width: "100%" }}>
            <Words lang={lang} size={34} color={AMBER} weight={800}>
              {say(lang, "小鱼公式 · Sune", "Sune")}
            </Words>
            <div style={{ marginTop: 8 }}>
              {"R U R′ U R U2 R′".split(" ").map((m, i) => (
                <Chip key={i} size={52}>
                  {m}
                </Chip>
              ))}
            </div>
          </Panel>
        </div>
      )}
      {c.id === "cb03-03" && (
        <Note lang={lang} t={t} from={c.speech.start} to={c.end} title={say(lang, "顶上只有一块黄色", "Exactly one yellow on top")} width={560}>
          <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
            <TopView yellow={[false, false, true, false]} mark={2} size={180} />
            <span>{say(lang, "放在左前方", "put it front-left")}</span>
          </div>
        </Note>
      )}
      {c.id === "cb03-04" && (
        <Note lang={lang} t={t} from={c.speech.start} to={c.end} title={say(lang, "没有，或者有两块", "None, or two")} width={560}>
          <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
            <TopView yellow={[false, false, false, false]} sides={{ 2: "left" }} mark={2} size={180} />
            <span>{say(lang, "左前角的黄色朝左", "front-left corner's yellow faces left")}</span>
          </div>
        </Note>
      )}
      {c.id === "cb04-02" && <Headlights lang={lang} t={t} c={c} />}
      {c.id === "cb04-04" && (
        <Note lang={lang} t={t} from={c.speech.start} to={c.end} title={say(lang, "没有车头灯？", "No headlights?")}>
          {say(lang, "先在随便哪一面做一次换角公式，车头灯就出来了。", "Do the corner algorithm once from anywhere, and they appear.")}
        </Note>
      )}

      {/* Once more */}
      {recap && inSolve && (
        <>
          <StageBar lang={lang} stage={solveAt(solve, tl.plan, src)?.stage ?? 0} t={t} from={byId["cb05-01"].start} />
          <div style={{ position: "absolute", right: 70, top: 60, fontFamily: MONO, fontSize: 40, color: MUTED, opacity: rise(t, byId["cb05-01"].start, byId["cb05-01"].start + 0.5) }}>
            {lang === "zh" ? "快放" : "fast"} ×{((shot.to - shot.from) / (shot.end - shot.start)).toFixed(1)}
          </div>
        </>
      )}
      {c.id === "cb05-02" && (
        <div style={{ position: "absolute", right: COLUMN.right, width: COLUMN.width, top: 420, display: "flex", justifyContent: "center", opacity: window_(t, c.speech.start + 2, c.end) }}>
          <Panel style={{ textAlign: "center", width: "100%" }}>
            <div style={{ fontFamily: MONO, fontSize: 44, color: MINT, fontWeight: 700 }}>is.lucasacademy.org/cube</div>
            <Words lang={lang} size={30} color={MUTED} style={{ marginTop: 6 }}>
              {say(lang, "点「Solve it for me」，一步一步看", "Press “Solve it for me” and watch it step by step")}
            </Words>
          </Panel>
        </div>
      )}

      {/* The question that ends the film */}
      {c.id === "cb06-01" && t < tl.endCardStart && (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 300px", opacity: window_(t, c.speech.start, tl.endCardStart, 0.8, 0.5) }}>
          <Words lang={lang} size={lang === "zh" ? 58 : 50} weight={700} style={{ textAlign: "center", textShadow: "0 4px 24px rgba(0,0,0,.8)" }}>
            {c[lang]}
          </Words>
        </AbsoluteFill>
      )}
      {t >= tl.endCardStart && (
        <AbsoluteFill style={{ opacity: rise(t, tl.endCardStart, tl.endCardStart + 0.6) }}>
          <AbsoluteFill style={{ background: NIGHT, opacity: 0.7 }} />
          <Title lang={lang} t={t} from={tl.endCardStart} />
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

/** The YouTube cover: the question and a scrambled cube, nothing else (README "YouTube covers"; one language each). */
export const Cube2x2Cover: FC<{ lang: Lang }> = ({ lang }) => (
  <AbsoluteFill style={{ background: NIGHT }}>
    <AbsoluteFill style={{ transform: "translateX(430px) scale(1.08)" }}>
      <Img src={file("footage/hero.jpg")} style={{ width: 1920, height: 1080 }} />
    </AbsoluteFill>
    <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(4,7,13,1) 0%, rgba(4,7,13,.92) 38%, rgba(4,7,13,0) 58%)" }} />
    <AbsoluteFill style={{ justifyContent: "center", paddingLeft: 120 }}>
      <Words lang={lang} size={lang === "zh" ? 150 : 118} weight={800} style={{ maxWidth: lang === "zh" ? 760 : 900 }}>
        {say(
          lang,
          <>
            <span style={{ color: AMBER }}>二阶魔方</span>
            <br />
            怎么还原？
          </>,
          <>
            How Do You Solve a <span style={{ color: AMBER }}>2×2 Cube</span>?
          </>,
        )}
      </Words>
    </AbsoluteFill>
  </AbsoluteFill>
);
