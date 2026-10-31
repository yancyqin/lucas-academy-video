/**
 * 「你爱听 AI 说「是的」吗？」 · 从新闻看教育 / Lessons from the Headlines (docs/ai-sycophancy/). The series is never numbered.
 *
 * Built like 「跨越中等收入陷阱」 (MiddleIncomeTrapVideo.tsx): Yancy's cloned voice, captions in a separate SRT, a shot
 * list in scripts/ai-sycophancy/edit.json timed by build_timeline.py, cross-fades, chapter cards and the chapter bar.
 * Words on cards are 「中文|English」, the English smaller underneath. The pictures differ: real footage from Pexels
 * (picked by Yancy, checked by Codex; no shot shows Bowen Wan, her family, her doctor or her home) and chat panels
 * drawn here. A chat panel is a re-creation, never a screenshot: generic bubbles that imitate no product, every one
 * labelled with where its words come from (the complaint's Chinese originals, or our own test log, 2026-10-30), and no
 * taper schedule or dose plan is ever shown. Each message shows her (or the model's) Chinese with our English
 * under it, since one picture carries both the Chinese and the English audio track (Yancy, 2026-10-31).
 * The green-screen shots (G1–G5) play as plain footage for now; the chat goes beside them until the screens are
 * tracked and keyed.
 */
import { createContext, useContext, useEffect, useState, type CSSProperties, type FC, type ReactNode } from "react";
import {
  AbsoluteFill,
  Easing,
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
import { ChapterBar, type Chapter } from "../middle-income-trap/ChapterBar";

const DIR = "ai-sycophancy";
const file = (p: string) => staticFile(`${DIR}/${p}`);

type Msg = { who: "her" | "me" | "ai" | "date" | "time" | "note" | "hidden"; by?: string; zh: string; en?: string };
type Shot = {
  k: string; start: number; end: number; clip?: string; rate?: number; green?: boolean;
  lower?: string; lowerAt?: number; items?: string[] | [string, string][]; itemsAt?: number[]; big?: string; bigAt?: number;
  line?: string; lineAt?: number; num?: string; sub?: string; numAt?: number; likes?: boolean;
  msgs?: Msg[]; msgsAt?: number[]; head?: string; label?: string;
  lines?: [string, string][]; linesAt?: number[]; by?: string; barHint?: boolean;
  note?: string; noteAt?: number; noteFirst?: boolean;
  from?: string; fromDate?: string; to?: string; toDate?: string; gap?: string;
  cols?: [string, string, string][]; colsAt?: number[];
};
export type AsTimeline = {
  fps: number; durationSeconds: number; shots: Shot[]; chapters: Chapter[];
  lines: Record<string, { start: number; end: number; text: string }>;
};
export type AsProps = { tl?: AsTimeline | null; lang?: "zh" | "en" };

export const calculateAsMetadata: CalculateMetadataFunction<AsProps> = async ({ props, abortSignal }) => {
  const r = await fetch(file("timeline.json"), { signal: abortSignal });
  if (!r.ok) throw Error("Run scripts/ai-sycophancy/build_timeline.py and assets.py first");
  const tl = (await r.json()) as AsTimeline;
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
const SANS = "'PingFang SC', 'Helvetica Neue', sans-serif";
const FADE = 0.8;
const CARD = 2.9;
const LIFT = 150;
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = Easing.bezier(0.3, 0.7, 0.2, 1);
const SHADOW = "0 4px 30px rgba(0,0,0,.75), 0 1px 3px rgba(0,0,0,.8)";
const PEXELS = "实拍 · Pexels|Footage · Pexels";

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

const useT = () => useCurrentFrame() / useVideoConfig().fps;
/** A shot that opens a chapter waits for the chapter card (CARD) before its own words come in, as in
 * 「跨越中等收入陷阱」; `useAt()(a)` is when something timed at `a` may appear. */
const Hold = createContext(0);
const useAt = () => { const h = useContext(Hold); return (a: number) => Math.max(a, h); };
const appear = (t: number, at: number, d = 0.8) => interpolate(t, [at, at + d], [0, 1], { ...clamp, easing: ease });
const rise = (o: number): CSSProperties => ({ opacity: o, transform: `translateY(${(1 - o) * 18}px)` });

const Dark: FC<{ children?: ReactNode; style?: CSSProperties }> = ({ children, style }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 40%, #1b2128 0%, ${INK} 70%)`, ...style }}>{children}</AbsoluteFill>
);

/** A small line of provenance above the chapter bar. */
const Label: FC<{ text: string; right?: boolean }> = ({ text, right }) => (
  <div style={{ position: "absolute", [right ? "right" : "left"]: 40, bottom: 118, fontFamily: SERIF, fontWeight: 300,
    letterSpacing: 1, color: "rgba(255,255,255,.72)", textShadow: "0 1px 6px rgba(0,0,0,.9)", textAlign: right ? "right" : "left" }}>
    <Bi s={text} size={right ? 18 : 22} en={{ marginTop: 2 }} />
  </div>
);

// ---- footage ----
const Footage: FC<{ s: Shot; dur: number }> = ({ s, dur }) => {
  const t = useT();
  const sc = interpolate(t, [0, dur + FADE], [1.0, 1.05], clamp);
  const dim = s.lines || s.items || s.num || s.line || s.big ? 0.82 : 1;
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <AbsoluteFill style={{ transform: `scale(${sc})` }}>
        <OffthreadVideo src={file(`clips/${s.clip}.mp4`)} muted playbackRate={s.rate ?? 1}
          style={{ width: "100%", height: "100%", objectFit: "cover", filter: `brightness(${dim})` }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0) 62%, rgba(8,10,13,.55) 100%)" }} />
      <Label text={PEXELS} right />
    </AbsoluteFill>
  );
};

