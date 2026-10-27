// "How Do You Solve a 5×5 Cube?" / 「五阶魔方怎么还原？」 (CUBE-5X5.md §4): the cube series' second film, made like
// the 2×2 one (one picture, English first, a Chinese audio track; English leads on screen, Chinese small under it;
// the cube small on the left, the cards in the right-hand column; the chapter bar along the bottom). Every picture
// is the cube page itself, recorded by scripts/cube-2x2/capture.mjs --film cube-5x5. What is new is the big cube:
// its three kinds of piece, inner layers in the notation (2R, M, 2-3Rw), the 3×3's seven steps for the frame, and
// the commutators that do the edges and the centres, shown as A, B, A′, B′ over the step's moves.
import type { FC, ReactNode } from "react";
import { AbsoluteFill, Audio, Img, staticFile, useCurrentFrame, useVideoConfig, type CalculateMetadataFunction } from "remotion";
import {
  AMBER,
  Bi,
  CENTRE,
  COLUMN,
  ChapterCard,
  ChapterTrack,
  Chip,
  EN,
  Footage,
  INK,
  LEFT,
  LinkCard,
  MINT,
  MONO,
  MUTED,
  NIGHT,
  Note,
  PAGE,
  Panel,
  SAFE_BOTTOM,
  STICKER,
  Side,
  Sticker,
  Title,
  XFADE,
  ZH,
  faceSign,
  moveAt,
  prime,
  rise,
  sourceAt,
  window_,
  type Cue,
  type CubeMove,
  type CubeProps,
  type CubeTimeline,
  type Layout,
  type PlanStage,
  type Take,
} from "../cube-2x2/Cube2x2Video";

const DIR = "cube-5x5";
const file = (p: string) => staticFile(`${DIR}/${p}`);
const N = 5;
/** Takes that always fill their shot: the slow camera turns. */
const STRETCH = new Set(["hero", "meet", "anatomy"]);
/** The 5×5's number of positions: 8!·3⁷·12!·2¹⁰·24!³ / 4!¹², 75 digits. */
const POSITIONS = "282870942277741856536180333107150328293127731985672134721536000000000000000";

