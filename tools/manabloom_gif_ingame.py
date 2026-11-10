r"""Build docs/manabloom.gif from a screen recording of Manabloom in game, plus the drawn ladder.

  uv run --with pillow --with imageio-ffmpeg python tools/manabloom_gif_ingame.py <recording.mp4> <times.json>

times.json names the moments in the recording (seconds): {"spring": 10, "summer": 66, "autumn": 86,
"winter": 106, "tooltip": 70, "leaves": [62, 80], "fight": [228, 248], "bear": [252, 276]}. Every crop keeps clear
of character names (unit frames, nameplates, chat): the action bars, the minimap tooltip, a screen edge.
The bud -> flower -> berry ladder is drawn from the addon's textures (manabloom_gif.bar), for a clean progression.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manabloom_gif  # noqa: E402
from manabloom_gif import bar  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "manabloom.gif"
W, H = 640, 360
try:
    FONT = ImageFont.truetype("segoeui.ttf", 19)
except OSError:
    FONT = ImageFont.load_default()
BARS = (370, 938, 670, 1080)        # the first four buttons of both bars, wreaths and motifs
TOOLTIP = (1408, 22, 1692, 224)      # the minimap button's tooltip
EDGE = (0, 60, 420, 760)             # the left screen edge, open world, where leaves fall, clear of names
FF = imageio_ffmpeg.get_ffmpeg_exe()


def grab(video, t, tmp):
    p = Path(tmp) / f"t{t:.2f}.png"
    if not p.exists():
        subprocess.run([FF, "-v", "error", "-y", "-ss", f"{t}", "-i", video, "-frames:v", "1", str(p)], check=True)
    return Image.open(p).convert("RGB")


def drawn(img):
    """A drawn 640x300 frame, centred on a card of the bar's brown, at its own size (no stretching)."""
    c = Image.new("RGB", (W, H), (58, 48, 40))
    c.paste(img.convert("RGB").crop((0, 0, 640, 300)), ((W - 640) // 2, (H - 300) // 2))
    return c


def card(img, caption, scale=None):
    """The crop centred on a dark card, scaled to fit, with a caption above."""
    c = Image.new("RGB", (W, H), (24, 22, 30))
    s = scale or min((W - 40) / img.width, (H - 70) / img.height)
    im = img.resize((int(img.width * s), int(img.height * s)), Image.LANCZOS)
    c.paste(im, ((W - im.width) // 2, 50 + (H - 60 - im.height) // 2))
    ImageDraw.Draw(c).text((W // 2, 24), caption, fill=(225, 222, 235), anchor="mm", font=FONT)
    return c


def main(video, times):
    frames, ms = [], []

    def add(img, d):
        frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=128))
        ms.append(d)

    with tempfile.TemporaryDirectory() as tmp:
        for season, label in (("spring", "spring: a vine with blossom"), ("summer", "summer: oxeye daisies"),
                              ("autumn", "autumn: oak leaves and acorns"), ("winter", "winter: frost")):
            add(card(grab(video, times[season], tmp).crop(BARS), f"{label}  (in game, best spell white)"), 1400)
        steps = [(1, "an efficient cast: a bud"), (2, "two buds"), (3, "flower and bud"), (4, "two flowers"),
                 (5, "berry and flower"), (6, "two berries"), (5, "a poor cast: a step back"), (0, "a few quiet seconds: it rests")]
        for step, cap in steps:
            add(drawn(bar("spring", step, cap)), 850)
        a, b = times["fight"]
        t = a
        while t <= b:
            add(card(grab(video, t, tmp).crop(BARS), "in a real fight: the bramble on every wreath"), 600)
            t += 1.5
        add(card(grab(video, times["tooltip"], tmp).crop(TOOLTIP), "the minimap leaf: your spells ranked by mana efficiency"), 2600)
        # the falling leaves are too small and dark to read in the recording (rain, a dark screen edge), so this
        # part is the drawn version: manabloom_gif's leaf sequence (its frames after the 4 seasons and 9 ladder steps)
        drawn_gif = Path(tmp) / "drawn.gif"
        manabloom_gif.OUT = drawn_gif
        manabloom_gif.main()
        with Image.open(drawn_gif) as g:
            for i in range(13, g.n_frames, 2):
                g.seek(i)
                add(drawn(g), 166)
        a, b = times["bear"]
        t = a
        while t <= b:
            add(card(grab(video, t, tmp).crop(BARS), "Bear Form: the bar becomes bear abilities, which cost no mana: no wreaths"), 500)
            t += 2.0
    frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=ms, loop=0, optimize=True)
    print(OUT, f"{OUT.stat().st_size / 1024:.0f} KB, {len(frames)} frames, {sum(ms) / 1000:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1], json.loads(Path(sys.argv[2]).read_text()))
