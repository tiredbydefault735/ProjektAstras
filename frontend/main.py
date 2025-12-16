"""
ProjektAstras - PyQt6 Frontend
Main application entry point.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for backend imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import resource path utilities
from utils import get_static_path

# Setup debug logging
# Nuitka onefile: __file__ points to temp dir with 'onefile_' in path
is_exe = 'onefile_' in str(Path(__file__).resolve()).lower()
if is_exe:
    # In EXE mode, write log next to executable
    log_file = Path(sys.argv[0]).parent / "debug.log"
else:
    # In dev mode, write to project root
    log_file = Path(__file__).parent.parent / "debug.log"

def debug_log(message):
    """Write debug message to log file and print to console"""
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")
        print(message)
    except Exception as e:
        print(f"Failed to write log: {e}")

# Clear old log
try:
    if log_file.exists():
        log_file.unlink()
except:
    pass

debug_log("=== ProjektAstras Debug Log ===")
debug_log(f"sys.frozen: {getattr(sys, 'frozen', False)}")
debug_log(f"sys.executable: {sys.executable}")
if hasattr(sys, '_MEIPASS'):
    debug_log(f"sys._MEIPASS: {sys._MEIPASS}")

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFontDatabase

from screens.start_screen import StartScreen
from screens.simulation_screen import SimulationScreen
from screens.settings_screen import SettingsScreen
from styles.stylesheet import get_stylesheet
from styles.color_presets import DEFAULT_PRESET


class ArachfaraApp(QMainWindow):
    """Main application window with screen management."""

    def __init__(self, color_preset=None):
        super().__init__()
        self.setWindowTitle("Projekt Astras")
        self.setWindowIconText("Astras")

        # Set color preset (default if not provided)
        self.color_preset = color_preset or DEFAULT_PRESET

        # Window size and position
        self.setGeometry(100, 100, 1400, 900)

        # Start in fullscreen mode
        self.showFullScreen()

        # Central widget: stacked widget for screen management
        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)

        # Create screens with color preset
        self.start_screen = StartScreen(
            self.go_to_simulation, self.open_settings, self.color_preset
        )
        self.simulation_screen = SimulationScreen(self.go_to_start, self.color_preset)
        self.settings_screen = SettingsScreen(
            self.apply_theme, self.go_to_start, self.color_preset
        )

        # Add screens to stacked widget
        self.stacked.addWidget(self.start_screen)
        self.stacked.addWidget(self.simulation_screen)
        self.stacked.addWidget(self.settings_screen)

        # Start with start screen
        self.stacked.setCurrentWidget(self.start_screen)

        # Apply stylesheet with current preset
        self.setStyleSheet(get_stylesheet(self.color_preset))

    def go_to_simulation(self):
        """Switch to simulation screen."""
        self.stacked.setCurrentWidget(self.simulation_screen)

    def open_settings(self):
        """Open settings screen."""
        self.stacked.setCurrentWidget(self.settings_screen)

    def apply_theme(self, preset_name):
        """Apply a theme by name at runtime and notify screens to refresh inline styles."""
        from styles.color_presets import get_preset_by_name

        preset = get_preset_by_name(preset_name)
        if not preset:
            return
        self.color_preset = preset
        # Apply global stylesheet
        self.setStyleSheet(get_stylesheet(self.color_preset))

        # Notify screens so they can update inline styles
        try:
            if hasattr(self.start_screen, "update_theme"):
                self.start_screen.update_theme(self.color_preset)
            if hasattr(self.simulation_screen, "update_theme"):
                self.simulation_screen.update_theme(self.color_preset)
            if hasattr(self.settings_screen, "update_theme"):
                self.settings_screen.update_theme(self.color_preset)
        except Exception:
            # Avoid crashing on theme application; stylesheet will still be applied globally
            pass

    def go_to_start(self):
        """Switch to start screen."""
        self.stacked.setCurrentWidget(self.start_screen)

    def closeEvent(self, event):
        """Handle window close."""
        if self.simulation_screen.is_running:
            self.simulation_screen.stop_simulation()
        super().closeEvent(event)


def main(preset_name=None):
    """
    Start the application.

    Args:
        preset_name: Optional color preset name. If not provided, uses DEFAULT_PRESET.
    """
    from styles.color_presets import get_preset_by_name

    app = QApplication(sys.argv)

    # Load custom Minecraft font using centralized resource path utility
    font_path = get_static_path("fonts/Minecraft.ttf")
    debug_log(f"Font path: {font_path}")
    debug_log(f"Font exists: {font_path.exists()}")
    if font_path.exists():
        debug_log("Font file found!")
    else:
        debug_log("ERROR: Font file NOT found!")
        # List what's actually in the directory
        try:
            parent = font_path.parent
            if parent.exists():
                debug_log(f"Contents of {parent}:")
                for item in parent.iterdir():
                    debug_log(f"  - {item.name}")
            else:
                debug_log(f"ERROR: Directory {parent} does not exist!")
        except Exception as e:
            debug_log(f"Error listing directory: {e}")
    font_id = QFontDatabase.addApplicationFont(str(font_path))
    if font_id != -1:
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        print(f"Loaded custom font: {font_families}")
    else:
        print("Failed to load Minecraft.ttf, using fallback fonts")

    # Get preset if specified
    preset = None
    if preset_name:
        preset = get_preset_by_name(preset_name)

    window = ArachfaraApp(color_preset=preset)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
