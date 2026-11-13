"""Hand-drawn circles (owner 2026-11-04): the pack the owner draws on, and reading the drawings back.

  pack OUT_DIR       画圈位置参考.pdf (where each circle goes, numbered) and 画圈-在这里画.pdf (clean pages to draw on)
  ingest PDF|DIR     read the owner's strokes (PDF ink annotations, or red pixels on the clean pages) into
                     src/data/impressionism-strokes.json; marks not drawn keep a placeholder

Each page is one painting at PAGE_W wide with a caption strip under it; pages.json in OUT_DIR records
where the picture sits on each page so strokes map back to picture fractions.
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
MARKS = json.loads((Path(__file__).parent / 'marks.json').read_text())
IMG = ROOT / 'public/impressionism-secret/img'
STROKES = ROOT / 'src/data/impressionism-strokes.json'
PAGE_W, STRIP = 1600, 260
FONT = '/System/Library/Fonts/Hiragino Sans GB.ttc'
RED = (230, 30, 30)


def font(size):
    return ImageFont.truetype(FONT, size)


def picture(name):
    return Image.open(IMG / f'{name}.jpg').convert('RGB')


def page(p, n, reference):
    im = picture(p['img'])
    h = round(im.height * PAGE_W / im.width)
    im = im.resize((PAGE_W, h), Image.LANCZOS)
    pg = Image.new('RGB', (PAGE_W, h + STRIP), (250, 247, 240))
    pg.paste(im, (0, 0))
    d = ImageDraw.Draw(pg)
    if reference:
        for m in p['marks']:
            x0, y0, x1, y1 = (m['box'][0] * PAGE_W, m['box'][1] * h, m['box'][2] * PAGE_W, m['box'][3] * h)
            for k in range(0, 360, 12):  # dashed ellipse
                d.arc([x0, y0, x1, y1], k, k + 7, fill=(255, 215, 0), width=7)
            tx, ty = min(max(x0 + 8, 8), PAGE_W - 90), min(max(y0 + 8, 8), h - 70)
            d.rounded_rectangle([tx, ty, tx + 78, ty + 56], 10, fill=(20, 15, 12))
            d.text((tx + 39, ty + 28), m['id'], font=font(36), fill=(255, 215, 0), anchor='mm')
    d.text((24, h + 18), f"{n}　{p['zh']}", font=font(40), fill=(30, 25, 20))
    line = '　'.join(f"{m['id']} {m['zh']}" for m in p['marks'])
    # wrap the mark list into the strip
    y, cur = h + 78, ''
    for ch in line:
        if d.textlength(cur + ch, font=font(28)) > PAGE_W - 48:
            d.text((24, y), cur, font=font(28), fill=(70, 60, 50)); y += 40; cur = ''
        cur += ch
    d.text((24, y), cur, font=font(28), fill=(70, 60, 50))
    return pg, h


def pack(out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    pages, meta = {True: [], False: []}, []
    for n, p in enumerate(MARKS['paintings'], 1):
        for ref in (True, False):
            pg, h = page(p, n, ref)
            pages[ref].append(pg)
        meta.append({'img': p['img'], 'page_w': PAGE_W, 'pic_h': h, 'page_h': h + STRIP})
        pages[False][-1].save(out / f"{n:02d}-{p['img']}.png")  # clean page, to diff drawn PNGs against
    for ref, name in ((True, '画圈位置参考.pdf'), (False, '画圈-在这里画.pdf')):
        pages[ref][0].save(out / name, save_all=True, append_images=pages[ref][1:], resolution=150)
    (out / 'pages.json').write_text(json.dumps(meta, indent=1))
    print(len(meta), 'pages ->', out)


def placeholder(box, seed):
    """A hand-drawn-looking closed loop around a box (owner 2026-11-04: "画闭合的，不要 overlap"): starts
    near eleven o'clock and goes once round clockwise back to where it began, its radius wobbling a few
    percent the way a hand does (the wobble repeats every turn, so the ends meet); in picture fractions."""
    x0, y0, x1, y1 = box
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 * 1.1, (y1 - y0) / 2 * 1.12
    pts = []
    for i in range(97):
        a = math.radians(-105 + 360 * i / 96)
        k = 1 + 0.035 * math.sin(3 * a + seed) + 0.02 * math.sin(5 * a + 2 * seed)
        pts.append([round(cx + rx * k * math.cos(a), 4), round(cy + ry * k * math.sin(a), 4)])
    return [pts]


def strokes(*_):
    """Write the strokes file: the owner's drawing where there is one, a placeholder loop otherwise."""
    old = json.loads(STROKES.read_text()) if STROKES.exists() else {}
    out = {}
    for p in MARKS['paintings']:
        for n, m in enumerate(p['marks']):
            o = old.get(m['id'])
            # v10 round 2 (owner 2026-11-04: "我看你本身的手绘就不错了"): the loops are mine, at the
            # boxes in marks.json; the owner's drawing only moved Titian's two (t1, t2)
            out[m['id']] = o if o and o.get('drawn') is True else {'img': p['img'], 'drawn': False,
                                                                   'strokes': placeholder(m['box'], n * 1.7 + len(m['id']))}
    STROKES.write_text(json.dumps(out, indent=0))
    print(len(out), 'marks,', sum(v['drawn'] for v in out.values()), 'drawn by the owner')