/** A place or a date, top left, like a caption in a documentary. */
const Lower: FC<{ text: string; at: number }> = ({ text, at }) => {
  const t = useT();
  const o = appear(t, useAt()(at), 0.9);
  return (
    <div style={{ position: "absolute", left: 70, top: 64, fontFamily: SERIF, color: PAPER, textShadow: SHADOW, background: "rgba(10,12,15,.62)",
      borderRadius: 14, padding: "18px 30px 20px", ...rise(o) }}>
      <div style={{ width: 60, height: 3, background: GOLD, marginBottom: 14 }} />
      <Bi s={text} size={44} zh={{ letterSpacing: 4 }} en={{ color: SOFT }} />
    </div>
  );
};

const Chips: FC<{ items: string[]; at: number[] }> = ({ items, at }) => {
  const t = useT();
  const A = useAt();
  return (
    <div style={{ position: "absolute", left: 80, right: 80, bottom: LIFT, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 22 }}>
      {items.map((w, i) => {
        const o = appear(t, A(at[i] ?? 0), 0.6);
        return (
          <div key={w} style={{ ...rise(o), fontFamily: SERIF, color: PAPER, textAlign: "center",
            background: "rgba(10,12,15,.66)", borderRadius: 12, padding: "10px 30px", textShadow: SHADOW,
            border: "1px solid rgba(201,164,90,.35)" }}><Bi s={w} size={46} zh={{ letterSpacing: 3 }} en={{ color: SOFT }} /></div>
        );
      })}
    </div>
  );
};

const Big: FC<{ text: string; at: number }> = ({ text, at }) => {
  const t = useT();
  const o = appear(t, at, 0.5);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 60 }}>
      <div style={{ fontFamily: SERIF, fontSize: 300, color: GOLD, opacity: o, transform: `scale(${1.2 - 0.2 * o})`,
        textShadow: "0 10px 60px rgba(0,0,0,.85)", lineHeight: 1, letterSpacing: 20 }}>「{bi(text)[0]}」</div>
      {bi(text)[1] ? <div style={{ fontFamily: SERIF, fontSize: 60, fontWeight: 300, color: PAPER, opacity: o, marginTop: 18,
        textShadow: SHADOW }}>“{bi(text)[1]}”</div> : null}
    </AbsoluteFill>
  );
};

const QuoteLine: FC<{ text: string; at: number }> = ({ text, at }) => {
  const t = useT();
  const o = appear(t, at, 1.0);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: LIFT, textAlign: "center", fontFamily: SERIF, ...rise(o) }}>
      <span style={{ display: "inline-block", background: "rgba(10,12,15,.66)", borderRadius: 14, padding: "16px 44px" }}>
        <Bi s={text} size={52} color={PAPER} zh={{ letterSpacing: 4, textShadow: SHADOW }} en={{ color: SOFT, textShadow: SHADOW }} />
      </span>
    </div>
  );
};

