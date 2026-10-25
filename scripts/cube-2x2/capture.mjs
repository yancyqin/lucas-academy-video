// Records the cube page's footage for 「二阶魔方怎么还原？」 (CUBE-2X2.md) frame by frame in headless Chrome.
//
//   node scripts/cube-2x2/capture.mjs [solve|hero|meet|notation ...] [--url http://127.0.0.1:8133/cube/]
//
// The page is inception-space-ui's /cube/ with ?debug: its manual clock (__cube.manual / tick) moves the page
// exactly 1/30 s per frame whatever the machine does, and its guide ("Solve it for me") plays the solve stage
// by stage. Each take becomes public/cube-2x2/footage/<take>.mp4, its last frame <take>.jpg, and <take>.json:
// for every move, the frames it turns between, and where each stage and step starts, so the film can show the
// move that is turning and run the footage on a speed curve keyed to the narration.
//
// Takes:
//   hero      the scrambled cube from the usual view, one slow turn round (the opening), 20 s
//   meet      a solved cube turning slowly, tilted to show top and bottom (meet the cube), 20 s
//   notation  R, R′, U, U′, F, F′, B, B′, U2 (and back), y, y′ on a solved cube, each held a moment
//   letters   R, U, F, R′, U2 on a solved cube, the order the letters line names them (v0.3)
//   page      the real page, panel and all: "Step by step", "Next move" ×4, "Next step", "Play" (v0.3)
//   solve     the whole guided solve of the scramble, one take: the first layer seen from below, the rest from
//             above, a turn round at the end

import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(fileURLToPath(import.meta.url), "../../..");
const OUT = join(ROOT, "public/cube-2x2/footage");
const PLAYWRIGHT = process.env.PLAYWRIGHT_DIR
  ? join(process.env.PLAYWRIGHT_DIR, "package.json")
  : "/Users/yqin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json";
const { chromium } = createRequire(PLAYWRIGHT)("playwright");

const args = process.argv.slice(2);
const flag = (name, fallback) => (args.includes(`--${name}`) ? args[args.indexOf(`--${name}`) + 1] : fallback);
const BASE = flag("url", "http://127.0.0.1:8133/cube/");
const TAKES = args.filter((arg, at) => !arg.startsWith("--") && !(at > 0 && args[at - 1].startsWith("--")));
/** The film's scramble (a 67-move beginner's solve that shows every rule once: CUBE-2X2.md §2). */
const SCRAMBLE = "F' U' B' R D F R2 F D R2 B2 L";
const FPS = 30;
const FRAME_MS = 1000 / FPS;
/** Camera pitch for the first layer: from below, so the white layer is in view while it is built. */
const BELOW = -0.72;

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true, channel: "chrome" });

/** Takes of the real page, panel and all, as a visitor sees it: no extra light, nothing hidden. */
const REAL_PAGE = new Set(["page"]);

