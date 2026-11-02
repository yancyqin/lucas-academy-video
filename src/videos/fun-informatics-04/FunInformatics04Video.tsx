/**
 * 「诺贝尔奖：光遗传学是什么？从信息学的角度看」 · 趣味信息学 4 (FUN-INFORMATICS-04.md, docs/fun-informatics-04/).
 *
 * Built like 「你爱听 AI 说「是的」吗？」 (AiSycophancyVideo.tsx): narration in a separate track, captions in a separate
 * SRT, a shot list in scripts/fun-informatics-04/edit.json timed by build_timeline.py, cross-fades, chapter cards and the
 * chapter bar. Pictures: Muse clips Yancy generated and Codex stills (labelled 「AI 生成 · 示意」), Pexels footage, Wikimedia
 * Commons lab recordings shown small in a microscope window with their credit, the Nobel committee's illustrations
 * (credited), episode 1's own picture, and the diagrams drawn here: a neuron's spikes beside a switch, the alga's
 * light-gated door, the eye's chain of cells, and the encode → decode chain. The diagrams carry no claim beyond the
 * narration: the eye is drawn in the order the signal travels, not as anatomy.
 */
import { createContext, useContext, useEffect, useState, type CSSProperties, type FC, type ReactNode } from "react";
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
import { ChapterBar, type Chapter } from "../middle-income-trap/ChapterBar";

const DIR = "fun-informatics-04";
const file = (p: string) => staticFile(`${DIR}/${p}`);

type Shot = {
  k: string; start: number; end: number; label?: string; clip?: string; shape?: string; rate?: number; in?: number;
  img?: string; bg?: string; zoom?: [number, number]; focus?: [number, number]; fit?: "cover" | "contain"; dim?: number;
  ring?: [number, number]; ringAt?: number; ringText?: string;
  lower?: string; lowerAt?: number; big?: string; bigAt?: number;
  lines?: [string, string][]; linesAt?: number[];
  name?: string; mode?: string;
  count?: [number, number]; countAt?: number;
  verse?: string; ref?: string; verseAt?: number;
  ask?: string[]; askAt?: number[];
};
export type Fi04Timeline = {
  fps: number; durationSeconds: number; shots: Shot[]; chapters: Chapter[]; draft?: boolean;
  lines: Record<string, { start: number; end: number; text: string }>;
};
export type Fi04Props = { tl?: Fi04Timeline | null; lang?: "zh" | "en" };

