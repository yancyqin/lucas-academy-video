// 中英阅读 (ZHONG-YING.md): a lesson of 语言的桥's 看得见的诗 read aloud, verse by verse, in Chinese and then in
// English, with the lesson's own narration. The painting on the left is the work's art-lab living painting,
// painted in stroke by stroke while the Chinese is read and brought alive while the English is (paint.py,
// living.mjs); on the right the verse lights up word by word as it is read. The series seal 中英阅读 opens the
// film with the intro line, and stays small in the corner.
import type { CSSProperties, FC } from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  type CalculateMetadataFunction,
} from "remotion";

type Lang = "zh" | "en";
type Word = { text: string; start: number | null; end: number | null };
type Cue = { kind: "intro" | "title" | "verse" | "closing" | "subscribe"; lang: Lang; work: number | null; unit: number | null; start: number; end: number; words: Word[] };
type Work = {
  id: string;
  units: number[];
  style: string;
  title: Record<Lang, string>;
  by: Record<Lang, string>;
  start: number;
  end: number;
};
type Chapter = { zh: string; en: string; start: number; end: number };
// The look back under the closing lines: the works' MiniMax clips once more, or a work's own living end where it
// has none (paint-recap.mp4, paint.py).
type Recap = { start: number; end: number; fade: number; clips: { work: string; file: string; from: number; skip?: number }[] };
export type ZhongYingTimeline = {
  film: string;
  fps: number;
  durationSeconds: number;
  endCardStart: number;
  title: Record<Lang, string>;
  cues: Cue[];
  works: Work[];
  recap?: Recap | null;
  chapters: Chapter[];
};
export type ZhongYingProps = { film: string; tl?: ZhongYingTimeline | null };

const PAPER = "#f6f1e7",
  INK = "#2a2520",
  MUTED = "#8c8172",
  FAINT = "#c4baab",
  SEAL = "#b8352a",
  LINE = "rgba(80, 64, 48, 0.16)";
const ZH = 'Baskerville, "Songti SC", "STSong", serif'; // Latin letters and digits in Chinese text from Baskerville
const EN = 'Baskerville, "Hoefler Text", Georgia, serif';
const SANS = '"Avenir Next", "Helvetica Neue", sans-serif';
const PIC = { x: 56, y: 70, w: 1200, h: 800 };
const COL = { x: 1300, w: 560 };

const ease = (x: number) => {
  const t = Math.max(0, Math.min(1, x));
  return t * t * (3 - 2 * t);
};
const rise = (t: number, a: number, b: number) => ease((t - a) / Math.max(0.001, b - a));
const window_ = (t: number, a: number, b: number, inn = 0.5, out = 0.5) => Math.min(rise(t, a, a + inn), 1 - rise(t, b - out, b));

