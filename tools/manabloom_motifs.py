r"""Draw Manabloom's bramble motifs in their own colours: motif_{bud,flower,berry}.tga (64x64).

  python tools/manabloom_motifs.py

The wreath carries efficiency (tinted red to white); the motifs carry the bramble's stage, in natural colours so
they read apart in any season and any efficiency colour (9 Nov 2026): a dark-green bud on a lighter-green calyx,
a white flower, a black berry. Two sit on each wreath, north and south, and climb a six-step ladder:
bud / bud+bud / flower+bud / flower+flower / berry+flower / berry+berry.

True to the bramble's flower genes (Albia, content/base/agents/bramble.toml): five broad rounded petals (shape
0.7), radial, open cup, many stamens; the berry an aggregate of drupelets (13 drawn, on the golden angle: H).
Each motif has a thin dark rim, so the white flower still reads on a white wreath.
"""
import math
import struct
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parents[1]
SIZE, SS = 64, 4
N = SIZE * SS
GOLDEN = math.pi * (3 - math.sqrt(5))
yy, xx = (np.mgrid[0:N, 0:N] + 0.5) / SS
C = SIZE / 2


class Paint:
    def __init__(self):
        self.rgb = np.zeros((N, N, 3))
        self.a = np.zeros((N, N))

    def put(self, alpha, rgb):
        alpha = np.clip(alpha, 0, 1)[..., None]
        col = np.broadcast_to(np.asarray(rgb, float), (N, N, 3)) if np.ndim(rgb) == 1 else rgb
        self.rgb = col * alpha + self.rgb * (1 - alpha)
        self.a = alpha[..., 0] + self.a * (1 - alpha[..., 0])


def soft(d):  # signed distance (inside > 0, in pixels) to an anti-aliased mask
    return np.clip(d * SS / 1.2, 0, 1)


def disc(cx, cy, r):
    return soft(r - np.hypot(xx - cx, yy - cy))


def petal(cx, cy, ang, length, shape=0.7):
    dx, dy = xx - cx, yy - cy
    u = (dx * math.cos(ang) + dy * math.sin(ang)) / length
    v = -dx * math.sin(ang) + dy * math.cos(ang)
    uc = np.clip(u, 0, 1)
    w = length * (0.25 + 0.3 * shape) * uc ** 0.55 * np.sqrt(np.clip(1 - uc ** 5, 0, 1))
    return soft(w - np.abs(v)) * (u >= 0) * (u <= 1)


def sepal(cx, cy, ang, length, width=0.24):
    dx, dy = xx - cx, yy - cy
    u = (dx * math.cos(ang) + dy * math.sin(ang)) / length
    v = -dx * math.sin(ang) + dy * math.cos(ang)
    w = length * width * np.clip(1 - np.clip(u, 0, 1), 0, 1) ** 0.8 * (u > 0)
    return soft(w - np.abs(v)) * (u <= 1)


def rim(p, px=1.6, tone=(0.06, 0.07, 0.05)):
    """A thin dark rim round everything drawn so far, drawn underneath it."""
    a = p.a
    grown = a.copy()
    k = int(px * SS)
    for dy in range(-k, k + 1, 2):
        for dx in range(-k, k + 1, 2):
            if dx * dx + dy * dy <= k * k:
                grown = np.maximum(grown, np.roll(np.roll(a, dy, 0), dx, 1))
    under = Paint()
    under.put(grown * 0.85, tone)
    under.put(p.a, p.rgb)
    return under


LEAF_GREEN, DARK_GREEN = (0.46, 0.72, 0.32), (0.16, 0.38, 0.14)
WHITE, STAMEN, CENTRE = (0.97, 0.96, 0.94), (0.93, 0.86, 0.46), (0.72, 0.78, 0.40)
BLACK, GLINT, RIM = (0.07, 0.05, 0.09), (0.62, 0.62, 0.74), (0.36, 0.34, 0.56)
BERRY = (0.11, 0.04, 0.14)  # deep purple-black: a ripe blackberry, and lighter than the gaps and the dark rim