export const calculateFi04Metadata: CalculateMetadataFunction<Fi04Props> = async ({ props, abortSignal }) => {
  const r = await fetch(file(`timeline.${props.lang ?? "zh"}.json`), { signal: abortSignal });
  if (!r.ok) throw Error("Run scripts/fun-informatics-04/assets.py and build_timeline.py first");
  const tl = (await r.json()) as Fi04Timeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

// ---- look ----
const INK = "#0d1216";
const PAPER = "#eee6d6";
const SOFT = "#cfd5d8";
const MUTED = "#8a949b";
const GOLD = "#d2ad62";
const BLUE = "#5aa2ff";
const AMBER = "#ffb13d";
const GREEN = "#8fd16a";
const RED = "#ff6b5e";
const NOBEL_BG = "#6a95db";
const SERIF = "'NotoSerifSC', 'Songti SC', serif";
const FADE = 0.8;
const CARD = 2.6;
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = Easing.bezier(0.3, 0.7, 0.2, 1);
const SHADOW = "0 4px 30px rgba(0,0,0,.75), 0 1px 3px rgba(0,0,0,.8)";

/** Every word drawn here, in each film's language; the shots' own words come in timeline.<lang>.json. */
const WORDS = {
  zh: {
    touched: "摸中笔记本", times: (n: number) => ` / ${n} 次`, verseRef: (r: string) => `—— ${r}（和合本）`, quote: (t: string) => `「${t}」`,
    prize: "2026 诺贝尔生理学或医学奖", opto: "光遗传学", laureates: "卡尔·戴塞罗思　　彼得·黑格曼　　格奥尔格·内格尔",
    tNobel: "诺贝尔奖", tQ: "光遗传学是什么？", tSub: "从信息学的角度看", byline: "趣味信息学 4　·　作者 Yancy Qin | Lucas Academy",
    end1: "如果你喜欢这期视频，欢迎订阅！", end2: "在这里，我们一起学习、一起思考", end3: "也欢迎留言，告诉我们你感兴趣的话题",
    credits: ["画面：Pexels 实拍；Wikimedia Commons 实验录像（CC BY，作者见说明）；",
      "诺贝尔生理学或医学奖委员会插图（Mattias Karlén 绘）；第一期画面；AI 生成的示意画面（Muse、Codex）",
      "音乐：莫扎特《小星星变奏曲》K. 265，Simone Renzi 演奏（CC BY 3.0）", "经文：和合本"],
    neuron: "一个神经细胞", sameHeight: "每一次，都差不多一样高", fire01: "发 = 1　不发 = 0", likeSwitch: "是不是有点像开关？",
    slow: "发得慢", fast: "发得快", rate1: "什么时候发、发得多快，也都带着信息", rate2: "「发，还是不发」是最基本的一步",
    alga: "小绿藻", halfMs: "半毫秒", ourEyes: "我们的眼睛", tenMs: "至少十毫秒", ms: (i: number) => `${i} 毫秒`, faster: "快了二十多倍",
    light: "光", door: "一道门", particles: "带电的小颗粒", inside: "细胞里面", signal: "电信号",
    cells: "装上光控开关，什么细胞都听光的话", marked: "装了开关的那一种", others: "旁边别的细胞", onlyMarked: "只有装了开关的才会响应",
    press: "按一下：是，或者不是", oneBit: "= 一个比特", string: "一串开开关关，才是一句话",
    eyeSwitches: "眼睛自己的光开关", rodsCones: "视杆、视锥细胞", relay: "后面接力的细胞", nerve: "视神经「电线」", brain: "大脑",
    broken: "光开关坏了，人就慢慢看不见了", wire: "接力的细胞和「电线」还是好的", newQ: "装上新的光开关？",
    amber: "新开关认琥珀色的光，对眼睛更安全", dim: "平常的光不够，要很亮的光",
    shannon: "就像第二期讲过的香农通信图",
    steps: [["眼前的画面", "世界"], ["特制眼镜", "编码"], ["琥珀色光点", "传过去"], ["新的光开关", "接收"], ["大脑", "解码"]] as [string, string][],
    keySteps: ["编码", "解码"], scale: 1,
  },
  en: {
    touched: "Touched the notebook", times: (n: number) => ` / ${n}`, verseRef: (r: string) => `— ${r}`, quote: (t: string) => `“${t}”`,
    prize: "2026 Nobel Prize in Physiology or Medicine", opto: "Optogenetics", laureates: "Karl Deisseroth　·　Peter Hegemann　·　Georg Nagel",
    tNobel: "The Nobel Prize", tQ: "What Is Optogenetics?", tSub: "Seen Through Informatics", byline: "Fun Informatics 4　·　By Yancy Qin | Lucas Academy",
    end1: "If you enjoyed this video, please subscribe!", end2: "Here, we learn and think together", end3: "Leave a comment: what topics would you like to explore?",
    credits: ["Pictures: footage from Pexels; lab recordings from Wikimedia Commons (CC BY, authors in the description);",
      "illustrations by the Nobel Committee for Physiology or Medicine (Mattias Karlén); Fun Informatics 1; AI-generated illustrative shots (Muse, Codex)",
      "Music: Mozart, 12 Variations on “Ah vous dirai-je, Maman”, K. 265, played by Simone Renzi (CC BY 3.0)", "Scripture: World English Bible; John 1:5, King James Version"],
    neuron: "One nerve cell", sameHeight: "About the same height every time", fire01: "fire = 1    don't fire = 0", likeSwitch: "A bit like a switch?",
    slow: "Slow", fast: "Fast", rate1: "When signals come, and how fast, carry information too", rate2: "“Fire, or don't fire” is the most basic step",
    alga: "Tiny alga", halfMs: "Half a millisecond", ourEyes: "Our eyes", tenMs: "At least 10 ms", ms: (i: number) => `${i} ms`, faster: "Twenty times faster",
    light: "Light", door: "A door", particles: "Charged particles", inside: "Inside the cell", signal: "Electrical signal",
    cells: "With a light switch, any cell listens to light", marked: "The kind with the switch", others: "The cells next to them", onlyMarked: "Only the cells with the switch respond",
    press: "One press: yes, or no", oneBit: "= one bit", string: "A string of ons and offs makes a sentence",
    eyeSwitches: "The eye's own light switches", rodsCones: "rods and cones", relay: "Relay cells behind them", nerve: "Optic nerve, the “wire”", brain: "Brain",
    broken: "The light switches fail, and sight fades", wire: "The relay cells and the “wire” are still fine", newQ: "New light switches?",
    amber: "The new switch answers amber light, safer for the eye", dim: "Ordinary light isn't enough; it needs bright light",
    shannon: "Like Shannon's diagram from episode 2",
    steps: [["The scene", "the world"], ["Special glasses", "encode"], ["Amber dots", "send"], ["New light switches", "receive"], ["The brain", "decode"]] as [string, string][],
    keySteps: ["encode", "decode"], scale: 0.78,
  },
};
const Lang = createContext<"zh" | "en">("zh");
const useW = () => WORDS[useContext(Lang)];

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
const appear = (t: number, at: number, d = 0.8) => interpolate(t, [at, at + d], [0, 1], { ...clamp, easing: ease });
const rise = (o: number): CSSProperties => ({ opacity: o, transform: `translateY(${(1 - o) * 18}px)` });

const Dark: FC<{ children?: ReactNode; style?: CSSProperties }> = ({ children, style }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 42%, #1a2229 0%, ${INK} 72%)`, ...style }}>{children}</AbsoluteFill>
);

/** Where the picture comes from, small, bottom right above the chapter bar. */
const Label: FC<{ text?: string }> = ({ text }) => (!text ? null : (
  <div style={{ position: "absolute", right: 40, bottom: 120, fontFamily: SERIF, fontWeight: 300, fontSize: 19, letterSpacing: 1,
    color: "rgba(255,255,255,.75)", textShadow: "0 1px 6px rgba(0,0,0,.9)", maxWidth: 900, textAlign: "right" }}>{text}</div>
));

const Lower: FC<{ text: string; at: number }> = ({ text, at }) => {
  const o = appear(useT(), at);
  return (
    <div style={{ position: "absolute", left: 70, top: 64, ...rise(o) }}>
      <div style={{ fontFamily: SERIF, fontSize: 40, color: PAPER, letterSpacing: 3, textShadow: SHADOW, borderLeft: `4px solid ${GOLD}`,
        padding: "8px 28px 8px 20px", background: "rgba(8,10,13,.62)", borderRadius: "0 12px 12px 0" }}>{text}</div>
    </div>
  );
};

const Big: FC<{ text: string; at: number }> = ({ text, at }) => {
  const o = appear(useT(), at);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 80 }}>
      <div style={{ fontFamily: SERIF, fontSize: 92, color: PAPER, letterSpacing: 10, textShadow: SHADOW, ...rise(o),
        background: "rgba(8,10,13,.45)", borderRadius: 20, padding: "10px 48px" }}>{text}</div>
    </AbsoluteFill>
  );
};

const Count: FC<{ value: [number, number]; at: number }> = ({ value, at }) => {
  const t = useT();
  const w = useW();
  const o = appear(t, at);
  const n = Math.round(interpolate(t, [at, at + 1.6], [0, value[0]], { ...clamp, easing: ease }));
  return (
    <div style={{ position: "absolute", right: 90, top: 80, textAlign: "right", fontFamily: SERIF, ...rise(o),
      background: "rgba(8,10,13,.6)", borderRadius: 18, padding: "14px 34px" }}>
      <div style={{ fontSize: 30, color: SOFT, letterSpacing: 3 }}>{w.touched}</div>
      <div style={{ fontSize: 96, color: PAPER }}>{n}<span style={{ fontSize: 50, color: MUTED }}>{w.times(value[1])}</span></div>
    </div>
  );
};

