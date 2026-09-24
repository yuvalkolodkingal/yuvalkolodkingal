"""An ASCII portrait that types itself in, row by row.

Three sources: a photo (downsampled through a density ramp), a text file of
ready-made ASCII art, or the built-in DNA double helix when there is nothing
else. Two choices keep the result readable instead of noisy: one ink colour
(per-character rainbows read as static) and a ramp that starts with a space,
so anything bright washes out and only the subject prints.

Each row is wrapped in a clip that wipes left to right with a small block
cursor riding the edge, staggered top to bottom. The portrait prints once and
freezes. It is SMIL inside the SVG, so GitHub plays it.
"""

import math
from pathlib import Path

from theme import MONO, card, esc, svg_open

DEFAULTS = {
    # 84 x 47 characters lands the finished SVG at 371 x 372, so the portrait
    # and a 490-wide info card add up to an 860 row and the edges line up.
    "cols": 84,
    "rows": 47,
    "font": 6.8,
    "title": "./portrait.sh",
    "mode": "helix",
    "ramp": " .`:-=+*cs#%@",
    "invert": False,
}


def image_grid(path, cols, rows, ramp, invert=False):
    """Downsample an image to a character grid using the density ramp."""
    try:
        from PIL import Image
    except ImportError as error:  # pragma: no cover
        raise SystemExit("portrait mode=image needs Pillow: pip install pillow") from error

    image = Image.open(path).convert("L").resize((cols, rows), Image.LANCZOS)
    pixels = image.load()
    grid = []
    for y in range(rows):
        line = []
        for x in range(cols):
            value = pixels[x, y]
            if invert:
                value = 255 - value
            index = int((255 - value) / 255 * (len(ramp) - 1))
            line.append(ramp[index])
        grid.append("".join(line).rstrip())
    return grid


def text_grid(path, cols, rows):
    """Read pre-made ASCII art, clipped and padded to the grid."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    grid = [line[:cols].rstrip() for line in lines[:rows]]
    while len(grid) < rows:
        grid.append("")
    return grid


def helix_grid(cols, rows, ramp):
    """A DNA double helix drawn straight into the character grid."""
    grid = [[" "] * cols for _ in range(rows)]
    centre = cols / 2
    amplitude = cols * 0.25
    period = 26.0
    bases = "ATGC"
    labelled = 0

    for row in range(rows):
        phase = row / period * 2 * math.pi
        left = centre + amplitude * math.sin(phase)
        right = centre - amplitude * math.sin(phase)
        depth = math.cos(phase)

        def glyph(front):
            weight = (depth if front else -depth) * 0.5 + 0.5
            return ramp[max(2, int(2 + weight * (len(ramp) - 3)))]

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


def build_grid(config, root):
    opts = {**DEFAULTS, **config}
    cols, rows, ramp = int(opts["cols"]), int(opts["rows"]), opts["ramp"]
    mode = opts.get("mode", "helix")
    source = opts.get("source")
    if mode == "image":
        path = (root / source) if source else None
        if path and path.exists():
            return image_grid(path, cols, rows, ramp, bool(opts.get("invert")))
        print(f"portrait: {source!r} not found, drawing the helix instead")
    elif mode == "text":
        path = (root / source) if source else None
        if path and path.exists():
            return text_grid(path, cols, rows)
        print(f"portrait: {source!r} not found, drawing the helix instead")
    return helix_grid(cols, rows, ramp)


# CSS that makes the wipe honour prefers-reduced-motion: the clip-path
# property beats the presentation attribute, and display hides the cursors.
REDUCED_CSS = "@media (prefers-reduced-motion:reduce){.w{clip-path:none}.c{display:none}}"


def elements(theme, config, grid, x0, y0, static=False, prefix="w"):
    """The portrait as (defs, body, width, height) to place inside any card.

    Each row types itself in with a clip that wipes left to right and a
    block cursor riding the edge, staggered top to bottom; with static=True
    the rows are simply there.
    """
    opts = {**DEFAULTS, **config}
    cols, rows, font = int(opts["cols"]), int(opts["rows"]), float(opts["font"])
    adv = font * 0.6
    line_h = font
    width = cols * adv
    height = rows * line_h
    ink = theme.colour(config.get("color"), theme.ink)
    step, dur = 0.045, 0.34
    defs, body = [], []
    for index, line in enumerate(grid):
        if not line.strip():
            continue
        y = y0 + index * line_h
        run = len(line) * adv
        begin = index * step
        if not static:
            defs.append(
                f'<clipPath id="{prefix}{index}">'
                f'<rect x="{x0}" y="{y - line_h:.2f}" width="0" height="{line_h + 2:.2f}">'
                f'<animate attributeName="width" from="0" to="{run:.2f}" '
                f'dur="{dur}s" begin="{begin:.3f}s" fill="freeze"/>'
                f"</rect></clipPath>"
            )
        clip = "" if static else f' class="w" clip-path="url(#{prefix}{index})"'
        body.append(
            f'<text{clip} x="{x0}" y="{y:.2f}" xml:space="preserve" '
            f'font-family="{MONO}" font-size="{font}" fill="{ink}" '
            f'textLength="{run:.2f}" lengthAdjust="spacing">{esc(line)}</text>'
        )
        if not static:
            body.append(
                f'<rect class="c" x="{x0}" y="{y - line_h + 1:.2f}" width="{adv:.2f}" '
                f'height="{line_h:.2f}" fill="{theme.accent}" opacity="0">'
                f'<animate attributeName="x" from="{x0}" to="{x0 + run:.2f}" '
                f'dur="{dur}s" begin="{begin:.3f}s"/>'
                f'<animate attributeName="opacity" values="0;1;1;0" '
                f'keyTimes="0;0.02;0.95;1" dur="{dur}s" begin="{begin:.3f}s"/>'
                f"</rect>"
            )
    return "".join(defs), "".join(body), width, height


def render(theme, config, grid, static=False):
    opts = {**DEFAULTS, **config}
    pad_x, pad_y = 14, 34
    defs, body, inner_w, inner_h = elements(theme, config, grid, pad_x, pad_y, static)
    width = inner_w + pad_x * 2
    height = inner_h + pad_y + 18
    label = config.get("label") or "ASCII art portrait"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.2f} {height:.2f}" '
        f'role="img" aria-label="{esc(label)}">',
        f"<style>{REDUCED_CSS}</style>",
        card(theme, width, height),
        f'<text x="{width / 2:.1f}" y="24" text-anchor="middle" '
        f'font-family="{MONO}" font-size="11" fill="{theme.dim}">{esc(opts["title"])}</text>',
        f"<defs>{defs}</defs>",
        body,
        "</svg>",
    ]
    return "\n".join(out) + "\n"
