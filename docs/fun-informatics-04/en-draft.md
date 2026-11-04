# The Nobel Prize: What Is Optogenetics? Seen Through Informatics · English script v0.1.1 (2026-11-01)

Fun Informatics 4. By Yancy Qin | Lucas Academy. Its own film, not a dub (Yancy 11-01: 文字比较多，就要出独立的英文片). Structure, facts and
sources: [FUN-INFORMATICS-04.md](../../FUN-INFORMATICS-04.md); the Chinese script it follows: [zh-draft.md](zh-draft.md) v0.2.

- Same line ids as the Chinese film, one English line for each Chinese line, so the two films share one shot list
  (scripts/fun-informatics-04/edit.json). Written as Yancy speaking, the way the Chinese is; no new facts, no quips.
- Episode 1's English film is quoted in its own words (its it02-06, it04-08, it07-07, it08-05).
- Verses: World English Bible (public domain), except John 1:5, where the WEB's "hasn't overcome it" would lose the
  point the film builds on (the light shines, but is it received?); there the film reads the King James Version (public
  domain), "the darkness comprehended it not", which keeps it. The Chinese film reads the CUV 「黑暗却不接受光」.
- v0.1.1: og02-10 "rat nerve cells" → "rats' nerve cells" (the voice's "rat" was heard as "red" twice); og03-02 "a string of ons and offs" → "a whole string of switches, on and off" ("ons" was heard as "ions").
- Names as said in English: Peter Hegemann, Georg Nagel, Karl Deisseroth, Francis Crick, James Watson.

---

## OG00 · A Dish of Green Water

- og00-01 | Have you ever wondered: if the brain had switches too, what would happen if you pressed one?
- og00-02 | The scientists who won this year's Nobel Prize in Physiology or Medicine gave that question an answer.
- og00-03 | They really did find a switch, and put it into a mouse's brain. The light came on, and the mouse's whiskers moved.
- og00-04 | Later, a man who could no longer see put on a pair of glasses that give off light, practised for a few months, and began to make out the crosswalk on the street.
- og00-05 | Sounds like magic, right? But back in episode 1, we said there's no magic inside a computer. And there's none here either.
- og00-06 | It has a name: optogenetics. And its story begins with a dish of green water.
- og00-07 | Let's take a look at a dish of water.
- og00-08 | Stirred into it is a tiny, tiny green alga. Line up a hundred of them, and they're only a millimetre and a half long. You can't see them one by one, so the whole dish just looks faintly green.
- og00-09 | Now, let's shine a light from one side.
- og00-10 | After a while, the green slowly drifts over toward the light. It's these little algae, swimming toward it.
- og00-11 | Each one is a single cell. No eyes, no brain. So how does it know which side the light is on?
- og00-12 | More than thirty years ago, a scientist in Germany named Peter Hegemann wanted to know that too.
- og00-13 | Following that question all the way led to optogenetics. So what is optogenetics? Today, I'd like to look at it with you, through the lens of informatics.

## OG01 · Switches

- og01-01 | Remember episode 1? We asked: how does a computer add 1 + 1?
- og01-02 | The answer was switches. A computer has billions of tiny switches, each either on or off. On is 1, off is 0.
- og01-03 | With two switches and two lamps, it works out 1 plus 1: "one, zero".
- og01-04 | What about our brains? The brain has about ninety billion nerve cells.
- og01-05 | A nerve cell either sends a signal or it doesn't, and the signals it sends are all about the same size. Isn't that a bit like a switch?
- og01-06 | Of course, the brain is far more complicated than a computer: when signals come, and how fast, carry information too. But "fire, or don't fire" is the most basic step.
- og01-07 | Scientists had long wished they could press the switch of one particular kind of nerve cell from the outside, and see what happens.
- og01-08 | Francis Crick, who discovered the DNA double helix with James Watson, thought about this. Nerve signals are so fast, he said, that the best way to press such a switch would be with light. He admitted himself that it sounded far-fetched.

## OG02 · The Alga's Switch

- og02-01 | Let's go back to that dish of green water.
- og02-02 | The alga has a small orange dot on it, called the eyespot. Hegemann found that half a millisecond after light hits the eyespot, an electrical signal appears.
- og02-03 | How fast is half a millisecond? When light enters our eyes, turning it into an electrical signal takes at least ten milliseconds. The tiny alga is twenty times faster.
- og02-04 | He guessed: with something that fast, there can't be many steps in between. Maybe one single thing both catches the light, and is itself a door. Light arrives, the door opens, charged particles flow into the cell, and that's an electrical signal.
- og02-05 | Back then, many people didn't believe it. No one had ever seen a door that light could open.
- og02-06 | Later, he and another scientist, Georg Nagel, put the alga's gene for this door into frog eggs. The door grew on the surface of the eggs, and when light shone on it, the door opened in less than a millisecond.
- og02-07 | The door has a name: channelrhodopsin. That's hard to remember, so let's just call it a "light switch".
- og02-08 | The best part: put it into other cells, and those cells start listening to light, too.
- og02-09 | In America, there was a doctor who was also a scientist, Karl Deisseroth. He had met many patients in psychiatry, and he wanted very much to understand how a living brain works.
- og02-10 | He wrote to Nagel, got the gene, and put it into rats' nerve cells in a dish. Blue light came on, and the nerve cells fired at once. That was in 2005.
- og02-11 | Two years later, they put the light switch into the brains of living mice, shining light in through a very thin optical fibre. The light came on, and the mouse's whiskers moved.
- og02-12 | The light lit up a small patch, but only the one kind of nerve cell that had the switch responded. The cells right next to them acted as if they hadn't heard a thing.
- og02-13 | From then on, scientists had a switch. They could pick one kind of nerve cell and press it from the outside. One flash of light, one signal.

## OG03 · From Switches to Messages

- og03-01 | But one press of a switch can only say "yes" or "no". That's one bit.
- og03-02 | To say a whole sentence, you need a whole string of switches, on and off.
- og03-03 | In episode 1 we also said: one string of 0s and 1s, five meanings. It never changed once. Only the rule did.
- og03-04 | So, could light, flashing on and off, carry a whole picture into a pair of eyes that can't see?

## OG04 · The Eye

- og04-01 | Actually, our eyes already have light switches of their own. They sit in the retina, at the very back of the eye, and they're called rods and cones.
- og04-02 | They turn light into electrical signals and pass them along, like a relay, to the cells behind them, and finally along the optic nerve into the brain.
- og04-03 | There's a disease called retinitis pigmentosa that makes these light switches fail, one by one, and little by little, a person stops being able to see.
- og04-04 | But often, the relay cells behind them, and the optic nerve, that "wire", are still fine.
- og04-05 | It's like a camera whose light-sensing chip is broken, while the cable to the computer still works perfectly.
- og04-06 | So could we give those healthy cells new light switches?

## OG05 · Seeing the Crosswalk Again

- og05-01 | Someone really tried.
- og05-02 | In 2021, scientists reported on a 58-year-old patient. He had this disease, and he could no longer see things.
- og05-03 | Doctors delivered a gene into one of his eyes, so that relay cells in his retina grew light switches. This switch also came from an alga, but it doesn't respond to blue light. It responds to amber light, which is safer for the eye.
- og05-04 | But the new switch only opens with very bright light. Ordinary light isn't enough.
- og05-05 | So he also wears special glasses. A camera on them spots where the scene in front of him is getting brighter or darker, and instantly turns that into flickering amber dots of light on his retina.
- og05-06 | What the glasses do has a name in informatics: "encoding". Turning the scene into dots of light the new switches can catch.
- og05-07 | And his brain has to learn "decoding": reading those dots of light back into the shapes of things.
- og05-08 | At first, he felt the glasses weren't much help.
- og05-09 | After a few months of practice, he began to make out the white stripes of the crosswalk on the street.
- og05-10 | In the lab, with a notebook on the table, he could find it and reach out to touch it, 36 times out of 39.
- og05-11 | Of course, this is only one patient, and only part of his sight came back. Without the glasses, he still can't see. The treatment is still in clinical trials.
- og05-12 | But think about it: the light is still light, and the switches are still switches. What changed is the rule. His brain spent a few months learning to read a new one.

## OG06 · Light in the Bible

- og06-01 | With all this talk about light, I'm reminded how often the Bible talks about light, too.
- og06-02 | Sometimes, it means the light our eyes can see. Genesis chapter 1 says: "God made the two great lights: the greater light to rule the day, and the lesser light to rule the night. He also made the stars."
- og06-03 | A psalm says: "Your word is a lamp to my feet, and a light for my path." It sounds like a lamp you'd carry on a walk at night. But what it means is God's word.
- og06-04 | More often, the Bible means spiritual light. Jesus said: "I am the light of the world. He who follows me will not walk in the darkness, but will have the light of life."
- og06-05 | And in John's Gospel: "The light shineth in darkness; and the darkness comprehended it not."
- og06-06 | The light keeps shining. But whether it's received is another matter.
- og06-07 | Do you need a light like this?
- og06-08 | Besides our eyes, what kind of decoder do we need to receive a light like this?
- og06-09 | If you enjoyed this video, please subscribe to our channel! Here, we learn and think together.
- og06-10 | And leave a comment to tell us what topics you'd like to explore!
