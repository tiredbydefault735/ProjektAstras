"""
StartScreen - First screen with logo and buttons.
"""

import sys
from pathlib import Path

# Add parent directory to path for config imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QGraphicsOpacityEffect,
)
from PyQt6.QtGui import QPixmap, QFont, QColor, QMovie, QIcon
from PyQt6.QtCore import Qt
from utils import get_static_path
from frontend.i18n import _, set_language, get_language


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

        gif_path = get_static_path(config.START_SCREEN_BACKGROUND)
        if gif_path.exists():
            self.movie = QMovie(str(gif_path))
            self.bg_label.setMovie(self.movie)
            self.movie.start()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 80)
        main_layout.setSpacing(0)

        # Top row: language flags (right aligned)
        top_row = QHBoxLayout()
        top_row.addStretch()

        # Flag icons (try common names in static/icons)
        possible_en = config.FLAG_EN_PATHS
        possible_de = config.FLAG_DE_PATHS

        def find_first(paths):
            for p in paths:
                pth = get_static_path(p)
                if pth.exists():
                    return pth
            # fallback to first path (may not exist)
            return get_static_path(paths[0])

        en_flag = find_first(possible_en)
        de_flag = find_first(possible_de)

        def make_flag_button(path, code):
            btn = QPushButton()
            btn.setFixedSize(config.FLAG_BUTTON_WIDTH, config.FLAG_BUTTON_HEIGHT)
            btn.setStyleSheet("border: none; background: transparent; color: #ffffff;")
            try:
                if Path(path).exists():
                    pix = QPixmap(str(path))
                    if not pix.isNull():
                        btn.setIcon(QIcon(pix))
                        btn.setIconSize(btn.size())
            except Exception:
                pass
            # Fallback: show language code if icon missing
            if btn.icon().isNull():
                btn.setText(code.upper())
                btn.setStyleSheet(
                    "border: none; background: transparent; color: #ffffff; font-weight: bold;"
                )
                btn.setFont(QFont("Minecraft", 12))
            btn.show()
            btn.clicked.connect(lambda _, c=code: self.change_language(c))
            return btn

        self.btn_flag_en = make_flag_button(en_flag, "en")
        self.btn_flag_de = make_flag_button(de_flag, "de")

        # Attach flags to this widget so we can position them manually
        self.btn_flag_en.setParent(self)
        self.btn_flag_de.setParent(self)
        # Initialize selection visuals
        try:
            self.change_language(get_language())
        except Exception:
            pass

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
        header.setObjectName("start_header")
        header.setText(self._header_html())
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
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(180, 75, 75, 0);
            }
        """

        # Buttons
        self.btn_start = QPushButton(_("Start Simulation"))
        btn_start_font = QFont("Minecraft", 11)
        btn_start_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_start.setFont(btn_start_font)
        self.btn_start.setFixedHeight(40)
        self.btn_start.setStyleSheet(button_style)
        self.btn_start.clicked.connect(self._on_start_clicked)
        button_layout.addWidget(self.btn_start)

        self.btn_settings = QPushButton(_("Species Information"))
        btn_settings_font = QFont("Minecraft", 11)
        btn_settings_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_settings.setFont(btn_settings_font)
        self.btn_settings.setFixedHeight(40)
        self.btn_settings.setStyleSheet(button_style)
        self.btn_settings.clicked.connect(self.on_species_info)
        button_layout.addWidget(self.btn_settings)

        self.btn_exit = QPushButton(_("Exit"))
        btn_exit_font = QFont("Minecraft", 11)
        btn_exit_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_exit.setFont(btn_exit_font)
        self.btn_exit.setFixedHeight(40)
        self.btn_exit.setStyleSheet(button_style)
        self.btn_exit.clicked.connect(self.on_exit)
        button_layout.addWidget(self.btn_exit)

        # Register to receive language change notifications
        try:
            from frontend.i18n import register_language_listener

            register_language_listener(self.update_language)
        except Exception:
            pass

    def update_language(self):
        """Update UI texts when global language changes (do not call set_language here)."""
        try:
            # Update header and buttons
            if hasattr(self, "_header_html"):
                # Replace header HTML content
                header = self.findChild(QLabel, "start_header")
                if header is not None:
                    header.setText(self._header_html())
            if hasattr(self, "btn_start"):
                self.btn_start.setText(_("Start Simulation"))
            if hasattr(self, "btn_settings"):
                self.btn_settings.setText(_("Species Information"))
            if hasattr(self, "btn_exit"):
                self.btn_exit.setText(_("Exit"))
        except Exception:
            pass

    def _on_start_clicked(self):
        self.btn_start.setVisible(False)
        if self.go_to_simulation:
            self.go_to_simulation()

    def _header_html(self):
        # Compose header HTML using translations
        title = _("PROJEKT ASTRAS")
        subtitle = _("Simulation v1.0")
        return (
            '<div style="text-align: center; line-height: 0.8;">'
            f'<p style="font-family: Minecraft; font-size: 24pt; font-weight: bold; '
            f'color: #ffffff; margin: 0px; padding: 0px; letter-spacing: 1px;">{title}</p>'
            f'<p style="font-family: Minecraft; font-size: 14pt; '
            f'color: #cccccc; margin: 0px; margin-top: 5px; padding: 0px; letter-spacing: 1px;">{subtitle}</p>'
            "</div>"
        )

    def on_species_info(self):
        """Navigate to the Species Info screen; fall back to dialog if no callback."""
        # Prefer the stacked widget navigation callback if provided
        if hasattr(self, "go_to_settings") and callable(self.go_to_settings):
            try:
                self.go_to_settings()
                return
            except Exception:
                pass

        # Fallback: show a simple dialog with the infographic
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton

        dlg = QDialog(self)
        dlg.setWindowTitle("Species Information")
        layout = QVBoxLayout(dlg)

        img_path = get_static_path("ui/icefang_info.png")
        info_label = QLabel()
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if img_path.exists():
            pm = QPixmap(str(img_path))
            # scale image to reasonable size within dialog
            try:
                scaled = pm.scaledToWidth(
                    700, Qt.TransformationMode.SmoothTransformation
                )
                info_label.setPixmap(scaled)
            except Exception:
                info_label.setPixmap(pm)
        else:
            info_label.setText("No infographic available")

        layout.addWidget(info_label)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)

        dlg.exec()

    def change_language(self, code):
        try:
            set_language(code)
        except Exception:
            pass
        # Update UI labels
        self.btn_start.setText(_("Start Simulation"))
        self.btn_settings.setText(_("Species Information"))
        self.btn_exit.setText(_("Exit"))
        # Update header
        header = self.findChild(QLabel, "start_header")
        if header:
            header.setText(self._header_html())
        # Update flag visibility to indicate selection (simple opacity)
        current = get_language()

        def set_opacity(widget, on):
            effect = QGraphicsOpacityEffect(widget)
            effect.setOpacity(1.0 if on else 0.45)
            widget.setGraphicsEffect(effect)

        set_opacity(self.btn_flag_en, current == "en")
        set_opacity(self.btn_flag_de, current == "de")

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

        # Position language flags at bottom-right corner (20px padding)
        try:
            padding = 20
            spacing = 6
            fx = (
                width
                - padding
                - (self.btn_flag_de.width() if hasattr(self, "btn_flag_de") else 0)
            )
            fy = (
                height
                - padding
                - (self.btn_flag_de.height() if hasattr(self, "btn_flag_de") else 0)
            )
            # Place right-most (de) then en to its left
            if hasattr(self, "btn_flag_de"):
                self.btn_flag_de.move(fx, fy)
                self.btn_flag_de.raise_()
                fx -= self.btn_flag_en.width() + spacing
            if hasattr(self, "btn_flag_en"):
                self.btn_flag_en.move(fx, fy)
                self.btn_flag_en.raise_()
        except Exception:
            pass

        # Ensure flags are above the background/movie as well
        try:
            if hasattr(self, "btn_flag_de"):
                self.btn_flag_de.raise_()
            if hasattr(self, "btn_flag_en"):
                self.btn_flag_en.raise_()
        except Exception:
            pass

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
