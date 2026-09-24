"""Colour palettes and the SVG helpers every panel is drawn with.

Every SVG the engine emits is self-contained. GitHub loads README images
through an <img> tag behind its camo proxy, which means: no external CSS, no
web fonts, no scripts, no foreignObject. Anything that moves has to be a CSS
keyframe or a SMIL animation living inside the file itself, and anything
that has a colour gets it from the Theme passed in, never from a global.

A Theme is a frozen dataclass. Panels take one as an argument so the same
renderer can emit a dark and a light file for the README's <picture> pair.
"""

from dataclasses import dataclass, field, replace
from typing import Optional, Tuple

MONO = (
    "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
    "'DejaVu Sans Mono','Liberation Mono',monospace"
)

_ESCAPES = (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"))


def esc(text):
    """Escape text for use inside an SVG text node or attribute."""
    out = str(text)
    for raw, encoded in _ESCAPES:
        out = out.replace(raw, encoded)
    return out


def _rgb(hex_colour):
    value = hex_colour.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(channel)))) for channel in rgb)


def mix(a, b, t):
    """Linear blend of two hex colours, t=0 gives a, t=1 gives b."""
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(ca + (cb - ca) * t for ca, cb in zip(ra, rb)))


def luminance(hex_colour):
    """Relative luminance, 0 (black) to 1 (white)."""
    def channel(value):
        value /= 255
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(part) for part in _rgb(hex_colour))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    """WCAG contrast ratio between two colours."""
    la, lb = luminance(a), luminance(b)
    light, dark = max(la, lb), min(la, lb)
    return (light + 0.05) / (dark + 0.05)


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    panel: str
    border: str
    fg: str
    dim: str
    blue: str
    purple: str
    teal: str
    yellow: str
    pink: str
    green: str
    orange: str
    red: str
    cyan: str
    # Set for dark palettes; a light one flips what "bright" means.
    dark: bool = True
    # Five heat levels, none -> most, matching GitHub's data-level 0..4.
    heat: Tuple[str, ...] = ()
    # Snake body, head first, as (colour, size) pairs.
    snake: Tuple[Tuple[str, float], ...] = ()
    flash: str = ""
    ink: str = ""       # ASCII portrait ink
    accent: str = ""    # the one colour used for headings and the cursor

    def __post_init__(self):
        if not self.accent:
            object.__setattr__(self, "accent", self.blue)
        if not self.ink:
            object.__setattr__(self, "ink", mix(self.fg, "#ffffff" if self.dark else "#000000", 0.35))
        if not self.heat:
            top = self.blue
            if self.dark:
                stops = (
                    mix(self.bg, self.border, 0.55),
                    mix(self.bg, top, 0.32),
                    mix(self.bg, top, 0.62),
                    top,
                    mix(top, "#ffffff", 0.35),
                )
            else:
                stops = (
                    mix(self.bg, self.border, 0.55),
                    mix(self.bg, top, 0.32),
                    mix(self.bg, top, 0.62),
                    top,
                    mix(top, "#000000", 0.3),
                )
            object.__setattr__(self, "heat", stops)
        if not self.flash:
            object.__setattr__(self, "flash", mix(self.purple, "#ffffff", 0.8) if self.dark else mix(self.purple, "#000000", 0.5))
        if not self.snake:
            toward = "#ffffff" if self.dark else "#000000"
            body = self.purple
            object.__setattr__(
                self,
                "snake",
                (
                    (mix(body, toward, 0.75), 12.0),
                    (mix(body, toward, 0.55), 11.5),
                    (body, 11.0),
                    (mix(body, self.bg, 0.12), 10.0),
                    (mix(body, self.bg, 0.24), 9.0),
                    (mix(body, self.bg, 0.36), 8.0),
                    (mix(body, self.bg, 0.5), 7.0),
                ),
            )

    def colour(self, name, default=None):
        """Resolve a colour by role name ("blue", "fg") or pass a hex through."""
        if not name:
            return default or self.fg
        if name.startswith("#"):
            return name
        value = getattr(self, name.replace("-", "_"), None)
        if isinstance(value, str) and value:
            return value
        return default or self.fg


