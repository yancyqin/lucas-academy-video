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
const only = new Set(process.argv.slice(2));
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
  } finally {
    await browser.close({ silent: true });
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
