import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {
  firstAnswerFunctions,
  loopSummary,
  rollerCoasterQuestions,
  spiralSummary,
} from '../scripts/roller-coaster-conversation';

export const ROLLER_COASTER_CHAT_FPS = 30;
export const ROLLER_COASTER_CHAT_DURATION = 36 * ROLLER_COASTER_CHAT_FPS;

const Q1_START = 12;
const Q1_END = 244;
const A1_START = 254;
const A1_END = 450;
const Q2_START = 462;
const Q2_END = 534;
const A2_START = 544;
const A2_END = 680;
const Q3_START = 692;
const Q3_END = 724;
const A3_START = 824;

type GraphKind = (typeof firstAnswerFunctions)[number]['id'] | 'circle' | 'spiral';

export const RollerCoasterChatVideo: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={styles.canvas}>
      <AmbientBackground frame={frame} />
      <div style={styles.window}>
        <TopBar frame={frame} />
        <div style={styles.thread}>
          {frame < A1_START ? (
            <QuestionScene end={Q1_END} frame={frame} index={0} start={Q1_START} />
          ) : frame < Q2_START ? (
            <FunctionSuggestionsScene frame={frame} />
          ) : frame < A2_START ? (
            <QuestionScene end={Q2_END} frame={frame} index={1} start={Q2_START} />
          ) : frame < Q3_START ? (
            <LoopAnswerScene frame={frame} />
          ) : frame < A3_START ? (
            <QuestionScene end={Q3_END} frame={frame} index={2} start={Q3_START} />
          ) : (
            <SpiralAnswerScene frame={frame} />
          )}
        </div>
        <Composer />
      </div>
    </AbsoluteFill>
  );
};

const QuestionScene: React.FC<{
  end: number;
  frame: number;
  index: number;
  start: number;
}> = ({end, frame, index, start}) => {
  const question = rollerCoasterQuestions[index];
  const typing = clamp((frame - start) / Math.max(1, end - start));
  const visibleText = question.text.slice(0, Math.floor(question.text.length * typing));
  const entrance = smoothstep(clamp((frame - start) / 16));
  const attachment = 'attachment' in question ? question.attachment : undefined;
  const isLong = question.text.length > 60;

  return (
    <div
      style={{
        ...styles.questionStage,
        opacity: entrance,
        transform: `translateY(${interpolate(entrance, [0, 1], [26, 0])}px)`,
      }}
    >
      <div style={styles.youLabel}>YOU</div>
      {attachment ? (
        <div style={styles.uploadedSketchCard}>
          <Img src={staticFile(attachment)} style={styles.uploadedSketch} />
          <div style={styles.uploadedBadge}>Uploaded image</div>
        </div>
      ) : null}
      <div
        style={{
          ...styles.questionBubble,
          fontSize: isLong ? 55 : 72,
          minHeight: isLong ? 250 : 200,
        }}
      >
        <span>{visibleText}</span>
        {frame < end ? <TypingCursor frame={frame} large /> : null}
      </div>
      <div style={styles.questionCounter}>QUESTION {index + 1} / 3</div>
    </div>
  );
};

const FunctionSuggestionsScene: React.FC<{frame: number}> = ({frame}) => {
  const progress = clamp((frame - A1_START) / (A1_END - A1_START));

  return (
    <AnswerLayout
      frame={frame}
      progress={progress}
      question={rollerCoasterQuestions[0].text}
      speed={8}
    >
      <div style={styles.answerEyebrow}>FOUR QUICK DIRECTIONS</div>
      <div style={styles.graphGrid}>
        {firstAnswerFunctions.map((item, index) => {
          const itemProgress = smoothstep(clamp((progress - index * 0.12) / 0.28));
          return (
            <div
              key={item.id}
              style={{
                ...styles.graphCard,
                opacity: itemProgress,
                transform: `translateY(${interpolate(itemProgress, [0, 1], [24, 0])}px)`,
              }}
            >
              <div style={styles.graphCopy}>
                <div style={styles.graphTitle}>{item.title}</div>
                <div style={styles.graphFormula}>{item.formula}</div>
                <div style={styles.graphNote}>{item.note}</div>
              </div>
              <FunctionGraph kind={item.id} progress={itemProgress} />
            </div>
          );
        })}
      </div>
    </AnswerLayout>
  );
};

