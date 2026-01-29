import logging
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QSlider,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from utils import get_static_path
from frontend.i18n import _
from .custom_widgets import CustomCheckBox

logger = logging.getLogger(__name__)


class SpeciesPanel(QWidget):
    """Subspecies controls panel.

    @ivar color_preset: Active color preset
    @ivar species_config: Configuration dictionary for species
    @ivar species_checkboxes: Checkboxes for enabling/disabling species
    @ivar loner_speed_sliders: Sliders for loner speed
    @ivar clan_speed_sliders: Sliders for clan speed
    @ivar member_sliders: Sliders for initial member count
    @ivar member_value_labels: Labels displaying slider values
    """

    def __init__(self, species_config, color_preset=None):
        """Initialize the species panel.

        @param species_config: Dictionary containing species configuration
        @param color_preset: Optional color preset to apply
        """
        super().__init__()
        self.color_preset = color_preset
        self.species_config = species_config
        self.species_checkboxes = {}
        self.loner_speed_sliders = {}
        self.clan_speed_sliders = {}
        self.member_sliders = {}
        self.member_value_labels = {}
        # Keep label widgets so we can update their text on language change
        self.loner_speed_labels = {}
        self.clan_speed_labels = {}
        self.member_labels = {}

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(12)

        # Title
        self.title = QLabel(_("Spezies"))
        title_font = QFont("Minecraft", 15, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.title.setFont(title_font)
        layout.addWidget(self.title)

        # Create entry for each species
        species_names = {
            "Icefang": "Icefang",
            "Crushed_Critters": "Crushed Critters",
            "Spores": "Spores",
            "The_Corrupted": "The Corrupted",
        }

        for species_id, display_name in species_names.items():
            # Checkbox for enable/disable with custom icons
            unchecked_path = str(get_static_path("ui/Checkbox_unchecked.png"))
            checked_path = str(get_static_path("ui/Checkbox_checked.png"))
            # Debug logging removed: debug_log does not exist
            logger.debug(
                f"Checkbox unchecked: {unchecked_path}, exists: {Path(unchecked_path).exists()}"
            )

            checkbox = CustomCheckBox(display_name, unchecked_path, checked_path)
            checkbox_font = QFont("Minecraft", 12)
            checkbox_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
            checkbox.setFont(checkbox_font)
            checkbox.setChecked(True)
            self.species_checkboxes[species_id] = checkbox
            layout.addWidget(checkbox)

            # Loner speed slider
            loner_speed_layout = QHBoxLayout()
            loner_speed_layout.setSpacing(5)

            loner_speed_label = QLabel(_("Loner Speed:"))
            loner_speed_label_font = QFont("Minecraft", 11)
            loner_speed_label_font.setLetterSpacing(
                QFont.SpacingType.AbsoluteSpacing, 1
            )
            loner_speed_label.setFont(loner_speed_label_font)
            loner_speed_label.setFixedWidth(110)
            self.loner_speed_labels[species_id] = loner_speed_label
            loner_speed_layout.addWidget(loner_speed_label)

            loner_slider = QSlider(Qt.Orientation.Horizontal)
            loner_slider.setMinimum(1)
            loner_slider.setMaximum(10)
            loner_slider.setValue(5)
            self.loner_speed_sliders[species_id] = loner_slider
            loner_speed_layout.addWidget(loner_slider)

            layout.addLayout(loner_speed_layout)

            # Clan speed slider
            clan_speed_layout = QHBoxLayout()
            clan_speed_layout.setSpacing(5)

            clan_speed_label = QLabel(_("Clan Speed:"))
            clan_speed_label_font = QFont("Minecraft", 11)
            clan_speed_label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
            clan_speed_label.setFont(clan_speed_label_font)
            clan_speed_label.setFixedWidth(110)
            self.clan_speed_labels[species_id] = clan_speed_label
            clan_speed_layout.addWidget(clan_speed_label)

            clan_slider = QSlider(Qt.Orientation.Horizontal)
            clan_slider.setMinimum(1)
            clan_slider.setMaximum(10)
            clan_slider.setValue(5)
            self.clan_speed_sliders[species_id] = clan_slider
            clan_speed_layout.addWidget(clan_slider)

            layout.addLayout(clan_speed_layout)

            # Member slider with value display
            member_layout = QHBoxLayout()
            member_layout.setSpacing(5)

            member_label = QLabel(_("Mitglieder:"))
            member_label_font = QFont("Minecraft", 11)
            member_label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
            member_label.setFont(member_label_font)
            member_label.setFixedWidth(110)
            self.member_labels[species_id] = member_label
            member_layout.addWidget(member_label)

            member_value_label = QLabel("5")
            member_value_font = QFont("Minecraft", 11)
            member_value_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
            member_value_label.setFont(member_value_font)
            member_value_label.setFixedWidth(30)
            member_value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.member_value_labels[species_id] = member_value_label
            member_layout.addWidget(member_value_label)

            member_slider = QSlider(Qt.Orientation.Horizontal)
            member_slider.setMinimum(0)
            member_slider.setMaximum(30)
            member_slider.setValue(5)
            member_slider.valueChanged.connect(
                lambda value, sid=species_id: self.update_member_value(sid, value)
            )
            self.member_sliders[species_id] = member_slider
            member_layout.addWidget(member_slider)

            layout.addLayout(member_layout)

            # Add spacing between species
            layout.addSpacing(25)

        layout.addStretch()
        self.setLayout(layout)
        self.update_theme(self.color_preset)
        try:
            from frontend.i18n import register_language_listener

            register_language_listener(self.update_language)
        except Exception:
            pass

    # Note: EnvironmentPanel handles its own language updates.

    def update_language(self) -> None:
        """Update UI texts when language changes."""
        try:
            from frontend.i18n import _

            if hasattr(self, "title"):
                self.title.setText(_("Spezies"))
            # species subtitle removed
            # Update per-species labels (loner/clan/member)
            try:
                for sid in self.species_checkboxes.keys():
                    if sid in self.loner_speed_labels:
                        self.loner_speed_labels[sid].setText(_("Loner Speed:"))
                    if sid in self.clan_speed_labels:
                        self.clan_speed_labels[sid].setText(_("Clan Speed:"))
                    if sid in self.member_labels:
                        self.member_labels[sid].setText(_("Mitglieder:"))
            except Exception:
                pass
        except Exception:
            pass

    def update_member_value(self, species_id, value):
        """Update the member value label when slider changes."""
        if species_id in self.member_value_labels:
            self.member_value_labels[species_id].setText(str(value))

    def get_enabled_species_populations(self):
        """Get populations for enabled species based on member sliders."""
        populations = {}
        for species_id, checkbox in self.species_checkboxes.items():
            if checkbox.isChecked():
                populations[species_id] = self.member_sliders[species_id].value()
        return populations

    def update_theme(self, preset):
        """Update inline styles for the species panel."""
        self.color_preset = preset
        bg = preset.get_color("bg_primary") if preset else "#1a1a1a"
        border = preset.get_color("border_light") if preset else "#666666"
        text = preset.get_color("text_primary") if preset else "#ffffff"
        accent = preset.get_color("accent_primary") if preset else "#cc0000"
        # Additional fallbacks used below to avoid calling preset.get_color when preset is None
        bg_tertiary = preset.get_color("bg_tertiary") if preset else "#333333"
        text_secondary = preset.get_color("text_secondary") if preset else "#cccccc"

        # Panel background (no border for cleaner look)
        self.setStyleSheet(f"background-color: {bg}; border: none;")

        # Text elements
        self.title.setStyleSheet(f"color: {text}; background: transparent;")
        # species subtitle removed; no styling required

        # Style checkboxes and sliders
        for checkbox in self.species_checkboxes.values():
            checkbox.setStyleSheet(
                f"""
                QCheckBox {{
                    color: {text};
                    background: transparent;
                    spacing: 8px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: none;
                    background: transparent;
                }}
                QCheckBox::indicator:checked {{
                    background: transparent;
                }}
            """
            )

        # Keep the slider groove visible (thin line) but transparent container backgrounds
        slider_style = f"""
            QSlider {{
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {border};
                height: 2px;
                background: transparent;
                border-radius: 1px;
            }}
            QSlider::sub-page:horizontal, QSlider::add-page:horizontal {{
                background: transparent;
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                border: none;
                width: 12px;
                height: 12px;
                margin: -5px 0;
                border-radius: 2px;
            }}
        """

        for slider in self.loner_speed_sliders.values():
            slider.setStyleSheet(slider_style)

        for slider in self.clan_speed_sliders.values():
            slider.setStyleSheet(slider_style)

        for slider in self.member_sliders.values():
            slider.setStyleSheet(slider_style)

        # Make sure labels and value boxes have transparent backgrounds
        try:
            for sid, lbl in self.loner_speed_labels.items():
                lbl.setStyleSheet(f"color: {text}; background: transparent;")
            for sid, lbl in self.clan_speed_labels.items():
                lbl.setStyleSheet(f"color: {text}; background: transparent;")
            for sid, lbl in self.member_labels.items():
                lbl.setStyleSheet(f"color: {text}; background: transparent;")
            for sid, val in self.member_value_labels.items():
                val.setStyleSheet(f"color: {text}; background: transparent;")
        except Exception:
            pass
