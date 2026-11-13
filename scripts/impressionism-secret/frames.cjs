/**
 * Render check frames for 你知道印象派的秘密吗？ with one bundle and one browser:
 * the middle of every cue, plus a few in-between moments of the moving shots
 * (extraction, Salon zoom, focus pulls, encode, Camille). Writes out/impressionism-secret/frames/.
 *   node scripts/impressionism-secret/frames.cjs [cue-id,...] [--moments]
 */
const fs = require("node:fs");
const path = require("node:path");
const { bundle } = require("@remotion/bundler");
const { openBrowser, selectComposition, renderStill } = require("@remotion/renderer");

const ROOT = path.resolve(__dirname, "../..");
const OUT = path.join(ROOT, "out/impressionism-secret/frames");
const tl = require(path.join(ROOT, "src/data/impressionism-secret.json"));
const args = process.argv.slice(2);
const moments = args.includes("--moments");
const only = new Set(args.filter((a) => !a.startsWith("--")).flatMap((a) => a.split(",")));

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const serveUrl = await bundle({ entryPoint: path.join(ROOT, "src/index.ts"), rootDir: ROOT });
  const browser = await openBrowser("chrome");
  try {
    const composition = await selectComposition({ serveUrl, id: "ImpressionismPicture", puppeteerInstance: browser });
    const jobs = [];
    for (const cue of tl.cues) {
      if (only.size && !only.has(cue.id)) continue;
      const mid = (cue.start + cue.end) / 2;
      jobs.push([cue.id, mid]);
      if (moments) for (const k of [0.08, 0.3, 0.7, 0.9]) jobs.push([`${cue.id}-${String(k).slice(2)}`, cue.start + k * (cue.end - cue.start)]);
    }
    if (!only.size) jobs.push(["endcard", tl.endCardStart + 3]);
    for (const [name, sec] of jobs) {
      const frame = Math.min(composition.durationInFrames - 1, Math.round(sec * tl.fps));
      await renderStill({ serveUrl, composition, frame, output: path.join(OUT, `${name}.jpg`), imageFormat: "jpeg",
        jpegQuality: 80, puppeteerInstance: browser, inputProps: { audio: "none" },
        offthreadVideoCacheSizeInBytes: 536870912, mediaCacheSizeInBytes: 268435456, offthreadVideoThreads: 2 });
      process.stdout.write(`${name} `);
    }
    console.log(`\n${jobs.length} frames in ${OUT}`);
  } finally {
    await browser.close({ silent: true });
  }
})();
