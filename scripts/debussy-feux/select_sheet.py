"""select_sheet.py — numbered contact sheets of fireworks-film candidates for the owner to choose from."""
import cv2, numpy as np, json
from PIL import Image, ImageDraw, ImageFont
D = "/Users/yqin/repo/playground/lucas-academy-video-data/debussy-impressions"
OUT = f"{D}/feux"
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
A = [  # (id, zh, en/artist, note)
 ("fire-1", "坠落的火箭", "Whistler · Nocturne in Black and Gold – The Falling Rocket · 1875", "画里就有焰火"),
 ("night-3", "旧巴特西桥", "Whistler · Nocturne: Blue and Gold – Old Battersea Bridge · c.1872–75", "右上有焰火"),
 ("feux-gardens", "黑与金的夜曲：花园", "Whistler · Nocturne in Black and Gold, The Gardens · 1876", "夜里的游乐园"),
 ("feux-firewheel", "火轮", "Whistler · Nocturne: Black and Gold – The Fire Wheel · 1875", "焰火轮（图小）"),
 ("feux-lights", "克里莫恩的灯", "Whistler · Nocturne: Blue and Silver – Cremorne Lights · 1872", "河边灯火（图小）"),
 ("feux-ensor", "焰火", "James Ensor · Fireworks · 1887", "画里就有焰火（图小）"),
 ("feux-cremorne", "克里莫恩花园 2 号", "Whistler · Cremorne Gardens, No. 2 · 1872–77", "黄昏花园、灯笼"),
 ("feux-sargent", "康乃馨、百合、玫瑰", "Sargent · Carnation, Lily, Lily, Rose · 1885–86", "黄昏点灯笼的孩子"),
 ("night-1", "夜晚的蒙马特大道", "Pissarro · The Boulevard Montmartre at Night · 1897", "城市夜灯"),
 ("feux-korovin", "巴黎夜晚的林荫道", "Korovin · Parisian Boulevard at Night · c.1908", "城市夜灯"),
 ("feux-ury", "莱比锡大街", "Lesser Ury · Leipziger Straße · 1889", "雨夜街灯"),
 ("feux-cafe", "夜间露天咖啡馆", "Van Gogh · Café Terrace at Night · 1888", "星空、灯"),
 ("night-2", "罗讷河上的星夜", "Van Gogh · Starry Night over the Rhône · 1888", "星空、河"),
 ("feux-sangiorgio", "黄昏的圣乔治马焦雷", "Monet · San Giorgio Maggiore at Dusk · 1908", "黄昏、水面"),
 ("feux-parliament", "国会大厦·日落", "Monet · The Houses of Parliament, Sunset · 1903", "黄昏、泰晤士河"),
 ("feux-waterloo", "滑铁卢桥·日落", "Monet · Waterloo Bridge, London, at Sunset · 1904", "黄昏、桥"),
 ("feux-lavacourt", "拉瓦库尔的塞纳河日落", "Monet · Sunset on the Seine at Lavacourt, Winter · 1880", "冬日黄昏"),
 ("feux-sunrise", "日出·印象", "Monet · Impression, Sunrise · 1872", "港口晨曦（图小）"),
 ("feux-july14", "巴黎七月十四日", "Van Gogh · The Fourteenth of July Celebration in Paris · 1886", "国庆节（白天）"),
 ("fire-2", "蒙托格伊街的节日", "Monet · The Rue Montorgueil, 30 June 1878", "节日彩旗（白天）"),
 ("fire-3", "圣德尼街的节日", "Monet · Rue Saint-Denis, 30 June 1878", "节日彩旗（白天）"),
]
C = ["beijing-tower", "river-bridge", "marina", "dubrovnik", "moonrise-sea", "alicante-sail", "river-village", "cobble-street",
     "moonpath", "pink-moon-boat", "swiss-village", "eave-moon", "fishing-pier", "roof-moon", "milkyway-lake", "honfleur"]

def font(sz): return ImageFont.truetype(FONT, sz)
def tile(img_path, title, sub, note, n, tw=520, th=400, label_h=92):
    im = Image.open(img_path).convert("RGB"); im.thumbnail((tw, th - 6), Image.LANCZOS)
    t = Image.new("RGB", (tw, th + label_h), (24, 24, 26)); t.paste(im, ((tw - im.width) // 2, (th - im.height) // 2))
    d = ImageDraw.Draw(t)
    d.rectangle([0, 0, 64, 44], fill=(0, 0, 0)); d.text((10, 4), f"{n:02d}", font=font(30), fill=(255, 210, 90))
    d.text((10, th + 4), title, font=font(24), fill=(255, 255, 255))
    d.text((10, th + 36), sub[:62], font=font(15), fill=(190, 190, 190))
    d.text((10, th + 60), note, font=font(17), fill=(255, 200, 120))
    return t

def sheet(tiles, cols, path, head):
    tw, thh = tiles[0].size; rows = (len(tiles) + cols - 1) // cols
    S = Image.new("RGB", (cols * tw + (cols + 1) * 10, rows * thh + (rows + 1) * 10 + 70), (12, 12, 14))
    ImageDraw.Draw(S).text((14, 16), head, font=font(32), fill=(255, 255, 255))
    for i, t in enumerate(tiles): S.paste(t, (10 + (i % cols) * (tw + 10), 80 + (i // cols) * (thh + 10)))
    S.save(path, quality=86); print(path, S.size)

ta = []
for n, (pid, zh, en, note) in enumerate(A, 1):
    p = f"{D}/art/{pid}.jpg"; w, h = Image.open(p).size
    ta.append(tile(p, zh, en, f"{note} · {w}×{h}", n))
sheet(ta, 4, f"{OUT}/candidates-paintings.jpg", "焰火 · 候选名画（1–21）：有焰火 / 节日 / 夜景 / 黄昏")
tc = []
for n, k in enumerate(C, len(A) + 1):
    p = f"{D}/clair/paint/aligned/{k}.png"
    tc.append(tile(p, k, "《月光》里用过的照片→印象派画（有原照片）", "", n))
sheet(tc, 4, f"{OUT}/candidates-clair.jpg", "焰火 · 候选（22–37）：《月光》里的夜景画（原照片可直接做“变暗之前”）")
json.dump({"paintings": [a[0] for a in A], "clair": C}, open(f"{OUT}/candidates.json", "w"), indent=1)
