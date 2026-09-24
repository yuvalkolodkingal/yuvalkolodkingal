"""The person's flagship projects, printed like `systemctl status`.

A project that is live is a service that is running, and systemd already
has the perfect way to say so: a green dot, a unit name, when it started
and how long ago, where the docs are, and the last few journal lines. So
the panel borrows that output line for line. Everything a real status
print derives from the kernel (PID, tasks, memory, CPU) is decorative
here, so those numbers come from a hash of the unit name and never change
between builds; nothing on the card should look different tomorrow unless
the person changed the config.
"""

import hashlib
from datetime import date, datetime

from theme import MONO, STILL_CSS, card, esc, mix, still_layer, svg_open, title_bar

DEFAULTS = {
    "title": "",
    "host": "",
    "font": 11.5,
    "row_height": 21,
    "empty": "no units found",
}

PROJECT_DEFAULTS = {
    "name": "",
    "description": "",
    "url": "",
    "since": "",
    "status": "active (running)",
    "docs": "",
    "lines": (),
    "exec": "",
}

# What the main process would be called, by the repository's language.
EXEC_BY_LANGUAGE = {
    "javascript": "node",
    "typescript": "node",
    "python": "python3",
    "ruby": "ruby",
    "java": "java",
    "kotlin": "java",
    "php": "php-fpm",
    "go": "server",
    "rust": "server",
    "c": "server",
    "c++": "server",
    "shell": "bash",
}

# The first word of the status decides its colour, like systemd's own.
STATUS_COLOURS = {
    "active": "green",
    "activating": "yellow",
    "reloading": "yellow",
    "deactivating": "yellow",
    "failed": "red",
    "inactive": "dim",
}

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _digest(name):
    return hashlib.sha256(name.encode("utf-8")).digest()


def _fit(content, columns):
    content = content or ""
    if columns <= 0:
        return ""
    if len(content) <= columns:
        return content
    return content[: max(columns - 3, 0)].rstrip() + "..."


