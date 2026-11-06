// Race 1b: the same perceptron rule in plain JavaScript (Node). Trains on the 419 pictures of
// pictures.py's many_examples(), then times predict() on the 10 test pictures.
// Run: node perceptron_js.mjs   (writes results/perceptron-js.json)
import { execFileSync } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
// the pictures come from pictures.py, so Python and JavaScript race on exactly the same 400 numbers
const data = JSON.parse(execFileSync('python3', ['-c',
  'import json; from pictures import TEST, many_examples; ' +
  'print(json.dumps({"train": [[p, a] for p, a in many_examples()], "test": [[n, p, a] for n, p, a in TEST]}))'],
  { cwd: here, maxBuffer: 1 << 26 }).toString());

function predict(picture, points) {
  let total = 0;
  for (let i = 0; i < picture.length; i++) {
    if (picture[i] === 1) total = total + points[i];
  }
  return total > 0;
}

function train(picture, answer, points) {
  const guess = predict(picture, points);
  if (guess === answer) return;
  const change = answer ? 1 : -1;
  for (let i = 0; i < picture.length; i++) {
    if (picture[i] === 1) points[i] = points[i] + change;
  }
}

const points = new Array(400).fill(0);   // plain arrays: typed arrays measured slower here (0.47 µs)
const t0 = process.hrtime.bigint();
let rounds = 0;
for (rounds = 1; rounds <= 200; rounds++) {
  let mistakes = 0;
  for (const [picture, answer] of data.train) {
    if (predict(picture, points) !== answer) mistakes++;
    train(picture, answer, points);
  }
  if (mistakes === 0) break;
}
const trainSeconds = Number(process.hrtime.bigint() - t0) / 1e9;

const rows = [];
let sink = 0;   // keep the results alive so the engine can't skip the work
for (const [name, picture, answer] of data.test) {
  const loops = 2_000_000;
  for (let i = 0; i < 200_000; i++) sink += predict(picture, points);   // warm up the JIT
  const best = [];
  for (let k = 0; k < 5; k++) {
    const s = process.hrtime.bigint();
    for (let i = 0; i < loops; i++) sink += predict(picture, points);
    best.push(Number(process.hrtime.bigint() - s) / 1e9 / loops);
  }
  const said = predict(picture, points);
  rows.push({ picture: name, answer, said, right: said === answer, seconds: Math.min(...best) });
}
const seconds = rows.map((r) => r.seconds).sort((a, b) => a - b);
const median = (seconds[4] + seconds[5]) / 2;
const out = {
  system: 'Perceptron (Rosenblatt rule), plain JavaScript',
  setting: `trained on ${data.train.length} pictures; Node ${process.version} on ${process.arch}`,
  training: { pictures: data.train.length, rounds, seconds: trainSeconds },
  right: rows.filter((r) => r.right).length, n: rows.length,
  median_seconds: median, min_seconds: seconds[0], max_seconds: seconds[9], rows, sink,
};
mkdirSync(join(here, 'results'), { recursive: true });
writeFileSync(join(here, 'results', 'perceptron-js.json'), JSON.stringify(out, null, 2));
for (const r of rows) console.log(`${r.picture.padEnd(8)} ${r.right ? 'right' : 'WRONG'}  ${(r.seconds * 1e9).toFixed(1)} ns`);
console.log(`trained in ${rounds} rounds (${(trainSeconds * 1000).toFixed(1)} ms); ${out.right}/${out.n} right; median ${(median * 1e9).toFixed(1)} ns per picture`);
