import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {
  milestone2FinalSurface,
  milestone2GeoGebraImage,
  milestone2Question,
  milestone2Steps,
} from '../scripts/roller-coaster-milestone2';

export const ROLLER_COASTER_M2_FPS = 30;
export const ROLLER_COASTER_M2_DURATION = 675;

const QUESTION_END = 150;
const STEP_STARTS = [150, 264, 354] as const;
const FINAL_START = 444;
const CUTSCENE_START = 570;

export const RollerCoasterMilestone2Video: React.FC = () => {
  const frame = useCurrentFrame();

  if (frame >= CUTSCENE_START) {
    return <SurfaceCutscene frame={frame} />;
  }

  return (
    <AbsoluteFill style={styles.canvas}>
      <Backdrop frame={frame} />
      <div style={styles.window}>
        <Header frame={frame} />
        <main style={styles.main}>
          {frame < QUESTION_END ? (
            <QuestionScene frame={frame} />
          ) : frame < FINAL_START ? (
            <IterationScene frame={frame} />
          ) : (
            <FinalScene frame={frame} />
          )}
        </main>
        <div style={styles.composer}>
          <span>Message ChatGPT</span>
          <div style={styles.send}>↑</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const QuestionScene: React.FC<{frame: number}> = ({frame}) => {
  const enter = ease(clamp((frame - 8) / 20));
  const typed = clamp((frame - 26) / 104);
  const text = milestone2Question.slice(
    0,
    Math.floor(milestone2Question.length * typed),
  );

  return (
    <div
      style={{
        ...styles.questionStage,
        opacity: enter,
        transform: `translateY(${interpolate(enter, [0, 1], [28, 0])}px)`,
      }}
    >
      <div style={styles.milestoneTag}>MILESTONE 2 · THE 3D TRACK</div>
      <div style={styles.you}>YOU</div>
      <div style={styles.questionBubble}>
        {text}
        {frame < 134 ? <span style={{opacity: frame % 20 < 12 ? 1 : 0}}>│</span> : null}
      </div>
      <div style={styles.slowLabel}>THE QUESTION SLOWS DOWN</div>
    </div>
  );
};

const IterationScene: React.FC<{frame: number}> = ({frame}) => {
  let index = 0;
  for (let i = STEP_STARTS.length - 1; i >= 0; i--) {
    if (frame >= STEP_STARTS[i]) {
      index = i;
      break;
    }
  }
  const nextStart = index === STEP_STARTS.length - 1 ? FINAL_START : STEP_STARTS[index + 1];
  const local = clamp((frame - STEP_STARTS[index]) / (nextStart - STEP_STARTS[index]));
  const step = milestone2Steps[index];
  const enter = ease(clamp(local / 0.1));
  const titleText = typeText(step.title, clamp((local - 0.03) / 0.25));
  const formulaText = typeText(step.formula, clamp((local - 0.2) / 0.38));
  const noteText = typeText(step.note, clamp((local - 0.52) / 0.3));
  const typingPhase = local < 0.3 ? 'title' : local < 0.64 ? 'formula' : local < 0.86 ? 'note' : 'done';

  return (
    <div style={styles.answerScene}>
      <CompactQuestion text={step.prompt} />
      <div style={styles.assistantLine}>
        <div style={styles.avatar}>✦</div>
        <span>ChatGPT</span>
        <span style={styles.stepCount}>ITERATION {index + 1} / 3</span>
      </div>
      <div
        style={{
          ...styles.iterationCard,
          opacity: enter,
          transform: `translateY(${interpolate(enter, [0, 1], [12, 0])}px)`,
        }}
      >
        <div style={styles.copyColumn}>
          <div style={styles.eyebrow}>{step.eyebrow}</div>
          <h1 style={styles.stepTitle}>
            {titleText}{typingPhase === 'title' ? <TypingCursor /> : null}
          </h1>
          <div style={styles.formula}>
            {formulaText}{typingPhase === 'formula' ? <TypingCursor light /> : null}
          </div>
          <p style={styles.note}>
            {noteText}{typingPhase === 'note' ? <TypingCursor /> : null}
          </p>
        </div>
        <TrackDiagram kind={step.kind} progress={ease(clamp((local - 0.22) / 0.6))} />
      </div>
      <SpeedRail speed={step.speed} progress={local} />
    </div>
  );
};

const FinalScene: React.FC<{frame: number}> = ({frame}) => {
  const {fps} = useVideoConfig();
  const local = frame - FINAL_START;
  const enter = spring({frame: local, fps, config: {damping: 18, stiffness: 100}});
  const formulaIn = ease(clamp((local - 16) / 50));
  const imageIn = ease(clamp((local - 28) / 52));
  const endIn = ease(clamp((local - 260) / 70));

  return (
    <div style={styles.finalScene}>
      <CompactQuestion text={milestone2Steps[2].prompt} />
      <div style={{...styles.finalTitleRow, opacity: enter}}>
        <div>
          <div style={styles.eyebrow}>FINAL GEOGEBRA SURFACE</div>
          <h1 style={styles.finalTitle}>Funnel → golden spiral → (0, 0, 0)</h1>
        </div>
        <div style={styles.finalSpeed}>20×</div>
      </div>
      <div style={styles.finalGrid}>
        <div
          style={{
            ...styles.finalFormulaCard,
            opacity: formulaIn,
            transform: `translateX(${interpolate(formulaIn, [0, 1], [-28, 0])}px)`,
          }}
        >
          <div style={styles.copyPaste}>ONE GEOGEBRA SURFACE</div>
          <pre style={styles.finalFormula}>{milestone2FinalSurface}</pre>
          <div style={styles.originProof}>
            <span style={styles.check}>✓</span>
            Starts high on Y · spirals down · ribbon closes at the origin
          </div>
        </div>
        <div
          style={{
            ...styles.geogebraFrame,
            opacity: imageIn,
            transform: `scale(${interpolate(imageIn, [0, 1], [0.96, 1])})`,
          }}
        >
          <Img
            src={staticFile(milestone2GeoGebraImage)}
            style={styles.geogebraImage}
          />
          <div style={styles.liveBadge}><span /> GEOGEBRA 3D</div>
        </div>
      </div>
      <div style={{...styles.finalCaption, opacity: endIn}}>
        ONE QUESTION · THREE ITERATIONS · ONE RIDEABLE SURFACE
      </div>
      <SpeedRail speed={20} progress={clamp(local / 120)} />
    </div>
  );
};

const SurfaceCutscene: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - CUTSCENE_START;
  const progress = clamp(local / (ROLLER_COASTER_M2_DURATION - CUTSCENE_START));
  const reveal = ease(clamp(local / 28));
  const blur = interpolate(progress, [0, 0.72, 1], [0, 0, 10]);
  const scale = interpolate(progress, [0, 1], [0.94, 1.08]);
  const nextIn = ease(clamp((progress - 0.38) / 0.36));
  const fade = interpolate(progress, [0.82, 1], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{...styles.cutscene, opacity: fade}}>
      <div
        style={{
          ...styles.surfaceTrackWrap,
          opacity: reveal,
          filter: `blur(${blur}px)`,
          transform: `scale(${scale})`,
        }}
      >
        <SurfaceFunctionGraph progress={ease(clamp(local / 26))} />
      </div>
      <div style={{...styles.cutsceneShade, opacity: interpolate(progress, [0, 1], [0, 0.48])}} />
      <div style={{...styles.surfaceImageLabel, opacity: reveal}}>SURFACE</div>
      <div style={{...styles.nextAct, opacity: nextIn}}>
        <span>MILESTONE 3</span>
        BUILD THE ROLLER COASTER
      </div>
    </AbsoluteFill>
  );
};

