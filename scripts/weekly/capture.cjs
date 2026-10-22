/** Record live product pages for 好奇新世界 (the weekly film), in real time.
 *
 * Chrome's own screencast streams every repaint with its timestamp, so CSS transitions, WebGL, workers and
 * timers all run at their real speed; the frames are then resampled to constant 30 fps. A drawn cursor glides
 * between targets and a ripple marks each click (both live in the page, so they are in the frames).
 *
 *   node scripts/weekly/capture.cjs scripts/weekly/001/captures.cjs [name ...]
 *
 * A captures file exports an array of {name, url, viewport, scale, seed, css, run: async (r) => {...}}.
 * `r` is the recorder below: r.page, r.hold(sec), r.glide(target, sec), r.click(target), r.type(target, text),
 * r.scroll(to, sec), r.mark(name), r.waitFor(fn | selector). Output: public/weekly/<ep>/captures/<lang>/<name>.mp4
 * plus <name>.json (duration and the marks, in seconds from the start of the video).
 */
const {chromium} = require('/Users/yqin/repo/ai-testing/node_modules/playwright');
const {spawnSync} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '../..');
// The film the pictures are for: WEEKLY_LANG=en records the English pages (the spec file reads it too).
const LANG = process.env.WEEKLY_LANG || 'zh';
const FPS = 30;
const CURSOR = `<svg xmlns="http://www.w3.org/2000/svg" width="30" height="39" viewBox="0 0 26 34"><path d="M2 2 L2 27 L8.5 21 L13 31 L17.5 29 L13 19.5 L22 19.5 Z" fill="#1f2b26" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>`;
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function installCursor(page, x, y) {
  await page.evaluate(([svg, x, y]) => {
    if (document.getElementById('cap-cursor')) return;
    const style = document.createElement('style');
    style.textContent = `#cap-cursor{position:fixed;left:0;top:0;z-index:2147483647;pointer-events:none;transition-property:transform;transition-timing-function:cubic-bezier(.45,0,.25,1)}
      #cap-ripple{position:fixed;left:0;top:0;width:52px;height:52px;margin:-26px 0 0 -26px;border-radius:50%;border:3px solid #f2a541;z-index:2147483646;pointer-events:none;opacity:0}
      #cap-ripple.go{animation:cap-ripple .55s ease-out forwards}
      @keyframes cap-ripple{from{opacity:.85;scale:.3}to{opacity:0;scale:1.5}}`;
    const c = document.createElement('div');
    c.id = 'cap-cursor';
    c.innerHTML = svg;
    c.style.transform = `translate(${x - 2}px, ${y - 2}px)`;
    const r = document.createElement('div');
    r.id = 'cap-ripple';
    document.documentElement.append(style, r, c);
  }, [CURSOR, x, y]);
}

class Recorder {
  constructor(page, cdp, spec) {
    Object.assign(this, {page, cdp, spec, frames: [], marks: {}, x: spec.viewport.width * 0.82, y: spec.viewport.height * 0.86});
  }

  async start(dir) {
    this.dir = dir;
    this.cdp.on('Page.screencastFrame', async ({data, metadata, sessionId}) => {
      const file = path.join(dir, String(this.frames.length).padStart(6, '0') + '.jpg');
      this.frames.push({file, t: metadata.timestamp});
      fs.writeFile(file, Buffer.from(data, 'base64'), () => {});
      await this.cdp.send('Page.screencastFrameAck', {sessionId}).catch(() => {});
    });
    const {width, height} = this.spec.viewport;
    const scale = this.spec.scale ?? 1;
    await this.cdp.send('Page.startScreencast', {format: 'jpeg', quality: 92, maxWidth: Math.round(width * scale), maxHeight: Math.round(height * scale), everyNthFrame: 1});
    // The first frame's timestamp is the video's zero; nudge a repaint so it comes now.
    await installCursor(this.page, this.x, this.y);
    await sleep(120);
    this.t0 = this.frames[0]?.t ?? Date.now() / 1000;
    this.wall0 = Date.now() / 1000;
  }

  now() { return Date.now() / 1000 - this.wall0; }
  mark(name) { this.marks[name] = +this.now().toFixed(3); }
  async hold(sec) { await sleep(sec * 1000); }

  async point(target) {
    if (Array.isArray(target)) return target;
    const loc = typeof target === 'string' ? this.page.locator(target).first() : target;
    await loc.waitFor({state: 'visible', timeout: 30000});
    await loc.scrollIntoViewIfNeeded().catch(() => {});
    const b = await loc.boundingBox();
    return [b.x + b.width / 2, b.y + b.height * 0.55];
  }

  async glide(target, sec) {
    const [x, y] = await this.point(target);
    sec ??= Math.min(1.1, 0.45 + Math.hypot(x - this.x, y - this.y) / 1000);
    await installCursor(this.page, this.x, this.y);  // again after a navigation, which drops it
    await this.page.evaluate(([x, y, sec]) => {
      const c = document.getElementById('cap-cursor');
      c.style.transitionDuration = sec + 's';
      c.style.transform = `translate(${x - 2}px, ${y - 2}px)`;
    }, [x, y, sec]);
    await this.page.mouse.move(x, y, {steps: Math.max(2, Math.round(sec * 20))});
    await sleep(sec * 1000 + 40);
    this.x = x; this.y = y;
  }

  async click(target, {glide = true, after = 0.35} = {}) {
    if (glide) await this.glide(target);
    await sleep(120);
    await this.page.evaluate(([x, y]) => {
      const r = document.getElementById('cap-ripple');
      r.style.transform = `translate(${x}px, ${y}px)`;
      r.classList.remove('go'); void r.offsetWidth; r.classList.add('go');
    }, [this.x, this.y]);
    await this.page.mouse.click(this.x, this.y);
    await sleep(after * 1000);
  }

