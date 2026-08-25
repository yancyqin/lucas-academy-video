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
import {
  hybridContraction,
  hybridSurfaceDisplay,
  hybridSurfacePoint,
  hybridTurns,
  shortVideoRefinementQuestion,
} from '../scripts/roller-coaster-short';

export const ROLLER_COASTER_SHORT_FPS = 30;
export const ROLLER_COASTER_SHORT_DURATION = 840;

const FIRST_QUESTION_END = 118;
const QUICK_DIRECTIONS_END = 185;
const LOOP_END = 265;
const SKETCH_END = 365;
const MILESTONE_2_QUESTION_END = 485;
const PROCESS_END = 585;
const FINAL_END = 750;

export const RollerCoasterMilestonesShortVideo: React.FC = () => {
  const frame = useCurrentFrame();

  if (frame >= FINAL_END) return <SurfaceCutscene frame={frame} />;

  let scene: React.ReactNode;
  if (frame < FIRST_QUESTION_END) scene = <FirstQuestion frame={frame} />;
  else if (frame < QUICK_DIRECTIONS_END) scene = <QuickDirections frame={frame} />;
  else if (frame < LOOP_END) scene = <LoopBeat frame={frame} />;
  else if (frame < SKETCH_END) scene = <SketchBeat frame={frame} />;
  else if (frame < MILESTONE_2_QUESTION_END) scene = <Milestone2Question frame={frame} />;
  else if (frame < PROCESS_END) scene = <CompressedProcess frame={frame} />;
  else scene = <HybridFinal frame={frame} />;

  return (
    <AbsoluteFill style={styles.canvas}>
      <Ambient frame={frame} />
      <div style={styles.phoneWindow}>
        <Header frame={frame} />
        <main style={styles.main}>{scene}</main>
        <Composer />
      </div>
    </AbsoluteFill>
  );
};

const FirstQuestion: React.FC<{frame: number}> = ({frame}) => {
  const question = rollerCoasterQuestions[0].text;
  const progress = ease(clamp((frame - 10) / 96));
  const text = question.slice(0, Math.floor(question.length * progress));
  return (
    <section style={styles.centerStage}>
      <div style={styles.milestone}>MILESTONE 1 · THE FIRST QUESTION</div>
      <div style={styles.you}>YOU</div>
      <div style={styles.heroQuestion}>
        {text}<Cursor frame={frame} />
      </div>
      <div style={styles.slow}>THE STORY SLOWS DOWN HERE</div>
    </section>
  );
};

const QuickDirections: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - FIRST_QUESTION_END;
  return (
    <ThreadAnswer question={rollerCoasterQuestions[0].text} speed="12×">
      <div style={styles.eyebrow}>FAST SEARCH · KEEP ONLY THE SHAPES</div>
      <h1 style={styles.sceneTitle}>Four quick directions</h1>
      <div style={styles.formulaStack}>
        {firstAnswerFunctions.map((item, index) => {
          const show = ease(clamp((local - index * 8) / 14));
          return (
            <div key={item.id} style={{...styles.formulaRow, opacity: show, transform: `translateX(${24 * (1 - show)}px)`}}>
              <span>{item.title}</span><strong>{item.formula}</strong>
            </div>
          );
        })}
      </div>
    </ThreadAnswer>
  );
};

const LoopBeat: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - QUICK_DIRECTIONS_END;
  const questionProgress = ease(clamp(local / 20));
  const answer = ease(clamp((local - 14) / 32));
  return (
    <ThreadAnswer question={rollerCoasterQuestions[1].text.slice(0, Math.floor(rollerCoasterQuestions[1].text.length * questionProgress))} speed="16×">
      <div style={{...styles.loopCard, opacity: answer}}>
        <div>
          <div style={styles.eyebrow}>YES — USE A PARAMETRIC CURVE</div>
          <h1 style={styles.sceneTitle}>{loopSummary.title}</h1>
          <div style={styles.largeFormula}>{loopSummary.circle}</div>
          <div style={styles.pair}><span>{loopSummary.x}</span><span>{loopSummary.y}</span></div>
        </div>
        <CircleGraph progress={answer} />
      </div>
    </ThreadAnswer>
  );
};

