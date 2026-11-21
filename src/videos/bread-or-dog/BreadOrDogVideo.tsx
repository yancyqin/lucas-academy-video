/**
 * 「怎么骗过 AI：面包还是狗？」 / "How to Fool an AI: Dog or Bread?" · docs/bread-or-dog/ (script v0.4).
 *
 * One picture for both tracks: English is the default audio, Chinese a separate m4a (Yancy, 2026-11-16: 「Louise 1.1，
 * 英文视频配中文音轨」). As the butterfly film: few words, icons first; words that stay are English large with Chinese
 * small under them; captions are SRTs, never burned in.
 *
 * Timed by scripts/bread-or-dog/build_timeline.py (public/bread-or-dog/timeline.json): every beat hangs on a line's slot
 * (the longer of its English and Chinese takes). Title → it used to be hard (our own look-alike photos, paper cards:
 * Yao 2017, Geirhos et al. 2019 with their CC BY 4.0 cat-with-elephant-skin picture and our own ResNet-50's answer) →
 * trick 1: a real Shiba next to an AI "Shiba", the six AIs' answers, then Yancy's Muse clip cuts it open from the head
 * (tl.muse; until it exists, a dissolve to the end reference frame) → trick 2: the trap in the question, as chat bubbles
 * with the models' own words → trick 3: picture + noise ×25 = attacked picture, ResNet's answers → trick 4: the BREAD
 * note, CLIP's answer → why it is hard now: the photo cut into patches, attention lines, ear/eye/tail together, then a
 * wall of pictures for the data → the cake → credits. Every quote is a model's real reply (data folder picks.html);
 * every research fact is in history-sources.md.
 */
import type { CSSProperties, FC, ReactNode } from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  type CalculateMetadataFunction,
} from "remotion";

const DIR = "bread-or-dog";
export const file = (p: string) => staticFile(`${DIR}/${p}`);

export type BdTimeline = {
  fps: number; durationSeconds: number; title: [number, number]; credits: [number, number];
  sections: Record<string, [number, number]>; lines: Record<string, { start: number; end: number }>;
  music?: string;
  // Yancy's Muse clip of the cake being cut from the head: play it from `from` s into the clip, starting at film time `at`
  muse?: { src: string; from: number; at: number; until: number; length: number; last: string | null } | null;
};
export type BdProps = { tl?: BdTimeline | null };

export const calculateBdMetadata: CalculateMetadataFunction<BdProps> = async ({ props, abortSignal }) => {
  const r = await fetch(file("timeline.json"), { signal: abortSignal });
  if (!r.ok) throw Error("Run scripts/bread-or-dog/assets.py and build_timeline.py first");
  const tl = (await r.json()) as BdTimeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

// ---- look ----
export const BG = "#15100c";
export const INK = "#f7f0e6";
export const SOFT = "#d3c5b3";
export const MUTED = "#9a8d7d";
export const GOLD = "#f2b84b";
export const OK = "#4cc97a";
export const BAD = "#ef5b4f";
export const CAKE = "#f39ab6";
export const SANS = "'Helvetica Neue', 'PingFang SC', sans-serif";
const SERIF = "Georgia, 'Songti SC', serif";
export const SHADOW = "0 3px 18px rgba(0,0,0,.7), 0 1px 3px rgba(0,0,0,.8)";
export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
export const ease = Easing.bezier(0.3, 0.7, 0.2, 1);
export const fadeIn = (t: number, at: number, d = 0.4) => interpolate(t, [at, at + d], [0, 1], { ...clamp, easing: ease });
export const fadeOut = (t: number, at: number, d = 0.4) => interpolate(t, [at - d, at], [1, 0], clamp);
export const pop = (t: number, at: number) => interpolate(t, [at, at + 0.18, at + 0.32], [0.6, 1.08, 1], { ...clamp, easing: ease });
// visible between a and b, cross-fading d at both ends
const span = (t: number, a: number, b: number, d = 0.35) => Math.min(fadeIn(t, a - d / 2, d), fadeOut(t, b + d / 2, d));

const useT = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return f / fps;
};

