// Screenshots of the real product (https://lang.lucasacademy.org) for the Language Bridge films.
//
// Drives Remotion's bundled chrome-headless-shell over the DevTools protocol
// (Node 22 has WebSocket built in, so nothing to install). Every state starts
// from a fresh page with storage cleared, at 1440x900 CSS px and 2x pixels.
//
//   node scripts/reciprocal-doors-capture-product.mjs
import {spawn} from 'node:child_process';
import {mkdirSync, mkdtempSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const out = resolve(root, 'public/images/reciprocal-doors/product');
const chrome = resolve(
  root,
  'node_modules/.remotion/chrome-headless-shell/mac-arm64/chrome-headless-shell-mac-arm64/chrome-headless-shell',
);
const URL = 'https://lang.lucasacademy.org/';
const PORT = 9337;
const VIEW = {width: 1440, height: 900, deviceScaleFactor: 2, mobile: false};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Each state: a name and the page script that puts the product into it.
const clickText = (scope, text) =>
  `[...${scope}.querySelectorAll('button')].find((b) => (b.innerText || '').trim().startsWith(${JSON.stringify(text)}))?.click()`;
// Opening the study dialog is animated: wait until it is really there before using it.
const openStudy = (label) => `${clickText('document', label)}; for (let i = 0; i < 100 && !document.querySelector('dialog[open]'); i++) await new Promise((r) => setTimeout(r, 100)); await new Promise((r) => setTimeout(r, 600)); const d = document.querySelector('dialog[open]'); if (!d) throw new Error('study dialog did not open');`;
const scrollTo = (text) => `[...d.querySelectorAll('*')].find((e) => e.children.length === 0 && e.textContent.trim().toLowerCase() === ${JSON.stringify(text.toLowerCase())})?.scrollIntoView({block: 'start'})`;
const tick = (label) => `[...document.querySelectorAll('main input[type=checkbox]')].find((i) => (i.closest('label')?.innerText || i.parentElement?.innerText || '').includes(${JSON.stringify(label)}))?.click()`;
const tapWord = (match) => `[...document.querySelectorAll('main button')].find((b) => ${match})?.click()`;
const openTools = `document.querySelectorAll('details').forEach((d) => (d.open = true))`;
// [name, interface language, page script]. The product remembers the order in
// localStorage 'lucas-lang.first'; English-first also turns the interface English.
const STATES = [
  ['home', 'zh', ''],
  ['pinyin', 'zh', tick('拼音')],
  ['tools', 'zh', openTools],
  ['english-first', 'zh', clickText('document', '中文在前')],
  ['word', 'zh', tapWord(`(b.getAttribute('aria-label') || '').startsWith('爱，')`)],
  ['study', 'zh', openStudy('逐句学')],
  ['study-split', 'zh', `${openStudy('逐句学')} ${clickText('d', '拆成短句')}`],
  ['study-talk', 'zh', `${openStudy('逐句学')} ${scrollTo('说说你会怎么做')}`],
  ['study-switch', 'zh', `${openStudy('逐句学')} ${clickText('d', '换你来教')}; await new Promise((r) => setTimeout(r, 300)); ${scrollTo('换个角色，再试一次')}`],
  ['en-home', 'en', ''],
  ['en-pinyin', 'en', tick('Pinyin')],
  ['en-tools', 'en', openTools],
  ['en-word', 'en', tapWord(`b.innerText.trim() === 'love'`)],
  ['en-study', 'en', openStudy('Study verse by verse')],
  ['en-study-switch', 'en', `${openStudy('Study verse by verse')} ${clickText('d', 'Your turn to teach')}; await new Promise((r) => setTimeout(r, 300)); ${scrollTo('Switch roles and try again')}`],
];

// Where things are on screen (CSS px; the PNG is 2x), so the film can point at them.
const MEASURE = `
  const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); return r.width ? {x: r.x, y: r.y, w: r.width, h: r.height} : null; };
  const smallest = (text, root = document) => { const want = text.toLowerCase(); let best = null; for (const e of root.querySelectorAll('*')) { const t = (e.textContent || '').toLowerCase(); if (t.includes(want) && e.getClientRects().length && (!best || t.length < best.textContent.length)) best = e; } return best; };
  // Only buttons on screen: the page keeps hidden copies (e.g. the other language's switch).
  const button = (label, root = document) => [...root.querySelectorAll('button')].find((b) => b.getClientRects().length && b.getBoundingClientRect().width && (b.getAttribute('aria-label') || b.innerText || '').trim().startsWith(label));
  const either = (find, ...labels) => labels.map((l) => find(l)).find(Boolean);
  const dialog = document.querySelector('dialog[open]');
  const panel = document.querySelector('aside.word-panel');
  const main = document.querySelector('main');
  // A sentence is a row of word buttons: climb from its first word to the whole line.
  const line = (word) => { let e = word; while (e && e.getBoundingClientRect().width < 600) e = e.parentElement; return e; };
  const inDialog = (fn) => (dialog ? fn(dialog) : null);
  return {
    title: box(main.querySelector('h1')),
    toolbar: box(either(button, '逐句学', 'Study verse by verse')?.parentElement),
    studyButton: box(either(button, '逐句学', 'Study verse by verse')),
    listenButton: box(either(button, '听这一小段', 'Listen to this part')),
    pinyinToggle: box(either((l) => smallest(l, main), '拼音', 'Pinyin')),
    dictationToggle: box(either(smallest, '默写先读的语言', 'Dictation: hide')),
    moreTools: box(either(smallest, '更多工具', 'More tools')),
    toolsPopover: box(main.querySelector('details[open] > :not(summary)')),
    langToggle: box(button('中文在前') || button('English first')),
    playZh: box(either(button, '读第1节中文', 'Read verse 1 in Chinese')),
    playEn: box(either(button, '读第1节English', 'Read verse 1 in English')),
    verseZh: box(line(button('我，wǒ', main))),
    verseEn: box(line([...main.querySelectorAll('button')].find((b) => b.innerText.trim() === 'If'))),
    sidebarQuote: box(either(smallest, '你会的词，可以教给我', 'Teach me the words you know')),
    wordPanel: box(panel && getComputedStyle(panel).display !== 'none' ? panel : null),
    wordPicture: box(panel?.querySelector('img')),
    wordListen: box(panel && (button('听这个词', panel) || button('Hear the word', panel))),
    dialog: box(dialog && [dialog, ...dialog.querySelectorAll(':scope > *, :scope > * > *')].filter((e) => e.getClientRects().length).sort((a, b) => { const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect(); return rb.width * Math.min(rb.height, innerHeight) - ra.width * Math.min(ra.height, innerHeight); }).find((e) => e.getBoundingClientRect().width < innerWidth * 0.95)),
    studyListen: box(inDialog((d) => button('听这一句', d) || button('Hear this verse', d))),
    talkCard: box(inDialog((d) => (smallest('说说你会怎么做', d) || smallest('What would you do?', d))?.parentElement)),
    switchBlock: box(inDialog((d) => (smallest('换个角色，再试一次', d) || smallest('Switch roles and try again', d))?.parentElement)),
    switchButton: box(inDialog((d) => button('换你来教', d) || button('Your turn to teach', d))),
  };
`;
const regions = {};

mkdirSync(out, {recursive: true});
const profile = mkdtempSync(join(tmpdir(), 'rd-capture-'));
const browser = spawn(chrome, [`--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, '--hide-scrollbars', '--no-first-run', 'about:blank'], {stdio: 'ignore'});

try {
  let targets;
  for (let i = 0; i < 50 && !targets; i++) {
    await sleep(200);
    targets = await fetch(`http://127.0.0.1:${PORT}/json/list`).then((r) => r.json()).catch(() => undefined);
  }
  const page = targets.find((t) => t.type === 'page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, {once: true}));
  let next = 0;
  const waiting = new Map();
  ws.addEventListener('message', (event) => {
    const message = JSON.parse(event.data);
    const done = waiting.get(message.id);
    if (!done) return;
    waiting.delete(message.id);
    message.error ? done.reject(new Error(message.error.message)) : done.resolve(message.result);
  });
  const send = (method, params = {}) =>
    new Promise((resolve, reject) => {
      const id = ++next;
      waiting.set(id, {resolve, reject});
      ws.send(JSON.stringify({id, method, params}));
    });
  const run = async (expression) => {
    const {result, exceptionDetails} = await send('Runtime.evaluate', {expression: `(async () => { ${expression} })()`, awaitPromise: true, returnByValue: true});
    if (exceptionDetails) throw new Error(exceptionDetails.exception?.description ?? exceptionDetails.text);
    return result.value;
  };
  const settle = () => run(`await document.fonts.ready; await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))); await new Promise((r) => setTimeout(r, 700));`);

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', VIEW);
  for (const [name, language, action] of STATES) {
    await send('Page.navigate', {url: URL});
    await sleep(400);
    for (let i = 0; i < 50 && (await run('return document.readyState').catch(() => '')) !== 'complete'; i++) await sleep(200);
    await run(`localStorage.clear(); sessionStorage.clear(); ${language === 'en' ? `localStorage.setItem('lucas-lang.first', '"en"');` : ''}`);
    await send('Page.reload', {ignoreCache: true});
    await sleep(400);
    for (let i = 0; i < 50 && (await run('return document.readyState').catch(() => '')) !== 'complete'; i++) await sleep(200);
    await settle();
    if (action) await run(action);
    await settle();
    const {data} = await send('Page.captureScreenshot', {format: 'png'});
    writeFileSync(join(out, `${name}.png`), Buffer.from(data, 'base64'));
    regions[name] = Object.fromEntries(Object.entries(await run(MEASURE)).filter(([, v]) => v));
    console.log(`captured ${name}: ${Object.keys(regions[name]).join(', ')}`);
  }
  ws.close();
  writeFileSync(join(out, 'regions.json'), `${JSON.stringify({scale: VIEW.deviceScaleFactor, viewport: {width: VIEW.width, height: VIEW.height}, regions}, null, 2)}\n`);
} finally {
  browser.kill();
}
