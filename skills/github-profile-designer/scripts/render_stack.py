"""The tools someone uses, printed like `ls -F --color=auto ~/stack`.

A badge wall says the same thing in thirty brand colours. This panel says it
in the theme's: each group is a directory (bold accent, trailing slash), the
tools inside it are the files, indented two columns and coloured by group so
the eye can tell languages from infra without reading. Groups sit side by
side the way ls fills a wide terminal, and wrap to a new row when they do
not fit. Anything the person shipped gets the executable marker, `*`.
"""

from theme import PROMPT_TAIL, MONO, card, esc, prompt, svg_open, title_bar

DEFAULTS = {
    "title": "ls -F --color=auto ~/stack",
    "groups": [],
    "columns": 0,          # groups per row; 0 fits as many as the width allows
    "font": 11.5,
    "row_height": 21,
    "gap": 2,              # blank columns between groups, like ls
    "show_prompt": True,   # the prompt line that follows the listing
    "empty": "ls: cannot access '~/stack': No such file or directory",
}

# One colour per group, cycling; the directory name itself is always accent.
GROUP_COLOURS = ("blue", "teal", "purple", "yellow")


def _groups(config):
    """Normalise the [stack] groups into (name, items, exec) triples."""
    out = []
    for entry in config.get("groups") or DEFAULTS["groups"]:
        if isinstance(entry, dict):
            name = str(entry.get("name", "") or "").strip()
            items = [str(item) for item in (entry.get("items") or []) if str(item).strip()]
            executable = bool(entry.get("exec", False)) or name.lower() == "shipped"
        else:
            name, items, executable = str(entry), [], False
        if name or items:
            out.append((name or "misc", items, executable))
    return out


def _fit(text, columns):
    text = text or ""
    if len(text) <= columns:
        return text
    return text[: max(columns - 3, 0)].rstrip() + "..."


def _pack(groups, total_columns, gap, per_row):
    """Lay groups out left to right, wrapping like ls does when a row is full.

    Returns rows of (group_index, column_offset, width_in_columns). A group
    that is wider than the whole panel gets a row to itself and is clipped.
    """
    widths = []
    for name, items, executable in groups:
        longest = max([len(name) + 1] + [len(item) + 2 + (1 if executable else 0) for item in items])
        widths.append(min(longest, total_columns))
    rows, current, used = [], [], 0
    for index, width in enumerate(widths):
        need = width + (gap if current else 0)
        full = per_row and len(current) >= per_row
        if current and (used + need > total_columns or full):
            rows.append(current)
            current, used = [], 0
            need = width
        current.append((index, used + (need - width), width))
        used += need
    if current:
        rows.append(current)
    return rows


def render(theme, config, ctx, width=860, static=False):
    opts = {**DEFAULTS, **{k: v for k, v in config.items() if k in DEFAULTS}}
    font, row_h, gap = float(opts["font"]), int(opts["row_height"]), int(opts["gap"])
    adv = font * 0.6
    pad = 20
    first_y = 66
    profile = (ctx or {}).get("profile") or {}
    groups = _groups(opts)
    total_columns = max(int((width - pad * 2) / adv), 8)
    try:
        per_row = int(opts["columns"] or 0)  # "auto", "", or 0 all mean fit
    except (TypeError, ValueError):
        per_row = 0
    rows = _pack(groups, total_columns, gap, per_row) if groups else []

    # Visual lines: each row of groups is as tall as its tallest group, with a
    # blank line between rows, then the prompt line after the listing.
    lines = []
    for row in rows:
        lines.append(max(1 + len(groups[index][1]) for index, _, _ in row))
    listing_lines = sum(lines) + max(len(lines) - 1, 0) if lines else 1
    prompt_line = listing_lines + (1 if opts["show_prompt"] else 0)
    height = first_y + prompt_line * row_h + (30 if opts["show_prompt"] else 12)

    label = config.get("label") or (
        "Tech stack: " + "; ".join(f"{name}: {', '.join(items)}" for name, items, _ in groups)
        if groups else "Tech stack: not listed yet"
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

    def cell(x, y, chars, body):
        # textLength pins every viewer's font to the same column grid, so the
        # groups line up whatever monospace face the browser picks.
        return (
            f'<text x="{x:.1f}" y="{y}" font-family="{MONO}" font-size="{font:g}" '
            f'textLength="{len(chars) * adv:.1f}" lengthAdjust="spacing" xml:space="preserve">{body}</text>'
        )

    if not groups:
        out.append(
            f'<g{attrs(0)}><text x="{pad}" y="{first_y}" font-family="{MONO}" font-size="{font:g}" '
            f'fill="{theme.dim}">{esc(opts["empty"])}</text></g>'
        )

    # Each visual line is one reveal group so the listing prints top to
    # bottom across all columns, the way a terminal would.
    line = 0
    for row_index, row in enumerate(rows):
        for local in range(lines[row_index]):
            y = first_y + line * row_h
            parts = []
            for index, offset, columns in row:
                name, items, executable = groups[index]
                x = pad + offset * adv
                colour = theme.colour(GROUP_COLOURS[index % len(GROUP_COLOURS)])
                if local == 0:
                    shown = _fit(name, columns - 1)
                    parts.append(cell(x, y, shown + "/",
                        f'<tspan fill="{theme.accent}" font-weight="700">{esc(shown)}</tspan>'
                        f'<tspan fill="{theme.fg}">/</tspan>'))
                elif local - 1 < len(items):
                    item = _fit(items[local - 1], columns - 2 - (1 if executable else 0))
                    marker = "*" if executable else ""
                    parts.append(cell(x + 2 * adv, y, item + marker,
                        f'<tspan fill="{colour}">{esc(item)}</tspan>'
                        + (f'<tspan fill="{theme.fg}">*</tspan>' if marker else "")))
            out.append(f"<g{attrs(line)}>{''.join(parts)}</g>")
            line += 1
        line += 1  # the blank line between rows of groups

    if opts["show_prompt"]:
        y = first_y + (prompt_line - 1) * row_h
        user, host = str(profile.get("user") or "me"), str(profile.get("host") or "github")
        shell_chars = f"{user}@{host}{PROMPT_TAIL}"
        cursor_x = pad + len(shell_chars) * adv
        cursor_class = "" if static else ' class="k"'
        out.append(
            f"<g{attrs(line)}>"
            f"{cell(pad, y, shell_chars, prompt(theme, user, host, ''))}"
            f'<rect{cursor_class} x="{cursor_x:.1f}" y="{y - font + 2:.1f}" width="{adv:.1f}" height="{font + 2:.1f}" fill="{theme.accent}"/>'
            f"</g>"
        )

    out.append("</svg>")
    return "\n".join(out) + "\n"
