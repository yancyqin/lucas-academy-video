// 「报数为什么说『幺』？」 / "Why Do Pilots Say 'Bravo'?" (FUN-INFORMATICS-03.md §5).
// One sheet of warm paper: marker-doodle pictures (Codex, labelled AI), hand-lettered words, a moving
// static that eats whatever noise touches, and the family's own Pictionary footage in NS02.
import { useLayoutEffect, useRef, type CSSProperties, type FC, type ReactNode } from "react";
import {
  AbsoluteFill,
  Audio,
  Freeze,
  Img,
  OffthreadVideo,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  type CalculateMetadataFunction,
} from "remotion";
import { monotoneRamp, rampAt, type RampKey } from "../../lib/timeRamps";

type Lang = "zh" | "en";
type Cue = { id: string; section: string; zh: string; en: string; start: number; end: number; speech: { start: number; end: number } };
type Ev = { name: string; cue: string; start: number; end: number; src: string; srcStart: number | null; srcEnd: number | null };
export type NoiseTimeline = {
  lang: Lang;
  fps: number;
  durationSeconds: number;
  endCardStart: number;
  leadIn: number;
  cues: Cue[];
  events: Ev[];
  footageSeconds: Record<string, number>;
  draft: boolean;
};
export type NoiseProps = { tl?: NoiseTimeline | null; lang?: Lang };

const DIR = "fun-informatics-03";
const file = (p: string) => staticFile(`${DIR}/${p}`);
const PAPER = "#f3eee5",
  INK = "#2b2926",
  MUTED = "#8a837a",
  TEAL = "#0f766e",
  ORANGE = "#c2410c",
  YELLOW = "#f2c14e",
  SKY = "#6fb7e0",
  RED = "#d64545",
  GREEN = "#2f9e5b";
const ZH = '"PingFang SC", "Hiragino Sans GB", sans-serif';
const EN = '"Avenir Next", "Helvetica Neue", sans-serif';
const HAND = '"Marker Felt", "Chalkboard SE", "PingFang SC", sans-serif';
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = (x: number) => {
  const t = Math.max(0, Math.min(1, x));
  return t * t * (3 - 2 * t);
};
/** 0 → 1 between a and b, eased. */
const rise = (t: number, a: number, b: number) => ease((t - a) / Math.max(0.001, b - a));

export const calculateNoiseMetadata: CalculateMetadataFunction<NoiseProps> = async ({ props, abortSignal }) => {
  const response = await fetch(file(`timeline.${props.lang ?? "zh"}.json`), { signal: abortSignal });
  if (!response.ok) throw Error("Run fi03:timeline first");
  const tl = (await response.json()) as NoiseTimeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

/** Everything a scene needs: film time, the language, its cues and events. */
type Ctx = { t: number; lang: Lang; tl: NoiseTimeline; cue: (id: string) => Cue; ev: (name: string) => Ev | undefined };
/** A moment inside a cue's speech, as a fraction of it. */
const at = (c: Cue, f: number) => c.speech.start + f * (c.speech.end - c.speech.start);

// ---------------------------------------------------------------- building blocks

/** The moving static: grey snow, seeded by the frame so every render matches. */
const Static: FC<{ opacity: number; style?: CSSProperties; seed?: number }> = ({ opacity, style, seed = 0 }) => {
  const frame = useCurrentFrame();
  const ref = useRef<HTMLCanvasElement>(null);
  useLayoutEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const g = canvas.getContext("2d")!;
    const { width, height } = canvas;
    const img = g.createImageData(width, height);
    let s = (frame * 7919 + seed * 104729) >>> 0 || 1;
    for (let i = 0; i < width * height; i++) {
      s ^= s << 13;
      s ^= s >>> 17;
      s ^= s << 5;
      const v = (s >>> 0) % 256;
      img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = v * 0.55 + 70;
      img.data[i * 4 + 3] = 255;
    }
    g.putImageData(img, 0, 0);
  }, [frame, seed]);
  if (opacity <= 0.001) return null;
  return (
    <canvas
      ref={ref}
      width={240}
      height={136}
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%", opacity, imageRendering: "pixelated", ...style }}
    />
  );
};

const Paper: FC<{ children?: ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 40%, #f8f4ec 0%, ${PAPER} 60%, #e9e2d6 100%)` }}>{children}</AbsoluteFill>
);

const AiTag: FC<{ lang: Lang }> = ({ lang }) => (
  <div style={{ position: "absolute", right: 34, bottom: 26, fontFamily: lang === "zh" ? ZH : EN, fontSize: 22, color: MUTED, letterSpacing: 1 }}>
    {lang === "zh" ? "AI 生成" : "AI-generated"}
  </div>
);

/** A Codex picture, filling the frame, drifting slowly. */
const Picture: FC<{ name: string; t: number; from: number; to: number; lang: Lang; zoom?: [number, number]; children?: ReactNode }> = ({
  name,
  t,
  from,
  to,
  lang,
  zoom = [1.02, 1.08],
  children,
}) => {
  const k = interpolate(t, [from, to], zoom, clamp);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ transform: `scale(${k})` }}>
        <Img src={file(`images/${name}.png`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        {children}
      </AbsoluteFill>
      <AiTag lang={lang} />
    </AbsoluteFill>
  );
};

/** Hand-lettered word that pops in at `from`. */
const Pop: FC<{ t: number; from: number; children: ReactNode; style?: CSSProperties; tilt?: number }> = ({ t, from, children, style, tilt = 0 }) => {
  const p = rise(t, from, from + 0.35);
  const bounce = 1 + 0.12 * Math.sin(Math.min(1, (t - from) / 0.35) * Math.PI);
  return (
    <div style={{ opacity: p, transform: `scale(${(0.6 + 0.4 * p) * (p >= 1 ? 1 : bounce)}) rotate(${tilt}deg)`, ...style }}>{children}</div>
  );
};

/** A speech bubble with a guess in it. */
const Bubble: FC<{ t: number; from: number; text: string; right?: boolean; good?: boolean; bad?: boolean; style?: CSSProperties; lang: Lang }> = ({
  t,
  from,
  text,
  right,
  good,
  bad,
  style,
  lang,
}) => {
  if (t < from) return null;
  const border = good ? GREEN : bad ? RED : INK;
  return (
    <Pop t={t} from={from} style={{ position: "absolute", ...style }} tilt={right ? 2 : -2}>
      <div
        style={{
          position: "relative",
          background: "#fffdf8",
          border: `5px solid ${border}`,
          borderRadius: 40,
          padding: "16px 34px",
          fontFamily: lang === "zh" ? ZH : HAND,
          fontWeight: 700,
          fontSize: 52,
          color: INK,
          whiteSpace: "nowrap",
          boxShadow: "0 8px 0 rgba(0,0,0,.08)",
        }}
      >
        {text}
        {good && <span style={{ color: GREEN, marginLeft: 16 }}>✓</span>}
        {bad && <span style={{ color: RED, marginLeft: 16 }}>✗</span>}
      </div>
    </Pop>
  );
};

