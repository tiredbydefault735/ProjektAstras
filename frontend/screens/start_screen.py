"""
StartScreen - First screen with logo and buttons.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QGraphicsOpacityEffect,
)
from PyQt6.QtGui import QPixmap, QFont, QColor, QMovie
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
        # Animated background - fill entire widget
        self.bg_label = QLabel(self)
        self.bg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        gif_path = get_static_path("ui/astras.gif")
        if gif_path.exists():
            self.movie = QMovie(str(gif_path))
            self.bg_label.setMovie(self.movie)
            self.movie.start()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 80)
        main_layout.setSpacing(0)

        # Get background color from preset if available (with transparency built-in)
        bg_color = (
            self.color_preset.get_color("bg_secondary")
            if self.color_preset
            else "#2a2a2a"
        )

        # Very slight reddish grey for container (80% opacity)
        bg_color_rgba = "rgba(52, 48, 50, 0)"

        # Logo above container
        self.logo_label = QLabel(self)
        logo_path = get_static_path("src/logo_astras_pix.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            scaled_pixmap = pixmap.scaledToWidth(
                250, Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(scaled_pixmap)
            self.logo_label.setFixedSize(250, 250)
            self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Center container with title and buttons
        self.center_container = QFrame(self)
        self.center_container.setFixedSize(480, 420)
        self.center_container.setStyleSheet(
            f"background-color: {bg_color_rgba}; border: none;"
        )
        self.center_container.setContentsMargins(10, 10, 10, 10)

        button_layout = QVBoxLayout(self.center_container)
        button_layout.setContentsMargins(30, 40, 30, 40)
        button_layout.setSpacing(0)

        # Title and subtitle as single HTML label for tight spacing control
        header = QLabel()
        header.setTextFormat(Qt.TextFormat.RichText)
        header.setText(
            '<div style="text-align: center; line-height: 0.8;">'
            '<p style="font-family: Minecraft; font-size: 24pt; font-weight: bold; '
            'color: #ffffff; margin: 0px; padding: 0px; letter-spacing: 1px;">PROJEKT ASTRAS</p>'
            '<p style="font-family: Minecraft; font-size: 14pt; '
            'color: #cccccc; margin: 0px; margin-top: 5px; padding: 0px; letter-spacing: 1px;">Simulation v1.0</p>'
            "</div>"
        )
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("background-color: transparent;")
        header.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(header)

        # Minimal spacing before buttons

        # Button style with very slight reddish grey and rounded corners
        button_style = """
            QPushButton {
                background-color: rgba(60, 56, 58, 0);
                color: white;
                border: 2px solid rgba(80, 76, 78, 0);
                border-radius: 0px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(70, 66, 68, 0);
                border-color: rgba(90, 86, 88, 0);
            }
        """

        # Buttons
        btn_start = QPushButton("Start Simulation")
        btn_start_font = QFont("Minecraft", 11)
        btn_start_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        btn_start.setFont(btn_start_font)
        btn_start.setFixedHeight(40)
        btn_start.setStyleSheet(button_style)
        btn_start.clicked.connect(self.go_to_simulation)
        button_layout.addWidget(btn_start)

        btn_settings = QPushButton("Settings")
        btn_settings_font = QFont("Minecraft", 11)
        btn_settings_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        btn_settings.setFont(btn_settings_font)
        btn_settings.setFixedHeight(40)
        btn_settings.setStyleSheet(button_style)
        btn_settings.clicked.connect(self.on_settings)
        button_layout.addWidget(btn_settings)

        btn_exit = QPushButton("Exit")
        btn_exit_font = QFont("Minecraft", 11)
        btn_exit_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        btn_exit.setFont(btn_exit_font)
        btn_exit.setFixedHeight(40)
        btn_exit.setStyleSheet(button_style)
        btn_exit.clicked.connect(self.on_exit)
        button_layout.addWidget(btn_exit)

    def resizeEvent(self, event):
        """Handle resize to scale background properly and reposition elements."""
        super().resizeEvent(event)

        # Calculate center position
        width = self.width()
        height = self.height()

        # Total height: logo (250) + spacing (5) + container (420) = 675
        total_height = 625
        start_y = (height - total_height) // 2

        # Center logo horizontally
        logo_x = (width - 250) // 2
        self.logo_label.move(logo_x, start_y)

        # Position container below logo with minimal spacing
        container_x = (width - 480) // 2
        container_y = start_y + 250 + 5  # logo height + minimal spacing
        self.center_container.move(container_x, container_y)

        # Resize background to match widget size
        self._resize_background(event)

    def _resize_background(self, event):
        """Handle resize to scale background properly."""
        # Resize background to match widget size
        size = event.size()
        self.bg_label.setGeometry(0, 0, size.width(), size.height())

        # Ensure proper z-order: background -> logo/container
        self.bg_label.lower()
        self.logo_label.raise_()
        self.center_container.raise_()

        # Scale movie to cover the area while maintaining aspect ratio
        if hasattr(self, "movie"):
            from PyQt6.QtCore import QSize

            movie_size = self.movie.currentPixmap().size()
            if not movie_size.isEmpty():
                # Calculate scaling to cover the entire area
                scale_w = size.width() / movie_size.width()
                scale_h = size.height() / movie_size.height()
                scale = max(scale_w, scale_h)  # Use larger scale to cover
                new_size = QSize(
                    int(movie_size.width() * scale), int(movie_size.height() * scale)
                )
                self.movie.setScaledSize(new_size)

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
