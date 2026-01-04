import json
import os
import os
import json
import gettext
from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "static" / "locale"

_current_lang = "en"
_po_catalog = {}
_gettext_trans = None

import json
import gettext
from pathlib import Path

# Locale directory (project root)/i18n
# Translations are stored under `i18n/<lang>/LC_MESSAGES/*.mo`
LOCALE_DIR = Path(__file__).parent.parent / "i18n"

# Current runtime state
_current_lang = "en"
_po_catalog = {}
_gettext_trans = None


def _parse_po(path: Path) -> dict:
    """Very small PO parser that extracts msgid/msgstr pairs."""
    entries = {}
    msgid = None
    msgstr = None
    state = None
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.startswith("#") or line.strip() == "":
                continue
            if line.startswith("msgid "):
                msgid = eval(line[6:])
                msgstr = ""
                state = "id"
            elif line.startswith("msgstr "):
                msgstr = eval(line[7:])
                state = "str"
            elif line.startswith('"') and state is not None:
                txt = eval(line)
                if state == "id":
                    msgid += txt
                elif state == "str":
                    msgstr += txt
            else:
                if msgid is not None:
                    entries[msgid] = msgstr
                msgid = None
                msgstr = None
                state = None
    if msgid is not None:
        entries[msgid] = msgstr
    # drop header entry
    if "" in entries:
        entries.pop("")
    return entries


def _load_translations(lang: str):
    """Load translations for `lang`.

    Preference order:
      1) compiled .mo at LOCALE_DIR/<lang>/LC_MESSAGES/projektas.mo
      2) .po at LOCALE_DIR/<lang>/LC_MESSAGES/projektas.po
      3) .po at LOCALE_DIR/<lang>.po
      4) JSON at LOCALE_DIR/<lang>.json
    """
    global _po_catalog, _gettext_trans
    _po_catalog = {}
    _gettext_trans = None

    # 1) compiled .mo
    mo_path = LOCALE_DIR / lang / "LC_MESSAGES" / "projektas.mo"
    if mo_path.exists():
        try:
            _gettext_trans = gettext.translation(
                "projektas", localedir=str(LOCALE_DIR), languages=[lang]
            )
            return
        except Exception:
            _gettext_trans = None

    # 2) .po inside lang/LC_MESSAGES
    po_inner = LOCALE_DIR / lang / "LC_MESSAGES" / "projektas.po"
    if po_inner.exists():
        try:
            _po_catalog = _parse_po(po_inner)
            return
        except Exception:
            _po_catalog = {}

    # 3) top-level .po like locale/en.po
    po_top = LOCALE_DIR / f"{lang}.po"
    if po_top.exists():
        try:
            _po_catalog = _parse_po(po_top)
            return
        except Exception:
            _po_catalog = {}

    # 4) JSON fallback
    json_path = LOCALE_DIR / f"{lang}.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                _po_catalog = json.load(f)
        except Exception:
            _po_catalog = {}


def set_language(lang: str):
    global _current_lang
    _current_lang = lang
    _load_translations(lang)


def get_language() -> str:
    return _current_lang


def available_languages() -> list:
    """Return discovered language identifiers present in `LOCALE_DIR`."""
    langs = set()
    # top-level JSON/PO files: en.json, en.po
    for p in LOCALE_DIR.glob("*.json"):
        langs.add(p.stem)
    for p in LOCALE_DIR.glob("*.po"):
        langs.add(p.stem)
    # directories like 'en', 'de'
    for p in LOCALE_DIR.iterdir():
        if p.is_dir():
            langs.add(p.name)
    return sorted(langs)


def _(text: str) -> str:
    """Translate `text` using loaded catalog or gettext translation."""
    if _gettext_trans is not None:
        try:
            return _gettext_trans.gettext(text)
        except Exception:
            pass
    try:
        return _po_catalog.get(text, text)
    except Exception:
        return text


# initialize default language
set_language(_current_lang)


# Export shorthand
__all__ = ["_", "set_language", "get_language", "available_languages"]