const Verse: FC<{ text: string; refText: string; at: number }> = ({ text, refText, at }) => {
  const t = useT();
  const w = useW();
  const size = w.scale < 1 ? (text.length > 60 ? 44 : 50) : text.length > 26 ? 50 : 56;
  const o = at <= 0.05 ? 1 : appear(t, at, 1.2);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 90 }}>
      <div style={{ maxWidth: 1720, textAlign: "center", fontFamily: SERIF, ...rise(o) }}>
        <div style={{ fontSize: size, lineHeight: 1.55, color: PAPER, letterSpacing: w.scale < 1 ? 1 : 4, textShadow: SHADOW }}>{w.quote(text)}</div>
        <div style={{ fontSize: 32, color: GOLD, marginTop: 18, letterSpacing: 3, textShadow: SHADOW }}>{w.verseRef(refText)}</div>
      </div>
    </AbsoluteFill>
  );
};

const Ask: FC<{ lines: string[]; at: number[] }> = ({ lines, at }) => {
  const t = useT();
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 90 }}>
      <div style={{ maxWidth: 1760, textAlign: "center", fontFamily: SERIF }}>
        {lines.map((l, i) => (
          <div key={i} style={{ fontSize: i === 0 ? 76 : 48, lineHeight: 1.5, color: i === 0 ? PAPER : SOFT, letterSpacing: 4,
            textShadow: SHADOW, marginTop: i ? 26 : 0, ...rise(appear(t, at[i] ?? 0, 1.1)) }}>{l}</div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ---- pictures ----
const Footage: FC<{ s: Shot; dur: number }> = ({ s, dur }) => {
  const t = useT();
  const { fps } = useVideoConfig();
  const sc = interpolate(t, [0, dur + FADE], [1.0, 1.05], clamp);
  const busy = s.verse || s.ask || s.big;
  const dim = s.dim ?? (busy ? 0.62 : 1);
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <AbsoluteFill style={{ transform: `scale(${sc})` }}>
        <OffthreadVideo src={file(`clips/${s.clip}.mp4`)} muted playbackRate={s.rate ?? 1} startFrom={Math.round((s.in ?? 0) * fps)}
          style={{ width: "100%", height: "100%", objectFit: "cover", filter: `brightness(${dim})` }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0) 62%, rgba(8,10,13,.55) 100%)" }} />
      <Label text={s.label} />
    </AbsoluteFill>
  );
};

/** A small lab recording in a round microscope window, over a blurred still. */
const Window: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const { fps } = useVideoConfig();
  const o = appear(t, 0.2, 1.0);
  return (
    <AbsoluteFill style={{ background: INK }}>
      {s.bg ? <Img src={file(`stills/${s.bg}`)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "blur(18px) brightness(.55)" }} /> : null}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 40 }}>
        <div style={{ width: 640, height: 640, borderRadius: "50%", overflow: "hidden", border: `6px solid rgba(238,230,214,.85)`,
          boxShadow: "0 20px 80px rgba(0,0,0,.6)", opacity: o, transform: `scale(${0.94 + 0.06 * o})`, background: "#000" }}>
          <OffthreadVideo src={file(`clips/${s.clip}.mp4`)} muted playbackRate={s.rate ?? 1} startFrom={Math.round((s.in ?? 0) * fps)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </div>
      </AbsoluteFill>
      <Label text={s.label} />
    </AbsoluteFill>
  );
};

const Still: FC<{ s: Shot; dur: number }> = ({ s, dur }) => {
  const t = useT();
  const [z0, z1] = s.zoom ?? [1.0, 1.06];
  const [fx, fy] = s.focus ?? [0.5, 0.5];
  const z = interpolate(t, [0, dur + FADE], [z0, z1], { ...clamp, easing: Easing.inOut(Easing.sin) });
  const ro = s.ring ? appear(t, s.ringAt ?? 0, 0.9) : 0;
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <AbsoluteFill style={{ transform: `scale(${z})`, transformOrigin: `${fx * 100}% ${fy * 100}%` }}>
        <Img src={file(`stills/${s.img}`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        {s.ring ? (
          <div style={{ position: "absolute", left: `${s.ring[0] * 100}%`, top: `${s.ring[1] * 100}%`, width: 120, height: 120,
            marginLeft: -60, marginTop: -60, borderRadius: "50%", border: `4px solid ${AMBER}`, opacity: ro,
            boxShadow: `0 0 30px ${AMBER}`, transform: `scale(${1.4 - 0.4 * ro})` }} />
        ) : null}
      </AbsoluteFill>
      {s.ringText ? (
        <div style={{ position: "absolute", left: 1180, top: 470, fontFamily: SERIF, fontSize: 56, color: AMBER, letterSpacing: 6,
          textShadow: SHADOW, ...rise(appear(t, (s.ringAt ?? 0) + 0.4)) }}>{s.ringText}</div>
      ) : null}
      <Label text={s.label} />
    </AbsoluteFill>
  );
};

const Nobel: FC<{ s: Shot; dur: number }> = ({ s, dur }) => {
  const t = useT();
  const [z0, z1] = s.zoom ?? [1.0, 1.06];
  const [fx, fy] = s.focus ?? [0.5, 0.5];
  const z = interpolate(t, [0, dur + FADE], [z0, z1], { ...clamp, easing: Easing.inOut(Easing.sin) });
  const cover = s.fit === "cover";
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: cover ? "#000" : s.img?.includes("adv") ? "#fff" : NOBEL_BG }}>
      <AbsoluteFill style={{ transform: `scale(${z})`, transformOrigin: `${fx * 100}% ${fy * 100}%`, padding: cover ? 0 : "40px 60px 150px" }}>
        <Img src={file(`stills/${s.img}`)} style={{ width: "100%", height: "100%", objectFit: cover ? "cover" : "contain",
          objectPosition: `${fx * 100}% ${fy * 100}%` }} />
      </AbsoluteFill>
      <Label text={s.label} />
    </AbsoluteFill>
  );
};

