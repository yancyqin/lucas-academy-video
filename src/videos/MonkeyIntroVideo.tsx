import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import data from '../data/monkey-society.json';
import script from '../scripts/intro.en.json';

type WorldKey = 'winWin' | 'darkForest';

type Segment = {
  id: string;
  start: number;
  end: number;
  scene: string;
  caption: string;
  voiceover: string;
};

type TimelinePoint = {
  round: number;
  shareRate: number;
  totalBananas: number;
  betrayals: number;
  types: Record<string, {average: number; shareRate: number}>;
};

const fps = script.fps;
const segments = script.segments as Segment[];
const audioFiles = segments.map((segment, index) => {
  const number = String(index + 1).padStart(2, '0');
  return `audio/en/intro/${number}-${segment.id}.wav`;
});

export const MonkeyIntroVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const seconds = frame / fps;
  const active = currentSegment(seconds);
  const sceneProgress = active
    ? clamp((seconds - active.start) / Math.max(1, active.end - active.start), 0, 1)
    : 0;
  const bgWorld: WorldKey = seconds < 58 || seconds > 84 ? 'winWin' : 'darkForest';

  return (
    <AbsoluteFill style={styles.screen}>
      <IntroAudio />
      <BrightWorld worldKey={bgWorld} />
      <div style={styles.header}>
        <div>
          <div style={styles.brand}>Lucas Academy</div>
          <div style={styles.title}>Monkey Republic</div>
        </div>
        <div style={styles.badges}>
          {['AI', 'Data Science', 'Social Experiments'].map((tag) => (
            <span key={tag} style={styles.badgePill}>
              {tag}
            </span>
          ))}
        </div>
      </div>

      <div style={styles.scene}>
        {active?.scene === 'hero' && <HeroScene progress={sceneProgress} />}
        {active?.scene === 'rules' && <RulesScene progress={sceneProgress} />}
        {active?.scene === 'slow' && <SlowRoundsScene progress={sceneProgress} />}
        {active?.scene === 'society' && <SocietyScene progress={sceneProgress} />}
        {active?.scene === 'question' && <QuestionScene progress={sceneProgress} />}
        {active?.scene === 'vision' && <VisionScene progress={sceneProgress} />}
        {active?.scene === 'close' && <CloseScene progress={sceneProgress} />}
      </div>

      <Caption caption={active?.caption ?? ''} progress={sceneProgress} />
      <ProgressRail frame={frame} duration={durationInFrames} />
    </AbsoluteFill>
  );
};

const IntroAudio: React.FC = () => (
  <>
    {segments.map((segment, index) => (
      <Sequence
        key={segment.id}
        from={Math.round(segment.start * fps)}
        durationInFrames={Math.round((segment.end - segment.start) * fps)}
      >
        <Audio src={staticFile(audioFiles[index])} />
      </Sequence>
    ))}
  </>
);

const HeroScene: React.FC<{progress: number}> = ({progress}) => {
  const lift = interpolate(progress, [0, 1], [34, 0], {easing: Easing.out(Easing.cubic)});
  return (
    <div style={styles.heroGrid}>
      <div style={{...styles.heroCopy, transform: `translateY(${lift}px)`}}>
        <div style={styles.eyebrow}>
          Same monkeys.
          <br />
          Different rules.
        </div>
        <h1 style={styles.heroTitle}>A game that becomes a society.</h1>
        <p style={styles.heroText}>
          Students run simulations, change the world rules, and watch trust become visible.
        </p>
      </div>
      <MonkeyOrbit progress={progress} worldKey="winWin" />
    </div>
  );
};

