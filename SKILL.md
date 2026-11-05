---
name: trmnl-grayscale
description: "Use when creating greyscale art for TRMNL X. Generate region-only or full-screen artwork, then export and verify native 16-gray PNGs without changing the device or surrounding layout."
license: MIT
compatibility: "Python 3.10+ and Pillow 10+. An already approved image-generation tool, or locally executed art code, is needed to create original artwork. No network or device access is required for conversion."
---

# TRMNL grayscale artwork

Create **artwork**, not a replacement dashboard. Support one reserved picture region (for example the picture panel beside a quote and weekly dinners) or an explicitly requested whole-screen illustration. This skill does not install tools, provide an image-generation service, upload anything, or activate a device.

Local tools: [converter / validator / prompt / preview](scripts/trmnl_art.py) and [clearly labeled procedural example generator](scripts/make_examples.py).

## 1. Establish the art region before generating

- Ask whether this is a picture-region asset or full-screen artwork. For a screen that already contains quotes/dinners, default to **picture-region intent**, never default to a full-screen output size.
- Obtain **native pixel width and height** from a measured current layout, an explicit user choice, or a trusted annotated reference. Do not guess from a verbal description such as “top-right square”, or use a source image's size as the slot size. When the user's description and the current screen disagree, show them the measured screen and ask. The helper requires `--size WIDTHxHEIGHT` or explicit `--full-screen`.
- A region's location is independent of its image dimensions. Record X/Y only for an optional placement preview. Do not draw coordinates, the rest of the screen, quotes, dinners, dates, UI or a device mockup into the artwork.
- For responsive layouts, border/content bounds, preview scaling and quote wrapping can change the available area. Read [region measurement](references/targets.md) before converting CSS/screenshot pixels. If the saved markup and physical description disagree, do not silently move the image or claim a verified preset.
- Read the [model profile](assets/trmnl-x.json). Supported full-screen target is landscape TRMNL X: 1872×1404, 4-bit grayscale / 16 grays, PNG smaller than 750,000 bytes. This is not the 800×480 OG profile.

## 2. Actually create the artwork

Read [art direction](references/art-direction.md). Compose for the requested aspect ratio, bold enough for e-ink, with separated grays and breathing room around the subject.

A prompt helper is available:

```sh
python scripts/trmnl_art.py prompt --brief "a friendly autumn botanical illustration" --size 800x1190
```

**800×1190 is the picture panel measured on [the example menu screen](examples/menu-screen.png) with a one-line quote. It is not a preset for other layouts; remeasure.** The command prints a prompt, not an image. Use an **already available, approved** image generator with the actual brief and target ratio, or write and execute local Pillow/vector art code when appropriate. If the generator cannot use the exact dimensions, choose its closest supported aspect ratio and prepare the resulting file below. Do not claim creation succeeded until an image file really exists.

If there is no suitable tool or spending/upload approval, report that specific blocker. Never install tools, spend credits, send private reference images, invent a generated result, or substitute a test pattern for requested AI artwork. Procedural art is valid only when honestly identified and suitable for the brief.

## 3. Prepare and independently validate

```sh
python scripts/trmnl_art.py prepare out/source.png out/picture.png --size 800x1190
python scripts/trmnl_art.py validate out/picture.png --size 800x1190
```

- `contain` is the default: preserve the entire subject/aspect ratio on white. `--fit cover` is an explicit center crop; inspect it before accepting. Never stretch.
- `--dither none` is the default for line art/flat illustrations. Use `--dither floyd-steinberg` deliberately for photographic/tonal material; compare the visual result.
- Optional `--margin 0.06` adds white safety space. `--contrast` is explicit, not a license to crush features.
- The helper composites alpha onto white, applies EXIF orientation, strips metadata, writes true grayscale-4 PNG bytes and validates their dimensions, CRCs, scanline decode and size. It never overwrites an input or previous export.
- If a file is over the limit, simplify noise/dithering/composition; do not silently shrink the region, change the target or return an invalid image.
- A well-formed output proves file compatibility, not artistic quality or physical-panel appearance. Inspect the real image at approximately its display size, not only enlarged on a monitor.

Whole-screen art requires explicit intent:

```sh
python scripts/trmnl_art.py prepare out/source.png out/full-art.png --full-screen
```

## 4. Optional local placement preview

If an approved local reference and a verified native-image box are available:

```sh
python scripts/trmnl_art.py preview examples/menu-screen.png out/picture.png out/placement.png --box 22,22,800,1190
```

This box was measured on the example screen; for any other frame, measure its own box. The art must match the box exactly. The preview preserves decoded pixels outside the box, so quotes/menu remain untouched. It is an ordinary local preview, **not a device-ready full-screen export, upload, proof of deployment or camera observation**.

## 5. Return evidence; keep publication separate

Return the actual artwork, dimensions, byte size, gray/bit-depth validator result, fit/dither choices and any crop/geometry limitations. Distinguish generated art, prepared asset, local composition and physically observed display. Never publish a private reference frame, household content, prompt, report, credential or signed URL. Keep new outputs under ignored `out/` unless the user explicitly approves publishing those exact files.

Device/plugin/playlist changes, merges, skill installation and paid image calls require their own approval. This repository ships no uploader and needs no TRMNL key. Never call the playlist-advancing `/api/display` just to inspect an image. Source/render/fetch timestamps and a physical observation are different evidence.
