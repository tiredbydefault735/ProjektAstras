from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QCheckBox,
    QSlider,
)
from PyQt6.QtGui import QFont
from frontend.i18n import _


class SpeciesPanel(QWidget):
    """Species panel: subspecies controls."""

    def __init__(self, species_config, color_preset=None):
        super().__init__()
        self.color_preset = color_preset
        self.species_config = species_config
        self.species_checkboxes = {}
        self.loner_speed_sliders = {}
        self.clan_speed_sliders = {}
        self.loner_speed_value_labels = {}
        self.clan_speed_value_labels = {}
        self.member_sliders = {}
        self.member_value_labels = {}
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

        # Populate controls for each species from config
        try:
            for species_name, cfg in (self.species_config or {}).items():
                # Container row for this species
                row = QHBoxLayout()
                row.setSpacing(8)

                chk = QCheckBox(species_name)
                chk.setChecked(True)
                chk.setToolTip(cfg.get("home_region", ""))
                row.addWidget(chk)
                self.species_checkboxes[species_name] = chk

                # Member slider: 1 .. max_clan_members (fallback 1..10)
                max_members = int(cfg.get("max_clan_members", 6))
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setMinimum(1)
                slider.setMaximum(max(1, max_members))
                default_members = max(1, int(slider.maximum() // 2))
                slider.setValue(default_members)
                slider.setFixedWidth(120)
                row.addWidget(slider)
                self.member_sliders[species_name] = slider

                # Member value label
                lbl = QLabel(str(default_members))
                lbl.setFixedWidth(28)
                row.addWidget(lbl)
                self.member_value_labels[species_name] = lbl

                # Wire slider to update label
                try:
                    slider.valueChanged.connect(
                        lambda v, s=species_name: self.update_member_value(s, v)
                    )
                except Exception:
                    pass

                layout.addLayout(row)
        except Exception:
            pass

        layout.addStretch()
        self.setLayout(layout)
        self.update_theme(self.color_preset)

    def update_species_compatibility(self, region_name):
        """Enable/disable species controls based on region compatibility."""
        # Try to use per-species min/max survival temps from config
        try:
            for sid, chk in self.species_checkboxes.items():
                cfg = (self.species_config or {}).get(sid, {})
                min_t = cfg.get("min_survival_temp", -100)
                max_t = cfg.get("max_survival_temp", 100)
                # Region compatibility will be handled by EnvironmentPanel which
                # calls update_species_compatibility_by_temp when appropriate.
                # Here we simply ensure checkboxes remain enabled.
                try:
                    chk.setEnabled(True)
                except Exception:
                    pass
        except Exception:
            pass

    def update_species_compatibility_by_temp(self, temperature):
        """Enable/disable species based on a temperature value."""
        try:
            for sid, chk in self.species_checkboxes.items():
                cfg = (self.species_config or {}).get(sid, {})
                min_t = cfg.get("min_survival_temp", -100)
                max_t = cfg.get("max_survival_temp", 100)
                can_survive = min_t <= temperature <= max_t
                try:
                    chk.setEnabled(can_survive)
                    # keep checked only if survivable
                    chk.setChecked(can_survive and chk.isChecked())
                except Exception:
                    pass
        except Exception:
            pass

    def update_language(self):
        try:
            if hasattr(self, "title"):
                self.title.setText(_("Spezies"))
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
        if species_id in self.member_value_labels:
            self.member_value_labels[species_id].setText(str(value))

    def get_enabled_species_populations(self):
        populations = {}
        for species_id, checkbox in self.species_checkboxes.items():
            if checkbox.isChecked():
                populations[species_id] = self.member_sliders.get(species_id, 1)
        return populations

    def update_theme(self, preset):
        self.color_preset = preset
        bg = preset.get_color("bg_primary") if preset else "#1a1a1a"
        self.setStyleSheet(f"background-color: {bg}; border: none;")
