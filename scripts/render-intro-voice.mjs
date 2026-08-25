import {mkdir, rm, writeFile} from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';

import script from '../src/scripts/intro.en.json' with {type: 'json'};

const run = promisify(execFile);
const __dirname = dirname(fileURLToPath(import.meta.url));
const audioDir = resolve(__dirname, '../public/audio/en/intro');
const tmpDir = resolve(__dirname, '../tmp/intro-voice');
const voice = process.env.INTRO_VOICE || 'Samantha';
const rate = process.env.INTRO_RATE || '142';

await mkdir(audioDir, {recursive: true});
await mkdir(tmpDir, {recursive: true});

for (const [index, segment] of script.segments.entries()) {
  const number = String(index + 1).padStart(2, '0');
  const textPath = resolve(tmpDir, `${number}-${segment.id}.txt`);
  const aiffPath = resolve(tmpDir, `${number}-${segment.id}.aiff`);
  const wavPath = resolve(audioDir, `${number}-${segment.id}.wav`);

  await writeFile(textPath, `${segment.voiceover}\n`);
  await run('say', ['-v', voice, '-r', rate, '-f', textPath, '-o', aiffPath]);
  await run('afconvert', ['-f', 'WAVE', '-d', 'LEI16@44100', aiffPath, wavPath]);
  console.log(`Wrote ${wavPath}`);
}

await rm(tmpDir, {recursive: true, force: true});