def bud():
    p = Paint()
    r, rot = 24, -math.pi / 2
    for k in range(5):                                   # the lighter-green calyx, sepals spread a little
        p.put(sepal(C, C, rot + (k + 0.5) * 2 * math.pi / 5, r, 0.30), LEAF_GREEN)
    p.put(disc(C, C, r * 0.48), DARK_GREEN)              # the dark-green bud, closed
    for k in range(5):                                   # its own sepals folded over it: faint seams
        a = rot + k * 2 * math.pi / 5
        p.put(sepal(C, C, a, r * 0.46, 0.08), (0.10, 0.26, 0.09))
    p.put(disc(C - 3, C - 3, 2.2), (0.40, 0.62, 0.34))  # a glint, so it reads round
    return rim(p)


def flower():
    p = Paint()
    r, rot = 28, -math.pi / 2
    for k in range(5):                                   # five broad white petals
        p.put(petal(C, C, rot + k * 2 * math.pi / 5, r), WHITE)
    p.put(disc(C, C, r * 0.40), STAMEN)                  # the ring of many stamens
    for k in range(16):
        a = rot + k * 2 * math.pi / 16
        p.put(disc(C + r * 0.33 * math.cos(a), C + r * 0.33 * math.sin(a), 1.4), (0.80, 0.66, 0.22))
    p.put(disc(C, C, r * 0.20), CENTRE)                  # the carpels in the middle
    return rim(p)


def berry():
    """The accurate form with the readable colours (the author, 9 Nov 2026, after trying 13 small, 7 big and 9 packed):
    13 drupelets on the golden angle with a rim round the fruit's outline, coloured like the 9-drupelet version,
    a purple-black body over near-black gaps, each drupelet with a cool rim light, a gloss and a white point."""
    p = Paint()
    r, rot = 24, -math.pi / 2
    for k in range(5):                                   # sepals folded back behind the fruit
        p.put(sepal(C, C, rot + (k + 0.5) * 2 * math.pi / 5, r * 1.15, 0.22), LEAF_GREEN)
    p.put(disc(C, C, r * 0.86), (0.02, 0.01, 0.03))      # the gaps between drupelets
    n = 13
    for i in range(n):
        j = n - 1 - i
        d = r * 0.62 * math.sqrt((j + 0.5) / n)
        a = rot + j * GOLDEN
        x, y = C + d * math.cos(a), C + d * math.sin(a)
        sz = r * 0.25
        p.put(disc(x, y, sz), BERRY)
        p.put(disc(x, y, sz) * (1 - disc(x - sz * 0.16, y - sz * 0.16, sz)) * 0.8, RIM)   # rim light, lower right
        p.put(disc(x - sz * 0.30, y - sz * 0.30, sz * 0.30), GLINT)                      # a small gloss
        p.put(disc(x - sz * 0.33, y - sz * 0.33, sz * 0.12), (1.0, 1.0, 1.0))           # its white point
    p.put(disc(C, C, r * 0.86) * (1 - disc(C - r * 0.05, C - r * 0.05, r * 0.86)) * 0.8, RIM)  # the fruit's outline
    return rim(p)


def tga(path, p):
    rgb = p.rgb.reshape(SIZE, SS, SIZE, SS, 3).mean(axis=(1, 3))
    a = p.a.reshape(SIZE, SS, SIZE, SS).mean(axis=(1, 3))
    # un-premultiply the averaged colour so edges keep their hue
    num = (p.rgb * p.a[..., None]).reshape(SIZE, SS, SIZE, SS, 3).mean(axis=(1, 3))
    rgb = np.where(a[..., None] > 1e-4, num / np.maximum(a[..., None], 1e-4), rgb)
    head = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, SIZE, SIZE, 32, 0x28)
    v = (np.clip(rgb, 0, 1) * 255).round().astype(np.uint8)
    al = (np.clip(a, 0, 1) * 255).round().astype(np.uint8)
    path.write_bytes(head + np.dstack([v[..., 2], v[..., 1], v[..., 0], al]).tobytes())


def main():
    for name, draw in (("bud", bud), ("flower", flower), ("berry", berry)):
        tga(OUT / f"motif_{name}.tga", draw())
        print(OUT / f"motif_{name}.tga")


if __name__ == "__main__":
    main()
