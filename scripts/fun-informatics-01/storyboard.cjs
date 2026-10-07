// Write docs/fun-informatics-01/storyboard.md: the film as it is actually cut — every line with its
// time in both films, the picture under it (from src/videos/fun-informatics-01/shots.ts) and the card
// on top. Generated; edit the lines in zh-edit.md / en-edit.md and the pictures in shots.ts.
//
//   node scripts/fun-informatics-01/storyboard.cjs
const fs = require('fs');
const os = require('os');
const path = require('path');
const esbuild = require('esbuild');

const ROOT = path.resolve(__dirname, '../..');
const tmp = path.join(os.tmpdir(), `it01-shots-${process.pid}.cjs`);
esbuild.buildSync({entryPoints: [path.join(ROOT, 'src/videos/fun-informatics-01/shots.ts')], bundle: true, platform: 'node', format: 'cjs', outfile: tmp, logLevel: 'silent'});
const {VISUALS, CARDS, INTRO, RULER} = require(tmp);
fs.unlinkSync(tmp);

const tl = {zh: JSON.parse(fs.readFileSync(path.join(ROOT, 'public/fun-informatics-01/timeline.zh.json'))),
  en: JSON.parse(fs.readFileSync(path.join(ROOT, 'public/fun-informatics-01/timeline.en.json')))};
const edit = {zh: fs.readFileSync(path.join(ROOT, 'docs/fun-informatics-01/zh-edit.md'), 'utf8'),
  en: fs.readFileSync(path.join(ROOT, 'docs/fun-informatics-01/en-edit.md'), 'utf8')};
const lineOf = (lang, id) => {
  const m = edit[lang].match(new RegExp(`^- ${id} \\| (.+)$`, 'm'));
  return m ? m[1].replace(/<strong>(.*?)<\/strong>/g, '**$1**') : '';
};
const sections = [...edit.zh.matchAll(/^## (IT\d\d) · (.+)$/gm)].map((m) => ({id: m[1].toLowerCase(), title: m[2]}));
const cue = (lang, id) => tl[lang].cues.find((c) => c.id === id);
const mmss = (t) => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`;
const ids = tl.zh.cues.map((c) => c.id);
const range = (a, b) => ids.slice(ids.indexOf(a), ids.indexOf(b) + 1);

const FILE = {
  'bits-close.mp4': '比特墙（From Bits to Meaning，近景）', 'bits.mp4': '比特墙（远景）',
  'pixels-close.mp4': '像素墙（Pixels: From Dots to Form，近景）', 'pixels.mp4': '像素墙（远景）',
  'games-close.mp4': '游戏墙（Three Games，近景）', 'games.mp4': '游戏墙（远景）',
  'fractal-main.mp4': '分形放大（z → z² + c，每秒 ×2）', 'fractal-overdrive.mp4': '分形放大·算过头（每秒 ×8，最后碎成色块）',
  'corridor.mp4': '走廊：沿环形走廊走到「THE PIXEL SCIENCE ROOM」门口', 'entry.mp4': '进门：落点朝北，再右转看到三面画',
  'nativity.mp4': '房间中央：绕耶稣降生像全息半圈', 'readers.mp4': '比特墙展签页（按 R → Read，慢慢往下滚）',
  'transit-chamber.mp4': '太空舱',
  'circuit-board.png': 'Codex 图：电路板', 'chip-die.png': 'Codex 图：芯片切片',
  'mr-yancy-bits-reading-guide.svg': '读法指南图：01000001 → 65 → A，下面四张读法卡',
  'wall-1-triangles-to-3d.png': '三角形 → 立体的三阶段图（散三角 → 剪影 → 圣母与圣子线框）',
  'stills/fractal-main-6.png': '分形定格（×64 那一帧）', 'stills/fractal-main-20.png': '分形定格（×100 万那一帧）',
  'stills/bits-close-112.png': '比特墙定格：像素拼成的耶稣降生像',
};
const name = (f) => FILE[f] || f;
const secs = ([a, b]) => (a === b ? `定格在第 ${a} 秒` : `第 ${a}–${b} 秒`);
const visualText = (v) => {
  switch (v.kind) {
    case 'clip': return `${name(v.file)}，${secs(v.span)}${v.dim ? '（压暗）' : ''}${v.overlay ? '，左上角显示公式和放大倍数' : ''}${v.pip ? `；右上角小窗：${name(v.pip.file)} ${secs(v.pip.span)}` : ''}`;
    case 'montage': return `${name(v.file)}，几段剪在一起：${v.spans.map(secs).join(' → ')}`;
    case 'ramp': {
      const k = v.keys.zh;
      const at = (t) => {
        if (t <= k[0][0]) return k[0][1];
        for (let i = 1; i < k.length; i++) {
          const [t0, s0, v0] = k[i - 1], [t1, s1, v1] = k[i];
          if (t > t1) continue;
          const h = t1 - t0, u = (t - t0) / h;
          return (2 * u ** 3 - 3 * u ** 2 + 1) * s0 + (u ** 3 - 2 * u ** 2 + u) * h * v0 + (3 * u ** 2 - 2 * u ** 3) * s1 + (u ** 3 - u ** 2) * h * v1;
        }
        return k[k.length - 1][1];
      };
      let top = 0;
      for (let t = 0; t < k[k.length - 1][0]; t += 1 / 30) top = Math.max(top, (at(t + 1 / 30) - at(t)) * 30);
      return `${name(v.file)}，第 ${k[0][1]}–${k[k.length - 1][1]} 秒一镜到底，曲线变速（最快约 ${Math.round(top)} 倍）：` +
        k.map(([t, s, sp]) => `${t} 秒→画的第 ${s} 秒（${sp}×）`).join(' · ');
    }
    case 'image': return name(v.file);
    case 'switch': return `${v.first ? `${name(v.first)}，然后 ` : ''}Codex 图：开关一开一关（灯跟着亮灭）${v.pip ? `；右上角小窗：${name(v.pip.file)} ${secs(v.pip.span)}` : ''}`;
    case 'grid': return `房间的玻璃格点（深色背景）${v.pip ? `；右上角小窗：${name(v.pip.file)} ${secs(v.pip.span)}` : ''}`;
    case 'pixelzoom': return v.from === v.to ? `${name(v.file)}${v.from > 1 ? `，放大 ${v.from} 倍看到方格` : ''}` : `${name(v.file)}，从 ${v.from} 倍放大到 ${v.to} 倍，像素变成一格一格的方块`;
    case 'split': return `左右分屏：左 ${visualText(v.left)}；右 ${visualText(v.right)}`;
    case 'wall': return `五张定格排成一排：${v.items.map((i) => i.label.zh).join(' · ')}`;
  }
};
const cardText = (c) => {
  switch (c.kind) {
    case 'words': return `${c.kicker ? `（小标：${c.kicker.zh}）` : ''}「${c.text.zh}」${c.small ? ` 下面小字「${c.small.zh}」` : ''}`;
    case 'big': return `大字 \`${c.text}\`${c.small ? ` 下面「${c.small.zh}」` : ''}`;
    case 'note': return `左下角提示条「${c.text.zh}」`;
    case 'carry': return '进位卡：左栏「我们的数」8 → 9 → 10，右栏「计算机的数」0 → 1 → 10（it03-03 时出现）';
    case 'adder': return '加法器卡：开关 A / B、规则框「只有一个开着」「两个都开着」、灯「和」「进位」；按句子切开关；真值表 0+0=0、0+1=1、1+0=1、1+1=10 逐行出现；it07-07 电流流动，it07-08 四组接成一排，it07-09 满屏开关，it07-10 每个像素几百次 z² + c';
    case 'guess': return '猜数卡：1–8 八个数，Q1 比 4 大吗？是 → Q2 比 6 大吗？是 → Q3 是 7 吗？是！，最后留下 7';
    case 'ruler': return `香农的尺子：${RULER.map((r) => `${r.value} ${r.label.zh}`).join(' · ')}（每个刻度在对应句子开始时落上去，it10-11 全部到齐，标题变成「信息 = 你还得问多少」）`;
    case 'fractal-pixel': return '一个像素卡：圈出一个像素，c = −0.74797 + 0.13380 i，z → z² + c，计数到第 227 次，跑出去了 → 就是这个颜色';
  }
};

