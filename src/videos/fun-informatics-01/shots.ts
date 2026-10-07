/**
 * Picture plan for 「计算机怎么算 1+1=？ / How Does a Computer Add 1 + 1=?」 (FUN-INFORMATICS-01.md §3).
 *
 * Two layers, both keyed by narration cue ids:
 *  - VISUALS cover the whole film, back to back, cross-dissolving: room recordings, the fractal zoom,
 *    the Codex circuit pictures, stills. A footage `span` [a, b] is mapped onto the visual's length,
 *    so the painting reaches second b exactly as the narration moves on (a == b freezes on a).
 *    The painting takes start at their loop's second 0, so a span reads straight off the painting
 *    timetables in FUN-INFORMATICS-01.md §4.
 *  - CARDS sit on top for a cue range: words, equations, and the explainers drawn here
 *    (the carry, the switch adder, the guessing game, Shannon's ruler, one fractal pixel).
 */

export type Label = {zh: string; en: string};
export type Span = [number, number];
/** A speed-curve key: [shot second, footage second, playback speed there]. */
export type RampKey = [number, number, number];

export type Visual =
  | {kind: 'clip'; file: string; span: Span; dim?: number; push?: number; boost?: number; overlay?: 'fractal' | 'overdrive'; pip?: {file: string; span: Span}}
  | {kind: 'montage'; file: string; spans: Span[]; dim?: number}
  /** One unbroken take with a speed curve (cubic Hermite between keys): slow on the moments the words name, fast between. */
  | {kind: 'ramp'; file: string; keys: Record<'zh' | 'en', RampKey[]>; dim?: number}
  | {kind: 'image'; file: string; fit?: 'cover' | 'contain'; push?: number; dim?: number}
  | {kind: 'switch'; first?: string; pip?: {file: string; span: Span}}
  | {kind: 'grid'; pip?: {file: string; span: Span}}
  | {kind: 'pixelzoom'; file: string; focus: [number, number]; from: number; to: number}
  | {kind: 'split'; left: Visual; right: Visual}
  | {kind: 'wall'; items: {file: string; label: Label}[]};

export type Card =
  | {kind: 'words'; text: Label; small?: Label; kicker?: Label}
  | {kind: 'big'; text: string; small?: Label}
  | {kind: 'note'; text: Label}
  | {kind: 'carry'}
  | {kind: 'adder'}
  | {kind: 'guess'}
  | {kind: 'ruler'}
  | {kind: 'fractal-pixel'};

export type Shot<T> = {from: string; to: string} & T;

const FRACTAL = 'fractal-main.mp4';
const BITS = 'bits-close.mp4';
const PIXELS = 'pixels-close.mp4';
const GAMES = 'games-close.mp4';
const NATIVITY_STILL = 'stills/bits-close-112.png';

/** The opening: loading screen, then the transit chamber with the title (it00-01 is said over it). */
export const INTRO = {
  loadingSeconds: 2.0,
  chamber: {file: 'transit-chamber.mp4', span: [0, 11.5] as Span},
  last: 'it00-01',
  titleUntil: 'it00-02',
  series: {zh: '趣味信息学1', en: 'Fun Informatics 1'} as Label,
  byline: {zh: '作者 Yancy Qin, Louise Yang | Lucas Academy', en: 'By Yancy Qin, Louise Yang | Lucas Academy'} as Label,
};

export const Q1: Label = {zh: '计算机的图像，能无限放大吗？', en: 'Can a computer picture be zoomed in forever?'};

