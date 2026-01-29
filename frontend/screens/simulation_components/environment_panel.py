import json
import logging
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QSlider,
    QPushButton,
    QHBoxLayout,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

# Adjust path for utils
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from utils import get_static_path
from frontend.i18n import _

logger = logging.getLogger(__name__)


class EnvironmentPanel(QWidget):
    """Region environment controls panel.

    @ivar color_preset: Active color preset
    @ivar map_widget: Reference to the map widget
    @ivar species_config: Species configuration
    @ivar species_panel: Reference to species panel
    @ivar current_food_level: Current food level setting
    @ivar region_config: Loaded region configuration data
    """

    def __init__(
        self,
        color_preset=None,
        map_widget=None,
        species_config=None,
        species_panel=None,
    ):
        """Initialize the environment panel.

        @param color_preset: Optional color preset
        @param map_widget: Optional reference to simulation map widget
        @param species_config: Optional species configuration dict
        @param species_panel: Optional reference to species panel
        """
        super().__init__()
        self.color_preset = color_preset
        self.map_widget = map_widget  # Reference to map widget for updating background
        self.species_config = species_config  # Reference to species config
        self.species_panel = (
            species_panel  # Reference to species panel for checkbox control
        )
        self.current_food_level = 5  # Default food level (1-10)

        # Load region config for temperature ranges
        self.region_config = {}
        try:
            region_json_path = get_static_path("data/region.json")
            with open(region_json_path, "r", encoding="utf-8") as f:
                self.region_config = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load region.json: {e}")

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Title
        self.title = QLabel(_("Region"))
        title_font = QFont("Minecraft", 15, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.title.setFont(title_font)
        layout.addWidget(self.title)

        # Region Selection (subtitle removed; only title + combo)

        self.region_combo = QComboBox()
        self.region_combo.addItems(
            ["Snowy Abyss", "Wasteland", "Evergreen Forest", "Corrupted Caves"]
        )
        self.region_combo.setFixedHeight(30)
        self.region_combo.currentTextChanged.connect(self.on_region_changed)
        layout.addWidget(self.region_combo)

        # Store region name to key mapping
        self.region_name_to_key = {
            "Snowy Abyss": "Snowy_Abyss",
            "Wasteland": "Wasteland",
            "Evergreen Forest": "Evergreen_Forest",
            "Corrupted Caves": "Corrupted_Caves",
        }

        # Temperature Section
        self.temp_label = QLabel(_("Temperatur:"))
        temp_label_font = QFont("Minecraft", 12)
        temp_label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.temp_label.setFont(temp_label_font)
        layout.addWidget(self.temp_label)

        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(-50)
        self.temp_slider.setMaximum(50)
        self.temp_slider.setValue(20)
        layout.addWidget(self.temp_slider)

        self.temp_value_label = QLabel(_("Temp: 20 C°"))
        temp_value_font = QFont("Minecraft", 11)
        temp_value_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.temp_value_label.setFont(temp_value_font)
        self.temp_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp_slider.valueChanged.connect(self.on_temp_value_changed)
        layout.addWidget(self.temp_value_label)

        # Set initial temperature range based on default region (Snowy Abyss)
        self.update_temperature_range("Snowy Abyss")

        # Food Section
        self.food_label_title = QLabel(_("Nahrung:"))
        food_title_font = QFont("Minecraft", 12)
        food_title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.food_label_title.setFont(food_title_font)
        layout.addWidget(self.food_label_title)

        # Anzahl Nahrungsplätze
        # Food Level Label (missing initialization fix)
        self.food_label = QLabel("1/10")
        food_label_font = QFont("Minecraft", 11)
        food_label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.food_label.setFont(food_label_font)
        layout.addWidget(self.food_label)
        self.food_places_label = QLabel(_("Nahrungsplätze: 5"))
        food_places_font = QFont("Minecraft", 11)
        food_places_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.food_places_label.setFont(food_places_font)
        layout.addWidget(self.food_places_label)

        self.food_places_slider = QSlider(Qt.Orientation.Horizontal)
        self.food_places_slider.setMinimum(1)
        self.food_places_slider.setMaximum(10)
        self.food_places_slider.setValue(5)
        self.food_places_slider.valueChanged.connect(self.on_food_places_changed)
        layout.addWidget(self.food_places_slider)

        # Nahrungsmenge pro Platz
        self.food_amount_label = QLabel(_("Nahrungsmenge: 50"))
        food_amount_font = QFont("Minecraft", 11)
        food_amount_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.food_amount_label.setFont(food_amount_font)
        layout.addWidget(self.food_amount_label)

        self.food_amount_slider = QSlider(Qt.Orientation.Horizontal)
        self.food_amount_slider.setMinimum(10)
        self.food_amount_slider.setMaximum(200)
        self.food_amount_slider.setValue(50)
        self.food_amount_slider.valueChanged.connect(
            lambda v: self.food_amount_label.setText(
                _("Nahrungsmenge: {v}").format(v=v)
            )
        )
        layout.addWidget(self.food_amount_slider)

        # Day/Night Section
        self.day_night_label = QLabel(_("Tag - Nacht:"))
        day_night_label_font = QFont("Minecraft", 12)
        day_night_label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.day_night_label.setFont(day_night_label_font)
        layout.addWidget(self.day_night_label)

        day_night_layout = QHBoxLayout()
        day_night_layout.setSpacing(5)

        day_btn = QPushButton(_("Tag"))
        day_btn_font = QFont("Minecraft", 11)
        day_btn_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        day_btn.setFont(day_btn_font)
        day_btn.setFixedHeight(30)
        day_btn.setCheckable(True)
        day_btn.setChecked(True)
        day_btn.clicked.connect(lambda: self.on_day_night_toggle(True))
        day_night_layout.addWidget(day_btn)

        night_btn = QPushButton(_("Nacht"))
        night_btn_font = QFont("Minecraft", 11)
        night_btn_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        night_btn.setFont(night_btn_font)
        night_btn.setFixedHeight(30)
        night_btn.setCheckable(True)
        night_btn.clicked.connect(lambda: self.on_day_night_toggle(False))
        day_night_layout.addWidget(night_btn)

        self.day_btn = day_btn
        self.night_btn = night_btn
        self.start_is_day = True  # Default: Start bei Tag

        layout.addLayout(day_night_layout)

        layout.addStretch()

        self.setLayout(layout)
        self.update_theme(self.color_preset)
        try:
            from frontend.i18n import register_language_listener

            register_language_listener(self.update_language)
        except Exception:
            pass

    def on_day_night_toggle(self, is_day):
        """Toggle between day and night mode."""
        self.start_is_day = is_day
        if is_day:
            self.day_btn.setChecked(True)
            self.night_btn.setChecked(False)
        else:
            self.day_btn.setChecked(False)
            self.night_btn.setChecked(True)

    def on_region_changed(self, region_name):
        """Called when region selection changes."""
        if self.map_widget:
            self.map_widget.set_region(region_name)
        # Update temperature slider range based on region
        self.update_temperature_range(region_name)
        # Update species checkboxes based on region temperature compatibility
        self.update_species_compatibility(region_name)

    def update_temperature_range(self, region_name):
        """Update temperature slider min/max based on selected region."""
        # Convert display name to JSON key
        region_key = self.region_name_to_key.get(region_name, "Wasteland")

        if region_key in self.region_config:
            region_data = self.region_config[region_key]
            min_temp = region_data.get("min_temp", -50)
            max_temp = region_data.get("max_temp", 50)

            # Update slider range
            self.temp_slider.setMinimum(min_temp)
            self.temp_slider.setMaximum(max_temp)

            # Set value to middle of range
            mid_temp = (min_temp + max_temp) // 2
            self.temp_slider.setValue(mid_temp)

            # Update label with range info
            # Use translatable template for temperature display
            try:
                from frontend.i18n import _

                self.temp_value_label.setText(
                    _("Temp: {value} C° ({min} bis {max})").format(
                        value=mid_temp, min=min_temp, max=max_temp
                    )
                )
            except Exception:
                self.temp_value_label.setText(
                    f"Temp: {mid_temp} C° ({min_temp} bis {max_temp})"
                )

    def on_temp_value_changed(self, value):
        """Update label when temperature slider value changes."""
        min_temp = self.temp_slider.minimum()
        max_temp = self.temp_slider.maximum()
        try:
            from frontend.i18n import _

            self.temp_value_label.setText(
                _("Temp: {value} C° ({min} bis {max})").format(
                    value=value, min=min_temp, max=max_temp
                )
            )
        except Exception:
            self.temp_value_label.setText(
                f"Temp: {value} C° ({min_temp} bis {max_temp})"
            )
        # Update species compatibility based on selected temperature
        self.update_species_compatibility_by_temp(value)

    def update_species_compatibility(self, region_name):
        """Enable/disable species checkboxes based on region temperature compatibility."""
        if not self.species_panel or not self.species_config:
            return

        # Get region temperature range
        region_key = self.region_name_to_key.get(region_name, "Wasteland")
        if region_key not in self.region_config:
            return

        region_data = self.region_config[region_key]
        region_min_temp = region_data.get("min_temp", -50)
        region_max_temp = region_data.get("max_temp", 50)

        # Check each species
        for species_id, checkbox in self.species_panel.species_checkboxes.items():
            if species_id in self.species_config:
                species_data = self.species_config[species_id]
                species_min_temp = species_data.get("min_survival_temp", -100)
                species_max_temp = species_data.get("max_survival_temp", 100)

                # Check if species can survive in this region's temperature range
                # Species can survive if there's ANY overlap between region temp and survival temp
                can_survive = not (
                    region_max_temp < species_min_temp
                    or region_min_temp > species_max_temp
                )

                if not can_survive:
                    # Disable and uncheck species that can't survive
                    checkbox.setChecked(False)
                    checkbox.setEnabled(False)
                    checkbox.setStyleSheet(checkbox.styleSheet() + " color: #666666;")
                else:
                    # Enable species that can survive
                    checkbox.setEnabled(True)
                    # Reset style (will be updated by update_theme)

    def update_species_compatibility_by_temp(self, temperature):
        """Enable/disable species checkboxes based on specific temperature."""
        if not self.species_panel or not self.species_config:
            return

        # Check each species
        for species_id, checkbox in self.species_panel.species_checkboxes.items():
            if species_id in self.species_config:
                species_data = self.species_config[species_id]
                species_min_temp = species_data.get("min_survival_temp", -100)
                species_max_temp = species_data.get("max_survival_temp", 100)

                # Check if species can survive at this specific temperature
                can_survive = species_min_temp <= temperature <= species_max_temp

                if not can_survive:
                    # Disable and uncheck species that can't survive
                    checkbox.setChecked(False)
                    checkbox.setEnabled(False)
                    checkbox.setStyleSheet(checkbox.styleSheet() + " color: #666666;")
                else:
                    # Enable and auto-check species that can survive
                    checkbox.setEnabled(True)
                    checkbox.setChecked(True)
                    # Reset style (will be updated by update_theme)

    def set_species_panel(self, species_panel):
        """Set reference to species panel after it's created."""
        self.species_panel = species_panel

    def on_food_places_changed(self, v):
        """Handler for food places slider: update label and preview food on map."""
        try:
            # update label
            self.food_places_label.setText(_("Nahrungsplätze: {v}").format(v=v))
        except Exception:
            try:
                self.food_places_label.setText(f"Nahrungsplätze: {v}")
            except Exception:
                pass

        # preview on map if available
        try:
            amount = (
                self.food_amount_slider.value()
                if hasattr(self, "food_amount_slider")
                else 0
            )
            max_amount = (
                self.food_amount_slider.maximum()
                if hasattr(self, "food_amount_slider")
                else 100
            )
            if hasattr(self, "map_widget") and self.map_widget is not None:
                try:
                    # create a deterministic seed for preview so positions
                    # remain consistent when the simulation starts
                    import random

                    random_modifier = random.randint(0, 999999)
                    self._pending_food_seed = (
                        hash((v, amount)) ^ random_modifier
                    ) & 0xFFFFFFFF
                    self.map_widget.preview_food_sources(
                        v,
                        amount,
                        amount,
                        transition_progress=1.0,
                        seed=self._pending_food_seed,
                    )
                except Exception:
                    pass
        except Exception:
            pass

    def increase_food(self):
        """Increase food level."""
        self.current_food_level = min(10, self.current_food_level + 1)
        self.food_label.setText(f"{self.current_food_level}/10")

    def decrease_food(self):
        """Decrease food level."""
        self.current_food_level = max(1, self.current_food_level - 1)
        self.food_label.setText(f"{self.current_food_level}/10")

    def get_selected_region(self):
        """Get currently selected region."""
        return self.region_combo.currentText()

    def get_temperature(self):
        """Get current temperature value."""
        return self.temp_slider.value()

    def get_food_places(self):
        """Get number of food places."""
        return self.food_places_slider.value()

    def get_food_amount(self):
        """Get food amount per place."""
        return self.food_amount_slider.value()

    def get_is_day(self):
        """Get day/night state."""
        return self.day_btn.isChecked()

    def set_controls_enabled(self, enabled):
        """Enable/disable region selection (only before simulation starts)."""
        self.region_combo.setEnabled(enabled)

    def update_theme(self, preset):
        """Update inline styles for the environment panel."""
        self.color_preset = preset
        bg = preset.get_color("bg_primary") if preset else "#1a1a1a"
        border = preset.get_color("border_light") if preset else "#666666"
        text = preset.get_color("text_primary") if preset else "#ffffff"
        accent = preset.get_color("accent_primary") if preset else "#cc0000"
        bg_tertiary = preset.get_color("bg_tertiary") if preset else "#333333"
        text_secondary = preset.get_color("text_secondary") if preset else "#cccccc"

        # Panel background (no border for cleaner look)
        self.setStyleSheet(f"background-color: {bg}; border: none;")

        # Text elements
        self.title.setStyleSheet(f"color: {text}; background: transparent;")
        # region subtitle removed; no styling required
        self.temp_label.setStyleSheet(
            f"color: {text_secondary}; background: transparent;"
        )
        self.temp_value_label.setStyleSheet(f"color: {text}; background: transparent;")
        self.food_label_title.setStyleSheet(
            f"color: {text_secondary}; background: transparent;"
        )
        self.food_places_label.setStyleSheet(f"color: {text}; background: transparent;")
        self.food_amount_label.setStyleSheet(f"color: {text}; background: transparent;")
        self.day_night_label.setStyleSheet(
            f"color: {text_secondary}; background: transparent;"
        )

        # Style sliders (temp, food_places, food_amount)
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
        self.temp_slider.setStyleSheet(slider_style)
        self.food_places_slider.setStyleSheet(slider_style)
        self.food_amount_slider.setStyleSheet(
            f"""
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
        )

        # Style combobox
        combo_style = f"""
            QComboBox {{
                background-color: {bg_tertiary};
                color: {text};
                border: 1px solid {border};
                padding: 5px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {text};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {bg_tertiary};
                color: {text};
                selection-background-color: {accent};
            }}
        """
        self.region_combo.setStyleSheet(combo_style)

        # Style buttons
        button_style = f"""
            QPushButton {{
                background-color: {bg_tertiary};
                color: {text};
                border: none;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {accent};
            }}
            QPushButton:checked {{
                background-color: {accent};
            }}
        """
        self.day_btn.setStyleSheet(button_style)
        self.night_btn.setStyleSheet(button_style)
        # Ensure labels and small display boxes are transparent to avoid dark boxes
        try:
            if hasattr(self, "temp_label") and self.temp_label is not None:
                self.temp_label.setStyleSheet(
                    f"color: {text_secondary}; background: transparent;"
                )
            if hasattr(self, "temp_value_label") and self.temp_value_label is not None:
                self.temp_value_label.setStyleSheet(
                    f"color: {text}; background: transparent;"
                )
            if hasattr(self, "food_label") and self.food_label is not None:
                self.food_label.setStyleSheet(
                    f"color: {text}; background: transparent;"
                )
            if (
                hasattr(self, "food_places_label")
                and self.food_places_label is not None
            ):
                self.food_places_label.setStyleSheet(
                    f"color: {text}; background: transparent;"
                )
            if (
                hasattr(self, "food_amount_label")
                and self.food_amount_label is not None
            ):
                self.food_amount_label.setStyleSheet(
                    f"color: {text}; background: transparent;"
                )
        except Exception:
            pass

    def update_language(self) -> None:
        """Update UI texts for environment panel when language changes."""
        try:
            from frontend.i18n import _

            if hasattr(self, "title"):
                self.title.setText(_("Region"))
            # Region subtitle removed; nothing to update here
            if hasattr(self, "temp_label"):
                self.temp_label.setText(_("Temperatur:"))
            if hasattr(self, "food_label_title"):
                self.food_label_title.setText(_("Nahrung:"))
            # Update dynamic numeric labels to use translated templates
            try:
                if hasattr(self, "temp_slider") and hasattr(self, "temp_value_label"):
                    # Recompute temp display based on current slider value
                    min_temp = self.temp_slider.minimum()
                    max_temp = self.temp_slider.maximum()
                    cur = self.temp_slider.value()
                    self.temp_value_label.setText(
                        _("Temp: {value} C° ({min} bis {max})").format(
                            value=cur, min=min_temp, max=max_temp
                        )
                    )
            except Exception:
                pass
            try:
                if hasattr(self, "food_places_label") and hasattr(
                    self, "food_places_slider"
                ):
                    v = self.food_places_slider.value()
                    self.food_places_label.setText(_("Nahrungsplätze: {v}").format(v=v))
            except Exception:
                pass
            try:
                if hasattr(self, "food_amount_label") and hasattr(
                    self, "food_amount_slider"
                ):
                    v = self.food_amount_slider.value()
                    self.food_amount_label.setText(_("Nahrungsmenge: {v}").format(v=v))
            except Exception:
                pass
            if hasattr(self, "day_night_label"):
                self.day_night_label.setText(_("Tag - Nacht:"))
            # Update the individual day/night buttons if they exist
            try:
                if hasattr(self, "day_btn"):
                    self.day_btn.setText(_("Tag"))
                if hasattr(self, "night_btn"):
                    self.night_btn.setText(_("Nacht"))
            except Exception:
                pass
            # Update day/night buttons in EnvironmentPanel if present
            try:
                if hasattr(self, "environment_panel"):
                    if hasattr(self.environment_panel, "day_btn"):
                        self.environment_panel.day_btn.setText(_("Tag"))
                    if hasattr(self.environment_panel, "night_btn"):
                        self.environment_panel.night_btn.setText(_("Nacht"))
            except Exception:
                pass

        except Exception:
            pass
