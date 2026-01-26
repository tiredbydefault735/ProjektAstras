from pathlib import Path
import json

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSizePolicy,
    QSplitter,
    QFrame,
    QScrollArea,
)
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

from utils import get_static_path


class SpeciesInfoScreen(QWidget):
    """Full-page species info screen similar in layout to SimulationScreen."""

    def __init__(self, go_back_callback=None, color_preset=None):
        super().__init__()
        self.go_back = go_back_callback
        self.color_preset = color_preset
        self._pixmap = None

        self.init_ui()
        # Load species data for the right-hand details panel
        try:
            json_path = get_static_path("data/species.json")
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    self.species_data = json.load(f)
            else:
                self.species_data = {}
        except Exception:
            self.species_data = {}

        # Populate details list
        self._populate_details()

        # Load default infographic if present and set matching region background
        try:
            img_path = get_static_path("ui/icefang_info.png")
            if img_path.exists():
                pm = QPixmap(str(img_path))
                self._pixmap = pm
                # If species data includes Icefang, set region background
                try:
                    region = None
                    if getattr(self, "species_data", None):
                        region = self.species_data.get("Icefang", {}).get("home_region")
                    if region:
                        self.set_region_background(region)
                except Exception:
                    pass
                self._update_pixmap()
            else:
                self.img_label.setText("No infographic available")
        except Exception:
            self.img_label.setText("No infographic available")

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Top bar with back and exit buttons
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.btn_back = QPushButton("← Back")
        btn_back_font = QFont("Minecraft", 12)
        btn_back_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_back.setFont(btn_back_font)
        from config import BUTTON_FIXED_WIDTH

        self.btn_back.setFixedWidth(BUTTON_FIXED_WIDTH)
        self.btn_back.clicked.connect(self._on_back)
        top_bar.addWidget(self.btn_back)

        top_bar.addStretch()

        self.btn_exit = QPushButton("Exit")
        btn_exit_font = QFont("Minecraft", 12)
        btn_exit_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_exit.setFont(btn_exit_font)
        self.btn_exit.setFixedWidth(BUTTON_FIXED_WIDTH)
        self.btn_exit.clicked.connect(self.on_exit)
        top_bar.addWidget(self.btn_exit)

        main_layout.addLayout(top_bar)

        # Content splitter: left image, right species details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: details panel
        self.left_frame = QFrame()
        left_layout = QVBoxLayout(self.left_frame)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)

        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_container = QFrame()
        self.details_layout = QVBoxLayout(self.details_container)
        self.details_layout.setContentsMargins(0, 0, 0, 0)
        self.details_layout.setSpacing(10)
        self.details_scroll.setWidget(self.details_container)

        left_layout.addWidget(self.details_scroll)
        splitter.addWidget(self.left_frame)

        # Right: image area (will show region background via stylesheet)
        self.right_frame = QFrame()
        right_layout = QVBoxLayout(self.right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        # Add subtle drop shadow behind the infographic image
        try:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(24)
            shadow.setColor(QColor(0, 0, 0, 160))
            shadow.setOffset(6, 6)
            self.img_label.setGraphicsEffect(shadow)
        except Exception:
            pass

        right_layout.addWidget(self.img_label)
        splitter.addWidget(self.right_frame)

        # Give right side more space by default (info left, graphic right)
        splitter.setSizes([400, 800])

        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()

    def _update_pixmap(self):
        if getattr(self, "_pixmap", None) is None:
            return
        try:
            w = max(200, int(self.width() * 0.55))
            scaled = self._pixmap.scaledToWidth(
                w, Qt.TransformationMode.SmoothTransformation
            )
            self.img_label.setPixmap(scaled)
        except Exception:
            try:
                self.img_label.setPixmap(self._pixmap)
            except Exception:
                pass

    def update_language(self):
        # Update translated button texts when language changes
        try:
            from frontend.i18n import _

            if hasattr(self, "btn_back"):
                self.btn_back.setText("← " + _("Back"))
            if hasattr(self, "btn_exit"):
                self.btn_exit.setText(_("Exit"))
        except Exception:
            pass

    def update_theme(self, preset):
        # Apply color preset to background if provided
        self.color_preset = preset
        try:
            bg = preset.get_color("bg_secondary") if preset else "#2a2a2a"
            self.setStyleSheet(f"background-color: {bg};")
        except Exception:
            pass

    def set_region_background(self, region_name: str | None):
        """Try to locate a background image for the given region and apply it.

        This will try several candidate paths under `static/` and apply the
        first existing image as the left panel background via stylesheet.
        """
        if not region_name:
            return
        candidates = [
            f"ui/{region_name}.png",
            f"ui/{region_name}.jpg",
            f"ui/{region_name.lower()}.png",
            f"ui/{region_name.lower()}.jpg",
            f"ui/bg_{region_name}.png",
            f"ui/bg_{region_name}.jpg",
            f"src/{region_name}.png",
        ]
        for rel in candidates:
            p = get_static_path(rel)
            try:
                if p.exists():
                    # Use stylesheet to set the background image for the right frame
                    safe_path = str(p).replace("\\", "/")
                    # apply to right frame which now holds the infographic
                    if hasattr(self, "right_frame"):
                        self.right_frame.setStyleSheet(
                            f"background-image: url('{safe_path}'); background-position: center; background-repeat: no-repeat;"
                        )
                    return
            except Exception:
                continue
        # If none found, clear background
        try:
            if hasattr(self, "right_frame"):
                self.right_frame.setStyleSheet("")
        except Exception:
            pass

    def _populate_details(self):
        # Populate the right-hand details panel from self.species_data
        try:
            # clear existing
            if hasattr(self, "details_layout"):
                for i in reversed(range(self.details_layout.count())):
                    w = self.details_layout.itemAt(i).widget()
                    if w is not None:
                        w.setParent(None)
        except Exception:
            pass

        if not getattr(self, "species_data", None):
            try:
                lbl = QLabel("No species data available")
                self.details_layout.addWidget(lbl)
            except Exception:
                pass
            return

        for name, cfg in self.species_data.items():
            try:
                title = QLabel(f"{name}")
                title_font = QFont("Minecraft", 12, QFont.Weight.Bold)
                title.setFont(title_font)
                title.setStyleSheet("color: #ffffff;")
                self.details_layout.addWidget(title)

                info_lines = []
                home = cfg.get("home_region", "-")
                hp = cfg.get("hp", "-")
                food = cfg.get("food_intake", "-")
                max_clan = cfg.get("max_clan_members", "-")
                info_lines.append(f"Heimat: {home}")
                info_lines.append(f"HP: {hp}")
                info_lines.append(f"Futteraufnahme: {food}")
                info_lines.append(f"Max Clan Größe: {max_clan}")

                interactions = cfg.get("interactions", {})
                if interactions:
                    info_lines.append("Interaktionen:")
                    for other, rel in interactions.items():
                        info_lines.append(f" - {other}: {rel}")

                info_text = "<br>".join(info_lines)
                lbl = QLabel(info_text)
                lbl.setWordWrap(True)
                lbl.setStyleSheet("color: #dddddd;")
                self.details_layout.addWidget(lbl)
            except Exception:
                pass

        try:
            self.details_layout.addStretch()
        except Exception:
            pass

    def _on_back(self):
        if callable(self.go_back):
            try:
                self.go_back()
            except Exception:
                pass

    def on_exit(self):
        from PyQt6.QtWidgets import QApplication

        try:
            QApplication.quit()
        except Exception:
            pass
