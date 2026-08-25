import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {
  milestone3BuildPhases,
  milestone3Question,
} from '../scripts/roller-coaster-milestone3';
import {
  buildFragments,
  coreLines,
  STAGE_COLOR,
  STAGE_LABEL,
  STAGE_ORDER,
  type FragmentStage,
} from '../scripts/roller-coaster-milestone3-fragments';

export const ROLLER_COASTER_M3_BUILD_VERTICAL_FPS = 30;
export const ROLLER_COASTER_M3_BUILD_VERTICAL_DURATION = 510;

const QUESTION_END = 84;
const BUILD_END = 156;
const CLOUD_START = BUILD_END;
const SPREAD_FRAMES = 174;
const CONVERGE_START = SPREAD_FRAMES;
const CONVERGE_FRAMES = 66;
const READY_LOCAL = 232;
const FADE_START = 480;
const FADE_END = 510;

const STAGE_START: Record<FragmentStage, number> = {
  formula: 0,
  geometry: 26,
  runtime: 58,
  testing: 108,
  deploy: 140,
};

const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));
const WIDTH = 1080;
const HEIGHT = 1920;
const CENTER_X = WIDTH / 2;
const CENTER_Y = HEIGHT / 2;

const clamp = (value: number) => Math.max(0, Math.min(1, value));
const ease = (value: number) => value * value * (3 - 2 * value);
const easeOut = (value: number) => 1 - Math.pow(1 - value, 3);
const typeText = (text: string, progress: number) =>
  text.slice(0, Math.ceil(text.length * ease(clamp(progress))));

const hash = (index: number, salt: number) => {
  const value = Math.sin((index + 1) * 12.9898 + salt * 78.233) * 43758.5453;
  return value - Math.floor(value);
};

/**
 * Native portrait placement. The cloud uses the full tall frame instead of
 * shrinking a landscape cloud into a horizontal card.
 */
const PORTRAIT_FRAGMENTS = (() => {
  const stageRank = new Map<FragmentStage, number>();
  return buildFragments.map((fragment, index) => {
    const rank = stageRank.get(fragment.stage) ?? 0;
    stageRank.set(fragment.stage, rank + 1);
    const angle = index * GOLDEN_ANGLE + fragment.layer * 0.82;
    const spread = Math.sqrt((index + 1) / buildFragments.length);
    const estimatedWidth = fragment.text.length * (12 + fragment.layer * 3.7);
    const radiusX = 130 + spread * 350;
    const radiusY = 250 + spread * 650;
    const x = Math.max(
      48 + estimatedWidth / 2,
      Math.min(WIDTH - 48 - estimatedWidth / 2, CENTER_X + Math.cos(angle) * radiusX),
    );
    const y = Math.max(150, Math.min(HEIGHT - 160, CENTER_Y + Math.sin(angle) * radiusY));
    return {
      ...fragment,
      index,
      emit: STAGE_START[fragment.stage] + rank * (fragment.stage === 'testing' ? 4.2 : 3.2),
      travel: 34 + (2 - fragment.layer) * 8,
      x,
      y,
      angle,
      spin: (hash(index, 2) > 0.5 ? 1 : -1) * (0.42 + hash(index, 3) * 0.72),
      bob: hash(index, 4) * Math.PI * 2,
      tilt: (hash(index, 5) - 0.5) * 8,
    };
  });
})();

