/**
 * Picture plan for "全人教育①：老师的权柄从哪里来？" (lucas-academy-media#5).
 *
 * A shot covers cues `from`..`to` (inclusive) and is timed by the narration
 * timeline. Pictures are Codex concept images (public/whole-person-01/concept)
 * or stock footage (public/whole-person-01/footage); a missing file shows a
 * labelled placeholder, and missing footage falls back to its concept image.
 * All words on screen are typeset here, never drawn into a picture.
 */

export type Label = {zh: string; en: string};

/** Slow camera on a concept image: zoom from→to, drifting toward (x, y) in 0–1. */
export type Drift = {z0: number; z1: number; x: number; y: number};

export type Picture =
  | {kind: 'concept'; image: string; next?: string; drift?: Drift}
  | {kind: 'footage'; file: string; fallback: string}
  | {kind: 'panels'; images: string[]; reveal: string[]};

export type Card =
  | {kind: 'scripture'; text: Label; source: Label}
  | {kind: 'words'; text: Label}
  | {kind: 'questions'; items: Label[]; reveal: string[]}
  | {kind: 'math'};

export type Shot = {
  from: string;
  to: string;
  picture: Picture;
  /** "概念示意 / Concept illustration" chip for invented classroom scenes. */
  concept?: boolean;
  /** Scripture reference chip, top right. */
  ref?: Label;
  card?: Card;
  /** Card appears from this cue (defaults to `from`). */
  cardFrom?: string;
};

const PUSH: Drift = {z0: 1, z1: 1.06, x: 0.5, y: 0.45};

export const TITLE_IMAGE = 'wp01-classroom.png';

