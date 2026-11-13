#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_all_swatches 3.28.py  -  Kitchen Prompt Generator V3.28 swatch environment setup
=============================================================================
Double-click this file (or run `python setup_all_swatches.py`) from the folder
that contains kitchen_prompt_generator V3.28.html.

What it does
------------
1. Creates the six case-sensitive swatch folders next to this script.
2. For every swatch name the dashboard can request, writes a valid 1x1 grey
   baseline JPEG named exactly "<option name>.jpg" - but ONLY if that file
   does not already exist.
3. Never overwrites, deletes, renames or modifies anything that is already
   on disk. Files are opened in exclusive-create mode, so even a race with
   another program cannot clobber an existing file.
4. Prints a status report and waits for ENTER so the window stays open.

Source of the filename matrix
-----------------------------
Parsed from the V3.28 dashboard (swatchList()/DDM/swPath()): the dashboard
requests ./<folder>/<option value>.jpg for every selectable option
(group headers are not options). Expected totals, identical to the
dashboard's own built-in self-test: 18 / 9 / 57 / 49 / 8 / 12 = 153 files.
The dashboard's "Flooring Materials" folder serves BOTH the flooring-species
dropdown (18 woods) and the flooring-stone dropdown (31 stones) = 49 files.
"""

import base64
import os
import sys
import traceback
from pathlib import Path

# --------------------------------------------------------------------------
# Baseline image: 1x1 solid grey baseline JPEG (332 bytes), SOI..EOI intact.
# --------------------------------------------------------------------------
_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oACAEBAAA/APSK/9k="
)

# --------------------------------------------------------------------------
# Filename matrix (folder -> option names). Folder names are case-sensitive
# and must match the dashboard's FOLDERS array exactly.
# --------------------------------------------------------------------------
WOODS = [
        'White Oak',
        'Red Oak',
        'American Walnut',
        'Hard Maple',
        'Black Cherry',
        'White Ash',
        'Hickory',
        'Alder',
        'Knotty Pine',
        'Douglas Fir',
        'White Cedar',
        'Redwood',
        'Genuine Teak',
        'African Mahogany',
        'White Ebony',
        'Zebrawood',
        'Wenge',
        'Rosewood',
    ]

GRAINS = [
        'Straight Grain',
        'Flat-sawn (Cathedral)',
        'Rift-sawn (Linear)',
        'Quarter-sawn',
        'Book-matched Vertical',
        'Slip-matched',
        'Chevron Diagonal',
        'Herringbone',
        'End-Grain Block',
    ]

COUNTERTOP = [
        'Calacatta Gold',
        'Carrara White',
        'Statuario',
        'Thassos White',
        'Arabescato',
        'Mystery White',
        'Volakas',
        'Arabescato Breccia',
        'Bianco Lasa',
        'Calacatta Monet',
        'Calacatta Ondulato',
        'Calacatta Picasso',
        'Calacatta Zebrino Verde',
        'Calacatta-Borghini',
        'Nero Marquina',
        'Black Mirage',
        'Saint Laurent',
        'Nero Portoro',
        'Black Dune',
        'Blue Violet Black',
        'Saint Laurent Black',
        'Blue Pearl Granite',
        'Black Basalt',
        'Pietra Grey',
        'Bardiglio Nuvolato',
        'Invisible Grey',
        'Calacatta Viola',
        'Fior di Bosco',
        'Unfilled Silver Travertine',
        'Pacific Grey',
        'Picasso Grey',
        'Grey Basalt',
        'Crema Marfil',
        'Emperador Dark',
        'Breccia Oniciata',
        'Botticino',
        'Sequoia Brown',
        'Walnut Travertine',
        'Breccia Sarda',
        'Verde Alpi',
        'Rosso Levanto',
        'Blue de Savoie',
        'Blue Sodalite',
        'Lilac',
        'Abbey Green',
        'Calacatta Cipollino',
        'Cipollino Verde',
        'Connemara Irish Green',
        'Fantastico Arni',
        'Green Botanic Wave',
        'Ming Green',
        'Verde Borgogna',
        'Verde Guatemala',
        'Verde Luana',
        'Cipollino Verde Ondulato',
        'Onice-Fantastico',
        'Tiger Onyx',
    ]

FLOOR_STONES = [
        'Carrara Marble',
        'Calacatta Marble',
        'Thassos White Marble',
        'Crema Marfil Limestone',
        'Ivory Travertine',
        'Bardiglio Marble',
        'Grey Basalt',
        'Slate Grey',
        'Bluestone Limestone',
        'Nero Marquina Marble',
        'Absolute Black Granite',
        'Black Basalt',
        'Black Slate',
        'Noce Travertine',
        'Emperador Dark Marble',
        'Jerusalem Gold Limestone',
        'Buff Sandstone',
        'Verde Alpi Marble',
        'Serpentine Green',
        'Green Slate',
        'Azul Macaubas Quartzite',
        'Blue Pearl Granite',
        'Rosso Verona Marble',
        'Rosa Portogallo Marble',
        'Red Sandstone',
        'Terracotta-toned Limestone',
        'Giallo Siena Marble',
        'Golden Sandstone',
        'Honey Onyx',
        'Terrazzo (multi-colour chips)',
        'Pebble Mosaic',
    ]

FLOORING_WOOD_PATTERNS = [
        'Straight (Plank)',
        'Herringbone',
        'Chevron',
        'Basketweave',
        'Versailles (Parquet Blocks)',
        'Brick pattern',
        'Diagonal',
        'Hexagon',
    ]

FLOORING_STONE_PATTERNS = [
        'Vein-Cut',
        'Cross-Cut (Fleuri)',
        'Bookmatched',
        'Slipmatched',
        'Diamond',
        'Herringbone',
        'Chevron',
        'Checkerboard',
        'Basketweave',
        'Versailles',
        'Hexagon',
        'Medallion Mosaic',
    ]

def _dedupe(seq):
    seen, out = set(), []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out

SWATCH_MATRIX = {
    "Wood Species": _dedupe(WOODS),
    "Grain & cut": _dedupe(GRAINS),
    "Countertop Materials": _dedupe(COUNTERTOP),
    "Flooring Materials": _dedupe(WOODS + FLOOR_STONES),
    "Flooring Patterns Wood": _dedupe(FLOORING_WOOD_PATTERNS),
    "Flooring Patterns Stone": _dedupe(FLOORING_STONE_PATTERNS),
}
EXPECTED_COUNTS = {
    "Wood Species": 18,
    "Grain & cut": 9,
    "Countertop Materials": 57,
    "Flooring Materials": 49,
    "Flooring Patterns Wood": 8,
    "Flooring Patterns Stone": 12,
}

_ILLEGAL_CHARS = set('<>:"/\\|?*')


def _configure_console():
    """Avoid UnicodeEncodeError on legacy Windows consoles."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _wait_for_user():
    """Persistent terminal hold so a double-clicked window never vanishes."""
    print()
    while True:
        try:
            input("Press ENTER to close this window...")
            break
        except EOFError:           # no interactive stdin available
            break
        except KeyboardInterrupt:
            break


