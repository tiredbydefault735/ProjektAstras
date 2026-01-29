"""
SimulationScreen - Main simulation view with map and controls.
"""

from __future__ import annotations
import json
import logging
import copy
import sys
import math
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union, Callable

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
    QFrame,
    QStackedWidget,
    QSplitter,
    QMessageBox,
    QApplication,
    QPlainTextEdit,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

logger = logging.getLogger(__name__)

from backend.model import SimulationModel
from screens.simulation_map import SimulationMapWidget
from frontend.i18n import _
from config import (
    RIGHT_COLUMN_MIN_WIDTH,
    MAX_SIMULATION_TIME,
    MAP_MIN_WIDTH,
    MAP_MIN_HEIGHT,
    PANEL_STACK_MIN_HEIGHT,
    BUTTON_FIXED_WIDTH,
    UPDATE_TIMER_INTERVAL_MS,
    LOG_FONT_FAMILY,
    LOG_FONT_SIZE,
)

from .simulation_components.custom_widgets import CustomImageButton
from .simulation_components.stats_dialog import StatsDialog
from .simulation_components.log_dialog import LogDialog, LogHighlighter
from .simulation_components.species_panel import SpeciesPanel
from .simulation_components.environment_panel import EnvironmentPanel
from .simulation_components.live_graph_view import LiveGraphView
from .simulation_components.control_bar import ControlBar


