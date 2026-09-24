"""The neofetch card: the portrait on the left, system facts on the right.

Exactly what `neofetch` prints, with the person as the machine: OS is the
role, Host the university, Kernel the focus, Uptime the account age,
Packages the repositories, Memory the contributions. Values can carry
placeholders like {repos} or {uptime} that the daily build fills from the
cached GitHub data; a placeholder with no data prints as -- in dim.

The portrait types itself in (SMIL wipe, once) and the rows slide in with
a CSS stagger, so reduced motion shows everything at once.
"""

from datetime import date, datetime

import render_portrait
from theme import MONO, card, esc, svg_open, title_bar

DEFAULTS = {
    "title": "neofetch",
    "font": 11.5,
    "row_height": 19,
    "swatches": True,
    "portrait_width": 370,
}


def _age(iso, today):
    """'1 year, 2 months' from an ISO date, the way uptime would put it."""
    if not iso:
        return ""
    try:
        start = date.fromisoformat(iso[:10])
    except ValueError:
        return ""
    months = (today.year - start.year) * 12 + today.month - start.month
    if today.day < start.day:
        months -= 1
    months = max(months, 0)
    years, months = divmod(months, 12)
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months or not years:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    return ", ".join(parts)


def live_values(ctx):
    """Every placeholder the rows may use, from the cached data files."""
    github = ctx.get("github") or {}
    contrib = ctx.get("contributions") or {}
    totals = github.get("totals") or {}
    user = github.get("user") or {}
    stats = contrib.get("stats") or {}
    languages = github.get("languages") or []
    build = ctx.get("build") or {}
    try:
        today = datetime.strptime(build.get("generated_at", ""), "%Y-%m-%d %H:%M UTC").date()
    except ValueError:
        today = date.today()

    def number(value):
        return f"{int(value):,}" if value not in (None, "") else ""

    return {
        "uptime": _age(user.get("created_at", ""), today),
        "repos": number(totals.get("repos")),
        "original_repos": number(totals.get("original_repos")),
        "stars": number(totals.get("stars")),
        "forks": number(totals.get("forks")),
        "followers": number(totals.get("followers")),
        "following": number(totals.get("following")),
        "contributions": number(contrib.get("total")),
        "streak": f"{stats['current_streak']}d" if "current_streak" in stats else "",
        "longest_streak": f"{stats['longest_streak']}d" if "longest_streak" in stats else "",
        "active_days": number(stats.get("active_days")),
        "best_day": f"{stats.get('best_day', '')} ({stats.get('best_day_count', 0)})" if stats.get("best_day") else "",
        "top_language": languages[0]["name"] if languages else "",
        "languages": ", ".join(l["name"] for l in languages[:3]),
        "language_shares": ", ".join(f"{l['name']} {l['percent']:g}%" for l in languages[:3]),
        "built": build.get("generated_at", ""),
        "location": user.get("location", ""),
    }


def fill(value, values):
    """Replace {placeholders}; returns (text, complete)."""
    complete = True
    out = str(value)
    for key, live in values.items():
        token = "{" + key + "}"
        if token in out:
            if live:
                out = out.replace(token, live)
            else:
                out = out.replace(token, "--")
                complete = False
    return out, complete


