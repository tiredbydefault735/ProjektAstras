"""
SimulationScreen - Main simulation view with map and controls.
"""

# Log rendering constants
LOG_FONT_FAMILY = "Consolas"
LOG_FONT_SIZE = 12

import json
import sys
from pathlib import Path

# Add parent directory to path for backend imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import resource path utilities
from utils import get_static_path

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
    QDialog,
    QTextEdit,
    QPlainTextEdit,
    QSplitter,
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QSize,
    QRegularExpression,
)
import time
from PyQt6.QtGui import (
    QFont,
    QIcon,
    QPixmap,
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
)

from backend.model import SimulationModel
from .simulation_map import SimulationMapWidget
from frontend.i18n import _

# Import single-class modules
from .species_panel import SpeciesPanel
from .environment_panel import EnvironmentPanel
from .stats_dialog import StatsDialog
from .log_dialog import LogDialog
from .log_highlighter import LogHighlighter
from .custom_image_button import CustomImageButton
from .custom_checkbox import CustomCheckbox


class SimulationScreen(QWidget):
    def show_final_stats(self):
        """Show final statistics dialog and save stats for later viewing."""
        if self.sim_model:
            stats = self.sim_model.get_final_stats()
            self.last_stats = stats  # Save stats for later
            dialog = StatsDialog(stats, self)
            dialog.exec()

    def show_previous_stats(self):
        """Show stats from the previous simulation if available."""
        if hasattr(self, "last_stats") and self.last_stats:
            dialog = StatsDialog(self.last_stats, self)
            dialog.exec()
        else:
            from PyQt6.QtWidgets import QMessageBox

            try:
                QMessageBox.information(
                    self,
                    _("Keine Statistik"),
                    _("Es sind keine Statistiken der vorherigen Simulation verfügbar."),
                )
            except Exception:
                QMessageBox.information(
                    self,
                    "Keine Statistik",
                    "Es sind keine Statistiken der vorherigen Simulation verfügbar.",
                )

    """Main simulation screen."""

    def __init__(self, go_to_start_callback, color_preset=None):
        super().__init__()
        self.go_to_start = go_to_start_callback
        self.color_preset = color_preset
        self.is_running = False
        # Add missing speed value labels
        self.loner_speed_value_label = QLabel("1.0x")
        self.clan_speed_value_label = QLabel("1.0x")
        speed_value_font = QFont("Minecraft", 10)
        speed_value_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.loner_speed_value_label.setFont(speed_value_font)
        self.clan_speed_value_label.setFont(speed_value_font)
        self.sim_model = None
        self.update_timer = None
        self.animation_timer = None
        # Timer-driven simulation updates
        self.update_timer = None
        self.last_stats = None  # Holds stats from the previous simulation

        # Disaster UI removed
        self.disaster_label = None
        self.log_dialog = None
        self.time_step = 0
        self.log_expanded = False  # Track log expansion state
        self.simulation_time = 0  # Time in seconds
        self.max_simulation_time = 300  # 5 minutes = 300 seconds
        self.simulation_speed = 1  # Speed multiplier (1x, 2x, 5x)
        self.population_data = {}  # Store population history for live graph
        self.live_graph_widget = None  # Widget for live graph, initialized later
        # Live graph enabled by default
        self.enable_live_graph = True
        # UI throttling state
        self._last_ui_update_time = 0.0
        self._ui_frame_count = 0
        self._ui_target_fps = 12  # cap UI updates to 12 FPS
        self._ui_frame_skip_graph = 3  # update graph every 3 UI frames
        self._latest_step = None

        # Load species config
        json_path = get_static_path("data/species.json")
        # Debug logging removed: debug_log does not exist
        print(f"DEBUG: species.json path: {json_path}")
        print(f"DEBUG: species.json exists: {json_path.exists()}")
        try:
            with open(json_path, "r") as f:
                self.species_config = json.load(f)
        except FileNotFoundError:
            self.species_config = {}
            # Debug logging removed: debug_log does not exist
            print(f"Warning: Could not load species.json from {json_path}")

        # Don't initialize simulation model here - will be created on first start
        # self.sim_model is already set to None above

        self.init_ui()
        try:
            from frontend.i18n import register_language_listener

            register_language_listener(self.update_language)
        except Exception:
            pass

    def init_ui(self):
        """Initialize UI."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Top bar: back button
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        btn_back = QPushButton(_("← Back"))
        self.btn_back = btn_back
        btn_back_font = QFont("Minecraft", 12)
        btn_back_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        btn_back.setFont(btn_back_font)
        btn_back.setFixedWidth(100)
        btn_back.clicked.connect(self.on_back)
        top_bar.addWidget(btn_back)

        top_bar.addStretch()

        btn_exit = QPushButton(_("Exit"))
        self.btn_exit = btn_exit
        btn_exit_font = QFont("Minecraft", 12)
        btn_exit_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        btn_exit.setFont(btn_exit_font)
        btn_exit.setFixedWidth(100)
        btn_exit.clicked.connect(self.on_exit)
        top_bar.addWidget(btn_exit)

        main_layout.addLayout(top_bar)

        # Content: Use QSplitter for 75/25 split with dynamic resizing
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setHandleWidth(5)

        # Left column: Map area (75%)
        left_column = QFrame()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Disaster label removed

        self.map_frame = QFrame()
        self.map_frame.setStyleSheet(
            "background-color: #ffffff; border: 2px solid #000000;"
        )
        map_layout = QVBoxLayout(self.map_frame)
        map_layout.setContentsMargins(0, 0, 0, 0)

        self.map_widget = SimulationMapWidget()
        self.map_widget.setMinimumSize(600, 400)  # Minimum size for usability
        map_layout.addWidget(self.map_widget)

        left_layout.addWidget(self.map_frame)
        content_splitter.addWidget(left_column)

        # Right column: Settings and controls (25%)
        right_column = QFrame()
        right_column.setMinimumWidth(300)
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(10, 0, 0, 0)
        right_layout.setSpacing(10)

        # Tab buttons
        tab_buttons_layout = QHBoxLayout()
        tab_buttons_layout.setSpacing(5)

        self.btn_region_tab = QPushButton(_("Region"))
        region_tab_font = QFont("Minecraft", 12)
        region_tab_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_region_tab.setFont(region_tab_font)
        self.btn_region_tab.setCheckable(True)
        self.btn_region_tab.setChecked(True)
        self.btn_region_tab.setFixedHeight(35)
        self.btn_region_tab.clicked.connect(lambda: self.switch_sidebar_tab("region"))
        tab_buttons_layout.addWidget(self.btn_region_tab)

        self.btn_species_tab = QPushButton(_("Spezies"))
        species_tab_font = QFont("Minecraft", 12)
        species_tab_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_species_tab.setFont(species_tab_font)
        self.btn_species_tab.setCheckable(True)
        self.btn_species_tab.setChecked(False)
        self.btn_species_tab.setFixedHeight(35)
        self.btn_species_tab.clicked.connect(lambda: self.switch_sidebar_tab("species"))
        tab_buttons_layout.addWidget(self.btn_species_tab)

        right_layout.addLayout(tab_buttons_layout)

        # Use QStackedWidget to prevent layout shifts when switching tabs
        self.panel_stack = QStackedWidget()
        self.panel_stack.setMinimumHeight(400)

        # Create panels
        self.species_panel = SpeciesPanel(self.species_config, self.color_preset)
        self.panel_stack.addWidget(self.species_panel)  # Index 0

        self.environment_panel = EnvironmentPanel(
            self.color_preset, self.map_widget, self.species_config, self.species_panel
        )
        self.panel_stack.addWidget(self.environment_panel)  # Index 1

        # Initialize species compatibility for default region and temperature
        self.environment_panel.update_species_compatibility("Snowy Abyss")
        # Also check with initial temperature value
        initial_temp = self.environment_panel.get_temperature()
        self.environment_panel.update_species_compatibility_by_temp(initial_temp)

        # Show region/environment panel by default
        self.panel_stack.setCurrentIndex(1)

        right_layout.addWidget(self.panel_stack)

        # Store log text in variable instead of label (use module-level `_`)
        try:
            self.log_text = _("Simulation bereit.")
        except Exception:
            self.log_text = "Simulation bereit."

        # Control section at bottom of right column
        right_layout.addSpacing(20)

        # Stats and Log buttons (only shown before simulation starts)
        self.stats_log_widget = QWidget()
        stats_log_layout = QHBoxLayout(self.stats_log_widget)
        stats_log_layout.setContentsMargins(0, 0, 0, 0)
        stats_log_layout.setSpacing(10)

        self.btn_stats = QPushButton(_("Stats"))
        stats_font = QFont("Minecraft", 12)
        stats_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_stats.setFont(stats_font)
        self.btn_stats.setFixedHeight(40)
        self.btn_stats.clicked.connect(self.on_stats)
        stats_log_layout.addWidget(self.btn_stats)

        self.btn_log = QPushButton(_("Log"))
        log_btn_font = QFont("Minecraft", 12)
        log_btn_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_log.setFont(log_btn_font)
        self.btn_log.setFixedHeight(40)
        self.btn_log.clicked.connect(self.open_log_dialog)
        stats_log_layout.addWidget(self.btn_log)

        right_layout.addWidget(self.stats_log_widget)

        # Live graph area (shown during simulation)
        control_section = QWidget()
        control_layout = QVBoxLayout(control_section)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)
        # (All matplotlib axis configuration and plotting is handled in update_live_graph after the axis is created)
        # (spine styling for live_graph_ax is handled after creation in initialize_live_graph or update_live_graph)

        # (All grid configuration for live_graph_ax is handled after creation in initialize_live_graph or update_live_graph)

        # (Live graph widget and axis are initialized only when simulation starts)
        # (Do not reference self.live_graph_widget or self.live_graph_ax here)

        # Play/Pause and Stop Buttons
        play_controls_layout = QHBoxLayout()
        self.btn_play_pause = QPushButton("▶")
        play_font = QFont("Minecraft", 16)
        play_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_play_pause.setFont(play_font)
        self.btn_play_pause.setFixedHeight(40)
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        play_controls_layout.addWidget(self.btn_play_pause)

        self.btn_stop = QPushButton(_("Reset/Stop"))
        stop_font = QFont("Minecraft", 16)
        stop_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_stop.setFont(stop_font)
        self.btn_stop.setFixedHeight(40)
        self.btn_stop.clicked.connect(self.stop_simulation)
        play_controls_layout.addWidget(self.btn_stop)
        play_controls_layout.addStretch()
        control_layout.addLayout(play_controls_layout)

        # Info display row with timer, day/night, and speed controls
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)

        # Timer display
        self.timer_label = QLabel("00:00")
        timer_font = QFont("Minecraft", 14)
        timer_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.timer_label.setFont(timer_font)
        self.timer_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(self.timer_label)

        # Day/Night indicator
        self.day_night_label = QLabel("☀️")
        day_night_font = QFont("Minecraft", 16)
        day_night_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.day_night_label.setFont(day_night_font)
        self.day_night_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(self.day_night_label)

        # Speed control buttons next to time
        speed_label = QLabel("Sim Speed:")
        speed_label_font = QFont("Minecraft", 9)
        speed_label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        speed_label.setFont(speed_label_font)
        speed_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(speed_label)

        # Replace text speed buttons with image buttons from static/ui
        one_img = str(get_static_path("ui/one_times.png"))
        two_img = str(get_static_path("ui/two_times.png"))
        five_img = str(get_static_path("ui/five_times.png"))

        self.btn_speed_1x = CustomImageButton(one_img)
        self.btn_speed_1x.setChecked(True)
        self.btn_speed_1x.clicked.connect(lambda: self.set_speed(1))
        info_layout.addWidget(self.btn_speed_1x)

        self.btn_speed_2x = CustomImageButton(two_img)
        self.btn_speed_2x.clicked.connect(lambda: self.set_speed(2))
        info_layout.addWidget(self.btn_speed_2x)

        self.btn_speed_5x = CustomImageButton(five_img)
        self.btn_speed_5x.clicked.connect(lambda: self.set_speed(5))
        info_layout.addWidget(self.btn_speed_5x)

        info_layout.addStretch()
        control_layout.addLayout(info_layout)

        # Live info row
        live_info_layout = QHBoxLayout()
        live_info_layout.setSpacing(10)

        # Temperature display (live)
        self.live_temp_label = QLabel("🌡️ 0°C")
        live_temp_font = QFont("Minecraft", 11)
        live_temp_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.live_temp_label.setFont(live_temp_font)
        self.live_temp_label.setStyleSheet("color: #88ccff;")
        live_info_layout.addWidget(self.live_temp_label)

        # Day/Night indicator (live)
        self.live_day_night_label = QLabel(_("☀️ Tag"))
        live_dn_font = QFont("Minecraft", 11)
        live_dn_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.live_day_night_label.setFont(live_dn_font)
        self.live_day_night_label.setStyleSheet("color: #ffcc44;")
        live_info_layout.addWidget(self.live_day_night_label)
        live_info_layout.addStretch()
        control_layout.addLayout(live_info_layout)

        # Disaster severity UI removed.

        # Developer controls removed (Force Disaster)

        # Add control section to right column
        right_layout.addWidget(control_section)

        # Add graph container (for live graph)
        self.graph_container = QFrame()
        self.graph_container.setVisible(False)
        right_layout.addWidget(self.graph_container)

        right_layout.addStretch()

        # Add right column to splitter
        content_splitter.addWidget(right_column)

        # Set initial splitter sizes (75% / 25%)
        content_splitter.setSizes([7500, 2500])

        main_layout.addWidget(content_splitter)

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
                # Ignore theme update errors silently
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
        # Disaster severity slider removed; no per-slider styling required.

        # Force Disaster button removed; no styling required.

    def toggle_simulation(self):
        """Start/resume simulation."""
        if not self.is_running:
            # Nur beim ersten Start initialisieren (wenn kein Model existiert)
            if self.sim_model is None:
                # Deaktiviere Region-Auswahl
                self.environment_panel.set_controls_enabled(False)

                # Initialisiere Simulation
                self.sim_model = SimulationModel()
                populations = self.species_panel.get_enabled_species_populations()
                # If the species panel returns no enabled species (empty dict),
                # use a sensible default so the simulation doesn't stop immediately.
                # This can happen when the species UI hasn't been populated.
                if not populations:
                    populations = {}
                    for species_name, stats in (self.species_config or {}).items():
                        # Default to a small starting clan size (3) if not specified
                        populations[species_name] = max(
                            1, int(stats.get("max_clan_members", 3) / 2)
                        )
                food_places = self.environment_panel.get_food_places()
                food_amount = self.environment_panel.get_food_amount()
                start_temp = self.environment_panel.get_temperature()
                start_is_day = self.environment_panel.get_is_day()
                region_display = self.environment_panel.get_selected_region()
                # Map display name to region key for backend
                region_key = self.environment_panel.region_name_to_key.get(
                    region_display, "Wasteland"
                )
                self.sim_model.setup(
                    self.species_config,
                    populations,
                    food_places,
                    food_amount,
                    start_temp,
                    start_is_day,
                    region_key,
                )

                # Wire per-species speed sliders to the simulation model.
                # We compute the average of all species sliders and apply it
                # as a global multiplier in the refactored backend.
                def update_global_speeds():
                    try:
                        # For each species slider, compute per-species multiplier and
                        # apply it to the SimulationModel. Also compute averages
                        # for display in the global labels.
                        loner_vals = []
                        clan_vals = []
                        for sid, s in self.species_panel.loner_speed_sliders.items():
                            try:
                                m = s.value() / 5.0
                                loner_vals.append(m)
                                # update per-species UI label if present
                                try:
                                    lbl = (
                                        self.species_panel.loner_speed_value_labels.get(
                                            sid
                                        )
                                    )
                                    if lbl:
                                        lbl.setText(f"{m:.1f}x")
                                except Exception:
                                    pass
                                if self.sim_model:
                                    # call per-species setter if available
                                    try:
                                        self.sim_model.set_loner_speed_for_species(
                                            sid, m
                                        )
                                    except Exception:
                                        # fallback to global setter
                                        self.sim_model.set_loner_speed(m)
                            except Exception:
                                continue

                        for sid, s in self.species_panel.clan_speed_sliders.items():
                            try:
                                m = s.value() / 5.0
                                clan_vals.append(m)
                                # update per-species UI label if present
                                try:
                                    lbl = (
                                        self.species_panel.clan_speed_value_labels.get(
                                            sid
                                        )
                                    )
                                    if lbl:
                                        lbl.setText(f"{m:.1f}x")
                                except Exception:
                                    pass
                                if self.sim_model:
                                    try:
                                        self.sim_model.set_clan_speed_for_species(
                                            sid, m
                                        )
                                    except Exception:
                                        self.sim_model.set_clan_speed(m)
                            except Exception:
                                continue

                        avg_loner = (
                            sum(loner_vals) / len(loner_vals) if loner_vals else 1.0
                        )
                        avg_clan = sum(clan_vals) / len(clan_vals) if clan_vals else 1.0

                        # Update UI labels
                        try:
                            self.loner_speed_value_label.setText(f"{avg_loner:.1f}x")
                            self.clan_speed_value_label.setText(f"{avg_clan:.1f}x")
                        except Exception:
                            pass
                    except Exception:
                        pass

                # Connect signals (use current slider objects to avoid late-binding)
                for sid, slider in list(self.species_panel.loner_speed_sliders.items()):
                    try:
                        slider.valueChanged.connect(
                            lambda v, s=slider: update_global_speeds()
                        )
                    except Exception:
                        pass
                for sid, slider in list(self.species_panel.clan_speed_sliders.items()):
                    try:
                        slider.valueChanged.connect(
                            lambda v, s=slider: update_global_speeds()
                        )
                    except Exception:
                        pass

                # Set initial global speeds from current slider positions
                try:
                    update_global_speeds()
                except Exception:
                    pass

                # Initial disaster severity is managed by the backend; UI control removed.

                # Set region background (still use display name for UI)
                self.map_widget.set_region(region_display)

                # Initialize population data for live graph
                self.population_data = {}
                for species_name in populations.keys():
                    self.population_data[species_name] = []

                # Hide tabs and stats/log buttons, show graph
                self.btn_region_tab.setVisible(False)
                self.btn_species_tab.setVisible(False)
                self.panel_stack.setVisible(False)
                self.stats_log_widget.setVisible(False)
                self.graph_container.setVisible(True)

                # Initialize graph if not already created
                if self.live_graph_widget is None:
                    self.initialize_live_graph()

            # Resume (oder Start)
            self.is_running = True
            self.btn_play_pause.setText("⏸")
            # Start timer-based simulation loop
            self.start_simulation_timer()

    def toggle_play_pause(self):
        """Toggle between play and pause."""
        if self.is_running:
            # Currently running, so pause
            # stop timer-driven loop
            self.stop_simulation_timer()
            self.is_running = False
            self.btn_play_pause.setText("▶")
            self.btn_play_pause.setStyleSheet(
                "background-color: #4CAF50; color: white;"
            )
            self.timer_label.setText(self.timer_label.text() + " ⏸")
        else:
            # Currently paused or not started, so play/start
            self.btn_play_pause.setStyleSheet("")
            # Remove pause symbol from timer if present
            timer_text = self.timer_label.text().replace(" ⏸", "")
            self.timer_label.setText(timer_text)
            self.toggle_simulation()

    def stop_simulation(self):
        """Stop and reset simulation."""
        show_stats = self.is_running and self.sim_model

        self.environment_panel.set_controls_enabled(True)

        # stop timer-driven loop if running
        self.stop_simulation_timer()

        self.is_running = False
        self.btn_play_pause.setText("▶")
        self.btn_play_pause.setStyleSheet("")
        self.time_step = 0
        self.simulation_time = 0

        # Save model reference for stats before clearing
        sim_model_for_stats = self.sim_model

        # Reset Model to None so it will be recreated on next start
        self.sim_model = None

        # Clear population data for live graph
        self.population_data = {}
        if self.live_graph_widget:
            self.update_live_graph()

        # Show tabs and stats/log buttons, hide graph
        self.btn_region_tab.setVisible(True)
        self.btn_species_tab.setVisible(True)
        self.panel_stack.setVisible(True)
        self.stats_log_widget.setVisible(True)
        self.graph_container.setVisible(False)

        # Show stats popup after everything is stopped/reset
        if show_stats and sim_model_for_stats:
            stats = sim_model_for_stats.get_final_stats()
            self.last_stats = stats
            dialog = StatsDialog(stats, self)
            dialog.exec()

    def set_speed(self, speed):
        """Set simulation speed multiplier."""
        self.simulation_speed = speed

        # Update button checked states
        self.btn_speed_1x.setChecked(speed == 1)
        self.btn_speed_2x.setChecked(speed == 2)
        self.btn_speed_5x.setChecked(speed == 5)
        # Timer-driven updates use `update_simulation_with_speed` which
        # will run `simulation_speed` steps per timer tick; no worker here.

    def on_loner_speed_changed(self, value):
        """Handle loner speed slider change."""
        # Convert slider value (5-20) to multiplier (0.5-2.0)
        multiplier = value / 10.0
        self.loner_speed_value_label.setText(f"{multiplier:.1f}x")
        if self.sim_model:
            self.sim_model.set_loner_speed(multiplier)

    def on_clan_speed_changed(self, value):
        """Handle clan speed slider change."""
        # Convert slider value (5-20) to multiplier (0.5-2.0)
        multiplier = value / 10.0
        self.clan_speed_value_label.setText(f"{multiplier:.1f}x")
        if self.sim_model:
            self.sim_model.set_clan_speed(multiplier)

    # Developer helper for forcing disasters removed.

    def update_simulation_with_speed(self):
        """Update simulation multiple times based on speed setting."""
        for i in range(self.simulation_speed):
            is_last = i == self.simulation_speed - 1
            self.update_simulation(update_ui=is_last)

    def update_simulation(self, update_ui=True):
        """Step simulation und update display."""
        if self.sim_model and self.is_running:
            data = self.sim_model.step()
            # If backend indicates finished (max runtime reached), stop simulation
            try:
                if data.get("finished"):
                    # Let stop_simulation handle showing final stats
                    self.stop_simulation()
                    return
            except Exception:
                pass
            stats = data.get("stats", {})
            self.map_widget.draw_groups(
                data["groups"],
                data.get("loners", []),
                data.get("food_sources", []),
                data.get("transition_progress", 1.0),
            )
            self.time_step = data["time"]

            # Track simulation time (each step = 0.1 seconds)
            self.simulation_time = self.time_step * 0.1

            # --- Live graph and log update ---
            # Always use backend's population_history for up-to-date graph
            population_history = stats.get("population_history", {})
            if population_history:
                self.population_data = {
                    k: list(v) for k, v in population_history.items()
                }
            self.update_live_graph()

            # Update log text from backend logs (try to translate each line)
            logs = data.get("logs", [])
            if logs:
                try:
                    self.log_text = "\n".join([_(l) for l in logs])
                except Exception:
                    self.log_text = "\n".join(logs)
                if self.log_dialog is not None and self.log_dialog.isVisible():
                    self.log_dialog.update_log(self.log_text)

            if update_ui:
                # Update timer display
                minutes = int(self.simulation_time // 60)
                seconds = int(self.simulation_time % 60)
                # Timer display (MM:SS) - same in all languages
                self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

                # Update day/night indicator
                is_day = data.get("is_day", True)
                self.day_night_label.setText("☀️" if is_day else "🌙")

                # Update live temperature display
                current_temp = stats.get("temperature", 0)
                temp_color = (
                    "#88ccff"
                    if current_temp < 0
                    else "#ffcc44" if current_temp > 25 else "#ffffff"
                )
                try:
                    self.live_temp_label.setText(
                        _("Temp: {val}°C").format(val=current_temp)
                    )
                except Exception:
                    self.live_temp_label.setText(f"🌡️ {current_temp}°C")
                self.live_temp_label.setStyleSheet(
                    f"color: {temp_color}; padding: 0 10px;"
                )

                # Update live day/night display
                is_day = stats.get("is_day", True)
                if is_day:
                    self.live_day_night_label.setText("Tag")
                    self.live_day_night_label.setStyleSheet(
                        "color: #ffcc44; padding: 0 10px;"
                    )
                else:
                    self.live_day_night_label.setText("Nacht")
                    self.live_day_night_label.setStyleSheet(
                        "color: #8888ff; padding: 0 10px;"
                    )

                # Disaster visuals removed

            # --- Stop simulation if all arach are dead ---
            # Check if all populations are zero. Only stop when we actually have
            # species counts (avoid stopping immediately when counts dict is empty).
            species_counts = stats.get("species_counts", {})
            if species_counts and all(count == 0 for count in species_counts.values()):
                self.stop_simulation()

    # Timer-based simulation management (replaces threaded worker)
    def start_simulation_timer(self):
        """Start QTimer that runs simulation steps in the main thread.

        The timer calls `update_simulation_with_speed`, which runs
        `simulation_speed` steps per tick and updates the UI once.
        """
        if not self.sim_model:
            return
        timer = getattr(self, "update_timer", None)
        if timer is not None and timer.isActive():
            return
        self.update_timer = QTimer(self)
        # Base interval: 100ms per UI update; backend steps per tick scale with speed
        self.update_timer.setInterval(100)
        self.update_timer.timeout.connect(self.update_simulation_with_speed)
        self.update_timer.start()

    def stop_simulation_timer(self):
        """Stop the QTimer if running."""
        try:
            timer = getattr(self, "update_timer", None)
            if timer is not None and timer.isActive():
                timer.stop()
        except Exception:
            pass
        self.update_timer = None

    # Disaster flash removed

    def open_log_dialog(self):
        """Open log popup dialog."""
        if self.log_dialog is None or not self.log_dialog.isVisible():
            self.log_dialog = LogDialog(self.log_text, self)
            self.log_dialog.show()
        else:
            dlg = getattr(self, "log_dialog", None)
            if dlg is not None:
                try:
                    dlg.raise_()
                except Exception:
                    pass
                try:
                    dlg.activateWindow()
                except Exception:
                    pass

    def on_stats(self):
        """Show previous simulation statistics if available."""
        self.show_previous_stats()

    def initialize_live_graph(self):
        """Initialize the live graph widget."""
        # Skip initialization when live graph is disabled
        if not getattr(self, "enable_live_graph", False):
            return

        try:
            import matplotlib

            matplotlib.use("QtAgg")
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
            from matplotlib.figure import Figure

            # Create matplotlib figure
            fig = Figure(figsize=(5, 3), facecolor="#1a1a1a")
            self.live_graph_widget = FigureCanvasQTAgg(fig)
            self.live_graph_ax = fig.add_subplot(111)

            # Style the axes
            self.live_graph_ax.set_facecolor("#1a1a1a")
            self.live_graph_ax.tick_params(colors="#ffffff", labelsize=8)
            self.live_graph_ax.set_xlabel("Time (s)", color="#ffffff", fontsize=9)
            self.live_graph_ax.set_ylabel("Population", color="#ffffff", fontsize=9)
            self.live_graph_ax.set_title(
                "Live Population", color="#ffffff", fontsize=10
            )
            for spine in self.live_graph_ax.spines.values():
                spine.set_color("#666666")

            # Ensure graph_container has a layout

            if self.graph_container.layout() is None:
                self.graph_container.setLayout(QVBoxLayout())
            layout = self.graph_container.layout()

            if layout is not None:
                # Add the live graph widget
                layout.addWidget(self.live_graph_widget)

                # Create and add the legend label if it doesn't exist
                if (
                    not hasattr(self, "graph_legend_label")
                    or self.graph_legend_label is None
                ):
                    from PyQt6.QtWidgets import QLabel

                    self.graph_legend_label = QLabel()
                    self.graph_legend_label.setStyleSheet(
                        "color: #ffffff; font-size: 11px; padding: 4px 0 0 0;"
                    )
                    self.graph_legend_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(self.graph_legend_label)

                # Create and add the log display widget if it doesn't exist
                if not hasattr(self, "log_display") or self.log_display is None:
                    from PyQt6.QtWidgets import QPlainTextEdit

                    self.log_display = QPlainTextEdit()
                    self.log_display.setReadOnly(True)
                    # Use monospace and slightly larger font for readability
                    self.log_display.setStyleSheet(
                        f"background-color: #222; color: #fff; font-family: {LOG_FONT_FAMILY}; font-size: {LOG_FONT_SIZE}px; margin-top: 6px; border: none;"
                    )
                    self.log_display.setMinimumHeight(80)
                    LogHighlighter(self.log_display.document())
                    layout.addWidget(self.log_display)

            # Prepare line objects cache for efficient updates
            self._live_lines = {}
            self._live_last_xlim = (0, 1)
            self._live_last_ylim = (0, 1)
            # Update graph immediately
            self.update_live_graph()

        except ImportError:
            # Fallback if matplotlib is not available
            from PyQt6.QtWidgets import QLabel

            label = QLabel("Matplotlib nicht verfügbar")
            label.setStyleSheet("color: #ffffff; font-size: 12px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout = self.graph_container.layout()
            if layout is not None:
                layout.addWidget(label)

    def update_graph_legend(self):
        """Update the text legend below the graph."""
        colors = {
            "Icefang": "#cce6ff",
            "Crushed_Critters": "#cc9966",
            "Spores": "#66cc66",
            "The_Corrupted": "#cc66cc",
        }

        # Create colored text for each species
        legend_parts = []
        for species_name in sorted(self.population_data.keys()):
            color = colors.get(species_name, "#ffffff")
            # Replace underscores with spaces for display
            display_name = species_name.replace("_", " ")
            legend_parts.append(
                f'<span style="color: {color}; font-weight: bold;">{display_name}</span>'
            )

        if legend_parts:
            self.graph_legend_label.setText(" | ".join(legend_parts))
        else:
            self.graph_legend_label.setText("")

    def update_language(self):
        """Refresh UI texts when the global language changes."""
        try:
            # Main right-side tabs and controls
            if hasattr(self, "btn_region_tab"):
                self.btn_region_tab.setText(_("Region"))
            if hasattr(self, "btn_species_tab"):
                self.btn_species_tab.setText(_("Spezies"))
            if hasattr(self, "btn_stats"):
                self.btn_stats.setText(_("Stats"))
            if hasattr(self, "btn_log"):
                self.btn_log.setText(_("Log"))
            if hasattr(self, "btn_stop"):
                self.btn_stop.setText(_("Reset/Stop"))
            # Update top-bar navigation buttons
            if hasattr(self, "btn_back"):
                self.btn_back.setText(_("← Back"))
            if hasattr(self, "btn_exit"):
                self.btn_exit.setText(_("Exit"))

            # Day/night label: preserve icon and set localized text
            if hasattr(self, "live_day_night_label"):
                txt = self.live_day_night_label.text()
                if "☀️" in txt:
                    self.live_day_night_label.setText(_("☀️ Tag"))
                elif "🌙" in txt:
                    self.live_day_night_label.setText(_("🌙 Nacht"))

            # Notify nested panels
            if hasattr(self, "species_panel") and hasattr(
                self.species_panel, "update_language"
            ):
                try:
                    self.species_panel.update_language()
                except Exception:
                    pass
            if hasattr(self, "environment_panel") and hasattr(
                self.environment_panel, "update_language"
            ):
                try:
                    self.environment_panel.update_language()
                except Exception:
                    pass
        except Exception:
            pass

    def update_live_graph(self):
        """Update the live population graph with current data using matplotlib."""
        # Skip updating when live graph is disabled
        if not getattr(self, "enable_live_graph", False):
            return
        if self.live_graph_widget is None or not hasattr(self, "live_graph_ax"):
            return

        # Get species colors
        colors = {
            "Icefang": "#cce6ff",
            "Crushed_Critters": "#cc9966",
            "Spores": "#66cc66",
            "The_Corrupted": "#cc66cc",
        }

        # Only plot enabled (active) species
        enabled_species = set()
        if hasattr(self, "species_panel") and hasattr(
            self.species_panel, "get_enabled_species_populations"
        ):
            enabled_species = set(
                self.species_panel.get_enabled_species_populations().keys()
            )
        # Update or create Line2D objects instead of clearing the axes
        max_x = 0
        max_y = 1
        for species_name, history in self.population_data.items():
            if enabled_species and species_name not in enabled_species:
                # hide line if exists
                if species_name in self._live_lines:
                    line = self._live_lines[species_name]
                    line.set_visible(False)
                continue
            if not history:
                continue
            time_points = [i * 0.1 for i in range(len(history))]
            color = colors.get(species_name, "#ffffff")
            if species_name not in self._live_lines:
                # create a new line and add to cache
                (line,) = self.live_graph_ax.plot(
                    time_points,
                    history,
                    label=species_name.replace("_", " "),
                    color=color,
                )
                self._live_lines[species_name] = line
            else:
                line = self._live_lines[species_name]
                line.set_xdata(time_points)
                line.set_ydata(history)
                line.set_visible(True)

            if len(time_points) > max_x:
                max_x = len(time_points) * 0.1
            if max(history) > max_y:
                max_y = max(history)

        self.live_graph_ax.set_facecolor("#1a1a1a")
        self.live_graph_ax.tick_params(colors="#ffffff", labelsize=8)
        self.live_graph_ax.set_xlabel("Time (s)", color="#ffffff", fontsize=9)
        self.live_graph_ax.set_ylabel("Population", color="#ffffff", fontsize=9)
        self.live_graph_ax.set_title("Live Population", color="#ffffff", fontsize=10)
        for spine in self.live_graph_ax.spines.values():
            spine.set_color("#666666")

        # Only show legend if there is data
        if any(len(history) > 0 for history in self.population_data.values()):
            self.live_graph_ax.legend(
                loc="upper right", fontsize=8, facecolor="#1a1a1a", labelcolor="#ffffff"
            )

        # Adjust axes limits only when needed
        try:
            cur_xlim = self.live_graph_ax.get_xlim()
            cur_ylim = self.live_graph_ax.get_ylim()
        except Exception:
            cur_xlim = (0, 1)
            cur_ylim = (0, 1)

        new_xlim = (0, max(1, max_x))
        new_ylim = (0, max(1, max_y * 1.1))
        if new_xlim != cur_xlim:
            self.live_graph_ax.set_xlim(new_xlim)
        if new_ylim != cur_ylim:
            self.live_graph_ax.set_ylim(new_ylim)

        # Draw only the canvas (non-blocking where possible)
        try:
            self.live_graph_widget.draw_idle()
        except Exception:
            self.live_graph_widget.draw()
        self.update_graph_legend()

        # Update log display under the graph
        if hasattr(self, "log_display") and self.log_display is not None:
            # Show the last 15 log lines (adjust as needed)
            log_lines = self.log_text.split("\n")[-15:]
            # Use plain text; LogHighlighter handles coloring
            self.log_display.setPlainText("\n".join(log_lines))

    def on_back(self):
        """Go back to start screen."""
        self.stop_simulation()
        self.go_to_start()

    def on_exit(self):
        """Exit application."""
        from PyQt6.QtWidgets import QApplication

        self.stop_simulation()
        QApplication.quit()
