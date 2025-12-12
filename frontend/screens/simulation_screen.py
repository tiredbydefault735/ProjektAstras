"""
SimulationScreen - Main simulation view with map and controls.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for backend imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSlider,
    QFrame,
    QCheckBox,
    QStackedWidget,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from backend.model import SimulationModel
from screens.simulation_map import SimulationMapWidget


class SpeciesPanel(QWidget):
    """Species panel: subspecies controls."""

    def __init__(self, species_config, color_preset=None):
        super().__init__()
        self.color_preset = color_preset
        self.species_config = species_config
        self.species_checkboxes = {}
        self.species_sliders = {}
        self.member_sliders = {}

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # Title
        self.title = QLabel("Spezies")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title.setFont(title_font)
        layout.addWidget(self.title)

        self.subtitle = QLabel("Subspezies:")
        layout.addWidget(self.subtitle)

        # Create entry for each species
        species_names = {
            "Icefang": "Icefang",
            "Crushed_Critters": "Crushed Critters",
            "Spores": "Spores",
            "The_Corrupted": "The Corrupted",
        }

        for species_id, display_name in species_names.items():
            # Checkbox for enable/disable
            checkbox = QCheckBox(display_name)
            checkbox.setChecked(True)
            self.species_checkboxes[species_id] = checkbox
            layout.addWidget(checkbox)

            # Speed slider
            speed_layout = QHBoxLayout()
            speed_layout.setSpacing(5)

            speed_label = QLabel("Geschwi:")
            speed_layout.addWidget(speed_label)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(1)
            slider.setMaximum(10)
            slider.setValue(5)
            self.species_sliders[species_id] = slider
            speed_layout.addWidget(slider)

            layout.addLayout(speed_layout)

            # Member slider
            member_layout = QHBoxLayout()
            member_layout.setSpacing(5)

            member_label = QLabel("Mitglieder:")
            member_layout.addWidget(member_label)

            member_slider = QSlider(Qt.Orientation.Horizontal)
            member_slider.setMinimum(0)
            member_slider.setMaximum(20)
            member_slider.setValue(5)
            self.member_sliders[species_id] = member_slider
            member_layout.addWidget(member_slider)

            layout.addLayout(member_layout)

        layout.addStretch()
        self.setLayout(layout)
        self.update_theme(self.color_preset)

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

        # Panel background (no border for cleaner look)
        self.setStyleSheet(f"background-color: {bg}; border: none;")

        # Text elements
        self.title.setStyleSheet(f"color: {text}; background: transparent;")
        self.subtitle.setStyleSheet(
            f"color: {preset.get_color('text_secondary')}; background: transparent;"
        )

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
                    background-color: {preset.get_color('bg_tertiary')};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {accent};
                }}
            """
            )

        slider_style = f"""
            QSlider::groove:horizontal {{
                border: none;
                height: 6px;
                background: {preset.get_color('bg_tertiary')};
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                border: none;
                width: 16px;
                height: 16px;
                margin: -5px 0;
            }}
        """

        for slider in self.species_sliders.values():
            slider.setStyleSheet(slider_style)

        for slider in self.member_sliders.values():
            slider.setStyleSheet(slider_style)


