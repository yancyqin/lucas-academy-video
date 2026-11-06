#!/usr/bin/env python3
"""Liberty Leading the People without Liberty, for Muse — and Liberty herself, to lay back on the clip.

Owner 11-05: 「自由引导人民 你让codex做一个去掉中间女人的图 完了我们生成视频，再把女人加回去」. Codex paints the picture without
her (codex/real-liberty-plate.png, `codex_real.py liberty-plate liberty-plate`); this script
  1. registers Codex's picture onto the 4K scan (ECC affine, her area left out of the fit),
  2. finds her as the big region where the two differ (colour distance, kept only near the middle of the picture,
     holes filled) — her body, cap, flag, pole and musket,
  3. writes codex/liberty-plate.png = the real scan everywhere except a generous region around her, where Codex's fill is
     used (what Muse animates), and codex/liberty-cutout.png = the scan with a tight soft alpha around her (what goes back
     on top of the clip), plus codex/liberty-plate-check.jpg (scan | plate | matte | plate + cut-out) to look at.

  .venv-reframe/bin/python scripts/blue-wave/liberty_plate.py [THRESHOLD]
"""
import os, sys
import cv2
import numpy as np
from PIL import Image
from scipy import ndimage

DATA = os.environ.get("BLUE_WAVE_DATA", "/Users/yqin/repo/playground/lucas-academy-video-data/blue-wave")
WORK = 1024                    # analysis width
THRESH = float(sys.argv[1]) if len(sys.argv) > 1 else 22.0      # Lab distance that counts as "she was here"
WEAK = 12.0                    # ... and the lower distance her outline may grow through, if connected to her and close to her
                               # (her right foot on the beam differs from Codex's wood by only ~20)
MIDDLE = (0.28, 0.78)          # her parts (flag included) lie between these fractions of the width
TIGHT, LOOSE = 0.004, 0.008    # dilation of the cut-out matte / of the fill region, as fractions of the width (a wider fill
                               # reaches the kneeling man's face and ghosts it)
FEATHER = 0.0025               # soft edge of the cut-out, fraction of the width
# her right foot on the beam: pink toes on brown wood barely differ from Codex's wood, so it is marked by hand (centre x, y,
# radius x, y as fractions of the picture)
FOOT = (0.600, 0.672, 0.030, 0.048)
NEAR = 0.05                    # a smaller piece this close to her (fraction of the width) is part of her (her right foot is ~0.04 away)

def lab(rgb):
    return cv2.cvtColor(rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB)

