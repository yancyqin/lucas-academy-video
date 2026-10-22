/**
 * 「法国人走上街头，出路在哪里？」 · 从新闻看教育 / Lessons from the Headlines (NEWS-EDUCATION-01.md). The series is never numbered.
 *
 * One picture for two audio tracks (owner, 2026-10-20): Yancy's voice in Chinese and in English, each line starting
 * at the same moment (scripts/news-education-01/build_timeline.py). So nothing on screen belongs to one language only:
 * footage, archival paintings and documents, maps, numbers, dates and icons; the few labels that carry words (title,
 * rights / power, the three branches, the classroom rule, the end card) show both languages. The shot list is
 * scripts/news-education-01/edit.json; each shot fades into the next.
 */
import { useEffect, useState, type CSSProperties, type FC, type ReactNode } from "react";
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

const DIR = "news-education-01";
const file = (p: string) => staticFile(`${DIR}/${p}`);

type Shot = {
  k: string; start: number; end: number; src?: string; rate?: number; from?: number; num?: string; sub?: string;
  numAt?: number; fit?: "cover" | "contain"; ground?: "dark" | "paper"; push?: [number, number, number, number];
  map?: string; mode?: string; items?: [string, string][]; year?: string; place?: string; focusAt?: number[];
  left?: string; right?: string; overlay?: string;
};
type MapData = { land: string; focus: Record<string, string>; dots: Record<string, [number, number]> };
export type Ne01Timeline = { fps: number; durationSeconds: number; draft: boolean; shots: Shot[]; footageSeconds: Record<string, number>; endCardStart: number };
export type Ne01Props = { tl?: Ne01Timeline | null; maps?: Record<string, MapData> | null };

export const calculateNe01Metadata: CalculateMetadataFunction<Ne01Props> = async ({ props, abortSignal }) => {
  const r = await fetch(file("timeline.json"), { signal: abortSignal });
  if (!r.ok) throw Error("Run scripts/news-education-01/build_timeline.py first");
  const tl = (await r.json()) as Ne01Timeline;
  const maps = (await (await fetch(file("maps/maps.json"), { signal: abortSignal })).json()) as Record<string, MapData>;
  return { props: { ...props, tl, maps }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

// ---- look ----
const INK = "#0f1317";
const LAND = "#1c232a";
const EDGE = "#2f3943";
const EMBER = "#e2733c";
const GOLD = "#c9a45a";
const PAPER = "#ece3d2";
const SOFT = "#d9d3c7";
const SERIF = "'NotoSerifSC', 'Songti SC', serif";
const FADE = 0.8; // seconds of cross-fade between shots
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = Easing.bezier(0.3, 0.7, 0.2, 1);

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

/** Seconds since the enclosing Sequence began. */
const useT = () => useCurrentFrame() / useVideoConfig().fps;
const appear = (t: number, at: number, d = 0.8) => interpolate(t, [at, at + d], [0, 1], { ...clamp, easing: ease });

// ---- overlays: a number or date, language-neutral ----
const Num: FC<{ value: string; sub?: string; at?: number }> = ({ value, sub, at = 0.6 }) => {
  const t = useT();
  const o = appear(t, at, 1.0);
  return (
    <div style={{ position: "absolute", left: 110, bottom: 96, opacity: o, transform: `translateY(${(1 - o) * 16}px)`, fontFamily: SERIF, color: "#fff",
      textShadow: "0 4px 30px rgba(0,0,0,.75), 0 1px 3px rgba(0,0,0,.8)" }}>
      <div style={{ fontSize: 132, fontWeight: 300, letterSpacing: 2, lineHeight: 1 }}>{value}</div>
      {sub ? <div style={{ fontSize: 40, fontWeight: 300, opacity: 0.85, marginTop: 14, letterSpacing: 4 }}>{sub}</div> : null}
    </div>
  );
};

// ---- footage and stills ----
const Clip: FC<{ tl: Ne01Timeline; s: Shot; dur: number }> = ({ tl, s, dur }) => {
  const src = s.src!;
  const have = (tl.footageSeconds[src] ?? 10) - (s.from ?? 0) - 0.1;
  const rate = Math.max(0.5, Math.min(s.rate ?? 1, have / Math.max(dur, 0.1)));
  return (
    <AbsoluteFill style={{ background: INK }}>
      <OffthreadVideo src={file(`footage/${src}`)} muted playbackRate={rate} startFrom={Math.round((s.from ?? 0) * 30)}
        style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0) 55%, rgba(0,0,0,.35) 100%)" }} />
    </AbsoluteFill>
  );
};

