r"""Draw Manabloom's bramble wreath at its four stages: bramble_{seed,bud,flower,berry}.tga.

  python tools/manabloom_bramble.py

The shared bramble on the bars: efficient casts ripen it (seed -> bud -> flower -> berry), poor ones send it
back. Drawn flat and fine, in the spring wreath's style, from the bramble's own flower genes in Albia's flower
system (its bramble.toml and flower3d.py):
  * five petals (C), radial symmetry, an open cup (no tube), petal shape 0.7 (broad, rounded: obovate);
  * many stamens in a ring (C: a Rosaceae flower);
  * five sepals: closed round the bud, folded back (so out of sight from above) behind the open flower, and
    showing behind the fruit;
  * the berry an aggregate of drupelets on a domed receptacle (C: up to 50-100 carpels per flower, each able to
    become a drupelet, newworldencyclopedia.org/entry/Blackberry); 13 drawn, big enough to read at bar size, set
    on the golden angle (H: no source
    found for how blackberry drupelets are arranged);
  * the seed one pip (pyrene), with its pitted surface, just sprouting its two seed leaves;
  * one motif per wreath, at its top centre, over the season's wreath (cane() is kept for a whole-wreath look).
White and greys, so the addon tints it by efficiency. Uses manabloom_textures' canvas and TGA writer.
"""
import math

import numpy as np

from manabloom_textures import C, EDGE, N, OUT, SS, Canvas, disc, finish, leaf, line, perimeter, tga, xx, yy

GOLDEN = math.pi * (3 - math.sqrt(5))  # 137.5 degrees
SHAPE = 0.7                            # bramble's petal shape gene


def petal(cv, cx, cy, ang, length, tone=0.97):
    """An obovate petal from the flower's centre: narrow at the base, broadest near the tip, rounded off."""
    dx, dy = xx - cx, yy - cy
    u = (dx * math.cos(ang) + dy * math.sin(ang)) / length
    v = -dx * math.sin(ang) + dy * math.cos(ang)
    w = length * (0.25 + 0.3 * SHAPE) * np.clip(u, 0, 1) ** 0.55 * np.sqrt(np.clip(1 - np.clip(u, 0, 1) ** 5, 0, 1))
    inside = (u >= 0) & (u <= 1) & (np.abs(v) < w)
    a = np.clip((w - np.abs(v)) * SS / 1.2, 0, 1) * inside
    shade = tone * (0.86 + 0.14 * u) - 0.10 * (np.abs(v) < 0.35)  # a faint midline, lighter to the rim
    cv.put(a, shade)


def sepal(cv, cx, cy, ang, length, tone=0.55):
    dx, dy = xx - cx, yy - cy
    u = (dx * math.cos(ang) + dy * math.sin(ang)) / length
    v = -dx * math.sin(ang) + dy * math.cos(ang)
    w = length * 0.22 * np.clip(1 - np.clip(u, 0, 1), 0, 1) ** 0.8 * (u > 0)
    a = np.clip((w - np.abs(v)) * SS / 1.2, 0, 1) * (u <= 1)
    cv.put(a, np.full((N, N), tone))


def flower(cv, cx, cy, r, rot):
    # seen from above the sepals are folded back out of sight: drawn, they read as five more petals
    for k in range(5):
        petal(cv, cx, cy, rot + k * 2 * math.pi / 5, r)
    disc(cv, cx, cy, r * 0.42, 0.62)                       # the stamens' ring, darker than the petals
    disc(cv, cx, cy, r * 0.24, 0.85)                       # the carpels in the middle
    for k in range(14):                                    # many stamens: their tips
        a = rot + k * 2 * math.pi / 14
        disc(cv, cx + r * 0.36 * math.cos(a), cy + r * 0.36 * math.sin(a), 0.6, 0.95)


def bud(cv, cx, cy, r, rot):
    for k in range(5):                                     # sepals closed round it: a five-pointed star
        a = rot + k * 2 * math.pi / 5
        sepal(cv, cx, cy, a, r, 0.5)
    disc(cv, cx, cy, r * 0.40, 1.0)                         # the pale petal tip showing between them