const SketchBeat: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - LOOP_END;
  const sketchIn = ease(clamp(local / 22));
  const answerIn = ease(clamp((local - 30) / 38));
  return (
    <section style={styles.sketchStage}>
      <div style={styles.sketchQuestionRow}>
        <div style={{...styles.sketchCard, opacity: sketchIn}}>
          <Img src={staticFile(rollerCoasterQuestions[2].attachment)} style={styles.sketchImage} />
        </div>
        <div style={styles.smallQuestion}>{rollerCoasterQuestions[2].text}</div>
      </div>
      <div style={{...styles.sketchAnswer, opacity: answerIn, transform: `translateY(${30 * (1 - answerIn)}px)`}}>
        <div style={styles.eyebrow}>FROM THE REAL SKETCH TO A FUNCTION</div>
        <h1 style={styles.sceneTitle}>{spiralSummary.title}</h1>
        <div style={styles.greenFormula}>{spiralSummary.x}</div>
        <div style={styles.greenFormula}>{spiralSummary.y}</div>
        <MiniSpiral progress={answerIn} />
        <SpeedPill value="20×" />
      </div>
    </section>
  );
};

const Milestone2Question: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - SKETCH_END;
  const question = '3d xyz plane like a funal shape spiraling down';
  const progress = ease(clamp((local - 8) / 92));
  const text = question.slice(0, Math.floor(question.length * progress));
  return (
    <section style={styles.centerStage}>
      <div style={styles.milestone}>MILESTONE 2 · THE 3D TRACK</div>
      <div style={styles.you}>YOU</div>
      <div style={{...styles.heroQuestion, fontSize: 68, minHeight: 380}}>
        {text}<Cursor frame={frame} />
      </div>
      <div style={styles.slow}>ONE MORE DECISION POINT</div>
    </section>
  );
};

const CompressedProcess: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - MILESTONE_2_QUESTION_END;
  const steps = [
    ['01', '3D FUNNEL', 'Turn a centerline downward'],
    ['02', 'SURFACE', 'Give the line a width parameter v'],
    ['03', 'ONE TAPER', 'Slow the golden contraction'],
  ] as const;
  return (
    <ThreadAnswer question="Build one rideable Surface." speed="20×">
      <div style={styles.eyebrow}>THE MIDDLE IS COMPRESSED</div>
      <h1 style={styles.sceneTitle}>Three useful decisions. Nothing extra.</h1>
      <div style={styles.processStack}>
        {steps.map(([number, title, note], index) => {
          const show = ease(clamp((local - index * 18) / 18));
          return (
            <div key={number} style={{...styles.processCard, opacity: show, transform: `scale(${0.96 + show * 0.04})`}}>
              <strong>{number}</strong>
              <div><h2>{title}</h2><p>{note}</p></div>
              <span>✓</span>
            </div>
          );
        })}
      </div>
      <SpeedPill value="20×" />
    </ThreadAnswer>
  );
};

const HybridFinal: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - PROCESS_END;
  const questionIn = ease(clamp(local / 24));
  const graphIn = ease(clamp((local - 20) / 48));
  const formulaIn = ease(clamp((local - 55) / 48));
  return (
    <section style={styles.finalStage}>
      <div style={{...styles.refinementQuestion, opacity: questionIn}}>{shortVideoRefinementQuestion}</div>
      <div style={{...styles.finalHeading, opacity: graphIn}}>
        <div style={styles.eyebrow}>ONE CONTINUOUS HYBRID</div>
        <h1>Funnel × slow logarithmic contraction</h1>
        <p><b>k = {hybridContraction}</b> · 5 turns · no piecewise join</p>
      </div>
      <div style={{...styles.surfaceCard, opacity: graphIn}}>
        <HybridSurfaceGraph reveal={graphIn} />
      </div>
      <pre style={{...styles.hybridFormula, opacity: formulaIn}}>{hybridSurfaceDisplay}</pre>
      <div style={{...styles.finalCheck, opacity: formulaIn}}>✓ Slower gaps · one rule · ends at (0, 0, 0)</div>
    </section>
  );
};

const SurfaceCutscene: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - FINAL_END;
  const progress = clamp(local / (ROLLER_COASTER_SHORT_DURATION - FINAL_END));
  const reveal = ease(clamp(local / 20));
  const scale = interpolate(progress, [0, 1], [0.92, 1.12]);
  const blur = interpolate(progress, [0.72, 1], [0, 9], {extrapolateLeft: 'clamp'});
  const next = ease(clamp((progress - 0.38) / 0.32));
  return (
    <AbsoluteFill style={styles.cutscene}>
      <div style={{...styles.cutsceneGraph, opacity: reveal, transform: `scale(${scale})`, filter: `blur(${blur}px)`}}>
        <HybridSurfaceGraph reveal={reveal} />
      </div>
      <div style={styles.surfaceLabel}>ONE SURFACE</div>
      <div style={{...styles.nextAct, opacity: next}}><span>MILESTONE 3</span>BUILD IT IN THE MANIFOLD</div>
    </AbsoluteFill>
  );
};

