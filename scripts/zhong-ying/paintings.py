"""How each living painting is painted while its verses are read (ZHONG-YING.md §Painting).

Coordinates are fractions of the picture (x right, y down), as in the art lab's living.html.

REGIONS — the Chinese reading paints the picture in. Each region belongs to one verse (unit) and starts on
one of that verse's Chinese words ("河水#2" = its second 河水), so the sun is painted as 「白日」 is read and the
tower as 「楼」 is. A region is a shape, optionally narrowed by colour ("not_near": pixels far from these
colours), and a brush radius `r` in pixels of the 1230-wide film picture. Regions earlier in a work's list win
where shapes overlap. A region marked `over` is an object lying on something else (a boat on the river, a
child in the sand): the paint around it is first laid under it too, so its shape doesn't show early, and it is
painted on top when its word comes. Paper not in any region is laid down before the first stroke (it is blank paper anyway);
an oil painting lists regions for its whole canvas.

Shapes: ("rect", x, y, w, h) · ("circle", cx, cy, r) · ("poly", [[x, y], ...]) · ("or", s, s, ...) · ("and", s, s).

LIVING — the English reading adds the art lab's living brushes to what is already painted, one stroke per
entry, starting on one of the verse's English words: a brush key of that work and the path the brush is drawn
along (drawn over `dur` seconds), or ("tap", x, y) for a Draw Alive object (boat, monkey, eagle).
"""
from __future__ import annotations

import re

SKY_BLUE = (160, 190, 228)

