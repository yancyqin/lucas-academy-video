/** Render stills with one bundle and one browser, then contact sheets: out/fun-economics-02/frames/sheet-N.png.
 * One frame per cue (late in its slot) by default, or named frames from a JSON file ({"name": frame}).
 *   node scripts/fun-economics-02/frames.cjs [cue ids, comma separated] [--at=0.7] [--shots=file.json] [--comp=FunEconomics02En]
 */
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const { bundle } = require("@remotion/bundler");
const { openBrowser, selectComposition, renderStill } = require("@remotion/renderer");

const ROOT = path.resolve(__dirname, "../..");
const OUT = path.join(ROOT, "out/fun-economics-02/frames");
const optArg = (name) => (process.argv.find((a) => a.startsWith(`--${name}=`)) || "").split("=")[1];
const at = Number(optArg("at") || 0.7);
const only = new Set(process.argv.slice(2).filter((a) => !a.startsWith("--")).flatMap((a) => a.split(",")));

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const serveUrl = await bundle({ entryPoint: path.join(ROOT, "src/index.ts"), rootDir: ROOT });
  const browser = await openBrowser("chrome");
  try {
    const id = optArg("comp") || "FunEconomics02Zh";
    const composition = await selectComposition({ serveUrl, id, puppeteerInstance: browser });
    const tl = composition.props.tl;
    let shots;
    if (optArg("shots")) shots = Object.entries(JSON.parse(fs.readFileSync(optArg("shots"), "utf8")));
    else if (!tl) shots = [[id, 0]];
    else {
      shots = tl.cues.filter((c) => !only.size || only.has(c.id)).map((c) => [c.id, Math.round((c.start + at * (c.end - c.start)) * tl.fps)]);
      if (!only.size) shots.push(["end", Math.round((tl.endCardStart + 3) * tl.fps)]);
    }
    const files = [];
    for (const [name, frame] of shots) {
      const output = path.join(OUT, `${name}.png`);
      await renderStill({ composition, serveUrl, output, frame: Math.min(composition.durationInFrames - 1, frame), puppeteerInstance: browser });
      files.push(output);
      process.stdout.write(`${name} `);
    }
    console.log();
    for (let k = 0; k * 12 < files.length && files.length > 1; k++) {
      const group = files.slice(k * 12, k * 12 + 12);
      const n = group.length;
      const filter = group.map((_, i) => `[${i}]scale=640:360[v${i}]`).join(";") + ";" + group.map((_, i) => `[v${i}]`).join("") +
        `xstack=inputs=${n}:layout=` + group.map((_, i) => `${(i % 3) * 640}_${Math.floor(i / 3) * 360}`).join("|") + ":fill=white[out]";
      const sheet = path.join(OUT, `sheet-${k + 1}.png`);
      const r = spawnSync("ffmpeg", ["-v", "error", "-y", ...group.flatMap((f) => ["-i", f]), "-filter_complex", n > 1 ? filter : "[0]scale=640:360[out]", "-map", "[out]", sheet], { stdio: "inherit" });
      if (r.status !== 0) throw Error("contact sheet failed");
      console.log(sheet);
    }
  } finally {
    await browser.close({ silent: true });
  }
})().catch((e) => { console.error(e); process.exit(1); });
