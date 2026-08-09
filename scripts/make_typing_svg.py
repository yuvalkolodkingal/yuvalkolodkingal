#!/usr/bin/env python3
"""Build the looping typewriter header as an animated SVG.

Types each line out character by character, holds it with a blinking cursor,
backspaces it, then moves to the next line and repeats forever.

The whole sequence is encoded as one SMIL timeline per line with
repeatCount="indefinite", because SMIL has no way to loop a group. Each
animation runs the full cycle length and spends most of it parked at zero.

Usage:
    python scripts/make_typing_svg.py
"""

from pathlib import Path

from theme import BLUE, MONO, card, esc

OUT = Path(__file__).resolve().parent.parent / "assets" / "typing-header.svg"

WIDTH = 860
HEIGHT = 78
FONT = 27
ADV = FONT * 0.6
BASELINE = 50

PER_CHAR = 0.075     # typing speed
ERASE_CHAR = 0.028   # backspacing is quicker than typing
HOLD = 1.7
GAP = 0.35
BLINK = 0.5

LINES = [
    "Hi there, I'm Yuval \U0001f44b",
    "Lab Automation & Synthetic Biology",
    "Full-Stack Development",
]


def columns(text):
    """Width in monospace columns, counting emoji as double width."""
    return sum(2 if ord(char) > 0x2500 else 1 for char in text)


def timeline(points, cycle):
    """Turn [(seconds, value), ...] into SMIL values/keyTimes attributes."""
    values = ";".join(str(value) for _, value in points)
    keys = ";".join(f"{min(time / cycle, 1):.5f}" for time, _ in points)
    return values, keys


def build():
    widths = [columns(line) for line in LINES]
    slots = [count * PER_CHAR + HOLD + count * ERASE_CHAR + GAP for count in widths]
    cycle = sum(slots)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        f'aria-label="{esc(" / ".join(LINES))}">',
        card(WIDTH, HEIGHT),
        "<defs>",
    ]

    starts = []
    running = 0.0
    for slot in slots:
        starts.append(running)
        running += slot

    # Clip rects: one per line, each revealing its text left to right.
    for index, line in enumerate(LINES):
        count = widths[index]
        run = count * ADV
        left = (WIDTH - run) / 2
        start = starts[index]
        type_dur = count * PER_CHAR

        points = [(0.0, 0)]
        if start > 0:
            points.append((start, 0))
        for step in range(1, count + 1):
            points.append((start + step * PER_CHAR, round(step * ADV, 2)))
        points.append((start + type_dur + HOLD, round(run, 2)))
        for step in range(1, count + 1):
            points.append(
                (
                    start + type_dur + HOLD + step * ERASE_CHAR,
                    round((count - step) * ADV, 2),
                )
            )
        points.append((cycle, 0))

        values, keys = timeline(points, cycle)
        out.append(
            f'<clipPath id="t{index}">'
            f'<rect x="{left:.2f}" y="0" width="0" height="{HEIGHT}">'
            f'<animate attributeName="width" calcMode="discrete" '
            f'values="{values}" keyTimes="{keys}" dur="{cycle:.3f}s" '
            f'repeatCount="indefinite"/>'
            f"</rect></clipPath>"
        )

    out.append("</defs>")

    for index, line in enumerate(LINES):
        count = widths[index]
        run = count * ADV
        left = (WIDTH - run) / 2
        start = starts[index]
        type_dur = count * PER_CHAR

        # textLength pins the advance so the clip edge always lands on a
        # character boundary, whatever monospace font the reader has.
        out.append(
            f'<text clip-path="url(#t{index})" x="{left:.2f}" y="{BASELINE}" '
            f'xml:space="preserve" font-family="{MONO}" font-size="{FONT}" '
            f'font-weight="600" fill="{BLUE}" textLength="{run:.2f}" '
            f'lengthAdjust="spacing">{esc(line)}</text>'
        )

        # Cursor: solid while typing and erasing, blinking through the hold.
        cursor = [(0.0, 0)]
        if start > 0:
            cursor.append((start, 0))
        cursor.append((start, 1))
        cursor.append((start + type_dur, 1))
        blink_at = start + type_dur
        state = 0
        while blink_at < start + type_dur + HOLD:
            cursor.append((blink_at, state))
            state = 1 - state
            blink_at += BLINK
        cursor.append((start + type_dur + HOLD, 1))
        cursor.append((start + type_dur + HOLD + count * ERASE_CHAR, 0))
        cursor.append((cycle, 0))

        opacity, opacity_keys = timeline(cursor, cycle)

        moves = [(0.0, round(left, 2))]
        if start > 0:
            moves.append((start, round(left, 2)))
        for step in range(1, count + 1):
            moves.append((start + step * PER_CHAR, round(left + step * ADV, 2)))
        moves.append((start + type_dur + HOLD, round(left + run, 2)))
        for step in range(1, count + 1):
            moves.append(
                (
                    start + type_dur + HOLD + step * ERASE_CHAR,
                    round(left + (count - step) * ADV, 2),
                )
            )
        moves.append((cycle, round(left, 2)))
        xs, x_keys = timeline(moves, cycle)

        out.append(
            f'<rect y="{BASELINE - FONT + 5}" width="{ADV:.2f}" '
            f'height="{FONT}" fill="{BLUE}" opacity="0" x="{left:.2f}">'
            f'<animate attributeName="x" calcMode="discrete" values="{xs}" '
            f'keyTimes="{x_keys}" dur="{cycle:.3f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" calcMode="discrete" '
            f'values="{opacity}" keyTimes="{opacity_keys}" '
            f'dur="{cycle:.3f}s" repeatCount="indefinite"/>'
            f"</rect>"
        )

    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"{OUT}: {len(LINES)} lines")


if __name__ == "__main__":
    main()
