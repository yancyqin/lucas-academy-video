/** Render one frame per cue (late in its slot, when its cards are up) with one bundle and one browser,
 * then a contact sheet: out/fun-economics-01/frames/sheet-N.png.
 *   node scripts/fun-economics-01/frames.cjs [cue ids, comma separated] [--at=0.7] [--lang=en] [--comp=FunEconomics01ExtraZh --out=fun-economics-01-7x8]
 */
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const { bundle } = require("@remotion/bundler");
const { openBrowser, selectComposition, renderStill } = require("@remotion/renderer");

const ROOT = path.resolve(__dirname, "../..");
const langArg = process.argv.find((a) => a.startsWith("--lang="));
const LANG = langArg ? langArg.slice(7) : "zh";
const optArg = (name) => (process.argv.find((a) => a.startsWith(`--${name}=`)) || "").split("=")[1];
const OUT = path.join(ROOT, `out/${optArg("out") || "fun-economics-01"}/frames-${LANG}`);
const atArg = process.argv.find((a) => a.startsWith("--at="));
const at = atArg ? Number(atArg.slice(5)) : 0.7;
const only = new Set(process.argv.slice(2).filter((a) => !a.startsWith("--")).flatMap((a) => a.split(",")));

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const serveUrl = await bundle({ entryPoint: path.join(ROOT, "src/index.ts"), rootDir: ROOT });
  const browser = await openBrowser("chrome");
  try {
    const composition = await selectComposition({ serveUrl, id: optArg("comp") || (LANG === "en" ? "FunEconomics01En" : "FunEconomics01Zh"), puppeteerInstance: browser });
    const tl = composition.props.tl;
    const shots = tl.cues.filter((c) => !only.size || only.has(c.id)).map((c) => [c.id, c.start + at * (c.end - c.start)]);
    if (!only.size) shots.push(["end", tl.endCardStart + 3]);
    const files = [];
    for (const [id, t] of shots) {
      const output = path.join(OUT, `${id}.png`);
      await renderStill({ composition, serveUrl, output, frame: Math.min(composition.durationInFrames - 1, Math.round(t * tl.fps)), puppeteerInstance: browser });
      files.push(output);
      process.stdout.write(`${id} `);
    }
    console.log();
    for (let k = 0; k * 12 < files.length; k++) {
      const group = files.slice(k * 12, k * 12 + 12);
      const args = group.flatMap((f) => ["-i", f]);
      const n = group.length;
      const filter = group.map((_, i) => `[${i}]scale=640:360[v${i}]`).join(";") + ";" + group.map((_, i) => `[v${i}]`).join("") +
        `xstack=inputs=${n}:layout=` + group.map((_, i) => `${(i % 3) * 640}_${Math.floor(i / 3) * 360}`).join("|") + ":fill=white[out]";
      const sheet = path.join(OUT, `sheet-${k + 1}.png`);
      const r = spawnSync("ffmpeg", ["-v", "error", "-y", ...args, "-filter_complex", n > 1 ? filter : "[0]scale=640:360[out]", "-map", "[out]", sheet], { stdio: "inherit" });
      if (r.status !== 0) throw Error("contact sheet failed");
      console.log(sheet);
    }
  } finally {
    await browser.close({ silent: true });
  }
})().catch((e) => { console.error(e); process.exit(1); });
