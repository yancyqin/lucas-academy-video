import {mkdir, writeFile} from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

import {Society} from '../../snake-lab/v3-coder/games/monkey-republic/society.js';
import {WORLD_PRESETS} from '../../snake-lab/v3-coder/public/games/monkey-republic/constants.js';
import {
  PERSONALITIES,
  STUDENT_STARTER,
} from '../../snake-lab/v3-coder/public/games/monkey-republic/personalities.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const outputPath = resolve(__dirname, '../src/data/monkey-society.json');

const VISUAL_SEED = 20260705;
const VISUAL_ROUNDS = 100;
const MEDIAN_SEEDS = Array.from({length: 20}, (_, index) => 1000 + index * 7919);

const studentColors = [
  '#22c55e',
  '#14b8a6',
  '#0ea5e9',
  '#8b5cf6',
  '#ec4899',
  '#f97316',
  '#84cc16',
  '#64748b',
];

function makeStudents(count) {
  return Array.from({length: count}, (_, index) => ({
    id: `student-${index + 1}`,
    name: index === 0 ? STUDENT_STARTER.label : `Class Monkey ${index + 1}`,
    color: studentColors[index % studentColors.length],
    dials: {...STUDENT_STARTER.dials},
  }));
}

function runSociety({worldKey, rounds, studentCount, seed}) {
  const society = new Society({
    students: makeStudents(studentCount),
    world: WORLD_PRESETS[worldKey],
    seed,
    roundsTarget: rounds,
    spawnBots: true,
  });
  society.runBatch(rounds);
  const report = society.report();
  return {
    ...report,
    citizenCount: society.citizens.length,
    groups: society.groups().map((group) => ({
      key: group.key,
      label: group.label,
      color: group.color,
      count: group.count,
      total: round1(group.total),
      average: round1(group.average),
      shareRate: round2(group.shareRate),
    })),
  };
}

function summarizeWorld(worldKey, rounds, studentCount) {
  const reports = MEDIAN_SEEDS.map((seed) =>
    runSociety({worldKey, rounds, studentCount, seed})
  );
  const winnerCounts = {};
  for (const report of reports) {
    const key = report.leader?.personality ?? 'none';
    winnerCounts[key] = (winnerCounts[key] ?? 0) + 1;
  }
  return {
    worldKey,
    rounds,
    studentCount,
    citizenCount: reports[0]?.citizenCount ?? 0,
    medianFinalShareRate: median(reports.map((report) => report.shareRate)),
    medianBananasPerCitizen: round1(
      median(reports.map((report) => report.totalBananas / report.citizenCount))
    ),
    medianBetrayals: Math.round(median(reports.map((report) => report.betrayals))),
    medianRepairs: Math.round(median(reports.map((report) => report.repairs))),
    winnerCounts,
  };
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2
    ? sorted[middle]
    : (sorted[middle - 1] + sorted[middle]) / 2;
}

function round1(value) {
  return Math.round(value * 10) / 10;
}

function round2(value) {
  return Math.round(value * 100) / 100;
}

const cast = [
  {
    key: 'student',
    label: STUDENT_STARTER.label,
    emoji: STUDENT_STARTER.emoji,
    color: '#22c55e',
    human: STUDENT_STARTER.human,
  },
  ...PERSONALITIES.map((personality) => ({
    key: personality.key,
    label: personality.label,
    emoji: personality.emoji,
    color: personality.color,
    human: personality.human,
  })),
];

const data = {
  generatedAt: new Date().toISOString(),
  engine: 'snake-lab/v3-coder/games/monkey-republic/society.js',
  visualRounds: VISUAL_ROUNDS,
  cast,
  worlds: {
    winWin: WORLD_PRESETS.winWin,
    darkForest: WORLD_PRESETS.darkForest,
  },
  visualRuns: {
    winWin: runSociety({
      worldKey: 'winWin',
      rounds: VISUAL_ROUNDS,
      studentCount: 1,
      seed: VISUAL_SEED,
    }),
    darkForest: runSociety({
      worldKey: 'darkForest',
      rounds: VISUAL_ROUNDS,
      studentCount: 1,
      seed: VISUAL_SEED,
    }),
  },
  classMedians: {
    winWin100: summarizeWorld('winWin', 100, 8),
    darkForest100: summarizeWorld('darkForest', 100, 8),
  },
};

await mkdir(dirname(outputPath), {recursive: true});
await writeFile(outputPath, `${JSON.stringify(data, null, 2)}\n`);
console.log(`Wrote ${outputPath}`);