export const calculateZhongYingMetadata: CalculateMetadataFunction<ZhongYingProps> = async ({ props, abortSignal }) => {
  const response = await fetch(staticFile(`zhong-ying/${props.film}/timeline.json`), { signal: abortSignal });
  if (!response.ok) throw Error("Run scripts/zhong-ying/build_timeline.py first");
  const tl = (await response.json()) as ZhongYingTimeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

/** The series seal: 中英阅读 cut in a vermilion square, read like a seal (right column first, top to bottom).
 * `clean` leaves out the worn print, for the cover, where it is a small icon. */
export const Seal: FC<{ size: number; clean?: boolean; style?: CSSProperties }> = ({ size, clean, style }) => (
  <svg width={size} height={size} viewBox="0 0 100 100" style={style}>
    <defs>
      <filter id="seal-rough" x="-5%" y="-5%" width="110%" height="110%">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="4" result="noise" />
        <feColorMatrix in="noise" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -6 4" result="speckle" />
        <feComposite in="SourceGraphic" in2="speckle" operator="in" result="worn" />
        <feTurbulence type="turbulence" baseFrequency="0.06" numOctaves="2" seed="9" result="warp" />
        <feDisplacementMap in="worn" in2="warp" scale="1.6" />
      </filter>
    </defs>
    <g filter={clean ? undefined : "url(#seal-rough)"}>
      <rect x="4" y="4" width="92" height="92" rx="7" fill={SEAL} />
      <rect x="10" y="10" width="80" height="80" rx="3" fill="none" stroke={PAPER} strokeWidth="1.6" opacity="0.9" />
      {[
        ["中", 70, 37],
        ["英", 70, 75],
        ["阅", 30, 37],
        ["读", 30, 75],
      ].map(([ch, x, y]) => (
        <text key={ch as string} x={x as number} y={y as number} textAnchor="middle" fontFamily={ZH} fontWeight={900} fontSize={34} fill={PAPER}>
          {ch}
        </text>
      ))}
    </g>
  </svg>
);

/** One cue's words: read ones in ink, the one being read in vermilion, the rest still pale. */
const Words: FC<{ cue: Cue | undefined; words: Word[]; t: number; lang: Lang; size: number; lineHeight: number; align?: "left" | "center" }> = ({
  cue,
  words,
  t,
  lang,
  size,
  lineHeight,
  align = "left",
}) => {
  const playing = cue && t >= cue.start - 0.05;
  let last: "read" | "now" | "next" = "next";
  const spans = words.map((w, i) => {
    if (w.text === "\n") return <br key={i} />;
    let state: "read" | "now" | "next";
    if (w.start === null) state = last === "now" ? "read" : last;
    else if (!playing) state = cue && t > cue.end ? "read" : "next";
    else {
      const nextStart = words.slice(i + 1).find((x) => x.start !== null)?.start ?? (w.end ?? 0) + 0.3;
      state = t >= Math.min(nextStart, (w.end ?? 0) + 0.35) ? "read" : t >= w.start - 0.04 ? "now" : "next";
    }
    last = state;
    const color = state === "read" ? INK : state === "now" ? SEAL : FAINT;
    const sep = lang === "en" && i > 0 && words[i - 1].text !== "\n" ? " " : "";
    return (
      <span key={i}>
        {sep}
        <span style={{ color, transition: "none", textDecoration: state === "now" ? `underline ${SEAL}` : undefined, textUnderlineOffset: size * 0.22, textDecorationThickness: Math.max(2, size * 0.05) }}>
          {w.text}
        </span>
      </span>
    );
  });
  return (
    <div style={{ fontFamily: lang === "zh" ? ZH : EN, fontSize: size, lineHeight: `${lineHeight}px`, textAlign: align, fontWeight: lang === "zh" ? 500 : 400, letterSpacing: lang === "zh" ? "0.06em" : 0 }}>
      {spans}
    </div>
  );
};

/** A size that keeps each of the verse's own lines on one line of the column (a scripture verse just wraps). */
const textSize = (words: Word[], lang: Lang) => {
  const lines: string[] = [""];
  for (const w of words) if (w.text === "\n") lines.push(""); else lines[lines.length - 1] += (lang === "en" && lines[lines.length - 1] ? " " : "") + w.text;
  const longest = Math.max(...lines.map((l) => l.length));
  const count = words.filter((w) => w.start !== null).length;
  if (lang === "zh") {
    const base = count <= 12 ? 50 : count <= 24 ? 44 : 38;
    return lines.length > 1 ? Math.min(base, Math.floor(COL.w / (longest * 1.08))) : base;
  }
  const base = count <= 16 ? 34 : count <= 24 ? 31 : 28;
  return lines.length > 1 ? Math.max(24, Math.min(base, Math.floor(COL.w / (longest * 0.47)))) : base;
};

const ChapterBar: FC<{ tl: ZhongYingTimeline; t: number }> = ({ tl, t }) => {
  const inset = 60;
  const width = 1920 - inset * 2;
  const x = (s: number) => inset + (s / tl.durationSeconds) * width;
  const gap = 6;
  const current = tl.chapters.findIndex((c) => t >= c.start && t < c.end);
  return (
    <>
      {tl.chapters.map((c, i) => {
        const left = x(c.start) + (i ? gap / 2 : 0);
        const right = x(c.end) - (i < tl.chapters.length - 1 ? gap / 2 : 0);
        const w = right - left;
        const on = i === current;
        const played = Math.max(0, Math.min(1, (t - c.start) / (c.end - c.start)));
        return (
          <div key={i}>
            <div style={{ position: "absolute", left, width: w, bottom: 36, textAlign: "center", whiteSpace: "nowrap", overflow: "hidden" }}>
              <div style={{ fontFamily: ZH, fontSize: 24, fontWeight: on ? 700 : 500, color: on ? INK : MUTED }}>{c.zh}</div>
              <div style={{ fontFamily: SANS, fontSize: 15, color: on ? SEAL : MUTED, opacity: on ? 1 : 0.85 }}>{c.en}</div>
            </div>
            <div style={{ position: "absolute", left, width: w, bottom: 16, height: 8, borderRadius: 4, background: LINE, overflow: "hidden" }}>
              <div style={{ width: `${played * 100}%`, height: "100%", background: on ? SEAL : "rgba(140, 110, 90, 0.55)" }} />
            </div>
          </div>
        );
      })}
      {current >= 0 && (
        <div style={{ position: "absolute", left: x(t) - 10, bottom: 25, width: 0, height: 0, borderLeft: "10px solid transparent", borderRight: "10px solid transparent", borderTop: `13px solid ${SEAL}` }} />
      )}
    </>
  );
};

const TitleCard: FC<{ tl: ZhongYingTimeline; t: number }> = ({ tl, t }) => {
  const end = tl.works[0].start;
  const o = window_(t, 0, end, 0.8, 0.9);
  const intro = tl.cues.filter((c) => c.kind === "intro");
  return (
    <AbsoluteFill style={{ opacity: o, alignItems: "center" }}>
      <div style={{ position: "absolute", top: 70, opacity: rise(t, 0.1, 0.9), transform: `scale(${0.92 + 0.08 * rise(t, 0.1, 0.9)})` }}>
        <Seal size={136} />
      </div>
      <div style={{ position: "absolute", top: 248, width: "100%", textAlign: "center", opacity: rise(t, 0.4, 1.2) }}>
        <div style={{ fontFamily: ZH, fontSize: 84, fontWeight: 700, color: INK, letterSpacing: "0.08em" }}>{tl.title.zh}</div>
        <div style={{ fontFamily: EN, fontSize: 44, fontStyle: "italic", color: INK, marginTop: 10 }}>{tl.title.en}</div>
        <div style={{ fontFamily: SANS, fontSize: 22, color: MUTED, marginTop: 26, letterSpacing: "0.04em" }}>By Lucas Academy Team</div>
      </div>
      <div style={{ position: "absolute", top: 600, width: 1500, left: 210, opacity: rise(t, intro[0].start - 0.5, intro[0].start) }}>
        <Words cue={intro[0]} words={intro[0].words} t={t} lang="zh" size={42} lineHeight={64} align="center" />
        <div style={{ height: 26 }} />
        <Words cue={intro[1]} words={intro[1].words} t={t} lang="en" size={33} lineHeight={48} align="center" />
      </div>
    </AbsoluteFill>
  );
};

const WorkPanel: FC<{ tl: ZhongYingTimeline; wi: number; t: number }> = ({ tl, wi, t }) => {
  const work = tl.works[wi];
  const o = window_(t, work.start, work.end, 0.7, 0.7);
  if (o <= 0) return null;
  const cues = tl.cues.filter((c) => c.kind === "verse" && c.work === wi);
  // The verse on screen: from its Chinese reading until the next verse's Chinese reading begins.
  const zhCues = cues.filter((c) => c.lang === "zh");
  let k = zhCues.findIndex((c, i) => t < (zhCues[i + 1]?.start ?? Infinity) - 0.25);
  if (k < 0) k = zhCues.length - 1;
  const unit = zhCues[k].unit;
  const zh = zhCues[k];
  const en = cues.find((c) => c.lang === "en" && c.unit === unit)!;
  // The work's title and author are read first (over the title already on screen); the first verse waits for them.
  // After the last work's last verse, the film's closing lines take the verse's place.
  const closing = tl.cues.filter((c) => c.kind === "closing" && c.work === wi);
  const closeAt = closing.length ? closing[0].start - 0.4 : work.end;
  const prevEnd = k > 0 ? zhCues[k].start - 0.25 : zhCues[0].start - 0.6;
  const nextStart = zhCues[k + 1] ? zhCues[k + 1].start - 0.25 : closeAt;
  const verseO = window_(t, prevEnd, nextStart, 0.35, k + 1 < zhCues.length ? 0.3 : 0.7);
  const zhSize = textSize(zh.words, "zh"),
    enSize = textSize(en.words, "en");
  return (
    <AbsoluteFill style={{ opacity: o }}>
      <div style={{ position: "absolute", left: COL.x, top: PIC.y + 4, width: COL.w }}>
        <div style={{ fontFamily: ZH, fontSize: 44, fontWeight: 700, color: INK, letterSpacing: "0.06em" }}>{work.title.zh}</div>
        <div style={{ fontFamily: EN, fontSize: 28, fontStyle: "italic", color: INK, marginTop: 4 }}>{work.title.en}</div>
        <div style={{ fontFamily: SANS, fontSize: 17, color: MUTED, marginTop: 8 }}>
          {work.by.zh} · {work.by.en}
        </div>
        <div style={{ width: 64, height: 2, background: SEAL, opacity: 0.7, marginTop: 22 }} />
      </div>
      <div style={{ position: "absolute", left: COL.x, top: 300, width: COL.w, opacity: verseO }}>
        <Words cue={zh} words={zh.words} t={t} lang="zh" size={zhSize} lineHeight={Math.round(zhSize * 1.55)} />
        <div style={{ height: Math.round(enSize * 0.9) }} />
        <Words cue={en} words={en.words} t={t} lang="en" size={enSize} lineHeight={Math.round(enSize * 1.42)} />
      </div>
      {closing.length === 2 && <Closing zh={closing[0]} en={closing[1]} t={t} o={window_(t, closeAt, work.end, 0.5, 0.7)} />}
    </AbsoluteFill>
  );
};

const Closing: FC<{ zh: Cue; en: Cue; t: number; o: number }> = ({ zh, en, t, o }) => {
  if (o <= 0) return null;
  const zhSize = textSize(zh.words, "zh"),
    enSize = textSize(en.words, "en");
  return (
    <div style={{ position: "absolute", left: COL.x, top: 300, width: COL.w, opacity: o }}>
      <Words cue={zh} words={zh.words} t={t} lang="zh" size={zhSize} lineHeight={Math.round(zhSize * 1.55)} />
      <div style={{ height: Math.round(enSize * 0.9) }} />
      <Words cue={en} words={en.words} t={t} lang="en" size={enSize} lineHeight={Math.round(enSize * 1.42)} />
    </div>
  );
};

const RecapPanel: FC<{ tl: ZhongYingTimeline; t: number }> = ({ tl, t }) => {
  const r = tl.recap!;
  const o = window_(t, r.start, r.end, 0.7, 0.7);
  const closing = tl.cues.filter((c) => c.kind === "closing");
  if (o <= 0 || closing.length !== 2) return null;
  return (
    <AbsoluteFill style={{ opacity: o }}>
      <div style={{ position: "absolute", left: COL.x, top: PIC.y + 4, width: COL.w }}>
        <div style={{ fontFamily: ZH, fontSize: 44, fontWeight: 700, color: INK, letterSpacing: "0.06em" }}>{tl.title.zh}</div>
        <div style={{ fontFamily: EN, fontSize: 28, fontStyle: "italic", color: INK, marginTop: 4 }}>{tl.title.en}</div>
        <div style={{ fontFamily: SANS, fontSize: 17, color: MUTED, marginTop: 8 }}>回顾 · Looking back</div>
        <div style={{ width: 64, height: 2, background: SEAL, opacity: 0.7, marginTop: 22 }} />
      </div>
      <Closing zh={closing[0]} en={closing[1]} t={t} o={rise(t, closing[0].start - 0.6, closing[0].start - 0.1)} />
    </AbsoluteFill>
  );
};

/** The end card: the seal and where to find the lessons, and the series' last line read under them (subscribe and
 * leave a comment; owner, 2026-10-28), lighting up as it is read. */
const EndCard: FC<{ tl: ZhongYingTimeline; t: number }> = ({ tl, t }) => {
  const o = rise(t, tl.endCardStart, tl.endCardStart + 1);
  if (o <= 0) return null;
  const [zh, en] = (["zh", "en"] as const).map((lang) => tl.cues.find((c) => c.kind === "subscribe" && c.lang === lang));
  return (
    <AbsoluteFill style={{ opacity: o, background: PAPER, alignItems: "center", justifyContent: "center" }}>
      <Seal size={132} />
      <div style={{ fontFamily: ZH, fontSize: 40, color: INK, marginTop: 34, letterSpacing: "0.08em" }}>语言的桥 · 看得见的诗</div>
      <div style={{ fontFamily: EN, fontSize: 30, fontStyle: "italic", color: INK, marginTop: 8 }}>Poems You Can See</div>
      <div style={{ fontFamily: SANS, fontSize: 26, color: SEAL, marginTop: 30, letterSpacing: "0.03em" }}>lang.lucasacademy.org</div>
      <div style={{ fontFamily: SANS, fontSize: 20, color: MUTED, marginTop: 40 }}>Lucas Academy</div>
      {zh && en && (
        <div style={{ width: 1240, marginTop: 64 }}>
          <Words cue={zh} words={zh.words} t={t} lang="zh" size={38} lineHeight={60} align="center" />
          <div style={{ height: 14 }} />
          <Words cue={en} words={en.words} t={t} lang="en" size={30} lineHeight={44} align="center" />
        </div>
      )}
    </AbsoluteFill>
  );
};

export const ZhongYingVideo: FC<ZhongYingProps> = ({ film, tl }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!tl) return <AbsoluteFill style={{ background: PAPER }} />;
  const t = frame / fps;
  const inWorks = t >= tl.works[0].start - 0.7 && t < tl.endCardStart + 1;
  const panelO = Math.min(rise(t, tl.works[0].start - 0.2, tl.works[0].start + 0.6), 1 - rise(t, tl.endCardStart, tl.endCardStart + 0.8));
  return (
    <AbsoluteFill style={{ background: PAPER }}>
      <Audio src={staticFile(`zhong-ying/${film}/narration.wav`)} />
      {t < tl.works[0].start + 0.1 && <TitleCard tl={tl} t={t} />}
      {inWorks && (
        <div
          style={{
            position: "absolute",
            left: PIC.x,
            top: PIC.y,
            width: PIC.w,
            height: PIC.h,
            opacity: panelO,
            background: "#f3eee3",
            boxShadow: "0 1px 2px rgba(60,45,30,.18), 0 12px 34px rgba(60,45,30,.14)",
            outline: "1px solid rgba(90,70,50,.18)",
          }}
        />
      )}
      {tl.works.map((w) => {
        const from = Math.round(w.start * fps);
        const frames = Math.round(w.end * fps) - from;
        return (
          <Sequence key={w.id} from={from} durationInFrames={frames}>
            <div style={{ position: "absolute", left: PIC.x, top: PIC.y, width: PIC.w, height: PIC.h, opacity: window_(t, w.start, w.end, 0.7, 0.7) }}>
              <OffthreadVideo src={staticFile(`zhong-ying/${film}/paint-${w.id}.mp4`)} muted style={{ width: PIC.w, height: PIC.h, display: "block" }} />
            </div>
          </Sequence>
        );
      })}
      {tl.recap && (
        <Sequence from={Math.round(tl.recap.start * fps)} durationInFrames={Math.round((tl.recap.end - tl.recap.start) * fps)}>
          <div style={{ position: "absolute", left: PIC.x, top: PIC.y, width: PIC.w, height: PIC.h, opacity: window_(t, tl.recap.start, tl.recap.end, 0.7, 0.7) }}>
            <OffthreadVideo src={staticFile(`zhong-ying/${film}/paint-recap.mp4`)} muted style={{ width: PIC.w, height: PIC.h, display: "block" }} />
          </div>
        </Sequence>
      )}
      {tl.works.map((_, wi) => (
        <WorkPanel key={wi} tl={tl} wi={wi} t={t} />
      ))}
      {tl.recap && <RecapPanel tl={tl} t={t} />}
      {inWorks && <Seal size={70} style={{ position: "absolute", left: COL.x + COL.w - 70, top: PIC.y + PIC.h - 70, opacity: panelO * 0.95 }} />}
      <EndCard tl={tl} t={t} />
      <div style={{ position: "absolute", inset: 0, opacity: t < tl.endCardStart ? 1 : 1 - rise(t, tl.endCardStart, tl.endCardStart + 0.8) }}>
        <ChapterBar tl={tl} t={t} />
      </div>
    </AbsoluteFill>
  );
};

