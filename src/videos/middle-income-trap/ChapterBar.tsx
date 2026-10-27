/**
 * Chapter bar for 「跨越中等收入陷阱」 (MIDDLE-INCOME-TRAP.md, 进度条). Yancy, 2026-10-25: 下面要有进度条，像魔方那期一样.
 * Same layout as the cube film's ChapterTrack (branch claude/cube-2x2-film): one segment per chapter, segmented the way
 * YouTube segments its own bar from the description's chapters (same starts and proportions, small gaps), every
 * chapter named above its segment in Chinese with a shorter English name under it (2026-10-26), a ▼ riding the
 * playing point. The bar on the picture cannot be clicked; it tells the viewer where each part is so they can jump
 * there with YouTube's bar just below. At the title, ↓ arrows over every chapter say "jump to any part". At sc00-09
 * (「可以跳过下一段」) a big arc jumps from the start of 「证据」 to the start of 「学什么有用」 (Yancy, 2026-10-26: 这句的
 * 时候要加个箭头，有需要可以跳; the small marks of the first cut went unseen).
 */
import type { FC } from "react";

export type Chapter = { id: string; name: string; start: number; end: number; en?: string; enShort?: string };
export type Skip = { from: number; to: number; opacity: number; draw: number };

const EMBER = "#e2733c";
const GOLD = "#c9a45a";
const PAPER = "#ece3d2";
const MUTED = "#8f989f";
const SERIF = "'NotoSerifSC', 'Songti SC', serif";
const INSET = 18;
const GAP = 4;
const PILL = { background: "rgba(8,10,13,.62)", borderRadius: 12, padding: "6px 22px", display: "inline-block" } as const;

export const ChapterBar: FC<{ chapters: Chapter[]; duration: number; t: number; hint?: number; skip?: Skip | null }> = ({
  chapters, duration, t, hint = 0, skip = null,
}) => {
  const width = 1920 - INSET * 2;
  const x = (time: number) => INSET + (time / duration) * width;
  const current = chapters.findIndex((ch) => t >= ch.start && t < ch.end);
  const box = (i: number) => {
    const left = x(chapters[i].start) + (i ? GAP / 2 : 0);
    const right = x(chapters[i].end) - (i < chapters.length - 1 ? GAP / 2 : 0);
    return { left, w: right - left };
  };
  const bob = (i: number) => `translateY(${Math.sin(t * 5 + i) * 4}px)`;
  const fit = (w: number, chars: number, max: number, min: number) => Math.max(min, Math.min(max, Math.floor((w - 10) / chars)));
  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 170,
        background: "linear-gradient(180deg, rgba(8,10,13,0) 0%, rgba(8,10,13,.78) 100%)" }} />
      {hint > 0 && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 176, textAlign: "center", opacity: hint,
          fontFamily: SERIF, color: GOLD, textShadow: "0 2px 10px rgba(0,0,0,.9)" }}>
          <span style={PILL}>
            <div style={{ fontSize: 34, letterSpacing: 3 }}>点下面的进度条，跳到任意部分</div>
            <div style={{ fontSize: 22, fontWeight: 300, letterSpacing: 0.5 }}>Use the bar below to jump to any part</div>
          </span>
        </div>
      )}
      {chapters.map((ch, i) => {
        const { left, w } = box(i);
        const on = i === current;
        const played = Math.max(0, Math.min(1, (t - ch.start) / (ch.end - ch.start)));
        const zh = fit(w, [...ch.name].length + 0.3, 22, 13);  // the whole name fits
        const en = fit(w, (ch.enShort ?? "").length * 0.52 + 0.3, 15, 9);
        return (
          <div key={ch.id}>
            {hint > 0 && (
              <div style={{ position: "absolute", left, width: w, bottom: 112, textAlign: "center", opacity: hint,
                fontSize: 40, color: GOLD, transform: bob(i) }}>↓</div>
            )}
            <div style={{ position: "absolute", left, width: w, bottom: 26, textAlign: "center", overflow: "hidden",
              whiteSpace: "nowrap", fontFamily: SERIF, color: on ? PAPER : MUTED, opacity: on ? 1 : 0.85,
              textShadow: "0 1px 6px rgba(0,0,0,.9)", lineHeight: 1.15 }}>
              <div style={{ fontSize: zh, fontWeight: on ? 400 : 300 }}>{ch.name}</div>
              {ch.enShort ? <div style={{ fontSize: en, fontWeight: 300, letterSpacing: 0.3 }}>{ch.enShort}</div> : null}
            </div>
            <div style={{ position: "absolute", left, width: w, bottom: 12, height: 8, borderRadius: 4,
              background: "rgba(255,255,255,.22)", overflow: "hidden" }}>
              <div style={{ width: `${played * 100}%`, height: "100%", background: on ? EMBER : "rgba(226,115,60,.6)" }} />
            </div>
          </div>
        );
      })}
      {skip ? <SkipArc x0={x(chapters[skip.from].start)} x1={x(chapters[skip.to].start) + 6} opacity={skip.opacity} draw={skip.draw} t={t} /> : null}
      {current >= 0 && (
        <div style={{ position: "absolute", left: x(t) - 11, bottom: 19, width: 0, height: 0,
          borderLeft: "11px solid transparent", borderRight: "11px solid transparent", borderTop: `14px solid ${GOLD}` }} />
      )}
    </div>
  );
};

