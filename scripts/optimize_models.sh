#!/usr/bin/env bash
# Compresses every .glb in assets/models-raw/ (fresh Meshy downloads, often
# 40-170MB) down to a web-sized file in assets/models/, then rebuilds the
# site manifest. Safe to re-run; already-optimized files are skipped.
#
# Usage:
#   1. Drop raw Mixamo-animated .glb exports from Meshy into assets/models-raw/
#   2. Run: bash scripts/optimize_models.sh
#   3. Rename the resulting file in assets/models/ if you want a cleaner name
#      (character-slug.glb or character-slug__animation-slug.glb), then
#      run scripts/build_manifest.py again if you renamed anything.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW_DIR="$ROOT/assets/models-raw"
OUT_DIR="$ROOT/assets/models"
TEXTURE_SIZE="${TEXTURE_SIZE:-1536}"

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

if [ "$found" -eq 0 ]; then
  echo "No .glb files found in $RAW_DIR"
  exit 0
fi

python3 "$ROOT/scripts/build_manifest.py"