/** A hand-drawn ring that draws itself around something (positions in % of the parent). */
const Ring: FC<{ t: number; from: number; x: number; y: number; rx: number; ry: number; color?: string }> = ({ t, from, x, y, rx, ry, color = ORANGE }) => {
  const p = rise(t, from, from + 0.7);
  if (p <= 0) return null;
  const len = 2 * Math.PI * Math.sqrt((rx * rx + ry * ry) / 2) * 1.15;
  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", overflow: "visible" }}>
      <path
        d={`M ${x + rx} ${y} A ${rx} ${ry} 0 1 1 ${x + rx * 0.98} ${y - ry * 0.2} A ${rx * 1.05} ${ry * 1.08} 0 0 1 ${x + rx * 1.02} ${y + ry * 0.25}`}
        fill="none"
        stroke={color}
        strokeWidth={0.9}
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
        style={{ strokeWidth: 9, strokeDasharray: len, strokeDashoffset: len * (1 - p) }}
      />
    </svg>
  );
};

const Underline: FC<{ t: number; from: number; width: number; color?: string }> = ({ t, from, width, color = YELLOW }) => {
  const p = rise(t, from, from + 0.6);
  return (
    <svg width={width} height={30} style={{ display: "block", margin: "0 auto" }}>
      <path d={`M 6 18 Q ${width / 2} 6 ${width - 6} 16`} stroke={color} strokeWidth={12} strokeLinecap="round" fill="none" strokeDasharray={width * 1.1} strokeDashoffset={width * 1.1 * (1 - p)} />
    </svg>
  );
};

/** A paper card, like the printed game cards. */
const Card: FC<{ children: ReactNode; color?: string; style?: CSSProperties }> = ({ children, color = INK, style }) => (
  <div
    style={{
      background: "#fffdf8",
      border: `6px solid ${color}`,
      borderRadius: 34,
      boxShadow: "0 14px 0 rgba(0,0,0,.07), 0 30px 60px rgba(60,40,10,.12)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      ...style,
    }}
  >
    {children}
  </div>
);

const Tag: FC<{ color: string; children: ReactNode; lang: Lang; style?: CSSProperties }> = ({ color, children, lang, style }) => (
  <div style={{ background: color, color: "#fff", borderRadius: 18, padding: "10px 30px", fontSize: 40, fontWeight: 700, fontFamily: lang === "zh" ? ZH : EN, ...style }}>{children}</div>
);

/** Footage at a speed-ramped source time, as a rounded card over its own blurred copy. */
const Footage: FC<{ ctx: Ctx; name: string; keys: RampKey[]; style?: CSSProperties; background?: boolean; children?: ReactNode }> = ({
  ctx,
  name,
  keys,
  style,
  background = true,
  children,
}) => {
  const dur = ctx.tl.footageSeconds[`${name}.mp4`] ?? 1;
  const src = Math.max(0, Math.min(dur - 0.07, rampAt(keys, ctx.t)));
  return (
    <>
      {background && (
        <AbsoluteFill style={{ overflow: "hidden" }}>
          <Img src={file(`footage/${name}.jpg`)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "blur(38px) saturate(0.9) brightness(1.04)", transform: "scale(1.25)" }} />
          <AbsoluteFill style={{ background: "rgba(243,238,229,.35)" }} />
        </AbsoluteFill>
      )}
      <div style={{ position: "absolute", borderRadius: 30, overflow: "hidden", boxShadow: "0 24px 70px rgba(50,35,10,.28)", aspectRatio: "3 / 4", ...style }}>
        <Freeze frame={0}>
          <OffthreadVideo src={file(`footage/${name}.mp4`)} muted trimBefore={Math.round(src * ctx.tl.fps)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </Freeze>
        {children}
      </div>
    </>
  );
};

/** Source time of a footage clip as the ramp reaches it (for bubbles keyed to what was said). */
const source = (ctx: Ctx, name: string, keys: RampKey[]) => Math.min(ctx.tl.footageSeconds[`${name}.mp4`] ?? 1, rampAt(keys, ctx.t));

const Center: FC<{ children: ReactNode; style?: CSSProperties }> = ({ children, style }) => (
  <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", ...style }}>{children}</AbsoluteFill>
);

const Big: FC<{ children: ReactNode; size?: number; color?: string; font?: string; style?: CSSProperties }> = ({ children, size = 220, color = INK, font = HAND, style }) => (
  <div style={{ fontFamily: font, fontSize: size, color, lineHeight: 1, fontWeight: 700, ...style }}>{children}</div>
);

/** Concentric radio rings out of the walkie-talkie while an event plays. */
const Rings: FC<{ t: number; ev?: Ev }> = ({ t, ev }) => {
  if (!ev || t < ev.start - 0.1 || t > ev.end + 0.6) return null;
  return (
    <>
      {[0, 1, 2].map((k) => {
        const p = ((t - ev.start) / 0.9 + k / 3) % 1;
        return (
          <div
            key={k}
            style={{
              position: "absolute",
              left: "50%",
              top: "48%",
              width: 260 + p * 760,
              height: 260 + p * 760,
              marginLeft: -(130 + p * 380),
              marginTop: -(130 + p * 380),
              borderRadius: "50%",
              border: `8px solid ${SKY}`,
              opacity: (1 - p) * 0.7,
            }}
          />
        );
      })}
    </>
  );
};

// ---------------------------------------------------------------- scenes, one per shot

type Scene = FC<{ ctx: Ctx; c: Cue }>;

