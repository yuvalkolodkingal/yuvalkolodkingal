"""The closing line: the session ends the way it began, at a prompt.

The reader has scrolled through a whole shell session, so the page should
not just stop; it should log out. One prompt types `exit` with a block
cursor, the shell answers `logout`, and the connection-closed line carries
the build stamp, which is the honest place for it: the last thing a real
session prints is when it happened.

Typing is a SMIL clip that plays once and freezes, because there is no
loop to park in. The two answer lines are CSS reveals, so reduced motion
can show the finished panel at once; the SMIL clip cannot be gated by a
media query, so the clipped text carries a class and the media query
simply removes its clip-path and hides the cursor.
"""

from theme import MONO, PROMPT_TAIL, card, esc, prompt, svg_open

DEFAULTS = {
    "command": "exit",
    "farewell": "Connection to {host} closed.",
    "show_build": True,
    "host": "",             # falls back to [profile] host
    "font": 11.5,
    "row_height": 20,
    "per_char": 0.06,       # typing speed, seconds per character
    "begin": 0.4,           # seconds before the first character
}


def _stamp(build):
    """'last build 2026-09-24 06:17 UTC · a1b2c3d' from the build dict."""
    build = build or {}
    when = str(build.get("generated_at") or "").strip()
    sha = str(build.get("sha") or "").strip()[:7]
    if not when and not sha:
        return ""
    parts = ["last build"]
    if when:
        parts.append(when)
    if sha:
        parts.append(("· " if when else "") + sha)
    return " ".join(parts)


def render(theme, config, ctx, width=860, static=False):
    config = config or {}
    ctx = ctx or {}
    opts = {**DEFAULTS, **{k: v for k, v in config.items() if k in DEFAULTS}}
    profile = ctx.get("profile") or {}
    font, row_h = float(opts["font"]), int(opts["row_height"])
    adv = font * 0.6
    pad = 20
    per_char, begin = float(opts["per_char"]), float(opts["begin"])

    user = profile.get("user") or profile.get("username") or "me"
    host = str(opts["host"] or profile.get("host") or "github")
    command = str(opts["command"] or "exit")
    farewell = str(opts["farewell"] or "")
    try:
        farewell = farewell.format(host=host, user=user)
    except (KeyError, IndexError, ValueError):
        pass  # an unknown placeholder is shown as written, not a build failure
    stamp = _stamp(ctx.get("build")) if opts["show_build"] else ""

    first_y = 29
    height = first_y + 2 * row_h + 15
    columns = int((width - pad * 2) / adv)
    line = f"{user}@{host}{PROMPT_TAIL}{command}"
    count = len(line)
    run = count * adv
    type_end = begin + count * per_char

    # Drop the stamp rather than let it run into the farewell on a narrow card.
    if stamp and len(farewell) + len(stamp) + 3 > columns:
        stamp = ""

    label = config.get("label") or f"{line}; logout; {farewell}".rstrip("; ")
    animation = (
        "" if static else
        ".r{opacity:0;animation:in .45s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-10px)}"
        "to{opacity:1;transform:none}}"
        "@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1;"
        "transform:none}.t{clip-path:none}.c{display:none}}"
    )

    out = [svg_open(width, height, label), f"<style>{animation}</style>", card(theme, width, height)]

    if not static:
        widths = ";".join(f"{step * adv:.2f}" for step in range(count + 1))
        keys = ";".join(f"{step / count:.5f}" for step in range(count + 1))
        out.append(
            "<defs>"
            f'<clipPath id="exit-clip"><rect x="{pad}" y="0" width="0" height="{height}">'
            f'<animate attributeName="width" calcMode="discrete" values="{widths}" '
            f'keyTimes="{keys}" begin="{begin:g}s" dur="{count * per_char:.3f}s" fill="freeze"/>'
            "</rect></clipPath></defs>"
        )

    # textLength pins the advance so the clip edge lands between characters
    # whichever monospace font the reader has.
    clip = "" if static else ' class="t" clip-path="url(#exit-clip)"'
    out.append(
        f'<text{clip} x="{pad}" y="{first_y}" xml:space="preserve" font-family="{MONO}" '
        f'font-size="{font:g}" textLength="{run:.2f}" lengthAdjust="spacing">'
        f"{prompt(theme, user, host, command)}</text>"
    )

    if not static:
        xs = ";".join(f"{pad + step * adv:.2f}" for step in range(count + 1))
        out.append(
            f'<rect class="c" x="{pad}" y="{first_y - font + 2:.1f}" width="{adv:.2f}" '
            f'height="{font + 2:.1f}" fill="{theme.accent}">'
            f'<animate attributeName="x" calcMode="discrete" values="{xs}" keyTimes="{keys}" '
            f'begin="{begin:g}s" dur="{count * per_char:.3f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{type_end + 0.3:.2f}s" fill="freeze"/>'
            "</rect>"
        )

    def attrs(delay):
        if static:
            return ""
        return f' class="r" style="animation-delay:{delay:.2f}s"'

    logout_y = first_y + row_h
    out.append(
        f'<g{attrs(type_end + 0.3)}><text x="{pad}" y="{logout_y}" font-family="{MONO}" '
        f'font-size="{font:g}" fill="{theme.dim}">logout</text></g>'
    )

    last_y = first_y + 2 * row_h
    parts = []
    if farewell:
        parts.append(
            f'<text x="{pad}" y="{last_y}" font-family="{MONO}" font-size="{font:g}" '
            f'fill="{theme.dim}">{esc(farewell)}</text>'
        )
    if stamp:
        parts.append(
            f'<text x="{width - pad:g}" y="{last_y}" text-anchor="end" font-family="{MONO}" '
            f'font-size="{font:g}" fill="{theme.dim}">{esc(stamp)}</text>'
        )
    if parts:
        out.append(f'<g{attrs(type_end + 0.5)}>{"".join(parts)}</g>')

    out.append("</svg>")
    return "\n".join(out) + "\n"