const Art: FC<{ s: Shot; dur: number; src?: string }> = ({ s, dur, src }) => {
  const t = useT();
  const [p0, p1, ox, oy] = s.push ?? [1.0, 1.08, 50, 45];
  const sc = interpolate(t, [0, Math.max(dur + FADE, 0.1)], [p0, p1], { ...clamp, easing: Easing.inOut(Easing.sin) });
  const image = file(`art/${src ?? s.src}`);
  const paper = s.ground === "paper";
  const fit = s.fit ?? "cover";
  const flat = (src ?? s.src ?? "").endsWith(".png");
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: flat ? "#e6dbc4" : paper ? "#2a241c" : "#120f0c" }}>
      {fit === "contain" && !flat ? (
        <Img src={image} style={{ position: "absolute", left: -90, top: -90, width: 2100, height: 1260, objectFit: "cover",
          filter: paper ? "blur(40px) brightness(.55) sepia(.4)" : "blur(46px) brightness(.35) saturate(.8)" }} />
      ) : null}
      <AbsoluteFill style={{ transform: `scale(${sc})`, transformOrigin: `${ox}% ${oy}%` }}>
        <Img src={image} style={{ width: "100%", height: "100%", objectFit: fit,
          filter: fit === "contain" && !flat ? "drop-shadow(0 24px 50px rgba(0,0,0,.6))" : undefined }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---- icons (simple strokes, no words) ----
const Icon: FC<{ name: string; size?: number; color?: string }> = ({ name, size = 120, color = SOFT }) => {
  const st = { fill: "none", stroke: color, strokeWidth: 5, strokeLinecap: "round", strokeLinejoin: "round" } as const;
  const shapes: Record<string, ReactNode> = {
    school: <><path d="M14 98V48L60 22l46 26v50Z" {...st} /><path d="M46 98V70h28v28M60 22V6l18 6-18 6" {...st} /><path d="M30 40c4-10 14-10 18 0M76 40c4-12 14-12 16 0" stroke={EMBER} strokeWidth={5} fill="none" /></>,
    student: <><circle cx="60" cy="34" r="16" {...st} /><path d="M28 104c2-26 14-40 32-40s30 14 32 40" {...st} /><path d="M38 20l22-10 22 10-22 10Z" {...st} /></>,
    teacher: <><circle cx="48" cy="32" r="15" {...st} /><path d="M18 104c2-26 12-40 30-40 10 0 18 4 24 12" {...st} /><path d="M70 30h40v34H70" {...st} /><path d="M66 76l28-20" {...st} /></>,
    person: <><circle cx="60" cy="34" r="17" {...st} /><path d="M26 106c2-28 14-44 34-44s32 16 34 44" {...st} /></>,
    child: <><circle cx="60" cy="46" r="14" {...st} /><path d="M36 106c2-22 10-34 24-34s22 12 24 34" {...st} /></>,
    moon: <><path d="M78 18a44 44 0 1 0 26 66 36 36 0 0 1-26-66Z" {...st} /><circle cx="92" cy="30" r="3" fill={color} /></>,
    coin: <><circle cx="60" cy="60" r="42" {...st} /><path d="M76 40c-18-10-38 0-38 20s20 30 38 20M30 54h36M30 66h36" {...st} /></>,
    jobs: <><rect x="16" y="40" width="88" height="60" rx="8" {...st} /><path d="M44 40V28h32v12M16 64h88" {...st} /></>,
    scales: <><path d="M60 14v86M30 100h60M22 34h76" {...st} /><path d="M22 34 8 66h28Z M98 34 84 66h28Z" {...st} /></>,
    vote: <><rect x="20" y="52" width="80" height="50" rx="6" {...st} /><path d="M44 52V18h32v34M50 34l8 8 14-16" {...st} /></>,
    speech: <><path d="M14 22h92v58H52l-22 20V80H14Z" {...st} /><path d="M34 44h52M34 60h34" {...st} /></>,
    gavel: <><path d="M30 28l34-18 12 22-34 18Z" {...st} /><path d="M58 40l40 40" {...st} /><path d="M16 104h52" {...st} /></>,
    dome: <><path d="M20 100h80M28 100V62h64v38M42 62v38M60 62v38M78 62v38M30 62c0-22 14-34 30-34s30 12 30 34M60 28V12" {...st} /></>,
    columns: <><path d="M14 40 60 14l46 26ZM20 104h80M28 46v50M50 46v50M70 46v50M92 46v50" {...st} /></>,
    hand: <><path d="M30 104V56c0-6 10-6 10 0v-26c0-6 10-6 10 0v20-28c0-6 10-6 10 0v28-22c0-6 10-6 10 0v34c4-10 14-10 14-2l-6 28c-4 14-12 22-26 22H44c-8 0-14-6-14-12" {...st} /></>,
    book: <><path d="M60 30c-16-10-32-10-46-6v70c14-4 30-4 46 6 16-10 32-10 46-6V24c-14-4-30-4-46 6Z" {...st} /><path d="M60 30v70" {...st} /></>,
    skiers: <><circle cx="34" cy="26" r="9" {...st} /><path d="M34 36l-6 26 14 18M28 62l-14 8M8 96l52-14" {...st} /><circle cx="88" cy="26" r="9" {...st} /><path d="M88 36l6 26-14 18M94 62l14 8M112 96 60 82" {...st} /></>,
    card: <><rect x="14" y="26" width="92" height="64" rx="8" {...st} /><circle cx="40" cy="52" r="10" {...st} /><path d="M24 78c4-10 28-10 32 0M66 46h28M66 60h28" {...st} /></>,
    chair: <><path d="M34 12v94M34 62h52M86 62v44M34 62v44" {...st} /><path d="M34 12c8 2 12 6 12 12v38" {...st} /></>,
    question: <><path d="M38 40c0-14 10-22 22-22s22 8 22 20c0 16-22 18-22 34" {...st} /><circle cx="60" cy="98" r="4" fill={color} /></>,
  };
  return <svg width={size} height={size} viewBox="0 0 120 120">{shapes[name]}</svg>;
};

const Dark: FC<{ children: ReactNode; style?: CSSProperties }> = ({ children, style }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 40%, #1b2128 0%, ${INK} 70%)`, ...style }}>{children}</AbsoluteFill>
);

// ---- graphics ----
const Nums: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const items = s.items ?? [];
  return (
    <Dark>
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 150 }}>
        {items.map(([v, icon], i) => {
          const o = appear(t, 0.3 + i * 0.9, 0.9);
          return (
            <div key={v} style={{ display: "flex", flexDirection: "column", alignItems: "center", opacity: o, transform: `translateY(${(1 - o) * 24}px)` }}>
              <Icon name={icon} size={150} color={i === 0 ? EMBER : SOFT} />
              <div style={{ fontFamily: SERIF, fontWeight: 300, fontSize: v.length > 8 ? 96 : 140, color: "#fff", marginTop: 26, letterSpacing: 2 }}>{v}</div>
            </div>
          );
        })}
      </AbsoluteFill>
    </Dark>
  );
};

