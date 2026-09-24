"""Language share across the person's repositories, printed like `du -sh`.

One row per language: percentage, a bar that grows in from the left, the
name. Colours come from GitHub's linguist palette when known (Python is
always that blue) so the bar reads the same as the language chip on a
repository page; unknown languages cycle through the theme accents.
"""

from theme import MONO, card, esc, mix, svg_open, title_bar

DEFAULTS = {
    "limit": 6,
    "title": "du -sh languages/* | sort -rh",
    "font": 11.5,
    "row_height": 24,
    "empty": "no language data yet",
}


def render(theme, config, github, width=860, static=False):
    opts = {**DEFAULTS, **{k: v for k, v in config.items() if k in DEFAULTS}}
    font, row_h = float(opts["font"]), int(opts["row_height"])
    adv = font * 0.6
    pad = 20
    languages = list((github or {}).get("languages") or [])[: int(opts["limit"])]
    cycle = [theme.blue, theme.purple, theme.teal, theme.yellow, theme.pink, theme.green, theme.orange, theme.cyan]

    first_y = 66
    rows = max(len(languages), 1)
    height = first_y + rows * row_h + 12
    top = max((entry.get("percent", 0) for entry in languages), default=0) or 1

    label = config.get("label") or (
        "Languages by bytes across repositories: "
        + ", ".join(f"{e['name']} {e['percent']}%" for e in languages)
        if languages else "Languages: no data yet"
    )
    animation = (
        "" if static else
        ".r{opacity:0;animation:in .4s ease-out forwards}"
        "@keyframes in{from{opacity:0}to{opacity:1}}"
        ".b{transform:scaleX(0);transform-origin:left;animation:grow .9s cubic-bezier(.2,.8,.2,1) forwards}"
        "@keyframes grow{to{transform:scaleX(1)}}"
        "@media (prefers-reduced-motion:reduce){.r,.b{animation:none;opacity:1;transform:none}}"
    )
    out = [
        svg_open(width, height, label),
        f"<style>{animation}</style>",
        card(theme, width, height),
        title_bar(theme, width, opts["title"]),
    ]

    def attrs(index, cls="r"):
        if static:
            return ""
        return f' class="{cls}" style="animation-delay:{0.2 + index * 0.09:.2f}s"'

    if not languages:
        out.append(
            f'<g{attrs(0)}><text x="{pad}" y="{first_y}" font-family="{MONO}" font-size="{font}" '
            f'fill="{theme.dim}">{esc(opts["empty"])}</text></g>'
        )

    name_col = max((len(e["name"]) for e in languages), default=8)
    bar_x = pad + (7 + 1 + name_col + 2) * adv
    bar_w = width - pad - bar_x
    for index, entry in enumerate(languages):
        y = first_y + index * row_h
        colour = entry.get("color") or cycle[index % len(cycle)]
        percent = float(entry.get("percent", 0))
        w = max(bar_w * percent / 100.0, 3)
        out.append(
            f"<g{attrs(index)}>"
            f'<text x="{pad + 6 * adv:.1f}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="{font}" fill="{theme.fg}">{percent:.1f}%</text>'
            f'<text x="{pad + 8 * adv:.1f}" y="{y}" font-family="{MONO}" font-size="{font}" fill="{colour}" font-weight="600">{esc(entry["name"])}</text>'
            f'<rect x="{bar_x:.1f}" y="{y - font + 1:.1f}" width="{bar_w:.1f}" height="{font + 1:.1f}" rx="3" fill="{mix(theme.bg, theme.border, 0.7)}"/>'
            f'<rect{attrs(index, "b")} x="{bar_x:.1f}" y="{y - font + 1:.1f}" width="{w:.1f}" height="{font + 1:.1f}" rx="3" fill="{colour}"/>'
            f"</g>"
        )
    out.append("</svg>")
    return "\n".join(out) + "\n"
