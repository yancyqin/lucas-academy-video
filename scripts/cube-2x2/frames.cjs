/** Stills for checking a 2×2 cube film timeline (CUBE-2X2.md): one bundle, one browser, a frame per moment asked for.
 *
 *    node scripts/cube-2x2/frames.cjs [zh|en] [cb02-05,cb03-02 ...] [--at 0.3,0.9]
 *
 * For every cue (or only those listed) it renders the frames at the given fractions of the cue's speech
 * (default 0.8), Writes out/cube-2x2/frames[.en]/.
 */
const fs = require("node:fs");
const path = require("node:path");
const { bundle } = require("@remotion/bundler");
const { openBrowser, selectComposition, renderStill } = require("@remotion/renderer");

const ROOT = path.resolve(__dirname, "../..");
const args = process.argv.slice(2);
const lang = args.includes("en") ? "en" : "zh";
const atIndex = args.indexOf("--at");
const fractions = atIndex >= 0 ? args[atIndex + 1].split(",").map(Number) : [0.8];
const only = new Set(args.filter((a, i) => /^cb\d\d-\d\d/.test(a) && args[i - 1] !== "--at").flatMap((a) => a.split(",")));
const OUT = path.join(ROOT, `out/cube-2x2/frames${lang === "en" ? ".en" : ""}`);

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const serveUrl = await bundle({ entryPoint: path.join(ROOT, "src/index.ts"), rootDir: ROOT });
  const browser = await openBrowser("chrome");
  try {
    const id = lang === "en" ? "Cube2x2" : "Cube2x2ZhTrack";
    const composition = await selectComposition({ serveUrl, id, puppeteerInstance: browser, inputProps: {} });
    const tl = composition.props.tl;
    const jobs = [];
    for (const cue of tl.cues) {
      if (only.size && !only.has(cue.id)) continue;
      for (const f of fractions) jobs.push([`${cue.id}-${String(Math.round(f * 100)).padStart(3, "0")}`, cue.speech.start + f * (cue.speech.end - cue.speech.start)]);

    }
    if (!only.size) jobs.push(["end-card", tl.endCardStart + 2]);
    for (const [name, t] of jobs) {
      const frame = Math.min(composition.durationInFrames - 1, Math.round(t * tl.fps));
      await renderStill({ composition, serveUrl, frame, output: path.join(OUT, `${name}.png`), puppeteerInstance: browser, inputProps: {} });
      console.log(name, frame);
    }
  } finally {
    await browser.close({ silent: true });
  }
})();