const Num: FC<{ value: string; sub?: string; at: number }> = ({ value, sub, at }) => {
  const t = useT();
  const o = appear(t, at, 1.0);
  return (
    <div style={{ position: "absolute", left: 110, right: 110, bottom: LIFT, fontFamily: SERIF, color: "#fff", textShadow: SHADOW, ...rise(o) }}>
      <div style={{ fontSize: 150, fontWeight: 300, letterSpacing: 2, lineHeight: 1, color: GOLD }}>{value}</div>
      {sub ? <div style={{ marginTop: 14, opacity: 0.95, maxWidth: 1500 }}><Bi s={sub} size={40} zh={{ fontWeight: 300, letterSpacing: 3 }} /></div> : null}
    </div>
  );
};

/** sc04-05: thumbs-up, one after another, rising off the phone. */
const Likes: FC<{ dur: number }> = ({ dur }) => {
  const t = useT();
  const n = 14;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {[...Array(n)].map((_, i) => {
        const at = 0.4 + (i * (dur - 1.5)) / n;
        const p = interpolate(t, [at, at + 2.6], [0, 1], clamp);
        if (p <= 0 || p >= 1) return null;
        const x = 1180 + ((i * 137) % 420);
        return (
          <svg key={i} width={90} height={90} viewBox="0 0 120 120" style={{ position: "absolute", left: x, top: 760 - p * 560,
            opacity: Math.sin(p * Math.PI), transform: `scale(${0.7 + 0.5 * p})` }}>
            <path d="M18 58h18v46H18Z M36 62l18-34c4-8 16-6 16 4v16h28c8 0 12 6 10 14l-8 34c-2 6-6 8-12 8H36Z"
              fill={i % 3 === 0 ? EMBER : GOLD} stroke="rgba(0,0,0,.4)" strokeWidth={3} strokeLinejoin="round" />
          </svg>
        );
      })}
    </AbsoluteFill>
  );
};

// ---- chats ----
const W_CJK = 1.0, W_LAT = 0.56;
const textWidth = (s: string, size: number) => [...s].reduce((w, ch) => w + size * (/[⺀-￿]/.test(ch) ? W_CJK : W_LAT), 0);
const linesOf = (s: string, size: number, width: number) => Math.max(1, Math.ceil(textWidth(s, size) / width));

/** Gold for every 「是的」 an AI says: the word the film is about. */
const Marked: FC<{ text: string }> = ({ text }) => (
  <>{text.split(/(是的)/).map((p, i) => (p === "是的" ? <span key={i} style={{ color: GOLD, fontWeight: 600 }}>{p}</span> : <span key={i}>{p}</span>))}</>
);

const CHAT = { left: 250, width: 1420, top: 70, height: 800 };
const MSG = 38, LINE = 1.5, BUBBLE = 880, PAD = 24, EN_MSG = 24;

const msgHeight = (m: Msg, text: string) => {
  if (m.who === "date") return 78;
  if (m.who === "time") return 52;
  if (m.who === "note") return 30 + linesOf(text, 30, 1100) * 46;
  if (m.who === "hidden") return 210;
  // a little narrower than the bubble, so an estimate errs towards more lines (the newest message must not be cut off)
  const en = m.en ? 8 + linesOf(m.en, EN_MSG, (BUBBLE - PAD * 2) * 0.88) * EN_MSG * 1.35 : 0;
  return (m.by || m.who !== "ai" ? 36 : 0) + linesOf(text, MSG, (BUBBLE - PAD * 2) * 0.92) * MSG * LINE + en + PAD * 2 + 22;
};

