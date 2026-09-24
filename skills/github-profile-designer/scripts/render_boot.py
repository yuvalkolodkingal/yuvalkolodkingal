"""The boot log: the page opens like a machine starting up.

A systemd-style log prints line by line with rising kernel timestamps, a
few `[  OK  ]` unit lines that describe the person (targets reached,
services started, volumes mounted), then the login banner with a real
"Last login" stamp written by the daily build, and a prompt with a blinking
cursor that every heading on the page then continues.

Everything is CSS keyframes, so prefers-reduced-motion shows the finished
log at once. The lines come from config; the defaults are built from the
profile so an empty [boot] section still boots something sensible.
"""

from theme import MONO, card, esc, prompt, prompt_length, svg_open, title_bar

DEFAULTS = {
    "kernel": "6.18.0-profile",
    "font": 11.5,
    "row_height": 19,
    "step": 0.16,           # seconds between lines printing
    "show_login": True,       # "<host> login: <user>" and "Password:" before the stamp
    "show_last_login": True,
    "show_prompt": True,
    "title": "tty1",
}


def default_lines(profile):
    user = profile.get("user", "me")
    host = profile.get("host", "github")
    return [
        {"kind": "kernel", "text": f"Linux version {{kernel}} ({user}@{host}) #1 SMP PREEMPT_DYNAMIC"},
        {"kind": "kernel", "text": "Command line: BOOT_IMAGE=/vmlinuz root=/dev/github rw quiet"},
        {"kind": "ok", "text": "Reached target basic.target - Basic System."},
        {"kind": "ok", "text": f"Started {user}.service - Profile page."},
        {"kind": "ok", "text": "Reached target multi-user.target - Multi-User System."},
    ]


def _stamp(build):
    """'Wed Sep 24 06:17 2026 UTC' from the build's generated_at."""
    from datetime import datetime

    raw = (build or {}).get("generated_at") or ""
    try:
        when = datetime.strptime(raw, "%Y-%m-%d %H:%M UTC")
    except ValueError:
        when = datetime.utcnow()
    return when.strftime("%a %b %d %H:%M %Y UTC")