const RulesScene: React.FC<{progress: number}> = ({progress}) => {
  const worldKey: WorldKey = progress < 0.55 ? 'winWin' : 'darkForest';
  const payoff = data.worlds[worldKey].payoff as unknown as Record<string, [number, number]>;
  const accent = worldKey === 'winWin' ? colors.green : colors.purple;
  return (
    <div style={styles.rulesLayout}>
      <div style={styles.choicePanel}>
        <div style={styles.panelTitle}>Every round</div>
        <div style={styles.choiceRow}>
          <ChoiceCard action="SHARE" emoji="🍌" accent={colors.green} />
          <div style={styles.choiceOr}>or</div>
          <ChoiceCard action="GRAB" emoji="✋" accent={colors.orange} />
        </div>
        <p style={styles.panelText}>Two actions are simple. The world behind them is not.</p>
      </div>
      <div style={styles.ruleTable}>
        <div style={{...styles.panelTitle, color: accent}}>
          {worldKey === 'winWin' ? 'Win-Win Jungle' : 'Dark Forest'}
        </div>
        <PayoffRows payoff={payoff} accent={accent} />
      </div>
    </div>
  );
};

const SlowRoundsScene: React.FC<{progress: number}> = ({progress}) => {
  const moments = data.teachingRuns.winWin;
  const index = Math.min(moments.length - 1, Math.floor(progress * moments.length));
  const moment = moments[index];
  const encounter = moment.encounter;
  return (
    <div style={styles.slowLayout}>
      <div style={styles.roundCard}>
        <div style={styles.roundLabel}>Slow round {moment.round}</div>
        <div style={styles.duel}>
          <MonkeyBadge name="Rookie Monkey" action={encounter.actions.left} score={encounter.scores.left} />
          <div style={styles.versus}>meets</div>
          <MonkeyBadge
            name={encounter.opponent.name}
            action={encounter.actions.right}
            score={encounter.scores.right}
          />
        </div>
        <div style={styles.payoffCallout}>
          Rookie: {formatSigned(encounter.payoff.left)} bananas · Opponent:{' '}
          {formatSigned(encounter.payoff.right)} bananas
        </div>
      </div>
      <div style={styles.causePanel}>
        <div style={styles.panelTitle}>Cause and effect</div>
        <ul style={styles.cleanList}>
          <li>Choices change banana totals.</li>
          <li>Memories change future trust.</li>
          <li>One round can echo into the next.</li>
        </ul>
      </div>
    </div>
  );
};

const SocietyScene: React.FC<{progress: number}> = ({progress}) => {
  const worldKey: WorldKey = progress < 0.52 ? 'winWin' : 'darkForest';
  const run = data.visualRuns[worldKey];
  const timeline = run.timeline as TimelinePoint[];
  const point = timeline[Math.min(timeline.length - 1, Math.floor(progress * timeline.length))];
  const accent = worldKey === 'winWin' ? colors.green : colors.purple;
  return (
    <div style={styles.societyLayout}>
      <div style={styles.miniSociety}>
        <MonkeyOrbit progress={progress} worldKey={worldKey} />
      </div>
      <div style={styles.metricsPanel}>
        <div style={{...styles.panelTitle, color: accent}}>
          {worldKey === 'winWin' ? 'Win-Win patterns' : 'Dark Forest patterns'}
        </div>
        <BigMetric label="Share rate" value={`${Math.round(point.shareRate * 100)}%`} accent={accent} />
        <BigMetric
          label="Bananas per monkey"
          value={String(Math.round(point.totalBananas / run.citizenCount))}
          accent={colors.orange}
        />
        <BigMetric label="Betrayals" value={String(point.betrayals)} accent={colors.red} />
      </div>
    </div>
  );
};

const QuestionScene: React.FC<{progress: number}> = ({progress}) => (
  <div style={styles.questionLayout}>
    <div style={styles.questionMark}>?</div>
    <div>
      <div style={styles.eyebrow}>Not a final answer</div>
      <h2 style={styles.questionTitle}>A question students carry out of the game.</h2>
      <p style={styles.questionText}>
        If rules can train strategy, how do we understand ourselves?
      </p>
      <p style={{...styles.questionText, opacity: interpolate(progress, [0.35, 0.8], [0, 1])}}>
        How do we think, create, and contribute to the real world?
      </p>
    </div>
  </div>
);