def berry(cv, cx, cy, r, rot):
    for k in range(5):                                     # sepals folded back, tips just showing
        sepal(cv, cx, cy, rot + (k + 0.5) * 2 * math.pi / 5, r * 1.15, 0.5)
    disc(cv, cx, cy, r * 0.92, 0.18)                       # the dark gaps between drupelets
    n = 13
    for i in range(n):                                     # drupelets on the dome, outside in
        j = n - 1 - i
        d = r * 0.66 * math.sqrt((j + 0.5) / n)
        a = rot + j * GOLDEN
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        size = r * 0.27
        disc(cv, x, y, size, 0.42 + 0.12 * (1 - d / r))      # dark, like the ripe fruit
        disc(cv, x - size * 0.32, y - size * 0.32, size * 0.32, 1.0)  # each drupelet's glint


def seed(cv, cx, cy, r, rot):
    ca, sa = math.cos(rot), math.sin(rot)
    u = ((xx - cx) * ca + (yy - cy) * sa) / (r * 0.62)
    v = (-(xx - cx) * sa + (yy - cy) * ca) / (r * 0.44)
    d = np.hypot(u, v)
    pits = 0.08 * ((np.sin(xx * 4.1) * np.sin(yy * 4.1)) > 0.3)  # the pitted coat
    cv.put(np.clip((1 - d) * r * 0.44 * SS / 1.2, 0, 1), 0.48 - 0.12 * np.clip(v, -1, 1) ** 2 - pits)
    disc(cv, cx - r * 0.12, cy - r * 0.10, r * 0.10, 0.95)   # a glint, so it reads as a seed, not a hole
    for side in (-1, 1):                                      # just sprouting: two seed leaves, a V away from the pip
        leaf(cv, cx + ca * r * 0.25, cy + sa * r * 0.25, rot + side * 0.55, r * 0.75, r * 0.22, tone=0.9)


def cane(cv):
    """A fine arching cane round the button, with small hooked prickles along it."""
    pts = [perimeter(i / 320) for i in range(321)]
    for i, ((x0, y0, n0), (x1, y1, n1)) in enumerate(zip(pts, pts[1:])):
        wob = 1.6 * math.sin(i / 320 * 2 * math.pi * 4)        # four gentle arches, one per side
        line(cv, x0 + n0[0] * (3 + wob), y0 + n0[1] * (3 + wob), x1 + n1[0] * (3 + wob), y1 + n1[1] * (3 + wob), 0.8, 0.62)
    for i in range(24):                                         # prickles: short, hooked back along the cane
        x, y, (nx, ny) = perimeter((i + 0.5) / 24)
        wob = 1.6 * math.sin((i + 0.5) / 24 * 2 * math.pi * 4)
        bx, by = x + nx * (3 + wob), y + ny * (3 + wob)
        tx, ty = -ny, nx                                        # along the cane
        line(cv, bx, by, bx + nx * 2.2 - tx * 1.2, by + ny * 2.2 - ty * 1.2, 0.45, 0.55)


STAGES = {"seed": (seed, 13.0), "bud": (bud, 13.0), "flower": (flower, 13.0), "berry": (berry, 12.0)}


def wreath(stage):
    """Two motifs, top centre and bottom centre, laid over the season's wreath (9 Nov 2026: as a whole wreath of
    its own the seed and bud were a bare cane that vanished at bar size; one motif at the top wasn't distinct
    enough). The stages differ in shape and in lightness: dark seed, star bud, bright flower, dark berry."""
    cv = Canvas()
    draw, r = STAGES[stage]
    draw(cv, C, C - EDGE - 4, r, -math.pi / 2)
    draw(cv, C, C + EDGE + 4, r, math.pi / 2)
    return cv


def main():
    for stage in STAGES:
        v, a = finish(wreath(stage))
        tga(OUT / f"bramble_{stage}.tga", v, a)
        print(stage, OUT / f"bramble_{stage}.tga")


if __name__ == "__main__":
    main()
