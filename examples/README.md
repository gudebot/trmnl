# Examples on a real menu screen

- `menu-screen.png`: a real **1872×1404** TRMNL X frame, exactly as the device showed it on 2026-11-04 and read from the device's current-image endpoint (no playlist change). Left: a picture panel with the day's quote under it. Right: the week's dinners. Bottom: the "On the Menu" bar. It is published with the screen owner's permission as a reference layout. It is a 4-bit grayscale PNG with no metadata chunks.
- `region-art.png`: the repository's own `images/2026-10/gudetama-halloween-color-gray.png`, prepared by `trmnl_art.py prepare` to exactly **800×1190**, 16-gray/4-bit grayscale (contain fit, no dithering). No image service was called.
There is no separate preview image. The device was showing this same Gudetama picture that day, so placing `region-art.png` into the panel at **22,22** (box `22,22,800,1190`) reproduces `menu-screen.png`: only 187 of 2.6 million pixels differ, mostly at the panel's four rounded corners, which the device clips. `menu-screen.png` is therefore both the layout reference and what the placed art looks like, and that agreement is the check that the measured box is right (the tests rebuild the placement and compare it).

## How the box was measured

On `menu-screen.png` the panel's grey border is 4 native pixels (the layout's 2 px CSS border × 1.8): columns 18–21 and 822–825, rows 18–21 and 1212–1215. The image area inside it is **800×1190** at **22,22**. The layout gives the picture 44 % of the width, and the quote takes the space under it. A two-line quote makes the panel about 51 px shorter. The picture uses `object-fit: contain`, so art made at 800×1190 still fits whole. The panel also has rounded corners, so keep the subject a little away from the corners. Remeasure for any other layout; see [targets](../references/targets.md).

The Gudetama picture is a wide scene, so it shows letterboxed (white above and below) in the tall panel. New art drawn at the panel's portrait ratio (about 2:3) fills it.

Regenerate into a new, ignored output directory (this also writes `region-preview.png` there, a local placement for inspection that is not committed):

```sh
python scripts/make_examples.py --output-dir out/examples
```

The generator refuses to overwrite existing exports. Original root-level artwork is not modified. Validate the art (not the preview) with:

```sh
python scripts/trmnl_art.py validate examples/region-art.png --size 800x1190
```
