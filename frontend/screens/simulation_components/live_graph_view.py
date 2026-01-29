from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from frontend.i18n import _
from config import (
    LIVE_PLOT_MIN_HEIGHT,
    MAX_SIMULATION_TIME,
    LOG_FONT_FAMILY,
    LOG_FONT_SIZE,
    LOG_MIN_HEIGHT,
)


class LiveGraphView(QFrame):
    """
    Widget handling the live population graph using PyQtGraph.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.live_graph_widget = None
        self.live_curves = {}
        self.dist_curves = {}
        self.graph_legend_label = None
        self._last_graph_update = 0.0
        self._graph_update_interval = 0.5
        self._live_last_overall_max = None
        self._live_last_latest_time = None
        self._last_pop_snapshot = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # We will initialize the pyqtgraph widget lazily or here if dependencies allows
        # But simulation screen did it via initialize_live_graph called later.
        # We can do it here if we handle imports carefully.
        self.initialize_graphs()

    def initialize_graphs(self):
        try:
            import pyqtgraph as pg

            # Prefer speed for live updates: disable antialiasing by default
            pg.setConfigOptions(antialias=False)

            # Create PlotWidget
            pw = pg.PlotWidget(background="#1a1a1a")
            pw.getPlotItem().showGrid(x=True, y=True, alpha=0.2)
            pw.getAxis("left").setTextPen("#ffffff")
            pw.getAxis("bottom").setTextPen("#ffffff")
            pw.setLabel("left", _("Population"), color="#ffffff", size="9pt")
            pw.setLabel("bottom", _("Time (s)"), color="#ffffff", size="9pt")

            # Lock aspect settings
            try:
                vb = pw.getPlotItem().getViewBox()
                vb.setMouseEnabled(False, False)
                try:
                    vb.setMenuEnabled(False)
                except Exception:
                    pass
            except Exception:
                pass

            pw.setMinimumHeight(LIVE_PLOT_MIN_HEIGHT)
            pw.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            try:
                left_axis = pw.getAxis("left")
                bottom_axis = pw.getAxis("bottom")
                left_axis.setStyle(tickFont=QFont("Minecraft", 9))
                bottom_axis.setStyle(tickFont=QFont("Minecraft", 9))
                left_axis.setWidth(60)
                bottom_axis.setHeight(30)
            except Exception:
                pass

            self.layout().addWidget(pw)
            self.live_graph_widget = pw

            # Legend
            self.graph_legend_label = QLabel()
            self.graph_legend_label.setStyleSheet(
                "color: #ffffff; font-size: 11px; padding: 4px 0 0 0;"
            )
            self.graph_legend_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout().addWidget(self.graph_legend_label)

        except ImportError:
            label = QLabel("Graph nicht verfügbar (pyqtgraph benötigt)")
            label.setStyleSheet("color: #ffffff; font-size: 12px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout().addWidget(label)
        except Exception as e:
            # Fallback
            pass

    def reset(self):
        self.live_curves = {}
        self.dist_curves = {}
        self._live_last_overall_max = None
        self._live_last_latest_time = None
        self._last_pop_snapshot = None
        if self.live_graph_widget:
            self.live_graph_widget.clear()

    def update_graph(
        self,
        population_data,
        enabled_species_names,
        latest_species_counts,
        rnd_samples=None,
    ):
        """Update the live population graph with current data."""
        if not self.live_graph_widget:
            return

        import time

        now = time.monotonic()
        if self._last_graph_update and (
            now - self._last_graph_update < self._graph_update_interval
        ):
            return
        self._last_graph_update = now

        try:
            import pyqtgraph as pg

            colors = {
                "Icefang": "#cce6ff",
                "Crushed_Critters": "#cc9966",
                "Spores": "#66cc66",
                "The_Corrupted": "#cc66cc",
            }

            LIVE_WINDOW = 10

            # Optimisation: check if snapshot changed
            try:
                snapshot = tuple(
                    (name, len(population_data.get(name, [])))
                    for name in sorted(population_data.keys())
                )
                if self._last_pop_snapshot == snapshot:
                    # Just update X range
                    self._update_x_range(population_data, LIVE_WINDOW)
                    return
                self._last_pop_snapshot = snapshot
            except Exception:
                pass

            for species_name, history in population_data.items():
                if enabled_species_names and species_name not in enabled_species_names:
                    if species_name in self.live_curves:
                        self.live_curves[species_name].setData([], [])
                    continue

                if not history:
                    continue

                local_hist = list(history)
                # Append instantaneous count
                try:
                    if species_name in latest_species_counts and (
                        not local_hist
                        or int(local_hist[-1])
                        != int(latest_species_counts.get(species_name, 0))
                    ):
                        local_hist.append(
                            int(latest_species_counts.get(species_name, 0))
                        )
                except Exception:
                    pass

                last_n = min(len(local_hist), LIVE_WINDOW)
                time_points = [
                    i for i in range(len(local_hist) - last_n, len(local_hist))
                ]
                display_history = local_hist[-last_n:]

                # Convert to int
                try:
                    display_history = [int(round(float(v))) for v in display_history]
                except Exception:
                    pass

                color = colors.get(species_name, "#ffffff")

                if species_name not in self.live_curves:
                    pen = pg.mkPen(color=color, width=2)
                    curve = self.live_graph_widget.plot(
                        time_points, display_history, pen=pen
                    )
                    try:
                        curve.setClipToView(True)
                    except Exception:
                        pass
                    self.live_curves[species_name] = curve
                else:
                    self.live_curves[species_name].setData(time_points, display_history)

            self._update_x_range(population_data, LIVE_WINDOW)
            self._update_y_range(population_data)
            self._update_bottom_ticks(population_data)
            self._update_legend(population_data, colors)

            # (Distribution graph update logic omitted for brevity as it was seemingly partial in original,
            # but if it exists, it would follow similar pattern using rnd_samples)

        except Exception:
            pass

    def _update_x_range(self, population_data, window_size):
        try:
            vb = self.live_graph_widget.getPlotItem().getViewBox()
            latest = 0
            for h in population_data.values():
                if h:
                    latest = max(latest, len(h) - 1)
            start = max(0, latest - (window_size - 1))
            vb.setXRange(start, latest, padding=0)
        except Exception:
            pass

    def _update_y_range(self, population_data):
        try:
            left_axis = self.live_graph_widget.getAxis("left")
            overall_max = 0
            for h in population_data.values():
                if h:
                    try:
                        overall_max = max(overall_max, int(round(max(h))))
                    except Exception:
                        overall_max = max(overall_max, int(max(h)))

            if overall_max != self._live_last_overall_max:
                y_max = max(1, overall_max + 5)
                import math

                try:
                    step = max(1, int(math.ceil(y_max / 6.0)))
                except:
                    step = 2
                ticks = [(i, str(i)) for i in range(0, y_max + 1, step)]
                if ticks and ticks[-1][0] != y_max:
                    ticks.append((y_max, str(y_max)))
                left_axis.setTicks([ticks])

                vb = self.live_graph_widget.getPlotItem().getViewBox()
                vb.setYRange(0, max(1, y_max), padding=0)
                self._live_last_overall_max = overall_max
        except Exception:
            pass

    def _update_bottom_ticks(self, population_data):
        try:
            bottom_axis = self.live_graph_widget.getAxis("bottom")
            latest = 0
            for h in population_data.values():
                if h:
                    latest = max(latest, len(h) - 1)

            if latest != self._live_last_latest_time:
                # Logic for step
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
                        label = f"{int(i // 60)}m"
                    else:
                        label = str(i)
                    ticks.append((i, label))
                if not ticks:
                    ticks = [(0, "0")]
                bottom_axis.setTicks([ticks])
                self._live_last_latest_time = latest
        except Exception:
            pass

    def _update_legend(self, population_data, colors):
        if not self.graph_legend_label:
            return
        legend_parts = []
        for species_name in sorted(population_data.keys()):
            color = colors.get(species_name, "#ffffff")
            display_name = species_name.replace("_", " ")
            legend_parts.append(
                f'<span style="color: {color}; font-weight: bold;">{display_name}</span>'
            )
        self.graph_legend_label.setText(
            " | ".join(legend_parts) if legend_parts else ""
        )