class EnvironmentPanel(QWidget):
    """Region panel: environment controls."""

    def __init__(self, color_preset=None):
        super().__init__()
        self.color_preset = color_preset
        self.current_food_level = 5  # Default food level (1-10)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Title
        self.title = QLabel("Region")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title.setFont(title_font)
        layout.addWidget(self.title)

        # Region Selection
        self.region_label = QLabel("Region:")
        layout.addWidget(self.region_label)

        from PyQt6.QtWidgets import QComboBox

        self.region_combo = QComboBox()
        self.region_combo.addItems(
            ["Snowy_Abyss", "Wasteland", "Evergreen_Forest", "Corrupted_Caves"]
        )
        self.region_combo.setFixedHeight(30)
        layout.addWidget(self.region_combo)

        # Temperature Section
        self.temp_label = QLabel("Temperatur:")
        layout.addWidget(self.temp_label)

        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(-50)
        self.temp_slider.setMaximum(50)
        self.temp_slider.setValue(20)
        layout.addWidget(self.temp_slider)

        self.temp_value_label = QLabel("Temp: 20 C°")
        self.temp_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp_slider.valueChanged.connect(
            lambda v: self.temp_value_label.setText(f"Temp: {v} C°")
        )
        layout.addWidget(self.temp_value_label)

        # Food Section
        self.food_label_title = QLabel("Nahrung:")
        layout.addWidget(self.food_label_title)

        # Anzahl Nahrungsplätze
        self.food_places_label = QLabel("Nahrungsplätze: 5")
        layout.addWidget(self.food_places_label)

        self.food_places_slider = QSlider(Qt.Orientation.Horizontal)
        self.food_places_slider.setMinimum(1)
        self.food_places_slider.setMaximum(10)
        self.food_places_slider.setValue(5)
        self.food_places_slider.valueChanged.connect(
            lambda v: self.food_places_label.setText(f"Nahrungsplätze: {v}")
        )
        layout.addWidget(self.food_places_slider)

        # Nahrungsmenge pro Platz
        self.food_amount_label = QLabel("Nahrungsmenge: 50")
        layout.addWidget(self.food_amount_label)

        self.food_amount_slider = QSlider(Qt.Orientation.Horizontal)
        self.food_amount_slider.setMinimum(10)
        self.food_amount_slider.setMaximum(200)
        self.food_amount_slider.setValue(50)
        self.food_amount_slider.valueChanged.connect(
            lambda v: self.food_amount_label.setText(f"Nahrungsmenge: {v}")
        )
        layout.addWidget(self.food_amount_slider)

        # Day/Night Section
        self.day_night_label = QLabel("Tag - Nacht:")
        layout.addWidget(self.day_night_label)

        day_night_layout = QHBoxLayout()
        day_night_layout.setSpacing(5)

        day_btn = QPushButton("Tag")
        day_btn.setFixedHeight(30)
        day_btn.setCheckable(True)
        day_btn.setChecked(True)
        day_btn.clicked.connect(lambda: self.on_day_night_toggle(True))
        day_night_layout.addWidget(day_btn)

        night_btn = QPushButton("Nacht")
        night_btn.setFixedHeight(30)
        night_btn.setCheckable(True)
        night_btn.clicked.connect(lambda: self.on_day_night_toggle(False))
        day_night_layout.addWidget(night_btn)

        self.day_btn = day_btn
        self.night_btn = night_btn

        layout.addLayout(day_night_layout)

        layout.addStretch()

        self.setLayout(layout)
        self.update_theme(self.color_preset)

    def on_day_night_toggle(self, is_day):
        """Toggle between day and night mode."""
        if is_day:
            self.day_btn.setChecked(True)
            self.night_btn.setChecked(False)
        else:
            self.day_btn.setChecked(False)
            self.night_btn.setChecked(True)

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

        # Panel background (no border for cleaner look)
        self.setStyleSheet(f"background-color: {bg}; border: none;")

        # Text elements
        self.title.setStyleSheet(f"color: {text}; background: transparent;")
        self.region_label.setStyleSheet(
            f"color: {preset.get_color('text_secondary')}; background: transparent;"
        )
        self.temp_label.setStyleSheet(
            f"color: {preset.get_color('text_secondary')}; background: transparent;"
        )
        self.temp_value_label.setStyleSheet(f"color: {text}; background: transparent;")
        self.food_label_title.setStyleSheet(
            f"color: {preset.get_color('text_secondary')}; background: transparent;"
        )
        self.food_places_label.setStyleSheet(f"color: {text}; background: transparent;")
        self.food_amount_label.setStyleSheet(f"color: {text}; background: transparent;")
        self.day_night_label.setStyleSheet(
            f"color: {preset.get_color('text_secondary')}; background: transparent;"
        )

        # Style sliders (temp, food_places, food_amount)
        slider_style = f"""
            QSlider::groove:horizontal {{
                border: none;
                height: 6px;
                background: {bg_tertiary};
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                border: none;
                width: 16px;
                height: 16px;
                margin: -5px 0;
            }}
        """
        self.temp_slider.setStyleSheet(slider_style)
        self.food_places_slider.setStyleSheet(slider_style)
        self.food_amount_slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                border: none;
                height: 6px;
                background: {bg_tertiary};
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                border: none;
                width: 16px;
                height: 16px;
                margin: -5px 0;
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


