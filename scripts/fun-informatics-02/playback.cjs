const { build } = require("esbuild");
const fs = require("node:fs");
const path = require("node:path");
const ROOT = path.resolve(__dirname, "../..");
const target = path.join(ROOT, "out/fun-informatics-02/playback.cjs");
(async () => {
  await build({
    entryPoints: [path.join(ROOT, "src/videos/fun-informatics-02/playback.ts")],
    outfile: target,
    bundle: true,
    platform: "node",
    format: "cjs",
  });
  const { buildPlayback } = require(target);
  const file = path.join(ROOT, `public/fun-informatics-02/timeline.${process.argv[2] || "zh"}.json`);
  const tl = JSON.parse(fs.readFileSync(file, "utf8"));
  Object.assign(tl, buildPlayback(tl));
  fs.writeFileSync(file, JSON.stringify(tl, null, 2) + "\n");
  console.log(
    "Validated five continuous speed curves; " +
      tl.gameFeedback.length +
      " original feedback cues",
  );
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
