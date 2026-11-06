"""The 20 x 20 pictures: the 12 training examples from perceptron.html, plus 10 new test pictures.

Strokes are drawn exactly like the page's JavaScript (stroke/seven20/one20), so a 7 here is the same 7 there.
"""
import math

N = 20


def blank():
    return [0] * (N * N)


def js_round(v):
    return math.floor(v + 0.5)   # JavaScript's Math.round


def stroke(pic, x0, y0, x1, y1, w=2):
    steps = max(abs(x1 - x0), abs(y1 - y0)) * 2 or 1
    for s in range(steps + 1):
        x = js_round(x0 + (x1 - x0) * s / steps)
        y = js_round(y0 + (y1 - y0) * s / steps)
        for dy in range(w):
            for dx in range(w):
                xx, yy = x + dx, y + dy
                if 0 <= xx < N and 0 <= yy < N:
                    pic[yy * N + xx] = 1
    return pic


def seven(dx, dy, tilt):
    p = stroke(blank(), 4 + dx, 3 + dy, 14 + dx, 3 + dy)
    return stroke(p, 14 + dx, 3 + dy, 8 + dx + tilt, 16 + dy)


def one(dx, dy, flag):
    p = stroke(blank(), 10 + dx, 3 + dy, 10 + dx, 16 + dy)
    return stroke(p, 10 + dx, 3 + dy, 7 + dx, 6 + dy) if flag else p


# the page's "7 or 1" set at 20 x 20
TRAIN = [
    (seven(0, 0, 0), True), (one(0, 0, True), False),
    (seven(-3, 1, -1), True), (one(-5, 1, False), False),
    (seven(3, -2, 1), True), (one(4, -2, True), False),
    (seven(1, 2, 2), True), (one(-2, 2, True), False),
    (seven(-2, -3, 0), True), (one(6, -1, False), False),
    (seven(4, 0, -2), True), (one(-7, 0, True), False),
]

# new positions and tilts, never seen in training
TEST = [
    ('seven-a', seven(2, 1, -1), True), ('one-a', one(2, 1, True), False),
    ('seven-b', seven(-1, -1, 1), True), ('one-b', one(-3, -2, False), False),
    ('seven-c', seven(5, 2, 0), True), ('one-c', one(5, 2, True), False),
    ('seven-d', seven(-4, -1, 2), True), ('one-d', one(-6, 1, True), False),
    ('seven-e', seven(0, 3, -2), True), ('one-e', one(3, -3, False), False),
]


def many_examples():
    """A bigger class: 7s and 1s at every position and tilt, except the ones used in TEST."""
    used = {(dx, dy, t) for dx, dy, t in [(2, 1, -1), (-1, -1, 1), (5, 2, 0), (-4, -1, 2), (0, 3, -2)]}
    used_ones = {(2, 1, True), (-3, -2, False), (5, 2, True), (-6, 1, True), (3, -3, False)}
    out = []
    for dx in range(-5, 6):
        for dy in range(-3, 4):
            for tilt in (-2, 0, 2):
                if (dx, dy, tilt) not in used:
                    out.append((seven(dx, dy, tilt), True))
    for dx in range(-7, 7):
        for dy in range(-3, 4):
            for flag in (True, False):
                if (dx, dy, flag) not in used_ones:
                    out.append((one(dx, dy, flag), False))
    return out


def as_text(pic):
    """The picture as 20 lines of # (ink) and . (paper): the same 400 numbers the perceptron reads."""
    return '\n'.join(''.join('#' if pic[r * N + c] else '.' for c in range(N)) for r in range(N))


PROMPT = ("This is a 20 by 20 black-and-white picture of a handwritten digit. "
          "'#' is black ink and '.' is white paper.\n\n{grid}\n\n"
          "Is this the digit 7? Answer with only one word: YES or NO.")


def prompt_for(pic):
    return PROMPT.format(grid=as_text(pic))


if __name__ == '__main__':
    for name, pic, answer in TEST:
        print(name, 'YES' if answer else 'NO')
        print(as_text(pic))
        print()