class SimulationScreen(QWidget):
    """Main simulation screen."""

    def __init__(self, go_to_start_callback, color_preset=None):
        super().__init__()
        self.go_to_start = go_to_start_callback
        self.color_preset = color_preset
        self.is_running = False
        self.sim_model = None
        self.update_timer = None
        self.animation_timer = None
        self.time_step = 0

        # Load species config
        json_path = (
            Path(__file__).parent.parent.parent / "static" / "data" / "species.json"
        )
        try:
            with open(json_path, "r") as f:
                self.species_config = json.load(f)
        except FileNotFoundError:
            self.species_config = {}

        # Initialize simulation model
        self.sim_model = SimulationModel()
        # Initial populations will be set when simulation starts
        self.sim_model.setup(self.species_config, {}, food_places=5, food_amount=50)

        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Top bar: back button
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        btn_back = QPushButton("← Back")
        btn_back.setFixedWidth(100)
        btn_back.clicked.connect(self.on_back)
        top_bar.addWidget(btn_back)

        top_bar.addStretch()

        btn_exit = QPushButton("Exit")
        btn_exit.setFixedWidth(100)
        btn_exit.clicked.connect(self.on_exit)
        top_bar.addWidget(btn_exit)

        main_layout.addLayout(top_bar)

        # Content: map (left, large) and sidebar (right, compact)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        # Map area (left, main focus) - white background with fixed size
        self.map_frame = QFrame()
        self.map_frame.setFixedSize(1200, 600)  # Breiter für bessere Platznutzung
        self.map_frame.setStyleSheet(
            "background-color: #ffffff; border: 2px solid #000000;"
        )
        map_layout = QVBoxLayout(self.map_frame)
        map_layout.setContentsMargins(0, 0, 0, 0)

        self.map_widget = SimulationMapWidget()
        self.map_widget.setFixedSize(1200, 600)
        map_layout.addWidget(self.map_widget)

        content_layout.addWidget(self.map_frame)

        # Sidebar: Tab buttons and panels
        sidebar_frame = QFrame()
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(10)

        # Tab buttons
        tab_buttons_layout = QHBoxLayout()
        tab_buttons_layout.setSpacing(5)

        self.btn_species_tab = QPushButton("Spezies")
        self.btn_species_tab.setCheckable(True)
        self.btn_species_tab.setChecked(True)
        self.btn_species_tab.setFixedHeight(35)
        self.btn_species_tab.clicked.connect(lambda: self.switch_sidebar_tab("species"))
        tab_buttons_layout.addWidget(self.btn_species_tab)

        self.btn_region_tab = QPushButton("Region")
        self.btn_region_tab.setCheckable(True)
        self.btn_region_tab.setChecked(False)
        self.btn_region_tab.setFixedHeight(35)
        self.btn_region_tab.clicked.connect(lambda: self.switch_sidebar_tab("region"))
        tab_buttons_layout.addWidget(self.btn_region_tab)

        sidebar_layout.addLayout(tab_buttons_layout)

        # Use QStackedWidget to prevent layout shifts when switching tabs
        self.panel_stack = QStackedWidget()
        self.panel_stack.setFixedSize(250, 550)

        # Create panels
        self.species_panel = SpeciesPanel(self.species_config, self.color_preset)
        self.panel_stack.addWidget(self.species_panel)  # Index 0

        self.environment_panel = EnvironmentPanel(self.color_preset)
        self.panel_stack.addWidget(self.environment_panel)  # Index 1

        # Show species panel by default
        self.panel_stack.setCurrentIndex(0)

        sidebar_layout.addWidget(self.panel_stack)
        sidebar_layout.addStretch()

        content_layout.addWidget(sidebar_frame)

        main_layout.addLayout(content_layout)

        # Log area (bottom, full width, persistent)
        self.log_frame = QFrame()
        self.log_frame.setFixedHeight(120)
        self.log_frame.setStyleSheet(
            "background-color: #1a1a1a; border: 2px solid #666666;"
        )
        log_layout = QVBoxLayout(self.log_frame)
        log_layout.setContentsMargins(5, 5, 5, 5)

        log_title = QLabel("Logs:")
        log_title.setStyleSheet("color: #ffffff; font-weight: bold;")
        log_layout.addWidget(log_title)

        self.log_label = QLabel("Simulation bereit.")
        self.log_label.setStyleSheet(
            "color: #33ff33; font-family: monospace; font-size: 9px;"
        )
        self.log_label.setWordWrap(True)
        self.log_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        log_layout.addWidget(self.log_label)

        main_layout.addWidget(self.log_frame)

        # Bottom control bar
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedWidth(50)
        self.btn_play.setFixedHeight(40)
        self.btn_play.clicked.connect(self.toggle_simulation)
        control_layout.addWidget(self.btn_play)

        self.btn_pause = QPushButton("||")
        self.btn_pause.setFixedWidth(50)
        self.btn_pause.setFixedHeight(40)
        self.btn_pause.clicked.connect(self.pause_simulation)
        control_layout.addWidget(self.btn_pause)

        self.btn_stop = QPushButton("⏹")
        self.btn_stop.setFixedWidth(50)
        self.btn_stop.setFixedHeight(40)
        self.btn_stop.clicked.connect(self.stop_simulation)
        control_layout.addWidget(self.btn_stop)

        control_layout.addStretch()

        self.btn_stats = QPushButton("Stats")
        self.btn_stats.setFixedWidth(100)
        self.btn_stats.setFixedHeight(40)
        self.btn_stats.clicked.connect(self.on_stats)
        control_layout.addWidget(self.btn_stats)

        main_layout.addLayout(control_layout)

        self.setLayout(main_layout)
        # Apply initial theme to inline-styled widgets
        self.update_theme(self.color_preset)

    def switch_sidebar_tab(self, tab_name):
        """Switch between Species and Region tabs."""
        if tab_name == "species":
            self.btn_species_tab.setChecked(True)
            self.btn_region_tab.setChecked(False)
            self.panel_stack.setCurrentIndex(0)  # Show species panel
        elif tab_name == "region":
            self.btn_species_tab.setChecked(False)
            self.btn_region_tab.setChecked(True)
            self.panel_stack.setCurrentIndex(1)  # Show region panel

        # Ensure log frame stays visible
        if hasattr(self, "log_frame"):
            self.log_frame.setVisible(True)
            self.log_frame.raise_()

    def update_theme(self, preset):
        """Update inline styles for the simulation screen and child panels."""
        self.color_preset = preset
        if not preset:
            return

        # Map frame: keep map background white but update border color
        map_border = preset.get_color("map_border")
        self.map_frame.setStyleSheet(
            f"background-color: #ffffff; border: 2px solid {map_border};"
        )

        # Species panel updates itself
        if hasattr(self, "species_panel") and self.species_panel:
            try:
                self.species_panel.update_theme(preset)
            except Exception:
                pass

        # Environment panel updates itself
        if hasattr(self, "environment_panel") and self.environment_panel:
            try:
                self.environment_panel.update_theme(preset)
            except Exception:
                pass

        # Style tab buttons
        if hasattr(self, "btn_species_tab") and hasattr(self, "btn_region_tab"):
            text = preset.get_color("text_primary")
            bg_tertiary = preset.get_color("bg_tertiary")
            accent = preset.get_color("accent_primary")

            tab_button_style = f"""
                QPushButton {{
                    background-color: {bg_tertiary};
                    color: {text};
                    border: none;
                    padding: 8px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {accent};
                }}
                QPushButton:checked {{
                    background-color: {accent};
                }}
            """
            self.btn_species_tab.setStyleSheet(tab_button_style)
            self.btn_region_tab.setStyleSheet(tab_button_style)

        # Logs/frame colors
        log_bg = preset.get_color("bg_tertiary")
        log_border = preset.get_color("border_light")
        log_text = preset.get_color("log_text")
        self.log_frame.setStyleSheet(
            f"background-color: {log_bg}; border: 2px solid {log_border};"
        )
        self.log_label.setStyleSheet(
            f"color: {log_text}; font-family: monospace; font-size: 9px;"
        )

    def toggle_simulation(self):
        """Start/resume simulation."""
        if not self.is_running:
            # Deaktiviere Region-Auswahl
            self.environment_panel.set_controls_enabled(False)

            # Initialisiere Simulation
            self.sim_model = SimulationModel()
            populations = self.species_panel.get_enabled_species_populations()
            food_places = self.environment_panel.get_food_places()
            food_amount = self.environment_panel.get_food_amount()
            self.sim_model.setup(
                self.species_config, populations, food_places, food_amount
            )

            self.is_running = True
            self.btn_play.setText("⏸")

            # Start Update-Timer (100ms = 10 steps/sec)
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_simulation)
            self.update_timer.start(100)

    def pause_simulation(self):
        """Pause simulation."""
        if self.is_running:
            if self.update_timer:
                self.update_timer.stop()
            self.is_running = False
            self.btn_play.setText("▶")

    def stop_simulation(self):
        """Stop and reset simulation."""
        self.environment_panel.set_controls_enabled(True)

        if self.update_timer:
            self.update_timer.stop()
            self.update_timer = None

        self.is_running = False
        self.btn_play.setText("▶")
        self.time_step = 0

        # Reset Model
        self.sim_model = SimulationModel()
        self.sim_model.setup(self.species_config, {}, food_places=5, food_amount=50)

        self.log_label.setText("Simulation bereit.")
        self.map_widget.clear_map()

    def update_simulation(self):
        """Step simulation und update display."""
        if self.sim_model:
            data = self.sim_model.step()
            self.map_widget.draw_groups(
                data["groups"], data.get("loners", []), data.get("food_sources", [])
            )
            self.time_step = data["time"]

            # Update logs
            logs = data.get("logs", [])
            if logs:
                log_text = "\n".join(logs[-10:])
                self.log_label.setText(log_text)

    def on_stats(self):
        """Show statistics (placeholder)."""
        # Get current logs and append stats
        current_logs = self.log_label.text()
        stats_info = f"\n[STATS] Zeit: {self.time_step}"
        if current_logs:
            self.log_label.setText(current_logs + stats_info)
        else:
            self.log_label.setText(stats_info)

    def on_back(self):
        """Go back to start screen."""
        self.stop_simulation()
        self.go_to_start()

    def on_exit(self):
        """Exit application."""
        from PyQt6.QtWidgets import QApplication

        self.stop_simulation()
        QApplication.quit()