export const VISUALS: Shot<{visual: Visual}>[] = [
  // 00 · Q1: the fractal zoom, never frozen, until the question is put aside (Yancy, 2026-10-06)
  {from: 'it00-02', to: 'it00-05', visual: {kind: 'clip', file: FRACTAL, span: [0, 23.4], overlay: 'fractal'}},
  // 01 · Q2: no numbers inside, only switches; into the room
  {from: 'it01-01', to: 'it01-02', visual: {kind: 'grid'}},
  {from: 'it01-03', to: 'it01-03', visual: {kind: 'image', file: 'circuit-board.png', push: 0.08}},
  {from: 'it01-04', to: 'it01-04', visual: {kind: 'switch', first: 'chip-die.png'}},
  {from: 'it01-05', to: 'it01-05', visual: {kind: 'switch', pip: {file: FRACTAL, span: [6, 14]}}},
  {from: 'it01-06', to: 'it01-06', visual: {kind: 'clip', file: 'corridor.mp4', span: [22, 31]}},
  {from: 'it01-07', to: 'it01-07', visual: {kind: 'clip', file: 'entry.mp4', span: [0, 10.4]}},
  // 02 · two states, one bit
  {from: 'it02-01', to: 'it02-04', visual: {kind: 'clip', file: BITS, span: [12, 31.5]}},
  {from: 'it02-05', to: 'it02-05', visual: {kind: 'clip', file: BITS, span: [30, 30], dim: 0.5}},
  {from: 'it02-06', to: 'it02-06', visual: {kind: 'switch'}},
  // 03 · counting with two symbols; each row of the wall's counter appears as its line is said
  {from: 'it03-01', to: 'it03-01', visual: {kind: 'clip', file: BITS, span: [37.5, 39.5]}},
  {from: 'it03-02', to: 'it03-03', visual: {kind: 'clip', file: BITS, span: [39, 39], dim: 0.6}},
  // Row k's bits gather from 38.5 + 2.45k and its "→ k" lights at ~41 + 2.45k: each line starts with its row
  // mostly gathered and the value lights about halfway through, as the value is said (Yancy: keep them in sync).
  {from: 'it03-04', to: 'it03-04', visual: {kind: 'clip', file: BITS, span: [39.9, 42.35]}},
  {from: 'it03-05', to: 'it03-05', visual: {kind: 'clip', file: BITS, span: [42.35, 44.8]}},
  {from: 'it03-06', to: 'it03-06', visual: {kind: 'clip', file: BITS, span: [44.8, 47.25]}},
  {from: 'it03-07', to: 'it03-07', visual: {kind: 'clip', file: BITS, span: [47.25, 49.7]}},
  {from: 'it03-08', to: 'it03-08', visual: {kind: 'clip', file: BITS, span: [49.7, 51.9]}},
  // 04 · how switches add: 1 + 1 = 10, then counting on to 65
  {from: 'it04-01', to: 'it04-08', visual: {kind: 'grid'}},
  {from: 'it04-09', to: 'it04-09', visual: {kind: 'clip', file: BITS, span: [52, 59.5]}},
  // 05 · a rule turns numbers into letters
  {from: 'it05-01', to: 'it05-01', visual: {kind: 'clip', file: BITS, span: [65, 73]}},
  {from: 'it05-02', to: 'it05-02', visual: {kind: 'clip', file: BITS, span: [72.5, 72.5], dim: 0.55}},
  {from: 'it05-03', to: 'it05-03', visual: {kind: 'image', file: 'mr-yancy-bits-reading-guide.svg', fit: 'contain'}},
  {from: 'it05-04', to: 'it05-05', visual: {kind: 'clip', file: BITS, span: [74, 87.5]}},
  // 06 · pixels: the smallest piece; the arrangement is the picture
  {from: 'it06-01', to: 'it06-02', visual: {kind: 'clip', file: PIXELS, span: [15, 34], boost: 1.5}},
  {from: 'it06-03', to: 'it06-06', visual: {kind: 'clip', file: PIXELS, span: [40, 72], boost: 2.2}},
  {from: 'it06-07', to: 'it06-08', visual: {kind: 'clip', file: BITS, span: [97, 117]}},
  {from: 'it06-09', to: 'it06-09', visual: {kind: 'clip', file: PIXELS, span: [77, 94], boost: 1.8}},
  // cube → ball → Madonna as one take on a speed curve, not cuts (Yancy, 2026-10-07). Painting: grid cube clean
  // 138.5, rounds until ~178, ball with diagonals 183, scatters 184.4–186.6, gathers until Madonna is whole at 191,
  // fades out from 194.1. Keys follow each language's words: 立方体 / cube, 球 / ball, 散开 / scatter, 圣母与圣子 / Madonna.
  {from: 'it06-10', to: 'it06-10', visual: {kind: 'ramp', file: PIXELS, keys: {
    zh: [[0, 138, 1], [1.3, 140, 1.2], [4.5, 179, 1.5], [5.2, 184.4, 1.2], [5.9, 186.6, 1.2], [8.1, 191.2, 0.5], [12.2, 193.8, 0.4]],
    en: [[0, 138, 1], [0.8, 139.6, 2], [2.3, 179, 2], [2.9, 184.4, 1.2], [3.7, 186.6, 1.2], [6.4, 191.2, 0.5], [10.7, 193.8, 0.4]],
  }}},
  {from: 'it06-11', to: 'it06-11', visual: {kind: 'image', file: 'wall-1-triangles-to-3d.png', fit: 'contain'}},
  // 07 · Q1 answered: a smallest unit; the "infinite" picture is computed, by switches doing 1 + 1
  {from: 'it07-01', to: 'it07-01', visual: {kind: 'pixelzoom', file: NATIVITY_STILL, focus: [975, 650], from: 1, to: 1}},
  {from: 'it07-02', to: 'it07-03', visual: {kind: 'pixelzoom', file: NATIVITY_STILL, focus: [975, 650], from: 1, to: 24}},
  {from: 'it07-04', to: 'it07-04', visual: {kind: 'split',
    left: {kind: 'pixelzoom', file: NATIVITY_STILL, focus: [975, 650], from: 24, to: 24},
    right: {kind: 'clip', file: FRACTAL, span: [8, 14]}}},
  {from: 'it07-05', to: 'it07-05', visual: {kind: 'clip', file: FRACTAL, span: [14, 20], overlay: 'fractal'}},
  {from: 'it07-06', to: 'it07-06', visual: {kind: 'pixelzoom', file: 'stills/fractal-main-20.png', focus: [960, 540], from: 1, to: 40}},
  {from: 'it07-07', to: 'it07-09', visual: {kind: 'grid'}},
  {from: 'it07-10', to: 'it07-10', visual: {kind: 'grid', pip: {file: FRACTAL, span: [10, 18]}}},
  {from: 'it07-11', to: 'it07-11', visual: {kind: 'grid'}},
  // 08 · sound, motion; one pattern, five meanings
  {from: 'it08-01', to: 'it08-02', visual: {kind: 'clip', file: BITS, span: [121, 143]}},
  {from: 'it08-03', to: 'it08-05', visual: {kind: 'clip', file: BITS, span: [150, 166.3]}},
  {from: 'it08-06', to: 'it08-06', visual: {kind: 'montage', file: BITS, spans: [[168.8, 171.8], [173, 175.8]]}},
  // 09 · how a game is made; the fractal's rule
  {from: 'it09-01', to: 'it09-02', visual: {kind: 'clip', file: GAMES, span: [1, 15]}},
  {from: 'it09-03', to: 'it09-03', visual: {kind: 'clip', file: GAMES, span: [18, 22]}},
  {from: 'it09-04', to: 'it09-04', visual: {kind: 'clip', file: GAMES, span: [21, 41]}},
  {from: 'it09-05', to: 'it09-05', visual: {kind: 'clip', file: GAMES, span: [73, 85]}},
  {from: 'it09-06', to: 'it09-06', visual: {kind: 'clip', file: FRACTAL, span: [0, 6], overlay: 'fractal'}},
  {from: 'it09-07', to: 'it09-07', visual: {kind: 'image', file: 'stills/fractal-main-6.png'}},
  {from: 'it09-08', to: 'it09-08', visual: {kind: 'clip', file: FRACTAL, span: [12, 23.4], overlay: 'fractal'}},
  {from: 'it09-09', to: 'it09-09', visual: {kind: 'clip', file: FRACTAL, span: [23.4, 23.4], dim: 0.45}},
  // 10 · Shannon's ruler
  {from: 'it10-01', to: 'it10-05', visual: {kind: 'grid'}},
  {from: 'it10-06', to: 'it10-07', visual: {kind: 'clip', file: GAMES, span: [1, 15]}},
  {from: 'it10-08', to: 'it10-08', visual: {kind: 'clip', file: GAMES, span: [44, 70]}},
  {from: 'it10-09', to: 'it10-09', visual: {kind: 'grid', pip: {file: FRACTAL, span: [0, 23.4]}}},
  {from: 'it10-10', to: 'it10-10', visual: {kind: 'clip', file: 'nativity.mp4', span: [0, 20]}},
  {from: 'it10-11', to: 'it10-11', visual: {kind: 'grid'}},
  // 11 · back to the two questions
  {from: 'it11-01', to: 'it11-01', visual: {kind: 'clip', file: 'entry.mp4', span: [7, 10.4]}},
  {from: 'it11-02', to: 'it11-02', visual: {kind: 'split',
    left: {kind: 'pixelzoom', file: NATIVITY_STILL, focus: [975, 650], from: 24, to: 24},
    right: {kind: 'clip', file: FRACTAL, span: [10, 20]}}},
  {from: 'it11-03', to: 'it11-03', visual: {kind: 'wall', items: [
    {file: 'stills/pixels-close-64.png', label: {zh: '图画', en: 'Pictures'}},
    {file: 'stills/bits-close-85.png', label: {zh: '字母', en: 'Letters'}},
    {file: 'stills/bits-close-130.png', label: {zh: '声音', en: 'Sound'}},
    {file: 'stills/games-close-68.png', label: {zh: '游戏', en: 'Games'}},
    {file: 'stills/pixels-close-192.png', label: {zh: '立体的形状', en: 'A solid shape'}},
  ]}},
  {from: 'it11-04', to: 'it11-04', visual: {kind: 'clip', file: BITS, span: [15, 21]}},
  {from: 'it11-05', to: 'it11-05', visual: {kind: 'montage', file: PIXELS, spans: [[214, 223], [241, 248.5]]}},
  {from: 'it11-06', to: 'it11-07', visual: {kind: 'clip', file: PIXELS, span: [184, 195], dim: 0.6}},
  {from: 'it11-08', to: 'it11-08', visual: {kind: 'clip', file: 'entry.mp4', span: [0, 3]}},
];

