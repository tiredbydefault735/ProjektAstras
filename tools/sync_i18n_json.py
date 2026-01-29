#!/usr/bin/env python3
"""Scan project for _(...) usages and ensure i18n JSON files contain all keys.

Usage: python tools/sync_i18n_json.py
"""
import argparse
import sys

# Prevent .pyc files (__pycache__) from being generated
sys.dont_write_bytecode = True

from pathlib import Path
import re
import json
import logging

ROOT = Path(__file__).parent.parent
I18N_DIR = ROOT / "i18n"

# Match _('...') or_("...") simple occurrences
pattern = re.compile(r"_\(\s*['\"](.*?)['\"]\s*\)")

logger = logging.getLogger(__name__)


def find_keys():
    keys = set()
    for p in ROOT.rglob("*.py"):
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            logger.warning(f"Could not read file {p}", exc_info=True)
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
        logger.error(f"Could not parse JSON file {p}", exc_info=True)
        sys.exit(1)


def write_json(p: Path, d: dict, dry_run: bool = False):
    if dry_run:
        logger.info(f"[Dry Run] Would write to {p}")
        return
    p.parent.mkdir(parents=True, exist_ok=True)

    temp_p = p.with_suffix(".tmp")
    temp_p.write_text(
        json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    # Atomic replace
    temp_p.replace(p)


def main(dry_run: bool = False):
    try:
        keys = find_keys()
        logger.info(f"Found {len(keys)} translatable keys")

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

        write_json(en_path, en, dry_run=dry_run)
        write_json(de_path, de, dry_run=dry_run)

        # Remove compiled .mo files if present
        removed = 0
        for mo in (
            I18N_DIR / "de" / "LC_MESSAGES" / "projektas.mo",
            I18N_DIR / "en" / "LC_MESSAGES" / "projektas.mo",
        ):
            try:
                if mo.exists():
                    if dry_run:
                        logger.info(f"[Dry Run] Would remove {mo}")
                    else:
                        mo.unlink()
                        removed += 1
                        logger.info(f"Removed {mo}")
            except Exception as e:
                logger.error(f"Failed to remove {mo}: {e}")

        logger.info(
            f"Wrote en.json (+{added_en}), de.json (+{added_de}), removed {removed} .mo files"
        )
    except Exception as e:
        logger.error(f"Sync process failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync i18n JSON files.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Do not write changes to files."
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging."
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    main(dry_run=args.dry_run)