def render(theme, config, ctx, width=860, static=False):
    opts = {**DEFAULTS, **{k: v for k, v in config.items() if k in DEFAULTS}}
    font, row_h = float(opts["font"]), int(opts["row_height"])
    adv = font * 0.6
    profile = ctx.get("profile", {})
    user, host = profile.get("user", "me"), profile.get("host", "github")
    rows = list(config.get("rows") or [])
    values = live_values(ctx)

    portrait_cfg = ctx.get("portrait_config") or {}
    grid = ctx.get("portrait_grid") or []
    show_portrait = bool(grid)
    portrait_w = int(opts["portrait_width"]) if show_portrait else 0

    pad = 20
    left = portrait_w + 14 if show_portrait else pad
    first_y = 66
    key_w = max((len(r.get("key", "")) for r in rows if isinstance(r, dict)), default=6) + 2
    value_x = left + key_w * adv
    columns = int((width - pad - value_x) / adv)

    swatch_rows = 2 if opts["swatches"] else 0
    text_h = (2 + len(rows)) * row_h + swatch_rows * 16 + 12
    height = max(first_y + text_h, 372 if show_portrait else 0)

    label = config.get("label") or f"neofetch for {profile.get('name', user)}: " + "; ".join(
        f"{r.get('key')}: {fill(r.get('value', ''), values)[0]}" for r in rows if isinstance(r, dict) and r.get("key")
    )
    css = (
        "" if static else
        ".r{opacity:0;animation:in .45s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}"
        "@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1;transform:none}}"
        + render_portrait.REDUCED_CSS
    )
    out = [svg_open(width, height, label), f"<style>{css}</style>", card(theme, width, height), title_bar(theme, width, opts["title"])]

    if show_portrait:
        # Centre the grid in the left column, under the title bar.
        p_opts = {**render_portrait.DEFAULTS, **portrait_cfg}
        p_font = float(p_opts["font"])
        grid_w = int(p_opts["cols"]) * p_font * 0.6
        grid_h = int(p_opts["rows"]) * p_font
        x0 = max(14, (portrait_w - grid_w) / 2 + 6)
        y0 = 52 + max(0, (height - 52 - 12 - grid_h) / 2) + p_font
        defs, body, _, _ = render_portrait.elements(theme, portrait_cfg, grid, x0, y0, static)
        out.append(f"<defs>{defs}</defs>{body}")

    def attrs(index):
        return "" if static else f' class="r" style="animation-delay:{0.35 + index * 0.06:.2f}s"'

    # Header: user@host and a dashed rule the width of it, like neofetch.
    head = f"{user}@{host}"
    out.append(
        f'<g{attrs(0)}><text x="{left:.1f}" y="{first_y}" font-family="{MONO}" font-size="{font}" font-weight="600">'
        f'<tspan fill="{theme.accent}">{esc(user)}</tspan><tspan fill="{theme.fg}">@</tspan>'
        f'<tspan fill="{theme.accent}">{esc(host)}</tspan></text>'
        f'<text x="{left:.1f}" y="{first_y + row_h}" font-family="{MONO}" font-size="{font}" fill="{theme.dim}">{"-" * len(head)}</text></g>'
    )

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        y = first_y + (index + 2) * row_h
        key = str(row.get("key", ""))
        value, complete = fill(row.get("value", ""), values)
        colour = theme.colour(row.get("color"), theme.fg) if complete else theme.dim
        if len(value) > columns:
            value = value[: columns - 1].rstrip() + "…"
        parts = []
        if key:
            parts.append(
                f'<text x="{left:.1f}" y="{y}" font-family="{MONO}" font-size="{font}" '
                f'fill="{theme.accent}" font-weight="600">{esc(key)}:</text>'
            )
        parts.append(
            f'<text x="{value_x:.1f}" y="{y}" font-family="{MONO}" font-size="{font}" fill="{colour}">{esc(value)}</text>'
        )
        out.append(f"<g{attrs(index + 1)}>{''.join(parts)}</g>")

    if opts["swatches"]:
        y = first_y + (len(rows) + 2) * row_h + 2
        colours = [theme.bg, theme.red, theme.green, theme.yellow, theme.blue, theme.purple, theme.teal, theme.fg]
        blocks = "".join(
            f'<rect x="{left + step * 22:.1f}" y="{y}" width="18" height="9" rx="2" fill="{colour}" stroke="{theme.border}" stroke-width="0.5"/>'
            for step, colour in enumerate(colours)
        )
        blocks += "".join(
            f'<rect x="{left + step * 22:.1f}" y="{y + 13}" width="18" height="9" rx="2" fill="{colour}" opacity="0.7" stroke="{theme.border}" stroke-width="0.5"/>'
            for step, colour in enumerate(colours)
        )
        out.append(f"<g{attrs(len(rows) + 1)}>{blocks}</g>")

    out.append("</svg>")
    return "\n".join(out) + "\n"