const note = (zh: string, en: string): Card => ({kind: 'note', text: {zh, en}});

/**
 * The switch adder, cue by cue: which switches are on, which rule box is lit, how many rows of the
 * table are showing (`rows`, and when each appears), and the later views of it (current flowing,
 * four adders in a row, a screen full of them). The card picks the state of the latest cue started.
 */
export type AdderState =
  | {a: boolean; b: boolean; then?: [boolean, boolean]; hot?: 'sum' | 'carry'; rows: number; readout?: boolean; flow?: boolean}
  | {view: 'chain' | 'tiles' | 'pixels'};
export const ADDER: Record<string, AdderState> = {
  'it04-01': {a: false, b: false, rows: 0},
  'it04-02': {a: false, b: false, rows: 0},
  'it04-03': {a: true, b: false, hot: 'sum', rows: 0},
  'it04-04': {a: true, b: true, hot: 'carry', rows: 0},
  'it04-05': {a: false, b: false, rows: 1},
  'it04-06': {a: true, b: false, then: [false, true], rows: 3},
  'it04-07': {a: true, b: true, rows: 4, readout: true},
  'it07-07': {a: true, b: true, rows: 4, flow: true},
  'it07-08': {view: 'chain'},
  'it07-09': {view: 'tiles'},
  'it07-10': {view: 'pixels'},
};
/** Which cue reveals each row of the table (row 0: 0+0, 1: 0+1, 2: 1+0, 3: 1+1). */
export const ADDER_ROWS = ['it04-05', 'it04-06', 'it04-06', 'it04-07'];

