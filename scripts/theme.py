"""Shared Tokyo Night palette and SVG helpers.

Every SVG in this repo is self-contained: GitHub loads them through an <img>
tag, which means no external CSS, no fonts from the network and no scripts.
Anything that needs to move has to be a CSS keyframe or SMIL animation living
inside the file itself.
"""

# Tokyo Night
BG = "#1a1b27"
PANEL = "#1f2335"
BORDER = "#2f344d"
FG = "#a9b1d6"
DIM = "#565f89"
BLUE = "#70a5fd"
PURPLE = "#bf91f3"
TEAL = "#38bdae"
YELLOW = "#e0af68"
PINK = "#ff7a93"

# none -> brightest, in Tokyo Night blues so the heatmap sits with the rest
# of the profile instead of importing GitHub's green.
HEAT = ["#1e2235", "#243a63", "#2f5fa8", "#4d8fe0", "#70a5fd", "#a5d6ff"]

MONO = (
    "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
    "'DejaVu Sans Mono','Liberation Mono',monospace"
)

_ESCAPES = (
    ("&", "&amp;"),
    ("<", "&lt;"),
    (">", "&gt;"),
    ('"', "&quot;"),
)


def esc(text):
    """Escape text for use inside an SVG text node or attribute."""
    out = str(text)
    for raw, encoded in _ESCAPES:
        out = out.replace(raw, encoded)
    return out


def card(width, height, radius=10):
    """The rounded panel every card is drawn on."""
    return (
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" '
        f'rx="{radius}" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>'
    )


def title_bar(width, label, y=26):
    """A terminal-style title bar: three dots and a window title."""
    dots = "".join(
        f'<circle cx="{cx}" cy="{y - 5}" r="4.5" fill="{color}"/>'
        for cx, color in ((22, PINK), (40, YELLOW), (58, TEAL))
    )
    return (
        f"{dots}"
        f'<text x="{width / 2}" y="{y}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="11" fill="{DIM}">{esc(label)}</text>'
        f'<line x1="12" y1="{y + 12}" x2="{width - 12}" y2="{y + 12}" '
        f'stroke="{BORDER}" stroke-width="1"/>'
    )