def _jpeg_bytes():
    data = base64.b64decode(_JPEG_B64)
    if not (data.startswith(b"\xff\xd8") and data.endswith(b"\xff\xd9")):
        raise RuntimeError("Embedded JPEG payload failed its SOI/EOI check.")
    return data


def _validate_matrix():
    problems = []
    for folder, names in SWATCH_MATRIX.items():
        if len(names) != EXPECTED_COUNTS[folder]:
            problems.append(f"{folder}: expected {EXPECTED_COUNTS[folder]} names, got {len(names)}")
        for n in names:
            if _ILLEGAL_CHARS.intersection(n):
                problems.append(f"{folder}/{n}: contains a character illegal in Windows filenames")
    return problems


def _ensure_folder(base: Path, name: str, report: dict):
    """Create folder only if absent. Returns the Path, or None if unusable."""
    path = base / name
    # Warn about case-variant lookalikes (matters on case-sensitive systems).
    try:
        for entry in base.iterdir():
            if entry.name != name and entry.name.lower() == name.lower():
                report["warnings"].append(
                    f'Found "{entry.name}" but the dashboard needs exactly "{name}". '
                    f"Rename it if it holds your real textures."
                )
    except OSError:
        pass

    if path.is_dir():
        report["folders_existing"].append(name)
        return path
    if path.exists():
        report["errors"].append(f'"{name}" exists but is a FILE, not a folder. Left untouched.')
        return None
    try:
        path.mkdir(parents=False, exist_ok=False)
        report["folders_created"].append(name)
        return path
    except FileExistsError:
        report["folders_existing"].append(name)
        return path if path.is_dir() else None
    except OSError as exc:
        report["errors"].append(f'Could not create folder "{name}": {exc}')
        return None


_OTHER_EXT = (".png", ".jpeg", ".webp", ".jpe", ".gif", ".bmp", ".tif", ".tiff", ".avif")


def _scan_folder(folder_path: Path):
    """Snapshot of what is already in a folder (lower-cased names -> real names)."""
    try:
        return {e.name.lower(): e.name for e in folder_path.iterdir()}
    except OSError:
        return {}