export const calculateCube5x5Metadata: CalculateMetadataFunction<CubeProps> = async ({ props, abortSignal }) => {
  const response = await fetch(file("timeline.json"), { signal: abortSignal });
  if (!response.ok) throw Error("Run c5:timeline first");
  const tl = (await response.json()) as CubeTimeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

const CENTRED = new Set(["cf00-03", "cf00-04", "cf12-03"]);
const layoutAt = (cues: Cue[], t: number): Layout => {
  const i = Math.max(0, cues.findIndex((c) => c.start <= t && t < c.end));
  const target = (k: number) => (k < 0 ? LEFT : CENTRED.has(cues[k].id) ? CENTRE : LEFT);
  const now = target(i);
  const before = target(i - 1);
  const w = i === 0 ? 1 : rise(t, cues[i].start, cues[i].start + 0.9);
  return { x: before.x + (now.x - before.x) * w, y: before.y + (now.y - before.y) * w, s: before.s + (now.s - before.s) * w };
};

// ------------------------------------------------------------------ notation (cube.js formatMove, home frame)

/** A move's name as the cube page writes it (cube.js formatMove): inner layers, wide turns, M E S. */
const moveName = (m: CubeMove, n = N) => {
  const outer = n - 1;
  const index = m.axis;
  const near = [0, 2, 4][index];
  const far = near ^ 1;
  const suffix = (face: number) => (m.quarter === (faceSign(face) > 0 ? 3 : 1) ? "" : m.quarter === 2 ? "2" : "′");
  if (m.lo <= -outer && m.hi >= outer) return "xyz"[index] + suffix(near);
  if (m.lo === 0 && m.hi === 0) return "MES"[index] + suffix(index === 2 ? near : far);
  const depth = (face: number, c: number) => (outer - faceSign(face) * c) / 2 + 1;
  const letterOf = (face: number) => (face === near ? "RUF" : "LDB")[index];
  if (m.lo === m.hi) {
    const face = depth(near, m.lo) <= depth(far, m.lo) ? near : far;
    const layer = depth(face, m.lo);
    return `${layer > 1 ? layer : ""}${letterOf(face)}${suffix(face)}`;
  }
  const touches = (face: number) => (faceSign(face) > 0 ? m.hi : -m.lo) === outer;
  const face = touches(near) ? near : touches(far) ? far : depth(near, m.hi) <= depth(far, m.lo) ? near : far;
  const first = Math.min(depth(face, m.lo), depth(face, m.hi));
  const last = Math.max(depth(face, m.lo), depth(face, m.hi));
  const layers = first === 1 ? (last === 2 ? "" : `${last}`) : `${first}-${last}`;
  return `${layers}${letterOf(face)}w${suffix(face)}`;
};

const NOTATION = /^(\d+)?(?:-(\d+))?([RLUDFBMESxyz])(w)?(['′2])?$/;
/** The move a name stands for (the letters take records names only): the inverse of moveName. */
const parseMove = (label: string, n = N): CubeMove => {
  const found = NOTATION.exec(label);
  if (!found) throw new Error(`not a move: ${label}`);
  const [, a, b, letter, wide, turn = ""] = found;
  const outer = n - 1;
  const quarterOf = (clockwise: number) => (turn === "2" ? 2 : turn ? 4 - clockwise : clockwise);
  if ("xyz".includes(letter)) return { axis: "xyz".indexOf(letter), lo: -outer, hi: outer, quarter: quarterOf(3) };
  // M follows L, E follows D, S follows F.
  if ("MES".includes(letter)) return { axis: "MES".indexOf(letter), lo: 0, hi: 0, quarter: quarterOf(letter === "S" ? 3 : 1) };
  const face = "RLUDFB".indexOf(letter);
  const first = wide ? (b ? Number(a) : 1) : Number(a ?? 1);
  const last = wide ? Number(b ?? a ?? 2) : first;
  const at = (d: number) => faceSign(face) * (outer - 2 * (d - 1));
  return { axis: face >> 1, lo: Math.min(at(first), at(last)), hi: Math.max(at(first), at(last)), quarter: quarterOf(faceSign(face) > 0 ? 3 : 1) };
};

const FACE_NAME: Record<string, [string, string, string, string]> = {
  // [the face, which way round it is seen, "from the …" for a layer count, Chinese count prefix]
  R: ["Right face", "", "from the right", "右"],
  L: ["Left face", " (seen from the left)", "from the left", "左"],
  U: ["Top face (Up)", "", "from the top", "上"],
  D: ["Bottom face (Down)", " (seen from below)", "from the bottom", "下"],
  F: ["Front face", "", "from the front", "前"],
  B: ["Back face", " (seen from behind)", "from the back", "后"],
};
const FACE_ZH: Record<string, [string, string]> = {
  R: ["右面", ""],
  L: ["左面", "（从左边看）"],
  U: ["上面", ""],
  D: ["下面", "（从下面看）"],
  F: ["前面", ""],
  B: ["后面", "（从后面看）"],
};
const ordinal = (k: number) => (k === 1 ? "1st" : k === 2 ? "2nd" : k === 3 ? "3rd" : `${k}th`);

/** What a move means, in both languages (the page's notation, cube/README.md). */
const LIKE: Record<string, string> = { x: "R", y: "U", z: "F", M: "L", E: "D", S: "F" };
const meaning = (label: string): [string, string] => {
  const found = NOTATION.exec(label.replace(/′/g, "'"));
  if (!found) return [label, label];
  const [, a, b, letter, wide, rawTurn = ""] = found;
  const turn = rawTurn === "'" ? "′" : rawTurn;
  if ("xyz".includes(letter) || "MES".includes(letter)) {
    const like = LIKE[letter] + turn;
    return "xyz".includes(letter)
      ? [`The whole cube, turned like ${like}`, `整个魔方，像 ${like} 一样转`]
      : [`The middle layer, turned like ${like}`, `正中间那一层，跟 ${like} 同向`];
  }
  const [faceEn, seenEn, fromEn, zhFrom] = FACE_NAME[letter];
  const [faceZh, seenZh] = FACE_ZH[letter];
  let en = faceEn;
  let zh = faceZh;
  if (wide) {
    const first = b ? Number(a) : 1;
    const last = Number(b ?? a ?? 2);
    [en, zh] = first === 1 ? [`The ${fromEn.slice(9)} ${last} layers`, `${zhFrom}边 ${last} 层`] : [`Layers ${first}–${last} ${fromEn}`, `${zhFrom}数第 ${first}–${last} 层`];
  } else if (a) {
    [en, zh] = [`The ${ordinal(Number(a))} layer ${fromEn}`, `${zhFrom}数第 ${a} 层`];
  }
  if (turn === "2") return [`${en} · a half turn`, `${zh} · 转半圈`];
  if (turn === "′") return [`${en} · counterclockwise${seenEn}`, `${zh} · 逆时针${seenZh}`];
  return [`${en} · clockwise${seenEn}`, `${zh} · 顺时针${seenZh}`];
};

/**
 * A little 5×5 drawn from above-front-right (top white, front green, right red): the turning layers lit, the rest
 * dimmed, and an arrow showing which way the front (or top) stickers travel.
 */
const MoveIcon: FC<{ move: CubeMove; size?: number }> = ({ move, size = 230 }) => {
  const h = N / 2;
  const k = size / (N * 2.2);
  const P = (x: number, y: number, z: number) => [size / 2 + (x - z) * 0.866 * k, size / 2 + ((x + z) * 0.5 - y) * k];
  const poly = (pts: number[][]) => pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const lit = (c: number[]) => 2 * c[move.axis] >= move.lo - 0.01 && 2 * c[move.axis] <= move.hi + 0.01;
  const g = 0.1;
  const stickers: { pts: number[][]; colour: number; on: boolean }[] = [];
  for (let i = 0; i < N; i += 1) {
    for (let j = 0; j < N; j += 1) {
      const a = -h + i;
      const b = -h + j;
      stickers.push({ pts: [P(a + g, h, b + g), P(a + 1 - g, h, b + g), P(a + 1 - g, h, b + 1 - g), P(a + g, h, b + 1 - g)], colour: 2, on: lit([a + 0.5, h - 0.5, b + 0.5]) });
      stickers.push({ pts: [P(a + g, b + g, h), P(a + 1 - g, b + g, h), P(a + 1 - g, b + 1 - g, h), P(a + g, b + 1 - g, h)], colour: 4, on: lit([a + 0.5, b + 0.5, h - 0.5]) });
      stickers.push({ pts: [P(h, b + g, a + g), P(h, b + g, a + 1 - g), P(h, b + 1 - g, a + 1 - g), P(h, b + 1 - g, a + g)], colour: 0, on: lit([h - 0.5, b + 0.5, a + 0.5]) });
    }
  }
  // The arrow, at the middle of the turning layers: a quarter turn about +axis (right-hand rule) carries the front
  // stickers down for x, right for y, and the top stickers left for z; the other way round for quarter 3.
  const c = (move.lo + move.hi) / 4;
  const sign = move.quarter === 1 ? 1 : -1;
  const reach = 0.78 * h;
  const lift = h + 0.04;
  const ends: [number[], number[]] =
    move.axis === 0
      ? [[c, sign * reach, lift], [c, -sign * reach, lift]]
      : move.axis === 1
        ? [[-sign * reach, c, lift], [sign * reach, c, lift]]
        : [[sign * reach, lift, c], [-sign * reach, lift, c]];
  const [x0, y0] = P(ends[0][0], ends[0][1], ends[0][2]);
  const [x1, y1] = P(ends[1][0], ends[1][1], ends[1][2]);
  const angle = Math.atan2(y1 - y0, x1 - x0);
  const head = k * 0.95;
  const tip = (da: number) => [x1 - head * Math.cos(angle + da), y1 - head * Math.sin(angle + da)];
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ flexShrink: 0 }}>
      {stickers.map((s, i) => (
        <polygon key={i} points={poly(s.pts)} fill={STICKER[s.colour]} opacity={s.on ? 1 : 0.2} stroke="#0b0e13" strokeWidth={1.5} />
      ))}
      <line x1={x0} y1={y0} x2={x1} y2={y1} stroke={AMBER} strokeWidth={k * 0.42} strokeLinecap="round" />
      <polygon points={poly([[x1, y1], tip(0.55), tip(-0.55)])} fill={AMBER} stroke={AMBER} strokeWidth={4} strokeLinejoin="round" />
      {move.quarter === 2 && (
        <text x={x1 + 8} y={y1 - 14} fill={AMBER} fontFamily={MONO} fontWeight={800} fontSize={k * 1.4}>
          ×2
        </text>
      )}
    </svg>
  );
};

