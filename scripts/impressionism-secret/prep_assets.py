"""Prepare the pictures for 你知道印象派的秘密吗？ (run with Pillow + numpy + scipy).

Sources live outside the repo (the repo is public; media is not committed):
  lucas-academy-video-data/impressionism-secret/public/{art,portraits,codex}
which public/impressionism-secret links to. This script writes, beside them:
  img/<id>.jpg|png      every picture the film uses, long side <= 2400
  tiles/<id>.jpg        <= 800 px copies for walls and strips
  masks/<id>.png        soft white = stays sharp in a focus pull (AI real scenes)
  lift/<id>.png         self-portrait subject on transparency, same frame as the original
  glow/<id>.png         gold edge of that subject, for the "extraction" moment
  img/salon-wide.jpg    the wide Salon painting with the period's Salon paintings in its empty frames
and src/videos/impressionism-secret/assets.generated.ts (ids and sizes).

The subject lift uses macOS Vision through scripts/impressionism-secret/cutout.swift.
"""
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
PUB = (ROOT / "public/impressionism-secret").resolve()
OUT_TS = ROOT / "src/videos/impressionism-secret/assets.generated.ts"
MAX = 2400

ART = [
    "meissonier-1814", "daguerre-boulevard", "muybridge-horse-in-motion", "salon-meissonier-friedland",
    "titian-venus-urbino", "manet-olympia", "manet-luncheon", "manet-fifer", "manet-railway", "manet-monet-studio-boat",
    "manet-morisot-violets", "monet-impression-sunrise", "monet-woman-parasol", "monet-gare-saint-lazare",
    "monet-women-garden", "monet-camille-green-dress", "monet-red-kerchief", "monet-camille-bench",
    "monet-la-japonaise", "monet-camille-deathbed", "degas-orchestra-opera", "degas-place-concorde",
    "degas-dance-class", "hiroshige-sudden-shower", "morisot-cradle", "morisot-harbor-lorient",
    "renoir-moulin-galette", "cezanne-sainte-victoire-viaduct", "cezanne-sainte-victoire-late",
    "cezanne-basket-of-apples", "seurat-grande-jatte", "seurat-grande-jatte-detail", "nadar-studio-1860",
    "monet-nadar-1899", "salon-bonheur-horse-fair", "salon-bastien-lepage-joan", "salon-breton-song-of-lark",
    "salon-bouguereau-breton", "salon-delaroche-napoleon-alps",
    # v10 (owner 2026-11-04): the paintings the owner's Muse dance clips were made from, and Monet's 1890 haystacks
    "degas-etoile", "degas-rehearsal-stage", "degas-waiting", "degas-barre", "degas-blue-dancers",
    "renoir-bougival", "renoir-dance-city", "monet-haystacks",
]
# v10 (owner 2026-11-04): "不需要 codex 生成的图了", then the same day: "codex 图不是完全不用吧 我的意思是和
# muse 重复就不用了，不重复的还可以用". Kept: the real-scene pictures no clip repeats. Dropped: the scenes a clip
# replays, and the Salon portrait family (portrait, wide Salon, in-between portraits, expressions), which the Muse
# Salon clips were made from. CODEX, MORPH, FOCUS, LIFT and the filled Salon stay listed for the record.
V10_NO_CODEX = True
V10_CODEX = ["real-fifer-1866", "real-concorde-1875", "real-cradle-1872", "real-apples-still-life"]
PORTRAITS = ["manet-self", "monet-self", "degas-self", "morisot-self", "renoir-self", "cezanne-self",
             "seurat-laurent", "pissarro-self", "zola-by-manet"]
LIFT = ["manet-self", "monet-self", "degas-self", "renoir-self", "cezanne-self", "pissarro-self"]  # pastel/drawing: oval frame instead
CODEX = ["salon-group-painting-v2", "salon-group-painting-wide", "salon-hall-empty", "manet-annoyed", "real-railway-1873",
         "real-sainte-victoire-light", "real-fifer-1866", "real-opera-pit-1870", "real-concorde-1875",
         "real-parasol-1875", "real-cradle-1872", "real-moulin-galette-1876", "real-grande-jatte-1884",
         "real-apples-still-life", "real-le-havre-dawn-1872", "expr-degas", "expr-renoir", "expr-cezanne",
         "salon-group-4k", "salon-wide-4k"]
