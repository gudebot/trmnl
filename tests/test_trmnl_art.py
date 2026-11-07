import base64
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("trmnl_art", ROOT / "scripts/trmnl_art.py")
assert spec is not None and spec.loader is not None
art = importlib.util.module_from_spec(spec)
spec.loader.exec_module(art)


def png_from_rows(width, height, rows, *, bits=4, color=0, interlace=0, extra=b""):
    header = struct.pack(">IIBBBBB", width, height, bits, color, 0, 0, interlace)
    return (art.PNG_MAGIC + art.chunk(b"IHDR", header) + extra
            + art.chunk(b"IDAT", zlib.compress(rows)) + art.chunk(b"IEND", b""))


class ArtTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="trmnl-art-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.png"
        self.output = self.root / "export.png"
        Image.new("RGB", (40, 20), "black").save(self.source)

    def export(self, size=(80, 80), **kwargs):
        return art.prepare(self.source, self.output, size, **kwargs)

    def pixels(self, path=None):
        with Image.open(path or self.output) as img:
            return img.convert("L").copy()

    def test_explicit_size_and_bounds(self):
        self.assertEqual(art.size_value("576x576"), (576, 576))
        for value in ("0x1", "-1x10", "10x0", "1.5x2", "10 x 10", "1873x10", "10x1405", "010x20"):
            with self.subTest(value=value), self.assertRaises(art.ArtError):
                art.size_value(value)

    def test_gray4_roundtrip_even_odd_and_single_pixel(self):
        for width in (1, 3, 20):
            with self.subTest(width=width):
                pixels = bytes((i % 16) * 17 for i in range(width * 3))
                raw = art.encode_gray4(width, 3, pixels)
                self.assertEqual(art.validate_png(raw)["bitDepth"], 4)
                with Image.open(io.BytesIO(raw)) as img:
                    self.assertEqual(img.convert("L").tobytes(), pixels)

    def test_encoder_refuses_wrong_samples(self):
        for pixels in (b"", b"\x01", b"\x00\x00"):
            with self.subTest(pixels=pixels), self.assertRaises(art.ArtError):
                art.encode_gray4(1, 1, pixels)

    def test_exact_expected_dimensions(self):
        raw = art.encode_gray4(3, 1, bytes([0, 17, 255]))
        with self.assertRaises(art.ArtError):
            art.validate_png(raw, (4, 1))

    def test_canonical_png_has_only_three_chunks(self):
        self.export()
        raw = self.output.read_bytes()
        kinds, at = [], 8
        while at < len(raw):
            n = struct.unpack(">I", raw[at:at + 4])[0]
            kinds.append(raw[at + 4:at + 8])
            at += n + 12
        self.assertEqual(kinds, [b"IHDR", b"IDAT", b"IEND"])
        self.assertEqual(art.validate_png(raw)["colorType"], "grayscale")

    def test_old_eight_bit_grayscale_is_not_claimed_four_bit(self):
        img = Image.new("L", (10, 10), 17)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        with self.assertRaises(art.ArtError):
            art.validate_png(buf.getvalue())

    def test_crc_corruption(self):
        raw = bytearray(art.encode_gray4(1, 1, b"\x00"))
        raw[29] ^= 1
        with self.assertRaises(art.ArtError):
            art.validate_png(bytes(raw))

    def test_truncation_and_trailing_data(self):
        raw = art.encode_gray4(1, 1, b"\x00")
        for value in (b"", raw[:-1], raw[:20], raw + b"extra", b"not-png"):
            with self.subTest(size=len(value)), self.assertRaises(art.ArtError):
                art.validate_png(value)

    def test_invalid_header_palette_alpha_and_interlace(self):
        cases = [png_from_rows(1, 1, b"\x00\x00", interlace=1),
                 png_from_rows(1, 1, b"\x00\x00", color=4),
                 png_from_rows(1, 1, b"\x00\x00", extra=art.chunk(b"PLTE", b"\x00\x00\x00")),
                 png_from_rows(1, 1, b"\x00\x00", extra=art.chunk(b"tRNS", b"\x00\x00")),
                 png_from_rows(1, 1, b"\x00\x00", extra=art.chunk(b"tEXt", b"key\x00value")),
                 png_from_rows(1, 1, b"\x00\x00", extra=art.chunk(b"ABCD", b"")),
                 png_from_rows(1, 1, b"\x00\x00", extra=art.chunk(b"a?Cd", b""))]
        for raw in cases:
            with self.subTest(rawSize=len(raw)), self.assertRaises(art.ArtError):
                art.validate_png(raw)

    def test_native_bounds_validated_before_inflate(self):
        raw = png_from_rows(9999, 1, b"\x00\x00")
        with self.assertRaises(art.ArtError):
            art.validate_png(raw)

    def test_bounded_decompression_and_exact_row_length(self):
        for rows in (b"\x00", b"\x00" * 1_000_000):
            raw = png_from_rows(1, 1, rows)
            with self.assertRaises(art.ArtError):
                art.validate_png(raw)

    def test_all_standard_row_filters_decode(self):
        native = [bytes([0x12, 0x30]), bytes([0x45, 0x60])]
        for method in range(5):
            rows = bytearray()
            previous = bytes(2)
            for row in native:
                rows.append(method)
                for x, value in enumerate(row):
                    a = row[x - 1] if x else 0
                    b = previous[x]
                    c = previous[x - 1] if x else 0
                    predictor = (0, a, b, (a + b) // 2, art.paeth(a, b, c))[method]
                    rows.append((value - predictor) & 255)
                previous = row
            with self.subTest(method=method):
                raw = png_from_rows(3, 2, bytes(rows))
                self.assertEqual(art.validate_png(raw)["grayLevelsUsed"], 6)
                with Image.open(io.BytesIO(raw)) as img:
                    self.assertEqual(img.convert("L").tobytes(), bytes(v * 17 for v in range(1, 7)))

    def test_bad_filter_is_rejected(self):
        with self.assertRaises(art.ArtError):
            art.validate_png(png_from_rows(1, 1, b"\x05\x00"))

    def test_byte_limit_strictly_under_and_not_raiseable(self):
        raw = art.encode_gray4(1, 1, b"\x00")
        with self.assertRaises(art.ArtError):
            art.validate_png(raw, max_bytes=len(raw))
        for limit in (0, -1, 750001, True):
            with self.subTest(limit=limit), self.assertRaises(art.ArtError):
                art.validate_png(raw, max_bytes=limit)

    def test_alpha_is_composited_on_white(self):
        Image.new("RGBA", (40, 20), (0, 0, 0, 0)).save(self.source)
        self.export()
        self.assertEqual(set(self.pixels().tobytes()), {255})

    def test_contain_never_stretches(self):
        self.export()
        img = self.pixels()
        self.assertEqual(img.getpixel((40, 0)), 255)
        self.assertEqual(img.getpixel((0, 40)), 0)
        self.assertEqual(img.getpixel((40, 40)), 0)

    def test_cover_crop_is_explicit(self):
        self.export(fit="cover")
        self.assertEqual(set(self.pixels().tobytes()), {0})

    def test_margin_reserves_white_space(self):
        Image.new("L", (40, 40), 0).save(self.source)
        self.export(margin=0.1)
        self.assertEqual(self.pixels().getpixel((7, 40)), 255)
        self.assertEqual(self.pixels().getpixel((8, 40)), 0)

    def test_floyd_dither_stays_gray16_and_four_bit(self):
        image = Image.linear_gradient("L").resize((80, 80))
        image.save(self.source)
        result = self.export(dither="floyd-steinberg")
        self.assertLessEqual(result["grayLevelsUsed"], 16)
        self.assertTrue(all(v % 17 == 0 for v in self.pixels().tobytes()))

    def test_invalid_tuning_values_are_rejected(self):
        for kwargs in ({"margin": float("nan")}, {"margin": 0.3}, {"contrast": float("inf")},
                       {"contrast": 3}, {"fit": "stretch"}, {"dither": "random"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(art.ArtError):
                self.export(**kwargs)

    def test_source_and_existing_output_never_overwritten(self):
        before = self.source.read_bytes()
        with self.assertRaises(art.ArtError):
            art.prepare(self.source, self.source, (80, 80))
        self.assertEqual(self.source.read_bytes(), before)
        self.export()
        previous = self.output.read_bytes()
        with self.assertRaises(art.ArtError):
            self.export()
        self.assertEqual(self.output.read_bytes(), previous)

    def test_symlink_output_is_refused(self):
        self.output.symlink_to(self.source)
        before = self.source.read_bytes()
        with self.assertRaises(art.ArtError):
            self.export()
        self.assertEqual(self.source.read_bytes(), before)

    def test_limit_failure_creates_no_export(self):
        with self.assertRaises(art.ArtError):
            self.export(max_bytes=10)
        self.assertFalse(self.output.exists())

    def test_corrupt_or_non_image_input(self):
        self.source.write_bytes(b"not a real image")
        with self.assertRaises(art.ArtError):
            self.export()

    def test_animated_input_is_not_silently_first_frame(self):
        image = Image.new("RGBA", (20, 20), "black")
        image.save(self.source, format="PNG", save_all=True,
                   append_images=[Image.new("RGBA", (20, 20), "white")], duration=100)
        with self.assertRaises(art.ArtError):
            self.export()

    def test_exif_orientation_applied_before_sizing(self):
        self.source = self.root / "rotated.jpg"
        exif = Image.Exif()
        exif[274] = 6
        Image.new("RGB", (40, 20), "black").save(self.source, exif=exif)
        self.assertEqual(art.read_image(self.source).size, (20, 40))

    def test_preview_preserves_every_pixel_outside_art_box(self):
        frame_path = self.root / "frame.png"
        preview_path = self.root / "preview.png"
        before = Image.new("RGB", (80, 60), (17, 100, 200)).convert("RGBA")
        before.save(frame_path)
        self.export((32, 32))
        box = (40, 4, 32, 32)
        result = art.preview(frame_path, self.output, preview_path, box)
        after = art.read_image(preview_path)
        for rect in ((0, 0, 80, 4), (0, 36, 80, 60), (0, 4, 40, 36), (72, 4, 80, 36)):
            self.assertEqual(before.crop(rect).tobytes(), after.crop(rect).tobytes())
        self.assertEqual(after.crop((40, 4, 72, 36)).tobytes(), art.read_image(self.output).tobytes())
        self.assertIn("not device-ready", result["purpose"])

    def test_preview_mismatch_or_out_of_bounds_is_rejected(self):
        frame = self.root / "frame.png"
        Image.new("RGB", (80, 60), "white").save(frame)
        self.export((32, 32))
        for box in ((40, 4, 20, 20), (70, 40, 32, 32), (-1, 0, 32, 32)):
            with self.subTest(box=box), self.assertRaises(art.ArtError):
                art.preview(frame, self.output, self.root / "preview.png", box)

    def test_prompt_is_region_only_and_not_a_generation_claim(self):
        prompt = art.image_prompt("a small botanical illustration", (576, 576))
        self.assertIn("576x576", prompt)
        self.assertIn("one reserved picture region", prompt)
        self.assertIn("no text, letters, logos, watermarks, quote, dinner list", prompt)
        self.assertIn("a prompt is not an image", prompt)
        with self.assertRaises(art.ArtError):
            art.image_prompt("   ", (80, 80))

    def test_prompt_matches_the_target_shape_and_e_ink_style(self):
        tall = art.image_prompt("two characters at a feast", (800, 1190))
        self.assertIn("portrait 2:3", tall)
        self.assertIn("tall, vertical composition", tall)
        for phrase in ("Bold, clean black outlines", "flat simple shading", "plain white background",
                       "No very pale pastel", "no text, letters, logos, watermarks"):
            self.assertIn(phrase, tall)
        self.assertIn("landscape 3:2", art.image_prompt("a skyline", (1200, 600)))
        self.assertIn("ask the image tool for square", art.image_prompt("a plant", (576, 576)))
        self.assertEqual(art.generator_aspect((1872, 1404)), "landscape")

    def test_review_prompt_is_a_checklist_not_a_model_call(self):
        review = art.review_prompt("two characters at a feast", (800, 1190))
        for line in ("800x1190", "Do not call any tools", "SUBJECT:", "SCENE:", "E-INK:", "TEXT:", "VERDICT: PASS or REDO"):
            self.assertIn(line, review)
        run = subprocess.run([sys.executable, str(ROOT / "scripts/trmnl_art.py"), "review-prompt",
                              "--brief", "a plant", "--size", "800x1190"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("VERDICT", run.stdout)
        with self.assertRaises(art.ArtError):
            art.review_prompt(" ", (80, 80))

    def test_cli_requires_explicit_target(self):
        run = subprocess.run([sys.executable, str(ROOT / "scripts/trmnl_art.py"), "prepare",
                              str(self.source), str(self.output)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertFalse(self.output.exists())

    def test_cli_prepare_and_validate_actual_bytes(self):
        for args in (["prepare", str(self.source), str(self.output), "--size", "80x80"],
                     ["validate", str(self.output), "--size", "80x80"]):
            run = subprocess.run([sys.executable, str(ROOT / "scripts/trmnl_art.py"), *args], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)["status"], "PASS")

    def test_full_screen_requires_explicit_flag_and_is_native(self):
        run = subprocess.run([sys.executable, str(ROOT / "scripts/trmnl_art.py"), "prepare",
                              str(self.source), str(self.output), "--full-screen"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        proof = json.loads(run.stdout)
        self.assertEqual((proof["width"], proof["height"]), (1872, 1404))
        self.assertEqual(proof["target"], "full-screen artwork")

    def test_existing_repository_artwork_exports_without_modifying_original(self):
        path = ROOT / "images" / "2026-10" / "Cinnamoroll_Halloween.png"
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        result = art.prepare(path, self.output, (576, 576))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

    def test_model_profile_matches_converter(self):
        model = json.loads((ROOT / "assets/trmnl-x.json").read_text())
        self.assertEqual((model["width"], model["height"]), (art.WIDTH, art.HEIGHT))
        self.assertEqual((model["bit_depth"], model["colors"], model["image_size_limit"]), (4, 16, art.MAX_BYTES))


if __name__ == "__main__":
    unittest.main()