const visualAt = {}; const cardAt = {};
for (const v of VISUALS) range(v.from, v.to).forEach((id, k) => { visualAt[id] = {v, first: k === 0, span: `${v.from}${v.to !== v.from ? `–${v.to}` : ''}`}; });
for (const c of CARDS) range(c.from, c.to).forEach((id, k) => { cardAt[id] = {c, first: k === 0, span: `${c.from}${c.to !== c.from ? `–${c.to}` : ''}`}; });

const out = [];
out.push('# 计算机怎么算 1+1=？ 台词与分镜（成片 v3 · 2026-10-07）', '');
out.push('按成片实际剪出来的样子生成（`node scripts/fun-informatics-01/storyboard.cjs`）。每句：中英文成片里的开始时间、台词、画面、叠在上面的卡片。',
  '要改台词：改 `docs/fun-informatics-01/zh-edit.md` / `en-edit.md`（或者直接在这里改，我照着改回去）。要改画面或卡片：在这里写清楚，我改 `shots.ts`。', '',
  `开头 0:00–0:06：加载屏 2 秒 → 太空舱，片名卡「计算机怎么算 1+1=？」+「${INTRO.series.zh}」+「${INTRO.byline.zh}」，it00-01 说完、it00-02 开口前淡出。`, '');
for (const s of sections) {
  out.push(`## ${s.id.toUpperCase()} · ${s.title}`, '');
  for (const id of ids.filter((i) => i.startsWith(s.id))) {
    const zh = cue('zh', id); const en = cue('en', id);
    out.push(`### ${id} · 中 ${mmss(zh.start)} / 英 ${mmss(en.start)}`, '');
    out.push(`- 台词：${lineOf('zh', id)}`);
    out.push(`- English: ${lineOf('en', id)}`);
    const v = visualAt[id];
    if (id === 'it00-01') out.push('- 画面：太空舱 + 片名卡（见开头）');
    else if (v) out.push(v.first ? `- 画面${v.span.includes('–') ? `（${v.span} 一个镜头）` : ''}：${visualText(v.v.visual)}` : `- 画面：接上一句，同一个镜头继续（${v.span}）`);
    const c = cardAt[id];
    if (c) out.push(c.first ? `- 卡片${c.span.includes('–') ? `（${c.span}）` : ''}：${cardText(c.c.card)}` : `- 卡片：同上（${c.span}）`);
    out.push('');
  }
}
out.push(`结尾 中 ${mmss(tl.zh.endCardStart)} / 英 ${mmss(tl.en.endCardStart)}：结束卡（片名、is.lucasacademy.org、素材出处、${INTRO.byline.zh}），10 秒。`, '');
fs.writeFileSync(path.join(ROOT, 'docs/fun-informatics-01/storyboard.md'), out.join('\n'));
console.log('wrote docs/fun-informatics-01/storyboard.md,', ids.length, 'lines');