export const CARDS: Shot<{card: Card}>[] = [
  {from: 'it00-02', to: 'it00-02', card: {kind: 'words', text: Q1}},
  {from: 'it00-05', to: 'it00-05', card: {kind: 'words', text: {zh: '真的是这样吗？', en: 'Is that really so?'}}},
  {from: 'it01-01', to: 'it01-01', card: {kind: 'big', text: '1 + 1 = ?', small: {zh: '计算机怎么算？', en: 'How does a computer add?'}}},
  {from: 'it01-02', to: 'it01-02', card: {kind: 'big', text: '1 + 1 = 2 ?'}},
  {from: 'it01-03', to: 'it01-03', card: note('打开计算机：没有数字，只有电路', 'Inside a computer: no numbers, only circuits')},
  {from: 'it01-04', to: 'it01-04', card: note('线的尽头：一个小小的开关', 'At the end of every line: a tiny switch')},
  {from: 'it02-05', to: 'it02-05', card: {kind: 'words', text: {zh: '比特 = 二选一', en: 'A bit = one choice out of two'}, small: {zh: '它只记一件事：选了哪一个', en: 'It records one thing: which one was chosen'}}},
  {from: 'it02-06', to: 'it02-06', card: note('开关：关 = 0，开 = 1', 'A switch: off = 0, on = 1')},
  {from: 'it03-02', to: 'it03-03', card: {kind: 'carry'}},
  {from: 'it04-01', to: 'it04-07', card: {kind: 'adder'}},
  {from: 'it04-08', to: 'it04-08', card: {kind: 'big', text: '1 + 1 = 10', small: {zh: '二进制，读作“一零”', en: 'binary, read “one, zero”'}}},
  {from: 'it05-02', to: 'it05-02', card: {kind: 'big', text: '65 = ?', small: {zh: '65 自己，没有什么特别的意思', en: 'On its own, 65 means nothing special'}}},
  {from: 'it06-01', to: 'it06-01', card: note('像素：屏幕上最小的一块', 'A pixel: the smallest piece of a screen')},
  {from: 'it06-11', to: 'it06-11', card: note('同样的像素，换一条规则 · 2,400 个三角形，4,060 条边', 'Same pixels, a different rule · 2,400 triangles, 4,060 edges')},
  {from: 'it07-01', to: 'it07-01', card: {kind: 'words', text: Q1}},
  {from: 'it07-03', to: 'it07-03', card: {kind: 'words', text: {zh: '有最小单元：像素', en: 'There is a smallest unit: the pixel'}}},
  {from: 'it07-05', to: 'it07-05', card: note('每放大一次，程序就重新算一张图', 'Every zoom, the program computes a brand-new picture')},
  {from: 'it07-06', to: 'it07-06', card: note('算出来的图，也是有限的像素', 'A computed picture is still a finite set of pixels')},
  {from: 'it07-07', to: 'it07-10', card: {kind: 'adder'}},
  {from: 'it07-11', to: 'it07-11', card: {kind: 'words', text: {zh: '算出来的数，除了颜色，还能变成什么？', en: 'Besides a colour, what else can a computed number become?'}}},
  {from: 'it09-02', to: 'it09-02', card: note('一百多个格子，只有几个数在变', 'Over a hundred squares; only a few numbers change')},
  {from: 'it09-03', to: 'it09-03', card: note('下一帧 = 规则（这几个数）', 'next frame = rules(these few numbers)')},
  {from: 'it09-06', to: 'it09-06', card: {kind: 'big', text: 'z → z² + c', small: {zh: '只有一行公式', en: 'a single line of formula'}}},
  {from: 'it09-07', to: 'it09-07', card: {kind: 'fractal-pixel'}},
  {from: 'it09-09', to: 'it09-09', card: {kind: 'words', text: {zh: '无限不在图里，在规则里。', en: 'The infinity is not in the picture. It is in the rule.'}, small: {zh: '图，每次都是有限的', en: 'The picture is finite every time'}}},
  {from: 'it10-01', to: 'it10-01', card: {kind: 'ruler'}},
  {from: 'it10-02', to: 'it10-03', card: {kind: 'guess'}},
  {from: 'it10-04', to: 'it10-05', card: {kind: 'ruler'}},
  {from: 'it10-06', to: 'it10-06', card: note('要问的只有一件事：按了哪个方向？ ↑ ↓ ← →', 'The only thing to ask: which way was pressed? ↑ ↓ ← →')},
  {from: 'it10-07', to: 'it10-07', card: note('其它格子：规则算出来，不用问 · 一步最多 2 比特', 'Every other square: the rules work it out · at most 2 bits a step')},
  {from: 'it10-08', to: 'it10-08', card: note('121 个点 → 约 7 个问题 · 55 步 → 几百个问题', '121 spots → about 7 questions · 55 moves → a few hundred')},
  {from: 'it10-09', to: 'it10-09', card: {kind: 'words', text: {zh: '知道公式，只要几个数', en: 'Know the formula, and you need only a few numbers'},
    small: {zh: 'c = −0.7436439 + 0.1318259 i  ·  每秒 ×2  ·  24 秒', en: 'c = −0.7436439 + 0.1318259 i  ·  ×2 a second  ·  24 s'}}},
  {from: 'it10-10', to: 'it10-10', card: note('20,000 个三角形，每一个在哪儿都得问', '20,000 triangles, and you must ask where every one is')},
  {from: 'it10-11', to: 'it10-11', card: {kind: 'ruler'}},
  {from: 'it11-01', to: 'it11-01', card: {kind: 'big', text: '1 + 1 = 10', small: {zh: '两个开关算出来的', en: 'computed by two switches'}}},
  {from: 'it11-02', to: 'it11-02', card: {kind: 'words', text: {zh: '图有最小单元，无限在规则里', en: 'A picture has a smallest unit; the infinity is in the rule'}}},
  {from: 'it11-06', to: 'it11-06', card: {kind: 'words', text: {zh: '再复杂的图像，背后也是许多小小的像素，按规则排在一起。',
    en: 'However complex a picture is, behind it are many tiny pixels, arranged by a rule.'}}},
  {from: 'it11-07', to: 'it11-07', card: {kind: 'words', text: {zh: '下一次，接着香农的问题往下走', en: 'Next time, Shannon’s question a little further'}, small: INTRO.series}},
];

