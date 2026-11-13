"""Upload folder for 「一片落叶，为什么让卡车急刹车？」 on the Desktop: the film (English default + Mandarin track), the
Mandarin track as m4a, both SRTs, both covers (+ the alternate pair), both descriptions.

    python3 scripts/leaf-truck/package.py [--update]

--update rewrites the files of an existing Desktop folder in place instead of making 「…-上传-2」.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[2]
BUILD = REPO / "out/leaf-truck/build"
COVERS = Path("/Users/yqin/repo/playground/lucas-academy-video-data/leaf-truck/covers")
NAME = "一片落叶为什么让卡车急刹车-上传"
STEM = "一片落叶"
COVER, ALT = "cover-a-leaves", "cover-b-brake"
MUSIC = "waltz"   # the mix build.py made: build/leaf-truck.<MUSIC>.mp4 (Yancy 11-12 picked the waltz)

AWARD = "https://www.iru.org/system/files/AWARD_Impact%20Assessment_D7.3.pdf"
MUSOPEN = "https://archive.org/details/musopen-chopin-complete-works-flac"
PEXELS = "Yaroslav Shuraev, RDNE Stock project, Anastasia Shuraeva"
DEFAULT_TAGS = ["education", "parenting", "art", "arthistory", "stem", "bilingual", "bilingualchildren", "lucas_academy"]
OWN_TAGS = {
    "en": ["selfdriving", "driverlesstruck", "autonomousdriving", "criticalthinking", "systemsthinking", "problemsolving",
           "lidar", "engineering", "thinkingskills"],
    "zh": ["无人驾驶", "自动驾驶", "批判性思维", "系统思维", "逆向思维", "解决问题", "激光雷达", "思维方式"],
}
CHAPTERS = [  # section in the timeline, zh, en (titles from docs/leaf-truck/{zh,en}-draft.md)
    ("LF01", "一片落叶", "A few leaves"),
    ("LF02", "太敏感，又太迟钝", "Too sensitive, and not sensitive enough"),
    ("LF03", "先别急着猜", "Don't guess yet"),
    ("LF04", "每次只改一个地方", "Change one thing at a time"),
    ("LF05", "一脚刹车，牵动一串", "One hard stop, a chain of effects"),
    ("LF06", "难的是取舍", "The hard part is the trade-off"),
    ("LF07", "回到我们自己", "Back to us"),
]


def stamp(seconds):
    s = int(seconds)
    return f"{s // 60}:{s % 60:02}"


def chapters():
    sec = json.loads((BUILD / "timeline.json").read_text())["sections"]
    rows = [(0 if k == "LF01" else sec[k], zh, en) for k, zh, en in CHAPTERS]
    assert all(b[0] - a[0] >= 10 for a, b in zip(rows, rows[1:])), "YouTube needs 10 s per chapter"
    return rows


def description(lang):
    times = "\n".join(f"{stamp(t)} {zh if lang == 'zh' else en}" for t, zh, en in chapters())
    own = OWN_TAGS[lang]
    hashtags = " ".join(f"#{t}" for t in DEFAULT_TAGS + own)
    tags = " ".join(f"#{t}" for t in own + DEFAULT_TAGS)
    assert len(tags) <= 500
    if lang == "zh":
        return f"""【标题】
一片落叶，为什么让卡车急刹车？

【简介】
奥地利一个小镇上，一辆无人驾驶卡车每天在两座工厂之间送货，却常常为几片落叶一脚急刹：同一条路上，它急刹车的次数最多是人类司机的十一倍。可路上一块只有 14.4 厘米高的木托盘，它反倒看不出来。

太敏感，又太迟钝，该从哪儿下手？工程师没有急着换传感器，先把一个半月里的四十七次停车记了下来。我们再设想一个「每次只改一个地方」的小测试，看一脚急刹怎样牵动后车、货物和电量，最后从目标往回想，找到不止一个办法。纸飞机飞不远，钥匙找不到，我们每天也在这样想问题。

章节
{times}

真实案例出处：AWARD 项目（欧盟 Horizon 2020）D7.3《Impact assessment and user survey results》2.0 版（2024），第 4.8 节、第 5.8.2.1 节
{AWARD}
「每次只改一个地方」的测试是我们设想的，不是报告里的实验；把树叶、树枝当作「不是障碍」，出自同一项目的无人叉车。
卡车和道路画面是 AI 生成的情景重现，不是真实录像。

作者 Yancy Qin | Lucas Academy
旁白使用 Louise 的授权声线

