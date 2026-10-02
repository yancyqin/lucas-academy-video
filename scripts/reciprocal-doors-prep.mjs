// Builds the timelines for the Language Bridge (语言的桥) films from the narration files.
//
// Two films, one per language (owner, 2026-10-01): the Chinese video and the
// English video each get their own timeline, so a line lasts as long as that
// language needs. Scene beats key off line starts, so the same scenes play in
// both; the directed pauses are identical. Captions for each film are written in
// both languages on that film's own time codes.
//
//   node scripts/reciprocal-doors-prep.mjs
//
// Narration comes from ../lucas-academy-media (tightened copies). Missing files
// are estimated so a film can be laid out before synthesis finishes.
import {execFileSync} from 'node:child_process';
import {existsSync, mkdirSync, readdirSync, writeFileSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

import script from '../src/scripts/reciprocal-doors.json' with {type: 'json'};

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const media = resolve(root, '../lucas-academy-media/outputs');
// Tightened copies (scripts/reciprocal-doors-tighten.py): clean edges, pauses
// inside a line capped, identical treatment for both languages.
const narrationDir = {
  zh: resolve(media, 'fangfang/zh/reciprocal-doors-tight'),
  en: resolve(media, 'louise/en/reciprocal-doors-tight'),
};
const audioOut = resolve(root, 'public/audio/reciprocal-doors');
const imageDir = resolve(root, 'public/images/reciprocal-doors');
const deliverables = resolve(root, 'out/reciprocal-doors');

const TITLE = 4.0; // silent title card
const SCENE_LEAD = 0.7; // picture settles before the first line
const SCENE_TAIL = 0.9; // breath after the last line of a scene
const CHUNK_GAP = 0.45;
const PART_GAP = 0.3;
const DEMO_GAP = 0.55; // a taught phrase gets room on both sides
// Playback tempo per film. Viewers found the Chinese film right at 1.5x; the
// owner chose 1.3x (2026-10-02). The narration is time-stretched (ffmpeg atempo,
// pitch kept -- the same kind of stretch a player's speed setting uses, so the
// verified takes stay as they were) and the film's pauses shrink with it. The
// taught phrases (demo parts) keep their slow reading.
const TEMPO = {zh: 1.3, en: 1.0};
// Lines whose stretched take reads wrong get a take voiced at the fast pace instead
// (scripts/reciprocal-doors-fast.py, already tightened); those play as they are.
const fastDir = {zh: resolve(media, 'fangfang/zh/reciprocal-doors-fast')};
const END_CARD = 4.5;
const TRACKS = ['zh', 'en'];

const duration = (file) =>
  Number(
    execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file])
      .toString()
      .trim(),
  );

// CosyVoice pads each line with ~0.5 s of leading/trailing silence; the timeline
// sets the pauses itself, so strip the padding (pauses inside a line stay).
const EDGE = 'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06';
const trimSilence = (source, target, tempo = 1) =>
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', source, '-af', `${EDGE},areverse,${EDGE},areverse${tempo === 1 ? '' : `,atempo=${tempo}`}`, target]);

const estimate = (part) =>
  part.lang === 'zh'
    ? [...part.text.replace(/[，。：；？“”、]/g, '')].length * 0.27
    : part.text.split(/\s+/).length * 0.38;

// <strong> marks emphasis for the voice only; subtitles show plain text.
const plain = (text) => text.replace(/<\/?strong>/g, '');
const round = (n) => Math.round(n * 1000) / 1000;
const missing = [];

for (const track of TRACKS) mkdirSync(resolve(audioOut, track), {recursive: true});
mkdirSync(deliverables, {recursive: true});

