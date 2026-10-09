/** [film seconds, source seconds, playback speed]. */
export type RampKey = [number, number, number];

/** Cubic Hermite source-time curve, shared by both Fun Informatics films. */
export const rampAt = (keys: RampKey[], t: number): number => {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    const [t0, s0, v0] = keys[i - 1];
    const [t1, s1, v1] = keys[i];
    if (t > t1) continue;
    const h = t1 - t0;
    const u = (t - t0) / h;
    return (
      (2 * u ** 3 - 3 * u ** 2 + 1) * s0 +
      (u ** 3 - 2 * u ** 2 + u) * h * v0 +
      (3 * u ** 2 - 2 * u ** 3) * s1 +
      (u ** 3 - u ** 2) * h * v1
    );
  }
  return keys[keys.length - 1][1];
};

/** Nonnegative, continuous speed, including zero-speed viewing holds. */
export const monotoneRamp = (points: [number, number][]): RampKey[] => {
  const ordered = points.filter((p, i) => i === 0 || p[0] > points[i - 1][0]);
  return ordered.map(([t, s], i) => {
    if (i === 0 || i === ordered.length - 1) return [t, s, 0];
    const a = (s - ordered[i - 1][1]) / (t - ordered[i - 1][0]);
    const b = (ordered[i + 1][1] - s) / (ordered[i + 1][0] - t);
    return [t, s, a <= 0 || b <= 0 ? 0 : Math.min(a, b)];
  });
};

export const filmTimeForSource = (keys: RampKey[], source: number): number => {
  let low = keys[0][0],
    high = keys[keys.length - 1][0];
  for (let n = 0; n < 48; n++) {
    const middle = (low + high) / 2;
    if (rampAt(keys, middle) < source) low = middle;
    else high = middle;
  }
  return (low + high) / 2;
};
