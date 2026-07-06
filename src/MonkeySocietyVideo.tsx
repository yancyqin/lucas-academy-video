import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import data from './data/monkey-society.json';

type WorldKey = 'winWin' | 'darkForest';

type CastMember = {
  key: string;
  label: string;
  emoji: string;
  color: string;
  human: string;
};

type TimelinePoint = {
  round: number;
  shareRate: number;
  totalBananas: number;
  topScore: number;
  betrayals: number;
  repairs: number;
  types: Record<string, {average: number; shareRate: number}>;
};

const cast = data.cast as CastMember[];
const worldCopy: Record<WorldKey, {kicker: string; lesson: string; accent: string}> = {
  winWin: {
    kicker: 'World A: Win-Win Jungle',
    lesson: 'Sharing creates extra bananas, so trust has room to grow.',
    accent: '#16a34a',
  },
  darkForest: {
    kicker: 'World B: Dark Forest',
    lesson: 'Sharing still helps a little, but betrayal hurts enough to reshape belief.',
    accent: '#7c3aed',
  },
};

export const MonkeySocietyVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames, fps} = useVideoConfig();
  const midpoint = Math.floor(durationInFrames / 2);
  const worldKey: WorldKey = frame < midpoint ? 'winWin' : 'darkForest';
  const phaseFrame = worldKey === 'winWin' ? frame : frame - midpoint;
  const phaseDuration = worldKey === 'winWin' ? midpoint : durationInFrames - midpoint;
  const progress = clamp(phaseFrame / Math.max(1, phaseDuration - 1), 0, 1);
  const run = data.visualRuns[worldKey];
  const timeline = run.timeline as TimelinePoint[];
  const point = timeline[Math.min(timeline.length - 1, Math.floor(progress * timeline.length))];
  const previousPoint = timeline[Math.max(0, Math.floor(progress * timeline.length) - 1)];
  const phaseIntro = spring({
    frame: phaseFrame,
    fps,
    config: {damping: 18, stiffness: 70},
  });
  const copy = worldCopy[worldKey];
  const payoff = data.worlds[worldKey].payoff as unknown as Record<string, [number, number]>;
  const classMedian = worldKey === 'winWin' ? data.classMedians.winWin100 : data.classMedians.darkForest100;

  return (
    <AbsoluteFill style={styles.screen}>
      <JungleBackdrop worldKey={worldKey} />
      <div style={styles.topBar}>
        <div>
          <div style={styles.brand}>Lucas Academy Video Lab</div>
          <div style={styles.title}>Monkey Republic: Society Simulation</div>
        </div>
        <div style={{...styles.worldPill, borderColor: copy.accent, color: copy.accent}}>
          Round {point.round}/100
        </div>
      </div>

      <section style={styles.stage}>
        <aside style={styles.leftPanel}>
          <div style={{...styles.kicker, color: copy.accent}}>{copy.kicker}</div>
          <h1 style={styles.headline}>Same monkeys. Different rules.</h1>
          <p style={styles.lesson}>{copy.lesson}</p>
          <PayoffTable payoff={payoff} accent={copy.accent} />
        </aside>

        <main style={styles.societyWrap}>
          <div
            style={{
              ...styles.societyAura,
              borderColor: copy.accent,
              opacity: interpolate(phaseIntro, [0, 1], [0.2, 0.8]),
              transform: `translate(-50%, -50%) scale(${interpolate(phaseIntro, [0, 1], [0.92, 1])})`,
            }}
          />
          <SocietyRing
            frame={frame}
            point={point}
            previousPoint={previousPoint}
            accent={copy.accent}
          />
          <div style={styles.centerBadge}>
            <div style={styles.centerEmoji}>🐵</div>
            <div style={styles.centerTitle}>9 monkeys</div>
            <div style={styles.centerSub}>1 Rookie + 8 bots</div>
          </div>
        </main>

        <aside style={styles.rightPanel}>
          <Metric label="Share rate now" value={`${Math.round(point.shareRate * 100)}%`} accent={copy.accent} />
          <Metric
            label="Bananas / monkey"
            value={String(Math.round(point.totalBananas / run.citizenCount))}
            accent="#d97706"
          />
          <Metric label="Betrayals" value={String(point.betrayals)} accent="#dc2626" />
          <ShareVine timeline={timeline} point={point} accent={copy.accent} />
          <Ranking point={point} />
        </aside>
      </section>

      <footer style={styles.footer}>
        <div>
          <strong>Class-size check:</strong> 8 student monkeys + 64 bots, 100 rounds, 20 seeds.
        </div>
        <div>
          Median result here: {Math.round(classMedian.medianFinalShareRate * 100)}% final sharing,
          {' '}
          {classMedian.medianBananasPerCitizen} bananas per citizen.
        </div>
      </footer>
    </AbsoluteFill>
  );
};

