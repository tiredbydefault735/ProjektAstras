import math
import logging
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QCheckBox,
    QWidget,
    QStackedWidget,
    QSizePolicy,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from frontend.i18n import _
from config import MIN_PANEL_HEIGHT

logger = logging.getLogger(__name__)


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
        # Show final and peak populations so the text matches the plotted history
        text = "<b>" + _("Spezies im Spiel (aktuell / Max):") + "</b><br>"
        species_counts = stats.get("species_counts", {}) or {}
        population_history = stats.get("population_history", {}) or {}
        all_species = set(list(species_counts.keys()) + list(population_history.keys()))
        for species in sorted(all_species):
            final_count = int(species_counts.get(species, 0))
            hist = population_history.get(species, []) or []
            try:
                peak = int(max(hist)) if hist else final_count
            except Exception:
                try:
                    peak = (
                        int(max([int(round(float(v))) for v in hist]))
                        if hist
                        else final_count
                    )
                except Exception:
                    logger.exception("Error calculating peak population")
                    peak = final_count
            text += f"• {species}: {final_count} / {peak}<br>"

        # Totals: current total population and aggregated death counts
        try:
            total_current = (
                sum(int(v) for v in species_counts.values()) if species_counts else 0
            )
        except Exception:
            logger.exception("Error calculating total_current")
            total_current = 0
        deaths = stats.get("deaths", {}) or {}
        try:
            total_combat = sum(int(v) for v in deaths.get("combat", {}).values())
        except Exception:
            logger.exception("Error calculating total_combat")
            total_combat = 0
        try:
            total_starvation = sum(
                int(v) for v in deaths.get("starvation", {}).values()
            )
        except Exception:
            logger.exception("Error calculating total_starvation")
            total_starvation = 0
        try:
            total_temperature = sum(
                int(v) for v in deaths.get("temperature", {}).values()
            )
        except Exception:
            logger.exception("Error calculating total_temperature")
            total_temperature = 0

        text += f"<br><b>{_('Insgesamt im Spiel:')}</b> {total_current}<br>"
        text += f"<br><b>{_('Todesfälle gesamt:')}</b><br>"
        text += f"• {_('Kampf')}: {total_combat}<br>"
        text += f"• {_('Verhungert')}: {total_starvation}<br>"
        text += f"• {_('Temperatur')}: {total_temperature}<br>"

        # Peak populations per species (explicit)
        try:
            text += f"<br><b>{_('Peak Populationen pro Spezies:')}</b><br>"
            for species in sorted(all_species):
                hist = population_history.get(species, []) or []
                try:
                    peak_val = (
                        int(max(hist)) if hist else int(species_counts.get(species, 0))
                    )
                except Exception:
                    try:
                        peak_val = (
                            int(max([int(round(float(v))) for v in hist]))
                            if hist
                            else int(species_counts.get(species, 0))
                        )
                    except Exception:
                        logger.exception(f"Error calculating peak for {species}")
                        peak_val = int(species_counts.get(species, 0))
                text += f"• {species}: {peak_val}<br>"
        except Exception:
            logger.exception("Error in peak population section")
            pass

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
            logger.exception("Error storing stats")
            self._stats = {}

        # Add a short summary of randomizer samples (helps debugging missing events)
        try:
            rnd = stats.get("rnd_samples", {}) or {}
            regen_count = len(rnd.get("regen", []))
            clan_count = len(rnd.get("clan_growth", []))
            loner_count = len(rnd.get("loner_spawn", []))
            try:
                regen_sum = 0
                for v in rnd.get("regen", []):
                    if v is not None:
                        val = v[1] if isinstance(v, (list, tuple)) else v
                        regen_sum += int(val)
            except Exception:
                logger.exception("Error calculating regen_sum")
                regen_sum = 0
            try:
                clan_sum = 0
                for v in rnd.get("clan_growth", []):
                    if v is not None:
                        val = v[1] if isinstance(v, (list, tuple)) else v
                        clan_sum += int(val)
            except Exception:
                logger.exception("Error calculating clan_sum")
                clan_sum = 0
            try:
                loner_sum = 0
                for v in rnd.get("loner_spawn", []):
                    if v is not None:
                        val = v[1] if isinstance(v, (list, tuple)) else v
                        loner_sum += int(val)
            except Exception:
                logger.exception("Error calculating loner_sum")
                loner_sum = 0

            text += (
                f"<br><b>{_('Randomizer (Samples):')}</b><br>"
                f"• {_('Regeneration')}: {regen_count} ({regen_sum})<br>"
                f"• {_('Clanwachstum')}: {clan_count} ({clan_sum})<br>"
                f"• {_('Einzelgänger Spawn')}: {loner_count} ({loner_sum})<br>"
            )
        except Exception:
            logger.exception("Error processing randomizer samples")
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
            pw.setMinimumHeight(MIN_PANEL_HEIGHT)
            try:
                pw.setMaximumHeight(16777215)
            except Exception:
                pass
            try:
                # QSizePolicy already imported
                pw.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
            except Exception:
                pass
            pw.getPlotItem().showGrid(x=True, y=True, alpha=0.2)
            pw.getAxis("left").setTextPen("#ffffff")
            pw.getAxis("bottom").setTextPen("#ffffff")
            pw.setLabel("left", _("Population"), color="#ffffff", size="10pt")
            # remove explicit seconds unit to reduce clutter
            pw.setLabel("bottom", _("Time (s)"), color="#ffffff", size="10pt")

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
                right_stack = QStackedWidget()

                # Page 0: final population plot
                page_stats = QWidget()
                p_stats_layout = QVBoxLayout(page_stats)
                p_stats_layout.setContentsMargins(0, 0, 0, 0)
                p_stats_layout.addWidget(pw)

                # Randomizer toggles for final-stats overlay
                try:
                    rnd_toggle_layout = QHBoxLayout()
                    rnd_toggle_layout.setSpacing(8)
                    rnd_toggle_layout.setContentsMargins(0, 6, 0, 6)
                    self._stats_rnd_toggles = {}
                    cb = QCheckBox(_("Regeneration"))
                    cb.setChecked(False)
                    rnd_toggle_layout.addWidget(cb)
                    self._stats_rnd_toggles["regen"] = cb
                    cb = QCheckBox(_("Clanwachstum"))
                    cb.setChecked(False)
                    rnd_toggle_layout.addWidget(cb)
                    self._stats_rnd_toggles["clan_growth"] = cb
                    cb = QCheckBox(_("Einzelgänger Spawn"))
                    cb.setChecked(False)
                    rnd_toggle_layout.addWidget(cb)
                    self._stats_rnd_toggles["loner_spawn"] = cb
                    rnd_toggle_layout.addStretch()
                    p_stats_layout.addLayout(rnd_toggle_layout)

                    # overlay curves storage
                    self._stats_rnd_curves = {}

                    def _refresh_stats_overlays():
                        try:
                            samples = (self._stats or {}).get("rnd_samples", {}) or {}
                            # compute y_max from population history similar to plot above
                            pop_hist = (self._stats or {}).get(
                                "population_history", {}
                            ) or {}
                            overall_max = 0
                            for h in pop_hist.values():
                                if h:
                                    try:
                                        overall_max = max(
                                            overall_max, int(round(max(h)))
                                        )
                                    except Exception:
                                        try:
                                            overall_max = max(overall_max, int(max(h)))
                                        except Exception:
                                            pass
                            padded = max(1.0, float(overall_max) * 1.10)
                            y_max = int(math.ceil(padded))
                            scale = float(y_max) / 100.0 if y_max > 0 else 1.0

                            colors = {
                                "regen": (102, 204, 102),
                                "clan_growth": (102, 170, 255),
                                "loner_spawn": (255, 204, 102),
                            }

                            for key, cb in self._stats_rnd_toggles.items():
                                enabled = False
                                try:
                                    enabled = cb.isChecked()
                                except Exception:
                                    enabled = False
                                vals = samples.get(key, []) or []
                                if enabled and vals:
                                    x = []
                                    y = []
                                    for item in vals:
                                        if (
                                            isinstance(item, (list, tuple))
                                            and len(item) == 2
                                        ):
                                            # (time, value)
                                            t_val, v_val = item
                                            # Convert ticks to seconds (assuming 0.1s tick rate / 10 ticks per sec)
                                            x.append(float(t_val) / 10.0)
                                            y.append(float(v_val))
                                        else:
                                            # legacy fallback: use index
                                            x.append(float(len(x)))
                                            try:
                                                y.append(float(item))
                                            except Exception:
                                                y.append(0.0)

                                    # Scale each series to fit the population Y-range
                                    # Use expected maxima per-randomizer so small-series
                                    # (e.g. regen=1..3) don't get amplified to full height.
                                    expected_max_map = {
                                        "regen": 10.0,
                                        "clan_growth": 10.0,
                                        "loner_spawn": 5.0,
                                    }
                                    expected_max = expected_max_map.get(key, 10.0)
                                    expected_max = max(1.0, float(expected_max))

                                    # How strongly overlays should fill the population Y range
                                    overlay_strength = 0.6

                                    # Compute scaled y values clamped to [0, y_max*overlay_strength]
                                    y_scaled = []
                                    for yi in y:
                                        try:
                                            frac = float(yi) / expected_max
                                        except Exception:
                                            frac = 0.0
                                        frac = max(0.0, min(frac, 1.0))
                                        y_scaled.append(frac * y_max * overlay_strength)
                                    if key not in self._stats_rnd_curves:
                                        try:
                                            # Use dotted lines as requested
                                            pen = pg.mkPen(
                                                color=colors.get(key, (200, 200, 200)),
                                                width=2,
                                                style=Qt.PenStyle.DotLine,
                                            )
                                            curve = pw.plot(
                                                x,
                                                y_scaled,
                                                pen=pen,
                                                name=key,
                                            )
                                            self._stats_rnd_curves[key] = curve
                                        except Exception:
                                            self._stats_rnd_curves[key] = None
                                    else:
                                        try:
                                            if (
                                                self._stats_rnd_curves.get(key)
                                                is not None
                                            ):
                                                self._stats_rnd_curves[key].setData(
                                                    x, y_scaled
                                                )
                                        except Exception:
                                            pass
                                else:
                                    try:
                                        if (
                                            key in self._stats_rnd_curves
                                            and self._stats_rnd_curves[key] is not None
                                        ):
                                            self._stats_rnd_curves[key].setData([], [])
                                    except Exception:
                                        pass

                        except Exception:
                            return

                    # connect toggles
                    for cb in self._stats_rnd_toggles.values():
                        try:
                            cb.stateChanged.connect(
                                lambda _=None: _refresh_stats_overlays()
                            )
                        except Exception:
                            pass

                    # initial overlay pass
                    try:
                        _refresh_stats_overlays()
                    except Exception:
                        pass
                except Exception:
                    pass

                # Page 1: Randomizers graph (uses rnd_samples from stats)
                page_rand = QWidget()
                p_rand_layout = QVBoxLayout(page_rand)
                p_rand_layout.setContentsMargins(0, 0, 0, 0)

                try:
                    import pyqtgraph as pg

                    rpw = pg.PlotWidget(background="#151515")
                    rpw.getPlotItem().showGrid(x=True, y=True, alpha=0.15)
                    rpw.setMinimumHeight(MIN_PANEL_HEIGHT)
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
                            # normalize to percentages so axis isn't dominated by outliers
                            total = sum(counts)
                            if total > 0:
                                counts = [c / total * 100.0 for c in counts]
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
                            # normalize to percentages so axis isn't dominated by outliers
                            total = sum(counts)
                            if total > 0:
                                counts = [c / total * 100.0 for c in counts]
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
                                    # normalize time-series to percentage of max to avoid extreme spikes
                                    maxy = max(y) if y else 0.0
                                    if maxy > 0:
                                        y = [yi / maxy * 100.0 for yi in y]
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
                # Build stats string (match logic from __init__ to show peaks)
                text = "<b>" + _("Spezies im Spiel (aktuell / Max):") + "</b><br>"
                species_counts = stats.get("species_counts", {}) or {}
                population_history = stats.get("population_history", {}) or {}
                all_species = set(
                    list(species_counts.keys()) + list(population_history.keys())
                )
                for species in sorted(all_species):
                    final_count = int(species_counts.get(species, 0))
                    hist = population_history.get(species, []) or []
                    try:
                        peak = int(max(hist)) if hist else final_count
                    except Exception:
                        try:
                            peak = (
                                int(max([int(round(float(v))) for v in hist]))
                                if hist
                                else final_count
                            )
                        except Exception:
                            peak = final_count
                    text += f"• {species}: {final_count} / {peak}<br>"
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
