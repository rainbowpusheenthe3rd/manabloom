r"""Draw Manabloom's seasonal frames: {autumn,winter,spring,summer}.tga.

  python tools/manabloom_textures.py

Each is a 128x128 wreath around an action button (the button fills the middle 1/SCALE of it), drawn in white and
greys so the addon can tint it by mana efficiency (red worst, through blue, to white best) with SetVertexColor.
The season is in the shapes: autumn oak leaves and acorns, winter frost and snowflakes, spring blossom on a vine,
summer ivy. Drawn at 4x and averaged down, for clean edges.
"""
import math
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT
SIZE, SS = 128, 4
N = SIZE * SS
SCALE = 1.5                      # the texture is this many button widths across
EDGE = SIZE / SCALE / 2          # the button's half-width, in texture pixels (about 42.7)
HOLE = EDGE - 4                  # nothing is drawn inside this half-width: the icon stays clear
rng = np.random.default_rng(7)

yy, xx = (np.mgrid[0:N, 0:N] + 0.5) / SS  # pixel centres, in texture pixels
C = SIZE / 2


class Canvas:
    def __init__(self):
        self.a = np.zeros((N, N))
        self.v = np.zeros((N, N))

    def put(self, alpha, shade):
        """Paint over what's there."""
        alpha = np.clip(alpha, 0, 1)
        self.v = shade * alpha + self.v * (1 - alpha)
        self.a = alpha + self.a * (1 - alpha)


def perimeter(t):
    """A point on the button's edge, t in [0, 1) going round from the top-left corner, and the outward normal."""
    s = (t % 1) * 4
    side, f = int(s), s - int(s)
    e = EDGE
    pts = [((-e + 2 * e * f, -e), (0, -1)), ((e, -e + 2 * e * f), (1, 0)),
           ((e - 2 * e * f, e), (0, 1)), ((-e, e - 2 * e * f), (-1, 0))]
    (x, y), n = pts[side]
    return C + x, C + y, n


def leaf(cv, cx, cy, ang, length, width, lobes=0, lobe_depth=0.0, tone=0.9):
    """An almond leaf (lobed like an oak with lobes > 0) from its base at (cx, cy), pointing along ang."""
    dx, dy = xx - cx, yy - cy
    u = (dx * math.cos(ang) + dy * math.sin(ang)) / length
    v = -dx * math.sin(ang) + dy * math.cos(ang)
    prof = np.clip(np.sin(np.pi * np.clip(u, 0, 1)), 0, 1) ** 0.75
    if lobes:
        prof = prof * (1 - lobe_depth + lobe_depth * np.abs(np.sin(lobes * np.pi * u)))
    half = width * prof
    inside = (u >= 0) & (u <= 1) & (np.abs(v) < half)
    edge = np.clip((half - np.abs(v)) * SS / 1.5, 0, 1) * inside
    shade = tone * (0.78 + 0.22 * np.clip(v / (width + 1e-6), -1, 1))       # lit from one side
    shade = np.where((np.abs(v) < 0.45) & (u < 0.92), shade * 0.6, shade)    # midrib
    for k in (0.3, 0.5, 0.7):                                                # side veins
        vein = np.abs((u - k) * length - np.abs(v) * 0.7) < 0.35
        shade = np.where(vein & inside & (np.abs(v) > 0.6), shade * 0.75, shade)
    cv.put(edge, shade)
    stem = (u > -0.18) & (u < 0.02) & (np.abs(v) < 0.6)
    cv.put(stem * 1.0, np.full((N, N), tone * 0.55))


def disc(cv, cx, cy, r, shade, soft=1.0):
    d = np.hypot(xx - cx, yy - cy)
    cv.put(np.clip((r - d) * SS / soft, 0, 1), shade if np.ndim(shade) else np.full((N, N), shade))


def line(cv, x0, y0, x1, y1, w, shade):
    px, py = x1 - x0, y1 - y0
    L2 = px * px + py * py or 1
    t = np.clip(((xx - x0) * px + (yy - y0) * py) / L2, 0, 1)
    d = np.hypot(xx - (x0 + t * px), yy - (y0 + t * py))
    cv.put(np.clip((w - d) * SS / 1.2, 0, 1), np.full((N, N), shade))


