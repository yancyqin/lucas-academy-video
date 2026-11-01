// Captures the art lab's living painting of every work of a 中英阅读 film while its English verses add living
// brushes (ZHONG-YING.md), frame by frame in headless Chrome.
//
//   python3 -m http.server 8746 -d <art lab export>      (lucas-academy-video-data/zhong-ying/art-lab-<sha>)
//   node scripts/zhong-ying/living.mjs climb-higher [--only <work id>] [--url http://127.0.0.1:8746]
//
// The page is the real living.html. Brushes are painted with real mouse strokes, so the page's own pointer code
// feeds them point by point, a little more each frame — the stroke is drawn on at the speed of the film. Draw
// Alive objects (boats, monkeys, the eagle) wake with __living.wake. The page's clock is not used: every frame
// is drawn with __living.drawAt(t) on the film's clock and read back from the canvas.
//
// Writes public/zhong-ying/<film>/living-<work>.mp4 (the picture's own size), living-<work>.jpg (the untouched
// picture, which paint.py paints in) and living-<work>.json ({firstFrame}: the film frame it starts on).
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(fileURLToPath(import.meta.url), "../../..");
const PLAYWRIGHT = process.env.PLAYWRIGHT_DIR
  ? join(process.env.PLAYWRIGHT_DIR, "package.json")
  : "/Users/yqin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json";
const { chromium } = createRequire(PLAYWRIGHT)("playwright");

const args = process.argv.slice(2);
const flag = (name, fallback) => (args.includes(`--${name}`) ? args[args.indexOf(`--${name}`) + 1] : fallback);
const film = args[0];
const ONLY = flag("only", null);
const BASE = flag("url", "http://127.0.0.1:8746");
const DIR = join(ROOT, "public/zhong-ying", film);
const tl = JSON.parse(readFileSync(join(DIR, "timeline.json"), "utf8"));
const FPS = tl.fps;
// The page's clock when a work's living part begins. Marks and objects move on the page's absolute clock, so an
// object woken at an arbitrary moment hops to wherever its motion is then. So the clock is chosen (always
// positive, so nothing woken earlier is held still) to wake the work's main mover — its first boat, or the
// eagle — when its motion is as close to rest as it gets. The terms are living-brushes.js move(), in pixels of
// an object about 60 px (boat) or 580 × 300 px (eagle): a boat drifts 0.2·w·sin(0.25t + φ), bobs and tilts a
// little; the eagle sways 0.025·w·sin(0.35t), rises 0.11·h·(1 − cos 0.55t) and tilts 2°·sin(0.55t).
const MOTION = {
  boat: (t, phase) => 12 * Math.abs(Math.sin(0.25 * t + phase)) + 2 * Math.abs(Math.sin(1.7 * t + phase)) + 1 * Math.abs(Math.sin(1.3 * t + phase)),
  wind: (t) => 14.5 * Math.abs(Math.sin(0.35 * t)) + 33 * (1 - Math.cos(0.55 * t)) + 10 * Math.abs(Math.sin(0.55 * t)),
};
function startClock(strokes) {
  const tap = strokes.find((s) => !s.pts && MOTION[s.brush]);
  if (!tap) return 3;
  const phase = tap.path[1] * 2 * Math.PI;                    // object.cx / stageWidth · TAU
  const from = tap.start - strokes[0].start + 1;              // the first frame's page time is then ≥ 1
  let best = from;
  for (let t = from; t < from + 200; t += 0.01) if (MOTION[tap.brush](t, phase) < MOTION[tap.brush](best, phase)) best = t;
  return best - (tap.start - strokes[0].start);
}
const WARPS = new Set(["river", "sway"]); // brushes that move the picture itself (living-brushes.js kind "warp")

const browser = await chromium.launch({ headless: true, channel: "chrome" });
const page = await browser.newPage({ viewport: { width: 1600, height: 1100 }, deviceScaleFactor: 1 });
page.on("pageerror", (e) => console.error("page:", e.message));

/** A path in picture fractions: a polyline, or ("ring", cx, cy, r) for a little circle. */
function points(path) {
  if (path[0] === "ring") {
    const [, cx, cy, r] = path;
    return Array.from({ length: 25 }, (_, i) => [cx + r * Math.cos((i / 24) * 2 * Math.PI), cy + r * 0.8 * Math.sin((i / 24) * 2 * Math.PI)]);
  }
  return path;
}
/** The point a fraction p of the way along a polyline. */
function along(pts, p) {
  const seg = pts.slice(1).map((q, i) => Math.hypot(q[0] - pts[i][0], q[1] - pts[i][1]));
  let d = p * seg.reduce((a, b) => a + b, 0);
  for (let i = 0; i < seg.length; i++) {
    if (d <= seg[i] || i === seg.length - 1) {
      const k = seg[i] ? Math.min(1, d / seg[i]) : 0;
      return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k];
    }
    d -= seg[i];
  }
  return pts[pts.length - 1];
}

