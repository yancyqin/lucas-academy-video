import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
} from 'remotion';
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

export const ROLLER_COASTER_M3_BUILD_FPS = 30;
export const ROLLER_COASTER_M3_BUILD_DURATION = 510;

/** The request finishes typing and holds. */
const QUESTION_END = 84;
/** The agent build runs fast and short — it is a transition, not the subject. */
const BUILD_END = 156;
/** Everything after this frame belongs to the word cloud. */
const CLOUD_START = BUILD_END;
/** Cloud-local frames: 5.8 s of spread, then 2.2 s of collapse. */
const SPREAD_FRAMES = 174;
const CONVERGE_START = SPREAD_FRAMES;
const CONVERGE_FRAMES = 66;
const READY_LOCAL = 232;
/** The last second is a clean fade into the game recording. */
const FADE_START = 480;
const FADE_END = 510;

/** Where each stage starts emitting, in cloud-local frames. */
const STAGE_START: Record<FragmentStage, number> = {
  formula: 0,
  geometry: 26,
  runtime: 58,
  testing: 108,
  deploy: 140,
};
/** The gap between two fragments of one stage; it shrinks as the work speeds up. */
const STAGE_SPACING: Record<FragmentStage, number> = {
  formula: 3.2,
  geometry: 3,
  runtime: 2.9,
  testing: 4.2,
  deploy: 3.6,
};
/** How long a fragment takes to reach its place. Later work flies out faster. */
const STAGE_TRAVEL: Record<FragmentStage, number> = {
  formula: 58,
  geometry: 53,
  runtime: 48,
  testing: 43,
  deploy: 38,
};

const CENTER_X = 960;
const CENTER_Y = 540;
const BASE_RADIUS = 715;
const Y_SQUASH = 0.56;
/** The golden angle — the same constant the ride itself is built on. */
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

const LAYER_SIZE = [19, 26, 33];
const LAYER_ALPHA = [0.44, 0.76, 1];
const LAYER_BLUR = [3, 1.1, 0];
const LAYER_PARALLAX = [0.35, 0.7, 1.15];
/** Each depth layer fills its own spiral, turned so the three never line up. */
const LAYER_PHASE = [0, 2.1, 4.2];
/**
 * Disjoint annuli. The near and middle layers are kept out of the centre so
 * the calculation the fragments come from stays readable underneath them; the
 * far layer, which is dim and blurred, is free to drift across everything.
 */
const LAYER_SPAN: [number, number][] = [[0.28, 1], [0.42, 0.8], [0.6, 1]];

/** Deterministic per-fragment jitter — a Remotion render may not use random. */
const hash = (index: number, salt: number) => {
  const value = Math.sin((index + 1) * 12.9898 + salt * 78.233) * 43758.5453;
  return value - Math.floor(value);
};

const clamp = (value: number) => Math.max(0, Math.min(1, value));
const ease = (value: number) => value * value * (3 - 2 * value);
const easeOut = (value: number) => 1 - Math.pow(1 - value, 3);
const typeText = (text: string, progress: number) =>
  text.slice(0, Math.ceil(text.length * ease(clamp(progress))));

/** Roughly how much room a fragment's type takes, for the relaxation below. */
const measure = (fragment: {text: string; layer: 0 | 1 | 2; weight?: number; chip?: string}) => {
  const size = LAYER_SIZE[fragment.layer] * (fragment.weight ?? 1);
  // The cloud is set in a monospace face, so a character count is an accurate
  // width; a chip adds its padding, its gap and its mark.
  const width = fragment.text.length * size * 0.58 + (fragment.chip ? 32 + size * 0.7 : 0);
  const height = size * (fragment.chip ? 1.9 : 1.35);
  return {size, width, height};
};