def acorn(cv, cx, cy, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    nut = ((xx - cx) * ca + (yy - cy) * sa) / 5.5, (-(xx - cx) * sa + (yy - cy) * ca) / 4.2
    d = np.hypot(*nut)
    cv.put(np.clip((1 - d) * 4.2 * SS / 1.5, 0, 1), 0.92 - 0.25 * np.clip(nut[1], -1, 1) ** 2)
    capx, capy = cx - ca * 3.2, cy - sa * 3.2
    cap = np.hypot(((xx - capx) * ca + (yy - capy) * sa) / 3.2, (-(xx - capx) * sa + (yy - capy) * ca) / 4.8)
    hatch = 0.5 + 0.12 * (np.sin(xx * 3.1) * np.sin(yy * 3.1) > 0)
    cv.put(np.clip((1 - cap) * 3.2 * SS / 1.5, 0, 1), hatch)
    line(cv, capx - ca * 2.5, capy - sa * 2.5, capx - ca * 5, capy - sa * 5 - 1, 0.7, 0.5)


def flake(cv, cx, cy, r, shade=1.0):
    for k in range(6):
        a = k * math.pi / 3 + 0.26
        ex, ey = cx + r * math.cos(a), cy + r * math.sin(a)
        line(cv, cx, cy, ex, ey, 0.7, shade)
        for f in (0.45, 0.72):
            bx, by = cx + r * f * math.cos(a), cy + r * f * math.sin(a)
            for s in (-1, 1):
                b = a + s * 0.75
                line(cv, bx, by, bx + r * 0.28 * math.cos(b), by + r * 0.28 * math.sin(b), 0.55, shade)
    disc(cv, cx, cy, 1.4, shade)


def blossom(cv, cx, cy, r, rot):
    for k in range(5):
        a = rot + k * 2 * math.pi / 5
        disc(cv, cx + r * 0.55 * math.cos(a), cy + r * 0.55 * math.sin(a), r * 0.52, 0.97)
    disc(cv, cx, cy, r * 0.32, 0.55)
    for k in range(5):
        a = rot + (k + 0.5) * 2 * math.pi / 5
        disc(cv, cx + r * 0.3 * math.cos(a), cy + r * 0.3 * math.sin(a), 0.5, 0.4)


def glow(cv, strength=0.45):
    """A soft halo just outside the button, so the efficiency colour reads even between the leaves."""
    d = np.maximum(np.abs(xx - C), np.abs(yy - C)) - EDGE
    cv.put(strength * np.exp(-((d - 1.5) / 3.2) ** 2) * (d > -3), np.full((N, N), 1.0))


def autumn():
    cv = Canvas()
    glow(cv)
    for i in range(20):
        t = i / 20 + rng.uniform(-0.012, 0.012)
        x, y, (nx, ny) = perimeter(t)
        out = math.atan2(ny, nx) + rng.uniform(-0.9, 0.9)
        back = rng.uniform(1, 4)
        leaf(cv, x - nx * back, y - ny * back, out, rng.uniform(13, 18), rng.uniform(4.2, 5.4),
             lobes=5, lobe_depth=0.35, tone=rng.uniform(0.78, 1.0))
    for (x, y, a) in ((C - EDGE - 3, C - EDGE - 2, 2.4), (C + EDGE + 3, C + EDGE + 1, -0.7), (C + EDGE + 4, C - EDGE - 3, 0.9)):
        acorn(cv, x, y, a)
    leaf(cv, C + EDGE + 8, C + EDGE + 14, 2.2, 10, 3.4, lobes=5, lobe_depth=0.35, tone=0.85)   # one falling
    return cv


def winter():
    cv = Canvas()
    glow(cv, 0.55)
    for i in range(36):  # frost: short crystals growing out from the edge
        x, y, (nx, ny) = perimeter(i / 36 + rng.uniform(-0.01, 0.01))
        a = math.atan2(ny, nx) + rng.uniform(-0.6, 0.6)
        L = rng.uniform(5, 11)
        ex, ey = x + L * math.cos(a), y + L * math.sin(a)
        line(cv, x, y, ex, ey, 0.8, 0.95)
        for s in (-1, 1):
            b = a + s * 0.8
            mx, my = x + L * 0.55 * math.cos(a), y + L * 0.55 * math.sin(a)
            line(cv, mx, my, mx + 3 * math.cos(b), my + 3 * math.sin(b), 0.6, 0.85)
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        flake(cv, C + sx * (EDGE + 5), C + sy * (EDGE + 5), 8)
    for _ in range(14):
        x, y, (nx, ny) = perimeter(rng.uniform(0, 1))
        disc(cv, x + nx * rng.uniform(8, 18), y + ny * rng.uniform(8, 18), rng.uniform(0.7, 1.3), 1.0)
    return cv


def spring():
    cv = Canvas()
    glow(cv)
    pts = [perimeter(i / 240) for i in range(241)]
    for (x0, y0, n0), (x1, y1, n1), i in zip(pts, pts[1:], range(240)):
        w = 2.2 * math.sin(i / 240 * 2 * math.pi * 9)
        line(cv, x0 + n0[0] * (3 + w), y0 + n0[1] * (3 + w), x1 + n1[0] * (3 + w), y1 + n1[1] * (3 + w), 0.9, 0.6)
    for i in range(18):
        x, y, (nx, ny) = perimeter(i / 18 + 0.02)
        a = math.atan2(ny, nx) + (0.9 if i % 2 else -0.9)
        leaf(cv, x + nx * 3, y + ny * 3, a, rng.uniform(8, 11), rng.uniform(2.6, 3.4), tone=0.85)
    for i, t in enumerate((0.0, 0.17, 0.33, 0.5, 0.66, 0.83)):
        x, y, (nx, ny) = perimeter(t + 0.04)
        blossom(cv, x + nx * 5, y + ny * 5, rng.uniform(6, 7.5), rng.uniform(0, 6.28))
    return cv


def summer():
    cv = Canvas()
    glow(cv, 0.35)
    for i in range(30):
        x, y, (nx, ny) = perimeter(i / 30 + rng.uniform(-0.01, 0.01))
        a = math.atan2(ny, nx) + rng.uniform(-1.1, 1.1)
        leaf(cv, x - nx * 2, y - ny * 2, a, rng.uniform(11, 16), rng.uniform(4.5, 6), tone=rng.uniform(0.82, 1.0))
    return cv


# Autumn and summer redrawn in spring's fine-outline style (9 Nov 2026: the dense leaf rings read as "skittles"
# once coloured). A fine stem round the button, a few small things on it in mirror pairs, and one motif at each
# corner. No randomness, so they're symmetrical and redraw the same.
def stem(cv, tone=0.6, width=0.8, amp=1.4, off=3):
    pts = [perimeter(i / 320) for i in range(321)]
    for i, ((x0, y0, n0), (x1, y1, n1)) in enumerate(zip(pts, pts[1:])):
        w = amp * math.sin(i / 320 * 2 * math.pi * 4)  # one gentle arch per side
        line(cv, x0 + n0[0] * (off + w), y0 + n0[1] * (off + w), x1 + n1[0] * (off + w), y1 + n1[1] * (off + w), width, tone)


def pairs(cv, at, draw):
    """draw(x, y, outward angle) at fractions `at` along each side, so each side mirrors the others."""
    for side in range(4):
        for f in at:
            x, y, (nx, ny) = perimeter((side + f) / 4)
            draw(x + nx * 3, y + ny * 3, math.atan2(ny, nx))


def daisy(cv, cx, cy, r, rot):
    """An oxeye daisy seen from above: a ring of narrow white ray florets round a domed disc of tiny florets."""
    for k in range(21):
        a = rot + k * 2 * math.pi / 21
        leaf(cv, cx + math.cos(a) * r * 0.25, cy + math.sin(a) * r * 0.25, a, r * 0.8, r * 0.13, tone=0.97)
    disc(cv, cx, cy, r * 0.32, 0.62)
    for k in range(8):
        a = k * GOLDEN_ANGLE
        d = r * 0.22 * math.sqrt((k + 0.5) / 8)
        disc(cv, cx + d * math.cos(a), cy + d * math.sin(a), 0.5, 0.8)


GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))


