"""
SimulationScreen - Main simulation view with map and controls.
"""

# Log rendering constants
LOG_FONT_FAMILY = "Consolas"
LOG_FONT_SIZE = 12

import json
import sys
import math
from pathlib import Path

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
    QSlider,
    QFrame,
    QCheckBox,
    QStackedWidget,
    QDialog,
    QTextEdit,
    QPlainTextEdit,
    QSplitter,
)
from PyQt6.QtCore import Qt, QTimer, QSize, QRegularExpression
from PyQt6.QtGui import (
    QFont,
    QIcon,
    QPixmap,
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
)

from backend.model import SimulationModel
from screens.simulation_map import SimulationMapWidget
from frontend.i18n import _


class LogHighlighter(QSyntaxHighlighter):
    """Simple syntax highlighter for log colorization using regex rules."""

    def __init__(self, document):
        super().__init__(document)

        def fmt(color_hex, bold=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color_hex))
            f.setFontFamily(LOG_FONT_FAMILY)
            f.setFontPointSize(LOG_FONT_SIZE)
            if bold:
                f.setFontWeight(QFont.Weight.Bold)
            return f

        # Use inline (?i) for case-insensitive matching to avoid enum differences
        self.rules = [
            (QRegularExpression(r"(?i)☠️.*verhungert.*"), fmt("#cc3333")),
            (QRegularExpression(r"(?i)❄️.*Temperatur.*"), fmt("#99ddff")),
            (QRegularExpression(r"(?i)stirbt an Temperatur"), fmt("#ff9999")),
            (QRegularExpression(r"(?i)🍽️|🍖|\bisst\b"), fmt("#cd853f")),
            (QRegularExpression(r"(?i)👥.*tritt.*bei"), fmt("#bb88ff")),
            (QRegularExpression(r"(?i)verlässt|verlassen"), fmt("#ff9944")),
            (QRegularExpression(r"(?i)⚔️|💀"), fmt("#ff6666")),
            (QRegularExpression(r"(?i)🌡️"), fmt("#66ccff")),
            (QRegularExpression(r"(?i)☀️"), fmt("#ffdd44")),
            (QRegularExpression(r"(?i)🌙"), fmt("#aa88ff")),
        ]

    def highlightBlock(self, text: str | None) -> None:
        if not text:
            return
        for rx, fmt in self.rules:
            it = rx.globalMatch(text)
            while it.hasNext():
                m = it.next()
                start = m.capturedStart()
                length = m.capturedLength()
                self.setFormat(start, length, fmt)