/** The move card: the name, what it means in both languages, and the little cube. */
const MoveCard: FC<{ label: string; move: CubeMove; opacity: number; top: number; big?: boolean }> = ({ label, move, opacity, top, big }) => {
  const [en, zh] = meaning(label);
  return (
    <div style={{ position: "absolute", top, right: COLUMN.right, width: COLUMN.width, display: "flex", justifyContent: "center", opacity }}>
      <Panel style={{ width: COLUMN.width - 60, display: "flex", alignItems: "center", gap: 28, padding: "18px 28px" }}>
        <MoveIcon move={move} size={big ? 230 : 180} />
        <div>
          <div style={{ fontFamily: MONO, fontSize: big ? 120 : label.length > 4 ? 72 : 92, fontWeight: 800, color: AMBER, lineHeight: 1 }}>{label}</div>
          <Bi en={en} zh={zh} size={big ? 34 : 29} weight={650} style={{ marginTop: 10 }} />
        </div>
      </Panel>
    </div>
  );
};

// ------------------------------------------------------------------ the solve's overlays

/** The solver's named algorithms (cube/src/solver/beginner.js ALGORITHMS). */
const ALG: Record<string, [string, string]> = {
  "R U R' U'": ["The little move", "小动作"],
  "U R U' R' U' F' U F": ["Middle edge, to the right", "中层棱，往右"],
  "U' L' U L U F U' F'": ["Middle edge, to the left", "中层棱，往左"],
  "F R U R' U' F'": ["The cross algorithm", "十字公式"],
  "R U R' U R U2 R'": ["Sune", "小鱼公式"],
  "R' F R' B2 R F' R' B2 R2": ["The corner algorithm", "换角公式"],
  "R U' R U R U R U' R' U' R2": ["The edge algorithm", "换棱公式"],
};

/** Part, step and title of each stage (the solve plan's keys). */
const STAGES: Record<string, { part: number; step?: number; en: string; zh: string }> = {
  "frame-cross": { part: 1, step: 1, en: "White cross", zh: "白色十字" },
  "frame-corners": { part: 1, step: 2, en: "White corners", zh: "白色的角" },
  "frame-middle": { part: 1, step: 3, en: "Middle layer", zh: "中间层" },
  "frame-yellow-cross": { part: 1, step: 4, en: "Yellow cross", zh: "黄色十字" },
  "frame-yellow-face": { part: 1, step: 5, en: "Yellow face", zh: "顶面全黄" },
  "frame-yellow-corners": { part: 1, step: 6, en: "Yellow corners", zh: "黄色的角" },
  "frame-yellow-edges": { part: 1, step: 7, en: "Yellow edges", zh: "黄色的棱" },
  parity: { part: 2, en: "Parity check", zh: "奇偶检查" },
  edges: { part: 2, en: "Edges", zh: "边" },
  "centre-2": { part: 3, en: "Yellow centre", zh: "黄色中心" },
  "centre-3": { part: 3, en: "White centre", zh: "白色中心" },
  "centre-4": { part: 3, en: "Red centre", zh: "红色中心" },
  "centre-0": { part: 3, en: "Green centre", zh: "绿色中心" },
  "centre-5": { part: 3, en: "Orange centre", zh: "橙色中心" },
};
const PARTS: Record<number, [string, string]> = { 1: ["Part 1 · The frame", "第一部分 · 骨架"], 2: ["Part 2 · The edges", "第二部分 · 边"], 3: ["Part 3 · The centres", "第三部分 · 中心"] };

type Group = { label: string; from: number; to: number };
/** A commutator step's moves, as set-up, A, B, A′, B′ and the set-up undone (its alg is "[A, B]"). */
const groupsOf = (step: PlanStage["steps"][number]): Group[] | null => {
  const found = step.alg ? /^\[(.+), (.+)\]$/.exec(step.alg) : null;
  if (!found) return null;
  const count = (text: string) => text.trim().split(/\s+/).length;
  const a = count(found[1]);
  const b = count(found[2]);
  const setup = (step.moves.length - 2 * (a + b)) / 2;
  if (setup < 0 || !Number.isInteger(setup)) return null;
  const out: Group[] = [];
  let at = 0;
  for (const [label, size] of [["set-up", setup], ["A", a], ["B", b], ["A′", a], ["B′", b], ["undo", setup]] as const) {
    if (size > 0) out.push({ label, from: at, to: at + size });
    at += size;
  }
  return out;
};
const GROUP_ZH: Record<string, string> = { "set-up": "准备", A: "A", B: "B", "A′": "撤回 A", "B′": "撤回 B", undo: "撤回准备" };

/** What the solve take shows at a source time: the stage, the step and how far into it (the 2×2 film's rule). */
const solveAt = (take: Take, plan: PlanStage[], src: number) => {
  const frame = Math.round(src * take.fps);
  const turning = take.moves.find((m) => m.start < frame && frame < m.end);
  const next = turning ?? take.moves.find((m) => m.start >= frame);
  const lastDone = [...take.moves].reverse().find((m) => m.end <= frame);
  const sameStep = lastDone && next && lastDone.step === next.step && lastDone.stage === next.stage;
  const resting = lastDone && frame - lastDone.end <= 18;
  // A new stage begins at its event (after its camera move), not as soon as the last one's moves are done.
  const nextStage = next && lastDone && next.stage !== lastDone.stage ? take.stages.find((s) => s.stage === next.stage) : undefined;
  const between = nextStage !== undefined && frame < nextStage.frame;
  const ref = turning ?? (sameStep ? next : resting || between ? lastDone : next ?? lastDone);
  if (!ref || ref.stage === undefined || ref.step === undefined) return null;
  const stage = ref.stage;
  const step = plan[stage].steps[ref.step];
  const labels = step.moves.map((m) => moveName(m));
  const doneCount = take.moves.filter((m) => m.stage === stage && m.step === ref.step && m.end <= frame).length;
  return { stage, key: plan[stage].key, stepIndex: ref.step, steps: plan[stage].steps.length, step, labels, turning: turning ? turning.index ?? -1 : -1, done: doneCount };
};
type At = NonNullable<ReturnType<typeof solveAt>>;