  async type(target, text, cps = 9) {
    await this.click(target);
    for (const ch of text) { await this.page.keyboard.type(ch); await sleep(1000 / cps); }
  }

  /** Ease the page to `to`: a y, a promise of one, a selector or a locator (its top, 24 px below the edge). */
  async scroll(to, sec = 1.2) {
    to = await to;
    const loc = typeof to === 'string' ? this.page.locator(to).first() : to;
    const y1 = typeof to === 'number' ? to : await loc.evaluate(e => e.getBoundingClientRect().top + scrollY - 24);
    await this.page.evaluate(([y1, ms]) => new Promise(done => {
      const y0 = scrollY, t0 = performance.now();
      const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      (function step(now) {
        const k = Math.min(1, (now - t0) / ms);
        window.scrollTo(0, y0 + (y1 - y0) * ease(k));
        k < 1 ? requestAnimationFrame(step) : done();
      })(t0);
    }), [y1, sec * 1000]);
  }

  async waitFor(what, timeout = 60000) {
    if (typeof what === 'string') return this.page.locator(what).first().waitFor({state: 'visible', timeout});
    return this.page.waitForFunction(what, null, {timeout, polling: 100});
  }

  async stop() {
    await sleep(200);
    await this.cdp.send('Page.stopScreencast');
    await sleep(300);
    return this.now();
  }
}

/** Resample the variable-rate screencast to constant 30 fps and encode. */
function encode(rec, duration, mp4) {
  const list = path.join(rec.dir, 'frames.txt');
  const f = rec.frames;
  const lines = [];
  for (let i = 0; i < f.length; i++) {
    const t = f[i].t - rec.t0;
    const next = i + 1 < f.length ? f[i + 1].t - rec.t0 : duration;
    if (next <= 0) continue;
    lines.push(`file '${f[i].file}'`, `duration ${Math.max(0.001, next - Math.max(0, t)).toFixed(4)}`);
  }
  lines.push(`file '${f[f.length - 1].file}'`);
  fs.writeFileSync(list, lines.join('\n') + '\n');
  const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list,
    '-vf', `fps=${FPS},scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p`, '-c:v', 'libx264', '-preset', 'slow', '-crf', '16',
    '-movflags', '+faststart', '-t', duration.toFixed(3), mp4], {stdio: 'inherit'});
  if (r.status) throw Error(`ffmpeg failed for ${mp4}`);
}

async function main() {
  const [specFile, ...only] = process.argv.slice(2);
  if (!specFile) throw Error('usage: node scripts/weekly/capture.cjs scripts/weekly/<ep>/captures.cjs [name ...]');
  const ep = path.basename(path.dirname(path.resolve(specFile)));
  const specs = require(path.resolve(specFile)).filter(s => !only.length || only.includes(s.name));
  const outDir = path.join(ROOT, 'public/weekly', ep, 'captures', LANG);
  fs.mkdirSync(outDir, {recursive: true});
  for (const spec of specs) {
    // The screencast captures the real window, not Playwright's emulated viewport: size the window itself (its
    // frame adds ~87 px of height in new headless) and set the pixel ratio with a flag. Checked and corrected below.
    const {width, height} = spec.viewport;
    const browser = await chromium.launch({channel: 'chrome', headless: true, args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist',
      '--autoplay-policy=no-user-gesture-required', `--window-size=${width},${height + 87}`, `--force-device-scale-factor=${spec.scale ?? 1}`]});
    const context = await browser.newContext({viewport: null, locale: spec.locale ?? (LANG === 'en' ? 'en-US' : 'zh-CN'), colorScheme: spec.colorScheme ?? 'light'});
    if (spec.seed != null) await context.addInitScript(seed => {
      let s = seed >>> 0;  // mulberry32: the same seed gives the same game every run
      Math.random = () => { s += 0x6D2B79F5; let t = s; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
    }, spec.seed);
    if (spec.init) await context.addInitScript(spec.init);
    const page = await context.newPage();
    const cdp = await context.newCDPSession(page);
    const inner = await page.evaluate(() => [innerWidth, innerHeight]);
    if (inner[0] !== width || inner[1] !== height) {
      const {windowId, bounds} = await cdp.send('Browser.getWindowForTarget');
      await cdp.send('Browser.setWindowBounds', {windowId, bounds: {width: bounds.width + width - inner[0], height: bounds.height + height - inner[1]}});
    }
    console.log(`▶ ${spec.name}: ${spec.url}`);
    await page.goto(spec.url, {waitUntil: 'networkidle', timeout: 90000}).catch(e => console.warn('  goto:', e.message.split('\n')[0]));
    if (spec.css) await page.addStyleTag({content: spec.css});
    if (spec.prepare) await spec.prepare(page);
    const frameDir = fs.mkdtempSync(path.join(outDir, `.${spec.name}-`));
    const rec = new Recorder(page, cdp, spec);
    await rec.start(frameDir);
    await spec.run(rec);
    const duration = await rec.stop();
    const mp4 = path.join(outDir, `${spec.name}.mp4`);
    encode(rec, duration, mp4);
    fs.writeFileSync(path.join(outDir, `${spec.name}.json`), JSON.stringify({name: spec.name, url: spec.url, duration: +duration.toFixed(3), frames: rec.frames.length, marks: rec.marks}, null, 1) + '\n');
    fs.rmSync(frameDir, {recursive: true, force: true});
    console.log(`  ${duration.toFixed(1)} s, ${rec.frames.length} repaints (${(rec.frames.length / duration).toFixed(1)}/s) -> ${path.relative(ROOT, mp4)}`);
    await browser.close();
  }
}

main().catch(e => { console.error(e); process.exit(1); });
