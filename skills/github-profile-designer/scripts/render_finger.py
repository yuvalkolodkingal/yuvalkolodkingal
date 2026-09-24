"""The contact card, printed like `finger <user>` on a BSD box.

A profile ends with how to reach the person, and finger already prints
exactly that: login and name on one line, where they sit and what shell
they run on the next, then office, mail and whatever else, an "On since"
line that doubles as the build stamp, and the .plan file underneath. The
panel copies that output line for line so the page closes the same way it
opened, as one session on one host.

An SVG shown through <img> cannot carry a clickable link, so the mail and
site rows are only painted blue; the README prints a Markdown link line
under the card for the real anchors.
"""

from datetime import date, datetime

from theme import MONO, card, esc, svg_open, title_bar

DEFAULTS = {
    "title": "",
    "login": "",
    "name": "",
    "directory": "",
    "shell": "/bin/zsh",
    "office": "",
    "mail": "",
    "site": "",
    "fields": (),
    "plan": (),
    "font": 11.5,
    "row_height": 21,
    "column": 40,       # where the second column of the top block starts
    "tty": "pts/0",
    "origin": "github-actions",
    "no_plan": "No Plan.",
}

# Keys whose values are addresses; they get the link colour.
LINK_KEYS = {"mail", "site", "url", "web", "www", "email", "e-mail", "homepage", "blog"}


def _fit(content, columns):
    content = content or ""
    if columns <= 0:
        return ""
    if len(content) <= columns:
        return content
    return content[: max(columns - 3, 0)].rstrip() + "..."


