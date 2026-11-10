r"""Draw Manabloom's logo at 400x400: the spring wreath in moonlight white round a bramble flower, on the minimap
button's dark forest disc.

  uv run python tools/manabloom_logo.py <out.png>

Redraws the wreath and the flower at high resolution from the addon's own drawing code (manabloom_textures,
manabloom_motifs) by raising their supersampling before their grids are built, so nothing is upscaled. The spring
wreath draws from the same random sequence as the addon's, after autumn's and winter's draws, so it's the same wreath.
"""
import sys
import types
from pathlib import Path

import numpy as np
from PIL import Image

TOOLS = Path(__file__).resolve().parent


def load(name, old, new):
    """Import a tools module with one line changed (its resolution), as its own namespace."""
    src = (TOOLS / f"{name}.py").read_text(encoding="utf-8")
    assert src.count(old) == 1, old
    mod = types.ModuleType(name + "_hires")
    mod.__file__ = str(TOOLS / f"{name}.py")
    sys.path.insert(0, str(TOOLS))
    exec(compile(src.replace(old, new), mod.__file__, "exec"), mod.__dict__)
    return mod


def main(out):
    tex = load("manabloom_textures", "SIZE, SS = 128, 4", "SIZE, SS = 128, 16")   # 2048 px internally
    tex.autumn(); tex.winter()                                                    # advance to spring's draws
    cv = tex.spring()
    k = 4                                                                         # 2048 -> 512
    a = cv.a.reshape(512, k, 512, k).mean(axis=(1, 3))
    v = (cv.v * cv.a).reshape(512, k, 512, k).mean(axis=(1, 3)) / np.maximum(a, 1e-6)
    hole = (np.abs(np.arange(512) - 256)[None, :] < tex.HOLE * 4) & (np.abs(np.arange(512) - 256)[:, None] < tex.HOLE * 4)
    a = np.where(hole, 0, a)
    white = np.array([1.00, 0.97, 0.96])
    wreath = np.dstack([np.clip(v[..., None] * white, 0, 1), a[..., None]])
    wreath = Image.fromarray((wreath * 255).astype("uint8"), "RGBA")

    mot = load("manabloom_motifs", "SIZE, SS = 64, 4", "SIZE, SS = 64, 32")      # 2048 px internally
    p = mot.flower()
    k = 8                                                                         # 2048 -> 256
    fa = p.a.reshape(256, k, 256, k).mean(axis=(1, 3))
    frgb = (p.rgb * p.a[..., None]).reshape(256, k, 256, k, 3).mean(axis=(1, 3)) / np.maximum(fa[..., None], 1e-6)
    flower = Image.fromarray((np.dstack([np.clip(frgb, 0, 1), fa[..., None]]) * 255).astype("uint8"), "RGBA")

    # the minimap disc: dark forest green, moonlit to the top left, with a pale silver rim
    n = 400
    y, x = np.mgrid[0:n, 0:n] + 0.5 - n / 2
    r = np.hypot(x, y) / (n / 2 - 2)
    light = np.clip(0.5 - (x + y) / n, 0, 1)
    rgb = np.stack([0.05 + 0.06 * light, 0.12 + 0.10 * light, 0.10 + 0.10 * light], axis=-1)
    rim = np.exp(-((r - 0.95) / 0.02) ** 2)[..., None]
    rgb = rgb * (1 - rim) + np.array([0.78, 0.86, 0.80]) * rim
    alpha = np.clip((1 - r) * n / 2, 0, 1)
    logo = Image.fromarray((np.dstack([rgb, alpha]) * 255).astype("uint8"), "RGBA")

    ws = 330
    logo.alpha_composite(wreath.resize((ws, ws), Image.LANCZOS), ((n - ws) // 2, (n - ws) // 2))
    fs = 190
    logo.alpha_composite(flower.resize((fs, fs), Image.LANCZOS), ((n - fs) // 2, (n - fs) // 2))
    logo.save(out)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1])