const SurfaceFunctionGraph: React.FC<{progress: number}> = ({progress}) => {
  const cells = makeSurfaceMeshCells();
  return (
    <svg viewBox="0 0 1600 900" style={styles.surfaceTrackSvg}>
      <g opacity={progress}>
        {cells.map((cell, index) => (
          <polygon
            key={index}
            points={cell.points}
            fill={cell.fill}
            stroke="#6f7075"
            strokeWidth="1.35"
            strokeLinejoin="round"
          />
        ))}
      </g>
    </svg>
  );
};

const CompactQuestion: React.FC<{text: string}> = ({text}) => (
  <div style={styles.compactRow}>
    <div style={styles.compactBubble}>{text}</div>
  </div>
);

const TypingCursor: React.FC<{light?: boolean}> = ({light = false}) => {
  const frame = useCurrentFrame();
  return (
    <span
      style={{
        ...styles.typingCursor,
        background: light ? '#b99dff' : '#17141f',
        opacity: frame % 12 < 8 ? 1 : 0.18,
      }}
    />
  );
};

const SpeedRail: React.FC<{progress: number; speed: number}> = ({progress, speed}) => (
  <div style={styles.speedRail}>
    <div style={styles.speedCopy}>
      <span>ANSWER PLAYBACK</span>
      <strong>{speed}×</strong>
    </div>
    <div style={styles.speedTrack}>
      <div style={{...styles.speedFill, width: `${Math.max(8, progress * 100)}%`}} />
    </div>
    <div style={styles.speedScale}>8× <span>→</span> 20×</div>
  </div>
);

