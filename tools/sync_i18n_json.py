#!/usr/bin/env python3
"""Scan project for _(...) usages and ensure i18n JSON files contain all keys.

Usage: python tools/sync_i18n_json.py
"""
from pathlib import Path
import re
import json

ROOT = Path(__file__).parent.parent
I18N_DIR = ROOT / "i18n"

# Match _('...') or_("...") simple occurrences
pattern = re.compile(r"_\(\s*['\"](.*?)['\"]\s*\)")


def find_keys():
    keys = set()
    for p in ROOT.rglob("*.py"):
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in pattern.finditer(txt):
            keys.add(m.group(1))
    return sorted(keys)


def load_json(p: Path):
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(p: Path, d: dict):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(d, ensure_ascii=False, indent=4, sort_keys=True), encoding="utf-8"
    )


def main():
    keys = find_keys()
    print(f"Found {len(keys)} translatable keys")

    en_path = I18N_DIR / "en.json"
    de_path = I18N_DIR / "de.json"

    en = load_json(en_path)
    de = load_json(de_path)

    added_en = 0
    added_de = 0
    for k in keys:
        if k not in en:
            en[k] = k
            added_en += 1
        if k not in de:
            # If de already had a translation in a nested folder, keep it; otherwise default to key
            de[k] = de.get(k, k)
            added_de += 1

    write_json(en_path, en)
    write_json(de_path, de)

    # Remove compiled .mo files if present
    removed = 0
    for mo in (
        I18N_DIR / "de" / "LC_MESSAGES" / "projektas.mo",
        I18N_DIR / "en" / "LC_MESSAGES" / "projektas.mo",
    ):
        try:
            if mo.exists():
                mo.unlink()
                removed += 1
                print(f"Removed {mo}")
        except Exception as e:
            print(f"Failed to remove {mo}: {e}")

    print(
        f"Wrote en.json (+{added_en}), de.json (+{added_de}), removed {removed} .mo files"
    )


if __name__ == "__main__":
    main()
