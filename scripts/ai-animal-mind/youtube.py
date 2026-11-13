"""YouTube upload text for 「动物想什么？AI 知道吗？」: 【标题】【简介】【标签】, Chinese and English.

    python3 scripts/ai-animal-mind/youtube.py

One video with an English and a Chinese voice track, so there is one text per language for the two titles and
descriptions. Credits list only what the film's shots use (timeline.json, clips.json, footage-sources.json), plus the
Bach section's own sources (the Jesu film's credits), the music, the animal sound recordings and the AI-generated pictures. Tags
follow scripts/youtube_tags.py. Writes out/ai-animal-mind/delivery/youtube-description.{zh,en}.txt.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from youtube_tags import hashtags  # noqa: E402

PUB = ROOT / "public/ai-animal-mind"
EDIT = json.loads((ROOT / "scripts/ai-animal-mind/edit.json").read_text())
# the real animal sounds (edit.json `sounds`, docs/ai-animal-mind/sound-sources.json), by source folder
SOUND_CREDITS = {
    "dolphin-atlantic-spotted-madeira": {
        "zh": "大西洋斑海豚：Redaelli L.、Caruso F.、dos Santos M.E.、Alves F.、Dinis A.（2026），马德拉群岛齿鲸声音数据集，Zenodo，https://doi.org/10.5281/zenodo.17952229，CC BY 4.0",
        "en": "Atlantic spotted dolphins: Redaelli L., Caruso F., dos Santos M.E., Alves F., Dinis A. (2026), Dataset of odontocete acoustic signals from the Madeira archipelago, Zenodo, https://doi.org/10.5281/zenodo.17952229, CC BY 4.0"},
    "sperm-whale-dswp": {
        "zh": "抹香鲸：Dominica Sperm Whale Project，DSWP 数据集（Paradise 等 2025，Project CETI），https://huggingface.co/datasets/orrp/DSWP，CC BY 4.0",
        "en": "Sperm whale codas: Dominica Sperm Whale Project, DSWP dataset (Paradise et al. 2025, Project CETI), https://huggingface.co/datasets/orrp/DSWP, CC BY 4.0"},
    "elephant-king2010": {
        "zh": "非洲象：King L.E.、Soltis J.、Douglas-Hamilton I.、Savage A.、Vollrath F.（2010），PLoS ONE 5(4): e10346，https://doi.org/10.1371/journal.pone.0010346，CC BY 2.5",
        "en": "African elephant rumble: King L.E., Soltis J., Douglas-Hamilton I., Savage A., Vollrath F. (2010), PLoS ONE 5(4): e10346, https://doi.org/10.1371/journal.pone.0010346, CC BY 2.5"},
    "humpback-twain": {
        "zh": "座头鲸 Twain 和研究者放的那一声：McCowan B.、Hubbard J.、Walker L.、Sharpe F.、Frediani J.、Doyle L.（2023），Zenodo，https://doi.org/10.5281/zenodo.8247515，CC BY 4.0",
        "en": "The humpback Twain and the researchers' playback: McCowan B., Hubbard J., Walker L., Sharpe F., Frediani J., Doyle L. (2023), Zenodo, https://doi.org/10.5281/zenodo.8247515, CC BY 4.0"},
    "pig-soundwel": {
        "zh": "猪叫：Briefer E.F. 等，Soundwel 猪叫声数据库，Zenodo，https://doi.org/10.5281/zenodo.8252482，CC BY 4.0",
        "en": "Pig calls: Briefer E.F. et al., The Soundwel Database: a labeled pig vocalization repository, Zenodo, https://doi.org/10.5281/zenodo.8252482, CC BY 4.0"},
    "monkey-vervet-mcvicker": {
        "zh": "长尾黑颚猴：Roland McVicker 录音（1982），大英图书馆，维基共享资源，CC BY 4.0",
        "en": "Vervet monkeys: recorded by Roland McVicker (1982), British Library, via Wikimedia Commons, CC BY 4.0"},
}
OUT = ROOT / "out/ai-animal-mind/delivery"

TEXT = {
    "zh": {
        "title": "动物想什么？AI 知道吗？",  # Yancy 11-11: 「标题改为：动物想什么？AI知道吗」 (was AI 知道动物在想什么吗？)
        "intro": "猴子会欣赏夕阳吗？\n\n我最喜欢在海边看夕阳。可是猴子看到夕阳，是什么感觉呢？AI 现在好像能「理解」人话了，它能帮我们听懂动物吗？"
                 "有人让 AI 去听鲸和海豚、去分猪叫的好与不好、去看小动物的脸……这一期只问问题，不讲答案，因为这个问题现在还没有答案。你觉得呢？",
        "sounds_head": "动物的声音（真实录音：节选、滤波、调整了音量；大象的低吼加了一点饱和，让手机也听得见；许可证 https://creativecommons.org/licenses/by/4.0/ 、https://creativecommons.org/licenses/by/2.5/ ）",
        "credits_head": "画面", "pexels": "· 实拍（Pexels）：{}",
        "muse": "· 部分画面由 AI 生成：视频片段用 Muse，图片用 Codex",
        "hans": "· 聪明的汉斯（1904）：Karl Krall，公版，https://commons.wikimedia.org/wiki/File:CleverHans.jpg",
        "monet": "· 莫奈《睡莲池上的桥》（1899）：大都会艺术博物馆，CC0，https://commons.wikimedia.org/wiki/File:Bridge_over_a_Pond_of_Water_Lilies_MET_DT1854.jpg",
        "jesu": "· 巴赫那一段的画面出自我们的《耶稣，世人仰望的喜悦》：米开朗琪罗《创造亚当》所在的西斯廷礼拜堂（美国国务院照片，公版）；"
                "国际空间站延时（NASA，公版）；米开朗琪罗《哀悼基督》，Fred Romero 摄，CC BY 2.0；布罗莫火山延时，Justin Ng，CC BY 3.0；仙纳度国家公园日出延时（公版）",
        "music": "音乐\n· 莫扎特《小星星变奏曲》K. 265，Simone Renzi 演奏，CC BY 3.0，https://commons.wikimedia.org/wiki/File:Mozart_-_12_Variations_K._265_-_Simone_Renzi.mp3（按段落剪辑）\n"
                 "· 巴赫《耶稣，世人仰望的喜悦》BWV 147/10，Gli Armonici 乐团，CC0（去掉了合唱）",
        "voice": "配音：AI 合成语音（旁白使用 Louise 的授权声线）",
        "studies": "片中提到的研究（按出现顺序）：海豚叫声模型 DolphinGemma；抹香鲸的「字母表」（Sharma 等，2024）；大象的名字（Pardo 等，2024）；"
                   "座头鲸 Twain（McCowan 等，2023）；海豚 CHAT；聪明的汉斯（Pfungst，1907）；猪叫的情绪（Briefer 等，2022）；"
                   "人怎么看狗的情绪（Molinaro、Wynne，2025）；老鼠的表情（Dolensek 等，2020）；鸽子分辨莫奈和毕加索（Watanabe 等，1995）；"
                   "老鼠跟着节拍（Ito 等，2022）；绢毛猴和狨猴更喜欢安静（McDermott、Hauser，2007）",
        "byline": "作者：Yancy Qin | Lucas Academy",
        "tags": ["ai", "人工智能", "动物", "动物情绪", "动物语言", "科普", "猴子", "夕阳", "巴赫", "米开朗琪罗"],
    },
    "en": {
        "title": "What Are Animals Thinking? Does AI Know?",
        "intro": "Do monkeys enjoy a sunset?\n\nI love watching the sunset by the sea. But what does a monkey feel when it sees one? AI seems to "
                 "\"understand\" our language now; could it help us understand animals? People are letting AI listen to whales and dolphins, "
                 "sort happy pig sounds from unhappy ones, and read little animal faces... This video only asks questions. Nobody has the answer yet. What do you think?",
        "sounds_head": "Animal sounds (real recordings: excerpted, filtered and level-adjusted; the elephant rumble lightly saturated so it carries on phone speakers; licences https://creativecommons.org/licenses/by/4.0/ , https://creativecommons.org/licenses/by/2.5/ )",
        "credits_head": "Pictures", "pexels": "· Footage (Pexels): {}",
        "muse": "· Some shots were made with AI (video clips with Muse, images with Codex)",
        "hans": "· Clever Hans (1904): Karl Krall, public domain, https://commons.wikimedia.org/wiki/File:CleverHans.jpg",
        "monet": "· Claude Monet, Bridge over a Pond of Water Lilies (1899): The Metropolitan Museum of Art, CC0, https://commons.wikimedia.org/wiki/File:Bridge_over_a_Pond_of_Water_Lilies_MET_DT1854.jpg",
        "jesu": "· The Bach section comes from our film \"Jesu, Joy of Man's Desiring\": the Sistine Chapel with Michelangelo's Creation of Adam "
                "(U.S. State Department photo, public domain); ISS time-lapse (NASA, public domain); Michelangelo's Pietà, photo by Fred Romero, CC BY 2.0; "
                "Mount Bromo time-lapse by Justin Ng, CC BY 3.0; Shenandoah National Park sunrise time-lapse (public domain)",
        "music": "Music\n· W. A. Mozart, 12 Variations on \"Ah vous dirai-je, Maman\", K. 265, played by Simone Renzi, CC BY 3.0, "
                 "https://commons.wikimedia.org/wiki/File:Mozart_-_12_Variations_K._265_-_Simone_Renzi.mp3 (edited into sections)\n"
                 "· J. S. Bach, Jesu, Joy of Man's Desiring, BWV 147/10, Orchestra Gli Armonici, CC0 (choir removed)",
        "voice": "Voice: AI speech synthesis (the narrator uses Louise's licensed voice)",
        "studies": "Research mentioned (in order): DolphinGemma; the sperm whale \"alphabet\" (Sharma et al., 2024); elephant names (Pardo et al., 2024); "
                   "the humpback Twain (McCowan et al., 2023); the dolphin CHAT system; Clever Hans (Pfungst, 1907); pig call emotions (Briefer et al., 2022); "
                   "how people read dog emotions (Molinaro & Wynne, 2025); mouse facial expressions (Dolensek et al., 2020); pigeons telling Monet from Picasso "
                   "(Watanabe et al., 1995); rats keeping the beat (Ito et al., 2022); tamarins and marmosets preferring silence (McDermott & Hauser, 2007)",
        "byline": "By Yancy Qin | Lucas Academy",
        "tags": ["ai", "artificial intelligence", "animals", "animal emotions", "animal communication", "science", "monkeys", "sunset", "bach", "michelangelo"],
    },
}


def main() -> None:
    tl = json.loads((PUB / "timeline.json").read_text())
    clips = json.loads((PUB / "clips.json").read_text())
    src = json.loads((ROOT / "docs/ai-animal-mind/footage-sources.json").read_text())["pexels"]
    used = {clips[s["clip"]]["source"] for s in tl["shots"] if s.get("clip") in clips}
    pexels = sorted({src[s[7:]]["by"] for s in used if s.startswith("pexels:")}, key=str.lower)
    imgs = {s.get("img", "") for s in tl["shots"]}
    OUT.mkdir(parents=True, exist_ok=True)
    for lang, t in TEXT.items():
        credits = [t["credits_head"], t["pexels"].format(("、" if lang == "zh" else ", ").join(pexels)), t["muse"]]
        if "clever-hans-1904.jpg" in imgs:
            credits.append(t["hans"])
        if "monet-bridge-met-dt1854.jpg" in imgs:
            credits.append(t["monet"])
        credits.append(t["jesu"])
        folders = list(dict.fromkeys(e["src"].split("/")[0] for e in EDIT.get("sounds", [])))
        sounds = [t["sounds_head"]] + [f"· {SOUND_CREDITS[f][lang]}" for f in folders]
        body = "\n\n".join([t["intro"], t["studies"], "\n".join(credits), "\n".join(sounds), t["music"], t["voice"],
                             t["byline"], hashtags(t["tags"])])
        (OUT / f"youtube-description.{lang}.txt").write_text(f"【标题】\n{t['title']}\n\n【简介】\n{body}\n" if lang == "zh"
                                                            else f"[Title]\n{t['title']}\n\n[Description]\n{body}\n")
        print(lang, len(body), "characters")


SHORT_TEXT = {  # the vertical shorts (shorts.json, build_short.py); titles are suggestions for Yancy to change
    "ocean": {"zh": ("动物想什么？AI 知道吗？（海洋篇）",
                     "有人录了很多年海豚的声音，交给 AI 去听；抹香鲸「咔嗒、咔嗒」，座头鲸和人来来回回「对话」了二十分钟……它们在说什么呢？"),
              "en": ("What Are Animals Thinking? Does AI Know? (Ocean)",
                     "People spent years recording dolphins and let AI listen. Sperm whales click in little strings. A humpback "
                     "called back to people for twenty minutes... What were they saying?")},
    "animals": {"zh": ("动物想什么？AI 知道吗？（陆地篇）",
                       "猴子会欣赏夕阳吗？你看得出猫和狗开不开心吗？AI 能分出猪叫的「好」和「不好」，老鼠听莫扎特会跟着点头……它们在想什么呢？"),
                "en": ("What Are Animals Thinking? Does AI Know? (On Land)",
                       "Do monkeys enjoy a sunset? Can you tell if a cat or a dog is happy? AI can sort happy pig sounds from "
                       "unhappy ones, and rats bob their heads to Mozart... What are they thinking?")},
}
SHORT_TAGS = {"ocean": {"zh": ["海豚", "鲸", "海洋"], "en": ["dolphins", "whales", "ocean"]},
              "animals": {"zh": ["猫", "狗", "夕阳"], "en": ["cats", "dogs", "sunset"]}}
SHORT_FULL = {"zh": "完整版：《动物想什么？AI 知道吗？》", "en": 'Full video: "What Are Animals Thinking? Does AI Know?"'}


def shorts() -> None:
    """Upload text for each built short: its own footage authors and recordings, K. 265 only (no Bach in the shorts)."""
    clips = json.loads((PUB / "clips.json").read_text())
    src = json.loads((ROOT / "docs/ai-animal-mind/footage-sources.json").read_text())["pexels"]
    by_name = {e.get("name", e["src"]): e["src"].split("/")[0] for e in EDIT.get("sounds", [])}
    out = ROOT / "out/ai-animal-mind/shorts"
    for f, lang in ((f, lang) for f in sorted((PUB / "shorts").glob("*.json")) for lang in ("zh", "en")):
        name = f.stem  # one picture per short (the English video with a Chinese track): a text in each language
        tl = json.loads(f.read_text())
        t, (title, intro) = TEXT[lang], SHORT_TEXT[name][lang]
        used = {clips[s["clip"]]["source"] for s in tl["shots"] if s["clip"] in clips}
        pexels = sorted({src[u[7:]]["by"] for u in used if u.startswith("pexels:")}, key=str.lower)
        credits = [t["credits_head"], t["pexels"].format(("、" if lang == "zh" else ", ").join(pexels))]
        if any(u.startswith("muse:") for u in used):
            credits.append(t["muse"])
        folders = list(dict.fromkeys(by_name[s["name"]] for s in tl["sounds"]))
        head = t["sounds_head"] if "elephant-king2010" in folders else re.sub(r"[；;] ?(大象的低吼|the elephant rumble)[^；;]*", "", t["sounds_head"])
        sounds = [head] + [f"· {SOUND_CREDITS[x][lang]}" for x in folders] if folders else []
        tags = [x for x in t["tags"] if x not in ("巴赫", "米开朗琪罗", "bach", "michelangelo", "夕阳", "sunset")] + SHORT_TAGS[name][lang]
        body = "\n\n".join([intro, SHORT_FULL[lang], "\n".join(credits), *(["\n".join(sounds)] if sounds else []),
                             t["music"].split("\n· 巴赫")[0].split("\n· J. S. Bach")[0], t["voice"], t["byline"],
                             hashtags(tags + ["shorts"])])
        (out / f"youtube-{name}.{lang}.txt").write_text(f"【标题】\n{title}\n\n【简介】\n{body}\n" if lang == "zh"
                                                       else f"[Title]\n{title}\n\n[Description]\n{body}\n")
        print(name, lang, len(body), "characters")


if __name__ == "__main__":
    main()
    shorts()