/** The fractal pixel shown in it09-07: fractal-main.mp4 at 6 s (×64), computed by mandelbrot_zoom.py. */
export const FRACTAL_PIXEL = {at: [812, 472] as [number, number], c: '−0.74797 + 0.13380 i', iterations: 227, rgb: [140, 235, 189]};

/** Shannon's ruler (it10): stations, revealed when their cue starts. */
export const RULER: {value: string; label: Label; at: string}[] = [
  {value: '0', label: {zh: '两面都是正面的硬币', en: 'A coin with two heads'}, at: 'it10-05'},
  {value: '1', label: {zh: '抛一次普通硬币', en: 'One toss of a normal coin'}, at: 'it10-05'},
  {value: '2', label: {zh: '贪吃蛇走一步', en: 'One Snake step'}, at: 'it10-07'},
  {value: '3', label: {zh: '猜 1 到 8', en: 'Guess 1 to 8'}, at: 'it10-04'},
  {value: '~100', label: {zh: '整段分形视频', en: 'The whole fractal clip'}, at: 'it10-09'},
  {value: '~400', label: {zh: '一整盘五子棋', en: 'A whole Gomoku game'}, at: 'it10-08'},
  {value: '几百万', label: {zh: '一个 3D 扫描', en: 'A 3D scan'}, at: 'it10-10'},
];
export const RULER_MILLIONS_EN = 'millions';
