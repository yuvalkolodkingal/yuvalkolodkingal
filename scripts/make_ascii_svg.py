#!/usr/bin/env python3
"""Turn an image into a monochrome ASCII portrait that types itself in.

Two design choices keep this readable instead of noisy:

  Monochrome. One light fill colour. Per-character rainbow colouring is what
  makes most ASCII portraits look like static.

  High contrast. The leading space in the ramp means anything bright washes
  out to nothing, so only the subject prints.

Each row is wrapped in a clip that wipes left to right with a small block
cursor riding the edge, staggered top to bottom. The portrait prints once and
freezes. It is SMIL inside the SVG, so GitHub plays it.

Usage:
    python scripts/make_ascii_svg.py                     # helix, no photo needed
    python scripts/make_ascii_svg.py source-prepped.png  # your own portrait
    python scripts/make_ascii_svg.py --preview           # dump the grid as text
"""

import math
import sys
from pathlib import Path

from theme import BLUE, MONO, card, esc

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "ascii-portrait.svg"

# 84 x 47 characters lands the finished SVG at 371 x 372, so the portrait and
# the 490-wide info card add up to the heatmap's 860 and the edges line up.
COLS = 84
ROWS = 47
FONT = 6.8
ADV = FONT * 0.6          # forced per-character advance, see textLength below
LINE_H = 6.8
PAD_X = 14
PAD_Y = 34

INK = "#c7d0f0"

# bright (sparse) -> dark (dense). The leading space clears the background.
RAMP = " .`:-=+*cs#%@"


def image_grid(path, cols=COLS, rows=ROWS):
    """Downsample an image to a character grid using the density ramp."""
    from PIL import Image

    image = Image.open(path).convert("L").resize((cols, rows), Image.LANCZOS)
    pixels = image.load()

    grid = []
    for y in range(rows):
        line = []
        for x in range(cols):
            # 0 = black -> densest glyph, 255 = white -> space
            index = int((255 - pixels[x, y]) / 255 * (len(RAMP) - 1))
            line.append(RAMP[index])
        grid.append("".join(line))
    return grid


def helix_grid(cols=COLS, rows=ROWS):
    """A DNA double helix, drawn straight into the character grid.

    Used when no photo is supplied. Drawing it as characters rather than
    converting a rendered image keeps the strands crisp at this size.
    """
    grid = [[" "] * cols for _ in range(rows)]
    centre = cols / 2
    # A turn is 26 rows tall and 2 x 0.25 x 84 characters wide, which at this
    # font's 0.6 advance ratio comes out close to square. Widen the amplitude
    # or shorten the period and it flattens into horizontal bands.
    amplitude = cols * 0.25
    period = 26.0
    bases = "ATGC"
    labelled = 0

    for row in range(rows):
        phase = row / period * 2 * math.pi
        left = centre + amplitude * math.sin(phase)
        right = centre - amplitude * math.sin(phase)
        # cos gives which strand is nearer the viewer, so the front one prints
        # with a denser glyph than the one behind it.
        depth = math.cos(phase)

        def glyph(front):
            weight = (depth if front else -depth) * 0.5 + 0.5
            return RAMP[max(2, int(2 + weight * (len(RAMP) - 3)))]

        rungs_visible = abs(math.sin(phase)) > 0.18
        if rungs_visible and row % 2 == 0:
            start, end = sorted((int(round(left)), int(round(right))))
            for x in range(start + 2, end - 1):
                if 0 <= x < cols:
                    grid[row][x] = "-" if abs(depth) < 0.75 else "."

        for x, front in ((left, depth > 0), (right, depth <= 0)):
            column = int(round(x))
            if 0 <= column < cols:
                grid[row][column] = glyph(front)
            if 0 <= column + 1 < cols:
                grid[row][column + 1] = glyph(front)

        # Label a base pair where the strands are furthest apart, once per half
        # turn. A pairs with T, G pairs with C.
        if abs(math.sin(phase)) > 0.985:
            index = labelled % 4
            labelled += 1
            partner_index = (index // 2) * 2 + (1 - index % 2)
            slot = int(round(min(left, right))) - 3
            if 0 <= slot < cols:
                grid[row][slot] = bases[index]
            partner = int(round(max(left, right))) + 3
            if 0 <= partner < cols:
                grid[row][partner] = bases[partner_index]

    return ["".join(line).rstrip() for line in grid]


def render(grid):
    width = COLS * ADV + PAD_X * 2
    height = ROWS * LINE_H + PAD_Y + 18

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.2f} {height:.2f}" '
        f'role="img" aria-label="ASCII art portrait">',
        card(width, height),
        f'<text x="{width / 2:.1f}" y="24" text-anchor="middle" '
        f'font-family="{MONO}" font-size="11" fill="#565f89">./portrait.sh</text>',
        "<defs>",
    ]

    step = 0.045
    dur = 0.34

    for index, line in enumerate(grid):
        if not line.strip():
            continue
        y = PAD_Y + index * LINE_H
        run = len(line) * ADV
        begin = index * step
        out.append(
            f'<clipPath id="w{index}">'
            f'<rect x="{PAD_X}" y="{y - LINE_H:.2f}" width="0" '
            f'height="{LINE_H + 2:.2f}">'
            f'<animate attributeName="width" from="0" to="{run:.2f}" '
            f'dur="{dur}s" begin="{begin:.3f}s" fill="freeze"/>'
            f"</rect></clipPath>"
        )

    out.append("</defs>")

    for index, line in enumerate(grid):
        if not line.strip():
            continue
        y = PAD_Y + index * LINE_H
        run = len(line) * ADV
        begin = index * step
        # textLength with lengthAdjust="spacing" pins the character advance so
        # the columns line up whatever monospace font the reader happens to have.
        out.append(
            f'<text clip-path="url(#w{index})" x="{PAD_X}" y="{y:.2f}" '
            f'xml:space="preserve" font-family="{MONO}" font-size="{FONT}" '
            f'fill="{INK}" textLength="{run:.2f}" lengthAdjust="spacing">'
            f"{esc(line)}</text>"
        )
        out.append(
            f'<rect x="{PAD_X}" y="{y - LINE_H + 1:.2f}" width="{ADV:.2f}" '
            f'height="{LINE_H:.2f}" fill="{BLUE}" opacity="0">'
            f'<animate attributeName="x" from="{PAD_X}" '
            f'to="{PAD_X + run:.2f}" dur="{dur}s" begin="{begin:.3f}s"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" '
            f'keyTimes="0;0.02;0.95;1" dur="{dur}s" begin="{begin:.3f}s"/>'
            f"</rect>"
        )

    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    args = [arg for arg in sys.argv[1:] if arg != "--preview"]
    source = args[0] if args else None

    if source and Path(source).exists():
        grid = image_grid(source)
        print(f"portrait from {source}")
    else:
        if source:
            print(f"{source} not found, drawing the helix instead")
        grid = helix_grid()

    if "--preview" in sys.argv:
        print("\n".join(grid))
        return

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(grid), encoding="utf-8")
    print(f"{OUT}: {COLS}x{ROWS} characters")


if __name__ == "__main__":
    main()
