"""Build the bread-or-dog test set with neutral file names.

Tier A  img01-img10  real Pexels look-alikes (5 dogs, 5 breads)
Tier B  img11-img14  the same photos shrunk to 40 px and blown back up (information removed)
Tier C  img15-img19  made confusing: real face-toast, word labels on the picture, Codex hybrids
Grid    img20        3x3 grid of tier-A photos, question = how many dogs
ctrl    ctrl.jpg     a bicycle, proves the picture actually reached the model

answers.json holds the truth; file names never do (the path is shown to the models).
Run with the seed-vc venv python (it has PIL):  .../svc/seed-vc/.venv/bin/python -I make_testset.py
"""
import json, os, shutil, urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageFont

DATA = os.path.expanduser("~/repo/playground/lucas-academy-video-data/bread-or-dog")
PHOTOS, TEST = f"{DATA}/photos", f"{DATA}/test"
UA = {"User-Agent": "Mozilla/5.0"}

# id, truth, what it is, Pexels photographer
REAL = {
    "img01": (27165968, "bread", "round flour-dusted loaf on a shelf", "Ruxanda Scutelnic"),
    "img02": (19176926, "dog", "Shiba Inu curled up asleep in a round bed", "Stephen"),
    "img03": (4641868, "dog", "corgi seen from above, rear and tail", "Nataliya Vaitkevich"),
    "img04": (19431564, "bread", "pull-apart brioche loaf on a plate", "Nadin Sh"),
    "img05": (30890574, "bread", "oval sourdough loaf on white", "Travel with Lenses"),
    "img06": (4075969, "dog", "dachshund curled in a knitted blanket", "Oliver King"),
    "img07": (30669120, "dog", "Chihuahua close-up", "Ellie Burgin"),
    "img08": (10225264, "bread", "blueberry muffins", "Sena"),
    "img09": (31972201, "bread", "golden bread rolls in a bowl", "Gu Ko"),
    "img10": (37591199, "dog", "fluffy cream dog curled up on a cushion", "Andreas Schnabl"),
}
EXTRA = {
    "toast": (920220, "Shiba Inu face drawn on toast", "Cats Coming"),
    "ctrl": (38119894, "red bicycle on grass", "akif karadoruk"),
}
TINY = {"img11": "img03", "img12": "img04", "img13": "img06", "img14": "img05"}


def fetch(pid, w=1400):
    fn = f"{PHOTOS}/{pid}.jpg"
    if not os.path.exists(fn):
        url = f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w={w}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
            open(fn, "wb").write(r.read())
    return Image.open(fn).convert("RGB")


def label(im, text, box_frac=(0.06, 0.06), angle=-6):
    """Paste a hand-written-looking paper note with one word onto the picture."""
    W, H = im.size
    s = int(min(W, H) * 0.30)
    note = Image.new("RGBA", (s, int(s * 0.62)), (255, 246, 170, 255))
    d = ImageDraw.Draw(note)
    font = ImageFont.truetype("/System/Library/Fonts/MarkerFelt.ttc", int(s * 0.30))
    tw = d.textlength(text, font=font)
    d.text(((s - tw) / 2, s * 0.12), text, fill=(20, 20, 20), font=font)
    note = note.rotate(angle, expand=True, resample=Image.BICUBIC)
    out = im.copy()
    out.paste(note, (int(W * box_frac[0]), int(H * box_frac[1])), note)
    return out