class CustomCheckBox(QCheckBox):
    """Custom checkbox that draws image directly."""

    def __init__(self, text, unchecked_path, checked_path, parent=None):
        super().__init__(text, parent)
        self.unchecked_pixmap = QPixmap(unchecked_path)
        self.checked_pixmap = QPixmap(checked_path)

        # Scale pixmaps to 20x20 if needed
        if not self.unchecked_pixmap.isNull():
            self.unchecked_pixmap = self.unchecked_pixmap.scaled(
                20,
                20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        if not self.checked_pixmap.isNull():
            self.checked_pixmap = self.checked_pixmap.scaled(
                20,
                20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        # Hide default indicator and add spacing for our custom image
        self.setStyleSheet(
            """
            QCheckBox {
                spacing: 30px;
            }
            QCheckBox::indicator {
                width: 0px;
                height: 0px;
            }
        """
        )
        self.setMinimumHeight(28)

    def paintEvent(self, a0):
        super().paintEvent(a0)
        from PyQt6.QtGui import QPainter

        painter = QPainter(self)

        # Draw checkbox image at left position
        pixmap = self.checked_pixmap if self.isChecked() else self.unchecked_pixmap
        if not pixmap.isNull():
            painter.drawPixmap(0, (self.height() - 20) // 2, pixmap)

        painter.end()


class CustomImageButton(QPushButton):
    """Button that draws a centered image; supports checked state with optional alternate image."""

    def __init__(self, image_path, checked_image_path=None, parent=None, size=36):
        super().__init__(parent)
        self.pixmap = QPixmap(image_path)
        self.checked_pixmap = (
            QPixmap(checked_image_path) if checked_image_path else None
        )
        self.setCheckable(True)
        self.setFixedSize(size, size)
        self.setStyleSheet("border: none; background: transparent;")

    def paintEvent(self, event):
        super().paintEvent(event)
        from PyQt6.QtGui import QPainter

        painter = QPainter(self)
        pix = (
            self.checked_pixmap
            if (self.isChecked() and self.checked_pixmap)
            else self.pixmap
        )
        if not pix.isNull():
            scaled = pix.scaled(
                max(4, self.width() - 8),
                max(4, self.height() - 8),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        painter.end()


class StatsDialog(QDialog):
    """Popup dialog to display final simulation statistics."""

    def __init__(self, stats, parent=None):
        super().__init__(parent)
        # initialize layout and widgets for stats dialog
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

        # Horizontal layout for text and graph
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left side: Stats text
        stats_text = QLabel()
        stats_font = QFont("Minecraft", 11)
        stats_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        stats_text.setFont(stats_font)
        stats_text.setWordWrap(True)
        stats_text.setStyleSheet("color: #ffffff; padding: 10px;")
        stats_text.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Build stats string (each section added once, loops separate)
        text = "<b>" + _("Spezies im Spiel:") + "</b><br>"
        for species, count in stats.get("species_counts", {}).items():
            text += f"• {species}: {count}<br>"

        # Combat deaths
        text += f"<br><b>{_('Todesfälle (Kampf):')}</b><br>"
        for species, count in stats.get("deaths", {}).get("combat", {}).items():
            text += f"• {species}: {count}<br>"

        # Starvation deaths
        text += f"<br><b>{_('Todesfälle (Verhungert):')}</b><br>"
        for species, count in stats.get("deaths", {}).get("starvation", {}).items():
            text += f"• {species}: {count}<br>"

        # Temperature deaths
        text += f"<br><b>{_('Todesfälle (Temperatur):')}</b><br>"
        for species, count in stats.get("deaths", {}).get("temperature", {}).items():
            text += f"• {species}: {count}<br>"

        # Summary numbers
        text += f"<br><b>{_('Maximale Clans:')}</b> {stats.get('max_clans', 0)}<br>"
        text += f"<b>{_('Futterplätze:')}</b> {stats.get('food_places', 0)}"

        # store stats reference and text widget for language refresh and summaries
        try:
            self._stats = stats
        except Exception:
            self._stats = {}

        # Add a short summary of randomizer samples (helps debugging missing events)
        try:
            rnd = stats.get("rnd_samples", {}) or {}
            regen_count = len(rnd.get("regen", []))
            clan_count = len(rnd.get("clan_growth", []))
            loner_count = len(rnd.get("loner_spawn", []))
            try:
                regen_sum = sum(int(v) for v in rnd.get("regen", []) if v is not None)
            except Exception:
                regen_sum = 0
            try:
                clan_sum = sum(
                    int(v) for v in rnd.get("clan_growth", []) if v is not None
                )
            except Exception:
                clan_sum = 0
            try:
                loner_sum = sum(
                    int(v) for v in rnd.get("loner_spawn", []) if v is not None
                )
            except Exception:
                loner_sum = 0

            text += (
                f"<br><b>{_('Randomizer (Samples):')}</b><br>"
                f"• {_('Regeneration')}: {regen_count} ({regen_sum})<br>"
                f"• {_('Clanwachstum')}: {clan_count} ({clan_sum})<br>"
                f"• {_('Einzelgänger Spawn')}: {loner_count} ({loner_sum})<br>"
            )
        except Exception:
            pass

        stats_text.setText(text)
        # store for language refresh
        self._stats_text = stats_text
        # Register listener so dialog updates if language changes while open
        try:
            from frontend.i18n import register_language_listener

            register_language_listener(self._refresh_texts)
        except Exception:
            pass
        content_layout.addWidget(stats_text, 1)

        # (no separate Y-label column; use axis labels on the plot)

        # Right side: Population graph (use PyQtGraph for real-time performance)
        try:
            import pyqtgraph as pg

            pg.setConfigOptions(antialias=True)

            pw = pg.PlotWidget(background="#1a1a1a")
            # Give final-stats graph more vertical room so curves aren't squished
            pw.setMinimumHeight(300)
            try:
                pw.setMaximumHeight(16777215)
            except Exception:
                pass
            try:
                from PyQt6.QtWidgets import QSizePolicy

                pw.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
            except Exception:
                pass
            pw.getPlotItem().showGrid(x=True, y=True, alpha=0.2)
            pw.getAxis("left").setTextPen("#ffffff")
            pw.getAxis("bottom").setTextPen("#ffffff")
            pw.setLabel("left", "Population", color="#ffffff", size="10pt")
            # remove explicit seconds unit to reduce clutter
            pw.setLabel("bottom", "Zeit", color="#ffffff", size="10pt")

            # Disable user interaction; do NOT lock aspect ratio so the plot
            # can expand vertically to use available space.
            try:
                vb = pw.getPlotItem().getViewBox()
                try:
                    vb.setAspectLocked(False)
                except Exception:
                    pass
                vb.setMouseEnabled(False, False)
                try:
                    vb.setMenuEnabled(False)
                except Exception:
                    pass
            except Exception:
                pass

            population_history = stats.get("population_history", {})
            colors = {
                "Icefang": "#cce6ff",
                "Crushed_Critters": "#cc9966",
                "Spores": "#66cc66",
                "The_Corrupted": "#cc66cc",
            }

            for species, history in population_history.items():
                if history:
                    # Downsample final stats to 5-second steps for clarity
                    # population_history entries are per second; take every 5th
                    ds = 5
                    sampled = history[::ds]
                    # Force integer populations for final stats
                    try:
                        sampled = [int(round(float(v))) for v in sampled]
                    except Exception:
                        try:
                            sampled = [int(v) for v in sampled]
                        except Exception:
                            pass
                    time_points = [i * ds for i in range(len(sampled))]
                    pen = pg.mkPen(colors.get(species, "#ffffff"), width=2)
                    try:
                        pw.plot(time_points, sampled, pen=pen, name=species)
                    except Exception:
                        pass

            # Set Y-axis ticks for final stats: integers when max<10, else steps of 5
            try:
                # Axis styling and adaptive tick selection to avoid label crowding
                left_axis = pw.getAxis("left")
                bottom_axis = pw.getAxis("bottom")
                try:
                    left_axis.setStyle(tickFont=QFont("Minecraft", 10))
                    bottom_axis.setStyle(tickFont=QFont("Minecraft", 10))
                except Exception:
                    pass
                try:
                    # Reduce reserved left axis width so the Y-label sits closer to axis
                    left_axis.setWidth(60)
                except Exception:
                    pass
                try:
                    bottom_axis.setHeight(30)
                except Exception:
                    pass

                overall_max = 0
                max_len = 0
                for history in population_history.values():
                    if history:
                        try:
                            overall_max = max(overall_max, int(round(max(history))))
                        except Exception:
                            overall_max = max(overall_max, int(max(history)))
                        try:
                            max_len = max(max_len, len(history))
                        except Exception:
                            pass

                # Y axis: add small headroom and choose step to keep ~6 ticks
                padded = max(1.0, float(overall_max) * 1.10)
                y_max = int(math.ceil(padded))
                try:
                    import math as _math

                    # Choose a "nice" step so we have at most ~6 ticks
                    nice = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
                    y_step = None
                    for s in nice:
                        if float(y_max) / float(s) <= 6:
                            y_step = s
                            break
                    if y_step is None:
                        # fallback to ceil division
                        y_step = max(1, int(_math.ceil(float(y_max) / 6.0)))

                    # Ensure visible spacing: prefer steps of 10 or more when range is larger
                    try:
                        if y_max >= 20 and y_step < 10:
                            y_step = 10
                    except Exception:
                        pass
                except Exception:
                    y_step = 1 if y_max < 10 else 2
                y_ticks = [(i, str(i)) for i in range(0, y_max + 1, y_step)]
                if y_ticks and y_ticks[-1][0] != y_max:
                    y_ticks.append((y_max, str(y_max)))
                # Show numeric Y-axis labels with the chosen ticks
                try:
                    left_axis.setTicks([y_ticks])
                except Exception:
                    pass
                try:
                    vb = pw.getPlotItem().getViewBox()
                    vb.setYRange(0, y_max, padding=0.20)
                except Exception:
                    pass

                # Bottom axis: compute total duration from population_history and ds
                ds = 5
                total_seconds = max_len * ds if max_len else 0
                # Choose step to avoid overcrowding (seconds or minutes)
                if total_seconds <= 60:
                    step = 5
                elif total_seconds <= 180:
                    step = 30
                elif total_seconds <= 600:
                    step = 60
                else:
                    step = 60

                bottom_ticks = []
                for i in range(0, int(total_seconds) + 1, step):
                    if step >= 60:
                        # show minutes for coarse steps
                        label = f"{int(i // 60)}m"
                    else:
                        label = str(i)
                    bottom_ticks.append((i, label))
                if not bottom_ticks:
                    bottom_ticks = [(0, "0")]
                try:
                    bottom_axis.setTicks([bottom_ticks])
                except Exception:
                    pass

                # no separate Y label widget to populate
            except Exception:
                pass

            # Create a stacked area so we can switch between final population
            # stats and Randomizers visualization using toggle buttons below.
            try:
                from PyQt6.QtWidgets import QStackedWidget, QWidget

                right_stack = QStackedWidget()

                # Page 0: final population plot
                page_stats = QWidget()
                p_stats_layout = QVBoxLayout(page_stats)
                p_stats_layout.setContentsMargins(0, 0, 0, 0)
                p_stats_layout.addWidget(pw)

                # Page 1: Randomizers graph (uses rnd_samples from stats)
                page_rand = QWidget()
                p_rand_layout = QVBoxLayout(page_rand)
                p_rand_layout.setContentsMargins(0, 0, 0, 0)

                try:
                    import pyqtgraph as pg

                    rpw = pg.PlotWidget(background="#151515")
                    rpw.getPlotItem().showGrid(x=True, y=True, alpha=0.15)
                    rpw.setMinimumHeight(300)
                    rpw.setLabel("left", "Value", color="#ffffff", size="9pt")
                    rpw.setLabel("bottom", "Samples", color="#ffffff", size="9pt")
                    try:
                        rpw.addLegend(offset=(8, 8))
                    except Exception:
                        pass

                    # Plot rnd_samples as histograms for better distribution view
                    rnd = stats.get("rnd_samples", {}) or {}
                    colors = {
                        "regen": (102, 204, 102),
                        "clan_growth": (102, 170, 255),
                        "loner_spawn": (255, 204, 102),
                    }
                    display_names = {
                        "regen": "Nahrung (Regeneration)",
                        "clan_growth": "Clanwachstum",
                        "loner_spawn": "Einzelgänger Spawn",
                    }

                    # Collect histograms per series
                    has_any = False
                    max_bin = 0
                    hist_data = {}
                    for key, vals in rnd.items():
                        try:
                            nums = [int(v) for v in vals if v is not None]
                        except Exception:
                            nums = []
                        if not nums:
                            hist_data[key] = ([], [], None)
                            continue
                        has_any = True
                        if key == "regen":
                            # Aggregate regen into bins: 0-1, 2-4, 5-9, 10+
                            ranges = [(0, 1), (2, 4), (5, 9), (10, 10**9)]
                            counts = [0] * len(ranges)
                            for n in nums:
                                for i, (a, b) in enumerate(ranges):
                                    if a <= n <= b:
                                        counts[i] += 1
                                        break
                            bins = list(range(len(ranges)))
                            # labels for bottom axis
                            labels = ["0-1", "2-4", "5-9", "10+"]
                            hist_data[key] = (bins, counts, labels)
                            max_bin = max(max_bin, len(bins) - 1)
                        else:
                            mx = max(nums)
                            max_bin = max(max_bin, mx)
                            # build simple count histogram bins 0..mx
                            counts = [0] * (mx + 1)
                            for n in nums:
                                counts[n] += 1
                            bins = list(range(0, mx + 1))
                            hist_data[key] = (bins, counts, None)

                    if not has_any:
                        # nothing to show
                        placeholder = QLabel(_("Keine Randomizer-Daten verfügbar"))
                        placeholder.setStyleSheet("color: #999999;")
                        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        p_rand_layout.addWidget(placeholder)
                    else:
                        # Create grouped bar chart: shift bars slightly per series
                        try:
                            from pyqtgraph import BarGraphItem

                            group_keys = [
                                k
                                for k in ("regen", "clan_growth", "loner_spawn")
                                if k in hist_data
                            ]
                            # width per bar
                            bw = 0.2
                            offsets = {
                                "regen": -bw,
                                "clan_growth": 0.0,
                                "loner_spawn": bw,
                            }
                            for key in group_keys:
                                bins, counts = hist_data.get(key, ([], []))
                                if not bins:
                                    continue
                                x = [b + offsets.get(key, 0) for b in bins]
                                bg = BarGraphItem(
                                    x=x,
                                    height=counts,
                                    width=bw,
                                    brush=pg.mkBrush(colors.get(key, (200, 200, 200))),
                                )
                                rpw.addItem(bg)
                                try:
                                    # add legend symbol
                                    rpw.plot(
                                        [],
                                        [],
                                        pen=pg.mkPen((0, 0, 0, 0)),
                                        name=display_names.get(key, key),
                                    )
                                except Exception:
                                    pass
                        except Exception:
                            # fallback to time-series if BarGraphItem not available
                            for key, vals in rnd.items():
                                try:
                                    x = list(range(len(vals)))
                                    y = [float(v) for v in vals]
                                    pen = pg.mkPen(
                                        colors.get(key, (200, 200, 200)), width=2
                                    )
                                    rpw.plot(
                                        x, y, pen=pen, name=display_names.get(key, key)
                                    )
                                except Exception:
                                    pass

                    p_rand_layout.addWidget(rpw)
                except Exception:
                    # If pyqtgraph missing, show a placeholder
                    placeholder = QLabel(
                        _("Randomizers graph nicht verfügbar (pyqtgraph benötigt)")
                    )
                    placeholder.setStyleSheet("color: #999999;")
                    placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    p_rand_layout.addWidget(placeholder)

                right_stack.addWidget(page_stats)
                right_stack.addWidget(page_rand)

                # expose stack to dialog for button callbacks
                self._right_stack = right_stack

                content_layout.addWidget(right_stack, 2)
            except Exception:
                # fallback: add the population plot directly
                content_layout.addWidget(pw, 2)
        except Exception:
            no_graph_label = QLabel(_("Graph nicht verfügbar\n(pyqtgraph benötigt)"))
            no_graph_label.setStyleSheet("color: #999999;")
            no_graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(no_graph_label, 2)

        main_layout.addLayout(content_layout)

        # Toggle buttons to switch between Stats and Randomizers graph
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_view_stats = QPushButton(_("Stats"))
        self.btn_view_stats.setCheckable(True)
        self.btn_view_stats.setChecked(True)
        self.btn_view_stats.clicked.connect(lambda: self._switch_stats_page(0))
        btn_row.addWidget(self.btn_view_stats)

        self.btn_view_random = QPushButton(_("Randomizers"))
        self.btn_view_random.setCheckable(True)
        self.btn_view_random.setChecked(False)
        self.btn_view_random.clicked.connect(lambda: self._switch_stats_page(1))
        btn_row.addWidget(self.btn_view_random)

        btn_row.addStretch()
        main_layout.addLayout(btn_row)

        # Close button
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
        """Rebuild localized strings for the dialog when language changes."""
        try:
            from frontend.i18n import _

            # window title
            try:
                self.setWindowTitle(_("Simulations-Statistiken"))
            except Exception:
                pass
            # title (first QLabel added in layout)
            try:
                # title is the first widget in the main layout
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
                text += f"<br><b>{_('Todesfälle (Kampf):')}</b><br>"
                for species, count in stats.get("deaths", {}).get("combat", {}).items():
                    text += f"• {species}: {count}<br>"
                text += f"<br><b>{_('Todesfälle (Verhungert):')}</b><br>"
                for species, count in (
                    stats.get("deaths", {}).get("starvation", {}).items()
                ):
                    text += f"• {species}: {count}<br>"
                text += f"<br><b>{_('Todesfälle (Temperatur):')}</b><br>"
                for species, count in (
                    stats.get("deaths", {}).get("temperature", {}).items()
                ):
                    text += f"• {species}: {count}<br>"
                text += (
                    f"<br><b>{_('Maximale Clans:')}</b> {stats.get('max_clans', 0)}<br>"
                )
                text += f"<b>{_('Futterplätze:')}</b> {stats.get('food_places', 0)}"
                if hasattr(self, "_stats_text") and self._stats_text is not None:
                    try:
                        self._stats_text.setText(text)
                    except Exception:
                        pass
            except Exception:
                pass

        except Exception:
            pass

    def _switch_stats_page(self, idx: int):
        """Switch the right-side stacked widget between Stats and Randomizers."""
        try:
            if hasattr(self, "_right_stack") and self._right_stack is not None:
                self._right_stack.setCurrentIndex(int(idx))
            # update button checked states
            self.btn_view_stats.setChecked(idx == 0)
            self.btn_view_random.setChecked(idx == 1)
        except Exception:
            pass


class LogDialog(QDialog):
    """Popup dialog to display simulation logs."""

    def __init__(self, log_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Simulation Logs"))
        self.setModal(False)
        self.resize(600, 400)

        # Set dark theme
        self.setStyleSheet("background-color: #1a1a1a; color: #ffffff;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel(_("Simulation Logs"))
        title_font = QFont("Minecraft", 14)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        title.setFont(title_font)
        title.setStyleSheet("color: #ffffff; font-weight: bold;")
        layout.addWidget(title)

        # Text area with scroll (use QPlainTextEdit for performance)
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        text_font = QFont(LOG_FONT_FAMILY, LOG_FONT_SIZE)
        text_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.text_edit.setFont(text_font)
        self.text_edit.setStyleSheet(
            f"background-color: #2a2a2a; color: #ffffff; border: 1px solid #666666; font-family: {LOG_FONT_FAMILY}; font-size: {LOG_FONT_SIZE}px;"
        )
        # Enable word wrapping and scrolling
        self.text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # Populate plain text and attach highlighter for colorization
        self.text_edit.setPlainText(log_text)
        LogHighlighter(self.text_edit.document())
        layout.addWidget(self.text_edit)

        # Close button
        close_btn = QPushButton(_("Schließen"))
        close_btn_font = QFont("Minecraft", 12)
        close_btn_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        close_btn.setFont(close_btn_font)
        close_btn.setStyleSheet(
            "background-color: #444444; color: #ffffff; "
            "border: 2px solid #666666; padding: 5px;"
        )
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def colorize_logs(self, log_text):
        """Return plain log text. Coloring is handled by QSyntaxHighlighter."""
        if not log_text:
            return ""

        # Keep as plain text; LogHighlighter applies formats to the document.
        return log_text

    def update_log(self, log_text):
        """Update the log text in the dialog."""
        scrollbar = self.text_edit.verticalScrollBar()
        was_at_bottom = False
        if scrollbar is not None:
            was_at_bottom = (
                scrollbar.value() >= scrollbar.maximum() - 10
            )  # 10px threshold

        # Replace plain text; highlighter will reformat visually
        self.text_edit.setPlainText(self.colorize_logs(log_text))

        # Force scrollbar update
        self.text_edit.ensureCursorVisible()

        # Only auto-scroll if user was already at the bottom
        if scrollbar is not None and was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())


class SpeciesPanel(QWidget):
    """Species panel: subspecies controls."""

    def __init__(self, species_config, color_preset=None):
        super().__init__()
        self.color_preset = color_preset
        self.species_config = species_config
        self.species_checkboxes = {}
        self.loner_speed_sliders = {}
        self.clan_speed_sliders = {}
        self.member_sliders = {}
        self.member_value_labels = {}
        # Keep label widgets so we can update their text on language change
        self.loner_speed_labels = {}
        self.clan_speed_labels = {}
        self.member_labels = {}

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(12)

        # Title
        self.title = QLabel(_("Spezies"))
        title_font = QFont("Minecraft", 15, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.title.setFont(title_font)
        layout.addWidget(self.title)

        # Create entry for each species
        species_names = {
            "Icefang": "Icefang",
            "Crushed_Critters": "Crushed Critters",
            "Spores": "Spores",
            "The_Corrupted": "The Corrupted",
        }

        for species_id, display_name in species_names.items():
            # Checkbox for enable/disable with custom icons
            unchecked_path = str(get_static_path("ui/Checkbox_unchecked.png"))
            checked_path = str(get_static_path("ui/Checkbox_checked.png"))
            # Debug logging removed: debug_log does not exist
            print(
                f"DEBUG: Checkbox unchecked: {unchecked_path}, exists: {Path(unchecked_path).exists()}"
            )

            checkbox = CustomCheckBox(display_name, unchecked_path, checked_path)
            checkbox_font = QFont("Minecraft", 12)
            checkbox_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
            checkbox.setFont(checkbox_font)
            checkbox.setChecked(True)
            self.species_checkboxes[species_id] = checkbox
            layout.addWidget(checkbox)

            # Loner speed slider
            loner_speed_layout = QHBoxLayout()
            loner_speed_layout.setSpacing(5)

            loner_speed_label = QLabel(_("Loner Speed:"))
            loner_speed_label_font = QFont("Minecraft", 11)
            loner_speed_label_font.setLetterSpacing(
                QFont.SpacingType.AbsoluteSpacing, 1
            )
            loner_speed_label.setFont(loner_speed_label_font)
            loner_speed_label.setFixedWidth(110)
            self.loner_speed_labels[species_id] = loner_speed_label
            loner_speed_layout.addWidget(loner_speed_label)

            loner_slider = QSlider(Qt.Orientation.Horizontal)
            loner_slider.setMinimum(1)
            loner_slider.setMaximum(10)
            loner_slider.setValue(5)
            self.loner_speed_sliders[species_id] = loner_slider
            loner_speed_layout.addWidget(loner_slider)

            layout.addLayout(loner_speed_layout)

            # Clan speed slider
            clan_speed_layout = QHBoxLayout()
            clan_speed_layout.setSpacing(5)

            clan_speed_label = QLabel(_("Clan Speed:"))
            clan_speed_label_font = QFont("Minecraft", 11)
            clan_speed_label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
            clan_speed_label.setFont(clan_speed_label_font)
            clan_speed_label.setFixedWidth(110)
            self.clan_speed_labels[species_id] = clan_speed_label
            clan_speed_layout.addWidget(clan_speed_label)

            clan_slider = QSlider(Qt.Orientation.Horizontal)
            clan_slider.setMinimum(1)
            clan_slider.setMaximum(10)
            clan_slider.setValue(5)
            self.clan_speed_sliders[species_id] = clan_slider
            clan_speed_layout.addWidget(clan_slider)

            layout.addLayout(clan_speed_layout)

            # Member slider with value display
            member_layout = QHBoxLayout()
            member_layout.setSpacing(5)

            member_label = QLabel(_("Mitglieder:"))
            member_label_font = QFont("Minecraft", 11)
            member_label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
            member_label.setFont(member_label_font)
            member_label.setFixedWidth(110)
            self.member_labels[species_id] = member_label
            member_layout.addWidget(member_label)

            member_value_label = QLabel("5")
            member_value_font = QFont("Minecraft", 11)
            member_value_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
            member_value_label.setFont(member_value_font)
            member_value_label.setFixedWidth(30)
            member_value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.member_value_labels[species_id] = member_value_label
            member_layout.addWidget(member_value_label)

            member_slider = QSlider(Qt.Orientation.Horizontal)
            member_slider.setMinimum(0)
            member_slider.setMaximum(20)
            member_slider.setValue(5)
            member_slider.valueChanged.connect(
                lambda value, sid=species_id: self.update_member_value(sid, value)
            )
            self.member_sliders[species_id] = member_slider
            member_layout.addWidget(member_slider)

            layout.addLayout(member_layout)

            # Add spacing between species
            layout.addSpacing(25)

        layout.addStretch()
        self.setLayout(layout)
        self.update_theme(self.color_preset)
        try:
            from frontend.i18n import register_language_listener

            register_language_listener(self.update_language)
        except Exception:
            pass

    # Note: EnvironmentPanel handles its own language updates.

    def update_language(self):
        """Update UI texts when language changes."""
        try:
            from frontend.i18n import _

            if hasattr(self, "title"):
                self.title.setText(_("Spezies"))
            # species subtitle removed
            # Update per-species labels (loner/clan/member)
            try:
                for sid in self.species_checkboxes.keys():
                    if sid in self.loner_speed_labels:
                        self.loner_speed_labels[sid].setText(_("Loner Speed:"))
                    if sid in self.clan_speed_labels:
                        self.clan_speed_labels[sid].setText(_("Clan Speed:"))
                    if sid in self.member_labels:
                        self.member_labels[sid].setText(_("Mitglieder:"))
            except Exception:
                pass
        except Exception:
            pass

    def update_member_value(self, species_id, value):
        """Update the member value label when slider changes."""
        if species_id in self.member_value_labels:
            self.member_value_labels[species_id].setText(str(value))

    def get_enabled_species_populations(self):
        """Get populations for enabled species based on member sliders."""
        populations = {}
        for species_id, checkbox in self.species_checkboxes.items():
            if checkbox.isChecked():
                populations[species_id] = self.member_sliders[species_id].value()
        return populations

    def update_theme(self, preset):
        """Update inline styles for the species panel."""
        self.color_preset = preset
        bg = preset.get_color("bg_primary") if preset else "#1a1a1a"
        border = preset.get_color("border_light") if preset else "#666666"
        text = preset.get_color("text_primary") if preset else "#ffffff"
        accent = preset.get_color("accent_primary") if preset else "#cc0000"
        # Additional fallbacks used below to avoid calling preset.get_color when preset is None
        bg_tertiary = preset.get_color("bg_tertiary") if preset else "#333333"
        text_secondary = preset.get_color("text_secondary") if preset else "#cccccc"

        # Panel background (no border for cleaner look)
        self.setStyleSheet(f"background-color: {bg}; border: none;")

        # Text elements
        self.title.setStyleSheet(f"color: {text}; background: transparent;")
        # species subtitle removed; no styling required

        # Style checkboxes and sliders
        for checkbox in self.species_checkboxes.values():
            checkbox.setStyleSheet(
                f"""
                QCheckBox {{
                    color: {text};
                    background: transparent;
                    spacing: 8px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: none;
                    background: transparent;
                }}
                QCheckBox::indicator:checked {{
                    background: transparent;
                }}
            """
            )

        # Keep the slider groove visible (thin line) but transparent container backgrounds
        slider_style = f"""
            QSlider {{
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {border};
                height: 2px;
                background: transparent;
                border-radius: 1px;
            }}
            QSlider::sub-page:horizontal, QSlider::add-page:horizontal {{
                background: transparent;
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                border: none;
                width: 12px;
                height: 12px;
                margin: -5px 0;
                border-radius: 2px;
            }}
        """

        for slider in self.loner_speed_sliders.values():
            slider.setStyleSheet(slider_style)

        for slider in self.clan_speed_sliders.values():
            slider.setStyleSheet(slider_style)

        for slider in self.member_sliders.values():
            slider.setStyleSheet(slider_style)

        # Make sure labels and value boxes have transparent backgrounds
        try:
            for sid, lbl in self.loner_speed_labels.items():
                lbl.setStyleSheet(f"color: {text}; background: transparent;")
            for sid, lbl in self.clan_speed_labels.items():
                lbl.setStyleSheet(f"color: {text}; background: transparent;")
            for sid, lbl in self.member_labels.items():
                lbl.setStyleSheet(f"color: {text}; background: transparent;")
            for sid, val in self.member_value_labels.items():
                val.setStyleSheet(f"color: {text}; background: transparent;")
        except Exception:
            pass


class EnvironmentPanel(QWidget):
    """Region panel: environment controls."""

    def __init__(
        self,
        color_preset=None,
        map_widget=None,
        species_config=None,
        species_panel=None,
    ):
        super().__init__()
        self.color_preset = color_preset
        self.map_widget = map_widget  # Reference to map widget for updating background
        self.species_config = species_config  # Reference to species config
        self.species_panel = (
            species_panel  # Reference to species panel for checkbox control
        )
        self.current_food_level = 5  # Default food level (1-10)

        # Load region config for temperature ranges
        self.region_config = {}
        try:
            region_json_path = get_static_path("data/region.json")
            with open(region_json_path, "r") as f:
                self.region_config = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load region.json: {e}")

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Title
        self.title = QLabel(_("Region"))
        title_font = QFont("Minecraft", 15, QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.title.setFont(title_font)
        layout.addWidget(self.title)

        # Region Selection (subtitle removed; only title + combo)

        from PyQt6.QtWidgets import QComboBox

        self.region_combo = QComboBox()
        self.region_combo.addItems(
            ["Snowy Abyss", "Wasteland", "Evergreen Forest", "Corrupted Caves"]
        )
        self.region_combo.setFixedHeight(30)
        self.region_combo.currentTextChanged.connect(self.on_region_changed)
        layout.addWidget(self.region_combo)

        # Store region name to key mapping
        self.region_name_to_key = {
            "Snowy Abyss": "Snowy_Abyss",
            "Wasteland": "Wasteland",
            "Evergreen Forest": "Evergreen_Forest",
            "Corrupted Caves": "Corrupted_Caves",
        }

        # Temperature Section
        self.temp_label = QLabel(_("Temperatur:"))
        temp_label_font = QFont("Minecraft", 12)
        temp_label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.temp_label.setFont(temp_label_font)
        layout.addWidget(self.temp_label)

        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(-50)
        self.temp_slider.setMaximum(50)
        self.temp_slider.setValue(20)
        layout.addWidget(self.temp_slider)

        self.temp_value_label = QLabel(_("Temp: 20 C°"))
        temp_value_font = QFont("Minecraft", 11)
        temp_value_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.temp_value_label.setFont(temp_value_font)
        self.temp_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp_slider.valueChanged.connect(self.on_temp_value_changed)
        layout.addWidget(self.temp_value_label)

        # Set initial temperature range based on default region (Snowy Abyss)
        self.update_temperature_range("Snowy Abyss")

        # Food Section
        self.food_label_title = QLabel(_("Nahrung:"))
        food_title_font = QFont("Minecraft", 12)
        food_title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.food_label_title.setFont(food_title_font)
        layout.addWidget(self.food_label_title)

        # Anzahl Nahrungsplätze
        # Food Level Label (missing initialization fix)
        self.food_label = QLabel("1/10")
        food_label_font = QFont("Minecraft", 11)
        food_label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.food_label.setFont(food_label_font)
        layout.addWidget(self.food_label)
        self.food_places_label = QLabel(_("Nahrungsplätze: 5"))
        food_places_font = QFont("Minecraft", 11)
        food_places_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.food_places_label.setFont(food_places_font)
        layout.addWidget(self.food_places_label)

        self.food_places_slider = QSlider(Qt.Orientation.Horizontal)
        self.food_places_slider.setMinimum(1)
        self.food_places_slider.setMaximum(10)
        self.food_places_slider.setValue(5)
        self.food_places_slider.valueChanged.connect(
            lambda v: self.food_places_label.setText(
                _("Nahrungsplätze: {v}").format(v=v)
            )
        )
        layout.addWidget(self.food_places_slider)

        # Nahrungsmenge pro Platz
        self.food_amount_label = QLabel(_("Nahrungsmenge: 50"))
        food_amount_font = QFont("Minecraft", 11)
        food_amount_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.food_amount_label.setFont(food_amount_font)
        layout.addWidget(self.food_amount_label)

        self.food_amount_slider = QSlider(Qt.Orientation.Horizontal)
        self.food_amount_slider.setMinimum(10)
        self.food_amount_slider.setMaximum(200)
        self.food_amount_slider.setValue(50)
        self.food_amount_slider.valueChanged.connect(
            lambda v: self.food_amount_label.setText(
                _("Nahrungsmenge: {v}").format(v=v)
            )
        )
        layout.addWidget(self.food_amount_slider)

        # Day/Night Section
        self.day_night_label = QLabel(_("Tag - Nacht:"))
        day_night_label_font = QFont("Minecraft", 12)
        day_night_label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.day_night_label.setFont(day_night_label_font)
        layout.addWidget(self.day_night_label)

        day_night_layout = QHBoxLayout()
        day_night_layout.setSpacing(5)

        day_btn = QPushButton(_("Tag"))
        day_btn_font = QFont("Minecraft", 11)
        day_btn_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        day_btn.setFont(day_btn_font)
        day_btn.setFixedHeight(30)
        day_btn.setCheckable(True)
        day_btn.setChecked(True)
        day_btn.clicked.connect(lambda: self.on_day_night_toggle(True))
        day_night_layout.addWidget(day_btn)

        night_btn = QPushButton(_("Nacht"))
        night_btn_font = QFont("Minecraft", 11)
        night_btn_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        night_btn.setFont(night_btn_font)
        night_btn.setFixedHeight(30)
        night_btn.setCheckable(True)
        night_btn.clicked.connect(lambda: self.on_day_night_toggle(False))
        day_night_layout.addWidget(night_btn)

        self.day_btn = day_btn
        self.night_btn = night_btn
        self.start_is_day = True  # Default: Start bei Tag

        layout.addLayout(day_night_layout)

        layout.addStretch()

        self.setLayout(layout)
        self.update_theme(self.color_preset)
        try:
            from frontend.i18n import register_language_listener

            register_language_listener(self.update_language)
        except Exception:
            pass

    def on_day_night_toggle(self, is_day):
        """Toggle between day and night mode."""
        self.start_is_day = is_day
        if is_day:
            self.day_btn.setChecked(True)
            self.night_btn.setChecked(False)
        else:
            self.day_btn.setChecked(False)
            self.night_btn.setChecked(True)

    def on_region_changed(self, region_name):
        """Called when region selection changes."""
        if self.map_widget:
            self.map_widget.set_region(region_name)
        # Update temperature slider range based on region
        self.update_temperature_range(region_name)
        # Update species checkboxes based on region temperature compatibility
        self.update_species_compatibility(region_name)

    def update_temperature_range(self, region_name):
        """Update temperature slider min/max based on selected region."""
        # Convert display name to JSON key
        region_key = self.region_name_to_key.get(region_name, "Wasteland")

        if region_key in self.region_config:
            region_data = self.region_config[region_key]
            min_temp = region_data.get("min_temp", -50)
            max_temp = region_data.get("max_temp", 50)

            # Update slider range
            self.temp_slider.setMinimum(min_temp)
            self.temp_slider.setMaximum(max_temp)

            # Set value to middle of range
            mid_temp = (min_temp + max_temp) // 2
            self.temp_slider.setValue(mid_temp)

            # Update label with range info
            # Use translatable template for temperature display
            try:
                from frontend.i18n import _

                self.temp_value_label.setText(
                    _("Temp: {value} C° ({min} bis {max})").format(
                        value=mid_temp, min=min_temp, max=max_temp
                    )
                )
            except Exception:
                self.temp_value_label.setText(
                    f"Temp: {mid_temp} C° ({min_temp} bis {max_temp})"
                )

    def on_temp_value_changed(self, value):
        """Update label when temperature slider value changes."""
        min_temp = self.temp_slider.minimum()
        max_temp = self.temp_slider.maximum()
        try:
            from frontend.i18n import _

            self.temp_value_label.setText(
                _("Temp: {value} C° ({min} bis {max})").format(
                    value=value, min=min_temp, max=max_temp
                )
            )
        except Exception:
            self.temp_value_label.setText(
                f"Temp: {value} C° ({min_temp} bis {max_temp})"
            )
        # Update species compatibility based on selected temperature
        self.update_species_compatibility_by_temp(value)

    def update_species_compatibility(self, region_name):
        """Enable/disable species checkboxes based on region temperature compatibility."""
        if not self.species_panel or not self.species_config:
            return

        # Get region temperature range
        region_key = self.region_name_to_key.get(region_name, "Wasteland")
        if region_key not in self.region_config:
            return

        region_data = self.region_config[region_key]
        region_min_temp = region_data.get("min_temp", -50)
        region_max_temp = region_data.get("max_temp", 50)

        # Check each species
        for species_id, checkbox in self.species_panel.species_checkboxes.items():
            if species_id in self.species_config:
                species_data = self.species_config[species_id]
                species_min_temp = species_data.get("min_survival_temp", -100)
                species_max_temp = species_data.get("max_survival_temp", 100)

                # Check if species can survive in this region's temperature range
                # Species can survive if there's ANY overlap between region temp and survival temp
                can_survive = not (
                    region_max_temp < species_min_temp
                    or region_min_temp > species_max_temp
                )

                if not can_survive:
                    # Disable and uncheck species that can't survive
                    checkbox.setChecked(False)
                    checkbox.setEnabled(False)
                    checkbox.setStyleSheet(checkbox.styleSheet() + " color: #666666;")
                else:
                    # Enable species that can survive
                    checkbox.setEnabled(True)
                    # Reset style (will be updated by update_theme)

    def update_species_compatibility_by_temp(self, temperature):
        """Enable/disable species checkboxes based on specific temperature."""
        if not self.species_panel or not self.species_config:
            return

        # Check each species
        for species_id, checkbox in self.species_panel.species_checkboxes.items():
            if species_id in self.species_config:
                species_data = self.species_config[species_id]
                species_min_temp = species_data.get("min_survival_temp", -100)
                species_max_temp = species_data.get("max_survival_temp", 100)

                # Check if species can survive at this specific temperature
                can_survive = species_min_temp <= temperature <= species_max_temp

                if not can_survive:
                    # Disable and uncheck species that can't survive
                    checkbox.setChecked(False)
                    checkbox.setEnabled(False)
                    checkbox.setStyleSheet(checkbox.styleSheet() + " color: #666666;")
                else:
                    # Enable and auto-check species that can survive
                    checkbox.setEnabled(True)
                    checkbox.setChecked(True)
                    # Reset style (will be updated by update_theme)

    def set_species_panel(self, species_panel):
        """Set reference to species panel after it's created."""
        self.species_panel = species_panel

    def increase_food(self):
        """Increase food level."""
        self.current_food_level = min(10, self.current_food_level + 1)
        self.food_label.setText(f"{self.current_food_level}/10")

    def decrease_food(self):
        """Decrease food level."""
        self.current_food_level = max(1, self.current_food_level - 1)
        self.food_label.setText(f"{self.current_food_level}/10")

    def get_selected_region(self):
        """Get currently selected region."""
        return self.region_combo.currentText()

    def get_temperature(self):
        """Get current temperature value."""
        return self.temp_slider.value()

    def get_food_places(self):
        """Get number of food places."""
        return self.food_places_slider.value()

    def get_food_amount(self):
        """Get food amount per place."""
        return self.food_amount_slider.value()

    def get_is_day(self):
        """Get day/night state."""
        return self.day_btn.isChecked()

    def set_controls_enabled(self, enabled):
        """Enable/disable region selection (only before simulation starts)."""
        self.region_combo.setEnabled(enabled)

    def update_theme(self, preset):
        """Update inline styles for the environment panel."""
        self.color_preset = preset
        bg = preset.get_color("bg_primary") if preset else "#1a1a1a"
        border = preset.get_color("border_light") if preset else "#666666"
        text = preset.get_color("text_primary") if preset else "#ffffff"
        accent = preset.get_color("accent_primary") if preset else "#cc0000"
        bg_tertiary = preset.get_color("bg_tertiary") if preset else "#333333"
        text_secondary = preset.get_color("text_secondary") if preset else "#cccccc"

        # Panel background (no border for cleaner look)
        self.setStyleSheet(f"background-color: {bg}; border: none;")

        # Text elements
        self.title.setStyleSheet(f"color: {text}; background: transparent;")
        # region subtitle removed; no styling required
        self.temp_label.setStyleSheet(
            f"color: {text_secondary}; background: transparent;"
        )
        self.temp_value_label.setStyleSheet(f"color: {text}; background: transparent;")
        self.food_label_title.setStyleSheet(
            f"color: {text_secondary}; background: transparent;"
        )
        self.food_places_label.setStyleSheet(f"color: {text}; background: transparent;")
        self.food_amount_label.setStyleSheet(f"color: {text}; background: transparent;")
        self.day_night_label.setStyleSheet(
            f"color: {text_secondary}; background: transparent;"
        )

        # Style sliders (temp, food_places, food_amount)
        slider_style = f"""
            QSlider {{
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {border};
                height: 2px;
                background: transparent;
                border-radius: 1px;
            }}
            QSlider::sub-page:horizontal, QSlider::add-page:horizontal {{
                background: transparent;
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                border: none;
                width: 12px;
                height: 12px;
                margin: -5px 0;
                border-radius: 2px;
            }}
        """
        self.temp_slider.setStyleSheet(slider_style)
        self.food_places_slider.setStyleSheet(slider_style)
        self.food_amount_slider.setStyleSheet(
            f"""
            QSlider {{
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {border};
                height: 2px;
                background: transparent;
                border-radius: 1px;
            }}
            QSlider::sub-page:horizontal, QSlider::add-page:horizontal {{
                background: transparent;
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                border: none;
                width: 12px;
                height: 12px;
                margin: -5px 0;
                border-radius: 2px;
            }}
        """
        )

        # Style combobox
        combo_style = f"""
            QComboBox {{
                background-color: {bg_tertiary};
                color: {text};
                border: 1px solid {border};
                padding: 5px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {text};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {bg_tertiary};
                color: {text};
                selection-background-color: {accent};
            }}
        """
        self.region_combo.setStyleSheet(combo_style)

        # Style buttons
        button_style = f"""
            QPushButton {{
                background-color: {bg_tertiary};
                color: {text};
                border: none;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {accent};
            }}
            QPushButton:checked {{
                background-color: {accent};
            }}
        """
        self.day_btn.setStyleSheet(button_style)
        self.night_btn.setStyleSheet(button_style)
        # Ensure labels and small display boxes are transparent to avoid dark boxes
        try:
            if hasattr(self, "temp_label") and self.temp_label is not None:
                self.temp_label.setStyleSheet(
                    f"color: {text_secondary}; background: transparent;"
                )
            if hasattr(self, "temp_value_label") and self.temp_value_label is not None:
                self.temp_value_label.setStyleSheet(
                    f"color: {text}; background: transparent;"
                )
            if hasattr(self, "food_label") and self.food_label is not None:
                self.food_label.setStyleSheet(
                    f"color: {text}; background: transparent;"
                )
            if (
                hasattr(self, "food_places_label")
                and self.food_places_label is not None
            ):
                self.food_places_label.setStyleSheet(
                    f"color: {text}; background: transparent;"
                )
            if (
                hasattr(self, "food_amount_label")
                and self.food_amount_label is not None
            ):
                self.food_amount_label.setStyleSheet(
                    f"color: {text}; background: transparent;"
                )
        except Exception:
            pass

    def update_language(self):
        """Update UI texts for environment panel when language changes."""
        try:
            from frontend.i18n import _

            if hasattr(self, "title"):
                self.title.setText(_("Region"))
            # Region subtitle removed; nothing to update here
            if hasattr(self, "temp_label"):
                self.temp_label.setText(_("Temperatur:"))
            if hasattr(self, "food_label_title"):
                self.food_label_title.setText(_("Nahrung:"))
            # Update dynamic numeric labels to use translated templates
            try:
                if hasattr(self, "temp_slider") and hasattr(self, "temp_value_label"):
                    # Recompute temp display based on current slider value
                    min_temp = self.temp_slider.minimum()
                    max_temp = self.temp_slider.maximum()
                    cur = self.temp_slider.value()
                    self.temp_value_label.setText(
                        _("Temp: {value} C° ({min} bis {max})").format(
                            value=cur, min=min_temp, max=max_temp
                        )
                    )
            except Exception:
                pass
            try:
                if hasattr(self, "food_places_label") and hasattr(
                    self, "food_places_slider"
                ):
                    v = self.food_places_slider.value()
                    self.food_places_label.setText(_("Nahrungsplätze: {v}").format(v=v))
            except Exception:
                pass
            try:
                if hasattr(self, "food_amount_label") and hasattr(
                    self, "food_amount_slider"
                ):
                    v = self.food_amount_slider.value()
                    self.food_amount_label.setText(_("Nahrungsmenge: {v}").format(v=v))
            except Exception:
                pass
            if hasattr(self, "day_night_label"):
                self.day_night_label.setText(_("Tag - Nacht:"))
            # Update the individual day/night buttons if they exist
            try:
                if hasattr(self, "day_btn"):
                    self.day_btn.setText(_("Tag"))
                if hasattr(self, "night_btn"):
                    self.night_btn.setText(_("Nacht"))
            except Exception:
                pass
            # Update day/night buttons in EnvironmentPanel if present
            try:
                if hasattr(self, "environment_panel"):
                    if hasattr(self.environment_panel, "day_btn"):
                        self.environment_panel.day_btn.setText(_("Tag"))
                    if hasattr(self.environment_panel, "night_btn"):
                        self.environment_panel.night_btn.setText(_("Nacht"))
            except Exception:
                pass

        except Exception:
            pass


class SimulationScreen(QWidget):
    def show_final_stats(self):
        """Show final statistics dialog and save stats for later viewing."""
        if self.sim_model:
            stats = self.sim_model.get_final_stats()
            self.last_stats = stats  # Save stats for later
            dialog = StatsDialog(stats, self)
            dialog.exec()

    def show_previous_stats(self):
        """Show stats from the previous simulation if available."""
        if hasattr(self, "last_stats") and self.last_stats:
            dialog = StatsDialog(self.last_stats, self)
            dialog.exec()
        else:
            from PyQt6.QtWidgets import QMessageBox

            try:
                from frontend.i18n import _

                QMessageBox.information(
                    self,
                    _("Keine Statistik"),
                    _("Es sind keine Statistiken der vorherigen Simulation verfügbar."),
                )
            except Exception:
                QMessageBox.information(
                    self,
                    "Keine Statistik",
                    "Es sind keine Statistiken der vorherigen Simulation verfügbar.",
                )

    """Main simulation screen."""

    def __init__(self, go_to_start_callback, color_preset=None):
        super().__init__()
        self.go_to_start = go_to_start_callback
        self.color_preset = color_preset
        self.is_running = False
        # Add missing speed value labels
        self.loner_speed_value_label = QLabel("1.0x")
        self.clan_speed_value_label = QLabel("1.0x")
        speed_value_font = QFont("Minecraft", 10)
        speed_value_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.loner_speed_value_label.setFont(speed_value_font)
        self.clan_speed_value_label.setFont(speed_value_font)
        self.sim_model = None
        self.update_timer = None
        self.animation_timer = None
        self.last_stats = None  # Holds stats from the previous simulation

        self.log_dialog = None
        self.time_step = 0
        self.log_expanded = False  # Track log expansion state
        self.simulation_time = 0  # Time in seconds
        self.max_simulation_time = 300  # 5 minutes = 300 seconds
        self.simulation_speed = 1  # Speed multiplier (1x, 2x, 5x)
        self.population_data = {}  # Store population history for live graph
        self.live_graph_widget = None  # Widget for live graph, initialized later
        # Throttle live graph updates to avoid UI overwork (seconds)
        self._last_graph_update = 0.0
        self._graph_update_interval = 0.5

        # Load species config
        json_path = get_static_path("data/species.json")
        # Debug logging removed: debug_log does not exist
        print(f"DEBUG: species.json path: {json_path}")
        print(f"DEBUG: species.json exists: {json_path.exists()}")
        try:
            with open(json_path, "r") as f:
                self.species_config = json.load(f)
        except FileNotFoundError:
            self.species_config = {}
            # Debug logging removed: debug_log does not exist
            print(f"Warning: Could not load species.json from {json_path}")

        # Don't initialize simulation model here - will be created on first start
        # self.sim_model is already set to None above

        self.init_ui()
        try:
            from frontend.i18n import register_language_listener

            register_language_listener(self.update_language)
        except Exception:
            pass

    def init_ui(self):
        """Initialize UI."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Top bar: back button
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        btn_back = QPushButton(_("← Back"))
        btn_back_font = QFont("Minecraft", 12)
        btn_back_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        btn_back.setFont(btn_back_font)
        btn_back.setFixedWidth(100)
        btn_back.clicked.connect(self.on_back)
        top_bar.addWidget(btn_back)

        top_bar.addStretch()

        btn_exit = QPushButton(_("Exit"))
        btn_exit_font = QFont("Minecraft", 12)
        btn_exit_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        btn_exit.setFont(btn_exit_font)
        btn_exit.setFixedWidth(100)
        btn_exit.clicked.connect(self.on_exit)
        top_bar.addWidget(btn_exit)

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
        self.map_widget.setMinimumSize(600, 400)  # Minimum size for usability
        map_layout.addWidget(self.map_widget)

        left_layout.addWidget(self.map_frame)
        content_splitter.addWidget(left_column)

        # Right column: Settings and controls (25%)
        right_column = QFrame()
        right_column.setMinimumWidth(300)
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
        self.panel_stack.setMinimumHeight(400)

        # Create panels
        self.species_panel = SpeciesPanel(self.species_config, self.color_preset)
        self.panel_stack.addWidget(self.species_panel)  # Index 0

        self.environment_panel = EnvironmentPanel(
            self.color_preset, self.map_widget, self.species_config, self.species_panel
        )
        self.panel_stack.addWidget(self.environment_panel)  # Index 1

        # Initialize species compatibility for default region and temperature
        self.environment_panel.update_species_compatibility("Snowy Abyss")
        # Also check with initial temperature value
        initial_temp = self.environment_panel.get_temperature()
        self.environment_panel.update_species_compatibility_by_temp(initial_temp)

        # Show region/environment panel by default
        self.panel_stack.setCurrentIndex(1)

        right_layout.addWidget(self.panel_stack)

        # Store log text in variable instead of label (use module-level `_`)
        try:
            self.log_text = _("Simulation bereit.")
        except Exception:
            self.log_text = "Simulation bereit."

        # Control section at bottom of right column
        right_layout.addSpacing(20)

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

        # Live graph area (shown during simulation)
        control_section = QWidget()
        control_layout = QVBoxLayout(control_section)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)
        # (All matplotlib axis configuration and plotting is handled in update_live_graph after the axis is created)
        # (spine styling for live_graph_ax is handled after creation in initialize_live_graph or update_live_graph)

        # (All grid configuration for live_graph_ax is handled after creation in initialize_live_graph or update_live_graph)

        # (Live graph widget and axis are initialized only when simulation starts)
        # (Do not reference self.live_graph_widget or self.live_graph_ax here)

        # Play/Pause and Stop Buttons
        play_controls_layout = QHBoxLayout()
        self.btn_play_pause = QPushButton("▶")
        play_font = QFont("Minecraft", 16)
        play_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_play_pause.setFont(play_font)
        self.btn_play_pause.setFixedHeight(40)
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        play_controls_layout.addWidget(self.btn_play_pause)

        self.btn_stop = QPushButton(_("Reset/Stop"))
        stop_font = QFont("Minecraft", 16)
        stop_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.btn_stop.setFont(stop_font)
        self.btn_stop.setFixedHeight(40)
        self.btn_stop.clicked.connect(self.stop_simulation)
        play_controls_layout.addWidget(self.btn_stop)
        play_controls_layout.addStretch()
        control_layout.addLayout(play_controls_layout)

        # Info display row with timer, day/night, and speed controls
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)

        # Timer display
        self.timer_label = QLabel("00:00")
        timer_font = QFont("Minecraft", 14)
        timer_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.timer_label.setFont(timer_font)
        self.timer_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(self.timer_label)

        # Day/Night indicator
        self.day_night_label = QLabel("☀️")
        day_night_font = QFont("Minecraft", 16)
        day_night_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.day_night_label.setFont(day_night_font)
        self.day_night_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(self.day_night_label)

        # Speed control buttons next to time
        speed_label = QLabel("Sim Speed:")
        speed_label_font = QFont("Minecraft", 9)
        speed_label_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        speed_label.setFont(speed_label_font)
        speed_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(speed_label)

        # Replace text speed buttons with image buttons from static/ui
        one_img = str(get_static_path("ui/one_times.png"))
        two_img = str(get_static_path("ui/two_times.png"))
        five_img = str(get_static_path("ui/five_times.png"))

        self.btn_speed_1x = CustomImageButton(one_img)
        self.btn_speed_1x.setChecked(True)
        self.btn_speed_1x.clicked.connect(lambda: self.set_speed(1))
        info_layout.addWidget(self.btn_speed_1x)

        self.btn_speed_2x = CustomImageButton(two_img)
        self.btn_speed_2x.clicked.connect(lambda: self.set_speed(2))
        info_layout.addWidget(self.btn_speed_2x)

        self.btn_speed_5x = CustomImageButton(five_img)
        self.btn_speed_5x.clicked.connect(lambda: self.set_speed(5))
        info_layout.addWidget(self.btn_speed_5x)

        info_layout.addStretch()
        control_layout.addLayout(info_layout)

        # Live info row
        live_info_layout = QHBoxLayout()
        live_info_layout.setSpacing(10)

        # Temperature display (live)
        self.live_temp_label = QLabel("🌡️ 0°C")
        live_temp_font = QFont("Minecraft", 11)
        live_temp_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.live_temp_label.setFont(live_temp_font)
        self.live_temp_label.setStyleSheet("color: #88ccff;")
        live_info_layout.addWidget(self.live_temp_label)

        # Day/Night indicator (live)
        self.live_day_night_label = QLabel(_("☀️ Tag"))
        live_dn_font = QFont("Minecraft", 11)
        live_dn_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.live_day_night_label.setFont(live_dn_font)
        self.live_day_night_label.setStyleSheet("color: #ffcc44;")
        live_info_layout.addWidget(self.live_day_night_label)
        live_info_layout.addStretch()
        control_layout.addLayout(live_info_layout)

        # Add control section to right column
        right_layout.addWidget(control_section)

        # Add graph container (for live graph)
        self.graph_container = QFrame()
        self.graph_container.setVisible(False)
        right_layout.addWidget(self.graph_container)

        right_layout.addStretch()

        # Add right column to splitter
        content_splitter.addWidget(right_column)

        # Set initial splitter sizes (75% / 25%)
        content_splitter.setSizes([7500, 2500])

        main_layout.addWidget(content_splitter)

        self.setLayout(main_layout)
        # Apply initial theme to inline-styled widgets
        self.update_theme(self.color_preset)

    def switch_sidebar_tab(self, tab_name):
        """Switch between Species and Region tabs."""
        if tab_name == "species":
            self.btn_species_tab.setChecked(True)
            self.btn_region_tab.setChecked(False)
            self.panel_stack.setCurrentIndex(0)  # Show species panel
        elif tab_name == "region":
            self.btn_species_tab.setChecked(False)
            self.btn_region_tab.setChecked(True)
            self.panel_stack.setCurrentIndex(1)  # Show region panel

    def update_theme(self, preset):
        """Update inline styles for the simulation screen and child panels."""
        self.color_preset = preset
        if not preset:
            return

        # Map frame: keep map background white but update border color
        map_border = preset.get_color("map_border")
        self.map_frame.setStyleSheet(
            f"background-color: #ffffff; border: 2px solid {map_border};"
        )

        # Species panel updates itself
        if hasattr(self, "species_panel") and self.species_panel:
            try:
                self.species_panel.update_theme(preset)
            except Exception:
                # Ignore theme update errors silently
                pass

        # Environment panel updates itself
        if hasattr(self, "environment_panel") and self.environment_panel:
            try:
                self.environment_panel.update_theme(preset)
            except Exception:
                pass

        # Style tab buttons
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

    def toggle_simulation(self):
        """Start/resume simulation."""
        if not self.is_running:
            # Nur beim ersten Start initialisieren (wenn kein Model existiert)
            if self.sim_model is None:
                # Deaktiviere Region-Auswahl
                self.environment_panel.set_controls_enabled(False)

                # Initialisiere Simulation
                self.sim_model = SimulationModel()
                populations = self.species_panel.get_enabled_species_populations()
                food_places = self.environment_panel.get_food_places()
                food_amount = self.environment_panel.get_food_amount()
                start_temp = self.environment_panel.get_temperature()
                start_is_day = self.environment_panel.get_is_day()
                region_display = self.environment_panel.get_selected_region()
                # Map display name to region key for backend
                region_key = self.environment_panel.region_name_to_key.get(
                    region_display, "Wasteland"
                )
                self.sim_model.setup(
                    self.species_config,
                    populations,
                    food_places,
                    food_amount,
                    start_temp,
                    start_is_day,
                    region_key,
                )

                # Set region background (still use display name for UI)
                self.map_widget.set_region(region_display)

                # Initialize population data for live graph
                self.population_data = {}
                for species_name in populations.keys():
                    self.population_data[species_name] = []

                # Hide tabs and stats/log buttons, show graph
                self.btn_region_tab.setVisible(False)
                self.btn_species_tab.setVisible(False)
                self.panel_stack.setVisible(False)
                self.stats_log_widget.setVisible(False)
                self.graph_container.setVisible(True)

                # Initialize graph if not already created
                if self.live_graph_widget is None:
                    self.initialize_live_graph()

            # Resume (oder Start)
            self.is_running = True
            self.btn_play_pause.setText("⏸")

            # Start Update-Timer with speed multiplier
            if not self.update_timer:
                self.update_timer = QTimer()
                self.update_timer.timeout.connect(self.update_simulation_with_speed)
            self.update_timer.start(100)

    def toggle_play_pause(self):
        """Toggle between play and pause."""
        if self.is_running:
            # Currently running, so pause
            if self.update_timer:
                self.update_timer.stop()
            self.is_running = False
            self.btn_play_pause.setText("▶")
            self.btn_play_pause.setStyleSheet(
                "background-color: #4CAF50; color: white;"
            )
            self.timer_label.setText(self.timer_label.text() + " ⏸")
        else:
            # Currently paused or not started, so play/start
            self.btn_play_pause.setStyleSheet("")
            # Remove pause symbol from timer if present
            timer_text = self.timer_label.text().replace(" ⏸", "")
            self.timer_label.setText(timer_text)
            self.toggle_simulation()

    def stop_simulation(self):
        """Stop and reset simulation."""
        show_stats = self.is_running and self.sim_model

        self.environment_panel.set_controls_enabled(True)

        if self.update_timer:
            self.update_timer.stop()
            self.update_timer = None

        self.is_running = False
        self.btn_play_pause.setText("▶")
        self.btn_play_pause.setStyleSheet("")
        self.time_step = 0
        self.simulation_time = 0

        # Save model reference for stats before clearing
        sim_model_for_stats = self.sim_model

        # Reset Model to None so it will be recreated on next start
        self.sim_model = None

        # Clear population data for live graph
        self.population_data = {}
        if self.live_graph_widget:
            self.update_live_graph()

        # Show tabs and stats/log buttons, hide graph
        self.btn_region_tab.setVisible(True)
        self.btn_species_tab.setVisible(True)
        self.panel_stack.setVisible(True)
        self.stats_log_widget.setVisible(True)
        self.graph_container.setVisible(False)

        # Show stats popup after everything is stopped/reset
        if show_stats and sim_model_for_stats:
            stats = sim_model_for_stats.get_final_stats()
            self.last_stats = stats
            dialog = StatsDialog(stats, self)
            dialog.exec()

    def set_speed(self, speed):
        """Set simulation speed multiplier."""
        self.simulation_speed = speed

        # Update button checked states
        self.btn_speed_1x.setChecked(speed == 1)
        self.btn_speed_2x.setChecked(speed == 2)
        self.btn_speed_5x.setChecked(speed == 5)

    def on_loner_speed_changed(self, value):
        """Handle loner speed slider change."""
        # Convert slider value (5-20) to multiplier (0.5-2.0)
        multiplier = value / 10.0
        self.loner_speed_value_label.setText(f"{multiplier:.1f}x")
        if self.sim_model:
            self.sim_model.set_loner_speed(multiplier)

    def on_clan_speed_changed(self, value):
        """Handle clan speed slider change."""
        # Convert slider value (5-20) to multiplier (0.5-2.0)
        multiplier = value / 10.0
        self.clan_speed_value_label.setText(f"{multiplier:.1f}x")
        if self.sim_model:
            self.sim_model.set_clan_speed(multiplier)

    def update_simulation_with_speed(self):
        """Update simulation multiple times based on speed setting."""
        for i in range(self.simulation_speed):
            is_last = i == self.simulation_speed - 1
            self.update_simulation(update_ui=is_last)

    def update_simulation(self, update_ui=True):
        """Step simulation und update display."""
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

            # Track simulation time (each step = 0.1 seconds)
            self.simulation_time = self.time_step * 0.1

            # Hard stop at max_simulation_time (5 minutes = 300s)
            if self.simulation_time >= self.max_simulation_time:
                self.add_log(
                    f"⏹️ Simulation endet nach {self.max_simulation_time} Sekunden."
                )
                self.stop_simulation()

            # --- Live graph and log update ---
            # Always use backend's population_history for up-to-date graph
            population_history = stats.get("population_history", {})
            if population_history:
                self.population_data = {
                    k: list(v) for k, v in population_history.items()
                }
            # Capture recent random draw samples from backend for distribution graph
            try:
                self.rnd_samples = data.get("rnd_samples", {})
            except Exception:
                self.rnd_samples = {}
            # Keep the latest instantaneous species counts for smoother live plotting
            try:
                self._latest_species_counts = stats.get("species_counts", {})
            except Exception:
                self._latest_species_counts = {}
            self.update_live_graph()

            # Append any generated logs to central log buffer using add_log helper
            # (some code paths expect add_log to exist)
            try:
                for line in logs:
                    # keep existing translation behavior when possible
                    try:
                        from frontend.i18n import _

                        self.add_log(_(line))
                    except Exception:
                        self.add_log(line)
            except Exception:
                # if logs isn't iterable or add_log missing, ignore
                pass

            # Update log text from backend logs (try to translate each line)
            logs = data.get("logs", [])
            if logs:
                try:
                    from frontend.i18n import _

                    self.log_text = "\n".join([_(l) for l in logs])
                except Exception:
                    self.log_text = "\n".join(logs)
                if self.log_dialog is not None and self.log_dialog.isVisible():
                    self.log_dialog.update_log(self.log_text)

            if update_ui:
                # Update timer display
                minutes = int(self.simulation_time // 60)
                seconds = int(self.simulation_time % 60)
                # Timer display (MM:SS) - same in all languages
                self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

                # Update day/night indicator
                is_day = data.get("is_day", True)
                self.day_night_label.setText("☀️" if is_day else "🌙")

                # Update live temperature display
                current_temp = stats.get("temperature", 0)
                temp_color = (
                    "#88ccff"
                    if current_temp < 0
                    else "#ffcc44" if current_temp > 25 else "#ffffff"
                )
                try:
                    from frontend.i18n import _

                    self.live_temp_label.setText(
                        _("🌡️ {val}°C").format(val=current_temp)
                    )
                except Exception:
                    self.live_temp_label.setText(f"🌡️ {current_temp}°C")
                self.live_temp_label.setStyleSheet(
                    f"color: {temp_color}; padding: 0 10px;"
                )

                # Update live day/night display
                is_day = stats.get("is_day", True)
                if is_day:
                    self.live_day_night_label.setText(_("☀️ Tag"))
                    self.live_day_night_label.setStyleSheet(
                        "color: #ffcc44; padding: 0 10px;"
                    )
                else:
                    self.live_day_night_label.setText(_("🌙 Nacht"))
                    self.live_day_night_label.setStyleSheet(
                        "color: #8888ff; padding: 0 10px;"
                    )

            # --- Stop simulation if all arach are dead ---
            # Check if all populations are zero
            if all(count == 0 for count in stats.get("species_counts", {}).values()):
                self.stop_simulation()

    def open_log_dialog(self):
        """Open log popup dialog."""
        if self.log_dialog is None or not self.log_dialog.isVisible():
            self.log_dialog = LogDialog(self.log_text, self)
            self.log_dialog.show()
        else:
            self.log_dialog.raise_()
            self.log_dialog.activateWindow()

    def on_stats(self):
        """Show previous simulation statistics if available."""
        self.show_previous_stats()

    def initialize_live_graph(self):
        """Initialize the live graph widget."""
        try:
            import pyqtgraph as pg

            # Prefer speed for live updates: disable antialiasing by default
            pg.setConfigOptions(antialias=False)

            # Create PlotWidget
            pw = pg.PlotWidget(background="#1a1a1a")
            pw.getPlotItem().showGrid(x=True, y=True, alpha=0.2)
            pw.getAxis("left").setTextPen("#ffffff")
            pw.getAxis("bottom").setTextPen("#ffffff")
            pw.setLabel("left", "Population", color="#ffffff", size="9pt")
            pw.setLabel("bottom", "Time (s)", color="#ffffff", size="9pt")

            # Lock aspect ratio to square and disable interactions
            try:
                vb = pw.getPlotItem().getViewBox()
                # Do not lock aspect ratio for the live plot to avoid widget
                # resizing jitter when axis labels/ticks change.
                # vb.setAspectLocked(True, ratio=1)
                vb.setMouseEnabled(False, False)
                try:
                    vb.setMenuEnabled(False)
                except Exception:
                    pass
            except Exception:
                pass

            # Allow live plot to grow taller (fixes vertically squished graphs)
            try:
                from PyQt6.QtWidgets import QSizePolicy

                # Give a reasonable minimum height but allow expansion so the
                # plot can use more vertical space instead of being compressed.
                # Make live graph slightly smaller to give room for distribution graph
                pw.setMinimumHeight(240)
                try:
                    # Remove any strict maximum so layouts may expand vertically
                    pw.setMaximumHeight(16777215)
                except Exception:
                    pass
                pw.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
            except Exception:
                pass

            # Prepare storage for curves (line style)
            # ensure curves dict exists
            self.live_graph_widget = pw
            self.live_graph_ax = None
            self.live_curves = {}
            # Cache last tick/max values to avoid updating axis layout every frame
            self._live_last_overall_max = None
            self._live_last_latest_time = None

            # Try to set pixel/font styling for axes and reserve axis sizes
            try:
                from PyQt6.QtGui import QFont

                left_axis = pw.getAxis("left")
                bottom_axis = pw.getAxis("bottom")
                left_axis.setStyle(tickFont=QFont("Minecraft", 9))
                bottom_axis.setStyle(tickFont=QFont("Minecraft", 9))
                # Reserve larger axis sizes so labels have room and the plot
                # area can expand vertically instead of compressing ticks.
                try:
                    # Reduce reserved left axis width for the live graph
                    left_axis.setWidth(60)
                except Exception:
                    pass
                try:
                    bottom_axis.setHeight(30)
                except Exception:
                    pass
            except Exception:
                pass

            # Ensure graph_container has a layout
            if self.graph_container.layout() is None:
                self.graph_container.setLayout(QVBoxLayout())
            layout = self.graph_container.layout()

            if layout is not None:
                layout.addWidget(self.live_graph_widget)

                if (
                    not hasattr(self, "graph_legend_label")
                    or self.graph_legend_label is None
                ):
                    from PyQt6.QtWidgets import QLabel

                    self.graph_legend_label = QLabel()
                    self.graph_legend_label.setStyleSheet(
                        "color: #ffffff; font-size: 11px; padding: 4px 0 0 0;"
                    )
                    self.graph_legend_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(self.graph_legend_label)

                if not hasattr(self, "log_display") or self.log_display is None:
                    from PyQt6.QtWidgets import QPlainTextEdit

                    self.log_display = QPlainTextEdit()
                    self.log_display.setReadOnly(True)
                    self.log_display.setStyleSheet(
                        f"background-color: #222; color: #fff; font-family: {LOG_FONT_FAMILY}; font-size: {LOG_FONT_SIZE}px; margin-top: 6px; border: none;"
                    )
                    self.log_display.setMinimumHeight(80)
                    LogHighlighter(self.log_display.document())
                    layout.addWidget(self.log_display)

            # Update graph immediately
            self.update_live_graph()

        except Exception:
            from PyQt6.QtWidgets import QLabel

            label = QLabel("Graph nicht verfügbar (pyqtgraph benötigt)")
            label.setStyleSheet("color: #ffffff; font-size: 12px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout = self.graph_container.layout()
            if layout is not None:
                layout.addWidget(label)

    def update_graph_legend(self):
        """Update the text legend below the graph."""
        colors = {
            "Icefang": "#cce6ff",
            "Crushed_Critters": "#cc9966",
            "Spores": "#66cc66",
            "The_Corrupted": "#cc66cc",
        }

        # Create colored text for each species
        legend_parts = []
        for species_name in sorted(self.population_data.keys()):
            color = colors.get(species_name, "#ffffff")
            # Replace underscores with spaces for display
            display_name = species_name.replace("_", " ")
            legend_parts.append(
                f'<span style="color: {color}; font-weight: bold;">{display_name}</span>'
            )

        if legend_parts:
            self.graph_legend_label.setText(" | ".join(legend_parts))
        else:
            self.graph_legend_label.setText("")

    def add_log(self, text: str):
        """Append a line to the centralized log buffer and update displays.

        Keeps the buffer reasonably sized and updates open log widgets.
        """
        try:
            if not hasattr(self, "log_text") or self.log_text is None:
                self.log_text = ""
            # keep single-line entries
            if text is None:
                return
            # append with newline
            if self.log_text:
                self.log_text = self.log_text + "\n" + str(text)
            else:
                self.log_text = str(text)

            # trim to last 1000 lines
            parts = self.log_text.split("\n")
            if len(parts) > 1000:
                parts = parts[-1000:]
                self.log_text = "\n".join(parts)

            # update live log display (if present)
            try:
                if hasattr(self, "log_display") and self.log_display is not None:
                    # show last 15 lines
                    self.log_display.setPlainText("\n".join(parts[-15:]))
                if self.log_dialog is not None and self.log_dialog.isVisible():
                    try:
                        self.log_dialog.update_log(self.log_text)
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def update_language(self):
        """Refresh UI texts when the global language changes."""
        try:
            from frontend.i18n import _

            # Main right-side tabs and controls
            if hasattr(self, "btn_region_tab"):
                self.btn_region_tab.setText(_("Region"))
            if hasattr(self, "btn_species_tab"):
                self.btn_species_tab.setText(_("Spezies"))
            if hasattr(self, "btn_stats"):
                self.btn_stats.setText(_("Stats"))
            if hasattr(self, "btn_log"):
                self.btn_log.setText(_("Log"))
            if hasattr(self, "btn_stop"):
                self.btn_stop.setText(_("Reset/Stop"))
            # Update top-bar navigation buttons
            if hasattr(self, "btn_back"):
                self.btn_back.setText(_("← Back"))
            if hasattr(self, "btn_exit"):
                self.btn_exit.setText(_("Exit"))

            # Day/night label: preserve icon and set localized text
            if hasattr(self, "live_day_night_label"):
                txt = self.live_day_night_label.text()
                if "☀️" in txt:
                    self.live_day_night_label.setText(_("☀️ Tag"))
                elif "🌙" in txt:
                    self.live_day_night_label.setText(_("🌙 Nacht"))

            # Notify nested panels
            if hasattr(self, "species_panel") and hasattr(
                self.species_panel, "update_language"
            ):
                try:
                    self.species_panel.update_language()
                except Exception:
                    pass
            if hasattr(self, "environment_panel") and hasattr(
                self.environment_panel, "update_language"
            ):
                try:
                    self.environment_panel.update_language()
                except Exception:
                    pass
        except Exception:
            pass

    def update_live_graph(self):
        """Update the live population graph with current data using matplotlib."""
        # Ensure PyQtGraph widget available
        if not hasattr(self, "live_graph_widget") or self.live_graph_widget is None:
            return

        # Throttle frequent calls to avoid UI lag; allow forced immediate by bypassing interval
        try:
            import time

            now = time.monotonic()
            if getattr(self, "_last_graph_update", 0.0) and (
                now - self._last_graph_update
                < getattr(self, "_graph_update_interval", 0.5)
            ):
                return
            self._last_graph_update = now
        except Exception:
            pass

        try:
            import pyqtgraph as pg

            colors = {
                "Icefang": "#cce6ff",
                "Crushed_Critters": "#cc9966",
                "Spores": "#66cc66",
                "The_Corrupted": "#cc66cc",
            }

            enabled_species = set()
            if hasattr(self, "species_panel") and hasattr(
                self.species_panel, "get_enabled_species_populations"
            ):
                enabled_species = set(
                    self.species_panel.get_enabled_species_populations().keys()
                )

            # Ensure live_curves dict exists
            if not hasattr(self, "live_curves"):
                self.live_curves = {}

            # Live window length in seconds
            LIVE_WINDOW = 10

            # Fast-skip: if the population lengths haven't changed since last update,
            # avoid re-plotting full curves (only update X range).
            try:
                snapshot = tuple(
                    (name, len(self.population_data.get(name, [])))
                    for name in sorted(self.population_data.keys())
                )
                if getattr(self, "_last_pop_snapshot", None) == snapshot:
                    # update X range quickly (no heavy redraw)
                    try:
                        vb = self.live_graph_widget.getPlotItem().getViewBox()
                        latest = 0
                        for h in self.population_data.values():
                            if h:
                                latest = max(latest, len(h) - 1)
                        start = max(0, latest - (LIVE_WINDOW - 1))
                        vb.setXRange(start, latest, padding=0)
                    except Exception:
                        pass
                    return
                self._last_pop_snapshot = snapshot
            except Exception:
                pass

            for species_name, history in self.population_data.items():
                if enabled_species and species_name not in enabled_species:
                    # hide curve if exists
                    if species_name in self.live_curves:
                        self.live_curves[species_name].setData([], [])
                    continue

                if not history:
                    continue

                # population_data is taken from backend population_history (1 entry = 1s)
                # For live plotting we only draw the most recent LIVE_WINDOW seconds
                # Use a local copy and append latest instantaneous count (if available)
                local_hist = list(history)
                try:
                    latest_counts = getattr(self, "_latest_species_counts", {}) or {}
                    if species_name in latest_counts and (
                        not local_hist
                        or int(local_hist[-1])
                        != int(latest_counts.get(species_name, 0))
                    ):
                        # append current instantaneous count so the graph reflects current state
                        local_hist.append(int(latest_counts.get(species_name, 0)))
                except Exception:
                    pass

                last_n = min(len(local_hist), LIVE_WINDOW)
                time_points = [
                    i for i in range(len(local_hist) - last_n, len(local_hist))
                ]
                display_history = local_hist[-last_n:]
                # Force integer populations for display (round then int)
                try:
                    display_history = [int(round(float(v))) for v in display_history]
                except Exception:
                    try:
                        display_history = [int(v) for v in display_history]
                    except Exception:
                        pass
                color = colors.get(species_name, "#ffffff")

                if species_name not in self.live_curves:
                    try:
                        pen = pg.mkPen(color=color, width=2)
                        curve = self.live_graph_widget.plot(
                            time_points, display_history, pen=pen
                        )
                        # Improve performance for streaming data
                        try:
                            curve.setClipToView(True)
                        except Exception:
                            pass
                        self.live_curves[species_name] = curve
                    except Exception:
                        pass
                else:
                    # Update existing curve/scatter with new data
                    try:
                        self.live_curves[species_name].setData(
                            time_points, display_history
                        )
                    except Exception:
                        pass

            # Ensure viewbox aspect lock and set moving window range
            try:
                vb = self.live_graph_widget.getPlotItem().getViewBox()
                # Moving window: show last LIVE_WINDOW seconds
                try:
                    latest = 0
                    for h in self.population_data.values():
                        if h:
                            latest = max(latest, len(h) - 1)
                    start = max(0, latest - (LIVE_WINDOW - 1))
                    vb.setXRange(start, latest, padding=0)
                except Exception:
                    pass
            except Exception:
                pass

            # Update Y-axis ticks/range only when max changes to avoid layout jitter
            try:
                left_axis = self.live_graph_widget.getAxis("left")
                overall_max = 0
                for h in self.population_data.values():
                    if h:
                        try:
                            overall_max = max(overall_max, int(round(max(h))))
                        except Exception:
                            overall_max = max(overall_max, int(max(h)))

                if overall_max != getattr(self, "_live_last_overall_max", None):
                    # Add 5 population units of headroom above current max
                    y_max = max(1, overall_max + 5)
                    # Limit number of Y ticks to avoid vertical crowding
                    try:
                        import math

                        step = max(1, int(math.ceil(y_max / 6.0)))
                    except Exception:
                        step = 1 if y_max < 10 else 2
                    ticks = [(i, str(i)) for i in range(0, y_max + 1, step)]
                    if ticks and ticks[-1][0] != y_max:
                        ticks.append((y_max, str(y_max)))
                    try:
                        left_axis.setTicks([ticks])
                    except Exception:
                        pass
                    try:
                        vb = self.live_graph_widget.getPlotItem().getViewBox()
                        vb.setYRange(0, max(1, y_max), padding=0)
                    except Exception:
                        pass
                    self._live_last_overall_max = overall_max
            except Exception:
                pass

            # Update bottom-axis ticks only when latest time changes
            try:
                bottom_axis = self.live_graph_widget.getAxis("bottom")
                latest = 0
                for h in self.population_data.values():
                    if h:
                        latest = max(latest, len(h) - 1)
                if latest != getattr(self, "_live_last_latest_time", None):
                    # Choose tick spacing based on overall time length so labels
                    # are not overcrowded. Use minutes for long runs.
                    if latest <= 20:
                        step = 1
                    elif latest <= 60:
                        step = 5
                    elif latest <= 180:
                        step = 30
                    else:
                        step = 60

                    ticks = []
                    for i in range(0, latest + 1, step):
                        if latest >= 60:
                            # show minutes only for long timelines
                            label = f"{int(i // 60)}m"
                        else:
                            label = str(i)
                        ticks.append((i, label))
                    if not ticks:
                        ticks = [(0, "0")]
                    try:
                        bottom_axis.setTicks([ticks])
                    except Exception:
                        pass
                    self._live_last_latest_time = latest
            except Exception:
                pass

            self.update_graph_legend()

        except Exception:
            # If pyqtgraph not available or fails, silently skip graph update
            return

        # Update log display under the graph
        if hasattr(self, "log_display") and self.log_display is not None:
            # Show the last 15 log lines (adjust as needed)
            log_lines = self.log_text.split("\n")[-15:]
            # Use plain text; LogHighlighter handles coloring
            self.log_display.setPlainText("\n".join(log_lines))

        # Update distribution graph (recent random draws)
        try:
            if (
                hasattr(self, "dist_graph_widget")
                and self.dist_graph_widget is not None
            ):
                samples = getattr(self, "rnd_samples", {}) or {}
                colors = {
                    "regen": "#66cc66",
                    "clan_growth": "#66aaff",
                    "loner_spawn": "#ffcc66",
                }

                # Ensure curves dict exists
                if not hasattr(self, "dist_curves"):
                    self.dist_curves = {}

                for key in ["regen", "clan_growth", "loner_spawn"]:
                    vals = samples.get(key, [])
                    if not vals:
                        # clear existing curve if any
                        if key in self.dist_curves:
                            try:
                                self.dist_curves[key].setData([], [])
                            except Exception:
                                pass
                        continue

                    x = list(range(len(vals)))
                    y = [float(v) for v in vals]
                    color = colors.get(key, "#ffffff")
                    display_names = {
                        "regen": "Nahrung (Regeneration)",
                        "clan_growth": "Clanwachstum",
                        "loner_spawn": "Einzelgänger Spawn",
                    }
                    if key not in self.dist_curves:
                        try:
                            pen = pg.mkPen(color=color, width=2)
                            name = display_names.get(key, key)
                            curve = self.dist_graph_widget.plot(
                                x, y, pen=pen, name=name
                            )
                            try:
                                curve.setClipToView(True)
                            except Exception:
                                pass
                            self.dist_curves[key] = curve
                        except Exception:
                            pass
                    else:
                        try:
                            self.dist_curves[key].setData(x, y)
                        except Exception:
                            pass

                # Adjust view range to latest samples
                try:
                    vb = self.dist_graph_widget.getPlotItem().getViewBox()
                    latest = 0
                    for v in samples.values():
                        if v:
                            latest = max(latest, len(v) - 1)
                    start = max(0, latest - 60)
                    vb.setXRange(start, latest, padding=0)
                except Exception:
                    pass
        except Exception:
            pass

    def on_back(self):
        """Go back to start screen."""
        self.stop_simulation()
        self.go_to_start()

    def on_exit(self):
        """Exit application."""
        from PyQt6.QtWidgets import QApplication

        self.stop_simulation()
        QApplication.quit()
