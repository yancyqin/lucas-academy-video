import {
  filmTimeForSource,
  monotoneRamp,
  rampAt,
  type RampKey,
} from "../../lib/timeRamps";

type Cue = {
  id: string;
  start: number;
  end: number;
  speech: { start: number; end: number };
};
type Event = {
  time: number;
  shownAt?: number;
  action: string;
  word?: string;
  value: string;
  stepIndex: number;
};
type Timeline = {
  fps: number;
  cues: Cue[];
  markers?: Record<string, Record<string, number>>;
  footageSeconds: Record<string, number>;
  recordings: Record<string, { events: Event[] }>;
};
export type PlaybackPlan = {
  start: number;
  end: number;
  keys: RampKey[];
  teaching?: [number, number];
};
export type GameFeedback = { time: number; file: string; kind: string };

/** One plan feeds the picture and the restored original game feedback sounds. */
export const buildPlayback = (tl: Timeline) => {
  const cue = (id: string) => tl.cues.find((c) => c.id === id)!;
  const marker = (id: string, phrase: string) =>
    tl.markers?.[id]?.[phrase] ?? cue(id).start;
  const plans: Record<string, PlaybackPlan> = {};
  for (const unfamiliar of [false, true]) {
    const start = cue(unfamiliar ? "cl03-08" : "cl03-03").start;
    const end = cue(unfamiliar ? "cl03-08" : "cl03-07").end;
    const length = end - start;
    const t4 = Math.max(0, marker("cl03-04", "英文这里") - start);
    const t5 = cue("cl03-05").start - start;
    const t6 = cue("cl03-06").start - start;
    const names = unfamiliar
      ? ["letters-pro2511-en", "letters-pro2511-zh"]
      : ["letters-jhn316-en", "letters-jhn316-zh"];
    for (const [i, name] of names.entries()) {
      const events = tl.recordings[name]?.events ?? [];
      const before = events.find(
        (e) =>
          e.action === "correct" &&
          (i === 0 ? e.word === "world" && e.value === "l" : e.value === "人"),
      );
      const after = events.find(
        (e) =>
          e.action === "correct" &&
          (i === 0 ? e.word === "world" && e.value === "d" : e.value === "人"),
      );
      const sourceBefore = Math.max(0, before?.shownAt ?? 0);
      const sourceAfter = after ? after.time + 0.3 : sourceBefore;
      const sourceEnd = Math.max(
        0,
        (tl.footageSeconds[name + ".mp4"] ?? 1) - 0.15,
      );
      const points: [number, number][] = unfamiliar
        ? [
            [0, 0],
            [length * 0.2, 0],
            [length * 0.83, sourceEnd],
            [length, sourceEnd],
          ]
        : i === 0
          ? [
              [0, 0],
              [t4, sourceBefore],
              [t5, sourceAfter],
              [t6, sourceAfter],
              [length * 0.88, sourceEnd],
              [length, sourceEnd],
            ]
          : [
              [0, 0],
              [t4, sourceBefore],
              [t5, sourceBefore],
              [t6, sourceAfter],
              [length * 0.88, sourceEnd],
              [length, sourceEnd],
            ];
      plans[name] = {
        start,
        end,
        keys: monotoneRamp(points),
        ...(unfamiliar ? {} : { teaching: [t4, t6] as [number, number] }),
      };
    }
  }
  const name = "words-psa231-zh";
  const events = tl.recordings[name]?.events ?? [];
  // Skip the two superscription units, then follow FOUR actual word choices.
  const first = events.find((e) => e.action === "correct" && e.stepIndex === 2);
  const last = events.find((e) => e.action === "correct" && e.stepIndex === 5);
  const start = cue("cl04-04").start,
    end = cue("cl04-05").end;
  const sourceStart = first?.shownAt ?? 0,
    sourceEnd = Math.min(
      (tl.footageSeconds[name + ".mp4"] ?? 18) - 0.1,
      (last?.time ?? 13.9) + 0.25,
    );
  plans[name] = {
    start,
    end,
    keys: monotoneRamp([
      [0, sourceStart],
      [cue("cl04-05").speech.end - start, sourceStart],
      [end - start - 1, sourceEnd],
      [end - start, sourceEnd],
    ]),
  };

  const feedback: GameFeedback[] = [];
  for (const [name, plan] of Object.entries(plans)) {
    const lo = plan.keys[0][1],
      hi = plan.keys.at(-1)![1];
    let streak = 0,
      lastTime = -10;
    for (const event of tl.recordings[name]?.events ?? []) {
      if (event.action === "wrong") streak = 0;
      else if (event.action === "correct") streak++;
      else continue;
      if (event.time <= lo || event.time > hi) continue;
      const local = filmTimeForSource(plan.keys, event.time);
      if (
        plan.teaching &&
        local >= plan.teaching[0] &&
        local < plan.teaching[1]
      )
        continue;
      // Fast-forward remains continuous, but rapid feedback is kept unobtrusive.
      if (local - lastTime < 0.6) continue;
      const n = Math.max(1, Math.min(streak, 6));
      feedback.push({
        time: Math.round((plan.start + local) * 1000) / 1000,
        file:
          event.action === "wrong"
            ? "damage.wav"
            : n === 1
              ? "correct.wav"
              : `correct-${n}.wav`,
        kind: event.action,
      });
      lastTime = local;
    }
  }
  // Check the actual source time at EVERY delivery frame, not just the keys.
  for (const [name, plan] of Object.entries(plans)) {
    let previous = -Infinity;
    for (
      let frame = 0;
      frame <= Math.ceil((plan.end - plan.start) * tl.fps);
      frame++
    ) {
      const source = rampAt(plan.keys, frame / tl.fps);
      if (source + 1e-6 < previous)
        throw Error(`${name}: source moves backwards at frame ${frame}`);
      previous = source;
    }
    if (previous > (tl.footageSeconds[name + ".mp4"] ?? 0) + 1e-3)
      throw Error(`${name}: source exceeds recording`);
  }
  return {
    playback: plans,
    gameFeedback: feedback.sort((a, b) => a.time - b.time),
  };
};
