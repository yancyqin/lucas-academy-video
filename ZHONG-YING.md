# 中英阅读 · Read Aloud in Chinese and English

A series that reads one lesson of 语言的桥's 看得见的诗 (lucas-academy-lang) aloud: every verse once in Chinese and
then once in English, verse by verse, with the narration the lesson already has. No explanation. Three films so far:

| Film | Lesson | Works | Length |
|---|---|---|---|
| 爬高一点，看远一点 · Climb Higher, See Farther | `climb-higher` | 登鹳雀楼 · Foreign Lands · 诗篇 121:1–2 | 2:33 |
| 小船去远方 · Little Boats, Far Away | `little-boats` | 早发白帝城 · Where Go the Boats? · 以赛亚书 40:31 | 3:22 |
| 美好能否留存？ · Can Beauty Last? | `can-beauty-last` | 春夜喜雨 · Sonnet 18 · 传道书 3:11 | not built |

## What the owner decided (2026-10-26)

- **Voices:** first cut used the lesson's published clips (read at 0.75 for learners). The owner found them too
  slow and the delivery improvable (2026-10-26), so every verse is re-voiced for the series at speed 1.0
  (`scripts/zhong-ying/narration.py`): Fangfang zh and Louise en, zero-shot-instruct, one instruction per voice
  (「请用亲切、有感情的语气，像给孩子朗读诗歌一样读。」 / "Please read aloud in a warm, expressive voice, like reading a poem
  to a child."), two takes per line, polyphones as pinyin tokens (朝 zhāo, 还 huán, 重 chóng, 磨 mò). Whisper is
  judged by sound (toneless pinyin for Chinese, letters for English): it writes classical words as homophones
  and sometimes in traditional characters. Every line is levelled to −20 LUFS before mixing.
- **Sunny's recorded voice (2026-10-27):** the Chinese of the Tang poems and the scriptures is read by Sunny, not AI
  (her voice samples, iPhone memos **Windchime 18** — 早发白帝城 — and **Windchime 19** — 登鹳雀楼, 诗篇 121,
  以赛亚书 40:31; the owner, 2026-10-28: both are Sunny, never label them anyone else's). `scripts/zhong-ying/sunny_voice.py`
  aligns the known text, cuts one clip per verse in the memo's real pauses (`lucas-academy-video-data/zhong-ying/narration/sunny/`;
  the aligner started 「我要向山举目」 0.1 s late and an aligner-timed cut clipped 「我」), and `films.clip()` prefers
  those clips; the other lines keep the AI takes. The memos are already clean (silence gated to digital zero), so
  no denoising, only a 70 Hz high-pass; every line is levelled to −20 LUFS before mixing, so her lines sit at the AI
  lines' loudness. For stronger feeling than the AI and a more professional sound than the phone,
  `voice_versions.py` made audition versions on 早发白帝城 (studio-processed / converted to Fangfang's voice / a new
  Fangfang reading prompted with Sunny's style); the owner chose **A, Sunny's voice studio-processed**
  (`sunny_voice.py` STUDIO), which is what the film uses.
- **Feeling in AI voices (2026-10-28, `emotion_lab.py`):** CosyVoice3 only knows the instructions it was trained on
  (dialects, loud/soft, slow/fast, and 「请非常开心/伤心/生气地说一句话」); free-form tone descriptions barely move it.
  The reading copies the REFERENCE recording's prosody, so the lever is an expressive reference: on short lines
  Fangfang prompted with her own most expressive take widened her pitch spread ~40 % (4.4 → 6.1 st, still her
  voice); over whole texts the gain shrank to take-to-take noise and the owner rejected the Fangfang readings.
  Sunny prompted with her own sample's reading of the same kind of text (poem ← her 登鹳雀楼, scripture ← her 诗篇 121),
  held to her own pace and never above 2.1 syllables/s ("朗读速度不要太快"), is the current candidate.
- **语言的桥 lessons in the same voices (2026-10-28):** `scripts/zhong-ying/lesson_voice.py` voices a lang lesson
  from lang's narration scripts — Sunny's Chinese, Matthew's English, each prompted with their own reading, never
  faster than it; Whisper by sound picks among takes (`--only` for retakes). First use: lang lesson
  `can-beauty-last` 「美好能否留存？」 (看得见的诗 · 第三期: 春夜喜雨, Sonnet 18, 传道书 3:11), published with lang's
  `publish-audio.mjs … voice.zh=sunny/zh voice.en=matthew/en speed=0.75`.
- **Joins:** every line is cut by its sound — out from the aligned words to where it has really gone quiet — with
  raised-cosine fades (`build_timeline.py` `sound_span`, `fade`). Cutting at the aligner's times clicked and
  clipped first words (the English of 诗篇 121:2 started on a 0.145 jump). "Quiet" is 42 dB under the line's
  peak or within 6 dB of the take's own floor, so a hissy take is not cut a second before its voice.
  `narration.py choose` passes over takes with a lone short sound at the head or tail (`strays`).
- **Three steps per work (2026-10-27):** painted (Chinese) → alive (English) → moving: after a work's last verse the
  living painting dissolves into a MiniMax-Hailuo-02 clip made from the same picture (`minimax_prep.py`; jobs with
  `scripts/debussy-impressions/minimax_job.py`, `MINIMAX_DATA=…/zhong-ying`; 1080P, 6 s, first frame only, fixed
  camera, small motions). First try, one each for 爬高一点: Foreign Lands held its oil style; 诗篇 121 greyed its
  paper; 登鹳雀楼 turned the pale ink into a saturated painting with a sea of clouds. `--tone` can pull a clip's
  colour back frame by frame, but the owner chose the MiniMax originals as they are (「还可以」).
- **Order:** Chinese then English, one verse at a time (中英一句一句读).
- **Intro:** one line, both voices, over the title card: 「学习语言最好的方式是朗读。不论你是想学中文还是英文，跟我们一起读吧。」 /
  "The best way to learn a language is to read it aloud. Whether you want to learn Chinese or English, read along
  with us." Generated for this series (fangfang/zh zero-shot and louise/en zero-shot-instruct, speed 1.0, three takes
  each, all Whisper-exact; zh take c and en take a chosen).
- **Painting:** each work's art-lab living painting (lucas-visual-art-lab `living.html`). While a verse is read in
  Chinese, its part of the picture is painted in stroke by stroke; while it is read in English, the art lab's living
  brushes are added to it, stroke by stroke. Both follow the words (`scripts/zhong-ying/paintings.py`): 「白日」
  paints the sun and "sun" makes it glow, 「楼」 paints the tower last.
- **Text:** the verse in both languages on the right, each word lighting up as it is read (逐词来亮).
- **Series mark:** the 中英阅读 seal (`Seal` in `src/videos/zhong-ying/ZhongYingVideo.tsx`), big on the title card and
  small in the corner. This is the owner's request and goes beyond the README's ribbon-on-the-cover-only rule.
- **No music**, and no channel ending question; instead each film closes on one or two lines the owner wrote
  (2026-10-27, see §Next), read after the last work. An end card names the lesson site.
- **Chapter bar** along the bottom as in the cube films; YouTube chapters are the same (the intro is its own
  chapter when it is 10 s or more).

## Rebuild

Python scripts run with the repo's venvs; data lands in `lucas-academy-video-data/zhong-ying/` and
`public/zhong-ying/<film>/` (git-ignored: the timeline carries the NIV text).

Cleaned 2026-10-30 (owner: 清理除了桌面以外的文件): only the readers' own memos stay in
`lucas-academy-video-data/zhong-ying/narration/{sunny,matthew}/raw/` (Sunny's Windchime 18 and 19, Matthew's two New
Recordings — the only copies on this Mac). Takes, alignments, art-lab exports, MiniMax runs, captures and renders went
to the Trash (`中英阅读-清理-20261030`), and the finished films are on the Desktop, so a rebuild starts from step 1:
voices, art-lab export, MiniMax.

1. Export the art lab: `git -C ../lucas-visual-art-lab archive origin/main | tar -x -C ../lucas-academy-video-data/zhong-ying/art-lab-<sha>`.
2. Intro takes: `lucas-narrate` on `zhong-ying/narration/intro-{zh,en}.json` (in lucas-academy-media), Whisper-check
   with `scripts/check_narration.py`, copy the chosen takes to `narration/intro-{zh,en}.wav`.
3. `.venv-align/bin/python scripts/zhong-ying/align.py climb-higher little-boats` — word timings by forced alignment
   (stable-ts), first word corrected to the voice's onset.
4. `.venv-reframe/bin/python scripts/zhong-ying/build_timeline.py climb-higher little-boats` — layout, chapters, the
   narration mix at −16 LUFS.
5. Serve the art-lab export (`python3 -m http.server 8746 -d <export>`) and run
   `node scripts/zhong-ying/living.mjs <film>` — the living layer, captured frame by frame in headless Chrome
   (Playwright from the Codex runtime, system Chrome): real mouse strokes, `__living.drawAt(t)` on the film clock.
6. `.venv-reframe/bin/python scripts/zhong-ying/paint.py <film>` — the painting under the text (`--still <s> …` for
   checking stills).
7. `python3 scripts/zhong-ying/render.py <film>` then `python3 scripts/zhong-ying/package.py <film> <upload dir>`.

## Notes

- The living page feeds a point on every pointer move however short, so the capture moves the mouse only once the
  brush has gone the page's own step (9 px for marks, 16 for warps); otherwise a short dab stacks dozens of marks.
- Objects lying on something else (a boat on the river, a child in the sand, the mill) are marked `over`: the
  paint around them is first laid under them too — the picture with the object inpainted away (on oils with the
  canvas's own brushwork borrowed from beside it; on paper, plain paper) — and the object is painted on top when
  its word comes. Without this, an object read late leaves its silhouette as a hole of blank canvas. When the
  object is painted, the margin around it settles back to the picture only where the paint around it has already
  arrived (otherwise the child in Foreign Lands sat in a square of sky two verses before the sky was painted).
- The settling of all regions uses one blur, so the regions' settle masks add up to exactly 1 (no seams where two
  regions meet). `paint.py <film> --check` confirms every work ends on exactly the art lab's picture.
- The living page's clock (living.mjs `startClock`) is chosen per work so its main mover — the first boat, or the
  eagle — wakes when its drift is at rest; otherwise it visibly hops when it comes alive. Every tap must wake an
  object (`__living.wake` returns true) or the capture stops.
- Each reveal stroke is clipped to its region (slightly dilated), so a big wash never uncovers a part whose word
  hasn't been read yet; when a region's strokes are done its last gaps settle in over 0.6 s, so the finished
  picture is exactly the art lab's.

## Cover

The owner's brief (2026-10-27): **双语朗读 written big and eye-catching, the title small, the icon clean.** This series
does not follow README §YouTube covers (one question, a ribbon): what a viewer must see first is that it is a
bilingual read-aloud. `ZhongYingCover` (`ZhongYingVideo.tsx`) puts 双语朗读 over one work's painting (the art lab's
1536 × 1024 original), the title small beneath it after the 中英阅读 seal drawn clean (no worn print), and no ribbon.
Layout **a** writes on the painting's open sky; the owner chose it over **b** (a paper column beside the painting, 双语
in ink, 朗读 in seal red; still in the code) and asked for a bigger title (now 84 px under the 230–250 px 双语朗读).
English covers say "Bilingual Read-Aloud" with the English title.
爬高一点 uses Foreign Lands (the child in the cherry tree), 小船去远方 Where Go the Boats (the child setting boats on the
river). `python3 scripts/zhong-ying/cover.py <film> <upload dir>` copies the painting, renders every cover at
1920 × 1080 (`out/zhong-ying/<film>/cover.<layout>.<lang>.png`) and writes `cover.<layout>.<lang>.jpg` at 1280 × 720
into the upload folder.