const MsgView: FC<{ m: Msg; text: string }> = ({ m, text }) => {
  if (m.who === "date") {
    return (
      <div style={{ textAlign: "center", paddingTop: 18, color: GOLD, fontFamily: SERIF, fontSize: 28, letterSpacing: 3 }}>
        — {bi(text)[0]} — <span style={{ fontSize: 20, fontWeight: 300, color: MUTED }}>{bi(text)[1]}</span>
      </div>
    );
  }
  if (m.who === "time") {
    return <div style={{ textAlign: "center", color: MUTED, fontFamily: SERIF, fontSize: 24, fontStyle: "italic" }}>{bi(text)[0]} <span style={{ fontSize: 18 }}>{bi(text)[1]}</span></div>;
  }
  if (m.who === "note") {
    return (
      <div style={{ textAlign: "center", color: SOFT, fontFamily: SERIF, fontSize: 30, padding: "8px 120px", lineHeight: 1.5 }}>
        {bi(text)[0]}<div style={{ fontSize: 20, color: MUTED, fontWeight: 300 }}>{bi(text)[1]}</div>
      </div>
    );
  }
  const right = m.who === "her" || m.who === "me";
  const who = m.who === "her" ? "她|She" : m.who === "me" ? "我们|Us" : `${m.by ?? "AI"}|`;
  const bubble: CSSProperties = {
    maxWidth: BUBBLE, padding: PAD, borderRadius: 22, fontFamily: SANS, fontSize: MSG, lineHeight: LINE, color: PAPER,
    background: right ? "#3a2a21" : "#1c252e", border: `1px solid ${right ? "rgba(226,115,60,.45)" : "rgba(201,164,90,.28)"}`,
    borderTopRightRadius: right ? 6 : 22, borderTopLeftRadius: right ? 22 : 6, boxShadow: "0 10px 30px rgba(0,0,0,.35)",
  };
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: right ? "flex-end" : "flex-start", padding: "0 40px" }}>
      <div style={{ fontFamily: SERIF, fontSize: 22, color: right ? EMBER : GOLD, marginBottom: 8, letterSpacing: 2 }}>
        {bi(who)[0]} <span style={{ fontSize: 16, color: MUTED }}>{bi(who)[1]}</span>
      </div>
      {m.who === "hidden" ? (
        <div style={{ ...bubble, width: 640, height: 130, position: "relative", overflow: "hidden" }}>
          {[0, 1, 2, 3].map((i) => <div key={i} style={{ height: 14, borderRadius: 7, background: "rgba(217,211,199,.35)", width: `${90 - i * 12}%`, marginTop: i ? 14 : 4, filter: "blur(4px)" }} />)}
          <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column",
            fontFamily: SERIF, fontSize: 28, color: SOFT, background: "rgba(28,37,46,.55)" }}>
            {bi(text)[0]}<span style={{ fontSize: 18, color: MUTED }}>{bi(text)[1]}</span>
          </div>
        </div>
      ) : (
        <div style={bubble}>
          {m.who === "ai" ? <Marked text={text} /> : text}
          {m.en ? <div style={{ fontSize: EN_MSG, lineHeight: 1.35, color: "#a9b1b8", marginTop: 8 }}>{m.en}</div> : null}
        </div>
      )}
    </div>
  );
};

const Chat: FC<{ s: Shot; lang: "zh" | "en" }> = ({ s, lang }) => {
  const t = useT();
  const msgs = s.msgs ?? [];
  const A = useAt();
  const at = (s.msgsAt ?? []).map(A);
  const text = (m: Msg) => m.zh;
  const area = CHAT.height - 96 - 60;
  let y = 0;
  const placed = msgs.map((m, i) => {
    const h = msgHeight(m, bi(text(m))[0]);
    const p = appear(t, at[i] ?? 0, 0.55);
    const top = y;
    y += h * p;
    return { m, top, h, p };
  });
  const scroll = Math.max(0, y - area);
  return (
    <Dark>
      <div style={{ position: "absolute", left: CHAT.left, top: CHAT.top, width: CHAT.width, height: CHAT.height, borderRadius: 26,
        background: "rgba(14,18,22,.92)", border: "1px solid rgba(201,164,90,.22)", boxShadow: "0 30px 80px rgba(0,0,0,.55)", overflow: "hidden",
        opacity: appear(t, 0, 0.6) }}>
        <div style={{ height: 96, display: "flex", alignItems: "center", gap: 18, padding: "0 40px", borderBottom: "1px solid rgba(255,255,255,.06)",
          fontFamily: SERIF }}>
          <div style={{ width: 14, height: 14, borderRadius: 7, background: GOLD }} />
          <div style={{ color: PAPER, fontSize: 32, letterSpacing: 2 }}>{bi(s.head ?? "")[0]}</div>
          <div style={{ color: MUTED, fontSize: 22, fontWeight: 300 }}>{bi(s.head ?? "")[1]}</div>
        </div>
        <div style={{ position: "absolute", left: 0, right: 0, top: 96 + 20, height: area, overflow: "hidden",
          WebkitMaskImage: scroll > 0 ? "linear-gradient(180deg, transparent 0, #000 90px)" : undefined }}>
          {placed.map(({ m, top, p }, i) => (p > 0 ? (
            <div key={i} style={{ position: "absolute", left: 0, right: 0, top: top - scroll, opacity: p, transform: `translateY(${(1 - p) * 24}px)` }}>
              <MsgView m={m} text={text(m)} />
            </div>
          ) : null))}
        </div>
      </div>
      {s.label ? <Label text={s.label} /> : null}
    </Dark>
  );
};

