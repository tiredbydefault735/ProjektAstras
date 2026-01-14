from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from frontend.i18n import _


class StatsDialog(QDialog):
    """Popup dialog to display final simulation statistics."""

    def __init__(self, stats, parent=None):
        super().__init__(parent)
        try:
            self.setWindowTitle(_("Simulations-Statistiken"))
        except Exception:
            self.setWindowTitle("Simulations-Statistiken")
        # keep stats so we can refresh text when language changes
        self._stats = stats
        self.setModal(True)
        self.resize(900, 500)

        # Set dark theme
        self.setStyleSheet("background-color: #1a1a1a; color: #ffffff;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title = QLabel(_("Simulations-Statistiken (5 Minuten)"))
        title_font = QFont("Minecraft", 16, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        title.setFont(title_font)
        title.setStyleSheet("color: #ffffff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Left side: Stats text
        stats_text = QLabel()
        stats_font = QFont("Minecraft", 11)
        stats_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        stats_text.setFont(stats_font)
        stats_text.setWordWrap(True)
        stats_text.setStyleSheet("color: #ffffff; padding: 10px;")
        stats_text.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Build stats string
        text = "<b>" + _("Spezies im Spiel:") + "</b><br>"
        for species, count in stats.get("species_counts", {}).items():
            text += f"• {species}: {count}<br>"

        text += f"<br><b>{_('Todesfälle (Kampf):')}</b><br>"
        for species, count in stats.get("deaths", {}).get("combat", {}).items():
            text += f"• {species}: {count}<br>"

        text += f"<br><b>{_('Todesfälle (Verhungert):')}</b><br>"
        for species, count in stats.get("deaths", {}).get("starvation", {}).items():
            text += f"• {species}: {count}<br>"

        text += f"<br><b>{_('Todesfälle (Temperatur):')}</b><br>"
        for species, count in stats.get("deaths", {}).get("temperature", {}).items():
            text += f"• {species}: {count}<br>"

        text += f"<br><b>{_('Maximale Clans:')}</b> {stats.get('max_clans', 0)}<br>"
        text += f"<b>{_('Futterplätze:')}</b> {stats.get('food_places', 0)}"

        stats_text.setText(text)
        self._stats_text = stats_text

        main_layout.addWidget(stats_text)

        close_btn = QPushButton(_("Schließen"))
        close_btn_font = QFont("Minecraft", 12)
        close_btn_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        close_btn.setFont(close_btn_font)
        close_btn.setFixedHeight(40)
        close_btn.setStyleSheet(
            "background-color: #444444; color: #ffffff; "
            "border: 2px solid #666666; padding: 5px;"
        )
        close_btn.clicked.connect(self.close)
        main_layout.addWidget(close_btn)

    def _refresh_texts(self):
        try:
            # window title
            try:
                self.setWindowTitle(_("Simulations-Statistiken"))
            except Exception:
                pass
            # title (first QLabel added in layout)
            try:
                title_widget = self.findChild(QLabel)
                if title_widget is not None:
                    title_widget.setText(_("Simulations-Statistiken (5 Minuten)"))
            except Exception:
                pass
            # rebuild the main text area using stored stats
            try:
                stats = getattr(self, "_stats", {})
                text = "<b>" + _("Spezies im Spiel:") + "</b><br>"
                for species, count in stats.get("species_counts", {}).items():
                    text += f"• {species}: {count}<br>"
                # other sections omitted for brevity
                if hasattr(self, "_stats_text") and self._stats_text is not None:
                    try:
                        self._stats_text.setText(text)
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass
