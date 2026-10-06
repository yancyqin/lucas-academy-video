/**
 * Picture plan for "全人教育的五个理念 / Five Principles of Whole-Person
 * Education" (lucas-academy-media#5), following the parents deck
 * (lucasacademy.org/presentation/?deck=parents).
 *
 * Each section plays its app recording as a dimmed, blurred background under
 * the cards; a demo shot brings a recording up full and sharp. Footage and
 * images live in public/whole-person-01/{footage,images}; anything missing
 * renders as a labelled placeholder. All words on screen are typeset here.
 */

export type Label = {zh: string; en: string};

/** A recording, `from` seconds in; `fit: 'contain'` letterboxes over a blurred copy. */
export type Clip = {file: string; from?: number; fit?: 'cover' | 'contain'};

export type Card =
  | {kind: 'principle'; n: number; title: Label; subtitle?: Label}
  | {kind: 'words'; text: Label; small?: Label; kicker?: Label}
  | {kind: 'quote'; text: Label; source: Label}
  | {kind: 'scripture'; text: Label; source: Label}
  | {kind: 'list'; items: Label[]; reveal: string[]; heading?: Label}
  | {kind: 'steps'; reveal: [string, string]}
  | {kind: 'drawing'; who: Label; sketch: string; final: string; finished?: string}
  | {kind: 'image'; file: string; caption: Label}
  | {kind: 'contrast'; kicker?: Label; heading: Label; yes: {term: Label; gloss: Label}; no: {term: Label; gloss: Label}}
  | {kind: 'question'; question: BigQuestion};

export type Shot = {
  from: string;
  to: string;
  /** Full-screen recording (background goes clear underneath); no caption = quiet montage shot. */
  demo?: Clip & {caption?: Label; url?: string};
  card?: Card;
};

/** Background recording for each section, dimmed under the cards. */
/** A big title question: [before, highlight, after] on line one, an optional line two. */
export type BigQuestion = {first: Record<'zh' | 'en', [string, string, string]>; second?: Label};

/** The question the film opens on, answers at principle 1, and the YouTube cover asks (owner 2026-10-06);
 * two lines, the line-end comma dropped. */
export const QUESTION: BigQuestion = {
  first: {zh: ['孩子说', '“不”', ''], en: ['Your Child Says ', '“No.”', '']},
  second: {zh: '你怎么办？', en: 'Now What?'},
};

/** The question answered first, in the same big type. */
export const EDUCATOR: BigQuestion = {first: {zh: ['谁是', '教育者', '？'], en: ['Who Is an ', 'Educator', '?']}};

/** The opening (owner 2026-10-06): the first frame is the cover — the question, big — plus what the cover
 * leaves out: Lucas Academy, the film's name and the byline. It stays through 「在回答这个问题之前……」; then
 * 「谁是教育者？」 big, until the answer begins. The transit chamber (avatar hidden) runs underneath. */
export const INTRO = {
  chamber: {file: 'transit-chamber.mp4', from: 0} as Clip,
  name: {zh: '全人教育的五个理念', en: 'Five Principles of Whole-Person Education'} as Label,
  byline: {zh: 'By Lucas Academy Team', en: 'By Lucas Academy Team'} as Label,
  /** The opening card gives way to 「谁是教育者？」 as this line starts… */
  coverUntil: 'wp00-01',
  /** …which leaves as this one starts. */
  educatorUntil: 'wp00-02',
  last: 'wp00-03',
};

export const SECTION_BG: Record<string, Clip> = {
  wp00: {file: 'journey-of-art.mp4', from: 8},
  wp01: {file: 'journey-of-art.mp4', from: 50},
  wp02: {file: 'live-painting.mp4', from: 0},
  wp03: {file: 'language-bridge.mp4', from: 0},
  wp04: {file: 'van-gogh-room.mp4', from: 22, fit: 'contain'},
  wp05: {file: 'snake-ranking.mp4', from: 30},
  wp06: {file: 'journey-of-art.mp4', from: 88},
};

export const PRINCIPLES: Label[] = [
  {zh: '权柄', en: 'Authority'},
  {zh: '目标', en: 'Purpose'},
  {zh: '互教互学', en: 'Learning from each other'},
  {zh: '引导探索', en: 'Guided discovery'},
  {zh: '你来作主', en: 'You are the boss'},
];

const FIVE = ['wp00-08', 'wp00-08', 'wp00-08', 'wp00-08', 'wp00-08'];