const ThreadAnswer: React.FC<{children: React.ReactNode; question: string; speed: string}> = ({children, question, speed}) => (
  <section style={styles.threadStage}>
    <div style={styles.compactQuestion}>{question}</div>
    <div style={styles.assistant}><span>✦</span><b>ChatGPT</b><em>{speed}</em></div>
    <div style={styles.answerBody}>{children}</div>
  </section>
);

const Header: React.FC<{frame: number}> = ({frame}) => (
  <header style={styles.header}>
    <div style={styles.logo}>✦</div>
    <div><b>ROLLER COASTER</b><span>FUNCTION LAB</span></div>
    <div style={{...styles.recording, opacity: 0.65 + Math.sin(frame / 8) * 0.3}}>●</div>
  </header>
);

const Composer = () => <div style={styles.composer}><span>Message ChatGPT</span><b>↑</b></div>;

const Ambient: React.FC<{frame: number}> = ({frame}) => (
  <AbsoluteFill style={styles.ambient}>
    <div style={{...styles.glow, transform: `translate(${Math.sin(frame / 80) * 30}px, ${Math.cos(frame / 90) * 30}px)`}} />
    <div style={{...styles.glow, ...styles.glowTwo}} />
  </AbsoluteFill>
);

const Cursor: React.FC<{frame: number}> = ({frame}) => <span style={{...styles.cursor, opacity: frame % 18 < 12 ? 1 : 0.18}} />;
const SpeedPill: React.FC<{value: string}> = ({value}) => <div style={styles.speedPill}><span>ANSWER</span><i /><b>{value}</b></div>;

const CircleGraph: React.FC<{progress: number}> = ({progress}) => {
  const points = Array.from({length: 121}, (_, index) => {
    const t = (index / 120) * Math.PI * 2;
    return [270 + 185 * Math.sin(t), 245 - 185 * (1 - Math.cos(t)) / 2] as const;
  });
  return (
    <svg viewBox="0 0 540 470" style={styles.circleGraph}>
      <line x1="45" x2="495" y1="280" y2="280" stroke="#d9dedd" strokeWidth="3" />
      <line x1="270" x2="270" y1="32" y2="430" stroke="#d9dedd" strokeWidth="3" />
      <path d={path(points)} pathLength={1} fill="none" stroke="#119b78" strokeWidth="12" strokeLinecap="round" strokeDasharray="1" strokeDashoffset={1 - progress} />
    </svg>
  );
};

const MiniSpiral: React.FC<{progress: number}> = ({progress}) => {
  const points = Array.from({length: 181}, (_, index) => {
    const t = (index / 180) * Math.PI * 7;
    const r = 18 + 6.6 * t;
    return [390 + r * Math.cos(t), 245 + r * 0.7 * Math.sin(t)] as const;
  });
  return (
    <svg viewBox="0 0 780 490" style={styles.miniSpiral}>
      <path d={path(points)} pathLength={1} fill="none" stroke="#167dc5" strokeWidth="10" strokeLinecap="round" strokeDasharray="1" strokeDashoffset={1 - progress} />
    </svg>
  );
};

type MeshCell = {depth: number; fill: string; points: string};

const makeHybridMesh = (): MeshCell[] => {
  const cells: MeshCell[] = [];
  const rows = 150;
  const columns = 5;
  const projected = (u: number, v: number) => {
    const p = hybridSurfacePoint(u, v);
    return {
      x: 450 + p.x * 39 + p.z * 10,
      y: 52 + (12 - p.y) * 52 - p.z * 12,
      depth: p.z - p.x * 0.18,
    };
  };
  for (let row = 0; row < rows; row++) {
    const u0 = (row / rows) * hybridTurns * Math.PI * 2;
    const u1 = ((row + 1) / rows) * hybridTurns * Math.PI * 2;
    for (let column = 0; column < columns; column++) {
      const v0 = -0.45 + (column / columns) * 0.9;
      const v1 = -0.45 + ((column + 1) / columns) * 0.9;
      const quad = [projected(u0, v0), projected(u1, v0), projected(u1, v1), projected(u0, v1)];
      const shade = 190 + Math.round((column / (columns - 1)) * 28);
      cells.push({
        depth: quad.reduce((sum, point) => sum + point.depth, 0) / quad.length,
        fill: `rgb(${shade},${shade},${shade + 3})`,
        points: quad.map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(' '),
      });
    }
  }
  return cells.sort((a, b) => a.depth - b.depth);
};

