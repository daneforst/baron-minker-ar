#!/usr/bin/env bash
# Compresses every .glb in assets/models-raw/ (fresh Meshy downloads, often
# 40-170MB) down to a web-sized file in assets/models/, then rebuilds the
# site manifest. Safe to re-run; already-optimized files are skipped.
#
# Also compresses any matching .usdz (iOS Quick Look AR) dropped alongside
# a .glb of the same name -- same filename, different extension, e.g.
# rahul__running.glb + rahul__running.usdz.
#
# Usage:
#   1. Drop raw Mixamo-animated .glb (and, for iOS AR, matching .usdz)
#      exports from Meshy into assets/models-raw/
#   2. Run: bash scripts/optimize_models.sh
#   3. Rename the resulting file(s) in assets/models/ if you want a cleaner
#      name (character-slug.glb/.usdz or character-slug__animation-slug.glb/.usdz),
#      then run scripts/build_manifest.py again if you renamed anything.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW_DIR="$ROOT/assets/models-raw"
OUT_DIR="$ROOT/assets/models"
TEXTURE_SIZE="${TEXTURE_SIZE:-1536}"
BLENDER_PY="${BLENDER_PY:-/Applications/Blender.app/Contents/Resources/3.5/python/bin/python3.10}"

mkdir -p "$OUT_DIR"

shopt -s nullglob
found=0
for src in "$RAW_DIR"/*.glb; do
  found=1
  base="$(basename "$src" .glb)"
  dest="$OUT_DIR/$base.glb"
  if [ -f "$dest" ]; then
    echo "skip (already optimized): $base.glb"
    continue
  fi
  echo "optimizing: $base.glb"
  # No geometry compression (draco/meshopt): Android's native Scene Viewer
  # (used for in-AR placement) renders Draco-compressed skinned meshes in
  # their static bind pose instead of playing the animation, even though
  # the in-browser preview (three.js) handles the exact same file fine.
  # Texture compression + mesh simplification alone still cut raw Meshy
  # exports by ~70% with no compatibility risk.
  npx --yes @gltf-transform/cli optimize "$src" "$dest" \
    --compress false \
    --texture-compress webp \
    --texture-size "$TEXTURE_SIZE"
done

for src in "$RAW_DIR"/*.usdz; do
  found=1
  base="$(basename "$src" .usdz)"
  dest="$OUT_DIR/$base.usdz"
  if [ -f "$dest" ]; then
    echo "skip (already optimized): $base.usdz"
    continue
  fi
  if [ ! -x "$BLENDER_PY" ]; then
    echo "skip (Blender python not found at $BLENDER_PY, set \$BLENDER_PY): $base.usdz"
    continue
  fi
  echo "optimizing: $base.usdz"
  "$BLENDER_PY" "$ROOT/scripts/optimize_usdz.py" "$src" "$dest" "$TEXTURE_SIZE"
done

if [ "$found" -eq 0 ]; then
  echo "No .glb/.usdz files found in $RAW_DIR"
  exit 0
fi

python3 "$ROOT/scripts/build_manifest.py"