// ---- icons (24-unit grid) ----
type IconP = { size: number; color: string; style?: CSSProperties };
const Svg: FC<IconP & { children: ReactNode }> = ({ size, color, children, style }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2.1} strokeLinecap="round"
    strokeLinejoin="round" style={{ display: "block", flex: "none", ...style }}>{children}</svg>
);
export const Bot: FC<IconP> = (p) => (
  <Svg {...p}><rect x="4" y="8" width="16" height="11" rx="3" /><path d="M12 8V4.5" /><circle cx="12" cy="3.6" r="1.1" />
    <circle cx="9" cy="13.2" r="1.2" fill={p.color} /><circle cx="15" cy="13.2" r="1.2" fill={p.color} /><path d="M2 12.5v3M22 12.5v3" /></Svg>
);
export const Dog: FC<IconP> = (p) => (
  <Svg {...p}><path d="M6.2 9.2 4.6 3.8l4.6 2.6M17.8 9.2l1.6-5.4-4.6 2.6" />
    <path d="M6 9.5C6 7 8.7 5.6 12 5.6s6 1.4 6 3.9v3.6c0 3.7-2.7 6.7-6 6.7s-6-3-6-6.7z" />
    <circle cx="9.5" cy="11.6" r=".95" fill={p.color} /><circle cx="14.5" cy="11.6" r=".95" fill={p.color} />
    <path d="M10.9 15.1h2.2L12 16.4z" fill={p.color} /></Svg>
);
export const Cat: FC<IconP> = (p) => (
  <Svg {...p}><path d="M5.5 10.5 5 3.8l4.6 3M18.5 10.5l.5-6.7-4.6 3" />
    <path d="M5.5 10.5c0-2.6 2.9-4 6.5-4s6.5 1.4 6.5 4v2.2c0 3.8-2.9 6.8-6.5 6.8s-6.5-3-6.5-6.8z" />
    <path d="M9.3 11.6v1M14.7 11.6v1" /><path d="M11.2 15h1.6L12 15.9z" fill={p.color} /><path d="M2.5 14.5l4 .5M2.8 17l3.9-.6M21.5 14.5l-4 .5M21.2 17l-3.9-.6" /></Svg>
);
export const Bread: FC<IconP> = (p) => (
  <Svg {...p}><path d="M4 11.2C4 7.8 7.6 5.5 12 5.5s8 2.3 8 5.7c0 1.2-.7 2-1.8 2.2V19H5.8v-5.6C4.7 13.2 4 12.4 4 11.2z" />
    <path d="M9 10.2l1.6-2.1M12.7 10.2l1.6-2.1" /></Svg>
);
const Elephant: FC<IconP> = (p) => (
  <Svg {...p}><path d="M5 17V11a6 6 0 0 1 6-6h3a6 6 0 0 1 6 6v6" /><path d="M8 17v2.5M16 17v2.5" />
    <path d="M20 11.5c1.6 0 2 1.4 2 3s-.6 3-1.8 3" /><circle cx="15.5" cy="9.6" r=".9" fill={p.color} /><path d="M9.5 6.5c-1.6 1-2.2 3-1.6 4.6" /></Svg>
);
export const Cake: FC<IconP> = (p) => (
  <Svg {...p}><path d="M3 19.5h18v-8L3 15.5z" /><path d="M3 17.5h18" /><circle cx="17.5" cy="7.6" r="1.7" /><path d="M17.5 5.9V4.2" /></Svg>
);
export const Camera: FC<IconP> = (p) => (
  <Svg {...p}><rect x="3" y="7" width="18" height="13" rx="2.5" /><circle cx="12" cy="13.5" r="3.6" /><path d="M8.5 7l1.5-2.5h4L15.5 7" /></Svg>
);
const Sparkle: FC<IconP> = (p) => (
  <Svg {...p}><path d="M11 3.5l1.7 4.9 4.9 1.7-4.9 1.7L11 16.7l-1.7-4.9-4.9-1.7 4.9-1.7z" /><path d="M18.5 14.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z" /></Svg>
);
const Person: FC<IconP> = (p) => (
  <Svg {...p}><circle cx="12" cy="8" r="4" /><path d="M4 20.5c.8-4.2 4-6.5 8-6.5s7.2 2.3 8 6.5" /></Svg>
);
export const Check: FC<IconP> = (p) => <Svg {...p}><path d="M4.5 12.5l4.6 4.5L19.5 6.5" /></Svg>;
const Paper: FC<IconP> = (p) => (
  <Svg {...p}><path d="M6 3h9l4 4v14H6z" /><path d="M15 3v4h4M9 11h7M9 14.5h7M9 18h5" /></Svg>
);

// ---- pieces ----
const Pic: FC<{ src: string; w: number; h: number; style?: CSSProperties; imgStyle?: CSSProperties }> = ({ src, w, h, style, imgStyle }) => (
  <div style={{ width: w, height: h, borderRadius: 18, overflow: "hidden", boxShadow: "0 18px 50px rgba(0,0,0,.55)", ...style }}>
    <Img src={file(src)} style={{ width: "100%", height: "100%", objectFit: "cover", display: "block", ...imgStyle }} />
  </div>
);

const Heading: FC<{ t: number; at: number; n: number }> = ({ t, at, n }) => (
  <div style={{ position: "absolute", left: 70, top: 52, display: "flex", alignItems: "baseline", gap: 16, fontFamily: SANS,
    opacity: fadeIn(t, at, 0.5), transform: `translateY(${interpolate(fadeIn(t, at, 0.5), [0, 1], [-14, 0])}px)` }}>
    <span style={{ fontSize: 46, fontWeight: 800, color: GOLD, letterSpacing: 1 }}>Trick {n}</span>
    <span style={{ fontSize: 30, color: SOFT }}>第{"一二三四"[n - 1]}招</span>
  </div>
);

type Said = "dog" | "bread" | "cat" | "elephant";
const ICON: Record<Said, FC<IconP>> = { dog: Dog, bread: Bread, cat: Cat, elephant: Elephant };
// a model's answer: robot, name, year, what it said
export const Chip: FC<{ name: string; year?: string; said: Said; label?: string; ok: boolean | null; t: number; at: number; big?: boolean }> =
  ({ name, year, said, label, ok, t, at, big }) => {
    const color = ok === null ? INK : ok ? OK : BAD;
    const s = big ? 1.25 : 1;
    const Icon = ICON[said];
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 12 * s, padding: `${10 * s}px ${20 * s}px`, borderRadius: 40,
        background: "rgba(20,15,11,.85)", boxShadow: `inset 0 0 0 2px ${color}88`, fontFamily: SANS, whiteSpace: "nowrap",
        opacity: fadeIn(t, at, 0.2), transform: `scale(${pop(t, at)})` }}>
        <Bot size={34 * s} color={SOFT} />
        <span style={{ fontSize: 30 * s, fontWeight: 700, color: INK }}>{name}</span>
        {year ? <span style={{ fontSize: 22 * s, color: MUTED }}>{year}</span> : null}
        <span style={{ width: 2, height: 30 * s, background: "rgba(255,255,255,.18)" }} />
        <Icon size={38 * s} color={color} />
        {label ? <span style={{ fontSize: 30 * s, fontWeight: 700, color }}>{label}</span> : null}
      </div>
    );
  };

export const MODELS: [string, string][] = [["AlexNet", "2012"], ["ResNet", "2015"], ["CLIP", "2021"], ["LLaVA", "2024"], ["Fable", "2026"], ["Astra", "2026"]];