const Prize: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const w = useW();
  return (
    <AbsoluteFill>
      <Img src={file(`stills/${s.bg}`)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "blur(10px) brightness(.4)" }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 60, fontFamily: SERIF, textAlign: "center" }}>
        <div style={{ fontSize: 40, color: GOLD, letterSpacing: w.scale < 1 ? 3 : 8, ...rise(appear(t, 0.2)) }}>{w.prize}</div>
        <div style={{ fontSize: 120 * (w.scale < 1 ? 0.85 : 1), color: PAPER, letterSpacing: w.scale < 1 ? 4 : 20, marginTop: 16, textShadow: SHADOW, ...rise(appear(t, 0.7)) }}>{w.opto}</div>
        <div style={{ fontSize: 34, color: SOFT, letterSpacing: w.scale < 1 ? 1 : 4, marginTop: 30, ...rise(appear(t, 1.4)) }}>{w.laureates}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Title: FC = () => {
  const t = useT();
  const w = useW();
  const en = w.scale < 1;
  return (
    <AbsoluteFill>
      <Img src={file("stills/dish-beam.png")} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "brightness(.42)" }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 40, fontFamily: SERIF, textAlign: "center" }}>
        <div style={{ fontSize: 46, color: GOLD, letterSpacing: en ? 4 : 10, ...rise(appear(t, 0.2)) }}>{w.tNobel}</div>
        <div style={{ fontSize: en ? 112 : 132, color: PAPER, letterSpacing: en ? 2 : 14, marginTop: 10, textShadow: SHADOW, ...rise(appear(t, 0.5)) }}>{w.tQ}</div>
        <div style={{ fontSize: 54, color: SOFT, letterSpacing: en ? 3 : 10, marginTop: 18, ...rise(appear(t, 1.0)) }}>{w.tSub}</div>
        <div style={{ fontSize: 28, color: MUTED, letterSpacing: en ? 2 : 6, marginTop: 60, ...rise(appear(t, 1.5)) }}>{w.byline}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Card: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const w = useW();
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 80, fontFamily: SERIF }}>
        <div style={{ textAlign: s.lines?.[0]?.[1] === "step" ? "left" : "center" }}>
          {(s.lines ?? []).map(([text, kind], i) => {
            const o = appear(t, s.linesAt?.[i] ?? 0);
            const style: CSSProperties = kind === "lead" ? { fontSize: 96, color: PAPER, letterSpacing: 10 }
              : kind === "lead2" ? { fontSize: 64, color: SOFT, letterSpacing: 8 }
              : kind === "q" ? { fontSize: 110, color: BLUE, letterSpacing: 10, marginTop: 20 }
              : { fontSize: 60, color: PAPER, letterSpacing: 5, marginTop: 26 };
            return (
              <div key={i} style={{ ...style, ...(w.scale < 1 ? { fontSize: Number(style.fontSize) * w.scale, letterSpacing: 1 } : {}), ...rise(o) }}>
                {kind === "step" ? <span style={{ color: GOLD, marginRight: 24 }}>·</span> : null}{text}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </Dark>
  );
};

const End: FC = () => {
  const t = useT();
  const w = useW();
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, textAlign: "center", paddingBottom: 30 }}>
        <div style={{ fontSize: 66 * (w.scale < 1 ? 0.85 : 1), color: PAPER, letterSpacing: w.scale < 1 ? 1 : 6, ...rise(appear(t, 0.2)) }}>{w.end1}</div>
        <div style={{ fontSize: 44, color: SOFT, letterSpacing: w.scale < 1 ? 1 : 4, marginTop: 24, ...rise(appear(t, 0.8)) }}>{w.end2}</div>
        <div style={{ fontSize: 40, color: GOLD, letterSpacing: w.scale < 1 ? 1 : 4, marginTop: 24, ...rise(appear(t, 1.4)) }}>{w.end3}</div>
        <div style={{ marginTop: 80, fontSize: 22, color: MUTED, lineHeight: 1.8, letterSpacing: 1, ...rise(appear(t, 2.4)) }}>
          {w.credits.map((c) => <div key={c}>{c}</div>)}
          <div style={{ marginTop: 18, fontSize: 26, color: SOFT, letterSpacing: w.scale < 1 ? 2 : 4 }}>{w.byline}</div>
        </div>
      </AbsoluteFill>
    </Dark>
  );
};

// ---- diagrams ----
const W = 1920, H = 1080;
const Caption: FC<{ text: string; at?: number; y?: number; color?: string; size?: number }> = ({ text, at = 0.3, y = 860, color = PAPER, size = 50 }) => {
  const o = appear(useT(), at);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: y, textAlign: "center", fontFamily: SERIF, fontSize: size, color,
      letterSpacing: 5, textShadow: SHADOW, ...rise(o) }}>{text}</div>
  );
};

/** A voltage trace: spikes of one height at the given times (seconds), scrolling in from the right. */
const trace = (spikes: number[], t: number, x0: number, x1: number, y: number, h: number, span = 6) => {
  const pts: string[] = [];
  const left = t - span;
  for (let i = 0; i <= 400; i++) {
    const ts = left + (i / 400) * span;
    const x = x0 + (i / 400) * (x1 - x0);
    let v = 0;
    for (const s of spikes) {
      const d = ts - s;
      if (d >= 0 && d < 0.06) v = Math.max(v, Math.sin((d / 0.06) * Math.PI));
      else if (d >= 0.06 && d < 0.14) v = Math.min(v, -0.18 * Math.sin(((d - 0.06) / 0.08) * Math.PI));
    }
    if (ts > t) break;
    pts.push(`${x.toFixed(1)},${(y - v * h).toFixed(1)}`);
  }
  return pts.join(" ");
};
const lastSpike = (spikes: number[], t: number) => spikes.filter((s) => s <= t).pop() ?? -9;

