"""The looping typewriter header.

Types each line out character by character, holds it with a blinking cursor,
backspaces it, then moves to the next line and repeats forever. The whole
sequence is one SMIL timeline per line with repeatCount="indefinite", because
SMIL has no way to loop a group; each animation runs the full cycle and
spends most of it parked at zero.
"""

from theme import MONO, card, esc, svg_open

DEFAULTS = {
    "height": 78,
    "font": 27,
    "per_char": 0.075,    # typing speed, seconds per character
    "erase_char": 0.028,  # backspacing is quicker than typing
    "hold": 1.7,
    "gap": 0.35,
    "blink": 0.5,
}


def columns(text):
    """Width in monospace columns, counting emoji as double width."""
    return sum(2 if ord(char) > 0x2500 else 1 for char in text)


def timeline(points, cycle):
    """Turn [(seconds, value), ...] into SMIL values/keyTimes attributes."""
    values = ";".join(str(value) for _, value in points)
    keys = ";".join(f"{min(time / cycle, 1):.5f}" for time, _ in points)
    return values, keys


def render(theme, config, width=860):
    lines = list(config.get("lines") or [])
    if not lines:
        raise ValueError("[typing] needs at least one line")
    opts = {**DEFAULTS, **{k: v for k, v in config.items() if k in DEFAULTS}}
    height = opts["height"]
    font = opts["font"]
    adv = font * 0.6
    baseline = round(height * 0.64)
    per_char, erase_char = opts["per_char"], opts["erase_char"]
    hold, gap, blink = opts["hold"], opts["gap"], opts["blink"]
    colour = theme.colour(config.get("color"), theme.accent)

    widths = [columns(line) for line in lines]
    slots = [count * per_char + hold + count * erase_char + gap for count in widths]
    cycle = sum(slots)

    out = [svg_open(width, height, " / ".join(lines)), card(theme, width, height), "<defs>"]

    starts, running = [], 0.0
    for slot in slots:
        starts.append(running)
        running += slot

    for index, line in enumerate(lines):
        count = widths[index]
        run = count * adv
        left = (width - run) / 2
        start = starts[index]
        type_dur = count * per_char

        points = [(0.0, 0)]
        if start > 0:
            points.append((start, 0))
        for step in range(1, count + 1):
            points.append((start + step * per_char, round(step * adv, 2)))
        points.append((start + type_dur + hold, round(run, 2)))
        for step in range(1, count + 1):
            points.append((start + type_dur + hold + step * erase_char, round((count - step) * adv, 2)))
        points.append((cycle, 0))

        values, keys = timeline(points, cycle)
        out.append(
            f'<clipPath id="t{index}">'
            f'<rect x="{left:.2f}" y="0" width="0" height="{height}">'
            f'<animate attributeName="width" calcMode="discrete" '
            f'values="{values}" keyTimes="{keys}" dur="{cycle:.3f}s" '
            f'repeatCount="indefinite"/>'
            f"</rect></clipPath>"
        )
    out.append("</defs>")

    for index, line in enumerate(lines):
        count = widths[index]
        run = count * adv
        left = (width - run) / 2
        start = starts[index]
        type_dur = count * per_char

        # textLength pins the advance so the clip edge always lands on a
        # character boundary, whatever monospace font the reader has.
        out.append(
            f'<text clip-path="url(#t{index})" x="{left:.2f}" y="{baseline}" '
            f'xml:space="preserve" font-family="{MONO}" font-size="{font}" '
            f'font-weight="600" fill="{colour}" textLength="{run:.2f}" '
            f'lengthAdjust="spacing">{esc(line)}</text>'
        )

        cursor = [(0.0, 0)]
        if start > 0:
            cursor.append((start, 0))
        cursor.append((start, 1))
        cursor.append((start + type_dur, 1))
        blink_at, state = start + type_dur, 0
        while blink_at < start + type_dur + hold:
            cursor.append((blink_at, state))
            state = 1 - state
            blink_at += blink
        cursor.append((start + type_dur + hold, 1))
        cursor.append((start + type_dur + hold + count * erase_char, 0))
        cursor.append((cycle, 0))
        opacity, opacity_keys = timeline(cursor, cycle)

        moves = [(0.0, round(left, 2))]
        if start > 0:
            moves.append((start, round(left, 2)))
        for step in range(1, count + 1):
            moves.append((start + step * per_char, round(left + step * adv, 2)))
        moves.append((start + type_dur + hold, round(left + run, 2)))
        for step in range(1, count + 1):
            moves.append((start + type_dur + hold + step * erase_char, round(left + (count - step) * adv, 2)))
        moves.append((cycle, round(left, 2)))
        xs, x_keys = timeline(moves, cycle)

        out.append(
            f'<rect y="{baseline - font + 5}" width="{adv:.2f}" '
            f'height="{font}" fill="{colour}" opacity="0" x="{left:.2f}">'
            f'<animate attributeName="x" calcMode="discrete" values="{xs}" '
            f'keyTimes="{x_keys}" dur="{cycle:.3f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" calcMode="discrete" '
            f'values="{opacity}" keyTimes="{opacity_keys}" '
            f'dur="{cycle:.3f}s" repeatCount="indefinite"/>'
            f"</rect>"
        )

    out.append("</svg>")
    return "\n".join(out) + "\n"
