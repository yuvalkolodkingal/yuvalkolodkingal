"""The contribution calendar with a snake eating its way across it.

This is the whole graph, not an extra panel next to one: month labels, day
labels, the legend and the stats footer, with a snake crawling the squares in
a serpentine. Every square it reaches flashes and drops to empty. Once it
leaves the far side the calendar regrows in a wave from the left and the run
starts over. The snake glides between squares rather than jumping, and the
body follows the head a beat behind, so the turns read as a real snake.
"""

from datetime import date

from theme import MONO, STILL_CSS, card, esc, svg_open

CELL = 12
GAP = 3
PITCH = CELL + GAP
PAD_L = 18
LABEL_W = 30
GRID_X = PAD_L + LABEL_W
GRID_Y = 40
GRID_H = 7 * PITCH - GAP

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

DEFAULTS = {
    "step": 0.045,    # seconds per square
    "regrow": 3.2,    # the calendar growing back once the snake has gone
    "pause": 1.0,     # a beat before it all starts again
    "lead_in": 6,     # squares of run-up before the first column
    "footer": True,
    "cached_note": "",  # e.g. "2026-09-01" when the calendar could not be refreshed
}


def to_columns(days):
    """Group days into week columns, Sunday first (GitHub's layout)."""
    columns, current = [], []
    for day in days:
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


def render(theme, config, payload, width=860):
    opts = {**DEFAULTS, **{k: v for k, v in config.items() if k in DEFAULTS}}
    step, regrow, pause, lead_in = opts["step"], opts["regrow"], opts["pause"], int(opts["lead_in"])
    heat = theme.heat
    snake = theme.snake
    flash = theme.flash

    days = payload.get("days", [])
    stats = payload.get("stats", {})
    columns = to_columns(days)
    weeks = len(columns)
    grid_w = weeks * PITCH - GAP

    legend_y = GRID_Y + GRID_H + 26
    footer_y = legend_y + 28
    height = footer_y + 18 if opts["footer"] else legend_y + 24

    lead_out = len(snake) + 5
    path = [(-lead_in + offset, 0) for offset in range(lead_in)]
    path += serpentine(weeks)
    path += [(weeks + offset, path[-1][1]) for offset in range(lead_out)]

    crawl = len(path) * step
    total = crawl + regrow + pause
    eaten_at = {cell: index for index, cell in enumerate(path)}

    def fraction(seconds):
        return min(max(seconds / total, 0.0), 1.0)

    label = f"Contribution calendar for the last year with a snake eating the active days; {payload.get('total', 0)} contributions"
    out = [
        svg_open(width, height, label),
        f"<style>{STILL_CSS}</style>",
        "<defs>"
        '<filter id="glow" x="-80%" y="-80%" width="260%" height="260%">'
        '<feGaussianBlur stdDeviation="2.6" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/>'
        "</feMerge></filter></defs>",
        card(theme, width, height),
    ]

    for index, name in month_labels(columns):
        out.append(
            f'<text x="{GRID_X + index * PITCH}" y="30" font-family="{MONO}" '
            f'font-size="10" fill="{theme.dim}">{name}</text>'
        )
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(
            f'<text x="{GRID_X - 8}" y="{GRID_Y + row * PITCH + CELL - 2}" '
            f'text-anchor="end" font-family="{MONO}" font-size="10" '
            f'fill="{theme.dim}">{name}</text>'
        )

    snap = 0.55 * step
    motion, still = [], []
    for week, column in enumerate(columns):
        for row, day in enumerate(column):
            x = GRID_X + week * PITCH
            y = GRID_Y + row * PITCH
            level = 0 if day is None else min(int(day.get("level", 0)), len(heat) - 1)
            rect = (
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{heat[level]}"'
            )
            if level == 0:
                out.append(rect + "/>")
                continue
            still.append(rect + "/>")

            bite = eaten_at[(week, row)] * step
            back = crawl + (week / max(weeks - 1, 1)) * regrow
            count = day["count"]
            plural = "" if count == 1 else "s"
            marks = [
                (0.0, heat[level]),
                (bite - snap, heat[level]),
                (bite, flash),
                (bite + snap, heat[0]),
                (back, heat[0]),
                (min(back + 0.45, total), heat[level]),
                (total, heat[level]),
            ]
            values = ";".join(colour for _, colour in marks)
            keys = ";".join(f"{fraction(when):.5f}" for when, _ in marks)
            motion.append(
                rect + ">"
                f'<animate attributeName="fill" values="{values}" '
                f'keyTimes="{keys}" dur="{total:.2f}s" repeatCount="indefinite"/>'
                f"<title>{count} contribution{plural} on {day['date']}</title>"
                f"</rect>"
            )

    stops = [fraction(index * step) for index in range(len(path))] + [1.0]
    keys = ";".join(f"{stop:.5f}" for stop in stops)
    for offset, (colour, size) in enumerate(snake):
        nudge = (CELL - size) / 2
        xs, ys = [], []
        for index in range(len(path)):
            week, row = path[max(index - offset, 0)]
            xs.append(f"{GRID_X + week * PITCH + nudge:.2f}")
            ys.append(f"{GRID_Y + row * PITCH + nudge:.2f}")
        xs.append(xs[-1])
        ys.append(ys[-1])
        head = ' filter="url(#glow)"' if offset == 0 else ""
        motion.append(
            f'<rect width="{size}" height="{size}" rx="{size / 3.6:.2f}" '
            f'fill="{colour}" x="-100" y="{GRID_Y}"{head}>'
            f'<animate attributeName="x" values="{";".join(xs)}" '
            f'keyTimes="{keys}" dur="{total:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y" values="{";".join(ys)}" '
            f'keyTimes="{keys}" dur="{total:.2f}s" repeatCount="indefinite"/>'
            f"</rect>"
        )

    out.append(f'<g class="m">{"".join(motion)}</g><g class="s">{"".join(still)}</g>')

    legend_w = len(heat) * (CELL + 4) - 4
    right = GRID_X + grid_w
    swatch_x = right - 34 - legend_w
    baseline = legend_y + CELL - 2
    out.append(
        f'<text x="{swatch_x - 10}" y="{baseline}" text-anchor="end" '
        f'font-family="{MONO}" font-size="10" fill="{theme.dim}">Less</text>'
    )
    for index, colour in enumerate(heat):
        out.append(
            f'<rect x="{swatch_x + index * (CELL + 4)}" y="{legend_y}" '
            f'width="{CELL}" height="{CELL}" rx="2.5" fill="{colour}"/>'
        )
    out.append(
        f'<text x="{right}" y="{baseline}" text-anchor="end" '
        f'font-family="{MONO}" font-size="10" fill="{theme.dim}">More</text>'
    )

    if opts["footer"]:
        footer = (
            f"{payload.get('total', 0):,} contributions in the last year"
            f"  |  streak {stats.get('current_streak', 0)}d (longest {stats.get('longest_streak', 0)}d)"
            f"  |  best {human_date(stats.get('best_day'))} ({stats.get('best_day_count', 0)})"
        )
        note = ""
        if opts.get("cached_note"):
            note = f'<tspan fill="{theme.dim}">  (cached {esc(opts["cached_note"])})</tspan>'
        out.append(
            f'<text x="{PAD_L}" y="{footer_y}" font-family="{MONO}" font-size="11" '
            f'fill="{theme.fg}">{esc(footer)}{note}</text>'
        )

    out.append("</svg>")
    return "\n".join(out) + "\n", total
