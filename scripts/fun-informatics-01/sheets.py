"""Storyboard sheets: one frame of the finished Chinese film per narration line, labelled with its id and start time.

  ../lucas-academy-media/.conda/bin/python scripts/fun-informatics-01/sheets.py [OUT_DIR]

Takes each line's frame at 75% of its speech from out/fun-informatics-01/delivery/fun-informatics-01.zh.mp4
and writes OUT_DIR/storyboard-1.jpg (IT00–IT05) and storyboard-2.jpg (IT06–IT11).
OUT_DIR defaults to out/fun-informatics-01/storyboard-sheets. Needs Pillow (the lucas-academy-media env has it).
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FILM = ROOT / "out/fun-informatics-01/delivery/fun-informatics-01.zh.mp4"
COLS, W, H, CAP = 5, 480, 270, 28


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "out/fun-informatics-01/storyboard-sheets"
    out.mkdir(parents=True, exist_ok=True)
    tl = json.loads((ROOT / "public/fun-informatics-01/timeline.zh.json").read_text())
    for c in tl["cues"]:
        t = c["speech"]["start"] + 0.75 * (c["speech"]["end"] - c["speech"]["start"])
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(FILM), "-frames:v", "1",
                        "-vf", f"scale={W}:{H}", str(out / f"{c['id']}.png")], check=True)
    start = {c["id"]: c["start"] for c in tl["cues"]}
    ids = [c["id"] for c in tl["cues"]]
    sections = sorted({i[:4] for i in ids})
    font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 18)
    for n, group_sections in enumerate([sections[:6], sections[6:]], 1):
        group = [i for i in ids if i[:4] in group_sections]
        rows = (len(group) + COLS - 1) // COLS
        sheet = Image.new("RGB", (COLS * W, rows * (H + CAP)), (22, 24, 30))
        draw = ImageDraw.Draw(sheet)
        for k, i in enumerate(group):
            x, y = (k % COLS) * W, (k // COLS) * (H + CAP)
            sheet.paste(Image.open(out / f"{i}.png").convert("RGB"), (x, y + CAP))
            t = start[i]
            draw.text((x + 6, y + 4), f"{i}  {int(t // 60)}:{int(t % 60):02d}", fill=(127, 227, 255), font=font)
        sheet.save(out / f"storyboard-{n}.jpg", quality=88)
        print(out / f"storyboard-{n}.jpg", sheet.size, len(group))


if __name__ == "__main__":
    main()
