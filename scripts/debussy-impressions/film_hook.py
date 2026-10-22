"""film_hook.py SRC DST — make the film's render copy of the art lab: copy SRC (an art-lab checkout) to DST and add the
film-only hooks to living.html (never committed to the art lab):
  * __living.filmSnap() paints the default effects and returns the masks and the creatures' positions;
  * __living.filmShow({warps, marks, gain, drift}) reveals each effect along a direction, shows chosen creatures,
    scales the effects for full screen (gain) and sets the drifting sky's offset (drift = pixels, from the film's
    own clock, so the clouds start from the painting when the wand brings them);
  * __living.filmCapture(id, i0, i1) plays film-live/<id>.json and posts frames to the local frame sink (toDataURL:
    toBlob is throttled in a hidden browser pane).
"""
import shutil, sys, os
src, dst = sys.argv[1], sys.argv[2]
if os.path.exists(dst): shutil.rmtree(dst)
shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git", "output", "tmp"))
p = os.path.join(dst, "living.html"); s = open(p).read()

GAIN = '''      if (!o) continue;
      if (film.gain !== 1) { const g = film.gain, gl = 1 + (g - 1) * 0.6;   // film only: effects read at full screen
        o = { dx: o.dx * g, dy: o.dy * g, light: o.light * gl, shiver: o.shiver * g, ripple: o.ripple * g,
              flowX: o.flowX * g, flowY: o.flowY * g, glint: o.glint * gl, drift: o.drift }; }'''
a = "      if (!o) continue;\n      dispAcc[k * 4] += fin(o.dx, -30, 30) * w;"
assert a in s, "drawLiving anchor"; s = s.replace(a, GAIN + "\n      dispAcc[k * 4] += fin(o.dx, -30, 30) * w;", 1)

HOOK = r'''// ---- Film hook (render copy only, never committed) ----
const film = { final: null, marks: null, gain: 1 };
function filmSnap(){
  paintDefaults();
  film.final = {}; for (const k in own.warps) film.final[k] = own.warps[k].slice();
  film.marks = own.strokes.slice();
  const masks = {}; for (const k in film.final){ const ix = []; film.final[k].forEach((v, c) => { if (v) ix.push(c); }); masks[k] = ix; }
  return { W, H, GW, GH, warps: Object.keys(film.final), masks,
           marks: film.marks.map(st => ({ key: st.key, x: st.marks[0] && st.marks[0].x, y: st.marks[0] && st.marks[0].y })) };
}
function filmShow(spec){
  if (spec.gain) film.gain = spec.gain;
  driftOffsetOverride = (typeof spec.drift === "number") ? spec.drift : null;
  for (const k in film.final){
    const sp = spec.warps && spec.warps[k], src = film.final[k], g = new Uint8Array(GW * GH);
    if (sp){
      const [pr, dx, dy] = sp; let lo = 1e9, hi = -1e9;
      const at = c => ((c % GW) + .5) / GW * dx + (Math.floor(c / GW) + .5) / GH * dy;
      for (let c = 0; c < GW * GH; c++) if (src[c]) { const u = at(c); if (u < lo) lo = u; if (u > hi) hi = u; }
      const lim = lo + (hi - lo + 1e-6) * pr;
      for (let c = 0; c < GW * GH; c++) if (src[c] && at(c) <= lim) g[c] = 1;
    }
    own.warps[k] = g;
  }
  const counts = {};
  own.strokes = film.marks.filter(st => {
    const n = (counts[st.key] = (counts[st.key] || 0) + 1) - 1, m = spec.marks && spec.marks[st.key];
    return Array.isArray(m) ? m.includes(n) : n < (m || 0);
  });
  warpRev++; showing = own;
}
async function filmCapture(id, i0, i1){
  const S = await (await fetch(`film-live/${id}.json?r=${Date.now()}`)).json();
  if (!film.final) filmSnap();
  const sm = x => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); };
  const N = Math.round((S.t_end - S.live_t0) * 30), end = Math.min(N, i1);
  for (let i = i0; i < end; i++){
    const t = S.live_t0 + i / 30, warps = {}, marks = {};
    let drift = null;
    for (const w of S.warps) if (t >= w.t0){
      warps[w.key] = [sm((t - w.t0) / w.dur), w.dir[0], w.dir[1]];
      if (w.drift){                                   // the wind rises over `ramp` seconds: offset = ∫ speed·smoothstep
        const R = w.ramp || 4, u = (t - w.t0) / R;
        drift = w.drift * (u < 1 ? R * (u ** 3 - u ** 4 / 2) : (t - w.t0) - R / 2);
      }
    }
    if (drift === null && S.warps.some(w => w.drift)) drift = 0;
    for (const m of S.marks) marks[m.key] = m.order.filter((_, q) => m.times[q] <= t);
    filmShow({ warps, marks, gain: S.gain, drift });
    drawFrame(t);
    await fetch(`http://127.0.0.1:8742/frame?name=live-${id}&i=${i}`, { method: "POST", body: cv.toDataURL("image/jpeg", 0.95) });
  }
  return `${id} ${i0}-${end} of ${N}`;
}

window.__living = {'''
a = "window.__living = {"
assert s.count(a) == 1; s = s.replace(a, HOOK, 1)
a = "  build: buildLpp,"
assert a in s; s = s.replace(a, "  filmSnap, filmShow, filmCapture,\n  build: buildLpp,", 1)
open(p, "w").write(s)
print("film copy ready:", dst)