async function take(name, script) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.addInitScript(() => {
    Object.defineProperty(document, "hidden", { get: () => false, configurable: true });
    Object.defineProperty(document, "visibilityState", { get: () => "visible", configurable: true });
    try {
      localStorage.clear();
    } catch {}
  });
  page.on("pageerror", error => console.error(`${name}: page error: ${error.message}`));
  await page.goto(`${BASE}?size=2&debug`);
  await page.waitForFunction(() => window.__cube);
  // The cube alone, full frame: the panel and every overlay go (except for a take of the real page).
  const real = REAL_PAGE.has(name);
  if (!real) {
    await page.addStyleTag({
      content: ".panel,.hud,.facing,.stage-tools,.guide-hud,.layer-chip,.toast{display:none!important}.app{grid-template-columns:1fr!important}",
    });
  }
  await page.waitForTimeout(400);
  await page.evaluate(real => {
    const c = window.__cube;
    if (real) {
      c.manual(true);
      c.reset();
      c.reset();
      c.view.resetView();
      c.setSpeed(2);
      return;
    }
    // The page lights the cube from above, so a white bottom reads grey. The first layer is built on the
    // bottom and filmed from below, so the film adds one light from underneath (the page itself is unchanged).
    const key = c.view.scene.children.find(object => object.isDirectionalLight);
    const under = key.clone();
    under.position.set(3, -10, 7);
    under.intensity = 1.6;
    c.view.scene.add(under);
    c.view.dirty = true;
    c.manual(true);
    c.reset();
    c.reset();
    c.view.resetView();
    c.setSpeed(1); // one move a second: a quarter turn animates for 0.6 s, a half turn 0.75 s
  }, real);

  const ffmpeg = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", `${FPS}`, "-i", "-",
    "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", "-g", "15", join(OUT, `${name}.mp4`)], { stdio: ["pipe", "inherit", "inherit"] });
  let frame = 0;
  let last = null;
  const record = { fps: FPS, take: name, scramble: null, frames: 0, moves: [], stages: [], steps: [], marks: [] };

  const rec = {
    page,
    record,
    get frame() {
      return frame;
    },
    /** Moves the page on one frame (turning the camera by `orbit` first) and records it. */
    async tick(orbit = null, ms = FRAME_MS) {
      const state = await page.evaluate(
        ({ ms, orbit }) => {
          const c = window.__cube;
          if (orbit) c.view.orbit(orbit[0], orbit[1]);
          c.tick(ms);
          return { landed: c.guide?.model.landed ?? null, taken: c.guide?.model.taken ?? null };
        },
        { ms, orbit },
      );
      last = await page.screenshot({ type: "jpeg", quality: 94 });
      ffmpeg.stdin.write(last);
      frame += 1;
      return state;
    },
    async hold(count) {
      for (let at = 0; at < count; at += 1) await rec.tick();
    },
    /** Eases the camera to (yaw, pitch) over `count` frames. */
    async swing(yaw, pitch, count) {
      const from = await page.evaluate(() => ({ yaw: window.__cube.view.yaw, pitch: window.__cube.view.pitch }));
      const ease = t => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
      let was = from;
      for (let at = 1; at <= count; at += 1) {
        const t = ease(at / count);
        const now = { yaw: from.yaw + (yaw - from.yaw) * t, pitch: from.pitch + (pitch - from.pitch) * t };
        await rec.tick([now.yaw - was.yaw, now.pitch - was.pitch]);
        was = now;
      }
    },
    /**
     * Plays notation on the page, one move at a time, and records it. A typed move animates in 150 ms
     * (220 ms for a half turn), so the page's clock runs at a quarter of real time here: each turn takes
     * 0.6 s (0.88 s) of film, the same pace as the guide's turns in the solve.
     */
    async play(text, hold = 0) {
      const moves = text.split(/\s+/).filter(Boolean);
      for (const label of moves) {
        const start = frame;
        await page.evaluate(label => window.__cube.play(label), label);
        const half = label.includes("2");
        const frames = half ? 26 : 18;
        for (let at = 0; at < frames; at += 1) await rec.tick(null, (half ? 220 : 150) / (frames - 2));
        record.moves.push({ label, start, end: frame });
        await rec.hold(hold);
      }
    },
    mark(name) {
      record.marks.push({ name, frame });
    },
    /** A drawn pointer glides to an element over `count` frames, then presses it (a ring shows the press). */
    async press(selector, count = 18) {
      await page.evaluate(() => {
        if (document.getElementById("cap-cursor")) return;
        const cursor = document.createElement("div");
        cursor.id = "cap-cursor";
        cursor.style.cssText = "position:fixed;left:1500px;top:900px;width:46px;height:46px;z-index:99999;pointer-events:none;" +
          "background:url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M4 2 L4 19 L8.5 15 L11.5 22 L14.5 20.7 L11.5 14 L18 14 Z' fill='white' stroke='black' stroke-width='1.4' stroke-linejoin='round'/></svg>\") no-repeat;";
        const ring = document.createElement("div");
        ring.id = "cap-ring";
        ring.style.cssText = "position:fixed;width:20px;height:20px;border:4px solid #9ed7bd;border-radius:50%;z-index:99998;pointer-events:none;opacity:0;";
        document.body.append(cursor, ring);
      });
      const target = await page.evaluate(selector => {
        const element = document.querySelector(selector);
        element.scrollIntoView({ block: "nearest" });
        const box = element.getBoundingClientRect();
        const cursor = document.getElementById("cap-cursor");
        return { x: box.left + box.width / 2, y: box.top + box.height / 2, fromX: parseFloat(cursor.style.left), fromY: parseFloat(cursor.style.top) };
      }, selector);
      const ease = t => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
      for (let at = 1; at <= count; at += 1) {
        const t = ease(at / count);
        await page.evaluate(({ x, y }) => {
          const cursor = document.getElementById("cap-cursor");
          cursor.style.left = `${x}px`;
          cursor.style.top = `${y}px`;
        }, { x: target.fromX + (target.x - target.fromX) * t, y: target.fromY + (target.y - target.fromY) * t });
        await rec.tick();
      }
      await page.evaluate(({ selector, x, y }) => {
        document.querySelector(selector).click();
        const ring = document.getElementById("cap-ring");
        ring.style.left = `${x - 10}px`;
        ring.style.top = `${y - 10}px`;
        ring.dataset.age = "0";
      }, { selector, ...target });
      record.marks.push({ name: `press ${selector}`, frame });
    },
    /** Moves the page on `count` frames, growing and fading the press ring. */
    async run(count) {
      for (let at = 0; at < count; at += 1) {
        await page.evaluate(() => {
          const ring = document.getElementById("cap-ring");
          if (!ring || ring.dataset.age === undefined) return;
          const age = Number(ring.dataset.age) + 1;
          ring.dataset.age = String(age);
          const size = 20 + age * 5;
          const x = parseFloat(ring.style.left) + 10;
          const y = parseFloat(ring.style.top) + 10;
          ring.style.width = ring.style.height = `${size}px`;
          ring.style.left = `${x - size / 2}px`;
          ring.style.top = `${y - size / 2}px`;
          ring.style.opacity = String(Math.max(0, 1 - age / 12));
          if (age > 12) delete ring.dataset.age;
        });
        await rec.tick();
      }
    },
  };

  await script(rec);
  ffmpeg.stdin.end();
  await new Promise((resolve, reject) => ffmpeg.on("close", code => (code ? reject(new Error(`ffmpeg ${code}`)) : resolve())));
  if (last) writeFileSync(join(OUT, `${name}.jpg`), last);
  record.frames = frame;
  writeFileSync(join(OUT, `${name}.json`), JSON.stringify(record, null, 1) + "\n");
  console.log(`${name}: ${frame} frames (${(frame / FPS).toFixed(1)} s), ${record.moves.length} moves`);
  await page.close();
}