const S0001: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  if (lang === "en") {
    return (
      <Picture name="pilot-radio" t={t} from={c.start} to={c.end} lang={lang} zoom={[1.0, 1.06]}>
        <Bubble t={t} from={at(c, 0.55)} text="B … ?" lang={lang} style={{ left: "36%", top: "16%" }} />
      </Picture>
    );
  }
  const q = 1 - rise(t, at(c, 0.6), at(c, 0.8));
  const keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"];
  const lit = (k: number) => [at(c, 0.75), at(c, 0.85), at(c, 0.95)][k];
  return (
    <Paper>
      <Center style={{ right: 560 }}>
        <div style={{ position: "relative" }}>
          <Big size={420} style={{ opacity: q, position: "absolute", left: "50%", transform: "translateX(-50%)" }}>?</Big>
          <Pop t={t} from={at(c, 0.7)}>
            <Big size={330}>110</Big>
          </Pop>
        </div>
      </Center>
      <div style={{ position: "absolute", right: 210, top: 210, display: "grid", gridTemplateColumns: "repeat(3, 120px)", gap: 22 }}>
        {keys.map((k, i) => {
          const order = k === "1" ? (t > lit(1) ? 1 : t > lit(0) ? 0 : -1) : k === "0" ? (t > lit(2) ? 2 : -1) : -1;
          const on = order >= 0;
          return (
            <div key={k} style={{ height: 120, borderRadius: 60, border: `5px solid ${on ? TEAL : "#cfc6b8"}`, background: on ? "#d9f0ea" : "#fffdf8", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: HAND, fontSize: 56, color: on ? TEAL : MUTED }}>
              {k}
            </div>
          );
        })}
      </div>
    </Paper>
  );
};

const Flip: FC<{ t: number; from: number; a: string; b: string; size: number; color?: string; font?: string }> = ({ t, from, a, b, size, color = ORANGE, font = HAND }) => {
  const p = rise(t, from, from + 0.5);
  const angle = p * 180;
  const front = angle < 90;
  return (
    <div style={{ perspective: 900, width: size * 1.05, textAlign: "center" }}>
      <div style={{ transform: `rotateX(${front ? angle : angle - 180}deg)` }}>
        <Big size={size} color={front ? INK : color} font={front ? HAND : font}>
          {front ? a : b}
        </Big>
      </div>
    </div>
  );
};

const S0002: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  if (lang === "en") {
    const rows: [string, string, number][] = [["B", "Bravo", 0.2], ["D", "Delta", 0.55], ["T", "Tango", 0.8]];
    return (
      <Paper>
        <Center>
          {rows.map(([a, b, f]) => (
            <div key={a} style={{ display: "flex", alignItems: "center", gap: 50, height: 230 }}>
              <Big size={170} style={{ width: 160, textAlign: "center" }}>{a}</Big>
              <Big size={110} color={MUTED} style={{ opacity: rise(t, at(c, f), at(c, f) + 0.3) }}>→</Big>
              <Pop t={t} from={at(c, f) + 0.15}>
                <Big size={150} color={ORANGE} style={{ width: 520 }}>{b}</Big>
              </Pop>
            </div>
          ))}
        </Center>
      </Paper>
    );
  }
  const row1 = at(c, 0.58),
    row2 = at(c, 0.86);
  const digits = (d: string[], from: number, words: string[]) => (
    <div style={{ display: "flex", gap: 40, justifyContent: "center" }}>
      {d.map((x, i) => (words[i] === x ? <Big key={i} size={200} style={{ width: 210, textAlign: "center" }}>{x}</Big> : <Flip key={i} t={t} from={from + i * 0.12} a={x} b={words[i]} size={200} font={ZH} />))}
    </div>
  );
  return (
    <Paper>
      <Center style={{ gap: 60 }}>
        {digits(["1", "1", "0"], row1, ["幺", "幺", "零"])}
        <div style={{ opacity: rise(t, row2 - 0.4, row2) }}>{digits(["1", "2", "0"], row2, ["幺", "二", "零"])}</div>
      </Center>
    </Paper>
  );
};

const S0003: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  if (lang === "en") {
    return (
      <Paper>
        <Center style={{ flexDirection: "row", gap: 70 }}>
          <Big size={300}>9</Big>
          <Big size={130} color={MUTED} style={{ opacity: rise(t, at(c, 0.45), at(c, 0.6)) }}>→</Big>
          <Pop t={t} from={at(c, 0.6)}>
            <Big size={210} color={ORANGE}>
              nine<span style={{ color: TEAL }}>r</span>
            </Big>
          </Pop>
        </Center>
      </Paper>
    );
  }
  return (
    <Picture name="pilot-radio" t={t} from={c.start} to={c.end} lang={lang}>
      <Bubble t={t} from={at(c, 0.55)} text="7 → 拐" lang={lang} style={{ left: "34%", top: "12%" }} />
      <Bubble t={t} from={at(c, 0.82)} text="0 → 洞" right lang={lang} style={{ left: "52%", top: "30%" }} />
    </Picture>
  );
};

const Title: FC<{ lang: Lang; t: number; from: number; small?: boolean }> = ({ lang, t, from }) => (
  <Center style={{ opacity: rise(t, from, from + 0.6) }}>
    <div style={{ textAlign: "center" }}>
      <div style={{ fontFamily: lang === "zh" ? ZH : EN, fontWeight: 800, fontSize: lang === "zh" ? 132 : 110, color: INK }}>
        {lang === "zh" ? (
          <>
            报数为什么说「<span style={{ color: ORANGE }}>幺</span>」？
          </>
        ) : (
          <>
            Why Do Pilots Say “<span style={{ color: ORANGE }}>Bravo</span>”?
          </>
        )}
      </div>
      <Underline t={t} from={from + 0.4} width={lang === "zh" ? 900 : 1100} />
      <div style={{ fontFamily: EN, fontSize: 40, color: TEAL, marginTop: 26, fontWeight: 600 }}>{lang === "zh" ? "趣味信息学3 · Fun Informatics 3" : "Fun Informatics 3"}</div>
      <div style={{ fontFamily: lang === "zh" ? ZH : EN, fontSize: 32, color: MUTED, marginTop: 40 }}>
        {lang === "zh" ? "作者 Yancy Qin, Louise Yang | Lucas Academy" : "By Yancy Qin, Louise Yang | Lucas Academy"}
      </div>
    </div>
  </Center>
);

const S0004: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  const pair = lang === "zh" ? ["一", "七"] : ["B", "9"];
  const noise = rise(t, at(c, 0.55), at(c, 1)) * (1 - rise(t, c.speech.end + 0.3, c.speech.end + 1.1));
  const title = c.speech.end + 0.4;
  return (
    <Paper>
      <Center style={{ flexDirection: "row", gap: 260, opacity: 1 - rise(t, title - 0.3, title) }}>
        {pair.map((x) => (
          <Big key={x} size={300} font={lang === "zh" ? ZH : HAND}>
            {x}
          </Big>
        ))}
      </Center>
      <Static opacity={noise * 0.85} />
      <Title lang={lang} t={t} from={title} />
    </Paper>
  );
};