export const SHOTS: Shot[] = [
  // WP01 · 老师说的话，都对吗？
  {from: 'wp01-01', to: 'wp01-03', concept: true,
    picture: {kind: 'concept', image: 'wp01-classroom.png', drift: {z0: 1.02, z1: 1.14, x: 0.62, y: 0.4}}},
  {from: 'wp01-04', to: 'wp01-04', concept: true,
    picture: {kind: 'concept', image: 'wp01-classroom.png', drift: {z0: 1.14, z1: 1.18, x: 0.62, y: 0.4}},
    card: {kind: 'words', text: {zh: '教育的权柄，从哪里来？', en: 'Where does the authority to teach come from?'}}},

  // WP02 · 一切属于神
  {from: 'wp02-01', to: 'wp02-01',
    picture: {kind: 'footage', file: 'wp02-light.mp4', fallback: 'wp02-light.png'},
    card: {kind: 'scripture',
      text: {zh: '因为国度、权柄、荣耀，全是你的，直到永远。阿们！',
        en: 'For yours is the kingdom and the power and the glory forever. Amen.'},
      source: {zh: '马太福音 6:13（和合本）', en: 'Matthew 6:13 (NIV footnote)'}}},
  {from: 'wp02-02', to: 'wp02-04', concept: true,
    picture: {kind: 'concept', image: 'wp02-home-classroom.png', drift: PUSH},
    card: {kind: 'words', text: {zh: '一切属于神', en: 'Everything belongs to God'}}},

  // WP03 · 老师先受教，再教人
  {from: 'wp03-01', to: 'wp03-02', concept: true, ref: {zh: '马太福音 28:18–20', en: 'Matthew 28:18–20'},
    picture: {kind: 'concept', image: 'wp03-read-first.png', drift: {z0: 1, z1: 1.08, x: 0.4, y: 0.45}}},
  {from: 'wp03-03', to: 'wp03-03', concept: true,
    picture: {kind: 'concept', image: 'wp03-read-first.png', drift: {z0: 1.08, z1: 1.12, x: 0.4, y: 0.45}},
    card: {kind: 'words', text: {zh: '教导的权柄是领受的', en: 'The authority to teach is received'}}},
  {from: 'wp03-04', to: 'wp03-05', concept: true, ref: {zh: '马太福音 13:52', en: 'Matthew 13:52'},
    picture: {kind: 'concept', image: 'wp03-read-first.png', next: 'wp03-read-together.png', drift: PUSH}},

  // WP04 · 一起查一查
  {from: 'wp04-01', to: 'wp04-01', ref: {zh: '使徒行传 17:11', en: 'Acts 17:11'},
    picture: {kind: 'footage', file: 'wp04-pages.mp4', fallback: 'wp04-pages.png'}},
  {from: 'wp04-03', to: 'wp04-06', concept: true,
    picture: {kind: 'concept', image: 'wp04-look-together.png', drift: {z0: 1, z1: 1.1, x: 0.5, y: 0.55}}},

  // WP05 · 孩子也能帮助老师
  {from: 'wp05-01', to: 'wp05-03', concept: true, ref: {zh: '马太福音 11:25', en: 'Matthew 11:25'},
    picture: {kind: 'concept', image: 'wp05-children.png', drift: PUSH}},
  {from: 'wp05-04', to: 'wp05-07', concept: true,
    picture: {kind: 'concept', image: 'wp05-listen.png', drift: {z0: 1, z1: 1.12, x: 0.6, y: 0.45}}},

  // WP06 · 老师仍然要负责
  {from: 'wp06-01', to: 'wp06-01', concept: true,
    picture: {kind: 'concept', image: 'wp06-help.png', drift: PUSH}},
  {from: 'wp06-02', to: 'wp06-02', concept: true,
    picture: {kind: 'panels', images: ['wp06-help.png', 'wp06-protect.png', 'wp06-explain.png'], reveal: ['wp06-02', 'wp06-02', 'wp06-02']}},
  {from: 'wp06-03', to: 'wp06-04', concept: true, cardFrom: 'wp06-04',
    picture: {kind: 'concept', image: 'wp06-explain.png', drift: PUSH},
    card: {kind: 'math'}},

  // WP07 · 给别人打开学习的门
  {from: 'wp07-01', to: 'wp07-01', ref: {zh: '路加福音 11:52', en: 'Luke 11:52'},
    picture: {kind: 'footage', file: 'wp07-key-door.mp4', fallback: 'wp07-key-door.png'}},
  {from: 'wp07-02', to: 'wp07-02', concept: true,
    picture: {kind: 'concept', image: 'wp07-invite.png', drift: {z0: 1, z1: 1.06, x: 0.5, y: 0.5}}},
  {from: 'wp07-03', to: 'wp07-05', concept: true,
    picture: {kind: 'concept', image: 'wp07-invite.png', drift: {z0: 1.06, z1: 1.12, x: 0.35, y: 0.5}},
    card: {kind: 'questions', reveal: ['wp07-03', 'wp07-04', 'wp07-05'], items: [
      {zh: '谁还没有被听见？', en: 'Who has not been heard?'},
      {zh: '谁需要多一点帮助？', en: 'Who needs more help?'},
      {zh: '还有什么问题，值得一起看看？', en: 'What other question should we explore together?'},
    ]}},

  // WP08 · 用权柄服事
  {from: 'wp08-01', to: 'wp08-02', ref: {zh: '约翰福音 13:13–14', en: 'John 13:13–14'}, cardFrom: 'wp08-02',
    picture: {kind: 'footage', file: 'wp08-basin.mp4', fallback: 'wp08-basin.png'},
    card: {kind: 'words', text: {zh: '彼此服事', en: 'Serve one another'}}},
  {from: 'wp08-03', to: 'wp08-05', concept: true,
    picture: {kind: 'concept', image: 'wp08-listen.png', drift: PUSH}},

  // WP09 · 一间课堂，可以怎样改变？
  {from: 'wp09-01', to: 'wp09-06', concept: true,
    picture: {kind: 'panels', images: ['wp09-a-ask.png', 'wp09-b-example.png', 'wp09-c-add.png'], reveal: ['wp09-02', 'wp09-03', 'wp09-04']}},

  // WP10 · 结尾
  {from: 'wp10-01', to: 'wp10-02', concept: true,
    picture: {kind: 'concept', image: 'wp10-four.png', drift: {z0: 1.08, z1: 1, x: 0.5, y: 0.5}}},
  {from: 'wp10-03', to: 'wp10-04', concept: true,
    picture: {kind: 'concept', image: 'wp10-four.png', drift: {z0: 1, z1: 1, x: 0.5, y: 0.5}},
    card: {kind: 'questions', reveal: ['wp10-03', 'wp10-04'], items: [
      {zh: '今天你能帮助谁？', en: 'Whom can you help today?'},
      {zh: '你又愿意听谁多说一句呢？', en: 'Whose words will you make time to hear?'},
    ]}},
];
