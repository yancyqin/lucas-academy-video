"""Time 「Challenge: Which Butterflies Are Real?」 from its narration takes: timeline, two mixes and both SRTs.

  /Users/yqin/repo/playground/lucas-academy-video/.venv-align/bin/python scripts/butterfly-challenge/build_timeline.py
      [--voice louise --speed 1.1] [--langs en,zh] [--upto N] [--tag NAME]

Writes public/butterfly-challenge/timeline.json (read by src/videos/butterfly-challenge/ButterflyChallengeVideo.tsx)
and out/butterfly-challenge/<tag>/{mix.<lang>.wav, butterfly-challenge.<lang>.srt for en and zh-Hans}.
--upto N stops after pair N's video (the voice test was --upto 2 with one language: --langs zh).

One picture, two voice tracks (Yancy, 2026-11-12: 「默认语言英文，配中文音轨」, louise 1.1 for both): every line gets one
slot, as long as the longer of its English and Chinese takes, and each language's take starts at its slot's start,
so either track fits the same picture (as 「动物想什么？AI 知道吗？」). Each language gets its own mix (its own lines duck
the music) and its own SRT; the other-language SRT of each track is the same timing with the paired line.

The film (script.zh.md): title over a mosaic of all twenty pictures, the intro, then for each pair the two pictures
exactly as the models saw them, a 5-4-3-2-1 count with no voice, the reveal (green ✓ on the real one, red ✗ on the AI one, each model's
pick, running score; a reveal line when the script has one), then the real video with its name while the narration
talks about it. A clip shorter than its narration slows down (60 fps clips to as little as half speed, others to
0.8x) and then holds its last frame with a slow push-in, or, when that hold would pass 3 s (pair 10), dissolves to
the pair's real photo and pushes in on that. The end: the final score, the AI pictures that fooled
both models, credits.

Scores come from the data folder (pairs/answers.json, experiment/{astra,fable}.json) and must equal the script's
per-pair lines, or the build stops. Music: Chopin, Grande valse brillante Op. 18 (Olga Gurevich, Musopen, CC0; data
music/SOURCES.md), one bed for the whole film through music_ducking.envelope (K. 265 until Yancy's 11-12 note).
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(HERE))
import music_ducking  # noqa: E402
import narrate  # noqa: E402

# 「跨越中等收入陷阱」's builder for decode, lufs, ffread, srt_pieces, stamp (same file name as this one, so by path)
_spec = importlib.util.spec_from_file_location("mit_build_timeline", ROOT / "scripts/middle-income-trap/build_timeline.py")
mit = importlib.util.module_from_spec(_spec)
_argv, sys.argv = sys.argv, sys.argv[:1]  # its module code reads --speed; keep ours away from it
_spec.loader.exec_module(mit)
sys.argv = _argv
import codex_hdphoto  # noqa: E402

args = sys.argv[1:]
VOICE = narrate.opt(args, "--voice", "louise")
SPEED = float(narrate.opt(args, "--speed", "1.1"))
QSPEED = float(narrate.opt(args, "--qspeed", str(SPEED)))
LANGS = narrate.opt(args, "--langs", "en,zh").split(",")
UPTO = int(narrate.opt(args, "--upto", "10"))
DATA = next(p / "lucas-academy-video-data" for p in ROOT.parents if (p / "lucas-academy-video-data").is_dir())
FILM = DATA / "butterfly-challenge"
# Yancy 11-12: 「不要用小星星了 … 我有喜欢的肖邦」 → Chopin, Grande valse brillante Op. 18, Olga Gurevich (Musopen 2012, CC0)
MUSIC = FILM / "music/raw/chopin-op18-gurevich-musopen.flac"
PUB = ROOT / "public/butterfly-challenge"
OUT = ROOT / "out/butterfly-challenge" / narrate.opt(args, "--tag", f"{VOICE}-{SPEED:.2f}-{'-'.join(LANGS)}")
SR = mit.SR
FPS = 30

TITLE = 2.5          # the title alone, music only (3.5 until Yancy's 「一开始废话太多了」, 2026-11-12)
GAP, QUESTION_GAP = 0.45, 1.0
INTRO_TAIL = 0.8     # after "OK, here is pair one." / 「好，第一对。」
PAIR_IN, COUNT = 0.4, 5.0   # pictures fade in, then exactly 5 s of 5-4-3-2-1 with no voice (Yancy 2026-11-12: 改成5秒以后公布答案)
REVEAL_LEAD, REVEAL_TAIL, REVEAL_MIN = 1.0, 0.8, 3.2
CLIP_LEAD, CLIP_TAIL, CLIP_MIN, XFADE, LONG_HOLD = 0.9, 1.6, 5.0, 0.5, 3.0
END_LEAD, END_TAIL, CREDITS = 1.2, 3.0, 9.0  # the tail lets the closing question breathe
BED_LUFS, FINAL_LUFS, FINAL_TP = -20.0, -16.0, -2.2
EN_MAX = 42

# the real videos, in pair order (script.zh.md 字卡; g1 is CC BY and is credited on screen)
CLIPS = [
    ("g1-greta-oto-commons", "玻璃翼蝶", "Glasswing", "Greta oto", 30, "Video: Brandon (Flickr: bpprice) · CC BY 2.0"),
    ("p08-2901459", "蓝摩门凤蝶", "Blue Mormon", "Papilio polymnestor", 30, ""),
    ("p15-5129671", "孔雀石蝶", "Malachite", "Siproeta stelenes", 24, ""),
    ("p16-5241558", "豹纹蛱蝶", "Leopard-spotted butterfly", "", 30, ""),
    ("p17-7855586", "孔雀蛱蝶", "European Peacock", "Aglais io", 24, ""),
    ("p18-8450772", "眼灰蝶", "Blue", "Polyommatus sp.", 30, ""),
    ("p26-16001770", "红斑紫蛱蝶", "Red-spotted Purple", "Limenitis arthemis astyanax", 60, ""),
    ("p44-38657643", "美洲黑凤蝶", "Black Swallowtail", "Papilio polyxenes", 60, ""),
    ("p67-36683557", "红带袖蝶", "Postman", "Heliconius sp.", 30, ""),
    ("p69-37672883", "鸟翼凤蝶", "Birdwing", "Ornithoptera sp.", 30, ""),
]
sys.path.insert(0, str(HERE))
from assets import USABLE  # noqa: E402

# A pair whose narration moves to a second clip: (clip key, fps, line, seconds into that line, on-screen credit).
# Pair 6: closed wings (grey) for 「合着翅膀是灰色的」, then the open-winged male for 「雄蝶打开翅膀，才是亮蓝色」 —
# Whisper puts 雄蝶 at 3.9 s into the zh take and "Only when a male" at 4.2 s into the en take.
SECOND = {6: ("c06-polyommatus-icarus-open-commons", 24, "sc06-01", 3.9, "Video: NaIzletuSi · CC BY 3.0")}


def pair_data():
    """Sides, picks and scores from the data folder, checked against the script's per-pair lines."""
    answers = json.loads((FILM / "pairs/answers.json").read_text())
    picks = {w: {r["n"]: r for r in json.loads((FILM / f"experiment/{w}.json").read_text())} for w in ("astra", "fable")}
    species = {k: s["species"].split(" ")[0] for k, s in codex_hdphoto.specs().items()}
    credits = json.loads((FILM / "photos/credits.json").read_text())
    script = (ROOT / "docs/butterfly-challenge/script.zh.md").read_text()
    said = re.findall(r"真的是 \*\*([AB])\*\*。Astra ([✓✗])，Fable ([✓✗])。比分 \*\*(\d+) : (\d+)\*\*", script)
    assert len(said) == 10, f"script has {len(said)} pair lines"
    out, sa, sf_ = [], 0, 0
    for a, (real, ca, cf, ta, tf) in zip(answers, said):
        n = a["n"]
        ra, rf = picks["astra"][n], picks["fable"][n]
        assert ra["real"] == rf["real"] == a["real"] == real, f"pair {n}: sides differ"
        assert ra["correct"] == (ca == "✓") and rf["correct"] == (cf == "✓"), f"pair {n}: script ✓/✗ differ from experiment"
        sa += ra["correct"]; sf_ += rf["correct"]
        assert (sa, sf_) == (int(ta), int(tf)), f"pair {n}: running score {sa}:{sf_} vs script {ta}:{tf}"
        slot = a["key"].split("-")[0]
        c = credits[slot]
        who = re.match(r"\(c\) (.+?), ", c["attribution"])
        photo = f"Photo: {who[1] + ' · ' if who else ''}iNaturalist · {c['license'].upper().replace('CC-BY', 'CC BY')}"
        key, zh, en, latin, fps, clip_credit = CLIPS[n - 1]
        assert key == a["key"]
        out.append({"n": n, "real": real, "ai": species[a["ai"]], "astra": ra["guess"], "fable": rf["guess"],
                    "astraOk": ra["correct"], "fableOk": rf["correct"], "score": [sa, sf_],
                    "photo": photo, "key": key, "name": {"zh": zh, "en": en, "latin": latin},
                    "clipCredit": clip_credit, "fps": fps})
    return out