const MapCard: FC<{ s: Shot; maps: Record<string, MapData> }> = ({ s, maps }) => {
  const t = useT();
  const m = maps[s.map!];
  const ids = Object.keys(m.focus);
  const dots = Object.entries(m.dots);
  const breath = 1 + 0.08 * Math.sin(t * 2.2);
  return (
    <AbsoluteFill style={{ background: INK }}>
      <svg width={1920} height={1080} viewBox="0 0 1920 1080">
        <path d={m.land} fill={LAND} stroke={EDGE} strokeWidth={1.2} />
        {ids.map((id, i) => {
          const at = s.mode === "sequence" ? 0.4 + i * 1.5 : 0.3;
          const on = appear(t, at, 1.0);
          return <path key={id} d={m.focus[id]} fill={EMBER} fillOpacity={0.12 + 0.55 * on} stroke={EMBER} strokeOpacity={0.4 + 0.6 * on} strokeWidth={2} />;
        })}
        {s.mode === "spread"
          ? dots.flatMap(([name, [x, y]], i) => {
              const ring = [...Array(name === "creteil" ? 1 : 9)].map((_, k) => {
                const a = (k * 2.4 + i) % (2 * Math.PI), r = name === "creteil" ? 0 : 14 + (k % 3) * 16;
                return [x + r * Math.cos(a), y + r * Math.sin(a)] as [number, number];
              });
              return ring.map(([px, py], k) => {
                const at = name === "creteil" ? 0.2 : 1.2 + i * 0.35 + k * 0.12;
                const o = appear(t, at, 0.5);
                return <circle key={`${name}${k}`} cx={px} cy={py} r={(name === "creteil" ? 13 * breath : 6) * o} fill={name === "creteil" ? "#fff" : EMBER} opacity={o} />;
              });
            })
          : dots.map(([name, [x, y]], i) => {
              const at = s.mode === "sequence" ? 0.6 + i * 1.5 : 0.6;
              const o = appear(t, at, 0.6);
              return <circle key={name} cx={x} cy={y} r={10 * o * breath} fill="#fff" opacity={o} />;
            })}
      </svg>
    </AbsoluteFill>
  );
};

