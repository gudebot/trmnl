#!/usr/bin/env python3
"""Create explicitly synthetic procedural art + a top-right local placement demo.

Not an AI-generation service, a current-layout measurement or a live device write.
All output paths are exclusive: existing files are never overwritten.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trmnl_art import ArtError, create_output, prepare, preview


BOX = (1200, 80, 576, 576)  # Illustrative only; never a personal/live preset.


def save_new(image, path):
    buffer = io.BytesIO()
    image.info.clear()
    image.save(buffer, format="PNG")
    create_output(path, buffer.getvalue())


def label(image, xy, text, scale=3, color=(30, 30, 30)):
    """Portable bitmap label: no external fonts, downloads or operating-system paths."""
    font = ImageFont.load_default()
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    mask = Image.new("L", (max(1, int(right - left)), max(1, int(bottom - top))), 0)
    ImageDraw.Draw(mask).text((-left, -top), text, fill=255, font=font)
    mask = mask.resize((mask.width * scale, mask.height * scale), Image.Resampling.NEAREST)
    image.paste(color, xy, mask)


def botanical():
    image = Image.new("RGB", (1000, 1000), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((220, 840, 780, 890), fill=(238, 238, 238))
    draw.line([(495, 840), (500, 170)], fill=(34, 34, 34), width=17)
    for y, gray in ((280, 153), (430, 187), (580, 119), (730, 170)):
        draw.ellipse((190, y - 110, 490, y + 15), fill=(gray, gray, gray), outline=(34, 34, 34), width=7)
        draw.line([(220, y - 60), (500, y + 10)], fill=(51, 51, 51), width=6)
        draw.ellipse((510, y - 180, 810, y - 55), fill=(221, 221, 221), outline=(34, 34, 34), width=7)
        draw.line([(500, y + 10), (780, y - 120)], fill=(51, 51, 51), width=6)
    draw.ellipse((448, 116, 552, 230), fill=(102, 102, 102), outline=(17, 17, 17), width=7)
    return image


def reference():
    image = Image.new("RGB", (1872, 1404), "white")
    draw = ImageDraw.Draw(image)
    label(image, (100, 75), "SYNTHETIC REGION DEMO - NOT A LIVE SCREEN", scale=3)
    draw.rounded_rectangle((70, 160, 1090, 830), radius=18, outline=(85, 85, 85), width=4)
    label(image, (110, 195), "EXISTING DINNER CONTENT", scale=3)
    for index, name in enumerate(("MON - sample dinner", "TUE - sample dinner", "WED - sample dinner", "THU - sample dinner", "FRI - sample dinner")):
        y = 300 + index * 95
        label(image, (130, y), name, scale=3)
        draw.line((110, y + 55, 1040, y + 55), fill=(204, 204, 204), width=2)
    draw.rounded_rectangle((1190, 70, 1786, 666), radius=12, outline=(119, 119, 119), width=3)
    label(image, (1210, 710), "ART REGION ONLY", scale=3)
    draw.rounded_rectangle((70, 930, 1786, 1250), radius=18, outline=(119, 119, 119), width=3)
    label(image, (130, 1020), "Existing quote stays outside the art box.", scale=3)
    label(image, (130, 1130), "These words and all other pixels are preserved.", scale=3)
    return image


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    out = args.output_dir
    names = ["botanical-source.png", "reference-frame.png", "square-art.png", "region-preview.png"]
    if any((out / name).exists() for name in names):
        parser.error("Choose a new output directory; this generator never overwrites exports.")
    try:
        save_new(botanical(), out / names[0])
        save_new(reference(), out / names[1])
        art = prepare(out / names[0], out / names[2], (576, 576), margin=0.04)
        placement = preview(out / names[1], out / names[2], out / names[3], BOX)
        print(json.dumps({"art": art, "placement": placement, "source": "local procedural botanical drawing", "aiGenerationServiceCalled": False, "liveLayoutReproduced": False}, sort_keys=True))
        return 0
    except (ArtError, OSError) as exc:
        parser.exit(2, f"ERROR: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
