/**
 * What the phones and laptops in the green-screen shots of 「你爱听 AI 说「是的」吗？」 show (G1–G5).
 * scripts/ai-sycophancy/composite_screens.py renders this once per shot, at the screen's shape and the clip's length,
 * with the shot's cue times converted to the clip's own clock, then warps it onto the tracked screen. A generic chat
 * app that imitates no real one. Only what the narration names is readable; everything else is grey bars, so no
 * one's words are invented.
 */
import type { CSSProperties, FC } from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig, type CalculateMetadataFunction } from "remotion";

export type ScreenProps = { kind: string; width: number; height: number; seconds: number; cues: number[]; lines?: string[] };

export const calculateScreenMetadata: CalculateMetadataFunction<ScreenProps> = async ({ props }) => ({
  width: props.width, height: props.height, durationInFrames: Math.max(1, Math.round(props.seconds * 30)), fps: 30,
});

const BG = "#1c252e";
const PANEL = "#141b21";
const AI = "#26313b";
const ME = "#3a2a21";
const GOLD = "#c9a45a";
const PAPER = "#ece3d2";
const MUTED = "#8f989f";
const SANS = "'PingFang SC', 'Helvetica Neue', sans-serif";
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const pop = (t: number, at: number) => interpolate(t, [at, at + 0.35], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });

const Bars: FC<{ n: number; width: number; color?: string }> = ({ n, width, color = "rgba(217,211,199,.32)" }) => (
  <div>
    {[...Array(n)].map((_, i) => (
      <div key={i} style={{ height: width * 0.045, borderRadius: 99, background: color, width: `${i === n - 1 ? 58 : 92 - (i % 2) * 8}%`,
        marginTop: i ? width * 0.035 : 0 }} />
    ))}
  </div>
);

const Bubble: FC<{ me?: boolean; o?: number; size: number; style?: CSSProperties; children: React.ReactNode }> = ({ me, o = 1, size, style, children }) => (
  <div style={{ alignSelf: me ? "flex-end" : "flex-start", maxWidth: "82%", padding: size * 0.6, borderRadius: size * 0.7,
    borderTopRightRadius: me ? size * 0.2 : size * 0.7, borderTopLeftRadius: me ? size * 0.7 : size * 0.2, background: me ? ME : AI,
    color: PAPER, fontFamily: SANS, fontSize: size, lineHeight: 1.45, opacity: o, transform: `translateY(${(1 - o) * size}px)`, ...style }}>
    {children}
  </div>
);

/** A phone chat: header, messages from the top. */
const Phone: FC<{ children: React.ReactNode; input?: React.ReactNode }> = ({ children, input }) => {
  const { width } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: SANS }}>
      <div style={{ height: width * 0.2, display: "flex", alignItems: "flex-end", paddingBottom: width * 0.035, justifyContent: "center",
        borderBottom: "1px solid rgba(255,255,255,.07)", background: PANEL }}>
        <div style={{ width: width * 0.05, height: width * 0.05, borderRadius: 99, background: GOLD, marginRight: width * 0.025 }} />
        <div style={{ color: PAPER, fontSize: width * 0.05 }}>AI</div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: width * 0.04, padding: width * 0.05 }}>{children}</div>
      {input ? <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, padding: width * 0.04, background: PANEL }}>{input}</div> : null}
    </AbsoluteFill>
  );
};

/** A laptop chat window: a dark sidebar, the conversation on the right. */
const Laptop: FC<{ tabs?: string[]; active?: number; children: React.ReactNode }> = ({ tabs, active = -1, children }) => {
  const { width } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: SANS, flexDirection: "row" }}>
      <div style={{ width: width * 0.2, background: PANEL, padding: width * 0.02 }}>
        {[...Array(6)].map((_, i) => <div key={i} style={{ height: width * 0.012, borderRadius: 99, background: "rgba(217,211,199,.18)", marginTop: width * 0.03, width: `${80 - (i % 3) * 15}%` }} />)}
      </div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {tabs ? (
          <div style={{ display: "flex", gap: width * 0.015, padding: width * 0.02, borderBottom: "1px solid rgba(255,255,255,.07)" }}>
            {tabs.map((tab, i) => (
              <div key={tab} style={{ padding: `${width * 0.008}px ${width * 0.022}px`, borderRadius: width * 0.012, fontSize: width * 0.026,
                color: i === active ? "#16120d" : MUTED, background: i === active ? GOLD : "rgba(255,255,255,.06)" }}>{tab}</div>
            ))}
          </div>
        ) : null}
        <div style={{ display: "flex", flexDirection: "column", gap: width * 0.022, padding: width * 0.04 }}>{children}</div>
      </div>
    </AbsoluteFill>
  );
};