const SocietyRing: React.FC<{
  frame: number;
  point: TimelinePoint;
  previousPoint: TimelinePoint;
  accent: string;
}> = ({frame, point, previousPoint, accent}) => {
  const radius = 286;
  return (
    <>
      {cast.map((member, index) => {
        const angle = -Math.PI / 2 + (index / cast.length) * Math.PI * 2;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        const stats = point.types[member.key] ?? {average: 0, shareRate: 0.5};
        const previous = previousPoint.types[member.key] ?? stats;
        const scoreDelta = stats.average - previous.average;
        const pulse = 1 + Math.sin(frame / 8 + index) * 0.025;
        const mood = scoreDelta < -0.5 || stats.average <= 0 ? '☹' : stats.shareRate > 0.72 ? '☺' : '•';
        return (
          <div
            key={member.key}
            style={{
              ...styles.monkeyNode,
              left: `calc(50% + ${x}px)`,
              top: `calc(50% + ${y}px)`,
              borderColor: member.key === 'student' ? accent : member.color,
              boxShadow: `0 18px 34px rgba(37, 28, 11, 0.16), 0 0 0 ${Math.max(
                4,
                Math.round(stats.shareRate * 18)
              )}px ${withAlpha(member.color, 0.14)}`,
              transform: `translate(-50%, -50%) scale(${pulse})`,
            }}
          >
            <div style={styles.nodeFace}>
              <span style={styles.monkeyEmoji}>🐵</span>
              <span style={styles.personalityEmoji}>{member.emoji}</span>
              <span style={styles.moodMark}>{mood}</span>
            </div>
            <div style={styles.nodeName}>{member.label}</div>
            <div style={styles.nodeScore}>{Math.round(stats.average)} bananas</div>
            <div style={styles.shareTrack}>
              <div
                style={{
                  ...styles.shareFill,
                  width: `${Math.round(stats.shareRate * 100)}%`,
                  background: member.key === 'student' ? accent : member.color,
                }}
              />
            </div>
          </div>
        );
      })}
    </>
  );
};

const PayoffTable: React.FC<{
  payoff: Record<string, [number, number]>;
  accent: string;
}> = ({payoff, accent}) => {
  const rows = [
    ['Share + Share', payoff.shareShare],
    ['Grab vs Share', payoff.grabShare],
    ['Share vs Grab', payoff.shareGrab],
    ['Grab + Grab', payoff.grabGrab],
  ] as const;
  return (
    <div style={styles.payoffBox}>
      <div style={styles.payoffTitle}>Banana rules</div>
      {rows.map(([label, values]) => (
        <div key={label} style={styles.payoffRow}>
          <span>{label}</span>
          <strong style={{color: accent}}>
            {formatSigned(values[0])} / {formatSigned(values[1])}
          </strong>
        </div>
      ))}
    </div>
  );
};

const Metric: React.FC<{label: string; value: string; accent: string}> = ({label, value, accent}) => (
  <div style={styles.metric}>
    <div style={styles.metricLabel}>{label}</div>
    <div style={{...styles.metricValue, color: accent}}>{value}</div>
  </div>
);