export const RollerCoasterMilestone3BuildVerticalVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const fade = interpolate(frame, [FADE_START, FADE_END], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill style={{opacity: fade}}>
        {frame < QUESTION_END ? <PortraitQuestion frame={frame} /> : null}
        {frame >= QUESTION_END && frame < BUILD_END ? <PortraitBuild frame={frame} /> : null}
        {frame >= CLOUD_START ? <PortraitCloud frame={frame} /> : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const PortraitShell: React.FC<{children: React.ReactNode; frame: number}> = ({children, frame}) => (
  <AbsoluteFill style={styles.canvas}>
    <div
      style={{
        ...styles.ambientGlow,
        transform: `translate(${Math.sin(frame / 80) * 24}px,${Math.cos(frame / 96) * 28}px)`,
      }}
    />
    <div style={styles.window}>
      <PortraitHeader frame={frame} />
      {children}
      <div style={styles.composer}><span>Message Agent</span><b>↑</b></div>
    </div>
  </AbsoluteFill>
);

const PortraitHeader: React.FC<{frame: number}> = ({frame}) => (
  <header style={styles.header}>
    <div style={styles.logo}>⌁</div>
    <div style={styles.headerCopy}>
      <b style={styles.headerTitle}>ROLLER COASTER</b>
      <span style={styles.headerSubtitle}>AGENT BUILD</span>
    </div>
    <em style={{...styles.live, opacity: 0.7 + Math.sin(frame / 9) * 0.2}}>● M3</em>
  </header>
);

const PortraitQuestion: React.FC<{frame: number}> = ({frame}) => {
  const entrance = ease(clamp((frame - 6) / 18));
  const typing = clamp((frame - 10) / 58);
  const rhythm = typing + 0.02 * Math.sin(typing * 11);
  const text = milestone3Question.slice(0, Math.floor(milestone3Question.length * rhythm));
  return (
    <PortraitShell frame={frame}>
      <section style={{...styles.questionStage, opacity: entrance}}>
        <div style={styles.milestone}>MILESTONE 3 · BUILD THE RIDE</div>
        <div style={styles.you}>YOU</div>
        <div style={styles.questionBubble}>
          {text}
          {frame < 76 ? <Cursor frame={frame} /> : null}
        </div>
        <div style={styles.questionNote}>THE REQUEST SLOWS DOWN<br />THE BUILD WILL NOT</div>
      </section>
    </PortraitShell>
  );
};

const PortraitBuild: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - QUESTION_END;
  const span = BUILD_END - QUESTION_END;
  const phaseLength = span / milestone3BuildPhases.length;
  const index = Math.min(milestone3BuildPhases.length - 1, Math.floor(local / phaseLength));
  const phase = milestone3BuildPhases[index];
  const phaseLocal = local - index * phaseLength;
  const progress = clamp(phaseLocal / phaseLength);
  const enter = ease(clamp(phaseLocal / 4));
  const overall = clamp(local / span);

  return (
    <PortraitShell frame={frame}>
      <section style={styles.buildStage}>
        <div style={styles.compactQuestion}>{milestone3Question}</div>
        <div style={styles.agentRow}>
          <div style={styles.agentAvatar}>⌁</div>
          <div style={styles.agentCopy}><b>Agent</b><span>building in workspace</span></div>
          <em style={styles.speed}>{phase.speed}×</em>
        </div>
        <div style={styles.stepGrid}>
          {milestone3BuildPhases.map((item, itemIndex) => (
            <div
              key={item.id}
              style={{
                ...styles.step,
                ...(itemIndex === index ? styles.stepActive : {}),
                opacity: itemIndex > index ? 0.42 : 1,
              }}
            >
              <span style={styles.stepNumber}>{itemIndex < index ? '✓' : item.step}</span>
              <b>{item.label}</b>
            </div>
          ))}
        </div>
        <div style={{...styles.agentPanel, opacity: enter, transform: `translateY(${12 * (1 - enter)}px)`}}>
          <div style={styles.panelTop}>
            <div style={styles.panelIdentity}><span>{phase.step}</span><b>{phase.label}</b></div>
            <div style={styles.running}><i /> RUNNING</div>
          </div>
          <h1 style={styles.phaseTitle}>{typeText(phase.title, progress / 0.13)}</h1>
          <div style={styles.filePath}>{typeText(phase.file, (progress - 0.04) / 0.13)}</div>
          <div style={styles.terminal}>
            {phase.lines.map((line, lineIndex) => {
              const lineProgress = clamp((progress - 0.12 - lineIndex * 0.16) / 0.14);
              return (
                <div key={line} style={{...styles.terminalLine, opacity: lineProgress > 0 ? 1 : 0}}>
                  <span>{line.startsWith('✓') ? '✓' : line.startsWith('+') ? '+' : '›'}</span>
                  <code>{typeText(line.replace(/^[✓+]\s*/, ''), lineProgress)}</code>
                </div>
              );
            })}
          </div>
          <div style={styles.phaseFooter}>
            <span>{index + 1} / 6</span>
            <div style={styles.progressTrack}><i style={{...styles.progressFill, width: `${overall * 100}%`}} /></div>
            <strong>{Math.round(overall * 100)}%</strong>
          </div>
        </div>
      </section>
    </PortraitShell>
  );
};

const activeStage = (local: number): FragmentStage => {
  let current: FragmentStage = 'formula';
  for (const stage of STAGE_ORDER) if (local >= STAGE_START[stage]) current = stage;
  return current;
};

const PortraitCloud: React.FC<{frame: number}> = ({frame}) => {
  const local = frame - CLOUD_START;
  const gather = ease(clamp((local - CONVERGE_START) / CONVERGE_FRAMES));
  const ready = ease(clamp((local - READY_LOCAL) / 28));
  const stage = activeStage(local);
  const stageIndex = STAGE_ORDER.indexOf(stage);
  const progress = clamp(local / (SPREAD_FRAMES + CONVERGE_FRAMES));

  return (
    <AbsoluteFill style={styles.cloud}>
      <div style={styles.cloudGrid} />
      <div style={{...styles.coreShade, opacity: 0.9 * (1 - ready)}} />
      <div style={{...styles.cloudHeader, opacity: 1 - ready}}>
        <span style={{...styles.cloudDot, background: STAGE_COLOR[stage]}} />
        <b style={{...styles.stageName, color: STAGE_COLOR[stage]}}>{gather > 0.35 ? 'RESOLVING' : STAGE_LABEL[stage]}</b>
        <em style={styles.cloudIndex}>{String(stageIndex + 1).padStart(2, '0')} / 05</em>
      </div>

      {PORTRAIT_FRAGMENTS.map((fragment) => {
        const born = local - fragment.emit;
        if (born <= 0) return null;
        const travel = easeOut(clamp(born / fragment.travel));
        const opacity = (0.38 + fragment.layer * 0.29) * clamp(born / 7)
          * (1 - Math.pow(gather, 1.35)) * (1 - ready);
        if (opacity < 0.004) return null;
        const startAngle = fragment.angle + fragment.spin * (1 - travel) + gather * fragment.spin * 2.8;
        const x = CENTER_X + (fragment.x - CENTER_X) * travel * (1 - gather)
          + Math.cos(startAngle) * 32 * (1 - travel);
        const y = CENTER_Y + (fragment.y - CENTER_Y) * travel * (1 - gather)
          + Math.sin(startAngle) * 52 * (1 - travel)
          + Math.sin(local / 18 + fragment.bob) * 4 * (1 - gather);
        const size = (14 + fragment.layer * 4.5) * (fragment.weight ?? 1);
        const color = STAGE_COLOR[fragment.stage];
        return (
          <span
            key={fragment.text}
            style={{
              ...(fragment.chip ? styles.cloudChip : styles.fragment),
              left: x,
              top: y,
              fontSize: size,
              color,
              borderColor: fragment.chip ? `${color}66` : undefined,
              opacity,
              transform: `translate(-50%,-50%) rotate(${fragment.tilt * travel}deg) scale(${0.7 + travel * 0.3 - gather * 0.42})`,
              textShadow: `0 0 ${12 + size * 0.5}px ${color}66`,
            }}
          >
            {fragment.chip ? <i>{fragment.chip}</i> : null}{fragment.text}
          </span>
        );
      })}

      <PortraitCore local={local} gather={gather} ready={ready} />
      <div style={{...styles.cloudFooter, opacity: 1 - ready}}>
        <b>THE MANIFOLD · GOLDEN FUNNEL</b>
        <div style={styles.cloudMeter}><i style={{...styles.cloudMeterFill, width: `${progress * 100}%`}} /></div>
        <span>{Math.round(progress * 100)}%</span>
      </div>
      <Ready ready={ready} />
    </AbsoluteFill>
  );
};

const PortraitCore: React.FC<{local: number; gather: number; ready: number}> = ({local, gather, ready}) => {
  const opacity = ease(clamp(local / 16)) * (1 - ready);
  if (opacity < 0.004) return null;
  return (
    <div style={{...styles.core, opacity, transform: `translate(-50%,-50%) scale(${1 + gather * 0.16})`}}>
      <div style={{...styles.coreRing, transform: `translate(-50%,-50%) rotate(${local * (1.1 + gather * 4)}deg)`}} />
      <div style={styles.coreLines}>
        {coreLines.map((line, index) => (
          <code key={line} style={{fontSize: index === 0 ? 23 : 16, opacity: index === 0 ? 1 : 0.72}}>
            {typeText(line, (local - index * 5) / 16)}
          </code>
        ))}
      </div>
    </div>
  );
};

const Ready: React.FC<{ready: number}> = ({ready}) => {
  if (ready <= 0) return null;
  return (
    <div
      style={{
        ...styles.ready,
        opacity: ready,
        transform: `translate(-50%,-50%) scale(${0.84 + ready * 0.16})`,
        filter: ready < 1 ? `blur(${(1 - ready) * 10}px)` : undefined,
      }}
    >
      <div style={styles.readyCheck}>✓</div>
      <h1 style={styles.readyTitle}>READY<br />TO RIDE</h1>
      <p style={styles.readySubtitle}>GOLDEN FUNNEL · BUILD COMPLETE</p>
    </div>
  );
};

const Cursor: React.FC<{frame: number}> = ({frame}) => (
  <span style={{...styles.cursor, opacity: frame % 18 < 12 ? 1 : 0.15}} />
);

const styles: Record<string, React.CSSProperties> = {
  canvas: {background: 'linear-gradient(160deg,#e9f8f3 0%,#e8eef4 54%,#d7e5e4 100%)', color: '#17201e', fontFamily: 'Inter, Avenir Next, Arial, sans-serif', overflow: 'hidden'},
  ambientGlow: {position: 'absolute', width: 1080, height: 1080, left: -310, top: -240, borderRadius: '50%', background: 'radial-gradient(circle,rgba(31,184,142,.25),rgba(31,184,142,0) 68%)', filter: 'blur(25px)'},
  window: {position: 'absolute', inset: '42px 32px 46px', borderRadius: 46, overflow: 'hidden', background: 'rgba(255,255,255,.97)', boxShadow: '0 34px 105px rgba(31,58,51,.2)', border: '1px solid rgba(255,255,255,.85)'},
  header: {height: 108, padding: '0 30px', display: 'flex', alignItems: 'center', gap: 15, borderBottom: '1px solid #e4ebe8', background: '#fbfcfc'},
  logo: {width: 48, height: 48, borderRadius: 15, display: 'grid', placeItems: 'center', background: '#17201e', color: '#fff', fontSize: 28},
  headerCopy: {display: 'flex', flexDirection: 'column', gap: 3},
  headerTitle: {fontSize: 17, letterSpacing: '.06em'},
  headerSubtitle: {fontSize: 11, color: '#75807c', fontWeight: 800, letterSpacing: '.14em'},
  live: {marginLeft: 'auto', color: '#0b936e', fontSize: 14, fontWeight: 900, letterSpacing: '.1em', fontStyle: 'normal'},
  composer: {position: 'absolute', left: 72, right: 72, bottom: 36, height: 72, border: '1px solid #dce3df', borderRadius: 24, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 17px 0 25px', color: '#929b97', background: '#fff', boxShadow: '0 8px 22px rgba(32,60,52,.08)', fontSize: 18},
  questionStage: {height: 1650, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 48px 115px', boxSizing: 'border-box'},
  milestone: {fontSize: 17, color: '#0d936f', fontWeight: 900, letterSpacing: '.14em', marginBottom: 40},
  you: {fontSize: 15, color: '#747d79', fontWeight: 900, letterSpacing: '.15em', marginBottom: 16},
  questionBubble: {minHeight: 450, borderRadius: 40, background: '#17201e', color: '#fff', padding: '65px 56px', boxSizing: 'border-box', fontSize: 74, lineHeight: 1.08, fontWeight: 820, letterSpacing: '-.045em', boxShadow: '0 30px 70px rgba(23,32,30,.23)'},
  cursor: {display: 'inline-block', width: 6, height: '1em', marginLeft: 8, verticalAlign: '-.1em', borderRadius: 3, background: '#50d8b1'},
  questionNote: {fontSize: 14, lineHeight: 1.7, color: '#8a938f', fontWeight: 900, letterSpacing: '.16em', textAlign: 'center', marginTop: 34},
  buildStage: {padding: '22px 38px 130px', boxSizing: 'border-box'},
  compactQuestion: {height: 64, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', fontSize: 18, fontWeight: 750, color: '#3c4643'},
  agentRow: {height: 72, display: 'grid', gridTemplateColumns: '48px 1fr auto', alignItems: 'center', gap: 14},
  agentAvatar: {width: 44, height: 44, borderRadius: 14, display: 'grid', placeItems: 'center', background: '#17201e', color: '#fff', fontSize: 27},
  agentCopy: {display: 'flex', flexDirection: 'column', gap: 3, fontSize: 18},
  speed: {fontSize: 19, color: '#0b936e', fontWeight: 900, fontStyle: 'normal'},
  stepGrid: {display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, margin: '12px 0 18px'},
  step: {height: 72, borderRadius: 17, background: '#edf3f0', display: 'flex', alignItems: 'center', gap: 10, padding: '0 13px', border: '1px solid transparent'},
  stepActive: {background: '#fff', borderColor: '#b9ddd1', boxShadow: '0 8px 22px rgba(34,62,54,.1)'},
  stepNumber: {width: 27, height: 27, borderRadius: 9, display: 'grid', placeItems: 'center', background: '#dcebe6', color: '#087558', fontSize: 10, fontWeight: 950},
  agentPanel: {height: 1090, background: '#fff', border: '1px solid #dfe6e3', borderRadius: 28, padding: '32px 34px', boxSizing: 'border-box', boxShadow: '0 16px 40px rgba(31,58,51,.09)'},
  panelTop: {height: 52, display: 'flex', alignItems: 'center', justifyContent: 'space-between'},
  panelIdentity: {display: 'flex', alignItems: 'center', gap: 12},
  running: {fontSize: 12, color: '#0b8a68', fontWeight: 900, letterSpacing: '.11em'},
  phaseTitle: {fontSize: 50, lineHeight: 1.08, letterSpacing: '-.04em', margin: '34px 0 28px', minHeight: 164},
  filePath: {minHeight: 74, borderRadius: 14, background: '#eef3f1', color: '#63706b', display: 'flex', alignItems: 'center', padding: '12px 18px', boxSizing: 'border-box', overflowWrap: 'anywhere', fontFamily: 'SFMono-Regular, Menlo, monospace', fontSize: 17, lineHeight: 1.4},
  terminal: {height: 530, marginTop: 24, borderRadius: 22, background: '#17201e', padding: '30px 26px', boxSizing: 'border-box', color: '#eaf4f1', fontFamily: 'SFMono-Regular, Menlo, monospace'},
  terminalLine: {minHeight: 100, display: 'flex', alignItems: 'center', gap: 14, fontSize: 20, lineHeight: 1.35},
  phaseFooter: {height: 82, display: 'grid', gridTemplateColumns: '52px 1fr 56px', alignItems: 'center', gap: 14, fontSize: 13, color: '#76807c'},
  progressTrack: {height: 8, borderRadius: 8, background: '#dfe7e4', overflow: 'hidden'},
  progressFill: {display: 'block', height: '100%', borderRadius: 8, background: 'linear-gradient(90deg,#19a77f,#3b80c8)'},
  cloud: {background: 'radial-gradient(ellipse at 50% 50%,#20393a 0%,#111c1e 42%,#060a0b 100%)', overflow: 'hidden', color: '#fff', fontFamily: 'Inter, Avenir Next, Arial, sans-serif'},
  cloudGrid: {position: 'absolute', inset: 0, opacity: .1, backgroundImage: 'linear-gradient(rgba(145,240,210,.35) 1px,transparent 1px),linear-gradient(90deg,rgba(145,240,210,.35) 1px,transparent 1px)', backgroundSize: '64px 64px', maskImage: 'radial-gradient(ellipse at center,#000 0%,transparent 78%)'},
  coreShade: {position: 'absolute', left: '50%', top: '50%', width: 1000, height: 860, transform: 'translate(-50%,-50%)', borderRadius: '50%', background: 'radial-gradient(ellipse at center,rgba(4,10,11,.95) 0%,rgba(4,10,11,.62) 48%,rgba(4,10,11,0) 74%)'},
  cloudHeader: {position: 'absolute', left: 48, right: 48, top: 62, height: 54, display: 'grid', gridTemplateColumns: '12px 1fr auto', alignItems: 'center', gap: 14, fontSize: 16, letterSpacing: '.2em'},
  cloudDot: {width: 10, height: 10, borderRadius: '50%'},
  stageName: {fontSize: 16},
  cloudIndex: {color: '#7f978f', fontSize: 13, fontStyle: 'normal'},
  fragment: {position: 'absolute', whiteSpace: 'nowrap', fontFamily: 'SFMono-Regular, Menlo, monospace', fontWeight: 720, letterSpacing: '-.03em'},
  cloudChip: {position: 'absolute', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 7, padding: '7px 10px', borderRadius: 9, border: '1px solid', background: 'rgba(6,16,17,.74)', fontFamily: 'SFMono-Regular, Menlo, monospace', fontWeight: 720},
  core: {position: 'absolute', left: '50%', top: '50%', width: 920, textAlign: 'center', transformOrigin: 'center'},
  coreRing: {position: 'absolute', left: '50%', top: '50%', width: 360, height: 360, borderRadius: '50%', border: '1px dashed rgba(142,240,207,.55)', boxShadow: '0 0 80px rgba(78,214,173,.25),inset 0 0 65px rgba(78,214,173,.1)'},
  coreLines: {position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, color: '#f2fffb', textShadow: '0 0 28px rgba(142,240,207,.55)'},
  cloudFooter: {position: 'absolute', left: 48, right: 48, bottom: 62, display: 'grid', gridTemplateColumns: 'auto 1fr auto', alignItems: 'center', gap: 17, fontSize: 12, letterSpacing: '.14em', color: '#7f978f'},
  cloudMeter: {height: 4, borderRadius: 4, background: 'rgba(145,240,210,.16)', overflow: 'hidden'},
  cloudMeterFill: {display: 'block', height: '100%', borderRadius: 4, background: 'linear-gradient(90deg,#8ef0cf,#6fd6ff)'},
  ready: {position: 'absolute', left: '50%', top: '50%', width: 940, textAlign: 'center', transformOrigin: 'center', color: '#fff'},
  readyCheck: {width: 92, height: 92, margin: '0 auto 38px', borderRadius: 30, display: 'grid', placeItems: 'center', background: '#8ef0cf', color: '#0d1f1b', fontSize: 50, fontWeight: 950, boxShadow: '0 0 70px rgba(142,240,207,.5)'},
  readyTitle: {margin: 0, fontSize: 122, lineHeight: .9, letterSpacing: '-.055em', fontWeight: 900, textShadow: '0 0 70px rgba(142,240,207,.3)'},
  readySubtitle: {margin: '38px 0 0', color: '#8ef0cf', fontSize: 18, fontWeight: 900, letterSpacing: '.2em'},
};