def autumn_fine():
    """A thin oak twig, small lobed oak leaves in mirror pairs, an acorn at each corner."""
    cv = Canvas()
    glow(cv, 0.3)
    stem(cv, tone=0.55, width=0.85, amp=1.2)
    pairs(cv, (0.5,), lambda x, y, a: (
        leaf(cv, x, y, a - 0.7, 9, 3.2, lobes=5, lobe_depth=0.35, tone=0.95),
        leaf(cv, x, y, a + 0.7, 9, 3.2, lobes=5, lobe_depth=0.35, tone=0.95)))
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        acorn(cv, C + sx * (EDGE + 4), C + sy * (EDGE + 4), math.atan2(sy, sx))
    return cv


def summer_fine():
    """A fine meadow stem, small leaves in mirror pairs, an oxeye daisy at each corner."""
    cv = Canvas()
    glow(cv, 0.3)
    stem(cv, tone=0.6, width=0.75, amp=1.4)
    pairs(cv, (0.33, 0.67), lambda x, y, a: (
        leaf(cv, x, y, a - 0.8, 7, 2.4, tone=0.85),
        leaf(cv, x, y, a + 0.8, 7, 2.4, tone=0.85)))
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        daisy(cv, C + sx * (EDGE + 3), C + sy * (EDGE + 3), 9, math.atan2(sy, sx))
    return cv


