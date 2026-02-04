"""
StartScreen - First screen with logo and buttons.
"""

from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional, Any
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
from config import (
    START_SCREEN_GIF_PATH,
    FLAG_ICON_EN_CANDIDATES,
    FLAG_ICON_DE_CANDIDATES,
    UI_FONT_FAMILY,
)


class StartScreen(QWidget):
    """Start/intro screen with logo and navigation buttons."""

    def __init__(
        self,
        go_to_simulation_callback: Callable[[], None],
        color_preset: Optional[Any] = None,
    ) -> None:
        super().__init__()
        self.go_to_simulation = go_to_simulation_callback
        self.color_preset = color_preset
        self.center_container = None
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize UI."""
        self.bg_label = QLabel(self)
        self.bg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        gif_path = get_static_path(START_SCREEN_GIF_PATH)
        if gif_path.exists():
            self.movie = QMovie(str(gif_path))
            self.bg_label.setMovie(self.movie)
            self.movie.start()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 80)
        main_layout.setSpacing(0)

        top_row = QHBoxLayout()
        top_row.addStretch()

        possible_en = FLAG_ICON_EN_CANDIDATES
        possible_de = FLAG_ICON_DE_CANDIDATES

        def find_first(paths):
            for p in paths:
                pth = get_static_path(p)
                if pth.exists():
                    return pth
            return get_static_path(paths[0])

        en_flag = find_first(possible_en)
        de_flag = find_first(possible_de)

        def make_flag_button(path, code):
            btn = QPushButton()
            btn.setFixedSize(48, 32)
            btn.setStyleSheet("border: none; background: transparent; color: #ffffff;")
            try:
                if Path(path).exists():
                    pix = QPixmap(str(path))
                    if not pix.isNull():
                        btn.setIcon(QIcon(pix))
                        btn.setIconSize(btn.size())
            except Exception:
                pass
            if btn.icon().isNull():
                btn.setText(code.upper())
                btn.setStyleSheet(
                    "border: none; background: transparent; color: #ffffff; font-weight: bold;"
                )
                btn.setFont(QFont(UI_FONT_FAMILY, 12))
            btn.show()
            btn.clicked.connect(lambda _, c=code: self.change_language(c))
            return btn

        self.btn_flag_en = make_flag_button(en_flag, "en")
        self.btn_flag_de = make_flag_button(de_flag, "de")

        self.btn_flag_en.setParent(self)
        self.btn_flag_de.setParent(self)
        try:
            self.change_language(get_language())
        except Exception:
            pass

        bg_color = (
            self.color_preset.get_color("bg_secondary")
            if self.color_preset
            else "#2a2a2a"
        )

        bg_color_rgba = "rgba(52, 48, 50, 0)"

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

        self.center_container = QFrame(self)
        self.center_container.setFixedSize(480, 300)
        self.center_container.setStyleSheet(
            f"background-color: {bg_color_rgba}; border: none;"
        )
        self.center_container.setContentsMargins(10, 10, 10, 10)

        button_layout = QVBoxLayout(self.center_container)
        button_layout.setContentsMargins(30, 10, 30, 10)
        button_layout.setSpacing(5)

        header = QLabel()
        header.setTextFormat(Qt.TextFormat.RichText)
        header.setObjectName("start_header")
        header.setText(self._header_html())
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("background-color: transparent;")
        header.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(header)

        button_style = """
            QPushButton {
                background-color: rgba(60, 56, 58, 0);
                color: white;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 50);
            }
        """

        self.btn_start = QPushButton(_("Start Simulation"))
        btn_start_font = QFont("Minecraft", 11)
        btn_start_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_start.setFont(btn_start_font)
        self.btn_start.setFixedHeight(40)
        self.btn_start.setStyleSheet(button_style)
        self.btn_start.clicked.connect(self._on_start_clicked)
        button_layout.addWidget(self.btn_start)

        self.btn_exit = QPushButton(_("Exit"))
        btn_exit_font = QFont("Minecraft", 11)
        btn_exit_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_exit.setFont(btn_exit_font)
        self.btn_exit.setFixedHeight(40)
        self.btn_exit.setStyleSheet(button_style)
        self.btn_exit.clicked.connect(self.on_exit)
        button_layout.addWidget(self.btn_exit)

        try:
            from frontend.i18n import register_language_listener

            register_language_listener(self.update_language)
        except Exception:
            pass

    def update_language(self) -> None:
        """Update UI texts when global language changes (do not call set_language here)."""
        try:
            if hasattr(self, "_header_html"):
                header = self.findChild(QLabel, "start_header")
                if header is not None:
                    header.setText(self._header_html())
            if hasattr(self, "btn_start"):
                self.btn_start.setText(_("Start Simulation"))
            if hasattr(self, "btn_exit"):
                self.btn_exit.setText(_("Exit"))
        except Exception:
            pass

    def _on_start_clicked(self):
        self.btn_start.setVisible(False)
        if self.go_to_simulation:
            self.go_to_simulation()

    def _header_html(self):
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

    def change_language(self, code: str) -> None:
        try:
            set_language(code)
        except Exception:
            pass
        self.btn_start.setText(_("Start Simulation"))
        self.btn_exit.setText(_("Exit"))
        header = self.findChild(QLabel, "start_header")
        if header:
            header.setText(self._header_html())
        current = get_language()

        def set_opacity(widget, on):
            effect = QGraphicsOpacityEffect(widget)
            effect.setOpacity(1.0 if on else 0.45)
            widget.setGraphicsEffect(effect)

        set_opacity(self.btn_flag_en, current == "en")
        set_opacity(self.btn_flag_de, current == "de")

    def resizeEvent(self, a0):
        """Handle resize to scale background properly and reposition elements."""
        super().resizeEvent(a0)

        width = self.width()
        height = self.height()

        total_height = 555
        start_y = (height - total_height) // 2

        logo_x = (width - 250) // 2
        self.logo_label.move(logo_x, start_y)

        container_x = (width - 480) // 2
        container_y = start_y + 250 + 5
        self.center_container.move(container_x, container_y)

        self._resize_background(a0)

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
            if hasattr(self, "btn_flag_de"):
                self.btn_flag_de.move(fx, fy)
                self.btn_flag_de.raise_()
                fx -= self.btn_flag_en.width() + spacing
            if hasattr(self, "btn_flag_en"):
                self.btn_flag_en.move(fx, fy)
                self.btn_flag_en.raise_()
        except Exception:
            pass

        try:
            if hasattr(self, "btn_flag_de"):
                self.btn_flag_de.raise_()
            if hasattr(self, "btn_flag_en"):
                self.btn_flag_en.raise_()
        except Exception:
            pass

    def _resize_background(self, event):
        """Handle resize to scale background properly."""
        size = event.size()
        self.bg_label.setGeometry(0, 0, size.width(), size.height())

        self.bg_label.lower()
        self.logo_label.raise_()
        self.center_container.raise_()

        if hasattr(self, "movie"):
            from PyQt6.QtCore import QSize

            movie_size = self.movie.currentPixmap().size()
            if not movie_size.isEmpty():
                scale_w = size.width() / movie_size.width()
                scale_h = size.height() / movie_size.height()
                scale = max(scale_w, scale_h)
                new_size = QSize(
                    int(movie_size.width() * scale), int(movie_size.height() * scale)
                )
                self.movie.setScaledSize(new_size)

    def on_exit(self):
        """Exit button clicked."""
        from PyQt6.QtWidgets import QApplication

        QApplication.quit()

    def update_theme(self, preset):
        """Update inline styles used by the Start screen."""
        self.color_preset = preset
        bg_color = preset.get_color("bg_secondary") if preset else "#2a2a2a"
        if self.center_container is not None:
            self.center_container.setStyleSheet(
                f"background-color: {bg_color}; border: none;"
            )