// a paper, as our own card (title, authors, venue, year) — no screenshots of figures we may not reuse
const PaperCard: FC<{ t: number; at: number; title: string; who: string; zh: string; style?: CSSProperties }> = ({ t, at, title, who, zh, style }) => (
  <div style={{ display: "flex", gap: 22, alignItems: "flex-start", padding: "26px 34px", borderRadius: 18, width: 760,
    background: "#f6efe3", color: "#2a1f15", boxShadow: "0 20px 50px rgba(0,0,0,.5)", fontFamily: SANS,
    opacity: fadeIn(t, at, 0.35), transform: `translateY(${interpolate(fadeIn(t, at, 0.35), [0, 1], [30, 0])}px) rotate(-1.2deg)`, ...style }}>
    <Paper size={54} color="#8a5a2b" />
    <div>
      <div style={{ fontFamily: SERIF, fontSize: 36, lineHeight: 1.22, fontWeight: 700 }}>{title}</div>
      <div style={{ fontSize: 24, color: "#6d5a45", marginTop: 10 }}>{who}</div>
      <div style={{ fontSize: 24, color: "#8a5a2b", marginTop: 6 }}>{zh}</div>
    </div>
  </div>
);

const Tag: FC<{ t: number; at: number; who: string; said: string; style?: CSSProperties }> = ({ t, at, who, said, style }) => (
  <div style={{ position: "absolute", display: "flex", alignItems: "center", gap: 12, padding: "12px 22px", borderRadius: 40,
    background: "rgba(20,15,11,.9)", boxShadow: `inset 0 0 0 2px ${BAD}aa`, fontFamily: SANS, whiteSpace: "nowrap", opacity: fadeIn(t, at, 0.2),
    transform: `scale(${pop(t, at)})`, ...style }}>
    <Bot size={34} color={SOFT} /><span style={{ fontSize: 28, color: SOFT, fontWeight: 600 }}>{who}</span>
    <span style={{ fontSize: 36, color: BAD, fontWeight: 800 }}>“{said}”</span>
  </div>
);

// a chat bubble: me (right, warm) or a model (left, dark), English large and Chinese small
const Bubble: FC<{ who: "me" | string; en: ReactNode; zh: string; t: number; at: number; tone?: "ok" | "bad"; w?: number }> =
  ({ who, en, zh, t, at, tone, w = 820 }) => {
    const me = who === "me";
    const ring = tone === "ok" ? OK : tone === "bad" ? BAD : "transparent";
    return (
      <div style={{ alignSelf: me ? "flex-end" : "flex-start", maxWidth: w, fontFamily: SANS, opacity: fadeIn(t, at, 0.3),
        transform: `translateY(${interpolate(fadeIn(t, at, 0.3), [0, 1], [24, 0])}px)` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8, justifyContent: me ? "flex-end" : "flex-start" }}>
          {me ? <Person size={30} color={GOLD} /> : <Bot size={32} color={SOFT} />}
          <span style={{ fontSize: 26, fontWeight: 700, color: me ? GOLD : SOFT }}>{me ? "Me · 我" : who}</span>
        </div>
        <div style={{ padding: "20px 28px", borderRadius: 26, borderTopRightRadius: me ? 6 : 26, borderTopLeftRadius: me ? 26 : 6,
          background: me ? "#5a3b1d" : "#2b231c", boxShadow: `inset 0 0 0 3px ${ring}, 0 10px 30px rgba(0,0,0,.4)` }}>
          <div style={{ fontSize: 40, lineHeight: 1.28, color: INK, fontWeight: 500 }}>{en}</div>
          <div style={{ fontSize: 27, lineHeight: 1.35, color: SOFT, marginTop: 10 }}>{zh}</div>
        </div>
      </div>
    );
  };

export const Pill: FC<{ t: number; at: number; color: string; icon: ReactNode; en: string; zh: string; style?: CSSProperties }> =
  ({ t, at, color, icon, en, zh, style }) => (
    <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "16px 34px", borderRadius: 60, fontFamily: SANS,
      background: "rgba(20,15,11,.88)", boxShadow: `inset 0 0 0 3px ${color}`, opacity: fadeIn(t, at, 0.15),
      transform: `scale(${pop(t, at)})`, ...style }}>
      {icon}
      <span style={{ fontSize: 60, fontWeight: 800, color }}>{en}</span>
      <span style={{ fontSize: 36, color: SOFT }}>{zh}</span>
    </div>
  );

// ---- sections ----
const Title: FC<{ t: number; end: number }> = ({ t, end }) => (
  <AbsoluteFill style={{ opacity: fadeOut(t, end, 0.5) }}>
    <AbsoluteFill style={{ flexDirection: "row" }}>
      {["dog-shiba.jpg", "bread-boule.jpg"].map((s) => (
        <div key={s} style={{ flex: 1, overflow: "hidden" }}>
          <Img src={file(s)} style={{ width: "100%", height: "100%", objectFit: "cover",
            transform: `scale(${interpolate(t, [0, end], [1.1, 1.0], clamp)})` }} />
        </div>
      ))}
    </AbsoluteFill>
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(15,10,7,.72) 0%, rgba(15,10,7,.35) 65%, rgba(15,10,7,.2) 100%)" }} />
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SANS, color: INK, textShadow: SHADOW }}>
      <div style={{ fontSize: 136, fontWeight: 800, letterSpacing: -1, opacity: fadeIn(t, 0.2, 0.6) }}>Dog or Bread?</div>
      <div style={{ fontSize: 58, fontWeight: 500, color: SOFT, marginTop: 6, opacity: fadeIn(t, 0.4, 0.6) }}>狗，还是面包？</div>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 40, padding: "12px 30px", borderRadius: 40,
        background: "rgba(15,10,7,.6)", boxShadow: `inset 0 0 0 2px ${GOLD}`, opacity: fadeIn(t, 0.9, 0.6) }}>
        <Bot size={44} color={GOLD} />
        <span style={{ fontSize: 44, fontWeight: 700 }}>How to fool an AI</span>
        <span style={{ fontSize: 32, color: SOFT }}>怎么骗过 AI</span>
      </div>
    </AbsoluteFill>
  </AbsoluteFill>
);

const PAIRS: [string, string][] = [["dog-shiba.jpg", "bread-boule.jpg"], ["dog-dachshund.jpg", "bread-sourdough.jpg"],
  ["dog-fluffy.jpg", "bread-brioche.jpg"], ["dog-corgi.jpg", "bread-rolls.jpg"]];

