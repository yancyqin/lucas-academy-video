/** 好奇新世界 · 第 1 期 (001–003): the live product recordings. See docs/weekly/001/zh-edit.md for where each is used.
 *   node scripts/weekly/capture.cjs scripts/weekly/001/captures.cjs [name ...]                 the Chinese film
 *   WEEKLY_LANG=en node scripts/weekly/capture.cjs scripts/weekly/001/captures.cjs [name ...]  the English film
 * Each film shows the products in its own language and with its own content (owner, 2026-10-20): English pages,
 * the WEB verse, an English sentence. Pages that are English already (Newton, the Python homework, the museum walk)
 * are recorded once, in captures/zh, and both films use them. Mark names are the same in both languages.
 */
const LANG = process.env.WEEKLY_LANG || 'zh';
const EN = LANG === 'en';
const HD = {width: 1280, height: 720};  // CSS px; scale 1.5 gives 1920×1080 frames with UI big enough to read on YouTube
const WEEKLY = n => `https://lucasacademy.org/weekly/?edition=${n}&lang=${LANG}`;
// A demo shot shows the demo alone: the site header and the Weekly toolbar are hidden for it.
const NO_CHROME = '.la-chrome, .weekly-toolbar, .brainstorm-weekly-toolbar { display: none !important; }';
const centre = sel => async page => {
  await page.locator(sel).first().evaluate(e => e.scrollIntoView({block: 'center'}));
  await page.waitForTimeout(1500);
};
const pick = (sel, text) => async r => r.click(r.page.locator(sel, {hasText: text}).first());
// 诗篇 119:105 (CUV / WEB, both public domain): the sentence-game example
const VERSE = EN ? 'Your word is a lamp to my feet, and a light for my path.' : '你的话是我脚前的灯，是我路上的光。';
const plain = t => t.replace(/[^\p{L}\p{N}]/gu, '').toLowerCase();  // letters only, for matching tiles to the verse
/** The sentence playground (bible.lucasacademy.org/sentence): type the verse, pick a game, play it through.
 * Each step clicks the enabled tile whose text continues the verse (longest match), so one rule plays both games. */