/** Chat bubbles beside a green-screen phone until the screen is keyed (G1). */
const Bubbles: FC<{ msgs: Msg[]; at: number[] }> = ({ msgs, at }) => {
  const t = useT();
  return (
    <div style={{ position: "absolute", right: 90, top: 170, width: 760, display: "flex", flexDirection: "column", gap: 26 }}>
      {msgs.map((m, i) => {
        const o = appear(t, at[i] ?? 0, 0.6);
        return (
          <div key={i} style={{ ...rise(o), alignSelf: "flex-start", maxWidth: 760, padding: 26, borderRadius: 22, borderTopLeftRadius: 6,
            fontFamily: SANS, fontSize: 40, lineHeight: 1.45, color: PAPER, background: "rgba(28,37,46,.9)",
            border: "1px solid rgba(201,164,90,.35)", boxShadow: "0 16px 40px rgba(0,0,0,.5)" }}>
            {m.zh}{m.en ? <div style={{ fontSize: 26, lineHeight: 1.35, color: "#a9b1b8", marginTop: 8 }}>{m.en}</div> : null}
          </div>
        );
      })}
    </div>
  );
};

// ---- cards ----
const Card: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const A = useAt();
  const at = (s.linesAt ?? []).map(A);
  const look = (kind: string): [number, CSSProperties, CSSProperties] =>
    kind === "lead" ? [48, { fontWeight: 300, color: SOFT, letterSpacing: 4 }, { color: MUTED }]
      : kind === "key2" ? [66, { color: GOLD, letterSpacing: 4 }, { color: SOFT }]
        : kind === "q" ? [84, { color: PAPER, letterSpacing: 6 }, { color: SOFT }]
          : kind === "step" ? [52, { color: PAPER, letterSpacing: 3 }, { color: MUTED }]
            : kind === "cite" ? [56, { color: PAPER, letterSpacing: 2, lineHeight: 1.5, maxWidth: 1600 }, { color: SOFT, maxWidth: 1400, fontStyle: "italic" }]
              : [104, { color: GOLD, letterSpacing: 8 }, { color: SOFT }];
  const last = at.length ? at[at.length - 1] : 0;
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, textAlign: "center", padding: "0 120px 110px" }}>
        {(s.lines ?? []).map(([text, kind], i) => {
          const [size, zh, en] = look(kind);
          return (
            <div key={i} style={{ marginTop: i ? (kind === "step" ? 34 : 44) : 0, display: "flex", flexDirection: "column", alignItems: "center",
              ...rise(appear(t, at[i] ?? 0, 0.9)) }}>
              {kind === "step" ? <div style={{ width: 40, height: 3, background: GOLD, marginBottom: 14 }} /> : null}
              <Bi s={text} size={size} zh={zh} en={en} />
            </div>
          );
        })}
        {s.by ? <div style={{ marginTop: 46, color: GOLD, ...rise(appear(t, last + 0.8, 0.9)) }}><Bi s={s.by} size={30} zh={{ fontWeight: 300, letterSpacing: 2 }} /></div> : null}
      </AbsoluteFill>
    </Dark>
  );
};

const Nums: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const A = useAt();
  const at = (s.itemsAt ?? []).map(A);
  const items = s.items as [string, string][];
  const note = s.note ? (
    <div key="note" style={{ color: SOFT, maxWidth: 1500, textAlign: "center", margin: s.noteFirst ? "0 0 70px" : "70px 0 0", ...rise(appear(t, A(s.noteAt ?? 0), 0.9)) }}>
      <Bi s={s.note} size={42} zh={{ fontWeight: 300, letterSpacing: 3 }} en={{ color: MUTED }} />
    </div>
  ) : null;
  const row = (
    <div key="row" style={{ display: "flex", alignItems: "flex-start", justifyContent: "center", gap: 220 }}>
      {items.map(([v, sub], i) => (
        <div key={v} style={{ display: "flex", flexDirection: "column", alignItems: "center", fontFamily: SERIF, ...rise(appear(t, at[i] ?? 0, 0.9)) }}>
          <Bi s={v} size={bi(v)[0].length > 6 ? 120 : 170} color={i === items.length - 1 ? GOLD : "#fff"} zh={{ fontWeight: 300, letterSpacing: 2, lineHeight: 1.1 }} en={{ color: SOFT }} />
          <div style={{ marginTop: 22, color: SOFT, maxWidth: items.length > 1 ? 700 : 1400, textAlign: "center" }}>
            <Bi s={sub} size={40} zh={{ fontWeight: 300, letterSpacing: 3 }} en={{ color: MUTED }} />
          </div>
        </div>
      ))}
    </div>
  );
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, paddingBottom: 100 }}>
        {s.noteFirst ? [note, row] : [row, note]}
      </AbsoluteFill>
    </Dark>
  );
};

