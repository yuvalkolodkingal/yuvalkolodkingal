"""The neofetch-style info card: key/value rows that slide in one by one.

The contribution graph covers the numbers, so this panel carries the things
a graph cannot say: what the person works on, where, and with what.
"""

from theme import MONO, card, esc, svg_open, title_bar

DEFAULTS = {"row_height": 21, "font": 11.5, "value_x": 122, "pad": 20}


def render(theme, config, profile, width=490, static=False):
    rows = list(config.get("rows") or [])
    if not rows:
        raise ValueError("[info] needs at least one row")
    opts = {**DEFAULTS, **{k: v for k, v in config.items() if k in DEFAULTS}}
    pad, value_x, row_h, font = opts["pad"], opts["value_x"], opts["row_height"], opts["font"]
    first_row_y = 66
    title = config.get("title") or f"{profile.get('user', 'me')}@{profile.get('host', 'github')}"
    label = config.get("label") or f"Profile info card for {profile.get('name', profile.get('username', ''))}"
    key_colour = theme.colour(config.get("key_color"), theme.accent)

    swatch_names = config.get("swatches") or ["dim", "pink", "teal", "yellow", "blue", "purple", "cyan", "fg"]
    swatches = [theme.colour(name) for name in swatch_names]
    show_swatches = config.get("show_swatches", True)

    swatch_y = first_row_y + len(rows) * row_h + 10
    height = swatch_y + (40 if show_swatches else 14)

    animation = (
        "" if static else
        ".r{opacity:0;animation:in .45s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-10px)}"
        "to{opacity:1;transform:none}}"
        "@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1;"
        "transform:none}}"
    )

    out = [
        svg_open(width, height, label),
        f"<style>{animation}</style>",
        card(theme, width, height),
        title_bar(theme, width, title),
    ]

    def row(index, body):
        delay = "" if static else f' style="animation-delay:{0.25 + index * 0.06:.2f}s"'
        css = "" if static else ' class="r"'
        return body.replace("__ATTRS__", f"{css}{delay}")

    for index, entry in enumerate(rows):
        if isinstance(entry, dict):
            key, value, colour = entry.get("key", ""), entry.get("value", ""), entry.get("color", "fg")
        else:
            key, value = (list(entry) + ["", ""])[:2]
            colour = entry[2] if len(entry) > 2 else "fg"
        y = first_row_y + index * row_h
        parts = []
        if key:
            parts.append(
                f'<text x="{pad}" y="{y}" font-family="{MONO}" '
                f'font-size="{font}" fill="{key_colour}" font-weight="600">'
                f"{esc(key)}</text>"
            )
        parts.append(
            f'<text x="{value_x}" y="{y}" font-family="{MONO}" font-size="{font}" '
            f'fill="{theme.colour(colour)}">{esc(value)}</text>'
        )
        out.append(row(index, f"<g __ATTRS__>{''.join(parts)}</g>"))

    if show_swatches:
        blocks = "".join(
            f'<rect x="{pad + step * 22}" y="{swatch_y}" width="18" height="9" '
            f'rx="2" fill="{colour}"/>'
            for step, colour in enumerate(swatches)
        )
        out.append(row(len(rows), f"<g __ATTRS__>{blocks}</g>"))

    out.append("</svg>")
    return "\n".join(out) + "\n"
