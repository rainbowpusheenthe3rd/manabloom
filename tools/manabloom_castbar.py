r"""Write the cast bar's flowers: petals_<season>.tga, centre_<season>.tga (64x64) and cast_bud.tga.

  uv run --no-project --with numpy --with pillow python tools/manabloom_castbar.py [check dir]

One flower per season, chosen so the four read apart at cast bar size (about 18 px):
  * spring: a five-petalled blossom (hawthorn, Crataegus monogyna), broad notched petals, a ring of stamens;
  * summer: the oxeye daisy (Leucanthemum vulgare), 21 narrow rays round a gold disc;
  * autumn: the saffron crocus (Crocus sativus, flowers October-November), six pointed tepals in two whorls of
    three, with its three red stigmas;
  * winter: the snowdrop (Galanthus nivalis) seen from below, three outer tepals round the green-marked inner cup.
Petals are drawn white so the addon tints them (white for a heal, violet for damage); the centres keep their own
colours. Disc florets and stamens sit at the golden angle (137.5 degrees), the way a real head packs them.
The bud is the closed flower ahead of the fill: green sepals with a white tip, in its own colours.

With a check dir, also writes <check dir>/castbar_check.png: the bar at game size (208 x 11, flowers 18 px) for
each season, half full, heal and damage, at 1x and 3x.
"""
import math
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SIZE, SS = 64, 4                       # texture size, supersampling
N = SIZE * SS
C = N / 2
GOLDEN = math.radians(137.507764)
EDGE = (38, 40, 44, 230)               # the thin dark line round each petal, so they read apart on the bar
HEAL, DAMAGE = (0.96, 0.97, 1.00), (0.72, 0.50, 0.98)   # Castbar.lua's tints


def tga(path, im):
    """32-bit uncompressed TGA, top-left origin: the same layout as manabloom_motifs.tga."""
    a = np.asarray(im.convert("RGBA"))
    head = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, im.width, im.height, 32, 0x28)
    path.write_bytes(head + a[..., [2, 1, 0, 3]].tobytes())


def petal(angle, length, width, base=0.0, notch=0.0, point=1.0, steps=40):
    """A petal's outline from the centre outwards along `angle`: widest past the middle, rounded or pointed tip
    (`point` > 1 sharpens it), an optional notch at the tip, starting `base` out from the centre."""
    side = []
    for i in range(steps + 1):
        t = i / steps
        w = width / 2 * math.sin(math.pi * t ** 0.8) ** (1 / point) * (0.35 + 0.65 * t ** 0.5)
        side.append((base + length * t, w))
    tip = (base + length * (1 - notch), 0)
    pts = [(x, w) for x, w in side] + [tip] + [(x, -w) for x, w in reversed(side)]
    ca, sa = math.cos(angle), math.sin(angle)
    return [(C + x * ca - y * sa, C + x * sa + y * ca) for x, y in pts]


