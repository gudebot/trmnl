#!/usr/bin/env python3
"""Local-only TRMNL X art preparation, independent PNG validation and placement preview.

Requires Pillow for decoding/resizing/dithering; the 4-bit PNG codec is stdlib.
No network requests, credentials, uploads, model calls or device writes.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import sys
import tempfile
import warnings
import zlib

WIDTH, HEIGHT, MAX_BYTES = 1872, 1404, 750_000
MAX_INPUT_BYTES, MAX_INPUT_PIXELS = 32_000_000, 20_000_000
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class ArtError(ValueError):
    """An input or output failed the documented art contract."""


def size_value(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([1-9][0-9]{0,4})[xX]([1-9][0-9]{0,4})", value)
    if not match:
        raise ArtError("Size must be positive WIDTHxHEIGHT in native image pixels.")
    size = (int(match[1]), int(match[2]))
    check_size(size)
    return size


def check_size(size: tuple[int, int]) -> None:
    if (len(size) != 2 or any(type(n) is not int for n in size)
            or not (1 <= size[0] <= WIDTH and 1 <= size[1] <= HEIGHT)):
        raise ArtError(f"Landscape TRMNL X bounds are 1..{WIDTH} by 1..{HEIGHT} pixels.")


def pillow():
    try:
        from PIL import Image, ImageEnhance, ImageOps
    except ImportError as exc:
        raise ArtError("Pillow is required for preparation/preview. Ask before installing dependencies.") from exc
    Image.MAX_IMAGE_PIXELS = MAX_INPUT_PIXELS
    return Image, ImageEnhance, ImageOps


def read_image(path: Path):
    Image, _, ImageOps = pillow()
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ArtError("Input must be a local image file no larger than 32,000,000 bytes.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as opened:
                if opened.format not in {"PNG", "JPEG", "WEBP"}:
                    raise ArtError("Use a static PNG, JPEG or WebP; no SVG/EPS, animation or multipage input.")
                if getattr(opened, "n_frames", 1) != 1:
                    raise ArtError("Animated/multipage inputs must be exported to a single approved frame first.")
                if opened.width * opened.height > MAX_INPUT_PIXELS:
                    raise ArtError("Input exceeds the 20,000,000-pixel decoding limit.")
                image = ImageOps.exif_transpose(opened).convert("RGBA")
                image.load()
                return image
    except ArtError:
        raise
    except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ArtError("Input is corrupt, unsupported or too large to decode safely.") from exc


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (struct.pack(">I", len(payload)) + kind + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))


def encode_gray4(width: int, height: int, pixels: bytes) -> bytes:
    """Encode exact gray-16 samples as a non-interlaced, color-type-0, 4-bit PNG."""
    check_size((width, height))
    if len(pixels) != width * height or any(p % 17 for p in pixels):
        raise ArtError("Pixels must use only the 16 evenly spaced grayscale levels.")
    rows = bytearray()
    for y in range(height):
        rows.append(0)  # PNG filter None; deliberately simple and independently testable.
        start = y * width
        for x in range(0, width, 2):
            high = pixels[start + x] // 17
            low = pixels[start + x + 1] // 17 if x + 1 < width else 0
            rows.append((high << 4) | low)
    header = struct.pack(">IIBBBBB", width, height, 4, 0, 0, 0, 0)
    return PNG_MAGIC + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b"")


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    distances = abs(p - a), abs(p - b), abs(p - c)
    return (a, b, c)[distances.index(min(distances))]


def validate_png(raw: bytes, expected: tuple[int, int] | None = None,
                 max_bytes: int = MAX_BYTES) -> dict:
    """Validate the actual bytes and decoded sample values, without trusting Pillow metadata."""
    if type(max_bytes) is not int or not (1 <= max_bytes <= MAX_BYTES):
        raise ArtError("The file limit may be stricter than, but never exceed, 750,000 bytes.")
    if len(raw) >= max_bytes:
        raise ArtError(f"PNG must be smaller than {max_bytes} bytes; simplify texture/dithering instead of changing the slot size.")
    if not raw.startswith(PNG_MAGIC):
        raise ArtError("Output is not a PNG.")
    at, kinds, compressed, header = 8, [], bytearray(), None
    while at < len(raw):
        if at + 12 > len(raw):
            raise ArtError("Truncated PNG chunk.")
        length = struct.unpack(">I", raw[at:at + 4])[0]
        if length > len(raw) - at - 12:
            raise ArtError("Truncated PNG payload.")
        kind = raw[at + 4:at + 8]
        if not re.fullmatch(rb"[A-Za-z]{4}", kind) or kind[2] & 32:
            raise ArtError("Invalid PNG chunk type.")
        data = raw[at + 8:at + 8 + length]
        checksum = struct.unpack(">I", raw[at + 8 + length:at + 12 + length])[0]
        if zlib.crc32(kind + data) & 0xFFFFFFFF != checksum:
            raise ArtError("PNG CRC mismatch.")
        if not kinds and kind != b"IHDR":
            raise ArtError("IHDR must be first.")
        if kind == b"IHDR":
            if kinds or length != 13:
                raise ArtError("Invalid or duplicate IHDR.")
            header = struct.unpack(">IIBBBBB", data)
        elif kind == b"IDAT":
            compressed.extend(data)
        elif kind == b"IEND":
            if length or at + 12 != len(raw):
                raise ArtError("Invalid IEND or trailing data.")
        else:
            raise ArtError("Only IHDR, IDAT and IEND chunks are accepted in grayscale-4 output.")
        kinds.append(kind)
        at += 12 + length
    if header is None or not kinds or kinds[-1] != b"IEND" or kinds.count(b"IEND") != 1 or not compressed:
        raise ArtError("PNG is incomplete.")
    width, height, bits, color, compression, filtering, interlace = header
    check_size((width, height))
    if (bits, color, compression, filtering, interlace) != (4, 0, 0, 0, 0):
        raise ArtError("Expected non-interlaced 4-bit grayscale PNG with no alpha or palette.")
    if expected is not None and (width, height) != expected:
        raise ArtError("PNG dimensions do not exactly match the requested art region.")
    stride = (width + 1) // 2
    total = (stride + 1) * height
    try:
        decoder = zlib.decompressobj()
        scanlines = decoder.decompress(bytes(compressed), total + 1)
    except zlib.error as exc:
        raise ArtError("Corrupt PNG compression.") from exc
    if len(scanlines) != total or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ArtError("PNG scanline size/compression stream does not match its dimensions.")
    previous = bytearray(stride)
    histogram = Counter()
    for y in range(height):
        offset = y * (stride + 1)
        method = scanlines[offset]
        if method > 4:
            raise ArtError("Invalid PNG row filter.")
        row = bytearray(scanlines[offset + 1:offset + 1 + stride])
        if method:
            for x in range(stride):
                a = row[x - 1] if x else 0
                b = previous[x]
                c = previous[x - 1] if x else 0
                predictor = a if method == 1 else b if method == 2 else (a + b) // 2 if method == 3 else paeth(a, b, c)
                row[x] = (row[x] + predictor) & 255
        for x in range(width):
            sample = row[x // 2] >> 4 if x % 2 == 0 else row[x // 2] & 15
            histogram[sample * 17] += 1
        previous = row
    return {"status": "PASS", "width": width, "height": height, "bitDepth": 4,
            "colorType": "grayscale", "alpha": False, "bytes": len(raw),
            "grayLevelsUsed": len(histogram), "sha256": hashlib.sha256(raw).hexdigest()}


def create_output(path: Path, raw: bytes) -> None:
    """Create exclusively; never overwrite an input, previous export or symlink."""
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise ArtError("Output exists. Choose a new path; originals/previous exports are never overwritten.") from exc
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def prepare(source: Path, output: Path, size: tuple[int, int], *, fit: str = "contain",
            dither: str = "none", margin: float = 0, contrast: float = 1,
            max_bytes: int = MAX_BYTES) -> dict:
    check_size(size)
    if fit not in {"contain", "cover"} or dither not in {"none", "floyd-steinberg"}:
        raise ArtError("Unsupported fit or dither mode.")
    if not math.isfinite(margin) or not 0 <= margin <= 0.2:
        raise ArtError("Margin must be a finite fraction between 0 and 0.2.")
    if not math.isfinite(contrast) or not 0.5 <= contrast <= 2:
        raise ArtError("Contrast must be a finite value between 0.5 and 2.")
    Image, ImageEnhance, ImageOps = pillow()
    source_image = read_image(source)
    white = Image.new("RGBA", source_image.size, "white")
    white.alpha_composite(source_image)
    gray = white.convert("L")
    if contrast != 1:
        gray = ImageEnhance.Contrast(gray).enhance(contrast)
    inner = tuple(max(1, round(n * (1 - 2 * margin))) for n in size)
    if fit == "cover":
        scaled = ImageOps.fit(gray, inner, method=Image.Resampling.LANCZOS)
    else:
        scaled = ImageOps.contain(gray, inner, method=Image.Resampling.LANCZOS)
    canvas = Image.new("L", size, 255)
    canvas.paste(scaled, ((size[0] - scaled.width) // 2, (size[1] - scaled.height) // 2))
    if dither == "none":
        pixels = canvas.point([min(15, (p + 8) // 17) * 17 for p in range(256)]).tobytes()
    else:
        palette = Image.new("P", (1, 1))
        colors = [v for p in range(16) for v in (p * 17,) * 3]
        palette.putpalette(colors + [255] * (768 - len(colors)))
        pixels = canvas.convert("RGB").quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG).convert("L").tobytes()
    raw = encode_gray4(*size, pixels)
    result = validate_png(raw, size, max_bytes)
    create_output(output, raw)
    result.update(fit=fit, dither=dither, margin=margin, contrast=contrast)
    return result


def validate_file(path: Path, expected=None, max_bytes=MAX_BYTES) -> dict:
    if type(max_bytes) is not int or not (1 <= max_bytes <= MAX_BYTES):
        raise ArtError("The file limit must be between 1 and 750,000 bytes.")
    if not path.is_file() or path.stat().st_size >= max_bytes:
        raise ArtError("PNG missing or over the configured byte limit.")
    return validate_png(path.read_bytes(), expected, max_bytes)


def preview(frame_path: Path, art_path: Path, output: Path, box: tuple[int, int, int, int]) -> dict:
    """Local reference preview only: preserve every decoded pixel outside the given box."""
    Image, _, _ = pillow()
    if len(box) != 4 or any(type(v) is not int for v in box):
        raise ArtError("Box must contain integer X,Y,WIDTH,HEIGHT in reference-image pixels.")
    x, y, width, height = box
    validate_file(art_path, (width, height))
    frame = read_image(frame_path)
    if x < 0 or y < 0 or x + width > frame.width or y + height > frame.height:
        raise ArtError("Art box extends outside the reference image.")
    art = read_image(art_path)
    frame.paste(art, (x, y))
    import io
    buffer = io.BytesIO()
    frame.info.clear()
    frame.save(buffer, format="PNG")
    create_output(output, buffer.getvalue())
    return {"status": "PASS", "purpose": "local placement preview, not device-ready output",
            "box": list(box), "outsideBox": "decoded pixels unchanged", "width": frame.width, "height": frame.height}


def generator_aspect(size: tuple[int, int]) -> str:
    """The image tool's closest standard shape: portrait (2:3), landscape (3:2) or square."""
    width, height = size
    if height >= width * 1.2:
        return "portrait"
    if width >= height * 1.2:
        return "landscape"
    return "square"