# Portrait → character in-between paintings (Codex), two per painter, in codex/morph-<painter>-<1|2>.png
MORPH = [f"morph-{p}-{i}" for p in ("manet", "monet", "degas", "renoir", "morisot", "cezanne", "seurat") for i in (1, 2)]
# Focus pulls on the AI real scenes: the part the painter later left out stays sharp.
# ("ellipse"|"rect", x0, y0, x1, y1) in fractions; "people-out"/"people-in" use the Vision subject mask.
FOCUS = {
    "real-railway-1873": [("rect", 0.18, 0.20, 0.98, 0.78), "people-out"],
    "real-fifer-1866": [("rect", 0.0, 0.0, 1.0, 1.0), "people-out"],
    "real-opera-pit-1870": [("rect", 0.0, 0.0, 1.0, 0.36)],
    "real-concorde-1875": [("ellipse", 0.30, 0.05, 0.72, 0.98)],
    "real-parasol-1875": [("ellipse", 0.50, 0.12, 0.70, 0.30)],
    "real-cradle-1872": [("rect", 0.45, 0.0, 1.0, 0.95)],
    "real-moulin-galette-1876": [("ellipse", 0.05, 0.42, 0.75, 1.05)],
    "real-grande-jatte-1884": [("ellipse", 0.62, 0.15, 1.0, 0.98)],
    "real-apples-still-life": [("rect", 0.0, 0.55, 1.0, 0.82)],
    "real-le-havre-dawn-1872": [("rect", 0.0, 0.0, 1.0, 0.62)],
    "real-sainte-victoire-light": [("ellipse", -0.05, -0.1, 0.78, 0.52)],
}
# The wide Salon's seven empty canvases, left to right, filled with paintings the Salon admired.
SALON_FILL = ["salon-delaroche-napoleon-alps", "salon-bouguereau-breton", "salon-meissonier-friedland",
              "meissonier-1814", "salon-bonheur-horse-fair", "salon-breton-song-of-lark", "salon-bastien-lepage-joan"]


def find_source(name: str) -> Path:
    for folder in ("art", "portraits", "codex"):
        for ext in (".jpg", ".png"):
            p = PUB / folder / f"{name}{ext}"
            if p.exists():
                return p
    raise FileNotFoundError(name)


def save_scaled(im: Image.Image, path: Path, limit: int) -> Image.Image:
    im = im.copy()
    im.thumbnail((limit, limit), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".png":
        im.save(path, optimize=True)
    else:
        im.convert("RGB").save(path, quality=90)
    return im


_cutout_bin = None


def subject_alpha(src: Path) -> Image.Image:
    """Vision subject mask (L), full frame."""
    global _cutout_bin
    if _cutout_bin is None:
        _cutout_bin = Path(tempfile.mkdtemp()) / "cutout"
        subprocess.run(["swiftc", "-O", str(ROOT / "scripts/impressionism-secret/cutout.swift"), "-o", str(_cutout_bin)], check=True)
    out = Path(tempfile.mkdtemp()) / "lift.png"
    subprocess.run([str(_cutout_bin), str(src), str(out)], check=True, capture_output=True)
    return Image.open(out).convert("RGBA").split()[3]


def focus_mask(name: str, size: tuple[int, int], src: Path) -> Image.Image:
    w, h = size
    m = Image.new("L", size, 0)
    from PIL import ImageDraw
    d = ImageDraw.Draw(m)
    people = None
    for spec in FOCUS[name]:
        if isinstance(spec, str):
            people = subject_alpha(src).resize(size).filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(6))
            continue
        kind, x0, y0, x1, y1 = spec
        box = [int(w * x0), int(h * y0), int(w * x1), int(h * y1)]
        (d.ellipse if kind == "ellipse" else d.rectangle)(box, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(int(w * 0.035)))
    if people is not None:
        m = ImageChops.multiply(m, ImageChops.invert(people))
    return m


def homography(src_pts, dst_pts):
    """Coefficients for Image.transform(PERSPECTIVE): maps output (dst) points back to input (src)."""
    a = []
    for (x, y), (u, v) in zip(dst_pts, src_pts):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    b = [c for p in src_pts for c in p]
    return np.linalg.solve(np.array(a, float), np.array(b, float))


