/** 好奇新世界 · 第 1 期: the archived Weekly pages, as they read, in the film's language.
 *   node scripts/weekly/stills.cjs scripts/weekly/001/stills.cjs [name ...]                  (Chinese)
 *   WEEKLY_LANG=en node scripts/weekly/stills.cjs scripts/weekly/001/stills.cjs [name ...]   (English)
 */
const W = n => `https://lucasacademy.org/weekly/?edition=${n}&lang=${process.env.WEEKLY_LANG || 'zh'}`;

module.exports = [
  {name: 'w001-hero', url: W('001')},
  {name: 'w001-museum', url: W('001'), anchor: '#discover'},
  {name: 'w001-demos', url: W('001'), anchor: '#discover', scroll: 720},
  {name: 'w001-ideas', url: W('001'), anchor: '#ideas'},
  {name: 'w001-perspective', url: W('001'), anchor: '.perspective'},
  {name: 'w001-balance', url: W('001'), anchor: '.balance-panel'},
  {name: 'w001-rules', url: W('001'), anchor: '.discussion'},
  {name: 'w001-doors', url: W('001'), anchor: '#doors'},
  {name: 'w001-matthew', url: W('001'), anchor: '#matthew'},
  {name: 'w001-atelier', url: W('001'), anchor: '#atelier'},
  {name: 'w001-submit', url: W('001'), anchor: '#submit'},
  {name: 'w002-hero', url: W('002')},
  {name: 'w002-chess', url: W('002'), anchor: '#chess'},
  {name: 'w002-chess-design', url: W('002'), anchor: '#chess-design'},
  {name: 'w002-language-bridge', url: W('002'), anchor: '#language-bridge'},
  {name: 'w002-coding', url: W('002'), anchor: '#coding'},
  {name: 'w002-coding-rainbow', url: W('002'), anchor: '#coding-rainbow'},
  {name: 'w002-coding-body', url: W('002'), anchor: '#coding-body'},
  {name: 'w002-questions', url: W('002'), anchor: '#questions'},
  {name: 'w002-possibilities', url: W('002'), anchor: '#possibilities'},
  {name: 'w002-brainstorm', url: W('002'), anchor: '#brainstorm'},
  {name: 'w002-informatics', url: W('002'), anchor: '#informatics'},
  {name: 'w003-hero', url: W('003')},
  {name: 'w003-wordplay', url: W('003'), anchor: '#wordplay'},
  {name: 'w003-informatics', url: W('003'), anchor: '#informatics'},
  {name: 'w003-chess', url: W('003'), anchor: '#chess'},
  {name: 'w003-coding', url: W('003'), anchor: '#coding'},
  {name: 'w003-journal', url: W('003'), anchor: '#journal'},
  {name: 'w003-bio', url: W('003'), anchor: '#bio'},
  {name: 'w003-questions', url: W('003'), anchor: '#questions'},
];