type DiagramKind = (typeof milestone2Steps)[number]['kind'];

const TrackDiagram: React.FC<{kind: DiagramKind; progress: number}> = ({
  kind,
  progress,
}) => {
  const points = makeTrackPoints(kind);
  const path = pointsToPath(points);
  const ribbonPath = pointsToPath(points.map(([x, y], i) => [x + Math.sin(i * 0.35) * 11, y - 10]));
  const dash = 1300 * (1 - progress);

  return (
    <div style={styles.diagramCard}>
      <svg viewBox="0 0 660 460" style={styles.svg}>
        <defs>
          <linearGradient id={`track-${kind}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#ba96ff" />
            <stop offset="0.5" stopColor="#7c5cff" />
            <stop offset="1" stopColor="#20c997" />
          </linearGradient>
          <radialGradient id="glow">
            <stop offset="0" stopColor="#7658ff" stopOpacity="0.34" />
            <stop offset="1" stopColor="#7658ff" stopOpacity="0" />
          </radialGradient>
        </defs>
        <ellipse cx="330" cy="228" rx="260" ry="190" fill="url(#glow)" />
        <path d="M70 385 L570 385" stroke="#d9d4e8" strokeWidth="2" />
        <path d="M100 420 L530 80" stroke="#e4e0ed" strokeWidth="2" />
        <path d="M122 80 L122 410" stroke="#e4e0ed" strokeWidth="2" />
        {kind === 'mobius' ? (
          <path d={ribbonPath} fill="none" stroke="#cbbcf7" strokeWidth="24" opacity="0.75" />
        ) : null}
        <path
          d={path}
          fill="none"
          stroke={`url(#track-${kind})`}
          strokeWidth={kind === 'origin' ? 18 : 11}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray="1300"
          strokeDashoffset={dash}
        />
        <circle cx="330" cy="385" r="8" fill="#16131f" />
        {kind === 'origin' ? (
          <g opacity={progress}>
            <circle cx="330" cy="385" r="26" fill="none" stroke="#20c997" strokeWidth="4" />
            <text x="348" y="420" fill="#16131f" fontSize="24" fontWeight="800">(0, 0, 0)</text>
          </g>
        ) : null}
        <text x="586" y="397" fill="#e64646" fontSize="23" fontWeight="800">x</text>
        <text x="530" y="75" fill="#26a269" fontSize="23" fontWeight="800">y</text>
        <text x="105" y="72" fill="#3867d6" fontSize="23" fontWeight="800">z</text>
      </svg>
      <div style={styles.diagramLabel}>
        {kind === 'mobius' ? 'GOLDEN SPIRAL + WIDTH PARAMETER v' : 'PARAMETRIC 3D PREVIEW'}
      </div>
    </div>
  );
};

const makeTrackPoints = (kind: DiagramKind): [number, number][] => {
  const pts: [number, number][] = [];
  const turns = 3.3;
  for (let i = 0; i <= 110; i++) {
    const t = (i / 110) * Math.PI * 2 * turns;
    const base = kind === 'mobius' || kind === 'origin'
      ? 182 * Math.pow((1 + Math.sqrt(5)) / 2, -0.16 * t)
      : 190 * (1 - 0.76 * (i / 110));
    const x = 330 + base * Math.sin(t);
    const y = 72 + 313 * (i / 110) + base * 0.23 * Math.cos(t);
    pts.push([x, y]);
  }
  pts[pts.length - 1] = [330, 385];
  return pts;
};

const pointsToPath = (points: [number, number][]) =>
  points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`).join(' ');

const makeSurfaceMeshCells = () => {
  const cells: {depth: number; fill: string; points: string}[] = [];
  const phi = (1 + Math.sqrt(5)) / 2;

  const point = (u: number, v: number) => {
    const collapse = 1 - u / (6 * Math.PI);
    const transition = u - 4 * Math.PI * (1 - Math.exp(-u / (4 * Math.PI)));
    const radius = 7 * collapse * Math.pow(phi, (-2 * transition) / Math.PI);
    const tilt = 0.35 * Math.sin(0.6 * u);
    const offset = v * collapse * Math.cos(tilt);
    const x = (radius + offset) * Math.cos(u);
    const y = 8 * collapse + v * collapse * Math.sin(tilt);
    const z = (radius + offset) * Math.sin(u);
    const screenX = 790 + x * 79 + z * 19;
    const screenY = 105 + (8 - y) * 82 - z * 21;
    return {screenX, screenY, depth: z - x * 0.16};
  };

  const uSegments = 78;
  const vSegments = 5;
  for (let ui = 0; ui < uSegments; ui++) {
    const u0 = (ui / uSegments) * 6 * Math.PI;
    const u1 = ((ui + 1) / uSegments) * 6 * Math.PI;
    for (let vi = 0; vi < vSegments; vi++) {
      const v0 = -0.45 + (vi / vSegments) * 0.9;
      const v1 = -0.45 + ((vi + 1) / vSegments) * 0.9;
      const quad = [point(u0, v0), point(u1, v0), point(u1, v1), point(u0, v1)];
      const shade = 188 + Math.round((vi / Math.max(1, vSegments - 1)) * 25);
      cells.push({
        depth: quad.reduce((sum, p) => sum + p.depth, 0) / quad.length,
        fill: `rgb(${shade}, ${shade}, ${shade + 4})`,
        points: quad.map((p) => `${p.screenX.toFixed(1)},${p.screenY.toFixed(1)}`).join(' '),
      });
    }
  }

  return cells.sort((a, b) => a.depth - b.depth);
};

const typeText = (text: string, progress: number) =>
  text.slice(0, Math.floor(text.length * ease(clamp(progress))));

const Backdrop: React.FC<{frame: number}> = ({frame}) => (
  <AbsoluteFill style={styles.backdrop}>
    <div
      style={{
        ...styles.orb,
        left: `${12 + Math.sin(frame / 90) * 3}%`,
        top: `${8 + Math.cos(frame / 110) * 4}%`,
      }}
    />
    <div style={{...styles.orb, ...styles.orbTwo}} />
  </AbsoluteFill>
);

const Header: React.FC<{frame: number}> = ({frame}) => (
  <header style={styles.header}>
    <div style={styles.dots}><i /><i /><i /></div>
    <div style={styles.headerTitle}>Roller Coaster Function Lab</div>
    <div style={styles.headerStatus}>
      <span style={{opacity: 0.55 + Math.sin(frame / 15) * 0.2}}>●</span> MILESTONE 2
    </div>
  </header>
);

const clamp = (n: number) => Math.max(0, Math.min(1, n));
const ease = (n: number) => n * n * (3 - 2 * n);

const styles: Record<string, React.CSSProperties> = {
  canvas: {background: '#ebe7f3', fontFamily: 'Inter, Avenir Next, Arial, sans-serif', color: '#17141f'},
  backdrop: {background: 'linear-gradient(135deg, #f1eef8 0%, #e3ddf0 48%, #d8d2e9 100%)', overflow: 'hidden'},
  orb: {position: 'absolute', width: 650, height: 650, borderRadius: '50%', background: 'radial-gradient(circle, rgba(143,105,255,.28), rgba(143,105,255,0) 68%)', filter: 'blur(18px)'},
  orbTwo: {left: '66%', top: '45%', background: 'radial-gradient(circle, rgba(48,201,151,.18), rgba(48,201,151,0) 68%)'},
  window: {position: 'absolute', inset: '42px 64px 48px', borderRadius: 30, overflow: 'hidden', background: 'rgba(255,255,255,.96)', boxShadow: '0 32px 100px rgba(44,35,69,.20), 0 2px 10px rgba(44,35,69,.10)', border: '1px solid rgba(255,255,255,.8)'},
  header: {height: 76, display: 'flex', alignItems: 'center', borderBottom: '1px solid #ece8f1', padding: '0 30px', position: 'relative', background: '#fbfaff'},
  dots: {display: 'flex', gap: 10},
  headerTitle: {position: 'absolute', left: '50%', transform: 'translateX(-50%)', fontSize: 20, fontWeight: 750, letterSpacing: '-.01em'},
  headerStatus: {marginLeft: 'auto', fontSize: 15, fontWeight: 800, color: '#7252d4', letterSpacing: '.08em'},
  main: {height: 850, padding: '30px 54px 20px', boxSizing: 'border-box'},
  composer: {position: 'absolute', left: 330, right: 330, bottom: 22, height: 64, border: '1px solid #ded9e6', borderRadius: 22, display: 'flex', alignItems: 'center', padding: '0 15px 0 24px', color: '#9b96a5', background: '#fff', boxShadow: '0 7px 18px rgba(40,30,70,.07)', fontSize: 18},
  send: {marginLeft: 'auto', width: 38, height: 38, borderRadius: '50%', background: '#17141f', color: '#fff', display: 'grid', placeItems: 'center', fontSize: 22, fontWeight: 800},
  questionStage: {height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', paddingBottom: 75, boxSizing: 'border-box'},
  milestoneTag: {fontSize: 18, color: '#7354d6', fontWeight: 900, letterSpacing: '.14em', marginBottom: 36},
  you: {alignSelf: 'flex-start', marginLeft: 190, fontSize: 17, fontWeight: 900, letterSpacing: '.15em', color: '#77717f', marginBottom: 12},
  questionBubble: {width: 1420, minHeight: 260, borderRadius: 38, background: '#17141f', color: '#fff', padding: '58px 68px', boxSizing: 'border-box', fontSize: 70, lineHeight: 1.16, fontWeight: 760, letterSpacing: '-.035em', boxShadow: '0 28px 60px rgba(23,20,31,.22)'},
  slowLabel: {fontSize: 15, letterSpacing: '.18em', color: '#8e8796', fontWeight: 800, marginTop: 30},
  answerScene: {height: '100%', position: 'relative'},
  compactRow: {display: 'flex', justifyContent: 'flex-end', height: 68},
  compactBubble: {background: '#f0edf4', borderRadius: 18, padding: '15px 22px', fontSize: 19, fontWeight: 650, color: '#3c3744'},
  assistantLine: {height: 54, display: 'flex', alignItems: 'center', gap: 12, fontSize: 19, fontWeight: 800},
  avatar: {width: 34, height: 34, borderRadius: 10, display: 'grid', placeItems: 'center', background: '#17141f', color: '#fff'},
  stepCount: {marginLeft: 'auto', color: '#8c8495', fontSize: 14, letterSpacing: '.12em'},
  iterationCard: {display: 'grid', gridTemplateColumns: '1.03fr .97fr', gap: 34, height: 575, background: '#fff', padding: '22px 12px 22px 56px', boxSizing: 'border-box', borderTop: '1px solid #ece8f1'},
  copyColumn: {padding: '28px 34px 10px 0', display: 'flex', flexDirection: 'column'},
  eyebrow: {fontSize: 15, color: '#7453d8', fontWeight: 900, letterSpacing: '.15em', marginBottom: 18},
  stepTitle: {fontSize: 42, lineHeight: 1.08, letterSpacing: '-.03em', margin: '0 0 24px', maxWidth: 660, minHeight: 92},
  formula: {background: '#242129', color: '#eee9ff', borderRadius: 14, padding: '21px 24px', fontFamily: 'SFMono-Regular, Menlo, monospace', fontSize: 20, lineHeight: 1.45, wordBreak: 'break-word', minHeight: 86, boxSizing: 'border-box'},
  note: {fontSize: 22, lineHeight: 1.45, color: '#625b6b', maxWidth: 650, margin: '22px 5px 0', minHeight: 64},
  typingCursor: {display: 'inline-block', width: 3, height: '1.05em', marginLeft: 5, verticalAlign: '-.12em', borderRadius: 2},
  diagramCard: {borderRadius: 18, overflow: 'hidden', position: 'relative', background: '#f7f5fa', border: '1px solid #e7e2ed'},
  svg: {width: '100%', height: '100%'},
  diagramLabel: {position: 'absolute', left: 18, bottom: 16, padding: '9px 13px', borderRadius: 10, background: 'rgba(255,255,255,.86)', backdropFilter: 'blur(8px)', fontSize: 13, fontWeight: 900, letterSpacing: '.1em', color: '#5d5666'},
  speedRail: {position: 'absolute', left: 0, right: 0, bottom: 8, height: 50, display: 'grid', gridTemplateColumns: '190px 1fr 95px', gap: 15, alignItems: 'center'},
  speedCopy: {display: 'flex', alignItems: 'baseline', gap: 12, fontSize: 12, letterSpacing: '.08em', color: '#79717f', fontWeight: 900},
  speedTrack: {height: 7, borderRadius: 8, background: '#e5e0ea', overflow: 'hidden'},
  speedFill: {height: '100%', borderRadius: 8, background: 'linear-gradient(90deg,#9575ef,#7658dc,#20c997)'},
  speedScale: {fontSize: 16, fontWeight: 900, color: '#6d6575'},
  finalScene: {height: '100%', position: 'relative'},
  finalTitleRow: {display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', height: 116},
  finalTitle: {fontSize: 39, margin: '0 0 8px', letterSpacing: '-.025em'},
  finalSpeed: {fontSize: 42, fontWeight: 950, color: '#7555d9', marginBottom: 10},
  finalGrid: {display: 'grid', gridTemplateColumns: '.82fr 1.18fr', gap: 24, height: 590},
  finalFormulaCard: {borderRadius: 25, background: '#17141f', padding: '31px 28px', color: '#fff', boxSizing: 'border-box', overflow: 'hidden'},
  copyPaste: {fontSize: 13, fontWeight: 900, color: '#a98cff', letterSpacing: '.14em', marginBottom: 22},
  finalFormula: {fontFamily: 'SFMono-Regular, Menlo, monospace', whiteSpace: 'pre-wrap', fontSize: 16.5, lineHeight: 1.47, color: '#f0ebff', margin: 0},
  originProof: {marginTop: 27, paddingTop: 23, borderTop: '1px solid #37313f', display: 'flex', gap: 12, alignItems: 'center', fontSize: 17, lineHeight: 1.4, color: '#c8c0d1'},
  check: {width: 27, height: 27, borderRadius: '50%', background: '#20c997', color: '#082d22', display: 'grid', placeItems: 'center', fontWeight: 950, flexShrink: 0},
  geogebraFrame: {borderRadius: 25, overflow: 'hidden', background: '#fff', border: '1px solid #ded9e7', position: 'relative', boxShadow: '0 16px 36px rgba(45,35,70,.12)'},
  geogebraImage: {width: '100%', height: '100%', objectFit: 'cover', objectPosition: '63% 50%'},
  liveBadge: {position: 'absolute', right: 18, top: 18, padding: '10px 13px', borderRadius: 10, background: 'rgba(255,255,255,.92)', fontSize: 13, fontWeight: 900, letterSpacing: '.1em', boxShadow: '0 5px 15px rgba(0,0,0,.12)'},
  finalCaption: {position: 'absolute', left: '50%', bottom: 57, transform: 'translateX(-50%)', background: '#fff', border: '1px solid #e2dce9', borderRadius: 16, padding: '14px 24px', fontSize: 14, fontWeight: 950, letterSpacing: '.13em', boxShadow: '0 9px 25px rgba(40,30,70,.12)', whiteSpace: 'nowrap'},
  cutscene: {background: 'radial-gradient(circle at 52% 46%, #ffffff 0%, #eeeeef 64%, #d8d8da 100%)', color: '#222228', fontFamily: 'Inter, Avenir Next, Arial, sans-serif', overflow: 'hidden'},
  surfaceTrackWrap: {position: 'absolute', inset: '3% 5%', transformOrigin: '50% 52%'},
  surfaceTrackSvg: {width: '100%', height: '100%', overflow: 'visible'},
  cutsceneShade: {position: 'absolute', inset: 0, background: 'linear-gradient(90deg, rgba(235,235,237,.42) 0%, rgba(255,255,255,0) 42%, rgba(20,20,24,.18) 100%)'},
  surfaceImageLabel: {position: 'absolute', left: 96, top: 82, fontSize: 24, fontWeight: 900, letterSpacing: '.18em', color: '#55555d'},
  nextAct: {position: 'absolute', bottom: 76, right: 98, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', fontSize: 27, fontWeight: 900, letterSpacing: '.12em', color: '#24242a'},
};