def petals(shapes, rim=3 * SS // 2):
    """White petals with a dark rim each (`rim` px at the supersampled size), lighter towards the tip."""
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for pts in shapes:
        d.polygon(pts, fill=(255, 255, 255, 255), outline=EDGE, width=rim)
    a = np.asarray(im).astype(float)
    y, x = np.mgrid[0:N, 0:N]
    r = np.hypot(x - C, y - C) / (N / 2)
    white = (a[..., 0] > 200)                                 # the fill, not the rim
    shade = 0.80 + 0.20 * np.clip(r / 0.85, 0, 1)
    for k in range(3):
        a[..., k] = np.where(white, 255 * shade, a[..., k])
    return Image.fromarray(a.round().astype("uint8"), "RGBA")


def dots(n, spread, size, colour, im=None, start=0):
    """n dots at the golden angle (Vogel's spiral), as florets or stamens pack."""
    im = im or Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(start, start + n):
        r, th = spread * math.sqrt(k / (start + n)), k * GOLDEN
        x, y = C + r * math.cos(th), C + r * math.sin(th)
        d.ellipse((x - size, y - size, x + size, y + size), fill=colour)
    return im


def disc(radius, fill, edge):
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((C - radius, C - radius, C + radius, C + radius), fill=fill, outline=edge, width=SS)
    return im


def spring():
    p = petals([petal(-math.pi / 2 + k * 2 * math.pi / 5, 0.47 * N, 0.40 * N, notch=0.06) for k in range(5)])
    c = disc(0.10 * N, (196, 214, 120, 255), (90, 100, 50, 255))
    dots(13, 0.15 * N, 0.022 * N, (150, 70, 90, 255), c)       # hawthorn's pink-purple anthers
    return p, c


def summer():
    p = petals([petal(k * 2 * math.pi / 21 + 0.1, 0.47 * N, 0.11 * N, base=0.05 * N, notch=0.04) for k in range(21)], rim=SS // 2)  # thin rays: a thin rim, or they go grey
    c = disc(0.17 * N, (236, 182, 34, 255), (150, 100, 20, 255))
    dots(55, 0.155 * N, 0.012 * N, (196, 128, 18, 255), c)      # the disc florets
    return p, c


def autumn():
    outer = [petal(-math.pi / 2 + k * 2 * math.pi / 3, 0.48 * N, 0.26 * N, point=1.8) for k in range(3)]
    inner = [petal(-math.pi / 2 + math.pi / 3 + k * 2 * math.pi / 3, 0.42 * N, 0.24 * N, point=1.8) for k in range(3)]
    p = petals(outer + inner)
    c = disc(0.06 * N, (238, 200, 70, 255), (150, 110, 30, 255))
    d = ImageDraw.Draw(c)
    for k in range(3):                                           # three red stigmas, the saffron
        th = -math.pi / 2 + 0.5 + k * 2 * math.pi / 3
        d.line((C, C, C + 0.20 * N * math.cos(th), C + 0.20 * N * math.sin(th)), fill=(204, 40, 24, 255), width=3 * SS)
    return p, c


def winter():
    p = petals([petal(math.pi / 2 + k * 2 * math.pi / 3, 0.48 * N, 0.34 * N, point=1.2) for k in range(3)])
    c = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    for k in range(3):                                           # the inner tepals, each with its green mark
        th = -math.pi / 2 + k * 2 * math.pi / 3
        pts = petal(th, 0.20 * N, 0.17 * N)
        d.polygon(pts, fill=(246, 250, 246, 255), outline=EDGE, width=SS)
        mx, my = C + 0.15 * N * math.cos(th), C + 0.15 * N * math.sin(th)
        d.ellipse((mx - 0.035 * N, my - 0.035 * N, mx + 0.035 * N, my + 0.035 * N), fill=(70, 150, 60, 255))
    return p, c


def bud():
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    up = -math.pi / 2
    d.polygon(petal(up, 0.42 * N, 0.36 * N, base=-0.18 * N, point=1.6), fill=(250, 250, 244, 255), outline=EDGE, width=SS)
    for side in (-0.42, 0.42):                                   # two sepals wrapped round it
        d.polygon(petal(up + side, 0.34 * N, 0.20 * N, base=-0.20 * N, point=1.5), fill=(84, 150, 70, 255),
                  outline=(30, 60, 30, 255), width=SS)
    return im


SEASONS = {"spring": spring, "summer": summer, "autumn": autumn, "winter": winter}


def small(im):
    return im.resize((SIZE, SIZE), Image.LANCZOS)


def flower(season, tint, px):
    """The flower as the addon draws it: tinted petals under the centre, at px."""
    p, c = (Image.open(ROOT / f"{k}_{season}.tga").convert("RGBA") for k in ("petals", "centre"))
    a = np.asarray(p).astype(float)
    a[..., :3] *= np.asarray(tint)
    out = Image.fromarray(a.round().astype("uint8"), "RGBA")
    out.alpha_composite(c)
    return out.resize((px, px), Image.LANCZOS)


def check(out):
    """Each season's bar at game size, half full, for a heal and a damage spell."""
    w, h, fl = 208, 11, 18
    rows = [(s, t) for s in SEASONS for t in (HEAL, DAMAGE)]
    sheet = Image.new("RGB", (w + 120, len(rows) * 40 + 10), (44, 52, 40))
    budi = Image.open(ROOT / "cast_bud.tga").convert("RGBA").resize((10, 10), Image.LANCZOS)
    for i, (season, tint) in enumerate(rows):
        x0, y0 = 20, 15 + i * 40
        d = ImageDraw.Draw(sheet)
        d.rectangle((x0 - 2, y0 - 2, x0 + w + 1, y0 + h + 1), outline=(240, 236, 255))     # 1 px border
        d.rectangle((x0, y0, x0 + w - 1, y0 + h - 1), fill=(14, 16, 14))
        d.rectangle((x0, y0, x0 + int(w * 0.55) - 1, y0 + h - 1), fill=(31, 92, 41))      # dark green fill
        for k in range(1, 6):
            cx = x0 + w * k / 6
            if k / 6 <= 0.55:
                f = flower(season, tint, fl)
                sheet.paste(f, (int(cx - fl / 2), int(y0 + h / 2 - fl / 2)), f)
            else:
                sheet.paste(budi, (int(cx - 5), int(y0 + h / 2 - 5)), budi)
        big = flower(season, tint, 34)
        sheet.paste(big, (x0 + w + 20, y0 + h // 2 - 17), big)
    sheet.save(out / "castbar_check.png")
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(out / "castbar_check_3x.png")
    print(out / "castbar_check.png")


def main():
    for season, make in SEASONS.items():
        p, c = make()
        tga(ROOT / f"petals_{season}.tga", small(p))
        tga(ROOT / f"centre_{season}.tga", small(c))
    tga(ROOT / "cast_bud.tga", small(bud()))
    if len(sys.argv) > 1:
        check(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