// The cover (owner, 2026-10-27): 双语朗读 big, the film's title small, a clean icon. Not a question: for this series
// the owner wants viewers to see first that it is a bilingual read-aloud (ZHONG-YING.md §Cover). The picture is one
// work's painting, full size (cover.py copies the art lab's 1536 × 1024 original to cover-<work>.jpg).
// Layout "a" writes on the painting's open sky; "b" puts the words in a paper column beside it.
type CoverProps = { film: "climb-higher" | "little-boats" | "can-beauty-last"; lang: Lang; layout: "a" | "b" };
const COVERS: Record<CoverProps["film"], {
  art: string;
  title: Record<Lang, string>;
  sky: { left: number; top: number; width: number; zh: number; en: number; enLines: string[] };
  crop: string;
}> = {
  "climb-higher": {
    art: "foreign-lands",
    title: { zh: "爬高一点，看远一点", en: "Climb Higher, See Farther" },
    sky: { left: 700, top: 100, width: 1180, zh: 250, en: 170, enLines: ["Bilingual", "Read-Aloud"] },
    crop: "0% 0%",
  },
  "little-boats": {
    art: "where-go-the-boats",
    title: { zh: "小船去远方", en: "Little Boats, Far Away" },
    sky: { left: 0, top: 48, width: 1920, zh: 230, en: 150, enLines: ["Bilingual Read-Aloud"] },
    crop: "0% 0%",
  },
  "can-beauty-last": {
    art: "sonnet-18",
    title: { zh: "美好能否留存？", en: "Can Beauty Last?" },
    sky: { left: 740, top: 340, width: 1140, zh: 230, en: 160, enLines: ["Bilingual", "Read-Aloud"] },
    crop: "0% 0%",
  },
};
const HALO = "0 0 18px rgba(246, 241, 231, 0.55), 0 0 46px rgba(246, 241, 231, 0.45)";

