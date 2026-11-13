/**
 * 「Challenge: Which Butterflies Are Real?」（猜一猜哪些蝴蝶是真的？和AI比一比）· docs/butterfly-challenge/.
 *
 * One picture for both tracks: English is the default audio, Chinese a separate track (Yancy, 2026-11-12:
 * 「默认语言英文，配中文音轨」). Yancy, same day: 「视频少用文字，用icon 如果一定要用文字，英文大，中文小一些。不用署名了」 and
 * 「就用绿勾和红叉来表示真假，尽量不用文字」 — so real is a big green ✓, AI a big red ✗, a model's pick is its robot and name
 * under the picture it chose, the score is robots and numbers, the end has a trophy; the few words left are English large
 * with Chinese small under them, and there is no byline. Captions are separate SRTs, never burned in.
 *
 * Timed by scripts/butterfly-challenge/build_timeline.py (public/butterfly-challenge/timeline.json, one slot per line,
 * the longer of the English and Chinese takes): title over a mosaic of all twenty test pictures → intro → for each
 * pair: the two pictures exactly as both models saw them (pairs/NN-A.jpg, NN-B.jpg), a 5-4-3-2-1 count, the reveal
 * (green ✓ and the photo credit on the real one, red ✗ on the AI one, each model's pick under the picture it chose,
 * each model's tally out of ten), then the real video with its name → final score and the AI pictures that fooled both
 * models (red ✗) → credits.
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

const DIR = "butterfly-challenge";
const file = (p: string) => staticFile(`${DIR}/${p}`);

type Pair = {
  n: number; real: "A" | "B"; ai: string; astra: "A" | "B"; fable: "A" | "B"; astraOk: boolean; fableOk: boolean;
  score: [number, number]; photo: string; key: string; name: { zh: string; en: string; latin: string };
  clipCredit: string; start: number; reveal: number; clip: number; end: number;
  video: { src: string; from: number; rate: number; hold: number | null; last: string; still?: string | null };
  video2?: { src: string; from: number; at: number; credit: string };  // pair 6: closed wings, then the open-winged male
};
export type BcTimeline = {
  fps: number; durationSeconds: number; title: [number, number]; pairs: Pair[];
  ending?: { start: number; blur: number; you?: number; end: number; pictures: string[] }; credits?: [number, number];
  lines: Record<string, { start: number; end: number }>;
};
export type BcProps = { tl?: BcTimeline | null };

export const calculateBcMetadata: CalculateMetadataFunction<BcProps> = async ({ props, abortSignal }) => {
  const r = await fetch(file("timeline.json"), { signal: abortSignal });
  if (!r.ok) throw Error("Run scripts/butterfly-challenge/assets.py and build_timeline.py first");
  const tl = (await r.json()) as BcTimeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

// ---- look ----
const BG = "#0d1012";
const INK = "#f4efe6";
const SOFT = "#c9c3b8";
const MUTED = "#8a918f";
const REAL = "#3ecf7a";
const WRONG = "#ef5b4f";
const GOLD = "#e9c46a";
const SANS = "'Helvetica Neue', 'PingFang SC', sans-serif";
const SHADOW = "0 3px 18px rgba(0,0,0,.7), 0 1px 3px rgba(0,0,0,.8)";
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = Easing.bezier(0.3, 0.7, 0.2, 1);
const fadeIn = (t: number, at: number, d = 0.4) => interpolate(t, [at, at + d], [0, 1], { ...clamp, easing: ease });
const fadeOut = (t: number, at: number, d = 0.5) => interpolate(t, [at - d, at], [1, 0], clamp);

const useT = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return f / fps;
};

// ---- icons (drawn here, 24-unit grid) ----
const Svg: FC<{ size: number; color: string; children: ReactNode; style?: CSSProperties }> = ({ size, color, children, style }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2.2} strokeLinecap="round"
    strokeLinejoin="round" style={{ display: "block", flex: "none", ...style }}>{children}</svg>
);
const Bot: FC<{ size: number; color: string }> = (p) => (
  <Svg {...p}><rect x="4" y="8" width="16" height="11" rx="3" /><path d="M12 8V4.5" /><circle cx="12" cy="3.6" r="1.1" />
    <circle cx="9" cy="13.2" r="1.2" fill={p.color} /><circle cx="15" cy="13.2" r="1.2" fill={p.color} /><path d="M2 12.5v3M22 12.5v3" /></Svg>
);
const Check: FC<{ size: number; color: string }> = (p) => <Svg {...p}><path d="M4.5 12.5l4.6 4.5L19.5 6.5" /></Svg>;
const Cross: FC<{ size: number; color: string }> = (p) => <Svg {...p}><path d="M6 6l12 12M18 6L6 18" /></Svg>;
const Person: FC<{ size: number; color: string }> = (p) => (
  <Svg {...p}><circle cx="12" cy="8" r="4" /><path d="M4 20.5c.8-4.2 4-6.5 8-6.5s7.2 2.3 8 6.5" /></Svg>
);
const Trophy: FC<{ size: number; color: string }> = (p) => (
  <Svg {...p}><path d="M7 4h10v5a5 5 0 0 1-10 0z" /><path d="M7 6H4.5a2.5 2.5 0 0 0 2.6 4M17 6h2.5a2.5 2.5 0 0 1-2.6 4" />
    <path d="M12 14v3.5M8.5 20h7M9.5 17.5h5" /></Svg>
);
// ---- pieces ----
const Mosaic: FC<{ t: number; dur: number }> = ({ t, dur }) => {
  const tiles = Array.from({ length: 20 }, (_, i) => `pairs/${String(Math.floor(i / 2) + 1).padStart(2, "0")}-${"AB"[i % 2]}.jpg`);
  // a fixed shuffle so A and B of a pair never sit side by side
  const order = [3, 14, 7, 18, 0, 11, 5, 16, 9, 2, 13, 6, 19, 10, 1, 12, 4, 17, 8, 15];
  const s = interpolate(t, [0, dur], [1.08, 1.0], clamp);
  return (
    <AbsoluteFill style={{ transform: `scale(${s})` }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gridTemplateRows: "repeat(4, 1fr)", width: "100%", height: "100%", gap: 6 }}>
        {order.map((k, i) => (
          <Img key={i} src={file(tiles[k])} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ))}
      </div>
    </AbsoluteFill>
  );
};

// the title's words leave after TITLE_WORDS s; the intro then plays over the mosaic alone (less text on screen)
const TITLE_WORDS = 5.5;
const Title: FC<{ t: number; end: number }> = ({ t, end }) => {
  const dim = interpolate(t, [0, 1.2, TITLE_WORDS, TITLE_WORDS + 1.2], [0.25, 0.62, 0.62, 0.3], clamp);
  return (
    <AbsoluteFill style={{ opacity: fadeOut(t, end, 0.6) }}>
      <Mosaic t={t} dur={end} />
      <AbsoluteFill style={{ background: `rgba(8,10,11,${dim})` }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SANS, color: INK, textShadow: SHADOW,
        opacity: fadeOut(t, TITLE_WORDS + 0.8, 0.8) }}>
        <div style={{ fontSize: 42, letterSpacing: 12, color: GOLD, fontWeight: 700, opacity: fadeIn(t, 0.3, 0.6) }}>CHALLENGE</div>
        <div style={{ fontSize: 122, fontWeight: 800, marginTop: 14, letterSpacing: -1, opacity: fadeIn(t, 0.5, 0.7) }}>Which Butterflies Are Real?</div>
        <div style={{ fontSize: 50, fontWeight: 500, marginTop: 10, color: SOFT, opacity: fadeIn(t, 0.7, 0.7) }}>猜一猜哪些蝴蝶是真的？</div>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 44, opacity: fadeIn(t, 1.1, 0.7),
          padding: "12px 30px", borderRadius: 40, background: "rgba(10,12,13,.55)", boxShadow: `inset 0 0 0 2px ${GOLD}` }}>
          <Bot size={46} color={GOLD} />
          <span style={{ fontSize: 46, fontWeight: 700 }}>Play against AI</span>
          <span style={{ fontSize: 32, color: SOFT }}>和AI比一比</span>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// each model's own tally out of ten (Yancy 2026-11-12: 「比分这么显示 Astra 1/10 Fable 2/10」); a tally that just went up pulses
const Tally: FC<{ who: string; n: number; flash: number }> = ({ who, n, flash }) => (
  <span style={{ display: "flex", alignItems: "center", gap: 12 }}>
    <Bot size={38} color={SOFT} />
    <span style={{ color: SOFT, fontWeight: 600 }}>{who}</span>
    <span style={{ display: "inline-block", fontSize: 46, fontWeight: 800, transform: `scale(${1 + 0.3 * flash})`,
      color: flash > 0.05 ? GOLD : INK }}>{n}</span>
    <span style={{ color: MUTED, fontSize: 30, marginLeft: -6 }}>/10</span>
  </span>
);
const Scoreboard: FC<{ a: number; f: number; opacity: number; flashA?: number; flashF?: number }> = ({ a, f, opacity, flashA = 0, flashF = 0 }) => (
  <div style={{ position: "absolute", top: 40, right: 56, opacity, fontFamily: SANS, color: INK, display: "flex", alignItems: "center", gap: 34,
    fontSize: 34, background: "rgba(10,12,13,.72)", padding: "10px 28px", borderRadius: 40, textShadow: SHADOW }}>
    <Tally who="Astra" n={a} flash={flashA} />
    <Tally who="Fable" n={f} flash={flashF} />
  </div>
);

// a model's pick, under the picture it chose; whether it was right shows from that picture's ✓ or ✗ (Yancy 2026-11-12:
// 「就用绿勾和红叉来表示真假，尽量不用文字」, so ✓/✗ only ever means real/AI)
const Chip: FC<{ who: string; style?: CSSProperties }> = ({ who, style }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 24px 8px 16px", borderRadius: 32, fontSize: 36, fontWeight: 700,
    whiteSpace: "nowrap", background: "rgba(255,255,255,.08)", border: "2px solid rgba(255,255,255,.55)", color: INK, ...style }}>
    <Bot size={38} color={INK} />
    <span>{who}</span>
  </div>
);

// real = green ✓, AI = red ✗, no words
const Mark: FC<{ real: boolean; size: number; pop: number }> = ({ real, size, pop }) => (
  <div style={{ width: size, height: size, borderRadius: size / 2, background: real ? REAL : WRONG, display: "flex",
    alignItems: "center", justifyContent: "center", boxShadow: "0 6px 24px rgba(0,0,0,.55)", opacity: Math.min(1, pop * 1.5),
    transform: `scale(${interpolate(pop, [0, 0.7, 1], [0.4, 1.12, 1])})` }}>
    {real ? <Check size={size * 0.62} color="#ffffff" /> : <Cross size={size * 0.56} color="#ffffff" />}
  </div>
);

const W = 860, H = 484, GAPX = 60, TOPY = 230, COUNT = 5;  // 5-4-3-2-1, then the reveal (Yancy 2026-11-12)
const PairCard: FC<{ p: Pair; t: number; prevScore: [number, number] }> = ({ p, t, prevScore }) => {
  const local = t - p.start;
  const revealed = t >= p.reveal;
  const r = fadeIn(t, p.reveal, 0.45);
  const count = Math.max(1, Math.min(COUNT, COUNT - Math.floor(t - (p.start + 0.4))));
  const inCount = t >= p.start + 0.4 && t < p.reveal;
  const tick = (t - (p.start + 0.4)) % 1;
  const score = revealed ? p.score : prevScore;
  const flash = revealed ? interpolate(t - p.reveal, [0.3, 0.55, 0.9], [0, 1, 0], clamp) : 0;
  const x0 = (1920 - 2 * W - GAPX) / 2;
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: SANS, color: INK, opacity: fadeIn(local, 0, 0.4) }}>
      <div style={{ position: "absolute", top: 44, left: 64, fontSize: 46, fontWeight: 800 }}>
        {p.n}<span style={{ color: MUTED, fontWeight: 400, fontSize: 32 }}> / 10</span>
      </div>
      <Scoreboard a={score[0]} f={score[1]} opacity={1} flashA={p.astraOk ? flash : 0} flashF={p.fableOk ? flash : 0} />
      {(["A", "B"] as const).map((side, i) => {
        const real = p.real === side;
        const x = x0 + i * (W + GAPX);
        const ring = revealed ? (real ? REAL : WRONG) : "rgba(255,255,255,.12)";
        const picks = [p.astra === side ? "Astra" : null, p.fable === side ? "Fable" : null].filter(Boolean) as string[];
        return (
          <div key={side}>
            <div style={{ position: "absolute", left: x, top: TOPY, width: W, height: H, borderRadius: 14, overflow: "hidden",
              boxShadow: revealed ? `0 0 0 ${4 + 4 * r}px ${ring}` : `0 0 0 2px ${ring}`,
              filter: revealed && !real ? `saturate(${1 - 0.15 * r}) brightness(${1 - 0.12 * r})` : undefined }}>
              <Img src={file(`pairs/${String(p.n).padStart(2, "0")}-${side}.jpg`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </div>
            {revealed && (
              <div style={{ position: "absolute", left: x + W - 150, top: TOPY + 22 }}><Mark real={real} size={128} pop={fadeIn(t, p.reveal, 0.4)} /></div>
            )}
            {revealed && real && (
              <div style={{ position: "absolute", left: x, top: TOPY + H + 14, width: W, textAlign: "right", fontSize: 21, color: MUTED, opacity: r }}>{p.photo}</div>
            )}
            {revealed && (
              <div style={{ position: "absolute", left: x, top: TOPY + H + 60, width: W, display: "flex", justifyContent: "center", gap: 22 }}>
                {picks.map((who, k) => (
                  <Chip key={who} who={who} style={{ opacity: fadeIn(t, p.reveal + 0.25 + 0.2 * k, 0.4),
                    transform: `translateY(${(1 - fadeIn(t, p.reveal + 0.25 + 0.2 * k, 0.4)) * 16}px)` }} />
                ))}
              </div>
            )}
          </div>
        );
      })}
      {inCount && (
        <div style={{ position: "absolute", left: 960 - 70, top: TOPY + H + 70, width: 140, height: 140, borderRadius: 70,
          display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(255,255,255,.06)",
          boxShadow: `inset 0 0 0 4px rgba(233,196,106,${0.9 - 0.6 * tick})`, fontSize: 84, fontWeight: 800, color: GOLD,
          transform: `scale(${1 + 0.12 * (1 - Math.min(1, tick * 4))})` }}>{count}</div>
      )}
    </AbsoluteFill>
  );
};

const Clip: FC<{ p: Pair; t: number; fps: number; next: number }> = ({ p, t, fps, next }) => {
  const local = t - p.clip;
  const hold = p.video.hold;
  const holding = hold !== null && local >= hold;
  const push = holding ? interpolate(local - hold!, [0, next - p.clip - hold!], [1.0, 1.08], clamp) : 1;
  const card = fadeIn(local, 0.6, 0.5);
  const v2 = p.video2;
  const second = v2 ? fadeIn(local, v2.at - 0.2, 0.4) : 0;
  return (
    <AbsoluteFill style={{ background: "#000", opacity: fadeIn(local, 0, 0.5) }}>
      {!holding && (
        <Sequence from={Math.round(p.clip * fps)} layout="none">
          <OffthreadVideo src={file(p.video.src)} muted playbackRate={p.video.rate} startFrom={Math.round(p.video.from * fps)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </Sequence>
      )}
      {holding && !p.video.still && <Img src={file(p.video.last)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${push})` }} />}
      {holding && p.video.still && (
        <>
          <Img src={file(p.video.last)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          <Img src={file(p.video.still)} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover",
            opacity: fadeIn(local - hold!, 0, 0.7), transform: `scale(${push})` }} />
        </>
      )}
      {v2 && local >= v2.at - 0.2 && (
        <AbsoluteFill style={{ opacity: second }}>
          <Sequence from={Math.round((p.clip + v2.at - 0.2) * fps)} layout="none">
            <OffthreadVideo src={file(v2.src)} muted startFrom={Math.round(v2.from * fps)}
              style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          </Sequence>
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ background: "linear-gradient(to top, rgba(0,0,0,.55), rgba(0,0,0,0) 34%)" }} />
      <div style={{ position: "absolute", left: 72, bottom: 66, fontFamily: SANS, color: INK, textShadow: SHADOW, opacity: card,
        transform: `translateY(${(1 - card) * 18}px)` }}>
        <div style={{ fontSize: 78, fontWeight: 800 }}>{p.name.en}</div>
        <div style={{ fontSize: 40, marginTop: 4, color: SOFT, fontWeight: 500 }}>{p.name.zh}</div>
      </div>
      <Scoreboard a={p.score[0]} f={p.score[1]} opacity={card} />
      {p.clipCredit && (
        <div style={{ position: "absolute", right: 56, bottom: 40, fontFamily: SANS, fontSize: 21, color: SOFT, textShadow: SHADOW, opacity: card }}>{p.clipCredit}</div>
      )}
      {v2 && (
        <div style={{ position: "absolute", right: 56, bottom: 40, fontFamily: SANS, fontSize: 21, color: SOFT, textShadow: SHADOW, opacity: second }}>{v2.credit}</div>
      )}
    </AbsoluteFill>
  );
};

const Ending: FC<{ e: NonNullable<BcTimeline["ending"]>; t: number; score: [number, number] }> = ({ e, t, score }) => {
  // the score moves up for the pictures, then back down when the viewer's own tally joins (sc11-03, 「你猜对了几个？」)
  const you = e.you ?? Infinity;
  // pictures leave first (over the half second before the question), then the score settles back down
  const up = interpolate(t, [e.blur - 0.2, e.blur + 0.6, you - 0.05, you + 0.65], [0, 1, 1, 0], { ...clamp, easing: ease });
  const pics = Math.min(interpolate(t, [e.blur - 0.2, e.blur + 0.6], [0, 1], { ...clamp, easing: ease }), fadeOut(t, you - 0.05, 0.5));
  const showYou = fadeIn(t, you, 0.6);
  const tallies: [string, string, boolean][] = [["Astra", String(score[0]), false], ["Fable", String(score[1]), false],
    ...(t >= you ? [["You", "?", true] as [string, string, boolean]] : [])];
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: SANS, color: INK, opacity: fadeIn(t - e.start, 0, 0.6) * fadeOut(t, e.end, 0.8) }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: interpolate(up, [0, 1], [270, 60]), display: "flex", flexDirection: "column",
        alignItems: "center", transform: `scale(${1 - 0.4 * up})` }}>
        <Trophy size={120} color={GOLD} />
        <div style={{ display: "flex", justifyContent: "center", alignItems: "flex-end", gap: 150, marginTop: 20 }}>
          {tallies.map(([who, n, isYou]) => (
            <div key={who} style={{ display: "flex", flexDirection: "column", alignItems: "center",
              opacity: isYou ? showYou : 1, transform: isYou ? `scale(${0.85 + 0.15 * showYou})` : undefined }}>
              <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                {isYou ? <Person size={70} color={INK} /> : <Bot size={70} color={SOFT} />}
                <span style={{ fontSize: 64, color: isYou ? INK : SOFT, fontWeight: 700 }}>{who}</span>
              </div>
              <div style={{ display: "flex", alignItems: "baseline" }}>
                <span style={{ fontSize: 200, fontWeight: 800, color: isYou ? REAL : GOLD, lineHeight: 1.05 }}>{n}</span>
                <span style={{ fontSize: 90, color: MUTED, fontWeight: 600 }}>/10</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 440, display: "flex", justifyContent: "center", gap: 36, opacity: pics }}>
        {e.pictures.map((src, i) => (
          <div key={src} style={{ opacity: fadeIn(t, e.blur + 0.3 * i, 0.5), position: "relative" }}>
            <div style={{ width: 560, height: 315, borderRadius: 12, overflow: "hidden", boxShadow: `0 0 0 5px ${WRONG}` }}>
              <Img src={file(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </div>
            <div style={{ position: "absolute", right: 16, top: 16 }}><Mark real={false} size={84} pop={fadeIn(t, e.blur + 0.3 * i + 0.2, 0.4)} /></div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// English large, Chinese small (Yancy, 2026-11-12); no byline. CC BY sources are credited here as well as on screen.
const CREDITS: [string, string][] = [
  ["Real photos: iNaturalist · Jason Eckberg, Francisco Farriols Sarabia, Robert Taylor, Cheongweei Gan, Michael Knapp, Robert Harris, Carlos Alexandre Mattos Raposo, Kai Squires (CC BY); two more CC0",
    "真实照片：iNaturalist（八张 CC BY，两张 CC0）"],
  ["Videos: Brandon (Flickr: bpprice), CC BY 2.0, and NaIzletuSi, CC BY 3.0, Wikimedia Commons · Pexels: Nithin PA, R Bude, Adolph Haben, Nicky Pe, Анатолий, Chris F, Hao Le, Matheus Bertelli, Joolsmagools",
    "视频：Wikimedia Commons、Pexels"],
  ["AI butterflies: Codex (OpenAI image generation) · real, common species in invented scenes, not copied from any photo",
    "AI 蝴蝶：Codex 图像生成，画的是真实的常见蝴蝶，场景是编的"],
  ["The test, Nov 12, 2026: GPT-6-Astra (Codex CLI) and Claude Fable 5.2 (Claude Code), a new chat for every pair, no context, no internet · the AI pictures in pairs 3, 4, 5, 7 and 8 were redrawn after earlier answers and asked again; the film shows the last answer",
    "测试：每一组都是新的对话，没有上下文、不能联网；第 3、4、5、7、8 组的 AI 图看过之前的回答以后重画过，又问了一次，片子里是最后一次的回答"],
  ["Music: Chopin, Grande valse brillante, Op. 18, played by Olga Gurevich (Musopen, CC0) · The narrator uses Louise’s licensed voice",
    "音乐：肖邦《降E大调华丽大圆舞曲》Op. 18，Olga Gurevich 演奏 · 旁白使用 Louise 的授权声线"],
];
const Credits: FC<{ t: number; at: [number, number] }> = ({ t, at }) => (
  <AbsoluteFill style={{ background: BG, fontFamily: SANS, opacity: fadeIn(t - at[0], 0, 0.8) * fadeOut(t, at[1], 1.2),
    alignItems: "center", justifyContent: "center", textAlign: "center", padding: "0 140px" }}>
    <div style={{ fontSize: 60, fontWeight: 800, color: INK }}>Which Butterflies Are Real?</div>
    <div style={{ fontSize: 32, color: SOFT, marginTop: 6 }}>猜一猜哪些蝴蝶是真的？</div>
    <div style={{ marginTop: 50, display: "flex", flexDirection: "column", gap: 22 }}>
      {CREDITS.map(([en, zh]) => (
        <div key={en}>
          <div style={{ fontSize: 26, lineHeight: 1.4, color: SOFT }}>{en}</div>
          <div style={{ fontSize: 19, lineHeight: 1.4, color: MUTED, marginTop: 2 }}>{zh}</div>
        </div>
      ))}
    </div>
  </AbsoluteFill>
);

export const ButterflyChallengeVideo: FC<BcProps> = ({ tl }) => {
  const t = useT();
  const { fps } = useVideoConfig();
  if (!tl) return <AbsoluteFill style={{ background: BG }} />;
  const pairs = tl.pairs;
  // every layer whose window holds t, later ones on top, so each cut is a short cross-fade
  return (
    <AbsoluteFill style={{ background: BG }}>
      {t < tl.title[1] + 0.6 && <Title t={t} end={tl.title[1] + 0.6} />}
      {pairs.map((p, i) => (
        <AbsoluteFill key={p.n}>
          {t >= p.start && t < p.clip + 0.5 && <PairCard p={p} t={t} prevScore={i > 0 ? pairs[i - 1].score : [0, 0]} />}
          {t >= p.clip && t < p.end + 0.5 && <Clip p={p} t={t} fps={fps} next={p.end + 0.5} />}
        </AbsoluteFill>
      ))}
      {tl.ending && t >= tl.ending.start && t < tl.ending.end && <Ending e={tl.ending} t={t} score={pairs[pairs.length - 1].score} />}
      {tl.credits && t >= tl.credits[0] && <Credits t={t} at={tl.credits} />}
    </AbsoluteFill>
  );
};