def _parse_date(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _parse_build(build):
    stamp = str((build or {}).get("generated_at") or "")
    try:
        return datetime.strptime(stamp[:16], "%Y-%m-%d %H:%M")
    except ValueError:
        pass
    day = _parse_date(stamp)
    if day:
        return datetime(day.year, day.month, day.day, 6, 0)
    return datetime.combine(date.today(), datetime.min.time()).replace(hour=6)


def _ago(since, now):
    """`10 months ago`, the way systemd rounds it, from two dates."""
    days = (now - since).days
    if days < 0:
        return "just now"
    months = (now.year - since.year) * 12 + (now.month - since.month)
    if now.day < since.day:
        months -= 1
    if months >= 12:
        years = months // 12
        return f"{years} year{'s' if years != 1 else ''} ago"
    if months >= 1:
        return f"{months} month{'s' if months != 1 else ''} ago"
    if days >= 14:
        weeks = days // 7
        return f"{weeks} weeks ago"
    if days >= 1:
        return f"{days} day{'s' if days != 1 else ''} ago"
    return "today"


def _unit(project, github, now):
    """Everything one unit prints, computed once so the rows stay in step."""
    raw = dict(PROJECT_DEFAULTS)
    raw.update({k: v for k, v in (project or {}).items() if k in PROJECT_DEFAULTS})
    name = str(raw["name"] or "unit").strip()
    short = name[:-8] if name.endswith(".service") else name
    unit = f"{short}.service"
    digest = _digest(short)

    exec_name = str(raw["exec"] or "")
    if not exec_name:
        language = ""
        for repo in (github or {}).get("top_repos") or []:
            if str(repo.get("name", "")).lower() == short.lower():
                language = str(repo.get("language") or "")
                break
        exec_name = EXEC_BY_LANGUAGE.get(language.lower(), "node")

    pid = 1000 + int.from_bytes(digest[0:2], "big") % 60000
    tasks = 4 + digest[2] % 20
    memory = 24 + int.from_bytes(digest[3:5], "big") % 400 + digest[5] % 10 / 10
    cpu_min = 1 + digest[6] % 58
    cpu_sec = digest[7] % 60
    cpu_ms = int.from_bytes(digest[8:10], "big") % 1000
    start_hour = 6 + digest[10] % 16
    start_min = digest[11] % 60
    start_sec = digest[12] % 60
    log_sec = digest[13] % 50

    since = _parse_date(raw["since"])
    if since:
        stamp = f"{since.strftime('%a')} {since.isoformat()} {start_hour:02d}:{start_min:02d}:{start_sec:02d} UTC"
        active_tail = f" since {stamp}; {_ago(since, now.date())}"
    else:
        active_tail = ""

    status = str(raw["status"] or PROJECT_DEFAULTS["status"]).strip()
    status_colour = STATUS_COLOURS.get(status.split(" ")[0].split("(")[0].lower(), "fg")

    lines = []
    for index, line in enumerate(list(raw["lines"] or [])[:4]):
        seconds = (log_sec + index * 2) % 60
        prefix = (
            f"{MONTHS[now.month - 1]} {now.day:2d} {now.hour:02d}:{now.minute:02d}:{seconds:02d} "
            f"__HOST__ {short}[{pid}]: "
        )
        lines.append((prefix, str(line)))

    return {
        "unit": unit,
        "short": short,
        "description": str(raw["description"] or ""),
        "status": status,
        "status_colour": status_colour,
        "active_tail": active_tail,
        "since": since,
        "docs": str(raw["docs"] or raw["url"] or ""),
        "exec": exec_name,
        "pid": pid,
        "tasks": tasks,
        "memory": f"{memory:.1f}M",
        "cpu": f"{cpu_min}min {cpu_sec}.{cpu_ms:03d}s",
        "lines": lines,
    }


def _from_repo(repo):
    return {
        "name": repo.get("name", ""),
        "description": repo.get("description") or "",
        "url": repo.get("url", ""),
        "docs": repo.get("url", ""),
    }


def render(theme, config, ctx, width=860, static=False):
    config = config or {}
    opts = {**DEFAULTS, **{k: v for k, v in config.items() if k in DEFAULTS}}
    font, row_h = float(opts["font"]), int(opts["row_height"])
    adv = font * 0.6
    pad = 20
    first_y = 66
    columns = int((width - pad * 2) / adv)
    label_end = 12      # the colon of "     Loaded:" sits in this column
    value_col = 13

    profile = (ctx or {}).get("profile") or {}
    github = (ctx or {}).get("github") or {}
    now = _parse_build((ctx or {}).get("build"))
    host = str(opts["host"] or profile.get("host") or "github")

    projects = [p for p in (config.get("projects") or []) if isinstance(p, dict) and p.get("name")]
    if not projects:
        top = (github.get("top_repos") or [{}])[0]
        if top.get("name"):
            projects = [_from_repo(top)]
    units = [_unit(project, github, now) for project in projects]

    title = opts["title"] or ("systemctl status " + " ".join(u["unit"] for u in units) if units else "systemctl status")
    if units:
        label = "systemctl status: " + "; ".join(
            f"{u['unit']} {u['status']}" + (f" since {u['since'].isoformat()}" if u["since"] else "")
            for u in units
        )
    else:
        label = "systemctl status: no units found"

    animation = (
        "" if static else
        ".r{opacity:0;animation:in .4s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
        "@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1;transform:none}}"
        + STILL_CSS
    )
    def attrs(index):
        if static:
            return ""
        return f' class="r" style="animation-delay:{0.2 + index * 0.05:.2f}s"'

    def node(x, content, colour, weight=None, anchor=None, fixed=False, extra=""):
        parts = [
            f'x="{x:.1f}"', 'y="__Y__"', f'font-family="{MONO}"', f'font-size="{font:g}"',
            f'fill="{colour}"', 'xml:space="preserve"',
        ]
        if weight:
            parts.append(f'font-weight="{weight}"')
        if anchor:
            parts.append(f'text-anchor="{anchor}"')
        if fixed:
            parts.append(f'textLength="{len(content) * adv:.1f}" lengthAdjust="spacing"')
        if extra:
            parts.append(extra)
        return f"<text {' '.join(parts)}>{esc(content)}</text>"

    def field(label_text, value_nodes):
        """A `     Label: value` row: label right-aligned in dim, value at column 13."""
        return (
            node(pad + label_end * adv, label_text + ":", theme.dim, anchor="end", fixed=True)
            + value_nodes
        )

    def value(content, colour=None, weight=None, col=value_col):
        return node(pad + col * adv, _fit(content, columns - col), colour or theme.fg, weight=weight)

    rows = []  # (index -> markup with __Y__), None for a blank row
    log_ink = mix(theme.dim, theme.fg, 0.45)
    value_room = columns - value_col

    for unit_index, unit in enumerate(units):
        if unit_index:
            rows.append(None)
        # ● name.service - description
        pulse = (
            "" if static else
            '<animate attributeName="opacity" values="1;0.35;1" dur="2.4s" repeatCount="indefinite"/>'
        )
        dot_colour = theme.colour(unit["status_colour"])
        dot = f'<circle cx="{pad + adv * 0.5:.1f}" cy="__CY__" r="3.4" fill="{dot_colour}">'
        # SMIL ignores media queries, so reduced-motion readers get a still twin.
        header = dot + "</circle>" if static else still_layer(dot + pulse + "</circle>", dot + "</circle>")
        desc_room = columns - 2 - len(unit["unit"]) - 3
        desc = _fit(unit["description"], desc_room) if desc_room > 8 else ""
        header += (
            f'<text x="{pad + 2 * adv:.1f}" y="__Y__" font-family="{MONO}" font-size="{font:g}" '
            f'fill="{theme.fg}" xml:space="preserve">'
            f'<tspan font-weight="600">{esc(unit["unit"])}</tspan>'
            + (f'<tspan fill="{theme.dim}"> - </tspan><tspan>{esc(desc)}</tspan>' if desc else "")
            + "</text>"
        )
        rows.append(header)

        # Loaded: loaded (/etc/systemd/system/x.service; enabled; preset: enabled)
        # Narrow cards drop the preset clause, then shorten the path, so the
        # line never runs past the card edge.
        path = f"/etc/systemd/system/{unit['unit']}"
        preset = "; preset: enabled"
        if len(f"loaded ({path}; enabled{preset})") > value_room:
            preset = ""
        if len(f"loaded ({path}; enabled{preset})") > value_room:
            path = f".../{unit['unit']}"
        if len(f"loaded ({path}; enabled{preset})") > value_room:
            path = _fit(path, max(value_room - len("loaded (; enabled)"), 4))
        loaded = (
            f'<text x="{pad + value_col * adv:.1f}" y="__Y__" font-family="{MONO}" font-size="{font:g}" '
            f'fill="{theme.dim}" xml:space="preserve">'
            f'<tspan fill="{theme.fg}">loaded</tspan> ({esc(path)}; '
            f'<tspan fill="{theme.fg}">enabled</tspan>'
            + (f'; preset: <tspan fill="{theme.fg}">enabled</tspan>' if preset else "")
            + ")</text>"
        )
        rows.append(field("Loaded", loaded))

        # Active: active (running) since Tue 2025-11-04 09:12:00 UTC; 10 months ago
        tail = _fit(unit["active_tail"], value_room - len(unit["status"]))
        active = (
            f'<text x="{pad + value_col * adv:.1f}" y="__Y__" font-family="{MONO}" font-size="{font:g}" '
            f'fill="{theme.fg}" xml:space="preserve">'
            f'<tspan fill="{dot_colour}" font-weight="700">{esc(unit["status"])}</tspan>{esc(tail)}'
            "</text>"
        )
        rows.append(field("Active", active))

        if unit["docs"]:
            rows.append(field("Docs", value(unit["docs"], theme.accent)))
        rows.append(field("Main PID", value(f"{unit['pid']} ({unit['exec']})")))
        rows.append(field("Tasks", value(str(unit["tasks"]))))
        rows.append(field("Memory", value(unit["memory"])))
        rows.append(field("CPU", value(unit["cpu"])))
        rows.append(field("CGroup", value(f"/system.slice/{unit['unit']}")))

        if unit["lines"]:
            rows.append(None)
        for prefix, message in unit["lines"]:
            prefix = prefix.replace("__HOST__", host)
            room = columns - len(prefix)
            rows.append(
                node(pad, prefix, theme.dim, fixed=True)
                + node(pad + len(prefix) * adv, _fit(message, room), log_ink)
            )

    if not units:
        rows.append(node(pad, opts["empty"], theme.dim))

    height = first_y + (len(rows) - 1) * row_h + 28
    out = [
        svg_open(width, height, label),
        f"<style>{animation}</style>",
        card(theme, width, height),
        title_bar(theme, width, title),
    ]

    shown = 0
    for index, markup in enumerate(rows):
        if markup is None:
            continue
        y = first_y + index * row_h
        body = markup.replace("__Y__", f"{y:g}").replace("__CY__", f"{y - font * 0.34:.1f}")
        out.append(f"<g{attrs(shown)}>{body}</g>")
        shown += 1

    out.append("</svg>")
    return "\n".join(out) + "\n"