def fill_salon(wide: Image.Image) -> Image.Image:
    """Put real Salon paintings into the empty grey canvases, in perspective."""
    arr = np.asarray(wide.convert("RGB")).astype(int)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    grey = (abs(r - g) < 14) & (abs(g - b) < 16) & (r > 35) & (r < 105)
    grey = ndimage.binary_opening(grey, iterations=3)
    labels, n = ndimage.label(grey)
    sizes = ndimage.sum(grey, labels, range(1, n + 1))
    big = sorted([i + 1 for i, s in enumerate(sizes) if s > wide.width * wide.height * 0.004],
                 key=lambda i: ndimage.center_of_mass(grey, labels, i)[1])
    if len(big) != len(SALON_FILL):
        raise SystemExit(f"expected {len(SALON_FILL)} empty canvases, found {len(big)}")
    out = wide.convert("RGB").copy()
    for lab, name in zip(big, SALON_FILL):
        ys, xs = np.nonzero(labels == lab)
        s, d_ = xs + ys, xs - ys
        quad = [(xs[s.argmin()], ys[s.argmin()]), (xs[d_.argmax()], ys[d_.argmax()]),
                (xs[s.argmax()], ys[s.argmax()]), (xs[d_.argmin()], ys[d_.argmin()])]  # tl, tr, br, bl
        art = Image.open(find_source(name)).convert("RGB")
        qw = max(np.hypot(quad[1][0] - quad[0][0], quad[1][1] - quad[0][1]), 1)
        qh = max(np.hypot(quad[3][0] - quad[0][0], quad[3][1] - quad[0][1]), 1)
        # cover-crop the painting to the canvas's proportions
        target = qw / qh
        aw, ah = art.size
        if aw / ah > target:
            nw = int(ah * target); art = art.crop(((aw - nw) // 2, 0, (aw - nw) // 2 + nw, ah))
        else:
            nh = int(aw / target); art = art.crop((0, (ah - nh) // 2, aw, (ah - nh) // 2 + nh))
        aw, ah = art.size
        coeffs = homography([(0, 0), (aw, 0), (aw, ah), (0, ah)], quad)
        warped = art.transform(out.size, Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC)
        mask = Image.fromarray(((labels == lab) * 255).astype("uint8")).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
        # a touch of the painting's own light and texture over the inserted picture
        warped = Image.blend(warped, ImageEnhance.Brightness(warped).enhance(0.92), 0.5).filter(ImageFilter.GaussianBlur(0.6))
        out.paste(warped, (0, 0), mask)
    return out


def main() -> None:
    sizes = {}
    for name in ART + PORTRAITS + (V10_CODEX if V10_NO_CODEX else CODEX + MORPH):
        src = find_source(name)
        im = Image.open(src)
        ext = ".png" if im.mode == "RGBA" else ".jpg"
        # the 4K Salon pictures stay 4K: the camera pushes in to single faces
        big = save_scaled(im, PUB / "img" / f"{name}{ext}", 3840 if name.endswith("-4k") else MAX)
        save_scaled(im.convert("RGB"), PUB / "tiles" / f"{name}.jpg", 800)
        sizes[name] = {"w": big.width, "h": big.height, "ext": ext}

    sizes.update(clips())
    if V10_NO_CODEX:
        write_ts(sizes)
        return
    wide = fill_salon(Image.open(find_source("salon-group-painting-wide")))
    big = save_scaled(wide, PUB / "img/salon-wide.jpg", MAX)
    save_scaled(wide, PUB / "tiles/salon-wide.jpg", 800)
    sizes["salon-wide"] = {"w": big.width, "h": big.height, "ext": ".jpg"}

    for name in FOCUS:
        src = find_source(name)
        w, h = sizes[name]["w"], sizes[name]["h"]
        save_scaled(focus_mask(name, Image.open(src).size, src).resize((w, h)), PUB / "masks" / f"{name}.png", MAX)

    for name in LIFT:
        src = find_source(name)
        orig = Image.open(src).convert("RGB")
        alpha = subject_alpha(src).resize(orig.size)
        lifted = orig.convert("RGBA"); lifted.putalpha(alpha)
        save_scaled(lifted, PUB / "lift" / f"{name}.png", MAX)
        edge = ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(9)), alpha.filter(ImageFilter.MinFilter(3)))
        edge = edge.point(lambda v: 255 if v > 40 else 0).filter(ImageFilter.GaussianBlur(3))
        glow = Image.new("RGBA", orig.size, (255, 214, 110, 0)); glow.putalpha(edge)
        save_scaled(glow, PUB / "glow" / f"{name}.png", MAX)

    # Seurat's dots as screen pixels: the detail averaged into a 40 x 40 grid.
    det = Image.open(find_source("seurat-grande-jatte-detail")).convert("RGB")
    det.resize((40, 40), Image.BOX).resize((800, 800), Image.NEAREST).save(PUB / "img/seurat-pixels.png")
    sizes["seurat-pixels"] = {"w": 800, "h": 800, "ext": ".png"}

    write_ts(sizes)


# The owner's generated clips (Muse; one MiniMax), all played from their 60 fps copies <name>.i60.mp4.
# `art` = the painting a clip was registered to (satie-gymnopedies align_video.py): the clip then sits
# exactly on the painting, and `inner` is the part of the frame the clip covers.
CLIP_ART = {"dance-class": ("degas-dance-class", "dance-class-c"), "etoile": ("degas-etoile", "etoile-b"),
            "rehearsal-stage": ("degas-rehearsal-stage", "rehearsal-stage"), "waiting": ("degas-waiting", "waiting"),
            "barre": ("degas-barre", "barre"), "bougival": ("renoir-bougival", "bougival"),
            "dance-city": ("renoir-dance-city", "dance-city")}
CLIP_NAMES = ["gen-opera", "gen-train-trim", "gen-le-havre", "gen-moulin", "gen-sainte-victoire", "minimax-parasol",
              "muse-parasol", "muse-m3", "dance-class", "etoile", "rehearsal-stage", "waiting", "barre",
              "bougival", "dance-city", "blue-dancers"]


def clips() -> dict:
    out = {}
    for name in CLIP_NAMES:
        f = PUB / "video" / f"{name}.i60.mp4"
        if not f.exists():
            print("missing clip", f.name)
            continue
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                "stream=width,height,nb_frames", "-of", "csv=p=0", str(f)], capture_output=True, text=True, check=True)
        w, h, n = (int(v) for v in probe.stdout.strip().split(","))
        c = {"w": w, "h": h, "frames60": n}
        if name in CLIP_ART:
            meta = json.loads((PUB / "video/src-gymnopedies" / f"{CLIP_ART[name][1]}.json").read_text())
            c.update(art=CLIP_ART[name][0], inner=meta["inner_x0y0x1y1"])
        out[name] = c
    return {"__clips__": out}


