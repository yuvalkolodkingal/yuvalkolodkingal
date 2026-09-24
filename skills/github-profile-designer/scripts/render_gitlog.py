"""Milestones printed as `git log --oneline --decorate`.

One line per entry from [[timeline]], newest first: a short hash derived
from the entry (stable between builds), decorations in git's colours, the
date, the subject. This is curated history, not the events feed, so it
reads the same on a quiet month as on a busy one.
"""

import hashlib

from theme import MONO, card, esc, svg_open, title_bar

DEFAULTS = {
    "title": "git log --oneline --decorate --date=short",
    "font": 11.5,
    "row_height": 21,
    "branch": "main",
    "limit": 12,
    "empty": "fatal: your current branch 'main' does not have any commits yet",
}


def _hash(entry):
    seed = f"{entry.get('date', '')}|{entry.get('subject', '')}"
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:7]


def render(theme, config, ctx, width=860, static=False):
    opts = {**DEFAULTS, **{k: v for k, v in config.items() if k in DEFAULTS}}
    font, row_h = float(opts["font"]), int(opts["row_height"])
    adv = font * 0.6
    pad = 20
    entries = [e for e in (ctx.get("timeline") or []) if isinstance(e, dict) and e.get("subject")]
    entries = sorted(entries, key=lambda e: str(e.get("date", "")), reverse=True)[: int(opts["limit"])]
    columns = int((width - pad * 2) / adv)
    first_y = 66
    rows = max(len(entries), 1)
    height = first_y + rows * row_h + 12

    label = config.get("label") or ("git log: " + "; ".join(e["subject"] for e in entries) if entries else "git log: no milestones yet")
    css = (
        "" if static else
        ".r{opacity:0;animation:in .3s ease-out forwards}@keyframes in{to{opacity:1}}"
        "@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1}}"
    )
    out = [svg_open(width, height, label), f"<style>{css}</style>", card(theme, width, height), title_bar(theme, width, opts["title"])]

    def attrs(index):
        return "" if static else f' class="r" style="animation-delay:{0.2 + index * 0.07:.2f}s"'

    if not entries:
        out.append(f'<g{attrs(0)}><text x="{pad}" y="{first_y}" font-family="{MONO}" font-size="{font}" fill="{theme.dim}">{esc(opts["empty"])}</text></g>')

    branch = str(opts["branch"])
    for index, entry in enumerate(entries):
        y = first_y + index * row_h
        date = str(entry.get("date", "")) or "----"
        tag = str(entry.get("tag", "") or "")
        decorations = []
        if index == 0:
            decorations.append(("HEAD -> " + branch, theme.teal))
            decorations.append(("origin/" + branch, theme.pink))
        if tag:
            decorations.append(("tag: " + tag, theme.yellow))
        deco_text = ""
        deco_len = 0
        if decorations:
            deco_text = f'<tspan fill="{theme.yellow}"> (</tspan>'
            for i, (name, colour) in enumerate(decorations):
                if i:
                    deco_text += f'<tspan fill="{theme.yellow}">, </tspan>'
                deco_text += f'<tspan fill="{colour}">{esc(name)}</tspan>'
            deco_text += f'<tspan fill="{theme.yellow}">)</tspan>'
            deco_len = 3 + sum(len(n) for n, _ in decorations) + 2 * (len(decorations) - 1)
        room = columns - 7 - 1 - len(date) - 1 - deco_len - 1
        subject = str(entry["subject"])
        if len(subject) > room:
            subject = subject[: max(room - 1, 0)].rstrip() + "…"
        out.append(
            f'<g{attrs(index)}><text x="{pad}" y="{y}" font-family="{MONO}" font-size="{font}" xml:space="preserve">'
            f'<tspan fill="{theme.yellow}">{_hash(entry)}</tspan>'
            f'<tspan fill="{theme.dim}"> {esc(date)}</tspan>'
            f'{deco_text}'
            f'<tspan fill="{theme.fg}"> {esc(subject)}</tspan>'
            f"</text></g>"
        )
    out.append("</svg>")
    return "\n".join(out) + "\n"