const VisionScene: React.FC<{progress: number}> = ({progress}) => (
  <div style={styles.visionPanel}>
    <div style={styles.eyebrow}>Lucas Academy Vision</div>
    <h2 style={styles.visionTitle}>Learning is not just about skills.</h2>
    <div style={styles.visionGrid}>
      {[
        ['Curiosity', 'thinking with better questions'],
        ['Discovery', 'creating through exploration'],
        ['Significance', 'searching for meaning in action'],
        ['Contribution', 'working on real-world problems that matter'],
      ].map(([word, line], index) => (
        <div
          key={word}
          style={{
            ...styles.visionCard,
            opacity: interpolate(progress, [index * 0.14, index * 0.14 + 0.25], [0, 1]),
            transform: `translateY(${interpolate(progress, [index * 0.14, index * 0.14 + 0.25], [22, 0])}px)`,
          }}
        >
          <strong>{word}</strong>
          <span>{line}</span>
        </div>
      ))}
    </div>
  </div>
);

const CloseScene: React.FC<{progress: number}> = ({progress}) => (
  <div style={styles.closePanel}>
    <div style={styles.closeMonkey}>🐵🍌</div>
    <h2 style={styles.closeTitle}>Monkey Republic</h2>
    <p style={styles.closeText}>A Lucas Academy social experiment</p>
    <div style={{...styles.closeTags, opacity: interpolate(progress, [0.2, 0.8], [0, 1])}}>
      <span>AI</span>
      <span>Game Design</span>
      <span>Data Science</span>
      <span>Meaningful Learning</span>
    </div>
  </div>
);

const Caption: React.FC<{caption: string; progress: number}> = ({caption, progress}) => (
  <div
    style={{
      ...styles.caption,
      opacity: interpolate(progress, [0, 0.08, 0.92, 1], [0, 1, 1, 0]),
    }}
  >
    {caption}
  </div>
);

const ProgressRail: React.FC<{frame: number; duration: number}> = ({frame, duration}) => (
  <div style={styles.progressRail}>
    <div style={{...styles.progressFill, width: `${(frame / duration) * 100}%`}} />
  </div>
);

const ChoiceCard: React.FC<{action: string; emoji: string; accent: string}> = ({action, emoji, accent}) => (
  <div style={{...styles.choiceCard, borderColor: accent}}>
    <div style={styles.choiceEmoji}>{emoji}</div>
    <div style={{...styles.choiceAction, color: accent}}>{action}</div>
  </div>
);

const PayoffRows: React.FC<{payoff: Record<string, [number, number]>; accent: string}> = ({payoff, accent}) => {
  const rows = [
    ['Share + Share', payoff.shareShare],
    ['Grab vs Share', payoff.grabShare],
    ['Share vs Grab', payoff.shareGrab],
    ['Grab + Grab', payoff.grabGrab],
  ] as const;
  return (
    <div style={styles.payoffRows}>
      {rows.map(([label, values]) => (
        <div key={label} style={styles.payoffLine}>
          <span>{label}</span>
          <strong style={{color: accent}}>
            {formatSigned(values[0])} / {formatSigned(values[1])}
          </strong>
        </div>
      ))}
    </div>
  );
};

const MonkeyBadge: React.FC<{name: string; action: string; score: number}> = ({name, action, score}) => {
  const share = action === 'SHARE';
  return (
    <div style={{...styles.monkeyBadge, borderColor: share ? colors.green : colors.orange}}>
      <div style={styles.badgeFace}>🐵</div>
      <div style={styles.badgeName}>{name}</div>
      <div style={{...styles.badgeAction, color: share ? colors.green : colors.orange}}>{action}</div>
      <div style={styles.badgeScore}>{score} bananas</div>
    </div>
  );
};

const BigMetric: React.FC<{label: string; value: string; accent: string}> = ({label, value, accent}) => (
  <div style={styles.bigMetric}>
    <span>{label}</span>
    <strong style={{color: accent}}>{value}</strong>
  </div>
);

