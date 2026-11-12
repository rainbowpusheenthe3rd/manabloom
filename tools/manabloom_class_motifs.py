r"""Write each class's ladder motifs for the addon: motif_<class>_<stage>.tga (64x64, stages 1 to 3).

  uv run --no-project --with numpy --with pillow python tools/manabloom_class_motifs.py [check dir]

The art is the flat class ladders the author chose on 10 Nov 2026 (manabloom_pivot_draft.stage_icon). The druid
keeps the shipped bramble (motif_bud/flower/berry.tga, from manabloom_motifs.py), so it isn't written here.

With a check dir, also writes <check dir>/class_check.png: every class's six-step ladder on a wreath at bar size
(a 36 px button), in the worst, middle and best efficiency colours, to check each stage reads at that size.
"""
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manabloom_pivot_draft as P  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SIZE = 64
CLASSES = ["Priest", "Mage", "Warlock", "Shaman", "Paladin", "Hunter"]
# Manabloom.lua's LADDER: which stage shows north and south at each of the six steps
LADDER = [(1,), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)]
RAMP = [(0.92, 0.16, 0.10), (0.30, 0.56, 1.00), (0.94, 0.97, 1.00)]   # worst, middle, best (classic colours)


def tga(path, im):
    """32-bit uncompressed TGA, top-left origin: the same layout as manabloom_motifs.tga."""
    a = np.asarray(im.convert("RGBA"))
    head = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, im.width, im.height, 32, 0x28)
    path.write_bytes(head + a[..., [2, 1, 0, 3]].tobytes())


def motif(cls, stage):
    """Stage 1 to 3 of a class's ladder, at 64 px."""
    return P.stage_icon(cls, stage - 1).resize((SIZE, SIZE), Image.LANCZOS)


def check(out):
    """Each class's six steps on a 36 px button with its wreath, in three efficiency colours, at 1x and 3x."""
    btn, scale, m = 36, 1.5, round(36 * 0.36)
    wreath = Image.open(ROOT / "autumn.tga").convert("RGBA")
    cell = int(btn * scale) + 6
    sheet = Image.new("RGB", (cell * 6 * 3 + 40, cell * len(CLASSES) + 10), (30, 26, 24))
    for r, cls in enumerate(CLASSES):
        icons = {s: motif(cls, s).resize((m, m), Image.LANCZOS) for s in (1, 2, 3)}
        for c, rgb in enumerate(RAMP):
            w = wreath.resize((int(btn * scale),) * 2, Image.LANCZOS)
            tint = np.asarray(w).astype(float)
            tint[..., :3] *= np.asarray(rgb)
            w = Image.fromarray(tint.round().astype("uint8"), "RGBA")
            for k, step in enumerate(LADDER):
                x, y = 10 + (c * 6 + k) * cell + (c * 10), 5 + r * cell
                tile = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
                o = (cell - btn) // 2
                tile.paste((70, 95, 60, 255), (o, o, o + btn, o + btn))
                tile.alpha_composite(w, ((cell - w.width) // 2, (cell - w.height) // 2))
                for i, s in enumerate(step):                    # north on the top edge, south on the bottom
                    cy = o - m * 0.15 if i == 0 else o + btn + m * 0.15
                    tile.alpha_composite(icons[s], (cell // 2 - m // 2, int(cy - m / 2)))
                sheet.paste(tile, (x, y), tile)
    sheet.save(out / "class_check.png")
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(out / "class_check_3x.png")
    print(out / "class_check.png")


def main():
    for cls in CLASSES:
        for s in (1, 2, 3):
            path = ROOT / f"motif_{cls.lower()}_{s}.tga"
            tga(path, motif(cls, s))
            print(path)
    if len(sys.argv) > 1:
        out = Path(sys.argv[1])
        out.mkdir(parents=True, exist_ok=True)
        check(out)


if __name__ == "__main__":
    main()