const Title: FC = () => {
  const t = useT();
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, color: "#fff", textAlign: "center" }}>
        <div style={{ fontSize: 36, fontWeight: 300, letterSpacing: 8, color: GOLD, opacity: appear(t, 0.2) }}>从新闻看教育 · LESSONS FROM THE HEADLINES</div>
        <div style={{ fontSize: 108, fontWeight: 400, marginTop: 50, opacity: appear(t, 0.6), letterSpacing: 6 }}>法国人走上街头，出路在哪里？</div>
        <div style={{ fontSize: 56, fontWeight: 300, marginTop: 30, opacity: appear(t, 1.1), color: SOFT }}>The French Take to the Streets. Where Is the Way Out?</div>
        <div style={{ fontSize: 30, fontWeight: 300, marginTop: 70, opacity: appear(t, 1.6), color: "#9aa3ac", letterSpacing: 3 }}>Yancy Qin | Lucas Academy</div>
      </AbsoluteFill>
    </Dark>
  );
};

const End: FC = () => {
  const t = useT();
  const credit: CSSProperties = { fontSize: 22, fontWeight: 300, color: "#8f989f", lineHeight: 1.7, letterSpacing: 0.5 };
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, color: "#fff", textAlign: "center" }}>
        <div style={{ opacity: appear(t, 0.3) }}><Icon name="book" size={90} color={GOLD} /></div>
        <div style={{ fontSize: 64, fontWeight: 400, marginTop: 24, opacity: appear(t, 0.6), letterSpacing: 6 }}>从新闻看教育 · Lessons from the Headlines</div>
        <div style={{ fontSize: 34, fontWeight: 300, marginTop: 22, opacity: appear(t, 1.0), color: SOFT, letterSpacing: 3 }}>Yancy Qin | Lucas Academy</div>
        <div style={{ marginTop: 70, opacity: appear(t, 1.8), maxWidth: 1500, ...credit }}>
          Footage: Pexels — Florian Delée and others; the ski runs are Yancy's own.<br />
          Images: Wikimedia Commons — public domain paintings and documents; Dhaka 2024: S.M.M. Musabbir Uddin (CC0, CC BY 4.0); Nepal 2025: Bijay Chaurasia (CC BY-SA 4.0); The Federalist (1788): Yale Law Library (CC BY 2.0).<br />
          Music: Bach, Air (U.S. Air Force Strings, public domain) · Satie, Gymnopédie No. 1 (Kevin MacLeod, CC BY 3.0) · Bach, Jesu, Joy of Man's Desiring (Orchestra Gli Armonici, CC0).<br />
          Scripture: 和合本 · World English Bible. Voice: Yancy's own voice, synthesized.
        </div>
      </AbsoluteFill>
    </Dark>
  );
};

const Chairs: FC = () => {
  const t = useT();
  const lit = Math.floor(interpolate(t, [0.8, 9], [0, 27], clamp));
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 40 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(9, 110px)", gap: 18 }}>
          {[...Array(27)].map((_, i) => (
            <div key={i} style={{ opacity: i < lit ? 1 : 0.18, transition: "none" }}><Icon name="chair" size={100} color={i < lit ? (i % 4 === 0 ? EMBER : SOFT) : "#46505a"} /></div>
          ))}
        </div>
        <div style={{ fontFamily: SERIF, fontWeight: 300, color: "#fff", fontSize: 64, letterSpacing: 4, opacity: appear(t, 0.4) }}>
          1991 → 2026 · <span style={{ color: EMBER }}>{Math.max(lit, 1)}</span>
        </div>
      </AbsoluteFill>
    </Dark>
  );
};

const Ai: FC = () => {
  const t = useT();
  const icons = ["jobs", "scales", "vote", "speech"];
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ border: `3px solid ${EDGE}`, borderRadius: 40, padding: "60px 90px", display: "flex", gap: 90, background: "rgba(255,255,255,.03)" }}>
          {icons.map((n, i) => (
            <div key={n} style={{ opacity: appear(t, 0.5 + i * 1.2), transform: `translateY(${(1 - appear(t, 0.5 + i * 1.2)) * 20}px)` }}><Icon name={n} size={170} /></div>
          ))}
          <div style={{ fontFamily: SERIF, fontSize: 140, color: SOFT, opacity: appear(t, 5.5), alignSelf: "center" }}>…</div>
        </div>
      </AbsoluteFill>
    </Dark>
  );
};

const Rights: FC = () => {
  const t = useT();
  const col = (icon: string, zh: string, en: string, color: string, at: number) => (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", opacity: appear(t, at), width: 620 }}>
      <Icon name={icon} size={220} color={color} />
      <div style={{ fontFamily: SERIF, fontSize: 150, color: "#fff", marginTop: 26 }}>{zh}</div>
      <div style={{ fontFamily: SERIF, fontWeight: 300, fontSize: 64, color, letterSpacing: 6 }}>{en}</div>
    </div>
  );
  return (
    <Dark>
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 120 }}>
        {col("speech", "权利", "right", SOFT, 0.4)}
        <div style={{ width: 2, height: 520, background: EDGE, opacity: appear(t, 1.2) }} />
        {col("gavel", "权力", "power", GOLD, 1.6)}
      </AbsoluteFill>
    </Dark>
  );
};

