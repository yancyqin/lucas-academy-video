"""Chinese labels on the Nobel committee's illustrations for the Chinese film.

    python3 scripts/fun-informatics-04/nobel_zh.py

Each English label is covered with the colour around it and the Chinese written in its place, in white, the size of
the line it replaces. Nothing else in the drawing changes; the credit (Mattias Karlén) stays on screen as before.
Boxes are in the 0.8x preview's pixels (the originals are 1.25x larger). Reads public/fun-informatics-04/footage/nobel/,
writes public/fun-informatics-04/stills/nobel-<key>.zh.jpg.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "public/fun-informatics-04/footage/nobel"
OUT = ROOT / "public/fun-informatics-04/stills"
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
SCALE = 1.25

LABELS = {  # key: [(x0, y0, x1, y1) in the preview, Chinese]
    "alga": [((583, 178, 700, 214), "眼点"), ((285, 620, 430, 657), "约 0.015 毫米"), ((250, 664, 468, 700), "衣藻"),
             ((968, 634, 1210, 672), "往光游")],
    "frog": [((138, 110, 370, 148), "衣藻里的"), ((180, 148, 328, 186), "这段基因"), ((198, 518, 310, 556), "卵"),
             ((228, 773, 296, 810), "青蛙"), ((695, 225, 760, 262), "离子"), ((872, 225, 975, 262), "关着"),
             ((1565, 160, 1642, 198), "光"), ((1562, 225, 1645, 262), "开了"), ((1572, 582, 1636, 618), "离子"),
             ((1508, 748, 1700, 786), "电信号")],
    "neuron": [((142, 88, 432, 125), "通道视紫红质"), ((210, 128, 362, 165), "的基因"), ((797, 88, 877, 126), "光"),
               ((150, 528, 310, 566), "神经细胞"), ((1557, 133, 1637, 172), "光"), ((1470, 350, 1534, 386), "离子"),
               ((1420, 538, 1512, 618), "神经\n信号")],
    "mouse": [((130, 80, 420, 118), "通道视紫红质"), ((200, 118, 350, 158), "的基因"), ((1150, 186, 1330, 225), "光纤"),
              ((1775, 124, 1868, 204), "神经\n信号")],
}


def ring_colour(a: np.ndarray, box: tuple) -> tuple:
    """The median colour of a thin ring just outside the box: the background the label sat on."""
    x0, y0, x1, y1 = box
    h, w = a.shape[:2]
    pad = 6
    parts = [a[max(y0 - pad, 0):y0, x0:x1], a[y1:min(y1 + pad, h), x0:x1], a[y0:y1, max(x0 - pad, 0):x0], a[y0:y1, x1:min(x1 + pad, w)]]
    px = np.concatenate([p.reshape(-1, 3) for p in parts if p.size])
    return tuple(int(v) for v in np.median(px, axis=0))


def main() -> None:
    for key, labels in LABELS.items():
        img = Image.open(SRC / f"{key}.jpg").convert("RGB")
        a = np.asarray(img)
        draw = ImageDraw.Draw(img)
        for (bx, text) in labels:
            x0, y0, x1, y1 = (int(round(v * SCALE)) for v in bx)
            draw.rectangle((x0, y0, x1, y1), fill=ring_colour(a, (x0, y0, x1, y1)))
            rows = text.split("\n")
            size = int((y1 - y0) / len(rows) * 0.82)
            font = ImageFont.truetype(FONT, size, index=0)
            cx = (x0 + x1) / 2
            for i, row in enumerate(rows):
                cy = y0 + (i + 0.5) * (y1 - y0) / len(rows)
                draw.text((cx, cy), row, font=font, fill=(255, 255, 255), anchor="mm")
        img.save(OUT / f"nobel-{key}.zh.jpg", quality=92)
        print("nobel", key)


if __name__ == "__main__":
    main()
