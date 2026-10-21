/** Still pictures of web pages for 好奇新世界: one 1920×1080 screenshot per entry (1280×720 CSS px at 1.5×).
 *
 *   node scripts/weekly/stills.cjs scripts/weekly/001/stills.cjs [name ...]
 *
 * A stills file exports [{name, url, anchor?, css?, wait?, scroll?}]: `anchor` scrolls that element to the top
 * (below the sticky header, as the page's own anchor links do), `scroll` adds pixels after it.
 * Output: public/weekly/<ep>/stills/<lang>/<name>.png
 */
const {chromium} = require('/Users/yqin/repo/ai-testing/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '../..');
// The film the pictures are for: WEEKLY_LANG=en records the English pages (the spec file reads it too).
const LANG = process.env.WEEKLY_LANG || 'zh';

async function main() {
  const [specFile, ...only] = process.argv.slice(2);
  const ep = path.basename(path.dirname(path.resolve(specFile)));
  const specs = require(path.resolve(specFile)).filter(s => !only.length || only.includes(s.name));
  const out = path.join(ROOT, 'public/weekly', ep, 'stills', LANG);
  fs.mkdirSync(out, {recursive: true});
  const browser = await chromium.launch({channel: 'chrome', headless: true, args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist']});
  const context = await browser.newContext({viewport: {width: 1280, height: 720}, deviceScaleFactor: 1.5, locale: LANG === 'en' ? 'en-US' : 'zh-CN'});
  const page = await context.newPage();
  let loaded = null;
  for (const s of specs) {
    console.log(`… ${s.name}`);
    if (loaded !== s.url) {
      await page.goto(s.url, {waitUntil: 'networkidle', timeout: 90000}).catch(e => console.warn('  goto:', e.message.split('\n')[0]));
      await page.waitForTimeout(s.wait ?? 2500);
      loaded = s.url;
    }
    await page.addStyleTag({content: 'html, body { scroll-behavior: auto !important; }' + (s.css || '')});
    // Scroll twice: content above the anchor (lazy pictures, demos) can still change height after the first jump.
    for (let pass = 0; pass < 2; pass++) {
      if (s.anchor) {
        await page.locator(s.anchor).first().evaluate((e, extra) => {
          // Only what really sticks to the top (the footer is .la-chrome too).
          const sticky = Math.max(0, ...[...document.querySelectorAll('.site-header, .la-chrome, [class*="toolbar"]')]
            .filter(el => ['sticky', 'fixed'].includes(getComputedStyle(el).position) && el.getBoundingClientRect().top < 200)
            .map(el => el.getBoundingClientRect().bottom));
          window.scrollTo({top: e.getBoundingClientRect().top + scrollY - sticky + (extra || 0), behavior: 'instant'});
        }, s.scroll ?? 0);
      } else await page.evaluate(() => window.scrollTo({top: 0, behavior: 'instant'}));
      await page.waitForTimeout(pass ? 500 : (s.settle ?? 1200));
    }
    // Pictures in view finish decoding first (bounded: a lazy image that never starts would wait forever).
    await page.evaluate(() => Promise.race([new Promise(r => setTimeout(r, 4000)),
      Promise.all([...document.images].filter(i => i.getBoundingClientRect().bottom > 0 && i.getBoundingClientRect().top < innerHeight).map(i => i.decode().catch(() => {})))]));
    if (s.anchor) console.log('   at', await page.locator(s.anchor).first().evaluate(e => [Math.round(scrollY), Math.round(e.getBoundingClientRect().top)]));
    const file = path.join(out, `${s.name}.png`);
    await page.screenshot({path: file});
    console.log(`  ${s.name} <- ${s.url}${s.anchor ? ' ' + s.anchor : ''}`);
  }
  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