COMPOSITION = {
    "portrait": "A tall, vertical composition: the main subjects large and in front, the setting behind and "
                "below them, any decorations above. Do not make a wide scene; it would be letterboxed.",
    "landscape": "A wide composition with the main subjects large and clearly separated across the frame.",
    "square": "A centred composition with the main subjects large in the middle.",
}


def image_prompt(brief: str, size: tuple[int, int], full_screen: bool = False) -> str:
    """Prompt in the style that reads well on a 16-gray panel (proven with GPT-6.1 Sol + GPT Image)."""
    check_size(size)
    if not brief.strip() or len(brief) > 10_000:
        raise ArtError("Provide a non-empty creative brief under 10,000 characters.")
    kind = "full-screen artwork" if full_screen else "standalone artwork for one reserved picture region"
    shape = generator_aspect(size)
    return (f"Create {kind}, targeting {size[0]}x{size[1]} pixels "
            f"(ask the image tool for {shape}{' 2:3' if shape == 'portrait' else ' 3:2' if shape == 'landscape' else ''}).\n"
            f"Creative brief: {brief.strip()}\n"
            f"{COMPOSITION[shape]} Leave white space around the edges; nothing important touches them.\n"
            "Style: cute and friendly; named characters stay faithful to their official look and are instantly "
            "recognizable. Bold, clean black outlines of consistent weight, flat simple shading, strong light/dark "
            "contrast, broad readable shapes and a plain white background.\n"
            "Design for a 16-gray e-ink display: separate shapes by outline and brightness, never by colour alone. "
            "No very pale pastel areas next to white, no gradients, hairlines, fine texture or photorealism.\n"
            "Output the illustration only: no text, letters, logos, watermarks, quote, dinner list, date, labels, UI, "
            "surrounding screen, device mockup or border. Other content is owned by the existing layout.\n"
            "After image generation, run prepare and validate; a prompt is not an image or proof of generation.\n")