def finish(cv):
    a, v = cv.a, cv.v
    hole = (np.abs(xx - C) < HOLE) & (np.abs(yy - C) < HOLE)
    a = np.where(hole, 0, a)
    a = a.reshape(SIZE, SS, SIZE, SS).mean(axis=(1, 3))
    v = (cv.v * np.where(hole, 0, cv.a)).reshape(SIZE, SS, SIZE, SS).mean(axis=(1, 3)) / np.maximum(a, 1e-6)
    return np.clip(v, 0, 1), a


def tga(path, v, alpha):
    h, w = alpha.shape
    head = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, w, h, 32, 0x28)
    g = (np.clip(v, 0, 1) * 255).round().astype(np.uint8)
    a = (np.clip(alpha, 0, 1) * 255).round().astype(np.uint8)
    path.write_bytes(head + np.dstack([g, g, g, a]).tobytes())


def leaf_icon():
    """One oak leaf, tip up and to the right, filling a 32x32 icon for the tooltip and chat (tinted there too)."""
    cv = Canvas()
    leaf(cv, 22, 108, -0.95, 118, 34, lobes=5, lobe_depth=0.35, tone=1.0)
    k = SS * 4  # 512 drawn pixels -> 32
    a = cv.a.reshape(32, k, 32, k).mean(axis=(1, 3))
    v = (cv.v * cv.a).reshape(32, k, 32, k).mean(axis=(1, 3)) / np.maximum(a, 1e-6)
    return np.clip(v, 0, 1), a


def minimap_disc():
    """The minimap button's ground: a 64x64 dark forest disc, moonlit at the top-left, with a pale silver rim."""
    n = 64 * SS
    y, x = (np.mgrid[0:n, 0:n] + 0.5) / SS - 32
    r = np.hypot(x, y) / 31
    alpha = np.clip((1 - r) * 31, 0, 1)
    light = np.clip(0.5 - (x + y) / 64, 0, 1)
    rgb = np.stack([0.05 + 0.06 * light, 0.12 + 0.10 * light, 0.10 + 0.10 * light], axis=-1)
    rim = np.exp(-((r - 0.9) / 0.05) ** 2)[..., None]
    rgb = rgb * (1 - rim) + np.array([0.78, 0.86, 0.80]) * rim
    rgb = rgb.reshape(64, SS, 64, SS, 3).mean(axis=(1, 3))
    alpha = alpha.reshape(64, SS, 64, SS).mean(axis=(1, 3))
    return rgb, alpha


def tga_rgb(path, rgb, alpha):
    h, w = alpha.shape
    head = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, w, h, 32, 0x28)
    v = (np.clip(rgb, 0, 1) * 255).round().astype(np.uint8)
    a = (np.clip(alpha, 0, 1) * 255).round().astype(np.uint8)
    path.write_bytes(head + np.dstack([v[..., 2], v[..., 1], v[..., 0], a]).tobytes())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    disc_rgb, disc_a = minimap_disc()
    tga_rgb(OUT / "disc.tga", disc_rgb, disc_a)
    leaf_v, leaf_a = leaf_icon()
    tga(OUT / "leaf.tga", leaf_v, leaf_a)
    # the AddOns-list icon: the minimap disc with the leaf in moonlight white, the best colour, on top (64x64)
    lv = leaf_v[..., None] * np.array([0.94, 0.97, 1.00])
    la = leaf_a[..., None] * 0.95
    rgb = disc_rgb.copy()
    rgb[16:48, 16:48] = rgb[16:48, 16:48] * (1 - la) + lv * la
    tga_rgb(OUT / "icon.tga", rgb, disc_a)
    print(f"leaf: {OUT / 'leaf.tga'}")
    # Only the seasons named on the command line are redrawn (all four if none). Winter and spring draw from the
    # same random sequence as the old autumn did, so redrawing them now would change them; leave them be unless
    # asked. The old dense autumn() and summer() stay above for reference; the fine ones are what ship.
    want = set(sys.argv[1:]) or {"autumn", "winter", "spring", "summer"}
    for name, draw in (("autumn", autumn_fine), ("winter", winter), ("spring", spring), ("summer", summer_fine)):
        if name not in want:
            continue
        v, a = finish(draw())
        tga(OUT / f"{name}.tga", v, a)
        print(f"{name}: {OUT / (name + '.tga')}")


if __name__ == "__main__":
    main()