/** Which time round the little move is on, in a step that repeats it. */
const repetition = (labels: string[], done: number, turning: number) => {
  const first = labels.findIndex((_, i) => labels.slice(i, i + 4).join(" ") === "R U R′ U′");
  if (first < 0) return null;
  const count = Math.floor((labels.length - first) / 4);
  const at = turning >= 0 ? turning : done;
  if (at < first) return { now: 0, count };
  return { now: Math.min(count, Math.floor((at - first) / 4) + 1), count };
};

const plainStep = (labels: string[]): [string, string] | null =>
  labels.every((l) => /^[xyz]/.test(l)) ? ["Turn the whole cube", "转动整个魔方"] : labels.every((l) => /^U/.test(l)) ? ["Turn the top", "转动顶层"] : null;

const StepStrip: FC<{ at: At; opacity: number }> = ({ at, opacity }) => {
  const groups = groupsOf(at.step);
  const name: [string, string] | null =
    at.key === "parity" ? ["One inner quarter turn", "里面一层转四分之一圈"] : groups ? ["Commutator", "交换子"] : at.step.alg ? ALG[at.step.alg] ?? null : plainStep(at.labels);
  const rep = repetition(at.labels, at.done, at.turning);
  const size = groups ? (at.labels.some((l) => l.length > 3) ? 28 : 34) : at.labels.length > 16 ? 30 : at.labels.length > 9 ? 34 : 42;
  const chip = (label: string, i: number) => (
    <Chip key={i} size={size} state={i < at.done ? "done" : i === at.turning ? "now" : "next"}>
      {label}
    </Chip>
  );
  return (
    <div style={{ position: "absolute", right: COLUMN.right, width: COLUMN.width, bottom: SAFE_BOTTOM + 20, display: "flex", justifyContent: "center", opacity }}>
      <Panel style={{ width: COLUMN.width - 60, padding: "16px 20px", textAlign: "center" }}>
        {(name || rep) && (
          <div style={{ display: "flex", justifyContent: "center", alignItems: "flex-end", gap: 26, marginBottom: 6 }}>
            {name && <Bi en={name[0]} zh={name[1]} size={28} color={AMBER} weight={800} />}
            {groups && at.step.alg && <div style={{ fontFamily: MONO, fontSize: 28, color: MUTED, fontWeight: 700 }}>{prime(at.step.alg)}</div>}
            {rep && rep.now > 0 && <Bi en={`× ${rep.now}`} zh={`第 ${rep.now} 次`} size={28} color={MINT} weight={800} />}
          </div>
        )}
        {groups ? (
          <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", alignItems: "flex-end", gap: "4px 10px" }}>
            {groups.map((g) => {
              const now = at.turning >= g.from && at.turning < g.to;
              const colour = g.label === "set-up" || g.label === "undo" ? MUTED : g.label.startsWith("A") ? MINT : AMBER;
              return (
                <div key={g.label} style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", borderTop: `4px solid ${colour}`, paddingTop: 4, opacity: now || at.turning < 0 ? 1 : 0.85 }}>
                  <div style={{ fontFamily: EN, fontSize: 24, fontWeight: 800, color: colour, lineHeight: 1.1 }}>
                    {g.label} <span style={{ fontFamily: ZH, fontSize: 18, color: MUTED, fontWeight: 600 }}>{g.label.length > 1 ? GROUP_ZH[g.label] : ""}</span>
                  </div>
                  <div>{at.labels.slice(g.from, g.to).map((label, i) => chip(label, g.from + i))}</div>
                </div>
              );
            })}
          </div>
        ) : (
          <div>{at.labels.map(chip)}</div>
        )}
      </Panel>
    </div>
  );
};

/** Top right through the solve: which part and step this is. */
const StageTag: FC<{ at: At; opacity: number; fast?: number }> = ({ at, opacity, fast }) => {
  const stage = STAGES[at.key];
  if (!stage) return null;
  const [part, partZh] = PARTS[stage.part];
  const counter =
    at.key === "edges" ? [` · ${at.stepIndex + 1} / ${at.steps}`, ` · ${at.stepIndex + 1} / ${at.steps}`] : stage.step ? [` · Step ${stage.step} of 7`, ` · 第 ${stage.step} 步，共 7 步`] : ["", ""];
  return (
    <div style={{ position: "absolute", right: 80, top: 50, textAlign: "right", opacity }}>
      <Bi en={`${part}${stage.part === 1 ? counter[0] : ""}`} zh={`${partZh}${stage.part === 1 ? counter[1] : ""}`} size={28} color={MUTED} align="right" />
      <Bi en={`${stage.en}${stage.part === 2 && at.key === "edges" ? counter[0] : ""}`} zh={stage.zh} size={40} color={INK} weight={800} align="right" style={{ marginTop: 6 }} />
      {fast && fast > 2.5 && <div style={{ fontFamily: MONO, fontSize: 26, color: AMBER, marginTop: 8, fontWeight: 700 }}>▶▶ ×{fast.toFixed(0)}</div>}
    </div>
  );
};

// ------------------------------------------------------------------ cards

/** The 75-digit number writing itself out, three digits at a time, then the dare. */
const BigNumber: FC<{ t: number; c: Cue }> = ({ t, c }) => {
  const groups = POSITIONS.replace(/\B(?=(\d{3})+(?!\d))/g, ",").split(",");
  const k = rise(t, c.speech.start + 0.3, c.speech.start + (c.speech.end - c.speech.start) * 0.4);
  const shown = Math.round(groups.length * k);
  const rows = [0, 5, 10, 15, 20].map((i) => groups.slice(i, i + 5));
  return (
    <Side t={t} from={c.speech.start} to={c.end} top={150}>
      <Panel style={{ textAlign: "center", width: 760 }}>
        <div style={{ fontFamily: MONO, fontSize: 40, fontWeight: 800, color: AMBER, lineHeight: 1.3, textAlign: "left", display: "inline-block" }}>
          {rows.map((row, r) => (
            <div key={r}>
              {row.map((g, i) => (
                <span key={i} style={{ opacity: r * 5 + i < shown ? 1 : 0.08 }}>
                  {g}
                  {r * 5 + i < groups.length - 1 ? "," : ""}
                </span>
              ))}
            </div>
          ))}
        </div>
        <Bi en="ways to scramble it: a 75-digit number" zh="种打乱的样子：一个七十五位数" size={34} color={INK} style={{ marginTop: 16 }} />
        <div style={{ opacity: rise(t, c.speech.start + (c.speech.end - c.speech.start) * 0.5, c.speech.start + (c.speech.end - c.speech.start) * 0.6), marginTop: 20 }}>
          <Bi en="Most people never solve one." zh="大多数人一次都没还原过。" size={36} color={AMBER} weight={800} />
        </div>
      </Panel>
    </Side>
  );
};