/** sc03-16: from 「在医生指导下进行」 to 「不提 Lam 减药计划」, thirteen days apart. */
const Span: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const draw = interpolate(t, [1.0, 3.0], [0, 1], { ...clamp, easing: ease });
  const end = (x: number, quote: string, date: string, o: number, gold: boolean) => (
    <div style={{ position: "absolute", left: x - 330, width: 660, top: 330, textAlign: "center", fontFamily: SERIF, ...rise(o) }}>
      <div style={{ color: MUTED, marginBottom: 18 }}><Bi s={date} size={32} zh={{ letterSpacing: 3 }} /></div>
      <Bi s={quote} size={50} color={gold ? GOLD : PAPER} zh={{ letterSpacing: 2 }} en={{ color: SOFT }} />
    </div>
  );
  return (
    <Dark>
      {end(520, s.from ?? "", s.fromDate ?? "", appear(t, 0.2), false)}
      {end(1400, s.to ?? "", s.toDate ?? "", appear(t, 2.6), true)}
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
        <path d={`M520 610H${520 + 880 * draw}`} stroke={EMBER} strokeWidth={6} strokeLinecap="round" />
        <circle cx={520} cy={610} r={12} fill={PAPER} />
        <circle cx={1400} cy={610} r={12} fill={GOLD} opacity={appear(t, 2.6)} />
      </svg>
      <div style={{ position: "absolute", left: 0, right: 0, top: 650, textAlign: "center", fontFamily: SERIF, ...rise(appear(t, 1.6)) }}>
        <Bi s={s.gap ?? ""} size={72} color={EMBER} zh={{ letterSpacing: 6 }} />
      </div>
      {s.note ? <div style={{ position: "absolute", left: 0, right: 0, top: 830, textAlign: "center", fontFamily: SERIF, ...rise(appear(t, s.noteAt ?? 5)) }}>
        <Bi s={s.note} size={46} color={SOFT} zh={{ fontWeight: 300, letterSpacing: 3 }} en={{ color: MUTED }} />
      </div> : null}
    </Dark>
  );
};

/** sc05-08～10: the same essay, the parent's mood, two scores. */
const Essay: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const at = s.colsAt ?? [];
  return (
    <Dark>
      <div style={{ position: "absolute", left: 160, right: 160, top: 130, display: "flex", gap: 120, justifyContent: "center" }}>
        {(s.cols ?? []).map(([said, score, comment], i) => (
          <div key={i} style={{ width: 700, textAlign: "center", fontFamily: SERIF, ...rise(appear(t, at[i] ?? 0, 0.9)) }}>
            <Bi s={said} size={38} color={SOFT} zh={{ letterSpacing: 2 }} en={{ color: MUTED }} />
            <div style={{ fontSize: 220, lineHeight: 1.1, marginTop: 30, color: i === 0 ? GOLD : MUTED, opacity: appear(t, (at[i] ?? 0) + 1.2) }}>{score}<span style={{ fontSize: 60 }}> 分</span></div>
            <div style={{ fontFamily: SANS, fontSize: 34, color: PAPER, marginTop: 20, padding: "18px 26px", borderRadius: 18, background: "#1c252e",
              border: "1px solid rgba(201,164,90,.28)", opacity: appear(t, (at[i] ?? 0) + 2.0) }}>
              {bi(comment)[0]}<div style={{ fontSize: 22, color: "#a9b1b8", marginTop: 6 }}>{bi(comment)[1]}</div>
            </div>
          </div>
        ))}
      </div>
      {s.note ? <div style={{ position: "absolute", left: 0, right: 0, top: 780, textAlign: "center", fontFamily: SERIF, ...rise(appear(t, s.noteAt ?? 0)) }}>
        <Bi s={s.note} size={50} color={GOLD} zh={{ letterSpacing: 4 }} en={{ color: SOFT }} />
      </div> : null}
      {s.label ? <Label text={s.label} /> : null}
    </Dark>
  );
};