for (const work of tl.works) {
  if (ONLY && work.id !== ONLY) continue;
  await page.goto(`${BASE}/living.html?w=${work.id}&lang=zh`);
  await page.waitForFunction(() => window.__living?.info().ready);
  await page.evaluate(() => { document.getElementById("hints").checked = false; window.__living.areas(false); });
  const geo = await page.evaluate(() => {
    const cv = document.getElementById("c"), r = cv.getBoundingClientRect(), { w, h } = window.__living.info();
    const sc = Math.min(r.width / w, r.height / h);
    return { W: w, H: h, sc, ox: r.left + (r.width - w * sc) / 2, oy: r.top + (r.height - h * sc) / 2 };
  });
  const client = ([fx, fy]) => [geo.ox + fx * geo.W * geo.sc, geo.oy + fy * geo.H * geo.sc];
  const grab = async (t) => Buffer.from((await page.evaluate((t) => {
    window.__living.drawAt(t);
    return document.getElementById("c").toDataURL("image/jpeg", 0.95);
  }, t)).split(",")[1], "base64");

  const strokes = work.living.map((s) => ({ ...s, pts: s.path[0] === "tap" ? null : points(s.path), dur: s.dur ?? 1.0 }))
    .sort((a, b) => a.start - b.start);
  const T0 = startClock(strokes);
  writeFileSync(join(DIR, `living-${work.id}.jpg`), await grab(T0));
  const first = Math.floor(strokes[0].start * FPS) - 1;
  const last = Math.round(work.end * FPS);
  const out = join(DIR, `living-${work.id}.mp4`);
  const ffmpeg = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", `${FPS}`, "-i", "-",
    "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", out], { stdio: ["pipe", "inherit", "inherit"] });
  let next = 0, active = null;
  for (let f = first; f < last; f++) {
    const t = f / FPS;
    while (next < strokes.length && strokes[next].start <= t) {
      const s = strokes[next++];
      if (active) { await page.mouse.up(); active = null; }
      await page.evaluate((key) => window.__living.select(key), s.brush);
      if (!s.pts) {
        const woke = await page.evaluate(([key, x, y]) => window.__living.wake(key, x, y) && window.__living.info().objects.length,
          [s.brush, s.path[1] * geo.W, s.path[2] * geo.H]);
        if (!woke) throw Error(`${work.id}: tapping ${s.brush} at ${s.path[1]}, ${s.path[2]} woke nothing`);
        console.log(`${work.id}: ${s.brush} awake (${woke} object${woke > 1 ? "s" : ""})`);
      } else {
        const [x, y] = client(s.pts[0]);
        await page.mouse.move(x, y);
        await page.mouse.down();
        active = { ...s, x, y, warp: WARPS.has(s.brush) };
      }
      console.log(`${work.id} ${t.toFixed(2)}s ${s.brush} on "${s.at}"`);
    }
    if (active) {
      // The page feeds a point on every pointer move however short, so move only once the brush has gone a
      // step (the page's own spacing: 9 px for marks, 16 for warps), as a hand would.
      const p = Math.min(1, (t - active.start) / active.dur);
      const [x, y] = client(along(active.pts, p));
      const moved = Math.hypot(x - active.x, y - active.y) / geo.sc;
      if (moved >= (active.warp ? 16 : 9) || (p >= 1 && moved >= 1)) {
        await page.mouse.move(x, y);
        active.x = x; active.y = y;
      }
      if (p >= 1) { await page.mouse.up(); active = null; }
    }
    ffmpeg.stdin.write(await grab(T0 + t - strokes[0].start));
  }
  if (active) await page.mouse.up();
  ffmpeg.stdin.end();
  await new Promise((resolve, reject) => ffmpeg.on("close", (code) => (code ? reject(new Error(`ffmpeg ${code}`)) : resolve())));
  writeFileSync(join(DIR, `living-${work.id}.json`), JSON.stringify({ firstFrame: first, frames: last - first, T0 }, null, 1));
  console.log(`${work.id}: ${last - first} frames → ${out}`);
}
await browser.close();