const CoverTitle: FC<{ text: string; lang: Lang; size: number; seal: number }> = ({ text, lang, size, seal }) => (
  <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: Math.round(seal * 0.28) }}>
    <Seal size={seal} clean />
    <div style={{ fontFamily: lang === "zh" ? ZH : EN, fontSize: size, fontWeight: lang === "zh" ? 700 : 400, fontStyle: lang === "en" ? "italic" : undefined, color: INK, letterSpacing: lang === "zh" ? "0.06em" : 0 }}>
      {text}
    </div>
  </div>
);

export const ZhongYingCover: FC<CoverProps> = ({ film, lang, layout }) => {
  const c = COVERS[film];
  const art = staticFile(`zhong-ying/${film}/cover-${c.art}.jpg`);
  if (layout === "a") {
    const big = lang === "zh"
      ? <div style={{ fontFamily: ZH, fontSize: c.sky.zh, fontWeight: 900, lineHeight: 1.08, letterSpacing: "0.08em", marginRight: "-0.08em" }}>双语朗读</div>
      : c.sky.enLines.map((line) => <div key={line} style={{ fontFamily: EN, fontSize: c.sky.en, fontWeight: 700, lineHeight: 1.02 }}>{line}</div>);
    return (
      <AbsoluteFill style={{ background: PAPER }}>
        <Img src={art} style={{ position: "absolute", inset: 0, width: 1920, height: 1080, objectFit: "cover", objectPosition: c.crop }} />
        <div style={{ position: "absolute", left: c.sky.left, top: c.sky.top, width: c.sky.width, textAlign: "center", color: INK, textShadow: HALO }}>
          {big}
          <div style={{ marginTop: lang === "zh" ? 18 : 30 }}>
            <CoverTitle text={c.title[lang]} lang={lang} size={lang === "zh" ? 84 : 78} seal={100} />
          </div>
        </div>
      </AbsoluteFill>
    );
  }
  const [first, second] = lang === "zh" ? ["双语", "朗读"] : ["Bilingual", "Read-Aloud"];
  const word = lang === "zh"
    ? { fontFamily: ZH, fontSize: 300, fontWeight: 900, lineHeight: 1.1, letterSpacing: "0.04em", marginRight: "-0.04em" }
    : { fontFamily: EN, fontSize: 108, fontWeight: 700, lineHeight: 1.08 };
  return (
    <AbsoluteFill style={{ background: PAPER }}>
      <Img src={art} style={{ position: "absolute", left: 0, top: 0, width: 1180, height: 1080, objectFit: "cover", objectPosition: c.crop }} />
      <div style={{ position: "absolute", left: 1180, top: 0, width: 740, height: 1080, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
        <div style={{ ...word, color: INK }}>{first}</div>
        <div style={{ ...word, color: SEAL }}>{second}</div>
        <div style={{ marginTop: 56 }}>
          <CoverTitle text={c.title[lang]} lang={lang} size={lang === "zh" ? 46 : 42} seal={70} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** The seal alone, large, for checking it. */
export const ZhongYingSeal: FC = () => (
  <AbsoluteFill style={{ background: PAPER, alignItems: "center", justifyContent: "center" }}>
    <Seal size={600} />
  </AbsoluteFill>
);
