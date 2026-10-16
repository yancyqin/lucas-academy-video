/**
 * 「你会算 7×8 吗？」 · Fun Economics 1 · Extra (FUN-ECONOMICS-01-7X8.md): the finger path of 7 × 8, explained on its own.
 *
 * Same look and cards as 「一根冰棍，要花多少钱？」 (imported from it). Backgrounds: the question on paper, Yancy's hand
 * footage, the arithmetic page (finger scene with the 10 × 10 grid scene in the middle, recorded in solo mode), and the
 * closing question on paper. Text is never small: 64 px is the floor on a 1080p frame.
 */
import { useContext, type FC, type ReactNode } from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  staticFile,
  useVideoConfig,
  type CalculateMetadataFunction,
} from "remotion";
import {
  BigText, C, Chip, FadeIn, LangCtx, NUM, Num, Paper, Big, rise, tx, useFonts, useT, type Lang, type Speech,
} from "../fun-economics-01/FunEconomics01Video";

const DIR = "fun-economics-01-7x8";
const file = (p: string) => staticFile(`${DIR}/${p}`);

type Cue = { id: string; start: number; end: number; speech: { start: number; end: number } };
export type ExtraTimeline = {
  lang: Lang; fps: number; durationSeconds: number; endCardStart: number; draft: boolean; footage: string[]; cues: Cue[];
};
export type ExtraProps = { tl?: ExtraTimeline | null; lang?: Lang };

export const calculateExtraMetadata: CalculateMetadataFunction<ExtraProps> = async ({ props, abortSignal }) => {
  const response = await fetch(file(`timeline.${props.lang ?? "zh"}.json`), { signal: abortSignal });
  if (!response.ok) throw Error("Run scripts/fun-economics-01-7x8/build_timeline.py first");
  const tl = (await response.json()) as ExtraTimeline;
  return { props: { ...props, tl }, fps: tl.fps, durationInFrames: Math.ceil(tl.durationSeconds * tl.fps) };
};

const speechOf = (cue: Cue): Speech => {
  const s0 = cue.speech.start - cue.start, s1 = cue.speech.end - cue.start;
  return { s0, s1, at: (f) => s0 + f * (s1 - s0), dur: cue.end - cue.start };
};

const Placeholder: FC<{ label: string }> = ({ label }) => (
  <AbsoluteFill>
    <Paper />
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ fontFamily: NUM, fontSize: 96, color: C.ghost, border: `8px dashed ${C.ghost}`, borderRadius: 40, padding: "40px 80px" }}>{label}</div>
    </AbsoluteFill>
  </AbsoluteFill>
);

const Clip: FC<{ tl: ExtraTimeline; name: string; startFrom?: number }> = ({ tl, name, startFrom = 0 }) => {
  const { fps } = useVideoConfig();
  if (!tl.footage.includes(name)) return <Placeholder label={name} />;
  return (
    <AbsoluteFill style={{ background: C.paper }}>
      <OffthreadVideo src={file(`footage/${name}`)} startFrom={Math.max(0, Math.round(startFrom * fps))} muted
        style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    </AbsoluteFill>
  );
};

// Digits and Latin letters inside Chinese text: the brush font has no good ones.
const D: FC<{ children: ReactNode; color?: string }> = ({ children, color }) => <span style={{ fontFamily: NUM, fontWeight: 700, color }}>{children}</span>;
const TITLE = { zh: <>你会算 <D color={C.orangeText}>7 × 8</D> 吗？</>, en: <>Can You Work Out <span style={{ color: C.orangeText }}>7 × 8</span>?</> };
const SERIES = { zh: <>趣味经济学 <D>1</D> · 番外</>, en: "Fun Economics 1 · Extra" };

