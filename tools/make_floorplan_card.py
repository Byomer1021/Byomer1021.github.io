"""Render the floorplan-parser card and hero image.

    python tools/make_floorplan_card.py

Writes assets/img/floorplan-card.png at 1600x900.

Two panels: a raster floor plan from the CVC-FP test split as it comes in,
and the same plan as the parser returns it -- walls, doors, windows, rooms
and the room-door graph. Both images are produced by the project's own
scripts (scripts/sekiller.py in the floorplan-parser repo) and copied here
as assets/img/floorplan-input.png and floorplan-output.png; this script only
lays them out, it does not redraw any result.
"""

import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"
OUT = IMG / "floorplan-card.png"

W, H = 1600, 900

BG = (14, 14, 18)
EDGE = (48, 50, 58)
TEXT = (229, 225, 231)
DIM = (132, 148, 149)
CYAN = (0, 245, 255)
GREEN = (78, 222, 163)

FONTS = pathlib.Path("C:/Windows/Fonts")


def font(name, size):
    p = FONTS / name
    if not p.exists():
        return ImageFont.load_default()
    return ImageFont.truetype(str(p), size)


def panel(src, box):
    """Fit `src` inside `box` (x0, y0, x1, y1) on a light paper panel."""
    x0, y0, x1, y1 = box
    paper = Image.new("RGB", (x1 - x0, y1 - y0), (247, 245, 240))
    im = Image.open(src).convert("RGB")
    pad = 18
    scale = min((paper.width - 2 * pad) / im.width, (paper.height - 2 * pad) / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    paper.paste(im, ((paper.width - im.width) // 2, (paper.height - im.height) // 2))
    return paper


def main():
    card = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(card)
    mono = lambda s: font("CascadiaMono.ttf", s)  # noqa: E731

    top, bottom, gap, side = 110, 860, 40, 40
    width = (W - 2 * side - gap) // 2
    boxes = [
        (side, top, side + width, bottom),
        (side + width + gap, top, W - side, bottom),
    ]
    labels = [
        ("INPUT", "a raster plan, pixels only", DIM),
        ("OUTPUT", "walls · doors · windows · rooms · graph", CYAN),
    ]
    for (x0, y0, x1, y1), src, (tag, sub, color) in zip(
        boxes, ("floorplan-input.png", "floorplan-output.png"), labels
    ):
        card.paste(panel(IMG / src, (x0, y0, x1, y1)), (x0, y0))
        d.rectangle((x0, y0, x1 - 1, y1 - 1), outline=EDGE, width=2)
        d.text((x0, 40), tag, font=mono(30), fill=color)
        d.text((x0 + 150, 46), sub, font=mono(22), fill=DIM)

    d.text((side, bottom + 8), "no learned models: thresholding, morphology, Hough, "
           "template matching, watershed", font=mono(18), fill=GREEN)
    card.save(OUT)
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
