"""Render the PayFlow card and hero image.

    python tools/make_payflow_card.py

Writes assets/img/payflow-card.png at 1600x900. The card grid crops to
16/9, so everything that matters sits inside the safe area with room to
spare.

The figure is a diagram, not a screenshot: it is drawn here rather than
captured so the numbers cannot go stale silently. They are checked
against the interpreter before drawing -- if PayFlow ever stops printing
8.91 for this program, this script fails instead of shipping a figure
that lies.
"""

import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "payflow-card.png"
PAYFLOW = ROOT / "assets" / "payflow"

W, H = 1600, 900

BG = (14, 14, 18)
PANEL = (22, 22, 28)
EDGE = (48, 50, 58)
TEXT = (229, 225, 231)
DIM = (132, 148, 149)
CYAN = (0, 245, 255)
GREEN = (78, 222, 163)
PURPLE = (208, 188, 255)
ORANGE = (255, 183, 107)

FONTS = pathlib.Path("C:/Windows/Fonts")


def font(name, size):
    path = FONTS / name
    if not path.exists():
        raise SystemExit(f"font not found: {path}")
    return ImageFont.truetype(str(path), size)


def verify_numbers():
    """Run the program in the figure and confirm it still prints 8.91."""
    src = """
plan Pro { price: 9.99 USD; trial: 7 days; }
fn netRevenue(p: money, cut: percent, vat: percent) -> money {
  return p split cut split vat;
}
paywall S { default { show Pro at netRevenue(9.99 USD, 3%, 8%); } }
"""
    code = (
        "import sys, json; sys.path.insert(0, r'%s');"
        "from _runner import run_source;"
        "print(json.loads(run_source(sys.stdin.read(), 'US'))['output'])"
    ) % PAYFLOW
    r = subprocess.run([sys.executable, "-c", code], input=src,
                       capture_output=True, text=True)
    got = r.stdout.strip()
    if "8.91 USD" not in got:
        raise SystemExit(
            "the figure claims 8.91 USD but the interpreter printed:\n"
            f"  {got or r.stderr.strip()}"
        )
    print(f"  verified against the interpreter: {got}")


def main():
    verify_numbers()

    mono = lambda s: font("CascadiaMono.ttf", s)
    sans_b = lambda s: font("segoeuib.ttf", s)

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # ---- terminal panel ----------------------------------------------------
    px0, py0, px1, py1 = 90, 96, W - 90, H - 96
    d.rounded_rectangle([px0, py0, px1, py1], radius=18, fill=PANEL, outline=EDGE, width=2)

    # title bar
    bar_h = 62
    d.rounded_rectangle([px0, py0, px1, py0 + bar_h], radius=18, fill=(28, 28, 35))
    d.rectangle([px0, py0 + bar_h - 18, px1, py0 + bar_h], fill=(28, 28, 35))
    d.line([px0, py0 + bar_h, px1, py0 + bar_h], fill=EDGE, width=2)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([px0 + 28 + i * 26, py0 + 24, px0 + 42 + i * 26, py0 + 38], fill=c)
    d.text((px0 + 132, py0 + 20), "payflow", font=mono(22), fill=DIM)
    d.text((px0 + 132 + 96, py0 + 20), "· split, per-step rounding", font=mono(22), fill=(96, 104, 116))

    x = px0 + 56
    y = py0 + bar_h + 46
    fm = mono(31)
    lh = 46

    def line(parts, indent=0):
        nonlocal y
        cx = x + indent
        for text, colour in parts:
            d.text((cx, y), text, font=fm, fill=colour)
            cx += d.textlength(text, font=fm)
        y += lh

    line([("fn ", PURPLE), ("netRevenue", CYAN),
          ("(p: ", TEXT), ("money", GREEN), (", cut: ", TEXT), ("percent", GREEN),
          (", vat: ", TEXT), ("percent", GREEN), (") ", TEXT)])
    line([("-> ", TEXT), ("money", GREEN), (" {", TEXT)], indent=56)
    line([("return", PURPLE), (" p ", TEXT), ("split", ORANGE), (" cut ", TEXT),
          ("split", ORANGE), (" vat;", TEXT)], indent=56)
    line([("}", TEXT)])

    y += 22
    line([("$ ", DIM), ("payflow  9.99 USD split 3% split 8%", TEXT)])
    y += 14

    # ---- the two candidate rules ------------------------------------------
    small = mono(26)
    big = font("CascadiaMono.ttf", 44)

    box_w = px1 - 56 - x

    row_y = y + 8
    d.rounded_rectangle([x, row_y, x + box_w, row_y + 96], radius=12,
                        fill=(18, 34, 30), outline=(45, 110, 90), width=2)
    d.text((x + 28, row_y + 16), "per-step", font=small, fill=GREEN)
    d.text((x + 28, row_y + 50), "9.99 -> 9.69 -> 8.91", font=small, fill=DIM)
    d.text((x + 560, row_y + 26), "8.91 USD", font=big, fill=GREEN)

    # The badge marks which of the two rules the language actually runs.
    bx = x + box_w - 300
    d.rounded_rectangle([bx, row_y + 28, bx + 268, row_y + 68], radius=20,
                        fill=(24, 52, 44), outline=(78, 222, 163), width=2)
    d.text((bx + 30, row_y + 36), "IMPLEMENTED", font=mono(24), fill=GREEN)

    row_y += 122
    d.rounded_rectangle([x, row_y, x + box_w, row_y + 96], radius=12,
                        fill=(26, 22, 22), outline=(78, 58, 58), width=2)
    d.text((x + 28, row_y + 16), "once-at-end", font=small, fill=(190, 140, 140))
    d.text((x + 28, row_y + 50), "9.99 * 0.97 * 0.92", font=small, fill=(120, 100, 100))
    d.text((x + 560, row_y + 26), "8.92 USD", font=big, fill=(190, 140, 140))
    d.text((bx + 30, row_y + 36), "REJECTED", font=mono(24), fill=(150, 110, 110))

    # ---- footer strip ------------------------------------------------------
    d.text((x, py1 - 62), "A DSL FOR SUBSCRIPTION PLANS, PAYWALL ROUTING AND REVENUE SPLITS",
           font=mono(24), fill=(104, 116, 122))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    print(f"  wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
