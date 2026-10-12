import {
  useEffect,
  useContext,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type FC,
  type ReactNode,
} from "react";
import {
  AbsoluteFill,
  Audio,
  Freeze,
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
import { rampAt } from "../../lib/timeRamps";
import type { PlaybackPlan } from "./playback";
import { SHOTS, type Shot } from "./shots";
import { FilmLanguage, L, type Language } from "./localization";

type Cue = {
  id: string;
  section: string;
  zh: string;
  en: string;
  start: number;
  end: number;
  speech: { start: number; end: number };
};
type RampKey = [number, number, number];
type Event = {
  time: number;
  shownAt?: number;
  action: string;
  word?: string;
  value: string;
  stepIndex: number;
  unitIndex: number;
};
type Recording = {
  events: Event[];
  videoStartOffsetSeconds: number;
  simulated: boolean;
};
export type ClaudeTimeline = {
  lang: Language;
  fps: number;
  durationSeconds: number;
  endCardStart: number;
  cues: Cue[];
  draft: boolean;
  playback: Record<string, PlaybackPlan>;
  markers?: Record<string, Record<string, number>>;
  musicExample?: {
    start: number;
    end: number;
    sourceStart: number;
    sourceEnd: number;
  };
  images: string[];
  art: string[];
  footage: string[];
  footageSeconds: Record<string, number>;
  recordings: Record<string, Recording>;
};
export type ClaudeProps = { tl?: ClaudeTimeline | null; lang?: Language };
const DIR = "fun-informatics-02";
const FONT = '"PingFang SC", "Hiragino Sans GB", sans-serif';
const EN = '"Avenir Next", "Helvetica Neue", sans-serif';
const GREEN = "#b5dabd",
  GOLD = "#efcc89",
  WHITE = "#fffdf4",
  SOFT = "#d5dcd1";
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const ease = (t: number) => {
  const x = Math.max(0, Math.min(1, t));
  return x * x * (3 - 2 * x);
};
const file = (p: string) => staticFile(`${DIR}/${p}`);
const glass: CSSProperties = {
  boxSizing: "border-box",
  background: "linear-gradient(145deg,rgba(12,40,35,.84),rgba(11,30,31,.8))",
  border: "1px solid rgba(212,234,205,.38)",
  borderRadius: 26,
  boxShadow: "0 20px 70px rgba(0,0,0,.25)",
  backdropFilter: "blur(18px)",
  color: WHITE,
};
export const calculateClaudeMetadata: CalculateMetadataFunction<
  ClaudeProps
> = async ({ props, abortSignal }) => {
  const response = await fetch(file(`timeline.${props.lang ?? "zh"}.json`), {
    signal: abortSignal,
  });
  if (!response.ok) throw Error("Run fi02:timeline first");
  const tl = (await response.json()) as ClaudeTimeline;
  return {
    props: { ...props, tl },
    fps: tl.fps,
    durationInFrames: Math.ceil(tl.durationSeconds * tl.fps),
  };
};

const Tag: FC<{ children: ReactNode; style?: CSSProperties }> = ({
  children,
  style,
}) => (
  <div
    style={{
      ...glass,
      padding: "10px 20px",
      fontSize: 24,
      borderRadius: 99,
      ...style,
    }}
  >
    <L>{children}</L>
  </div>
);
const Card: FC<{ children: ReactNode; style?: CSSProperties }> = ({
  children,
  style,
}) => (
  <div style={{ ...glass, padding: 44, ...style }}>
    <L>{children}</L>
  </div>
);
const Center: FC<{ children: ReactNode }> = ({ children }) => (
  <AbsoluteFill
    style={{
      alignItems: "center",
      justifyContent: "center",
      flexDirection: "row",
      padding: "100px 100px 150px",
    }}
  >
    <L>{children}</L>
  </AbsoluteFill>
);
const Heading: FC<{ small?: string; children: ReactNode }> = ({
  small,
  children,
}) => (
  <>
    <div
      style={{
        fontFamily: EN,
        fontSize: 24,
        letterSpacing: 4,
        color: GREEN,
        marginBottom: 20,
      }}
    >
      <L>{small}</L>
    </div>
    <div style={{ fontSize: 68, fontWeight: 650, lineHeight: 1.3 }}>
      <L>{children}</L>
    </div>
  </>
);
const Note: FC<{ children: ReactNode; style?: CSSProperties }> = ({
  children,
  style,
}) => (
  <div
    style={{
      position: "absolute",
      right: 54,
      bottom: 120,
      fontSize: 22,
      color: SOFT,
      ...glass,
      padding: "9px 16px",
      ...style,
    }}
  >
    <L>{children}</L>
  </div>
);

/** Full artwork uses its original ratio; only its blurred copy fills the margins. */
const Art: FC<{
  src: string;
  zoom?: number;
  dim?: number;
  caption?: string;
}> = ({ src, zoom = 1, dim = 0, caption }) => (
  <AbsoluteFill style={{ overflow: "hidden", background: "#16372e" }}>
    <Img
      src={file(src)}
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        objectFit: "cover",
        filter: "blur(40px)",
        transform: "scale(1.1)",
        opacity: 0.7,
      }}
    />
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${zoom})`,
      }}
    >
      <Img
        src={file(src)}
        style={{ width: "100%", height: "100%", objectFit: "contain" }}
      />
    </AbsoluteFill>
    <L>
      {dim > 0 && (
        <AbsoluteFill style={{ background: `rgba(3,17,18,${dim})` }} />
      )}
    </L>
    <L>
      {caption && (
        <div
          style={{
            position: "absolute",
            left: 54,
            bottom: 120,
            ...glass,
            padding: "10px 18px",
            fontSize: 22,
          }}
        >
          {caption}
        </div>
      )}
    </L>
  </AbsoluteFill>
);

const Still: FC<{ name: string; dim?: number }> = ({ name, dim = 0 }) => (
  <AbsoluteFill>
    <Img
      src={file(`images/${name}.png`)}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
    <L>
      {dim > 0 && (
        <AbsoluteFill style={{ background: `rgba(3,17,18,${dim})` }} />
      )}
    </L>
    <Note style={{ left: 54, right: "auto" }}>
      <L>AI 生成</L>
    </Note>
  </AbsoluteFill>
);
const Dissolve: FC<{
  name: string;
  at?: number;
  length?: number;
  time: number;
}> = ({ name, at = 2, length = 2.5, time }) => (
  <AbsoluteFill>
    <Img
      src={file(`images/${name}-photo.png`)}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
    <AbsoluteFill style={{ opacity: ease((time - at) / length) }}>
      <Img
        src={file(`images/${name}-monet.png`)}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
    </AbsoluteFill>
    <Note>
      <L>AI 生成 · 同构图实景／莫奈风</L>
    </Note>
  </AbsoluteFill>
);

const Portrait: FC<{
  name: string;
  sub: string;
  src?: string;
  question?: boolean;
  style?: CSSProperties;
}> = ({ name, sub, src, question, style }) => (
  <Card
    style={{
      width: 490,
      height: 680,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      gap: 24,
      ...style,
    }}
  >
    <L>
      {src ? (
        <Img
          src={file(src)}
          style={{
            width: 360,
            height: 420,
            objectFit: "contain",
            borderRadius: 10,
          }}
        />
      ) : (
        <div
          style={{ fontFamily: EN, fontSize: 240, color: GOLD, lineHeight: 1 }}
        >
          {question ? "?" : "Claude"}
        </div>
      )}
    </L>
    <div style={{ fontSize: 48, fontWeight: 650 }}>
      <L>{name}</L>
    </div>
    <div style={{ fontFamily: EN, fontSize: 28, color: GREEN }}>
      <L>{sub}</L>
    </div>
  </Card>
);

const Lifelines: FC<{ three?: boolean; time: number }> = ({
  three = false,
  time,
}) => {
  const lines = three
    ? [
        ["莫奈", 1840, 1926],
        ["德彪西", 1862, 1918],
        ["香农", 1916, 2001],
      ]
    : [
        ["莫奈", 1840, 1926],
        ["香农", 1916, 2001],
      ];
  const x = (year: number) => ((year - 1835) / 170) * 1330;
  return (
    <Center>
      <Card style={{ width: 1640 }}>
        <Heading small="A MOMENT IN COMMON">
          <L>{three ? "三位人类 Claude" : "他们在同一个世界里"}</L>
        </Heading>
        <div
          style={{
            position: "relative",
            height: three ? 430 : 345,
            marginTop: 55,
            marginLeft: 130,
          }}
        >
          <div
            style={{
              position: "absolute",
              left: x(1916),
              width: x(three ? 1918 : 1926) - x(1916),
              top: 0,
              bottom: 35,
              background: "rgba(239,204,137,.27)",
              borderLeft: `2px solid ${GOLD}`,
              borderRight: `2px solid ${GOLD}`,
            }}
          />
          <L>
            {lines.map(([name, a, b], i) => (
              <div
                key={name}
                style={{
                  position: "absolute",
                  left: 0,
                  top: i * 125,
                  width: 1330,
                  opacity: ease(time / 1.2 - i * 0.18),
                }}
              >
                <div
                  style={{
                    position: "absolute",
                    left: -130,
                    fontSize: 36,
                    top: 6,
                  }}
                >
                  {name}
                </div>
                <div
                  style={{
                    position: "absolute",
                    left: x(Number(a)),
                    width: x(Number(b)) - x(Number(a)),
                    height: 48,
                    background: i === 0 ? GREEN : i === 1 ? GOLD : "#a6cbd3",
                    borderRadius: 8,
                  }}
                />
                <div
                  style={{
                    position: "absolute",
                    left: x(Number(a)),
                    top: 60,
                    fontFamily: EN,
                    fontSize: 27,
                  }}
                >
                  {a}
                </div>
                <div
                  style={{
                    position: "absolute",
                    left: x(Number(b)) - 75,
                    top: 60,
                    fontFamily: EN,
                    fontSize: 27,
                  }}
                >
                  {b}
                </div>
              </div>
            ))}
          </L>
        </div>
        <div style={{ fontSize: 38, color: GOLD, textAlign: "center" }}>
          <L>
            {three ? "1916—1918 · 画画／作曲／刚出生" : "1916—1926 · 十年重叠"}
          </L>
        </div>
      </Card>
    </Center>
  );
};

const Chat: FC<{ cue: Cue; now: number; compact?: boolean }> = ({
  cue,
  now,
  compact = false,
}) => {
  const lang = useContext(FilmLanguage);
  const fraction = Math.max(
    0,
    Math.min(
      1,
      (now - cue.speech.start) /
        Math.max(1, cue.speech.end - cue.speech.start - 0.5),
    ),
  );
  const full = cue[lang];
  const typed = full.slice(0, Math.ceil(full.length * fraction));
  const text =
    lang === "en" && fraction < 1 ? typed.replace(/\s+\S*$/, "") : typed;
  return (
    <Card
      style={{
        position: "absolute",
        left: compact ? (lang === "en" ? 1050 : 1120) : 240,
        top: compact ? 645 : 300,
        width: compact ? (lang === "en" ? 780 : 710) : 1440,
        padding: compact ? 24 : 48,
      }}
    >
      <div
        style={{
          fontFamily: EN,
          color: GOLD,
          fontSize: compact ? 26 : 36,
          marginBottom: compact ? 8 : 20,
        }}
      >
        Claude
      </div>
      <div
        style={{
          fontSize: compact ? 27 : 48,
          lineHeight: lang === "en" ? 1.45 : 1.55,
          minHeight: compact ? 80 : 190,
        }}
      >
        <L>{text}</L>
        <span
          style={{ color: GREEN, opacity: Math.floor(now * 2) % 2 ? 1 : 0.3 }}
        >
          ▏
        </span>
      </div>
    </Card>
  );
};

const VideoAt: FC<{
  tl: ClaudeTimeline;
  name: string;
  keys: RampKey[];
  time: number;
}> = ({ tl, name, keys, time }) => {
  const source = Math.max(
    0,
    Math.min((tl.footageSeconds[name + ".mp4"] ?? 1) - 0.1, rampAt(keys, time)),
  );
  return (
    <AbsoluteFill style={{ overflow: "hidden", borderRadius: 20 }}>
      <Freeze frame={0}>
        <OffthreadVideo
          src={file(`footage/${name}.mp4`)}
          muted
          trimBefore={Math.round(source * tl.fps)}
          style={{ width: "100%", height: "100%", objectFit: "contain" }}
        />
      </Freeze>
    </AbsoluteFill>
  );
};

const LetterCard: FC<{
  language: "en" | "zh";
  time: number;
  length: number;
  firstAt?: number;
  secondAt?: number;
}> = ({ language, time, length, firstAt, secondAt }) => {
  const zh = language === "zh";
  const l = zh ? "神爱世" : "For God so loved the wor";
  const options = zh
    ? ["界", "代", "上", "人"]
    : time < (secondAt !== undefined ? secondAt - 0.4 : length * 0.5)
      ? ["l", "r", "m", "n"]
      : ["d", "t", "s", "k"];
  const firstLetter = time >= (firstAt ?? length * 0.35);
  const secondStep =
    time >= (secondAt !== undefined ? secondAt - 0.4 : length * 0.5);
  const reveal = time >= (secondAt ?? length * 0.8);
  const selected = zh
    ? reveal
      ? "人"
      : undefined
    : secondStep
      ? reveal
        ? "d"
        : undefined
      : firstLetter
        ? "l"
        : undefined;
  const text = zh
    ? l + (reveal ? "人" : "＿")
    : l + (reveal ? "ld" : firstLetter ? "l＿" : "＿＿");
  return (
    <Card
      style={{
        width: "100%",
        height: "100%",
        padding: "26px 42px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
      }}
    >
      <div
        style={{ fontSize: 58, fontFamily: zh ? FONT : EN, marginBottom: 25 }}
      >
        <L>{text}</L>
      </div>
      <div style={{ display: "flex", gap: 25 }}>
        <L>
          {options.map((o) => (
            <div
              key={o}
              style={{
                border: `2px solid ${o === selected ? GOLD : GREEN}`,
                background:
                  o === selected ? "rgba(239,204,137,.24)" : "transparent",
                borderRadius: 14,
                width: 120,
                height: 78,
                textAlign: "center",
                fontSize: 48,
                lineHeight: "74px",
                color: WHITE,
              }}
            >
              {o}
            </div>
          ))}
        </L>
      </div>
      <div
        style={{
          fontSize: 20,
          color: SOFT,
          position: "absolute",
          right: 26,
          bottom: 16,
        }}
      >
        <L>单字符选择 · 教学示意</L>
      </div>
    </Card>
  );
};

const GuessSplit: FC<{
  tl: ClaudeTimeline;
  first: Cue;
  last: Cue;
  time: number;
  unfamiliar?: boolean;
}> = ({ tl, first, last, time, unfamiliar = false }) => {
  const start = first.start,
    total = last.end - start;
  const cue = (id: string) => tl.cues.find((c) => c.id === id)!;
  const target4 = unfamiliar ? 0 : cue("cl03-04").start - start;
  const target5 = unfamiliar ? 0 : cue("cl03-05").start - start;
  const target6 = unfamiliar ? 0 : cue("cl03-06").start - start;
  const names = unfamiliar
    ? ["letters-pro2511-en", "letters-pro2511-zh"]
    : ["letters-jhn316-en", "letters-jhn316-zh"];
  return (
    <AbsoluteFill style={{ padding: "46px 70px 112px", gap: 24 }}>
      <div style={{ fontSize: 30, color: GREEN }}>
        bible.lucasacademy.org　·　
        <L>
          {unfamiliar
            ? "箴言 25:11 · 模拟试错"
            : "约翰福音 3:16 · 一个字母／一个汉字"}
        </L>
      </div>
      <L>
        {names.map((name, index) => {
          const recording = tl.recordings[name];
          const keys = tl.playback[name].keys;
          const demo = !unfamiliar && time >= target4 && time < target6;
          const demoStart = index === 0 ? target4 : target5;
          const demoLength =
            index === 0 ? target5 - target4 : target6 - target5;
          return (
            <div
              key={name}
              style={{
                position: "relative",
                height: 384,
                width: 1780,
                flexShrink: 0,
                ...glass,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  left: 20,
                  top: 12,
                  zIndex: 2,
                  fontFamily: EN,
                  fontSize: 21,
                  color: GREEN,
                  ...glass,
                  padding: "5px 13px",
                }}
              >
                {" "}
                {index === 0 ? "ENGLISH · LETTERS" : "中文 · 猜字"}
              </div>
              {demo ? (
                index === 0 && time >= target5 ? (
                  <LetterCard language="en" time={100} length={1} />
                ) : index === 1 && time < target5 ? (
                  <LetterCard language="zh" time={0} length={1} />
                ) : (
                  <LetterCard
                    language={index === 0 ? "en" : "zh"}
                    time={time - demoStart}
                    length={Math.max(1, demoLength)}
                    firstAt={
                      tl.lang === "en" && index === 0
                        ? (tl.markers?.["cl03-04"]?.["letter-l"] ??
                            cue("cl03-04").speech.start + 3) -
                          start -
                          demoStart
                        : undefined
                    }
                    secondAt={
                      tl.lang === "en" && index === 0
                        ? (tl.markers?.["cl03-04"]?.["letter-d"] ??
                            cue("cl03-04").speech.start + 4) -
                          start -
                          demoStart
                        : undefined
                    }
                  />
                )
              ) : recording ? (
                <VideoAt tl={tl} name={name} keys={keys} time={time} />
              ) : null}
            </div>
          );
        })}
      </L>
    </AbsoluteFill>
  );
};

const Probability: FC<{ surprise?: boolean; time: number }> = ({
  surprise = false,
  time,
}) => (
  <Card
    style={{
      position: "absolute",
      left: 100,
      top: 120,
      width: 1500,
      height: 505,
    }}
  >
    <Heading small="ILLUSTRATION">
      <L>{surprise ? "越有可能，越不意外" : "候选词的概率"}</L>
    </Heading>
    <div
      style={{
        display: "flex",
        alignItems: "end",
        gap: 70,
        height: 205,
        marginTop: 20,
      }}
    >
      <L>
        {[
          ["苹果", 0.62],
          ["面包", 0.24],
          ["书", 0.1],
          ["天空", 0.04],
        ].map(([label, p]) => (
          <div key={label} style={{ width: 200, textAlign: "center" }}>
            <div
              style={{
                fontFamily: EN,
                fontSize: 32,
                color: GOLD,
                marginBottom: 10,
              }}
            >
              {Math.round(Number(p) * 100)}%
            </div>
            <div
              style={{
                height: 180 * Number(p) * ease(time / 1.2) + 6,
                background: GREEN,
                borderRadius: "12px 12px 0 0",
              }}
            />
            <div style={{ fontSize: 35, marginTop: 14 }}>{label}</div>
          </div>
        ))}
      </L>
    </div>
    <div style={{ fontSize: 22, color: SOFT, marginTop: 28 }}>
      <L>示意 · 实际模型预测 token，候选来自词表；生成也可以按概率采样</L>
    </div>
  </Card>
);

const PixelLoss: FC<{ time: number; duration: number }> = ({
  time,
  duration,
}) => {
  const ref = useRef<HTMLCanvasElement>(null);
  const [bitmap, setBitmap] = useState<HTMLImageElement | null>(null);
  const [handle] = useState(() =>
    delayRender("Load bridge for pixel demonstration"),
  );
  useEffect(() => {
    const image = new Image();
    image.onload = () => {
      setBitmap(image);
      continueRender(handle);
    };
    image.onerror = () => continueRender(handle);
    image.src = file("art/monet-bridge-1899.jpg");
  }, [handle]);
  const n = Math.max(
    3,
    Math.round(interpolate(time, [0, duration * 0.7], [65, 3], clamp)),
  );
  useLayoutEffect(() => {
    const canvas = ref.current;
    if (!canvas || !bitmap) return;
    canvas.width = n;
    canvas.height = Math.round((n * bitmap.height) / bitmap.width);
    canvas
      .getContext("2d")!
      .drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  }, [bitmap, n]);
  return (
    <Center>
      <div style={{ height: 790, width: 640, position: "relative" }}>
        <canvas
          ref={ref}
          style={{ height: "100%", width: "100%", imageRendering: "pixelated" }}
        />
      </div>
      <Card style={{ marginLeft: 90, width: 700 }}>
        <Heading small="HOW MUCH CAN GO?">
          <L>{time < duration * 0.6 ? "细节越来越少" : "只剩几块颜色"}</L>
        </Heading>
        <div style={{ fontSize: 34, color: GREEN, marginTop: 30 }}>
          <L>冗余可以去掉</L>
          <br />
          <L>信息也丢了，就认不出了</L>
        </div>
      </Card>
    </Center>
  );
};

type SceneProps = { tl: ClaudeTimeline; shot: Shot; first: Cue; last: Cue };
const Scene: FC<SceneProps> = ({ tl, shot, first, last }) => {
  const english = tl.lang === "en";
  const frame = useCurrentFrame(),
    { fps } = useVideoConfig();
  const time = frame / fps,
    now = first.start + time,
    duration = last.end - first.start;
  const current = tl.cues.find((c) => c.start <= now && c.end > now) ?? last;
  const at = (id: string) =>
    tl.cues.find((c) => c.id === id)!.start - first.start;
  const local = (id: string) =>
    now - tl.cues.find((c) => c.id === id)!.speech.start;
  const pond = "art/water-lilies-1906.jpg";
  const background = <Art src={pond} dim={0.69} />;
  let visual: ReactNode = background;
  switch (shot.kind) {
    case "pond-open": {
      const begin = at("cl00-02"),
        end = at("cl00-03");
      const q = ease((time - begin) / (end - begin));
      visual = (
        <Art
          src={pond}
          zoom={Math.exp(Math.log(7) * (1 - q))}
          caption={q > 0.98 ? "Claude Monet · Water Lilies · 1906" : undefined}
        />
      );
      break;
    }
    case "pond-return":
      visual = (
        <Art
          src={pond}
          zoom={Math.exp(Math.log(4) * (1 - ease(time / (duration * 0.75))))}
        />
      );
      break;
    case "blanks": {
      const show = current.id === "cl00-05",
        q = show ? local("cl00-05") : 0;
      if (english) {
        visual = (
          <>
            {background}
            <Center>
              <Card style={{ width: 1640 }}>
                <div style={{ fontSize: 63, lineHeight: 1.7 }}>
                  Emma pulled on her{" "}
                  <span style={{ color: GOLD }}>
                    {q > 1.5 ? "shoes" : "sho__"}
                  </span>
                  <br />
                  and stepped out into the{" "}
                  <span style={{ color: GOLD }}>{q > 3 ? "rain" : "ra__"}</span>
                  .<br />
                  Beside the gate, she spotted a{" "}
                  <span style={{ color: GOLD }}>
                    {q > 5
                      ? ["cat", "dog", "fox"][Math.floor((q - 5) / 1.6) % 3]
                      : "___"}
                  </span>
                  .
                </div>
              </Card>
            </Center>
          </>
        );
        break;
      }
      visual = (
        <>
          <Still name="schoolbag-cat-monet" dim={0.3} />
          <Center>
            <Card style={{ width: 1640 }}>
              <div style={{ fontSize: 64, lineHeight: 1.65 }}>
                <L>小明背着书</L>
                <span style={{ color: GOLD }}>
                  <L>{q > 1.5 ? "包" : "＿"}</L>
                </span>
                <L>去上学，</L>
                <br />
                <L>路</L>
                <span style={{ color: GOLD }}>
                  <L>{q > 3 ? "上" : "＿"}</L>
                </span>
                <L>看见一只小</L>
                <span style={{ color: GOLD }}>
                  <L>
                    {q > 5
                      ? ["猫", "狗", "鸟"][Math.floor((q - 5) / 1.6) % 3]
                      : "＿"}
                  </L>
                </span>
                。
              </div>
            </Card>
          </Center>
        </>
      );
      break;
    }
    case "redundancy":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <div style={{ display: "flex", gap: 55 }}>
              <Card style={{ width: 730 }}>
                <Heading small="REDUNDANCY">
                  <L>猜得到的 · 冗余</L>
                </Heading>
                <div style={{ fontSize: 38, color: GREEN, marginTop: 32 }}>
                  <L>书包　路上</L>
                </div>
              </Card>
              <Card style={{ width: 730 }}>
                <Heading small="INFORMATION">
                  <L>猜不到的 · 信息</L>
                </Heading>
                <div style={{ fontSize: 38, color: GOLD, marginTop: 32 }}>
                  <L>猫？　狗？　鸟？</L>
                </div>
              </Card>
            </div>
          </Center>
        </>
      );
      break;
    case "title":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <div>
              <div style={{ fontSize: 116, fontWeight: 700, lineHeight: 1.27 }}>
                <L>你认识</L>
                <br />
                <span style={{ fontFamily: EN, color: GOLD }}>Claude</span>
                <L> 吗？</L>
              </div>
              <div
                style={{
                  fontFamily: EN,
                  fontSize: 33,
                  color: GREEN,
                  marginTop: 30,
                }}
              >
                {english ? "Fun Informatics 2" : "Do You Know Claude?"}
              </div>
              <div style={{ fontSize: 27, color: SOFT, marginTop: 58 }}>
                <L>作者 Yancy Qin, Louise Yang | Lucas Academy</L>
              </div>
            </div>
          </Center>
        </>
      );
      break;
    case "introductions":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <div style={{ display: "flex", gap: 70 }}>
              <Portrait
                name="克劳德·莫奈"
                sub="Claude Monet · 1840—1926"
                src="art/monet-nadar-1899.jpg"
              />
              <Portrait
                name="克劳德·香农"
                sub="Claude Shannon · 1916—2001"
                src="images/unicycle-juggler-monet.png"
                style={{ opacity: current.id === "cl01-02" ? 1 : 0.25 }}
              />
            </div>
          </Center>
          <Note>
            <L>独轮车插图 · AI 生成</L>
          </Note>
        </>
      );
      break;
    case "lifelines":
      visual = (
        <>
          <L>{background}</L>
          <Lifelines time={time} />
        </>
      );
      break;
    case "mystery":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <Portrait name="第三个 Claude" sub="稍后揭晓" question />
          </Center>
        </>
      );
      break;
    case "photography":
      visual = (
        <>
          <Art
            src="art/daguerre-boulevard.jpg"
            dim={0.12}
            caption="Louis Daguerre · Boulevard du Temple · 1838"
          />
          <div style={{ position: "absolute", top: 55, left: 65 }}>
            <Tag>
              <L>1839 · 照相术公开问世　→　1840 · 莫奈出生</L>
            </Tag>
          </div>
        </>
      );
      break;
    case "sunrise":
      visual = (
        <>
          <Art
            src="art/impression-sunrise.jpg"
            caption="Claude Monet · Impression, soleil levant · 1872"
          />
          <L>
            {current.id === "cl02-05" || current.id === "cl02-06" ? (
              <div style={{ position: "absolute", right: 70, top: 70 }}>
                <Card>
                  <div style={{ fontSize: 58, color: GOLD }}>
                    {current.id === "cl02-05"
                      ? "不过是个「印象」！"
                      : "「印象派」"}
                  </div>
                  <div style={{ fontSize: 28, marginTop: 15 }}>
                    1874 · 从一个名字开始
                  </div>
                </Card>
              </div>
            ) : null}
          </L>
        </>
      );
      break;
    case "bridge": {
      const q = ease((time - at("cl02-09")) / 2);
      const z =
        current.id === "cl02-09"
          ? 1 +
            2 *
              ease(
                local("cl02-09") /
                  Math.max(1, current.end - current.speech.start),
              )
          : current.id === "cl02-10"
            ? 3 -
              2 *
                ease(
                  local("cl02-10") /
                    Math.max(1, current.end - current.speech.start),
                )
            : 1;
      visual = (
        <>
          <L>{background}</L>
          <div
            style={{
              position: "absolute",
              left: 80,
              top: 90,
              width: 820,
              height: 820,
              opacity: 1 - q,
            }}
          >
            <Art
              src="images/giverny-bridge-photo.png"
              caption="日本桥实景 · AI 还原"
            />
          </div>
          <div
            style={{
              position: "absolute",
              left: interpolate(q, [0, 1], [1010, 0]),
              top: interpolate(q, [0, 1], [90, 0]),
              width: interpolate(q, [0, 1], [820, 1920]),
              height: interpolate(q, [0, 1], [820, 1080]),
              overflow: "hidden",
            }}
          >
            <Art
              src="art/monet-bridge-1899.jpg"
              zoom={z}
              caption="Claude Monet · 日本桥 · 1899"
            />
            <L>
              {current.id === "cl02-08" && (
                <div
                  style={{
                    position: "absolute",
                    left:
                      time - at("cl02-08") < 2
                        ? "25%"
                        : time - at("cl02-08") < 4
                          ? "45%"
                          : "30%",
                    top:
                      time - at("cl02-08") < 2
                        ? "23%"
                        : time - at("cl02-08") < 4
                          ? "38%"
                          : "68%",
                    width: 160,
                    height: 110,
                    border: `5px solid ${GOLD}`,
                    borderRadius: "50%",
                  }}
                />
              )}
            </L>
          </div>
        </>
      );
      break;
    }
    case "everyday": {
      const c = tl.cues.find((c) => c.id === "cl02-12")!;
      const marker = (phrase: string) =>
        tl.markers?.[c.id]?.[phrase] ??
        c.speech.start +
          ((c.speech.end - c.speech.start) * c.zh.indexOf(phrase)) /
            c.zh.length;
      const galleryAt = marker("这是街道") - first.start;
      const segment = galleryAt / 3;
      if (time < galleryAt) {
        const i = Math.min(2, Math.floor(time / segment));
        visual = (
          <Dissolve
            name={["street", "playground", "seaside"][i]}
            time={time - i * segment}
            at={Math.min(1, segment * 0.2)}
            length={Math.min(2.5, segment * 0.6)}
          />
        );
      } else {
        const active =
          now >= marker("这是海边") ? 2 : now >= marker("这是操场") ? 1 : 0;
        visual = (
          <>
            <L>{background}</L>
            <div
              style={{
                position: "absolute",
                left: 70,
                top: 250,
                display: "flex",
                gap: 28,
              }}
            >
              <L>
                {["street", "playground", "seaside"].map((name, i) => (
                  <Card
                    key={name}
                    style={{
                      width: 573,
                      padding: 18,
                      opacity: i === active ? 1 : 0.6,
                      borderColor: i === active ? GOLD : GREEN,
                    }}
                  >
                    <Img
                      src={file(`images/${name}-monet.png`)}
                      style={{
                        width: "100%",
                        aspectRatio: "16/9",
                        objectFit: "contain",
                        borderRadius: 12,
                      }}
                    />
                    <div
                      style={{
                        fontSize: 46,
                        textAlign: "center",
                        marginTop: 24,
                        color: i === active ? GOLD : WHITE,
                      }}
                    >
                      {["街道", "操场", "海边"][i]}
                    </div>
                  </Card>
                ))}
              </L>
            </div>
            <Note>
              <L>AI 生成 · 实景与莫奈风保持同一构图</L>
            </Note>
          </>
        );
      }
      break;
    }
    case "stacks":
      visual = (
        <>
          <L>{background}</L>
          <div
            style={{
              position: "absolute",
              inset: "120px 50px 175px",
              display: "flex",
              gap: 30,
            }}
          >
            <L>
              {[
                ["summer", "夏末"],
                ["autumn", "秋日暮色"],
                ["snow", "落日 · 雪"],
              ].map(([name, label], i) => (
                <div
                  key={name}
                  style={{
                    flex: 1,
                    position: "relative",
                    opacity:
                      current.id === "cl02-14" &&
                      Math.floor(local("cl02-14") / 2.5) % 3 !== i
                        ? 0.45
                        : 1,
                  }}
                >
                  <Art src={`art/stacks-${name}.jpg`} />
                  <div style={{ position: "absolute", bottom: 20, left: 20 }}>
                    <Tag>{label} · 1890—91</Tag>
                  </div>
                </div>
              ))}
            </L>
          </div>
          <div
            style={{
              position: "absolute",
              left: 65,
              top: 45,
              fontSize: 39,
              color: GOLD,
            }}
          >
            <L>同样的草堆，不一样的光</L>
          </div>
        </>
      );
      break;
    case "pixel-loss":
      visual = (
        <>
          <L>{background}</L>
          <PixelLoss time={time} duration={duration} />
        </>
      );
      break;
    case "unicycle":
      visual = <Still name="unicycle-juggler-monet" />;
      break;
    case "book-letters": {
      const count = Math.min(12, Math.floor(time * 0.65));
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <Card style={{ width: 1620 }}>
              <Heading small="CLAUDE SHANNON">
                <L>遮住后面的字母，再猜一个</L>
              </Heading>
              <div
                style={{
                  fontFamily: EN,
                  fontSize: 79,
                  marginTop: 60,
                  letterSpacing: 6,
                }}
              >
                INFORMATION
                <span style={{ background: "#223d33", color: "#223d33" }}>
                  <L> </L>
                  THEORY
                </span>
              </div>
              <div style={{ fontSize: 36, color: GOLD, marginTop: 35 }}>
                I N F O R M A T I O N　→　?
              </div>
              <div style={{ fontSize: 24, color: SOFT, marginTop: 28 }}>
                <L>受香农猜下一个字母的实验启发 · 游戏是教学简化</L>
              </div>
            </Card>
          </Center>
        </>
      );
      void count;
      break;
    }
    case "letters":
      visual = (
        <>
          <L>{background}</L>
          <GuessSplit tl={tl} first={first} last={last} time={time} />
        </>
      );
      break;
    case "unfamiliar":
      visual = (
        <>
          <Still name="golden-apples-monet" dim={0.6} />
          <GuessSplit
            tl={tl}
            first={first}
            last={last}
            time={time}
            unfamiliar
          />
        </>
      );
      break;
    case "listener":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <Card style={{ width: 1480, textAlign: "center" }}>
              <Heading small="THE LISTENER MATTERS">
                <L>同一句话，不同的听众</L>
              </Heading>
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  gap: 85,
                  marginTop: 65,
                  fontSize: 47,
                }}
              >
                <div>
                  <L>已经记在心里</L>
                  <br />
                  <span style={{ fontSize: 32, color: GREEN }}>
                    <L>能猜到</L>
                  </span>
                </div>
                <div>
                  <L>第一次读</L>
                  <br />
                  <span style={{ fontSize: 32, color: GOLD }}>
                    <L>有意外</L>
                  </span>
                </div>
              </div>
            </Card>
          </Center>
        </>
      );
      break;
    case "half":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <Card style={{ width: 1520 }}>
              <Heading small="SHANNON · HISTORICAL ESTIMATE">
                <L>英文里，大约一半是冗余</L>
              </Heading>
              <div
                style={{
                  display: "flex",
                  height: 85,
                  marginTop: 65,
                  borderRadius: 15,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: "50%",
                    background: GREEN,
                    color: "#16372e",
                    padding: 18,
                    fontSize: 34,
                  }}
                >
                  <L>语言规律决定的</L>
                </div>
                <div
                  style={{
                    width: "50%",
                    background: GOLD,
                    color: "#16372e",
                    padding: 18,
                    fontSize: 34,
                  }}
                >
                  <L>可以自由选择的</L>
                </div>
              </div>
              <div style={{ fontSize: 25, color: SOFT, marginTop: 35 }}>
                <L>历史估计 · 本片四选一游戏不测量冗余率</L>
              </div>
            </Card>
          </Center>
        </>
      );
      break;
    case "crossword":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <Card style={{ width: 1570 }}>
              <Heading small="WHY REDUNDANCY?">
                <L>规则让词能够相遇</L>
              </Heading>
              <div
                style={{
                  display: "flex",
                  gap: 100,
                  marginTop: 55,
                  alignItems: "center",
                }}
              >
                <div
                  style={{
                    fontFamily: EN,
                    fontSize: 60,
                    letterSpacing: 8,
                    lineHeight: 1.6,
                  }}
                >
                  XQJVMKTR
                  <br />
                  ZBGPHNWL
                </div>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(5,75px)",
                    gap: 6,
                  }}
                >
                  <L>
                    {"  C    L  WORLD  U    D    E  "
                      .slice(0, 25)
                      .split("")
                      .map((ch, i) => (
                        <div
                          key={i}
                          style={{
                            width: 75,
                            height: 75,
                            background:
                              ch === " " ? "rgba(0,0,0,.2)" : "#ededd6",
                            color: "#1c3d31",
                            textAlign: "center",
                            lineHeight: "75px",
                            fontSize: 40,
                            fontFamily: EN,
                          }}
                        >
                          {ch}
                        </div>
                      ))}
                  </L>
                </div>
              </div>
            </Card>
          </Center>
        </>
      );
      break;
    case "scramble": {
      const scrambled = "研表究明，汉字的序顺并不定一能影阅响读。";
      const correct = "研究表明，汉字的顺序并不一定能影响阅读。";
      const solved = current.id === "cl03-15" || current.id === "cl03-16";
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <Card style={{ width: 1580 }}>
              <div style={{ fontSize: 66, lineHeight: 1.65, color: GOLD }}>
                <L>{solved ? correct : scrambled}</L>
              </div>
              <div style={{ fontSize: 30, color: GREEN, marginTop: 38 }}>
                <L>
                  {current.id === "cl03-16"
                    ? "冗余像备份，帮消息扛过噪声"
                    : solved
                      ? "顺序错了一些，意思仍能补上"
                      : "网上的玩笑话 · 先自己读一遍"}
                </L>
              </div>
            </Card>
          </Center>
        </>
      );
      break;
    }
    case "coding":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <div style={{ display: "flex", gap: 70 }}>
              <Card style={{ width: 720 }}>
                <Heading small="COMPRESSION">
                  <L>消息更短</L>
                </Heading>
                <div style={{ fontSize: 42, color: GREEN, marginTop: 30 }}>
                  <L>去掉能猜到的部分</L>
                </div>
              </Card>
              <Card style={{ width: 720 }}>
                <Heading small="RELIABILITY">
                  <L>消息更结实</L>
                </Heading>
                <div style={{ fontSize: 42, color: GOLD, marginTop: 30 }}>
                  <L>留一些备份</L>
                </div>
              </Card>
            </div>
          </Center>
        </>
      );
      break;
    case "markov": {
      const text =
        "THE HEAD AND IN FRONTAL ATTACK ON AN ENGLISH WRITER THAT THE CHARACTER OF THIS POINT IS THEREFORE ANOTHER METHOD";
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <Card style={{ width: 1600 }}>
              <Heading small="SHANNON · 1948">
                <L>按前一个词的统计，再接一个词</L>
              </Heading>
              <div
                style={{
                  fontFamily: EN,
                  fontSize: 42,
                  lineHeight: 1.6,
                  marginTop: 38,
                  color: GOLD,
                }}
              >
                <L>
                  {text.slice(0, Math.min(text.length, Math.floor(time * 12)))}
                </L>
              </div>
              <div style={{ fontSize: 27, color: SOFT, marginTop: 35 }}>
                <L>二阶词近似 · 香农论文中的示例</L>
              </div>
            </Card>
          </Center>
        </>
      );
      break;
    }
    case "reveal":
      visual = (
        <>
          <L>{background}</L>
          <div
            style={{
              position: "absolute",
              left: 240,
              top: 140,
              fontFamily: EN,
              fontSize: 82,
              color: GOLD,
            }}
          >
            Claude
          </div>
          <Chat cue={current} now={now} />
          <Note>
            <L>文案与 Claude 合作完成 · AI 合成配音</L>
          </Note>
        </>
      );
      break;
    case "words": {
      const active = time >= at("cl04-05");
      const afterSpeech = Math.max(0, now - current.speech.end);
      const name = `words-psa231-${tl.lang}`;
      const keys = tl.playback[name].keys;
      visual = (
        <>
          <L>{background}</L>
          <L>
            {active ? (
              <>
                <div
                  style={{
                    position: "absolute",
                    left: 100,
                    top: 190,
                    width: 1720,
                    height: 485,
                  }}
                >
                  <VideoAt tl={tl} name={name} keys={keys} time={time} />
                </div>
                <div
                  style={{
                    position: "absolute",
                    left: 110,
                    top: 100,
                    fontSize: 38,
                    color: GOLD,
                  }}
                >
                  这次，每一步选一整个词
                </div>
                <Note>四选一为教学简化 · 一处先错，再选对</Note>
                {afterSpeech === 0 && <Chat cue={current} now={now} compact />}
              </>
            ) : (
              <Chat cue={current} now={now} />
            )}
          </L>
        </>
      );
      break;
    }
    case "training":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <Card style={{ width: 1500, marginTop: -280 }}>
              <Heading small="LEARNING TO PREDICT">
                <L>猜一个　→　对一下　→　调一调</L>
              </Heading>
              <div style={{ fontSize: 42, color: GREEN, marginTop: 45 }}>
                <L>规律可以学，练习可以继续。</L>
              </div>
              <div style={{ fontSize: 24, color: SOFT, marginTop: 32 }}>
                <L>真实模型预测下一个 token · 候选远不止四个</L>
              </div>
            </Card>
          </Center>
          <Chat cue={current} now={now} compact />
        </>
      );
      break;
    case "surprise":
    case "probability":
      visual = (
        <>
          <L>{background}</L>
          <Probability time={time} surprise={shot.kind === "surprise"} />
          <Chat cue={current} now={now} compact />
        </>
      );
      break;
    case "attention": {
      const reveal =
        current.id === "cl04-11"
          ? ease(Math.max(0, local("cl04-11")) / 0.8)
          : 0;
      if (english) {
        const reveal = ease(
          (now -
            (tl.markers?.["cl04-11"]?.["读到最后"] ??
              current.speech.start + 4)) /
            1.4,
        );
        visual = (
          <>
            {background}
            <Card
              style={{
                position: "absolute",
                left: 100,
                top: 120,
                width: 1720,
                padding: 54,
              }}
            >
              <Heading small="ATTENTION · ILLUSTRATION">
                Which earlier word helps?
              </Heading>
              <div
                style={{
                  position: "relative",
                  height: 315,
                  fontSize: 64,
                  lineHeight: 1.7,
                  marginTop: 35,
                }}
              >
                Maya lent <span style={{ color: GOLD }}>Ben</span> a book.
                <br />
                <span style={{ color: GOLD }}>He</span> read it on the train.
                <svg
                  viewBox="0 0 1600 315"
                  style={{
                    position: "absolute",
                    inset: 0,
                    width: "100%",
                    height: "100%",
                    opacity: reveal,
                  }}
                >
                  <path
                    d="M48 137 C48 95 420 140 420 65"
                    fill="none"
                    stroke={GOLD}
                    strokeWidth={6}
                  />
                  <circle cx="420" cy="65" r="8" fill={GOLD} />
                </svg>
              </div>
              <div style={{ fontSize: 32, color: GOLD, opacity: reveal }}>
                To understand “he”, look back at “Ben”.
              </div>
            </Card>
            <Note>Attention links are illustrative</Note>
            <Chat cue={current} now={now} compact />
          </>
        );
        break;
      }
      visual = (
        <>
          <Still name="apple-for-her-monet" dim={0.36} />
          <Card
            style={{
              position: "absolute",
              left: 100,
              top: 110,
              width: 1680,
              height: 510,
            }}
          >
            <div
              style={{
                fontFamily: EN,
                fontSize: 24,
                letterSpacing: 4,
                color: GREEN,
                marginBottom: 24,
              }}
            >
              ATTENTION · ILLUSTRATION
            </div>
            <div style={{ position: "relative", width: 1592, height: 290 }}>
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  top: 0,
                  fontSize: 60,
                  lineHeight: 1.4,
                }}
              >
                <span style={{ color: GOLD }}>
                  <L>小红</L>
                </span>
                <L>饿了，</L>
                <span style={{ color: GREEN }}>
                  <L>妈妈</L>
                </span>
                <L>给了她一个苹果。</L>
              </div>
              <svg
                viewBox="0 0 1592 290"
                width="100%"
                height="100%"
                style={{ position: "absolute", inset: 0, opacity: reveal }}
              >
                <defs>
                  <marker
                    id="attention-arrow"
                    markerUnits="userSpaceOnUse"
                    markerWidth="16"
                    markerHeight="16"
                    refX="14"
                    refY="8"
                    orient="auto"
                  >
                    <path d="M0 0 L16 8 L0 16" fill={GOLD} />
                  </marker>
                </defs>
                <path
                  d="M580 168 C580 115 60 145 60 94"
                  fill="none"
                  stroke={GOLD}
                  strokeWidth={7}
                  markerEnd="url(#attention-arrow)"
                />
                <path
                  d="M580 168 C580 135 360 135 360 94"
                  fill="none"
                  stroke={GREEN}
                  strokeWidth={2}
                />
              </svg>
              <div
                style={{
                  position: "absolute",
                  left: 550,
                  top: 180,
                  fontSize: 59,
                  lineHeight: 1.4,
                }}
              >
                <span style={{ color: GOLD }}>
                  <L>她</L>
                </span>
                <L>吃得很开心。</L>
              </div>
            </div>
            <div style={{ fontSize: 30, color: GOLD, opacity: reveal }}>
              <L>读到最后这个「她」，更关注前面的「小红」。</L>
            </div>
          </Card>
          <Note>
            <L>注意力连线为示意</L>
          </Note>
          <Chat cue={current} now={now} compact />
        </>
      );
      break;
    }
    case "paper":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <Card style={{ width: 1480, marginTop: -210 }}>
              <Heading small="VASWANI ET AL. · 2017">
                Attention Is All You Need
              </Heading>
              <div style={{ fontSize: 49, color: GREEN, marginTop: 38 }}>
                <L>注意力，就是你需要的一切。</L>
              </div>
            </Card>
          </Center>
          <Chat cue={current} now={now} compact />
        </>
      );
      break;
    case "trim": {
      const trim = current.id === "cl04-15";
      visual = (
        <>
          <L>{background}</L>
          <Card
            style={{ position: "absolute", left: 100, top: 120, width: 1650 }}
          >
            <Heading small="WHEN WORDS KEEP COMING">
              <L>一句话，能说清吗？</L>
            </Heading>
            <div style={{ fontSize: 42, lineHeight: 1.7, marginTop: 35 }}>
              <div>
                <L>先看问题里，有多少是新的。</L>
              </div>
              <L>
                {[
                  "这是一个非常值得我们深入思考的问题。",
                  "从很多不同的角度来看，它都非常重要。",
                  "总而言之，我们需要认真、全面地考虑。",
                ].map((text, i) => (
                  <div
                    key={text}
                    style={{
                      color: trim ? "#82928a" : SOFT,
                      opacity: trim ? 0.25 : 1,
                      textDecoration: trim ? "line-through" : "none",
                    }}
                  >
                    {text}
                  </div>
                ))}
              </L>
            </div>
          </Card>
          <Chat cue={current} now={now} compact />
        </>
      );
      break;
    }
    case "correction": {
      const correctionTime =
        tl.markers?.["cl04-18"]?.["莫奈"] ??
        tl.cues.find((c) => c.id === "cl04-18")!.speech.start + 2;
      const corrected =
        current.id === "cl04-18" &&
        (english ? now >= correctionTime : local("cl04-18") > 2);
      visual = (
        <>
          <L>{background}</L>
          <Card
            style={{ position: "absolute", left: 95, top: 140, width: 1650 }}
          >
            <Heading small="SOUNDS RIGHT?">
              <L>克劳德·</L>
              <span
                style={{
                  color: corrected ? "#f4a199" : WHITE,
                  textDecoration: corrected ? "line-through" : "none",
                }}
              >
                <L>香农</L>
              </span>
              {english ? "," : "，"}
            </Heading>
            <div style={{ fontSize: 59, lineHeight: 1.5, marginTop: 25 }}>
              <span
                style={{
                  borderBottom: corrected ? "4px solid #f4a199" : undefined,
                }}
              >
                <L>1840 年生在法国，</L>
              </span>
              <br />
              <span
                style={{
                  borderBottom: corrected ? "4px solid #f4a199" : undefined,
                }}
              >
                <L>是一位印象派画家。</L>
              </span>
            </div>
            <L>
              {corrected && (
                <div style={{ fontSize: 46, color: GOLD, marginTop: 30 }}>
                  ↑ 这是莫奈。通顺，不等于对。
                </div>
              )}
            </L>
          </Card>
          <Chat cue={current} now={now} compact />
        </>
      );
      break;
    }
    case "new-true":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <Card style={{ width: 1480, marginTop: -190 }}>
              <Heading small="READ WITH QUESTIONS">
                <L>有多少是新的？</L>
                <br />
                <L>有多少是真的？</L>
              </Heading>
            </Card>
          </Center>
          <Chat cue={current} now={now} compact />
        </>
      );
      break;
    case "useful-repeat":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <Card style={{ width: 1470, marginTop: -200 }}>
              <Heading small="REDUNDANCY WITH A PURPOSE">
                <L>重点再说一遍</L>
                <br />
                <L>步骤一步一步写</L>
              </Heading>
              <div style={{ fontSize: 40, color: GREEN, marginTop: 30 }}>
                <L>容易记住，也方便检查。</L>
              </div>
            </Card>
          </Center>
          <Chat cue={current} now={now} compact />
        </>
      );
      break;
    case "trio":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <div style={{ display: "flex", gap: 35 }}>
              <L>
                {[
                  [
                    "克劳德·莫奈",
                    "去掉冗余，留下光",
                    "art/impression-sunrise.jpg",
                  ],
                  [
                    "克劳德·香农",
                    "量出冗余，留一些备份",
                    "images/unicycle-juggler-monet.png",
                  ],
                  ["Claude · AI", "学会说话，也需要核对", ""],
                ].map(([name, sub, src], i) => (
                  <Card
                    key={name}
                    style={{
                      width: 520,
                      textAlign: "center",
                      opacity: time > i * 2 ? 1 : 0.4,
                    }}
                  >
                    {src ? (
                      <Img
                        src={file(src)}
                        style={{
                          width: "100%",
                          height: 300,
                          objectFit: "contain",
                        }}
                      />
                    ) : (
                      <div
                        style={{
                          height: 300,
                          fontFamily: EN,
                          fontSize: 80,
                          color: GOLD,
                          paddingTop: 80,
                        }}
                      >
                        Claude
                      </div>
                    )}
                    <div style={{ fontSize: 47, marginTop: 25 }}>{name}</div>
                    <div
                      style={{
                        fontSize: 28,
                        color: GREEN,
                        marginTop: 20,
                        lineHeight: 1.5,
                      }}
                    >
                      {sub}
                    </div>
                  </Card>
                ))}
              </L>
            </div>
          </Center>
          <Note>
            <L>独轮车插图 · AI 生成</L>
          </Note>
        </>
      );
      break;
    case "debussy":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <div style={{ display: "flex", gap: 90, alignItems: "center" }}>
              <Portrait
                name="克劳德·德彪西"
                sub="Claude Debussy · 1862—1918"
                src="art/debussy-nadar-1908.jpg"
              />
              <div>
                <Heading small="THE FOURTH CLAUDE">
                  <L>第四个 Claude</L>
                  <br />
                  <L>原来一直在耳边</L>
                </Heading>
                <div style={{ fontSize: 40, color: GOLD, marginTop: 40 }}>
                  <L>《月光》 · Clair de lune</L>
                </div>
                <div style={{ fontSize: 26, color: SOFT, marginTop: 24 }}>
                  <L>钢琴 · Laurens Goedhart</L>
                </div>
              </div>
            </div>
          </Center>
        </>
      );
      break;
    case "moon":
      visual = <Dissolve name="moonlit-water" time={time} at={2} length={3} />;
      break;
    case "cadence": {
      const q = ease(time / Math.max(1, last.speech.end - first.start));
      const arrived = !!tl.musicExample && now >= tl.musicExample.start + 18;
      visual = (
        <>
          <Still name="moonlit-water-monet" dim={0.5} />
          <Center>
            <Card style={{ width: 1600 }}>
              <Heading small="HARMONIC COLOUR · ILLUSTRATION">
                <L>回到「家」，可以走不同的路</L>
              </Heading>
              <div style={{ fontSize: 28, color: GREEN, marginTop: 35 }}>
                <L>期待中的路线（示意）</L>
              </div>
              <div
                style={{
                  display: "flex",
                  gap: 35,
                  alignItems: "center",
                  marginTop: 18,
                }}
              >
                <L>
                  {["出发", "紧张", "回家"].map((text, i) => (
                    <div
                      key={text}
                      style={{
                        width: 400,
                        padding: 22,
                        textAlign: "center",
                        fontSize: 36,
                        border: `2px solid ${GREEN}`,
                        borderRadius: 16,
                        opacity: 1 - q * 0.5,
                      }}
                    >
                      {text}
                    </div>
                  ))}
                </L>
              </div>
              <div style={{ fontSize: 28, color: GOLD, marginTop: 40 }}>
                <L>《月光》末段：另一条和声路线</L>
              </div>
              <div
                style={{
                  display: "flex",
                  gap: 35,
                  alignItems: "center",
                  marginTop: 18,
                }}
              >
                <L>
                  {["出发", "另一种颜色", "回家"].map((text, i) => (
                    <div
                      key={text}
                      style={{
                        width: 400,
                        padding: 22,
                        textAlign: "center",
                        fontSize: 39,
                        border: `2px solid ${GOLD}`,
                        borderRadius: 16,
                        opacity: i === 2 && !arrived ? 0.3 : 1,
                        background:
                          i === (arrived ? 2 : 1)
                            ? "rgba(239,204,137,.24)"
                            : "transparent",
                      }}
                    >
                      {text}
                    </div>
                  ))}
                </L>
              </div>
              <div style={{ fontSize: 34, color: GOLD, marginTop: 35 }}>
                <L>
                  {arrived
                    ? "最后的和弦也完整响完。路，可以不一样。"
                    : "留一点时间，听颜色怎样变化。"}
                </L>
              </div>
            </Card>
          </Center>
          <Note>
            <L>路线动画为示意 · 保留《月光》真实收束</L>
          </Note>
        </>
      );
      break;
    }
    case "three-lives":
      visual = (
        <>
          <L>{background}</L>
          <Lifelines three time={time} />
        </>
      );
      break;
    case "debussy-joke":
      visual = (
        <>
          <L>{background}</L>
          <Center>
            <div style={{ display: "flex", gap: 80, alignItems: "center" }}>
              <Portrait
                name="第四个 Claude"
                sub="德彪西"
                src="art/debussy-nadar-1908.jpg"
              />
              <div style={{ fontSize: 80, color: GOLD }}>←</div>
              <Card style={{ width: 750 }}>
                <Heading small="THE THIRD CLAUDE">Claude · AI</Heading>
                <div style={{ fontSize: 43, lineHeight: 1.6, marginTop: 40 }}>
                  <L>写稿时，</L>
                  <br />
                  <L>提到了德彪西。</L>
                </div>
              </Card>
            </div>
          </Center>
        </>
      );
      break;
    case "questions": {
      const text = current[tl.lang];
      const endings = [
        "有多少是新的呢？",
        "有多少是真的呢？",
        "什么是重要的呢？",
        "什么是可以忽略的呢？",
      ];
      const progress = Math.max(
        0,
        Math.min(
          1,
          (now - current.speech.start) /
            (current.speech.end - current.speech.start),
        ),
      );
      const spokenChars = progress * text.length;
      visual = (
        <>
          <Art src={pond} dim={0.58 + 0.1 * progress} />
          <Center>
            <div style={{ width: 1600 }}>
              <div style={{ fontSize: 41, color: GREEN, marginBottom: 42 }}>
                <L>在今天这个充满 AI 信息冗余的时代，</L>
                <br />
                <L>你怎么分辨——</L>
              </div>
              <L>
                {endings.map((q) => (
                  <div
                    key={q}
                    style={{
                      fontSize: 68,
                      lineHeight: 1.55,
                      color: GOLD,
                      opacity:
                        tl.markers?.[current.id]?.[q] !== undefined
                          ? ease((now - tl.markers[current.id][q]) / 0.45)
                          : ease(
                              (spokenChars -
                                text.indexOf(
                                  english
                                    ? (
                                        {
                                          "有多少是新的呢？": "what is new?",
                                          "有多少是真的呢？": "What is true?",
                                          "什么是重要的呢？": "What matters?",
                                          "什么是可以忽略的呢？":
                                            "What can you leave aside?",
                                        } as Record<string, string>
                                      )[q]
                                    : q,
                                )) /
                                3,
                            ),
                    }}
                  >
                    {q}
                  </div>
                ))}
              </L>
              <div
                style={{
                  fontSize: 39,
                  color: WHITE,
                  lineHeight: 1.55,
                  marginTop: 38,
                  opacity:
                    tl.markers?.[current.id]?.["这也是"] !== undefined
                      ? ease((now - tl.markers[current.id]["这也是"]) / 0.65)
                      : ease(
                          (spokenChars -
                            text.indexOf(
                              english ? "These are questions" : "这也是",
                            )) /
                            5,
                        ),
                }}
              >
                <L>这也是我们在 Lucas Academy</L>
                <br />
                <L>一起学习、一起思考的问题。</L>
              </div>
            </div>
          </Center>
        </>
      );
      break;
    }
  }
  return (
    <AbsoluteFill style={{ opacity: Math.min(1, frame / 12) }}>
      <L>{visual}</L>
    </AbsoluteFill>
  );
};

export const FunInformatics02Video: FC<ClaudeProps> = ({ tl }) => {
  const frame = useCurrentFrame(),
    { fps } = useVideoConfig();
  if (!tl) return null;
  return (
    <FilmLanguage.Provider value={tl.lang}>
      <AbsoluteFill
        style={{
          fontFamily: tl.lang === "en" ? EN : FONT,
          background: "#173b30",
          color: WHITE,
        }}
      >
        <Art src="art/water-lilies-1906.jpg" zoom={7} />
        <Audio src={file(`audio/${tl.lang}.mix.wav`)} />
        <L>
          {SHOTS.map((shot) => {
            const first = tl.cues.find((c) => c.id === shot.from)!,
              last = tl.cues.find((c) => c.id === shot.to)!;
            return (
              <Sequence
                key={shot.from}
                from={Math.round(first.start * fps)}
                durationInFrames={
                  Math.ceil((last.end - first.start) * fps) + 12
                }
              >
                <Scene tl={tl} shot={shot} first={first} last={last} />
              </Sequence>
            );
          })}
        </L>
        <L>
          {frame >= Math.round(tl.endCardStart * fps) && (
            <AbsoluteFill
              style={{
                alignItems: "center",
                justifyContent: "center",
                background: "#18382e",
              }}
            >
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 90, fontWeight: 650 }}>
                  {tl.lang === "en" ? (
                    <>
                      Do You Know <span style={{ color: GOLD }}>Claude?</span>
                    </>
                  ) : (
                    <>
                      你认识{" "}
                      <span style={{ fontFamily: EN, color: GOLD }}>
                        Claude
                      </span>{" "}
                      吗？
                    </>
                  )}
                </div>
                <div
                  style={{
                    fontFamily: EN,
                    fontSize: 32,
                    color: GREEN,
                    marginTop: 28,
                  }}
                >
                  {tl.lang === "en"
                    ? "Fun Informatics 2"
                    : "Do You Know Claude?"}
                </div>
                <div style={{ fontSize: 31, marginTop: 65 }}>
                  作者 Yancy Qin, Louise Yang | Lucas Academy
                </div>
              </div>
            </AbsoluteFill>
          )}
        </L>
      </AbsoluteFill>
    </FilmLanguage.Provider>
  );
};

export const FunInformatics02Cover: FC = () => (
  <AbsoluteFill style={{ fontFamily: FONT, color: WHITE }}>
    <Art src="art/water-lilies-1906.jpg" dim={0.32} />
    <div
      style={{
        position: "absolute",
        left: 105,
        top: 215,
        textShadow: "0 4px 35px rgba(0,0,0,.75)",
      }}
    >
      <div style={{ fontSize: 155, fontWeight: 750, lineHeight: 1.3 }}>
        <L>你认识</L>
        <br />
        <span style={{ fontFamily: EN, color: GOLD }}>Claude</span>
        <L> 吗？</L>
      </div>
      <div style={{ fontFamily: EN, fontSize: 45, marginTop: 28 }}>
        Do You Know Claude?
      </div>
    </div>
  </AbsoluteFill>
);

export const FunInformatics02EnglishCover: FC = () => (
  <AbsoluteFill style={{ fontFamily: EN, color: WHITE }}>
    <Art src="art/water-lilies-1906.jpg" dim={0.32} />
    <div
      style={{
        position: "absolute",
        left: 105,
        top: 235,
        fontSize: 145,
        fontWeight: 750,
        lineHeight: 1.2,
        textShadow: "0 4px 35px rgba(0,0,0,.75)",
      }}
    >
      Do you know
      <br />
      <span style={{ color: GOLD }}>Claude?</span>
    </div>
  </AbsoluteFill>
);
