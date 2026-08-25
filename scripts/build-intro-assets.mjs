import {mkdir, writeFile} from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

import script from '../src/scripts/intro.en.json' with {type: 'json'};

const __dirname = dirname(fileURLToPath(import.meta.url));
const captionPath = resolve(__dirname, '../public/captions/intro.en.srt');
const narrationPath = resolve(__dirname, '../public/narration/intro.en.txt');

function timestamp(seconds) {
  const ms = Math.round(seconds * 1000);
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  const n = ms % 1000;
  return `${pad(h)}:${pad(m)}:${pad(s)},${String(n).padStart(3, '0')}`;
}

function pad(value) {
  return String(value).padStart(2, '0');
}

const srt = script.segments
  .map((segment, index) => {
    return [
      String(index + 1),
      `${timestamp(segment.start)} --> ${timestamp(segment.end)}`,
      segment.caption,
    ].join('\n');
  })
  .join('\n\n');

const narration = script.segments
  .map((segment) => segment.voiceover)
  .join('\n\n');

await mkdir(dirname(captionPath), {recursive: true});
await mkdir(dirname(narrationPath), {recursive: true});
await writeFile(captionPath, `${srt}\n`);
await writeFile(narrationPath, `${narration}\n`);

console.log(`Wrote ${captionPath}`);
console.log(`Wrote ${narrationPath}`);
