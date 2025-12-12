"""
Color theme presets for ProjektAstras.
Modular color system for easy theme switching.
"""


class ColorPreset:
    """Base color preset class."""

    def __init__(self, name, colors):
        self.name = name
        self.colors = colors

    def get_color(self, key):
        """Get a color by key."""
        return self.colors.get(key, "#1a1a1a")


# Default Dark theme with red accents
DARK_RED = ColorPreset(
    name="Dark Red",
    colors={
        # Main colors
        "bg_primary": "#2a2a2a",
        "bg_secondary": "#2a2a2a",
        "bg_tertiary": "#333333",
        "text_primary": "#ffffff",
        "text_secondary": "#cccccc",
        "text_tertiary": "#999999",
        # Accent colors
        "accent_primary": "#cc0000",
        "accent_light": "#ff3333",
        "accent_dark": "#990000",
        # UI elements
        "border_light": "#666666",
        "border_dark": "#444444",
        "button_bg": "#333333",
        "button_hover": "#444444",
        "button_pressed": "#222222",
        # Special
        "map_bg": "#ffffff",
        "map_border": "#000000",
        "log_text": "#33ff33",
    },
)

# Blue theme variant
DARK_BLUE = ColorPreset(
    name="Dark Blue",
    colors={
        "bg_primary": "#1a2a3a",
        "bg_secondary": "#1a202c",
        "bg_tertiary": "#2d3748",
        "text_primary": "#ffffff",
        "text_secondary": "#cbd5e0",
        "text_tertiary": "#a0aec0",
        "accent_primary": "#2196f3",
        "accent_light": "#64b5f6",
        "accent_dark": "#1565c0",
        "border_light": "#4a5568",
        "border_dark": "#2d3748",
        "button_bg": "#2d3748",
        "button_hover": "#4a5568",
        "button_pressed": "#1a202c",
        "map_bg": "#ffffff",
        "map_border": "#000000",
        "log_text": "#4ade80",
    },
)

# Green theme variant
DARK_GREEN = ColorPreset(
    name="Dark Green",
    colors={
        "bg_primary": "#2a4a2a",
        "bg_secondary": "#2d5a2d",
        "bg_tertiary": "#3a7a3a",
        "text_primary": "#ffffff",
        "text_secondary": "#d4e8d4",
        "text_tertiary": "#a8d5a8",
        "accent_primary": "#22c55e",
        "accent_light": "#4ade80",
        "accent_dark": "#16a34a",
        "border_light": "#4ade80",
        "border_dark": "#22c55e",
        "button_bg": "#2d5a2d",
        "button_hover": "#3a7a3a",
        "button_pressed": "#1a2e1a",
        "map_bg": "#ffffff",
        "map_border": "#000000",
        "log_text": "#4ade80",
    },
)

# Purple theme variant
DARK_PURPLE = ColorPreset(
    name="Dark Purple",
    colors={
        "bg_primary": "#2a1a4a",
        "bg_secondary": "#2d1b4e",
        "bg_tertiary": "#3d2766",
        "text_primary": "#ffffff",
        "text_secondary": "#e0d4f7",
        "text_tertiary": "#c4a8f0",
        "accent_primary": "#a855f7",
        "accent_light": "#d946ef",
        "accent_dark": "#7e22ce",
        "border_light": "#a855f7",
        "border_dark": "#7e22ce",
        "button_bg": "#2d1b4e",
        "button_hover": "#3d2766",
        "button_pressed": "#1a0f2e",
        "map_bg": "#ffffff",
        "map_border": "#000000",
        "log_text": "#d946ef",
    },
)

# All available presets
AVAILABLE_PRESETS = [
    DARK_RED,
    DARK_BLUE,
    DARK_GREEN,
    DARK_PURPLE,
]

# Default preset
DEFAULT_PRESET = DARK_RED


def get_preset_by_name(name):
    """Get a preset by name."""
    for preset in AVAILABLE_PRESETS:
        if preset.name.lower() == name.lower():
            return preset
    return DEFAULT_PRESET


def get_all_preset_names():
    """Get all available preset names."""
    return [preset.name for preset in AVAILABLE_PRESETS]
