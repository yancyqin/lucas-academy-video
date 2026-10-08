/** Render a frame per approved cue using one bundle and one browser. */
const fs = require("node:fs");
const path = require("node:path");
const { bundle } = require("@remotion/bundler");
const {
  openBrowser,
  selectComposition,
  renderStill,
} = require("@remotion/renderer");
const ROOT = path.resolve(__dirname, "../..");
const OUT = path.join(ROOT, "out/fun-informatics-02/frames");
const details = process.argv.includes("--details");
const only = new Set(process.argv.slice(2).filter((a) => a !== "--details"));
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const serveUrl = await bundle({
    entryPoint: path.join(ROOT, "src/index.ts"),
    rootDir: ROOT,
  });
  const browser = await openBrowser("chrome");
  try {
    const composition = await selectComposition({
      serveUrl,
      id: "FunInformatics02Zh",
      puppeteerInstance: browser,
    });
    const tl = composition.props.tl;
    for (const cue of tl.cues) {
      if (details) continue;
      if (only.size && !only.has(cue.id)) continue;
      const time =
        cue.speech.start + (cue.speech.end - cue.speech.start) * 0.72;
      const frame = Math.round(time * tl.fps);
      await renderStill({
        serveUrl,
        composition,
        puppeteerInstance: browser,
        frame,
        scale: 0.5,
        imageFormat: "jpeg",
        jpegQuality: 88,
        output: path.join(OUT, cue.id + ".jpg"),
        timeoutInMilliseconds: 180000,
        logLevel: "error",
      });
      console.log(cue.id + " @ " + time.toFixed(2) + "s");
    }
    if (details) {
      const cue = (id) => tl.cues.find((c) => c.id === id);
      const letter = cue("cl03-04");
      const samples = {
        "letter-l": letter.start + (letter.end - letter.start) * 0.4,
        "letter-d": letter.start + (letter.end - letter.start) * 0.85,
        "letter-person": cue("cl03-06").start - 0.5,
        "words-play": cue("cl04-05").speech.end + 8,
        "words-four-steps": cue("cl04-05").end - 0.5,
        "cadence-ending": tl.musicExample.end - 0.4,
        "questions-reading-hold": tl.endCardStart - 1,
        "end-card": tl.endCardStart + 4,
      };
      for (const [name, time] of Object.entries(samples)) {
        await renderStill({
          serveUrl,
          composition,
          puppeteerInstance: browser,
          frame: Math.round(time * tl.fps),
          scale: 0.5,
          imageFormat: "jpeg",
          jpegQuality: 90,
          output: path.join(OUT, name + ".jpg"),
          timeoutInMilliseconds: 180000,
          logLevel: "error",
        });
        console.log(name + " @ " + time.toFixed(2) + "s");
      }
    }
  } finally {
    await browser.close({ silent: true });
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
