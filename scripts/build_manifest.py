#!/usr/bin/env python3
"""Rebuild data/models.json from whatever .glb files sit in assets/models.

Filename convention: <character-slug>[__<animation-slug>].glb
Examples:
  roseguard-cyclops.glb                -> "Roseguard Cyclops"
  roseguard-cyclops__walk.glb          -> "Roseguard Cyclops" / "Walk"
  roseguard-cyclops__idle-breathing.glb -> "Roseguard Cyclops" / "Idle Breathing"

Run after adding or removing files in assets/models:
  python3 scripts/build_manifest.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "assets" / "models"
OUT_FILE = ROOT / "data" / "models.json"


def titleize(slug: str) -> str:
    return " ".join(w.capitalize() for w in slug.split("-"))


def main():
    entries = []
    for glb in sorted(MODELS_DIR.glob("*.glb")):
        stem = glb.stem
        if "__" in stem:
            char_slug, anim_slug = stem.split("__", 1)
        else:
            char_slug, anim_slug = stem, ""

        entries.append(
            {
                "id": stem,
                "name": titleize(char_slug),
                "file": glb.name,
                "variant": titleize(anim_slug) if anim_slug else "",
                "sizeMB": round(glb.stat().st_size / 1_000_000, 2),
            }
        )

    OUT_FILE.write_text(json.dumps(entries, indent=2) + "\n")
    print(f"Wrote {len(entries)} model(s) to {OUT_FILE.relative_to(ROOT)}")
    for e in entries:
        label = f"{e['name']} — {e['variant']}" if e["variant"] else e["name"]
        print(f"  {label}  ({e['sizeMB']} MB)")


if __name__ == "__main__":
    main()
