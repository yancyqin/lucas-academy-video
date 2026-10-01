/**
 * Picture plan for "Why Did Van Gogh Paint Them?" (lucas-academy-media#3).
 *
 * Every picture is a real work — Van Gogh's paintings, drawings and letter
 * sketches, plus one earlier fresco for the halo — never a generated image.
 * A shot covers cues `from`..`to` (inclusive) and is timed by the narration.
 * Camera keys are in painting coordinates: x/y are 0–1 across the image,
 * z = 1 shows the whole painting.
 */

export type Label = {zh: string; en: string};

export type Cam = {t: number; x: number; y: number; z: number};

type Work = {w: number; h: number; title: Label; meta: string};

/** Pixel sizes are the files' in public/vg-why-paint-them/art (sources in SOURCES.txt). */
export const ART = {
  roulin: {w: 1514, h: 1960, title: {zh: '《邮差鲁兰》', en: 'Portrait of Postman Roulin'}, meta: '1888 · Detroit Institute of Arts'},
  'roulin-seated': {w: 1787, h: 2233, title: {zh: '《邮差约瑟夫·鲁兰》', en: 'The Postman Joseph Roulin'}, meta: '1888 · Museum of Fine Arts, Boston'},
  'roulin-moma': {w: 3840, h: 4537, title: {zh: '《约瑟夫·鲁兰》', en: 'Portrait of Joseph Roulin'}, meta: '1889 · The Museum of Modern Art'},
  'roulin-kmm': {w: 3650, h: 4410, title: {zh: '《约瑟夫·鲁兰》', en: 'Portrait of Joseph Roulin'}, meta: '1889 · Kröller-Müller Museum'},
  'roulin-drawing': {w: 3840, h: 5052, title: {zh: '《约瑟夫·鲁兰》素描', en: 'Joseph Roulin, drawing'}, meta: '1888 · J. Paul Getty Museum'},
  'berceuse-met': {w: 2901, h: 3710, title: {zh: '《摇篮曲（鲁兰夫人）》', en: 'La Berceuse (Augustine Roulin)'}, meta: '1889 · The Metropolitan Museum of Art'},
  'berceuse-kmm': {w: 1333, h: 1722, title: {zh: '《摇篮曲（鲁兰夫人）》', en: 'La Berceuse (Augustine Roulin)'}, meta: '1889 · Kröller-Müller Museum'},
  'mother-baby': {w: 2955, h: 3689, title: {zh: '《鲁兰夫人和她的宝宝》', en: 'Madame Roulin and Her Baby'}, meta: '1888 · The Metropolitan Museum of Art'},
  'armand-folkwang': {w: 2074, h: 2500, title: {zh: '《阿尔芒·鲁兰》', en: 'Armand Roulin'}, meta: '1888 · Museum Folkwang'},
  'armand-boijmans': {w: 3763, h: 4770, title: {zh: '《阿尔芒·鲁兰》', en: 'Armand Roulin'}, meta: '1888 · Museum Boijmans Van Beuningen'},
  camille: {w: 2480, h: 3084, title: {zh: '《卡米耶·鲁兰》', en: 'Camille Roulin'}, meta: '1888 · Van Gogh Museum'},
  marcelle: {w: 3840, h: 5514, title: {zh: '《马塞勒·鲁兰》', en: 'Marcelle Roulin'}, meta: '1888 · Van Gogh Museum'},
  'marcelle-private': {w: 1358, h: 2000, title: {zh: '《马塞勒·鲁兰》', en: 'Marcelle Roulin'}, meta: '1888 · private collection'},
  boch: {w: 3840, h: 5281, title: {zh: '《诗人（欧仁·博赫）》', en: 'The Poet (Eugène Boch)'}, meta: "1888 · Musée d'Orsay, Paris"},
  selfportrait: {w: 2481, h: 3008, title: {zh: '《自画像（灰毡帽）》', en: 'Self-Portrait with Grey Felt Hat'}, meta: '1887 · Van Gogh Museum'},
  sunflowers: {w: 3840, h: 4882, title: {zh: '《向日葵》', en: 'Sunflowers'}, meta: '1888 · The National Gallery, London'},
  sower: {w: 3579, h: 2853, title: {zh: '《播种者》', en: 'The Sower'}, meta: '1888 · Kröller-Müller Museum'},
  almond: {w: 3139, h: 2480, title: {zh: '《盛开的杏花》', en: 'Almond Blossom'}, meta: '1890 · Van Gogh Museum'},
  starry: {w: 3840, h: 3041, title: {zh: '《星空》', en: 'The Starry Night'}, meta: '1889 · The Museum of Modern Art'},
  'starry-rhone': {w: 3840, h: 2976, title: {zh: '《罗讷河上的星夜》', en: 'Starry Night over the Rhône'}, meta: "1888 · Musée d'Orsay, Paris"},
  'wheat-cypresses': {w: 3747, h: 2944, title: {zh: '《有柏树的麦田》', en: 'Wheat Field with Cypresses'}, meta: '1889 · The Metropolitan Museum of Art'},
  irises: {w: 3840, h: 2965, title: {zh: '《鸢尾花》', en: 'Irises'}, meta: '1889 · J. Paul Getty Museum'},
  mousme: {w: 3270, h: 4000, title: {zh: '《少女》', en: 'La Mousmé'}, meta: '1888 · National Gallery of Art, Washington'},
  arlesienne: {w: 2851, h: 3592, title: {zh: '《阿尔勒女人（吉诺夫人）》', en: "L'Arlésienne (Madame Ginoux)"}, meta: '1888–89 · The Metropolitan Museum of Art'},
  'bedroom-letter': {w: 3840, h: 2410, title: {zh: '给提奥的信里的《卧室》草图', en: 'The Bedroom, sketched in a letter to Theo'}, meta: 'Letter 705 · 1888-10-16 · Van Gogh Museum'},
  bedroom: {w: 3840, h: 3047, title: {zh: '《卧室》', en: 'The Bedroom'}, meta: '1888 · Van Gogh Museum'},
  'hospital-ward': {w: 2048, h: 1591, title: {zh: '《阿尔勒医院的病房》', en: 'Ward in the Hospital in Arles'}, meta: '1889 · Oskar Reinhart Collection, Winterthur'},
  'yellow-house': {w: 3840, h: 2979, title: {zh: '《黄房子》——他在阿尔勒的家', en: 'The Yellow House, his home in Arles'}, meta: '1888 · Van Gogh Museum'},
  giotto: {w: 1000, h: 925, title: {zh: '乔托《哀悼基督》', en: 'Giotto, Lamentation'}, meta: 'c. 1305 · Scrovegni Chapel, Padua'},
  'first-steps': {w: 1907, h: 1507, title: {zh: '《第一步（仿米勒）》', en: 'First Steps, after Millet'}, meta: '1890 · The Metropolitan Museum of Art'},
  'potato-eaters': {w: 3840, h: 2929, title: {zh: '《吃土豆的人》', en: 'The Potato Eaters'}, meta: '1885 · Van Gogh Museum'},
} satisfies Record<string, Work>;