const MonkeyOrbit: React.FC<{progress: number; worldKey: WorldKey}> = ({progress, worldKey}) => {
  const accent = worldKey === 'winWin' ? colors.green : colors.purple;
  const labels = ['Rookie', 'Sunny', 'Sneaky', 'Copycat', 'Learner', 'Suspicious', 'Grudger', 'Peacekeeper'];
  return (
    <div style={styles.orbitWrap}>
      <div style={{...styles.orbitRing, borderColor: accent}} />
      {labels.map((label, index) => {
        const angle = -Math.PI / 2 + (index / labels.length) * Math.PI * 2 + progress * 0.5;
        const x = Math.cos(angle) * 270;
        const y = Math.sin(angle) * 220;
        return (
          <div
            key={label}
            style={{
              ...styles.orbitMonkey,
              left: `calc(50% + ${x}px)`,
              top: `calc(50% + ${y}px)`,
              borderColor: index === 0 ? accent : colors.cardLine,
            }}
          >
            <span>🐵</span>
            <strong>{label}</strong>
          </div>
        );
      })}
      <div style={styles.orbitCenter}>
        <span>🍌</span>
        <strong>{worldKey === 'winWin' ? 'Trust grows' : 'Trust is tested'}</strong>
      </div>
    </div>
  );
};

const BrightWorld: React.FC<{worldKey: WorldKey}> = ({worldKey}) => {
  const dark = worldKey === 'darkForest';
  return (
    <AbsoluteFill
      style={{
        background: dark
          ? 'linear-gradient(180deg, #ddd6fe 0%, #dbeafe 46%, #dcfce7 100%)'
          : 'linear-gradient(180deg, #bae6fd 0%, #fef3c7 48%, #dcfce7 100%)',
      }}
    >
      <div style={{...styles.canopy, background: dark ? '#6d28d9' : '#15803d'}} />
      <div style={styles.sun}>{dark ? '◐' : '☀'}</div>
      <div style={styles.floatingBananas}>🍌 🍃 🍌 🍃 🍌 🍃 🍌</div>
      <div style={{...styles.hillBack, background: dark ? '#84cc16' : '#86efac'}} />
      <div style={{...styles.hillFront, background: dark ? '#4d7c0f' : '#65a30d'}} />
    </AbsoluteFill>
  );
};

function currentSegment(seconds: number) {
  return segments.find((segment) => seconds >= segment.start && seconds < segment.end) ?? segments[0];
}

