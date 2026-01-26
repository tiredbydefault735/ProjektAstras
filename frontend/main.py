"""
ProjektAstras - PyQt6 Frontend
Main application entry point.
"""

from __future__ import annotations
import sys
import logging
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Any

# Add parent directory to path for backend imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFontDatabase, QCloseEvent

from screens.start_screen import StartScreen
from screens.simulation_screen import SimulationScreen
from screens.species_info_screen import SpeciesInfoScreen
from styles.stylesheet import get_stylesheet
from frontend.i18n import _, set_language
from config import WINDOW_START_X, WINDOW_START_Y, WINDOW_WIDTH, WINDOW_HEIGHT

if TYPE_CHECKING:
    from styles.color_presets import ColorPresetShim

logger = logging.getLogger(__name__)


class ArachfaraApp(QMainWindow):
    """Main application window with screen management."""

    def __init__(self, color_preset: Optional[ColorPresetShim] = None) -> None:
        super().__init__()
        self.setWindowTitle(_("PROJEKT ASTRAS"))
        self.setWindowIconText("Astras")

        # Set color preset (optional)
        self.color_preset = color_preset

        # Window size and position
        self.setGeometry(WINDOW_START_X, WINDOW_START_Y, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Start in fullscreen mode
        self.showFullScreen()

        # Central widget: stacked widget for screen management
        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)

        # Create screens with optional color preset
        self.start_screen = StartScreen(
            self.go_to_simulation, self.go_to_species_info, self.color_preset
        )
        self.simulation_screen = SimulationScreen(self.go_to_start, self.color_preset)
        self.species_info_screen = SpeciesInfoScreen(
            self.go_to_start, self.color_preset
        )

        # Register screens with i18n
        try:
            from frontend.i18n import register_language_listener

            if hasattr(self.start_screen, "update_language"):
                register_language_listener(self.start_screen.update_language)
            if hasattr(self.simulation_screen, "update_language"):
                register_language_listener(self.simulation_screen.update_language)
            if hasattr(self.species_info_screen, "update_language"):
                register_language_listener(self.species_info_screen.update_language)
        except Exception:
            pass

        # Add screens to stacked widget
        self.stacked.addWidget(self.start_screen)
        self.stacked.addWidget(self.simulation_screen)
        self.stacked.addWidget(self.species_info_screen)

        # Start with start screen
        self.stacked.setCurrentWidget(self.start_screen)

        # Ensure screens refresh their language when the visible screen changes
        try:
            self.stacked.currentChanged.connect(self._on_screen_changed)
        except Exception:
            pass

        # Apply stylesheet with current preset
        self.setStyleSheet(get_stylesheet(self.color_preset))
        # Register to update window title on language change
        try:
            from frontend.i18n import register_language_listener

            def _update_title() -> None:
                try:
                    # use module-level _ (imported at top) to translate
                    self.setWindowTitle(_("PROJEKT ASTRAS"))
                except Exception:
                    pass

            register_language_listener(_update_title)
        except Exception:
            pass

    def go_to_simulation(self) -> None:
        """Switch to simulation screen."""
        self.stacked.setCurrentWidget(self.simulation_screen)

    def go_to_species_info(self) -> None:
        """Switch to species info page."""
        self.stacked.setCurrentWidget(self.species_info_screen)

    def open_settings(self) -> None:
        """Settings screen removed; noop callback."""
        return

    # Theme application and settings UI removed.

    def go_to_start(self) -> None:
        """Switch to start screen."""
        self.stacked.setCurrentWidget(self.start_screen)
        # Ensure start button is visible again if it was hidden
        try:
            if (
                hasattr(self.start_screen, "btn_start")
                and self.start_screen.btn_start is not None
            ):
                self.start_screen.btn_start.setVisible(True)
        except Exception:
            pass

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close."""
        if self.simulation_screen.is_running:
            self.simulation_screen.stop_simulation()
        super().closeEvent(event)

    def _on_screen_changed(self, index: int) -> None:
        """Called when the stacked widget changes visible screen.

        Force a language refresh for the newly shown screen so translations
        appear immediately without user interaction.
        """
        try:
            widget = self.stacked.widget(index)
            if widget is None:
                return
            if hasattr(widget, "update_language"):
                try:
                    widget.update_language()
                except Exception:
                    pass
            # Also refresh known child panels on SimulationScreen for immediate update
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

    Args:
        preset_name: Optional color preset name. If not provided, uses DEFAULT_PRESET.
    """
    from styles.color_presets import get_preset_by_name
    from utils import get_static_path

    # Initialize language
    set_language("de")

    app = QApplication(sys.argv)

    # Set application icon (for taskbar)
    icon_path = get_static_path("src/logo_astras_pix.png")
    if icon_path.exists():
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)
        logger.info(f"Loaded application icon from {icon_path}")
    else:
        logger.warning("Warning: Application icon not found")

    # Load custom Minecraft font
    font_path = get_static_path("fonts/Minecraft.ttf")
    font_id = QFontDatabase.addApplicationFont(str(font_path))
    if font_id != -1:
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        logger.info(f"Loaded custom font: {font_families}")
    else:
        logger.warning("Failed to load Minecraft.ttf, using fallback fonts")

    # Get preset if specified
    preset = None
    if preset_name:
        preset = get_preset_by_name(preset_name)

    window = ArachfaraApp(color_preset=preset)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