# The palettes. Values are the canonical published ones; the tokyo-night entry
# keeps the exact heat and snake ramps the original profile shipped with.
PALETTES = {
    "tokyo-night": Theme(
        name="tokyo-night", bg="#1a1b27", panel="#1f2335", border="#3b4261",
        fg="#a9b1d6", dim="#565f89", blue="#70a5fd", purple="#bf91f3",
        teal="#38bdae", yellow="#e0af68", pink="#ff7a93", green="#9ece6a",
        orange="#ff9e64", red="#f7768e", cyan="#7dcfff",
        heat=("#1e2235", "#26406e", "#2f6bbd", "#54a0f0", "#8fd0ff"),
        snake=(("#f0e0ff", 12.0), ("#e6ccff", 11.5), ("#bf91f3", 11.0),
               ("#ab7ce8", 10.0), ("#9668d8", 9.0), ("#8455c4", 8.0), ("#6a43a0", 7.0)),
        flash="#f0e0ff", ink="#c7d0f0",
    ),
    "tokyo-day": Theme(
        name="tokyo-day", bg="#e1e2e7", panel="#d5d6db", border="#b4b5c4",
        fg="#3760bf", dim="#848cb5", blue="#2e7de9", purple="#9854f1",
        teal="#118c74", yellow="#8c6c3e", pink="#f52a65", green="#587539",
        orange="#b15c00", red="#f52a65", cyan="#007197", dark=False, ink="#343b58",
    ),
    "catppuccin-mocha": Theme(
        name="catppuccin-mocha", bg="#1e1e2e", panel="#181825", border="#313244",
        fg="#cdd6f4", dim="#6c7086", blue="#89b4fa", purple="#cba6f7",
        teal="#94e2d5", yellow="#f9e2af", pink="#f5c2e7", green="#a6e3a1",
        orange="#fab387", red="#f38ba8", cyan="#89dceb",
    ),
    "catppuccin-latte": Theme(
        name="catppuccin-latte", bg="#eff1f5", panel="#e6e9ef", border="#ccd0da",
        fg="#4c4f69", dim="#8c8fa1", blue="#1e66f5", purple="#8839ef",
        teal="#179299", yellow="#df8e1d", pink="#ea76cb", green="#40a02b",
        orange="#fe640b", red="#d20f39", cyan="#04a5e5", dark=False,
    ),
    "dracula": Theme(
        name="dracula", bg="#282a36", panel="#21222c", border="#44475a",
        fg="#f8f8f2", dim="#6272a4", blue="#8be9fd", purple="#bd93f9",
        teal="#50fa7b", yellow="#f1fa8c", pink="#ff79c6", green="#50fa7b",
        orange="#ffb86c", red="#ff5555", cyan="#8be9fd",
    ),
    "nord": Theme(
        name="nord", bg="#2e3440", panel="#3b4252", border="#4c566a",
        fg="#d8dee9", dim="#7b88a1", blue="#88c0d0", purple="#b48ead",
        teal="#8fbcbb", yellow="#ebcb8b", pink="#bf616a", green="#a3be8c",
        orange="#d08770", red="#bf616a", cyan="#88c0d0",
    ),
    "gruvbox-dark": Theme(
        name="gruvbox-dark", bg="#282828", panel="#1d2021", border="#3c3836",
        fg="#ebdbb2", dim="#928374", blue="#83a598", purple="#d3869b",
        teal="#8ec07c", yellow="#fabd2f", pink="#fb4934", green="#b8bb26",
        orange="#fe8019", red="#fb4934", cyan="#8ec07c",
    ),
    "gruvbox-light": Theme(
        name="gruvbox-light", bg="#fbf1c7", panel="#f2e5bc", border="#d5c4a1",
        fg="#3c3836", dim="#928374", blue="#076678", purple="#8f3f71",
        teal="#427b58", yellow="#b57614", pink="#9d0006", green="#79740e",
        orange="#af3a03", red="#9d0006", cyan="#427b58", dark=False,
    ),
    "one-dark": Theme(
        name="one-dark", bg="#282c34", panel="#21252b", border="#3e4451",
        fg="#abb2bf", dim="#5c6370", blue="#61afef", purple="#c678dd",
        teal="#56b6c2", yellow="#e5c07b", pink="#e06c75", green="#98c379",
        orange="#d19a66", red="#e06c75", cyan="#56b6c2",
    ),
    "rose-pine": Theme(
        name="rose-pine", bg="#191724", panel="#1f1d2e", border="#26233a",
        fg="#e0def4", dim="#6e6a86", blue="#9ccfd8", purple="#c4a7e7",
        teal="#31748f", yellow="#f6c177", pink="#eb6f92", green="#9ccfd8",
        orange="#ebbcba", red="#eb6f92", cyan="#9ccfd8",
    ),
    "rose-pine-dawn": Theme(
        name="rose-pine-dawn", bg="#faf4ed", panel="#fffaf3", border="#dfdad9",
        fg="#575279", dim="#9893a5", blue="#286983", purple="#907aa9",
        teal="#56949f", yellow="#ea9d34", pink="#b4637a", green="#56949f",
        orange="#d7827e", red="#b4637a", cyan="#56949f", dark=False,
    ),
    "solarized-dark": Theme(
        name="solarized-dark", bg="#002b36", panel="#073642", border="#0f4a5a",
        fg="#93a1a1", dim="#586e75", blue="#268bd2", purple="#6c71c4",
        teal="#2aa198", yellow="#b58900", pink="#d33682", green="#859900",
        orange="#cb4b16", red="#dc322f", cyan="#2aa198",
    ),
    "solarized-light": Theme(
        name="solarized-light", bg="#fdf6e3", panel="#eee8d5", border="#d3cbb7",
        fg="#586e75", dim="#93a1a1", blue="#268bd2", purple="#6c71c4",
        teal="#2aa198", yellow="#b58900", pink="#d33682", green="#859900",
        orange="#cb4b16", red="#dc322f", cyan="#2aa198", dark=False,
    ),
    "github-dark": Theme(
        name="github-dark", bg="#0d1117", panel="#161b22", border="#30363d",
        fg="#c9d1d9", dim="#8b949e", blue="#58a6ff", purple="#bc8cff",
        teal="#39c5cf", yellow="#d29922", pink="#f778ba", green="#3fb950",
        orange="#db6d28", red="#f85149", cyan="#39c5cf",
        heat=("#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"),
    ),
    "github-light": Theme(
        name="github-light", bg="#ffffff", panel="#f6f8fa", border="#d0d7de",
        fg="#1f2328", dim="#656d76", blue="#0969da", purple="#8250df",
        teal="#1b7c83", yellow="#9a6700", pink="#bf3989", green="#1a7f37",
        orange="#bc4c00", red="#cf222e", cyan="#1b7c83", dark=False,
        heat=("#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"),
    ),
    "monokai": Theme(
        name="monokai", bg="#272822", panel="#1e1f1c", border="#3e3d32",
        fg="#f8f8f2", dim="#75715e", blue="#66d9ef", purple="#ae81ff",
        teal="#a1efe4", yellow="#e6db74", pink="#f92672", green="#a6e22e",
        orange="#fd971f", red="#f92672", cyan="#66d9ef",
    ),
    "everforest-dark": Theme(
        name="everforest-dark", bg="#2d353b", panel="#232a2e", border="#475258",
        fg="#d3c6aa", dim="#859289", blue="#7fbbb3", purple="#d699b6",
        teal="#83c092", yellow="#dbbc7f", pink="#e67e80", green="#a7c080",
        orange="#e69875", red="#e67e80", cyan="#7fbbb3",
    ),
    "kanagawa": Theme(
        name="kanagawa", bg="#1f1f28", panel="#16161d", border="#363646",
        fg="#dcd7ba", dim="#727169", blue="#7e9cd8", purple="#957fb8",
        teal="#7aa89f", yellow="#e6c384", pink="#d27e99", green="#98bb6c",
        orange="#ffa066", red="#e82424", cyan="#7fb4ca",
    ),
}

