r"""Draft Manabloom's race x class pivot: a wreath per race (its homeland's flora) and a three-stage ladder per
class (what grows when you cast well), drawn geometrically in natural colours, then composed into the pivot.

  uv run --with pillow python tools/manabloom_pivot_draft.py <out dir>

Writes <out>/race_wreaths.png, <out>/class_ladders.png and <out>/pivot.png. A draft for discussion (the author,
10 Nov 2026): 8 race palettes x 7 class ladders give the 22 classic mana-using combinations. The druid ladder is
the shipped bramble (motif_*.tga); the rest are new and drawn here.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manabloom_class_icons as CI  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MOTIFS = ROOT
SS = 4                              # supersampling
ICON = 96                           # a ladder stage, final size
WREATH = 150                        # a wreath tile, final size (the button is the middle two thirds)
BG = (52, 44, 38)
try:
    FONT = ImageFont.truetype("segoeui.ttf", 16)
    SMALL = ImageFont.truetype("segoeui.ttf", 13)
    BOLD = ImageFont.truetype("segoeuib.ttf", 16)
except OSError:
    FONT = SMALL = BOLD = ImageFont.load_default()

RACES = ["Human", "Dwarf", "Night Elf", "Gnome", "Orc", "Undead", "Tauren", "Troll"]
CLASSES = ["Druid", "Priest", "Mage", "Warlock", "Shaman", "Paladin", "Hunter"]
# classic's mana-using combinations (Forever may differ: check before building)
ALLOWED = {
    "Human": {"Priest", "Mage", "Warlock", "Paladin"}, "Dwarf": {"Priest", "Paladin", "Hunter"},
    "Night Elf": {"Druid", "Priest", "Hunter"}, "Gnome": {"Mage", "Warlock"},
    "Orc": {"Warlock", "Shaman", "Hunter"}, "Undead": {"Priest", "Mage", "Warlock"},
    "Tauren": {"Druid", "Shaman", "Hunter"}, "Troll": {"Priest", "Mage", "Shaman", "Hunter"},
}
HOME = {"Human": "Elwynn: wheat and dog rose", "Dwarf": "Dun Morogh: pine and heather",
        "Night Elf": "Teldrassil: bramble and moonflower", "Gnome": "Gnomeregan: copper, cogs, blue mushrooms",
        "Orc": "Durotar: thorn and cactus flower", "Undead": "Tirisfal: deathcap and nightshade",
        "Tauren": "Mulgore: prairie grass, wildflowers, feathers", "Troll": "Echo Isles: palm, orchid, shell"}
LADDER = {"Druid": "bud, flower, blackberry", "Priest": "candle, flame, halo", "Mage": "spark, glyph, crystal",
          "Warlock": "ember, fel flame, soul shard", "Shaman": "pebble, wave, storm",
          "Paladin": "dim seal, glowing seal, radiant seal", "Hunter": "flint point, fletched arrow, drawn bow"}


def canvas(size):
    im = Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def done(im, size):
    return im.resize((size, size), Image.LANCZOS)


def poly(d, pts, fill, outline=None, w=0):
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill, outline=outline, width=int(w * SS) if w else 0)


def circ(d, cx, cy, r, fill, outline=None, w=0):
    d.ellipse(((cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS), fill=fill, outline=outline,
              width=int(w * SS) if w else 0)


def line(d, pts, fill, w):
    d.line([(x * SS, y * SS) for x, y in pts], fill=fill, width=max(1, int(w * SS)), joint="curve")


def petal_pts(cx, cy, ang, length, width, n=24):
    """An obovate petal from the centre outwards, as a polygon."""
    out = []
    for i in range(n + 1):
        u = i / n
        wv = width * (u ** 0.55) * math.sqrt(max(0.0, 1 - u ** 5))
        out.append((u, wv))
    pts = [(cx + math.cos(ang) * u * length - math.sin(ang) * wv, cy + math.sin(ang) * u * length + math.cos(ang) * wv)
           for u, wv in out]
    pts += [(cx + math.cos(ang) * u * length + math.sin(ang) * wv, cy + math.sin(ang) * u * length - math.cos(ang) * wv)
            for u, wv in reversed(out)]
    return pts


def leaf_pts(cx, cy, ang, length, width, n=20):
    pts = []
    for i in range(n + 1):
        u = i / n
        wv = width * math.sin(math.pi * u) ** 0.8
        pts.append((cx + math.cos(ang) * u * length - math.sin(ang) * wv, cy + math.sin(ang) * u * length + math.cos(ang) * wv))
    for i in range(n, -1, -1):
        u = i / n
        wv = width * math.sin(math.pi * u) ** 0.8
        pts.append((cx + math.cos(ang) * u * length + math.sin(ang) * wv, cy + math.sin(ang) * u * length - math.cos(ang) * wv))
    return pts


def flower(d, cx, cy, r, n, petal, centre, rot=-math.pi / 2, shape=0.6):
    for k in range(n):
        poly(d, petal_pts(cx, cy, rot + k * 2 * math.pi / n, r, r * (0.25 + 0.3 * shape)), petal, (30, 26, 24), 1)
    circ(d, cx, cy, r * 0.28, centre)


def flame(d, cx, cy, h, outer, inner):
    """A teardrop flame, tip up, centred on (cx, cy), h tall; a smaller, brighter core inside."""
    def drop(scale, col, dy=0.0):
        pts = []
        for i in range(61):
            t = i / 60 * 2 * math.pi
            x = 0.5 * h * scale * math.sin(t) * math.sin(t / 2) ** 1.4
            y = -0.5 * h * scale * math.cos(t)
            pts.append((cx + x, cy + y + dy))
        poly(d, pts, col)
    drop(1.0, outer)
    drop(0.55, inner, h * 0.18)


# Class ladders: three stages each, natural colours -------------------------------------------------------------

def stage_icon_painted(cls, stage):
    """The painted trial (manabloom_class_icons.py): sharper, but the author judged the style much worse. Not used."""
    return CI.image(CI.CLASSES[cls](stage)).resize((ICON, ICON), Image.LANCZOS)


def stage_icon(cls, stage):
    """The class ladders: flat, bright, a distinct colour per stage. Primitive but largely right (the author)."""
    if cls == "Druid":
        name = ("bud", "flower", "berry")[stage]
        return Image.open(MOTIFS / f"motif_{name}.tga").convert("RGBA").resize((ICON, ICON), Image.LANCZOS)
    im, d = canvas(ICON)
    c = ICON / 2
    if cls == "Priest":
        circ(d, c, c + 6, 0, None)
        d.rounded_rectangle(((c - 10) * SS, (c - 2) * SS, (c + 10) * SS, (c + 34) * SS), 4 * SS, fill=(236, 228, 206),
                            outline=(60, 50, 40), width=SS)
        line(d, [(c, c - 2), (c, c - 9)], (40, 34, 30), 2)
        if stage >= 1:
            flame(d, c, c - 22, 30, (250, 160, 50), (255, 236, 160))
        if stage == 2:
            circ(d, c, c - 20, 26, None, (250, 214, 110), 3)
            for k in range(12):
                a = k * math.pi / 6
                line(d, [(c + math.cos(a) * 30, c - 20 + math.sin(a) * 30), (c + math.cos(a) * 38, c - 20 + math.sin(a) * 38)],
                     (250, 214, 110), 2)
    elif cls == "Mage":
        if stage == 0:
            for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
                poly(d, [(c, c), (c + math.cos(a - 0.25) * 10, c + math.sin(a - 0.25) * 10),
                         (c + math.cos(a) * 26, c + math.sin(a) * 26), (c + math.cos(a + 0.25) * 10, c + math.sin(a + 0.25) * 10)],
                     (176, 150, 255))
            circ(d, c, c, 5, (240, 236, 255))
        elif stage == 1:
            circ(d, c, c, 30, None, (150, 120, 250), 3)
            circ(d, c, c, 22, None, (150, 120, 250), 2)
            for k in range(6):
                a = k * math.pi / 3
                line(d, [(c + math.cos(a) * 22, c + math.sin(a) * 22), (c + math.cos(a + 2.1) * 22, c + math.sin(a + 2.1) * 22)],
                     (200, 180, 255), 2)
            circ(d, c, c, 5, (240, 236, 255))
        else:
            pts = [(c, c - 36), (c + 18, c - 12), (c + 14, c + 30), (c - 14, c + 30), (c - 18, c - 12)]
            poly(d, pts, (120, 196, 250), (30, 40, 70), 2)
            poly(d, [(c, c - 36), (c + 18, c - 12), (c, c + 30)], (176, 226, 255))
            poly(d, [(c, c - 36), (c - 18, c - 12), (c, c - 4)], (220, 244, 255))
    elif cls == "Warlock":
        # fel green is the ambient light: it rims the shadow side of the ember and the shard
        if stage == 0:
            circ(d, c, c, 22, (40, 90, 30, 120))
            circ(d, c + 2, c + 2, 13, (110, 230, 80))
            circ(d, c - 1, c - 1, 13, (240, 110, 30))
            circ(d, c - 4, c - 4, 5, (255, 210, 120))
        elif stage == 1:
            flame(d, c, c, 66, (80, 200, 60), (200, 255, 150))
        else:
            pts = [(c, c - 36), (c + 20, c), (c, c + 36), (c - 20, c)]
            poly(d, pts, (120, 50, 170), (30, 10, 40), 2)
            poly(d, [(c, c - 36), (c + 20, c), (c, c)], (170, 90, 220))
            poly(d, [(c + 20, c), (c, c + 36), (c + 2, c + 27), (c + 15, c + 2)], (110, 220, 90))
            poly(d, [(c - 20, c), (c, c + 36), (c - 2, c + 28), (c - 16, c + 1)], (90, 150, 110))
            circ(d, c, c, 7, (230, 190, 255))
    elif cls == "Shaman":
        if stage == 0:
            d.ellipse(((c - 26) * SS, (c - 16) * SS, (c + 26) * SS, (c + 18) * SS), fill=(140, 136, 128),
                      outline=(50, 46, 42), width=2 * SS)
            d.ellipse(((c - 16) * SS, (c - 10) * SS, (c + 2) * SS, (c - 2) * SS), fill=(180, 176, 168))
        elif stage == 1:
            pts = []
            for i in range(60):
                t = i / 59
                pts.append((c - 34 + 68 * t, c + 12 - 22 * math.sin(math.pi * t) * (1 - 0.4 * t)))
            pts += [(c + 34, c + 22), (c - 34, c + 22)]
            poly(d, pts, (60, 140, 220), (20, 40, 70), 2)
            circ(d, c + 14, c - 2, 8, (200, 230, 255))
        else:
            d.ellipse(((c - 34) * SS, (c - 34) * SS, (c + 34) * SS, (c - 4) * SS), fill=(70, 74, 90))
            poly(d, [(c + 2, c - 14), (c - 12, c + 8), (c - 2, c + 8), (c - 10, c + 36), (c + 14, c + 2), (c + 3, c + 2), (c + 12, c - 14)],
                 (255, 226, 80), (60, 50, 10), 2)
    elif cls == "Paladin":
        base = [(150, 110, 60), (226, 178, 70), (250, 214, 110)][stage]
        if stage == 2:
            for k in range(16):
                a = k * math.pi / 8
                line(d, [(c + math.cos(a) * 30, c + math.sin(a) * 30), (c + math.cos(a) * 44, c + math.sin(a) * 44)],
                     (255, 236, 160), 3)
        circ(d, c, c, 28, base, (60, 44, 20), 2)
        circ(d, c, c, 20, None, (90, 66, 30), 2)
        if stage >= 1:
            line(d, [(c, c - 14), (c, c + 14)], (255, 248, 220), 4)
            line(d, [(c - 10, c - 4), (c + 10, c - 4)], (255, 248, 220), 4)
    elif cls == "Hunter":
        # one arrow being made and then used: a knapped flint point, the point hafted and fletched, the arrow
        # nocked on a drawn bow. Drawn along the diagonal, local y running from the tip (negative) to the tail.
        def at(pts, s=1.0, ox=0.0, oy=0.0):
            k = math.sqrt(0.5)
            return [(c + ox + (x * s - y * s) * k, c + oy + (x * s + y * s) * k) for x, y in pts]

        def point_shape(serrate):
            """A side-notched point, tip up, base at y = 24; knapped edges zigzag when serrate."""
            right = []
            w = 21 if serrate else 15                                 # the loose point is broad, so it reads as one
            for i in range(13):                                       # tip (0, -34) down to the shoulder (w, 12)
                u = i / 12
                x, y = w * u, -34 + 46 * u
                if serrate and 0 < i < 12:
                    x += 0.9 if i % 2 else -0.3
                right.append((x, y))
            right += [(w - 7, 15), (w - 3, 24)] if serrate else [(9, 15), (13, 24)]
            left = [(-x, y) for x, y in reversed(right)]
            return right, left

        def head(s, oy, upright=False, serrate=False):
            f = (lambda p: [(c + x * s, c + y * s + oy) for x, y in p]) if upright else \
                (lambda p: at([(x, y + oy) for x, y in p], s))
            right, left = point_shape(serrate)
            poly(d, f(right + left), (112, 120, 136), (32, 36, 44), 2)   # flint, the shadowed half
            poly(d, f(left + [(0, 24)]), (186, 194, 210))                # the lit half, flat
            if serrate:                                               # flake scars: shallow ridges off the spine
                for y in (-18, -6, 6):
                    u = (y + 34) / 46
                    line(d, f([(0, y - 4), (-21 * u + 4, y + 2)]), (150, 158, 176), 1)
                    line(d, f([(0, y - 4), (21 * u - 4, y + 2)]), (84, 90, 104), 1)
            line(d, f([(0, -34), (0, 22)]), (236, 240, 248), 1)        # the ridge catches the light

        def shaft(y0, y1, s):
            line(d, at([(0, y0), (0, y1)], s), (60, 40, 24), 6)
            line(d, at([(0, y0), (0, y1)], s), (168, 120, 70), 3)

        def fletch(y, s):
            for side in (-1, 1):
                vane = [(0, y), (side * 9, y + 6), (side * 9, y + 18), (0, y + 14)]
                poly(d, at(vane, s), (200, 56, 44) if side < 0 else (238, 226, 200), (50, 24, 20), 1)

        if stage == 0:
            head(1.2, 6, upright=True, serrate=True)
        elif stage == 1:
            shaft(-8, 38, 1.0)
            fletch(20, 1.0)
            head(0.62, -30.5)                                          # its base sits on the shaft's top
        else:
            bow = [(x, -18 + 26 * (x / 34) ** 2) for x in [i * 2 - 34 for i in range(35)]]
            inner = [(x, y + 9 * (1 - 0.6 * abs(x) / 34)) for x, y in reversed(bow)]
            line(d, at([bow[0], (0, 22), bow[-1]]), (232, 226, 210), 1)   # the string, drawn back to the nock
            poly(d, at(bow + inner), (176, 118, 62), (50, 30, 16), 2)
            poly(d, at([(-3, -18), (3, -18), (3, -11), (-3, -11)]), (80, 130, 70))   # the grip's wrap
            shaft(-8, 24, 1.0)
            fletch(8, 1.0)
            head(0.62, -30.5)
    return finish(cls, stage, done(im, ICON))


# Ambient light: a soft glow in the class's light, rising with the stage, and a thin dark outline so every icon
# reads on a button. Warlocks are lit fel green at every stage.
GLOW = {
    "Priest": [None, ((255, 190, 90), 0.55), ((255, 214, 110), 0.9)],
    "Mage": [((176, 150, 255), 0.35), ((150, 120, 250), 0.55), ((140, 210, 255), 0.8)],
    "Warlock": [((90, 230, 70), 0.6), ((90, 240, 70), 0.8), ((100, 250, 80), 0.9)],
    "Shaman": [None, ((120, 190, 255), 0.45), ((255, 230, 120), 0.75)],
    "Paladin": [None, ((250, 200, 90), 0.5), ((255, 226, 130), 0.9)],
    "Hunter": [None, None, ((255, 206, 140), 0.45)],
}


def finish(cls, stage, im):
    from PIL import ImageChops, ImageFilter
    a = im.getchannel("A")
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    g = GLOW.get(cls, [None] * 3)[stage]
    if g:
        col, k = g
        halo = a.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(7))
        halo = halo.point(lambda v: int(min(255, v * k * 1.4)))
        n = im.width                                     # fade to nothing before the canvas edge: no square halos
        fall = Image.radial_gradient("L").resize((n, n)).point(lambda v: int(255 * max(0.0, 1 - (v / 255) ** 2 * 1.9)))
        halo = ImageChops.multiply(halo, fall)
        out.alpha_composite(Image.merge("RGBA", [Image.new("L", im.size, ch) for ch in col] + [halo]))
    edge = ImageChops.lighter(a.filter(ImageFilter.MaxFilter(3)), a)
    out.alpha_composite(Image.merge("RGBA", [Image.new("L", im.size, ch) for ch in (24, 20, 18)] + [edge]))
    out.alpha_composite(im)
    return out


# Race wreaths: homeland flora round the button, natural colours --------------------------------------------------

def wreath(race):
    im, d = canvas(WREATH)
    e, c = WREATH / 3, WREATH / 2                 # the button's half width; the centre
    stem = {"Human": (110, 140, 70), "Dwarf": (60, 90, 60), "Night Elf": (120, 80, 110), "Gnome": (190, 110, 60),
            "Orc": (130, 100, 70), "Undead": (110, 120, 100), "Tauren": (170, 160, 90), "Troll": (60, 130, 70)}[race]
    pts = []
    for i in range(201):
        t = i / 200 * 4
        side, f = int(t) % 4, t - int(t)
        x, y = [(-e + 2 * e * f, -e), (e, -e + 2 * e * f), (e - 2 * e * f, e), (-e, e - 2 * e * f)][side]
        wob = 1.5 * math.sin(i / 200 * 2 * math.pi * 4)
        nx, ny = [(0, -1), (1, 0), (0, 1), (-1, 0)][side]
        pts.append((c + x + nx * (4 + wob), c + y + ny * (4 + wob)))
    line(d, pts, stem, 2.2)
    corners = [(c - e - 4, c - e - 4), (c + e + 4, c - e - 4), (c + e + 4, c + e + 4), (c - e - 4, c + e + 4)]
    mids = [(c, c - e - 5, -math.pi / 2), (c + e + 5, c, 0), (c, c + e + 5, math.pi / 2), (c - e - 5, c, math.pi)]
    diag = [-3 * math.pi / 4, -math.pi / 4, math.pi / 4, 3 * math.pi / 4]   # each corner's outward direction
    for (x, y), (mx, my, a), da in zip(corners, mids, diag):
        if race == "Human":
            flower(d, x, y, 10, 5, (244, 170, 190), (240, 210, 90))
            for s in (-1, 1):                     # two wheat ears fanning out along the side
                ax = a + math.pi / 2 * s * 0.75   # the ear's axis, leaning along the side
                ux, uy = math.cos(ax), math.sin(ax)
                line(d, [(mx, my), (mx + ux * 18, my + uy * 18)], (190, 160, 80), 1.2)
                for k in range(4):                # paired grains up the ear, smaller towards the tip
                    gx, gy, g = mx + ux * (6 + k * 3.2), my + uy * (6 + k * 3.2), 5.5 - k * 0.6
                    for side in (-1, 1):
                        poly(d, leaf_pts(gx, gy, ax + side * 0.55, g, g * 0.42), (232, 196, 104), (120, 90, 40), 0.6)
                line(d, [(mx + ux * 18, my + uy * 18), (mx + ux * 23, my + uy * 23)], (232, 196, 104), 0.8)   # awn
        elif race == "Dwarf":
            ux, uy = math.cos(da), math.sin(da)   # heather spike pointing out of the corner: bells smaller to the tip
            line(d, [(x - ux * 6, y - uy * 6), (x + ux * 12, y + uy * 12)], (90, 70, 60), 1.2)
            for k in range(5):
                side = 1 if k % 2 else -1
                px, py = -uy * side, ux * side
                r = 3.0 - k * 0.4
                circ(d, x + ux * (k * 3.6 - 4) + px * 2.4, y + uy * (k * 3.6 - 4) + py * 2.4, r,
                     (176, 104, 196), (90, 40, 110), 0.6)
            ux, uy = math.cos(a), math.sin(a)     # pine sprig pointing outwards: needle pairs swept back
            line(d, [(mx - ux * 2, my - uy * 2), (mx + ux * 13, my + uy * 13)], (70, 60, 40), 1.4)
            for k in range(4):
                bx, by = mx + ux * (1 + k * 3.5), my + uy * (1 + k * 3.5)
                for side in (-1, 1):
                    ang = a + math.pi + side * 2.3
                    line(d, [(bx, by), (bx - math.cos(ang) * (7 - k), by - math.sin(ang) * (7 - k))], (40, 100, 64), 1.2)
        elif race == "Night Elf":
            flower(d, x, y, 11, 5, (236, 238, 250), (200, 210, 120))
            poly(d, leaf_pts(mx, my, a - 0.6, 12, 4), (150, 170, 180))
            poly(d, leaf_pts(mx, my, a + 0.6, 12, 4), (150, 170, 180))
        elif race == "Gnome":
            for k in range(8):                    # cog teeth
                ang = k * math.pi / 4
                circ(d, x + math.cos(ang) * 9, y + math.sin(ang) * 9, 3, (196, 120, 60))
            circ(d, x, y, 9, (210, 136, 70), (70, 40, 20), 1)
            circ(d, x, y, 3.5, (60, 40, 30))
            d.ellipse(((mx - 7) * SS, (my - 6) * SS, (mx + 7) * SS, (my + 1) * SS), fill=(80, 140, 230))
            line(d, [(mx, my), (mx, my + 6)], (220, 220, 200), 2)
        elif race == "Orc":
            flower(d, x, y, 9, 6, (230, 90, 50), (250, 210, 80), shape=0.3)
            for s in (-1, 1):
                poly(d, [(mx, my), (mx + math.cos(a + s * 0.9) * 12, my + math.sin(a + s * 0.9) * 12),
                         (mx + math.cos(a + s * 0.5) * 3, my + math.sin(a + s * 0.5) * 3)], (210, 200, 180))
        elif race == "Undead":
            d.pieslice(((x - 10) * SS, (y - 9) * SS, (x + 10) * SS, (y + 9) * SS), 180, 360, fill=(190, 210, 150))
            line(d, [(x, y), (x, y + 8)], (220, 220, 200), 3)
            for k in range(3):
                circ(d, mx + math.cos(a + (k - 1) * 0.7) * 6, my + math.sin(a + (k - 1) * 0.7) * 6, 3.2, (80, 40, 110))
        elif race == "Tauren":
            flower(d, x, y, 9, 5, (250, 210, 70), (140, 90, 40), shape=0.4)
            poly(d, leaf_pts(mx - math.cos(a) * 4, my - math.sin(a) * 4, a + 0.4, 16, 3.5), (250, 250, 245), (60, 50, 40), 1)
            line(d, [(mx - math.cos(a) * 4, my - math.sin(a) * 4), (mx + math.cos(a + 0.4) * 12, my + math.sin(a + 0.4) * 12)],
                 (80, 60, 40), 1.4)
        elif race == "Troll":
            for k, ang in enumerate((-1.9, -0.5, 0.9, 2.3)):     # orchid: lip below, petals round
                poly(d, petal_pts(x, y, ang - math.pi / 2, 10, 5), (210, 80, 190), (60, 20, 50), 1)
            poly(d, petal_pts(x, y, math.pi / 2, 9, 6), (250, 220, 240), (60, 20, 50), 1)
            d.pieslice(((mx - 7) * SS, (my - 6) * SS, (mx + 7) * SS, (my + 8) * SS), 180, 360, fill=(240, 210, 180),
                       outline=(120, 90, 70), width=SS)
            for k in range(4):
                line(d, [(mx, my + 1), (mx - 6 + k * 4, my - 4)], (150, 110, 90), 1)
    return done(im, WREATH)


def tile(race, cls):
    """A button in the race's wreath, the class's ladder strip beneath: what a combination would look like."""
    t = Image.new("RGBA", (WREATH, WREATH + 50), BG + (255,))
    b = WREATH // 3
    ImageDraw.Draw(t).rounded_rectangle((b, b, 2 * b, 2 * b), 6, fill=(70, 95, 60), outline=(20, 18, 16), width=2)
    t.alpha_composite(wreath(race))
    for k in range(3):
        icon = stage_icon(cls, k).resize((40, 40), Image.LANCZOS)
        t.alpha_composite(icon, (8 + k * 48, WREATH + 4))
    return t


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    # the class ladders
    W = 260 + 3 * (ICON + 20)
    sheet = Image.new("RGB", (W, 20 + len(CLASSES) * (ICON + 20)), BG)
    d = ImageDraw.Draw(sheet)
    for r, cls in enumerate(CLASSES):
        y = 20 + r * (ICON + 20)
        d.text((16, y + ICON // 2 - 10), cls, fill=(240, 236, 228), font=BOLD)
        d.text((16, y + ICON // 2 + 10), LADDER[cls], fill=(200, 194, 186), font=SMALL)
        for k in range(3):
            sheet.paste(stage_icon(cls, k), (260 + k * (ICON + 20), y), stage_icon(cls, k))
    sheet.save(out / "class_ladders.png")
    # the race wreaths
    sheet = Image.new("RGB", (4 * 330, 2 * (WREATH + 60)), BG)
    d = ImageDraw.Draw(sheet)
    for k, race in enumerate(RACES):
        x, y = (k % 4) * 330, (k // 4) * (WREATH + 60)
        b = WREATH // 3
        d.rounded_rectangle((x + 90 + b, y + 10 + b, x + 90 + 2 * b, y + 10 + 2 * b), 6, fill=(70, 95, 60))
        w = wreath(race)
        sheet.paste(w, (x + 90, y + 10), w)
        d.text((x + 165, y + WREATH + 22), race, fill=(240, 236, 228), font=BOLD, anchor="mm")
        d.text((x + 165, y + WREATH + 42), HOME[race], fill=(200, 194, 186), font=SMALL, anchor="mm")
    sheet.save(out / "race_wreaths.png")
    # the pivot
    CW, CH, LW, TOP = WREATH + 16, WREATH + 66, 130, 40
    sheet = Image.new("RGB", (LW + len(CLASSES) * CW, TOP + len(RACES) * CH), (36, 30, 26))
    d = ImageDraw.Draw(sheet)
    for j, cls in enumerate(CLASSES):
        d.text((LW + j * CW + CW // 2, TOP // 2), cls, fill=(240, 236, 228), font=BOLD, anchor="mm")
    for i, race in enumerate(RACES):
        y = TOP + i * CH
        d.text((14, y + CH // 2), race, fill=(240, 236, 228), font=BOLD, anchor="lm")
        for j, cls in enumerate(CLASSES):
            x = LW + j * CW + 8
            if cls in ALLOWED[race]:
                sheet.paste(tile(race, cls), (x, y + 8))
            else:
                d.text((x + WREATH // 2, y + CH // 2), "-", fill=(110, 100, 92), font=FONT, anchor="mm")
    sheet.save(out / "pivot.png")
    print("written to", out)


if __name__ == "__main__":
    main(sys.argv[1])