const LoopAnswerScene: React.FC<{frame: number}> = ({frame}) => {
  const progress = clamp((frame - A2_START) / (A2_END - A2_START));
  const copyIn = smoothstep(clamp(progress / 0.36));

  return (
    <AnswerLayout
      frame={frame}
      progress={progress}
      question={rollerCoasterQuestions[1].text}
      speed={12}
    >
      <div style={styles.loopLayout}>
        <div style={{...styles.loopCopy, opacity: copyIn}}>
          <div style={styles.answerEyebrow}>YES — USE A PARAMETRIC CURVE</div>
          <h2 style={styles.loopTitle}>{loopSummary.title}</h2>
          <div style={styles.largeFormula}>{loopSummary.circle}</div>
          <div style={styles.formulaPair}>
            <span>{loopSummary.x}</span>
            <span>{loopSummary.y}</span>
          </div>
          <p style={styles.loopNote}>{loopSummary.note}</p>
        </div>
        <div style={styles.loopGraphCard}>
          <FunctionGraph kind="circle" progress={smoothstep(clamp((progress - 0.08) / 0.7))} large />
          <div style={styles.loopGraphLabel}>one x-coordinate · multiple y-values</div>
        </div>
      </div>
    </AnswerLayout>
  );
};

const SpiralAnswerScene: React.FC<{frame: number}> = ({frame}) => {
  const progress = clamp((frame - A3_START) / (ROLLER_COASTER_CHAT_DURATION - A3_START - 20));
  const imageIn = smoothstep(clamp(progress / 0.34));
  const formulaIn = smoothstep(clamp((progress - 0.18) / 0.42));

  return (
    <AnswerLayout
      attachment={rollerCoasterQuestions[2].attachment}
      frame={frame}
      progress={progress}
      question={rollerCoasterQuestions[2].text}
      speed={20}
    >
      <div style={styles.spiralLayout}>
        <div
          style={{
            ...styles.generatedCard,
            opacity: imageIn,
            transform: `scale(${interpolate(imageIn, [0, 1], [0.96, 1])})`,
          }}
        >
          <Img
            alt="Generated image: Spiral Loop Parametric Graph Guide"
            src={staticFile(spiralSummary.generatedImage)}
            style={styles.generatedImage}
          />
        </div>
        <div
          style={{
            ...styles.spiralCopy,
            opacity: formulaIn,
            transform: `translateX(${interpolate(formulaIn, [0, 1], [26, 0])}px)`,
          }}
        >
          <div style={styles.answerEyebrow}>FROM SKETCH TO FUNCTION</div>
          <h2 style={styles.spiralTitle}>{spiralSummary.title}</h2>
          <div style={styles.spiralFormula}>{spiralSummary.x}</div>
          <div style={styles.spiralFormula}>{spiralSummary.y}</div>
          <p style={styles.spiralNote}>{spiralSummary.note}</p>
          <div style={styles.miniSpiralGraph}>
            <FunctionGraph kind="spiral" progress={formulaIn} />
          </div>
        </div>
      </div>
    </AnswerLayout>
  );
};

const AnswerLayout: React.FC<{
  attachment?: string;
  children: React.ReactNode;
  frame: number;
  progress: number;
  question: string;
  speed: number;
}> = ({attachment, children, frame, progress, question, speed}) => (
  <>
    <CompactQuestion attachment={attachment} text={question} />
    <div style={styles.answerHeader}>
      <AssistantAvatar pulse={progress < 0.96} />
      <span>ChatGPT</span>
    </div>
    <div style={styles.answerBody}>{children}</div>
    <SpeedMeter frame={frame} progress={progress} speed={speed} />
  </>
);

const CompactQuestion: React.FC<{attachment?: string; text: string}> = ({attachment, text}) => (
  <div style={styles.compactQuestionRow}>
    <div style={styles.compactQuestionBubble}>
      {attachment ? <Img src={staticFile(attachment)} style={styles.compactSketch} /> : null}
      <span>{text}</span>
    </div>
  </div>
);