def write_ts(sizes: dict) -> None:
    clip = sizes.pop("__clips__", {})
    lines = ["// Generated by scripts/impressionism-secret/prep_assets.py — do not edit.",
             "export const IMG = " + json.dumps(sizes, indent=1) + " as const;",
             "export type ImgId = keyof typeof IMG;",
             "export const CLIPS: Record<string, {w: number; h: number; frames60: number; art?: string; inner?: number[]}> = "
             + json.dumps(clip, indent=1) + ";",
             "export type ClipId = keyof typeof CLIPS;"]
    OUT_TS.write_text("\n".join(lines) + "\n")
    print(f"{len(sizes)} pictures, {len(clip)} clips")


# Codex covers (owner 2026-11-04): the B2 pair repainted by Codex inside the Salon hall (references: the B2 cover and
# codex/salon-cover-bg.png), name -> extra background blur in px at 1920 wide. a = the B2 framing, b = pulled back to the waist.
COVERS = {"cover-salon-a": 3, "cover-salon-b": 6}


def cover() -> None:
    """img/<name>.jpg, 1920 x 1080: the Codex picture with the hall behind the pair blurred a little more (Vision mask),
    for "封面背景用虚化的沙龙背景"."""
    for name, blur in COVERS.items():
        src = find_source(name)
        im = Image.open(src).convert("RGB")
        w, h = im.size
        ch = round(w * 9 / 16)
        box = (0, (h - ch) // 2, w, (h - ch) // 2 + ch)
        im = im.crop(box).resize((1920, 1080), Image.LANCZOS)
        alpha = subject_alpha(src).crop(box).resize(im.size).filter(ImageFilter.GaussianBlur(1.5))
        Image.composite(im, im.filter(ImageFilter.GaussianBlur(blur)), alpha).save(PUB / "img" / f"{name}.jpg", quality=92)


if __name__ == "__main__":
    import sys
    cover() if sys.argv[1:] == ["cover"] else main()
