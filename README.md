# Baron Minker — AR Gallery

Self-hosted viewer for the Baron Minker 3D characters, so AR access doesn't
depend on staying inside Meshy. Scan a QR code (printed or on-screen) and the
character opens directly in AR on the visitor's phone.

## How it's put together

- `index.html` — gallery grid, each card a live spinning preview
- `viewer.html?model=<id>` — full-screen viewer with the AR launch button
- `print.html` — one QR code per character, laid out for printing and cutting apart
- `data/models.json` — the list of characters the site reads; generated, don't hand-edit
- `assets/models/` — the actual (compressed) `.glb` files the site serves
- `assets/models-raw/` — drop zone for fresh, uncompressed Meshy exports

Built on Google's `<model-viewer>` web component (vendored in `assets/vendor/`,
no CDN dependency at runtime) which handles AR via Android Scene Viewer,
iOS Quick Look, and WebXR automatically — no app required on the visitor's end.

## Adding a new character

Meshy's raw downloads run 40-170MB, which is both too slow to load from a QR
scan and over GitHub's file-size limits. Every file gets compressed before
it's served:

1. Drop the raw `.glb` export into `assets/models-raw/`
2. Run:
   ```bash
   bash scripts/optimize_models.sh
   ```
   This compresses textures (WebP, capped at 1536px) and simplifies geometry,
   typically a ~70% size cut, and writes the result into `assets/models/`.
   Geometry itself is left uncompressed (no Draco/meshopt) — Draco-compressed
   skinned meshes render fine in the in-page viewer but freeze on the bind
   pose when handed off to Android's native Scene Viewer for AR placement.
3. (Optional) Rename the file in `assets/models/` to the convention
   `character-slug.glb` or `character-slug__animation-slug.glb`
   (e.g. `roseguard-cyclops__walk.glb`) for a cleaner display name, then run:
   ```bash
   python3 scripts/build_manifest.py
   ```

## iOS note

Android AR (Scene Viewer) works directly from the `.glb` files above — nothing
extra needed. iOS AR Quick Look needs a `.usdz` version of each model;
that conversion isn't wired up yet. Until then, the AR button still appears
on iPhones but will not be able to launch — orbiting/zooming the model works
everywhere.

## Preview locally

```bash
python3 -m http.server 8769
```

Then open `http://localhost:8769`.
