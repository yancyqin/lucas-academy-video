"""Invisible-noise pictures (targeted PGD adversarial examples) for round 2 of the bread-or-dog test.

The noise is computed against one model at a time, using that model's own gradients (white-box):
  adv1  Shiba (img02)      vs ResNet-50  -> pushed to "French loaf"
  adv2  sourdough (img05)  vs ResNet-50  -> pushed to "Pembroke" (corgi)
  adv3  Shiba (img02)      vs CLIP B/32  -> pushed to "a photo of bread."
  adv4  sourdough (img05)  vs CLIP B/32  -> pushed to "a photo of a dog."
  adv0a / adv0b  the same 448 x 448 crops with no noise (control)
Every pixel moves by at most EPS = 4/255 (about 1.6 %). Saved as PNG (JPEG would wipe the noise).
Each model sees the picture through its own standard preprocessing, written here as differentiable torch ops;
old_models.py then re-checks the saved PNGs through the ordinary PIL pipelines.
Also writes round2/adv_viz/<k>_noise.png (noise x 25, grey = 0) for the film.

Run with the seed-vc venv:  .../svc/seed-vc/.venv/bin/python -I adversarial.py
"""
import json, os
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")  # antialiased resize has no MPS backward
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import models
from torchvision.transforms.functional import to_tensor, to_pil_image

DATA = os.path.expanduser("~/repo/playground/lucas-academy-video-data/bread-or-dog")
R2 = f"{DATA}/round2"
DEV = "mps" if torch.backends.mps.is_available() else "cpu"
EPS, ALPHA, STEPS, S = 4 / 255, 0.5 / 255, 300, 448


def crop(k):
    im = Image.open(f"{DATA}/test/{k}.jpg").convert("RGB")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((S, S), Image.LANCZOS)
    return to_tensor(im).unsqueeze(0)


def resnet_fn():
    w = models.ResNet50_Weights.IMAGENET1K_V1
    m = models.resnet50(weights=w).eval().to(DEV)
    cats = w.meta["categories"]
    mean = torch.tensor([0.485, 0.456, 0.406], device=DEV).view(1, 3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225], device=DEV).view(1, 3, 1, 1)

    def logits(x):  # Resize(256, bilinear, antialias) -> CenterCrop(224) -> Normalize
        x = F.interpolate(x, size=(256, 256), mode="bilinear", antialias=True, align_corners=False)
        x = x[:, :, 16:240, 16:240]
        return m((x - mean) / std)
    return logits, cats


def clip_fn():
    from transformers import CLIPModel, CLIPProcessor
    mid = "openai/clip-vit-base-patch32"
    m = CLIPModel.from_pretrained(mid).eval().to(DEV)
    proc = CLIPProcessor.from_pretrained(mid)
    t = proc(text=["a photo of a dog.", "a photo of bread."], return_tensors="pt", padding=True).to(DEV)
    with torch.no_grad():
        tf = m.get_text_features(**t)
        tf = tf / tf.norm(dim=-1, keepdim=True)
    mean = torch.tensor(proc.image_processor.image_mean, device=DEV).view(1, 3, 1, 1)
    std = torch.tensor(proc.image_processor.image_std, device=DEV).view(1, 3, 1, 1)

    def logits(x):  # Resize(224, bicubic) -> Normalize
        x = F.interpolate(x, size=(224, 224), mode="bicubic", antialias=True, align_corners=False).clamp(0, 1)
        f = m.get_image_features(pixel_values=(x - mean) / std)
        f = f / f.norm(dim=-1, keepdim=True)
        return m.logit_scale.exp() * f @ tf.T
    return logits, ["dog", "bread"]


def pgd(logits, x0, target):
    x0 = x0.to(DEV)
    tgt = torch.tensor([target], device=DEV)
    delta = torch.zeros_like(x0, requires_grad=True)
    for i in range(STEPS):
        loss = F.cross_entropy(logits((x0 + delta).clamp(0, 1)), tgt)
        loss.backward()
        with torch.no_grad():
            delta -= ALPHA * delta.grad.sign()
            delta.clamp_(-EPS, EPS)
            delta.copy_((x0 + delta).clamp(0, 1) - x0)
        delta.grad = None
    x = (x0 + delta.detach()).clamp(0, 1)
    return (x * 255).round() / 255  # what a PNG will hold


def report(logits, names, x):
    with torch.no_grad():
        p = logits(x.to(DEV)).softmax(-1)[0].cpu()
    v, i = p.topk(min(3, len(names)))
    return [(names[j], round(float(q), 3)) for q, j in zip(v, i)]


def main():
    os.makedirs(f"{R2}/test", exist_ok=True)
    os.makedirs(f"{R2}/adv_viz", exist_ok=True)
    shiba, sour = crop("img02"), crop("img05")
    out = {}
    to_pil_image(shiba[0]).save(f"{R2}/test/adv0a.png")
    to_pil_image(sour[0]).save(f"{R2}/test/adv0b.png")
    out["adv0a"] = {"truth": "dog", "what": "img02 (Shiba) 448 px square crop, no noise (control)", "source": "img02"}
    out["adv0b"] = {"truth": "bread", "what": "img05 (sourdough) 448 px square crop, no noise (control)", "source": "img05"}

    for model, fn, jobs in [("ResNet-50", resnet_fn, [("adv1", "img02", shiba, "French loaf", "dog"),
                                                       ("adv2", "img05", sour, "Pembroke", "bread")]),
                            ("CLIP ViT-B/32", clip_fn, [("adv3", "img02", shiba, "bread", "dog"),
                                                        ("adv4", "img05", sour, "dog", "bread")])]:
        logits, names = fn()
        for k, src, x0, target, truth in jobs:
            before = report(logits, names, x0)
            x = pgd(logits, x0, names.index(target))
            after = report(logits, names, x)
            to_pil_image(x[0].cpu()).save(f"{R2}/test/{k}.png")
            d = (x.cpu() - x0)[0]
            to_pil_image((d * 25 + 0.5).clamp(0, 1)).save(f"{R2}/adv_viz/{k}_noise.png")
            out[k] = {"truth": truth, "what": f"{src} + invisible noise computed against {model}, pushed to '{target}' (max {round(EPS * 255)}/255 per pixel)",
                      "source": src, "attacked": model, "target": target, "before": before, "after": after,
                      "max_change": round(float(d.abs().max() * 255), 1), "mean_change": round(float(d.abs().mean() * 255), 2)}
            print(model, k, "before", before, "after", after, "max", out[k]["max_change"], "/255")
    json.dump(out, open(f"{R2}/adversarial.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