def main():
    scan = np.asarray(Image.open(f"{DATA}/art/liberty.jpg").convert("RGB"))
    H, W = scan.shape[:2]
    gen = np.asarray(Image.open(f"{DATA}/codex/real-liberty-plate.png").convert("RGB").resize((W, H), Image.LANCZOS))
    h = round(WORK * H / W)
    s_small = cv2.resize(scan, (WORK, h), interpolation=cv2.INTER_AREA)
    g_small = cv2.resize(gen, (WORK, h), interpolation=cv2.INTER_AREA)
    # 1. register, leaving the middle out of the fit
    fit = np.full((h, WORK), 255, np.uint8); fit[:, int(MIDDLE[0] * WORK):int(MIDDLE[1] * WORK)] = 0
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        _, warp = cv2.findTransformECC(cv2.cvtColor(s_small, cv2.COLOR_RGB2GRAY).astype(np.float32),
                                       cv2.cvtColor(g_small, cv2.COLOR_RGB2GRAY).astype(np.float32), warp, cv2.MOTION_AFFINE,
                                       (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), fit, 5)
    except cv2.error as e:
        print("ECC did not converge, using the plain resize:", e)
    g_small = cv2.warpAffine(g_small, warp, (WORK, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
    big = warp.copy(); big[:, 2] *= W / WORK
    gen = cv2.warpAffine(gen, big, (W, H), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
    print("registration", np.round(warp, 4).tolist())
    # 2. where they differ
    d = np.linalg.norm(lab(cv2.GaussianBlur(s_small, (0, 0), 2)) - lab(cv2.GaussianBlur(g_small, (0, 0), 2)), axis=2)
    outside = np.concatenate([d[:, :int(MIDDLE[0] * WORK)].ravel(), d[:, int(MIDDLE[1] * WORK):].ravel()])
    print(f"colour distance: outside the middle median {np.median(outside):.1f}, p95 {np.percentile(outside, 95):.1f}; "
          f"inside p50 {np.median(d[:, int(MIDDLE[0] * WORK):int(MIDDLE[1] * WORK)]):.1f}")
    m = d > THRESH
    m = ndimage.binary_opening(m, iterations=2); m = ndimage.binary_closing(m, iterations=4)
    lbl, n = ndimage.label(m)
    keep = np.zeros_like(m)
    for i, sl in enumerate(ndimage.find_objects(lbl), 1):
        comp = lbl[sl] == i; area = comp.sum()
        cx = (sl[1].start + sl[1].stop) / 2 / WORK
        if area > 0.002 * m.size and MIDDLE[0] < cx < MIDDLE[1]:
            keep[sl] |= comp
    # small pieces right next to her (her feet on the barricade, the tip of a bayonet) belong to her too
    near = ndimage.binary_dilation(keep, iterations=round(NEAR * WORK))
    for i, sl in enumerate(ndimage.find_objects(lbl), 1):
        comp = lbl[sl] == i
        if comp.sum() > 40 and (near[sl] & comp).any(): keep[sl] |= comp
    band = ndimage.binary_dilation(keep, iterations=round(NEAR * WORK))
    keep = ndimage.binary_propagation(keep, mask=(d > WEAK) & band | keep)
    keep = ndimage.binary_opening(keep, iterations=1)
    yy, xx = np.mgrid[0:h, 0:WORK]
    keep |= ((xx / WORK - FOOT[0]) / FOOT[2]) ** 2 + ((yy / h - FOOT[1]) / FOOT[3]) ** 2 < 1
    keep = ndimage.binary_closing(keep, iterations=6)      # close the notches in her skirt so the holes fill
    keep = ndimage.binary_fill_holes(keep)
    Image.fromarray(np.dstack([np.clip(d * 6, 0, 255).astype(np.uint8)] * 2 + [(keep * 255).astype(np.uint8)])).save(
        f"{DATA}/codex/liberty-diff.png")       # red/green = colour distance, blue = what counts as her
    print(f"her region: {keep.mean():.1%} of the picture, {n} raw blobs")
    def soft(mask, grow, feather):
        k = max(1, round(grow * WORK))
        g = ndimage.binary_dilation(mask, iterations=k).astype(np.float32)
        g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
        return np.clip(cv2.GaussianBlur(g, (0, 0), max(1.0, feather * W)), 0, 1)[..., None]
    fill = soft(keep, LOOSE, 0.003)
    cut = soft(keep, TIGHT, FEATHER)
    # 3. outputs
    plate = scan * (1 - fill) + gen * fill
    Image.fromarray(np.clip(plate + 0.5, 0, 255).astype(np.uint8)).save(f"{DATA}/codex/liberty-plate.png")
    Image.fromarray(np.dstack([scan, (cut[..., 0] * 255 + 0.5).astype(np.uint8)])).save(f"{DATA}/codex/liberty-cutout.png")
    back = plate * (1 - cut) + scan * cut
    over = scan * 0.5 + np.array([255, 40, 40]) * 0.5 * cut + scan * 0.5 * (1 - cut)
    tiles = [Image.fromarray(np.clip(x + 0.5, 0, 255).astype(np.uint8)).resize((960, round(960 * H / W)), Image.LANCZOS)
             for x in (scan.astype(np.float32), plate, over, back)]
    sheet = Image.new("RGB", (1940, 2 * tiles[0].height + 20), (255, 255, 255))
    for k, t in enumerate(tiles): sheet.paste(t, ((k % 2) * 980, (k // 2) * (t.height + 20)))
    sheet.save(f"{DATA}/codex/liberty-plate-check.jpg", quality=88)
    print("wrote liberty-plate.png, liberty-cutout.png, liberty-plate-check.jpg")

if __name__ == "__main__":
    main()
