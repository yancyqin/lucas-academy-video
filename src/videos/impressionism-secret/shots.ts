import type {ClipId, ImgId} from './assets.generated';

/**
 * Shot list for 你知道印象派的秘密吗？ / Do You Know the Secret of Impressionism?
 * One picture edit for both audio tracks, so almost nothing on screen is a word:
 * names, years and MANET/MONET (owner 2026-11-01; no "AI" badge, owner 2026-11-01 later the same day).
 *
 * v10 (owner 2026-11-04): "视频尽量把之前的 muse 视频都用上，手法也是油画 muse 视频切换", and Codex pictures only
 * where no Muse clip repeats them (the fifer's room, the Concorde, the cradle's gauze, the apples' table). The
 * owner's clips take turns with the paintings ('seq'), and every circle is a hand-drawn gold loop drawn on as
 * we watch (src/data/impressionism-strokes.json).
 * Each question ends its cue, so an answer and its marks start on the answer's cue.
 *
 * Coordinates are fractions of the picture. A camera key {t, x, y, z} puts point (x, y) of the picture
 * at the centre of the frame at progress t (0..1 of the shot or beat), z = 1 fitting the whole picture;
 * a key with `at` (a cue id, plus `delay`, a fraction of that cue) is placed at that moment instead.
 */
export type Cam = {t: number; x: number; y: number; z: number};
export type CamKey = {t?: number; at?: string; delay?: number; x: number; y: number; z: number};
export type Box = [number, number, number, number];
/** A hand-drawn circle (or line) drawn on along the owner's stroke, from its cue until `until` ends (or the shot ends). */
export type Mark = {id: string; at: string; delay?: number; until?: string};
export type Name = {zh: string; en: string; years: string};
/**
 * One beat of a 'seq' shot: the painting or one of the owner's clips, from its cue (the first beat from the
 * shot's start), with its own camera. A clip registered to its painting (CLIPS[clip].art) sits exactly on
 * the painting, so the dissolve between them lines up; any other clip fills the painting's place. A clip
 * only moves while it is on screen, carrying on where it last stopped, slowed to `rate` (or just enough
 * that it lasts).
 */
export type Beat = {at?: string; delay?: number; sec?: number; show: 'clip' | 'art' | 'year'; clip?: ClipId; art?: ImgId; fit?: 'frame';
  rate?: number; year?: string; cam: CamKey[]; marks?: Mark[]};
/** `sec`: seconds after the cue's first word, instead of `delay` (for beats laid out in a long silence). */

export type Shot = {from: string; to: string} & (
  | {kind: 'opening'; title: string}
  | {kind: 'art'; img: ImgId; cam: CamKey[]; marks?: Mark[]; dim?: number; year?: string;
     inset?: {img: ImgId; at: string; side: 'left' | 'right'}}
  | {kind: 'pair'; a: ImgId; b: ImgId; marksA?: Mark[]; marksB?: Mark[]}
  | {kind: 'seq'; art: ImgId; clip?: ClipId; beats: Beat[]}
  | {kind: 'intro'; img: ImgId; name: Name; then?: {img: ImgId; at: string; delay?: number; cam?: CamKey[]}}
  | {kind: 'faces'}
  | {kind: 'salon'}
  | {kind: 'letters'}
  | {kind: 'year'; year: string; bg: ImgId}
  | {kind: 'skip'; bg: ImgId}
  | {kind: 'camille'}
  | {kind: 'recap'}
  | {kind: 'game'}
  | {kind: 'closing'}
);

/** The painters, as themselves: their real portraits, in the order of the chapters. */
export const FACES: {img: ImgId; en: string; zh: string}[] = [
  {img: 'manet-self', en: 'Manet', zh: '马奈'}, {img: 'monet-self', en: 'Monet', zh: '莫奈'},
  {img: 'degas-self', en: 'Degas', zh: '德加'}, {img: 'morisot-self', en: 'Morisot', zh: '莫里索'},
  {img: 'renoir-self', en: 'Renoir', zh: '雷诺阿'}, {img: 'cezanne-self', en: 'Cézanne', zh: '塞尚'},
];

