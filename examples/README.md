# Examples on a real menu screen

- `menu-screen.png`: a real **1872×1404** TRMNL X frame, exactly as the device showed it on 2026-11-04 and read from the device's current-image endpoint (no playlist change). Left: a picture panel with the day's quote under it. Right: the week's dinners. Bottom: the "On the Menu" bar. It is published with the screen owner's permission as a reference layout. It is a 4-bit grayscale PNG with no metadata chunks.
- `region-art.png`: exact **800×1190**, 16-gray/4-bit grayscale botanical art, drawn by local procedural code (not an AI image service). It is sized for that screen's picture panel.
- `region-preview.png`: `region-art.png` placed into the picture panel of `menu-screen.png` at **22,22** (box `22,22,800,1190`). Every pixel outside the box is identical to `menu-screen.png`. This is an ordinary RGBA PNG for inspection, **not** a device-ready render or a live screen update.

## How the box was measured

On `menu-screen.png` the panel's grey border is 4 native pixels (the layout's 2 px CSS border × 1.8): columns 18–21 and 822–825, rows 18–21 and 1212–1215. The image area inside it is **800×1190** at **22,22**. The layout gives the picture 44 % of the width, and the quote takes the space under it. A two-line quote makes the panel about 51 px shorter. The picture uses `object-fit: contain`, so art made at 800×1190 still fits whole. The panel also has rounded corners, so keep the subject a little away from the corners. Remeasure for any other layout; see [targets](../references/targets.md).

The image that was in the panel on that day was a wide picture, letterboxed in the tall panel. Art made at the panel's own portrait ratio fills it.

Regenerate into a new, ignored output directory:

```sh
python scripts/make_examples.py --output-dir out/examples
```

The generator refuses to overwrite existing exports. Original root-level artwork is not modified. Validate the art (not the preview) with:

```sh
python scripts/trmnl_art.py validate examples/region-art.png --size 800x1190
```