# Which light palette pairs naturally with which dark one, for the
# `theme.light = "auto"` shortcut.
LIGHT_PARTNER = {
    "tokyo-night": "tokyo-day",
    "catppuccin-mocha": "catppuccin-latte",
    "gruvbox-dark": "gruvbox-light",
    "rose-pine": "rose-pine-dawn",
    "solarized-dark": "solarized-light",
    "github-dark": "github-light",
}


def get_theme(name, overrides=None):
    """Look a palette up by name and apply any [theme.colors] overrides."""
    key = (name or "tokyo-night").strip().lower()
    if key not in PALETTES:
        known = ", ".join(sorted(PALETTES))
        raise KeyError(f"unknown theme {name!r}; known themes: {known}")
    theme = PALETTES[key]
    if overrides:
        clean = {}
        for field_name, value in overrides.items():
            field_name = field_name.replace("-", "_")
            if field_name in Theme.__dataclass_fields__ and isinstance(value, str):
                clean[field_name] = value
        if clean:
            theme = replace(theme, **clean)
    return theme


# --- drawing helpers -------------------------------------------------------

def svg_open(width, height, label, extra_attrs=""):
    """The root element. width/height are the CSS pixel size GitHub shows."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:g}" height="{height:g}" '
        f'viewBox="0 0 {width:g} {height:g}" role="img" aria-label="{esc(label)}"{extra_attrs}>'
    )


def card(theme, width, height, radius=10):
    """The rounded panel every card is drawn on."""
    return (
        f'<rect x="0.5" y="0.5" width="{width - 1:g}" height="{height - 1:g}" '
        f'rx="{radius}" fill="{theme.bg}" stroke="{theme.border}" stroke-width="1"/>'
    )


def title_bar(theme, width, label, y=26):
    """A terminal-style title bar: three dots and a window title."""
    dots = "".join(
        f'<circle cx="{cx}" cy="{y - 5}" r="4.5" fill="{colour}"/>'
        for cx, colour in ((22, theme.pink), (40, theme.yellow), (58, theme.teal))
    )
    return (
        f"{dots}"
        f'<text x="{width / 2:g}" y="{y}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="11" fill="{theme.dim}">{esc(label)}</text>'
        f'<line x1="12" y1="{y + 12}" x2="{width - 12:g}" y2="{y + 12}" '
        f'stroke="{theme.border}" stroke-width="1"/>'
    )


def text(theme, x, y, content, size=11.5, colour=None, weight=None, anchor=None, extra=""):
    """A monospace text node in the theme's font stack."""
    attrs = [
        f'x="{x:g}"', f'y="{y:g}"', f'font-family="{MONO}"', f'font-size="{size:g}"',
        f'fill="{colour or theme.fg}"',
    ]
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    if extra:
        attrs.append(extra)
    return f"<text {' '.join(attrs)}>{esc(content)}</text>"


