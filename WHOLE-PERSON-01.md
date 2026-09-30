# 全人教育①：老师的权柄从哪里来？ / Whole-Person Education 1

Video of [yancyqin/lucas-academy-media#5](https://github.com/yancyqin/lucas-academy-media/issues/5).
Script confirmed by Yancy 2026-09-29 (small wording edits 2026-09-30 in wp05-07,
wp10-03, wp10-04). zh = Yancy's own voice (`yancy/zh`, instruct tone + 【】
emphasis), en = `louise/en` (Yancy's English clone rejected: accent).

## Status (2026-09-30) — work in progress, direction changing

- Preview v1 (`out/whole-person-01/preview-zh-v1.mp4`, local only) = idea 1
  only, zh in the earlier "classroom" tone (`whole-person-01-d`), concept
  placeholders. Yancy: the tone was wrong.
- Decided since: zh tone = 「请用轻松、亲切的语气，像坐在孩子旁边聊天一样说，语速放慢一点，问句要有真的在问的感觉。」
  at speed 0.9 (set in the media repo's `*-zh.narration.json` /
  `whole-person-ideas-2-5-zh.json`); not yet generated for the full script.
- Scope grew to all five ideas (idea 1 full + ideas 2–5 about 1 min each, per the
  community slides) — scripts confirmed in lucas-academy-media
  `data/scripts/whole-person-ideas-2-5*.{md,json}`. This edit does not
  include them yet.
- Backgrounds are to become app screen recordings with cross-fades
  (Inception Space, Art Lab + Sky Room floor with fish, Gallery, Chinese,
  Coder Arena) instead of concept images. Codex's 20 concept images are in
  `public/whole-person-01/concept/`, kept **local only** (not committed) in
  case they are used.
- Yancy has new ideas for the video and content — check with Yancy before
  continuing the edit.

## Pipeline

```bash
# 1. narration (lucas-academy-media, CPU)
#    zh: mode D = instruct tone + <strong> from the 【】 marks in
#        data/scripts/whole-person-01-authority-zh.emphasis.md
#        -> outputs/yancy/zh/whole-person-01-d/
.conda/bin/lucas-narrate data/scripts/whole-person-01-authority-en.json --profile louise/en --language en --speed 1.0 --output-dir outputs/louise/en/whole-person-01
# 2. timeline + audio tracks + SRTs (this repo; re-run after adding images/footage too)
npm run wp01:timeline
# 3. render zh / en / clean
npm run wp01:render
```

zh and en were split into sentences independently; `build_timeline.py` pairs
them into 48 shared cues (`GROUPS`). Every cue lasts `max(zh, en) + pause`, so
the one picture edit carries either audio track and both SRTs share cue
boundaries. Pictures are planned cue by cue in
`src/videos/whole-person-01/shots.ts`; anything missing renders as a labelled
placeholder, and missing footage falls back to its concept image.

## Concept images for Codex

Save as PNG, 1920×1080, with exactly these names in
`public/whole-person-01/concept/`, then re-run `npm run wp01:timeline`.
**No text in any image** — every word on screen is typeset in the edit.

### Shared style block — paste in front of every prompt

> Warm, simple children's picture-book illustration for an educational video,
> 16:9, 1920×1080. Soft flat colour with gentle paper texture and clean,
> slightly rounded charcoal outlines. Palette: cream paper (#F5EEDF), warm
> terracotta (#C9704F), dusty blue (#2F4A6D), sage green (#8FAE8B), honey
> yellow (#E7B75A), soft wood browns. Calm, kind, unhurried mood; morning
> light. Faces are simple — dot eyes, small curved mouth, no detailed
> features. Everyone is drawn at a natural size; nobody wears a crown, nobody
> is on strings, no halos, no glowing figures, no arrows or hierarchy
> diagrams. No text, no letters, no numbers, no logos, no watermark, no
> writing on boards or pages (use blank lines or soft scribble marks only).
> Keep the bottom 22% of the frame quiet (floor, table edge, plain wall)
> because subtitles sit there.

### The cast — paste after the style block in every classroom prompt

> The same five characters appear in every picture, always drawn the same:
> **the teacher** — an adult of about 40, short dark hair, round glasses,
> a mustard-yellow cardigan over a white shirt, dark blue trousers;
> **Mia** — girl about 8, two dark braids, terracotta dress;
> **Leo** — boy about 7, short curly brown hair, sage-green sweater (he is the
> one who raises his hand and does not get to finish);
> **Sam** — boy about 9, straight black hair, blue-and-white striped shirt;
> **Ada** — girl about 6, reddish-brown bob, yellow raincoat-style jacket.
> Diverse, ordinary children in a small, warm, wooden classroom with a big
> window on the left, a low bookshelf, a rug, and a plain blank chalkboard.

| file | used in | prompt (after style block + cast) |
| --- | --- | --- |
| `wp01-classroom.png` | 片头 + WP01 | Wide view of the classroom. The teacher stands at the front beside the blank chalkboard, mid-explanation, one hand open. The four children sit at two small tables facing the teacher. Leo raises his hand high with a curious, hopeful face. Everyone else looks toward the teacher. Leave clear empty wall space on the upper right. |
| `wp02-home-classroom.png` | WP02 一切属于神 | A gentle split scene, left half and right half joined by soft morning light: left, a family kitchen table where a parent helps a child read a picture book; right, the same classroom with the teacher sitting among the children on the rug. Both halves share one warm sky through their windows, with soft light falling equally on everyone. No figures above or below each other. |
| `wp02-light.png` | WP02 fallback for footage | No people. Soft morning sunlight streaming through a large wooden-framed window onto a quiet empty classroom rug and a closed book on a low table. Dust motes in the light. Peaceful. |
| `wp03-read-first.png` | WP03 老师先受教 | Early morning, classroom empty of children. The teacher sits alone at a small wooden desk by the window, reading an open book carefully, a pencil in hand and a notebook beside it (pages show only blank lines). A cup of tea. Quiet, attentive, humble. |
| `wp03-read-together.png` | WP03 再教人 | EXACT same viewpoint, desk and window as `wp03-read-first.png`, but now later in the day: the teacher sits at the same desk with the book open and the four children gathered close around it, leaning in and looking at the page together; Mia points at a line. Same line style so the two images can cross-fade. |
| `wp04-pages.png` | WP04 fallback for footage | Close-up, no faces: two pairs of hands — an adult's and a child's — resting on the two pages of an open book on a wooden table; the adult's finger rests on a line, the child's finger traces the paragraph above it. Pages show only soft grey lines, no real text. |
| `wp04-look-together.png` | WP04 一起查一查 | Mid shot. The teacher and Sam sit side by side at a table sharing one open book. Sam points at a line with a questioning look; the teacher points at the lines above and below it, smiling, as if saying "let's read around it". Mia and Ada lean in from the other side. Pages show blank lines only. |
| `wp05-children.png` | WP05 孩子也可以明白 | The four children sitting on the rug in a small circle around an open picture book, talking about it eagerly; Ada, the youngest, is explaining something with both hands while the others listen. The teacher sits on a low chair just behind them, listening, not leading. |
| `wp05-listen.png` | WP05 孩子帮助老师 | Group discussion at the tables. Mia is speaking to the teacher and pointing toward Leo, whose hand is still half-raised and whose mouth is open as if mid-sentence. The teacher has just turned toward Leo with a surprised, thankful expression, body turning to listen. Sam and Ada look at Leo too. |
| `wp06-help.png` | WP06 帮助 | The teacher kneels beside Ada's desk, helping her with a worksheet (blank boxes only); Ada looks relieved. Gentle, patient. |
| `wp06-protect.png` | WP06 制止 | On the rug, Sam has grabbed a toy block from Leo. The teacher steps in calmly between them with one open palm — firm but kind, not angry — protecting Leo. Leo looks up at the teacher. Nothing scary, no crying. |
| `wp06-explain.png` | WP06 说明错在哪里 | The teacher at the blank chalkboard holding chalk, turned toward the class and explaining; Mia at the front table looks at her own notebook with a thoughtful "oh, I see" face. Leave the **right half of the chalkboard completely empty and large** (the edit writes 2 + 3 = 5 there). |
| `wp07-key-door.png` | WP07 fallback for footage | No people. An old wooden door standing slightly open, warm light coming through the gap, and a simple brass key in the lock. Calm, inviting. |
| `wp07-invite.png` | WP07 给别人打开学习的门 | Circle discussion on the rug. Everyone sits at the same height, the teacher included. The teacher turns with an open, inviting hand toward Ada, who sits a little apart at the edge of the circle and has not spoken yet; the other children turn toward her too, making room. Keep the **right third of the image calm and simple** (question cards appear there). |
| `wp08-basin.png` | WP08 fallback for footage | Simple symbolic still life, no people: a plain clay basin with water, a ceramic jug beside it, and a folded linen towel, on a wooden floor in soft light. Not a historical scene, no robes, no feet. |
| `wp08-listen.png` | WP08 用权柄服事 | The teacher crouches down to Leo's eye level in the classroom, listening closely while Leo speaks, one hand on the desk; beside them Mia explains something to Ada using her fingers to count. The teacher's posture is humble and warm. |
| `wp09-a-ask.png` | WP09 格一 | Close mid shot at the tables: Mia raises her hand and says she does not understand this step yet — slightly worried face, pointing at her notebook. The teacher pauses mid-gesture to listen. |
| `wp09-b-example.png` | WP09 格二 | The teacher holds up three red apples and two green apples in two hands to show a new example; Mia's face brightens. Same table and light as the previous panel. |
| `wp09-c-add.png` | WP09 格三 | Sam leans in from the side, eagerly adding his own idea with an open hand; Mia, Ada and the teacher all turn to look at what he is showing, thinking it through together. Same table and light as the previous panels. |
| `wp10-four.png` | WP10 结尾 | Four figures standing side by side on a plain cream background, all drawn at exactly the same height and size, evenly spaced, each in their own soft circle of warm light: the teacher (with a book), a parent (holding a lunchbox), a friend of about 12 (with a backpack), and Leo (the child, holding a drawing that shows only colour shapes). Friendly, equal, welcoming. |

## Stock footage (optional — concept images cover every slot)

Muted, 1920×1080 or larger, H.264 MP4, 8–15 s, saved in
`public/whole-person-01/footage/`. Only licenses that allow free use in a
published video without attribution (Pexels License, Pixabay Content License,
or CC0); record the page URL for each in `public/whole-person-01/footage/SOURCES.txt`.
**No identifiable faces, no children, no church branding, no text on screen.**

| file | used in | look for |
| --- | --- | --- |
| `wp02-light.mp4` | WP02 主祷文经文卡 | Morning sun through a window, slow; or soft light over a quiet field / sky. Calm, not dramatic. |
| `wp04-pages.mp4` | WP04 天天查考圣经 | Close-up of hands turning the pages of an open Bible or old book; text must be blurred or unreadable. |
| `wp07-key-door.mp4` | WP07 知识的钥匙 | A key turning in an old wooden door, door opening into light. |
| `wp08-basin.mp4` | WP08 洗脚、服事 | Water poured from a jug into a simple basin; a towel beside it. No feet, no people. |

## Typeset in the edit (not drawn)

Title card; Matthew 6:13 card (和合本 + NIV footnote wording); keyword cards
(教育的权柄，从哪里来？ / 一切属于神 / 教导的权柄是领受的 / 彼此服事);
scripture reference chips (太 28:18–20, 13:52, 11:25; 徒 17:11; 路 11:52; 约 13:13–14);
the 2 + 3 = 5 chalkboard; question cards in WP07 and WP10; "概念示意 / Concept
illustration" chips on every classroom picture; bilingual captions; end card
with the essay link, verse list and the NIV copyright notice.