/** sc06-08～09: four habits; the one being talked about lights up. */
const Habits: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const at = s.itemsAt ?? [];
  const now = at.filter((a) => t >= a).length - 1;
  return (
    <Dark>
      <div style={{ position: "absolute", left: 240, right: 200, top: 120, fontFamily: SERIF }}>
        {(s.items as [string, string][]).map(([head, sub], i) => {
          const on = i === now;
          const seen = i <= now;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", height: 180, opacity: seen ? (on ? 1 : 0.55) : 0.22 }}>
              <div style={{ width: 90, fontSize: 64, color: on ? GOLD : MUTED }}>{i + 1}</div>
              <div style={{ width: 4, height: 110, background: on ? EMBER : GREY, marginRight: 44, borderRadius: 2 }} />
              <div>
                <Bi s={head} size={52} color={on ? PAPER : SOFT} zh={{ letterSpacing: 3 }} en={{ color: MUTED }} />
                {seen ? <div style={{ marginTop: 10 }}><Bi s={sub} size={32} color={on ? GOLD : MUTED} zh={{ fontWeight: 300, letterSpacing: 1 }} en={{ color: MUTED }} /></div> : null}
              </div>
            </div>
          );
        })}
      </div>
    </Dark>
  );
};

const Title: FC = () => {
  const t = useT();
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, color: "#fff", textAlign: "center", paddingBottom: 120 }}>
        <div style={{ fontSize: 34, fontWeight: 300, letterSpacing: 8, color: GOLD, opacity: appear(t, 0.1) }}>从新闻看教育 · LESSONS FROM THE HEADLINES</div>
        <div style={{ fontSize: 112, fontWeight: 400, marginTop: 34, opacity: appear(t, 0.3), letterSpacing: 8, textShadow: SHADOW }}>
          你爱听 AI 说「<span style={{ color: GOLD }}>是的</span>」吗？
        </div>
        <div style={{ fontSize: 54, fontWeight: 300, marginTop: 22, opacity: appear(t, 0.5), color: SOFT }}>Do You Like Hearing AI Say “Yes”?</div>
        <div style={{ fontSize: 30, fontWeight: 300, marginTop: 44, opacity: appear(t, 0.7), color: SOFT, letterSpacing: 3 }}>Yancy Qin | Lucas Academy</div>
      </AbsoluteFill>
    </Dark>
  );
};

const End: FC = () => {
  const t = useT();
  const credit: CSSProperties = { fontSize: 21, fontWeight: 300, color: MUTED, lineHeight: 1.8, letterSpacing: 0.3 };
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, color: "#fff", textAlign: "center", paddingBottom: 60 }}>
        <div style={{ fontSize: 60, fontWeight: 400, opacity: appear(t, 0.3), letterSpacing: 8 }}>从新闻看教育</div>
        <div style={{ fontSize: 34, fontWeight: 300, opacity: appear(t, 0.5), color: SOFT, marginTop: 8 }}>Lessons from the Headlines</div>
        <div style={{ fontSize: 32, fontWeight: 300, marginTop: 20, opacity: appear(t, 0.7), color: SOFT, letterSpacing: 3 }}>Yancy Qin | Lucas Academy</div>
        <div style={{ marginTop: 64, opacity: appear(t, 1.4), maxWidth: 1760, ...credit }}>
          对话原文：Wan v. OpenAI 起诉书（2026-10-27，旧金山高等法院；原告一方的说法，法院尚未判决）· Quoted chats: the complaint in Wan v. OpenAI (S.F. Superior Court, Oct 27, 2026; allegations, not findings)<br />
          对话画面是模拟，不是截图 · The chat panels are re-creations, not screenshots · 实验记录：Lucas Academy，2026-10-30 · Test log: our own, Oct 30, 2026<br />
          实拍画面：Pexels，作者见简介 · Footage: Pexels — authors listed in the description<br />
          音乐 Music：Satie, Gymnopédie No. 1 · Kevin MacLeod (incompetech.com), CC BY 3.0；Bach, Air · U.S. Air Force Strings，公有领域 public domain；Bach, Jesu, Joy of Man’s Desiring · Gli Armonici, CC0<br />
          配音：Yancy 本人的克隆声音 · Voice: Yancy’s own voice, synthesized
        </div>
      </AbsoluteFill>
    </Dark>
  );
};

