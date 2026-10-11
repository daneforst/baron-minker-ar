#!/usr/bin/env python3
"""Compress a raw Meshy .usdz export for web/AR delivery.

Meshy's USDZ textures come out at 2048-4096px, uncompressed PNG --
25-30MB per file, most of it texture data the animation doesn't need.
This extracts the archive, downsamples textures with macOS's built-in
`sips` (no extra deps), and repacks a spec-compliant USDZ with Pixar's
own packager (UsdUtils.CreateNewARKitUsdzPackage) so Quick Look doesn't
choke on a malformed zip.

Requires Blender's bundled Python (has the `pxr` USD bindings compiled
in; a bare system python3 does not).

Usage:
  /Applications/Blender.app/Contents/Resources/3.5/python/bin/python3.10 \\
    scripts/optimize_usdz.py <input.usdz> <output.usdz> [max_texture_px]
"""
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from pxr import UsdUtils


def main():
    src = Path(sys.argv[1]).resolve()
    dest = Path(sys.argv[2]).resolve()
    max_px = sys.argv[3] if len(sys.argv) > 3 else "1024"

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        with zipfile.ZipFile(src) as z:
            z.extractall(tmp)

        pngs = list(tmp.glob("*.png"))
        if pngs:
            subprocess.run(
                ["sips", "-Z", max_px, *[str(p) for p in pngs]],
                check=True,
                capture_output=True,
            )

        usdc_candidates = list(tmp.glob("*.usdc")) + list(tmp.glob("*.usda"))
        if not usdc_candidates:
            raise SystemExit(f"No root .usdc/.usda layer found in {src}")
        root_layer = usdc_candidates[0]

        dest.parent.mkdir(parents=True, exist_ok=True)
        ok = UsdUtils.CreateNewARKitUsdzPackage(str(root_layer), str(dest))
        if not ok:
            raise SystemExit(f"USDZ packaging failed for {src}")

    before = src.stat().st_size / 1_000_000
    after = dest.stat().st_size / 1_000_000
    print(f"{src.name} ({before:.1f} MB) -> {dest.name} ({after:.1f} MB)")


if __name__ == "__main__":
    main()
