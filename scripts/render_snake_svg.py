#!/usr/bin/env python3
"""Render the contribution calendar with a snake eating its way across it.

This is the whole graph, not an extra panel next to one: month labels, day
labels, the legend and the stats footer, with a snake crawling the squares in
a serpentine. Every square it reaches flashes and drops to empty. Once it
leaves the far side the calendar regrows in a wave from the left and the run
starts over.

The snake glides between squares rather than jumping, and the body follows the
head a beat behind, so the turns read as a real snake rather than a marching
block.

Usage:
    python scripts/render_snake_svg.py
"""

import json
from datetime import date
from pathlib import Path

from theme import DIM, FG, HEAT, MONO, card, esc

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "snake.svg"

CELL = 12
GAP = 3
PITCH = CELL + GAP
PAD_L = 18
LABEL_W = 30
GRID_X = PAD_L + LABEL_W
GRID_Y = 40
GRID_H = 7 * PITCH - GAP
WIDTH = 860

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

STEP = 0.045       # seconds per square
REGROW = 3.2       # the calendar growing back once the snake has gone
PAUSE = 1.0        # a beat before it all starts again
LEAD_IN = 6        # squares of run-up before the first column

# Head first, then the body tapering back to the tail. Purple rather than
# blue, so the snake reads against the squares it is eating.
SNAKE = [
    ("#f0e0ff", 12.0),
    ("#e6ccff", 11.5),
    ("#bf91f3", 11.0),
    ("#ab7ce8", 10.0),
    ("#9668d8", 9.0),
    ("#8455c4", 8.0),
    ("#6a43a0", 7.0),
]
FLASH = "#f0e0ff"


def to_columns(days):
    """Group days into week columns, Sunday first (GitHub's layout)."""
    columns, current = [], []
    for day in days:
        # weekday() is Monday=0..Sunday=6. GitHub rows: Sunday=0..Saturday=6.
        row = (date.fromisoformat(day["date"]).weekday() + 1) % 7
        if row == 0 and current:
            columns.append(current)
            current = []
        if not current:
            current = [None] * row
        current.append(day)
    if current:
        columns.append(current)
    return columns[-53:]


def month_labels(columns):
    labels, seen = [], None
    for index, column in enumerate(columns):
        first = next((day for day in column if day), None)
        if not first:
            continue
        point = date.fromisoformat(first["date"])
        key = (point.year, point.month)
        if key != seen:
            if not labels or index - labels[-1][0] >= 3:
                labels.append((index, MONTHS[point.month - 1]))
            seen = key
    return labels


def human_date(iso):
    if not iso:
        return "n/a"
    point = date.fromisoformat(iso)
    return f"{MONTHS[point.month - 1]} {point.day}"


def serpentine(count):
    """Every square in snake order: down one column, up the next."""
    path = []
    for week in range(count):
        rows = range(7) if week % 2 == 0 else range(6, -1, -1)
        for row in rows:
            path.append((week, row))
    return path


