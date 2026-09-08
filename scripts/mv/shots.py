"""The Rejoice shot list: one row per shot, in song order.

Cut points are derived from the measured lyric times, not typed in. A shot that
carries a line names that line as its `anchor`, and its start is placed so the
crossfade **finishes before the line arrives**:

    start = line.t - dissolve - LEAD
    previous shot's end = start + dissolve

Hand-typed timings drifted against the lyrics by about a second in both
directions once the dissolves got longer, because a cut placed 0.6s ahead of a
line is still dissolving when the word lands. Deriving the start from the line
and the dissolve keeps that fixed no matter how long the transition is.

Every shot is rendered to its own file at exactly its screen length, which is what
keeps the no-loop rule true by construction: a clip can never be asked to repeat
because it is never shorter than the time it has to fill. Where a source is shorter
than its span the shot is slowed -- forward only, never boomeranged.
"""
import json, pathlib

OVERLAP = 1.4          # default dissolve, long enough to read as a dissolve
LEAD = 0.15            # picture settled this long before the word
W, H, FPS = 1920, 1080, 30
SONG_END = 312.00      # a few seconds past the song, held silent on the last shot

_song = json.loads((pathlib.Path(__file__).resolve().parents[2] /
                    'src/songs/rejoice.json').read_text())
LINES = _song['lines']

# treatment keys:
#   fog=N     veiling fog, 0..1 strength
#   still     source is an image; movement is the camera only
#   exposure  eq brightness offset, for sources that fight the global grade
#   lightRamp graded shadow -> golden light across the shot (see FootageLayer)
#   blurRamp  (from%, to%) defocus easing off across the shot
#   srcEnd    cap the source window, to force a slowdown
#   dissolve  override the crossfade length for this shot's own dissolve
#   fadeIn    (opacity, seconds) opacity ramp at the head
#   fadeOut   seconds of opacity ramp to nothing at the tail
#   edgeSoften blur sigma for the frame's border, to hide de-watermarking
#   segments  [(src_from, src_to, screen_seconds)] -- different rates in one shot
#   holdLast  seconds the clip finishes early; the last frame fills the rest
#   tailZoom  (seconds, to) camera pulls back over the tail so it is not a freeze
#   anchor    line index this shot must be established for
#   start     explicit start, for shots that carry no line
SPEC = [
    # --- Intro, one designed sequence with its own rhythm (its beats are set by
    # --- hand, not by the lyrics): nebula -> cosmos -> Earth -> Israel -> Golgotha
    # --- -> the nail -> the cross, landing at 52.07 where the first pre-chorus
    # --- line needs the face. Short 0.7s dissolves throughout.
    # --- Intro: the nebula gives way to the neutron-star merger, and the merger
    # --- to deep space. Long opacity cross-fades rather than cuts.
    # --- Intro. The nebula gives way to the neutron-star merger over an 8.5s
    # --- opacity cross-fade, and the merger holds long enough to carry
    # --- "We could not understand" before Golgotha arrives.
    ("I1", "user-space-carina-nebula.jpg",              0.0, {"still": 1, "zoom": (1.00, 1.44), "fadeIn": (0.10, 5.5), "fadeOut": 4.5, "start": 0.00}),
    # NASA SVS 12740, public domain. Two rates inside one file: the spiral-in runs
    # at 1.383x so the merger flash (measured at source 13.52s, not the 13.61s a
    # coarser sampling suggested) lands at 22.35s on screen,
    # exactly where it sits now and where the title meets it; everything after the
    # flash runs at 2.47x, a much slower push through the dark and the bloom. The
# source is only used to 20.00s: past that the kilonova is already dimming.
    ("I2", "nasa-svs12740-ns-merger-1080p.mp4",         0.0, {"start": 16.50, "dissolve": 4.5,
                                                              "segments": [(9.85, 13.60, 5.63),
                                                                           (13.60, 20.00, 15.78)]}),
    ("I5", "gen-golgotha-aerial-v1.png",                0.0, {"still": 1, "zoom": (1.02, 1.15), "anchor": 3}),
    ("S03", "gen-biblical-nail-v1.png",                 0.0, {"still": 1, "zoom": (1.03, 1.13), "anchor": 4}),
    ("S05", "gen-mossy-cross-v2.png",                   0.0, {"still": 1, "zoom": (1.22, 1.02), "anchor": 5}),
    ("S07", "pexels-6491260-womans-face.mp4",          13.4, {"reverse": 1, "srcEnd": 20.6, "blurRamp": (75, 50), "anchor": 6}),
    ("S11", "user-jesus-silhouette-fog.mp4",            0.0, {"fog": 0.30, "anchor": 9}),
    ("S13", "user-bubbles-chorus-2.mp4",                0.0, {"fadeIn": (0.10, 3.0), "anchor": 14}),
    # The clip plays at its own pace and finishes 3.3s before the slot does. That
    # tail is not a freeze: the last frame stays while the camera keeps pulling
    # back at the same rate the push-in used (0.0084 of scale per second), so
    # the movement never changes pace, it only changes direction.
    ("S15", "minimax-kintsugi-repair-slow.mp4",         0.0, {"blurRamp": (68, 12), "holdLast": 3.3,
                                                              "tailZoom": (3.3, 1.171), "anchor": 16}),
    # Holds the whole second pre-chorus now that the cloud shot after it is gone.
    # Capped at 14.5s of source because the clip goes soft past 15s.
    ("S16", "pexels-6491260-womans-face.mp4",           0.0, {"blurRamp": (50, 25), "srcEnd": 14.5, "anchor": 20}),
    # One steady rate across the whole clip. A normal-speed second in the middle
    # read as a stutter next to the slowed halves, so the surge is gone and the
    # source plays end to end at 3.63x -- fit exactly, so the final frame (arms
    # open) is reached rather than trimmed off.
    ("S19", "minimax-coming-earth-to-glory-no-watermark.mp4", 0.0, {"fit": 1, "anchor": 23}),
    ("S21", "user-bubbles-chorus-1.mp4",                0.0, {"fadeIn": (0.10, 3.0), "anchor": 28}),
    ("S23", "pexels-6188046-blooming-flower.mp4",       0.0, {"anchor": 30}),
    ("S24", "pexels-27303243-milky-way.mp4",            0.0, {"anchor": 34}),
    ("S25", "pexels-6979565-three-crosses.mp4",         0.0, {"dissolve": 7.0, "anchor": 36}),
    ("S26", "pexels-11342250-sunset-clouds.mp4",        7.0, {"start": 235.50}),
    # Chorus 3 on a still: fades up over 1.4s and pushes slowly in for 22s.
        # The full 2944x1248 frame, so filling 16:9 crops the sides rather than the
    # figure. Its border is softened because the watermark removal is visible there.
    ("S27", "coming-no-watermark-full.mp4",             0.0, {"fadeIn": (0.10, 3.5), "edgeSoften": 26, "anchor": 38}),
    ("S29", "pexels-11342250-sunset-clouds.mp4",       25.0, {"anchor": 43}),
    ("S30", "wan-world-golden-light-slow.mp4",          5.5, {"lightRamp": 1, "anchor": 45}),
]