const home = async page => page.evaluate(() => ({ yaw: window.__cube.view.yaw, pitch: window.__cube.view.pitch }));

const SCRIPTS = {
  async hero(r) {
    r.record.scramble = SCRAMBLE;
    await r.page.evaluate(scramble => {
      window.__cube.play(scramble);
      window.__cube.flush();
    }, SCRAMBLE);
    const { yaw, pitch } = await home(r.page);
    await r.hold(15);
    await r.swing(yaw + Math.PI * 2, pitch, 570);
    await r.hold(15);
  },

  async meet(r) {
    const { yaw, pitch } = await home(r.page);
    await r.hold(15);
    await r.swing(yaw + Math.PI, -0.65, 270);
    r.mark("bottom");
    await r.hold(20);
    await r.swing(yaw + Math.PI * 2, pitch, 270);
    r.mark("top");
    await r.hold(20);
  },

  /** The real page: "Step by step", a few "Next move"s, "Next step", then "Play" (the film's opening and ending). */
  async page(r) {
    r.record.scramble = SCRAMBLE;
    await r.page.evaluate(scramble => {
      window.__cube.play(scramble);
      window.__cube.flush();
    }, SCRAMBLE);
    await r.run(20);
    await r.press("#guide-start-step", 20);
    await r.page.waitForFunction(() => window.__cube.guide);
    // Bring the guide's card into view in the panel, as a visitor would scroll to it.
    await r.page.evaluate(() => document.querySelector(".guide").scrollIntoView({ block: "start" }));
    await r.run(14);
    for (let k = 0; k < 4; k += 1) {
      await r.press("#guide-move", k === 0 ? 18 : 8);
      await r.run(26);
    }
    await r.press("#guide-step-button", 10);
    await r.run(70);
    await r.press("#guide-toggle", 12);
    await r.run(110);
  },

  /** R, U, F, R′, U2 on a solved cube: the letters line (cb01-01), in its order. */
  async letters(r) {
    await r.hold(8);
    for (const [text, rest] of [["R", 8], ["U", 8], ["F", 10], ["R'", 10], ["U2", 18]]) {
      r.mark(text);
      await r.play(text, rest);
    }
  },

  async notation(r) {
    await r.hold(20);
    // In the narration's order: R, R′ (cb01-03); U, U′, F, F′, B, B′ (cb01-04); U2 and back, y, y′ (cb01-05).
    for (const [text, rest] of [["R", 26], ["R'", 30], ["U", 22], ["U'", 22], ["F", 22], ["F'", 22], ["B", 22], ["B'", 30], ["U2", 22], ["U2", 22], ["y", 26], ["y'", 20]]) {
      r.mark(text);
      await r.play(text, rest);
    }
  },

  async solve(r) {
    r.record.scramble = SCRAMBLE;
    await r.page.evaluate(scramble => {
      window.__cube.play(scramble);
      window.__cube.flush();
      window.__cube.startGuide(false);
    }, SCRAMBLE);
    await r.page.waitForFunction(() => window.__cube.guide);
    const plan = await r.page.evaluate(() =>
      window.__cube.guide.model.stages.map(stage => ({
        key: stage.key,
        title: stage.title,
        steps: stage.steps.map(step => ({ text: step.text, alg: step.alg, moves: step.moves })),
      })),
    );
    r.record.plan = plan;
    const { yaw, pitch } = await home(r.page);
    await r.hold(30);
    let stageAt = -1;
    for (;;) {
      const at = await r.page.evaluate(() => {
        const g = window.__cube.guide;
        if (!g || g.model.exhausted) return null;
        const where = g.model.where();
        return { stage: where.stageIndex, step: where.stepIndex, into: where.into };
      });
      if (!at) break;
      if (at.stage !== stageAt) {
        if (stageAt >= 0) await r.hold(24);
        stageAt = at.stage;
        const want = plan[at.stage].key === "layer" ? BELOW : pitch;
        const now = await r.page.evaluate(() => window.__cube.view.pitch);
        if (Math.abs(now - want) > 0.01) await r.swing(yaw, want, 40);
        r.record.stages.push({ stage: at.stage, key: plan[at.stage].key, frame: r.frame });
        await r.hold(10);
      }
      if (at.into === 0) r.record.steps.push({ stage: at.stage, step: at.step, frame: r.frame });
      await r.page.evaluate(() => window.__cube.guidePlay("move"));
      const start = r.frame;
      for (let guard = 0; guard < 120; guard += 1) {
        const state = await r.tick();
        if (state.landed === null || (state.taken > 0 && state.landed >= state.taken && r.frame - start > 2)) break;
      }
      const step = plan[at.stage].steps[at.step];
      r.record.moves.push({ stage: at.stage, step: at.step, index: at.into, move: step.moves[at.into], start, end: r.frame });
      await r.hold(at.into === step.moves.length - 1 ? 16 : 3);
      if (await r.page.evaluate(() => !window.__cube.guide)) break;
    }
    r.mark("solved");
    await r.hold(20);
    await r.swing(yaw + Math.PI * 2, pitch, 150);
    await r.hold(15);
  },
};

for (const name of TAKES.length ? TAKES : Object.keys(SCRIPTS)) {
  if (!SCRIPTS[name]) throw new Error(`no take called ${name}`);
  await take(name, SCRIPTS[name]);
}
await browser.close();