// Measure every narration part once, both languages.
const measured = script.segments.map((segment) =>
  segment.chunks.map((chunk) => {
    const tracks = {};
    for (const track of TRACKS) {
      const parts = chunk.parts?.[track] ?? [{text: chunk[track], lang: track}];
      let offset = 0;
      tracks[track] = parts.map((part, index) => {
        const id = parts.length === 1 ? chunk.id : `${chunk.id}-p${index + 1}`;
        const fast = !part.demo && fastDir[track] && resolve(fastDir[track], `${id}.wav`);
        const useFast = Boolean(fast && existsSync(fast));
        const source = useFast ? fast : resolve(narrationDir[track], `${id}.wav`);
        let seconds;
        let file = null;
        if (existsSync(source)) {
          file = `audio/reciprocal-doors/${track}/${id}.wav`;
          trimSilence(source, resolve(root, 'public', file), part.demo || useFast ? 1 : TEMPO[track]);
          seconds = duration(resolve(root, 'public', file));
        } else {
          seconds = estimate(part);
          missing.push(`${track}/${id}`);
        }
        if (index > 0) offset += (part.demo || parts[index - 1].demo ? DEMO_GAP : PART_GAP) / TEMPO[track];
        const placed = {id, file, lang: part.lang, demo: Boolean(part.demo), offset: round(offset), seconds: round(seconds)};
        offset += seconds;
        return placed;
      });
    }
    const spoken = Object.fromEntries(TRACKS.map((track) => [track, round(tracks[track].at(-1).offset + tracks[track].at(-1).seconds)]));
    return {tracks, spoken};
  }),
);

const images = existsSync(imageDir) ? readdirSync(imageDir).filter((name) => /\.(png|jpe?g|webp)$/i.test(name)) : [];
const stamp = (seconds) => {
  const ms = Math.round(seconds * 1000);
  const pad = (n, w = 2) => String(n).padStart(w, '0');
  return `${pad(Math.floor(ms / 3600000))}:${pad(Math.floor(ms / 60000) % 60)}:${pad(Math.floor(ms / 1000) % 60)},${pad(ms % 1000, 3)}`;
};

// Two films (owner, 2026-10-01): a Chinese video and an English video, each on
// its own timeline -- a line lasts as long as that language needs, the directed
// pauses are the same in both.
for (const film of TRACKS) {
  let t = TITLE;
  const segments = script.segments.map((segment, s) => {
    const start = t;
    const chunks = segment.chunks.map((chunk, position) => {
      t += (chunk.pause ?? (position === 0 ? SCENE_LEAD : CHUNK_GAP)) / TEMPO[film];
      const {tracks, spoken} = measured[s][position];
      const placed = {id: chunk.id, zh: plain(chunk.zh), en: plain(chunk.en), start: round(t), slot: spoken[film], spoken, tracks: {[film]: tracks[film]}};
      t += spoken[film];
      return placed;
    });
    t += SCENE_TAIL / TEMPO[film];
    return {id: segment.id, start: round(start), end: round(t), chunks};
  });
  const total = round(t + END_CARD);
  const filmMissing = missing.filter((part) => part.startsWith(`${film}/`));
  writeFileSync(
    resolve(root, `src/scripts/reciprocal-doors.timeline.${film}.json`),
    `${JSON.stringify({fps: 30, lang: film, title: script.title, titleSeconds: TITLE, endCardSeconds: END_CARD, durationSeconds: total, images, missing: filmMissing, segments}, null, 2)}\n`,
  );

  // Captions for this film, in both languages, on its own time codes (UTF-8 SRT).
  const out = resolve(deliverables, film);
  mkdirSync(out, {recursive: true});
  const allChunks = segments.flatMap((segment) => segment.chunks);
  for (const [lang, name] of [['zh', 'zh-Hans'], ['en', 'en']]) {
    const cues = allChunks.map((chunk, index) => {
      // Linger a little after the line, but never into the next cue.
      const next = allChunks[index + 1]?.start ?? Infinity;
      const to = Math.min(chunk.start + chunk.slot + 0.35, next - 0.05);
      return `${index + 1}\n${stamp(chunk.start)} --> ${stamp(to)}\n${chunk[lang]}\n`;
    });
    writeFileSync(resolve(out, `language-bridge.${film}.${name}.srt`), cues.join('\n'));
  }
  console.log(`${film} film: ${total.toFixed(1)} s (${(total / 60).toFixed(2)} min)${filmMissing.length ? `, ${filmMissing.length} parts estimated (narration not ready)` : ''}`);
}
