#!/usr/bin/env python3
"""Rebuild data/models.json from whatever .glb/.usdz files sit in assets/models.

Filename convention: <character-slug>[__<animation-slug>].glb / .usdz
Examples:
  roseguard-cyclops.glb                -> "Roseguard Cyclops"
  roseguard-cyclops__walk.glb          -> "Roseguard Cyclops" / "Walk"
  roseguard-cyclops__idle-breathing.glb -> "Roseguard Cyclops" / "Idle Breathing"

A .usdz with the exact same stem as a .glb is attached to that entry as
usdzFile (real per-animation iOS AR).

A .usdz with NO matching same-stem .glb falls back to a shared static glb
named just "<character-slug>.glb" (no "__"), if one exists -- the entry
plays this animation on iOS (Quick Look), but shows the static pose on
web/Android, flagged "iosOnly": true. This covers characters where only
USDZ exports exist for a given animation.

Run after adding or removing files in assets/models:
  python3 scripts/build_manifest.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "assets" / "models"
OUT_FILE = ROOT / "data" / "models.json"


_MINOR_WORDS = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with"}


def titleize(slug: str) -> str:
    words = slug.split("-")
    out = []
    for i, w in enumerate(words):
        if 0 < i < len(words) - 1 and w.lower() in _MINOR_WORDS:
            out.append(w.lower())
        else:
            out.append(w.capitalize())
    return " ".join(out)


def split_stem(stem: str):
    if "__" in stem:
        char_slug, anim_slug = stem.split("__", 1)
    else:
        char_slug, anim_slug = stem, ""
    return char_slug, anim_slug


def main():
    entries = []
    glb_stems = {glb.stem for glb in MODELS_DIR.glob("*.glb")}

    # Characters where a bare "<slug>.glb" exists ONLY to serve as a shared
    # fallback for usdz-only animations (no real standalone glb variant) --
    # skip emitting a redundant unlabeled entry for that bare file itself.
    fallback_only_slugs = set()
    for usdz in MODELS_DIR.glob("*.usdz"):
        if usdz.stem in glb_stems:
            continue
        char_slug, _ = split_stem(usdz.stem)
        if char_slug in glb_stems and "__" not in char_slug:
            has_real_variant = any(
                split_stem(g.stem)[0] == char_slug and "__" in g.stem
                for g in MODELS_DIR.glob("*.glb")
            )
            if not has_real_variant:
                fallback_only_slugs.add(char_slug)

    for glb in sorted(MODELS_DIR.glob("*.glb")):
        stem = glb.stem
        if stem in fallback_only_slugs:
            continue
        char_slug, anim_slug = split_stem(stem)
        usdz = MODELS_DIR / f"{stem}.usdz"

        entry = {
            "id": stem,
            "name": titleize(char_slug),
            "file": glb.name,
            "variant": titleize(anim_slug) if anim_slug else "",
            "sizeMB": round(glb.stat().st_size / 1_000_000, 2),
        }
        if usdz.exists():
            entry["usdzFile"] = usdz.name
            entry["usdzSizeMB"] = round(usdz.stat().st_size / 1_000_000, 2)

        entries.append(entry)

    # USDZ-only animations: fall back to a shared "<character-slug>.glb"
    for usdz in sorted(MODELS_DIR.glob("*.usdz")):
        stem = usdz.stem
        if stem in glb_stems:
            continue  # already attached to its own matching glb above
        char_slug, anim_slug = split_stem(stem)
        fallback_glb = MODELS_DIR / f"{char_slug}.glb"
        if not fallback_glb.exists():
            print(f"  skip (no matching or fallback glb): {usdz.name}")
            continue

        entries.append(
            {
                "id": stem,
                "name": titleize(char_slug),
                "file": fallback_glb.name,
                "variant": titleize(anim_slug) if anim_slug else "",
                "sizeMB": round(fallback_glb.stat().st_size / 1_000_000, 2),
                "usdzFile": usdz.name,
                "usdzSizeMB": round(usdz.stat().st_size / 1_000_000, 2),
                "iosOnly": True,
            }
        )

    entries.sort(key=lambda e: (e["name"], e["variant"]))

    OUT_FILE.write_text(json.dumps(entries, indent=2) + "\n")
    print(f"Wrote {len(entries)} model(s) to {OUT_FILE.relative_to(ROOT)}")
    for e in entries:
        label = f"{e['name']} — {e['variant']}" if e["variant"] else e["name"]
        tag = " [iOS only]" if e.get("iosOnly") else (" [+ iOS]" if "usdzFile" in e else "")
        print(f"  {label}  ({e['sizeMB']} MB){tag}")


if __name__ == "__main__":
    main()
