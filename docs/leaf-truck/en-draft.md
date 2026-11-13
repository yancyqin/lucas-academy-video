# Why Did a Leaf Stop a Self-Driving Truck? · English draft v0.1 (2026-11-11)

Same lines as the Chinese draft, in natural English.

Spoken English avoids words Louise has garbled before:
- "road" becomes "trip" or "street" ("route" was heard as "root").
- "braked" becomes "hit the brakes" ("braked" was heard as "break").
- "can't / couldn't / didn't" become "cannot / could not / did not".

## LF01 · A few leaves

- lf01-01 | Let me tell you about a truck.
- lf01-02 | In a small town in Austria, it drives back and forth between two factories, with no driver.
- lf01-03 | The trip is short, and it goes slowly. But every so often, it slams on the brakes.
- lf01-04 | There is no one in front of it. No other car.
- lf01-05 | What stopped it was a few fallen leaves.

## LF02 · Too sensitive, and not sensitive enough

- lf02-01 | Later, the engineers compared over a month of records. On the same street, it hit the brakes up to eleven times as often as human drivers.
- lf02-02 | Every hard stop sent the cargo lurching forward.
- lf02-03 | Stranger still, testing found it could not detect a wooden pallet only fourteen centimeters tall.
- lf02-04 | Leaves, it treated as obstacles. A real obstacle, it did not see.
- lf02-05 | If this were your truck, where would you start?

## LF03 · Don't guess yet

- lf03-01 | A lot of people would say: the sensor is broken. Replace it.
- lf03-02 | The engineers did not rush. First, they logged every single stop.
- lf03-03 | Six and a half weeks, forty-seven stops. Some for other vehicles, some because it lost track of where it was, some for the weather.
- lf03-04 | Put every possible cause on the table, then check each one against the evidence.

## LF04 · Change one thing at a time

- lf04-01 | Why would leaves make it brake? Let's imagine a simple test.
- lf04-02 | In a simulator, a person steps onto a crosswalk, and the wind blows leaves across the street. The car stops.
- lf04-03 | Did it stop for the person, or for the leaves? From this one run, we cannot tell.
- lf04-04 | So change one thing at a time. First take away only the leaves. Then take away only the person. Which time do you think it still stops?
- lf04-05 | If it still stops once the person is gone, the problem is the leaves.
- lf04-06 | The real report found the cause: its lidar was missing a filter, so it could not tell leaves from real obstacles.

## LF05 · One hard stop, a chain of effects

- lf05-01 | A hard stop does not only affect the truck.
- lf05-02 | The car behind can nearly hit it, the cargo shifts, and it used about a fifth more energy.
- lf05-03 | A small flaw travels further than you would expect.

## LF06 · The hard part is the trade-off

- lf06-01 | So why not just make it less sensitive?
- lf06-02 | That fourteen-centimeter pallet is the answer. Too dull is no good either.
- lf06-03 | So start from the goal: ignore the leaves, but never miss a pallet or a person. Then work backward to what the truck needs to tell apart.
- lf06-04 | In the same project, engineers proposed more than one fix: teach the system to treat soft things like leaves and branches as non-obstacles, and add cameras to help the lidar see low objects.

## LF07 · Back to us

- lf07-01 | We do something like this every day.
- lf07-02 | Paper plane won't go far? Where's the problem? Is it wobbling, or dropping too fast?
- lf07-03 | Then change one fold at a time, and see how it flies.
- lf07-04 | Can't find your keys? Think back: when did you last use them?
- lf07-05 | I think even the most advanced engineering takes a big problem apart and lets different ways of thinking complement each other.
- lf07-06 | When new problems keep coming up, could we try ways of thinking we know well, and some we don't?
