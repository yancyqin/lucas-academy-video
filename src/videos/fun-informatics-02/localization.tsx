import {
  Children,
  cloneElement,
  createContext,
  isValidElement,
  useContext,
  type FC,
  type ReactNode,
} from "react";
export type Language = "zh" | "en";
export const FilmLanguage = createContext<Language>("zh");
export const COPY: Record<string, string> = {
  "AI 生成": "AI-generated",
  "AI 生成 · 同构图实景／莫奈风": "AI-generated · same view, two styles",
  莫奈: "Monet",
  德彪西: "Debussy",
  香农: "Shannon",
  "三位人类 Claude": "Three human Claudes",
  他们在同一个世界里: "Their lives overlapped",
  "1916—1918 · 画画／作曲／刚出生":
    "1916–1918 · painting / composing / newly born",
  "1916—1926 · 十年重叠": "1916–1926 · ten years together",
  "单字符选择 · 教学示意": "One character at a time · illustration",
  "箴言 25:11 · 模拟试错": "Proverbs 25:11 · simulated guesses",
  "约翰福音 3:16 · 一个字母／一个汉字":
    "John 3:16 · one letter / one character",
  "中文 · 猜字": "CHINESE · CHARACTERS",
  "越有可能，越不意外": "More likely, less surprising",
  候选词的概率: "How likely is each word?",
  苹果: "apple",
  面包: "bread",
  书: "book",
  天空: "sky",
  "示意 · 实际模型预测 token，候选来自词表；生成也可以按概率采样":
    "Illustration · models predict tokens from a vocabulary; generation can sample probabilities",
  细节越来越少: "Less and less detail",
  只剩几块颜色: "Only a few patches of colour",
  冗余可以去掉: "Redundancy can be removed",
  "信息也丢了，就认不出了": "Lose the information, lose the picture",
  "猜得到的 · 冗余": "What you can predict",
  "猜不到的 · 信息": "What is new",
  "书包 路上": "shoes · rain",
  "猫？ 狗？ 鸟？": "cat? · dog? · fox?",
  你认识: "Do you know",
  "吗？": "?",
  "作者 Yancy Qin, Louise Yang | Lucas Academy":
    "By Yancy Qin, Louise Yang | Lucas Academy",
  "克劳德·莫奈": "Claude Monet",
  "克劳德·香农": "Claude Shannon",
  "独轮车插图 · AI 生成": "Unicycle illustration · AI-generated",
  "第三个 Claude": "The third Claude",
  稍后揭晓: "Meet him soon",
  "1839 · 照相术公开问世 → 1840 · 莫奈出生":
    "1839 · photography announced → 1840 · Monet born",
  "不过是个「印象」！": "Just an ‘impression’!",
  "「印象派」": "‘Impressionism’",
  "1874 · 从一个名字开始": "1874 · a name that stayed",
  "日本桥实景 · AI 还原": "Japanese bridge · AI reconstruction",
  "Claude Monet · 日本桥 · 1899":
    "Claude Monet · The Japanese Footbridge · 1899",
  街道: "Street",
  操场: "Playground",
  海边: "Seaside",
  "AI 生成 · 实景与莫奈风保持同一构图":
    "AI-generated · both versions keep the same composition",
  夏末: "Late summer",
  秋日暮色: "Autumn twilight",
  "落日 · 雪": "Sunset · snow",
  "同样的草堆，不一样的光": "The same haystacks, different light",
  "遮住后面的字母，再猜一个": "Cover the next letter. Guess it.",
  "受香农猜下一个字母的实验启发 · 游戏是教学简化":
    "Inspired by Shannon’s next-letter experiment · simplified for teaching",
  "同一句话，不同的听众": "The same sentence, different listeners",
  已经记在心里: "Known by heart",
  能猜到: "Predictable",
  第一次读: "First reading",
  有意外: "Surprising",
  "英文里，大约一半是冗余": "About half of written English is redundancy",
  语言规律决定的: "Set by language patterns",
  可以自由选择的: "Chosen freely",
  "历史估计 · 本片四选一游戏不测量冗余率":
    "A historical estimate · our four-choice game does not measure redundancy",
  规则让词能够相遇: "Patterns let words fit together",
  "研表究明，汉字的序顺并不定一能影阅响读。":
    "The ltitle dog ran aorund the gadren.",
  "研究表明，汉字的顺序并不一定能影响阅读。":
    "The little dog ran around the garden.",
  "冗余像备份，帮消息扛过噪声": "Redundancy helps a message survive noise",
  "顺序错了一些，意思仍能补上": "Some letters moved; context still helps",
  "网上的玩笑话 · 先自己读一遍": "Try reading it before the voice does",
  消息更短: "A shorter message",
  去掉能猜到的部分: "Remove what you can predict",
  消息更结实: "A stronger message",
  留一些备份: "Keep some backup",
  "按前一个词的统计，再接一个词": "Use the previous word to choose the next",
  "二阶词近似 · 香农论文中的示例":
    "Second-order word approximation · Shannon’s example",
  "文案与 Claude 合作完成 · AI 合成配音":
    "Script developed with Claude · AI-cloned narration",
  "这次，每一步选一整个词": "This time, choose a whole word",
  "四选一为教学简化 · 一处先错，再选对":
    "Four choices for teaching · a wrong guess, then a correction",
  "猜一个 → 对一下 → 调一调": "Predict → check → adjust",
  "规律可以学，练习可以继续。": "Learn the patterns. Keep practising.",
  "真实模型预测下一个 token · 候选远不止四个":
    "Models predict the next token · many more than four candidates",
  注意力连线为示意: "Attention links are illustrative",
  "注意力，就是你需要的一切。": "Using context to predict what comes next",
  "一句话，能说清吗？": "Could one sentence say it?",
  "先看问题里，有多少是新的。": "First, ask how much is new.",
  "这是一个非常值得我们深入思考的问题。":
    "This is a question worthy of profound reflection.",
  "从很多不同的角度来看，它都非常重要。":
    "It is important from many different perspectives.",
  "总而言之，我们需要认真、全面地考虑。":
    "We must consider it carefully and comprehensively.",
  "克劳德·": "Claude ",
  "1840 年生在法国，": "born in France in 1840,",
  "是一位印象派画家。": "was an Impressionist painter.",
  "↑ 这是莫奈。通顺，不等于对。": "↑ That is Monet. Fluent does not mean true.",
  "有多少是新的？": "How much is new?",
  "有多少是真的？": "How much is true?",
  重点再说一遍: "Repeat the key point",
  步骤一步一步写: "Show every step",
  "容易记住，也方便检查。": "Easier to remember. Easier to check.",
  "去掉冗余，留下光": "Remove redundancy; keep the light",
  "量出冗余，留一些备份": "Measure redundancy; keep some backup",
  "学会说话，也需要核对": "Learn to talk; still need checking",
  "克劳德·德彪西": "Claude Debussy",
  "第四个 Claude": "The fourth Claude",
  原来一直在耳边: "You have been hearing him all along",
  "《月光》 · Clair de lune": "Clair de lune",
  "钢琴 · Laurens Goedhart": "Piano · Laurens Goedhart",
  "回到「家」，可以走不同的路": "Different routes can lead home",
  "期待中的路线（示意）": "The expected route · illustration",
  出发: "Start",
  紧张: "Tension",
  回家: "Home",
  "《月光》末段：另一条和声路线": "Clair de lune: a different route home",
  另一种颜色: "Another colour",
  "最后的和弦也完整响完。路，可以不一样。":
    "Hear the final chord finish. The route can be different.",
  "留一点时间，听颜色怎样变化。":
    "Take a moment. Listen to the colours change.",
  "路线动画为示意 · 保留《月光》真实收束":
    "Illustrative paths · the recording’s complete ending is preserved",
  "写稿时，": "While writing,",
  "提到了德彪西。": "brought up Debussy.",
  "有多少是新的呢？": "What is new?",
  "有多少是真的呢？": "What is true?",
  "什么是重要的呢？": "What matters?",
  "什么是可以忽略的呢？": "What can you leave aside?",
  "在今天这个充满 AI 信息冗余的时代，":
    "With so much AI-generated information around us,",
  "你怎么分辨——": "how do you tell?",
  "这也是我们在 Lucas Academy": "At Lucas Academy, we learn",
  "一起学习、一起思考的问题。": "and think about these questions together.",
};
/** Translate visible text only. Chinese game choices are deliberately retained. */
const translate = (children: ReactNode): ReactNode =>
  Children.map(children, (child) => {
    if (typeof child === "string")
      return COPY[child.replace(/\s+/g, " ").trim()] ?? child;
    if (
      isValidElement<{ children?: ReactNode }>(child) &&
      child.props.children !== undefined
    )
      return cloneElement(child, {}, translate(child.props.children));
    return child;
  });
export const L: FC<{ children?: ReactNode }> = ({ children }) => {
  const lang = useContext(FilmLanguage);
  return <>{lang === "en" ? translate(children) : children}</>;
};
