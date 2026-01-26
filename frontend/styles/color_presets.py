"""
Color presets removed; provide a minimal compatibility shim.
This module now exposes a tiny API that other modules can import without
requiring a full theme system.
"""

from typing import Optional, Dict, List, Any


class ColorPresetShim:
    def __init__(
        self, colors: Optional[Dict[str, str]] = None, name: str = "Default"
    ) -> None:
        self.name = name
        self.colors = colors or {}

    def get_color(self, key: str) -> str:
        return self.colors.get(key, "#1a1a1a")


DEFAULT_PRESET = ColorPresetShim()


def get_preset_by_name(name: str) -> ColorPresetShim:
    return DEFAULT_PRESET


def get_all_preset_names() -> List[str]:
    return ["Default"]