type Kind = "frame" | "wing" | "centre";
const kindAt = (i: number, j: number): Kind => {
  const border = (v: number) => v === 0 || v === N - 1;
  if (border(i) && border(j)) return "frame";
  if (border(i) || border(j)) return i === 2 || j === 2 ? "frame" : "wing";
  return i === 2 && j === 2 ? "frame" : "centre";
};
/** One face of the 5×5, its stickers coloured by the kind of piece they belong to; `on` kinds lit. */
const FaceMap: FC<{ on: Kind[]; size?: number }> = ({ on, size = 230 }) => {
  const cell = size / N;
  const colour: Record<Kind, string> = { frame: AMBER, wing: MINT, centre: "#7fb2ff" };
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ flexShrink: 0 }}>
      {Array.from({ length: N * N }, (_, n) => {
        const i = n % N;
        const j = Math.floor(n / N);
        const kind = kindAt(i, j);
        return <rect key={n} x={i * cell + 4} y={j * cell + 4} width={cell - 8} height={cell - 8} rx={8} fill={on.includes(kind) ? colour[kind] : "#2a3240"} />;
      })}
    </svg>
  );
};

const ANATOMY: Record<string, { on: Kind[]; title: [string, string]; body: [string, string] }> = {
  "cf01-01": { on: ["frame"], title: ["The frame = a 3×3", "骨架 = 一个三阶"], body: ["8 corners · 12 edge middles · 6 centres", "8 个角 · 12 个棱中块 · 6 个中心"] },
  "cf01-02": { on: ["wing"], title: ["Edge wings · 24", "边翼 · 24 块"], body: ["Two beside each edge middle", "每个棱中块两边各一块"] },
  "cf01-03": { on: ["centre"], title: ["Centre pieces · 48", "中心块 · 48 块"], body: ["Eight around each face's centre", "每面中心周围八块"] },
};

/** The three parts, the one being worked on lit. */
const PlanCard: FC<{ t: number; from: number; to: number; now?: number; top?: number }> = ({ t, from, to, now, top = 230 }) => (
  <Side t={t} from={from} to={to} top={top}>
    <Panel style={{ width: COLUMN.width - 60 }}>
      {(
        [
          [1, "The frame", "骨架", "like a 3×3", "像拼三阶一样", "frame"],
          [2, "The edges", "边", "commutators", "交换子", "wing"],
          [3, "The centres", "中心", "commutators", "交换子", "centre"],
        ] as const
      ).map(([n, en, zh, howEn, howZh, kind]) => (
        <div key={n} style={{ display: "flex", alignItems: "center", gap: 22, margin: "12px 0", opacity: !now || now === n ? 1 : 0.4 }}>
          <div style={{ fontFamily: EN, fontSize: 64, fontWeight: 800, color: kind === "frame" ? AMBER : kind === "wing" ? MINT : "#7fb2ff", width: 54 }}>{n}</div>
          <FaceMap on={[kind]} size={92} />
          <Bi en={`${en} · ${howEn}`} zh={`${zh} · ${howZh}`} size={34} weight={700} />
        </div>
      ))}
    </Panel>
  </Side>
);

/** A 3×3 top seen from above: which stickers are yellow, and corners' side stickers as bars at the edge. */
const TopGrid: FC<{ yellow: number[]; sides?: Record<number, "left" | "front">; mark?: number; size?: number; label?: string }> = ({ yellow, sides = {}, mark, size = 150, label }) => {
  const cell = size / 3;
  return (
    <svg width={size + 50} height={size + (label ? 76 : 50)} viewBox={`-25 -25 ${size + 50} ${size + (label ? 76 : 50)}`} style={{ flexShrink: 0 }}>
      {Array.from({ length: 9 }, (_, n) => (
        <rect key={n} x={(n % 3) * cell + 4} y={Math.floor(n / 3) * cell + 4} width={cell - 8} height={cell - 8} rx={8} fill={yellow.includes(n) ? STICKER[3] : "#3a4352"} stroke={n === mark ? MINT : "none"} strokeWidth={6} />
      ))}
      {Object.entries(sides).map(([n, where]) => {
        const x = Number(n) % 3;
        const y = Math.floor(Number(n) / 3);
        return where === "left" ? (
          <rect key={`s${n}`} x={-20} y={y * cell + 10} width={12} height={cell - 20} rx={5} fill={STICKER[3]} />
        ) : (
          <rect key={`s${n}`} x={x * cell + 10} y={size + 8} width={cell - 20} height={12} rx={5} fill={STICKER[3]} />
        );
      })}
      {label && (
        <text x={size / 2} y={size + 48} textAnchor="middle" fill={MUTED} fontSize={22} fontFamily={EN}>
          {label}
        </text>
      )}
    </svg>
  );
};

const AlgCard: FC<{ t: number; from: number; to: number; name: [string, string]; alg: string; top?: number; children?: ReactNode }> = ({ t, from, to, name, alg, top = 150, children }) => (
  <Side t={t} from={from} to={to} top={top}>
    <Panel style={{ textAlign: "center", width: COLUMN.width - 60 }}>
      <Bi en={name[0]} zh={name[1]} size={36} color={AMBER} weight={800} />
      <div style={{ marginTop: 10 }}>
        {alg.split(" ").map((m, i) => (
          <Chip key={i} size={alg.split(" ").length > 9 ? 40 : 48}>
            {m}
          </Chip>
        ))}
      </div>
      {children}
    </Panel>
  </Side>
);