const SplitPairs: FC<{ t: number; a: number; dim?: number }> = ({ t, a, dim = 0 }) => {
  const k = Math.max(0, Math.floor((t - a) / 1.1)) % PAIRS.length;
  return (
    <AbsoluteFill style={{ flexDirection: "row", gap: 6, filter: `brightness(${1 - 0.62 * dim}) blur(${5 * dim}px)` }}>
      {PAIRS[k].map((s, i) => (
        <div key={s} style={{ flex: 1, overflow: "hidden", position: "relative" }}>
          <Img src={file(s)} style={{ width: "100%", height: "100%", objectFit: "cover",
            transform: `scale(${interpolate((t - a) % 1.1, [0, 1.1], [1.06, 1.0], clamp)})` }} />
          <div style={{ position: "absolute", bottom: 40, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: 1 - dim }}>
            <div style={{ padding: 14, borderRadius: 50, background: "rgba(15,10,7,.6)" }}>
              {i === 0 ? <Dog size={58} color={INK} /> : <Bread size={58} color={INK} />}
            </div>
          </div>
        </div>
      ))}
    </AbsoluteFill>
  );
};

// it used to be hard: look-alikes, Yao 2017, Geirhos et al. 2019, texture; then today's two AIs get the clean photos right
const History: FC<{ t: number; L: (id: string) => number; end: number }> = ({ t, L, end }) => {
  const s = (id: string) => L(id);
  const grid = span(t, s("sc00-02") - 0.2, s("sc00-03"));
  const yao = span(t, s("sc00-03"), s("sc00-05"));
  const geirhos = span(t, s("sc00-05"), s("sc00-07"));
  const texture = span(t, s("sc00-07"), s("sc00-08"));
  const now = fadeIn(t, s("sc00-08") - 0.2, 0.4);
  return (
    <AbsoluteFill>
      {t < s("sc00-02") + 0.3 || t > s("sc00-08") - 0.6 ? <SplitPairs t={t} a={s("sc00-01")} dim={now} /> : null}
      {grid > 0 ? (
        <AbsoluteFill style={{ opacity: grid, background: BG }}>
          <Img src={file("lookalike-grid.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover",
            transform: `scale(${interpolate(t, [s("sc00-02"), s("sc00-03")], [1.25, 1.05], clamp)})` }} />
        </AbsoluteFill>
      ) : null}
      {yao > 0 ? (
        <AbsoluteFill style={{ opacity: yao, background: BG }}>
          <div style={{ position: "absolute", left: 90, top: 80 }}>
            <PaperCard t={t} at={s("sc00-03") + 0.2} title="Chihuahua or Muffin? Searching for the Best Computer Vision API"
              who="Mariya Yao · TOPBOTS · 2017" zh="吉娃娃还是松饼？六家公司的图像识别 API" />
          </div>
          <div style={{ position: "absolute", left: 90, top: 430, display: "flex", gap: 24 }}>
            <Pic src="chihuahua.jpg" w={560} h={420} style={{ opacity: fadeIn(t, s("sc00-03") + 0.6, 0.4) }} />
            <div style={{ position: "relative" }}>
              <Pic src="muffins.jpg" w={560} h={420} style={{ opacity: fadeIn(t, s("sc00-03") + 0.9, 0.4) }} />
              <Tag t={t} at={s("sc00-04") + 0.2} who="Microsoft" said="teddy bear" style={{ left: 250, top: 40 }} />
              <Tag t={t} at={s("sc00-04") + 1.6} who="Google" said="snout" style={{ left: 330, top: 300 }} />
            </div>
          </div>
        </AbsoluteFill>
      ) : null}
      {geirhos > 0 ? (
        <AbsoluteFill style={{ opacity: geirhos, background: BG }}>
          <div style={{ position: "absolute", left: 90, top: 110 }}>
            <PaperCard t={t} at={s("sc00-05") + 0.2} title="ImageNet-trained CNNs are biased towards texture"
              who="Geirhos et al. · ICLR 2019" zh="用 ImageNet 训练的卷积网络，偏爱看纹理" />
          </div>
          <div style={{ position: "absolute", right: 160, top: 110, opacity: fadeIn(t, s("sc00-06") - 0.1, 0.4) }}>
            <div style={{ width: 600, height: 600, borderRadius: 18, overflow: "hidden", boxShadow: "0 18px 50px rgba(0,0,0,.55)" }}>
              <Img src={file("cat-elephant.png")} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </div>
            <div style={{ fontFamily: SANS, fontSize: 18, color: MUTED, marginTop: 8 }}>Image: Geirhos et al., texture-vs-shape · CC BY 4.0</div>
            <div style={{ position: "absolute", left: -100, right: -100, top: 660, display: "flex", justifyContent: "center" }}>
              <Chip name="ResNet-50" said="elephant" label="Indian elephant" ok={false} t={t} at={s("sc00-06") + 1.0} big />
            </div>
          </div>
          <div style={{ position: "absolute", left: 160, top: 560, display: "flex", alignItems: "center", gap: 20, fontFamily: SANS,
            opacity: fadeIn(t, s("sc00-06") + 0.2, 0.3) }}>
            <Cat size={90} color={INK} /><span style={{ fontSize: 60, color: SOFT }}>+</span><Elephant size={90} color={INK} />
            <span style={{ fontSize: 34, color: SOFT, marginLeft: 12 }}>cat shape · elephant skin</span>
          </div>
        </AbsoluteFill>
      ) : null}
      {texture > 0 ? (
        <AbsoluteFill style={{ opacity: texture, background: BG, alignItems: "center", justifyContent: "center", flexDirection: "row", gap: 40 }}>
          {[["texture-fur.jpg", <Dog key="d" size={60} color={INK} />], ["texture-crust.jpg", <Bread key="b" size={60} color={INK} />]].map(([src, icon], i) => (
            <div key={i} style={{ position: "relative", opacity: fadeIn(t, s("sc00-07") + 0.25 * i, 0.4) }}>
              <Pic src={src as string} w={700} h={700} imgStyle={{ transform: `scale(${interpolate(t, [s("sc00-07"), s("sc00-08")], [1.0, 1.08], clamp)})` }} />
              <div style={{ position: "absolute", left: 20, bottom: 20, padding: 12, borderRadius: 40, background: "rgba(15,10,7,.7)",
                opacity: fadeIn(t, s("sc00-07") + 1.2 + 0.4 * i, 0.3) }}>{icon}</div>
            </div>
          ))}
        </AbsoluteFill>
      ) : null}
      {/* today's two AIs get every clean look-alike photo right (the older ones are shown being fooled later) */}
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 30, flexDirection: "row", opacity: now * fadeOut(t, end, 0.3) }}>
        {MODELS.slice(4).map(([n, y], i) => (
          <div key={n} style={{ display: "flex", alignItems: "center", gap: 12, padding: "16px 30px", borderRadius: 40,
            background: "rgba(20,15,11,.85)", fontFamily: SANS, opacity: fadeIn(t, s("sc00-08") + 0.8 + 0.15 * i, 0.2),
            transform: `scale(${pop(t, s("sc00-08") + 0.8 + 0.15 * i)})` }}>
            <Bot size={56} color={SOFT} /><span style={{ fontSize: 48, fontWeight: 700, color: INK }}>{n}</span>
            <span style={{ fontSize: 32, color: MUTED }}>{y}</span>
            <Check size={52} color={OK} style={{ opacity: fadeIn(t, s("sc00-08") + 1.5 + 0.2 * i, 0.2) }} />
          </div>
        ))}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// trick 1: the real Shiba and the AI "Shiba"; the six AIs' answers on the AI one; then the cut, full frame