def reduced_motion_css(selectors=".a"):
    """A style block that freezes CSS animations for readers who asked for that.

    SMIL animations cannot be gated by a media query, so panels that must
    respect prefers-reduced-motion are drawn with CSS keyframes and this block.
    """
    return (
        f"@media (prefers-reduced-motion:reduce){{{selectors}{{animation:none!important;"
        f"opacity:1!important;transform:none!important}}}}"
    )


STILL_CSS = ".s{display:none}@media (prefers-reduced-motion:reduce){.m{display:none}.s{display:inline}}"


def still_layer(motion, still):
    """Wrap a moving group and its frozen twin so reduced-motion shows the twin.

    SMIL cannot be paused by a media query, but `display` is not animated,
    so toggling which group is displayed is guaranteed to work everywhere.
    Emit STILL_CSS once in the file's <style> when using this.
    """
    return f'<g class="m">{motion}</g><g class="s">{still}</g>'


PROMPT_TAIL = ":~$ "


def prompt(theme, user, host, command):
    """Return the coloured tspans for a shell prompt line: user@host:~$ cmd.

    The same shape the README headings use, so the page reads as one shell.
    """
    return (
        f'<tspan fill="{theme.green}">{esc(user)}</tspan>'
        f'<tspan fill="{theme.dim}">@</tspan>'
        f'<tspan fill="{theme.purple}">{esc(host)}</tspan>'
        f'<tspan fill="{theme.dim}">{PROMPT_TAIL}</tspan>'
        f'<tspan fill="{theme.fg}">{esc(command)}</tspan>'
    )


def prompt_length(user, host, command=""):
    """Column count of the prompt line, for placing a cursor after it."""
    return len(user) + 1 + len(host) + len(PROMPT_TAIL) + len(command)
