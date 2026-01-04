"""
SettingsScreen - allow selecting a color theme at runtime.

Provides a simple UI with a dropdown of available themes and Apply/Cancel buttons.
Calling Apply will call back into the main app to change the active theme immediately.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QHBoxLayout,
    QPushButton,
)
from PyQt6.QtCore import Qt

from styles.color_presets import get_all_preset_names
from frontend.i18n import _


class SettingsScreen(QWidget):
    """Settings UI for runtime configuration (theme selection).

    Args:
        apply_callback: function(theme_name) -> None, called when user applies selection
        cancel_callback: function() -> None, called when user cancels/goes back
        color_preset: initial ColorPreset for theming the settings screen
    """

    def __init__(self, apply_callback, cancel_callback, color_preset=None):
        super().__init__()
        self.apply_callback = apply_callback
        self.cancel_callback = cancel_callback
        self.color_preset = color_preset
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel(_("Settings"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        # Theme selector
        theme_label = QLabel(_("Color Theme:"))
        layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        for name in get_all_preset_names():
            self.theme_combo.addItem(name)
        layout.addWidget(self.theme_combo)

        # Buttons
        btn_row = QHBoxLayout()
        btn_apply = QPushButton(_("Apply"))
        btn_apply.clicked.connect(self.on_apply)
        btn_row.addWidget(btn_apply)

        btn_cancel = QPushButton(_("Cancel"))
        btn_cancel.clicked.connect(self.on_cancel)
        btn_row.addWidget(btn_cancel)

        layout.addLayout(btn_row)

        layout.addStretch()
        self.setLayout(layout)

    def on_apply(self):
        selected = self.theme_combo.currentText()
        if self.apply_callback:
            self.apply_callback(selected)

    def on_cancel(self):
        if self.cancel_callback:
            self.cancel_callback()

    def update_theme(self, preset):
        """Update inline styles according to preset."""
        self.color_preset = preset
        bg = preset.get_color("bg_primary") if preset else "#2a2a2a"
        text = preset.get_color("text_primary") if preset else "#ffffff"
        self.setStyleSheet(f"background-color: {bg}; color: {text};")
        # Select current preset in combo if present
        try:
            if preset and hasattr(self, "theme_combo"):
                idx = self.theme_combo.findText(preset.name)
                if idx >= 0:
                    self.theme_combo.setCurrentIndex(idx)
        except Exception:
            pass
