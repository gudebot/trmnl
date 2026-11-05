import ast
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BundleTests(unittest.TestCase):
    def test_standard_skill_entry_and_explicit_support_links(self):
        text = (ROOT / "SKILL.md").read_text()
        self.assertTrue(text.startswith("---\n"))
        header = text.split("---", 2)[1]
        self.assertRegex(header, r"(?m)^name: trmnl-grayscale$")
        self.assertRegex(header, r"(?m)^description: ")
        for path in ("scripts/trmnl_art.py", "scripts/make_examples.py", "assets/trmnl-x.json", "references/targets.md", "references/art-direction.md"):
            self.assertIn("](" + path + ")", text)
            self.assertTrue((ROOT / path).is_file())

    def test_every_local_markdown_link_resolves(self):
        for file in ROOT.rglob("*.md"):
            if ".git" in file.parts or "out" in file.parts:
                continue
            for url in re.findall(r"\]\(([^)]+)\)", file.read_text()):
                if "://" not in url and not url.startswith("#"):
                    with self.subTest(file=str(file.relative_to(ROOT)), url=url):
                        self.assertTrue((file.parent / url.split("#")[0]).is_file())

    def test_profile_css_to_native_arithmetic(self):
        model = json.loads((ROOT / "assets/trmnl-x.json").read_text())
        ratio = model["native_pixels_per_css_pixel"]
        self.assertEqual(round(model["layout_width_css"] * ratio), model["width"])
        self.assertEqual(round(model["layout_height_css"] * ratio), model["height"])
        self.assertEqual(round(320 * ratio), 576)

    def test_converter_has_no_network_or_process_client(self):
        tree = ast.parse((ROOT / "scripts/trmnl_art.py").read_text())
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(x.name.split(".")[0] for x in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module.split(".")[0])
        self.assertFalse(modules & {"socket", "urllib", "requests", "httpx", "subprocess", "ftplib"})

    def test_committed_example_art_validates_and_preview_is_native(self):
        run = subprocess.run([sys.executable, str(ROOT / "scripts/trmnl_art.py"), "validate",
                              str(ROOT / "examples/region-art.png"), "--size", "800x1190"],
                             text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        proof = json.loads(run.stdout)
        self.assertEqual((proof["width"], proof["height"], proof["bitDepth"]), (800, 1190, 4))
        run = subprocess.run([sys.executable, str(ROOT / "scripts/trmnl_art.py"), "validate",
                              str(ROOT / "examples/menu-screen.png"), "--size", "1872x1404"], text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        from PIL import Image, ImageChops
        with Image.open(ROOT / "examples/region-preview.png") as image, Image.open(ROOT / "examples/menu-screen.png") as screen:
            self.assertEqual(image.size, (1872, 1404))
            preview, frame = image.convert("RGBA"), screen.convert("RGBA")
        x, y, w, h = 22, 22, 800, 1190
        outside = [(0, 0, 1872, y), (0, y + h, 1872, 1404), (0, y, x, y + h), (x + w, y, 1872, y + h)]
        for box in outside:
            with self.subTest(box=box):
                self.assertIsNone(ImageChops.difference(preview.crop(box), frame.crop(box)).getbbox())
        with Image.open(ROOT / "examples/region-art.png") as art:
            self.assertIsNone(ImageChops.difference(preview.crop((x, y, x + w, y + h)), art.convert("RGBA")).getbbox())
        # The device showed this same Gudetama picture, so the preview reproduces the real frame:
        # only the panel's clipped rounded corners (and a few resampling pixels) may differ.
        changed = sum(1 for p in ImageChops.difference(preview.convert("L"), frame.convert("L")).getdata() if p)
        self.assertLess(changed, 400)

    def test_example_box_matches_the_measured_panel_border(self):
        from PIL import Image
        with Image.open(ROOT / "examples/menu-screen.png") as screen:
            g = screen.convert("L")
        # 4 px grey border just outside the 800x1190 box at 22,22; white just inside it.
        for px in ((19, 400), (400, 19), (823, 600), (400, 1213)):
            self.assertEqual(g.getpixel(px), 204, px)
        for px in ((22, 400), (400, 22), (821, 600), (400, 1211)):
            self.assertEqual(g.getpixel(px), 255, px)

    def test_example_builder_reproduces_committed_examples(self):
        with tempfile.TemporaryDirectory(prefix="trmnl-examples-test-") as temp:
            run = subprocess.run([sys.executable, str(ROOT / "scripts/make_examples.py"), "--output-dir", temp], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)
            self.assertFalse(result["aiGenerationServiceCalled"])
            self.assertFalse(result["deviceChanged"])
            self.assertEqual((result["art"]["width"], result["art"]["height"]), (800, 1190))
            self.assertEqual(result["box"], [22, 22, 800, 1190])
            self.assertEqual(result["source"], "gudetama-halloween-color-gray.png")
            for name in ("region-art.png", "region-preview.png"):
                self.assertGreater((Path(temp) / name).stat().st_size, 0)
                with self.subTest(name=name):
                    self.assertEqual((Path(temp) / name).read_bytes(), (ROOT / "examples" / name).read_bytes())
            again = subprocess.run([sys.executable, str(ROOT / "scripts/make_examples.py"), "--output-dir", temp], text=True, capture_output=True)
            self.assertEqual(again.returncode, 2)

if __name__ == "__main__":
    unittest.main()