def review_prompt(brief: str, size: tuple[int, int]) -> str:
    """Checklist for a vision-capable model reviewing the prepared 16-gray file (not the colour original)."""
    check_size(size)
    if not brief.strip() or len(brief) > 10_000:
        raise ArtError("Provide a non-empty creative brief under 10,000 characters.")
    return (f"Review the attached picture. It is the final 16-gray e-ink version, {size[0]}x{size[1]}, "
            f"that will fill a picture region on a black-and-white e-ink screen. It was meant to show: {brief.strip()}\n"
            "Do not call any tools. Reply with exactly these lines, each short and concrete:\n"
            "SUBJECT: is every requested subject or character clearly recognizable? What looks off, if anything?\n"
            "SCENE: does the scene match the brief?\n"
            "E-INK: do the grays separate well; is anything washed out, too dark, muddy or cut off at the edges?\n"
            "TEXT: any letters, logos, watermarks or borders? (yes/no and where)\n"
            "VERDICT: PASS or REDO, with one reason\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("prepare", help="Export only the requested artwork region/full-screen art")
    make.add_argument("source", type=Path)
    make.add_argument("output", type=Path)
    target = make.add_mutually_exclusive_group(required=True)
    target.add_argument("--size", help="Region WIDTHxHEIGHT in native pixels; no implied location")
    target.add_argument("--full-screen", action="store_true", help="Explicitly request 1872x1404 artwork, not the existing menu")
    make.add_argument("--fit", choices=["contain", "cover"], default="contain")
    make.add_argument("--dither", choices=["none", "floyd-steinberg"], default="none")
    make.add_argument("--margin", type=float, default=0)
    make.add_argument("--contrast", type=float, default=1)
    make.add_argument("--max-bytes", type=int, default=MAX_BYTES)
    check = sub.add_parser("validate", help="Validate actual PNG chunks, sample layout, size and byte limit")
    check.add_argument("image", type=Path)
    check.add_argument("--size")
    check.add_argument("--max-bytes", type=int, default=MAX_BYTES)
    place = sub.add_parser("preview", help="Local-only composition; preserve pixels outside the art box")
    place.add_argument("frame", type=Path)
    place.add_argument("art", type=Path)
    place.add_argument("output", type=Path)
    place.add_argument("--box", required=True, help="X,Y,WIDTH,HEIGHT in reference image pixels")
    prompt = sub.add_parser("prompt", help="Build a region-aware prompt, NOT an image-generation call")
    prompt.add_argument("--brief", required=True)
    prompt_target = prompt.add_mutually_exclusive_group(required=True)
    prompt_target.add_argument("--size")
    prompt_target.add_argument("--full-screen", action="store_true")
    review = sub.add_parser("review-prompt", help="Build a review checklist for a vision model; NOT a model call")
    review.add_argument("--brief", required=True)
    review_target = review.add_mutually_exclusive_group(required=True)
    review_target.add_argument("--size")
    review_target.add_argument("--full-screen", action="store_true")
    args = parser.parse_args(argv)
    try:
        size = (WIDTH, HEIGHT)
        if args.command in {"prepare", "prompt", "review-prompt"}:
            size = (WIDTH, HEIGHT) if args.full_screen else size_value(args.size)
        if args.command == "prepare":
            result = prepare(args.source, args.output, size, fit=args.fit, dither=args.dither,
                             margin=args.margin, contrast=args.contrast, max_bytes=args.max_bytes)
            result["target"] = "full-screen artwork" if args.full_screen else "art region only"
        elif args.command == "validate":
            result = validate_file(args.image, size_value(args.size) if args.size else None, args.max_bytes)
        elif args.command == "preview":
            if not re.fullmatch(r"[0-9]+,[0-9]+,[1-9][0-9]*,[1-9][0-9]*", args.box):
                raise ArtError("Box must be X,Y,WIDTH,HEIGHT with non-negative origin and positive dimensions.")
            values = list(map(int, args.box.split(",")))
            result = preview(args.frame, args.art, args.output, (values[0], values[1], values[2], values[3]))
        elif args.command == "review-prompt":
            print(review_prompt(args.brief, size))
            return 0
        else:
            print(image_prompt(args.brief, size, args.full_screen))
            return 0
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ArtError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
