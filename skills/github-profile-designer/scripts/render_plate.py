"""A 96-well plate: the last 96 days of contributions, one well per day.

Eight rows (A to H) by twelve columns, filled column by column the way a
plate is loaded, oldest day at A1. A reader beam sweeps left to right once
and each column lights as the beam passes. It is the one panel on the page
that only a lab would draw, and it is real data.
"""

from theme import MONO, STILL_CSS, card, esc, mix, svg_open, title_bar

DEFAULTS = {
    "title": "plate-reader --last 96d",
    "days": 96,
    "pitch": 20,
    "radius": 6.5,
}

ROWS = "ABCDEFGH"


def render(theme, config, ctx, width=370, static=False):
    opts = {**DEFAULTS, **{k: v for k, v in config.items() if k in DEFAULTS}}
    pitch, radius = float(opts["pitch"]), float(opts["radius"])
    days = list((ctx.get("contributions") or {}).get("days") or [])[-int(opts["days"]):]
    cols = 12
    rows = len(ROWS)
    heat = theme.heat

    origin_x = 20 + 14
    origin_y = 66
    grid_w = (cols - 1) * pitch
    width = max(width, int(origin_x + grid_w + radius + 20))
    height = int(origin_y + (rows - 1) * pitch + radius + 44)
    positive = sum(1 for d in days if d.get("count", 0) > 0)
    read_on = days[-1]["date"] if days else ""

    label = config.get("label") or f"96-well plate: the last {len(days)} days of contributions, {positive} wells positive"
    css = "" if static else STILL_CSS
    out = [svg_open(width, height, label), f"<style>{css}</style>", card(theme, width, height), title_bar(theme, width, opts["title"])]
    if not static:
        out.append(
            "<defs>"
            '<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0" stop-color="{theme.accent}" stop-opacity="0"/>'
            f'<stop offset="0.5" stop-color="{theme.accent}" stop-opacity="0.9"/>'
            f'<stop offset="1" stop-color="{theme.accent}" stop-opacity="0"/>'
            "</linearGradient></defs>"
        )

    for r, name in enumerate(ROWS):
        out.append(
            f'<text x="{origin_x - 14:.1f}" y="{origin_y + r * pitch + 3:.1f}" text-anchor="end" '
            f'font-family="{MONO}" font-size="8" fill="{theme.dim}">{name}</text>'
        )
    for c in range(cols):
        out.append(
            f'<text x="{origin_x + c * pitch:.1f}" y="{origin_y - 14:.1f}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="8" fill="{theme.dim}">{c + 1}</text>'
        )

    empty = mix(theme.bg, theme.border, 0.35)
    motion, still = [], []
    for c in range(cols):
        for r in range(rows):
            index = c * rows + r
            day = days[index] if index < len(days) else None
            cx, cy = origin_x + c * pitch, origin_y + r * pitch
            if day is None:
                out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius}" fill="{empty}" stroke="{theme.border}" stroke-width="1"/>')
                continue
            level = min(int(day.get("level", 0)), len(heat) - 1)
            fill = heat[level] if level else empty
            title = f"<title>{day.get('count', 0)} on {day.get('date', '')}</title>"
            well = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius}" fill="{fill}" stroke="{theme.border}" stroke-width="1"'
            if static or level == 0:
                out.append(well + f">{title}</circle>")
                continue
            begin = 0.3 + c * 0.28
            motion.append(
                well + f' fill-opacity="0.15"><animate attributeName="fill-opacity" from="0.15" to="1" '
                f'dur="0.4s" begin="{begin:.2f}s" fill="freeze"/>{title}</circle>'
            )
            still.append(well + f">{title}</circle>")

    if not static:
        x0 = origin_x - pitch / 2
        x1 = origin_x + (cols - 1) * pitch + pitch / 2
        top = origin_y - radius - 4
        motion.append(
            f'<rect x="{x0:.1f}" y="{top:.1f}" width="10" height="{(rows - 1) * pitch + radius * 2 + 8:.1f}" '
            f'fill="url(#beam)" opacity="0">'
            f'<animate attributeName="x" from="{x0:.1f}" to="{x1:.1f}" dur="3.36s" begin="0.3s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.05;0.95;1" dur="3.36s" begin="0.3s" fill="freeze"/>'
            f"</rect>"
        )
        out.append(f'<g class="m">{"".join(motion)}</g><g class="s">{"".join(still)}</g>')

    caption = f"{len(days)} wells  |  {positive} positive  |  read {read_on}"
    out.append(
        f'<text x="{width / 2:.1f}" y="{height - 16}" text-anchor="middle" font-family="{MONO}" '
        f'font-size="10" fill="{theme.dim}">{esc(caption)}</text>'
    )
    out.append("</svg>")
    return "\n".join(out) + "\n"