const CakeTrick: FC<{ t: number; L: (id: string) => number; E: (id: string) => number; at: number; muse?: BdTimeline["muse"] }> =
  ({ t, L, E, at, muse }) => {
    const W = 860, H = 484;
    const s1 = L("sc01-01"), d1 = E("sc01-01") - s1;
    const s2 = L("sc01-02"), d2 = E("sc01-02") - s2;
    const focus = L("sc01-03");
    const reveal = L("sc01-04");
    const f = interpolate(t, [focus - 0.2, focus + 0.6], [0, 1], { ...clamp, easing: ease });
    // the right card grows to the whole frame
    const x0 = 1920 / 2 + 15, y0 = 220;
    const rx = interpolate(f, [0, 1], [x0, 0]), ry = interpolate(f, [0, 1], [y0, 0]);
    const rw = interpolate(f, [0, 1], [W, 1920]), rh = interpolate(f, [0, 1], [H, 1080]);
    const radius = interpolate(f, [0, 1], [18, 0]);
    // no Muse clip yet: hold the first frame, dissolve to the end reference just before 「其实是一个蛋糕」
    const opened = interpolate(t, [reveal - 0.5, reveal - 0.1], [0, 1], clamp);
    return (
      <AbsoluteFill>
        <div style={{ opacity: 1 - f }}><Heading t={t} at={at} n={1} /></div>
        <div style={{ position: "absolute", left: 1920 / 2 - 15 - W, top: y0, opacity: 1 - f }}>
          <Pic src="dog-shiba.jpg" w={W} h={H} style={{ opacity: fadeIn(t, at + 0.2, 0.5) }} />
          <div style={{ position: "absolute", left: 18, top: 18, display: "flex", alignItems: "center", gap: 10, padding: "10px 18px",
            borderRadius: 30, background: "rgba(15,10,7,.75)", fontFamily: SANS, opacity: fadeIn(t, s1 + d1 * 0.3, 0.3) }}>
            <Camera size={36} color={OK} /><span style={{ fontSize: 30, fontWeight: 700, color: INK }}>Real</span>
            <span style={{ fontSize: 24, color: SOFT }}>真的</span>
          </div>
        </div>
        <div style={{ position: "absolute", left: rx, top: ry, width: rw, height: rh, borderRadius: radius, overflow: "hidden",
          boxShadow: "0 18px 50px rgba(0,0,0,.55)", opacity: fadeIn(t, at + 0.2, 0.5) }}>
          {muse && t >= muse.at ? (
            <>
              {/* the clip is shorter than the rest of trick 1: its last frame holds, pushing in slowly on the cut */}
              {muse.last ? (
                <Img src={file(muse.last)} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover",
                  transformOrigin: "60% 38%", transform: `scale(${interpolate(t, [muse.at + muse.length - muse.from, muse.until], [1.0, 1.12], clamp)})` }} />
              ) : null}
              <Sequence from={Math.round(muse.at * 30)} durationInFrames={Math.max(1, Math.floor((muse.length - muse.from) * 30) - 1)} layout="none">
                <OffthreadVideo src={file(muse.src)} startFrom={Math.round(muse.from * 30)} muted
                  style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover" }} />
              </Sequence>
            </>
          ) : (
            <>
              <Img src={file("cake-dog-16x9.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover" }} />
              <Img src={file("cake-end.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", opacity: opened }} />
            </>
          )}
          <div style={{ position: "absolute", left: 18, top: 18, display: "flex", alignItems: "center", gap: 10, padding: "10px 18px",
            borderRadius: 30, background: "rgba(15,10,7,.75)", fontFamily: SANS, opacity: fadeIn(t, s1 + d1 * 0.65, 0.3) * (1 - f) }}>
            <Sparkle size={36} color={GOLD} /><span style={{ fontSize: 30, fontWeight: 700, color: INK }}>AI</span>
            <span style={{ fontSize: 24, color: SOFT }}>AI 画的</span>
          </div>
        </div>
        {/* what the six AIs said about the AI one: five dogs and a cat, no cake */}
        <div style={{ position: "absolute", left: 0, right: 0, top: y0 + H + 50, display: "flex", justifyContent: "center", gap: 16,
          flexWrap: "wrap", padding: "0 120px", opacity: 1 - f }}>
          {MODELS.map(([n], i) => (
            <Chip key={n} name={n} said={n === "AlexNet" ? "cat" : "dog"} ok={null} t={t} at={s2 + (d2 * 0.7 * i) / 6} />
          ))}
        </div>
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 40, display: "flex", justifyContent: "center" }}>
          <Pill t={t} at={reveal + 0.2} color={CAKE} icon={<Cake size={60} color={CAKE} />} en="Cake!" zh="蛋糕" />
        </div>
      </AbsoluteFill>
    );
  };

