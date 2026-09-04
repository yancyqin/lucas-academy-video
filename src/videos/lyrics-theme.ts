import {Easing} from 'remotion';

export type LyricSection = 'verse' | 'prechorus' | 'chorus' | 'bridge' | 'outro';

export type Palette = {
  base: string;
  glow: string;
  glowAlt: string;
  ink: string;
  size: number;
  weight: number;
  tracking: string;
  /** Dust falls in the perishable sections and rises in the reborn ones. */
  drift: 1 | -1;
};

export const PALETTES: Record<LyricSection, Palette> = {
  verse: {
    base: '#080a0f', glow: 'rgba(78,104,148,.30)', glowAlt: 'rgba(40,58,84,.24)',
    ink: '#d6dbe4', size: 78, weight: 300, tracking: '.005em', drift: 1,
  },
  prechorus: {
    base: '#0b0a0d', glow: 'rgba(150,116,84,.32)', glowAlt: 'rgba(78,86,116,.26)',
    ink: '#e7ded2', size: 84, weight: 400, tracking: '.01em', drift: 1,
  },
  chorus: {
    base: '#120c07', glow: 'rgba(232,166,74,.42)', glowAlt: 'rgba(196,96,48,.30)',
    ink: '#fff4e2', size: 106, weight: 700, tracking: '-.02em', drift: -1,
  },
  bridge: {
    base: '#050507', glow: 'rgba(206,214,236,.34)', glowAlt: 'rgba(120,92,168,.24)',
    ink: '#ffffff', size: 94, weight: 600, tracking: '.03em', drift: -1,
  },
  outro: {
    base: '#0a0908', glow: 'rgba(214,170,116,.26)', glowAlt: 'rgba(70,74,96,.20)',
    ink: '#eadfd0', size: 74, weight: 300, tracking: '.02em', drift: -1,
  },
};

/** Deterministic hash -- Remotion renders frames out of order, so no Math.random. */
export const hash = (i: number, salt: number) => {
  const x = Math.sin(i * 127.1 + salt * 311.7) * 43758.5453;
  return x - Math.floor(x);
};

export const easeOut = (v: number) =>
  Easing.out(Easing.cubic)(Math.min(1, Math.max(0, v)));

export const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

export const lerp = (a: number, b: number, k: number) => a + (b - a) * clamp01(k);

/**
 * Every motif is driven by one keyframe track, so a cue in the song JSON fully
 * describes when the motif appears, how far it gets, and when it leaves.
 * Pairs rather than tuples: tuple types do not survive a JSON import.
 */
export type Track = number[][];

export const sampleTrack = (keys: Track, now: number): number => {
  if (!keys.length) return 0;
  if (now <= keys[0][0]) return keys[0][1];
  const last = keys[keys.length - 1];
  if (now >= last[0]) return last[1];
  for (let i = 1; i < keys.length; i += 1) {
    const [t1, v1] = keys[i];
    if (now <= t1) {
      const [t0, v0] = keys[i - 1];
      const k = t1 === t0 ? 1 : (now - t0) / (t1 - t0);
      return lerp(v0, v1, Easing.inOut(Easing.ease)(k));
    }
  }
  return last[1];
};
