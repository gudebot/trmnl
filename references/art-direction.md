# Art direction for e-ink regions

## Start with the space, not a whole-screen mockup

An image for a reserved picture area should be **only that area's illustration**. Its surrounding quote, dinner plan, title, clock and other widgets belong to the existing layout. Put none of them in the picture. The art can sit in a left panel, a top-right square or elsewhere without regenerating the rest of the screen. A tall panel (such as 800×1190 on the example menu screen) wants a tall composition; a wide picture would be letterboxed in it.

Record the actual intended width/height and aspect ratio before drawing. Generate near that ratio when a provider restricts sizes, then contain-fit without losing the subject. A square source pasted into a rectangular slot is not proof that the slot itself is square. Do not silently crop a face/character to make a mismatched brief fit.

## Compose for 16 grays

- Prefer clear silhouettes, medium/bold edges, distinct values and limited texture.
- Separate the subject from its background by **brightness**, not hue. Two different colors can collapse to the same gray.
- Leave breathing room for ears, leaves, hats and other protruding details. Keep important features away from the edge.
- Avoid tiny lettering, hairlines and delicate near-white shading. If lettering is necessary, render it with a trusted local font rather than pretend generated text is guaranteed correct.
- Default to a light background and an uncluttered composition. Do not add a border unless the user wants one; the existing slot may already have one.
- Treat a physical e-ink panel differently from a backlit preview. Compatibility checks do not prove perceived contrast or refresh behavior.

## Choose dithering deliberately

`none` is usually the cleaner starting point for line art, cartoon illustrations and flat shapes. Floyd–Steinberg can represent tonal detail with spatial texture, but may make a small picture noisy or larger on disk. Compare the actual prepared files at intended display size. Do not claim one mode is universally better; export both to distinct paths when the choice matters.

## Example region brief

> A standalone botanical illustration for a measured 800×1190 portrait picture panel. One graceful plant with broad leaves, subtle 16-gray value separation, a white background, clear medium-weight lines, restrained shading and generous breathing room. No surrounding screen, quote, weekly dinners, clock, title, labels, frame or mockup. Preserve the whole plant when resized.

Use the user's creative subject, not the example plant by default. Do not silently replace requested generated artwork with a conversion of an old repo image or a procedural demo.

For a character scene in a tall panel, stack the action vertically (characters in front, table or setting behind, decorations above) instead of a wide banquet composition that will be letterboxed. Ask the generator for bold outlines and flat, well-separated tones; very light pastels (pale blue, cream) collapse toward white in 16 grays.

## Honest generation evidence

A returned prompt is not an image. A successful conversion proves preparation of a real input, not that a generative service was called. A local procedural drawing is an image but must not be described as an AI-service result. Record the source path/tool, the actual produced file, target dimensions and validator result; distinguish these from a local composition and a physical device observation. No invented images, API responses or claimed uploads.