const AssistantAvatar: React.FC<{pulse: boolean}> = ({pulse}) => {
  const frame = useCurrentFrame();
  const scale = pulse ? 1 + Math.sin(frame / 5) * 0.04 : 1;
  return (
    <div style={{...styles.assistantAvatar, transform: `scale(${scale})`}}>
      ✦
    </div>
  );
};

const SpeedMeter: React.FC<{frame: number; progress: number; speed: number}> = ({
  frame,
  progress,
  speed,
}) => {
  const shownSpeed = Math.max(1, Math.round(1 + (speed - 1) * progress ** 1.65));
  return (
    <div style={styles.speedMeter}>
      <div style={styles.speedPulse}>{Math.floor(frame / 8) % 2 === 0 ? '●' : '○'}</div>
      <div style={styles.speedLabel}>answer</div>
      <div style={styles.speedTrack}>
        <div style={{...styles.speedFill, width: `${progress * 100}%`}} />
      </div>
      <div style={styles.speedValue}>{shownSpeed}×</div>
    </div>
  );
};

const FunctionGraph: React.FC<{kind: GraphKind; large?: boolean; progress: number}> = ({
  kind,
  large = false,
  progress,
}) => {
  const width = large ? 620 : 380;
  const height = large ? 430 : 190;
  const graph = graphFor(kind, width, height);

  return (
    <svg height={height} viewBox={`0 0 ${width} ${height}`} width={width}>
      <defs>
        <linearGradient id={`curve-${kind}`} x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stopColor="#10a37f" />
          <stop offset="100%" stopColor="#2867d7" />
        </linearGradient>
      </defs>
      <line stroke="#d9dedc" strokeWidth="2" x1="22" x2={width - 18} y1={graph.axisY} y2={graph.axisY} />
      <line stroke="#d9dedc" strokeWidth="2" x1={graph.axisX} x2={graph.axisX} y1="16" y2={height - 16} />
      <path
        d={graph.path}
        fill="none"
        pathLength={1}
        stroke={`url(#curve-${kind})`}
        strokeDasharray="1"
        strokeDashoffset={1 - progress}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={large ? 8 : 6}
      />
      <circle cx={graph.end.x} cy={graph.end.y} fill="#ff8a3d" opacity={progress > 0.92 ? 1 : 0} r={large ? 9 : 7} />
    </svg>
  );
};

const graphFor = (kind: GraphKind, width: number, height: number) => {
  if (kind === 'circle') {
    return parametricGraph(
      (t) => 2 * Math.sin(t),
      (t) => 2 * (1 - Math.cos(t)),
      0,
      Math.PI * 2,
      [-4, 4],
      [-0.6, 4.7],
      width,
      height,
    );
  }
  if (kind === 'spiral') {
    return parametricGraph(
      (t) => (2 + 0.3 * t) * Math.cos(t),
      (t) => (2 + 0.3 * t) * Math.sin(t) - 0.15 * t,
      0,
      Math.PI * 8,
      [-22, 22],
      [-13, 9],
      width,
      height,
    );
  }

  const configs = {
    parabola: {domain: [-8, 8] as [number, number], range: [-10, 2] as [number, number], fn: (x: number) => -0.15 * x * x},
    sine: {domain: [-Math.PI * 2.3, Math.PI * 2.3] as [number, number], range: [-2.8, 2.8] as [number, number], fn: (x: number) => 2 * Math.sin(x)},
    damped: {domain: [0, 20] as [number, number], range: [-4.5, 4.5] as [number, number], fn: (x: number) => 4 * Math.exp(-0.08 * x) * Math.sin(x)},
    gaussian: {domain: [-8, 8] as [number, number], range: [-0.8, 5.8] as [number, number], fn: (x: number) => 5 * Math.exp(-(x * x) / 4)},
  } as const;
  const config = configs[kind];
  return cartesianGraph(config.fn, config.domain, config.range, width, height);
};

