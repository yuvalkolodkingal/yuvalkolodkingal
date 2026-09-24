"""Recent public activity, printed like `git log --oneline`.

One line per event from the public events feed: a short hash-like id in
yellow, a tag for the kind of event, the summary, the title or commit
message in dim, and how long ago it happened on the right. Rows print in
one by one, then the panel ends with a pager-style (END) marker.
"""

from theme import MONO, card, esc, svg_open, title_bar

DEFAULTS = {
    "limit": 10,
    "title": "git log --oneline --all",
    "font": 11.5,
    "row_height": 21,
    "empty": "no public activity in the last 90 days",
}

TAGS = {
    "push": ("push", "green"),
    "pr": ("pull", "purple"),
    "issue": ("issue", "orange"),
    "create": ("new", "teal"),
    "star": ("star", "yellow"),
    "fork": ("fork", "cyan"),
    "release": ("tag", "pink"),
    "comment": ("talk", "dim"),
    "review": ("review", "purple"),
    "public": ("open", "teal"),
}


def _fit(text, columns):
    text = text or ""
    if len(text) <= columns:
        return text
    return text[: max(columns - 1, 0)].rstrip() + "…"


def render(theme, config, github, width=860, static=False):
    opts = {**DEFAULTS, **{k: v for k, v in config.items() if k in DEFAULTS}}
    font, row_h = float(opts["font"]), int(opts["row_height"])
    adv = font * 0.6
    pad = 20
    events = list((github or {}).get("activity") or [])[: int(opts["limit"])]
    columns = int((width - pad * 2) / adv)
    first_y = 66
    rows = max(len(events), 1)
    height = first_y + rows * row_h + 30

    label = config.get("label") or (
        f"Recent GitHub activity: {len(events)} events" if events else "Recent GitHub activity: none yet"
    )
    animation = (
        "" if static else
        ".r{opacity:0;animation:in .4s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
        ".k{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        "@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1;transform:none}.k{animation:none}}"
    )
    out = [
        svg_open(width, height, label),
        f"<style>{animation}</style>",
        card(theme, width, height),
        title_bar(theme, width, opts["title"]),
    ]

    def attrs(index):
        if static:
            return ""
        return f' class="r" style="animation-delay:{0.2 + index * 0.07:.2f}s"'

    if not events:
        out.append(
            f'<g{attrs(0)}><text x="{pad}" y="{first_y}" font-family="{MONO}" font-size="{font}" '
            f'fill="{theme.dim}">{esc(opts["empty"])}</text></g>'
        )

    for index, event in enumerate(events):
        y = first_y + index * row_h
        tag, colour_name = TAGS.get(event.get("type", ""), ("event", "dim"))
        colour = theme.colour(colour_name)
        ago = event.get("ago", "")
        sha = (event.get("sha") or "0000000")[-7:]
        summary = event.get("summary", "")
        detail = event.get("detail", "")
        times = event.get("count", 1)
        if times > 1 and event.get("type") != "push":
            summary = f"{summary} ×{times}"
        # Column budget: sha(7) space tag(6) space summary ... ago right-aligned.
        left_cols = 7 + 1 + 6 + 1
        right_cols = len(ago) + 2
        body_cols = columns - left_cols - right_cols
        body = _fit(summary, body_cols)
        room = body_cols - len(body) - 2
        detail_text = _fit(detail, room) if room > 12 and detail else ""
        x_tag = pad + 8 * adv
        x_body = pad + left_cols * adv
        x_detail = x_body + (len(body) + 2) * adv
        parts = [
            f'<text x="{pad}" y="{y}" font-family="{MONO}" font-size="{font}" fill="{theme.yellow}">{esc(sha)}</text>',
            f'<text x="{x_tag:.1f}" y="{y}" font-family="{MONO}" font-size="{font}" fill="{colour}" font-weight="600">{esc(tag.ljust(6))}</text>',
            f'<text x="{x_body:.1f}" y="{y}" font-family="{MONO}" font-size="{font}" fill="{theme.fg}" xml:space="preserve">{esc(body)}</text>',
        ]
        if detail_text:
            parts.append(
                f'<text x="{x_detail:.1f}" y="{y}" font-family="{MONO}" font-size="{font}" fill="{theme.dim}">{esc(detail_text)}</text>'
            )
        parts.append(
            f'<text x="{width - pad}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="{font}" fill="{theme.dim}">{esc(ago)}</text>'
        )
        out.append(f"<g{attrs(index)}>{''.join(parts)}</g>")

    end_y = first_y + rows * row_h
    cursor_class = "" if static else ' class="k"'
    out.append(
        f'<g{attrs(rows)}>'
        f'<rect x="{pad}" y="{end_y - font + 2:.1f}" width="{adv * 5:.1f}" height="{font + 2:.1f}" fill="{theme.fg}"/>'
        f'<text x="{pad + adv * 0.3:.1f}" y="{end_y}" font-family="{MONO}" font-size="{font}" fill="{theme.bg}" font-weight="600">(END)</text>'
        f'<rect{cursor_class} x="{pad + adv * 5.6:.1f}" y="{end_y - font + 2:.1f}" width="{adv:.1f}" height="{font + 2:.1f}" fill="{theme.accent}"/>'
        f"</g>"
    )
    out.append("</svg>")
    return "\n".join(out) + "\n"