function formatSigned(value: number) {
  return value > 0 ? `+${value}` : String(value);
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

const colors = {
  ink: '#2d2118',
  muted: '#67523a',
  cream: 'rgba(255, 251, 235, 0.9)',
  cardLine: 'rgba(120, 83, 31, 0.2)',
  green: '#16a34a',
  purple: '#7c3aed',
  orange: '#d97706',
  red: '#dc2626',
};

const panelBase: React.CSSProperties = {
  background: colors.cream,
  border: `2px solid ${colors.cardLine}`,
  borderRadius: 28,
  boxShadow: '0 28px 70px rgba(87, 68, 36, 0.14)',
};

const styles: Record<string, React.CSSProperties> = {
  screen: {
    color: colors.ink,
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    overflow: 'hidden',
  },
  canopy: {
    position: 'absolute',
    left: -120,
    right: -120,
    top: -130,
    height: 250,
    borderBottomLeftRadius: '50%',
    borderBottomRightRadius: '50%',
  },
  sun: {
    position: 'absolute',
    top: 56,
    right: 112,
    fontSize: 110,
    color: '#f59e0b',
  },
  floatingBananas: {
    position: 'absolute',
    left: 590,
    right: 430,
    top: 126,
    fontSize: 40,
    letterSpacing: 10,
    opacity: 0.45,
  },
  hillBack: {
    position: 'absolute',
    left: -120,
    right: -120,
    bottom: -22,
    height: 190,
    borderTopLeftRadius: '55%',
    borderTopRightRadius: '55%',
    opacity: 0.52,
  },
  hillFront: {
    position: 'absolute',
    left: -120,
    right: -120,
    bottom: -116,
    height: 230,
    borderTopLeftRadius: '52%',
    borderTopRightRadius: '52%',
  },
  header: {
    position: 'absolute',
    top: 50,
    left: 72,
    right: 72,
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  brand: {
    fontSize: 30,
    fontWeight: 950,
    color: '#7c2d12',
    textTransform: 'uppercase',
  },
  title: {
    marginTop: 6,
    fontSize: 74,
    lineHeight: 0.95,
    fontWeight: 1000,
  },
  badges: {
    display: 'flex',
    gap: 12,
    marginTop: 10,
  },
  badgePill: {
    padding: '12px 18px',
    borderRadius: 999,
    background: 'rgba(255, 251, 235, 0.86)',
    border: `2px solid ${colors.cardLine}`,
    color: '#7c2d12',
    fontSize: 22,
    fontWeight: 900,
  },
  scene: {
    position: 'absolute',
    left: 72,
    right: 72,
    top: 172,
    bottom: 158,
  },
  heroGrid: {
    height: '100%',
    display: 'grid',
    gridTemplateColumns: '650px 1fr',
    gap: 52,
    alignItems: 'center',
  },
  heroCopy: {
    ...panelBase,
    padding: 48,
  },
  eyebrow: {
    color: colors.green,
    fontSize: 34,
    fontWeight: 950,
  },
  heroTitle: {
    margin: '24px 0',
    fontSize: 80,
    lineHeight: 0.95,
    letterSpacing: 0,
  },
  heroText: {
    margin: 0,
    fontSize: 34,
    lineHeight: 1.25,
    color: colors.muted,
    fontWeight: 720,
  },
  rulesLayout: {
    height: '100%',
    display: 'grid',
    gridTemplateColumns: '1fr 560px',
    gap: 48,
    alignItems: 'center',
  },
  choicePanel: {
    ...panelBase,
    padding: 46,
  },
  panelTitle: {
    fontSize: 38,
    fontWeight: 950,
  },
  choiceRow: {
    marginTop: 36,
    display: 'grid',
    gridTemplateColumns: '1fr 96px 1fr',
    gap: 20,
    alignItems: 'center',
  },
  choiceCard: {
    height: 260,
    border: '5px solid',
    borderRadius: 24,
    background: 'rgba(255, 255, 255, 0.8)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
  },
  choiceEmoji: {
    fontSize: 90,
  },
  choiceAction: {
    marginTop: 14,
    fontSize: 44,
    fontWeight: 950,
  },
  choiceOr: {
    textAlign: 'center',
    fontSize: 34,
    fontWeight: 950,
    color: colors.muted,
  },
  panelText: {
    margin: '34px 0 0',
    color: colors.muted,
    fontSize: 32,
    fontWeight: 720,
    lineHeight: 1.22,
  },
  ruleTable: {
    ...panelBase,
    padding: 42,
  },
  payoffRows: {
    marginTop: 24,
  },
  payoffLine: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 26,
    padding: '21px 0',
    borderTop: `1px solid ${colors.cardLine}`,
    fontSize: 33,
    fontWeight: 740,
  },
  slowLayout: {
    height: '100%',
    display: 'grid',
    gridTemplateColumns: '1.35fr 0.65fr',
    gap: 42,
    alignItems: 'center',
  },
  roundCard: {
    ...panelBase,
    padding: 46,
  },
  roundLabel: {
    fontSize: 38,
    color: colors.green,
    fontWeight: 950,
  },
  duel: {
    marginTop: 42,
    display: 'grid',
    gridTemplateColumns: '1fr 150px 1fr',
    gap: 26,
    alignItems: 'center',
  },
  versus: {
    textAlign: 'center',
    fontSize: 28,
    color: colors.muted,
    fontWeight: 950,
  },
  monkeyBadge: {
    minHeight: 280,
    border: '5px solid',
    borderRadius: 28,
    background: 'rgba(255, 255, 255, 0.84)',
    padding: 24,
    textAlign: 'center',
  },
  badgeFace: {
    fontSize: 82,
  },
  badgeName: {
    marginTop: 8,
    fontSize: 34,
    fontWeight: 950,
  },
  badgeAction: {
    marginTop: 10,
    fontSize: 40,
    fontWeight: 950,
  },
  badgeScore: {
    marginTop: 10,
    fontSize: 28,
    color: colors.muted,
    fontWeight: 850,
  },
  payoffCallout: {
    marginTop: 34,
    padding: '24px 28px',
    borderRadius: 20,
    background: 'rgba(254, 243, 199, 0.8)',
    fontSize: 32,
    fontWeight: 850,
  },
  causePanel: {
    ...panelBase,
    padding: 40,
  },
  cleanList: {
    margin: '28px 0 0',
    paddingLeft: 32,
    color: colors.muted,
    fontSize: 31,
    lineHeight: 1.34,
    fontWeight: 760,
  },
  societyLayout: {
    height: '100%',
    display: 'grid',
    gridTemplateColumns: '1fr 520px',
    gap: 42,
    alignItems: 'center',
  },
  miniSociety: {
    height: '100%',
    position: 'relative',
  },
  metricsPanel: {
    ...panelBase,
    padding: 40,
  },
  bigMetric: {
    marginTop: 26,
    padding: '22px 26px',
    borderRadius: 20,
    background: 'rgba(255, 255, 255, 0.68)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 24,
    fontSize: 30,
    fontWeight: 850,
  },
  questionLayout: {
    ...panelBase,
    height: '100%',
    padding: 60,
    display: 'grid',
    gridTemplateColumns: '300px 1fr',
    alignItems: 'center',
    gap: 58,
  },
  questionMark: {
    width: 260,
    height: 260,
    borderRadius: '50%',
    background: '#fef3c7',
    color: colors.orange,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 170,
    fontWeight: 1000,
  },
  questionTitle: {
    margin: '20px 0 26px',
    fontSize: 72,
    lineHeight: 1,
  },
  questionText: {
    margin: '18px 0 0',
    fontSize: 40,
    lineHeight: 1.22,
    color: colors.muted,
    fontWeight: 760,
  },
  visionPanel: {
    ...panelBase,
    height: '100%',
    padding: 50,
  },
  visionTitle: {
    margin: '18px 0 58px',
    fontSize: 64,
    lineHeight: 0.98,
  },
  visionGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 24,
  },
  visionCard: {
    minHeight: 140,
    borderRadius: 22,
    background: 'rgba(255, 255, 255, 0.72)',
    border: `2px solid ${colors.cardLine}`,
    padding: 26,
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
    fontSize: 26,
    lineHeight: 1.2,
  },
  closePanel: {
    ...panelBase,
    height: '100%',
    padding: 60,
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeMonkey: {
    fontSize: 110,
  },
  closeTitle: {
    margin: '16px 0 0',
    fontSize: 92,
    lineHeight: 1,
  },
  closeText: {
    margin: '22px 0 0',
    fontSize: 40,
    color: colors.muted,
    fontWeight: 800,
  },
  closeTags: {
    marginTop: 36,
    display: 'flex',
    gap: 16,
  },
  caption: {
    position: 'absolute',
    left: 220,
    right: 220,
    bottom: 54,
    minHeight: 82,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '18px 34px',
    borderRadius: 24,
    background: 'rgba(45, 33, 24, 0.82)',
    color: '#fff7ed',
    fontSize: 36,
    lineHeight: 1.16,
    fontWeight: 850,
    textAlign: 'center',
  },
  progressRail: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: 10,
    background: 'rgba(255, 251, 235, 0.4)',
  },
  progressFill: {
    height: '100%',
    background: colors.green,
  },
  orbitWrap: {
    position: 'relative',
    height: 650,
  },
  orbitRing: {
    position: 'absolute',
    left: '50%',
    top: '50%',
    width: 620,
    height: 500,
    border: '10px solid',
    borderRadius: '50%',
    transform: 'translate(-50%, -50%)',
    opacity: 0.55,
    background: 'rgba(255, 251, 235, 0.24)',
  },
  orbitMonkey: {
    position: 'absolute',
    width: 150,
    height: 128,
    transform: 'translate(-50%, -50%)',
    border: '4px solid',
    borderRadius: 24,
    background: 'rgba(255, 255, 255, 0.86)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    fontSize: 24,
    boxShadow: '0 16px 34px rgba(87, 68, 36, 0.16)',
  },
  orbitCenter: {
    position: 'absolute',
    left: '50%',
    top: '50%',
    width: 260,
    height: 180,
    transform: 'translate(-50%, -50%)',
    borderRadius: 28,
    background: colors.cream,
    border: `2px solid ${colors.cardLine}`,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    fontSize: 30,
    textAlign: 'center',
    fontWeight: 950,
  },
};