def render(payload):
    days = payload.get("days", [])
    stats = payload.get("stats", {})
    columns = to_columns(days)
    weeks = len(columns)
    grid_w = weeks * PITCH - GAP

    legend_y = GRID_Y + GRID_H + 26
    footer_y = legend_y + 28
    height = footer_y + 18

    # Run-up on the left and run-out on the right, so the snake enters and
    # leaves instead of popping into existence mid-grid. The run-out has to be
    # longer than the snake, or the tail parks on the canvas during the regrow
    # instead of following the head off the edge.
    lead_out = len(SNAKE) + 5
    path = [(-LEAD_IN + offset, 0) for offset in range(LEAD_IN)]
    path += serpentine(weeks)
    path += [(weeks + offset, path[-1][1]) for offset in range(lead_out)]

    crawl = len(path) * STEP
    total = crawl + REGROW + PAUSE
    eaten_at = {cell: index for index, cell in enumerate(path)}

    def fraction(seconds):
        return min(max(seconds / total, 0.0), 1.0)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" '
        f'aria-label="{esc(payload.get("total", 0))} contributions in the last '
        f'year, with a snake eating the graph">',
        "<defs>"
        '<filter id="glow" x="-80%" y="-80%" width="260%" height="260%">'
        '<feGaussianBlur stdDeviation="2.6" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/>'
        "</feMerge></filter></defs>",
        card(WIDTH, height),
    ]

    for index, name in month_labels(columns):
        out.append(
            f'<text x="{GRID_X + index * PITCH}" y="30" font-family="{MONO}" '
            f'font-size="10" fill="{DIM}">{name}</text>'
        )

    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(
            f'<text x="{GRID_X - 8}" y="{GRID_Y + row * PITCH + CELL - 2}" '
            f'text-anchor="end" font-family="{MONO}" font-size="10" '
            f'fill="{DIM}">{name}</text>'
        )

    # Squares. Only the ones with contributions animate, so a quiet year stays
    # a small file.
    snap = 0.55 * STEP
    for week, column in enumerate(columns):
        for row, day in enumerate(column):
            x = GRID_X + week * PITCH
            y = GRID_Y + row * PITCH
            level = 0 if day is None else min(int(day.get("level", 0)), len(HEAT) - 1)
            rect = (
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{HEAT[level]}"'
            )
            if level == 0:
                out.append(rect + "/>")
                continue

            bite = eaten_at[(week, row)] * STEP
            back = crawl + (week / max(weeks - 1, 1)) * REGROW
            count = day["count"]
            plural = "" if count == 1 else "s"

            # Hold the colour, flash white as the head arrives, drop to empty,
            # then fade back in on the regrow wave.
            marks = [
                (0.0, HEAT[level]),
                (bite - snap, HEAT[level]),
                (bite, FLASH),
                (bite + snap, HEAT[0]),
                (back, HEAT[0]),
                (min(back + 0.45, total), HEAT[level]),
                (total, HEAT[level]),
            ]
            values = ";".join(colour for _, colour in marks)
            keys = ";".join(f"{fraction(when):.5f}" for when, _ in marks)
            out.append(
                rect + ">"
                f'<animate attributeName="fill" values="{values}" '
                f'keyTimes="{keys}" dur="{total:.2f}s" repeatCount="indefinite"/>'
                f"<title>{count} contribution{plural} on {day['date']}</title>"
                f"</rect>"
            )

    # The snake. Each segment replays the head's path a beat behind, and the
    # motion interpolates between squares instead of stepping, which is what
    # makes it look alive on the turns.
    stops = [fraction(index * STEP) for index in range(len(path))] + [1.0]
    keys = ";".join(f"{stop:.5f}" for stop in stops)

    for offset, (colour, size) in enumerate(SNAKE):
        nudge = (CELL - size) / 2
        xs, ys = [], []
        for index in range(len(path)):
            week, row = path[max(index - offset, 0)]
            xs.append(f"{GRID_X + week * PITCH + nudge:.2f}")
            ys.append(f"{GRID_Y + row * PITCH + nudge:.2f}")
        xs.append(xs[-1])
        ys.append(ys[-1])

        head = ' filter="url(#glow)"' if offset == 0 else ""
        out.append(
            f'<rect width="{size}" height="{size}" rx="{size / 3.6:.2f}" '
            f'fill="{colour}" x="-100" y="{GRID_Y}"{head}>'
            f'<animate attributeName="x" values="{";".join(xs)}" '
            f'keyTimes="{keys}" dur="{total:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="{";".join(ys)}" '
            f'keyTimes="{keys}" dur="{total:.2f}s" repeatCount="indefinite"/>'
            f"</rect>"
        )

    legend_w = len(HEAT) * (CELL + 4) - 4
    right = GRID_X + grid_w
    swatch_x = right - 34 - legend_w
    baseline = legend_y + CELL - 2

    out.append(
        f'<text x="{swatch_x - 10}" y="{baseline}" text-anchor="end" '
        f'font-family="{MONO}" font-size="10" fill="{DIM}">Less</text>'
    )
    for step, colour in enumerate(HEAT):
        out.append(
            f'<rect x="{swatch_x + step * (CELL + 4)}" y="{legend_y}" '
            f'width="{CELL}" height="{CELL}" rx="2.5" fill="{colour}"/>'
        )
    out.append(
        f'<text x="{right}" y="{baseline}" text-anchor="end" '
        f'font-family="{MONO}" font-size="10" fill="{DIM}">More</text>'
    )

    footer = (
        f"{payload.get('total', 0):,} contributions in the last year"
        f"   ·   current streak {stats.get('current_streak', 0)}d"
        f"   ·   longest {stats.get('longest_streak', 0)}d"
        f"   ·   best day {human_date(stats.get('best_day'))}"
        f" ({stats.get('best_day_count', 0)})"
    )
    out.append(
        f'<text x="{PAD_L}" y="{footer_y}" font-family="{MONO}" font-size="11" '
        f'fill="{FG}">{esc(footer)}</text>'
    )

    out.append("</svg>")
    return "\n".join(out) + "\n", total


def main():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    svg, total = render(payload)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"{OUT}: {total:.1f}s loop")


if __name__ == "__main__":
    main()
