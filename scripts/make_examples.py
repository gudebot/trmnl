#!/usr/bin/env python3
"""Create procedural region art and place it on a real TRMNL X menu screen.

The reference is `examples/menu-screen.png`: a real screen as the device displayed it on
2026-11-04 (quote, weekly dinners and a picture panel), published with its owner's permission.
The art is local procedural drawing code, not an AI-generation service. Nothing is uploaded or
sent to a device. All output paths are exclusive: existing files are never overwritten.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trmnl_art import ArtError, create_output, prepare, preview

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "examples" / "menu-screen.png"
# Picture panel measured on menu-screen.png: the 4 px grey border runs at x=18-21 and 822-825,
# y=18-21 and 1212-1215, so the image box inside it is 800x1190 at 22,22. It belongs to that screen
# (a one-line quote); remeasure for other layouts. See references/targets.md.
BOX = (22, 22, 800, 1190)


def save_new(image, path):
    buffer = io.BytesIO()
    image.info.clear()
    image.save(buffer, format="PNG")
    create_output(path, buffer.getvalue())


def botanical(width=1000, height=1488):
    """A tall potted plant composed for a portrait picture panel (procedural, no fonts or network)."""
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    cx = width // 2
    ink = (34, 34, 34)
    # Pot and soil line.
    pot_top, pot_bottom = int(height * 0.80), int(height * 0.95)
    draw.polygon([(cx - 230, pot_top), (cx + 230, pot_top), (cx + 170, pot_bottom), (cx - 170, pot_bottom)],
                 fill=(170, 170, 170), outline=ink, width=9)
    draw.rectangle((cx - 255, pot_top - 55, cx + 255, pot_top), fill=(136, 136, 136), outline=ink, width=9)
    for x in range(cx - 150, cx + 151, 75):
        draw.line([(x, pot_top + 30), (x - 12, pot_bottom - 25)], fill=(119, 119, 119), width=6)
    # Stem.
    top = int(height * 0.13)
    draw.line([(cx, pot_top - 55), (cx - 8, top + 90)], fill=ink, width=18)
    # Alternating leaf pairs, larger near the base.
    leaf_ys = [int(height * f) for f in (0.70, 0.59, 0.48, 0.37, 0.27)]
    grays = (153, 187, 119, 204, 170)
    for i, (y, gray) in enumerate(zip(leaf_ys, grays)):
        span = 300 - i * 35
        h = 120 - i * 10
        left, right = (gray, gray, gray), (221, 221, 221) if i % 2 == 0 else (187, 187, 187)
        draw.ellipse((cx - span - 10, y - h, cx - 10, y + 10), fill=left, outline=ink, width=8)
        draw.line([(cx - span + 20, y - h // 2), (cx - 4, y + 4)], fill=(51, 51, 51), width=6)
        ry = y - 70
        draw.ellipse((cx + 10, ry - h, cx + span + 10, ry + 10), fill=right, outline=ink, width=8)
        draw.line([(cx + 4, ry + 4), (cx + span - 20, ry - h // 2)], fill=(51, 51, 51), width=6)
    # Flower head.
    fy = top + 40
    for dx, dy in ((-70, 0), (70, 0), (0, -70), (0, 70), (-50, -50), (50, -50), (-50, 50), (50, 50)):
        draw.ellipse((cx + dx - 62, fy + dy - 62, cx + dx + 62, fy + dy + 62), fill=(238, 238, 238), outline=ink, width=7)
    draw.ellipse((cx - 52, fy - 52, cx + 52, fy + 52), fill=(85, 85, 85), outline=(17, 17, 17), width=8)
    return image


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reference", type=Path, default=REFERENCE,
                        help="native 1872x1404 screen to place the art on (default: examples/menu-screen.png)")
    args = parser.parse_args(argv)
    out = args.output_dir
    names = ["botanical-source.png", "region-art.png", "region-preview.png"]
    if any((out / name).exists() for name in names):
        parser.error("Choose a new output directory; this generator never overwrites exports.")
    try:
        save_new(botanical(), out / names[0])
        art = prepare(out / names[0], out / names[1], BOX[2:], margin=0.04)
        placement = preview(args.reference, out / names[1], out / names[2], BOX)
        print(json.dumps({"art": art, "placement": placement, "box": list(BOX),
                          "reference": args.reference.name, "source": "local procedural botanical drawing",
                          "aiGenerationServiceCalled": False, "deviceChanged": False}, sort_keys=True))
        return 0
    except (ArtError, OSError) as exc:
        parser.exit(2, f"ERROR: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