function sentenceGame(mode) {
  const letters = plain(VERSE);
  return {
    url: 'https://bible.lucasacademy.org/sentence',
    viewport: HD, scale: 1.5,
    css: '.sp-intro, .sp-back, .sp-notice { display: none !important; }',  // the game card fills the frame
    async run(r) {
      await r.waitFor('textarea');
      if (EN && !/中文/.test(await r.page.locator('button.sp-language').textContent())) {
        await r.click('button.sp-language');  // the playground's own interface switch
      }
      await r.hold(1.2);
      await r.type('textarea', VERSE, EN ? 14 : 7);
      await r.hold(0.8);
      await r.click(r.page.locator('label', {has: r.page.locator(`input[value=${mode}]`)}).first());
      await r.hold(0.8);
      await r.click('button.sp-primary');
      r.mark('memorise');
      await r.hold(3.2);
      let done = 0;
      for (let step = 0; step < 60 && done < letters.length; step++) {
        const start = r.page.locator('button.sp-primary', {hasText: /开始|下一段|继续|start|next|continue|ready|let's play/i});
        if (await start.first().isVisible().catch(() => false)) { await r.click(start.first()); r.mark(`segment@${done}`); await r.hold(1.2); continue; }
        const tiles = (await r.page.$$eval('.sp-tile:not([disabled])', ts => ts.map((t, i) => [i, t.textContent]))).map(([i, t]) => [i, plain(t)]);
        const rest = letters.slice(done);
        const best = tiles.filter(([, t]) => t && rest.startsWith(t)).sort((a, b) => b[1].length - a[1].length)[0];
        if (!best) { await r.hold(0.6); continue; }
        await r.click(r.page.locator('.sp-tile:not([disabled])').nth(best[0]), {after: mode === 'words' ? 0.6 : EN ? 0.12 : 0.3});
        done += best[1].length;
      }
      r.mark('done');
      await r.hold(4);
    },
  };
}

/** Put a verse back together: each step clicks the tile whose text continues it. */
async function solveVerse(r, tileSel, verse, gap = 0.45) {
  const want = plain(verse);
  let done = 0;
  for (let step = 0; step < 30 && done < want.length; step++) {
    const tiles = (await r.page.$$eval(`${tileSel}:not([disabled])`, ts => ts.map((t, i) => [i, t.textContent]))).map(([i, t]) => [i, plain(t)]);
    const best = tiles.filter(([, t]) => t && want.slice(done).startsWith(t)).sort((a, b) => b[1].length - a[1].length)[0];
    if (!best) break;
    await r.click(r.page.locator(`${tileSel}:not([disabled])`).nth(best[0]), {after: gap});
    done += best[1].length;
  }
}
const JOHN316 = EN
  ? 'For God so loved the world, that he gave his only born Son, that whoever believes in him should not perish, but have eternal life.'
  : '「　神爱世人，甚至将他的独生子赐给[他们]，叫一切信他的，不致灭亡，反得永生。';

module.exports = [
  {
    name: 'avi',
    url: `https://is.lucasacademy.org/avi/?lang=${LANG}`,
    viewport: HD, scale: 1.5,
    async run(r) {
      await r.waitFor(() => !document.querySelector('.motions button[disabled]'));
      await r.hold(1.5);
      r.mark('colour');
      for (const c of ['#f6b6bc', '#aad6ec', '#c9b9e8', '#fff1d9']) { await r.click(`.colors button[data-color="${c}"]`); await r.hold(1.1); }
      r.mark('walk');
      await r.click('button[data-clip="Walk_Loop"]'); await r.hold(3.2);
      r.mark('float');
      await r.click('button[data-clip="Float_Loop"]'); await r.hold(3.6);
      r.mark('wave');
      await r.click('button[data-clip="Wave_Loop"]'); await r.hold(2.6);
      r.mark('back');
      await r.click('button[data-angle="back"]'); await r.hold(2.6);
      await r.click('button[data-angle="front"]'); await r.hold(2.0);
    },
  },
  {
    name: 'comeback',  // Weekly 002's in-page demo: two bots, the side more than 5 behind brings a piece back
    url: WEEKLY('002'),
    viewport: HD, scale: 1.5, css: NO_CHROME, prepare: centre('[data-chess-demo]'),
    async run(r) {
      await r.hold(1.2);
      await pick('[data-chess-demo] button', /播放|Play/)(r);
      r.mark('play');
      await r.waitFor('[data-chess-demo] .cd-option', 120000);
      r.mark('pause');
      await r.hold(3.0);
      await r.click('[data-chess-demo] .cd-option');
      r.mark('chosen');
      await r.hold(1.6);
      await r.click('[data-chess-demo] .comeback-target');
      r.mark('revived');
      await r.hold(10);
    },
  },
  {
    name: 'underground',  // Weekly 003's in-page demo at 75%: rocks fall on the side that is ahead
    url: WEEKLY('003'),
    viewport: HD, scale: 1.5, css: NO_CHROME, prepare: centre('[data-underground-demo]'),
    async run(r) {
      await r.waitFor('[data-underground-demo] .cd-play');
      await r.hold(1.2);
      await r.click('[data-underground-demo] .cd-play');
      r.mark('play');
      const rocks = () => r.page.evaluate(() => { const m = document.querySelector('[data-underground-demo]').innerText.match(/已落石 (\d+) 次|Rocks fallen: (\d+)/); return m ? +(m[1] || m[2]) : 0; });
      let seen = 0;
      for (let t = 0; t < 75 && seen < 4; t += 0.25) {
        const n = await rocks();
        if (n > seen) { seen = n; r.mark(`rock${n}`); }
        await r.hold(0.25);
      }
      await r.hold(4);
    },
  },
  {
    name: 'atelier',  // Weekly 001's five 3D studies, in the standalone studio the page links to
    url: `https://lucasacademy.org/weekly/atelier/?model=helios&lang=${LANG}`,
    viewport: HD, scale: 1.5,
    async run(r) {
      await r.waitFor('.model-card');
      await r.hold(2.5);
      for (let i = 0; i < 5; i++) {  // the five studies, in the studio's order
        if (i) { await r.click(r.page.locator('.model-card').nth(i)); await r.hold(1.8); }
        r.mark(`study${i + 1}`);
        await r.hold(2.2);
        await r.click('.action-button');  // each study's own action: freeze the orbits, start the gait, open the core…
        await r.hold(4.5);
      }
    },
  },
  {
    name: 'pieces',  // Weekly 002: the three Eclipse Court pieces in the page's 3D viewer
    url: WEEKLY('002') + '#chess-models',
    viewport: HD, scale: 1.5, css: NO_CHROME, prepare: centre('#chess-models [data-chess-model-launch]'),
    async run(r) {
      await r.hold(1.0);
      await r.click('#chess-models [data-chess-model-launch]');
      r.mark('launch');
      await r.hold(6);
      await r.page.locator('#chess-models').evaluate(e => e.scrollIntoView({block: 'start'}));
      await r.hold(8);
    },
  },
  {
    name: 'bible-sequence',  // Bible Sequence: memorise John 3:16, then put the phrases back in order
    url: `https://bible.lucasacademy.org/?passage=JHN.3.16&translation=${EN ? 'WEB' : 'CUV'}`,
    viewport: HD, scale: 1.5,
    async run(r) {
      await r.waitFor('button.btn--primary');
      await r.hold(7);
      r.mark('recall');
      await r.click('button.btn--primary');
      await r.hold(1.8);
      await solveVerse(r, '.bank .tile', JOHN316, 0.9);
      r.mark('done');
      await r.hold(5);
    },
  },
  {name: 'sentence-chars', ...sentenceGame('characters')},  // 句子游乐场 · 接字, with Psalm 119:105
  {name: 'sentence-words', ...sentenceGame('words')},       // 句子游乐场 · 接词
  {
    name: 'lang-class',  // Language Bridge: the classroom's weeks, then week 3's lesson, Weekly Journal No. 1
    url: 'https://lang.lucasacademy.org/class',
    viewport: HD, scale: 1.5,
    async run(r) {
      await r.waitFor('button.order-button');
      await r.hold(1.5);
      for (const w of ['Week 1', 'Week 2', 'Week 3']) { await r.click(r.page.locator('button', {hasText: w}).first()); await r.hold(1.6); }
      r.mark('journal');
      await r.click(r.page.locator('a, button', {hasText: /Start the lesson|开始/}).first());
      await r.page.waitForLoadState('networkidle').catch(() => {});
      await r.hold(2.5);
      await r.scroll(r.page.locator('.line-play').first().evaluate(e => e.getBoundingClientRect().top + scrollY - 200).catch(() => 600), 1.6);
      await r.hold(1.5);
      if (EN) {  // the English film reveals the English lines: "Think first, then tap to see the English"
        for (let i = 0; i < 2; i++) {
          await r.click(r.page.getByText(/Think first, then tap to see the English/).first());
          await r.hold(2.2);
        }
      }
      r.mark('word');
      await r.click(r.page.locator('button.word', {hasText: '青蛙'}).first());
      await r.hold(3.5);
      await r.scroll(r.page.locator('button.word', {hasText: '章节'}).first().evaluate(e => e.getBoundingClientRect().top + scrollY - 260).catch(() => 1200), 1.8);
      await r.hold(3);
    },
  },
  {
    name: 'glitch-arcade',  // The Glitch Arcade, cabinet 04 「身体是一个列表」: learn, then fix hits() — both list[0] become part
    url: `https://lucasacademy.org/app/?level=04-the-body-is-a-list&lang=${LANG}`,
    viewport: HD, scale: 1.5,
    async run(r) {
      await r.waitFor('button.action');
      await r.hold(3);
      await r.click(r.page.locator('button.action', {hasText: /看这台街机运行|Watch the cabinet/}));
      r.mark('demo');
      await r.hold(6);
      await r.click(r.page.locator('button', {hasText: /^修复$|^modify$/i}).first());
      r.mark('fix');
      await r.hold(2);
      await r.scroll(r.page.locator('.cm-editor').first().evaluate(e => e.getBoundingClientRect().top + scrollY - 220), 1.2);
      await r.hold(2.5);
      for (let k = 0; k < 2; k++) {
        // The edge of the k-th remaining "list[0]" in the loop body: click just before it, select it, type part.
        const box = await r.page.evaluate(() => {
          // CodeMirror splits a line into token spans: find "list[0]" in the line's text, then walk the text nodes
          // to the one holding its first character.
          const line = [...document.querySelectorAll('.cm-editor .cm-line')].find(l => l.textContent.includes('if (') && l.textContent.includes('list[0]'));
          if (!line) return null;
          let at = line.textContent.indexOf('list[0]');
          const walker = document.createTreeWalker(line, NodeFilter.SHOW_TEXT);
          for (let n; (n = walker.nextNode());) {
            if (at < n.textContent.length) {
              const range = document.createRange(); range.setStart(n, at); range.setEnd(n, at + 1);
              const b = range.getBoundingClientRect();
              return [b.left + 1, b.top + b.height / 2];
            }
            at -= n.textContent.length;
          }
          return null;
        });
        if (!box) break;
        await r.click(box, {after: 0.25});
        await r.page.keyboard.down('Shift');
        for (let i = 0; i < 7; i++) { await r.page.keyboard.press('ArrowRight'); await r.hold(0.05); }
        await r.page.keyboard.up('Shift');
        await r.hold(0.4);
        for (const ch of 'part') { await r.page.keyboard.type(ch); await r.hold(0.12); }
        await r.hold(0.8);
      }
      r.mark('check');
      await r.click(r.page.locator('button.action', {hasText: /运行检查|check/i}));
      await r.hold(4.5);
      r.mark('play');
      await r.click(r.page.locator('button.action', {hasText: /试玩|play/i}).first());
      await r.hold(7);
    },
  },
  {
    name: 'score-homework',  // Coding Class, Python homework 01: score starts at zero. Run only; never submit.
    url: 'https://lucasacademy.org/programs/coding-class/score-homework',
    viewport: HD, scale: 1.5,
    async run(r) {
      await r.waitFor('textarea.code-editor');
      await r.hold(2);
      await r.scroll('textarea.code-editor', 1.2);
      await r.hold(1.2);
      const lines = [['# TODO 1', 'score = 0'], ['# TODO 2', 'score = score + 10']];
      for (const [todo, code] of lines) {
        const at = await r.page.locator('textarea.code-editor').evaluate((t, todo) => {
          const i = t.value.indexOf(todo), eol = t.value.indexOf('\n', i) + 1;
          const lineNo = t.value.slice(0, eol).split('\n').length - 1;
          const cs = getComputedStyle(t), lh = parseFloat(cs.lineHeight) || 22, b = t.getBoundingClientRect();
          return {eol, x: b.left + parseFloat(cs.paddingLeft) + 8, y: b.top + parseFloat(cs.paddingTop) + lh * (lineNo + 0.5) - t.scrollTop};
        }, todo);
        await r.glide([at.x, at.y]);
        await r.page.locator('textarea.code-editor').evaluate((t, eol) => { t.focus(); t.setSelectionRange(eol, eol); }, at.eol);
        await r.hold(0.3);
        for (const ch of code) { await r.page.keyboard.type(ch); await r.hold(0.09); }
        await r.hold(0.8);
      }
      r.mark('run');
      await r.click('button.run-button');
      await r.waitFor(() => /\b10\b/.test(document.querySelector('pre:last-of-type')?.textContent || document.body.innerText), 60000).catch(() => {});
      await r.hold(1);
      await r.scroll(r.page.locator('text=Console').first().evaluate(e => e.getBoundingClientRect().top + scrollY - 200).catch(() => 900), 1.2);
      await r.hold(4);
    },
  },
  {
    name: 'newton',  // Physics: play Isaac Newton in 1666 with an AI partner that only knows what was known then
    url: 'https://lucasacademy.org/human-led-ai-collaboration/coach/?demo=newton-showcase',
    viewport: HD, scale: 1.5,
    async run(r) {
      await r.hold(6);
      r.mark('story');
      await r.click([640, 560]);
      await r.hold(5);
      for (let i = 0; i < 3; i++) {
        const readOn = r.page.locator('button', {hasText: /READ ON/i}).first();
        if (await readOn.isVisible().catch(() => false)) await r.click(readOn); else await r.page.keyboard.press('Space');
        await r.hold(4.5);
      }
      r.mark('next');
      for (let i = 0; i < 2; i++) {
        const next = r.page.locator('button', {hasText: '→'}).last();
        if (await next.isVisible().catch(() => false)) await r.click(next); else await r.page.keyboard.press('ArrowRight');
        await r.hold(5);
      }
    },
  },
];