export type ArtId = keyof typeof ART;

/** A picture on a wall or in a row: a work, with an optional label under it. */
export type Tile = {art: ArtId; label?: Label};

export type Shot = {from: string; to: string} & (
  | {kind: 'art'; art: ArtId; cam: Cam[]; chip?: boolean | Label; overlay?: 'starry-lines'}
  | {kind: 'pair'; left: Tile; right: Tile}
  | {kind: 'namecard'}
  | {kind: 'quote'; art: ArtId; cam: Cam; quote: Label; source: string}
  | {kind: 'letter'; art: ArtId; cam: Cam; source: Label}
  | {kind: 'row'; tiles: Tile[]; caption?: Label}
  | {kind: 'wall'; tiles: Tile[]; caption?: Label}
  | {kind: 'dissolve'; a: ArtId; b: ArtId; camA: Cam[]; camB: Cam[]; tag?: Label}
  | {kind: 'lesson'; n: number}
  | {kind: 'lessons-title'}
  | {kind: 'lessons-grid'}
);

const FULL = (t: number, z = 1): Cam => ({t, x: 0.5, y: 0.5, z});

/** Four lessons, then the ones still being planned (vg10-09). */
export const LESSONS: {art: ArtId; title: Label; more?: boolean}[] = [
  {art: 'first-steps', title: {zh: '珍惜的时刻', en: 'A cherished moment'}},
  {art: 'sower', title: {zh: '表达希望', en: 'Showing a hope'}},
  {art: 'roulin-drawing', title: {zh: '认真观察', en: 'Looking carefully'}},
  {art: 'potato-eaters', title: {zh: '看见普通人', en: 'Seeing ordinary people'}},
  {art: 'sunflowers', title: {zh: '更多课程构思中', en: 'More lessons on the way'}, more: true},
];

