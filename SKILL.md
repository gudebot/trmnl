---
name: trmnl-grayscale
description: "Use when creating greyscale art for TRMNL X. Generate region-only or full-screen artwork, then export and verify native 16-gray PNGs without changing the device or surrounding layout."
license: MIT
compatibility: "Python 3.10+ and Pillow 10+. An already approved image-generation tool, or locally executed art code, is needed to create original artwork. No network or device access is required for conversion."
---

# TRMNL grayscale artwork

Create **artwork**, not a replacement dashboard. Support one reserved picture region (for example the picture panel beside a quote and weekly dinners) or an explicitly requested whole-screen illustration. This skill does not install tools, provide an image-generation service, upload anything, or activate a device.

Local tools: [converter / validator / prompt / preview](scripts/trmnl_art.py) and [example builder](scripts/make_examples.py) (prepares existing repository artwork for the example screen).

## 1. Establish the art region before generating

- Ask whether this is a picture-region asset or full-screen artwork. For a screen that already contains quotes/dinners, default to **picture-region intent**, never default to a full-screen output size.
- Obtain **native pixel width and height** from a measured current layout, an explicit user choice, or a trusted annotated reference. Do not guess from a verbal description such as “top-right square”, or use a source image's size as the slot size. When the user's description and the current screen disagree, show them the measured screen and ask. The helper requires `--size WIDTHxHEIGHT` or explicit `--full-screen`.
- A region's location is independent of its image dimensions. Record X/Y only for an optional placement preview. Do not draw coordinates, the rest of the screen, quotes, dinners, dates, UI or a device mockup into the artwork.
- For responsive layouts, border/content bounds, preview scaling and quote wrapping can change the available area. Read [region measurement](references/targets.md) before converting CSS/screenshot pixels. If the saved markup and physical description disagree, do not silently move the image or claim a verified preset.
- Read the [model profile](assets/trmnl-x.json). Supported full-screen target is landscape TRMNL X: 1872×1404, 4-bit grayscale / 16 grays, PNG smaller than 750,000 bytes. This is not the 800×480 OG profile.

## 2. Actually create the artwork

Read [art direction](references/art-direction.md). The house style is a **cute cartoon illustration: bold clean black outlines, flat simple shading, strong light/dark contrast, a plain white background**, composed for the target's shape (a tall panel gets a tall, stacked scene). This style was chosen after a real test on the device's 800×1190 panel and reads well in 16 grays.

The prompt helper writes that style for the target's shape:

```sh
python scripts/trmnl_art.py prompt --brief "two cute cartoon characters sharing a holiday feast" --size 800x1190
```

**800×1190 is the picture panel measured on [the example menu screen](examples/menu-screen.png) with a one-line quote. It is not a preset for other layouts; remeasure.** The command prints a prompt, not an image. It names the image tool's closest shape (`portrait` 2:3 for this panel), so the subject survives the contain-fit.

**Preferred generator: OpenAI's image generation, with GPT-6.1 Sol (`gpt-6.1-sol`) as the model that writes and refines the prompt and calls the image tool.** GPT-6.1 Sol outputs text, not pixels: in OpenAI's Responses API it drives the hosted `image_generation` tool, and a GPT Image model renders the picture. Record both the orchestrating model and the image model that rendered it. Text-only models, including Claude, cannot produce images; a drawing coded by such a model is procedural art, not generated art, and must not be substituted for a requested generated image. Use another generator only when the user chooses it.

Use the generator through an **already available, approved** route with the actual brief and target ratio. If the generator cannot use the exact dimensions, choose its closest supported aspect ratio (2:3 portrait for an 800×1190 panel) and prepare the resulting file below. Do not claim creation succeeded until an image file really exists.

Workflow that produced an accepted image: (1) a one-off agent on GPT-6.1 Sol receives the subject and the helper's style rules, writes the final prompt and calls the image tool once with `portrait`; (2) prepare the result (section 3); (3) a vision-capable model reviews the **prepared 16-gray file**, not the colour original, with the checklist from `python scripts/trmnl_art.py review-prompt --brief "..." --size 800x1190`, and answers PASS or REDO; (4) show the user the original, the 16-gray file and a placement preview. A REDO goes back to step 1 with the reason. Cap the attempts (two generations) and report what each one cost.

**Corrections to a picture the user liked** ("remove the leaves", "swap the rolls for X", "turn him over") are edits, not new pictures. The same GPT-6.1 Sol agent calls the image tool in edit mode: it passes the **colour original** as the input image (in Hermes, `image_generate` with `image_url`; in the OpenAI API, the GPT Image edit endpoint). It lists only the requested changes and adds "keep everything else the same". That way the characters, pose, layout and style stay as they were, while a new generation would redraw the whole scene. Prepare the edited original as usual. Then review the old and new 16-gray files side by side (BEFORE | AFTER), asking, change by change, whether each one was made and whether anything else changed.

If there is no suitable tool or spending/upload approval, report that specific blocker. Never install tools, spend credits, send private reference images, invent a generated result, or substitute a test pattern or code-drawn picture for requested AI artwork.

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

Return the actual artwork, dimensions, byte size, gray/bit-depth validator result, fit/dither choices and any crop/geometry limitations. Distinguish generated art, prepared asset, local composition and physically observed display. Never publish a private reference frame, household content, prompt, report, credential or signed URL. Keep new outputs under ignored `out/` unless the user explicitly approves publishing those exact files. When publishing to this repository, commit only the prepared 16-gray file, one per picture, to `images/YYYY-MM/` for the month it is for (for example `images/2026-11/`). Leave the colour original out of the repository.

Device/plugin/playlist changes, merges, skill installation and paid image calls require their own approval. This repository ships no uploader and needs no TRMNL key. Never call the playlist-advancing `/api/display` just to inspect an image. Source/render/fetch timestamps and a physical observation are different evidence.