REGIONS: dict[str, list[dict]] = {
    "deng-guanque-lou": [
        dict(name="tower", over=True, unit=2, at="楼", r=4, shape=("rect", 0.06, 0.41, 0.095, 0.135)),
        dict(name="birds", over=True, unit=2, at="千里", r=3, shape=("rect", 0.48, 0.11, 0.115, 0.08)),
        dict(name="sun", unit=1, at="白日", r=13, shape=("circle", 0.837, 0.281, 0.058)),
        dict(name="cliff", unit=2, at="更", r=18, shape=("poly", [[0, 0.47], [0.17, 0.47], [0.2, 0.55], [0.25, 0.62],
                                                                 [0.3, 0.7], [0.38, 0.76], [0.37, 0.83], [0.2, 0.84], [0, 0.82]])),
        dict(name="mountains", unit=1, at="山", r=24, shape=("rect", 0.2, 0.47, 0.8, 0.19)),
        dict(name="sea", unit=1, at="海", r=16, shape=("rect", 0.78, 0.67, 0.22, 0.11)),
        dict(name="river", unit=1, at="黄河", r=20, shape=("poly", [[0.48, 0.68], [0.72, 0.67], [1, 0.66], [1, 0.98], [0.84, 0.93],
                                                                   [0.6, 0.84], [0.5, 0.78]])),
    ],
    "foreign-lands": [
        dict(name="child", over=True, unit=3, at="我", r=4, shape=("rect", 0.12, 0.355, 0.06, 0.1), not_near=[SKY_BLUE]),
        dict(name="boat", over=True, unit=6, at="大船", r=4, shape=("rect", 0.885, 0.555, 0.05, 0.07)),
        dict(name="tree", unit=3, at="樱桃树", r=11, shape=("rect", 0.05, 0, 0.32, 0.47), not_near=[SKY_BLUE]),
        dict(name="trunk", unit=4, at="树干", r=12, shape=("rect", 0, 0, 0.12, 1), not_near=[SKY_BLUE, (196, 206, 120)]),
        dict(name="river", over=True, unit=6, at="河", r=9, shape=("poly", [[0.53, 0.63], [0.69, 0.672], [0.68, 0.715], [0.58, 0.745], [0.42, 0.78],
                                                                [0.23, 0.805], [0.23, 0.76], [0.4, 0.742], [0.555, 0.712], [0.595, 0.69],
                                                                [0.525, 0.66]]), not_near=[(200, 205, 120)]),
        dict(name="sea", unit=6, at="大海", r=14, shape=("rect", 0.05, 0.585, 0.95, 0.06), not_near=[(190, 200, 120)]),
        dict(name="hills", unit=5, at="远", r=20, shape=("rect", 0.05, 0.59, 0.95, 0.1)),
        dict(name="sky", unit=5, at="要是", r=46, shape=("rect", 0, 0, 1, 0.61)),
        dict(name="grass", unit=4, at="远远", r=40, shape=("rect", 0, 0.6, 1, 0.4)),
    ],
    "psalm-121": [
        dict(name="child", over=True, unit=7, at="我", r=3, shape=("rect", 0.28, 0.695, 0.035, 0.1)),
        dict(name="birds", over=True, unit=8, at="天地", r=3, shape=("rect", 0.7, 0.165, 0.14, 0.1)),
        dict(name="sun", unit=7, at="举目", r=18, shape=("circle", 0.455, 0.3, 0.085)),
        dict(name="path", unit=7, at="向", r=8, shape=("poly", [[0.16, 1], [0.19, 0.88], [0.24, 0.8], [0.3, 0.77], [0.34, 0.78],
                                                               [0.29, 0.83], [0.26, 0.9], [0.27, 1]])),
        dict(name="mountains", unit=7, at="山", r=26, shape=("rect", 0, 0.34, 1, 0.27)),
        dict(name="grass", unit=8, at="耶和华", r=18, shape=("rect", 0, 0.72, 0.8, 0.16)),
    ],
    "zao-fa-baidi": [
        dict(name="pavilions", unit=1, at="白帝", r=3, shape=("rect", 0.03, 0.045, 0.1, 0.065)),
        dict(name="monkeys", over=True, unit=2, at="猿声", r=3, shape=("or", ("rect", 0.031, 0.536, 0.04, 0.08), ("rect", 0.936, 0.556, 0.052, 0.054))),
        dict(name="boat", over=True, unit=2, at="轻舟", r=4, shape=("rect", 0.655, 0.69, 0.072, 0.1)),
        dict(name="sun", unit=1, at="朝", r=10, shape=("circle", 0.237, 0.183, 0.036)),
        dict(name="cliff", unit=1, at="辞", r=20, shape=("rect", 0, 0.03, 0.235, 0.55)),
        dict(name="clouds", unit=1, at="彩云", r=22, shape=("rect", 0.12, 0, 0.38, 0.34)),
        dict(name="banks", unit=2, at="两岸", r=20, shape=("or", ("rect", 0, 0.5, 0.3, 0.38), ("rect", 0.84, 0.5, 0.16, 0.32))),
        dict(name="mountains", unit=2, at="万重山", r=22, shape=("rect", 0.63, 0.1, 0.37, 0.46)),
        dict(name="river", unit=1, at="千里", r=17, shape=("poly", [[0.21, 0.47], [0.36, 0.49], [0.5, 0.59], [0.62, 0.67], [0.8, 0.75],
                                                                   [1, 0.79], [1, 1], [0.85, 1], [0.7, 0.88], [0.52, 0.77],
                                                                   [0.4, 0.67], [0.28, 0.59], [0.21, 0.56]])),
    ],
    "where-go-the-boats": [
        dict(name="child", over=True, unit=6, at="小朋友", r=4, shape=("rect", 0.115, 0.59, 0.12, 0.14), not_near=[(225, 185, 95)]),
        dict(name="boats", over=True, unit=4, at="小船", r=4, shape=("rect", 0.228, 0.68, 0.115, 0.1), not_near=[(228, 188, 100), (150, 122, 95)]),
        dict(name="mill", over=True, unit=5, at="磨坊", r=5, shape=("rect", 0.775, 0.405, 0.11, 0.095), not_near=[(228, 188, 100), (140, 160, 128)]),
        dict(name="foam", over=True, unit=4, at="泡沫", r=5, shape=("rect", 0.735, 0.475, 0.07, 0.045), not_near=[(228, 188, 100)]),
        dict(name="near river", unit=3, at="河水", r=18,
             shape=("and", ("poly", [[0.54, 0.515], [0.77, 0.49], [0.79, 0.57], [0.73, 0.66], [0.56, 0.77], [0.42, 0.86], [0.26, 1],
                                     [0, 1], [0, 0.82], [0.16, 0.77], [0.32, 0.71], [0.46, 0.66], [0.6, 0.61], [0.62, 0.575],
                                     [0.55, 0.55]]), ("rect", 0, 0.6, 1, 0.4))),
        dict(name="far river", over=True, unit=5, at="河水", r=12,
             shape=("poly", [[0.52, 0.505], [0.78, 0.48], [0.8, 0.575], [0.74, 0.62], [0.6, 0.62], [0.62, 0.575], [0.53, 0.55]])),
        dict(name="hills", unit=5, at="山谷", r=22, shape=("rect", 0, 0.3, 1, 0.16), not_near=[(242, 190, 160), (232, 200, 120)]),
        dict(name="sky", unit=4, at="它们", r=48, shape=("rect", 0, 0, 1, 0.42)),
        dict(name="sand far", unit=3, at="两岸", r=34, shape=("rect", 0, 0.38, 1, 0.24)),
        dict(name="sand near", unit=3, at="沙滩", r=40, shape=("rect", 0, 0.58, 1, 0.42)),
    ],
    "isaiah-40-31": [
        dict(name="child", over=True, unit=7, at="奔跑", r=3, shape=("rect", 0.48, 0.77, 0.05, 0.1)),
        dict(name="man", over=True, unit=7, at="行走", r=3, shape=("rect", 0.53, 0.73, 0.04, 0.125)),
        dict(name="eagle", unit=7, at="鹰", r=7, shape=("rect", 0.46, 0.18, 0.1, 0.16)),
        dict(name="wings", unit=7, at="展翅", r=10, shape=("rect", 0.32, 0.04, 0.41, 0.3)),
        dict(name="sun", unit=7, at="耶和华", r=12, shape=("circle", 0.855, 0.158, 0.07)),
        dict(name="clouds", unit=7, at="得力", r=16, shape=("rect", 0.72, 0.18, 0.27, 0.15)),
        dict(name="path", unit=7, at="不疲乏", r=8, shape=("poly", [[0.29, 1], [0.44, 0.86], [0.52, 0.8], [0.57, 0.755], [0.61, 0.745],
                                                                  [0.6, 0.78], [0.52, 0.86], [0.42, 0.95], [0.39, 1]])),
        dict(name="mountains", unit=7, at="等候", r=24, shape=("rect", 0.04, 0.52, 0.92, 0.22)),
        dict(name="fields", unit=7, at="不困倦", r=24, shape=("rect", 0, 0.7, 1, 0.3)),
    ],
    # 看得见的诗 · 第三期 (lang lesson can-beauty-last, 2026-10-27)
    "chun-ye-xi-yu": [
        dict(name="boat", over=True, unit=3, at="江船", r=4, shape=("rect", 0.6, 0.55, 0.12, 0.1)),   # with its lamp's reflection
        dict(name="blossoms", over=True, unit=4, at="红", r=6, shape=("rect", 0.62, 0.5, 0.38, 0.5), not_near=[(238, 237, 232), (224, 226, 226)]),
        dict(name="city", unit=4, at="锦官城", r=10, shape=("rect", 0.58, 0.35, 0.42, 0.17)),
        dict(name="bank and path", unit=3, at="野径", r=10, shape=("poly", [[0, 0.42], [0.25, 0.42], [0.33, 0.47], [0.2, 0.55],
                                                                          [0.24, 0.62], [0, 0.64]])),
        dict(name="river", unit=2, at="润", r=18, shape=("poly", [[0.12, 0.47], [0.5, 0.46], [1, 0.49], [1, 0.72], [0.75, 0.75],
                                                                 [0.5, 0.72], [0.3, 0.65], [0.15, 0.57]])),
        dict(name="blossom haze", unit=4, at="红", r=6, shape=("rect", 0.62, 0.5, 0.38, 0.5)),   # the soft wash round the branches, below the river
        dict(name="hills", unit=2, at="夜", r=18, shape=("rect", 0, 0.24, 0.62, 0.23)),
        dict(name="clouds left", unit=1, at="好雨", r=20, shape=("rect", 0, 0, 0.45, 0.3)),
        dict(name="clouds right", unit=1, at="发生", r=20, shape=("rect", 0.45, 0, 0.55, 0.3)),
    ],
    "sonnet-18": [
        dict(name="girl", over=True, unit=11, at="诗", r=4, shape=("rect", 0.78, 0.715, 0.12, 0.205), not_near=[(141, 161, 60)]),
        dict(name="wildflowers", over=True, unit=10, at="生长", r=3, not_near=[(141, 161, 60)],
             shape=("or", ("rect", 0.07, 0.82, 0.05, 0.05), ("rect", 0.135, 0.85, 0.06, 0.08), ("rect", 0.37, 0.86, 0.05, 0.05),
                    ("rect", 0.64, 0.88, 0.05, 0.05), ("rect", 0.9, 0.89, 0.05, 0.05), ("rect", 0.94, 0.85, 0.04, 0.05))),
        dict(name="flying petals", over=True, unit=8, at="失去", r=3, shape=("rect", 0.33, 0.38, 0.12, 0.12), not_near=[(110, 180, 247)]),
        dict(name="sun", over=True, unit=7, at="眼睛", r=12, shape=("circle", 0.82, 0.135, 0.08),
             not_near=[(110, 180, 247), (138, 196, 245), (222, 221, 220), (223, 216, 204)]),
        dict(name="right cloud", over=True, unit=7, at="云", r=10, shape=("rect", 0.67, 0.08, 0.33, 0.26), not_near=[(110, 180, 247)]),
        dict(name="left cloud", over=True, unit=7, at="天空", r=10, shape=("rect", 0.16, 0.06, 0.37, 0.22), not_near=[(110, 180, 247)]),
        dict(name="tree", over=True, unit=6, at="风", r=8, not_near=[(110, 180, 247), (138, 196, 245), (105, 138, 70), (101, 136, 82), (129, 154, 82)],
             shape=("or", ("rect", 0, 0.24, 0.36, 0.34), ("poly", [[0, 0.69], [0.065, 0.69], [0.085, 0.6], [0.115, 0.52], [0.07, 0.52], [0.03, 0.6], [0, 0.64]]))),
        dict(name="hills", unit=5, at="温和", r=26, shape=("rect", 0, 0.55, 1, 0.15), not_near=[(110, 180, 247), (138, 196, 245)]),   # the meadow from 0.70, round the girl
        dict(name="meadow", unit=9, at="夏天", r=40, shape=("rect", 0, 0.68, 1, 0.32)),
        dict(name="sky", unit=5, at="夏天", r=46, shape=("rect", 0, 0, 1, 0.65)),
    ],
    "ecclesiastes-3-11": [
        dict(name="grandparent and child", over=True, unit=12, at="世人", r=3, shape=("rect", 0.33, 0.5, 0.09, 0.19)),
        dict(name="birds", over=True, unit=12, at="心", r=3,
             shape=("or", ("rect", 0.6, 0.195, 0.045, 0.06), ("rect", 0.665, 0.265, 0.045, 0.05), ("rect", 0.865, 0.33, 0.045, 0.045))),
        dict(name="buds", over=True, unit=12, at="始", r=4, shape=("rect", 0.02, 0.7, 0.2, 0.28)),
        dict(name="seed heads", over=True, unit=12, at="终", r=4, shape=("rect", 0.76, 0.74, 0.22, 0.24)),
        dict(name="spring", unit=12, at="各", r=10, shape=("rect", 0.06, 0.17, 0.17, 0.38)),
        dict(name="summer", unit=12, at="其", r=10, shape=("rect", 0.23, 0.17, 0.15, 0.48)),
        dict(name="autumn", unit=12, at="时", r=10, shape=("rect", 0.38, 0.17, 0.19, 0.38)),
        dict(name="sun", unit=12, at="美好", r=16, shape=("rect", 0.63, 0, 0.37, 0.36)),
        dict(name="stars", unit=12, at="神", r=20, shape=("rect", 0, 0, 0.34, 0.32)),
        dict(name="hill", unit=12, at="造", r=22, shape=("rect", 0, 0.58, 0.86, 0.42)),
    ],
}

