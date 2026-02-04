"""
ProjektAstras - PyQt6 Frontend
Main application entry point.
"""

from __future__ import annotations
import sys

sys.dont_write_bytecode = True

import logging
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFontDatabase, QCloseEvent

from screens.start_screen import StartScreen
from screens.simulation_screen import SimulationScreen
from styles.stylesheet import get_stylesheet
from frontend.i18n import _, set_language
from config import WINDOW_START_X, WINDOW_START_Y, WINDOW_WIDTH, WINDOW_HEIGHT

if TYPE_CHECKING:
    from styles.color_presets import ColorPresetShim

logger = logging.getLogger(__name__)


class ArachfaraApp(QMainWindow):
    """Main application window with screen management.

    @ivar color_preset: The active color preset for the UI
    @ivar stacked: The QStackedWidget holding different screens
    @ivar start_screen: Instance of the start screen
    @ivar simulation_screen: Instance of the simulation screen

    """

    def __init__(
        self,
        color_preset: Optional[ColorPresetShim] = None,
        auto_options: Optional[dict] = None,
    ) -> None:
        """Initialize the main application window.

        @param color_preset: Optional color preset to apply
        @param auto_options: Dictionary with automation options (auto_run, auto_quit, etc.)
        """
        super().__init__()
        self.setWindowTitle(_("PROJEKT ASTRAS"))
        self.setWindowIconText("Astras")

        self.color_preset = color_preset
        self.auto_options = auto_options or {}

        self.setGeometry(WINDOW_START_X, WINDOW_START_Y, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.showFullScreen()

        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)

        self.start_screen = StartScreen(self.go_to_simulation, self.color_preset)
        self.simulation_screen = SimulationScreen(self.go_to_start, self.color_preset)

        if self.auto_options.get("auto_run"):
            if hasattr(self.simulation_screen, "set_auto_run_config"):
                self.simulation_screen.set_auto_run_config(self.auto_options)

            from PyQt6.QtCore import QTimer

            QTimer.singleShot(500, self.go_to_simulation)
            QTimer.singleShot(
                1000,
                lambda: (
                    self.simulation_screen.toggle_simulation()
                    if not self.simulation_screen.is_running
                    else None
                ),
            )

        try:
            from frontend.i18n import register_language_listener

            if hasattr(self.start_screen, "update_language"):
                register_language_listener(self.start_screen.update_language)
            if hasattr(self.simulation_screen, "update_language"):
                register_language_listener(self.simulation_screen.update_language)
        except Exception:
            logger.exception("Failed to register language listeners")
            pass

        self.stacked.addWidget(self.start_screen)
        self.stacked.addWidget(self.simulation_screen)

        self.stacked.setCurrentWidget(self.start_screen)

        try:
            self.stacked.currentChanged.connect(self._on_screen_changed)
        except Exception:
            logger.exception("Failed to connect currentChanged")
            pass

        self.setStyleSheet(get_stylesheet(self.color_preset))
        try:
            from frontend.i18n import register_language_listener

            def _update_title() -> None:
                try:
                    self.setWindowTitle(_("PROJEKT ASTRAS"))
                except Exception:
                    logger.exception("Error updating window title")
                    pass

            register_language_listener(_update_title)
        except Exception:
            logger.exception("Failed to register title update listener")
            pass

    def go_to_simulation(self) -> None:
        """Switch to simulation screen."""
        self.stacked.setCurrentWidget(self.simulation_screen)

    def open_settings(self) -> None:
        """Settings screen removed; noop callback."""
        return

    def go_to_start(self) -> None:
        """Switch to start screen."""
        self.stacked.setCurrentWidget(self.start_screen)
        try:
            if (
                hasattr(self.start_screen, "btn_start")
                and self.start_screen.btn_start is not None
            ):
                self.start_screen.btn_start.setVisible(True)
        except Exception:
            pass

    def closeEvent(self, a0: Optional[QCloseEvent]) -> None:
        """Handle window close event.

        Stops the simulation if it is running.

        @param a0: The close event
        """
        if self.simulation_screen.is_running:
            self.simulation_screen.stop_simulation()
        super().closeEvent(a0)

    def _on_screen_changed(self, index: int) -> None:
        """Called when the stacked widget changes visible screen.

        Force a language refresh for the newly shown screen so translations
        appear immediately without user interaction.

        @param index: The index of the new current widget
        """
        try:
            widget = self.stacked.widget(index)
            if widget is None:
                return
            if hasattr(widget, "update_language"):
                try:
                    getattr(widget, "update_language")()
                except Exception:
                    pass
            try:
                if isinstance(widget, SimulationScreen):
                    try:
                        if hasattr(widget, "species_panel") and hasattr(
                            widget.species_panel, "update_language"
                        ):
                            widget.species_panel.update_language()
                    except Exception:
                        pass
                    try:
                        if hasattr(widget, "environment_panel") and hasattr(
                            widget.environment_panel, "update_language"
                        ):
                            widget.environment_panel.update_language()
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass


def main(preset_name: Optional[str] = None) -> None:
    """
    Start the application.

    @param preset_name: Optional color preset name. If not provided, uses DEFAULT_PRESET.
    """
    import argparse
    from styles.color_presets import get_preset_by_name
    from utils import get_static_path

    parser = argparse.ArgumentParser(description="Run Arachfara Frontend")
    parser.add_argument("--preset", type=str, help="Color preset name")
    parser.add_argument("--auto-run", action="store_true", help="Auto-start simulation")
    parser.add_argument(
        "--auto-quit", action="store_true", help="Quit after simulation"
    )
    parser.add_argument("--steps", type=int, default=3000, help="Max simulation steps")
    parser.add_argument("--output", type=str, help="Path for stats output JSON")
    parser.add_argument("--seed", type=int, help="RNG seed")
    parser.add_argument("--region", type=str, help="Region name")
    parser.add_argument("--temperature", type=float, help="Starting temperature")
    parser.add_argument("--food-places", type=int, help="Number of food places")
    parser.add_argument("--food-amount", type=float, help="Amount of food per place")
    parser.add_argument("--speed", type=int, help="Simulation speed multiplier")

    args, _ = parser.parse_known_args()

    preset_name = getattr(args, "preset", preset_name)

    auto_options = {
        "auto_run": args.auto_run,
        "auto_quit": args.auto_quit,
        "steps": args.steps,
        "output": args.output,
        "seed": args.seed,
        "region": args.region,
        "temperature": args.temperature,
        "food_places": args.food_places,
        "food_amount": args.food_amount,
        "speed": args.speed,
    }

    set_language("de")

    app = QApplication(sys.argv)

    icon_path = get_static_path("src/logo_astras_pix.png")
    if icon_path.exists():
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)
        logger.info(f"Loaded application icon from {icon_path}")
    else:
        logger.warning("Warning: Application icon not found")

    font_path = get_static_path("fonts/Minecraft.ttf")
    font_id = QFontDatabase.addApplicationFont(str(font_path))
    if font_id != -1:
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        logger.info(f"Loaded custom font: {font_families}")
    else:
        logger.warning("Failed to load Minecraft.ttf, using fallback fonts")

    preset = None
    if preset_name:
        preset = get_preset_by_name(preset_name)

    window = ArachfaraApp(color_preset=preset, auto_options=auto_options)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
