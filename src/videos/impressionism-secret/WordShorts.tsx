import type {CSSProperties, FC} from 'react';
import {AbsoluteFill, Audio, Easing, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {IMG, type ImgId} from './assets.generated';

/**
 * Two word-game Shorts from 你知道印象派的秘密吗？ (owner, 2026-11-02): Degas's opera
 * orchestra and Renoir's Moulin de la Galette. Each sentence shows with letters missing
 * (mostly vowels: still readable, which is the point), then every gap tries two or three
 * wrong letters before the right one lands; once a sentence is whole, the picture turns
 * from the generated real scene into the painting, and the Chinese types out under it.
 * The text fills in while the picture leaves things out. Vertical 1080x1920, no voice.
 */

export const SHORT_FPS = 30;

type Line = {en: string; zh: string}; // en: letters in [brackets] are missing
type Short = {clip: string; clipSeconds: number; art: ImgId; lines: Line[]};

export const SHORTS: Record<'degas' | 'renoir', Short> = {
  degas: {
    clip: 'gen-opera', clipSeconds: 6.9, art: 'degas-orchestra-opera',
    lines: [
      {en: 'I am D[e]g[a]s, fr[o]m 1870.', zh: '我是德加，来自1870年。'},
      {en: 'My impr[e]ss[io]n keeps the m[u]s[i]c.', zh: '我的印象，留下了音乐。'},
      {en: "I cut out the d[a]nc[e]rs' h[ea]ds, b[e]c[a]use your e[y]es can f[i]ll them in.", zh: '我切掉了舞者的头，因为你的眼睛会把它补上。'},
    ],
  },
  renoir: {
    clip: 'gen-moulin', clipSeconds: 6.9, art: 'renoir-moulin-galette',
    lines: [
      {en: 'I am R[e]n[oi]r, fr[o]m 1876.', zh: '我是雷诺阿，来自1876年。'},
      {en: 'An impr[e]ss[io]n is a f[ee]ling.', zh: '印象，是一种感觉。'},
      {en: 'Unl[i]ke a ph[o]t[o]graph, it k[ee]ps the l[i]ght, not the l[i]nes.', zh: '它不像照片：它留下光，不留轮廓。'},
      {en: 'It r[e]m[e]mb[e]rs how the l[i]ght d[a]nced on a S[u]nd[a]y aft[e]rn[oo]n.', zh: '它记得，在一个星期天的下午，光是怎么跳舞的。'},
    ],
  },
};

// Timing, in frames
const IN = 10;      // a sentence fades in
const READ = 30;    // time to read it with the gaps
const TRY = 4;      // each wrong letter
const LAND = 7;     // the right letter, before the next gap
const TURN = 15;    // real scene → painting
const ZH = 3;       // each Chinese character
const HOLD = 36;    // the whole sentence, both languages
const OUT = 8;      // a sentence fades out
const END = 105;    // the closing card

type Slot = {ch: string; gap: boolean; tries: string[]; at: number}; // at: frame the right letter lands
type Planned = {start: number; slots: Slot[]; whole: number; zhStart: number; end: number; zh: string};

const POOL = 'aeiouy';
/** Two or three wrong letters for a gap, the same on every render. */
function triesFor(ch: string, seed: number): string[] {
  const pool = POOL.split('').filter((c) => c !== ch.toLowerCase());
  const n = seed % 3 === 0 ? 3 : 2;
  const out: string[] = [];
  let k = seed * 7 + 3;
  while (out.length < n) {
    const c = pool[k % pool.length];
    if (!out.includes(c)) out.push(c);
    k = k * 5 + 11;
  }
  return out;
}

function plan(s: Short): {lines: Planned[]; total: number} {
  let t = 0;
  let seed = 1;
  const lines = s.lines.map((line) => {
    const start = t;
    let at = start + IN + READ;
    const slots: Slot[] = [];
    let inGap = false;
    for (const ch of line.en) {
      if (ch === '[') { inGap = true; continue; }
      if (ch === ']') { inGap = false; continue; }
      if (!inGap) { slots.push({ch, gap: false, tries: [], at: start}); continue; }
      const tries = triesFor(ch, seed++);
      at += tries.length * TRY;
      slots.push({ch, gap: true, tries, at});
      at += LAND;
    }
    const whole = at;
    const zhStart = whole + TURN;
    const end = zhStart + [...line.zh].length * ZH + HOLD;
    t = end;
    return {start, slots, whole, zhStart, end, zh: line.zh};
  });
  return {lines, total: t + END};
}

export const shortDuration = (which: keyof typeof SHORTS) => plan(SHORTS[which]).total;

/** The letters grouped into words, so a line only ever breaks between words. */
const words = (slots: Slot[]): Slot[][] => slots.reduce<Slot[][]>((out, slot) => {
  if (slot.ch === ' ') out.push([]);
  else out[out.length - 1].push(slot);
  return out;
}, [[]]);

const INK = '#fbf3e4';
const GOLD = '#e9b93a';
const MUTED = '#9c9283';
const BG = '#140f0c';
const EN_FONT = 'Baskerville, "Baskerville Old Face", Georgia, serif';
const ZH_FONT = '"PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** One letter: a gap (underlined) until its turn, then the tries, then the right letter in gold, settling to ink. */
const Letter: FC<{slot: Slot; frame: number}> = ({slot, frame}) => {
  if (!slot.gap) return <span>{slot.ch}</span>;
  const tryStart = slot.at - slot.tries.length * TRY;
  let shown = '';
  let color = INK;
  let lift = 0;
  if (frame >= slot.at) {
    shown = slot.ch;
    const k = interpolate(frame, [slot.at, slot.at + 14], [0, 1], clamp);
    color = k < 1 ? GOLD : INK;
    lift = interpolate(frame, [slot.at, slot.at + 5], [-10, 0], {...clamp, easing: Easing.out(Easing.cubic)});
  } else if (frame >= tryStart) {
    shown = slot.tries[Math.min(slot.tries.length - 1, Math.floor((frame - tryStart) / TRY))];
    color = MUTED;
  }
  return (
    <span style={{position: 'relative', display: 'inline-block'}}>
      <span style={{visibility: 'hidden'}}>{slot.ch}</span>
      {!shown || frame < slot.at ? (
        <span style={{position: 'absolute', left: '8%', right: '8%', bottom: '0.12em', height: 4, borderRadius: 2,
          background: frame >= tryStart ? GOLD : 'rgba(251,243,228,0.55)'}} />
      ) : null}
      {shown ? (
        <span style={{position: 'absolute', left: 0, right: 0, top: 0, textAlign: 'center', color,
          transform: `translateY(${lift}px)`}}>{shown}</span>
      ) : null}
    </span>
  );
};

export const WordShort: FC<{which: keyof typeof SHORTS}> = ({which}) => {
  const frame = useCurrentFrame();
  const s = SHORTS[which];
  const {lines, total} = plan(s);
  const endStart = total - END;
  const {w, h} = IMG[s.art];
  // the picture box: as large as fits above the text
  const boxH = 940;
  const boxTop = 150;
  const scale = Math.min(1000 / w, boxH / h);
  const pw = w * scale;
  const ph = h * scale;
  const pic: CSSProperties = {position: 'absolute', left: (1080 - pw) / 2, top: boxTop + (boxH - ph) / 2, width: pw, height: ph,
    objectFit: 'cover', boxShadow: '0 24px 70px rgba(0,0,0,0.6)'};
  // painting shown from each sentence's last letter until the next sentence; the real scene in between
  const paint = Math.max(0, ...lines.map((l, i) => {
    const off = i + 1 < lines.length ? lines[i + 1].start : total + 999;
    return interpolate(frame, [l.whole, l.whole + TURN, off, off + TURN], [0, 1, 1, 0], clamp);
  }));
  // the real scene only moves while it is on screen, slowed to stretch its 7 s over every turn
  const clipSpans = lines.map((l) => [l.start, l.whole + TURN] as const);
  const clipFrames = clipSpans.reduce((a, [x, y]) => a + (y - x), 0);
  const rate = Math.min(1, (s.clipSeconds * SHORT_FPS) / clipFrames);
  let used = 0;
  const art = staticFile(`impressionism-secret/img/${s.art}${IMG[s.art].ext}`);
  const tile = staticFile(`impressionism-secret/tiles/${s.art}.jpg`);
  const current = lines.findIndex((l) => frame >= l.start && frame < l.end);
  const line = current >= 0 ? lines[current] : null;
  const endO = interpolate(frame, [endStart, endStart + 18], [0, 1], clamp);
  return (
    <AbsoluteFill style={{background: BG}}>
      <Img src={tile} style={{position: 'absolute', inset: -80, width: 1240, height: 2080, objectFit: 'cover',
        filter: 'blur(50px) brightness(0.32) saturate(0.85)'}} />
      {clipSpans.map(([x, y], i) => {
        const from = used;
        used += (y - x) * rate;
        return (
          <Sequence key={i} from={x} durationInFrames={y - x} layout="none">
            <OffthreadVideo src={staticFile(`impressionism-secret/video/${s.clip}.i60.mp4`)} muted trimBefore={Math.round(from)}
              playbackRate={rate} style={pic} />
          </Sequence>
        );
      })}
      <Img src={art} style={{...pic, opacity: paint}} />
      {line && (
        <div style={{position: 'absolute', left: 80, width: 860, top: 1130, textAlign: 'center',
          opacity: interpolate(frame, [line.start, line.start + IN, line.end - OUT, line.end], [0, 1, 1, 0], clamp)}}>
          <div style={{fontFamily: EN_FONT, fontWeight: 700, fontSize: 66, lineHeight: 1.28, color: INK,
            textShadow: '0 4px 18px rgba(0,0,0,0.75)'}}>
            {words(line.slots).map((word, i) => (
              <span key={i}>
                {i > 0 ? ' ' : null}
                <span style={{display: 'inline-block', whiteSpace: 'nowrap'}}>
                  {word.map((slot, k) => <Letter key={k} slot={slot} frame={frame} />)}
                </span>
              </span>
            ))}
          </div>
          <div style={{fontFamily: ZH_FONT, fontWeight: 600, fontSize: 50, lineHeight: 1.45, color: INK, marginTop: 26,
            textShadow: '0 3px 14px rgba(0,0,0,0.75)'}}>
            {[...line.zh].slice(0, Math.max(0, Math.floor((frame - line.zhStart) / ZH) + 1)).join('')}
          </div>
        </div>
      )}
      <AbsoluteFill style={{opacity: endO, background: 'rgba(14,10,8,0.72)', alignItems: 'center', justifyContent: 'center'}}>
        <div style={{fontFamily: ZH_FONT, fontWeight: 800, fontSize: 86, color: INK, marginTop: -160}}>
          你知道印象派的<span style={{color: GOLD}}>秘密</span>吗？
        </div>
        <div style={{fontFamily: EN_FONT, fontStyle: 'italic', fontSize: 50, color: INK, marginTop: 18}}>
          Do You Know the <span style={{color: GOLD}}>Secret</span> of Impressionism?
        </div>
        <div style={{width: 120, height: 3, background: GOLD, margin: '44px 0 30px'}} />
        <div style={{fontFamily: ZH_FONT, fontSize: 38, color: INK, opacity: 0.9}}>完整视频 · Full video ↓</div>
        <div style={{fontFamily: EN_FONT, fontSize: 34, color: INK, letterSpacing: 6, marginTop: 26, opacity: 0.85}}>LUCAS ACADEMY</div>
      </AbsoluteFill>
      <Audio src={staticFile('impressionism-secret/music/src/satie-gymnopedie-1-laucke.flac')}
        volume={(f) => 0.42 * interpolate(f, [0, 20, total - 45, total], [0, 1, 1, 0], clamp)} />
      {lines.flatMap((l) => l.slots.filter((x) => x.gap).flatMap((x, i) => [
        ...x.tries.map((_, k) => (
          <Sequence key={`t${l.start}-${i}-${k}`} from={x.at - (x.tries.length - k) * TRY} durationInFrames={6} layout="none">
            <Audio src={staticFile('impressionism-secret/audio/sfx-try.wav')} volume={0.35} />
          </Sequence>
        )),
        <Sequence key={`h${l.start}-${i}`} from={x.at} durationInFrames={8} layout="none">
          <Audio src={staticFile('impressionism-secret/audio/sfx-hit.wav')} volume={0.5} />
        </Sequence>,
      ]))}
    </AbsoluteFill>
  );
};

/**
 * Covers for the two Shorts (owner, 2026-11-02): the picture above, two lines below. English
 * keeps its gaps on purpose (gold rules, no letters); Chinese is plain, one phrase in gold.
 * Degas: the orchestra-pit frame the owner picked (gen-opera, 6.2 s), dancers' heads intact
 * under "I cut out the dancers' heads". Renoir: the painting's dappled light.
 */
const COVERS = {
  degas: {
    img: 'impressionism-secret/img/short-degas-frame.png',
    en: ['I am Degas, from 1870', "I <cut out> the d[a]nc[e]rs' h[ea]ds"],
    sub: '我<切掉>了舞者的头', // a Chinese line under the English (owner)
    zh: ['我是德加，来自1870年', '我<切掉>了舞者的头'],
  },
  renoir: {
    img: 'impressionism-secret/img/renoir-moulin-galette.jpg',
    en: ['I am Renoir, from 1876', 'I r[e]m[e]mb[e]r how the <l[i]ght> d[a]nced on a S[u]nd[a]y aft[e]rn[oo]n.'],
    sub: '我记录了<光>',
    zh: ['我是雷诺阿，来自1876年', '我记得，|一个星期天的下午，|光是怎么<跳舞>的'],
  },
} as const;

/**
 * A line with its gaps left open: each missing letter keeps its width, marked by a gold rule.
 * Words in <angle brackets> are set in gold, like the gold word in the Chinese line under them.
 */
const Gapped: FC<{text: string}> = ({text}) => {
  const parts: {ch: string; gap: boolean; gold: boolean}[] = [];
  let gap = false;
  let gold = false;
  for (const ch of text) {
    if (ch === '[') gap = true;
    else if (ch === ']') gap = false;
    else if (ch === '<') gold = true;
    else if (ch === '>') gold = false;
    else parts.push({ch, gap, gold});
  }
  const wordsOf = parts.reduce<{ch: string; gap: boolean; gold: boolean}[][]>((out, p) => {
    if (p.ch === ' ') out.push([]);
    else out[out.length - 1].push(p);
    return out;
  }, [[]]);
  return (
    <>
      {wordsOf.map((word, i) => (
        <span key={i}>
          {i > 0 ? ' ' : null}
          <span style={{display: 'inline-block', whiteSpace: 'nowrap'}}>
            {word.map((p, k) => p.gap ? (
              <span key={k} style={{position: 'relative', display: 'inline-block'}}>
                <span style={{visibility: 'hidden'}}>{p.ch}</span>
                <span style={{position: 'absolute', left: '10%', right: '10%', bottom: '0.1em', height: 6, borderRadius: 3, background: GOLD}} />
              </span>
            ) : <span key={k} style={p.gold ? {color: GOLD} : undefined}>{p.ch}</span>)}
          </span>
        </span>
      ))}
    </>
  );
};

/** Chinese with one phrase in <angle brackets> set in gold; | starts a new line (Chinese wraps anywhere otherwise). */
const Marked: FC<{text: string}> = ({text}) => (
  <>{text.split('|').map((row, r) => (
    <div key={r}>{row.split(/(<[^>]+>)/).map((s, i) => s.startsWith('<') ? <span key={i} style={{color: GOLD}}>{s.slice(1, -1)}</span> : <span key={i}>{s}</span>)}</div>
  ))}</>
);

export const WordShortCover: FC<{which: keyof typeof COVERS; lang: 'zh' | 'en'}> = ({which, lang}) => {
  const c = COVERS[which];
  const long = which === 'renoir';
  return (
    <AbsoluteFill style={{background: BG}}>
      <Img src={staticFile(c.img)} style={{position: 'absolute', left: 0, top: 0, width: 1080, height: 1350, objectFit: 'cover',
        objectPosition: which === 'renoir' ? '42% 50%' : '50% 30%'}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(20,15,12,0) 0%, rgba(20,15,12,0) 52%, rgba(20,15,12,0.92) 68%, #140f0c 76%)'}} />
      <div style={{position: 'absolute', left: 70, width: 940, top: long ? 1180 : 1270, textAlign: 'center', color: INK,
        textShadow: '0 4px 20px rgba(0,0,0,0.8)'}}>
        {lang === 'en' ? (
          <>
            <div style={{fontFamily: EN_FONT, fontWeight: 700, fontSize: 70, marginBottom: 22, opacity: 0.95}}>{c.en[0]}</div>
            <div style={{fontFamily: EN_FONT, fontWeight: 700, fontSize: long ? 84 : 104, lineHeight: 1.25}}><Gapped text={c.en[1]} /></div>
            <div style={{fontFamily: ZH_FONT, fontWeight: 700, fontSize: 72, marginTop: 34}}><Marked text={c.sub} /></div>
          </>
        ) : (
          <>
            <div style={{fontFamily: ZH_FONT, fontWeight: 600, fontSize: 64, marginBottom: 26, opacity: 0.95}}>{c.zh[0]}</div>
            <div style={{fontFamily: ZH_FONT, fontWeight: 800, fontSize: long ? 96 : 116, lineHeight: 1.3}}><Marked text={c.zh[1]} /></div>
          </>
        )}
      </div>
    </AbsoluteFill>
  );
};