const hl = (on: number) => ({ background: `rgba(242,184,75,${0.4 * on})`, borderRadius: 8, padding: "0 4px",
  boxShadow: `0 0 0 ${3 * on}px rgba(242,184,75,${0.6 * on})` });

const TrapTrick: FC<{ t: number; L: (id: string) => number; at: number }> = ({ t, L, at }) => {
  const bStart = L("sc02-05"), qStart = L("sc02-08");
  const swap = (a: number) => fadeIn(t, a - 0.3, 0.4);
  const picA = 1 - swap(bStart);
  const chatA = 1 - swap(bStart), chatB = swap(bStart);
  const q = swap(qStart);
  return (
    <AbsoluteFill>
      <Heading t={t} at={at} n={2} />
      <div style={{ position: "absolute", left: 80, top: 190, filter: `brightness(${1 - 0.55 * q}) blur(${4 * q}px)` }}>
        <div style={{ position: "relative", width: 880, height: 660 }}>
          <Pic src="tray-puppy.jpg" w={880} h={660} style={{ position: "absolute", opacity: fadeIn(t, at + 0.2, 0.5) * picA }} />
          <Pic src="dog-shiba.jpg" w={880} h={660} style={{ position: "absolute", opacity: 1 - picA }} />
          {picA > 0.5 ? (
            <div style={{ position: "absolute", left: 18, top: 18, padding: 10, borderRadius: 30, background: "rgba(15,10,7,.75)",
              opacity: fadeIn(t, L("sc02-02"), 0.3) }}><Sparkle size={34} color={GOLD} /></div>
          ) : null}
        </div>
      </div>
      <div style={{ position: "absolute", left: 1010, top: 170, width: 840, opacity: 1 - q }}>
        {chatA > 0 ? (
          <div style={{ position: "absolute", top: 0, display: "flex", flexDirection: "column", gap: 34, width: 840, opacity: chatA }}>
            <Bubble who="me" t={t} at={L("sc02-03")} en="I baked this loaf this morning. How long should it cool before I slice it?"
              zh="这是我早上烤的面包，放凉多久再切？" />
            <Bubble who="LLaVA" t={t} at={L("sc02-04")} tone="bad"
              en={<>“…a small, round loaf of bread… let it cool for <b>at least an hour</b> before slicing…”</>}
              zh="「……一个小圆面包……至少放凉一小时再切……」" />
          </div>
        ) : null}
        {chatB > 0 ? (
          <div style={{ position: "absolute", top: 0, display: "flex", flexDirection: "column", gap: 34, width: 840, opacity: chatB }}>
            <Bubble who="me" t={t} at={L("sc02-05")} en="What kind of bread is this?" zh="这是什么面包？" />
            <Bubble who="Astra" t={t} at={L("sc02-06")} tone="bad"
              en={<>“That’s a perfectly toasted <span style={hl(fadeIn(t, L("sc02-07"), 0.4))}>Shiba inu</span> cinnamon roll, curled up in a fluffy bread basket.”</>}
              zh="「一个烤得刚刚好的柴犬肉桂卷，蜷在毛茸茸的面包篮里。」" />
          </div>
        ) : null}
      </div>
      {q > 0 ? (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 40, fontFamily: SANS, opacity: q }}>
          <div style={{ fontSize: 150, fontWeight: 800, color: GOLD, textShadow: SHADOW, transform: `scale(${pop(t, qStart)})` }}>?</div>
          <div style={{ display: "flex", gap: 40 }}>
            {[["Fooled?", "被骗了？"], ["Playing along?", "在陪我玩？"]].map(([en, zh], i) => (
              <div key={en} style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "22px 44px", borderRadius: 30,
                background: "rgba(20,15,11,.9)", boxShadow: `inset 0 0 0 3px ${GOLD}88`, opacity: fadeIn(t, qStart + 0.5 + 0.6 * i, 0.3) }}>
                <span style={{ fontSize: 58, fontWeight: 800, color: INK }}>{en}</span>
                <span style={{ fontSize: 34, color: SOFT, marginTop: 4 }}>{zh}</span>
              </div>
            ))}
          </div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};

const NoiseTrick: FC<{ t: number; L: (id: string) => number; E: (id: string) => number; at: number }> = ({ t, L, E, at }) => {
  const S = 470, y = 220;
  const xs = [125, 725, 1325];
  const s1 = L("sc03-01"), s2 = L("sc03-02"), d2 = E("sc03-02") - s2;
  const glyph = (txt: string, x: number, a: number) => (
    <div style={{ position: "absolute", left: x, top: y + S / 2 - 60, width: 130, textAlign: "center", fontFamily: SANS, fontSize: 100,
      fontWeight: 300, color: SOFT, opacity: fadeIn(t, a, 0.3) }}>{txt}</div>
  );
  return (
    <AbsoluteFill>
      <Heading t={t} at={at} n={3} />
      <div style={{ position: "absolute", left: xs[0], top: y, opacity: fadeIn(t, at + 0.2, 0.5) }}><Pic src="noise-clean.png" w={S} h={S} /></div>
      {glyph("+", xs[0] + S, s1 + 0.5)}
      <div style={{ position: "absolute", left: xs[1], top: y, opacity: fadeIn(t, s1 + 0.6, 0.4) }}>
        <Pic src="noise-x25.png" w={S} h={S} />
        <div style={{ position: "absolute", right: 14, bottom: 14, padding: "6px 14px", borderRadius: 20, background: "rgba(15,10,7,.8)",
          fontFamily: SANS, fontSize: 26, color: INK }}>×25</div>
      </div>
      {glyph("=", xs[1] + S, s1 + 1.4)}
      <div style={{ position: "absolute", left: xs[2], top: y, opacity: fadeIn(t, s1 + 1.5, 0.4) }}><Pic src="noise-attacked.png" w={S} h={S} /></div>
      <div style={{ position: "absolute", left: xs[0], top: y + S + 40, width: S, display: "flex", justifyContent: "center" }}>
        <Chip name="ResNet" year="2015" said="dog" label="dingo" ok t={t} at={s2 + 0.3} />
      </div>
      {/* after "On the right" / 「看右边」 in both tracks (Whisper word times on the mixes: 0.72–0.74 of the slot) */}
      <div style={{ position: "absolute", left: xs[2] - 60, top: y + S + 40, width: S + 120, display: "flex", justifyContent: "center" }}>
        <Chip name="ResNet" year="2015" said="bread" label="French loaf 100%" ok={false} t={t} at={s2 + d2 * 0.74} />
      </div>
    </AbsoluteFill>
  );
};