def _on_since(build):
    """`Wed Sep 24 06:17 (UTC)` from the build stamp, today at midnight without one."""
    stamp = str((build or {}).get("generated_at") or "").strip()
    if len(stamp) > 10 and stamp[10] == "T":     # ISO 8601 separator
        stamp = stamp[:10] + " " + stamp[11:]
    if stamp.endswith("Z"):
        stamp = stamp[:-1] + " UTC"
    zone = "UTC"
    parts = stamp.split()
    if len(parts) >= 3 and parts[-1].isalpha():
        zone = parts[-1].upper()
    when = None
    try:
        when = datetime.strptime(stamp[:16], "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            day = date.fromisoformat(stamp[:10])
            when = datetime(day.year, day.month, day.day)
        except ValueError:
            when = datetime.combine(date.today(), datetime.min.time())
    return f"{when.strftime('%a %b')} {when.day:2d} {when.strftime('%H:%M')} ({zone})"


def render(theme, config, ctx, width=860, static=False):
    config = config or {}
    opts = {**DEFAULTS, **{k: v for k, v in config.items() if k in DEFAULTS}}
    font, row_h = float(opts["font"]), int(opts["row_height"])
    adv = font * 0.6
    pad = 20
    first_y = 66
    columns = int((width - pad * 2) / adv)
    column = int(opts["column"])

    profile = (ctx or {}).get("profile") or {}
    github_user = ((ctx or {}).get("github") or {}).get("user") or {}

    login = str(opts["login"] or profile.get("user") or profile.get("username") or github_user.get("login") or "me")
    name = str(opts["name"] or profile.get("name") or github_user.get("name") or login)
    directory = str(opts["directory"] or f"/home/{login}")
    shell = str(opts["shell"] or DEFAULTS["shell"])
    office = str(opts["office"] or "")
    mail = str(opts["mail"] or "")
    site = str(opts["site"] or github_user.get("blog") or "")
    title = str(opts["title"] or f"finger {login}")
    plan = opts["plan"] or []
    if isinstance(plan, str):
        plan = [plan]
    plan = [str(line) for line in plan if str(line).strip()]

    key_colour = theme.accent
    link_colour = theme.blue

    def node(x, content, colour, weight=None):
        return (
            f'<text x="{x:.1f}" y="__Y__" font-family="{MONO}" font-size="{font:g}" '
            f'fill="{colour}" xml:space="preserve"'
            + (f' font-weight="{weight}"' if weight else "")
            + f' textLength="{len(content) * adv:.1f}" lengthAdjust="spacing">'
            f"{esc(content)}</text>"
        )

    def pair(col, key, value, colour, room):
        """`Key: value` starting at a column; the value is cut to the room left."""
        label = f"{key}: "
        value = _fit(value, room - len(label))
        markup = node(pad + col * adv, label, key_colour, weight="600")
        if value:
            markup += node(pad + (col + len(label)) * adv, value, colour)
        return markup, len(label) + len(value)

    rows = []

    # The top block: two pairs per line when the left one leaves the column free.
    top = [
        (("Login", login, theme.fg), ("Name", name, theme.fg)),
        (("Directory", directory, theme.fg), ("Shell", shell, theme.fg)),
    ]
    for left, right in top:
        left_markup, used = pair(0, left[0], left[1], left[2], columns)
        if used < column - 1:
            right_markup, _ = pair(column, right[0], right[1], right[2], columns - column)
            rows.append(left_markup + right_markup)
        else:
            rows.append(left_markup)
            rows.append(pair(0, right[0], right[1], right[2], columns)[0])

    for key, value in (("Office", office), ("Mail", mail), ("Site", site)):
        if value:
            colour = link_colour if key.lower() in LINK_KEYS else theme.fg
            rows.append(pair(0, key, value, colour, columns)[0])

    fields = opts["fields"] or []
    if isinstance(fields, (dict, str)):
        fields = [fields]
    for entry in fields:
        if isinstance(entry, dict):
            key, value, colour = entry.get("key", ""), entry.get("value", ""), entry.get("color", "")
        elif isinstance(entry, str):
            key, _, value = entry.partition(":")
            colour = ""
        else:
            key, value = (list(entry) + ["", ""])[:2]
            colour = entry[2] if len(entry) > 2 else ""
        key, value = str(key).strip(), str(value).strip()
        if not key or not value:
            continue
        if colour:
            fill = theme.colour(colour)
        else:
            fill = link_colour if key.lower() in LINK_KEYS else theme.fg
        rows.append(pair(0, key, value, fill, columns)[0])

    # On since Wed Sep 24 06:17 (UTC) on pts/0 from github-actions
    head = f"On since {_on_since((ctx or {}).get('build'))} on {opts['tty']} "
    tail = _fit(f"from {opts['origin']}", columns - len(head))
    rows.append(node(pad, head, theme.fg) + node(pad + len(head) * adv, tail, theme.dim))

    rows.append(node(pad, "Plan:", key_colour, weight="600"))
    if plan:
        for line in plan:
            rows.append(node(pad + 2 * adv, _fit(line, columns - 2), theme.fg))
    else:
        rows.append(node(pad + 2 * adv, _fit(str(opts["no_plan"]), columns - 2), theme.dim))

    contact = ", ".join(part for part in (office, mail, site) if part)
    label = f"finger {login}: {name}" + (f", {contact}" if contact else "") + (
        "; plan: " + " ".join(plan) if plan else ""
    )

    height = first_y + (len(rows) - 1) * row_h + 28
    animation = (
        "" if static else
        ".r{opacity:0;animation:in .45s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-10px)}"
        "to{opacity:1;transform:none}}"
        "@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1;"
        "transform:none}}"
    )

    def attrs(index):
        if static:
            return ""
        return f' class="r" style="animation-delay:{0.25 + index * 0.06:.2f}s"'

    out = [
        svg_open(width, height, label),
        f"<style>{animation}</style>",
        card(theme, width, height),
        title_bar(theme, width, title),
    ]
    for index, markup in enumerate(rows):
        y = first_y + index * row_h
        out.append(f"<g{attrs(index)}>{markup.replace('__Y__', f'{y:g}')}</g>")
    out.append("</svg>")
    return "\n".join(out) + "\n"
