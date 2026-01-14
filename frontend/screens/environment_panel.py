from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSlider,
    QPushButton,
    QHBoxLayout,
    QComboBox,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from frontend.i18n import _
from utils import get_static_path
import json


class EnvironmentPanel(QWidget):
    """Region panel: environment controls."""

    def __init__(
        self,
        color_preset=None,
        map_widget=None,
        species_config=None,
        species_panel=None,
    ):
        super().__init__()
        self.color_preset = color_preset
        self.map_widget = map_widget
        self.species_config = species_config
        self.species_panel = species_panel
        self.current_food_level = 5

        # Load region config for temperature ranges
        self.region_config = {}
        try:
            region_json_path = get_static_path("data/region.json")
            with open(region_json_path, "r") as f:
                self.region_config = json.load(f)
        except Exception:
            pass

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        self.title = QLabel(_("Region"))
        title_font = QFont("Minecraft", 15, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.title.setFont(title_font)
        layout.addWidget(self.title)

        self.region_combo = QComboBox()
        self.region_combo.addItems(
            ["Snowy Abyss", "Wasteland", "Evergreen Forest", "Corrupted Caves"]
        )
        self.region_combo.setFixedHeight(30)
        self.region_combo.currentTextChanged.connect(self.on_region_changed)
        layout.addWidget(self.region_combo)

        self.region_name_to_key = {
            "Snowy Abyss": "Snowy_Abyss",
            "Wasteland": "Wasteland",
            "Evergreen Forest": "Evergreen_Forest",
            "Corrupted Caves": "Corrupted_Caves",
        }

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
        layout.addWidget(self.temp_value_label)

        self.food_label_title = QLabel(_("Nahrung:"))
        layout.addWidget(self.food_label_title)

        self.food_label = QLabel("1/10")
        layout.addWidget(self.food_label)
        self.food_places_label = QLabel(_("Nahrungsplätze: 5"))
        layout.addWidget(self.food_places_label)

        self.food_places_slider = QSlider(Qt.Orientation.Horizontal)
        self.food_places_slider.setMinimum(1)
        self.food_places_slider.setMaximum(10)
        self.food_places_slider.setValue(5)
        self.food_places_slider.valueChanged.connect(
            lambda v: self.food_places_label.setText(
                _("Nahrungsplätze: {v}").format(v=v)
            )
        )
        layout.addWidget(self.food_places_slider)

        self.food_amount_label = QLabel(_("Nahrungsmenge: 50"))
        layout.addWidget(self.food_amount_label)

        # Food amount slider (was missing) - allows user to configure amount per food spot
        self.food_amount_slider = QSlider(Qt.Orientation.Horizontal)
        self.food_amount_slider.setMinimum(10)
        self.food_amount_slider.setMaximum(200)
        self.food_amount_slider.setValue(50)
        self.food_amount_slider.setTickInterval(10)
        self.food_amount_slider.valueChanged.connect(
            lambda v: self.food_amount_label.setText(
                _("Nahrungsmenge: {v}").format(v=v)
            )
        )
        layout.addWidget(self.food_amount_slider)

        day_night_layout = QHBoxLayout()
        day_btn = QPushButton(_("Tag"))
        day_btn.setCheckable(True)
        day_btn.setChecked(True)
        day_btn.clicked.connect(lambda: self.on_day_night_toggle(True))
        night_btn = QPushButton(_("Nacht"))
        night_btn.setCheckable(True)
        night_btn.clicked.connect(lambda: self.on_day_night_toggle(False))
        self.day_btn = day_btn
        self.night_btn = night_btn
        day_night_layout.addWidget(day_btn)
        day_night_layout.addWidget(night_btn)
        layout.addLayout(day_night_layout)

        layout.addStretch()
        self.setLayout(layout)
        # Initialize controls according to the currently selected region so
        # the temperature slider reflects the region's min/max on startup.
        try:
            self.on_region_changed(self.region_combo.currentText())
        except Exception:
            pass
        self.update_theme(self.color_preset)

    def on_day_night_toggle(self, is_day):
        self.day_btn.setChecked(is_day)
        self.night_btn.setChecked(not is_day)

    def on_region_changed(self, region_name):
        if self.map_widget:
            self.map_widget.set_region(region_name)
        self.update_temperature_range(region_name)
        self.update_species_compatibility(region_name)

    def update_temperature_range(self, region_name):
        region_key = self.region_name_to_key.get(region_name, "Wasteland")
        if region_key in self.region_config:
            region_data = self.region_config[region_key]
            min_temp = region_data.get("min_temp", -50)
            max_temp = region_data.get("max_temp", 50)
            self.temp_slider.setMinimum(min_temp)
            self.temp_slider.setMaximum(max_temp)
            mid_temp = (min_temp + max_temp) // 2
            self.temp_slider.setValue(mid_temp)
            try:
                self.temp_value_label.setText(
                    _("Temp: {value} C° ({min} bis {max})").format(
                        value=mid_temp, min=min_temp, max=max_temp
                    )
                )
            except Exception:
                self.temp_value_label.setText(
                    f"Temp: {mid_temp} C° ({min_temp} bis {max_temp})"
                )

    def get_selected_region(self):
        return self.region_combo.currentText()

    def get_temperature(self):
        return self.temp_slider.value()

    def get_food_places(self):
        return self.food_places_slider.value()

    def get_food_amount(self):
        try:
            return int(getattr(self, "food_amount_slider", None).value())
        except Exception:
            return 50

    def get_is_day(self):
        return self.day_btn.isChecked()

    def set_controls_enabled(self, enabled):
        self.region_combo.setEnabled(enabled)

    def set_species_panel(self, species_panel):
        """Set reference to species panel after it's created."""
        self.species_panel = species_panel

    def update_species_compatibility(self, region_name):
        """Enable/disable species checkboxes based on region temperature compatibility.

        Delegates to `species_panel.update_species_compatibility` when available; otherwise
        computes a fallback mid-temperature and applies compatibility by temperature.
        """
        # Prefer delegation when the species panel implements the logic
        try:
            if hasattr(self, "species_panel") and self.species_panel is not None:
                if hasattr(self.species_panel, "update_species_compatibility"):
                    try:
                        self.species_panel.update_species_compatibility(region_name)
                        return
                    except Exception:
                        pass
        except Exception:
            pass

        # Fallback: compute mid temperature for region and apply compatibility
        region_key = self.region_name_to_key.get(region_name, "Wasteland")
        if region_key in self.region_config:
            region_data = self.region_config[region_key]
            min_temp = region_data.get("min_temp", -50)
            max_temp = region_data.get("max_temp", 50)
            mid = (min_temp + max_temp) // 2
            self.update_species_compatibility_by_temp(mid)

    def update_species_compatibility_by_temp(self, temperature):
        """Enable/disable species checkboxes based on a specific temperature.

        Delegates to `species_panel.update_species_compatibility_by_temp` when available;
        otherwise toggles checkboxes found on the `species_panel` reference.
        """
        try:
            if hasattr(self, "species_panel") and self.species_panel is not None:
                if hasattr(self.species_panel, "update_species_compatibility_by_temp"):
                    try:
                        self.species_panel.update_species_compatibility_by_temp(
                            temperature
                        )
                        return
                    except Exception:
                        pass
        except Exception:
            pass

        # Fallback behavior: directly adjust any checkboxes present on species_panel
        try:
            for species_id, checkbox in getattr(
                self.species_panel, "species_checkboxes", {}
            ).items():
                species_data = (self.species_config or {}).get(species_id, {})
                species_min_temp = species_data.get("min_survival_temp", -100)
                species_max_temp = species_data.get("max_survival_temp", 100)
                can_survive = species_min_temp <= temperature <= species_max_temp
                try:
                    checkbox.setEnabled(can_survive)
                    checkbox.setChecked(can_survive)
                except Exception:
                    pass
        except Exception:
            pass

    def update_theme(self, preset):
        self.color_preset = preset

    def update_language(self):
        try:
            if hasattr(self, "title"):
                self.title.setText(_("Region"))
            if hasattr(self, "temp_label"):
                self.temp_label.setText(_("Temperatur:"))
        except Exception:
            pass