const S0101: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  const split = at(c, lang === "zh" ? 0.42 : 0.45);
  const second = rise(t, split - 0.25, split + 0.25);
  return (
    <AbsoluteFill>
      <Picture name="noisy-classroom" t={t} from={c.start} to={split + 0.3} lang={lang} />
      <AbsoluteFill style={{ opacity: second }}>
        <Picture name="crackly-phone" t={t} from={split} to={c.end} lang={lang} />
      </AbsoluteFill>
      <Static opacity={0.1 + 0.08 * Math.sin(t * 9)} style={{ mixBlendMode: "multiply" }} />
    </AbsoluteFill>
  );
};

const Radio: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  const ev = ctx.ev(c.id === "ns01-02" ? "radio-test1" : "radio-test2");
  const playing = ev && t >= ev.start && t <= ev.end;
  return (
    <AbsoluteFill>
      <Picture name="walkie-talkie" t={t} from={c.start} to={c.end} lang={lang} zoom={[1.0, 1.05]} />
      <Rings t={t} ev={ev} />
      <Static opacity={playing ? 0.28 : 0} style={{ mixBlendMode: "multiply" }} />
      {ev && c.id === "ns01-02" && <Bubble t={t} from={ev.end + 0.2} text="？" lang={lang} style={{ right: "22%", top: "16%" }} />}
    </AbsoluteFill>
  );
};

const S0103: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  const opts = lang === "zh" ? ["一", "七"] : ["B", "D", "E"];
  return (
    <Paper>
      <Center style={{ flexDirection: "row", gap: 90 }}>
        {opts.map((x, i) => (
          <Pop key={x} t={t} from={at(c, 0.05 + i * 0.12)} tilt={Math.sin(t * 2.4 + i * 1.7) * 6}>
            <Card style={{ width: 340, height: 420 }}>
              <Big size={260} font={lang === "zh" ? ZH : HAND}>{x}</Big>
            </Card>
          </Pop>
        ))}
      </Center>
    </Paper>
  );
};

const S0104: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  const glow = rise(t, at(c, 0.28), at(c, 0.4));
  const cover = rise(t, at(c, 0.68), at(c, 0.8));
  const units: [string, string][] = lang === "zh" ? [["y", "ī"], ["q", "ī"]] : [["B", "ee"], ["D", "ee"], ["E", "ee"], ["P", "ee"], ["T", "ee"], ["V", "ee"]];
  const zh = lang === "zh";
  return (
    <Paper>
      <Center style={{ flexDirection: "row", gap: zh ? 160 : 40 }}>
        {units.map(([head, tail], i) => (
          <div key={i} style={{ textAlign: "center" }}>
            <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "center" }}>
              <div style={{ position: "relative" }}>
                <Big size={zh ? 260 : 150} font={EN}>{head}</Big>
                <div style={{ position: "absolute", inset: -10, overflow: "hidden", borderRadius: 16, opacity: cover }}>
                  <Static opacity={1} seed={i + 1} />
                </div>
              </div>
              <Big size={zh ? 260 : 0} font={EN} color={glow > 0.5 ? TEAL : INK} style={{ marginLeft: zh ? 28 : 0 }}>{zh ? tail : ""}</Big>
            </div>
            {!zh && (
              <div style={{ fontFamily: EN, fontSize: 64, fontWeight: 700, color: glow > 0.5 ? TEAL : MUTED, marginTop: 10 }}>{tail}</div>
            )}
            {zh && <div style={{ fontFamily: ZH, fontSize: 70, color: MUTED, marginTop: 20 }}>{i === 0 ? "一" : "七"}</div>}
          </div>
        ))}
      </Center>
    </Paper>
  );
};

const S0105: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  if (lang === "zh") {
    const sign: CSSProperties = { position: "absolute", width: "8.6%", height: "15.5%", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: HAND, fontSize: 110, color: INK };
    return (
      <Picture name="buildings-wrong-door" t={t} from={c.start} to={c.end} lang={lang} zoom={[1.0, 1.04]}>
        <div style={{ ...sign, left: "34.4%", top: "13.4%", opacity: rise(t, at(c, 0.15), at(c, 0.3)) }}>1</div>
        <div style={{ ...sign, left: "69.1%", top: "13.4%", opacity: rise(t, at(c, 0.05), at(c, 0.2)) }}>7</div>
        <Bubble t={t} from={at(c, 0.55)} text="？" lang={lang} style={{ left: "6%", top: "48%" }} />
      </Picture>
    );
  }
  const sign: CSSProperties = { position: "absolute", width: "7.6%", height: "6.4%", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: EN, fontWeight: 800, fontSize: 60, color: INK };
  return (
    <Picture name="taxiway-fork" t={t} from={c.start} to={c.end} lang={lang} zoom={[1.0, 1.04]}>
      <div style={{ ...sign, left: "32.6%", top: "31.8%", opacity: rise(t, at(c, 0.1), at(c, 0.25)) }}>B</div>
      <div style={{ ...sign, left: "65.2%", top: "31.8%", opacity: rise(t, at(c, 0.05), at(c, 0.2)) }}>D</div>
    </Picture>
  );
};

