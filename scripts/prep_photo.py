#!/usr/bin/env python3
"""Prepare a photo so it converts to readable ASCII.

A flatly lit face converts to a dark, unreadable blob. Three steps fix that:

  1. Remove the background with rembg so the subject is isolated.
  2. Boost local contrast with OpenCV's CLAHE, which is what gives a flat face
     real highlights and shadows.
  3. Composite onto pure white so the background maps to the blank end of the
     ramp and prints as spaces.

This runs locally, once per photo. The daily workflow never touches it, so
opencv and rembg stay out of the automation's dependencies.

    pip install pillow numpy opencv-python rembg
    python scripts/prep_photo.py source-photo.jpg
    python scripts/make_ascii_svg.py source-prepped.png
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "source-prepped.png"


def cut_out(image):
    from rembg import remove

    return remove(image.convert("RGBA"))


def on_white(image):
    white = Image.new("RGBA", image.size, (255, 255, 255, 255))
    white.alpha_composite(image)
    return white.convert("L")


def boost(gray, clip=2.6, tile=8):
    import cv2

    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(tile, tile))
    return Image.fromarray(clahe.apply(np.array(gray)))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    source = Path(sys.argv[1])
    if not source.exists():
        print(f"no such file: {source}")
        return 1

    image = Image.open(source)
    image = cut_out(image)
    gray = on_white(image)
    gray = boost(gray)

    # Square it off so the character grid does not stretch the face.
    side = min(gray.size)
    left = (gray.width - side) // 2
    top = (gray.height - side) // 2
    gray = gray.crop((left, top, left + side, top + side))

    gray.save(OUT)
    print(f"{OUT}: {gray.size[0]}x{gray.size[1]}")
    print("now run: python scripts/make_ascii_svg.py source-prepped.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
