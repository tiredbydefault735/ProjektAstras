"""
StartScreen - First screen with logo and buttons.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
)
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtCore import Qt
from utils import get_static_path


class StartScreen(QWidget):
    """Start/intro screen with logo and navigation buttons."""

    def __init__(
        self, go_to_simulation_callback, go_to_settings_callback, color_preset=None
    ):
        super().__init__()
        self.go_to_simulation = go_to_simulation_callback
        self.go_to_settings = go_to_settings_callback
        self.color_preset = color_preset
        self.center_container = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 80)
        main_layout.setSpacing(0)

        # Get background color from preset if available
        bg_color = (
            self.color_preset.get_color("bg_secondary")
            if self.color_preset
            else "#2a2a2a"
        )

        # Center container
        self.center_container = QFrame()
        self.center_container.setFixedSize(900, 420)
        self.center_container.setStyleSheet(
            f"background-color: {bg_color}; border: none;"
        )

        container_layout = QHBoxLayout(self.center_container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(12)

        # Left: Logo
        logo_frame = QFrame()
        logo_frame.setFixedSize(360, 360)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 0, 0, 0)

        logo_label = QLabel()
        logo_path = get_static_path("src/logo_astras_pix.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            scaled_pixmap = pixmap.scaledToWidth(
                360, Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            logo_label.setText("NO LOGO")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_label.setStyleSheet("color: #cc0000;")

        logo_layout.addWidget(logo_label)
        container_layout.addWidget(logo_frame)

        # Right: Buttons
        button_frame = QFrame()
        button_frame.setFixedSize(420, 340)
        button_layout = QVBoxLayout(button_frame)
        button_layout.setContentsMargins(8, 8, 8, 8)
        button_layout.setSpacing(12)

        # Title
        title = QLabel("PROJEKT ASTRAS")
        title_font = QFont("Minecraft", 24, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ffffff; background-color: transparent;")
        button_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Simulation v1.0")
        subtitle_font = QFont("Minecraft", 14)
        subtitle_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #cccccc; background-color: transparent;")
        button_layout.addWidget(subtitle)

        # Stretch
        button_layout.addStretch()

        # Buttons
        btn_start = QPushButton("Start Simulation")
        btn_start_font = QFont("Minecraft", 13)
        btn_start_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        btn_start.setFont(btn_start_font)
        btn_start.setFixedHeight(50)
        btn_start.clicked.connect(self.go_to_simulation)
        button_layout.addWidget(btn_start)

        btn_settings = QPushButton("Settings")
        btn_settings_font = QFont("Minecraft", 13)
        btn_settings_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        btn_settings.setFont(btn_settings_font)
        btn_settings.setFixedHeight(50)
        btn_settings.clicked.connect(self.on_settings)
        button_layout.addWidget(btn_settings)

        btn_exit = QPushButton("Exit")
        btn_exit_font = QFont("Minecraft", 13)
        btn_exit_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        btn_exit.setFont(btn_exit_font)
        btn_exit.setFixedHeight(50)
        btn_exit.clicked.connect(self.on_exit)
        button_layout.addWidget(btn_exit)

        container_layout.addWidget(button_frame)

        # Add center container to main layout with center alignment
        wrapper = QVBoxLayout()
        wrapper.addStretch()
        wrapper.addWidget(self.center_container, alignment=Qt.AlignmentFlag.AlignCenter)
        wrapper.addStretch()

        main_layout.addLayout(wrapper)

        self.setLayout(main_layout)

    def on_settings(self):
        """Settings button clicked."""
        if self.go_to_settings:
            self.go_to_settings()

    def on_exit(self):
        """Exit button clicked."""
        from PyQt6.QtWidgets import QApplication

        QApplication.quit()

    def update_theme(self, preset):
        """Update inline styles used by the Start screen."""
        self.color_preset = preset
        bg_color = preset.get_color("bg_secondary") if preset else "#2a2a2a"
        # Update center container background
        if self.center_container is not None:
            self.center_container.setStyleSheet(
                f"background-color: {bg_color}; border: none;"
            )
