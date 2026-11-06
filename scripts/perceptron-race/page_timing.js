// Time the perceptron inside the web page (Brython). Open lucas-academy-ai's
// L2-lower-intermediate/perceptron/perceptron.html, wait for "Python 3.14 runs this code",
// paste this into the browser console, and copy the printed object into results/page.json.
(async () => {
  const byId = (id) => document.getElementById(id);
  [...byId('sizes').children].find((b) => b.textContent === '20 × 20').click();   // the 20 x 20 "7 or 1" set
  byId('untilBtn').click();                                                         // train until all right
  while (!byId('stopBtn').hidden) await new Promise((r) => setTimeout(r, 100));
  const points = byId('ptsData').textContent.replace(/^points = \[/, '').replace(/\]$/, '').split(',').map((s) => Number(s.trim()));
  const picture = Array.from({ length: 400 }, (_, i) => (Math.floor(i / 20) === 3 && i % 20 >= 4 && i % 20 <= 15 ? 1 : 0));
  const time = (fn, n) => { const t0 = performance.now(); for (let i = 0; i < n; i++) fn(); return (performance.now() - t0) / n / 1000; };
  const result = {
    trained: byId('msg').textContent,
    brython_seconds_per_call: time(() => window.py_predict(picture, points), 300),
    plain_javascript_seconds_per_call: time(() => { let t = 0; for (let i = 0; i < 400; i++) if (picture[i] === 1) t += points[i]; return t > 0; }, 100000),
  };
  console.log(result);
  return result;
})();
