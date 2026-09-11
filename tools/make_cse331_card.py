"""Render the CSE 331 card and hero image.

    python tools/make_cse331_card.py

Writes assets/img/cse331-card.png at 1600x900.

Two panels: the MIPS assembly written for assignment 1 on the left, and
the same algorithm's output coming out of the processor built in
assignment 3 on the right. That is the whole point of the repository in
one picture -- the program and the machine it runs on were both written
for the same course.

The figure is drawn rather than screenshotted, and the numbers in it are
the ones the assignment 1 brief gives for "Hello World 123". They are
checked by two testbenches in the repository; if they ever stop matching,
the tests fail there rather than this figure quietly going stale.
"""

import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "cse331-card.png"

W, H = 1600, 900

BG      = (14, 14, 18)
PANEL   = (22, 22, 28)
PANEL2  = (18, 20, 26)
EDGE    = (48, 50, 58)
TEXT    = (229, 225, 231)
DIM     = (132, 148, 149)
FAINT   = (96, 104, 116)
CYAN    = (0, 245, 255)
GREEN   = (78, 222, 163)
PURPLE  = (208, 188, 255)
ORANGE  = (255, 183, 107)

FONTS = pathlib.Path("C:/Windows/Fonts")


def font(name, size):
    p = FONTS / name
    if not p.exists():
        raise SystemExit(f"font not found: {p}")
    return ImageFont.truetype(str(p), size)


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    mono   = lambda s: font("CascadiaMono.ttf", s)
    mono_b = lambda s: font("CascadiaMono.ttf", s)

    # ---- header ------------------------------------------------------
    d.text((88, 60), "CSE 331  ·  COMPUTER ORGANIZATION", font=mono(26), fill=FAINT)

    gap   = 40
    top   = 120
    bot   = H - 150
    panel_w = (W - 176 - gap) // 2
    lx, rx = 88, 88 + panel_w + gap

    # ================= left panel: the assembly =======================
    d.rounded_rectangle([lx, top, lx + panel_w, bot], radius=16,
                        fill=PANEL, outline=EDGE, width=2)
    d.rounded_rectangle([lx, top, lx + panel_w, top + 54], radius=16, fill=(28, 28, 35))
    d.rectangle([lx, top + 36, lx + panel_w, top + 54], fill=(28, 28, 35))
    d.line([lx, top + 54, lx + panel_w, top + 54], fill=EDGE, width=2)
    d.text((lx + 26, top + 16), "1 ·  text_analyzer.asm", font=mono(22), fill=PURPLE)
    d.text((lx + panel_w - 96, top + 16), "MARS", font=mono(22), fill=FAINT)

    asm = [
        [("countVowels", CYAN), (":", TEXT)],
        [("        addi  ", TEXT), ("$sp, $sp, -12", TEXT)],
        [("        sw    ", TEXT), ("$ra, 0($sp)", TEXT)],
        [("", TEXT)],
        [("loop:   lb    ", TEXT), ("$t0, 0($s2)", TEXT)],
        [("        beq   ", TEXT), ("$t0, $zero, done", TEXT)],
        [("        move  ", TEXT), ("$a0, $t0", TEXT)],
        [("        jal   ", ORANGE), ("isVowel", CYAN)],
        [("        beq   ", TEXT), ("$v0, $zero, next", TEXT)],
        [("        addi  ", TEXT), ("$s3, $s3, 1", TEXT)],
        [("next:   addi  ", TEXT), ("$s2, $s2, 1", TEXT)],
        [("        j     ", ORANGE), ("loop", CYAN)],
        [("", TEXT)],
        [("done:   move  ", TEXT), ("$v0, $s3", TEXT)],
        [("        jr    ", ORANGE), ("$ra", TEXT)],
    ]
    fm = mono(25)
    y = top + 86
    for parts in asm:
        x = lx + 30
        for txt, col in parts:
            d.text((x, y), txt, font=fm, fill=col)
            x += d.textlength(txt, font=fm)
        y += 36

    # ================= right panel: the processor =====================
    d.rounded_rectangle([rx, top, rx + panel_w, bot], radius=16,
                        fill=PANEL2, outline=EDGE, width=2)
    d.rounded_rectangle([rx, top, rx + panel_w, top + 54], radius=16, fill=(28, 28, 35))
    d.rectangle([rx, top + 36, rx + panel_w, top + 54], fill=(28, 28, 35))
    d.line([rx, top + 54, rx + panel_w, top + 54], fill=EDGE, width=2)
    d.text((rx + 26, top + 16), "3 ·  mips_cpu.v", font=mono(22), fill=GREEN)
    d.text((rx + panel_w - 216, top + 16), "single-cycle", font=mono(22), fill=FAINT)

    y = top + 86
    d.text((rx + 30, y), "$ vvp tb_text.vvp", font=mono(25), fill=DIM)
    y += 48
    d.text((rx + 30, y), "the assignment 1 algorithm,", font=mono(24), fill=FAINT)
    y += 32
    d.text((rx + 30, y), "on the assignment 3 CPU", font=mono(24), fill=FAINT)
    y += 54

    d.text((rx + 30, y), '"Hello World 123"', font=mono(26), fill=TEXT)
    y += 50

    counts = [("characters", "15"), ("vowels", "3"), ("consonants", "7"),
              ("digits", "3"), ("spaces", "2")]
    fc = mono(26)
    for name, val in counts:
        d.text((rx + 56, y), name, font=fc, fill=DIM)
        d.text((rx + 300, y), val, font=mono_b(26), fill=GREEN)
        y += 38

    y += 18
    bx = rx + 30
    d.rounded_rectangle([bx, y, bx + 250, y + 44], radius=22,
                        fill=(24, 52, 44), outline=GREEN, width=2)
    d.text((bx + 34, y + 8), "RESULT: PASS", font=mono(24), fill=GREEN)

    # ---- the arrow between them --------------------------------------
    ax = lx + panel_w + gap // 2
    ay = (top + bot) // 2
    d.line([ax - 13, ay, ax + 13, ay], fill=GREEN, width=3)
    d.polygon([(ax + 16, ay), (ax + 4, ay - 8), (ax + 4, ay + 8)], fill=GREEN)

    # ---- footer strip -------------------------------------------------
    fy = bot + 44
    items = [
        ("1", "ASSEMBLY", PURPLE),
        ("2", "GATE-LEVEL DATAPATH", CYAN),
        ("3", "MIPS32 CPU", GREEN),
        ("4", "SEQUENTIAL MULTIPLIER", ORANGE),
    ]
    x = 88
    ff = mono(24)
    for num, label, col in items:
        d.text((x, fy), num, font=mono(24), fill=col)
        d.text((x + 26, fy), label, font=ff, fill=FAINT)
        x += 26 + d.textlength(label, font=ff) + 54

    d.text((W - 340, fy), "370 CHECKS", font=mono(24), fill=GREEN)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    print(f"  wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