const t = (art: ArtId, zh?: string, en?: string): Tile => (zh && en ? {art, label: {zh, en}} : {art});

/** Everything he painted of the Roulins that the video shows (not a complete count). */
const ROULIN_FAMILY: Tile[] = [
  t('roulin'), t('roulin-seated'), t('roulin-drawing'), t('roulin-kmm'), t('roulin-moma'),
  t('berceuse-met'), t('mother-baby'), t('berceuse-kmm'),
  t('armand-folkwang'), t('armand-boijmans'), t('camille'), t('marcelle'), t('marcelle-private'),
];

export const SHOTS: Shot[] = [
  // VG01 · 开场
  {from: 'vg01-01', to: 'vg01-02', kind: 'pair', left: {art: 'roulin', label: ART.roulin.title}, right: {art: 'boch', label: ART.boch.title}},
  {from: 'vg01-03', to: 'vg01-03', kind: 'art', art: 'roulin',
    cam: [{t: 0, x: 0.49, y: 0.56, z: 2.1}, {t: 0.45, x: 0.49, y: 0.5, z: 2.1}, {t: 1, x: 0.49, y: 0.24, z: 2.5}]},
  {from: 'vg01-04', to: 'vg01-04', kind: 'art', art: 'boch', cam: [FULL(0, 1.05), {t: 1, x: 0.22, y: 0.14, z: 2.4}]},
  {from: 'vg01-05', to: 'vg01-05', kind: 'pair', left: {art: 'roulin'}, right: {art: 'boch'}},

  // VG02 · 梵高是谁？ — what he painted, and the letters that tell us what he thought.
  {from: 'vg02-01', to: 'vg02-01', kind: 'namecard'},
  {from: 'vg02-02', to: 'vg02-02', kind: 'row', tiles: [
    t('starry-rhone', '星空', 'stars'), t('wheat-cypresses', '麦田', 'fields'),
    t('irises', '花', 'flowers'), t('mousme', '普通人', 'ordinary people'),
  ]},
  {from: 'vg02-03', to: 'vg02-03', kind: 'art', art: 'bedroom-letter', cam: [FULL(0), FULL(1, 1.1)], chip: true},
  {from: 'vg02-04', to: 'vg02-04', kind: 'pair',
    left: {art: 'bedroom-letter', label: {zh: '信里的草图', en: 'Sketch in the letter'}},
    right: {art: 'bedroom', label: {zh: '画出来的《卧室》', en: 'The painting'}}},

  // VG03 · 鲁兰 — then the whole family, again and again.
  {from: 'vg03-01', to: 'vg03-02', kind: 'art', art: 'roulin', cam: [FULL(0), {t: 1, x: 0.49, y: 0.45, z: 1.3}]},
  {from: 'vg03-03', to: 'vg03-03', kind: 'art', art: 'roulin', cam: [FULL(0), FULL(1, 1.04)], chip: true},
  {from: 'vg03-04', to: 'vg03-04', kind: 'art', art: 'roulin',
    cam: [
      {t: 0, x: 0.49, y: 0.24, z: 2.5}, {t: 0.3, x: 0.49, y: 0.24, z: 2.5},
      {t: 0.55, x: 0.52, y: 0.83, z: 2.3}, {t: 0.72, x: 0.52, y: 0.83, z: 2.3},
      {t: 1, x: 0.48, y: 0.58, z: 2.2},
    ]},
  {from: 'vg03-05', to: 'vg03-05', kind: 'quote', art: 'roulin', cam: {t: 0, x: 0.48, y: 0.4, z: 1.6},
    quote: {zh: '“一个比许多人更有意思的人”', en: '“A more interesting man than many people.”'},
    source: 'Letter 652 · 1888-07-31'},
  {from: 'vg03-06', to: 'vg03-06', kind: 'row', tiles: [
    t('berceuse-met', '妻子 奥古斯汀', 'his wife Augustine'), t('armand-folkwang', '大儿子 阿尔芒', 'Armand, the eldest'),
    t('camille', '二儿子 卡米耶', 'Camille'), t('marcelle', '小女儿 马塞勒', 'baby Marcelle'),
  ]},
  {from: 'vg03-07', to: 'vg03-07', kind: 'wall', tiles: ROULIN_FAMILY,
    caption: {zh: '梵高为鲁兰一家画的部分作品', en: 'Some of his portraits of the Roulin family'}},

  // VG04 · 朋友怎样照顾他？ — the hospital, his home, his room, the letter.
  {from: 'vg04-01', to: 'vg04-01', kind: 'art', art: 'roulin', cam: [FULL(0), {t: 1, x: 0.47, y: 0.36, z: 1.9}]},
  {from: 'vg04-02', to: 'vg04-02', kind: 'dissolve', a: 'hospital-ward', b: 'yellow-house',
    camA: [FULL(0, 1.04), {t: 1, x: 0.5, y: 0.55, z: 1.15}], camB: [FULL(0, 1.08), {t: 1, x: 0.44, y: 0.46, z: 1.18}]},
  {from: 'vg04-03', to: 'vg04-03', kind: 'letter', art: 'bedroom', cam: {t: 0, x: 0.5, y: 0.5, z: 1.05},
    source: {zh: '梵高写给弟弟提奥的信', en: 'Letter 729 · 1889-01-04 · to his brother Theo'}},
  {from: 'vg04-04', to: 'vg04-05', kind: 'art', art: 'roulin-kmm', cam: [{t: 0, x: 0.5, y: 0.36, z: 1.6}, FULL(0.7), FULL(1)], chip: true},

  // VG05 · 博赫
  {from: 'vg05-01', to: 'vg05-01', kind: 'art', art: 'boch', cam: [FULL(0, 1.1), FULL(1)]},
  {from: 'vg05-02', to: 'vg05-03', kind: 'art', art: 'boch', cam: [FULL(0), {t: 1, x: 0.47, y: 0.34, z: 1.5}], chip: true},
  {from: 'vg05-04', to: 'vg05-04', kind: 'art', art: 'boch',
    cam: [
      {t: 0, x: 0.5, y: 0.8, z: 2.2}, {t: 0.4, x: 0.5, y: 0.8, z: 2.2},
      {t: 0.75, x: 0.8, y: 0.2, z: 2.4}, {t: 1, x: 0.8, y: 0.2, z: 2.5},
    ]},
  {from: 'vg05-05', to: 'vg05-05', kind: 'art', art: 'boch', cam: [{t: 0, x: 0.5, y: 0.45, z: 1.4}, FULL(0.6), FULL(1)]},

  // VG06 · 我画出无限 — a room, then a sky much larger than a room.
  {from: 'vg06-01', to: 'vg06-02', kind: 'art', art: 'boch', cam: [FULL(0), {t: 1, x: 0.47, y: 0.3, z: 1.8}]},
  {from: 'vg06-03', to: 'vg06-03', kind: 'art', art: 'boch', cam: [{t: 0, x: 0.47, y: 0.2, z: 2.4}, {t: 1, x: 0.5, y: 0.2, z: 1.6}]},
  {from: 'vg06-04', to: 'vg06-04', kind: 'quote', art: 'boch', cam: {t: 0, x: 0.5, y: 0.3, z: 1.4},
    quote: {zh: '“我画出无限。”', en: '“I paint the infinite.”'}, source: 'Letter 663 · 1888-08-18'},
  {from: 'vg06-05', to: 'vg06-06', kind: 'dissolve', a: 'bedroom', b: 'starry-rhone',
    camA: [FULL(0, 1.12), FULL(1, 1.0)], camB: [FULL(0, 1.0), {t: 1, x: 0.5, y: 0.38, z: 1.2}],
    tag: {zh: '书信构想示意', en: 'Picturing the idea in the letter'}},

  // VG07 · 颜色也会说话 — a lullaby in colour, an old halo, then colour itself.
  {from: 'vg07-01', to: 'vg07-01', kind: 'letter', art: 'berceuse-met', cam: {t: 0, x: 0.5, y: 0.45, z: 1.1},
    source: {zh: '书信转述', en: 'Letter 673 · 1888-09-03 · paraphrased'}},
  {from: 'vg07-02', to: 'vg07-02', kind: 'art', art: 'giotto', cam: [FULL(0), {t: 1, x: 0.47, y: 0.6, z: 1.7}], chip: true},
  {from: 'vg07-03', to: 'vg07-03', kind: 'art', art: 'berceuse-met', cam: [FULL(0), {t: 1, x: 0.5, y: 0.3, z: 1.45}], chip: true},
  {from: 'vg07-04', to: 'vg07-04', kind: 'art', art: 'boch',
    cam: [{t: 0, x: 0.5, y: 0.82, z: 2}, {t: 0.5, x: 0.25, y: 0.3, z: 2}, {t: 1, x: 0.1, y: 0.06, z: 2.8}]},
  {from: 'vg07-05', to: 'vg07-05', kind: 'art', art: 'boch', cam: [FULL(0, 1.15), FULL(1)]},

  // VG08 · 杏花
  {from: 'vg08-01', to: 'vg08-01', kind: 'art', art: 'almond', cam: [FULL(0, 1.08), FULL(1)]},
  {from: 'vg08-02', to: 'vg08-02', kind: 'art', art: 'almond', cam: [FULL(0), FULL(1, 1.05)],
    chip: {zh: '送给小侄子的礼物', en: 'A gift for his nephew'}},
  {from: 'vg08-03', to: 'vg08-03', kind: 'art', art: 'almond', cam: [{t: 0, x: 0.6, y: 0.27, z: 2.4}, {t: 1, x: 0.36, y: 0.5, z: 2.2}]},
  {from: 'vg08-04', to: 'vg08-04', kind: 'art', art: 'almond', cam: [{t: 0, x: 0.45, y: 0.45, z: 1.5}, FULL(1)], chip: true},

  // VG09 · 星空
  {from: 'vg09-01', to: 'vg09-01', kind: 'art', art: 'starry', cam: [FULL(0, 1.08), FULL(1)], chip: true},
  {from: 'vg09-02', to: 'vg09-02', kind: 'art', art: 'starry', cam: [FULL(0), FULL(1)], overlay: 'starry-lines'},
  {from: 'vg09-03', to: 'vg09-03', kind: 'art', art: 'starry', cam: [FULL(0), FULL(1, 1.06)]},
  {from: 'vg09-04', to: 'vg09-04', kind: 'art', art: 'starry', cam: [FULL(0, 1.06), FULL(1)]},
  {from: 'vg09-05', to: 'vg09-05', kind: 'art', art: 'starry', cam: [{t: 0, x: 0.58, y: 0.8, z: 2}, {t: 1, x: 0.56, y: 0.78, z: 2.2}]},
  {from: 'vg09-06', to: 'vg09-06', kind: 'art', art: 'starry', cam: [{t: 0, x: 0.53, y: 0.4, z: 2}, {t: 1, x: 0.55, y: 0.38, z: 2.3}]},
  {from: 'vg09-07', to: 'vg09-07', kind: 'art', art: 'starry', cam: [FULL(0, 1.3), FULL(1)]},

  // VG10 · 课程 — each lesson with one of his works.
  {from: 'vg10-01', to: 'vg10-03', kind: 'lessons-title'},
  {from: 'vg10-04', to: 'vg10-04', kind: 'lesson', n: 0},
  {from: 'vg10-05', to: 'vg10-05', kind: 'lesson', n: 1},
  {from: 'vg10-06', to: 'vg10-06', kind: 'lesson', n: 2},
  {from: 'vg10-07', to: 'vg10-07', kind: 'lesson', n: 3},
  {from: 'vg10-09', to: 'vg10-09', kind: 'lesson', n: 4},
  {from: 'vg10-10', to: 'vg10-11', kind: 'lessons-grid'},

  // VG11 · 结尾 — the people he kept in his paintings.
  {from: 'vg11-01', to: 'vg11-01', kind: 'wall', tiles: [
    t('roulin'), t('berceuse-met'), t('boch'), t('armand-folkwang'), t('camille'), t('marcelle'),
    t('arlesienne'), t('mousme'), t('roulin-kmm'), t('mother-baby'), t('armand-boijmans'),
  ], caption: {zh: '他画下的身边的人', en: 'People close to him, in his paintings'}},
  {from: 'vg11-02', to: 'vg11-03', kind: 'pair', left: {art: 'roulin'}, right: {art: 'boch'}},
];