def en_cues(text: str, start: float, end: float):
    """English captions: at most two lines of at most EN_MAX letters per cue, broken evenly between words, a cue
    ending at a sentence end where it can; timed by length."""
    def balanced(words):
        k = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
        return " ".join(words[:k]), " ".join(words[k:])

    def fits(words):
        if len(" ".join(words)) <= EN_MAX:
            return True
        return len(words) > 1 and all(len(x) <= EN_MAX for x in balanced(words))

    pieces, cur = [], []
    for w in text.split():
        if cur and not fits(cur + [w]):
            pieces.append(cur); cur = [w]
        else:
            cur.append(w)
            if re.search(r"[.?!:;]$", w) and len(" ".join(cur)) > EN_MAX:
                pieces.append(cur); cur = []
    if cur:
        pieces.append(cur)
    # never leave a word or two alone at the end (11-12: "detail." sat on screen for 0.4 s): rebalance the last two
    if len(pieces) > 1 and len(pieces[-1]) < 3:
        words = pieces[-2] + pieces[-1]
        k = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
        if fits(words[:k]) and fits(words[k:]):
            pieces[-2:] = [words[:k], words[k:]]
        elif fits(words):
            pieces[-2:] = [words]
    total, t = sum(len(" ".join(p)) + CUE_PAD for p in pieces), start
    for p in pieces:
        line = " ".join(p)
        d = (end - start) * (len(line) + CUE_PAD) / total
        if len(line) > EN_MAX:
            line = "\n".join(balanced(p))
        yield t, t + d, line
        t += d


