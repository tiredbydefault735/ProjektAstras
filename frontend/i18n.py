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
_current_lang = "de"
_po_catalog = {}
_gettext_trans = None
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
        Preference order (JSON-first):
            1) JSON at LOCALE_DIR/<lang>.json
            2) JSON at LOCALE_DIR/<lang>/projektas.json
            3) compiled .mo at LOCALE_DIR/<lang>/LC_MESSAGES/projektas.mo
            4) .po at LOCALE_DIR/<lang>/LC_MESSAGES/projektas.po
            5) .po at LOCALE_DIR/<lang>.po
            6) fallback JSON at LOCALE_DIR/<lang>.json (redundant but safe)
    """
    global _po_catalog, _gettext_trans
    debug = os.environ.get("I18N_DEBUG")
    _po_catalog = {}
    _gettext_trans = None

    # 1) JSON at top-level like i18n/en.json
    json_top = LOCALE_DIR / f"{lang}.json"
    if json_top.exists():
        try:
            with open(json_top, "r", encoding="utf-8") as f:
                _po_catalog = json.load(f)
                if debug:
                    print(f"i18n: loaded JSON top-level {json_top}")
                return
        except Exception:
            _po_catalog = {}

    # 2) JSON inside lang directory: i18n/<lang>/projektas.json
    json_inner = LOCALE_DIR / lang / "projektas.json"
    if json_inner.exists():
        try:
            with open(json_inner, "r", encoding="utf-8") as f:
                _po_catalog = json.load(f)
                if debug:
                    print(f"i18n: loaded JSON inner {json_inner}")
                return
        except Exception:
            _po_catalog = {}

    # 3) compiled .mo
    mo_path = LOCALE_DIR / lang / "LC_MESSAGES" / "projektas.mo"
    if mo_path.exists():
        try:
            _gettext_trans = gettext.translation(
                "projektas", localedir=str(LOCALE_DIR), languages=[lang]
            )
            if debug:
                print(f"i18n: loaded MO {mo_path}")
            return
        except Exception:
            _gettext_trans = None

    # 4) .po inside lang/LC_MESSAGES
    po_inner = LOCALE_DIR / lang / "LC_MESSAGES" / "projektas.po"
    if po_inner.exists():
        try:
            _po_catalog = _parse_po(po_inner)
            if debug:
                print(f"i18n: loaded PO inner {po_inner}")
            return
        except Exception:
            _po_catalog = {}

    # 5) top-level .po like i18n/en.po
    po_top = LOCALE_DIR / f"{lang}.po"
    if po_top.exists():
        try:
            _po_catalog = _parse_po(po_top)
            if debug:
                print(f"i18n: loaded PO top {po_top}")
            return
        except Exception:
            _po_catalog = {}

    # 6) fallback: try top-level JSON again (safe no-op)
    if json_top.exists():
        try:
            with open(json_top, "r", encoding="utf-8") as f:
                _po_catalog = json.load(f)
                if debug:
                    print(f"i18n: fallback loaded JSON top {json_top}")
        except Exception:
            _po_catalog = {}


def set_language(lang: str):
    global _current_lang
    _current_lang = lang
    _load_translations(lang)
    # notify listeners after changing language
    try:
        _notify_language_change()
    except Exception:
        pass
    # As a final guarantee, try to find top-level application windows and
    # call `update_language()` on known screen attributes so UI refreshes.
    try:
        debug = os.environ.get("I18N_DEBUG")
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            for w in QApplication.topLevelWidgets():
                try:
                    # common screen attribute names used in ArachfaraApp
                    for attr in (
                        "start_screen",
                        "simulation_screen",
                        "settings_screen",
                    ):
                        obj = getattr(w, attr, None)
                        if obj is not None and hasattr(obj, "update_language"):
                            try:
                                obj.update_language()
                                if debug:
                                    print(
                                        f"i18n: forced update_language on {attr} of {w}"
                                    )
                            except Exception as e:
                                if debug:
                                    print(
                                        f"i18n: error forcing update_language on {attr}: {e}"
                                    )
                except Exception:
                    pass
    except Exception:
        # Non-fatal: if PyQt is not available or no app running, ignore
        pass
    return True


# Language change listeners
_lang_listeners: list = []


def register_language_listener(fn):
    """Register a callback to be invoked when the language changes.

    The callback will be called with no arguments.
    """
    try:
        _lang_listeners.append(fn)
        # If debugging enabled, print registration info
        try:
            if os.environ.get("I18N_DEBUG"):
                print(f"i18n: registered listener {fn}")
        except Exception:
            pass
        # Call the listener once to ensure UI is in sync with current language
        try:
            fn()
        except Exception:
            try:
                if os.environ.get("I18N_DEBUG"):
                    print(f"i18n: initial listener call failed for {fn}")
            except Exception:
                pass
    except Exception:
        pass


def _notify_language_change():
    # Optional debug logging controlled by environment variable `I18N_DEBUG`.
    debug = os.environ.get("I18N_DEBUG")
    try:
        if debug:
            print(
                f"i18n: notifying {len(_lang_listeners)} listeners for lang {_current_lang}"
            )
    except Exception:
        pass

    for fn in list(_lang_listeners):
        try:
            fn()
        except Exception as e:
            try:
                if debug:
                    print(f"i18n: listener {fn} raised: {e}")
            except Exception:
                pass


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
            # also consider json files inside the lang dir (e.g. i18n/en/projektas.json)
            for j in p.glob("*.json"):
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
__all__ = [
    "_",
    "set_language",
    "get_language",
    "available_languages",
    "register_language_listener",
]
