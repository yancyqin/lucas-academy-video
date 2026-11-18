"""Old vision models on the bread-or-dog set: AlexNet (2012), ResNet-50 (2015), CLIP ViT-B/32 (2021).

ImageNet has no "dog" or "bread" class, so the classifiers are read two ways:
  top-1 label (raw), and the summed probability of the 118 dog-breed classes vs the bread classes.
CLIP is asked zero-shot: "a photo of a dog." vs "a photo of bread." (it cannot say "neither").

Run with the seed-vc venv (torch + torchvision + transformers, nothing installed into it):
  ~/repo/playground/lucas-academy-video/svc/seed-vc/.venv/bin/python -I old_models.py
writes <data>/runs/old_models.jsonl  (--set r2: <data>/round2/runs/old_models.jsonl)
"""
import glob, json, os, sys
import torch
from PIL import Image
from torchvision import models

DATA = os.path.expanduser("~/repo/playground/lucas-academy-video-data/bread-or-dog")
DEV = "mps" if torch.backends.mps.is_available() else "cpu"
SKIP = {"img20"}  # grid: counting question, not for single-label classifiers


def groups(cats):
    dog = set(range(151, 269))  # ImageNet dog breeds, Chihuahua .. Mexican hairless
    bread_names = {"French loaf", "bagel", "pretzel", "dough"}
    bread = {i for i, c in enumerate(cats) if c in bread_names}
    assert len(dog) == 118 and len(bread) == 4, (len(dog), bread)
    assert cats[151] == "Chihuahua" and cats[268] == "Mexican hairless", (cats[151], cats[268])
    return dog, bread


def run_imagenet(name, ctor, weights, images, out):
    m = ctor(weights=weights).eval().to(DEV)
    tf, cats = weights.transforms(), weights.meta["categories"]
    dog, bread = groups(cats)
    for img in images:
        x = tf(Image.open(img).convert("RGB")).unsqueeze(0).to(DEV)
        with torch.no_grad():
            p = m(x).softmax(-1)[0].cpu()
        top = p.topk(5)
        top5 = [(cats[i], round(float(v), 3)) for v, i in zip(top.values, top.indices)]
        t1 = int(top.indices[0])
        verdict = "DOG" if t1 in dog else "BREAD" if t1 in bread else "NEITHER"
        rec = {"model": name, "image": os.path.basename(img).rsplit(".", 1)[0], "condition": "neutral",
               "verdict": verdict, "top1": top5[0][0], "top5": top5,
               "p_dog": round(float(p[list(dog)].sum()), 3), "p_bread": round(float(p[list(bread)].sum()), 3)}
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(name, rec["image"], verdict, top5[0], "dog", rec["p_dog"], "bread", rec["p_bread"])


def run_clip(images, out):
    from transformers import CLIPModel, CLIPProcessor
    mid = "openai/clip-vit-base-patch32"
    m = CLIPModel.from_pretrained(mid).eval().to(DEV)
    proc = CLIPProcessor.from_pretrained(mid)
    texts = ["a photo of a dog.", "a photo of bread."]
    for img in images:
        inp = proc(text=texts, images=Image.open(img).convert("RGB"), return_tensors="pt", padding=True).to(DEV)
        with torch.no_grad():
            p = m(**inp).logits_per_image.softmax(-1)[0].cpu()
        rec = {"model": "CLIP ViT-B/32 (2021)", "image": os.path.basename(img).rsplit(".", 1)[0], "condition": "neutral",
               "verdict": "DOG" if p[0] > p[1] else "BREAD", "p_dog": round(float(p[0]), 3), "p_bread": round(float(p[1]), 3)}
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("CLIP", rec["image"], rec["verdict"], rec["p_dog"], rec["p_bread"])


def main():
    base = DATA
    images = [f for f in sorted(glob.glob(f"{DATA}/test/*.jpg")) if os.path.basename(f)[:-4] not in SKIP]
    if "--set" in sys.argv and sys.argv[sys.argv.index("--set") + 1] == "r2":
        # round 2: every single picture asked the neutral question (res, text, scene2, adv); task items reuse round-1 photos
        base = f"{DATA}/round2"
        ans = json.load(open(f"{base}/answers.json"))
        images = [f"{base}/{a['file']}" if a.get("file") else f"{base}/test/{k}.jpg"
                  for k, a in ans.items() if "neutral" in a["asks"]]
    os.makedirs(f"{base}/runs", exist_ok=True)
    with open(f"{base}/runs/old_models.jsonl", "w") as out:
        run_imagenet("AlexNet (2012)", models.alexnet, models.AlexNet_Weights.IMAGENET1K_V1, images, out)
        run_imagenet("ResNet-50 (2015)", models.resnet50, models.ResNet50_Weights.IMAGENET1K_V1, images, out)
        run_clip(images, out)


if __name__ == "__main__":
    main()