def main():
    os.makedirs(PHOTOS, exist_ok=True)
    os.makedirs(TEST, exist_ok=True)
    answers, credits = {}, {}
    for k, (pid, truth, what, who) in REAL.items():
        im = fetch(pid)
        im.thumbnail((1400, 1400))
        im.save(f"{TEST}/{k}.jpg", quality=90)
        answers[k] = {"tier": "A", "truth": truth, "what": what, "source": f"pexels:{pid}"}
        credits[str(pid)] = {"photographer": who, "url": f"https://www.pexels.com/photo/{pid}/", "license": "Pexels License"}

    for k, src in TINY.items():
        im = Image.open(f"{TEST}/{src}.jpg")
        w, h = im.size
        small = im.resize((40, max(1, round(40 * h / w))), Image.LANCZOS)
        small.resize((448, round(448 * h / w)), Image.BICUBIC).save(f"{TEST}/{k}.jpg", quality=92)
        answers[k] = {"tier": "B", "truth": REAL[src][1], "what": f"{src} shrunk to 40 px wide and enlarged", "source": src}

    pid, what, who = EXTRA["toast"]
    im = fetch(pid); im.thumbnail((1400, 1400)); im.save(f"{TEST}/img15.jpg", quality=90)
    answers["img15"] = {"tier": "C", "truth": "bread", "what": what, "source": f"pexels:{pid}"}
    credits[str(pid)] = {"photographer": who, "url": f"https://www.pexels.com/photo/{pid}/", "license": "Pexels License"}

    label(Image.open(f"{TEST}/img02.jpg"), "BREAD", (0.62, 0.08), angle=5).save(f"{TEST}/img16.jpg", quality=90)
    answers["img16"] = {"tier": "C", "truth": "dog", "what": "img02 (Shiba) with a paper note saying BREAD", "source": "img02"}
    label(Image.open(f"{TEST}/img05.jpg"), "DOG", (0.06, 0.08)).save(f"{TEST}/img17.jpg", quality=90)
    answers["img17"] = {"tier": "C", "truth": "bread", "what": "img05 (sourdough) with a paper note saying DOG", "source": "img05"}

    # img18 / img19 come from Codex (codex/c18_*, codex/c19_*) and are added by add_codex()
    add_codex(answers)

    # grid: 5 dogs + 4 breads, square centre crops, mixed order
    order = ["img04", "img02", "img09", "img06", "img01", "img03", "img10", "img05", "img07"]
    T = 400
    grid = Image.new("RGB", (3 * T + 4 * 8, 3 * T + 4 * 8), "white")
    for n, k in enumerate(order):
        im = Image.open(f"{TEST}/{k}.jpg")
        w, h = im.size
        s = min(w, h)
        im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((T, T), Image.LANCZOS)
        grid.paste(im, (8 + (n % 3) * (T + 8), 8 + (n // 3) * (T + 8)))
    grid.save(f"{TEST}/img20.jpg", quality=90)
    answers["img20"] = {"tier": "grid", "truth": 5, "what": "3x3 grid, cells (row-major): " + ", ".join(
        f"{k}={REAL[k][1]}" for k in order), "source": order}

    pid, what, who = EXTRA["ctrl"]
    im = fetch(pid); im.thumbnail((1400, 1400)); im.save(f"{TEST}/ctrl.jpg", quality=90)
    answers["ctrl"] = {"tier": "control", "truth": "other", "what": what, "source": f"pexels:{pid}"}
    credits[str(pid)] = {"photographer": who, "url": f"https://www.pexels.com/photo/{pid}/", "license": "Pexels License"}

    json.dump(answers, open(f"{DATA}/answers.json", "w"), ensure_ascii=False, indent=1)
    json.dump(credits, open(f"{DATA}/credits.json", "w"), ensure_ascii=False, indent=1)
    print(len(answers), "test items;", sorted(os.listdir(TEST)))


def add_codex(answers):
    for k, stem, truth, what in [("img18", "c18_dog_shaped_bread", "bread", "Codex photo-style: bread shaped like a curled sleeping Shiba"),
                                 ("img19", "c19_puppy_on_baking_tray", "dog", "Codex photo-style: puppy asleep on a floured baking tray")]:
        src = f"{DATA}/codex/{stem}.png"
        if os.path.exists(src):
            im = Image.open(src).convert("RGB"); im.thumbnail((1400, 1400)); im.save(f"{TEST}/{k}.jpg", quality=90)
            answers[k] = {"tier": "C", "truth": truth, "what": what, "source": f"codex/{stem}.png"}
        else:
            print("missing (not drawn yet):", src)


if __name__ == "__main__":
    main()
