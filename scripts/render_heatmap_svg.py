#!/usr/bin/env python3
"""Render data/contributions.json as an animated heatmap SVG.

The classic 53-week x 7-day calendar of rounded boxes, revealed once with a
diagonal slide-down and then frozen. No looping glow. It plays when the
profile loads and then settles.

Usage:
    python scripts/render_heatmap_svg.py
"""

import json
from datetime import date
from pathlib import Path

from theme import DIM, FG, HEAT, MONO, card, esc

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "contrib-heatmap.svg"

CELL = 12
GAP = 3
PITCH = CELL + GAP
PAD_L = 18
PAD_R = 20
LABEL_W = 30
GRID_X = PAD_L + LABEL_W
GRID_Y = 40
GRID_H = 7 * PITCH - GAP

WIDTH = 860
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def to_columns(days):
    """Group days into week columns, Sunday first (GitHub's layout)."""
    columns = []
    current = []
    for day in days:
        # Python weekday(): Monday=0..Sunday=6. GitHub rows: Sunday=0..Saturday=6.
        row = (date.fromisoformat(day["date"]).weekday() + 1) % 7
        if row == 0 and current:
            columns.append(current)
            current = []
        if not current:
            # Pad the first partial week so the rows stay aligned.
            current = [None] * row
        current.append(day)
    if current:
        columns.append(current)
    return columns[-53:]


def month_labels(columns):
    """One label per month, at the first column that month appears in."""
    labels = []
    seen = None
    for index, column in enumerate(columns):
        first = next((day for day in column if day), None)
        if not first:
            continue
        point = date.fromisoformat(first["date"])
        key = (point.year, point.month)
        if key != seen:
            # Skip a label that would collide with the previous one.
            if not labels or index - labels[-1][0] >= 3:
                labels.append((index, MONTHS[point.month - 1]))
            seen = key
    return labels


def human_date(iso):
    if not iso:
        return "n/a"
    point = date.fromisoformat(iso)
    return f"{MONTHS[point.month - 1]} {point.day}"


def render(payload):
    days = payload.get("days", [])
    stats = payload.get("stats", {})
    columns = to_columns(days)

    grid_w = len(columns) * PITCH - GAP
    legend_y = GRID_Y + GRID_H + 26
    footer_y = legend_y + 28
    height = footer_y + 18

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{height}" viewBox="0 0 {WIDTH} {height}" '
        f'role="img" aria-label="{esc(payload.get("total", 0))} contributions '
        f'in the last year">',
        "<style>",
        # transform-box keeps the scale centred on each box rather than on the
        # SVG origin.
        ".d{opacity:0;transform-box:fill-box;transform-origin:center;"
        "animation:reveal .5s cubic-bezier(.2,.7,.3,1) forwards}",
        "@keyframes reveal{from{opacity:0;transform:translateY(-7px) scale(.55)}"
        "to{opacity:1;transform:none}}",
        ".f{opacity:0;animation:fade .6s ease-out forwards}",
        "@keyframes fade{to{opacity:1}}",
        "@media (prefers-reduced-motion:reduce){"
        ".d,.f{animation:none;opacity:1;transform:none}}",
        "</style>",
        card(WIDTH, height),
    ]

    for index, name in month_labels(columns):
        out.append(
            f'<text class="f" x="{GRID_X + index * PITCH}" y="30" '
            f'font-family="{MONO}" font-size="10" fill="{DIM}" '
            f'style="animation-delay:.05s">{name}</text>'
        )

    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(
            f'<text class="f" x="{GRID_X - 8}" '
            f'y="{GRID_Y + row * PITCH + CELL - 2}" text-anchor="end" '
            f'font-family="{MONO}" font-size="10" fill="{DIM}" '
            f'style="animation-delay:.05s">{name}</text>'
        )

    for week, column in enumerate(columns):
        for row, day in enumerate(column):
            if day is None:
                continue
            x = GRID_X + week * PITCH
            y = GRID_Y + row * PITCH
            level = min(int(day.get("level", 0)), len(HEAT) - 1)
            delay = (week + row * 2) * 0.011
            count = day["count"]
            plural = "" if count == 1 else "s"
            out.append(
                f'<rect class="d" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2.5" fill="{HEAT[level]}" '
                f'style="animation-delay:{delay:.3f}s">'
                f"<title>{count} contribution{plural} on {day['date']}</title>"
                f"</rect>"
            )

    # Legend, right-aligned so "More" ends flush with the grid rather than
    # spilling past the edge of the card.
    legend_w = len(HEAT) * (CELL + 4) - 4
    right = GRID_X + grid_w
    swatch_x = right - 34 - legend_w
    baseline = legend_y + CELL - 2

    out.append(
        f'<text class="f" x="{swatch_x - 10}" y="{baseline}" '
        f'text-anchor="end" font-family="{MONO}" font-size="10" fill="{DIM}" '
        f'style="animation-delay:.9s">Less</text>'
    )
    for step, color in enumerate(HEAT):
        out.append(
            f'<rect class="f" x="{swatch_x + step * (CELL + 4)}" y="{legend_y}" '
            f'width="{CELL}" height="{CELL}" rx="2.5" fill="{color}" '
            f'style="animation-delay:{0.9 + step * 0.05:.2f}s"/>'
        )
    out.append(
        f'<text class="f" x="{right}" y="{baseline}" text-anchor="end" '
        f'font-family="{MONO}" font-size="10" fill="{DIM}" '
        f'style="animation-delay:1.2s">More</text>'
    )

    total = payload.get("total", 0)
    footer = (
        f"{total:,} contributions in the last year"
        f"   ·   current streak {stats.get('current_streak', 0)}d"
        f"   ·   longest {stats.get('longest_streak', 0)}d"
        f"   ·   best day {human_date(stats.get('best_day'))}"
        f" ({stats.get('best_day_count', 0)})"
    )
    out.append(
        f'<text class="f" x="{PAD_L}" y="{footer_y}" font-family="{MONO}" '
        f'font-size="11" fill="{FG}" style="animation-delay:1.1s">'
        f"{esc(footer)}</text>"
    )

    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(payload), encoding="utf-8")
    print(f"{OUT}: {len(payload.get('days', []))} days, {payload.get('total', 0)} contributions")


if __name__ == "__main__":
    main()
