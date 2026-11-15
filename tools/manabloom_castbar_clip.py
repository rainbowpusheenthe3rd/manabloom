r"""Cut the cast bar clip for the front page and CurseForge from a screen recording: chosen segments, cropped tight
on the cast bar (no names: the crop holds only the bar, its spell name and the bloom), doubled in size, each with
a caption, as an animated WebP (smooth, small), an MP4, and a GIF at a third of the frame rate (8 fps, 48 colours, to stay small) for CurseForge.

  uv run --no-project --with pillow --with imageio-ffmpeg python tools/manabloom_castbar_clip.py REC.mp4 OUT_STEM

Segments and the crop are below (from castbar_2026-11-15_b.mp4, recorded at 1920 x 1080 in Darkshore).
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FF = imageio_ffmpeg.get_ffmpeg_exe()
CROP = (820, 866, 1110, 940)          # x0, y0, x1, y1 on the 1080p screen: the bar, its name, the bloom at its end
SCALE, FPS = 2, 24
SEGMENTS = [                          # (start s, end s, caption)
    (0.0, 13.0, "Damage flowers violet; a finished cast blooms at the end"),
    (20.5, 24.2, "Heals flower white"),
    (86.6, 90.0, "Break a cast and it wilts"),
]
CAP_H = 34
try:
    FONT = ImageFont.truetype("segoeui.ttf", 18)
except OSError:
    FONT = ImageFont.load_default()


def frames(video, start, end, tmp):
    x0, y0, x1, y1 = CROP
    out = Path(tmp) / f"seg_{start:.1f}"
    out.mkdir()
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-ss", str(start), "-to", str(end), "-i", video,
                    "-vf", f"crop={x1 - x0}:{y1 - y0}:{x0}:{y0},scale=iw*{SCALE}:ih*{SCALE}:flags=lanczos,fps={FPS}",
                    str(out / "f_%04d.png")], check=True)
    return sorted(out.glob("f_*.png"))


def main(video, stem):
    stem = Path(stem)
    pics = []
    with tempfile.TemporaryDirectory() as tmp:
        for start, end, caption in SEGMENTS:
            for p in frames(video, start, end, tmp):
                im = Image.open(p).convert("RGB")
                canvas = Image.new("RGB", (im.width, im.height + CAP_H), (16, 18, 16))
                canvas.paste(im, (0, 0))
                d = ImageDraw.Draw(canvas)
                w = d.textlength(caption, font=FONT)
                d.text(((im.width - w) / 2, im.height + 6), caption, fill=(232, 232, 224), font=FONT)
                pics.append(canvas)
        pics[0].save(stem.with_suffix(".webp"), save_all=True, append_images=pics[1:], duration=int(1000 / FPS),
                     loop=0, quality=80, method=4)
        half = [p.quantize(colors=48, method=Image.Quantize.MEDIANCUT) for p in pics[::3]]    # CurseForge: a GIF, 8 fps
        half[0].save(stem.with_suffix(".gif"), save_all=True, append_images=half[1:], duration=int(3000 / FPS),
                     loop=0, optimize=True)
        seq = Path(tmp) / "all"
        seq.mkdir()
        for i, im in enumerate(pics):
            im.save(seq / f"a_{i:05d}.png")
        subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i",
                        str(seq / "a_%05d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                        str(stem.with_suffix(".mp4"))], check=True)
    print(stem.with_suffix(".webp"), stem.with_suffix(".mp4"), len(pics), "frames")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