## Next: the fourth cut (owner, 2026-10-27)

Voice first; the owner listens before the films are rebuilt. **Status 2026-10-27 evening:** the owner approved
爬高一点's voice; it is rebuilt and packaged (`~/Desktop/中英阅读-第四版/爬高一点看远一点/`, 3:17.5, −16.3 LUFS). For
小船去远方 the owner asked for two fixes, now re-voiced and waiting for his second listen
(`~/Desktop/中英阅读-第四版-语音/`): 「它们最后会漂到哪里」 read 漂 piǎo/piào → `narration.py SPOKEN` marks 漂 piāo and v4
is take d (all three 漂 level in pitch; Whisper now writes 飄); the closing read 「必，从新得力」 → nine new takes, take
i pinned (`PINNED`), with a clause comparison (old b → i → g, no pause after 的) for the owner to choose by ear —
pitch and loudness traces could not tell the takes apart. If he meant Sunny's 以赛亚书 verse instead (her 必 is
drawn out to 0.34 s), that needs her retake or a careful time edit.
- **回顾 · Looking back (owner, 2026-10-27):** when every work has a MiniMax clip, the closing lines are read over a
  look back: the three clips play once more in order, each in its own third of the time, holding its last frame
  and dissolving into the next (`build_timeline.py` `recap`, `paint.py` `render_recap` → `paint-recap.mp4`, the
  film's `RecapPanel` with the film title and the closing text); it is its own chapter. 小船去远方 has no MiniMax
  clips, so its closing is read over the last painting.

1. **Titles and authors, read aloud** before each work's first verse, Chinese (Fangfang) then English (Louise),
   while the work's title shows and the paper is still blank. Spoken text (the screen keeps the dates and Bible
   versions; they are not read):

   | Work | 中文 (Fangfang) | English (Louise) |
   |---|---|---|
   | 登鹳雀楼 | 登鹳雀楼。唐，王之涣。 | On the Stork Tower, by Wang Zhihuan, Tang dynasty. |
   | Foreign Lands | 外面的世界。斯蒂文森。 | Foreign Lands, by Robert Louis Stevenson. |
   | 诗篇 121:1–2 | 诗篇第一百二十一篇，第一到二节。 | Psalm 121, verses 1 and 2. |
   | 早发白帝城 | 早发白帝城。唐，李白。 | Leaving Baidi at Dawn, by Li Bai, Tang dynasty. |
   | Where Go the Boats? | 小船漂到哪里去？斯蒂文森。 | Where Go the Boats? By Robert Louis Stevenson. |
   | 以赛亚书 40:31 | 以赛亚书第四十章，第三十一节。 | Isaiah, chapter 40, verse 31. |

   In `films.FILMS` as each work's `say`. Voiced with the closing lines by `narration.py extras` (three takes each,
   in the intro's voices, which the owner kept: Fangfang plain zero-shot, Louise with the intro's instruction) and
   `narration.py choose extras`; Whisper's digits are compared as spoken numbers. `align.py` aligns them (Chinese
   character by character: no lang tokens); `build_timeline.py` reads each title `TITLE_AT` after its work starts.