const S0107: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  const zh = lang === "zh";
  const stampEnd = at(c, zh ? 0.22 : 0.18);
  const pair = zh ? ["幺", "拐"] : ["Bravo", "Delta"];
  const sweep = rise(t, at(c, 0.6), at(c, 0.95));
  return (
    <Paper>
      <Center style={{ opacity: 1 - rise(t, stampEnd, stampEnd + 0.3) }}>
        <Pop t={t} from={c.start + 0.1} tilt={-6}>
          <Big size={zh ? 330 : 240} color={ORANGE} font={zh ? ZH : HAND}>{zh ? "拐！" : "Bravo!"}</Big>
        </Pop>
      </Center>
      <Center style={{ flexDirection: "row", gap: 110, opacity: rise(t, stampEnd, stampEnd + 0.3) }}>
        {pair.map((x, i) => (
          <Card key={x} color={i === 0 ? TEAL : ORANGE} style={{ width: zh ? 420 : 640, height: 460, position: "relative", overflow: "hidden" }}>
            <Big size={zh ? 280 : 170} font={zh ? ZH : HAND}>{x}</Big>
            <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${sweep * 30}%`, overflow: "hidden" }}>
              <Static opacity={0.92} seed={i + 4} />
            </div>
          </Card>
        ))}
      </Center>
    </Paper>
  );
};

const S0108: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  if (lang === "en") {
    return (
      <Paper>
        <Center style={{ gap: 30 }}>
          <Big size={260} color={INK}>
            nine<span style={{ color: TEAL, background: "#d9f0ea", borderRadius: 30, padding: "0 16px" }}>r</span>
          </Big>
          <div style={{ fontFamily: EN, fontSize: 48, color: MUTED, opacity: rise(t, at(c, 0.4), at(c, 0.55)) }}>one extra sound, easier to hear</div>
        </Center>
      </Paper>
    );
  }
  const a = at(c, 0.36),
    b = at(c, 0.66);
  const show = (from: number, to: number) => rise(t, from - 0.2, from + 0.2) * (1 - rise(t, to - 0.2, to + 0.2));
  const label: CSSProperties = { position: "absolute", left: 0, right: 0, bottom: 70, textAlign: "center", fontFamily: ZH, fontWeight: 800, fontSize: 110, color: ORANGE };
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ opacity: show(c.start - 1, a) }}>
        <Picture name="dice-one" t={t} from={c.start} to={a} lang={lang} />
        <div style={label}>幺</div>
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: show(a, b) }}>
        <Picture name="cane-seven" t={t} from={a} to={b} lang={lang} />
        <Center style={{ opacity: rise(t, a + 0.4, a + 0.9) * 0.35 }}>
          <Big size={760} color={SKY} style={{ transform: "translateX(-20px)" }}>7</Big>
        </Center>
        <div style={label}>拐</div>
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: show(b, c.end + 2) }}>
        <Picture name="hole-zero" t={t} from={b} to={c.end} lang={lang} />
        <Center style={{ opacity: rise(t, b + 0.4, b + 0.9) * 0.35 }}>
          <Big size={600} color={SKY}>0</Big>
        </Center>
        <div style={label}>洞</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const KeyLine: FC<{ t: number; from: number; lang: Lang; zh: string; en: string }> = ({ t, from, lang, zh, en }) => (
  <Paper>
    <Center>
      <Pop t={t} from={from}>
        <div style={{ fontFamily: lang === "zh" ? ZH : EN, fontWeight: 800, fontSize: lang === "zh" ? 104 : 86, color: INK, textAlign: "center", maxWidth: 1500, lineHeight: 1.25 }}>
          {lang === "zh" ? zh : en}
        </div>
      </Pop>
      <Underline t={t} from={from + 0.5} width={lang === "zh" ? 1100 : 1300} />
    </Center>
  </Paper>
);

const S0109: Scene = ({ ctx, c }) => <KeyLine t={ctx.t} from={at(c, 0.25)} lang={ctx.lang} zh="把容易听混的，说得不一样。" en="If two things sound alike, say them differently." />;

const POSTERS = ["r1-lucas", "r1-cachew", "r2-umbrella", "r2-moon", "r2-star"];
const S0201: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  return (
    <Paper>
      {POSTERS.map((p, i) => {
        const x = [12, 31, 50, 69, 88][i],
          tilt = [-7, 4, -3, 6, -5][i],
          y = [52, 44, 55, 45, 53][i];
        return (
          <Pop key={p} t={t} from={c.start + 0.2 + i * 0.35} tilt={tilt} style={{ position: "absolute", left: `${x}%`, top: `${y}%`, marginLeft: -170, marginTop: -230 }}>
            <Img src={file(`footage/${p}.jpg`)} style={{ width: 360, height: 480, objectFit: "cover", borderRadius: 18, border: "10px solid #fffdf8", boxShadow: "0 18px 40px rgba(50,35,10,.22)", filter: "contrast(1.15)" }} />
          </Pop>
        );
      })}
      <div style={{ position: "absolute", top: 70, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
        <Tag color={INK} lang={lang} style={{ fontSize: 50 }}>{lang === "zh" ? "你画我猜" : "Pictionary"}</Tag>
      </div>
    </Paper>
  );
};

/** Guesses keyed to the clip's own time; the last one is the right answer. */
type Guess = { src: number; zh: string; en: string; good?: boolean; bad?: boolean };
const GuessBubbles: FC<{ ctx: Ctx; now: number; guesses: Guess[] }> = ({ ctx, now, guesses }) => (
  <>
    {guesses.map((g, i) => {
      const left = i % 2 === 0;
      const row = Math.floor(i / 2);
      return (
        <Bubble
          key={i}
          t={now}
          from={g.src}
          text={ctx.lang === "zh" ? g.zh : g.en}
          good={g.good}
          bad={g.bad}
          right={!left}
          lang={ctx.lang}
          style={left ? { left: 90 + (row % 2) * 40, top: 150 + row * 160 } : { right: 90 + (row % 2) * 40, top: 230 + row * 160 }}
        />
      );
    })}
  </>
);

/** Round 1 with one drawing: the clip runs fast until the family's own voices, then in real time. */
const RoundOne: FC<{ ctx: Ctx; c: Cue; name: string; ev: string; srcFrom: number; guesses: Guess[]; tag?: boolean }> = ({ ctx, c, name, ev, srcFrom, guesses, tag }) => {
  const e = ctx.ev(ev)!;
  const keys = monotoneRamp([
    [c.start, srcFrom],
    [e.start, e.srcStart!],
    [e.end, e.srcEnd!],
    [c.end + 0.6, e.srcEnd! + 0.8],
  ]);
  const now = rampAt(keys, ctx.t);
  return (
    <AbsoluteFill>
      <Footage ctx={ctx} name={name} keys={keys} style={{ left: 660, top: 90, width: 600 }} />
      <GuessBubbles ctx={ctx} now={now} guesses={guesses} />
      {tag && (
        <div style={{ position: "absolute", left: 0, right: 0, top: 30, display: "flex", justifyContent: "center", opacity: 1 - rise(ctx.t, ctx.cue("ns02-03").start, ctx.cue("ns02-03").start + 0.6) }}>
          <Tag color={TEAL} lang={ctx.lang}>{ctx.lang === "zh" ? "第一轮 · 自由画" : "Round 1 · Free draw"}</Tag>
        </div>
      )}
    </AbsoluteFill>
  );
};

const LUCAS: Guess[] = [
  { src: 3.5, zh: "鸡蛋？", en: "Egg?", bad: true },
  { src: 8.2, zh: "头晕的人？", en: "Dizzy guy?", bad: true },
  { src: 10.1, zh: "外星人？", en: "Alien?", bad: true },
  { src: 13.7, zh: "疯狂的人？", en: "Crazy guy?", bad: true },
  { src: 18.7, zh: "小宝宝？", en: "Baby?", bad: true },
  { src: 26.4, zh: "Lucas！", en: "Lucas!", good: true },
];
const CACHEW: Guess[] = [
  { src: 10.6, zh: "三角形？", en: "Triangle?", bad: true },
  { src: 14.9, zh: "羊？", en: "Sheep?", bad: true },
  { src: 16.1, zh: "野蛮的羊？", en: "Barbarian sheep?", bad: true },
  { src: 17.1, zh: "一只狗？", en: "A dog?" },
  { src: 19.3, zh: "Cashew！", en: "Cashew!", good: true },
];

/** ns02-02 and ns02-03 share one shot: the round's tag, then Lucas being drawn and guessed. */
const S0202: Scene = ({ ctx }) => {
  const c2 = ctx.cue("ns02-02"),
    c3 = ctx.cue("ns02-03");
  return <RoundOne ctx={ctx} c={{ ...c3, start: c2.start }} name="r1-lucas" ev="lucas" srcFrom={0.5} guesses={LUCAS} tag />;
};

const Still: FC<{ name: string; style?: CSSProperties; children?: ReactNode }> = ({ name, style, children }) => (
  <div style={{ position: "absolute", borderRadius: 30, overflow: "hidden", boxShadow: "0 24px 70px rgba(50,35,10,.28)", aspectRatio: "3 / 4", ...style }}>
    <Img src={file(`footage/${name}.jpg`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    {children}
  </div>
);

const S0204: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  return (
    <Paper>
      <Still name="r1-lucas" style={{ left: 200, top: 90, width: 600 }}>
        <Ring t={t} from={at(c, 0.25)} x={51} y={49} rx={22} ry={14} />
      </Still>
      <div style={{ position: "absolute", left: 930, top: 300, width: 900 }}>
        <Pop t={t} from={at(c, 0.3)}>
          <div style={{ fontFamily: lang === "zh" ? ZH : EN, fontSize: lang === "zh" ? 70 : 62, fontWeight: 800, color: INK, lineHeight: 1.5, whiteSpace: "nowrap" }}>
            {lang === "zh" ? "圆圆的脸 + 两只眼睛" : "a round face + two eyes"}
          </div>
        </Pop>
        <Pop t={t} from={at(c, 0.7)}>
          <div style={{ fontFamily: lang === "zh" ? ZH : EN, fontSize: 70, fontWeight: 800, color: ORANGE, marginTop: 30 }}>{lang === "zh" ? "= 谁都像" : "= almost anyone"}</div>
        </Pop>
      </div>
    </Paper>
  );
};

const S0205: Scene = ({ ctx, c }) => <RoundOne ctx={ctx} c={c} name="r1-cachew" ev="cachew" srcFrom={4} guesses={CACHEW} />;

const TwinCard: FC<{ lang: Lang; t: number; from: number; pick?: number }> = ({ lang, t, from, pick }) => {
  const zh = lang === "zh";
  const words = zh ? ["雨伞", "蘑菇"] : ["umbrella", "mushroom"];
  return (
    <Pop t={t} from={from}>
      <Card color={ORANGE} style={{ width: 1100, height: 520, flexDirection: "column", justifyContent: "flex-start" }}>
        <div style={{ alignSelf: "stretch", margin: 22 }}>
          <Tag color={ORANGE} lang={lang} style={{ textAlign: "center" }}>{zh ? "第二轮 · 双胞胎" : "Round 2 · Twins"}</Tag>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 60, marginTop: 40 }}>
          {words.map((w, i) => (
            <div key={w} style={{ textAlign: "center", width: 400, opacity: pick === undefined || pick === i ? 1 : 0.3 }}>
              <div style={{ fontFamily: zh ? ZH : EN, fontWeight: 800, fontSize: zh ? 150 : 76, color: INK }}>{w}</div>
              <div style={{ display: "inline-block", marginTop: 18, border: `4px solid ${ORANGE}`, color: ORANGE, borderRadius: 40, padding: "4px 26px", fontFamily: zh ? ZH : EN, fontSize: 34, fontWeight: 700 }}>
                {i === 0 ? (zh ? "正面" : "HEADS") : zh ? "反面" : "TAILS"}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </Pop>
  );
};

const Coin: FC<{ t: number; from: number; lang: Lang }> = ({ t, from, lang }) => {
  const p = rise(t, from, from + 1.4);
  const spins = p * 6 * Math.PI + Math.PI * 0; // lands heads up
  const y = -Math.sin(p * Math.PI) * 170;
  const face = Math.cos(spins) >= 0;
  return (
    <div style={{ position: "absolute", left: "50%", top: 850, marginLeft: -90, transform: `translateY(${y}px) scaleY(${Math.abs(Math.cos(spins)) * 0.9 + 0.1})` }}>
      <div style={{ width: 180, height: 180, borderRadius: "50%", background: face ? YELLOW : "#d9a93a", border: "8px solid #b8862a", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: lang === "zh" ? ZH : EN, fontSize: 52, fontWeight: 800, color: "#7a5410" }}>
        {face ? (lang === "zh" ? "正" : "H") : lang === "zh" ? "反" : "T"}
      </div>
    </div>
  );
};

const S0206: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  const flip = at(c, 0.75);
  return (
    <Paper>
      <Center style={{ top: -170 }}>
        <TwinCard lang={lang} t={t} from={at(c, 0.05)} pick={t > flip + 1.5 ? 0 : undefined} />
      </Center>
      {t > flip - 0.1 && <Coin t={t} from={flip} lang={lang} />}
    </Paper>
  );
};

const TWINS = ["r2-umbrella", "r2-moon", "r2-star"];
const S0207: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  const timer = rise(t, at(c, 0.1), c.end - 0.2);
  return (
    <Paper>
      {TWINS.map((n, i) => {
        const dur = ctx.tl.footageSeconds[`${n}.mp4`] ?? 10;
        const keys = monotoneRamp([[c.start, 0.5], [c.end, dur - 0.2]]);
        return <Footage key={n} ctx={ctx} name={n} keys={keys} background={false} style={{ left: 90 + i * 590, top: 110, width: 560 }} />;
      })}
      <div style={{ position: "absolute", left: 520, right: 240, bottom: 70, height: 26, borderRadius: 13, background: "#e2d9cb", overflow: "hidden" }}>
        <div style={{ width: `${(1 - timer) * 100}%`, height: "100%", background: ORANGE }} />
      </div>
      <div style={{ position: "absolute", right: 110, bottom: 52, fontFamily: HAND, fontSize: 56, color: ORANGE }}>{Math.max(0, Math.ceil(15 * (1 - timer)))}s</div>
      <div style={{ position: "absolute", left: 110, bottom: 52, fontFamily: lang === "zh" ? ZH : EN, fontSize: 40, fontWeight: 700, color: INK }}>{lang === "zh" ? "只能猜一次" : "one guess"}</div>
    </Paper>
  );
};

const S0208: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  const e = ctx.ev("moon")!;
  const keys = monotoneRamp([[c.start, 3], [e.start, e.srcStart!], [e.end, e.srcEnd!], [c.end + 0.6, e.srcEnd! + 0.6]]);
  const now = rampAt(keys, t);
  const rock = Math.sin(t * 3.2) * 8;
  const before = t < e.start;
  return (
    <AbsoluteFill>
      <Footage ctx={ctx} name="r2-moon" keys={keys} style={{ left: 660, top: 90, width: 600 }} />
      {before && (
        <>
          <Bubble t={t} from={at(c, 0.4)} text={lang === "zh" ? "香蕉？" : "Banana?"} lang={lang} style={{ left: 170, top: 330, transform: `rotate(${rock}deg)` }} />
          <Bubble t={t} from={at(c, 0.5)} text={lang === "zh" ? "月亮？" : "Moon?"} right lang={lang} style={{ right: 200, top: 330, transform: `rotate(${-rock}deg)` }} />
          <div style={{ position: "absolute", left: 0, right: 0, bottom: 60, textAlign: "center", fontFamily: HAND, fontSize: 90, color: ORANGE, opacity: rise(t, at(c, 0.75), at(c, 0.85)) }}>50 / 50</div>
        </>
      )}
      {!before && (
        <GuessBubbles
          ctx={ctx}
          now={now}
          guesses={[
            { src: 8.8, zh: "香蕉？", en: "Banana?" },
            { src: 10.7, zh: "月亮！", en: "Moon!", good: true },
          ]}
        />
      )}
    </AbsoluteFill>
  );
};

const S0209: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  const e = ctx.ev("star")!;
  const mid = at(c, lang === "zh" ? 0.36 : 0.38);
  const uKeys = monotoneRamp([[c.start, 1], [mid, 9.6], [c.end + 1, 10.1]]);
  const sKeys = monotoneRamp([[c.start, 0.5], [e.start, e.srcStart!], [e.end, e.srcEnd!], [c.end + 0.6, e.srcEnd! + 0.6]]);
  const focusStar = rise(t, mid - 0.2, mid + 0.4);
  const sNow = rampAt(sKeys, t),
    uNow = rampAt(uKeys, t);
  return (
    <Paper>
      <div style={{ opacity: 1 - 0.55 * focusStar }}>
        <Footage ctx={ctx} name="r2-umbrella" keys={uKeys} background={false} style={{ left: 260, top: 100, width: 560 }}>
          <Ring t={t} from={at(c, 0.18)} x={51.5} y={66} rx={8} ry={14} />
        </Footage>
        <Bubble t={uNow} from={7.1} text={lang === "zh" ? "雨伞！" : "Umbrella!"} good lang={lang} style={{ left: 120, top: 760 }} />
      </div>
      <div style={{ opacity: 0.45 + 0.55 * focusStar }}>
        <Footage ctx={ctx} name="r2-star" keys={sKeys} background={false} style={{ left: 1100, top: 100, width: 560 }}>
          <Ring t={t} from={at(c, 0.7)} x={42} y={40} rx={18} ry={13} />
        </Footage>
        <Bubble t={sNow} from={8.8} text={lang === "zh" ? "海星？" : "Starfish?"} right lang={lang} style={{ right: 60, top: 130 }} />
        <Bubble t={sNow} from={17.3} text={lang === "zh" ? "哦，是星星！" : "Oh, it's a star!"} good right lang={lang} style={{ right: 40, top: 760 }} />
      </div>
    </Paper>
  );
};

const S0210: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  return (
    <Paper>
      <Still name="r2-umbrella" style={{ left: 330, top: 80, width: 520 }}>
        <Ring t={t} from={c.start + 0.2} x={51.5} y={66} rx={8} ry={14} />
      </Still>
      <Still name="r2-star" style={{ left: 1070, top: 80, width: 520 }}>
        <Ring t={t} from={c.start + 0.5} x={42} y={40} rx={18} ry={13} />
      </Still>
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 70, textAlign: "center" }}>
        <Pop t={t} from={at(c, 0.15)}>
          <span style={{ fontFamily: lang === "zh" ? ZH : EN, fontSize: 72, fontWeight: 800, color: INK }}>
            {lang === "zh" ? "多出来的几笔 = " : "the extra strokes = "}
            <span style={{ color: ORANGE }}>{lang === "zh" ? "冗余" : "redundancy"}</span>
          </span>
        </Pop>
      </div>
    </Paper>
  );
};

const S0301: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  return (
    <Paper>
      <Center style={{ flexDirection: "row", gap: 120, top: -60 }}>
        <Pop t={t} from={at(c, 0.1)}>
          <Card color={TEAL} style={{ width: 460, height: 560 }}>
            <Big size={lang === "zh" ? 300 : 150} font={lang === "zh" ? ZH : HAND} color={TEAL}>{lang === "zh" ? "幺" : "Bravo"}</Big>
          </Card>
        </Pop>
        <Pop t={t} from={at(c, 0.25)}>
          <div style={{ width: 420, height: 560, borderRadius: 34, overflow: "hidden", border: `6px solid ${ORANGE}`, boxShadow: "0 30px 60px rgba(60,40,10,.12)" }}>
            <Img src={file("footage/r2-star.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          </div>
        </Pop>
      </Center>
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 90, textAlign: "center", fontFamily: lang === "zh" ? ZH : EN, fontSize: 66, fontWeight: 800, color: INK, opacity: rise(t, at(c, 0.7), at(c, 0.85)) }}>
        {lang === "zh" ? "把容易混的，变得不一样" : "make look-alikes different"}
      </div>
    </Paper>
  );
};

const S0302: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  const p = rise(t, at(c, 0.35), at(c, 0.95));
  const word = lang === "zh" ? "幺幺零" : "BRAVO";
  return (
    <Paper>
      <div style={{ position: "absolute", top: 110, left: 0, right: 0, textAlign: "center" }}>
        <Pop t={t} from={c.start + 0.1}>
          <div style={{ fontFamily: lang === "zh" ? ZH : EN, fontSize: 76, fontWeight: 800, color: INK }}>{lang === "zh" ? "克劳德·香农" : "Claude Shannon"}</div>
          <div style={{ fontFamily: EN, fontSize: 40, color: MUTED, marginTop: 8 }}>1948</div>
        </Pop>
      </div>
      <div style={{ position: "absolute", left: 260, right: 260, top: 600, height: 10, background: "#d8cfc1", borderRadius: 5 }} />
      <div style={{ position: "absolute", left: 760, width: 400, top: 470, height: 270, borderRadius: 30, overflow: "hidden" }}>
        <Static opacity={0.75} />
      </div>
      <div style={{ position: "absolute", top: 548, left: 260 + p * 1100, transform: "translateX(-50%)" }}>
        <Card color={TEAL} style={{ padding: "8px 30px" }}>
          <span style={{ fontFamily: lang === "zh" ? ZH : HAND, fontSize: 70, fontWeight: 800, color: TEAL }}>{word}</span>
        </Card>
      </div>
      {p >= 1 && <div style={{ position: "absolute", right: 150, top: 520, fontSize: 90, color: GREEN }}>✓</div>}
    </Paper>
  );
};

const S0303: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  const zh = lang === "zh";
  const before = zh ? ["1", "1", "0"] : ["B", "R", "A", "V", "O"];
  const after = zh ? ["1", "7", "0"] : ["B", "R", "A", "V", "E"];
  const k = zh ? 1 : 4;
  const swap = at(c, 0.45);
  const flicker = t > swap - 0.25 && t < swap + 0.15;
  return (
    <Paper>
      <Center style={{ flexDirection: "row", gap: 36 }}>
        {before.map((x, i) => (
          <Card key={i} style={{ width: 200, height: 260, position: "relative", overflow: "hidden" }}>
            <Big size={170}>{i === k && t > swap ? after[i] : x}</Big>
            {i === k && flicker && <Static opacity={0.9} seed={9} />}
          </Card>
        ))}
      </Center>
      <div style={{ position: "absolute", right: 260, top: 230 }}>
        <Bubble t={t} from={at(c, 0.7)} text="？" lang={lang} style={{}} />
      </div>
    </Paper>
  );
};

const S0304: Scene = ({ ctx, c }) => {
  const { t, lang } = ctx;
  const zh = lang === "zh";
  const lines = zh
    ? [
        [0.36, "你有没有一句话，特别怕别人听错？"],
        [0.55, "你会怎么说，让它好好地传到对方那里？"],
      ]
    : [
        [0.42, "Is there something you'd hate to be misheard?"],
        [0.6, "How would you say it so it gets through?"],
      ];
  return (
    <AbsoluteFill>
      <Picture name="tin-can-phone" t={t} from={c.start} to={c.end} lang={lang} zoom={[1.0, 1.07]} />
      <AbsoluteFill style={{ background: `rgba(243,238,229,${0.55 * rise(t, at(c, 0.3), at(c, 0.4))})` }} />
      <Center style={{ gap: 40, top: -40 }}>
        {lines.map(([f, s]) => (
          <Pop key={s as string} t={t} from={at(c, f as number)}>
            <Card color={TEAL} style={{ padding: "26px 50px" }}>
              <span style={{ fontFamily: zh ? ZH : EN, fontSize: zh ? 62 : 56, fontWeight: 800, color: INK }}>{s}</span>
            </Card>
          </Pop>
        ))}
      </Center>
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 80, textAlign: "center", opacity: rise(t, at(c, 0.85), at(c, 0.95)) }}>
        <span style={{ fontFamily: zh ? ZH : EN, fontSize: 52, fontWeight: 700, color: ORANGE }}>{zh ? "在 Lucas Academy 一起学习、一起思考" : "Learning and thinking together at Lucas Academy"}</span>
      </div>
    </AbsoluteFill>
  );
};

/** Shots: the scene and the cues it covers. */
const SHOTS: [Scene, string, string][] = [
  [S0001, "ns00-01", "ns00-01"],
  [S0002, "ns00-02", "ns00-02"],
  [S0003, "ns00-03", "ns00-03"],
  [S0004, "ns00-04", "ns00-04"],
  [S0101, "ns01-01", "ns01-01"],
  [Radio, "ns01-02", "ns01-02"],
  [S0103, "ns01-03", "ns01-03"],
  [S0104, "ns01-04", "ns01-04"],
  [S0105, "ns01-05", "ns01-05"],
  [Radio, "ns01-06", "ns01-06"],
  [S0107, "ns01-07", "ns01-07"],
  [S0108, "ns01-08", "ns01-08"],
  [S0109, "ns01-09", "ns01-09"],
  [S0201, "ns02-01", "ns02-01"],
  [S0202, "ns02-02", "ns02-03"],
  [S0204, "ns02-04", "ns02-04"],
  [S0205, "ns02-05", "ns02-05"],
  [S0206, "ns02-06", "ns02-06"],
  [S0207, "ns02-07", "ns02-07"],
  [S0208, "ns02-08", "ns02-08"],
  [S0209, "ns02-09", "ns02-09"],
  [S0210, "ns02-10", "ns02-10"],
  [S0301, "ns03-01", "ns03-01"],
  [S0302, "ns03-02", "ns03-02"],
  [S0303, "ns03-03", "ns03-03"],
  [S0304, "ns03-04", "ns03-04"],
];
const XFADE = 0.35;

export const FunInformatics03Video: FC<NoiseProps> = ({ tl }) => {
  const frame = useCurrentFrame(),
    { fps } = useVideoConfig();
  if (!tl) return null;
  const t = frame / fps;
  const byId = Object.fromEntries(tl.cues.map((c) => [c.id, c]));
  const ctx: Ctx = { t, lang: tl.lang, tl, cue: (id) => byId[id], ev: (n) => tl.events.find((e) => e.name === n) };
  const first = tl.cues[0].start;
  return (
    <AbsoluteFill style={{ background: PAPER, color: INK, fontFamily: tl.lang === "zh" ? ZH : EN }}>
      <Audio src={file(`audio/${tl.lang}.mix.wav`)} />
      <Paper />
      {SHOTS.map(([S, from, to], i) => {
        const a = byId[from],
          b = byId[to];
        const start = i === 0 ? 0 : a.start;
        const end = b.end + XFADE;
        if (t < start - 0.01 || t > end) return null;
        const fadeIn = i === 0 ? 1 : rise(t, start, start + XFADE);
        return (
          <AbsoluteFill key={from} style={{ opacity: fadeIn }}>
            <S ctx={ctx} c={{ ...a, end: b.end }} />
          </AbsoluteFill>
        );
      })}
      {t >= tl.endCardStart && (
        <AbsoluteFill style={{ opacity: rise(t, tl.endCardStart, tl.endCardStart + 0.6) }}>
          <Paper>
            <Title lang={tl.lang} t={t} from={tl.endCardStart} />
          </Paper>
        </AbsoluteFill>
      )}
      {t < first + 0.2 && <AbsoluteFill style={{ background: PAPER, opacity: 1 - rise(t, 0, first) }} />}
    </AbsoluteFill>
  );
};
