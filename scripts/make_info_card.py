#!/usr/bin/env python3
"""Hand-author the neofetch-style info card as an animated SVG.

The contribution graph already covers the numbers, so this panel carries the
things a graph cannot say: what I work on, where, and with what.

Set STATIC=1 to emit a frozen frame, which is handy for local previews that
do not run animations.

Usage:
    python scripts/make_info_card.py
"""

import os
from pathlib import Path

from theme import BLUE, DIM, FG, MONO, PINK, PURPLE, TEAL, YELLOW, card, esc, title_bar

OUT = Path(__file__).resolve().parent.parent / "assets" / "info-card.svg"

WIDTH = 490
PAD = 20
KEY_X = PAD
VAL_X = 122
ROW_H = 21
FIRST_ROW_Y = 66
FONT = 11.5

HOST = "yuval@scojen"

ROWS = [
    ("Role", "Undergraduate Researcher, Scojen Institute", FG),
    ("Study", "Reichman University", FG),
    ("Focus", "Lab automation, synthetic biology", TEAL),
    ("Shipped", "calculab.bio", YELLOW),
    ("", "Molecular biology and biochemistry calculators", DIM),
    ("Languages", "Python, JavaScript, C++", FG),
    ("Frontend", "React, HTML, CSS", FG),
    ("Backend", "Node.js, Express, Flask, Django", FG),
    ("Infra", "Docker, Kubernetes, Linux, Git, CI/CD", FG),
    ("Poster", "FISEB / ILANIT 2026, Eilat", PURPLE),
    ("Location", "Rehovot, Israel", FG),
    ("Contact", "linkedin.com/in/yuvalkolodkin", BLUE),
]

SWATCHES = [DIM, PINK, TEAL, YELLOW, BLUE, PURPLE, "#7dcfff", FG]


def render(static=False):
    swatch_y = FIRST_ROW_Y + len(ROWS) * ROW_H + 10
    height = swatch_y + 40

    animation = (
        "" if static else
        ".r{opacity:0;animation:in .45s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-10px)}"
        "to{opacity:1;transform:none}}"
        "@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1;"
        "transform:none}}"
    )

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" '
        f'aria-label="Profile info card for Yuval Kolodkin Gal">',
        f"<style>{animation}</style>",
        card(WIDTH, height),
        title_bar(WIDTH, HOST),
    ]

    def row(index, body):
        delay = "" if static else f' style="animation-delay:{0.25 + index * 0.06:.2f}s"'
        css = "" if static else ' class="r"'
        return body.replace("__ATTRS__", f"{css}{delay}")

    for index, (key, value, color) in enumerate(ROWS):
        y = FIRST_ROW_Y + index * ROW_H
        parts = []
        if key:
            parts.append(
                f'<text x="{KEY_X}" y="{y}" font-family="{MONO}" '
                f'font-size="{FONT}" fill="{BLUE}" font-weight="600">'
                f"{esc(key)}</text>"
            )
        parts.append(
            f'<text x="{VAL_X}" y="{y}" font-family="{MONO}" font-size="{FONT}" '
            f'fill="{color}">{esc(value)}</text>'
        )
        out.append(row(index, f"<g __ATTRS__>{''.join(parts)}</g>"))

    swatches = "".join(
        f'<rect x="{PAD + step * 22}" y="{swatch_y}" width="18" height="9" '
        f'rx="2" fill="{color}"/>'
        for step, color in enumerate(SWATCHES)
    )
    out.append(row(len(ROWS), f"<g __ATTRS__>{swatches}</g>"))

    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    static = os.environ.get("STATIC") == "1"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(static), encoding="utf-8")
    print(f"{OUT}: {len(ROWS)} rows{' (static)' if static else ''}")


if __name__ == "__main__":
    main()