const HYBRID_MESH = makeHybridMesh();

const HybridSurfaceGraph: React.FC<{reveal: number}> = ({reveal}) => (
  <svg viewBox="0 0 900 760" style={styles.surfaceSvg}>
    <g opacity={reveal}>
      {HYBRID_MESH.map((cell, index) => (
        <polygon key={index} points={cell.points} fill={cell.fill} stroke="#686b70" strokeWidth="1.1" strokeLinejoin="round" />
      ))}
    </g>
  </svg>
);

const path = (points: ReadonlyArray<readonly [number, number]>) =>
  points.map(([x, y], index) => `${index === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ');

const clamp = (value: number) => Math.max(0, Math.min(1, value));
const ease = (value: number) => value * value * (3 - 2 * value);

const styles: Record<string, React.CSSProperties> = {
  canvas: {background: '#e9f2ef', color: '#171b1a', fontFamily: 'Inter, Avenir Next, Arial, sans-serif'},
  ambient: {background: 'linear-gradient(155deg,#e8f7f2 0%,#e8eef5 52%,#dce7ec 100%)', overflow: 'hidden'},
  glow: {position: 'absolute', width: 760, height: 760, left: -250, top: -180, borderRadius: '50%', background: 'radial-gradient(circle,rgba(31,181,140,.25),rgba(31,181,140,0) 68%)', filter: 'blur(20px)'},
  glowTwo: {left: 620, top: 1180, background: 'radial-gradient(circle,rgba(52,117,197,.2),rgba(52,117,197,0) 68%)'},
  phoneWindow: {position: 'absolute', inset: '48px 38px 54px', background: 'rgba(255,255,255,.96)', borderRadius: 42, overflow: 'hidden', border: '1px solid rgba(255,255,255,.9)', boxShadow: '0 35px 90px rgba(31,58,51,.18)'},
  header: {height: 106, borderBottom: '1px solid #e5e9e7', display: 'flex', alignItems: 'center', padding: '0 35px', gap: 17, boxSizing: 'border-box'},
  logo: {width: 50, height: 50, borderRadius: 15, display: 'grid', placeItems: 'center', color: '#fff', background: '#18201e', fontSize: 25},
  recording: {marginLeft: 'auto', color: '#11a17c', fontSize: 25},
  main: {height: 1600, padding: '35px 42px 20px', boxSizing: 'border-box'},
  composer: {position: 'absolute', height: 72, left: 92, right: 92, bottom: 30, border: '1px solid #d9dfdc', borderRadius: 24, padding: '0 15px 0 24px', display: 'flex', alignItems: 'center', color: '#929a97', background: '#fff', fontSize: 20, boxShadow: '0 8px 22px rgba(27,50,44,.07)'},
  centerStage: {height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 28px 120px', boxSizing: 'border-box'},
  milestone: {fontSize: 20, fontWeight: 900, letterSpacing: '.12em', color: '#0d8e6c', marginBottom: 38},
  you: {fontSize: 18, fontWeight: 900, color: '#717976', letterSpacing: '.14em', marginBottom: 16},
  heroQuestion: {background: '#17201e', color: '#fff', borderRadius: 38, padding: '48px 42px', minHeight: 430, boxSizing: 'border-box', fontSize: 62, lineHeight: 1.18, fontWeight: 760, letterSpacing: '-.035em', boxShadow: '0 28px 60px rgba(23,32,30,.2)'},
  cursor: {display: 'inline-block', width: 5, height: '1em', marginLeft: 7, verticalAlign: '-.1em', background: '#55ddb5', borderRadius: 3},
  slow: {fontSize: 16, color: '#88908d', letterSpacing: '.15em', fontWeight: 900, textAlign: 'center', marginTop: 28},
  threadStage: {height: '100%', display: 'flex', flexDirection: 'column'},
  compactQuestion: {alignSelf: 'flex-end', maxWidth: 800, borderRadius: 23, padding: '18px 24px', background: '#edf1ef', fontSize: 22, fontWeight: 650, lineHeight: 1.35},
  assistant: {height: 76, display: 'flex', alignItems: 'center', gap: 14, fontSize: 22},
  answerBody: {position: 'relative', flex: 1, borderTop: '1px solid #e6eae8', paddingTop: 34},
  eyebrow: {fontSize: 16, fontWeight: 900, color: '#0d9270', letterSpacing: '.13em', marginBottom: 15},
  sceneTitle: {fontSize: 48, lineHeight: 1.08, margin: '0 0 28px', letterSpacing: '-.035em'},
  formulaStack: {display: 'flex', flexDirection: 'column', gap: 17},
  formulaRow: {height: 126, background: '#f1f5f3', borderLeft: '7px solid #14a880', borderRadius: 18, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 27px', gap: 8},
  loopCard: {display: 'grid', gridTemplateRows: 'auto 1fr', height: '100%'},
  largeFormula: {fontFamily: 'Georgia, serif', fontSize: 63, background: '#eaf5f1', borderRadius: 20, padding: '24px 30px', color: '#087457'},
  pair: {display: 'flex', flexDirection: 'column', fontFamily: 'Georgia, serif', fontSize: 34, gap: 12, marginTop: 18},
  circleGraph: {width: '100%', height: 560, marginTop: -30},
  sketchStage: {height: '100%', paddingTop: 18},
  sketchQuestionRow: {height: 455, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 20},
  sketchCard: {width: 330, height: 330, background: '#f0f0ee', borderRadius: 24, padding: 13, boxSizing: 'border-box'},
  sketchImage: {width: '100%', height: '100%', objectFit: 'cover', borderRadius: 17, filter: 'contrast(1.06)'},
  smallQuestion: {background: '#edf1ef', padding: '20px 23px', borderRadius: 21, fontSize: 24, fontWeight: 700},
  sketchAnswer: {position: 'relative', paddingTop: 28, borderTop: '1px solid #e3e8e5'},
  greenFormula: {fontFamily: 'Georgia, serif', fontSize: 29, padding: '18px 22px', borderLeft: '6px solid #12a47c', background: '#edf7f3', marginBottom: 13},
  miniSpiral: {width: '100%', height: 500, marginTop: -35},
  speedPill: {position: 'absolute', bottom: 25, right: 5, height: 48, border: '1px solid #d5deda', background: '#fff', borderRadius: 24, display: 'flex', alignItems: 'center', gap: 12, padding: '0 16px', fontSize: 14, color: '#7b8581'},
  processStack: {display: 'flex', flexDirection: 'column', gap: 22, marginTop: 45},
  processCard: {height: 210, background: '#f0f5f3', border: '1px solid #dfe8e4', borderRadius: 28, display: 'grid', gridTemplateColumns: '90px 1fr 50px', alignItems: 'center', padding: '0 28px'},
  refinementQuestion: {background: '#edf1ef', borderRadius: 23, padding: '19px 24px', fontSize: 22, fontWeight: 700, lineHeight: 1.35, marginBottom: 28},
  finalStage: {height: '100%', display: 'flex', flexDirection: 'column'},
  finalHeading: {marginBottom: 14},
  surfaceCard: {height: 670, borderRadius: 28, background: 'radial-gradient(circle,#fff 0%,#eceeef 100%)', overflow: 'hidden', border: '1px solid #d9dcdd'},
  surfaceSvg: {width: '100%', height: '100%', overflow: 'visible'},
  hybridFormula: {fontFamily: 'SFMono-Regular, Menlo, monospace', fontSize: 20, lineHeight: 1.45, background: '#19201f', color: '#eef8f5', borderRadius: 24, padding: '24px 27px', margin: '20px 0 13px', whiteSpace: 'pre-wrap'},
  finalCheck: {fontSize: 20, fontWeight: 800, color: '#087457', textAlign: 'center'},
  cutscene: {background: 'radial-gradient(circle at 50% 38%,#fff 0%,#eceeef 64%,#d4d7d8 100%)', color: '#202423', fontFamily: 'Inter, Avenir Next, Arial, sans-serif', overflow: 'hidden'},
  cutsceneGraph: {position: 'absolute', left: -75, right: -75, top: 310, height: 1040, transformOrigin: '50% 50%'},
  surfaceLabel: {position: 'absolute', top: 95, left: 62, fontSize: 22, fontWeight: 900, letterSpacing: '.17em', color: '#626967'},
  nextAct: {position: 'absolute', left: 70, right: 70, bottom: 135, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', fontSize: 32, fontWeight: 900, letterSpacing: '.09em', textAlign: 'right'},
};