const Tension: FC<{ s: Shot; dur: number }> = ({ s, dur }) => {
  const t = useT();
  const build = s.mode === "build";
  const k = build ? interpolate(t, [0.3, Math.max(dur, 1)], [0.2, 1], clamp) : interpolate(t, [0.5, Math.min(6, dur)], [1, 0], { ...clamp, easing: ease });
  const shake = build ? Math.sin(t * 40) * 6 * k : Math.sin(t * 40) * 6 * k;
  const gap = interpolate(k, [0, 1], [260, 20]);
  const col = k > 0.5 ? EMBER : SOFT;
  const arrow = (dir: 1 | -1) => (
    <svg width={620} height={200} viewBox="0 0 620 200" style={{ transform: `scaleX(${dir})` }}>
      <path d={`M10 100H${520}`} stroke={col} strokeWidth={10 + 30 * k} strokeLinecap="round" opacity={0.5 + 0.5 * k} />
      <path d="M470 40 600 100 470 160Z" fill={col} opacity={0.5 + 0.5 * k} />
    </svg>
  );
  return (
    <Dark>
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap }}>
        <div style={{ transform: `translateX(${shake}px)` }}>{arrow(1)}</div>
        <div style={{ transform: `translateX(${-shake}px)` }}>{arrow(-1)}</div>
      </AbsoluteFill>
      {!build ? (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: appear(t, Math.min(6, dur) - 1, 1.5) }}>
          <Icon name="hand" size={200} color={GOLD} />
        </AbsoluteFill>
      ) : null}
    </Dark>
  );
};

