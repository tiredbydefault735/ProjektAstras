"""
SimulationMapWidget - Neu: Direktes Rendering für glitch-freie Darstellung
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt


class SimulationMapWidget(QGraphicsView):
    """Map Widget - direktes Rendering ohne Interpolation."""

    def __init__(self):
        super().__init__()

        # Create graphics scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Set background to white
        self.setBackgroundBrush(QColor(255, 255, 255))

        # Optimierte Darstellung
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    def draw_groups(self, groups_data, loners_data=None):
        """Zeichne Clans und Loners - DIREKTES Rendering."""
        self.scene.clear()

        # Viewport dimensions
        width = self.viewport().width()
        height = self.viewport().height()

        if width <= 0 or height <= 0:
            return

        # Scale
        scale_x = width / 1200.0
        scale_y = height / 600.0

        # Zeichne Loners (größere Kreise mit Rand)
        if loners_data:
            for loner in loners_data:
                x = loner["x"] * scale_x
                y = loner["y"] * scale_y

                color = loner["color"]
                rgb_color = QColor(
                    int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255
                )
                border_color = QColor(50, 50, 50, 255)

                # Kreis (6px Radius)
                circle = self.scene.addEllipse(
                    x - 6,
                    y - 6,
                    12,
                    12,
                    pen=QPen(border_color, 2),
                    brush=QBrush(rgb_color),
                )
                circle.setZValue(2)

        # Zeichne Clans (Quadrate mit Population-Text)
        for group in groups_data:
            if not group or "clans" not in group:
                continue

            for clan in group["clans"]:
                x = clan["x"] * scale_x
                y = clan["y"] * scale_y
                pop = clan["population"]

                # Größe basierend auf Population (40-120px - GRÖSSER für mehr Platznutzung)
                size = max(40, min(120, pop * 5))

                color = clan["color"]
                rgb_color = QColor(
                    int(color[0] * 255),
                    int(color[1] * 255),
                    int(color[2] * 255),
                    100,  # Semi-transparent
                )
                border_color = QColor(
                    int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 200
                )

                # Quadrat
                rect = self.scene.addRect(
                    x - size / 2,
                    y - size / 2,
                    size,
                    size,
                    pen=QPen(border_color, 2),
                    brush=QBrush(rgb_color),
                )
                rect.setZValue(0)

                # Population als Text
                text = QGraphicsTextItem(str(pop))
                text.setDefaultTextColor(QColor(0, 0, 0, 255))
                font = QFont("Arial", 10, QFont.Weight.Bold)
                text.setFont(font)

                # Zentriere Text
                text_width = text.boundingRect().width()
                text_height = text.boundingRect().height()
                text.setPos(x - text_width / 2, y - text_height / 2)
                text.setZValue(1)
                self.scene.addItem(text)

    def clear_map(self):
        """Lösche Map."""
        self.scene.clear()
