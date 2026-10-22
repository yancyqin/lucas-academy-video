"""SVG paths for the film's maps, from Natural Earth via world-atlas (countries-50m TopoJSON, public domain data).

  python3 scripts/news-education-01/maps.py <countries-50m.json>   -> public/news-education-01/maps/maps.json

Each map is a 1920x1080 frame in an equirectangular projection scaled by cos(mid-latitude): `land` is every country
in view, `focus` the ones the narration names (ISO numeric ids), `dots` the places it names.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "public/news-education-01/maps/maps.json"
topo = json.load(open(sys.argv[1]))
sx, sy = topo["transform"]["scale"]
tx, ty = topo["transform"]["translate"]
arcs = []
for arc in topo["arcs"]:
    x = y = 0
    pts = []
    for dx, dy in arc:
        x += dx; y += dy
        pts.append((x * sx + tx, y * sy + ty))
    arcs.append(pts)


def ring(idx):
    pts = []
    for i in idx:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]
        pts.extend(a if not pts else a[1:])
    return pts


def polys(geom):
    if geom["type"] == "Polygon":
        return [[ring(r) for r in geom["arcs"]]]
    if geom["type"] == "MultiPolygon":
        return [[ring(r) for r in p] for p in geom["arcs"]]
    return []


countries = {g.get("id"): g for g in topo["objects"]["countries"]["geometries"]}


def frame(lon0, lon1, lat0, lat1, W=1920, H=1080, pad=0.06):
    k = math.cos(math.radians((lat0 + lat1) / 2))
    w, h = (lon1 - lon0) * k, (lat1 - lat0)
    s = min(W * (1 - 2 * pad) / w, H * (1 - 2 * pad) / h)
    ox = (W - w * s) / 2 - lon0 * k * s
    oy = (H - h * s) / 2 + lat1 * s
    return lambda lon, lat: (round(ox + lon * k * s, 1), round(oy - lat * s, 1))


def path(geom, P, box):
    lon0, lon1, lat0, lat1 = box
    d = []
    for poly in polys(geom):
        for r in poly:
            if not any(lon0 - 25 <= x <= lon1 + 25 and lat0 - 25 <= y <= lat1 + 25 for x, y in r):
                continue
            pts = [P(x, y) for x, y in r]
            d.append("M" + "L".join(f"{x},{y}" for x, y in pts) + "Z")
    return "".join(d)


MAPS = {
    # France: Paris and Créteil; the whole country lights up as the blockades spread
    "france": {"box": (-6.0, 10.5, 41.0, 51.6), "focus": ["250"], "dots": {"creteil": (2.455, 48.79), "paris": (2.35, 48.86), "lyon": (4.83, 45.76), "marseille": (5.37, 43.30), "lille": (3.06, 50.63), "nantes": (-1.55, 47.22), "bordeaux": (-0.58, 44.84), "toulouse": (1.44, 43.60), "strasbourg": (7.75, 48.58)}},
    # South and Southeast Asia: Bangladesh, Nepal, Indonesia, the Philippines, India
    "asia": {"box": (66.0, 142.0, -11.5, 36.0), "focus": ["050", "524", "360", "608", "356"], "dots": {"dhaka": (90.41, 23.81), "kathmandu": (85.32, 27.72), "jakarta": (106.85, -6.21), "manila": (120.98, 14.60), "delhi": (77.21, 28.61)}},
    "madagascar": {"box": (25.0, 65.0, -30.0, -5.0), "focus": ["450"], "dots": {"antananarivo": (47.52, -18.88)}},
}
out = {}
for name, m in MAPS.items():
    box = m["box"]
    P = frame(*box)
    land = "".join(path(g, P, box) for cid, g in countries.items() if cid not in m["focus"])
    focus = {cid: path(countries[cid], P, box) for cid in m["focus"]}
    out[name] = {"land": land, "focus": focus, "dots": {k: P(*v) for k, v in m["dots"].items()}}
    print(name, len(land), {k: len(v) for k, v in focus.items()})
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out))