const Spike: FC<{ dur: number }> = ({ dur }) => {
  const t = useT();
  const w = useW();
  const spikes = [0.6, 1.5, 1.9, 3.1, 3.6, 4.8, 5.2, 6.3, 7.0, 7.9, 8.6, 9.5, 10.1, 11.2].filter((s) => s < dur + 1);
  const on = t - lastSpike(spikes, t) < 0.22;
  return (
    <Dark>
      <svg width={W} height={H} style={{ position: "absolute" }}>
        <text x={330} y={250} fill={MUTED} fontSize={34} fontFamily={SERIF} textAnchor="middle">{w.neuron}</text>
        <circle cx={330} cy={430} r={70} fill="#1f3a4a" stroke={on ? BLUE : "#3c6a80"} strokeWidth={6} />
        {[-60, -20, 25, 70].map((a, i) => (
          <line key={i} x1={330 + 70 * Math.cos((a * Math.PI) / 180 + Math.PI)} y1={430 + 70 * Math.sin((a * Math.PI) / 180 + Math.PI)}
            x2={330 + 150 * Math.cos((a * Math.PI) / 180 + Math.PI)} y2={430 + 150 * Math.sin((a * Math.PI) / 180 + Math.PI)} stroke="#3c6a80" strokeWidth={5} />
        ))}
        <line x1={400} y1={430} x2={520} y2={430} stroke="#3c6a80" strokeWidth={6} />
        <rect x={520} y={300} width={860} height={260} rx={16} fill="rgba(255,255,255,.03)" stroke="rgba(255,255,255,.08)" />
        <polyline points={trace(spikes, t, 540, 1360, 470, 140)} fill="none" stroke={BLUE} strokeWidth={4} />
        <text x={950} y={610} fill={MUTED} fontSize={28} fontFamily={SERIF} textAnchor="middle">{w.sameHeight}</text>
        <circle cx={1600} cy={430} r={90} fill={on ? "#ffe9a8" : "#2a2f35"} stroke={on ? GOLD : "#444b52"} strokeWidth={6}
          style={{ filter: on ? `drop-shadow(0 0 40px ${GOLD})` : "none" }} />
        <text x={1600} y={455} fill={on ? INK : MUTED} fontSize={76} fontFamily={SERIF} textAnchor="middle">{on ? "1" : "0"}</text>
        <text x={1600} y={590} fill={MUTED} fontSize={30} fontFamily={SERIF} textAnchor="middle">{w.fire01}</text>
      </svg>
      <Caption text={w.likeSwitch} at={Math.max(0.5, dur * 0.6)} />
    </Dark>
  );
};

const Rate: FC<{ dur: number }> = ({ dur }) => {
  const t = useT();
  const w = useW();
  const slow = [0.4, 1.8, 3.2, 4.6, 6.0, 7.4, 8.8, 10.2];
  const fast = Array.from({ length: 60 }, (_, i) => 0.2 + i * 0.28 + 0.06 * Math.sin(i * 1.7));
  return (
    <Dark>
      <svg width={W} height={H} style={{ position: "absolute" }}>
        <text x={260} y={330} fill={SOFT} fontSize={38} fontFamily={SERIF} textAnchor="end">{w.slow}</text>
        <polyline points={trace(slow, t, 300, 1660, 340, 110)} fill="none" stroke={BLUE} strokeWidth={4} />
        <text x={260} y={610} fill={SOFT} fontSize={38} fontFamily={SERIF} textAnchor="end">{w.fast}</text>
        <polyline points={trace(fast, t, 300, 1660, 620, 110)} fill="none" stroke={AMBER} strokeWidth={4} />
      </svg>
      <Caption text={w.rate1} at={0.6} y={790} size={46} color={SOFT} />
      <Caption text={w.rate2} at={Math.max(1.5, dur * 0.55)} y={870} size={46} />
    </Dark>
  );
};

const TimeBars: FC<{ dur: number }> = ({ dur }) => {
  const t = useT();
  const w = useW();
  const scale = 120; // px per millisecond
  const a = interpolate(t, [0.6, 1.2], [0, 0.5 * scale], { ...clamp, easing: ease });
  const b = interpolate(t, [1.8, 4.4], [0, 10 * scale], { ...clamp, easing: ease });
  return (
    <Dark>
      <svg width={W} height={H} style={{ position: "absolute" }}>
        <text x={300} y={350} fill={GREEN} fontSize={42} fontFamily={SERIF} textAnchor="end">{w.alga}</text>
        <rect x={340} y={315} width={a} height={50} rx={8} fill={GREEN} />
        <text x={360 + a} y={352} fill={GREEN} fontSize={38} fontFamily={SERIF} opacity={appear(t, 1.2)}>{w.halfMs}</text>
        <text x={300} y={530} fill={SOFT} fontSize={42} fontFamily={SERIF} textAnchor="end">{w.ourEyes}</text>
        <rect x={340} y={495} width={b} height={50} rx={8} fill="#7b8790" />
        <text x={360 + b} y={532} fill={SOFT} fontSize={38} fontFamily={SERIF} opacity={appear(t, 4.2)}>{w.tenMs}</text>
        {Array.from({ length: 11 }, (_, i) => (
          <g key={i} opacity={0.5}>
            <line x1={340 + i * scale} y1={590} x2={340 + i * scale} y2={606} stroke={MUTED} strokeWidth={2} />
            {i % 5 === 0 ? <text x={340 + i * scale} y={640} fill={MUTED} fontSize={24} textAnchor="middle" fontFamily={SERIF}>{w.ms(i)}</text> : null}
          </g>
        ))}
      </svg>
      <Caption text={w.faster} at={Math.max(4.6, dur * 0.7)} y={760} size={64} color={GREEN} />
    </Dark>
  );
};