const Headlights: FC<{ t: number; c: Cue }> = ({ t, c }) => (
  <Side t={t} from={c.speech.start + 0.8} to={c.end} top={230}>
    <Panel style={{ textAlign: "center", width: 640 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 84px)", gap: 10, justifyContent: "center" }}>
        <Sticker colour={0} size={84} glow />
        <Sticker colour={5} size={84} style={{ opacity: 0.55 }} />
        <Sticker colour={0} size={84} glow />
      </div>
      <Bi en="Two matching top corners = headlights" zh="上面两个角一样 = 车头灯" size={34} style={{ marginTop: 18 }} />
    </Panel>
  </Side>
);

const CommutatorCard: FC<{ t: number; from: number; to: number }> = ({ t, from, to }) => {
  const parts = [
    ["A", "do", "做", MINT],
    ["B", "do", "做", AMBER],
    ["A′", "undo", "撤回", MINT],
    ["B′", "undo", "撤回", AMBER],
  ] as const;
  const span = Math.max(0.1, to - from - 1);
  return (
    <Side t={t} from={from} to={to} top={230}>
      <Panel style={{ textAlign: "center", width: COLUMN.width - 60 }}>
        <Bi en="The commutator" zh="交换子" size={36} color={AMBER} weight={800} />
        <div style={{ display: "flex", justifyContent: "center", gap: 26, margin: "20px 0 14px" }}>
          {parts.map(([letter, en, zh, colour], i) => (
            <div key={letter} style={{ opacity: rise(t, from + (span * i) / 5, from + (span * i) / 5 + 0.4) }}>
              <div style={{ fontFamily: MONO, fontSize: 92, fontWeight: 800, color: colour, lineHeight: 1 }}>{letter}</div>
              <Bi en={en} zh={zh} size={28} align="center" />
            </div>
          ))}
        </div>
        <div style={{ opacity: rise(t, from + span * 0.8, from + span * 0.8 + 0.5) }}>
          <Bi en="→ only three pieces trade places" zh="→ 只有三块交换位置" size={34} weight={700} color={INK} />
        </div>
      </Panel>
    </Side>
  );
};

/** The centres in the solve's order, the one being solved lit, the done ones ticked; blue finishes by itself. */
const CENTRE_ORDER: [string, number, string, string][] = [
  ["centre-2", 3, "Yellow", "黄"],
  ["centre-3", 2, "White", "白"],
  ["centre-4", 0, "Red", "红"],
  ["centre-0", 4, "Green", "绿"],
  ["centre-5", 1, "Orange", "橙"],
  ["", 5, "Blue", "蓝"],
];
const CentreList: FC<{ at: At | null; t: number; from: number; to: number }> = ({ at, t, from, to }) => {
  const now = at ? CENTRE_ORDER.findIndex(([key]) => key === at.key) : -1;
  return (
    <Side t={t} from={from} to={to} top={230}>
      <Panel style={{ width: 560 }}>
        {CENTRE_ORDER.map(([key, colour, en, zh], i) => {
          const done = at === null || i < now;
          const on = i === now;
          return (
            <div key={en} style={{ display: "flex", alignItems: "center", gap: 18, margin: "8px 0", opacity: done || on ? 1 : 0.45 }}>
              <Sticker colour={colour} size={44} glow={on} />
              <Bi en={key ? en : `${en} · by itself`} zh={key ? zh : `${zh} · 自己完成`} size={30} weight={on ? 800 : 600} />
              {done && <span style={{ marginLeft: "auto", fontSize: 34, color: MINT }}>✓</span>}
            </div>
          );
        })}
      </Panel>
    </Side>
  );
};

/** The film's chapters, as YouTube shows them (package.py writes the same starts into the description). */
const CHAPTER_NAMES: Record<string, [string, string]> = {
  cf00: ["Challenge", "挑战"],
  cf01: ["The idea", "一张图看懂"],
  cf02: ["Letters", "字母"],
  cf03: ["Cross", "白十字"],
  cf04: ["Corners", "白角"],
  cf05: ["Middle", "中层"],
  cf06: ["Yellow\ncross", "黄十字"],
  cf07: ["Yellow\nface", "顶面全黄"],
  cf08: ["Yellow\ncorners", "黄角"],
  cf09: ["Yellow\nedges", "黄棱"],
  cf10: ["Part 2\nEdges", "第二部分 · 边"],
  cf11: ["Part 3\nCentres", "第三部分 · 中心"],
  cf12: ["Replay &\ntry online", "回顾 · 网上练"],
};

// ------------------------------------------------------------------ the film

export const Cube5x5Video: FC<CubeProps> = ({ tl, track = "en" }) => {
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
  const src = sourceAt(shot, t, STRETCH);
  const solve = tl.takes.solve;
  const inSolve = shot.take === "solve" && t < tl.endCardStart;
  // The opening and the replay fly past; once the cube is solved (cf11-04) there is no stage to name.
  const fastRun = c.section === "cf00" || c.section === "cf12" || c.id === "cf11-04";
  const speed = (shot.to - shot.from) / Math.max(0.1, shot.end - shot.start);
  const at = inSolve ? solveAt(solve, tl.plan, src) : null;
  const ending = c.id === "cf12-03" || t >= tl.endCardStart;
  const layout = t >= tl.endCardStart ? CENTRE : shot.take === "page" ? PAGE : layoutAt(tl.cues, t);
  // The move card: whenever a take is turning a move (and a moment after), in the letters and in the solve, except
  // where the moves fly past too fast to read (the opening, the fast stretches, the replay).
  const take = tl.takes[shot.take];
  const lettersPart = shot.take === "letters";
  const srcFrame = Math.round(src * (take?.fps ?? 30));
  const slow = inSolve && !fastRun && speed < 2.6;
  const turningNow = take && (lettersPart || slow) ? moveAt(take, srcFrame, lettersPart ? 40 : 14) : null;
  const cardMove = turningNow ? (turningNow.move ?? (turningNow.label ? parseMove(turningNow.label) : null)) : null;
  const cardLabel = turningNow ? (turningNow.move ? moveName(turningNow.move) : turningNow.label ? prime(turningNow.label) : null) : null;
  // Lines whose card stands in for the step strip.
  const rulesOnly = ["cf03-01", "cf06-01", "cf07-01", "cf07-02", "cf08-01", "cf09-02", "cf10-01", "cf10-02", "cf10-05", "cf11-01", "cf11-04"].includes(c.id);
  const part1 = byId["cf03-01"];

  return (
    <AbsoluteFill style={{ background: NIGHT, color: INK, fontFamily: EN }}>
      <Audio src={file(`audio/${track}.mix.wav`)} />
      {crossing && previous && (
        <Footage tl={tl} shot={previous} t={previous.end - 0.01} layout={previous.take === "page" ? PAGE : layoutAt(tl.cues, previous.end - 0.01)} dir={DIR} stretch={STRETCH} />
      )}
      <AbsoluteFill style={{ opacity: crossing ? rise(t, shot.start, shot.start + XFADE) : 1 }}>
        <Footage
          tl={tl}
          shot={shot}
          t={t}
          layout={layout}
          dir={DIR}
          stretch={STRETCH}
          dim={c.section === "cf00" && CENTRED.has(c.id) ? 0.72 * rise(t, byId["cf00-03"].start, byId["cf00-03"].start + 0.6) : ending ? 0.78 * rise(t, c.start, c.start + 0.8) : 0}
        />
      </AbsoluteFill>

      {/* Opening: the payoff and the dare, the page and its guide, the title and the skip hint */}
      {c.id === "cf00-01" && <BigNumber t={t} c={c} />}
      {c.id === "cf00-02" && <LinkCard t={t} from={c.start + 0.2} to={c.end} />}
      {(c.id === "cf00-03" || c.id === "cf00-04") && <Title t={t} from={byId["cf00-03"].start + 0.2} size={5} zh="五阶魔方怎么还原？" />}

      {/* The idea: three kinds of piece, then the three parts */}
      {ANATOMY[c.id] && (
        <Side t={t} from={c.start + 0.2} to={c.end} top={230}>
          <Panel style={{ width: COLUMN.width - 60, display: "flex", alignItems: "center", gap: 30 }}>
            <FaceMap on={ANATOMY[c.id].on} />
            <div>
              <Bi en={ANATOMY[c.id].title[0]} zh={ANATOMY[c.id].title[1]} size={44} color={AMBER} weight={800} />
              <Bi en={ANATOMY[c.id].body[0]} zh={ANATOMY[c.id].body[1]} size={30} weight={600} style={{ marginTop: 14 }} />
            </div>
          </Panel>
        </Side>
      )}
      {c.id === "cf01-04" && <PlanCard t={t} from={c.start + 0.2} to={c.end} />}

      {/* The letters: a card for each move as it turns */}
      {lettersPart && (
        <Note t={t} from={byId["cf02-01"].speech.start + 0.5} to={byId["cf02-02"].end} top={110} title={["Every move gets its card", "每个转动都有卡片"]}>
          {c.id === "cf02-02" ? ["A number in front picks an inner layer.", "字母前面的数字：第几层。"] : ["No need to memorise: it shows up every time.", "不用背：每次用到都会出现。"]}
        </Note>
      )}

      {/* The three parts */}
      {c.id === "cf03-01" && <ChapterCard t={t} from={c.start} number="PART 1" en="The Frame" zh="第一部分 · 骨架，像拼三阶一样" />}
      {c.id === "cf10-01" && <ChapterCard t={t} from={c.start} number="PART 2" en="The Edges" zh="第二部分 · 拼边" />}
      {c.id === "cf11-01" && <ChapterCard t={t} from={c.start} number="PART 3" en="The Centres" zh="第三部分 · 拼中心" />}
      {inSolve && !fastRun && at && t > part1.start + 3.2 && <StageTag at={at} opacity={rise(t, part1.start + 3.2, part1.start + 3.8)} fast={speed} />}
      {inSolve && !fastRun && at && !rulesOnly && speed < 6 && t > part1.start + 3.2 && <StepStrip at={at} opacity={rise(t, part1.start + 3.2, part1.start + 3.8)} />}
      {cardLabel && cardMove && !rulesOnly && (
        <MoveCard label={cardLabel} move={cardMove} top={lettersPart ? 400 : 380} big={lettersPart} opacity={lettersPart ? window_(t, byId["cf02-01"].start, byId["cf02-02"].end) : 1} />
      )}

      {/* Part 1: each step's rule */}
      {c.id === "cf03-01" && <PlanCard t={t} from={c.start + 3.0} to={c.end} now={1} />}
      {c.id === "cf06-01" && (
        <AlgCard t={t} from={c.speech.start} to={c.end} name={["The cross algorithm", "十字公式"]} alg="F R U R′ U′ F′" top={230}>
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", marginTop: 14 }}>
            <TopGrid yellow={[4]} label="dot · 点" size={110} />
            <span style={{ fontSize: 40, color: MUTED }}>→</span>
            <TopGrid yellow={[1, 3, 4]} label="L" size={110} />
            <span style={{ fontSize: 40, color: MUTED }}>→</span>
            <TopGrid yellow={[3, 4, 5]} label="line · 线" size={110} />
            <span style={{ fontSize: 40, color: MUTED }}>→</span>
            <TopGrid yellow={[1, 3, 4, 5, 7]} label="cross · 十字" size={110} />
          </div>
        </AlgCard>
      )}
      {c.id === "cf07-01" && <AlgCard t={t} from={c.speech.start} to={c.end} name={["Sune", "小鱼公式"]} alg="R U R′ U R U2 R′" top={250} />}
      {c.id === "cf07-02" && (
        <Side t={t} from={c.start + 0.2} to={c.end} top={230}>
          <Panel style={{ width: COLUMN.width - 60, display: "flex", justifyContent: "space-around" }}>
            <div style={{ textAlign: "center" }}>
              <TopGrid yellow={[1, 3, 4, 5, 7, 6]} mark={6} size={170} />
              <Bi en="Exactly one: front left" zh="只有一个：放左前方" size={28} align="center" />
            </div>
            <div style={{ textAlign: "center" }}>
              <TopGrid yellow={[1, 3, 4, 5, 7]} sides={{ 6: "left" }} mark={6} size={170} />
              <Bi en="None or two: yellow faces left" zh="没有或两个：黄色朝左" size={28} align="center" />
            </div>
          </Panel>
        </Side>
      )}
      {c.id === "cf08-01" && <Headlights t={t} c={c} />}
      {c.id === "cf09-02" && (
        <Note t={t} from={c.start + 0.2} to={c.end} title={["The frame is solved", "骨架完成"]} top={230}>
          {["It looks just like a 3×3. Left: the wings and the centres.", "看起来就是一个三阶。剩下：边翼和中心块。"]}
        </Note>
      )}

      {/* Part 2: the commutator, the parity check, one slowly, the rest fast */}
      {c.id === "cf10-01" && <PlanCard t={t} from={c.start + 3.0} to={c.end} now={2} />}
      {c.id === "cf10-02" && <CommutatorCard t={t} from={c.speech.start} to={c.end} />}
      {c.id === "cf10-03" && (
        <Note t={t} from={c.speech.start} to={c.end} title={["Odd order? One inner quarter turn", "单数顺序？里面一层转四分之一圈"]} top={230}>
          {["Three-way swaps can't fix two pieces that are simply swapped.", "三块轮换修不好只有两块对调的情况。"]}
        </Note>
      )}
      {c.id === "cf10-05" && (
        <Note t={t} from={c.start + 0.2} to={c.end} title={["Three wings traded places", "三块边翼换了位置"]} top={230}>
          {["Everything else is back where it was.", "其他所有块都回到了原处。"]}
        </Note>
      )}

      {/* Part 3: one block slowly, then face by face */}
      {c.id === "cf11-01" && <PlanCard t={t} from={c.start + 3.0} to={c.end} now={3} />}
      {(c.id === "cf11-03" || c.id === "cf11-04") && <CentreList at={c.id === "cf11-04" ? null : at} t={t} from={byId["cf11-03"].start + 0.2} to={byId["cf11-04"].end} />}

      {/* Once more */}
      {c.section === "cf12" && inSolve && (
        <>
          <div style={{ position: "absolute", right: 80, top: 56, opacity: rise(t, byId["cf12-01"].start, byId["cf12-01"].start + 0.5) }}>
            <Bi en={`Fast replay ×${speed.toFixed(0)}`} zh="快放" size={34} color={MUTED} align="right" />
          </div>
          <PlanCard t={t} from={byId["cf12-01"].start + 0.3} to={byId["cf12-01"].end} />
        </>
      )}

      {/* The chapter bar along the bottom, all film long; with the title, a pointer to Part 2 */}
      {t < tl.endCardStart && (
        <ChapterTrack
          tl={tl}
          t={t}
          names={CHAPTER_NAMES}
          hint={c.id === "cf00-04" ? window_(t, c.start + 0.2, c.end, 0.5, 0.5) : 0}
          hintText={["Already know the 3×3? Skip to Part 2 ↓", "已经会三阶？点下面直接跳到第二部分"]}
          hintAt={["cf10"]}
        />
      )}

      {/* Ending: the link again, the question, the end card */}
      {c.id === "cf12-02" && <LinkCard t={t} from={c.start + 0.2} to={c.end} end />}
      {c.id === "cf12-03" && t < tl.endCardStart && (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 230px", opacity: window_(t, c.speech.start, tl.endCardStart, 0.8, 0.5) }}>
          <Bi en={c.en} zh={c.zh} size={48} weight={700} align="center" style={{ textShadow: "0 4px 24px rgba(0,0,0,.8)" }} />
        </AbsoluteFill>
      )}
      {t >= tl.endCardStart && (
        <AbsoluteFill style={{ opacity: rise(t, tl.endCardStart, tl.endCardStart + 0.6) }}>
          <AbsoluteFill style={{ background: NIGHT, opacity: 0.75 }} />
          <Title t={t} from={tl.endCardStart} qr size={5} zh="五阶魔方怎么还原？" />
        </AbsoluteFill>
      )}
      {t < tl.leadIn && <AbsoluteFill style={{ background: NIGHT, opacity: 0.8 * (1 - rise(t, 0, tl.leadIn)) }} />}
      {tl.draft && <div style={{ position: "absolute", right: 24, bottom: 16, fontFamily: MONO, fontSize: 22, color: AMBER, opacity: 0.8 }}>DRAFT timeline</div>}
    </AbsoluteFill>
  );
};

/** The YouTube cover, as the 2×2 film's: the question, English first, a scrambled cube, the free-web-cube badge. */
export const Cube5x5Cover: FC = () => (
  <AbsoluteFill style={{ background: NIGHT }}>
    {/* The 5×5 fills more of its frame than the 2×2 did: smaller and further right, clear of the question. */}
    <AbsoluteFill style={{ transform: "translate(520px, 10px) scale(0.86)" }}>
      {/* Feathered, so the frame's own background has no edge once it is smaller than the cover. */}
      <Img
        src={file("footage/hero.jpg")}
        style={{ width: 1920, height: 1080, WebkitMaskImage: "radial-gradient(ellipse 50% 50% at 50% 50%, #000 80%, transparent 100%)" }}
      />
    </AbsoluteFill>
    <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(4,7,13,1) 0%, rgba(4,7,13,.92) 40%, rgba(4,7,13,0) 60%)" }} />
    <AbsoluteFill style={{ justifyContent: "center", paddingLeft: 120 }}>
      <div style={{ fontFamily: EN, fontSize: 122, fontWeight: 800, color: INK, lineHeight: 1.08, maxWidth: 900 }}>
        How Do You Solve a <span style={{ color: AMBER }}>5×5 Cube</span>?
      </div>
      <div style={{ fontFamily: ZH, fontSize: 64, fontWeight: 600, color: MUTED, marginTop: 30 }}>五阶魔方怎么还原？</div>
      <div style={{ alignSelf: "flex-start", marginTop: 44, padding: "16px 34px 18px", borderRadius: 30, background: MINT, color: "#06120c" }}>
        <div style={{ fontFamily: EN, fontSize: 46, fontWeight: 800 }}>✓ Free online cube included</div>
        <div style={{ fontFamily: ZH, fontSize: 30, fontWeight: 700, opacity: 0.8, marginTop: 2 }}>附免费网页魔方</div>
      </div>
    </AbsoluteFill>
  </AbsoluteFill>
);