const cartesianGraph = (
  fn: (x: number) => number,
  domain: [number, number],
  range: [number, number],
  width: number,
  height: number,
) => {
  const pad = 18;
  const points = Array.from({length: 121}, (_, index) => {
    const x = domain[0] + (index / 120) * (domain[1] - domain[0]);
    return project(x, fn(x), domain, range, width, height, pad);
  });
  return {
    axisX: project(0, 0, domain, range, width, height, pad).x,
    axisY: project(0, 0, domain, range, width, height, pad).y,
    end: points[points.length - 1],
    path: pathFrom(points),
  };
};

const parametricGraph = (
  xFn: (t: number) => number,
  yFn: (t: number) => number,
  start: number,
  end: number,
  domain: [number, number],
  range: [number, number],
  width: number,
  height: number,
) => {
  const pad = 22;
  const points = Array.from({length: 241}, (_, index) => {
    const t = start + (index / 240) * (end - start);
    return project(xFn(t), yFn(t), domain, range, width, height, pad);
  });
  return {
    axisX: project(0, 0, domain, range, width, height, pad).x,
    axisY: project(0, 0, domain, range, width, height, pad).y,
    end: points[points.length - 1],
    path: pathFrom(points),
  };
};

const project = (
  x: number,
  y: number,
  domain: [number, number],
  range: [number, number],
  width: number,
  height: number,
  pad: number,
) => ({
  x: pad + ((x - domain[0]) / (domain[1] - domain[0])) * (width - pad * 2),
  y: height - pad - ((y - range[0]) / (range[1] - range[0])) * (height - pad * 2),
});