/** The membrane with one door in it; blue light opens it and charged particles flow in, making a signal. */
const Gate: FC<{ dur: number }> = ({ dur }) => {
  const t = useT();
  const w = useW();
  const lightOn = interpolate(t, [dur * 0.32, dur * 0.36], [0, 1], clamp);
  const open = interpolate(t, [dur * 0.36, dur * 0.42], [0, 1], { ...clamp, easing: ease });
  const flow = Math.max(0, t - dur * 0.42);
  const cx = 960, my = 470;
  const ions = Array.from({ length: 14 }, (_, i) => {
    const phase = (flow * 1.1 + i * 0.37) % 2.6;
    const inside = open > 0.5 && flow > i * 0.18;
    const y = inside ? my - 150 + phase * 140 : my - 150 - (i % 4) * 30;
    const x = inside ? cx + Math.sin(i * 2.3 + phase) * (phase < 1 ? 10 : 70 + phase * 30) : cx - 500 + i * 75;
    return { x, y, show: inside ? phase < 2.5 : true };
  });
  const sig = interpolate(t, [dur * 0.5, dur * 0.56, dur * 0.62], [0, 1, 0], clamp);
  return (
    <Dark>
      <svg width={W} height={H} style={{ position: "absolute" }}>
        <defs>
          <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={BLUE} stopOpacity={0.85} /><stop offset="1" stopColor={BLUE} stopOpacity={0.05} /></linearGradient>
        </defs>
        <rect x={cx - 70} y={60} width={140} height={my - 60} fill="url(#beam)" opacity={lightOn} />
        <text x={cx + 110} y={140} fill={BLUE} fontSize={40} fontFamily={SERIF} opacity={lightOn}>{w.light}</text>
        {Array.from({ length: 30 }, (_, i) => {
          const x = 140 + i * 58;
          if (Math.abs(x - cx) < 90) return null;
          return <g key={i}><circle cx={x} cy={my - 30} r={20} fill="#d9c9a6" /><circle cx={x} cy={my + 30} r={20} fill="#d9c9a6" />
            <line x1={x} y1={my - 10} x2={x} y2={my + 10} stroke="#b9a785" strokeWidth={4} /></g>;
        })}
        <rect x={cx - 70 - open * 26} y={my - 60} width={58} height={120} rx={20} fill={RED} />
        <rect x={cx + 12 + open * 26} y={my - 60} width={58} height={120} rx={20} fill={RED} />
        <text x={cx - 230} y={my - 90} fill={RED} fontSize={34} fontFamily={SERIF} textAnchor="end" opacity={appear(t, 0.6)}>{w.door}</text>
        {ions.map((p, i) => p.show ? (
          <g key={i}><circle cx={p.x} cy={p.y} r={14} fill="#ff8a7a" /><text x={p.x} y={p.y + 7} fill="#fff" fontSize={22} textAnchor="middle">+</text></g>
        ) : null)}
        <text x={260} y={my - 150} fill="#ff8a7a" fontSize={30} fontFamily={SERIF} opacity={appear(t, 0.9)}>{w.particles}</text>
        <text x={110} y={my + 120} fill={MUTED} fontSize={28} fontFamily={SERIF}>{w.inside}</text>
        <polyline points={`700,860 900,860 950,${860 - sig * 120} 1000,860 1220,860`} fill="none" stroke={BLUE} strokeWidth={5} opacity={appear(t, dur * 0.48)} />
        <text x={1260} y={870} fill={BLUE} fontSize={36} fontFamily={SERIF} opacity={appear(t, dur * 0.5)}>{w.signal}</text>
      </svg>
    </Dark>
  );
};

const CELL_SPOTS = [[420, 360], [760, 300], [1120, 350], [1480, 320], [560, 650], [940, 640], [1320, 660], [1620, 600]];
const Cells: FC<{ dur: number }> = ({ dur }) => {
  const t = useT();
  const w = useW();
  return (
    <Dark>
      <svg width={W} height={H} style={{ position: "absolute" }}>
        {CELL_SPOTS.map(([x, y], i) => {
          const gotIt = appear(t, 0.4 + i * 0.25, 0.5);
          const flash = (Math.sin((t - dur * 0.55) * 6 + i) > 0.2 && t > dur * 0.55) ? 1 : 0;
          const shapes = [<ellipse key="a" cx={x} cy={y} rx={110} ry={80} />, <circle key="b" cx={x} cy={y} r={85} />,
            <rect key="c" x={x - 100} y={y - 70} width={200} height={140} rx={50} />];
          return (
            <g key={i} fill={flash ? "#2c5f8f" : "#1d2b36"} stroke={flash ? BLUE : "#3a4d5a"} strokeWidth={5}
              style={{ filter: flash ? `drop-shadow(0 0 24px ${BLUE})` : "none" }}>
              {shapes[i % 3]}
              <circle cx={x + 40} cy={y - 30} r={16 * gotIt} fill={BLUE} stroke="none" />
            </g>
          );
        })}
      </svg>
      <Caption text={w.cells} at={dur * 0.45} y={860} size={46} />
    </Dark>
  );
};

const Patch: FC<{ dur: number }> = ({ dur }) => {
  const t = useT();
  const w = useW();
  const r = interpolate(t, [0.5, 2.0], [0, 330], { ...clamp, easing: ease });
  const cx = 960, cy = 470;
  const pts = Array.from({ length: 70 }, (_, i) => {
    const a = i * 2.39996, d = 40 + Math.sqrt(i) * 62;
    return { x: cx + Math.cos(a) * d * 1.6, y: cy + Math.sin(a) * d * 0.95, marked: i % 3 === 0 };
  });
  return (
    <Dark>
      <svg width={W} height={H} style={{ position: "absolute" }}>
        <circle cx={cx} cy={cy} r={r} fill={BLUE} opacity={0.14} />
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={BLUE} strokeOpacity={0.4} strokeWidth={3} />
        {pts.map((p, i) => {
          const inside = Math.hypot(p.x - cx, p.y - cy) < r;
          const fire = p.marked && inside && Math.sin(t * 7 + i) > 0.3;
          return (
            <g key={i}>
              <line x1={p.x} y1={p.y} x2={p.x + 26} y2={p.y - 18} stroke="#3a4d5a" strokeWidth={3} />
              <circle cx={p.x} cy={p.y} r={14} fill={fire ? "#bfe0ff" : p.marked ? "#2b6f8a" : "#3a4048"}
                style={{ filter: fire ? `drop-shadow(0 0 16px ${BLUE})` : "none" }} />
            </g>
          );
        })}
      </svg>
      <div style={{ position: "absolute", right: 120, top: 120, fontFamily: SERIF, fontSize: 30, color: SOFT, lineHeight: 1.8, ...rise(appear(t, 0.8)) }}>
        <div><span style={{ color: "#5bb0cf" }}>●</span> {w.marked}</div>
        <div><span style={{ color: "#6a727c" }}>●</span> {w.others}</div>
      </div>
      <Caption text={w.onlyMarked} at={dur * 0.55} y={880} size={46} />
    </Dark>
  );
};

const BITS = "01000001";
const Bits: FC<{ dur: number }> = ({ dur }) => {
  const t = useT();
  const w = useW();
  // the single switch hands over to the row of eight without an empty moment between them
  const row = appear(t, dur * 0.42, 0.6);
  const single = 1 - appear(t, dur * 0.42, 0.4);
  return (
    <Dark>
      <svg width={W} height={H} style={{ position: "absolute" }}>
        <g opacity={single}>
          <rect x={900} y={300} width={120} height={200} rx={20} fill="#2a2f35" stroke="#5b636b" strokeWidth={4} />
          <rect x={925} y={Math.sin(t * 3) > 0 ? 325 : 405} width={70} height={70} rx={12} fill={Math.sin(t * 3) > 0 ? GOLD : "#555d65"} />
          <text x={960} y={580} fill={PAPER} fontSize={44} fontFamily={SERIF} textAnchor="middle">{w.press}</text>
          <text x={960} y={650} fill={GOLD} fontSize={40} fontFamily={SERIF} textAnchor="middle">{w.oneBit}</text>
        </g>
        {BITS.split("").map((b, i) => {
          const o = appear(t, dur * 0.42 + i * 0.12, 0.4);
          const x = 960 + (i - 3.5) * 150;
          return (
            <g key={i} opacity={o}>
              <rect x={x - 55} y={380} width={110} height={170} rx={18} fill="#2a2f35" stroke="#5b636b" strokeWidth={4} />
              <rect x={x - 32} y={b === "1" ? 400 : 465} width={64} height={64} rx={10} fill={b === "1" ? GOLD : "#555d65"} />
              <text x={x} y={620} fill={b === "1" ? GOLD : MUTED} fontSize={52} fontFamily={SERIF} textAnchor="middle">{b}</text>
            </g>
          );
        })}
      </svg>
      <Caption text={w.string} at={dur * 0.6} y={760} size={50} />
    </Dark>
  );
};