音乐：肖邦《升 c 小调圆舞曲》Op. 64 No. 2，Olga Gurevich 演奏。
录音：Musopen「Set Chopin Free」肖邦全集，CC0 1.0（放弃版权，进入公有领域）。
{MUSOPEN}
全曲使用，调整了音量。
素材：Pexels 视频（{PEXELS.replace(", ", "、")}）

{hashtags}

【标签】
{tags}

【上传设置】
视频：{STEM}.mp4（默认音轨英语，附带普通话音轨）
附加音轨：普通话（{STEM}-中文音轨.m4a）
字幕：{STEM}.en.srt（英语）、{STEM}.zh-Hans.srt（简体中文）
封面：youtube-cover.zh.jpg（备选：youtube-cover-备选.zh.jpg）
修改或合成的内容：是（卡车和道路画面为 AI 生成的情景重现）
"""
    return f"""【Title】
Why Did a Leaf Stop a Self-Driving Truck?

【Description】
In a small town in Austria, a driverless truck delivered goods between two factories every day, yet it often slammed on the brakes for a few fallen leaves: on the same street, it hit the brakes up to eleven times as often as human drivers. And a wooden pallet only 14.4 cm tall on the road? That it could not see.

Too sensitive and not sensitive enough at the same time: where would you start? The engineers did not rush to replace the sensor; first they logged every one of 47 stops over six and a half weeks. Then we imagine a small "change one thing at a time" test, follow one hard stop to the car behind, the cargo and the battery, and finally work backward from the goal to find more than one fix. A paper plane that won't fly far, keys we can't find: we think this way every day.

Chapters
{times}

The real case: AWARD project (EU Horizon 2020), D7.3 "Impact assessment and user survey results", version 2.0 (2024), sections 4.8 and 5.8.2.1
{AWARD}
The "change one thing at a time" test is our thought experiment, not an experiment in the report; treating leaves and branches as non-obstacles comes from the same project's driverless forklift.
The truck and road scenes are AI-generated reconstructions, not real footage.

By Yancy Qin | Lucas Academy
The narrator uses Louise's licensed voice.

Music: Chopin, Waltz in C-sharp minor, Op. 64 No. 2, played by Olga Gurevich.
Recording: Musopen "Set Chopin Free", The Complete Works of Frédéric Chopin, CC0 1.0 (public domain dedication).
{MUSOPEN}
The complete piece; volume adjusted.
Footage: Pexels videos ({PEXELS})

{hashtags}

【Tags】
{tags}

【Upload settings】
Video: {STEM}.mp4 (default audio English, Mandarin track included)
Additional audio track: Mandarin ({STEM}-中文音轨.m4a)
Captions: {STEM}.en.srt (English), {STEM}.zh-Hans.srt (Simplified Chinese)
Thumbnail: youtube-cover.en.jpg (alternate: youtube-cover-备选.en.jpg)
Altered or synthetic content: Yes (the truck and road scenes are AI-generated reconstructions)
"""


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    film = BUILD / f"leaf-truck.{MUSIC}.mp4"
    root = Path.home() / "Desktop" / NAME
    update = "--update" in sys.argv and root.is_dir()
    dest, n = root, 2
    while dest.exists() and not update:
        dest, n = root.with_name(f"{NAME}-{n}"), n + 1
    with tempfile.TemporaryDirectory(prefix=".leaf-upload-", dir=dest.parent) as tmp:
        folder = Path(tmp) / dest.name
        folder.mkdir()
        video = folder / f"{STEM}.mp4"
        shutil.copy2(film, video)
        assert sha(video) == sha(film)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-map", "0:a:1", "-c:a", "copy",
                        "-metadata:s:a:0", "language=zho", "-movflags", "+faststart", str(folder / f"{STEM}-中文音轨.m4a")],
                       check=True)
        shutil.copy2(BUILD / "captions.en.srt", folder / f"{STEM}.en.srt")
        shutil.copy2(BUILD / "captions.zh-Hans.srt", folder / f"{STEM}.zh-Hans.srt")
        for src, name in ((COVER, "youtube-cover"), (ALT, "youtube-cover-备选")):
            for lang in ("zh", "en"):
                jpg = COVERS / f"{src}.{lang}.jpg"
                with Image.open(jpg) as im:
                    assert im.size == (1280, 720), im.size
                shutil.copy2(jpg, folder / f"{name}.{lang}.jpg")
        for lang in ("zh", "en"):
            (folder / f"youtube-description.{lang}.txt").write_text(description(lang), encoding="utf-8")
        if update:
            for f in folder.iterdir():
                f.replace(dest / f.name)
        else:
            folder.rename(dest)
    print(dest)
    for f in sorted(dest.iterdir()):
        print(f"  {f.name}  {f.stat().st_size:,}")


if __name__ == "__main__":
    main()
