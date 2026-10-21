"""sky_fix.py — make a Codex sky strip scroll cleanly behind a painting.

wide-<id>.png = [ new sky tiles ... | the painting's sky ]. Steps, in order:
  1. the painting's own sky, its occluders (trees, rock, people) filled with fresh clouds from the new tiles,
     tone-matched to the sky around each hole (Codex's own "clean" version had ghosts and a slight colour shift);
  2. the new sky's blue matched to the painting's (a low percentile per column, so clouds don't count);
  3. the colour step removed row by row at the join (new → painting) and at the wrap (painting → new);
  4. faint column bands from tile joins removed; dark ghosts (real sky is never that dark) repainted;
  5. the picture-size sky mask: sky-coloured, not an occluder, thinning toward the horizon.
    python sky_fix.py ID PICTURE.jpg BAND [--drop A:B]   -> plate-<id>.jpg, mask-<id>.png
"""
import argparse, numpy as np, cv2
from scipy.ndimage import gaussian_filter1d

K = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions/faune/skies"
ap = argparse.ArgumentParser(); ap.add_argument("id"); ap.add_argument("picture"); ap.add_argument("band", type=float)
ap.add_argument("--drop", help="columns A:B of the wide strip to leave out (a ghosted tile)")
ap.add_argument("--keep", action="append", default=[], help="x,y,w,h (picture fractions): never sky — a figure the colour test would take for cloud")
a = ap.parse_args()
sid = a.id
wide = cv2.imread(f"{K}/wide-{sid}.png").astype(np.float32); cdx = cv2.imread(f"{K}/clean-{sid}.png").astype(np.float32)
sky = cv2.imread(f"{K}/sky-{sid}.png").astype(np.float32)
if a.drop:
    d0, d1 = map(int, a.drop.split(":")); wide = np.concatenate([wide[:, :d0], wide[:, d1:]], 1)
H, W = wide.shape[:2]; cw = sky.shape[1]; x0 = W - cw

def tone_fill(img, hole, src, sig):
    """Fill `hole` (0..1) in img with src, recoloured to the local colour of img around the hole (falling back to
    wider and wider surroundings deep inside big holes, where nothing nearby is valid)."""
    valid = 1 - hole
    def local_at(sg):
        S = cv2.GaussianBlur(img * valid[..., None], (0, 0), sg); V = cv2.GaussianBlur(valid, (0, 0), sg)
        return S / np.maximum(V, 1e-6)[..., None], V
    L1, V1 = local_at(sig); L2, V2 = local_at(sig * 4)
    G = (img * valid[..., None]).sum((0, 1)) / max(valid.sum(), 1)
    w1 = np.clip(V1 / 0.08, 0, 1)[..., None]; w2 = np.clip(V2 / 0.08, 0, 1)[..., None]
    local = w1 * L1 + (1 - w1) * (w2 * L2 + (1 - w2) * G[None, None])
    fill = np.clip(src * (local / (cv2.GaussianBlur(src, (0, 0), sig) + 1e-3)), 0, 255)
    al = cv2.GaussianBlur(hole, (0, 0), 6)[..., None]
    return img * (1 - al) + fill * al

def skyish(img):
    """Sky = everything in the band that is not dark and not foliage green (clouds may be cream, grey or pink)."""
    b, g, r = img[..., 0], img[..., 1], img[..., 2]; l = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    leafy = (g > r + 12) & (g > b + 4) & (l < 0.58)
    m = (~leafy & (l > 0.36)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)); return cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))

# 1) the painting's sky with its occluders filled
sk = skyish(sky); occl = np.abs(sky - cdx).mean(2) > 40
pic0 = cv2.imread(a.picture); PH0, PW0 = pic0.shape[:2]
zone = np.zeros(occl.shape, bool)
for r in a.keep:                                                        # where a white figure stands: follow its outline
    fx, fy, fw, fh = map(float, r.split(","))
    zone[int(fy * PH0):int((fy + fh) * PH0), int(fx * PW0):int((fx + fw) * PW0)] = True
if zone.any():
    fig = (np.abs(sky - cdx).mean(2) > 18) | (skyish(sky) == 0)          # Codex had to change it, or it is not sky-coloured
    fig = cv2.morphologyEx(fig.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fig)
    keepfig = np.zeros_like(fig)
    for k in range(1, n):                                              # the big pieces inside the zones are the figures
        if st[k, cv2.CC_STAT_AREA] > 3000 and zone[lab == k].mean() > 0.5: keepfig[lab == k] = 1
    # Codex repainted much of this sky, so "Codex changed it" means nothing here: only the figures are holes
    occl = cv2.dilate(keepfig, np.ones((11, 11), np.uint8)).astype(bool)