const NoteTrick: FC<{ t: number; L: (id: string) => number; at: number }> = ({ t, L, at }) => (
  <AbsoluteFill>
    <Heading t={t} at={at} n={4} />
    <div style={{ position: "absolute", left: 90, top: 180, opacity: fadeIn(t, at + 0.2, 0.5) }}>
      <Pic src="note-bread.jpg" w={1040} h={780} />
    </div>
    <div style={{ position: "absolute", left: 1200, top: 470 }}>
      <Chip name="CLIP" year="2021" said="bread" label="99.5%" ok={false} big t={t} at={L("sc04-02") + 0.5} />
    </div>
  </AbsoluteFill>
);

// why it is hard now: patches + attention, ear/eye/tail together, then the data, then the cake
const COLS = 8, ROWS = 6;
const FOCUS = [2, 4];                       // the face
const PARTS: [number, number][] = [[1, 4], [2, 4], [2, 3]];  // ear, eye/face, tail (img02, 8×6 grid)
const WhyNow: FC<{ t: number; L: (id: string) => number; E: (id: string) => number; end: number }> = ({ t, L, E, end }) => {
  const s1 = L("sc05-01"), s2 = L("sc05-02"), s3 = L("sc05-03"), s4 = L("sc05-04"), s5 = L("sc05-05"), s6 = L("sc05-06");
  const PW = 1280, PH = 720, px = (1920 - PW) / 2, py = 200;
  const cw = PW / COLS, ch = PH / ROWS;
  const split = interpolate(t, [s3, s3 + 0.8], [0, 1], { ...clamp, easing: ease });
  const gap = 10 * split;
  const lines = interpolate(t, [s3 + 1.0, s3 + 2.6], [0, 1], clamp) * (1 - fadeIn(t, s4, 0.4));
  const parts = fadeIn(t, s4 + 0.2, 0.4);
  const photo = 1 - fadeIn(t, s5 - 0.3, 0.5);
  const wall = span(t, s5, s6);
  const cake = fadeIn(t, s6 - 0.3, 0.5);
  const centre = (r: number, c: number) => [c * cw + cw / 2, r * ch + ch / 2];
  const [fx, fy] = centre(FOCUS[0], FOCUS[1]);
  return (
    <AbsoluteFill>
      {photo > 0 ? (
        <AbsoluteFill style={{ opacity: photo }}>
          <div style={{ position: "absolute", left: px, top: py, width: PW, height: PH }}>
            {split < 0.01 ? (
              <Pic src="dog-shiba.jpg" w={PW} h={PH} />
            ) : (
              Array.from({ length: COLS * ROWS }, (_, i) => {
                const r = Math.floor(i / COLS), c = i % COLS;
                const lit = PARTS.some(([pr, pc]) => pr === r && pc === c);
                return (
                  <div key={i} style={{ position: "absolute", left: c * cw + (c - COLS / 2 + 0.5) * gap, top: r * ch + (r - ROWS / 2 + 0.5) * gap,
                    width: cw, height: ch, overflow: "hidden", borderRadius: 4 * split,
                    boxShadow: lit && parts > 0 ? `0 0 0 ${5 * parts}px ${GOLD}` : r === FOCUS[0] && c === FOCUS[1] && lines > 0 ? `0 0 0 4px ${GOLD}` : "none",
                    filter: parts > 0 && !lit ? `brightness(${1 - 0.55 * parts})` : "none" }}>
                    <Img src={file("dog-shiba.jpg")} style={{ position: "absolute", left: -c * cw, top: -r * ch, width: PW, height: PH, objectFit: "cover" }} />
                  </div>
                );
              })
            )}
            {/* attention: the face patch looks at every other patch; then ear, eye and tail are tied together */}
            <svg width={PW} height={PH} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
              {lines > 0 ? Array.from({ length: COLS * ROWS }, (_, i) => {
                const r = Math.floor(i / COLS), c = i % COLS;
                if (r === FOCUS[0] && c === FOCUS[1]) return null;
                const [x, y] = centre(r, c);
                const k = Math.min(1, Math.max(0, lines * 1.6 - (i / (COLS * ROWS)) * 0.6));
                return <line key={i} x1={fx} y1={fy} x2={fx + (x - fx) * k} y2={fy + (y - fy) * k} stroke={GOLD} strokeWidth={2} strokeOpacity={0.55} />;
              }) : null}
              {parts > 0 ? PARTS.map(([r, c], i) => {
                const [a, b] = centre(r, c), [x2, y2] = centre(...PARTS[(i + 1) % PARTS.length]);
                return <line key={i} x1={a} y1={b} x2={a + (x2 - a) * parts} y2={b + (y2 - b) * parts} stroke={GOLD} strokeWidth={5} />;
              }) : null}
            </svg>
          </div>
          <div style={{ position: "absolute", left: px, top: py, width: PW, height: PH, display: "flex", alignItems: "center",
            justifyContent: "center", fontFamily: SANS, fontSize: 200, fontWeight: 800, color: GOLD, textShadow: SHADOW,
            opacity: fadeIn(t, s1 + 0.2, 0.3) * (1 - fadeIn(t, s2, 0.3)) }}>?</div>
          <div style={{ position: "absolute", right: 70, top: 60 }}>
            <PaperCard t={t} at={s2 + 0.3} title="Attention Is All You Need" who="Vaswani et al. · 2017 · the Transformer" zh="注意力 · Transformer"
              style={{ width: 640, opacity: fadeIn(t, s2 + 0.3, 0.35) * (1 - fadeIn(t, s3 - 0.2, 0.4)) }} />
          </div>
          <div style={{ position: "absolute", left: 0, right: 0, bottom: 50, display: "flex", justifyContent: "center", opacity: parts }}>
            <Chip name="ViT" said="dog" label="dog" ok t={t} at={s4 + (E("sc05-04") - s4) * 0.75} big />
          </div>
        </AbsoluteFill>
      ) : null}
      {wall > 0 ? (
        <AbsoluteFill style={{ opacity: wall, background: "#000", alignItems: "center", justifyContent: "center" }}>
          <Img src={file("data-wall.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover",
            transform: `scale(${interpolate(t, [s5, s6], [3.2, 1.0], { ...clamp, easing: ease })})` }} />
          <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(10,7,5,.75) 0%, rgba(10,7,5,.3) 70%)" }} />
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SANS, textShadow: SHADOW,
            opacity: fadeIn(t, s5 + 1.6, 0.4) }}>
            <div style={{ fontSize: 120, fontWeight: 800, color: INK }}>400,000,000</div>
            <div style={{ fontSize: 46, color: INK, marginTop: 6 }}>pictures with captions</div>
            <div style={{ fontSize: 34, color: SOFT, marginTop: 6 }}>4 亿张配了文字的图片 · CLIP, 2021</div>
          </AbsoluteFill>
        </AbsoluteFill>
      ) : null}
      {cake > 0 ? (
        <AbsoluteFill style={{ opacity: cake }}>
          <Img src={file("cake-dog-16x9.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover",
            transform: `scale(${interpolate(t, [s6, end], [1.0, 1.08], clamp)})` }} />
          <div style={{ position: "absolute", left: 0, right: 0, bottom: 40, display: "flex", justifyContent: "center" }}>
            <Pill t={t} at={E("sc05-06") - 0.6} color={CAKE} icon={<Cake size={60} color={CAKE} />} en="Cake" zh="蛋糕" />
          </div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};

const CREDITS: [string, string][] = [
  ["Photos (Pexels)", "Stephen · Ruxanda Scutelnic · Oliver King · Travel with Lenses · Andreas Schnabl · Nadin Sh · Nataliya Vaitkevich · Gu Ko · Sena · Ellie Burgin · and the photographers of the look-alike grids"],
  ["AI pictures and video", "Codex (OpenAI image generation): the cake Shiba, the puppy on the baking tray · the cut: Muse"],
  ["Research", "Yao, TOPBOTS 2017 · Geirhos et al., ICLR 2019 (cat-with-elephant-skin image CC BY 4.0) · Vaswani et al., NIPS 2017 · Dosovitskiy et al., ICLR 2021 · Geirhos et al., NeurIPS 2021 · Radford et al., ICML 2021"],
  ["Tested 2026-11-16", "AlexNet · ResNet-50 · CLIP ViT-B/32 · LLaVA 1.6 7B · Claude Fable 5.2 · GPT-6-Astra — one fresh chat per question, no context, no web; Fable and Astra were asked once more on every trick that fooled them"],
];

const Credits: FC<{ t: number; at: number; music?: string }> = ({ t, at, music }) => (
  <AbsoluteFill style={{ background: BG, alignItems: "center", justifyContent: "center", fontFamily: SANS, opacity: fadeIn(t, at, 0.6) }}>
    <div style={{ width: 1500, display: "flex", flexDirection: "column", gap: 30 }}>
      {[...CREDITS, ...(music ? ([["Music", music]] as [string, string][]) : [])].map(([k, v]) => (
        <div key={k}>
          <div style={{ fontSize: 26, color: GOLD, fontWeight: 700, letterSpacing: 1 }}>{k}</div>
          <div style={{ fontSize: 28, color: INK, lineHeight: 1.4, marginTop: 6 }}>{v}</div>
        </div>
      ))}
    </div>
  </AbsoluteFill>
);

const Section: FC<{ t: number; span: [number, number]; children: ReactNode }> = ({ t, span: sp, children }) => {
  const [a, b] = sp;
  if (t < a - 0.01 || t > b + 0.01) return null;
  return <AbsoluteFill style={{ opacity: Math.min(fadeIn(t, a, 0.35), fadeOut(t, b, 0.3)) }}>{children}</AbsoluteFill>;
};

export const BreadOrDogVideo: FC<BdProps> = ({ tl }) => {
  const t = useT();
  if (!tl) return <AbsoluteFill style={{ background: BG }} />;
  const L = (id: string) => tl.lines[id].start;
  const E = (id: string) => tl.lines[id].end;
  const sec = tl.sections;
  return (
    <AbsoluteFill style={{ background: BG }}>
      {t < tl.title[1] + 0.01 ? <Title t={t} end={tl.title[1]} /> : null}
      <Section t={t} span={sec.sc00}><History t={t} L={L} end={sec.sc00[1]} /></Section>
      <Section t={t} span={sec.sc01}><CakeTrick t={t} L={L} E={E} at={sec.sc01[0]} muse={tl.muse} /></Section>
      <Section t={t} span={sec.sc02}><TrapTrick t={t} L={L} at={sec.sc02[0]} /></Section>
      <Section t={t} span={sec.sc03}><NoiseTrick t={t} L={L} E={E} at={sec.sc03[0]} /></Section>
      <Section t={t} span={sec.sc04}><NoteTrick t={t} L={L} at={sec.sc04[0]} /></Section>
      <Section t={t} span={sec.sc05}><WhyNow t={t} L={L} E={E} end={sec.sc05[1]} /></Section>
      {t >= tl.credits[0] ? <Credits t={t} at={tl.credits[0]} music={tl.music} /> : null}
    </AbsoluteFill>
  );
};