const Year: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  return (
    <AbsoluteFill style={{ background: "#16120d" }}>
      <Img src={file("art/sc04-map-1775.png")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "contain", opacity: 0.18, filter: "sepia(.6)" }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, color: "#fff" }}>
        <div style={{ fontSize: 220, fontWeight: 300, letterSpacing: 10, opacity: appear(t, 0.3) }}>{s.year}</div>
        <div style={{ fontSize: 60, fontWeight: 300, color: GOLD, letterSpacing: 10, opacity: appear(t, 1.0) }}>{s.place}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Spectacles: FC<{ dur: number }> = ({ dur }) => {
  const t = useT();
  const draw = interpolate(t, [0.5, Math.min(7, dur)], [1, 0], { ...clamp, easing: ease });
  const st = { fill: "none", stroke: GOLD, strokeWidth: 9, strokeLinecap: "round", pathLength: 1, strokeDasharray: 1, strokeDashoffset: draw } as const;
  return (
    <AbsoluteFill style={{ background: "#120f0c" }}>
      <Img src={file("art/sc04-washington-portrait.jpg")} style={{ position: "absolute", left: -90, top: -90, width: 2100, height: 1260, objectFit: "cover",
        filter: "blur(40px) brightness(.3)" }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <svg width={1100} height={500} viewBox="0 0 1100 500">
          <circle cx="330" cy="250" r="150" {...st} />
          <circle cx="770" cy="250" r="150" {...st} />
          <path d="M480 240c40-40 100-40 140 0" {...st} />
          <path d="M180 230 40 180M920 230l140-50" {...st} />
        </svg>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Branches: FC = () => {
  const t = useT();
  const node = (icon: string, zh: string, en: string, x: number, y: number, at: number) => (
    <div style={{ position: "absolute", left: x - 170, top: y - 150, width: 340, display: "flex", flexDirection: "column", alignItems: "center", opacity: appear(t, at) }}>
      <Icon name={icon} size={170} color={SOFT} />
      <div style={{ fontFamily: SERIF, fontSize: 56, color: "#fff", marginTop: 6 }}>{zh}</div>
      <div style={{ fontFamily: SERIF, fontWeight: 300, fontSize: 36, color: GOLD, letterSpacing: 3 }}>{en}</div>
    </div>
  );
  const spin = t * 0.25;
  const arc = (a: number) => {
    const r = 330, cx = 960, cy = 560;
    const p = (q: number) => `${cx + r * Math.cos(q)},${cy + r * Math.sin(q)}`;
    return `M${p(a)} A${r},${r} 0 0 1 ${p(a + 1.2)}`;
  };
  return (
    <Dark>
      <svg width={1920} height={1080} style={{ position: "absolute", opacity: appear(t, 2.2) * 0.7 }}>
        <defs><marker id="arrowhead" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto"><path d="M0 0 10 5 0 10Z" fill={EMBER} /></marker></defs>
        {[0, 2.094, 4.189].map((a) => <path key={a} d={arc(a + spin + 0.45)} fill="none" stroke={EMBER} strokeWidth={5} markerEnd="url(#arrowhead)" />)}
      </svg>
      {node("dome", "国会", "Congress", 960, 230, 0.3)}
      {node("person", "总统", "President", 640, 800, 0.9)}
      {node("gavel", "法院", "Courts", 1280, 800, 1.5)}
    </Dark>
  );
};

const FEDERALIST = [
  "Ambition must be made to counteract ambition. The interest of the man must be connected with the constitutional rights of the place. It may be a reflection on human nature, that such devices should be necessary to control the abuses of government. But what is government itself, but the greatest of all reflections on human nature?",
  "If men were angels, no government would be necessary. If angels were to govern men, neither external nor internal controls on government would be necessary.",
  "In framing a government which is to be administered by men over men, the great difficulty lies in this: you must first enable the government to control the governed; and in the next place oblige it to control itself. A dependence on the people is, no doubt, the primary control on the government; but experience has taught mankind the necessity of auxiliary precautions.",
];
const Quote: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const at = (s.focusAt ?? []).map((x) => x - s.start);
  const active = at.filter((x) => t >= x - 0.3).length - 1;
  const last = active >= 3;
  return (
    <AbsoluteFill style={{ background: "#2a241c" }}>
      <div style={{ position: "absolute", left: 230, right: 230, top: 60, bottom: 60, boxSizing: "border-box", background: PAPER, boxShadow: "0 30px 80px rgba(0,0,0,.6)", padding: "64px 90px", fontFamily: "'Times New Roman', Georgia, serif", color: "#2a241c", overflow: "hidden" }}>
        <div style={{ fontSize: 26, letterSpacing: 6, color: "#7a6a52", marginBottom: 36 }}>THE FEDERALIST · No. 51 · 1788</div>
        {FEDERALIST.map((p, i) => {
          const on = i === active || (last && i === 1);
          const big = last && i === 1;
          return (
            <p key={i} style={{ fontSize: big ? 48 : 35, lineHeight: 1.45, margin: "0 0 26px", opacity: active < 0 ? 0.5 : on ? 1 : 0.22,
              background: on && !big ? "rgba(201,164,90,.18)" : "transparent", padding: "4px 10px", borderRadius: 6 }}>{p}</p>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Terms: FC = () => {
  const t = useT();
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: SERIF, color: "#fff" }}>
        <div style={{ display: "flex", gap: 24, opacity: appear(t, 0.3) }}>
          {[0, 1].map((i) => (
            <div key={i} style={{ width: 420 * appear(t, 0.8 + i * 1.2, 1.2), height: 46, background: i ? GOLD : SOFT, borderRadius: 6 }} />
          ))}
          <div style={{ width: 420, height: 46, border: `3px dashed #46505a`, borderRadius: 6, opacity: appear(t, 3.5) }} />
        </div>
        <div style={{ display: "flex", width: 1308, justifyContent: "space-between", fontSize: 52, fontWeight: 300, marginTop: 30, opacity: appear(t, 0.5) }}>
          <span>1789</span><span>1793</span><span style={{ color: GOLD }}>1797</span><span style={{ color: "#46505a" }}>…</span>
        </div>
      </AbsoluteFill>
    </Dark>
  );
};

const Two: FC = () => {
  const t = useT();
  return (
    <Dark>
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 120 }}>
        <div style={{ opacity: appear(t, 0.3) }}><Icon name="columns" size={300} color={SOFT} /></div>
        <div style={{ fontFamily: SERIF, fontSize: 140, color: "#6b747c", opacity: appear(t, 1.0) }}>+</div>
        <div style={{ opacity: appear(t, 1.4) }}><Icon name="hand" size={300} color={GOLD} /></div>
      </AbsoluteFill>
    </Dark>
  );
};

const Diptych: FC<{ s: Shot }> = ({ s }) => {
  const t = useT();
  const pane = (src: string, at: number) => (
    <div style={{ width: 760, height: 860, overflow: "hidden", opacity: appear(t, at), boxShadow: "0 24px 60px rgba(0,0,0,.6)" }}>
      <Img src={file(`art/${src}`)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${1 + t * 0.006})` }} />
    </div>
  );
  return (
    <Dark>
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 70 }}>
        {pane(s.left!, 0.2)}{pane(s.right!, 0.6)}
      </AbsoluteFill>
    </Dark>
  );
};

const Literacy: FC = () => {
  const t = useT();
  return (
    <Dark>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ position: "relative", width: 900, height: 700 }}>
          <div style={{ position: "absolute", left: 300, top: 360, opacity: appear(t, 0.3) }}><Icon name="book" size={300} color={SOFT} /></div>
          {[[120, 120, 2.0], [370, 20, 3.6], [620, 120, 5.2]].map(([x, y, at]) => (
            <div key={x} style={{ position: "absolute", left: x, top: y + (1 - appear(t, at)) * 60, opacity: appear(t, at) }}><Icon name="question" size={180} color={GOLD} /></div>
          ))}
        </div>
        <div style={{ fontFamily: SERIF, fontWeight: 300, fontSize: 44, color: SOFT, letterSpacing: 4, opacity: appear(t, 1.0) }}>critical literacy · 批判性读写</div>
      </AbsoluteFill>
    </Dark>
  );
};

const Rule: FC = () => {
  const t = useT();
  const bar = (zh: string, en: string, h: number, color: string, at: number) => (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 520 }}>
      <div style={{ height: 520, display: "flex", alignItems: "flex-end" }}>
        <div style={{ width: 200, height: h * appear(t, at, 1.4), background: color, borderRadius: "10px 10px 0 0" }} />
      </div>
      <div style={{ fontFamily: SERIF, fontSize: 84, color: "#fff", marginTop: 26, opacity: appear(t, at - 0.4) }}>{zh}</div>
      <div style={{ fontFamily: SERIF, fontWeight: 300, fontSize: 48, color, letterSpacing: 4, opacity: appear(t, at - 0.4) }}>{en}</div>
    </div>
  );
  return (
    <Dark>
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 160 }}>
        {bar("内容", "content", 140, SOFT, 1.0)}
        {bar("关系", "relationships", 500, GOLD, 2.4)}
      </AbsoluteFill>
    </Dark>
  );
};

const SkiCode: FC = () => {
  const t = useT();
  return (
    <div style={{ position: "absolute", right: 90, bottom: 80, display: "flex", alignItems: "center", gap: 30, padding: "26px 40px", borderRadius: 26,
      background: "rgba(10,14,18,.62)", opacity: appear(t, 1.0, 1.2) }}>
      <Icon name="skiers" size={140} color="#fff" />
      <svg width={90} height={40}><path d="M5 20h70M60 6l18 14-18 14" stroke={GOLD} strokeWidth={6} fill="none" strokeLinecap="round" /></svg>
      <Icon name="card" size={140} color={GOLD} />
    </div>
  );
};

const Question: FC = () => {
  const t = useT();
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end", paddingBottom: 120, fontFamily: SERIF, color: "#fff", textAlign: "center",
      textShadow: "0 4px 24px rgba(0,0,0,.8)" }}>
      <div style={{ fontSize: 58, letterSpacing: 4, opacity: appear(t, 1.0, 1.4), maxWidth: 1600 }}>你手里有理、也有力的时候，会先放下一点点吗？</div>
      <div style={{ fontSize: 38, fontWeight: 300, marginTop: 20, color: SOFT, opacity: appear(t, 1.8, 1.4), maxWidth: 1500 }}>When you have right on your side and strength in your hands, will you lay down just a little first?</div>
    </AbsoluteFill>
  );
};

// ---- the film ----
const ShotView: FC<{ tl: Ne01Timeline; maps: Record<string, MapData>; s: Shot; dur: number }> = ({ tl, maps, s, dur }) => {
  switch (s.k) {
    case "clip": return <Clip tl={tl} s={s} dur={dur} />;
    case "art": return <Art s={s} dur={dur} />;
    case "map": return <MapCard s={s} maps={maps} />;
    case "nums": return <Nums s={s} />;
    case "title": return <Title />;
    case "end": return <End />;
    case "chairs": return <Chairs />;
    case "ai": return <Ai />;
    case "rights": return <Rights />;
    case "tension": return <Tension s={s} dur={dur} />;
    case "year": return <Year s={s} />;
    case "spectacles": return <Spectacles dur={dur} />;
    case "branches": return <Branches />;
    case "quote": return <Quote s={s} />;
    case "terms": return <Terms />;
    case "two": return <Two />;
    case "diptych": return <Diptych s={s} />;
    case "literacy": return <Literacy />;
    case "rule": return <Rule />;
    default: return <Dark><div style={{ color: "#fff", fontSize: 60, margin: "auto" }}>{s.k}</div></Dark>;
  }
};

const Faded: FC<{ dur: number; first: boolean; children: ReactNode }> = ({ dur, first, children }) => {
  const t = useT();
  const o = first ? interpolate(t, [0, 1.2], [0, 1], clamp) : interpolate(t, [0, FADE], [0, 1], clamp);
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};

export const NewsEducation01Video: FC<Ne01Props> = ({ tl, maps }) => {
  useFonts();
  const { fps } = useVideoConfig();
  if (!tl || !maps) return <AbsoluteFill style={{ background: INK }} />;
  return (
    <AbsoluteFill style={{ background: INK }}>
      {tl.shots.map((s, i) => {
        const from = Math.round(s.start * fps);
        const dur = s.end - s.start;
        const len = Math.max(1, Math.round((dur + (i + 1 < tl.shots.length ? FADE : 0)) * fps));
        return (
          <Sequence key={i} from={from} durationInFrames={len}>
            <Faded dur={dur} first={i === 0}>
              <ShotView tl={tl} maps={maps} s={s} dur={dur} />
              {s.num ? (
                <Sequence from={s.numAt !== undefined ? Math.round((s.numAt - s.start) * fps) : 0}>
                  <Num value={s.num} sub={s.sub} at={s.numAt !== undefined ? 0.2 : 0.8} />
                </Sequence>
              ) : null}
              {s.overlay === "skicode" ? <SkiCode /> : null}
              {s.overlay === "question" ? <Question /> : null}
            </Faded>
          </Sequence>
        );
      })}
      {tl.draft ? <div style={{ position: "absolute", right: 30, top: 24, color: "#ff5", fontSize: 26, fontFamily: "monospace" }}>DRAFT</div> : null}
    </AbsoluteFill>
  );
};

/** The series ribbon across a cover's top-right corner (owner, 2026-10-21): the series name, never an episode number. */
const Ribbon: FC<{ text: string; size: number; a?: number; h?: number }> = ({ text, size, a = 175, h = 88 }) => {
  // A band at 45° whose centre sits a px in from both edges; the visible chord across the corner is 2a·√2 long,
  // and 2a·√2 − h along its inner edge, so the text must fit inside that.
  // The outer edge meets the frame 2a + h/√2 from the corner; the clip box must reach past it or it cuts the band.
  const box = 2 * a + h + 40, len = 2 * (a + h) * 1.42 + 200;
  return (
    <div style={{ position: "absolute", top: 0, right: 0, width: box, height: box, overflow: "hidden" }}>
      <div style={{ position: "absolute", left: box - a - len / 2, top: a - h / 2, width: len, height: h, transform: "rotate(45deg)",
        background: GOLD, color: "#16120d", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: SERIF,
        fontSize: size, letterSpacing: 2, boxShadow: "0 6px 20px rgba(0,0,0,.45)", whiteSpace: "nowrap" }}>
        {text}
      </div>
    </div>
  );
};

/** YouTube cover, 1280×720 (README "YouTube covers"): the question in Chinese only, over one frame of the Paris fire. */
export const NewsEducation01Cover: FC = () => {
  useFonts();
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Img src={file("art/cover-fire.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", objectPosition: "70% 50%" }} />
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(10,12,15,.92) 0%, rgba(10,12,15,.78) 38%, rgba(10,12,15,.15) 70%, rgba(10,12,15,0) 100%)" }} />
      <AbsoluteFill style={{ justifyContent: "center", paddingLeft: 70, fontFamily: SERIF, color: "#fff" }}>
        <div style={{ fontSize: 104, lineHeight: 1.22, letterSpacing: 4, textShadow: "0 4px 24px rgba(0,0,0,.6)" }}>
          法国人走上街头，<br /><span style={{ color: EMBER }}>出路</span>在哪里？
        </div>
      </AbsoluteFill>
      <Ribbon text="从新闻看教育" size={46} a={165} />
    </AbsoluteFill>
  );
};

/** The English cover: the same picture, the question in English only. */
export const NewsEducation01CoverEn: FC = () => {
  useFonts();
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Img src={file("art/cover-fire.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", objectPosition: "70% 50%" }} />
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(10,12,15,.93) 0%, rgba(10,12,15,.8) 42%, rgba(10,12,15,.15) 72%, rgba(10,12,15,0) 100%)" }} />
      <AbsoluteFill style={{ justifyContent: "center", paddingLeft: 70, fontFamily: SERIF, color: "#fff" }}>
        <div style={{ fontSize: 80, lineHeight: 1.1, letterSpacing: 1, textShadow: "0 4px 24px rgba(0,0,0,.6)", whiteSpace: "nowrap" }}>
          The French Take<br />to the Streets.<br />Where Is the<br /><span style={{ color: EMBER, whiteSpace: "nowrap" }}>Way Out</span>?
        </div>
      </AbsoluteFill>
      <Ribbon text="Lessons from the Headlines" size={30} a={215} />
    </AbsoluteFill>
  );
};