export const SHOTS: Shot[] = [
  // 开场白：问句「谁是教育者？」后停顿，片名在问句时仍在；第二句起换成这张卡
  {from: 'wp00-02', to: 'wp00-03',
    card: {kind: 'words', text: {zh: '老师、父母、朋友，孩子都可以是教育者。', en: 'Teachers, parents, friends, and kids can all be educators.'},
      small: {zh: '如果你这样想，这个视频，就是给你的。', en: 'If you see it that way, this video is for you.'}}},

  // 开头 · 天国的管家
  {from: 'wp00-04', to: 'wp00-04',
    card: {kind: 'words', text: {zh: '学习是拥有，而不是被喂养。', en: 'Learning is about owning, not being fed.'}}},
  {from: 'wp00-05', to: 'wp00-05',
    card: {kind: 'quote',
      text: {zh: '教育是在一个人完全忘记了他在学校所学的一切之后，仍然留下来的东西。',
        en: '“Education is that which remains, if one has forgotten everything he learned in school.”'},
      source: {zh: '爱因斯坦引用，《论教育》（1936）', en: 'Quoted by Einstein, “On Education” (1936)'}}},
  {from: 'wp00-06', to: 'wp00-06',
    card: {kind: 'scripture',
      text: {zh: '凡文士受教作天国的门徒，就像一个家主从他库里拿出新旧的东西来。',
        en: 'Therefore every teacher of the law who has become a disciple in the kingdom of heaven is like the owner of a house who brings out of his storeroom new treasures as well as old.'},
      source: {zh: '马太福音 13:52 · 和合本', en: 'Matthew 13:52 · NIV'}}},
  {from: 'wp00-07', to: 'wp00-07',
    card: {kind: 'words', text: {zh: '真正懂得怎样做主人，而不是被塑造', en: 'Truly learning to be the owner, rather than being shaped'},
      small: {zh: 'Lucas Academy 的团队相信', en: 'What the Lucas Academy team believes'}}},
  {from: 'wp00-08', to: 'wp00-08',
    card: {kind: 'list', heading: {zh: '全人教育的五个理念', en: 'Five principles of whole-person education'}, items: PRINCIPLES, reveal: FIVE}},

  // 理念 1 · 权柄
  // 回到开头的问题：「现在我们回答最开始的问题……它关乎……」，停顿，然后揭晓权柄
  {from: 'wp01-00', to: 'wp01-00a', card: {kind: 'question', question: QUESTION}},
  {from: 'wp01-01', to: 'wp01-01', card: {kind: 'principle', n: 1, title: PRINCIPLES[0]}},
  {from: 'wp01-02', to: 'wp01-02',
    card: {kind: 'words', text: {zh: '当孩子对权柄说「不」', en: 'When a child says no to authority'},
      small: {zh: '答错了一个问题，或者不愿意参与讨论', en: 'getting a question wrong, or not joining a discussion'}}},
  {from: 'wp01-03', to: 'wp01-04',
    card: {kind: 'words', text: {zh: '你为什么这么想？你的想法是什么？', en: 'Why do you think so? What’s your idea?'},
      small: {zh: '不是立即纠正、强调服从，而是带着好奇心问', en: 'Not rushing to correct or insist on obedience, but asking with curiosity'}}},
  {from: 'wp01-05', to: 'wp01-07',
    card: {kind: 'list', heading: {zh: '思考更深一层的问题', en: 'Thinking one layer deeper'},
      reveal: ['wp01-06', 'wp01-06', 'wp01-06', 'wp01-06', 'wp01-07', 'wp01-07', 'wp01-07'], items: [
        {zh: '一本书为什么会被选进课堂？', en: 'Why was this book chosen for class?'},
        {zh: '一个问题为什么被讨论？', en: 'Why is this question discussed?'},
        {zh: '一件作品为什么被看见？', en: 'Why does a work get seen?'},
        {zh: '欣赏它的标准是什么？', en: 'By what standard is it appreciated?'},
        {zh: '视频推荐的算法是怎样的？', en: 'How does video recommendation work?'},
        {zh: '为什么这些视频会推送给我？', en: 'Why are these videos pushed to me?'},
        {zh: 'AI 的方法和思路从哪里来？', en: 'Where do AI’s ways of solving problems come from?'},
      ]}},
  {from: 'wp01-08', to: 'wp01-09',
    card: {kind: 'list', heading: {zh: '孩子从很小就可以学会分辨', en: 'Kids can learn to discern from a very young age'},
      reveal: ['wp01-09', 'wp01-09'], items: [
        {zh: '批判性素养', en: 'critical literacy'},
        {zh: '问题化', en: 'problematizing'},
      ]}},
  {from: 'wp01-10', to: 'wp01-10',
    card: {kind: 'words', text: {zh: '问题化', en: 'Problematizing'},
      small: {zh: '把一件看起来已经有答案的事，重新变成一个问题', en: 'turning something that seems to have an answer back into a question'}}},
  {from: 'wp01-11', to: 'wp01-11',
    card: {kind: 'words', kicker: {zh: 'Lucas Academy 的团队相信', en: 'What the Lucas Academy team believes'}, text: {zh: '最终的权柄在于神', en: 'The final authority belongs to God'},
      small: {zh: '所以我们更愿意放下自己的权柄，释放孩子自己的想法', en: 'so we would rather set aside our own authority and set children’s ideas free'}}},
  {from: 'wp01-12', to: 'wp01-13',
    card: {kind: 'words', text: {zh: 'Lucas 和 Matthew 不想画命题画。', en: 'Lucas and Matthew didn’t want to draw the set topic.'},
      small: {zh: '我们问：为什么？', en: 'So we asked why.'}}},
  {from: 'wp01-14', to: 'wp01-14',
    card: {kind: 'drawing', who: {zh: 'Matthew', en: 'Matthew'}, sketch: 'matthew-sketch-original.jpg', final: 'matthew-preparation-final.jpg', finished: 'matthew-final-artwork.jpg'}},
  {from: 'wp01-15', to: 'wp01-16',
    card: {kind: 'drawing', who: {zh: 'Lucas', en: 'Lucas'}, sketch: 'lucas-sketch-original.jpg', final: 'lucas-preparation-final.jpg', finished: 'lucas-final-artwork.jpg'}},
  {from: 'wp01-17', to: 'wp01-18',
    card: {kind: 'words', text: {zh: '被尊重，也学习尊重别人', en: 'Respected, and learning to respect others'},
      small: {zh: '一件小事，给了孩子表达自己想法的空间', en: 'A small thing gave the kids room to express their own ideas'}}},
  {from: 'wp01-19', to: 'wp01-19',
    card: {kind: 'contrast', kicker: {zh: 'Lucas Academy 的团队相信', en: 'What the Lucas Academy team believes'}, heading: {zh: '在权柄的问题上，教育者应该是', en: 'When it comes to authority, educators should be'},
      yes: {term: {zh: 'authoritative', en: 'authoritative'}, gloss: {zh: '有权威又温暖', en: 'with both authority and warmth'}},
      no: {term: {zh: 'authoritarian', en: 'authoritarian'}, gloss: {zh: '专制', en: 'domineering'}}}},

  // 理念 2 · 目标
  {from: 'wp02-01', to: 'wp02-01', card: {kind: 'principle', n: 2, title: PRINCIPLES[1]}},
  {from: 'wp02-02', to: 'wp02-02',
    card: {kind: 'words', text: {zh: '我们不塑造你的孩子，', en: 'We don’t shape your kids.'},
      small: {zh: '我们帮助他们发现自己的价值。', en: 'We help them discover their own value.'}}},
  {from: 'wp02-03', to: 'wp02-03',
    card: {kind: 'scripture',
      text: {zh: '我们原是他的工作，在基督耶稣里造成的，为要叫我们行善，就是神所预备叫我们行的。',
        en: 'For we are God’s masterpiece. He has created us anew in Christ Jesus, so we can do the good things he planned for us long ago.'},
      source: {zh: '以弗所书 2:10 · 和合本', en: 'Ephesians 2:10 · NLT'}}},
  {from: 'wp02-04', to: 'wp02-04',
    card: {kind: 'words', text: {zh: '孩子本身就有价值', en: 'Every child already has value'},
      small: {zh: 'Lucas Academy 的团队相信', en: 'What the Lucas Academy team believes'}}},
  {from: 'wp02-05', to: 'wp02-06',
    card: {kind: 'words', text: {zh: '我们是神的大师之作，孩子也是。', en: 'We are God’s masterpiece, and so are our kids.'},
      small: {zh: '“工作”，原文的意思就是“作品”：masterpiece', en: 'The word means a work of art: a masterpiece'}}},
  {from: 'wp02-07', to: 'wp02-07',
    demo: {file: 'live-painting.mp4', caption: {zh: 'Art Lab · 我的画，按我的想法动起来', en: 'Art Lab · my drawing moves the way I choose'}}},
  {from: 'wp02-08', to: 'wp02-09',
    demo: {file: 'journey-of-art.mp4', from: 62, caption: {zh: 'Inception Space · 展厅', en: 'Inception Space · the gallery'}, url: 'is.lucasacademy.org'}},

  // 理念 3 · 互教互学
  {from: 'wp03-01', to: 'wp03-01', card: {kind: 'principle', n: 3, title: PRINCIPLES[2], subtitle: {zh: '终身学习', en: 'Learning for life'}}},
  {from: 'wp03-02', to: 'wp03-02',
    card: {kind: 'words', text: {zh: '学习者、教育者和志愿者组成的社区，', en: 'A community of learners, educators, and volunteers,'},
      small: {zh: '和孩子一起学习。', en: 'learning together with kids.'}}},
  {from: 'wp03-03', to: 'wp03-03',
    card: {kind: 'scripture',
      text: {zh: '又要彼此相顾，激发爱心，勉励行善。', en: 'And let us consider how we may spur one another on toward love and good deeds.'},
      source: {zh: '希伯来书 10:24 · 和合本', en: 'Hebrews 10:24 · NIV'}}},
  {from: 'wp03-04', to: 'wp03-05',
    demo: {file: 'language-bridge.mp4', caption: {zh: '语言的桥 · 你教我，我教你', en: 'Language Bridge · you teach me, I teach you'}, url: 'lang.lucasacademy.org'}},

  // 理念 4 · 引导探索
  {from: 'wp04-01', to: 'wp04-01', card: {kind: 'principle', n: 4, title: PRINCIPLES[3]}},
  {from: 'wp04-02', to: 'wp04-03', card: {kind: 'steps', reveal: ['wp04-02', 'wp04-03']}},
  {from: 'wp04-04', to: 'wp04-04',
    card: {kind: 'scripture',
      text: {zh: '你的话是我脚前的灯，是我路上的光。', en: 'Your word is a lamp for my feet, a light on my path.'},
      source: {zh: '诗篇 119:105 · 和合本', en: 'Psalm 119:105 · NIV'}}},
  {from: 'wp04-05', to: 'wp04-05',
    card: {kind: 'words', text: {zh: '灯和光，一步一步地指引我们', en: 'A lamp and a light guide us one step at a time'},
      small: {zh: '我们也学着这样引导孩子', en: 'and we learn to guide our kids the same way'}}},
  {from: 'wp04-06', to: 'wp04-07',
    demo: {file: 'van-gogh-room.mp4', fit: 'contain', caption: {zh: 'Inception Space · 梵高房间', en: 'Inception Space · Van Gogh room'}, url: 'is.lucasacademy.org'}},

  // 理念 5 · 你来作主
  {from: 'wp05-01', to: 'wp05-01', card: {kind: 'principle', n: 5, title: PRINCIPLES[4]}},
  {from: 'wp05-02', to: 'wp05-03',
    card: {kind: 'words', text: {zh: '孩子定方向，教育者做孩子的 agent', en: 'Kids set the direction. Educators act as their agents.'},
      small: {zh: '教育者示范管理 AI agent，孩子不直接与 AI agent 互动。', en: 'Educators demonstrate how to manage AI agents. Kids do not interact with them directly.'}}},
  {from: 'wp05-04', to: 'wp05-04',
    card: {kind: 'scripture',
      text: {zh: '……也要管理海里的鱼、空中的鸟，和地上各样行动的活物。', en: '“… Rule over the fish … the birds … and over every living creature …”'},
      source: {zh: '创世记 1:28 · 和合本', en: 'Genesis 1:28 · NIV'}}},
  {from: 'wp05-05', to: 'wp05-06',
    demo: {file: 'snake-ranking.mp4', caption: {zh: 'Snake-Lab · 你来定策略', en: 'Snake-Lab · you choose the strategy'}, url: 'lucasacademy.org/challenge'}},

  // 结尾
  {from: 'wp06-01', to: 'wp06-02',
    card: {kind: 'list', heading: {zh: '全人教育的五个理念', en: 'Five principles of whole-person education'}, items: PRINCIPLES, reveal: ['wp06-01', 'wp06-01', 'wp06-01', 'wp06-01', 'wp06-01']}},
];