export const Screen: FC<ScreenProps> = ({ kind, cues, lines = [] }) => {
  const { width, fps } = useVideoConfig();
  const t = useCurrentFrame() / fps;
  const big = width * 0.058; // phone text size
  if (kind === "G1") {
    // sc00-01: someone asked something (unreadable); the AI answers with praise, the two lines the narration reads
    return (
      <Phone>
        <Bubble me size={big} style={{ width: "62%" }}><Bars n={2} width={width * 0.6} /></Bubble>
        {lines.map((l, i) => <Bubble key={i} size={big} o={pop(t, cues[i] ?? 0)}>{l}</Bubble>)}
      </Phone>
    );
  }
  if (kind === "G3") {
    // sc04-05: an answer, and the thumb taps 👍
    const lit = pop(t, cues[0] ?? 1);
    const thumb = (fill: string) => (
      <svg width={big * 1.6} height={big * 1.6} viewBox="0 0 120 120">
        <path d="M18 58h18v46H18Z M36 62l18-34c4-8 16-6 16 4v16h28c8 0 12 6 10 14l-8 34c-2 6-6 8-12 8H36Z" fill={fill} stroke={MUTED} strokeWidth={6} strokeLinejoin="round" />
      </svg>
    );
    return (
      <Phone>
        <Bubble me size={big} style={{ width: "50%" }}><Bars n={1} width={width * 0.5} /></Bubble>
        <Bubble size={big} style={{ width: "78%" }}><Bars n={4} width={width * 0.7} /></Bubble>
        <div style={{ display: "flex", gap: big, marginLeft: big * 0.4, alignItems: "center" }}>
          <div style={{ transform: `scale(${1 + 0.35 * Math.sin(Math.min(1, lit) * Math.PI)})` }}>{thumb(lit > 0.5 ? GOLD : "none")}</div>
          <div style={{ transform: "rotate(180deg)" }}>{thumb("none")}</div>
        </div>
      </Phone>
    );
  }
  if (kind === "G5") {
    // sc06-04: the question is already typed; the line the film gives away is typed after it, then sent
    const [question, extra] = lines;
    const [typeFrom, typeTo, send] = cues;
    const n = Math.round(interpolate(t, [typeFrom, typeTo], [0, [...extra].length], clamp));
    const sent = pop(t, send);
    const typed = question + [...extra].slice(0, n).join("");
    const caret = Math.floor(t * 2) % 2 === 0 && sent < 0.01 ? "|" : "";
    return (
      <Phone input={sent < 0.5 ? (
        <div style={{ background: "#0f1418", borderRadius: big * 0.6, padding: big * 0.55, color: PAPER, fontSize: big * 0.9, lineHeight: 1.45 }}>
          {typed}<span style={{ color: GOLD }}>{caret}</span>
        </div>
      ) : null}>
        <Bubble size={big} style={{ width: "78%" }}><Bars n={3} width={width * 0.7} /></Bubble>
        {sent > 0 ? <Bubble me size={big * 0.9} o={sent}>{question}<span style={{ color: GOLD }}>{extra}</span></Bubble> : null}
      </Phone>
    );
  }
  if (kind === "G2") {
    // sc01-18: a long chat at night; nothing on it can be read (no dose, no schedule)
    return (
      <Laptop>
        {[0, 1, 2, 3, 4].map((i) => (
          <Bubble key={i} me={i % 2 === 0} size={width * 0.022} o={pop(t, i * 2.2)} style={{ width: i % 2 ? "70%" : "40%" }}>
            <Bars n={i % 2 ? 3 : 1} width={width * (i % 2 ? 0.5 : 0.3)} />
          </Bubble>
        ))}
      </Laptop>
    );
  }
  if (kind === "G4") {
    // sc05-03: the same first message to the three models, one after another
    const active = cues.filter((c) => t >= c).length - 1;
    return (
      <Laptop tabs={["Claude", "Codex", "qwen3:8b"]} active={active}>
        <Bubble me size={width * 0.024}>{lines[0]}</Bubble>
        <Bubble size={width * 0.024} o={active >= 0 ? 1 : 0} style={{ width: "70%" }}><Bars n={3} width={width * 0.5} /></Bubble>
      </Laptop>
    );
  }
  return <AbsoluteFill style={{ background: BG }} />;
};