CUE_PAD = 4  # a short cue gets a little more of its line's time, so nothing flashes by


def zh_cues(text: str, start: float, end: float):
    """Chinese captions as mit.srt_pieces (split after punctuation, merged up to SRT_MAX), but the limit counts
    characters, not the punctuation dropped from the cue's end (11-12: 「孔雀石」 alone for 0.7 s), and short cues get
    CUE_PAD more weight."""
    bare = lambda x: x.rstrip("，。；、！？：")  # noqa: E731
    parts = [q for q in re.split(r"(?<=[，。；：？！、])", text) if q.strip()]
    merged = []
    for q in parts:
        if merged and len(bare(merged[-1] + q)) <= mit.SRT_MAX:
            merged[-1] += q
        else:
            merged.append(q)
    total, t = sum(len(q) + CUE_PAD for q in merged), start
    for q in merged:
        d = (end - start) * (len(q) + CUE_PAD) / total
        yield t, t + d, q.rstrip("，。；、")
        t += d


def main():
    lines = {"zh": {l["id"]: l for l in narrate.load(SPEED, QSPEED)}, "en": {l["id"]: l for l in narrate.load_en(SPEED)}}
    takes = {lang: narrate.takes_dir(VOICE, lang) for lang in LANGS}
    pairs = pair_data()[:UPTO]
    ids = list(lines["zh"])
    audio = {lang: np.zeros(int(60 * 15 * SR), np.float32) for lang in LANGS}
    placed = {lang: {} for lang in LANGS}
    slots = {}

    def put(lid: str, t: float) -> float:
        """Every language's take at t; the slot is the longest of them."""
        ends = []
        for lang in LANGS:
            y = mit.decode(takes[lang] / f"s{lines[lang][lid]['speed']:.2f}" / f"{lid}.wav", trim=True)
            i = int(t * SR)
            audio[lang][i:i + len(y)] += y
            placed[lang][lid] = (round(t, 3), round(t + len(y) / SR, 3))
            ends.append(t + len(y) / SR)
        slots[lid] = (round(t, 3), round(max(ends), 3))
        return max(ends)

    def run(group, t):
        for k, lid in enumerate(group):
            if k:
                prev = group[k - 1]
                asked = any(lines[lang][prev]["question"] for lang in ("zh", "en"))
                t += max(lines["zh"][lid]["pause"] or GAP, QUESTION_GAP if asked else 0)
            t = put(lid, t)
        return t

    section = lambda s: [i for i in ids if i.startswith(s)]  # noqa: E731
    tl = {"fps": FPS, "voice": f"{VOICE} {SPEED} ({','.join(LANGS)})", "title": [0, 0], "pairs": [], "lines": {}}
    t = run(section("sc00"), TITLE + 0.3)
    tl["title"] = [0, round(t + INTRO_TAIL, 3)]
    t += INTRO_TAIL
    for p in pairs:
        group = section(f"sc{p['n']:02d}")
        reveal_ids = [i for i in group if lines["zh"][i]["reveal"]]
        clip_ids = [i for i in group if not lines["zh"][i]["reveal"]]
        p["start"] = round(t, 3)
        p["reveal"] = round(t + PAIR_IN + COUNT, 3)
        end_reveal = p["reveal"] + REVEAL_MIN
        if reveal_ids:
            end_reveal = max(end_reveal, run(reveal_ids, p["reveal"] + REVEAL_LEAD) + REVEAL_TAIL)
        p["clip"] = round(end_reveal, 3)
        e = run(clip_ids, p["clip"] + CLIP_LEAD) + CLIP_TAIL
        p["end"] = round(max(e, p["clip"] + CLIP_MIN), 3)
        need = p["end"] - p["clip"] + XFADE
        if p["n"] in SECOND:  # the first clip only has to last until the cut
            key2, fps2, line2, into, credit2 = SECOND[p["n"]]
            at = round(slots[line2][0] + into - p["clip"], 3)
            p["video2"] = {"src": f"clips/{key2}.mp4", "from": USABLE[key2][0], "at": at, "credit": credit2}
            assert USABLE[key2][1] - USABLE[key2][0] >= p["end"] - p["clip"] - at + XFADE, "second clip too short"
            need = at + 0.4
        a, b = USABLE[p["key"]]
        usable = b - a
        floor = 0.5 if p["fps"] >= 50 else 0.8
        rate = 1.0 if usable >= need else max(floor, usable / need)
        plays = usable / rate
        hold = round(plays, 3) if plays < need else None
        # a hold of more than LONG_HOLD s dissolves to the pair's real photo (the one in the test) instead of a frozen frame
        still = f"pairs/{p['n']:02d}-{p['real']}.jpg" if hold is not None and need - hold > LONG_HOLD else None
        p["video"] = {"src": f"clips/{p['key']}.mp4", "from": a, "rate": round(rate, 4), "hold": hold,
                      "last": f"clips/{p['key']}.last.jpg", "still": still}
        t = p["end"]
        tl["pairs"].append(p)
    if UPTO >= 10:
        t0 = t
        e1 = run(["sc11-01"], t0 + END_LEAD)
        blur_at = e1 + (lines["zh"]["sc11-02"]["pause"] or GAP)
        e2 = run(["sc11-02"], blur_at)
        # the closing question to the viewer (Yancy 11-12: 最后加一个语音 你猜对了几个？); a "You ?/10" tally joins the two AIs
        you_at = e2 + (lines["zh"]["sc11-03"]["pause"] or GAP)
        e2 = run(["sc11-03"], you_at)
        tl["ending"] = {"start": round(t0, 3), "blur": round(blur_at, 3), "you": round(you_at, 3), "end": round(e2 + END_TAIL, 3),
                        # the AI pictures that fooled both models (groups 2 and 4), with sc11-02 「骗到它们的，都是画得又细又像的 AI 蝴蝶」
                        "pictures": [f"pairs/{p['n']:02d}-{'B' if p['real'] == 'A' else 'A'}.jpg" for p in pairs
                                     if not p["astraOk"] and not p["fableOk"]]}
        tl["credits"] = [round(e2 + END_TAIL, 3), round(e2 + END_TAIL + CREDITS, 3)]
        total = e2 + END_TAIL + CREDITS
    else:
        total = t + 1.5
    tl["durationSeconds"] = round(total, 3)
    tl["lines"] = {k: {"start": a, "end": b} for k, (a, b) in slots.items()}

    OUT.mkdir(parents=True, exist_ok=True)
    n = int(total * SR)
    bed = mit.ffread(MUSIC)
    bed *= 10 ** ((BED_LUFS - mit.lufs(bed)) / 20)
    bed = np.tile(bed, int(np.ceil(n / len(bed))))[:n]
    for lang in LANGS:
        # this language's mix: its own lines duck K. 265
        cues = [{"speech": {"start": a, "end": b}} for a, b in placed[lang].values()]
        env_path = OUT / f"env.{lang}.wav"
        music_ducking.envelope(cues, total, BED_LUFS, env_path)
        env = mit.ffread(env_path)
        m = min(len(env), n)
        mix = audio[lang][:m] + bed[:m] * env[:m]
        mix *= 10 ** ((FINAL_LUFS - mit.lufs(mix)) / 20)
        sf.write(OUT / f"mix.{lang}.raw.wav", mix, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / f"mix.{lang}.raw.wav"), "-af",
                        f"alimiter=limit={10 ** (FINAL_TP / 20):.4f}:attack=5:release=60:level=false",
                        "-c:a", "pcm_s24le", str(OUT / f"mix.{lang}.wav")], check=True)
        # captions on this track's timing: its own lines, and the paired line in the other language
        own, other = [], []
        for lid, (a, b) in sorted(placed[lang].items(), key=lambda kv: kv[1][0]):
            zh_text = re.sub(r"【[^】]*】", "", lines["zh"][lid]["caption"])
            en_text = re.sub(r"【[^】]*】", "", lines["en"][lid]["caption"])
            zh_cues_ = list(zh_cues(zh_text, a, b))
            en_cues_ = list(en_cues(en_text, a, b))
            own += en_cues_ if lang == "en" else zh_cues_
            other += zh_cues_ if lang == "en" else en_cues_
        sub = {"en": ("en", "zh-Hans"), "zh": ("zh-Hans", "en")}[lang]
        for name, cues_ in ((sub[0], own), (sub[1], other)):
            (OUT / f"butterfly-challenge.{lang}-track.{name}.srt").write_text(
                "".join(f"{k}\n{mit.stamp(a)} --> {mit.stamp(b)}\n{s}\n\n" for k, (a, b, s) in enumerate(cues_, 1)))
    PUB.mkdir(parents=True, exist_ok=True)
    (PUB / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    holds = [(p["n"], p["video"]["rate"], p["video"]["hold"]) for p in tl["pairs"] if p["video"]["rate"] < 1 or p["video"]["hold"]]
    for lang in LANGS:
        pad = sum((slots[k][1] - slots[k][0]) - (b - a) for k, (a, b) in placed[lang].items())
        print(f"{lang}: {len(placed[lang])} lines, padding to the shared slots {pad:.1f} s")
    print(f"{VOICE} {SPEED} {LANGS}: {total:.1f} s; slowed/held clips {holds}; -> {OUT}")


if __name__ == "__main__":
    main()
