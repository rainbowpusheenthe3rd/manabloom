r"""Cut a short in-game GIF clip of Manabloom from a screen recording, with names blurred.

  uv run --with pillow --with imageio-ffmpeg python tools/manabloom_clip.py <recording.mp4> <start s> <end s> <out.gif>
      [caption] [x0,y0,x1,y1 crop on the 1080p screen] [scale] [fps]

Default crop: the lower part of the screen at half size, 6 frames a second. Blurs the chat box and the player frame's name, so no character names go
public; check the frames for other players' nameplates before publishing.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FF = imageio_ffmpeg.get_ffmpeg_exe()
TOP = 430                                  # keep y from here down (1080p): below most distant nameplates
BLUR = [(0, 700, 480, 960),                # the chat box
        (505, 752, 645, 782)]              # the player frame's name
FPS, SCALE = 6, 0.5
try:
    FONT = ImageFont.truetype("segoeui.ttf", 18)
except OSError:
    FONT = ImageFont.load_default()


def main(video, start, end, out, caption="", crop=None, scale=None, fps=None, smooth=None):
    box = tuple(int(v) for v in crop.split(",")) if crop else (0, TOP, 1920, 1080)
    k = float(scale) if scale else SCALE
    rate = float(fps) if fps else FPS
    x0, y0, x1, y1 = box
    # Crop in ffmpeg. With smooth, also drop the screen capture's repeated frames (it delivered about 11 new
    # frames a second, 9 Nov 2026) and motion-interpolate in-between frames back up to the frame rate.
    vf = f"crop={x1 - x0}:{y1 - y0}:{x0}:{y0}"
    if smooth:
        vf += f",mpdecimate,minterpolate=fps={rate}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
    else:
        vf += f",fps={rate}"
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([FF, "-v", "error", "-y", "-ss", str(start), "-t", str(float(end) - float(start)), "-i", video,
                        "-vf", vf, str(Path(tmp) / "f_%04d.png")], check=True)
        frames = []
        for p in sorted(Path(tmp).glob("f_*.png")):
            im = Image.open(p).convert("RGB")
            for b in BLUR:  # blur boxes are on the full screen: shift them into the crop
                bx = (b[0] - x0, b[1] - y0, b[2] - x0, b[3] - y0)
                cx = (max(0, bx[0]), max(0, bx[1]), min(im.width, bx[2]), min(im.height, bx[3]))
                if cx[0] < cx[2] and cx[1] < cx[3]:
                    im.paste(im.crop(cx).filter(ImageFilter.GaussianBlur(12)), cx[:2])
            im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
            if caption:
                d = ImageDraw.Draw(im)
                d.rectangle((0, 0, im.width, 26), fill=(20, 18, 24))
                d.text((im.width // 2, 13), caption, fill=(235, 232, 225), anchor="mm", font=FONT)
            frames.append(im if out.endswith(".webp") else im.convert("P", palette=Image.ADAPTIVE, colors=128))
    if out.endswith(".webp"):  # animated WebP: smooth frame rates at a fraction of a GIF's size (9 Nov 2026: 5 fps GIFs were choppy)
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=int(1000 / rate), loop=0, quality=72, method=4)
    else:
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=int(1000 / rate), loop=0, optimize=True)
    print(out, f"{Path(out).stat().st_size / 1024:.0f} KB, {len(frames)} frames")


if __name__ == "__main__":
    main(*sys.argv[1:])