const TitleCard: FC<{ at: number }> = ({ at }) => {
  const t = useT();
  const lang = useContext(LangCtx);
  const k = rise(t, at, 0.6);
  return (
    <AbsoluteFill style={{ opacity: k }}>
      <Paper />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 36 }}>
        <Big size={lang === "en" ? 140 : 170} style={{ transform: `translateY(${(1 - k) * 30}px)` }}>{TITLE[lang]}</Big>
        <Big size={76}>{SERIES[lang]}</Big>
        <div style={{ fontFamily: NUM, fontWeight: 700, fontSize: 64, color: C.ink }}>{tx(lang, "作者", "By")} Yancy Qin, Louise Yang | Lucas Academy</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const EndCard: FC<{ lang: Lang }> = ({ lang }) => {
  const t = useT();
  const k = rise(t, 0.2, 0.8);
  return (
    <AbsoluteFill style={{ opacity: k }}>
      <Paper />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 36 }}>
        <div style={{ fontFamily: NUM, fontWeight: 700, fontSize: 150, color: C.ink }}>Lucas Academy</div>
        <Big size={lang === "en" ? 76 : 84}>{SERIES[lang]} · {TITLE[lang]}</Big>
        <div style={{ fontFamily: NUM, fontWeight: 700, fontSize: 64, color: C.ink }}>{tx(lang, "作者", "By")} Yancy Qin, Louise Yang</div>
        <Big size={64} color={C.ghost}>{tx(lang, <>配音为 <D>AI</D> 合成</>, "Narration AI-voiced")}</Big>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const BigSum: FC<{ a: number; b: number; answer?: number; at: number; answerAt?: number }> = ({ a, b, answer, at, answerAt }) => {
  const t = useT();
  const shown = answerAt !== undefined && t >= answerAt;
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: rise(t, at), paddingBottom: 220 }}>
      <Num size={260}><span style={{ color: C.redText }}>{a}</span> × <span style={{ color: C.orangeText }}>{b}</span> = <span style={{ color: shown ? C.green : C.ghost }}>{shown ? answer : "?"}</span></Num>
    </AbsoluteFill>
  );
};

// ---- the shot list ----
type Bg = { from: string; to: string; render: (tl: ExtraTimeline, segStart: number) => ReactNode };
const PAGE_FROM = "hx02-01";  // page.<lang>.mp4 starts FADE before this cue, like the segment that shows it
const BGS: Bg[] = [
  { from: "hx00-01", to: "hx00-01", render: () => <Paper /> },
  { from: "hx01-01", to: "hx01-02", render: (tl) => <Clip tl={tl} name={`hands.${tl.lang}.mp4`} /> },
  { from: "hx02-01", to: "hx03-01", render: (tl, segStart) => <Clip tl={tl} name={`page.${tl.lang}.mp4`} startFrom={segStart - tl.cues.find((c) => c.id === PAGE_FROM)!.start} /> },
  { from: "hx03-02", to: "hx03-02", render: () => <Paper /> },
];

const CARDS: Record<string, (s: Speech, tl: ExtraTimeline) => ReactNode> = {
  "hx00-01": (s, tl) => (<>
    <BigSum a={7} b={8} answer={56} at={0} answerAt={s.at(0.3)} />
    <BigText at={s.at(0.62)} lines={[tx(tl.lang, "不背口诀，只用两只手？", "No times table, just two hands?")]} size={110} y={640} />
    <TitleCard at={s.s1 + 0.4} />
  </>),
  // The hand footage leaves the wall above the left hand and between the hands empty (the right hand rises high).
  "hx01-01": (s, tl) => (<>
    <Chip at={s.at(0.5)} x={70} y={60}>{tx(tl.lang, "左手伸出 ", "Left: ")}<Num size={92} color={C.redText}>2</Num>{tx(tl.lang, "", " up")}</Chip>
    <Chip at={s.at(0.85)} x={720} y={60}>{tx(tl.lang, "右手伸出 ", "Right: ")}<Num size={92} color={C.redText}>3</Num>{tx(tl.lang, "", " up")}</Chip>
  </>),
  "hx01-02": (s, tl) => (<>
    <Chip at={s.at(0.05)} x={70} y={60} out={s.at(0.45)}>{tx(tl.lang, <>伸出 <Num size={92}>5</Num> 根 = <Num size={92}>5</Num> 个十</>, <><Num size={92}>5</Num> up = <Num size={92}>5</Num> tens</>)} = <Num size={92} color={C.redText}>50</Num></Chip>
    <Chip at={s.at(0.48)} x={70} y={60} out={s.at(0.8)}>{tx(tl.lang, "弯着 ", "Bent: ")}<Num size={92} color={C.orangeText}>3 × 2 = 6</Num></Chip>
    <Chip at={s.at(0.82)} x={70} y={60}><Num size={92}>50 + 6 = <span style={{ color: C.green }}>56</span></Num></Chip>
  </>),
  "hx03-02": (s, tl) => (<>
    <BigSum a={6} b={7} at={0.05} />
    <BigText at={s.at(0.3)} lines={tx(tl.lang, ["伸出几根？弯着几根？", "和口诀一样吗？"], ["How many up? How many bent?", "Does it match the times table?"]) as ReactNode[]} size={tl.lang === "en" ? 88 : 104} y={560} />
  </>),
};