/** The eye, drawn in the order the signal travels: light → the eye's own light switches → relay cells → optic nerve → brain. */
const EyeChain: FC<{ mode: string; dur: number }> = ({ mode, dur }) => {
  const t = useT();
  const w = useW();
  const ys = [300, 420, 540, 660];
  const switchX = 600, relayX = 900, gangX = 1140;
  const broken = mode !== "normal";
  const fade = (i: number) => (mode === "broken" ? interpolate(t, [0.6 + i * 0.5, 1.1 + i * 0.5], [1, 0.15], clamp) : broken ? 0.15 : 1);
  const newOnes = ["new", "amber", "dim"].includes(mode);
  const markerColor = mode === "new" ? BLUE : AMBER;
  const markerIn = mode === "new" ? appear(t, 0.8, 0.8) : newOnes ? 1 : 0;
  const pulse = (t * 0.8) % 1;
  const signalOn = mode === "normal" || (mode === "amber" && t > dur * 0.45) || (mode === "dim" && t > dur * 0.55);
  const lightColor = mode === "amber" || (mode === "dim" && t > dur * 0.55) ? AMBER : "#fff6dc";
  const lightOpacity = mode === "dim" && t <= dur * 0.55 ? 0.35 : 0.9;
  const wire = mode === "wire" ? 0.5 + 0.5 * Math.sin(t * 4) : 0;
  return (
    <Dark>
      <svg width={W} height={H} style={{ position: "absolute" }}>
        {ys.map((y, i) => (
          <line key={`l${i}`} x1={120} y1={y} x2={switchX - 40} y2={y} stroke={lightColor} strokeWidth={mode === "dim" && t > dur * 0.55 ? 10 : 5}
            strokeOpacity={lightOpacity} strokeDasharray="18 14" strokeDashoffset={-t * 80} />
        ))}
        <text x={140} y={230} fill={lightColor} fontSize={36} fontFamily={SERIF} opacity={lightOpacity}>{w.light}</text>
        {ys.map((y, i) => (
          <g key={`s${i}`} opacity={fade(i)}>
            <rect x={switchX - 30} y={y - 40} width={60} height={80} rx={14} fill={GOLD} />
          </g>
        ))}
        <text x={switchX} y={760} fill={broken ? MUTED : GOLD} fontSize={30} fontFamily={SERIF} textAnchor="middle">{w.eyeSwitches}</text>
        <text x={switchX} y={800} fill={MUTED} fontSize={24} fontFamily={SERIF} textAnchor="middle">{w.rodsCones}</text>
        {mode === "broken" ? ys.map((y, i) => (
          <text key={`x${i}`} x={switchX} y={y + 16} fill={RED} fontSize={54} textAnchor="middle" opacity={interpolate(t, [1.0 + i * 0.5, 1.4 + i * 0.5], [0, 1], clamp)}>×</text>
        )) : null}
        {[360, 480, 600].map((y, i) => (
          <g key={`r${i}`}>
            <line x1={switchX + 30} y1={ys[i]} x2={relayX - 34} y2={y} stroke="#4a5a66" strokeWidth={4} />
            <line x1={switchX + 30} y1={ys[i + 1]} x2={relayX - 34} y2={y} stroke="#4a5a66" strokeWidth={4} />
            <circle cx={relayX} cy={y} r={34} fill="#22313c" stroke={wire ? GREEN : "#4f6574"} strokeWidth={wire ? 6 : 4} />
            <line x1={relayX + 34} y1={y} x2={gangX - 40} y2={480} stroke="#4a5a66" strokeWidth={4} />
          </g>
        ))}
        <circle cx={gangX} cy={480} r={44} fill="#22313c" stroke={wire ? GREEN : "#4f6574"} strokeWidth={wire ? 6 : 4} />
        {newOnes ? [[relayX, 360], [relayX, 480], [relayX, 600], [gangX, 480]].map(([x, y], i) => (
          <circle key={`m${i}`} cx={x + 22} cy={y - 26} r={15 * markerIn} fill={markerColor}
            style={{ filter: `drop-shadow(0 0 12px ${markerColor})` }} />
        )) : null}
        <text x={(relayX + gangX) / 2} y={760} fill={wire ? GREEN : SOFT} fontSize={30} fontFamily={SERIF} textAnchor="middle">{w.relay}</text>
        <path d={`M ${gangX + 44} 480 C 1350 480, 1420 470, 1560 470`} stroke={wire ? GREEN : "#6c7c88"} strokeWidth={wire ? 10 : 8} fill="none" />
        <text x={1400} y={430} fill={wire ? GREEN : SOFT} fontSize={30} fontFamily={SERIF} textAnchor="middle">{w.nerve}</text>
        <ellipse cx={1680} cy={470} rx={120} ry={95} fill="#2a2230" stroke={signalOn ? "#e9a8ff" : "#5b4f66"} strokeWidth={5}
          style={{ filter: signalOn ? "drop-shadow(0 0 30px #e9a8ff)" : "none" }} />
        <text x={1680} y={482} fill={SOFT} fontSize={36} fontFamily={SERIF} textAnchor="middle">{w.brain}</text>
        {signalOn ? [0, 0.33, 0.66].map((o, i) => {
          const p = (pulse + o) % 1;
          const x = interpolate(p, [0, 1], [switchX + 30, 1560]);
          return <circle key={`p${i}`} cx={x} cy={470 + Math.sin(p * 6) * 20} r={10} fill={BLUE} opacity={0.9} />;
        }) : null}
      </svg>
      {mode === "broken" ? <Caption text={w.broken} at={dur * 0.5} y={880} size={44} /> : null}
      {mode === "wire" ? <Caption text={w.wire} at={0.4} y={880} size={44} color={GREEN} /> : null}
      {mode === "new" ? <Caption text={w.newQ} at={1.4} y={880} size={48} color={BLUE} /> : null}
      {mode === "amber" ? <Caption text={w.amber} at={dur * 0.5} y={880} size={44} color={AMBER} /> : null}
      {mode === "dim" ? <Caption text={w.dim} at={0.6} y={880} size={44} color={AMBER} /> : null}
    </Dark>
  );
};