2. **Closing lines** (the owner's wording), Fangfang then Louise, after the last work, over its finished painting,
   then the end card:
   - 爬高一点，看远一点: 「诗人爬上一层楼，孩子爬上樱桃树，都想看得更远。是什么样的心，才能让我们看得更远呢？」 /
     "The poet climbed one floor higher, the child climbed the cherry tree; both wanted to see farther. What kind
     of heart lets us see farther?"
   - 小船去远方: 「小船漂向远方，不知道会被谁捞上岸。走远路的人不必害怕：等候耶和华的，必从新得力。」 /
     "Little boats float far away, not knowing who will bring them ashore. On a long road, we need not fear: those
     who hope in the Lord will renew their strength."

   In `films.FILMS` as each film's `closing`. With MiniMax clips for every work they are read over the 回顾 look back
   (above); otherwise the last work's span runs on under them, so its picture stays.
   **The series' last line (owner, 2026-10-28, wording B of three):** on the end card, after the closing, Fangfang
   then Louise (the intro's voices, in every film): 「喜欢的话，请订阅，也在留言里告诉我们你最喜欢哪一句。下次见！」 /
   "If you enjoyed it, subscribe, and tell us in the comments which line you liked best. See you next time!"
   `films.SUBSCRIBE`; voiced with `narration.py extras subscribe`; lit word by word under the seal; the card then
   holds `END_CARD` seconds alone (room for YouTube's end-screen elements).
3. **The noise at 1:03 of 小船去远方:** the chosen AI take for 「河水是深深的棕色……」 (`little-boats-v03-b`) has a loud
   0.15 s burst 0.4 s before the voice; `align.py` `fix_first` snapped the first word onto it, so the cut kept it.
   Fixed: `speech_onset` skips a sound under 0.3 s followed by 0.3 s of quiet (on the current lines it moves only
   this one), and `build_timeline.py` `strays()` reports any lone short sound left at a line's head or tail.
   **Two more sounds at 2:07 (owner, 2026-10-28):** take `little-boats-v05-a` reads 「京道」 before 「河水一直往前流」 —
   Whisper had noted it as `extra`, but `choose()` only looked at `odd`. Words Whisper hears beyond the line now
   count as a problem; the only pick this moved is v05 → take b (`little-boats-v05-b`, heard exactly).
4. **Matthew reads the English of the two Stevenson poems** (Foreign Lands, Where Go the Boats?), replacing Louise
   in those verses: one memo per poem, a clear pause between stanzas; cut by the pauses, studio chain A, levelled
   like the other lines; an audition before the rebuild. Recorded 2026-10-27 ("New Recording" = Foreign Lands,
   "New Recording 2" = Where Go the Boats?, kept in `narration/matthew/raw/`): every word right, but quiet
   (−37 / −35 LUFS) over a low room hum. `matthew_voice.py` made four audition versions (only louder / light
   spectral gating + studio A / strong gating + studio A / strong gating + a fuller chain); the owner chose **C,
   strong gating + the fuller chain**. `matthew_voice.py clips` cuts it into one clip per stanza
   (`narration/matthew/en/`, the way Sunny's are cut), and `films.clip()` prefers them (`RECORDED`).
5. **Rebuild** both films (align → timeline → living capture → paint → render → package); SRTs and the upload text
   gain the titles and the closing lines. Check: no stray sounds, −16 LUFS, every work ending on its picture.

Cleaned up 2026-10-27 (owner): older cuts, audition files and render outputs went to the Trash (`中英阅读-清理-20261027`). Kept: every take the voice choice reads (verses/extras, so a re-choose is stable), Matthew's raw memos + version C, Sunny's raw and zh-raw + emotion-lab/sunny (lesson_voice.py's references), the MiniMax originals, and 小船's voice preview + closing comparison until the owner confirms them.

小船去远方 gets MiniMax clips too (owner, 2026-10-27): they are made when the MiniMax quota renews, then the film
is rebuilt with its 回顾 like 爬高一点's.
2026-10-28: submitted at 09:01 PDT just after the reset. 早发白帝城 came back (v1, ready as minimax-zao-fa-baidi.mp4: the paper greys and the clouds deepen as with 登鹳雀楼, the boat drifts, the monkeys move). Where Go the Boats and 以赛亚书 40:31 failed with 1033 「system error」 twice each (v1 together, v2 one at a time). An hour later (owner: retry once): 以赛亚书 v3 came back but repaints the pale watercolour into a deep blue sky and a realistic eagle flying off (`--tone` leaves it washed out; previews on the Desktop, 中英阅读-MiniMax预览); Where Go the Boats v3 failed again (1033, third time, same picture and prompt). Owner: 「不用调，就这样就可以 做视频吧」 — 以赛亚书's clip as it is, and Where Go the Boats without one. Its slot in the 回顾 plays the end of its own panel (the living painting, alive), so the boats are on screen when 「小船漂向远方」 is read. 小船去远方 rebuilt and packaged 2026-10-28: `~/Desktop/中英阅读-第四版/小船去远方/`, 4:01.4, −16.2 LUFS, true peak −6.0, no black frames, every work ends on the art lab's picture, covers included. The owner saw nothing move there and asked for one more try (「再试一次 不行就算了」): v4, without the sentence about the child and with the 1440 picture as the first frame, came back — the boats drift down to the mill. Rebuilt with all three clips in the 回顾: 4:05.8, −16.2 LUFS, true peak −6.0, no black frames. (A clip-less work would still play its own panel's end in the 回顾.)

Still open: the voice credits
(the upload text still says all narration is AI: it needs Sunny, Matthew, Fangfang and Louise, named as the owner
says). The film already shows the closing in the verse's place and holds the first verse until the title is read;
`package.py` captions the titles and closing.

## 美好能否留存？ (`can-beauty-last`, prepared 2026-10-27)

The lesson is 看得见的诗 · 第三期 (lang PR #20, merged 2026-10-27): Sunny reads the Chinese, Matthew the English, and
the film takes the lesson's published clips (`films.clip` falls back to `lang/public/audio/<film>/<lang>/vNN-whole.mp3`;
`ZHONG_YING_LANG=…/lucas-academy-lang-beauty` while the main lang checkout is behind origin and holds the owner's own edits). The three living paintings are new in art-lab
(branch `living-poems-3`, not merged): `paint.py` reads pictures from an art-lab export, so export again once they
are on art-lab's main. The paint plans are in `paintings.py`; every pixel that needs paint belongs to a region
(checked by overlaying the regions on each picture).

MiniMax runs are prepared, not submitted: `minimax/{chun-ye-xi-yu,sonnet-18,ecclesiastes-3-11}/v1` (1080P, 6 s,
first frame only).

Built 2026-10-29 (owner: 「可以做 春夜喜雨 那个video了吧」). MiniMax at 11:10 PDT: 传道书 v1 came back (birds cross, leaves
drift, the watercolour kept; `minimax-ecclesiastes-3-11.mp4`, no `--tone`); 春夜喜雨 and Sonnet 18 v1 failed 1033
「system error」 within a minute. Not resent (owner's call): v2 of each is prepared — the 1440 picture as the first
frame, as for 小船's boats; Sonnet's prompt without the girl, 春夜喜雨's without the lamp. Until then those two end
alive on their own panels and the 回顾 replays those ends. Titles and closing in Sunny's and Matthew's voices:
`narration.py lesson-extras can-beauty-last`, then `lesson_voice.py DATA/narration/lesson-extras can-beauty-last zh|en
--only …` (`films.extra()` takes those first); both closings picked by hand to the take Whisper heard word for word
(takes.json `picked`). The closing is still the draft. Pictures from the art-lab export of PR #15
(`art-lab-6eb189c`, served on 8747 for `living.mjs --url`). Sonnet 18's hills end at 0.70 so the girl's
underpainting goes with the meadow (it hung below the hills as a tab for a minute).
Owner: 「Resubmit both」 → v2 of 春夜喜雨 and Sonnet 18 sent at 11:57 PDT; both failed 1033 again within 15 s (the
same picture-level failure as 小船's oil, which took four tries). Packaged film unchanged: only 传道书 moves.
Owner: 「Retry in an hour」 → v3 sent once each at 12:58 PDT: 768P, short prompts (rain/river/boat; breeze/branches/
grass/clouds), first frame = the film's own living capture (`living-<id>.jpg`, 1440×960). Both failed 1033 again
within a minute — three tries each, three different prompts and two resolutions. Not only the pictures, though:
以赛亚书 v1–v3 were the same request byte for byte (picture and prompt), 1033 twice, then a clip an hour later.
Film unchanged; not resent. Owner: 1033 is a database problem on MiniMax's side, not the request. 2026-10-30
(owner: 「再试一下 minimax」, 「应该还有额度」): v4 of each at 08:38 PDT, the art-lab picture (1536×1024, as every other
clip that came back) with v2's prompt (no girl, no lamp), 1080P. Both came back within three minutes: 春夜喜雨's rain
falls and the boat drifts, colours kept; Sonnet 18's grass and blossoms move in the wind and the sky deepens to a
stronger blue (kept without `--tone`, as 以赛亚书's). All three works now have a clip.
Owner: 「标题 作者 Sunny 都破音了 用Fangfang」 → the Chinese titles (title + author) are Fangfang's, like the other films'
(`films` `series_voices`; `narration.py extras can-beauty-last` voices them, `choose extras` picks, and
`films.extra()` now takes chosen.json before lesson-extras). Then 「最后回顾那段配音 应该是 fangfang/louise」: the
closing over the 回顾 too (`series_voices: {"zh": ("titles", "closing"), "en": ("closing",)}`, voiced with
`narration.py extras can-beauty-last-closing`). Sunny and Matthew read the verses and the English titles.
Fangfang's takes b and c pause between 好 and 雨, so a is pinned; Louise's b is pinned (both Whisper models hear
"God set", a and c "said"). lucas-narrate has no seed: the same script in the same order makes the same takes, so
more takes need different text or a different place in the script. The aligner put Louise's "lines;" in the quiet
before "God" (8.06 s; it is said at 7.08): `align.py` `pull_back` moves such a word back onto the voice no word
covers (it also fixes "subscribe," 2.0 → 1.5 s in the series' last line, as Whisper hears it). Film 6:09.2. 杜甫 is spelled 杜[f][ǔ] (`SPOKEN`): without it Whisper heard 杜福 / 渡府 in all three takes; take e is
pinned, the one heard as 「春夜喜雨，唐，杜甫」. 传道书's first three takes each had a lone sound before the voice
(`strays`), so three more were made; f is clean. Film 6:18.5 (was 6:25: Fangfang reads the titles faster).
