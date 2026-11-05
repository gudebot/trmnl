#!/usr/bin/env python3
"""Prepare the repository's Gudetama artwork for a real TRMNL X menu screen's picture panel.

The reference is `examples/menu-screen.png`: a real screen as the device displayed it on
2026-11-04 (quote, weekly dinners and a picture panel), published with its owner's permission.
The art is the repository's existing `gudetama-halloween-color-gray.png`, converted by
`trmnl_art.py prepare`; no image service is called. Nothing is uploaded or sent to a device.
All output paths are exclusive: existing files are never overwritten.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trmnl_art import ArtError, prepare, preview

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "examples" / "menu-screen.png"
SOURCE = ROOT / "gudetama-halloween-color-gray.png"
# Picture panel measured on menu-screen.png: the 4 px grey border runs at x=18-21 and 822-825,
# y=18-21 and 1212-1215, so the image box inside it is 800x1190 at 22,22. It belongs to that screen
# (a one-line quote); remeasure for other layouts. See references/targets.md.
BOX = (22, 22, 800, 1190)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reference", type=Path, default=REFERENCE,
                        help="native 1872x1404 screen to place the art on (default: examples/menu-screen.png)")
    parser.add_argument("--source", type=Path, default=SOURCE,
                        help="artwork to prepare (default: the repository's Gudetama image)")
    args = parser.parse_args(argv)
    out = args.output_dir
    names = ["region-art.png", "region-preview.png"]
    if any((out / name).exists() for name in names):
        parser.error("Choose a new output directory; this generator never overwrites exports.")
    try:
        art = prepare(args.source, out / names[0], BOX[2:])
        placement = preview(args.reference, out / names[0], out / names[1], BOX)
        print(json.dumps({"art": art, "placement": placement, "box": list(BOX),
                          "reference": args.reference.name, "source": args.source.name,
                          "aiGenerationServiceCalled": False, "deviceChanged": False}, sort_keys=True))
        return 0
    except (ArtError, OSError) as exc:
        parser.exit(2, f"ERROR: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
