/**
 * YouTube cover for 「跨越中等收入陷阱」, 1280×720 (README "YouTube covers"; the cover shows only a question). The
 * question is Yancy's own (2026-10-26, from sc07-01 with 「一个人或者国家」), over the stair city; the series ribbon across the top-right corner, as on
 * 「法国人走上街头」 (the series name, never an episode number).
 */
import { useEffect, useState, type FC } from "react";
import { AbsoluteFill, Img, continueRender, delayRender, staticFile } from "remotion";

const file = (p: string) => staticFile(`middle-income-trap/${p}`);
const GOLD = "#c9a45a";
const EMBER = "#e2733c";
const SERIF = "'NotoSerifSC', 'Songti SC', serif";

const useFonts = () => {
  const [handle] = useState(() => delayRender("fonts"));
  useEffect(() => {
    new FontFace("NotoSerifSC", `url(${file("fonts/NotoSerifSC-Regular.otf")})`, { weight: "400" }).load()
      .then((f) => { document.fonts.add(f); continueRender(handle); })
      .catch((e) => { console.error(e); continueRender(handle); });
  }, [handle]);
};

/** The series ribbon (same geometry as NewsEducation01Video's). */
const Ribbon: FC<{ text: string; size: number; a?: number; h?: number }> = ({ text, size, a = 175, h = 88 }) => {
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

export const MiddleIncomeTrapCover: FC = () => {
  useFonts();
  return (
    <AbsoluteFill style={{ background: "#0f1317" }}>
      <Img src={file("art/01-ceiling.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", objectPosition: "60% 30%" }} />
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(10,12,15,.9) 0%, rgba(10,12,15,.72) 40%, rgba(10,12,15,.1) 72%, rgba(10,12,15,0) 100%)" }} />
      <AbsoluteFill style={{ justifyContent: "center", paddingLeft: 70, fontFamily: SERIF, color: "#fff" }}>
        <div style={{ fontSize: 92, lineHeight: 1.25, letterSpacing: 4, textShadow: "0 4px 24px rgba(0,0,0,.6)" }}>
          是什么，<br />让一个人或者国家<br />停在<span style={{ color: EMBER }}>天花板</span>下面呢？
        </div>
      </AbsoluteFill>
      <Ribbon text="从新闻看教育" size={46} a={165} />
    </AbsoluteFill>
  );
};

/** The English cover (Yancy, 2026-10-27: 给我英文封面): the same picture, the question in English only, as
 * 「法国人走上街头」's English cover does. */
export const MiddleIncomeTrapCoverEn: FC = () => {
  useFonts();
  return (
    <AbsoluteFill style={{ background: "#0f1317" }}>
      <Img src={file("art/01-ceiling.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", objectPosition: "60% 30%" }} />
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(10,12,15,.93) 0%, rgba(10,12,15,.78) 42%, rgba(10,12,15,.12) 74%, rgba(10,12,15,0) 100%)" }} />
      <AbsoluteFill style={{ justifyContent: "center", paddingLeft: 70, fontFamily: SERIF, color: "#fff" }}>
        <div style={{ fontSize: 80, lineHeight: 1.12, letterSpacing: 1, textShadow: "0 4px 24px rgba(0,0,0,.6)", whiteSpace: "nowrap" }}>
          What Keeps a Person<br />or a Country<br />Stuck Under the<br /><span style={{ color: EMBER }}>Ceiling</span>?
        </div>
      </AbsoluteFill>
      <Ribbon text="Lessons from the Headlines" size={30} a={215} />
    </AbsoluteFill>
  );
};
