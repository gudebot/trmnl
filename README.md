# TRMNL grayscale artwork skill

A portable agent skill for creating artwork **for an exact reserved area** of a TRMNL X display, or explicitly creating a full-screen illustration. It is designed for layouts where the picture shares the screen with existing content such as a quote and weekly dinners.

The root [SKILL.md](SKILL.md) is the agent entry point. Supporting material is in `scripts/`, `references/` and `assets/`. Existing artwork at the repository root is preserved unchanged.

## What it does

- Guides original image creation with the agent's already approved image generator or appropriate locally executed art code.
- Requires a region's explicit width/height; a picture panel is an art tile, **not** a replacement screen containing your other widgets.
- Prepares exact-size, 16-gray, **true 4-bit grayscale PNG** output; full-screen TRMNL X is **1872×1404**, and exports must be **smaller than 750,000 bytes**.[1][2]
- Preserves aspect ratio, offers explicit contain/crop and optional Floyd–Steinberg dithering, composites transparency on white and strips metadata.
- Independently checks PNG bytes, CRCs, dimensions, filters, bounded decompression and the size cap.
- Makes an optional local placement preview with every decoded pixel **outside** the specified art box unchanged.

It does **not** add an image-generation service, buy image credits, upload artwork, alter a plugin/layout, merge a PR or install itself into an agent. There is no device API key, account identifier or network client in the converter.

## Requirements

Python 3.10+ and Pillow 10+. Locally exercised with Python 3.14.7 and Pillow 12.3.0; the minimum supported versions were not separately tested. Dependency requirements are declared in [requirements.txt](requirements.txt); use an existing suitable environment or obtain approval before any installation. ImageMagick is not needed. Validation and prompt construction themselves use only the Python standard library; preparation and placement use Pillow.

An AI-art request also needs an available, approved image-generation tool. A skill file or prompt alone does not grant that capability. **Preferred: OpenAI's image generation with GPT-6.1 Sol (`gpt-6.1-sol`)** writing and refining the prompt; see [SKILL.md](SKILL.md#2-actually-create-the-artwork). The bundled example script only converts existing repository artwork; it does not generate anything.

## Quick start: artwork for one region

First measure or explicitly choose the art tile's native pixel dimensions. **800×1190 below is the picture panel measured on [the example menu screen](examples/menu-screen.png) with a one-line quote.** Remeasure for your own layout; see [targets and measurement](references/targets.md).

```sh
# Prints a prompt; use the agent's approved image generator to create out/source.png.
python scripts/trmnl_art.py prompt --brief "a calm autumn illustration with a clear botanical silhouette" --size 800x1190

# Or prepare one of the existing example images. The original is never overwritten.
python scripts/trmnl_art.py prepare Cinnamoroll_Halloween.png out/picture.png --size 800x1190
python scripts/trmnl_art.py validate out/picture.png --size 800x1190
```

`prepare` prints JSON with the measured output dimensions, bit depth, bytes, hash and used gray count. The PNG has at most 16 possible grays; an illustration need not use all 16.

Options:

```sh
# Explicit crop, not stretching; inspect subject edges afterward.
python scripts/trmnl_art.py prepare out/source.png out/crop.png --size 800x1190 --fit cover

# Optional texture treatment; default is no dithering.
python scripts/trmnl_art.py prepare out/source.png out/tonal.png --size 800x1190 --dither floyd-steinberg --contrast 1.1 --margin 0.06

# Only when a full-screen illustration is genuinely wanted; not your menu layout.
python scripts/trmnl_art.py prepare out/source.png out/full-art.png --full-screen
```

Outputs are exclusively created: choose a new filename rather than overwrite a previous export. The helper never silently lowers resolution to meet the byte cap. A stricter `--max-bytes` is allowed, but the hardware cap cannot be raised.

## Check placement without changing quotes or dinners

Use an approved local reference frame and its verified art box:

```sh
python scripts/trmnl_art.py preview examples/menu-screen.png out/picture.png out/placement.png --box 22,22,800,1190
```

The box is **X,Y,WIDTH,HEIGHT in reference-image pixels**. `22,22,800,1190` is the measured picture panel of the example screen; use your own frame and box for other layouts. Asset dimensions must match exactly; references and artwork must be static local PNG/JPEG/WebP files. Pixels outside the box are copied unchanged, including color if present. The preview is an ordinary RGBA PNG for inspection, **not** a validated device-ready render or a live screen update.

A compatible art asset does not guarantee the final plugin composite fits the firmware's full-render limit. Local preview also does not establish how the physical panel looks.

## Examples and testing

See [examples](examples/README.md): a real menu screen (published with its owner's permission; it shows that day's quote and dinners), the repository's Gudetama artwork prepared for its picture panel, and a placement preview that reproduces that screen. They contain no account ID, device key or plugin markup.

```sh
python scripts/make_examples.py --output-dir out/examples
python -m unittest discover -s tests -v
```

Tests cover native/full-screen and region sizes, exact gray-4 bytes decoded independently by Pillow, all five PNG filters, CRC/corruption/bounds, alpha and EXIF handling, contain/crop, dithering, output preservation, oversize rejection, prompt semantics and pixel-for-pixel preservation outside the art box. A real existing repository image is also converted without modifying its original.

## Use from an agent

Read [SKILL.md](SKILL.md) and follow your agent platform's normal reviewed skill-import process. Keep the skill's explicitly linked `scripts/`, `assets/` and `references/` files together. Install/enable it only for the agent you actually approve; cloning this repo is not an installation. Do not broadly reseed unrelated skills.

For new work: establish the region, create the real image, prepare it, validate it, visually inspect it, then return the file. Publication and display changes are separate approvals. Keep private/new exports in ignored `out/` and stage only explicitly reviewed public files.

## Sources

[1] [Official TRMNL ImageMagick/image-format guide](https://docs.trmnl.com/go/diy/imagemagick-guide).

[2] [Official TRMNL device model registry](https://trmnl.com/api/models); the `v2` model is TRMNL X. The checked profile is reproduced in [assets/trmnl-x.json](assets/trmnl-x.json).