const Codec: FC<{ dur: number }> = ({ dur }) => {
  const t = useT();
  const w = useW();
  return (
    <Dark>
      <div style={{ position: "absolute", left: 0, right: 0, top: 150, textAlign: "center", fontFamily: SERIF, fontSize: 30, color: MUTED,
        letterSpacing: 4, ...rise(appear(t, 0.2)) }}>{w.shannon}</div>
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 18, paddingBottom: 120 }}>
        {w.steps.map(([a, b], i) => {
          const at = i < 3 ? 0.3 + i * 0.7 : dur * 0.5 + (i - 3) * 0.9;
          const key = w.keySteps.includes(b);
          return (
            <div key={a} style={{ display: "flex", alignItems: "center", gap: 18, ...rise(appear(t, at)) }}>
              <div style={{ width: 250, padding: "30px 10px", borderRadius: 22, textAlign: "center", fontFamily: SERIF,
                background: key ? "rgba(255,177,61,.14)" : "rgba(255,255,255,.05)", border: `2px solid ${key ? AMBER : "rgba(255,255,255,.18)"}` }}>
                <div style={{ fontSize: 36 * (w.scale < 1 ? 0.8 : 1), color: PAPER, letterSpacing: w.scale < 1 ? 0 : 2 }}>{a}</div>
                <div style={{ fontSize: key ? 52 : 30, color: key ? AMBER : MUTED, marginTop: 10, letterSpacing: 6 }}>{b}</div>
              </div>
              {i < w.steps.length - 1 ? <div style={{ fontSize: 44, color: MUTED }}>→</div> : null}
            </div>
          );
        })}
      </AbsoluteFill>
    </Dark>
  );
};

const Anim: FC<{ s: Shot; dur: number }> = ({ s, dur }) => {
  switch (s.name) {
    case "spike": return <Spike dur={dur} />;
    case "rate": return <Rate dur={dur} />;
    case "timebars": return <TimeBars dur={dur} />;
    case "gate": return <Gate dur={dur} />;
    case "cells": return <Cells dur={dur} />;
    case "patch": return <Patch dur={dur} />;
    case "bits": return <Bits dur={dur} />;
    case "eye": return <EyeChain mode={s.mode ?? "normal"} dur={dur} />;
    case "codec": return <Codec dur={dur} />;
    default: return <Dark />;
  }
};

const ShotView: FC<{ s: Shot; dur: number }> = ({ s, dur }) => {
  switch (s.k) {
    case "title": return <Title />;
    case "prize": return <Prize s={s} />;
    case "footage": return <Footage s={s} dur={dur} />;
    case "window": return <Window s={s} />;
    case "still": return <Still s={s} dur={dur} />;
    case "nobel": return <Nobel s={s} dur={dur} />;
    case "card": return <Card s={s} />;
    case "anim": return <Anim s={s} dur={dur} />;
    case "end": return <End />;
    default: return <Dark />;
  }
};

const Overlays: FC<{ s: Shot }> = ({ s }) => (
  <>
    {s.lower ? <Lower text={s.lower} at={s.lowerAt ?? 0} /> : null}
    {s.big ? <Big text={s.big} at={s.bigAt ?? 0} /> : null}
    {s.count ? <Count value={s.count} at={s.countAt ?? 0} /> : null}
    {s.verse ? <Verse text={s.verse} refText={s.ref ?? ""} at={s.verseAt ?? 0} /> : null}
    {s.ask ? <Ask lines={s.ask} at={s.askAt ?? []} /> : null}
  </>
);

const ChapterCard: FC<{ name: string; p: number }> = ({ name, p }) => {
  const o = interpolate(p, [0.1, 0.5, CARD - 0.5, CARD], [0, 1, 1, 0], clamp);
  return (
    <div style={{ position: "absolute", left: 70, top: 64, opacity: o, transform: `translateY(${(1 - o) * 12}px)`, fontFamily: SERIF,
      background: "rgba(10,12,15,.72)", borderRadius: 14, padding: "12px 34px", border: "1px solid rgba(210,173,98,.4)" }}>
      <div style={{ fontSize: 44, color: PAPER, letterSpacing: 6 }}>{name}</div>
    </div>
  );
};

const Faded: FC<{ first: boolean; children: ReactNode }> = ({ first, children }) => {
  const t = useT();
  const o = first ? interpolate(t, [0, 1.2], [0, 1], clamp) : interpolate(t, [0, FADE], [0, 1], clamp);
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};

export const FunInformatics04Video: FC<Fi04Props> = ({ tl, lang = "zh" }) => {
  useFonts();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!tl) return <AbsoluteFill style={{ background: INK }} />;
  const t = frame / fps;
  const chapters = tl.chapters.map((c) => ({ ...c, en: undefined, enShort: undefined }));
  const titleShot = tl.shots.find((s) => s.k === "title");
  const endShot = tl.shots.find((s) => s.k === "end");
  const cardAt = tl.chapters.map((c) => c.start);
  const card = cardAt.findIndex((a, i) => i > 0 && t >= a && t < a + CARD);
  const inTitle = titleShot && t >= titleShot.start && t < titleShot.end + 0.4;
  const barOn = !inTitle && (!endShot || t < endShot.start);
  return (
    <Lang.Provider value={lang}>
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
      {card >= 0 ? <ChapterCard name={tl.chapters[card].name} p={t - cardAt[card]} /> : null}
      {barOn ? <ChapterBar chapters={chapters} duration={tl.durationSeconds} t={t} /> : null}
    </AbsoluteFill>
    </Lang.Provider>
  );
};