LIVING: dict[str, list[dict]] = {
    "deng-guanque-lou": [
        dict(unit=1, at="sun", brush="sunglow", path=[[0.837, 0.281], [0.837, 0.281]], dur=0.3),
        dict(unit=1, at="River", brush="river", path=[[0.5, 0.74], [0.62, 0.78], [0.76, 0.8], [0.9, 0.82], [0.99, 0.84]], dur=1.4),
        dict(unit=1, at="sea", brush="river", path=[[0.56, 0.84], [0.7, 0.88], [0.84, 0.9], [0.98, 0.92]], dur=1.0),
        dict(unit=2, at="miles", brush="mist", path=[[0.22, 0.63], [0.4, 0.61], [0.6, 0.63], [0.82, 0.61]], dur=1.4),
        dict(unit=2, at="Climb", brush="birds", path=[[0.3, 0.24], [0.4, 0.2], [0.5, 0.22], [0.6, 0.19]], dur=1.2),
    ],
    "foreign-lands": [
        dict(unit=3, at="cherry", brush="petals", path=[[0.03, 0.05], [0.13, 0.09], [0.23, 0.05], [0.32, 0.13]], dur=1.2),
        dict(unit=3, at="climb", brush="sway", path=[[0.07, 0.16], [0.18, 0.12], [0.3, 0.09], [0.33, 0.3], [0.2, 0.38]], dur=1.2),
        dict(unit=4, at="foreign", brush="sparkle", path=[[0.12, 0.612], [0.4, 0.606], [0.68, 0.61], [0.96, 0.605]], dur=1.2),
        dict(unit=5, at="higher", brush="petals", path=[[0.24, 0.32], [0.29, 0.29], [0.34, 0.33]], dur=0.8),
        dict(unit=6, at="river", brush="sparkle", path=[[0.56, 0.665], [0.62, 0.7], [0.5, 0.74], [0.36, 0.765], [0.25, 0.785]], dur=1.2),
        dict(unit=6, at="ships.", brush="boat", path=("tap", 0.912, 0.6)),
    ],
    "psalm-121": [
        dict(unit=7, at="mountains—", brush="mist", path=[[0.04, 0.22], [0.24, 0.19], [0.44, 0.16], [0.6, 0.2]], dur=1.3),
        dict(unit=7, at="help", brush="birds", path=[[0.58, 0.12], [0.7, 0.09], [0.82, 0.12], [0.92, 0.1]], dur=1.0),
        dict(unit=8, at="Lord,", brush="rays", path=[[0.42, 0.31], [0.455, 0.29], [0.49, 0.31]], dur=0.8),
        dict(unit=8, at="earth.", brush="sway", path=[[0.04, 0.79], [0.28, 0.78], [0.52, 0.8], [0.76, 0.79]], dur=1.2),
    ],
    "zao-fa-baidi": [
        dict(unit=1, at="coloured", brush="colorclouds", path=[[0.15, 0.07], [0.27, 0.11], [0.38, 0.15], [0.46, 0.21]], dur=1.2),
        dict(unit=1, at="Jiangling,", brush="river", path=[[0.3, 0.54], [0.44, 0.61], [0.58, 0.69], [0.74, 0.77], [0.9, 0.83], [0.99, 0.88]], dur=1.6),
        dict(unit=2, at="monkeys", brush="monkey", path=("tap", 0.051, 0.566)),
        dict(unit=2, at="call", brush="monkey", path=("tap", 0.954, 0.583)),
        dict(unit=2, at="boat", brush="boat", path=("tap", 0.688, 0.759)),
    ],
    "where-go-the-boats": [
        dict(unit=3, at="river,", brush="river", path=[[0.03, 0.9], [0.18, 0.83], [0.33, 0.77], [0.47, 0.69], [0.6, 0.62]], dur=1.4),
        dict(unit=4, at="leaves", brush="leaves", path=[[0.08, 0.88], [0.22, 0.82], [0.37, 0.75]], dur=1.0),
        dict(unit=4, at="foam,", brush="foam", path=[[0.745, 0.5], [0.775, 0.495], [0.8, 0.5]], dur=0.7),
        dict(unit=4, at="Boats", brush="boat", path=("tap", 0.258, 0.735)),
        dict(unit=4, at="mine", brush="boat", path=("tap", 0.315, 0.752)),
        dict(unit=5, at="river", brush="river", path=[[0.56, 0.6], [0.66, 0.55], [0.74, 0.51]], dur=0.9),
        dict(unit=6, at="river,", brush="leaves", path=[[0.42, 0.72], [0.52, 0.66], [0.62, 0.6]], dur=1.0),
    ],
    "isaiah-40-31": [
        dict(unit=7, at="Lord", brush="sunglow", path=[[0.859, 0.161], [0.859, 0.161]], dur=0.3),
        dict(unit=7, at="strength.", brush="mist", path=[[0.74, 0.26], [0.85, 0.28], [0.97, 0.25]], dur=1.0),
        dict(unit=7, at="eagles;", brush="wind", path=("tap", 0.51, 0.251)),
        dict(unit=7, at="run", brush="sway", path=[[0.03, 0.8], [0.25, 0.77], [0.47, 0.82]], dur=1.0),
        dict(unit=7, at="walk", brush="sway", path=[[0.6, 0.8], [0.8, 0.77], [0.98, 0.82]], dur=1.0),
    ],
    "chun-ye-xi-yu": [
        dict(unit=1, at="rain", brush="springrain", path=[[0.1, 0.12], [0.3, 0.15], [0.5, 0.1], [0.7, 0.14], [0.9, 0.1]], dur=1.6),
        dict(unit=2, at="soaks", brush="river", path=[[0.2, 0.52], [0.4, 0.55], [0.6, 0.58], [0.85, 0.6]], dur=1.4),
        dict(unit=3, at="lamp", brush="lamplight", path=[[0.678, 0.585], [0.678, 0.585]], dur=0.3),
        dict(unit=4, at="flowers", brush="petals", path=[[0.7, 0.62], [0.82, 0.7], [0.92, 0.8]], dur=1.2),
    ],
    "sonnet-18": [
        dict(unit=5, at="summer’s", brush="mist", path=[[0.15, 0.3], [0.35, 0.26], [0.55, 0.3]], dur=1.2),
        dict(unit=6, at="winds", brush="sway", path=[[0.05, 0.3], [0.18, 0.35], [0.3, 0.42]], dur=1.0),
        dict(unit=6, at="buds", brush="petals", path=[[0.1, 0.3], [0.25, 0.33], [0.32, 0.4]], dur=1.0),
        dict(unit=7, at="eye", brush="sunglow", path=[[0.82, 0.135], [0.82, 0.135]], dur=0.3),
        dict(unit=9, at="summer", brush="sway", path=[[0.05, 0.8], [0.35, 0.78], [0.65, 0.82], [0.75, 0.8]], dur=1.2),
    ],
    "ecclesiastes-3-11": [
        dict(unit=12, at="beautiful", brush="rays", path=[[0.81, 0.165], [0.835, 0.15], [0.86, 0.165]], dur=0.6),
        dict(unit=12, at="time.", brush="petals", path=[[0.1, 0.3], [0.25, 0.38], [0.4, 0.42]], dur=1.0),
        dict(unit=12, at="eternity", brush="twinkle", path=[[0.03, 0.05], [0.15, 0.12], [0.28, 0.2]], dur=1.2),
        dict(unit=12, at="heart;", brush="birds", path=[[0.6, 0.22], [0.75, 0.2], [0.9, 0.24]], dur=1.0),
    ],
}


def find_word(words: list[dict], at: str) -> dict:
    """The word an entry starts on: "河水#2" is the second 河水 (case and punctuation don't matter)."""
    bare = lambda s: re.sub(r"[^\w]", "", s).lower()  # noqa: E731
    text, _, nth = at.partition("#")
    hits = [w for w in words if bare(w["text"]) == bare(text) and w["start"] is not None]
    if len(hits) < int(nth or 1):
        raise SystemExit(f"no {at!r} in {' '.join(w['text'] for w in words)}")
    return hits[int(nth or 1) - 1]