def render(theme, config, ctx, width=860, static=False):
    opts = {**DEFAULTS, **{k: v for k, v in config.items() if k in DEFAULTS}}
    font, row_h, step = float(opts["font"]), int(opts["row_height"]), float(opts["step"])
    adv = font * 0.6
    pad = 20
    profile = ctx.get("profile", {})
    build = ctx.get("build", {})
    user, host = profile.get("user", "me"), profile.get("host", "github")

    raw_lines = config.get("lines") or default_lines(profile)
    lines = []
    for entry in raw_lines:
        if isinstance(entry, str):
            entry = {"kind": "ok", "text": entry}
        text = str(entry.get("text", "")).replace("{kernel}", str(opts["kernel"]))
        lines.append({"kind": entry.get("kind", "ok"), "text": text})

    columns = int((width - pad * 2) / adv)
    total_rows = len(lines) + (3 if opts["show_login"] else 0) + (2 if opts["show_last_login"] else 0) + (1 if opts["show_prompt"] else 0)
    top = 64
    height = top + total_rows * row_h + 16

    finish = 0.3 + len(lines) * step
    label = config.get("label") or f"Boot log for {profile.get('name', user)}: " + "; ".join(l["text"] for l in lines)
    css = (
        "" if static else
        ".r{opacity:0;animation:in .05s linear forwards}"
        "@keyframes in{to{opacity:1}}"
        ".k{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        "@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1}.k{animation:none}}"
    )
    out = [svg_open(width, height, label), f"<style>{css}</style>", card(theme, width, height), title_bar(theme, width, str(opts["title"]))]

    def attrs(delay):
        return "" if static else f' class="r" style="animation-delay:{delay:.2f}s"'

    # Kernel timestamps rise like a real dmesg, deterministic per line.
    stamp = 0.0
    y = top
    for index, line in enumerate(lines):
        kind, text = line["kind"], line["text"]
        stamp += 0.0217 + (index % 3) * 0.0142 + (index % 5) * 0.0031
        y = top + index * row_h
        parts = []
        if kind == "kernel":
            parts.append(
                f'<text x="{pad}" y="{y}" font-family="{MONO}" font-size="{font}" fill="{theme.dim}" '
                f'xml:space="preserve">[{stamp:11.6f}] </text>'
            )
            body_x = pad + 15 * adv
            colour = theme.fg
        elif kind == "fail":
            parts.append(
                f'<text x="{pad}" y="{y}" font-family="{MONO}" font-size="{font}" xml:space="preserve">'
                f'<tspan fill="{theme.dim}">[</tspan><tspan fill="{theme.red}" font-weight="600">FAILED</tspan>'
                f'<tspan fill="{theme.dim}">]</tspan></text>'
            )
            body_x = pad + 9 * adv
            colour = theme.fg
        elif kind == "info":
            parts.append(
                f'<text x="{pad}" y="{y}" font-family="{MONO}" font-size="{font}" xml:space="preserve">'
                f'<tspan fill="{theme.dim}">[</tspan><tspan fill="{theme.blue}" font-weight="600"> INFO </tspan>'
                f'<tspan fill="{theme.dim}">]</tspan></text>'
            )
            body_x = pad + 9 * adv
            colour = theme.fg
        else:
            parts.append(
                f'<text x="{pad}" y="{y}" font-family="{MONO}" font-size="{font}" xml:space="preserve">'
                f'<tspan fill="{theme.dim}">[</tspan><tspan fill="{theme.green}" font-weight="600">  OK  </tspan>'
                f'<tspan fill="{theme.dim}">]</tspan></text>'
            )
            body_x = pad + 9 * adv
            colour = theme.fg
        room = columns - int((body_x - pad) / adv)
        shown = text if len(text) <= room else text[: room - 1].rstrip() + "…"
        # Unit names before " - " print bold, like systemd's own output.
        if " - " in shown and kind not in ("kernel",):
            head, tail = shown.split(" - ", 1)
            body = (
                f'<tspan fill="{colour}" font-weight="600">{esc(head)}</tspan>'
                f'<tspan fill="{theme.dim}"> - {esc(tail)}</tspan>'
            )
        else:
            body = f'<tspan fill="{colour}">{esc(shown)}</tspan>'
        parts.append(
            f'<text x="{body_x:.1f}" y="{y}" font-family="{MONO}" font-size="{font}" xml:space="preserve">{body}</text>'
        )
        out.append(f"<g{attrs(0.3 + index * step)}>{''.join(parts)}</g>")

    row = len(lines)
    at = finish
    if opts["show_login"]:
        row += 1  # a blank line, like the pause before getty draws the banner
        banner = config.get("banner") or f"{profile.get('name', user)} {opts['title']}"
        for text, delay in ((banner, 0.35), (f"{host} login: {user}", 0.75), ("Password:", 1.35)):
            y = top + row * row_h
            out.append(
                f'<g{attrs(at + delay)}><text x="{pad}" y="{y}" font-family="{MONO}" font-size="{font}" '
                f'fill="{theme.fg}" xml:space="preserve">{esc(text)}</text></g>'
            )
            row += 1
        at += 1.6
    if opts["show_last_login"]:
        if not opts["show_login"]:
            row += 1  # a beat of silence before the stamp
        y = top + row * row_h
        out.append(
            f'<g{attrs(at + 0.5)}><text x="{pad}" y="{y}" font-family="{MONO}" font-size="{font}" '
            f'fill="{theme.dim}" xml:space="preserve">Last login: {esc(_stamp(build))} on pts/0 from github-actions</text></g>'
        )
        row += 1
        at += 0.5
    if opts["show_prompt"]:
        y = top + row * row_h
        cursor_x = pad + prompt_length(user, host) * adv
        cursor = "" if static else f'<rect class="k" x="{cursor_x:.1f}" y="{y - font + 1:.1f}" width="{adv:.1f}" height="{font + 2:.1f}" fill="{theme.accent}"/>'
        out.append(
            f'<g{attrs(at + 0.3)}><text x="{pad}" y="{y}" font-family="{MONO}" font-size="{font}" '
            f'xml:space="preserve">{prompt(theme, user, host, "")}</text>{cursor}</g>'
        )
    out.append("</svg>")
    return "\n".join(out) + "\n"