/** Emission frame, place on the spiral, then push the type apart, once. */
const PLACED = (() => {
  const seenPerStage = new Map<FragmentStage, number>();
  const seenPerLayer = new Map<number, number>();
  const perLayerTotal = buildFragments.reduce<Record<number, number>>((counts, fragment) => {
    counts[fragment.layer] = (counts[fragment.layer] ?? 0) + 1;
    return counts;
  }, {});

  const placed = buildFragments.map((fragment, index) => {
    const seen = seenPerStage.get(fragment.stage) ?? 0;
    seenPerStage.set(fragment.stage, seen + 1);
    // Phyllotaxis WITHIN each depth layer: the golden angle spreads a layer
    // evenly over its own annulus. The three layers are turned against each
    // other, and the innermost band is left clear for the calculation the
    // fragments are thrown from.
    const rank = seenPerLayer.get(fragment.layer) ?? 0;
    seenPerLayer.set(fragment.layer, rank + 1);
    const [near, far] = LAYER_SPAN[fragment.layer];
    const radial = near + (far - near) * Math.sqrt((rank + 0.5) / perLayerTotal[fragment.layer]);
    const angle = rank * GOLDEN_ANGLE + LAYER_PHASE[fragment.layer] + (hash(index, 1) - 0.5) * 0.22;
    const radius = BASE_RADIUS * radial * (0.96 + hash(index, 4) * 0.09);
    const tilt = (hash(index, 5) - 0.5) * 10;
    const flat = measure(fragment);
    // Long type set on a slight tilt sweeps a taller box than its line height.
    const box = {
      ...flat,
      height: flat.height + Math.abs(Math.sin((tilt * Math.PI) / 180)) * flat.width,
    };
    return {
      ...fragment,
      index,
      emit: STAGE_START[fragment.stage] + seen * STAGE_SPACING[fragment.stage],
      travel: STAGE_TRAVEL[fragment.stage],
      spin: (0.5 + hash(index, 2) * 0.95) * (hash(index, 3) > 0.5 ? 1 : -1),
      tilt,
      bob: hash(index, 6) * Math.PI * 2,
      box,
      x: Math.cos(angle) * radius,
      y: Math.sin(angle) * radius * Y_SQUASH,
    };
  });

  // An even spiral spaces CENTRES, not set type, and these fragments are long.
  // A few passes of "if two boxes touch, push them apart" turn an even spiral
  // into a readable one without giving up the spiral's shape. Deterministic:
  // same inputs, same frames, every render.
  const movable = placed.filter(fragment => fragment.layer > 0);
  const PAD = 15;
  for (let pass = 0; pass < 160; pass++) {
    let moved = false;
    for (let a = 0; a < movable.length; a++) {
      for (let b = a + 1; b < movable.length; b++) {
        const one = movable[a];
        const two = movable[b];
        const dx = two.x - one.x;
        const dy = two.y - one.y;
        const overlapX = (one.box.width + two.box.width) / 2 + PAD - Math.abs(dx);
        const overlapY = (one.box.height + two.box.height) / 2 + PAD - Math.abs(dy);
        if (overlapX <= 0 || overlapY <= 0) continue;
        moved = true;
        // Separate along the cheaper axis; for wide type that is nearly always
        // vertical, which is also where this cloud has room to give.
        if (overlapY / (one.box.height + two.box.height) <= overlapX / (one.box.width + two.box.width)) {
          const push = (overlapY / 2 + 0.5) * (dy >= 0 ? 1 : -1);
          one.y -= push;
          two.y += push;
        } else {
          const push = (overlapX / 2 + 0.5) * (dx >= 0 ? 1 : -1);
          one.x -= push;
          two.x += push;
        }
      }
    }
    // Nothing may leave the frame, and nothing may sit on the core.
    for (const fragment of movable) {
      const limitX = 900 - fragment.box.width / 2;
      const limitY = 452 - fragment.box.height / 2;
      fragment.x = Math.max(-limitX, Math.min(limitX, fragment.x));
      fragment.y = Math.max(-limitY, Math.min(limitY, fragment.y));
      const clear = Math.hypot(fragment.x / 430, fragment.y / 150);
      if (clear < 1 && clear > 1e-6) {
        fragment.x /= clear;
        fragment.y /= clear;
      }
    }
    if (!moved) break;
  }

  // Back to polar, so the flight out and the collapse home stay one motion.
  return placed.map(fragment => ({
    ...fragment,
    angle: Math.atan2(fragment.y / Y_SQUASH, fragment.x),
    radius: Math.hypot(fragment.x, fragment.y / Y_SQUASH),
  }));
})();

