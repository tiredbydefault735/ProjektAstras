"""
Dynamic stylesheet generator using color presets.
Supports easy theme switching without code changes.
"""

from typing import Optional, Any, Dict


def get_stylesheet(preset: Optional[Any] = None) -> str:
    """
    Generate stylesheet from a color preset.

    Args:
        preset: ColorPreset object. If None, uses DEFAULT_PRESET.

    Returns:
        CSS stylesheet string.
    """
    # Default color set (used when no preset object is provided)
    default_colors = {
        "bg_primary": "#2a2a2a",
        "bg_secondary": "#2a2a2a",
        "bg_tertiary": "#333333",
        "text_primary": "#ffffff",
        "text_secondary": "#cccccc",
        "text_tertiary": "#999999",
        "accent_primary": "#cc0000",
        "accent_light": "#ff3333",
        "accent_dark": "#990000",
        "border_light": "#666666",
        "border_dark": "#444444",
        "button_bg": "#333333",
        "button_hover": "#444444",
        "button_pressed": "#222222",
        "map_bg": "#ffffff",
        "map_border": "#000000",
        "log_text": "#33ff33",
    }

    if preset is None:
        c = default_colors
    else:
        # Support either an object with .colors or a plain dict
        c = getattr(preset, "colors", preset)

    return f"""
    /* Global styles */
    QWidget {{
        background-color: {c['bg_primary']};
        color: {c['text_primary']};
    }}
    
    QMainWindow {{
        background-color: {c['bg_primary']};
    }}
    
    /* Buttons - sharp, pixel-perfect */
    QPushButton {{
        background-color: {c['button_bg']};
        color: {c['text_primary']};
        border: 2px solid {c['accent_primary']};
        padding: 8px 16px;
        font-weight: bold;
        font-size: 14px;
    }}
    
    QPushButton:hover {{
        background-color: {c['button_hover']};
        border: 2px solid {c['accent_light']};
    }}
    
    QPushButton:pressed {{
        background-color: {c['button_pressed']};
        border: 2px solid {c['accent_dark']};
    }}
    
    /* Tab widget */
    QTabWidget {{
        background-color: {c['bg_primary']};
        border: none;
    }}
    
    QTabBar::tab {{
        background-color: {c['bg_secondary']};
        color: {c['text_primary']};
        border: 2px solid {c['border_light']};
        padding: 8px 20px;
        margin-right: 2px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {c['accent_primary']};
        border: 2px solid {c['accent_light']};
        color: {c['text_primary']};
    }}
    
    QTabBar::tab:hover {{
        background-color: {c['bg_tertiary']};
    }}
    
    /* Labels */
    QLabel {{
        color: {c['text_primary']};
        background-color: transparent;
    }}
    
    /* Sliders */
    QSlider::groove:horizontal {{
        background-color: {c['bg_secondary']};
        height: 6px;
        border: 1px solid {c['border_light']};
    }}
    
    QSlider::handle:horizontal {{
        background-color: {c['accent_primary']};
        width: 18px;
        margin: -6px 0;
        border: 1px solid {c['accent_light']};
    }}
    
    QSlider::handle:horizontal:hover {{
        background-color: {c['accent_light']};
    }}
    
    /* Checkboxes */
    QCheckBox {{
        color: {c['text_primary']};
        spacing: 8px;
    }}
    
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border: 2px solid {c['border_light']};
        background-color: {c['bg_secondary']};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {c['accent_primary']};
        border: 2px solid {c['accent_light']};
    }}
    
    /* Spin boxes and line edits */
    QSpinBox, QLineEdit {{
        background-color: {c['bg_secondary']};
        color: {c['text_primary']};
        border: 2px solid {c['border_light']};
        padding: 4px;
    }}
    
    QSpinBox:focus, QLineEdit:focus {{
        border: 2px solid {c['accent_primary']};
    }}
    
    /* Scroll bars */
    QScrollBar:vertical {{
        width: 12px;
        background-color: {c['bg_primary']};
        border: 1px solid {c['bg_secondary']};
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {c['border_light']};
        border: 1px solid {c['border_dark']};
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {c['border_dark']};
    }}
    
    QScrollBar:horizontal {{
        height: 12px;
        background-color: {c['bg_primary']};
        border: 1px solid {c['bg_secondary']};
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {c['border_light']};
        border: 1px solid {c['border_dark']};
        min-width: 20px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {c['border_dark']};
    }}
    
    /* Group boxes */
    QGroupBox {{
        color: {c['text_primary']};
        border: 2px solid {c['border_light']};
        border-radius: 0px;
        margin-top: 12px;
        padding-top: 12px;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
    }}
"""