/** Degas's dancers in the order he painted them: painting, the owner's Muse clip of it (registered to it), year. */
const DANCERS: [ImgId, ClipId, string][] = [
  ['degas-dance-class', 'dance-class', '1874'], ['degas-rehearsal-stage', 'rehearsal-stage', '1874'],
  ['degas-etoile', 'etoile', 'c. 1876'], ['degas-barre', 'barre', '1877'], ['degas-waiting', 'waiting', 'c. 1882'],
  ['degas-blue-dancers', 'blue-dancers', '1898'],
];

const still = (x = 0.5, y = 0.5, z = 1): CamKey[] => [{t: 0, x, y, z}, {t: 1, x, y, z: z * 1.05}];
const push = (x: number, y: number, z0: number, z1: number): CamKey[] => [{t: 0, x, y, z: z0}, {t: 1, x, y, z: z1}];
const WHOLE = still();

export const SHOTS: Shot[] = [
  // IM00 · the Degas opening (v6): real scene and painting take turns, three clips and two paintings
  {from: 'im00-01', to: 'im00-03', kind: 'seq', clip: 'gen-opera', art: 'degas-orchestra-opera',
    beats: [
      {show: 'clip', rate: 0.55, cam: [{t: 0, x: 0.5, y: 0.5, z: 1.05}, {t: 1, x: 0.5, y: 0.4, z: 1.25}]},
      {at: 'im00-01', delay: 0.3, show: 'art', cam: [{t: 0, x: 0.5, y: 0.14, z: 2.2}, {t: 1, x: 0.5, y: 0.18, z: 2.0}],
        marks: [{id: 'o1', at: 'im00-01', delay: 0.42}]},
      {at: 'im00-02', show: 'clip', rate: 0.55, cam: [{t: 0, x: 0.5, y: 0.35, z: 1.3}, {t: 1, x: 0.5, y: 0.45, z: 1.15}]},
      {at: 'im00-02', delay: 0.24, show: 'art', cam: [{t: 0, x: 0.3, y: 0.36, z: 1.6}, {t: 1, x: 0.55, y: 0.34, z: 1.6}],
        marks: [{id: 'o2', at: 'im00-02', delay: 0.5}]},
      {at: 'im00-03', show: 'clip', rate: 0.55, cam: [{t: 0, x: 0.5, y: 0.45, z: 1.15}, {t: 1, x: 0.5, y: 0.38, z: 1.35}]},
    ]},
  // the laughed-at name, then today's queues: the Salon clip, the title over it
  {from: 'im00-04', to: 'im00-08', kind: 'opening', title: 'im00-08'},
  {from: 'im00-09', to: 'im00-09', kind: 'faces'},
  // IM02 · the Salon
  {from: 'im02-01', to: 'im02-01', kind: 'salon'},
  {from: 'im02-02', to: 'im02-03', kind: 'art', img: 'meissonier-1814',
    cam: [{t: 0, x: 0.5, y: 0.5, z: 1}, {at: 'im02-03', x: 0.5, y: 0.5, z: 1.03}, {t: 1, x: 0.45, y: 0.66, z: 1.35}],
    marks: [{id: 'm1', at: 'im02-03', delay: 0.05}, {id: 'm2', at: 'im02-03', delay: 0.45}]},
  {from: 'im02-04', to: 'im02-04', kind: 'art', img: 'salon-bouguereau-breton', cam: push(0.5, 0.42, 1, 1.25)},
  {from: 'im02-05', to: 'im02-05', kind: 'art', img: 'daguerre-boulevard', cam: push(0.55, 0.45, 1, 1.5)},
  {from: 'im02-06', to: 'im02-06', kind: 'pair', a: 'muybridge-horse-in-motion', b: 'salon-meissonier-friedland'},
  {from: 'im02-07', to: 'im02-08', kind: 'faces'},
  // IM03 · Manet
  // v11: warn before the whole art section (including Luncheon), then introduce Manet.
  {from: 'im03-04', to: 'im03-04', kind: 'skip', bg: 'manet-monet-studio-boat'},
  {from: 'im03-01', to: 'im03-01', kind: 'intro', img: 'manet-self', name: {zh: '马奈', en: 'Édouard Manet', years: '1832–1883'}},
  {from: 'im03-02', to: 'im03-02', kind: 'seq', art: 'manet-luncheon', beats: [
    {show: 'year', art: 'manet-monet-studio-boat', year: '1863', cam: WHOLE},
    // Both tracks say the title at 10.26 s after speech starts; centre the 8-frame dissolve there.
    {at: 'im03-02', sec: 10.1266666667, show: 'art', year: '1863', cam: still(0.5, 0.5, 1)},
  ]},
  {from: 'im03-03', to: 'im03-03', kind: 'year', year: '1865', bg: 'manet-monet-studio-boat'},
  // IM04 · Olympia (skippable chapter)
  {from: 'im04-01', to: 'im04-01', kind: 'art', img: 'manet-olympia', cam: WHOLE},
  {from: 'im04-02', to: 'im04-08', kind: 'pair', a: 'titian-venus-urbino', b: 'manet-olympia',
    marksA: [{id: 't1', at: 'im04-04', delay: 0.05, until: 'im04-05'}, {id: 't2', at: 'im04-04', delay: 0.28, until: 'im04-05'}],
    marksB: [{id: 'l1', at: 'im04-04', delay: 0.52, until: 'im04-05'}, {id: 'l2', at: 'im04-04', delay: 0.78, until: 'im04-05'},
             {id: 'l1', at: 'im04-08', delay: 0.05}]},
  {from: 'im04-09', to: 'im04-09', kind: 'art', img: 'manet-olympia', cam: [{t: 0, x: 0.5, y: 0.5, z: 1}, {t: 1, x: 0.5, y: 0.95, z: 0.55}]},
  // IM05 · two names; the fifer; Diderot; the railway
  {from: 'im05-01', to: 'im05-03', kind: 'letters'},
  {from: 'im05-04', to: 'im05-04', kind: 'art', img: 'monet-camille-green-dress', cam: [{t: 0, x: 0.5, y: 0.5, z: 1}, {t: 0.5, x: 0.83, y: 0.93, z: 4.5}, {t: 1, x: 0.83, y: 0.93, z: 4.8}]},
  // the room the boy would have stood in (Codex, no clip repeats it), then Manet's grey
  {from: 'im05-05', to: 'im05-08', kind: 'seq', art: 'manet-fifer',
    beats: [
      {show: 'art', art: 'real-fifer-1866', cam: still(0.5, 0.5, 1)},
      {at: 'im05-05', delay: 0.42, show: 'art', cam: [{t: 0, x: 0.5, y: 0.5, z: 1}, {t: 1, x: 0.5, y: 0.5, z: 1.06}],
        marks: [{id: 'f1', at: 'im05-06', delay: 0.05, until: 'im05-06'}, {id: 'f2', at: 'im05-07', delay: 0.45, until: 'im05-07'},
                {id: 'f3', at: 'im05-07', delay: 0.7, until: 'im05-07'}]},
    ]},
  {from: 'im05-09', to: 'im05-09', kind: 'art', img: 'manet-fifer', cam: still(0.5, 0.5, 1), inset: {img: 'zola-by-manet', at: 'im05-09', side: 'right'}},
  {from: 'im05-10', to: 'im05-11', kind: 'art', img: 'manet-self', cam: push(0.5, 0.4, 1, 1.2)},
  {from: 'im05-12', to: 'im05-14', kind: 'seq', clip: 'gen-train-trim', art: 'manet-railway',
    beats: [
      {show: 'art', cam: [{t: 0, x: 0.5, y: 0.5, z: 1}, {at: 'im05-13', x: 0.5, y: 0.5, z: 1.04}, {t: 1, x: 0.62, y: 0.3, z: 1.25}],
        marks: [{id: 'r1', at: 'im05-13', delay: 0.05}]},
      // the girl watching the steam, the woman glancing up: the clip's first 4.9 s (then she turns round, which in the painting she never does)
      {at: 'im05-14', show: 'clip', rate: 0.6, cam: [{t: 0, x: 0.5, y: 0.5, z: 1}, {t: 1, x: 0.5, y: 0.5, z: 1.05}]},
      {at: 'im05-14', delay: 0.5, show: 'art', cam: still(0.5, 0.5, 1),
        marks: [{id: 'r2', at: 'im05-14', delay: 0.52}, {id: 'r3', at: 'im05-14', delay: 0.66}]},
    ]},
  {from: 'im05-15', to: 'im05-15', kind: 'art', img: 'manet-monet-studio-boat', cam: push(0.45, 0.5, 1, 1.12)},
  // IM06 · 1874
  {from: 'im06-01', to: 'im06-01', kind: 'art', img: 'nadar-studio-1860', cam: push(0.5, 0.45, 1, 1.15), year: '1874'},
  {from: 'im06-02', to: 'im06-04', kind: 'seq', clip: 'gen-le-havre', art: 'monet-impression-sunrise',
    beats: [
      {show: 'clip', cam: still(0.5, 0.5, 1)},
      {at: 'im06-02', delay: 0.42, show: 'art', cam: [{t: 0, x: 0.5, y: 0.5, z: 1}, {t: 1, x: 0.55, y: 0.45, z: 1.25}]},
    ]},
  {from: 'im06-05', to: 'im06-06', kind: 'faces'},
  // IM07 · Monet, and Camille
  {from: 'im07-01', to: 'im07-01', kind: 'intro', img: 'monet-self', name: {zh: '莫奈', en: 'Claude Monet', years: '1840–1926'}},
  {from: 'im07-02', to: 'im07-04', kind: 'art', img: 'monet-women-garden', cam: still(0.5, 0.5, 1),
    marks: [{id: 'g1', at: 'im07-02', delay: 0.45}, {id: 'g2', at: 'im07-02', delay: 0.62}, {id: 'g3', at: 'im07-02', delay: 0.8}]},
  {from: 'im07-05', to: 'im07-09', kind: 'seq', art: 'monet-woman-parasol',
    beats: [
      {show: 'clip', clip: 'minimax-parasol', fit: 'frame', cam: WHOLE},
      {at: 'im07-05', delay: 0.6, show: 'art', cam: still(0.5, 0.45, 1)},
      // "look closely at her face": the owner's Muse parasol clip, then the painted face
      {at: 'im07-06', show: 'clip', clip: 'muse-parasol', cam: push(0.595, 0.22, 2.0, 2.3)},
      {at: 'im07-06', delay: 0.75, show: 'art',
        cam: [{t: 0, x: 0.595, y: 0.2, z: 2.3}, {at: 'im07-07', delay: 0.6, x: 0.595, y: 0.2, z: 2.4}, {at: 'im07-08', x: 0.5, y: 0.45, z: 1}, {t: 1, x: 0.5, y: 0.45, z: 1.04}],
        marks: [{id: 'p1', at: 'im07-07', delay: 0.05, until: 'im07-07'},
                {id: 'p2', at: 'im07-08', delay: 0.3}, {id: 'p3', at: 'im07-08', delay: 0.45}, {id: 'p4', at: 'im07-08', delay: 0.6},
                {id: 'p5', at: 'im07-08', delay: 0.78}]},
    ]},
  {from: 'im07-10', to: 'im07-10', kind: 'art', img: 'monet-haystacks', cam: push(0.5, 0.5, 1, 1.2)},
  {from: 'im07-11', to: 'im07-11', kind: 'art', img: 'monet-gare-saint-lazare', cam: push(0.5, 0.45, 1, 1.2)},
  {from: 'im07-12', to: 'im07-12', kind: 'art', img: 'monet-nadar-1899', cam: push(0.5, 0.4, 1, 1.12)},
  {from: 'im07-13', to: 'im07-15', kind: 'camille'},
  {from: 'im07-16', to: 'im07-17', kind: 'art', img: 'monet-camille-deathbed', cam: push(0.5, 0.35, 1, 1.35)},
  // IM08 · Degas
  {from: 'im08-01', to: 'im08-01', kind: 'intro', img: 'degas-self', name: {zh: '德加', en: 'Edgar Degas', years: '1834–1917'}},
  // back to the painting from the opening: the cut, then the friends in the pit, then the question
  {from: 'im08-02', to: 'im08-05', kind: 'art', img: 'degas-orchestra-opera',
    cam: [{t: 0, x: 0.5, y: 0.14, z: 2.2}, {at: 'im08-03', x: 0.5, y: 0.4, z: 1.35}, {at: 'im08-04', x: 0.5, y: 0.5, z: 1}, {t: 1, x: 0.5, y: 0.5, z: 1.04}],
    marks: [{id: 'o1', at: 'im08-02', delay: 0.3, until: 'im08-02'}, {id: 'o3', at: 'im08-03', delay: 0.45, until: 'im08-03'}]},
  {from: 'im08-06', to: 'im08-07', kind: 'seq', art: 'degas-place-concorde',
    beats: [
      {show: 'art', art: 'real-concorde-1875', cam: still(0.5, 0.5, 1)},
      {at: 'im08-06', delay: 0.38, show: 'art', cam: still(0.5, 0.5, 1),
        marks: [{id: 'c1', at: 'im08-07', delay: 0.05}, {id: 'c2', at: 'im08-07', delay: 0.55}]},
    ]},
  {from: 'im08-08', to: 'im08-09', kind: 'seq', clip: 'dance-class', art: 'degas-dance-class',
    beats: [
      {show: 'art', cam: still(0.5, 0.5, 1)},
      {at: 'im08-09', show: 'clip', cam: still(0.5, 0.5, 1.02)},
      {at: 'im08-09', delay: 0.38, show: 'art', cam: still(0.5, 0.5, 1.03),
        marks: [{id: 'd1', at: 'im08-09', delay: 0.4}, {id: 'd2', at: 'im08-09', delay: 0.58}, {id: 'd3', at: 'im08-09', delay: 0.76}]},
    ]},
  {from: 'im08-10', to: 'im08-10', kind: 'art', img: 'degas-orchestra-opera', cam: push(0.5, 0.4, 1, 1.1),
    marks: [{id: 'o1', at: 'im08-10', delay: 0.1}, {id: 'o2', at: 'im08-10', delay: 0.3}]},
  {from: 'im08-11', to: 'im08-11', kind: 'art', img: 'degas-self', cam: push(0.5, 0.4, 1, 1.15)},
  {from: 'im08-12', to: 'im08-14', kind: 'art', img: 'degas-rehearsal-stage', cam: push(0.5, 0.5, 1, 1.15)},
  // "Degas has been called the painter of dancing girls. Is it true?" — then about a minute with no narration
  // (owner 2026-11-04: "德加的 muse 视频都展示……展示的完整一些……中间可以和油画切换"): each of his dancers in
  // turn, painting then the owner's Muse clip, in the order he painted them; the answer comes after (im08-16).
  {from: 'im08-15', to: 'im08-15', kind: 'seq', art: 'degas-dance-class',
    beats: [
      {show: 'art', year: '1874', cam: push(0.5, 0.5, 1, 1.04)},
      ...DANCERS.flatMap(([art, clip, year], i): Beat[] => [
        ...(i ? [{at: 'im08-15', sec: 5.6 + i * 9.0 - 2.2, show: 'art' as const, art, year, cam: push(0.5, 0.5, 1, 1.03)}] : []),
        {at: 'im08-15', sec: 5.6 + i * 9.0, show: 'clip' as const, clip, art, rate: 1, cam: push(0.5, 0.5, 1.03, 1.08)},
      ]),
      {at: 'im08-15', sec: 5.6 + DANCERS.length * 9.0 - 2.2, show: 'art', art: 'degas-blue-dancers', cam: push(0.5, 0.5, 1.03, 1.06)},
    ]},
  // the answer, in his own words
  {from: 'im08-16', to: 'im08-16', kind: 'art', img: 'degas-blue-dancers', cam: push(0.5, 0.5, 1.06, 1.14)},
  // IM09 · Morisot
  {from: 'im09-01', to: 'im09-01', kind: 'intro', img: 'morisot-self', name: {zh: '莫里索', en: 'Berthe Morisot', years: '1841–1895'}},
  {from: 'im09-02', to: 'im09-03', kind: 'art', img: 'manet-morisot-violets', cam: push(0.5, 0.4, 1, 1.15)},
  // "how did she paint the gauze?": a real gauze, thread by thread (Codex), then her few strokes of white
  {from: 'im09-04', to: 'im09-07', kind: 'seq', art: 'morisot-cradle',
    beats: [
      {show: 'art', cam: [{t: 0, x: 0.5, y: 0.5, z: 1}, {t: 1, x: 0.5, y: 0.5, z: 1.03}]},
      {at: 'im09-06', show: 'art', art: 'real-cradle-1872', cam: push(0.72, 0.35, 1.3, 1.45)},
      {at: 'im09-07', show: 'art', cam: [{t: 0, x: 0.72, y: 0.35, z: 1.5}, {t: 1, x: 0.72, y: 0.35, z: 1.55}],
        marks: [{id: 'y1', at: 'im09-07', delay: 0.1}]},
    ]},
  {from: 'im09-08', to: 'im09-10', kind: 'art', img: 'morisot-harbor-lorient', cam: push(0.5, 0.5, 1, 1.2)},
  {from: 'im09-11', to: 'im09-13', kind: 'art', img: 'morisot-self', cam: push(0.5, 0.42, 1, 1.15)},
  // IM10 · Renoir
  {from: 'im10-01', to: 'im10-01', kind: 'intro', img: 'renoir-self', name: {zh: '雷诺阿', en: 'Pierre-Auguste Renoir', years: '1841–1919'},
    then: {img: 'renoir-moulin-galette', at: 'im10-01', delay: 0.55}},
  {from: 'im10-02', to: 'im10-06', kind: 'seq', clip: 'gen-moulin', art: 'renoir-moulin-galette',
    beats: [
      {show: 'clip', cam: still(0.5, 0.5, 1)},
      {at: 'im10-02', delay: 0.55, show: 'art',
        cam: [{t: 0, x: 0.5, y: 0.5, z: 1}, {at: 'im10-05', x: 0.5, y: 0.5, z: 1.04}, {at: 'im10-06', x: 0.55, y: 0.2, z: 1.3}, {t: 1, x: 0.5, y: 0.5, z: 1}],
        marks: [{id: 'n1', at: 'im10-03', delay: 0.05, until: 'im10-04'}, {id: 'n2', at: 'im10-03', delay: 0.3, until: 'im10-04'},
                {id: 'n3', at: 'im10-05', delay: 0.05, until: 'im10-05'}]},
    ]},
  {from: 'im10-07', to: 'im10-08', kind: 'seq', clip: 'bougival', art: 'renoir-bougival',
    beats: [
      {show: 'clip', cam: push(0.5, 0.42, 1, 1.05)},
      {at: 'im10-07', delay: 0.5, show: 'clip', clip: 'dance-city', art: 'renoir-dance-city', cam: push(0.5, 0.42, 1, 1.05)},
      {at: 'im10-08', show: 'art', art: 'renoir-dance-city', cam: push(0.5, 0.42, 1.05, 1.1)},
    ]},
  // IM11 · Cézanne
  {from: 'im11-01', to: 'im11-02', kind: 'intro', img: 'cezanne-self', name: {zh: '塞尚', en: 'Paul Cézanne', years: '1839–1906'}},
  {from: 'im11-03', to: 'im11-03', kind: 'art', img: 'cezanne-sainte-victoire-viaduct', cam: push(0.5, 0.45, 1, 1.12)},
  {from: 'im11-04', to: 'im11-05', kind: 'seq', clip: 'gen-sainte-victoire', art: 'cezanne-sainte-victoire-late',
    beats: [
      {show: 'art', cam: push(0.45, 0.4, 1, 1.05)},
      {at: 'im11-05', show: 'clip', cam: still(0.5, 0.5, 1)},
      {at: 'im11-05', delay: 0.45, show: 'art', cam: push(0.45, 0.4, 1, 1.12)},
    ]},
  // a table that would line up (Codex), then Cézanne's
  {from: 'im11-06', to: 'im11-06', kind: 'seq', art: 'cezanne-basket-of-apples',
    beats: [
      {show: 'art', art: 'real-apples-still-life', cam: still(0.5, 0.5, 1)},
      {at: 'im11-06', delay: 0.5, show: 'art', cam: still(0.5, 0.5, 1)},
    ]},
  {from: 'im11-07', to: 'im11-10', kind: 'art', img: 'cezanne-basket-of-apples',
    cam: [{t: 0, x: 0.5, y: 0.5, z: 1}, {at: 'im11-09', x: 0.5, y: 0.5, z: 1.03}, {at: 'im11-10', x: 0.55, y: 0.55, z: 1.25}, {t: 1, x: 0.55, y: 0.55, z: 1.3}],
    marks: [{id: 'a1', at: 'im11-07', delay: 0.05, until: 'im11-08'}, {id: 'a2', at: 'im11-07', delay: 0.3, until: 'im11-08'},
            {id: 'a3', at: 'im11-07', delay: 0.62, until: 'im11-08'}]},
  {from: 'im11-11', to: 'im11-11', kind: 'pair', a: 'monet-haystacks', b: 'cezanne-sainte-victoire-late'},
  // IM13 · the secret
  {from: 'im13-01', to: 'im13-01', kind: 'faces'},
  {from: 'im13-02', to: 'im13-04', kind: 'recap'},
  {from: 'im13-05', to: 'im13-07', kind: 'game'},
  {from: 'im13-08', to: 'im13-08', kind: 'art', img: 'manet-olympia', cam: still(0.5, 0.5, 1)},
  {from: 'im13-09', to: 'im13-09', kind: 'art', img: 'monet-nadar-1899', cam: push(0.5, 0.4, 1, 1.1), year: '1890'},
  {from: 'im13-10', to: 'im13-10', kind: 'art', img: 'manet-olympia', cam: push(0.5, 0.5, 1, 1.08), year: '1907'},
  {from: 'im13-11', to: 'im14-02', kind: 'closing'},
];

/** Camille, year by year (im07-13 to im07-15); only the year is on screen. */
export const CAMILLE: {img: ImgId; year: string}[] = [
  {img: 'monet-camille-green-dress', year: '1866'},
  {img: 'monet-women-garden', year: '1866'},
  {img: 'monet-red-kerchief', year: 'c. 1870'},
  {img: 'monet-camille-bench', year: '1873'},
  {img: 'monet-woman-parasol', year: '1875'},
  {img: 'monet-la-japonaise', year: '1876'},
];

/** The recap wall: each painter's painting, lit as their words are said (im13-02 / im13-03). */
export const RECAP: {img: ImgId; at: string; delay: number}[] = [
  {img: 'manet-railway', at: 'im13-02', delay: 0.02},
  {img: 'monet-haystacks', at: 'im13-02', delay: 0.38},
  {img: 'degas-orchestra-opera', at: 'im13-02', delay: 0.7},
  {img: 'morisot-cradle', at: 'im13-03', delay: 0.02},
  {img: 'renoir-moulin-galette', at: 'im13-03', delay: 0.36},
  {img: 'cezanne-sainte-victoire-late', at: 'im13-03', delay: 0.7},
];