const pathFrom = (points: Array<{x: number; y: number}>): string =>
  points.map((point, index) => `${index === 0 ? 'M' : 'L'}${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(' ');

const TypingCursor: React.FC<{frame: number; large?: boolean}> = ({frame, large = false}) => (
  <span
    style={{
      ...styles.cursor,
      height: large ? 56 : 30,
      opacity: Math.floor(frame / 8) % 2 === 0 ? 1 : 0.18,
    }}
  />
);

const TopBar: React.FC<{frame: number}> = ({frame}) => (
  <div style={styles.topBar}>
    <div style={styles.windowDots}>
      <span style={{...styles.dot, background: '#ff5f57'}} />
      <span style={{...styles.dot, background: '#febc2e'}} />
      <span style={{...styles.dot, background: '#28c840'}} />
    </div>
    <div style={styles.chatTitle}>
      <span style={styles.spark}>✦</span>
      <span>Roller Coaster Formulas</span>
    </div>
    <div style={styles.timecode}>{formatTime(frame / ROLLER_COASTER_CHAT_FPS)}</div>
  </div>
);

const AmbientBackground: React.FC<{frame: number}> = ({frame}) => {
  const drift = Math.sin(frame / 65) * 24;
  return (
    <>
      <div style={{...styles.glow, background: '#b7f7db', left: -130 + drift, top: 60}} />
      <div style={{...styles.glow, background: '#c9ccff', bottom: -170, right: -80 - drift}} />
    </>
  );
};

const Composer: React.FC = () => (
  <div style={styles.composerWrap}>
    <div style={styles.composer}>
      <span style={styles.plus}>＋</span>
      <span style={styles.placeholder}>Message ChatGPT</span>
      <span style={styles.mic}>◉</span>
    </div>
  </div>
);

const clamp = (value: number): number => Math.max(0, Math.min(1, value));
const smoothstep = (value: number): number => value * value * (3 - 2 * value);
const formatTime = (seconds: number): string => `00:${String(Math.floor(seconds)).padStart(2, '0')}`;

const font = 'Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

const styles: Record<string, React.CSSProperties> = {
  canvas: {alignItems: 'center', background: '#e9eceb', display: 'flex', fontFamily: font, justifyContent: 'center', overflow: 'hidden'},
  glow: {borderRadius: 999, filter: 'blur(90px)', height: 520, opacity: 0.55, position: 'absolute', width: 520},
  window: {background: '#fff', border: '1px solid rgba(15,23,42,0.08)', borderRadius: 28, boxShadow: '0 34px 100px rgba(15,23,42,0.18)', height: 970, overflow: 'hidden', position: 'relative', width: 1680},
  topBar: {alignItems: 'center', background: 'rgba(250,250,250,0.97)', borderBottom: '1px solid #e7e7e7', display: 'flex', height: 82, justifyContent: 'center', left: 0, position: 'absolute', right: 0, top: 0, zIndex: 8},
  windowDots: {display: 'flex', gap: 11, left: 28, position: 'absolute'},
  dot: {borderRadius: 999, height: 15, width: 15},
  chatTitle: {alignItems: 'center', color: '#202123', display: 'flex', fontSize: 24, fontWeight: 650, gap: 11},
  spark: {color: '#10a37f', fontSize: 29},
  timecode: {color: '#8a8d91', fontSize: 19, fontVariantNumeric: 'tabular-nums', position: 'absolute', right: 31},
  thread: {bottom: 104, left: 0, overflow: 'hidden', position: 'absolute', right: 0, top: 82},
  questionStage: {alignItems: 'center', bottom: 16, display: 'flex', flexDirection: 'column', justifyContent: 'center', left: 145, position: 'absolute', right: 145, top: 14},
  youLabel: {color: '#707276', fontSize: 20, fontWeight: 750, letterSpacing: 3, marginBottom: 17},
  questionBubble: {alignItems: 'center', background: '#2f2f2f', borderRadius: 34, boxShadow: '0 24px 55px rgba(0,0,0,0.16)', color: '#fff', display: 'flex', fontWeight: 560, justifyContent: 'center', letterSpacing: '-1.8px', lineHeight: 1.18, padding: '40px 68px 46px', textAlign: 'center', width: 1320},
  questionCounter: {color: '#989b9f', fontSize: 17, fontWeight: 700, letterSpacing: 2.2, marginTop: 18},
  uploadedSketchCard: {background: '#fff', border: '1px solid #dedede', borderRadius: 22, boxShadow: '0 16px 35px rgba(0,0,0,0.12)', height: 410, marginBottom: 22, overflow: 'hidden', padding: 9, position: 'relative', width: 470},
  uploadedSketch: {borderRadius: 15, height: '100%', objectFit: 'cover', width: '100%'},
  uploadedBadge: {background: 'rgba(255,255,255,0.9)', borderRadius: 999, bottom: 20, color: '#343638', fontSize: 16, fontWeight: 700, left: 20, padding: '9px 15px', position: 'absolute'},
  compactQuestionRow: {display: 'flex', justifyContent: 'flex-end', padding: '26px 112px 0', position: 'relative', zIndex: 4},
  compactQuestionBubble: {alignItems: 'center', background: '#f1f1f1', borderRadius: 24, color: '#262626', display: 'flex', fontSize: 25, gap: 14, lineHeight: 1.26, maxWidth: 930, padding: '17px 24px'},
  compactSketch: {borderRadius: 10, height: 78, objectFit: 'cover', width: 86},
  answerHeader: {alignItems: 'center', color: '#202123', display: 'flex', fontSize: 22, fontWeight: 700, gap: 12, left: 112, position: 'absolute', top: 134, zIndex: 3},
  assistantAvatar: {alignItems: 'center', background: '#111827', borderRadius: 999, color: '#fff', display: 'flex', fontSize: 22, height: 47, justifyContent: 'center', width: 47},
  answerBody: {bottom: 16, left: 112, position: 'absolute', right: 112, top: 196},
  answerEyebrow: {color: '#0b8267', fontSize: 16, fontWeight: 800, letterSpacing: 2.1, marginBottom: 12},
  graphGrid: {display: 'grid', gap: 18, gridTemplateColumns: '1fr 1fr'},
  graphCard: {alignItems: 'center', background: '#f7f9f8', border: '1px solid #e0e5e3', borderRadius: 21, display: 'flex', height: 245, justifyContent: 'space-between', overflow: 'hidden', padding: '20px 17px 20px 26px'},
  graphCopy: {minWidth: 245},
  graphTitle: {color: '#202523', fontSize: 28, fontWeight: 760, marginBottom: 8},
  graphFormula: {color: '#12352d', fontFamily: 'Georgia, "Times New Roman", serif', fontSize: 29, marginBottom: 8},
  graphNote: {color: '#777d7a', fontSize: 17},
  loopLayout: {alignItems: 'center', display: 'grid', gap: 54, gridTemplateColumns: '0.94fr 1.06fr', height: '100%'},
  loopCopy: {paddingLeft: 70},
  loopTitle: {fontSize: 44, lineHeight: 1.12, margin: '0 0 22px'},
  largeFormula: {background: '#eff8f5', borderLeft: '6px solid #10a37f', borderRadius: 14, color: '#12352d', fontFamily: 'Georgia, "Times New Roman", serif', fontSize: 47, marginBottom: 18, padding: '18px 24px', width: 'fit-content'},
  formulaPair: {color: '#222d29', display: 'flex', flexDirection: 'column', fontFamily: 'Georgia, "Times New Roman", serif', fontSize: 30, gap: 8},
  loopNote: {color: '#626965', fontSize: 22, lineHeight: 1.42, maxWidth: 540},
  loopGraphCard: {alignItems: 'center', background: '#f7f9f8', border: '1px solid #e0e5e3', borderRadius: 24, display: 'flex', flexDirection: 'column', height: 560, justifyContent: 'center'},
  loopGraphLabel: {color: '#6d7471', fontSize: 19, marginTop: 2},
  spiralLayout: {alignItems: 'center', display: 'grid', gap: 42, gridTemplateColumns: '1.08fr 0.92fr', height: '100%'},
  generatedCard: {background: '#fff', border: '1px solid #dedede', borderRadius: 22, boxShadow: '0 18px 42px rgba(20,25,24,0.13)', height: 555, overflow: 'hidden', padding: 10},
  generatedImage: {borderRadius: 14, height: '100%', objectFit: 'contain', width: '100%'},
  spiralCopy: {paddingRight: 20},
  spiralTitle: {fontSize: 42, lineHeight: 1.12, margin: '0 0 22px'},
  spiralFormula: {background: '#f1f7f5', borderLeft: '5px solid #10a37f', borderRadius: 12, color: '#16382f', fontFamily: 'Georgia, "Times New Roman", serif', fontSize: 27, marginBottom: 12, padding: '15px 18px'},
  spiralNote: {color: '#5f6663', fontSize: 20, lineHeight: 1.4, margin: '13px 0'},
  miniSpiralGraph: {background: '#fafbfb', border: '1px solid #e4e7e6', borderRadius: 16, height: 180, overflow: 'hidden'},
  speedMeter: {alignItems: 'center', background: 'rgba(255,255,255,0.96)', border: '1px solid #e4e7e6', borderRadius: 999, bottom: 20, boxShadow: '0 8px 22px rgba(18,30,26,0.08)', display: 'flex', gap: 10, padding: '9px 14px', position: 'absolute', right: 24, zIndex: 6},
  speedPulse: {color: '#10a37f', fontSize: 12},
  speedLabel: {color: '#7b817f', fontSize: 15},
  speedTrack: {background: '#dfe5e3', borderRadius: 99, height: 7, overflow: 'hidden', width: 96},
  speedFill: {background: '#10a37f', borderRadius: 99, height: '100%'},
  speedValue: {color: '#0d6f59', fontSize: 17, fontWeight: 850, minWidth: 34},
  cursor: {background: '#10a37f', borderRadius: 2, display: 'inline-block', marginLeft: 6, transform: 'translateY(5px)', width: 4},
  composerWrap: {alignItems: 'center', background: 'linear-gradient(180deg, rgba(255,255,255,0), #fff 24%)', bottom: 0, display: 'flex', height: 125, justifyContent: 'center', left: 0, position: 'absolute', right: 0, zIndex: 8},
  composer: {alignItems: 'center', background: '#fff', border: '1px solid #d8d8d8', borderRadius: 28, boxShadow: '0 4px 14px rgba(0,0,0,0.05)', color: '#6d7073', display: 'flex', fontSize: 22, height: 66, padding: '0 20px', width: 1180},
  plus: {color: '#444', fontSize: 28, marginRight: 16},
  placeholder: {flex: 1},
  mic: {color: '#333', fontSize: 20},
};
