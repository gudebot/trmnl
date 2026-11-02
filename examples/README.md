# Procedural region example

These examples are synthetic **local procedural art and layout demonstrations**, not images from an AI image-generation service or anyone's live device. They contain no real quote, dinner plan, private reference frame, account data or credentials.

- `square-art.png`: exact **576×576**, 16-gray/4-bit grayscale illustration, generated from local botanical drawing code.
- `region-preview.png`: a synthetic **1872×1404** reference with a **576×576** art region at **1200,80**, demonstrating a top-right picture beside/beyond other content. Every decoded pixel outside that box remains unchanged by the placement operation. This ordinary RGBA PNG is **not device-ready** and does not claim to reproduce a current live layout.

The numbers are **illustrative**, not a measured personal preset. Use actual measured/chosen dimensions for new requests.

Regenerate into a new, ignored output directory:

```sh
python scripts/make_examples.py --output-dir out/examples
```

The generator refuses to overwrite existing exports. Original root-level artwork is not modified. Validate the art (not the diagnostic preview) with:

```sh
python scripts/trmnl_art.py validate examples/square-art.png --size 576x576
```
