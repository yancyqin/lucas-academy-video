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
const lang = process.argv.includes("en") ? "en" : "zh";
const OUT = path.join(ROOT, `out/fun-informatics-02/frames${lang === "en" ? ".en" : ""}`);
const details = process.argv.includes("--details");
const tails = process.argv.includes("--tails");
const only = new Set(process.argv.slice(2).filter((a) => a !== "--details" && a !== "--tails" && a !== "en" && a !== "zh"));
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const serveUrl = await bundle({
    entryPoint: path.join(ROOT, "src/index.ts"),
    rootDir: ROOT,
  });
  const browser = await openBrowser("chrome");
  const audits = [];
  let label = "metadata";
  if (lang === "en") {
    const newPage = browser.newPage.bind(browser);
    browser.newPage = async (...args) => {
      const page = await newPage(...args);
      const close = page.close.bind(page);
      page.close = async (...closeArgs) => {
        try {
          const nodes = await page.evaluate(() => {
            const result = [];
            const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            let node;
            while ((node = walk.nextNode())) {
              const text = node.textContent.trim();
              if (!text || ["SCRIPT", "STYLE"].includes(node.parentElement?.tagName)) continue;
              const range = document.createRange();range.selectNodeContents(node);
              const r = range.getBoundingClientRect();
              if (r.width > 0 && r.height > 0) result.push({text, x:r.x, y:r.y, right:r.right, bottom:r.bottom});
            }
            return result;
          });
          audits.push({label, chinese:nodes.filter(n=>/[一-鿿]/.test(n.text)), outside:nodes.filter(n=>n.x < -1 || n.y < -1 || n.right > 1921 || n.bottom > 1081)});
        } catch (e) { audits.push({label,error:String(e)}); }
        return close(...closeArgs);
      };
      return page;
    };
  }
  try {
    const composition = await selectComposition({
      serveUrl,
      id: `FunInformatics02${lang === "en" ? "En" : "Zh"}`,
      puppeteerInstance: browser,
    });
    const tl = composition.props.tl;
    for (const cue of tl.cues) {
      if (details) continue;
      if (only.size && !only.has(cue.id)) continue;
      const time =
        cue.speech.start + (cue.speech.end - cue.speech.start) * (tails ? 0.98 : 0.72);
      const frame = Math.round(time * tl.fps);
      label = cue.id;
      await renderStill({
        serveUrl,
        composition,
        puppeteerInstance: browser,
        frame,
        scale: 0.5,
        imageFormat: "jpeg",
        jpegQuality: 88,
        output: path.join(OUT, cue.id + (tails ? ".tail" : "") + ".jpg"),
        timeoutInMilliseconds: 180000,
        logLevel: "error",
      });
      console.log(cue.id + " @ " + time.toFixed(2) + "s");
    }
    if (details) {
      const cue = (id) => tl.cues.find((c) => c.id === id);
      const letter = cue("cl03-04");
      const samples = {
        "letter-l": lang === "en" ? (tl.markers?.["cl03-04"]?.["letter-l"] ?? letter.speech.start + 3) + 0.15 : letter.start + (letter.end - letter.start) * 0.4,
        "letter-d": lang === "en" ? (tl.markers?.["cl03-04"]?.["letter-d"] ?? letter.speech.start + 4) + 0.25 : letter.start + (letter.end - letter.start) * 0.85,
        "letter-person": cue("cl03-06").start - 0.5,
        "words-play": cue("cl04-05").speech.end + 8,
        "words-four-steps": cue("cl04-05").end - 0.5,
        "ai-questions-pause": cue("cl04-19").end - 1,
        "cadence-ending": tl.musicExample.end - 0.4,
        "questions-reading-hold": tl.endCardStart - 1,
        "end-card": tl.endCardStart + 4,
      };
      for (const [name, time] of Object.entries(samples)) {
        label = name;
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
    if (lang === "en") fs.writeFileSync(path.join(OUT, details ? "text-audit.details.json" : tails ? "text-audit.tails.json" : "text-audit.json"), JSON.stringify(audits,null,2)+"\n");
    await browser.close({ silent: true });
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
