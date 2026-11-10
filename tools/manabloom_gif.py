r"""Render docs/manabloom.gif: Manabloom's animations on a mock bar, from the addon's own textures.

  uv run --with pillow python tools/manabloom_gif.py

Four buttons, best spell to worst, in seasonal colours. In turn: the seasons cycling; the bramble ladder climbing
on efficient casts and stepping back on poor ones; leaves falling down the screen edges while a spell is hovered
(one a second, red round to white over twelve, as in game).
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT
OUT = ROOT / "docs" / "manabloom.gif"
W, H = 640, 300
BTN, GAP = 64, 34
RAMPS = {  # as in Manabloom.lua
    "spring": [(0.52, 0.34, 0.24), (0.98, 0.50, 0.70), (0.55, 0.90, 0.42), (1.00, 0.97, 0.96)],
    "summer": [(0.80, 0.10, 0.12), (0.98, 0.55, 0.12), (0.40, 0.82, 0.30), (1.00, 0.98, 0.82)],
    "autumn": [(0.62, 0.10, 0.06), (0.93, 0.40, 0.08), (1.00, 0.76, 0.22), (1.00, 0.95, 0.78)],
    "winter": [(0.62, 0.08, 0.20), (0.52, 0.42, 0.80), (0.40, 0.68, 1.00), (0.97, 0.99, 1.00)],
}
CLASSIC = [(0.92, 0.16, 0.10), (0.62, 0.30, 0.92), (0.30, 0.56, 1.00), (0.94, 0.97, 1.00)]
LADDER = [(), ("bud",), ("bud", "bud"), ("flower", "bud"), ("flower", "flower"), ("berry", "flower"), ("berry", "berry")]
TS = [1.0, 0.69, 0.35, 0.0]                  # the four spells' places on the efficiency scale
ICONS = [(70, 150, 200), (150, 90, 200), (90, 170, 90), (200, 120, 60)]


def colour(ramp, t):
    t = min(max(t, 0), 1) * 3
    i = min(2, int(t))
    f = t - i
    return [ramp[i][k] + (ramp[i + 1][k] - ramp[i][k]) * f for k in range(3)]


def load(name):
    return np.array(Image.open(TEX / f"{name}.tga").convert("RGBA")).astype(float) / 255


def tinted(arr, rgb, size):
    x = arr.copy()
    x[..., :3] *= rgb
    return Image.fromarray((np.clip(x, 0, 1) * 255).astype("uint8")).resize((size, size), Image.LANCZOS)


WREATHS = {s: load(s) for s in RAMPS}
MOTIFS = {m: Image.open(TEX / f"motif_{m}.tga").convert("RGBA") for m in ("bud", "flower", "berry")}
LEAF = load("leaf")


try:
    FONT = ImageFont.truetype("segoeui.ttf", 19)
except OSError:
    FONT = ImageFont.load_default()


def bar(season, step=0, caption=""):
    # the action bar's own warm brown, so the near-black berry reads as it does in game
    img = Image.new("RGBA", (W, H), (58, 48, 40, 255))
    d = ImageDraw.Draw(img)
    x0 = (W - (4 * BTN + 3 * GAP)) // 2
    y0 = H // 2 - BTN // 2 + 10
    for i, t in enumerate(TS):
        x = x0 + i * (BTN + GAP)
        d.rounded_rectangle((x, y0, x + BTN, y0 + BTN), 6, fill=ICONS[i] + (255,), outline=(20, 18, 16, 255), width=2)
        ws = int(BTN * 1.5)
        img.alpha_composite(tinted(WREATHS[season], colour(RAMPS[season], t), ws), (x - (ws - BTN) // 2, y0 - (ws - BTN) // 2))
        m = int(BTN * 0.36)
        for j, name in enumerate(LADDER[step]):
            cy = y0 - int(m * 0.15) if j == 0 else y0 + BTN + int(m * 0.15)
            img.alpha_composite(MOTIFS[name].resize((m, m), Image.LANCZOS), (x + BTN // 2 - m // 2, cy - m // 2))
    d.text((W // 2, 26), caption, fill=(240, 236, 228, 255), anchor="mm", font=FONT)
    return img


def main():
    frames, times = [], []

    def add(img, ms):
        frames.append(img.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=255))
        times.append(ms)

    for s in ("spring", "summer", "autumn", "winter"):                    # 1. the seasons
        add(bar(s, 0, f"{s}: wreaths coloured best to worst"), 1300)
    seq = [(1, "efficient cast: a bud"), (2, "efficient: two buds"), (3, "efficient: flower and bud"),
           (4, "efficient: two flowers"), (5, "efficient: berry and flower"), (6, "efficient: two berries"),
           (5, "poor cast: a step back"), (4, "poor: another step back"), (0, "quiet for a few seconds: it rests")]
    for step, cap in seq:                                                  # 2. the bramble ladder
        add(bar("spring", step, cap), 900)
    rng = np.random.default_rng(4)                                         # 3. falling leaves on hover
    leaves = []
    for k in range(48):
        t = k / 12                                                         # seconds, 12 frames a second
        if k % 12 == 0:
            n = len(leaves)
            side = n % 2
            leaves.append({"t0": t, "x": (rng.uniform(0.02, 0.10) if side == 0 else rng.uniform(0.90, 0.98)) * W,
                           "c": colour(CLASSIC, (n % 12) / 11), "ph": rng.uniform(0, 6.28), "size": rng.integers(18, 26)})
        img = bar("spring", 0, "hovering a spell: leaves fall at the screen's edges, red round to white")
        for lf in leaves:
            age = t - lf["t0"]
            if age < 0:
                continue
            y = -20 + age / 4.0 * (H + 40)
            x = lf["x"] + math.sin(age * 1.3 + lf["ph"]) * 14
            leaf = tinted(LEAF, lf["c"], lf["size"]).rotate(math.degrees(lf["ph"] + age * 1.5), expand=True)
            leaf.putalpha(leaf.getchannel("A").point(lambda v: int(v * 0.85)))
            img.alpha_composite(leaf, (int(x - leaf.width / 2), int(y - leaf.height / 2)))
        add(img, 83)
    frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=times, loop=0, optimize=True, disposal=2)
    print(OUT, f"{OUT.stat().st_size / 1024:.0f} KB, {len(frames)} frames, {sum(times) / 1000:.1f} s")


if __name__ == "__main__":
    main()