DPI = 150  # pack pages are saved at 150 dpi: PDF points = pixels * 72 / DPI


def geometry():
    """Per page: the painting, its marks and where the picture sits (same layout as page())."""
    out = []
    for p in MARKS['paintings']:
        w, h = Image.open(IMG / f"{p['img']}.jpg").size
        out.append({**p, 'pic_h': round(h * PAGE_W / w)})
    return out


def centerline(xs, ys):
    """Points of one drawn stroke (pixels of a thick red line) as an ordered centreline. A loop goes round
    its centre clockwise, starting at the gap where the pen lifted (or at twelve o'clock when it closed);
    anything that does not go most of the way round is a line, left to right along its long axis."""
    import numpy as np
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    cx, cy = xs.mean(), ys.mean()
    ang = np.arctan2(ys - cy, xs - cx)
    bins = 72
    idx = ((ang + np.pi) / (2 * np.pi) * bins).astype(int) % bins
    filled = np.bincount(idx, minlength=bins) > 0
    if filled.sum() >= bins * 0.75:
        empty = np.flatnonzero(~filled)
        start = int(empty[len(empty) // 2]) + 1 if len(empty) else int(bins * 0.25)  # twelve o'clock is -pi/2
        pts = []
        for k in range(bins + 1):
            b = (start + k) % bins
            sel = idx == b
            if sel.any():
                pts.append([float(xs[sel].mean()), float(ys[sel].mean())])
        return pts
    # a line: principal axis
    c = np.cov(np.vstack([xs - cx, ys - cy]))
    vals, vecs = np.linalg.eigh(c)
    ax = vecs[:, -1] if vecs[0, -1] >= 0 else -vecs[:, -1]
    t = (xs - cx) * ax[0] + (ys - cy) * ax[1]
    edges = np.linspace(t.min(), t.max(), 41)
    pts = []
    for a, b in zip(edges[:-1], edges[1:]):
        sel = (t >= a) & (t <= b)
        if sel.any():
            pts.append([float(xs[sel].mean()), float(ys[sel].mean())])
    return pts


def assign(page, found):
    """found: list of strokes in picture fractions -> {mark id: [strokes]}, each to the mark whose box
    centre is nearest the stroke's centre (a mark may get several strokes, kept in drawing order)."""
    out = {}
    for st in found:
        if len(st) < 4:
            continue
        sx = sum(x for x, _ in st) / len(st); sy = sum(y for _, y in st) / len(st)
        best = min(page['marks'], key=lambda m: ((m['box'][0] + m['box'][2]) / 2 - sx) ** 2 + ((m['box'][1] + m['box'][3]) / 2 - sy) ** 2)
        out.setdefault(best['id'], []).append([[round(x, 4), round(y, 4)] for x, y in st])
    return out


def from_pdf(path):
    from pypdf import PdfReader
    reader = PdfReader(path)
    got = {}
    for page, g in zip(reader.pages, geometry()):
        H = float(page.mediabox.height)
        found = []
        for ref in page.get('/Annots') or []:
            a = ref.get_object()
            if a.get('/Subtype') != '/Ink':
                continue
            for ink in a.get('/InkList', []):
                v = [float(n) for n in ink]
                pts = [((x * DPI / 72) / PAGE_W, ((H - y) * DPI / 72) / g['pic_h']) for x, y in zip(v[0::2], v[1::2])]
                found.append(pts)  # in drawing order, as drawn
        got.update(assign(g, found))
    return got


def from_pixels(images):
    """Red strokes on the clean pages (PNG copies, or a flattened PDF rendered at DPI)."""
    import numpy as np
    from scipy import ndimage
    got = {}
    for n, g in enumerate(geometry(), 1):
        f = images.get(n)
        if f is None:
            continue
        im = np.asarray(Image.open(f).convert('RGB').resize((PAGE_W, g['pic_h'] + STRIP)), int)[:g['pic_h']]
        clean = np.asarray(page(g, n, False)[0], int)[:g['pic_h']]
        r, gg, b = im[..., 0], im[..., 1], im[..., 2]
        red = (r > 140) & (r - gg > 70) & (r - b > 60) & (np.abs(im - clean).sum(-1) > 60)
        red = ndimage.binary_closing(red, iterations=2)
        lab, k = ndimage.label(ndimage.binary_dilation(red, iterations=4))
        found = []
        for i in range(1, k + 1):
            ys, xs = np.nonzero((lab == i) & red)
            if len(xs) < 150:
                continue
            found.append([(x / PAGE_W, y / g['pic_h']) for x, y in centerline(xs, ys)])
        got.update(assign(g, found))
    return got


def ingest(path):
    """Read the owner's drawings (the pack PDF with ink, or the folder of drawn PNGs) into the strokes file."""
    import glob, re, subprocess, tempfile
    path = Path(path)
    if path.suffix.lower() == '.pdf':
        got = from_pdf(path)
        if not got:  # flattened: read the red pixels instead
            tmp = Path(tempfile.mkdtemp())
            subprocess.run(['pdftoppm', '-r', str(DPI), '-png', str(path), str(tmp / 'p')], check=True)
            got = from_pixels({int(re.search(r'(\d+)\.png$', f).group(1)): f for f in glob.glob(str(tmp / 'p-*.png'))})
    else:
        got = from_pixels({int(Path(f).name[:2]): f for f in glob.glob(str(path / '[0-9][0-9]-*.png'))})
    data = json.loads(STROKES.read_text()) if STROKES.exists() else {}
    for mid, sts in got.items():
        data[mid] = {'img': data.get(mid, {}).get('img'), 'drawn': True, 'strokes': sts}
    STROKES.write_text(json.dumps(data, indent=0))
    print('drawn:', ' '.join(sorted(got)) or 'none')
    strokes()


# ---- v10 round 2 (owner 2026-11-04): the drawings are a guide only ----
# "你不要用我画的，我画的就是个示意……不像艺术家圈出来的，主要是要手绘的那个意思。视频是要画出来，不是直接出现个圈"
# The owner's loops give where each circle goes, how big and at what tilt; the film draws a smooth,
# confident brush loop there instead (artist_loop), drawn on stroke by stroke.

def artist_loop(cx, cy, a, b, tilt, seed):
    """One hand-made loop in picture fractions: starts upper left, goes round clockwise a little more than
    once, opening slightly so the end passes outside the start, with a gentle low-frequency wobble."""
    pts = []
    turns = 1.13
    for i in range(97):
        u = i / 96
        t = math.radians(-125) + 2 * math.pi * turns * u
        k = (0.965 + 0.07 * u) * (1 + 0.022 * math.sin(2 * t + seed) + 0.012 * math.sin(3 * t + 2.3 * seed))
        x, y = a * k * math.cos(t), b * k * math.sin(t)
        pts.append([round(cx + x * math.cos(tilt) - y * math.sin(tilt), 4), round(cy + x * math.sin(tilt) + y * math.cos(tilt), 4)])
    return pts


def fit_loop(xs, ys, aspect):
    """Centre, half-axes and tilt of a drawn loop (pixel arrays; aspect = picture h/w so the fit is done in
    true proportions), returned in picture fractions."""
    import numpy as np
    X = np.vstack([xs, ys * aspect])
    c = X.mean(1, keepdims=True)
    vals, vecs = np.linalg.eigh(np.cov(X - c))
    a, b = np.sqrt(2 * vals[1]), np.sqrt(2 * vals[0])  # points spread round an ellipse: var = r^2 / 2
    v = vecs[:, 1]
    tilt = math.atan2(v[1], v[0])
    if tilt > math.pi / 2: tilt -= math.pi
    if tilt < -math.pi / 2: tilt += math.pi
    return float(c[0, 0]), float(c[1, 0]) / aspect, float(a), float(b), tilt


def guide(pdf):
    """Read the owner's guide loops off the drawn PDF (rendered, compared with the clean pages) and write
    smooth artist loops at their places into the strokes file; marks not drawn keep their box."""
    import glob, re, subprocess, tempfile
    import numpy as np
    from scipy import ndimage
    tmp = Path(tempfile.mkdtemp())
    subprocess.run(['pdftoppm', '-r', str(DPI), '-png', str(pdf), str(tmp / 'p')], check=True)
    pages = {int(re.search(r'(\d+)\.png$', f).group(1)): f for f in glob.glob(str(tmp / 'p-*.png'))}
    out, report = {}, []
    for n, g in enumerate(geometry(), 1):
        W, H = PAGE_W, g['pic_h']
        u = np.asarray(Image.open(pages[n]).convert('RGB').resize((W, H + STRIP)), int)[:H]
        c = np.asarray(page(g, n, False)[0], int)[:H]
        r, gg, b = u[..., 0], u[..., 1], u[..., 2]
        ink = (r > 150) & (gg > 115) & (b < 110) & (r - b > 85) & (np.abs(u - c).sum(-1) > 90)
        lab, k = ndimage.label(ndimage.binary_dilation(ink, iterations=7))
        loops = []
        for i in range(1, k + 1):
            ys, xs = np.nonzero((lab == i) & ink)
            if len(xs) < 120:
                continue
            fx, fy = xs / W, ys / H
            loops.append(fit_loop(fx, fy, H / W))
        # each loop to the nearest mark on its page; a mark may take more than one loop
        got = {}
        for L in loops:
            m = min(g['marks'], key=lambda m: ((m['box'][0] + m['box'][2]) / 2 - L[0]) ** 2 + ((m['box'][1] + m['box'][3]) / 2 - L[1]) ** 2)
            got.setdefault(m['id'], []).append(L)
        for j, m in enumerate(g['marks']):
            if m['id'] in got:
                sts = [artist_loop(cx, cy, a * 1.04, b * 1.04 * W / H, tilt, j * 1.3 + q) for q, (cx, cy, a, b, tilt) in enumerate(got[m['id']])]
                # b and the tilt were fitted in true proportions; artist_loop works in picture fractions
                sts = [artist_loop_true(cx, cy, a * 1.04, b * 1.04, tilt, H / W, j * 1.3 + q) for q, (cx, cy, a, b, tilt) in enumerate(got[m['id']])]
                out[m['id']] = {'img': g['img'], 'drawn': 'guide', 'strokes': sts}
                report.append(f"{m['id']}: {len(sts)} loop(s) from the drawing")
            else:
                x0, y0, x1, y1 = m['box']
                out[m['id']] = {'img': g['img'], 'drawn': False,
                                'strokes': [artist_loop_true((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 * 1.08, (y1 - y0) / 2 * 1.08 * H / W, 0.0, H / W, j * 1.3)]}
                report.append(f"{m['id']}: not drawn, placed by its box")
    STROKES.write_text(json.dumps(out, indent=0))
    print('\n'.join(report))


def artist_loop_true(cx, cy, a, b, tilt, aspect, seed):
    """artist_loop with a, b and tilt in true proportions (y scaled by aspect = h/w), back to fractions."""
    pts = artist_loop(cx, cy * aspect, a, b, tilt, seed)
    return [[x, round(y / aspect, 4)] for x, y in pts]


def preview(out):
    """Every painting with its loops as the film will draw them (for checking placement)."""
    data = json.loads(STROKES.read_text())
    for n, g in enumerate(geometry(), 1):
        im = picture(g['img']).resize((PAGE_W, g['pic_h']))
        d = ImageDraw.Draw(im)
        for m in g['marks']:
            for st in data[m['id']]['strokes']:
                d.line([(x * PAGE_W, y * g['pic_h']) for x, y in st], fill=(233, 185, 58), width=8, joint='curve')
            x, y = data[m['id']]['strokes'][0][0]
            d.text((x * PAGE_W, y * g['pic_h'] - 50), m['id'], font=font(40), fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
        im.save(Path(out) / f"{n:02d}-{g['img']}.jpg", quality=85)


if __name__ == '__main__':
    {'pack': pack, 'strokes': strokes, 'ingest': ingest, 'guide': guide, 'preview': preview}[sys.argv[1]](*sys.argv[2:])