/** A big arc over the chapter that can be skipped, drawn left to right, landing on the next chapter's start. */
const SkipArc: FC<{ x0: number; x1: number; opacity: number; draw: number; t: number }> = ({ x0, x1, opacity, draw, t }) => {
  const base = 1080 - 78;  // just above the chapter names
  const top = base - 210;
  const mid = (x0 + x1) / 2;
  const d = `M ${x0} ${base} C ${x0 + 10} ${top}, ${x1 - 10} ${top}, ${x1} ${base}`;
  const len = 2.2 * (x1 - x0) + 420;
  const land = Math.max(0, Math.min(1, (draw - 0.85) / 0.15));
  const pulse = 1 + 0.08 * Math.sin(t * 6);
  return (
    <div style={{ position: "absolute", inset: 0, opacity }}>
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
        <path d={d} fill="none" stroke="rgba(0,0,0,.55)" strokeWidth={14} strokeLinecap="round" strokeDasharray={len} strokeDashoffset={len * (1 - draw)} />
        <path d={d} fill="none" stroke={GOLD} strokeWidth={8} strokeLinecap="round" strokeDasharray={len} strokeDashoffset={len * (1 - draw)} />
        <g opacity={land} transform={`translate(${x1} ${base + 4}) scale(${pulse})`}>
          <path d="M -22 -30 L 0 4 L 22 -30 Z" fill={GOLD} stroke="rgba(0,0,0,.55)" strokeWidth={3} strokeLinejoin="round" />
        </g>
        <circle cx={x0} cy={base} r={9} fill={EMBER} opacity={Math.min(1, draw * 4)} />
      </svg>
      <div style={{ position: "absolute", left: mid - 330, width: 660, bottom: 1080 - top + 14, textAlign: "center", fontFamily: SERIF,
        color: GOLD, textShadow: "0 2px 12px rgba(0,0,0,.95)" }}>
        <span style={PILL}>
          <div style={{ fontSize: 40, letterSpacing: 3 }}>认同的话，可以跳过这一段</div>
          <div style={{ fontSize: 26, fontWeight: 300, letterSpacing: 0.5 }}>Agree? You can skip this part</div>
        </span>
      </div>
      <div style={{ position: "absolute", left: x1 + 30, bottom: 96, fontFamily: SERIF, color: PAPER, opacity: land,
        textShadow: "0 2px 12px rgba(0,0,0,.95)" }}>
        <span style={PILL}>
          <div style={{ fontSize: 36, letterSpacing: 3, color: GOLD }}>直接到这里</div>
          <div style={{ fontSize: 24, fontWeight: 300, letterSpacing: 0.5 }}>Jump to here</div>
        </span>
      </div>
    </div>
  );
};
