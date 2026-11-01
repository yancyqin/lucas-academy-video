// Dumps the reading texts of 语言的桥's 看得见的诗 lessons (lucas-academy-lang) as JSON for the 中英阅读 films.
//
//   node scripts/zhong-ying/texts.mjs <lang repo> <lesson id> > out.json
//
// Each unit keeps the lesson's own word segmentation ("\n" is a line break of its own) and its English. Scripture
// units have no English here: lang reads the NIV through its Worker, and the films take the narrated NIV from
// lucas-academy-media's (git-ignored) narration script instead, so it never enters this repository.
import { pathToFileURL } from "node:url";
import { join } from "node:path";

const [langRepo, lesson] = process.argv.slice(2);
if (!langRepo || !lesson) throw Error("usage: texts.mjs <lang repo> <lesson id>");
const { units } = await import(pathToFileURL(join(langRepo, "public/lessons", lesson, "text.js")).href);
const out = units.map((unit, i) => ({
  n: i + 1,
  tokens: unit.tokens,
  en: unit.en ?? null,
  ref: unit.ref ?? null,
}));
process.stdout.write(JSON.stringify(out, null, 1));