def _resolve(spec):
    """Turn anchors into starts, then give each shot the next one's fade-in room."""
    rows = []
    for sid, src, si, tr in spec:
        d = tr.get("dissolve", OVERLAP)
        start = tr["start"] if "start" in tr else round(LINES[tr["anchor"]]['t'] - d - LEAD, 2)
        rows.append([sid, src, si, start, None, tr.get("move", "in"), tr])
    for i, r in enumerate(rows):
        if i + 1 < len(rows):
            nxt = rows[i + 1]
            r[4] = round(nxt[3] + nxt[6].get("dissolve", OVERLAP), 2)
        else:
            r[4] = SONG_END
    return [tuple(r) for r in rows]


SHOTS = _resolve(SPEC)

COVERS = {
    "I1": "intro: the nebula, fading up by opacity and away again",
    "I2": "the merger; also carries 'We could not understand'",
    "I5": "'Your love, and yet we see' -- Golgotha",
    "S03": "'We could not understand' / 'and yet we see' -- the nail",
    "S05": "'We know, and still know in part' -- the cross",
    "S07": "pre-chorus 1, reversed so the face pulls into focus",
    "S11": "'Rejoice, the Lord is near' (chorus 1)",
    "S13": "chorus 1 tail into the first instrumental",
    "S15": "verse 2: broken pieces -> kintsugi, blurred then clearing",
    "S16": "the whole second pre-chorus on the face, defocus 50->25%",
    "S19": "chorus 2 -- earth into glory, one steady 3.63x slow",
    "S21": "chorus 2 tail into the long instrumental",
    "S23": "verse 3: knowing more than yesterday",
    "S24": "bridge: how wide, how long -- the galaxy",
    "S25": "bridge: your love will never end",
    "S26": "instrumental approach to the last chorus",
    "S27": "chorus 3: the luminous figure above the clouds",
    "S29": "the ending revisits the cloud sea",
    "S30": "the ending arrives back in the light",
}
