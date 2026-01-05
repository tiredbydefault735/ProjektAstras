"""
Color presets removed; provide a minimal compatibility shim.
This module now exposes a tiny API that other modules can import without
requiring a full theme system.
"""


class ColorPresetShim:
    def __init__(self, colors=None, name="Default"):
        self.name = name
        self.colors = colors or {}

    def get_color(self, key):
        return self.colors.get(key, "#1a1a1a")


DEFAULT_PRESET = ColorPresetShim()


def get_preset_by_name(name):
    return DEFAULT_PRESET


def get_all_preset_names():
    return ["Default"]