const ChapterCard: FC<{ index: number; name: string; en?: string; p: number }> = ({ index, name, en, p }) => {
  const o = interpolate(p, [0.15, 0.55, CARD - 0.5, CARD], [0, 1, 1, 0], clamp);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", pointerEvents: "none", opacity: o, paddingBottom: 60 }}>
      <div style={{ background: "rgba(10,12,15,.78)", borderRadius: 18, padding: "20px 64px 24px", textAlign: "center", fontFamily: SERIF,
        border: "1px solid rgba(201,164,90,.35)", transform: `translateY(${(1 - o) * 12}px)` }}>
        <div style={{ fontSize: 26, fontWeight: 300, color: GOLD, letterSpacing: 4 }}>第 {index + 1} 段 · Part {index + 1}</div>
        <div style={{ fontSize: 68, color: PAPER, letterSpacing: 8, marginTop: 8 }}>{name}</div>
        {en ? <div style={{ fontSize: 38, fontWeight: 300, color: SOFT, marginTop: 4 }}>{en}</div> : null}
      </div>
    </AbsoluteFill>
  );
};

const ShotView: FC<{ s: Shot; dur: number; lang: "zh" | "en" }> = ({ s, dur, lang }) => {
  switch (s.k) {
    case "title": return <Title />;
    case "footage": return <Footage s={s} dur={dur} />;
    case "chat": return <Chat s={s} lang={lang} />;
    case "card": return <Card s={s} />;
    case "nums": return <Nums s={s} />;
    case "span": return <Span s={s} />;
    case "essay": return <Essay s={s} />;
    case "habits": return <Habits s={s} />;
    case "end": return <End />;
    default: return <Dark><div style={{ color: "#fff", fontSize: 60, margin: "auto" }}>{s.k}</div></Dark>;
  }
};

/** Words laid over a footage shot. */
const Overlays: FC<{ s: Shot; dur: number }> = ({ s, dur }) => (
  s.k !== "footage" ? null : (
    <>
      {s.lower ? <Lower text={s.lower} at={s.lowerAt ?? 0} /> : null}
      {s.items ? <Chips items={s.items as string[]} at={s.itemsAt ?? []} /> : null}
      {s.big ? <Big text={s.big} at={s.bigAt ?? 0} /> : null}
      {s.line ? <QuoteLine text={s.line} at={s.lineAt ?? 0} /> : null}
      {s.num ? <Num value={s.num} sub={s.sub} at={s.numAt ?? 0} /> : null}
      {s.msgs ? <Bubbles msgs={s.msgs} at={s.msgsAt ?? []} /> : null}
      {s.likes ? <Likes dur={dur} /> : null}
    </>
  )
);

const Faded: FC<{ first: boolean; children: ReactNode }> = ({ first, children }) => {
  const t = useT();
  const o = first ? interpolate(t, [0, 1.2], [0, 1], clamp) : interpolate(t, [0, FADE], [0, 1], clamp);
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};

export const AiSycophancyVideo: FC<AsProps> = ({ tl, lang = "zh" }) => {
  useFonts();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!tl) return <AbsoluteFill style={{ background: INK }} />;
  const t = frame / fps;
  const title = tl.shots[0];
  // the bar's "jump to any part" hint: at the title, and while sc00-04 says how the film goes
  const plan = tl.shots.find((s) => s.barHint);
  const hint = Math.max(interpolate(t, [0.4, 1.2, title.end + 2.0, title.end + 2.8], [0, 1, 1, 0], clamp),
    plan ? interpolate(t, [plan.start + 0.5, plan.start + 1.1, plan.end - 0.6, plan.end], [0, 1, 1, 0], clamp) : 0);
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
            <Hold.Provider value={i > 1 && tl.chapters.some((c) => Math.abs(c.start - s.start) < 0.6) ? CARD - 0.2 : 0}>
              <Faded first={i === 0}>
                <ShotView s={s} dur={dur} lang={lang} />
                <Overlays s={s} dur={dur} />
              </Faded>
            </Hold.Provider>
          </Sequence>
        );
      })}
      {card >= 0 ? <ChapterCard index={card} name={tl.chapters[card].name} en={tl.chapters[card].en} p={t - cardAt[card]} /> : null}
      {t < tl.durationSeconds - 9 ? <ChapterBar chapters={tl.chapters} duration={tl.durationSeconds} t={t} hint={hint} /> : null}
    </AbsoluteFill>
  );
};