export const FunEconomics01ExtraVideo: FC<ExtraProps> = ({ tl }) => {
  useFonts();
  const { fps } = useVideoConfig();
  if (!tl) return null;
  const F = (x: number) => Math.round(x * fps);
  const at = (id: string) => tl.cues.find((c) => c.id === id)!;
  const FADE = 0.3;
  return (
    <LangCtx.Provider value={tl.lang}>
      <AbsoluteFill style={{ background: C.paper }}>
        {BGS.map((bg, i) => {
          const a = i === 0 ? 0 : at(bg.from).start - FADE, b = at(bg.to).end;
          return (
            <Sequence key={bg.from} from={F(a)} durationInFrames={Math.max(1, F(b) - F(a))}>
              <FadeIn d={i === 0 ? 0 : FADE}>{bg.render(tl, at(bg.from).start)}</FadeIn>
            </Sequence>
          );
        })}
        {tl.cues.map((cue) => {
          const card = CARDS[cue.id];
          if (!card) return null;
          return (
            <Sequence key={cue.id} from={F(cue.start)} durationInFrames={Math.max(1, F(cue.end) - F(cue.start))}>
              {card(speechOf(cue), tl)}
            </Sequence>
          );
        })}
        <Sequence from={F(tl.endCardStart)}><EndCard lang={tl.lang} /></Sequence>
        <Audio src={file(`audio/${tl.lang}.mix.wav`)} />
        {tl.draft && <div style={{ position: "absolute", right: 30, bottom: 24, fontFamily: NUM, fontWeight: 700, fontSize: 64, color: C.red, opacity: 0.7 }}>DRAFT</div>}
      </AbsoluteFill>
    </LangCtx.Provider>
  );
};

// YouTube cover (README "YouTube covers"): one big question, one picture (the hands making 2 and 3). zh: big Chinese, small
// English; en flipped.
const CoverFrame: FC<{ lang: Lang }> = ({ lang }) => {
  useFonts();
  const zh = (
    <LangCtx.Provider value="zh">
      <Big size={lang === "zh" ? 176 : 84} style={{ textAlign: "left", lineHeight: 1.12, whiteSpace: "nowrap", textShadow: "0 4px 0 rgba(255,255,255,.9)" }}>
        你会算<br /><Num size={lang === "zh" ? 168 : 80} color={C.orangeText}>7 × 8</Num> 吗？
      </Big>
    </LangCtx.Provider>
  );
  const en = (
    <div style={{ fontFamily: NUM, fontWeight: 700, fontSize: lang === "en" ? 132 : 64, lineHeight: 1.05, color: C.ink, whiteSpace: "nowrap", textShadow: "0 4px 0 rgba(255,255,255,.9)" }}>
      {lang === "en" ? <>Can You<br />Work Out<br /><span style={{ color: C.orangeText }}>7 × 8</span>?</> : <>Can You Work Out <span style={{ color: C.orangeText }}>7 × 8</span>?</>}
    </div>
  );
  return (
    <AbsoluteFill style={{ background: C.paper }}>
      <Img src={file("images/cover-hands.jpg")} style={{ position: "absolute", left: -420, top: 0, width: 1920, height: 1080 }} />
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(247,249,242,0) 52%, rgba(247,249,242,.9) 60%, rgba(247,249,242,.97) 100%)" }} />
      <div style={{ position: "absolute", left: 1110, top: 170, width: 790, display: "flex", flexDirection: "column", gap: 34 }}>
        {lang === "zh" ? <>{zh}{en}</> : <>{en}{zh}</>}
      </div>
    </AbsoluteFill>
  );
};
export const FunEconomics01ExtraCover: FC = () => <CoverFrame lang="zh" />;
export const FunEconomics01ExtraCoverEn: FC = () => <CoverFrame lang="en" />;
