r"""Draw Manabloom 1.1's 400x400 logo: the flowering cast bar on the dark forest disc.

  uv run --no-project --with numpy --with pillow python tools/manabloom_castbar_logo.py <out.png>

A cast bar across the disc as the addon draws it (Castbar.lua): a 1 px rim in the night elf's moonflower colour,
lit along the fill, a dark green fill, and the year's four flowers opening along it (snowdrop, hawthorn, oxeye
daisy, saffron crocus, winter to autumn) with a bud still ahead; at the end, the full bloom of a completed cast, a
white hawthorn blossom. The flowers come from tools/manabloom_castbar.py at its supersampled size (256 px), so
nothing is upscaled. Rendered at 4x and reduced.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manabloom_castbar as C  # noqa: E402

K = 4                                   # supersampling
S = 400 * K
RIM = (240, 236, 255)                   # night elf moonflower (Castbar.lua RACE_COLOUR)
FILL = (31, 92, 41)
BACK = (14, 16, 14)
DISC_IN, DISC_OUT = (30, 66, 58), (12, 34, 30)
FAINT, LIT = 0.22, 0.95


def flower(season, tint, px):
    """Tinted petals under the natural centre, from the generator's 256 px drawings, at px."""
    p, c = getattr(C, season)()
    a = np.asarray(p).astype(float)
    a[..., :3] *= np.asarray(tint)
    out = Image.fromarray(a.round().astype("uint8"), "RGBA")
    out.alpha_composite(c)
    return out.resize((px, px), Image.LANCZOS)


def disc():
    """The minimap button's dark forest disc: a soft radial gradient and a pale rim with a faint glow."""
    y, x = np.mgrid[0:S, 0:S]
    r = np.hypot(x - S / 2, y - S / 2) / (S / 2)
    t = np.clip(r / 0.95, 0, 1)[..., None]
    rgb = np.asarray(DISC_IN) * (1 - t) + np.asarray(DISC_OUT) * t
    alpha = np.clip((0.97 - r) * S / 4, 0, 1) * 255
    im = Image.fromarray(np.dstack([rgb, alpha]).round().astype("uint8"), "RGBA")
    ring = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(ring)
    m = int(S * 0.035)
    d.ellipse((m, m, S - m, S - m), outline=(196, 224, 210, 255), width=3 * K)
    glow = ring.filter(ImageFilter.GaussianBlur(5 * K))
    im.alpha_composite(glow)
    im.alpha_composite(ring)
    return im


def mix(c, a, bg=BACK):
    return tuple(int(bg[i] + (c[i] - bg[i]) * a) for i in range(3)) + (255,)


def main(out):
    im = disc()
    d = ImageDraw.Draw(im)
    w, h = int(S * 0.64), int(S * 0.07)                  # the bar: wide and thin, like the game's 208 x 11
    x0, y0 = int(S * 0.12), int(S * 0.5 - h / 2)
    e = 2 * K                                            # the rim, thicker than 1 px so it reads at 400
    p = 0.86                                             # how far the fill has gone
    d.rectangle((x0 - e, y0 - e, x0 + w + e, y0 + h + e), fill=mix(RIM, FAINT))
    d.rectangle((x0, y0, x0 + w, y0 + h), fill=BACK + (255,))
    d.rectangle((x0 - e, y0 - e, x0 + int(w * p), y0), fill=mix(RIM, LIT))          # lit along the fill
    d.rectangle((x0 - e, y0 + h, x0 + int(w * p), y0 + h + e), fill=mix(RIM, LIT))
    d.rectangle((x0 - e, y0 - e, x0, y0 + h + e), fill=mix(RIM, LIT))                # the left edge, lit
    d.rectangle((x0, y0, x0 + int(w * p), y0 + h), fill=FILL + (255,))
    fl = int(h * 1.65)                                   # Castbar.lua's FLOWER
    seasons = ["winter", "spring", "summer", "autumn"]
    for k in range(1, 6):
        cx, cy = x0 + w * k / 6, y0 + h / 2
        if k <= 4:
            f = flower(seasons[k - 1], C.HEAL, fl)
            im.alpha_composite(f, (int(cx - fl / 2), int(cy - fl / 2)))
        else:
            b = C.bud().resize((int(h * 1.25),) * 2, Image.LANCZOS)
            im.alpha_composite(b, (int(cx - b.width / 2), int(cy - b.height / 2)))
    big = flower("spring", C.HEAL, int(h * 3.4))           # the bloom of a completed cast, centred on the end
    im.alpha_composite(big, (int(x0 + w - big.width / 2), int(y0 + h / 2 - big.height / 2)))
    im.resize((400, 400), Image.LANCZOS).save(out)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1])
