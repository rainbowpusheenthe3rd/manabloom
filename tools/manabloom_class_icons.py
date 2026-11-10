r"""Manabloom's class ladders, drawn the blackberry's way: three stages per class, one object growing or being made.

  uv run --no-project --with numpy --with pillow python tools/manabloom_class_icons.py <out dir>

Writes <out>/class_icons.png: each class's three stages large, and again at the size they sit on a button.

The rules (the author, 10 Nov 2026), taken from the shipped bramble berry (manabloom_motifs.py), whose painter this reuses:
  1. one light: a key light from the top left (gloss and a white point), a cool rim light on the lower right;
  2. every part shaded on its own: each facet, drupelet, cloud lobe or flame layer gets its own light;
  3. layers: something sits behind (sepals, a stone base, a halo, rays);
  4. a dark outline round everything, so it holds on any icon;
  5. structure underneath, grown not placed: positions come from a growth rule (golden angle, a druse from one
     base, alternating knapping scars), never a fixed grid.
And each ladder is one thing growing or being made, so every step visibly becomes the next:
  Druid    bud -> flower -> blackberry                (the shipped motifs)
  Hunter   flint nodule -> knapped arrowhead -> fletched arrow
  Mage     one crystal -> three -> a full druse
  Priest   unlit candle -> lit candle -> candle in a halo
  Warlock  smouldering coal -> fel flame -> fel blaze
  Shaman   a wisp of cloud -> cumulus -> thunderhead with lightning
  Paladin  bronze seal -> gold seal -> radiant seal
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manabloom_motifs as M                                   # noqa: E402  (the berry's painter and grid)
from manabloom_motifs import Paint, disc, rim, soft, xx, yy, GOLDEN, SS, SIZE, N   # noqa: E402

L = np.array([-0.6, -0.8])                                     # light comes from the top left
RIM_COOL = (0.62, 0.70, 0.92)


# ---- primitives -------------------------------------------------------------------------------------------
def poly(pts):
    """Anti-aliased mask of a convex polygon (pixel coordinates on the 64 grid)."""
    s = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))
    sign = 1 if s > 0 else -1
    d = np.full(xx.shape, np.inf)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        ln = math.hypot(x2 - x1, y2 - y1) or 1
        d = np.minimum(d, sign * ((x2 - x1) * (yy - y1) - (y2 - y1) * (xx - x1)) / ln)
    return soft(d)


def seg(x1, y1, x2, y2, w):
    """A capsule: everything within w/2 of the segment."""
    dx, dy = x2 - x1, y2 - y1
    t = np.clip(((xx - x1) * dx + (yy - y1) * dy) / (dx * dx + dy * dy or 1), 0, 1)
    return soft(w / 2 - np.hypot(xx - (x1 + t * dx), yy - (y1 + t * dy)))


def drop(cx, cy, h, r, ang=0.0):
    """A teardrop flame: a disc of radius r at (cx, cy) drawn up to a point h - r away, leaning by ang."""
    ax, ay = math.sin(ang), -math.cos(ang)                     # along the flame
    px, py = math.cos(ang), math.sin(ang)                      # across it
    u = (xx - cx) * ax + (yy - cy) * ay
    w = (xx - cx) * px + (yy - cy) * py
    H = h - r
    hw = r * np.clip(1 - u / H, 0, 1) ** 1.25
    return np.maximum(soft(r - np.hypot(u, w)) * (u <= 0), soft(hw - np.abs(w)) * (u > 0) * (u <= H))


def rot(pts, cx, cy, a):
    c, s = math.cos(a), math.sin(a)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


def lit(n):
    """0 (facing away from the light) .. 1 (facing it), for a direction n."""
    n = np.asarray(n, float)
    n = n / (np.linalg.norm(n) or 1)
    return float(np.clip(0.5 + 0.5 * n @ (L / np.linalg.norm(L)), 0, 1))


def tone(base, k, dark=0.38, bright=1.18):
    return tuple(np.clip(np.asarray(base) * (dark + (bright - dark) * k), 0, 1))


def rimlight(mask, px=1.2, strength=0.75):
    """The cool rim on the lower right of a shape: the shape minus itself nudged up-left."""
    k = max(1, int(px * SS))
    return mask * (1 - np.roll(np.roll(mask, -k, 0), -k, 1)) * strength


def point(p, x, y, r=1.1):
    """The white point of the key light."""
    p.put(disc(x, y, r * 2.2) * 0.5, (1.0, 1.0, 1.0))
    p.put(disc(x, y, r), (1.0, 1.0, 1.0))


def under(p, draw):
    """Draw something behind an already rimmed picture (a glow that shouldn't get an outline)."""
    g = Paint()
    draw(g)
    g.put(p.a, p.rgb)
    return g


# ---- hunter: flint nodule -> knapped arrowhead -> fletched arrow ---------------------------------------------
FLINT, CORTEX = (0.50, 0.54, 0.64), (0.80, 0.76, 0.66)


def arrowhead(p, cx, cy, length, width, ang, scars=4):
    """A knapped point along ang (0 = right, y down). Flake scars alternate along the two edges, as knapping
    leaves them: each scar is its own facet, tilted towards its edge and a little forward, lit on its own."""
    def hw(f):                                                 # half width along the point, widest near the base
        return width * (1 - f) ** 0.85 * min(1.0, (f + 0.12) * 3.2)
    us = np.linspace(0.0, 1.0, scars + 2)
    whole = np.zeros_like(xx)
    for side in (-1, 1):
        shift = 0 if side == 1 else 0.5 / (scars + 1)          # the other edge's scars sit half a step on
        for i in range(len(us) - 1):
            f0, f1 = min(1, us[i] + shift * (i > 0)), min(1, us[i + 1] + shift)
            if f0 >= 1:
                continue
            quad = [(f0 * length, 0), (f0 * length, side * hw(f0)), (f1 * length, side * hw(f1)), (f1 * length, 0)]
            m = poly(rot(quad, cx, cy, ang))
            n = rot([(0.35, side)], 0, 0, ang)[0]
            k = lit(n) + (0.07 if i % 2 else -0.07)            # each scar is a shallow cup: alternate a little
            p.put(m, tone(FLINT, k, dark=0.30, bright=1.35))
            whole = np.maximum(whole, m)
    p.put(rimlight(whole), RIM_COOL)
    tip = rot([(length * 0.72, -width * 0.18)], cx, cy, ang)[0]
    point(p, *tip, r=0.9)
    return whole


def hunter(stage):
    p = Paint()
    if stage == 0:                                             # a nodule: chalky cortex, one flake struck off
        out = [(32 + 17 * math.cos(a) * (1 + 0.10 * math.sin(3 * a)), 34 + 14 * math.sin(a) * (1 + 0.08 * math.cos(2 * a)))
               for a in np.linspace(0, 2 * math.pi, 14, endpoint=False)]
        m = poly(out)
        p.put(m, CORTEX)
        p.put(m * np.clip((xx + yy - 66) / 20, 0, 1) * 0.55, (0.45, 0.42, 0.36))   # shade away from the light
        scar = poly([(26, 26), (38, 24), (41, 33), (33, 39), (25, 35)])           # the one knapped face
        p.put(scar, tone(FLINT, 0.55))
        p.put(scar * poly([(26, 26), (38, 24), (33, 31)]), tone(FLINT, 0.95))
        p.put(rimlight(m, 1.4, 0.5), RIM_COOL)
        point(p, 31, 27, 0.8)
    elif stage == 1:                                           # the point, knapped
        arrowhead(p, 13, 51, 44, 13, -math.pi / 4, scars=5)
    else:                                                      # hafted: shaft, fletching, the same point
        ang = -math.pi / 4
        p.put(seg(10, 54, 38, 26, 3.2), (0.40, 0.27, 0.14))   # the shaft, its lit side a stripe
        p.put(seg(10, 53.2, 38, 25.2, 1.2), (0.78, 0.58, 0.34))
        for side, col in ((-1, (0.93, 0.90, 0.82)), (1, (0.72, 0.28, 0.16))):    # two vanes, cream and red
            vane = rot([(0, 0), (11, 0), (8, side * 6.5), (-2, side * 6.5)], 9.5, 54.5, ang)
            vane = [(x + 3 * math.cos(ang), y + 3 * math.sin(ang)) for x, y in vane]
            m = poly(vane)
            p.put(m, tone(col, lit(rot([(0, side)], 0, 0, ang)[0])))
            p.put(rimlight(m, 1.0, 0.4), RIM_COOL)
        arrowhead(p, 34, 30, 22, 7.5, ang, scars=3)
    return rim(p)


# ---- mage: one crystal -> three -> a druse ---------------------------------------------------------------------
ICE = (0.58, 0.82, 1.0)


def crystal(p, bx, by, h, w, tilt):
    """A hexagonal prism seen side on, three faces and a pointed top, each facet lit by its own direction."""
    t = w * 1.25
    faces = [  # (polygon in local coords, base y up = negative), its facing
        ([(-w, 0), (-w, -(h - t)), (-w / 3, -(h - t)), (-w / 3, 0)], (-1, 0)),
        ([(-w / 3, 0), (-w / 3, -(h - t)), (w / 3, -(h - t)), (w / 3, 0)], (0, -0.15)),
        ([(w / 3, 0), (w / 3, -(h - t)), (w, -(h - t)), (w, 0)], (1, 0)),
        ([(-w, -(h - t)), (-w / 3, -(h - t)), (0, -h)], (-0.8, -0.9)),
        ([(-w / 3, -(h - t)), (w / 3, -(h - t)), (0, -h)], (0, -1)),
        ([(w / 3, -(h - t)), (w, -(h - t)), (0, -h)], (0.8, -0.9)),
    ]
    whole = np.zeros_like(xx)
    for pts, n in faces:
        m = poly(rot(pts, bx, by, tilt))
        p.put(m, tone(ICE, lit(rot([n], 0, 0, tilt)[0]), dark=0.30, bright=1.05))
        whole = np.maximum(whole, m)
    p.put(rimlight(whole, 1.0, 0.6), (0.85, 0.95, 1.0))
    return whole


def mage(stage):
    p = Paint()
    p.put(poly([(20, 52), (26, 47), (40, 47), (46, 52), (38, 56), (26, 56)]), (0.26, 0.22, 0.28))   # the rock
    # a druse grows from one base: the tallest in the middle, the rest leaning out in turn, each a little shorter
    n = (1, 3, 5)[stage]
    H = (24, 32, 38)[stage]
    order = sorted(range(n), key=lambda k: -k)                  # draw the outer, shorter ones first: they're behind
    for k in order:
        lean = 0 if k == 0 else (1 if k % 2 else -1) * (0.38 + 0.22 * ((k + 1) // 2 - 1))
        h = H * 0.80 ** ((k + 1) // 2)
        w = (5.5 if k == 0 else 4.2) * (0.92 ** ((k + 1) // 2))
        crystal(p, 33 + 4.5 * math.sin(lean), 51, h, w, lean)
    if stage == 2:                                              # a frost sparkle on the tallest
        for a in range(4):
            ang = a * math.pi / 2
            p.put(seg(26, 18, 26 + 4.5 * math.cos(ang), 18 + 4.5 * math.sin(ang), 1.0), (1, 1, 1))
    point(p, 31, 51 - H + 9, 0.8)
    return rim(p)


# ---- priest: unlit candle -> lit -> in a halo ------------------------------------------------------------------
WAX, GOLD = (0.90, 0.85, 0.74), (1.0, 0.80, 0.32)


def flame(p, cx, cy, h, cols, ang=0.0):
    """Layered: outer, middle, core, each a smaller teardrop on the same base."""
    for (f, col) in zip((1.0, 0.74, 0.46), cols):
        p.put(drop(cx, cy - h * (1 - f) * 0.15, h * f, h * 0.30 * f, ang), col)


def priest(stage):
    p = Paint()
    if stage == 2:                                              # the halo sits behind: lit top left, gold
        r, w = 13, 2.6                                          # kept 2 px off the edge: rim() rolls the image
        d = np.hypot(xx - 32, yy - 23)
        ring = soft(w / 2 - np.abs(d - r))
        k = np.clip(0.5 + 0.5 * ((xx - 32) * L[0] + (yy - 23) * L[1]) / np.maximum(d, 1e-6) / np.linalg.norm(L), 0, 1)
        col = np.asarray(GOLD)[None, None, :] * (0.45 + 0.7 * k[..., None])
        p.put(ring, np.clip(col, 0, 1))
        for a in range(12):                                     # short rays, alternating long and short
            ang = a * math.pi / 6
            ln = 3.5 if a % 2 else 2.0
            x0, y0 = 32 + (r + 2.5) * math.cos(ang), 23 + (r + 2.5) * math.sin(ang)
            p.put(seg(x0, y0, x0 + ln * math.cos(ang), y0 + ln * math.sin(ang), 1.3), tone(GOLD, lit((math.cos(ang), math.sin(ang)))))
    # the candle: three faces of a pillar, a lighter top, a drip on the lit side
    for x0, x1, n in ((25, 29, (-1, 0)), (29, 35, (0, -0.2)), (35, 39, (1, 0))):
        p.put(poly([(x0, 32), (x1, 32), (x1, 57), (x0, 57)]), tone(WAX, lit(n), dark=0.55, bright=1.05))
    top = soft(1 - np.hypot((xx - 32) / 7, (yy - 32) / 2.2))
    p.put(top, (0.97, 0.94, 0.86))
    p.put(seg(27, 32, 27, 40, 2.4), (0.98, 0.96, 0.90))         # a drip
    p.put(seg(32, 32, 32, 27.5, 1.1), (0.15, 0.12, 0.10))       # the wick
    body = poly([(25, 30), (39, 30), (39, 57), (25, 57)])
    p.put(rimlight(body, 1.0, 0.5), RIM_COOL)
    point(p, 27, 45, 0.8)
    if stage >= 1:
        flame(p, 32, 25, (12, 15)[stage - 1], [(1.0, 0.52, 0.12), (1.0, 0.80, 0.28), (1.0, 0.98, 0.88)])
    out = rim(p)
    if stage >= 1:                                              # a soft glow behind it all, no outline
        out = under(out, lambda g: g.put(disc(32, 22, 13) * 0.22 * np.clip(1 - np.hypot(xx - 32, yy - 22) / 13, 0, 1), GOLD))
    return out


# ---- warlock: smouldering coal -> fel flame -> fel blaze -------------------------------------------------------
COAL, FEL = (0.24, 0.16, 0.24), [(0.08, 0.38, 0.06), (0.40, 0.90, 0.16), (0.90, 1.0, 0.70)]


def warlock(stage):
    p = Paint()
    if stage >= 1:                                              # the flame rises behind the coal's front
        if stage == 2:
            flame(p, 24, 50, 24, FEL, ang=-0.50)
            flame(p, 40, 50, 26, FEL, ang=0.45)
        flame(p, 32, 48, (28, 42)[stage - 1], FEL)
    out = [(32 + 13 * math.cos(a) * (1 + 0.12 * math.sin(2 * a + 1)), 50 + 7 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9, endpoint=False)]
    for a, b in zip(out, out[1:] + out[:1]):                     # the coal's facets, each lit on its own
        n = ((a[0] + b[0]) / 2 - 32, (a[1] + b[1]) / 2 - 50 - 3)
        p.put(poly([(32, 47), a, b]), tone(COAL, lit(n), dark=0.5, bright=1.5))
    coal = poly(out)
    glow = (0.30, 0.55, 0.16) if stage == 0 else FEL[1]
    for (x0, y0, x1, y1) in ((32, 50, 24, 47), (32, 50, 40, 46), (32, 50, 30, 55), (24, 47, 21, 50), (40, 46, 43, 51)):
        p.put(seg(x0, y0, x1, y1, 0.9) * coal, glow)            # cracks glowing through
    p.put(rimlight(coal, 1.0, 0.5), RIM_COOL)
    point(p, 26, 46, 0.7)
    return rim(p)


# ---- shaman: wisp -> cumulus -> thunderhead -----------------------------------------------------------------------
def shaman(stage):
    p = Paint()
    if stage == 0:
        lobes = [(28, 40, 6.0), (36, 38, 7.5), (42, 41, 4.5)]
        body, base_y = (0.88, 0.90, 0.95), 46
    else:
        # a cumulus grows upwards from a flat base: lobes on the golden angle, each higher one a little smaller
        n, r0 = (7, 12)[stage - 1], (9.5, 10.5)[stage - 1]
        base_y = (46, 40)[stage - 1]
        lobes = [(32 + (11 - k * 0.6) * math.cos(k * GOLDEN), base_y - 3 - k * (2.6 if stage == 1 else 2.5),
                  r0 * 0.90 ** k) for k in range(n)]
        lobes += [(20, base_y - 2, r0 * 0.75), (44, base_y - 2, r0 * 0.75)]
        body = (0.88, 0.90, 0.95) if stage == 1 else (0.50, 0.53, 0.64)
    whole = np.zeros_like(xx)
    for x, y, r in sorted(lobes, key=lambda l: l[1]):            # top first, so lower lobes sit in front
        m = disc(x, y, r)
        p.put(m, body)
        p.put(m * (1 - disc(x + r * 0.28, y + r * 0.28, r)), tuple(min(1, c * 1.15 + 0.1) for c in body))   # lit cap
        whole = np.maximum(whole, m)
    flat = whole * (yy <= base_y + 1)                            # a cumulus has a flat, shaded base
    p.a, p.rgb = p.a * (yy <= base_y + 1) + 0, p.rgb
    under_c = tuple(c * 0.62 for c in body)
    p.put(flat * np.clip((yy - (base_y - 7)) / 7, 0, 1) * 0.75, under_c)
    p.put(rimlight(flat, 1.2, 0.45), RIM_COOL)
    top = min(lobes, key=lambda l: l[1] - l[2])
    point(p, top[0] - top[2] * 0.35, top[1] - top[2] * 0.35, 0.8)
    if stage == 2:                                               # lightning from its base
        bolt = [(35, base_y + 1, 29, base_y + 9), (29, base_y + 9, 35, base_y + 9), (35, base_y + 9, 28, base_y + 19)]
        for x0, y0, x1, y1 in bolt:
            p.put(seg(x0, y0, x1, y1, 2.6), (0.98, 0.94, 0.55))
            p.put(seg(x0, y0, x1, y1, 1.0), (1, 1, 1))
    return rim(p)


# ---- paladin: bronze seal -> gold -> radiant -----------------------------------------------------------------------
BRONZE = (0.62, 0.44, 0.24)


def seal(p, base, r=15):
    d = np.hypot(xx - 32, yy - 32)
    dirk = np.clip(0.5 + 0.5 * ((xx - 32) * L[0] + (yy - 32) * L[1]) / np.maximum(d, 1e-6) / np.linalg.norm(L), 0, 1)
    p.put(disc(32, 32, r), tone(base, 0.30))
    bevel = disc(32, 32, r) * (1 - disc(32, 32, r - 3))          # the raised rim, lit where it faces the light
    p.put(bevel, np.clip(np.asarray(base)[None, None, :] * (0.45 + 0.75 * dirk[..., None]), 0, 1))
    inner = disc(32, 32, r - 3)                                  # the dished face: lit on the far side
    p.put(inner * (1 - dirk) * 0.35, tuple(min(1, c * 1.25) for c in base))
    for (x0, y0, x1, y1), (lit_half, dark_half) in (
            ((28, 21, 36, 43), ((28, 32), (36, 32))),           # the cross, its arms bevelled
            ((21, 28, 43, 36), ((32, 28), (32, 36)))):
        vertical = x1 - x0 < y1 - y0
        if vertical:
            a = [(x0, y0), (32, y0 + 2), (32, y1 - 2), (x0, y1)]
            b = [(32, y0 + 2), (x1, y0), (x1, y1), (32, y1 - 2)]
            na, nb = (-1, 0), (1, 0)
        else:
            a = [(x0, y0), (x1, y0), (x1 - 2, 32), (x0 + 2, 32)]
            b = [(x0 + 2, 32), (x1 - 2, 32), (x1, y1), (x0, y1)]
            na, nb = (0, -1), (0, 1)
        p.put(poly(a), tone(base, lit(na), dark=0.80, bright=1.20))
        p.put(poly(b), tone(base, lit(nb), dark=0.80, bright=1.20))
    p.put(rimlight(disc(32, 32, r), 1.2, 0.55), RIM_COOL)


def paladin(stage):
    p = Paint()
    if stage == 2:                                               # rays behind: sixteen, long and short in turn
        for a in range(16):
            ang = a * math.pi / 8 + math.pi / 16
            ln = 30 if a % 2 == 0 else 24
            tri = [(32 + 12 * math.cos(ang - 0.10), 32 + 12 * math.sin(ang - 0.10)),
                   (32 + ln * math.cos(ang), 32 + ln * math.sin(ang)),
                   (32 + 12 * math.cos(ang + 0.10), 32 + 12 * math.sin(ang + 0.10))]
            p.put(poly(tri), tone((1.0, 0.86, 0.45), lit((math.cos(ang), math.sin(ang))), dark=0.6, bright=1.1))
    seal(p, BRONZE if stage == 0 else (0.98, 0.78, 0.30))
    point(p, 26, 25, 0.9 if stage else 0.6)
    return rim(p)


# ---- druid: the shipped bramble -----------------------------------------------------------------------------------
def druid(stage):
    return (M.bud, M.flower, M.berry)[stage]()


CLASSES = {"Druid": druid, "Hunter": hunter, "Mage": mage, "Priest": priest, "Warlock": warlock,
           "Shaman": shaman, "Paladin": paladin}
LADDER = {"Druid": "bud, flower, blackberry", "Hunter": "flint nodule, knapped point, fletched arrow",
          "Mage": "one crystal, three, a druse", "Priest": "unlit candle, lit, in a halo",
          "Warlock": "smouldering coal, fel flame, fel blaze", "Shaman": "wisp, cumulus, thunderhead",
          "Paladin": "bronze seal, gold seal, radiant seal"}


def image(p):
    """The supersampled paint, averaged down to SIZE with its colour un-premultiplied."""
    a = p.a.reshape(SIZE, SS, SIZE, SS).mean(axis=(1, 3))
    num = (p.rgb * p.a[..., None]).reshape(SIZE, SS, SIZE, SS, 3).mean(axis=(1, 3))
    rgb = num / np.maximum(a[..., None], 1e-4)
    return Image.fromarray((np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)[..., None]]) * 255).round().astype("uint8"),
                           "RGBA")


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        bold, small = ImageFont.truetype("segoeuib.ttf", 18), ImageFont.truetype("segoeui.ttf", 13)
    except OSError:
        bold = small = ImageFont.load_default()
    big, tiny, BG = 128, 18, (52, 44, 38)
    rowh = big + 24
    sheet = Image.new("RGB", (250 + 3 * (big + 16) + 40 + 3 * (tiny + 30), 20 + len(CLASSES) * rowh), BG)
    d = ImageDraw.Draw(sheet)
    icon_btn = Image.new("RGBA", (40, 40), (70, 95, 60, 255))   # a stand-in action button
    for r, (cls, draw) in enumerate(CLASSES.items()):
        y = 20 + r * rowh
        d.text((16, y + big // 2 - 18), cls, fill=(240, 236, 228), font=bold)
        d.text((16, y + big // 2 + 6), LADDER[cls], fill=(200, 194, 186), font=small)
        for k in range(3):
            im = image(draw(k))
            sheet.paste(im.resize((big, big), Image.LANCZOS), (250 + k * (big + 16), y), im.resize((big, big), Image.LANCZOS))
            btn = icon_btn.copy()                                 # at its real size, on the top edge of a button
            btn.alpha_composite(im.resize((tiny, tiny), Image.LANCZOS), ((40 - tiny) // 2, 0))
            sheet.paste(btn, (250 + 3 * (big + 16) + 40 + k * (tiny + 30), y + big // 2 - 20))
    sheet.save(out / "class_icons.png")
    print(out / "class_icons.png")


if __name__ == "__main__":
    main(sys.argv[1])