holes = cv2.dilate(((1 - sk) | occl).astype(np.uint8), np.ones((17, 17), np.uint8)).astype(np.float32)
base = tone_fill(sky, holes, wide[:, :cw], 0.05 * cw)                   # fresh clouds from the far-left tile
print(sid, "painting sky: repainted %.1f%% where it was hidden" % (holes.mean() * 100))
out = wide.copy(); out[:, x0:] = base

# 2) the new sky's blue → the painting's blue
skyc = np.percentile(out, 30, axis=0); target = np.percentile(base, 30, axis=0).mean(0)
low = np.stack([gaussian_filter1d(skyc[:, c], H * 0.35, mode="wrap") for c in range(3)], 1)
gain = target[None] / (low + 1e-3)
ramp = np.ones(W, np.float32); ramp[x0:] = 0
out = np.clip(out * (1 + (gain - 1) * ramp[:, None])[None], 0, 255)

# 3) row-wise colour steps at the join and at the wrap, removed on the new-sky side only
def unstep(img, cols_new, cols_ref, xs, wsh):
    d = img[:, cols_ref].mean(1) - img[:, cols_new].mean(1)
    d = cv2.GaussianBlur(d[:, None, :], (1, 0), sigmaX=1, sigmaY=8)[:, 0, :]
    for j, x in enumerate(xs): img[:, x] += d * wsh[j]
    return img
R = int(min(560, x0 * 0.25))
xs = np.arange(x0 - R, x0); out = unstep(out, np.arange(x0 - 24, x0), np.arange(x0, x0 + 24), xs, ((xs - (x0 - R)) / R) ** 2)
xs = np.arange(0, R); out = unstep(out, np.arange(0, 24), np.arange(W - 24, W), xs, (1 - xs / R) ** 2)

# 4a) column bands (shared by every row) in the new sky
hp = out - np.stack([gaussian_filter1d(out[..., c], 160, axis=1, mode="wrap") for c in range(3)], -1)
band = np.stack([gaussian_filter1d(np.median(hp, axis=0)[:, c], 6, mode="wrap") for c in range(3)], 1)
keep = np.ones(W, np.float32); keep[x0:] = 0; keep[x0 - 60:x0] = np.linspace(1, 0, 60); keep[:60] = np.minimum(keep[:60], np.linspace(0, 1, 60))
out = np.clip(out - band[None] * keep[None, :, None], 0, 255)
# 4b) ghosts
for rnd in range(2):
    lum = out.mean(2); thr = min(100.0, np.percentile(lum, 0.5) + 8)
    n, lab, st, _ = cv2.connectedComponentsWithStats((lum < thr).astype(np.uint8))
    big = np.zeros(lum.shape, np.uint8)
    for k in range(1, n):
        if st[k, cv2.CC_STAT_AREA] > 150: big[lab == k] = 1
    if not big.any(): break
    hole = cv2.dilate(big, np.ones((31, 31), np.uint8)).astype(np.float32)
    out = tone_fill(out, hole, np.roll(out, W // 3 + rnd * W // 7, axis=1), 0.04 * cw)
    print(sid, f"ghost pass {rnd + 1}: {int(big.sum())} dark px")
cv2.imwrite(f"{K}/plate-{sid}.jpg", np.clip(out, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 94])
step = lambda xa, xb: float(np.abs(out[:, xa].astype(float) - out[:, xb]).mean())
print(sid, "plate", (W, H), "join step %.1f  wrap step %.1f  typical %.1f" % (step(x0 - 1, x0), step(W - 1, 0), step(x0 // 2, x0 // 2 + 1)))

# 5) the sky mask, picture-size
pic = cv2.imread(a.picture); PH, PW = pic.shape[:2]; bh = sky.shape[0]
m = (sk & ~occl).astype(np.uint8)
inv = 1 - m; n, lab, st, _ = cv2.connectedComponentsWithStats(inv)   # small specks inside the sky move with it
for k in range(1, n):
    ys = np.nonzero(lab == k)[0]
    if ys.max() < bh - 3 and st[k, cv2.CC_STAT_AREA] < 4000 and not occl[lab == k].any(): m[lab == k] = 1
m = m.astype(np.float32)
m = cv2.GaussianBlur(cv2.erode(m, np.ones((5, 5), np.uint8)), (0, 0), 3) * np.clip((bh - np.arange(bh)) / (0.18 * bh), 0, 1)[:, None]
mask = np.zeros((PH, PW), np.float32); mask[:bh] = m if m.shape[1] == PW else cv2.resize(m, (PW, bh))
cv2.imwrite(f"{K}/mask-{sid}.png", (mask * 255).astype(np.uint8))
print(sid, "mask: sky %.0f%% of the band" % (mask[:bh].mean() * 100))