def _write_placeholder(folder_path: Path, filename: str, payload: bytes, existing: dict):
    """
    Returns ("created"|"kept"|"error: ...", note).
    A placeholder is written ONLY when nothing with that name exists in the folder
    (compared case-insensitively, so "white oak.JPG" also counts as present).
    Existing files are never opened for writing, so they can never be altered.
    """
    key = filename.lower()
    if key in existing:
        note = "" if existing[key] == filename else f'(found as "{existing[key]}")'
        return "kept", note
    target = folder_path / filename
    if target.exists() or target.is_symlink():
        return "kept", ""
    try:
        with open(target, "xb") as fh:        # "x" = fail if it already exists
            fh.write(payload)
        existing[key] = filename
        return "created", ""
    except FileExistsError:
        return "kept", ""
    except OSError as exc:
        return f"error: {exc}", ""


def main():
    _configure_console()
    base = Path(__file__).resolve().parent     # same folder as the dashboard HTML
    try:
        os.chdir(base)
    except OSError:
        pass

    print("=" * 64)
    print(" Kitchen Prompt Generator V3.28 - swatch environment setup")
    print("=" * 64)
    print(f" Target directory: {base}")
    print()

    problems = _validate_matrix()
    if problems:
        print("INTERNAL MATRIX CHECK FAILED - nothing was written:")
        for p in problems:
            print("  -", p)
        return

    payload = _jpeg_bytes()
    report = {
        "folders_created": [], "folders_existing": [],
        "created": {}, "skipped": {}, "failed": {},
        "errors": [], "warnings": [],
    }

    if not (base / "kitchen_prompt_generator V3.28.html").exists():
        report["warnings"].append(
            "kitchen_prompt_generator V3.28.html is not in this folder. "
            "Move this script next to the dashboard (or move the folders afterwards)."
        )

    for folder, names in SWATCH_MATRIX.items():
        created = skipped = 0
        fpath = _ensure_folder(base, folder, report)
        if fpath is None:
            report["failed"][folder] = len(names)
            print(f"[FAIL] {folder}: folder unavailable")
            continue
        existing = _scan_folder(fpath)
        kept_names = []
        for name in names:
            result, note = _write_placeholder(fpath, name + ".jpg", payload, existing)
            if result == "created":
                created += 1
                stem = name.lower()
                for ext in _OTHER_EXT:
                    if stem + ext in existing:
                        report["warnings"].append(
                            f'{folder}: "{existing[stem + ext]}" exists in another format. '
                            f'The dashboard only loads .jpg, so a placeholder "{name}.jpg" was added; '
                            f"convert your image to .jpg to replace it."
                        )
                        break
            elif result == "kept":
                skipped += 1
                kept_names.append(name + ".jpg" + (" " + note if note else ""))
            else:
                report["failed"][folder] = report["failed"].get(folder, 0) + 1
                report["errors"].append(f"{folder}/{name}.jpg -> {result}")
        report["created"][folder] = created
        report["skipped"][folder] = skipped
        report.setdefault("kept_names", {})[folder] = kept_names
        print(f"[ OK ] {folder:<26} new: {created:>3}   kept existing: {skipped:>3}   total: {len(names):>3}")

    total_new = sum(report["created"].values())
    total_kept = sum(report["skipped"].values())
    total_fail = sum(report["failed"].values())
    total_all = sum(len(v) for v in SWATCH_MATRIX.values())

    print()
    print("-" * 64)
    print(f" Folders created : {len(report['folders_created'])}   already present: {len(report['folders_existing'])}")
    print(f" Placeholders    : {total_new} written")
    print(f" Existing files  : {total_kept} found and left untouched (never overwritten)")
    print(f" Failures        : {total_fail}")
    print(f" Matrix size     : {total_all} swatches (expected 153)")
    print("-" * 64)
    kept_all = report.get("kept_names", {})
    if any(kept_all.values()):
        print(" Existing images found and left untouched:")
        for folder, lst in kept_all.items():
            if not lst:
                continue
            shown = lst[:25]
            print(f"   {folder} ({len(lst)}): " + ", ".join(shown) + (f", ... +{len(lst) - 25} more" if len(lst) > 25 else ""))
        print("-" * 64)
    for w in report["warnings"]:
        print("WARNING:", w)
    for e in report["errors"]:
        print("ERROR:  ", e)
    print()
    if total_fail or report["errors"]:
        print("Finished WITH problems - see above.")
    else:
        print("Done. Replace any placeholder with your real texture using the")
        print("same file name (keep the .jpg extension). In the dashboard,")
        print("click 'Check swatch folders' to confirm.")
        print("Note: placeholders are 1x1 grey, so they count as 'found' in the audit.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\nUNEXPECTED ERROR - no existing files were modified:\n")
        traceback.print_exc()
    finally:
        _wait_for_user()
