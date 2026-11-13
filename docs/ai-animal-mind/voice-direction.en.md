# What Are Animals Thinking? Does AI Know? · Voice direction (English track)

How each line is read; the captions always show [en-draft.md](en-draft.md). Same markers as Fun Informatics 4
(`scripts/ai-animal-mind/narrate.py` reads them): a section's `｜语气 X` is its tone, a line's own `｜语气 X` overrides it,
`停顿 N` is the silence before the line, `读 |` is what the voice reads when it differs from the caption.

**v0.1.1 (2026-11-10)**: am07-02 and am12-04 reworded and voiced again (en-draft v0.1.1); am06-04 voiced again ("Hans" was heard as "Huns"); am03-03's stray tail word after "elephants" trimmed at 5.02 s (original in alternates/); the two looking moments now 9.5 s (am08-03, am10-01).

**v0.1 (2026-11-10)**, for en-draft v0.1. Voice `louise/en` (Yancy, 11-10), zero-shot-instruct, 1.1 for every line, as
in Fun Informatics 4's English film. Yancy wants the film lively (「整体气氛比较活泼」); the liveliness comes from the music
and the cutting, not a "lively" instruction, which ran too fast across a whole film before (README, 2026-10-08).

Tones (nothing slow):

- base: "Please speak in a warm, curious voice, like discovering something interesting together with friends and parents."
- curious: "Please speak with warm curiosity, like wondering about a question together with a friend, never quizzing." (every question put to the viewer; at least 1.2 s of silence follows it)
- gentle: "Please speak gently and sincerely, like quietly sharing something close to your heart." (Yancy's own sunset, and the music and art section)

What the voice reads differently from the captions, and why:

- **AI → "A.I."**: said as two letters, never "eye".
- **Jesu → "Yay-zoo"**, **Pietà → "Pee-ay-tah"**, **Monet → "Mo-nay"**: names Louise may read the English way.
- **Quotation marks** around "understand", "alphabet", "good", "bad", "beautiful" are for the eye only; the voice reads the word plainly.
- Words Louise has slipped on before are avoided in the text itself: "cannot" not "can't", "is not" not "isn't" (README / narration lessons).

Risks to listen for: the dolphin and whale names of sounds ("click, click, click"), "hmm" in am08-03, the quoted replies in am04-04.

## AM00 · The Sunset ｜语气 base

am00-01 | Do monkeys enjoy a sunset? ｜停顿 1.0 ｜语气 curious
am00-02 | My favorite thing is watching the sunset by the sea. The water slides softly over the sand, the sea and the sky melt into one color, and I feel a kind of peace I cannot put into words. ｜停顿 1.6 ｜语气 gentle
am00-03 | So what does a monkey feel when it sees a sunset? ｜停顿 1.0 ｜语气 curious
am00-04 | A man who studied monkeys in Africa once told a story about one evening. ｜停顿 1.4
am00-05 | He was sitting alone on a hillside, watching the sun go down over a lake.
am00-06 | Two monkeys climbed up from either side. First, they shook hands. Then they sat down right beside him. ｜停顿 0.8
am00-07 | One man, two monkeys, all watching the sunset together. The monkeys only left when it got dark. ｜停顿 0.8
am00-08 | Monkeys notice the sunset. They even sit down to watch it. But do they enjoy it the way we do, with that romantic, almost philosophical feeling? ｜停顿 1.6 ｜语气 curious
am00-09 | I would love to know. But I cannot ask them. ｜停顿 1.2 ｜语气 gentle
am00-10 | So, can AI help me find out what animals are thinking? ｜停顿 0.8 ｜语气 curious
  读 | So, can A.I. help me find out what animals are thinking?

## AM01 · AI Learned Our Language ｜语气 base

am01-01 | These days, AI seems to "understand" what we say. You ask, it answers. You say half a sentence, and it finishes the rest. ｜停顿 3.0
  读 | These days, A.I. seems to understand what we say. You ask, it answers. You say half a sentence, and it finishes the rest.
am01-02 | How did it learn? Put simply: it read a huge amount of human writing, and practiced, over and over, guessing the next word.
am01-03 | So what if it listened to animal sounds, and practiced guessing the next sound? Would that work? ｜语气 curious
am01-04 | Some people are really trying. One group spent years recording dolphins, and now they are letting AI listen, and guess.
  读 | Some people are really trying. One group spent years recording dolphins, and now they are letting A.I. listen, and guess.
am01-05 | The AI has learned to make sounds a lot like a dolphin's. But what do those sounds mean? ｜语气 curious
  读 | The A.I. has learned to make sounds a lot like a dolphin's. But what do those sounds mean?
am01-06 | Our own language, we understand, so we can tell when the AI guesses right. With dolphins, who will tell us if it's right? ｜语气 curious
  读 | Our own language, we understand, so we can tell when the A.I. guesses right. With dolphins, who will tell us if it's right?

## AM02 · Click, Click ｜语气 base

am02-01 | Let's listen to sperm whales first. Out in the ocean, they go click, click, click, in little strings.
am02-02 | Some people recorded thousands of these strings, and had computers look for patterns.
am02-03 | And they found some. Some strings are fast, some are slow, some have an extra click, some stretch out a little. These changes can be mixed and matched, like building blocks.
am02-04 | The researchers said it's a bit like an "alphabet."
  读 | The researchers said it's a bit like an alphabet.
am02-05 | But if you know the alphabet, can you read a book? ｜语气 curious

## AM03 · Who's Calling Me? ｜语气 base

am03-01 | Just listening is not enough. So some people came up with an idea: ask the animals themselves.
am03-02 | On the African savanna, people recorded the low rumbles of elephants. After listening, an AI could guess which elephant a call was meant for, better than chance.
  读 | On the African savanna, people recorded the low rumbles of elephants. After listening, an A.I. could guess which elephant a call was meant for, better than chance.
am03-03 | Was it real? The researchers played the recordings back to the elephants.
am03-04 | A call meant for another elephant? It barely paid attention. The call meant for it? It called back, and walked toward the speaker.
am03-05 | Do elephants have names? And if they do, have they named rivers, and trees, and maybe even us? ｜语气 curious

## AM04 · Saying Something Back ｜语气 base

am04-01 | Once we can catch a tiny bit, we cannot help wondering: can we say something back?
am04-02 | Off the coast of Alaska, some people played a recorded whale call into the water. It was a call humpback whales use to say hello.
am04-03 | A humpback whale swam over and circled the boat. People played a call, and she called back. Back and forth, for twenty minutes.
am04-04 | The call people played probably meant something like "hello." So what did she say back? "Hello"? "Who are you?" Or "Keep it down"? ｜语气 curious

## AM05 · Making Up New Words ｜语气 base

am05-01 | Other people had a different idea: if we cannot understand dolphins, why not make up a few new words together with them?
am05-02 | One whistle means seaweed. Another whistle means scarf. If a dolphin learns to whistle it, people hand it the thing.
am05-03 | Does that count as talking? If you could agree on just three words with a dolphin, which three would you pick? ｜语气 curious

## AM06 · A Horse Who Could Do Math ｜语气 base

am06-01 | That reminds me of a horse. His name was Hans, and more than a hundred years ago, he was famous in Germany. ｜停顿 1.6
am06-02 | People said he could do math. Ask him a question, and he would tap out the answer with his hoof. Experts came to check, and said there was no trick.
am06-03 | Then someone had an idea: what if Hans could not see the person asking?
am06-04 | And suddenly, Hans could not answer. ｜停顿 0.8
am06-05 | It turned out he had been watching people all along. When he reached the right tap, the person asking would move, just a tiny bit, without even noticing. But Hans noticed. ｜停顿 0.8
am06-06 | Hans did not understand math. But maybe, he understood people very well? ｜语气 curious
am06-07 | Animals are so good at reading us. Are we any good at reading them? ｜语气 curious

## AM07 · Is It Happy? ｜语气 base

am07-01 | Their words, we do not understand yet. But what about feelings? Surely we can tell if an animal is happy or sad? ｜停顿 1.6
am07-02 | Some people recorded thousands of sounds from pigs: some when they were happy, some when they were scared or in pain. Then they gave them to an AI to learn.
  读 | Some people recorded thousands of sounds from pigs: some when they were happy, some when they were scared or in pain. Then they gave them to an A.I. to learn.
am07-03 | Afterwards, the AI could sort about nine out of ten: this sound is "good," that sound is "bad."
  读 | Afterwards, the A.I. could sort about nine out of ten: this sound is good, that sound is bad.
am07-04 | But wait. Who told the AI which sound was "good" and which was "bad" in the first place? ｜语气 curious
  读 | But wait. Who told the A.I. which sound was good, and which was bad, in the first place?
am07-05 | People did. So, are people good at telling? ｜语气 curious

## AM08 · Your Turn ｜语气 base

am08-01 | Let's try it ourselves.
am08-02 | Look at these cats and dogs. Can you tell if they're happy, or not? ｜语气 curious
am08-03 | Some are easy to read. Others... hmm, hard to say. ｜停顿 9.5

## AM09 · The Vacuum Cleaner ｜语气 base

am09-01 | Someone did an experiment. They asked lots of people to watch a video of a dog, and guess whether it was happy.
am09-02 | With a vacuum cleaner next to the dog, people said: it's unhappy. With a leash next to the dog, people said: it's happy.
am09-03 | Then the researchers quietly swapped the backgrounds. And people's answers swapped too.
am09-04 | So what were we looking at: the dog, or the vacuum cleaner? ｜语气 curious
am09-05 | What about other animals? Can you tell if they're happy, or not? ｜语气 curious

## AM10 · Little Faces ｜语气 base

am10-01 | Some people filmed close-ups of mouse faces, and gave them to an AI to look at. ｜停顿 9.5
  读 | Some people filmed close-ups of mouse faces, and gave them to an A.I. to look at.
am10-02 | The AI could tell: this one likes it, this one hates it, this one hurts, this one is scared.
  读 | The A.I. could tell: this one likes it, this one hates it, this one hurts, this one is scared.
am10-03 | A thirsty mouse drinking sugar water had a happier little face than a mouse that had already had plenty to drink.
am10-04 | Such a tiny face, with so much written on it? ｜语气 curious

## AM11 · Beauty ｜语气 base

am11-01 | So we can tell "good" from "bad." But what about "beautiful"? ｜停顿 1.6 ｜语气 curious
  读 | So we can tell good from bad. But what about beautiful?
am11-02 | Some people taught pigeons to look at paintings: Monet on one side, Picasso on the other. The pigeons learned, and could even sort paintings they had never seen before.
  读 | Some people taught pigeons to look at paintings: Mo-nay on one side, Picasso on the other. The pigeons learned, and could even sort paintings they had never seen before.
am11-03 | They can tell them apart. But do they like them? ｜语气 curious
am11-04 | Some people played Mozart to rats. Their little heads bobbed along to the beat.
am11-05 | Were they dancing? Or enjoying the music? ｜语气 curious
am11-06 | Some people let little monkeys choose for themselves: on one side, a slow lullaby. On the other, no sound at all. The little monkeys chose the quiet side.
am11-07 | When people were given the same choice, they chose the music.

## AM12 · Something Deep Inside ｜语气 gentle

am12-01 | Why do we want to listen to music? Why, when we see a sunset, do we stop, and want to paint it, write a song about it, or call out to someone: "Come and look!"? ｜停顿 1.6
am12-02 | Why can some music and art stir something so deep inside us?
am12-03 | Like this piece by Bach, "Jesu, Joy of Man's Desiring," and Michelangelo's "Pietà."
  读 | Like this piece by Bach, Yay-zoo, Joy of Man's Desiring, and Michelangelo's Pee-ay-tah.
am12-04 | So, what feelings are held inside these works? And can we feel them?

## AM13 · Back to the Sunset ｜语气 gentle

am13-01 | Those two monkeys sat on the hillside until dark. Was there a little bit of that feeling inside them, too? ｜停顿 9.0
am13-02 | Right now, nobody knows the answer. Lots of people are studying it, and AI is helping them listen, and look. ｜语气 base
  读 | Right now, nobody knows the answer. Lots of people are studying it, and A.I. is helping them listen, and look.
am13-03 | What do you think? Do monkeys enjoy a sunset? ｜停顿 1.0 ｜语气 curious