const ShareVine: React.FC<{
  timeline: TimelinePoint[];
  point: TimelinePoint;
  accent: string;
}> = ({timeline, point, accent}) => {
  const index = Math.max(0, timeline.findIndex((entry) => entry.round === point.round));
  const width = 430;
  const height = 132;
  const path = buildLinePath(timeline.slice(0, index + 1), width, height, (entry) => entry.shareRate);
  return (
    <div style={styles.chartBox}>
      <div style={styles.chartTitle}>Trust vine</div>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        <path
          d={`M0 ${height - 16} C110 ${height - 28} 230 ${height - 4} ${width} ${height - 18}`}
          fill="none"
          stroke="rgba(87, 68, 36, 0.16)"
          strokeWidth="14"
          strokeLinecap="round"
        />
        <path
          d={path}
          fill="none"
          stroke={accent}
          strokeWidth="10"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
};

const Ranking: React.FC<{point: TimelinePoint}> = ({point}) => {
  const rows = cast
    .map((member) => ({
      ...member,
      stats: point.types[member.key] ?? {average: 0, shareRate: 0.5},
    }))
    .sort((a, b) => b.stats.average - a.stats.average)
    .slice(0, 3);
  return (
    <div style={styles.ranking}>
      <div style={styles.rankingTitle}>Ranking now</div>
      {rows.map((row, index) => (
        <div key={row.key} style={styles.rankRow}>
          <span style={styles.rankIndex}>{index + 1}</span>
          <span style={{...styles.rankDot, background: row.color}} />
          <span style={styles.rankName}>{row.label}</span>
          <strong>{Math.round(row.stats.average)}</strong>
        </div>
      ))}
    </div>
  );
};

const JungleBackdrop: React.FC<{worldKey: WorldKey}> = ({worldKey}) => {
  const isDark = worldKey === 'darkForest';
  return (
    <AbsoluteFill
      style={{
        ...styles.backdrop,
        background: isDark
          ? 'linear-gradient(180deg, #c4b5fd 0%, #dbeafe 38%, #dcfce7 100%)'
          : 'linear-gradient(180deg, #bae6fd 0%, #fef3c7 44%, #dcfce7 100%)',
      }}
    >
      <div style={styles.sun}>{isDark ? '◐' : '☀'}</div>
      <div style={{...styles.canopy, background: isDark ? '#4c1d95' : '#15803d'}} />
      <div style={{...styles.ground, background: isDark ? '#4d7c0f' : '#65a30d'}} />
      <div style={styles.bananaSpray}>🍌 🍃 🍌 🍃 🍌 🍃 🍌</div>
    </AbsoluteFill>
  );
};

function buildLinePath(
  entries: TimelinePoint[],
  width: number,
  height: number,
  getValue: (entry: TimelinePoint) => number
) {
  if (entries.length === 0) return `M0 ${height}`;
  return entries
    .map((entry, index) => {
      const x = entries.length === 1 ? 0 : (index / (entries.length - 1)) * width;
      const y = height - 16 - clamp(getValue(entry), 0, 1) * (height - 34);
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');
}

function formatSigned(value: number) {
  return value > 0 ? `+${value}` : String(value);
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function withAlpha(hex: string, alpha: number) {
  const normalized = hex.replace('#', '');
  const bigint = parseInt(normalized, 16);
  const red = (bigint >> 16) & 255;
  const green = (bigint >> 8) & 255;
  const blue = bigint & 255;
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

const panelBase: React.CSSProperties = {
  background: 'rgba(255, 251, 235, 0.86)',
  border: '2px solid rgba(120, 83, 31, 0.18)',
  borderRadius: 26,
  boxShadow: '0 24px 60px rgba(87, 68, 36, 0.12)',
};

const styles: Record<string, React.CSSProperties> = {
  screen: {
    color: '#2d2118',
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    overflow: 'hidden',
  },
  backdrop: {
    overflow: 'hidden',
  },
  sun: {
    position: 'absolute',
    top: 46,
    right: 86,
    fontSize: 96,
    color: '#f59e0b',
  },
  canopy: {
    position: 'absolute',
    left: -80,
    right: -80,
    top: -120,
    height: 240,
    borderBottomLeftRadius: '50%',
    borderBottomRightRadius: '50%',
    opacity: 0.8,
  },
  ground: {
    position: 'absolute',
    left: -120,
    right: -120,
    bottom: -90,
    height: 250,
    borderTopLeftRadius: '50%',
    borderTopRightRadius: '50%',
  },
  bananaSpray: {
    position: 'absolute',
    left: 580,
    right: 450,
    top: 120,
    fontSize: 38,
    letterSpacing: 8,
    opacity: 0.4,
  },
  topBar: {
    position: 'absolute',
    top: 44,
    left: 70,
    right: 70,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  brand: {
    fontSize: 28,
    fontWeight: 800,
    color: '#7c2d12',
    textTransform: 'uppercase',
  },
  title: {
    marginTop: 8,
    fontSize: 54,
    lineHeight: 1,
    fontWeight: 950,
  },
  worldPill: {
    ...panelBase,
    borderRadius: 999,
    padding: '18px 30px',
    fontSize: 34,
    fontWeight: 900,
  },
  stage: {
    position: 'absolute',
    left: 70,
    right: 70,
    top: 164,
    bottom: 118,
    display: 'grid',
    gridTemplateColumns: '430px 1fr 470px',
    gap: 32,
    alignItems: 'stretch',
  },
  leftPanel: {
    ...panelBase,
    padding: 34,
  },
  kicker: {
    fontSize: 30,
    fontWeight: 900,
  },
  headline: {
    margin: '20px 0 20px',
    fontSize: 58,
    lineHeight: 0.98,
    letterSpacing: 0,
  },
  lesson: {
    margin: 0,
    color: '#5f4b32',
    fontSize: 27,
    lineHeight: 1.25,
    fontWeight: 650,
  },
  payoffBox: {
    marginTop: 26,
    padding: 20,
    borderRadius: 20,
    background: 'rgba(255, 255, 255, 0.58)',
    border: '1px solid rgba(120, 83, 31, 0.18)',
  },
  payoffTitle: {
    fontSize: 25,
    fontWeight: 900,
    marginBottom: 12,
  },
  payoffRow: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: 18,
    fontSize: 23,
    padding: '8px 0',
    borderTop: '1px solid rgba(120, 83, 31, 0.12)',
  },
  societyWrap: {
    position: 'relative',
    minWidth: 0,
  },
  societyAura: {
    position: 'absolute',
    left: '50%',
    top: '50%',
    width: 620,
    height: 620,
    border: '10px solid',
    borderRadius: '50%',
    background:
      'radial-gradient(circle, rgba(255, 255, 255, 0.76) 0%, rgba(254, 243, 199, 0.5) 55%, rgba(22, 163, 74, 0.08) 100%)',
    transform: 'translate(-50%, -50%)',
  },
  centerBadge: {
    ...panelBase,
    position: 'absolute',
    left: '50%',
    top: '50%',
    width: 290,
    height: 230,
    transform: 'translate(-50%, -50%)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
  },
  centerEmoji: {
    fontSize: 70,
    lineHeight: 1,
  },
  centerTitle: {
    marginTop: 10,
    fontSize: 32,
    fontWeight: 950,
  },
  centerSub: {
    marginTop: 5,
    fontSize: 24,
    color: '#6b5b47',
    fontWeight: 750,
  },
  monkeyNode: {
    position: 'absolute',
    width: 162,
    height: 172,
    background: 'rgba(255, 255, 255, 0.9)',
    border: '4px solid',
    borderRadius: 24,
    padding: 12,
    textAlign: 'center',
  },
  nodeFace: {
    position: 'relative',
    width: 70,
    height: 58,
    margin: '0 auto',
  },
  monkeyEmoji: {
    fontSize: 54,
    lineHeight: 1,
  },
  personalityEmoji: {
    position: 'absolute',
    right: -8,
    top: -2,
    fontSize: 28,
    background: '#fff7ed',
    borderRadius: 999,
    padding: 2,
  },
  moodMark: {
    position: 'absolute',
    left: -6,
    bottom: -6,
    width: 28,
    height: 28,
    borderRadius: 999,
    background: '#fef3c7',
    fontSize: 24,
    lineHeight: '28px',
    fontWeight: 900,
    color: '#7c2d12',
  },
  nodeName: {
    marginTop: 8,
    minHeight: 38,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 18,
    lineHeight: 1.05,
    fontWeight: 950,
    whiteSpace: 'normal',
    overflow: 'hidden',
  },
  nodeScore: {
    marginTop: 2,
    fontSize: 17,
    color: '#6b5b47',
    fontWeight: 800,
  },
  shareTrack: {
    marginTop: 10,
    height: 10,
    borderRadius: 999,
    background: 'rgba(87, 68, 36, 0.12)',
    overflow: 'hidden',
  },
  shareFill: {
    height: '100%',
    borderRadius: 999,
  },
  rightPanel: {
    display: 'grid',
    gap: 18,
    gridTemplateRows: '120px 120px 120px 196px 1fr',
  },
  metric: {
    ...panelBase,
    padding: '20px 26px',
  },
  metricLabel: {
    fontSize: 24,
    color: '#6b5b47',
    fontWeight: 800,
  },
  metricValue: {
    marginTop: 6,
    fontSize: 56,
    lineHeight: 1,
    fontWeight: 950,
  },
  chartBox: {
    ...panelBase,
    padding: '18px 20px 12px',
  },
  chartTitle: {
    fontSize: 26,
    fontWeight: 950,
    marginBottom: 2,
  },
  ranking: {
    ...panelBase,
    padding: 22,
  },
  rankingTitle: {
    fontSize: 26,
    fontWeight: 950,
    marginBottom: 12,
  },
  rankRow: {
    display: 'grid',
    gridTemplateColumns: '34px 18px 1fr 62px',
    gap: 12,
    alignItems: 'center',
    padding: '7px 0',
    fontSize: 21,
    borderTop: '1px solid rgba(120, 83, 31, 0.12)',
  },
  rankIndex: {
    color: '#7c2d12',
    fontWeight: 950,
  },
  rankDot: {
    width: 16,
    height: 16,
    borderRadius: 999,
  },
  rankName: {
    fontWeight: 850,
    overflow: 'hidden',
    whiteSpace: 'nowrap',
    textOverflow: 'ellipsis',
  },
  footer: {
    ...panelBase,
    position: 'absolute',
    left: 70,
    right: 70,
    bottom: 36,
    minHeight: 58,
    borderRadius: 18,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 36,
    padding: '18px 28px',
    color: '#5f4b32',
    fontSize: 25,
    fontWeight: 750,
  },
};