class SimulationScreen(QWidget):
    """Main simulation screen view with map and controls.

    @ivar go_to_start: Callback to return to start screen
    @ivar color_preset: Active color preset
    @ivar is_running: Boolean flag indicating if simulation is active
    @ivar sim_model: The simulation backend model instance
    @ivar last_stats: Stores statistics from the last finished simulation
    """

    def set_auto_run_config(self, options: Dict[str, Any]) -> None:
        """Set configuration for automated run."""
        self.auto_options = options
        if self.auto_options.get("steps"):
            # Convert steps to seconds (0.1s per step)
            self.max_simulation_time = self.auto_options["steps"] * 0.1

    def show_final_stats(self, external_stats: Optional[Dict[str, Any]] = None) -> None:
        """Show final statistics dialog and save stats for later viewing.

        @param external_stats: Optional stats dictionary to use instead of querying sim_model (e.g. if model destroyed)
        """
        stats = None
        if external_stats:
            stats = external_stats
        elif self.sim_model:
            stats = self.sim_model.get_final_stats()

        if stats:
            # Fallbacks for empty stats
            if self.sim_model:
                try:
                    sc = stats.get("species_counts", {}) or {}
                    if sc and all(int(v) == 0 for v in sc.values()):
                        live_counts = {}
                        try:
                            for g in self.sim_model.groups:
                                live_counts[g.name] = sum(c.population for c in g.clans)
                            for l in getattr(self.sim_model, "loners", []):
                                live_counts[l.species] = (
                                    live_counts.get(l.species, 0) + 1
                                )
                        except Exception:
                            live_counts = sc
                        stats["species_counts"] = live_counts
                except Exception:
                    pass
            self.last_stats = stats  # Save stats for later

            # Handle automation output
            if self.auto_options and self.auto_options.get("output"):
                try:
                    out_path = Path(self.auto_options["output"])
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(stats, f, indent=2)
                    logger.info(f"Saved stats to {out_path}")
                except Exception:
                    logger.exception("Failed to save stats output")

                if self.auto_options.get("auto_quit"):
                    QApplication.quit()
                    return

            dialog = StatsDialog(stats, self)
            dialog.exec()

    def show_previous_stats(self) -> None:
        """Show stats from the previous simulation if available."""
        if hasattr(self, "last_stats") and self.last_stats:
            dialog = StatsDialog(self.last_stats, self)
            dialog.exec()
        else:
            QMessageBox.information(
                self,
                _("Keine Statistik"),
                _("Es sind keine Statistiken der vorherigen Simulation verfügbar."),
            )

    def __init__(
        self,
        go_to_start_callback: Callable[[], None],
        color_preset: Optional[Any] = None,
    ) -> None:
        """Initialize the simulation screen.

        @param go_to_start_callback: Function to call to return to start screen
        @param color_preset: Optional color preset to apply
        """
        super().__init__()
        self.go_to_start = go_to_start_callback
        self.color_preset = color_preset
        self.auto_options = {}  # Initialize to empty dict
        self.is_running = False

        self.sim_model = None
        self.update_timer = None
        self.animation_timer = None
        self.last_stats = None  # Holds stats from the previous simulation

        self.log_dialog = None
        self.time_step = 0
        self.simulation_time = 0  # Time in seconds
        self.max_simulation_time = MAX_SIMULATION_TIME  # seconds
        self.simulation_speed = 1  # Speed multiplier (1x, 2x, 5x)
        self.population_data = {}  # Store population history for live graph

        # Load species config
        json_path = get_static_path("data/species.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                self.species_config = json.load(f)
        except FileNotFoundError:
            self.species_config = {}
            logger.warning(f"Could not load species.json from {json_path}")

        self.init_ui()
        try:
            from frontend.i18n import register_language_listener

            register_language_listener(self.update_language)
        except Exception:
            pass

    def init_ui(self):
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Top bar: back button
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.btn_back = QPushButton(_("← Back"))
        btn_back_font = QFont("Minecraft", 12)
        btn_back_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_back.setFont(btn_back_font)
        self.btn_back.setFixedWidth(BUTTON_FIXED_WIDTH)
        self.btn_back.clicked.connect(self.on_back)
        top_bar.addWidget(self.btn_back)

        top_bar.addStretch()

        self.btn_exit = QPushButton(_("Exit"))
        btn_exit_font = QFont("Minecraft", 12)
        btn_exit_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_exit.setFont(btn_exit_font)
        self.btn_exit.setFixedWidth(BUTTON_FIXED_WIDTH)
        self.btn_exit.clicked.connect(self.on_exit)
        top_bar.addWidget(self.btn_exit)

        main_layout.addLayout(top_bar)

        # Content: Use QSplitter for 75/25 split with dynamic resizing
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setHandleWidth(5)

        # Left column: Map area (75%)
        left_column = QFrame()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.map_frame = QFrame()
        self.map_frame.setStyleSheet(
            "background-color: #ffffff; border: 2px solid #000000;"
        )
        map_layout = QVBoxLayout(self.map_frame)
        map_layout.setContentsMargins(0, 0, 0, 0)

        self.map_widget = SimulationMapWidget()
        self.map_widget.setMinimumSize(MAP_MIN_WIDTH, MAP_MIN_HEIGHT)
        map_layout.addWidget(self.map_widget)

        left_layout.addWidget(self.map_frame)
        content_splitter.addWidget(left_column)

        # Right column: Settings and controls (25%)
        right_column = QFrame()
        right_column.setMinimumWidth(RIGHT_COLUMN_MIN_WIDTH)
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
        self.panel_stack.setMinimumHeight(PANEL_STACK_MIN_HEIGHT)

        # Create panels
        self.species_panel = SpeciesPanel(self.species_config, self.color_preset)
        self.panel_stack.addWidget(self.species_panel)  # Index 0

        self.environment_panel = EnvironmentPanel(
            self.color_preset, self.map_widget, self.species_config, self.species_panel
        )
        self.panel_stack.addWidget(self.environment_panel)  # Index 1

        # Initialize species compatibility
        self.environment_panel.update_species_compatibility("Snowy Abyss")
        initial_temp = self.environment_panel.get_temperature()
        self.environment_panel.update_species_compatibility_by_temp(initial_temp)
        self.environment_panel.temp_slider.valueChanged.connect(
            self.on_live_temp_change
        )

        self.panel_stack.setCurrentIndex(1)
        right_layout.addWidget(self.panel_stack)

        # Render default food preview
        self.preview_startup()

        # Store log text
        self.log_text = _("Simulation bereit.")

        # Control section at bottom of right column
        right_layout.addSpacing(40)

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

        # New Control Bar
        self.control_bar = ControlBar()
        self.control_bar.playPauseClicked.connect(self.toggle_play_pause)
        self.control_bar.stopClicked.connect(self.stop_simulation)
        self.control_bar.speedChanged.connect(self.set_speed)
        self.control_bar.chaosClicked.connect(self.on_inject_chaos)
        right_layout.addWidget(self.control_bar)

        # Graph Container for Live Graph
        self.graph_container = QFrame()
        self.graph_container.setVisible(False)
        graph_layout = QVBoxLayout(self.graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)

        self.live_graph_view = LiveGraphView()
        graph_layout.addWidget(self.live_graph_view)

        # Log display under graph
        self.log_display = QPlainTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet(
            f"background-color: #222; color: #fff; font-family: {LOG_FONT_FAMILY}; font-size: {LOG_FONT_SIZE}px; margin-top: 6px; border: none;"
        )
        self.log_display.setMinimumHeight(100)
        LogHighlighter(self.log_display.document())
        graph_layout.addWidget(self.log_display)

        right_layout.addWidget(self.graph_container)
        right_layout.addStretch()

        content_splitter.addWidget(right_column)
        content_splitter.setSizes([7500, 2500])

        main_layout.addWidget(content_splitter)

        self.update_theme(self.color_preset)

    def preview_startup(self):
        try:
            if (
                hasattr(self, "environment_panel")
                and self.environment_panel is not None
            ):

                def _preview_startup():
                    try:
                        num = self.environment_panel.food_places_slider.value()
                        amt = (
                            self.environment_panel.food_amount_slider.value()
                            if hasattr(self.environment_panel, "food_amount_slider")
                            else 100
                        )
                        try:
                            # set pending seed so startup preview can be reused
                            # Use random number mixed with hash to ensure different previews on revisit
                            import random

                            random_modifier = random.randint(0, 999999)
                            self._pending_food_seed = (
                                hash((num, amt)) ^ random_modifier
                            ) & 0xFFFFFFFF
                            self.map_widget.preview_food_sources(
                                num, amt, amt, seed=self._pending_food_seed
                            )
                        except Exception:
                            pass
                    except Exception:
                        pass

                try:
                    QTimer.singleShot(120, _preview_startup)
                except Exception:
                    _preview_startup()
        except Exception:
            pass

    def switch_sidebar_tab(self, tab_name):
        """Switch between Species and Region tabs."""
        if tab_name == "species":
            self.btn_species_tab.setChecked(True)
            self.btn_region_tab.setChecked(False)
            self.panel_stack.setCurrentIndex(0)
        elif tab_name == "region":
            self.btn_species_tab.setChecked(False)
            self.btn_region_tab.setChecked(True)
            self.panel_stack.setCurrentIndex(1)

    def update_theme(self, preset):
        """Update inline styles."""
        self.color_preset = preset
        if not preset:
            return

        map_border = preset.get_color("map_border")
        self.map_frame.setStyleSheet(
            f"background-color: #ffffff; border: 2px solid {map_border};"
        )

        if hasattr(self, "species_panel"):
            self.species_panel.update_theme(preset)
        if hasattr(self, "environment_panel"):
            self.environment_panel.update_theme(preset)

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

    def toggle_simulation(self) -> None:
        """Start/resume simulation."""
        if not self.is_running:
            # Nur beim ersten Start initialisieren (wenn kein Model existiert)
            if self.sim_model is None:
                self.environment_panel.set_controls_enabled(False)

                # Initialize Simulation
                self.sim_model = SimulationModel()
                populations = self.species_panel.get_enabled_species_populations()
                food_places = self.environment_panel.get_food_places()
                food_amount = self.environment_panel.get_food_amount()
                start_temp = self.environment_panel.get_temperature()
                start_is_day = self.environment_panel.get_is_day()
                region_display = self.environment_panel.get_selected_region()

                # Override from auto_options if present
                if self.auto_options:
                    if self.auto_options.get("food_places") is not None:
                        food_places = self.auto_options["food_places"]
                    if self.auto_options.get("food_amount") is not None:
                        food_amount = self.auto_options["food_amount"]
                    if self.auto_options.get("temperature") is not None:
                        start_temp = self.auto_options["temperature"]
                    if self.auto_options.get("region"):
                        region_display = self.auto_options["region"]

                region_key = self.environment_panel.region_name_to_key.get(
                    region_display, "Wasteland"
                )
                if (
                    region_display not in self.environment_panel.region_name_to_key
                    and "_" in region_display
                ):
                    region_key = region_display

                # Override populations if auto-running
                if self.auto_options:
                    for s_name in self.species_config.keys():
                        if s_name not in populations:
                            populations[s_name] = 20

                adj_species_config = copy.deepcopy(self.species_config or {})
                try:
                    for sname, val in populations.items():
                        if sname in adj_species_config and isinstance(
                            adj_species_config[sname], dict
                        ):
                            adj_species_config[sname]["max_clan_members"] = int(val)
                except Exception:
                    pass

                seed_val = (
                    self.auto_options.get("seed")
                    if self.auto_options and self.auto_options.get("seed") is not None
                    else getattr(self, "_pending_food_seed", None)
                )

                self.sim_model.setup(
                    adj_species_config,
                    populations,
                    food_places,
                    food_amount,
                    start_temperature=start_temp,
                    start_is_day=start_is_day,
                    region_name=region_key,
                    initial_food_positions=getattr(
                        self.map_widget, "_last_preview_positions", None
                    ),
                    rng_seed=seed_val,
                )

                self.map_widget.set_region(region_display)

                # Initialize population data
                self.population_data = {}
                for species_name in populations.keys():
                    self.population_data[species_name] = []

                # UI Visibility
                self.btn_region_tab.setVisible(False)
                self.btn_species_tab.setVisible(False)
                self.panel_stack.setVisible(False)
                self.stats_log_widget.setVisible(False)
                self.control_bar.setVisible(True)
                self.graph_container.setVisible(True)

                # Reset graph
                self.live_graph_view.reset()

            # Resume
            self.is_running = True

            if self.auto_options and self.auto_options.get("speed"):
                self.set_speed(self.auto_options["speed"])

            self.control_bar.set_running_state(True)

            if not self.update_timer:
                self.update_timer = QTimer()
                self.update_timer.timeout.connect(self.update_simulation_with_speed)
            self.update_timer.start(UPDATE_TIMER_INTERVAL_MS)

    def toggle_play_pause(self) -> None:
        """Toggle between play and pause."""
        if self.is_running:
            if self.update_timer:
                self.update_timer.stop()
            self.is_running = False
            self.control_bar.set_running_state(False)
            self.control_bar.timer_label.setText(
                self.control_bar.timer_label.text() + " ⏸"
            )
        else:
            # currently paused, resume
            # remove pause symbol
            t = self.control_bar.timer_label.text().replace(" ⏸", "")
            self.control_bar.timer_label.setText(t)
            self.toggle_simulation()

    def stop_simulation(self) -> None:
        """Stop and reset simulation."""
        show_stats = self.is_running and self.sim_model

        self.environment_panel.set_controls_enabled(True)

        if self.update_timer:
            self.update_timer.stop()
            self.update_timer = None

        self.is_running = False
        self.control_bar.set_running_state(False)
        self.time_step = 0
        self.simulation_time = 0

        sim_model_for_stats = self.sim_model
        self.sim_model = None

        import random

        random_modifier = random.randint(0, 999999)
        if hasattr(self, "_pending_food_seed"):
            self._pending_food_seed = (
                self._pending_food_seed ^ random_modifier
            ) & 0xFFFFFFFF

        self.population_data = {}
        self.live_graph_view.reset()

        # UI Visibility
        self.btn_region_tab.setVisible(True)
        self.btn_species_tab.setVisible(True)
        self.panel_stack.setVisible(True)
        self.stats_log_widget.setVisible(True)
        self.control_bar.setVisible(True)
        self.graph_container.setVisible(False)

        if show_stats and sim_model_for_stats:
            stats = sim_model_for_stats.get_final_stats()
            self.last_stats = stats
            self.show_final_stats(external_stats=stats)

    def set_speed(self, speed: int) -> None:
        """Set simulation speed multiplier."""
        self.simulation_speed = speed
        self.control_bar.update_speed_buttons(speed)

    def on_live_temp_change(self, value):
        """Update simulation temperature in real-time."""
        if self.sim_model and self.is_running:
            self.sim_model.set_temperature(float(value))

    def on_inject_chaos(self):
        """Inject randomness."""
        if self.sim_model and self.is_running:
            self.sim_model.inject_chaos()

    def update_simulation_with_speed(self) -> None:
        for i in range(self.simulation_speed):
            is_last = i == self.simulation_speed - 1
            self.update_simulation(update_ui=is_last)

    def update_simulation(self, update_ui: bool = True) -> None:
        if self.sim_model and self.is_running:
            data = self.sim_model.step()
            stats = data.get("stats", {})
            self.map_widget.draw_groups(
                data["groups"],
                data.get("loners", []),
                data.get("food_sources", []),
                data.get("transition_progress", 1.0),
            )
            self.time_step = data["time"]
            self.simulation_time = self.time_step * 0.1

            if self.simulation_time >= self.max_simulation_time:
                self.add_log(
                    f"⏹️ Simulation endet nach {self.max_simulation_time} Sekunden."
                )
                self.stop_simulation()
                self.stop_simulation()

            # Extinction Check
            try:
                species_counts = stats.get("species_counts", {})
                total_pop = sum(species_counts.values()) if species_counts else 0
                if total_pop == 0:
                    self.add_log("⏹️ Simulation beendet — alle Spezies ausgestorben.")
                    self.stop_simulation()
                    return
            except Exception:
                pass

            # Update Data
            population_history = stats.get("population_history", {})
            if population_history:
                self.population_data = {
                    k: list(v) for k, v in population_history.items()
                }

            # Live Graph Update calling View
            self.live_graph_view.update_graph(
                self.population_data,
                self.species_panel.get_enabled_species_populations().keys(),
                stats.get("species_counts", {}),
                data.get("rnd_samples", {}),
            )

            # Logs
            logs = data.get("logs", [])
            if logs:
                parsed = []
                for l in logs:
                    parsed.append(self._format_log_entry(l))
                self.log_text += "\n" + "\n".join(parsed)
                # truncate
                parts = self.log_text.split("\n")
                if len(parts) > 1000:
                    self.log_text = "\n".join(parts[-1000:])

                # update log widgets
                if self.log_dialog and self.log_dialog.isVisible():
                    self.log_dialog.update_log(self.log_text)
                if self.log_display:
                    self.log_display.setPlainText(
                        "\n".join(self.log_text.split("\n")[-15:])
                    )

            if update_ui:
                # Update Control Bar Info
                self.control_bar.update_time(self.simulation_time)
                is_day = data.get("is_day", True)
                self.control_bar.update_day_night_icon(is_day)
                current_temp = stats.get("temperature", 0)
                self.control_bar.update_live_info(current_temp, is_day)

            if all(count == 0 for count in stats.get("species_counts", {}).values()):
                self.stop_simulation()

    def open_log_dialog(self):
        if self.log_dialog is None or not self.log_dialog.isVisible():
            self.log_dialog = LogDialog(self.log_text, self)
            self.log_dialog.show()
        else:
            self.log_dialog.raise_()
            self.log_dialog.activateWindow()

    def on_stats(self):
        self.show_previous_stats()

    def on_back(self):
        self.stop_simulation()
        self.go_to_start()

    def on_exit(self):
        self.stop_simulation()
        QApplication.quit()

    def add_log(self, text):
        if not text:
            return
        self.log_text += "\n" + str(text)
        parts = self.log_text.split("\n")
        if len(parts) > 1000:
            self.log_text = "\n".join(parts[-1000:])
        if self.log_display:
            self.log_display.setPlainText("\n".join(parts[-15:]))
        if self.log_dialog and self.log_dialog.isVisible():
            self.log_dialog.update_log(self.log_text)

    def _format_log_entry(self, entry):
        # Simplified handling
        try:
            if isinstance(entry, dict):
                t = entry.get("time")
                msgid = entry.get("msgid", "")
                params = entry.get("params", {}) or {}
                # safe format
                try:
                    from frontend.i18n import _

                    # Custom format logic if needed or just .format
                    text = _(msgid).format(**params)
                except:
                    text = str(msgid)
                if t is not None:
                    return f"[t={t}] {text}"
                return text
            return str(entry)
        except:
            return str(entry)

    def update_language(self):
        if hasattr(self, "btn_back"):
            self.btn_back.setText(_("← Back"))
        if hasattr(self, "btn_exit"):
            self.btn_exit.setText(_("Exit"))
        if hasattr(self, "btn_region_tab"):
            self.btn_region_tab.setText(_("Region"))
        if hasattr(self, "btn_species_tab"):
            self.btn_species_tab.setText(_("Spezies"))
        if hasattr(self, "btn_stats"):
            self.btn_stats.setText(_("Stats"))
        if hasattr(self, "btn_log"):
            self.btn_log.setText(_("Log"))

        if hasattr(self, "species_panel"):
            self.species_panel.update_language()
        if hasattr(self, "environment_panel"):
            self.environment_panel.update_language()
        if hasattr(self, "control_bar"):
            self.control_bar.update_language()
