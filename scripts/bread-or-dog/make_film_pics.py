"""Pictures made for the v0.4 film (not test pictures) -> lucas-academy-video-data/bread-or-dog/film-pics/

  texture-fur.jpg, texture-crust.jpg   close crops for 「毛茸茸的狗，和烤得金黄的面包，纹理就很像」 (img02 fur, img05 crust)
  data-wall.jpg                        every Pexels search thumbnail from round 1 (candidates/pexels/*), tiled, for
                                       「几亿张配了文字的图片」 (a stand-in: these are our own 125 photos, not CLIP's data)

Run with the seed-vc venv python (it has PIL):  .../svc/seed-vc/.venv/bin/python -I make_film_pics.py
"""
import glob, os, random
from PIL import Image

DATA = os.path.expanduser("~/repo/playground/lucas-academy-video-data/bread-or-dog")
OUT = f"{DATA}/film-pics"


def main():
    os.makedirs(OUT, exist_ok=True)
    fur = Image.open(f"{DATA}/test/img02.jpg").convert("RGB").crop((430, 250, 690, 510))   # the Shiba's back
    crust = Image.open(f"{DATA}/test/img05.jpg").convert("RGB").crop((520, 330, 780, 590))  # the sourdough's crust
    for im, name in ((fur, "texture-fur.jpg"), (crust, "texture-crust.jpg")):
        im.resize((900, 900), Image.LANCZOS).save(f"{OUT}/{name}", quality=92)
    tiles = sorted(glob.glob(f"{DATA}/candidates/pexels/*/*.jpg"))
    random.Random(7).shuffle(tiles)
    T, cols = 160, 24
    rows = (len(tiles) * 3 + cols - 1) // cols  # each photo up to three times, so the wall is dense
    wall = Image.new("RGB", (cols * T, rows * T), "black")
    seq = (tiles * 3)[: cols * rows]
    for n, p in enumerate(seq):
        im = Image.open(p).convert("RGB")
        w, h = im.size
        s = min(w, h)
        im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((T - 4, T - 4), Image.LANCZOS)
        wall.paste(im, ((n % cols) * T + 2, (n // cols) * T + 2))
    wall.save(f"{OUT}/data-wall.jpg", quality=85)
    print("wrote", sorted(os.listdir(OUT)), wall.size, len(tiles), "photos")


if __name__ == "__main__":
    main()