export const RollerCoasterMilestone3BuildVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const fade = interpolate(frame, [FADE_START, FADE_END], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  // The thread opens out into the build itself: as the cloud takes over, the
  // chat window's chrome dissolves so the finish is full frame.
  const expand = ease(clamp((frame - CLOUD_START) / 42));

  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill style={{...styles.canvas, opacity: fade}}>
        <AbsoluteFill style={{opacity: 1 - expand}}>
          <Ambient frame={frame} />
          <div style={styles.window}>
            <Header frame={frame} />
            <main style={styles.main}>
              {frame < QUESTION_END ? (
                <QuestionScene frame={frame} />
              ) : (
                <AgentBuildScene frame={frame} />
              )}
            </main>
            <Composer />
          </div>
        </AbsoluteFill>
        {frame >= CLOUD_START ? <BuildWordCloud frame={frame} expand={expand} /> : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const activeStage = (local: number): FragmentStage => {
  let current: FragmentStage = 'formula';
  for (const stage of STAGE_ORDER) if (local >= STAGE_START[stage]) current = stage;
  return current;
};

const BuildWordCloud: React.FC<{frame: number; expand: number}> = ({frame, expand}) => {
  const local = frame - CLOUD_START;
  const gather = ease(clamp((local - CONVERGE_START) / CONVERGE_FRAMES));
  const ready = ease(clamp((local - READY_LOCAL) / 28));
  // The whole field breathes faster as the build accelerates.
  const tempo = 1 + 0.9 * ease(clamp(local / SPREAD_FRAMES));
  const swayX = Math.sin(local / 34) * 13;
  const swayY = Math.cos(local / 41) * 9;
  const stage = activeStage(local);
  const stageIndex = STAGE_ORDER.indexOf(stage);
  const progress = clamp(local / (SPREAD_FRAMES + CONVERGE_FRAMES));

  return (
    <AbsoluteFill
      style={{
        ...styles.cloudStage,
        top: 42 * (1 - expand),
        bottom: 48 * (1 - expand),
        left: 64 * (1 - expand),
        right: 64 * (1 - expand),
        borderRadius: 30 * (1 - expand),
        opacity: expand,
      }}
    >
      <div style={styles.cloudGrid} />
      <StageRings local={local} gather={gather} />
      <div style={{...styles.coreShade, opacity: 0.85 * (1 - ready)}} />

      {PLACED.map((fragment) => {
        const born = local - fragment.emit;
        if (born <= 0) return null;
        const travel = easeOut(clamp(born / fragment.travel));
        const settled = clamp((born - fragment.travel) / 90);
        const appear = clamp(born / 7);
        const opacity =
          LAYER_ALPHA[fragment.layer] * appear * (1 - 0.34 * settled)
          * (1 - Math.pow(gather, 1.4)) * (1 - ready);
        if (opacity <= 0.004) return null;
        // The spin is a TRANSIT, not a destination: a fragment swings out along
        // its own arc and settles on the layer's even spiral, so dense type
        // never lands on dense type.
        const angle = fragment.angle + fragment.spin * (1 - travel)
          + gather * gather * 2.6 * fragment.spin;
        const radius = fragment.radius * travel * (1 - gather);
        const parallax = LAYER_PARALLAX[fragment.layer];
        const bob = Math.sin((local * tempo) / 19 + fragment.bob) * 5 * (1 - gather);
        const x = CENTER_X + Math.cos(angle) * radius + swayX * parallax;
        const y = CENTER_Y + Math.sin(angle) * radius * Y_SQUASH + swayY * parallax + bob;
        const scale = (0.62 + 0.38 * travel) * (1 - 0.45 * gather);
        const size = LAYER_SIZE[fragment.layer] * (fragment.weight ?? 1);
        const color = STAGE_COLOR[fragment.stage];
        const blur = LAYER_BLUR[fragment.layer] + gather * 3;

        return (
          <span
            key={fragment.text}
            style={{
              ...(fragment.chip ? styles.chip : styles.fragment),
              left: x,
              top: y,
              fontSize: size,
              color,
              opacity,
              filter: blur > 0.05 ? `blur(${blur.toFixed(2)}px)` : undefined,
              transform: `translate(-50%, -50%) rotate(${(fragment.tilt * (0.35 + 0.65 * travel)).toFixed(2)}deg) scale(${scale.toFixed(4)})`,
              ...(fragment.chip
                ? {borderColor: `${color}55`, boxShadow: `0 0 ${(18 * parallax).toFixed(1)}px ${color}22`}
                : {textShadow: `0 0 ${(16 + size * 0.5).toFixed(0)}px ${color}66`}),
            }}
          >
            {fragment.chip ? <i style={{...styles.chipMark, color}}>{fragment.chip}</i> : null}
            {fragment.text}
          </span>
        );
      })}

      <CalculationCore local={local} gather={gather} ready={ready} tempo={tempo} />

      <div style={{...styles.stageCaption, opacity: (1 - ready) * clamp(local / 12)}}>
        <span style={{...styles.stageDot, background: STAGE_COLOR[stage]}} />
        <b style={{color: STAGE_COLOR[stage]}}>{gather > 0.35 ? 'RESOLVING' : STAGE_LABEL[stage]}</b>
        <small style={styles.stageIndex}>{String(stageIndex + 1).padStart(2, '0')} / 05</small>
      </div>

      <div style={{...styles.cloudMeta, opacity: (1 - ready) * clamp(local / 12)}}>
        <span>THE MANIFOLD · GOLDEN FUNNEL</span>
        <div style={styles.meterTrack}>
          <i style={{...styles.meterFill, width: `${(progress * 100).toFixed(1)}%`}} />
        </div>
        <strong>{Math.round(progress * 100)}%</strong>
      </div>

      <ReadyLockup ready={ready} />
    </AbsoluteFill>
  );
};

/** One expanding ring each time the build moves to the next kind of work. */
const StageRings: React.FC<{local: number; gather: number}> = ({local, gather}) => (
  <>
    {STAGE_ORDER.map((stage) => {
      const born = local - STAGE_START[stage];
      if (born < 0 || born > 60) return null;
      const t = born / 60;
      const size = 180 + easeOut(t) * 1520;
      return (
        <div
          key={stage}
          style={{
            ...styles.ring,
            width: size,
            height: size * Y_SQUASH,
            borderColor: STAGE_COLOR[stage],
            opacity: (1 - t) * 0.3 * (1 - gather),
          }}
        />
      );
    })}
  </>
);

/** The centre the fragments are thrown from, and collapse back into. */
const CalculationCore: React.FC<{local: number; gather: number; ready: number; tempo: number}> = ({
  local, gather, ready, tempo,
}) => {
  const wake = ease(clamp(local / 16));
  const dim = 1 - 0.42 * ease(clamp((local - 20) / 110));
  const pulse = 1 + Math.sin((local * tempo) / 8) * 0.035 + gather * 0.22;
  const opacity = wake * (dim + gather * 0.55) * (1 - ready);
  if (opacity <= 0.004) return null;

  return (
    <div style={{...styles.core, opacity, transform: `translate(-50%,-50%) scale(${pulse.toFixed(4)})`}}>
      <div
        style={{
          ...styles.coreRing,
          transform: `translate(-50%,-50%) rotate(${(local * (1.1 + gather * 5)).toFixed(2)}deg)`,
          opacity: 0.55 + gather * 0.45,
        }}
      />
      <div
        style={{
          ...styles.coreRing,
          ...styles.coreRingInner,
          transform: `translate(-50%,-50%) rotate(${(-local * (1.7 + gather * 7)).toFixed(2)}deg)`,
        }}
      />
      <div style={styles.coreLines}>
        {coreLines.map((line, index) => (
          <code
            key={line}
            style={{
              ...styles.coreLine,
              opacity: clamp((local - index * 5) / 14) * (index === 0 ? 1 : 0.74),
              fontSize: index === 0 ? 26 : 19,
            }}
          >
            {typeText(line, (local - index * 5) / 16)}
          </code>
        ))}
      </div>
    </div>
  );
};

const ReadyLockup: React.FC<{ready: number}> = ({ready}) => {
  if (ready <= 0) return null;
  return (
    <div
      style={{
        ...styles.readyLockup,
        opacity: ready,
        transform: `translate(-50%,-50%) scale(${(0.82 + ready * 0.18).toFixed(4)})`,
        filter: ready < 1 ? `blur(${((1 - ready) * 13).toFixed(2)}px)` : undefined,
      }}
    >
      <div style={styles.readyCheck}>✓</div>
      <h1 style={styles.readyTitle}>READY TO RIDE</h1>
      <p style={styles.readySubtitle}>GOLDEN FUNNEL · BUILD COMPLETE</p>
    </div>
  );
};

const QuestionScene: React.FC<{frame: number}> = ({frame}) => {
  const entrance = ease(clamp((frame - 6) / 18));
  // Typed at a human pace, then held: the one slow beat of the section. The
  // rate runs LINEAR — an eased reveal reads as a wipe, not as typing — with a
  // small wave on it so the hands behind it are not metronomic. The wave is
  // gentle enough that the character count never goes backwards.
  const typing = clamp((frame - 10) / 58);
  const rhythm = typing + 0.02 * Math.sin(typing * 11);
  const text = milestone3Question.slice(0, Math.floor(milestone3Question.length * rhythm));
  return (
    <section style={{...styles.questionStage, opacity: entrance}}>
      <div style={styles.milestone}>MILESTONE 3 · BUILD THE RIDE</div>
      <div style={styles.you}>YOU</div>
      <div style={styles.questionBubble}>
        {text}
        {frame < 76 ? <Cursor frame={frame} /> : null}
      </div>
      <div style={styles.questionNote}>THE REQUEST SLOWS DOWN · THE BUILD WILL NOT</div>
    </section>
  );
};

const AgentBuildScene: React.FC<{frame: number}> = ({frame}) => {
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
    <section style={styles.buildStage}>
      <div style={styles.compactQuestion}>{milestone3Question}</div>
      <div style={styles.agentRow}>
        <div style={styles.agentAvatar}>⌁</div>
        <b>Agent</b>
        <span>building in workspace</span>
        <em>{phase.speed}×</em>
      </div>
      <div style={styles.buildGrid}>
        <aside style={styles.planRail}>
          <div style={styles.planTitle}>BUILD PLAN</div>
          {milestone3BuildPhases.map((item, itemIndex) => {
            const done = itemIndex < index;
            const active = itemIndex === index;
            return (
              <div
                key={item.id}
                style={{
                  ...styles.planItem,
                  ...(active ? styles.planItemActive : {}),
                  opacity: itemIndex > index ? 0.42 : 1,
                }}
              >
                <span style={styles.planNumber}>{done ? '✓' : item.step}</span>
                <div><b>{item.label}</b><small>{item.title}</small></div>
              </div>
            );
          })}
        </aside>
        <div style={{...styles.agentPanel, opacity: enter, transform: `translateX(${10 * (1 - enter)}px)`}}>
          <div style={styles.panelTop}>
            <div><span>{phase.step}</span><b>{phase.label}</b></div>
            <div style={styles.running}><i /> RUNNING</div>
          </div>
          <h1 style={styles.phaseTitle}>{typeText(phase.title, progress / 0.12)}</h1>
          <div style={styles.filePath}>{typeText(phase.file, (progress - 0.05) / 0.12)}</div>
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
            <div style={{...styles.terminalCursor, opacity: frame % 8 < 5 ? 1 : 0}}>▋</div>
          </div>
          <div style={styles.phaseFooter}>
            <span>{index + 1} / {milestone3BuildPhases.length}</span>
            <div style={styles.progressTrack}><i style={{...styles.progressFill, width: `${overall * 100}%`}} /></div>
            <strong>{Math.round(overall * 100)}%</strong>
          </div>
        </div>
      </div>
    </section>
  );
};

const Header: React.FC<{frame: number}> = ({frame}) => (
  <header style={styles.header}>
    <div style={styles.dots}><i /><i /><i /></div>
    <div style={styles.headerTitle}>ROLLER COASTER · AGENT BUILD</div>
    <div style={{...styles.live, opacity: 0.65 + Math.sin(frame / 9) * 0.25}}>● MILESTONE 3</div>
  </header>
);

const Composer = () => <div style={styles.composer}><span>Message Agent</span><b>↑</b></div>;

const Ambient: React.FC<{frame: number}> = ({frame}) => (
  <AbsoluteFill style={styles.ambient}>
    <div style={{...styles.glow, transform: `translate(${Math.sin(frame / 90) * 35}px,${Math.cos(frame / 100) * 28}px)`}} />
    <div style={{...styles.glow, ...styles.glowBlue}} />
  </AbsoluteFill>
);

const Cursor: React.FC<{frame: number}> = ({frame}) => (
  <span style={{...styles.cursor, opacity: frame % 18 < 12 ? 1 : 0.15}} />
);

const styles: Record<string, React.CSSProperties> = {
  canvas: {background: '#e8f1ee', color: '#17201e', fontFamily: 'Inter, Avenir Next, Arial, sans-serif'},
  ambient: {background: 'linear-gradient(145deg,#e8f7f2 0%,#e8edf4 55%,#d7e4e5 100%)', overflow: 'hidden'},
  glow: {position: 'absolute', width: 850, height: 850, left: -180, top: -240, borderRadius: '50%', background: 'radial-gradient(circle,rgba(31,184,142,.23),rgba(31,184,142,0) 68%)', filter: 'blur(20px)'},
  glowBlue: {left: 1320, top: 470, background: 'radial-gradient(circle,rgba(54,113,203,.18),rgba(54,113,203,0) 68%)'},
  window: {position: 'absolute', inset: '42px 64px 48px', borderRadius: 30, overflow: 'hidden', background: 'rgba(255,255,255,.97)', boxShadow: '0 32px 100px rgba(31,58,51,.2)', border: '1px solid rgba(255,255,255,.8)'},
  header: {height: 76, padding: '0 30px', display: 'flex', alignItems: 'center', borderBottom: '1px solid #e6ebe8', background: '#fbfcfc'},
  dots: {display: 'flex', gap: 10},
  headerTitle: {position: 'absolute', left: '50%', transform: 'translateX(-50%)', fontSize: 18, fontWeight: 900, letterSpacing: '.08em'},
  live: {marginLeft: 'auto', color: '#0b936e', fontSize: 14, fontWeight: 900, letterSpacing: '.1em'},
  main: {height: 850, padding: '30px 54px 20px', boxSizing: 'border-box'},
  composer: {position: 'absolute', left: 330, right: 330, bottom: 22, height: 64, border: '1px solid #dce3df', borderRadius: 22, display: 'flex', alignItems: 'center', padding: '0 15px 0 24px', color: '#929b97', background: '#fff', boxShadow: '0 7px 18px rgba(32,60,52,.07)', fontSize: 18},
  questionStage: {height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 150px 92px', boxSizing: 'border-box'},
  milestone: {fontSize: 18, color: '#0d936f', fontWeight: 900, letterSpacing: '.15em', marginBottom: 32},
  you: {fontSize: 16, color: '#747d79', fontWeight: 900, letterSpacing: '.15em', marginBottom: 13},
  questionBubble: {minHeight: 250, borderRadius: 38, background: '#17201e', color: '#fff', padding: '57px 62px', boxSizing: 'border-box', fontSize: 72, lineHeight: 1.16, fontWeight: 780, letterSpacing: '-.04em', boxShadow: '0 28px 60px rgba(23,32,30,.22)'},
  cursor: {display: 'inline-block', width: 5, height: '1em', marginLeft: 8, verticalAlign: '-.1em', borderRadius: 3, background: '#50d8b1'},
  questionNote: {fontSize: 14, color: '#8a938f', fontWeight: 900, letterSpacing: '.16em', textAlign: 'center', marginTop: 27},
  buildStage: {height: '100%'},
  compactQuestion: {height: 54, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', fontSize: 18, fontWeight: 700, color: '#3c4643'},
  agentRow: {height: 52, display: 'flex', alignItems: 'center', gap: 11, fontSize: 18},
  agentAvatar: {width: 34, height: 34, borderRadius: 10, display: 'grid', placeItems: 'center', background: '#17201e', color: '#fff', fontSize: 23},
  buildGrid: {height: 670, display: 'grid', gridTemplateColumns: '405px 1fr', gap: 24, borderTop: '1px solid #e6ebe8', paddingTop: 20},
  planRail: {background: '#f2f6f4', borderRadius: 19, padding: '20px 14px', overflow: 'hidden'},
  planTitle: {fontSize: 12, color: '#78817e', fontWeight: 900, letterSpacing: '.14em', padding: '0 14px 12px'},
  planItem: {height: 89, borderRadius: 14, display: 'grid', gridTemplateColumns: '45px 1fr', alignItems: 'center', padding: '0 13px', gap: 7, marginBottom: 6},
  planItemActive: {background: '#fff', boxShadow: '0 8px 22px rgba(34,62,54,.09)', border: '1px solid #dce8e3'},
  planNumber: {width: 34, height: 34, borderRadius: 11, display: 'grid', placeItems: 'center', background: '#dcebe6', color: '#087558', fontSize: 12, fontWeight: 950},
  agentPanel: {background: '#fff', border: '1px solid #dfe6e3', borderRadius: 20, padding: '24px 30px', boxSizing: 'border-box', boxShadow: '0 14px 35px rgba(31,58,51,.08)'},
  panelTop: {height: 40, display: 'flex', alignItems: 'center', justifyContent: 'space-between'},
  running: {fontSize: 12, color: '#0b8a68', fontWeight: 900, letterSpacing: '.11em'},
  phaseTitle: {fontSize: 37, lineHeight: 1.08, letterSpacing: '-.03em', margin: '17px 0 15px', minHeight: 79},
  filePath: {height: 43, borderRadius: 10, background: '#eef3f1', color: '#63706b', display: 'flex', alignItems: 'center', padding: '0 14px', fontFamily: 'SFMono-Regular, Menlo, monospace', fontSize: 15},
  terminal: {height: 315, marginTop: 18, borderRadius: 16, background: '#17201e', padding: '22px 25px', boxSizing: 'border-box', color: '#eaf4f1', fontFamily: 'SFMono-Regular, Menlo, monospace'},
  terminalLine: {height: 55, display: 'flex', alignItems: 'center', gap: 14, fontSize: 17},
  terminalCursor: {color: '#4ed6ad', fontSize: 20},
  phaseFooter: {height: 47, display: 'grid', gridTemplateColumns: '45px 1fr 50px', alignItems: 'center', gap: 12, fontSize: 13, color: '#76807c'},
  progressTrack: {height: 7, borderRadius: 8, background: '#dfe7e4', overflow: 'hidden'},
  progressFill: {display: 'block', height: '100%', borderRadius: 8, background: 'linear-gradient(90deg,#19a77f,#3b80c8)'},

  cloudStage: {overflow: 'hidden', background: 'radial-gradient(circle at 50% 50%,#20393a 0%,#111c1e 42%,#070c0d 100%)', boxShadow: 'inset 0 0 0 1px rgba(145,240,210,.14)'},
  cloudGrid: {position: 'absolute', inset: 0, opacity: .1, backgroundImage: 'linear-gradient(rgba(145,240,210,.35) 1px,transparent 1px),linear-gradient(90deg,rgba(145,240,210,.35) 1px,transparent 1px)', backgroundSize: '64px 64px', maskImage: 'radial-gradient(circle at center,#000 0%,transparent 74%)'},
  coreShade: {position: 'absolute', left: '50%', top: '50%', width: 900, height: 620, transform: 'translate(-50%,-50%)', borderRadius: '50%', background: 'radial-gradient(ellipse at center,rgba(4,10,11,.92) 0%,rgba(4,10,11,.55) 46%,rgba(4,10,11,0) 72%)'},
  ring: {position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)', borderRadius: '50%', border: '1px solid', boxSizing: 'border-box'},
  fragment: {position: 'absolute', whiteSpace: 'nowrap', fontFamily: 'SFMono-Regular, Menlo, monospace', fontWeight: 700, letterSpacing: '-.03em', willChange: 'transform,opacity'},
  chip: {position: 'absolute', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', borderRadius: 8, border: '1px solid', background: 'rgba(6,16,17,.72)', fontFamily: 'SFMono-Regular, Menlo, monospace', fontWeight: 700, letterSpacing: '-.02em', willChange: 'transform,opacity'},
  chipMark: {fontStyle: 'normal', fontWeight: 900, opacity: .85},
  core: {position: 'absolute', left: '50%', top: '50%', width: 860, textAlign: 'center', transformOrigin: 'center'},
  coreRing: {position: 'absolute', left: '50%', top: '50%', width: 300, height: 300, borderRadius: '50%', border: '1px dashed rgba(142,240,207,.55)', boxShadow: '0 0 70px rgba(78,214,173,.26), inset 0 0 60px rgba(78,214,173,.1)'},
  coreRingInner: {width: 192, height: 192, borderStyle: 'solid', borderColor: 'rgba(158,200,255,.4)', boxShadow: 'none'},
  coreLines: {position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 7},
  coreLine: {display: 'block', whiteSpace: 'nowrap', color: '#f2fffb', fontFamily: 'SFMono-Regular, Menlo, monospace', fontWeight: 700, letterSpacing: '-.03em', textShadow: '0 0 26px rgba(142,240,207,.55)'},
  stageCaption: {position: 'absolute', left: 54, top: 44, display: 'flex', alignItems: 'center', gap: 12, fontSize: 15, fontWeight: 900, letterSpacing: '.2em'},
  stageDot: {width: 9, height: 9, borderRadius: '50%'},
  stageIndex: {color: '#7f978f', fontSize: 13},
  cloudMeta: {position: 'absolute', left: 54, right: 54, bottom: 44, display: 'grid', gridTemplateColumns: 'auto 1fr auto', alignItems: 'center', gap: 20, fontSize: 13, fontWeight: 900, letterSpacing: '.18em', color: '#7f978f'},
  meterTrack: {height: 3, borderRadius: 3, background: 'rgba(145,240,210,.16)', overflow: 'hidden'},
  meterFill: {display: 'block', height: '100%', borderRadius: 3, background: 'linear-gradient(90deg,#8ef0cf,#6fd6ff)'},
  readyLockup: {position: 'absolute', left: '50%', top: '50%', width: 1400, textAlign: 'center', color: '#fff', transformOrigin: 'center'},
  readyCheck: {width: 74, height: 74, margin: '0 auto 26px', borderRadius: 24, display: 'grid', placeItems: 'center', background: '#8ef0cf', color: '#0d1f1b', fontSize: 40, fontWeight: 950, boxShadow: '0 0 60px rgba(142,240,207,.5)'},
  readyTitle: {margin: 0, fontSize: 132, lineHeight: .94, letterSpacing: '-.055em', fontWeight: 900, textShadow: '0 0 70px rgba(142,240,207,.28)'},
  readySubtitle: {margin: '30px 0 0', color: '#8ef0cf', fontSize: 20, fontWeight: 900, letterSpacing: '.28em'},
};
