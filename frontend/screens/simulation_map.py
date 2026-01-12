"""
SimulationMapWidget - Neu: Direktes Rendering für glitch-freie Darstellung
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap
from PyQt6.QtCore import Qt


import os


class SimulationMapWidget(QGraphicsView):
    """Map Widget - direktes Rendering ohne Interpolation."""

    def __init__(self):
        super().__init__()

        # Create graphics scene (will resize with viewport)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Disable scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Region image mapping
        self.region_images = {
            "Snowy Abyss": os.path.join("static", "textures", "snowy_abyss.png"),
            "Wasteland": os.path.join("static", "textures", "wasteland.png"),
            "Evergreen Forest": os.path.join(
                "static", "textures", "evergreen_forest.png"
            ),
            "Corrupted Caves": os.path.join(
                "static", "textures", "corrupted_caves.png"
            ),
        }
        self.bg_pixmap = None

        # Current region
        self.current_region = "Snowy Abyss"

        # Set initial background
        self.set_region(self.current_region)

        # Optimierte Darstellung
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    def set_region(self, region_name):
        """Set the current region and update background image."""
        self.current_region = region_name
        image_path = self.region_images.get(region_name)
        if image_path and os.path.exists(image_path):
            self.bg_pixmap = QPixmap(image_path)
        else:
            self.bg_pixmap = None
        self.update_background()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_background()

    def update_background(self):
        # Remove any previous background pixmap item
        if hasattr(self, "_bg_item") and self._bg_item:
            self.scene.removeItem(self._bg_item)
            self._bg_item = None
        width = self.viewport().width()
        height = self.viewport().height()
        if self.bg_pixmap:
            scaled = self.bg_pixmap.scaled(
                width,
                height,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            from PyQt6.QtWidgets import QGraphicsPixmapItem

            self._bg_item = QGraphicsPixmapItem(scaled)
            self._bg_item.setZValue(-100)
            self.scene.addItem(self._bg_item)
        else:
            self._bg_item = None
            # Optionally fill with white rect if no image
            from PyQt6.QtWidgets import QGraphicsRectItem

            rect = QGraphicsRectItem(0, 0, width, height)
            rect.setBrush(QColor(255, 255, 255))
            rect.setPen(QPen(Qt.PenStyle.NoPen))
            rect.setZValue(-100)
            self.scene.addItem(rect)
            self._bg_item = rect

    def draw_groups(
        self,
        groups_data,
        loners_data=None,
        food_sources_data=None,
        transition_progress=1.0,
        cell_size=40,
    ):
        """Zeichne Clans, Loners und Nahrungsplätze - DIREKTES Rendering."""

        # Remove all items except the background
        for item in self.scene.items():
            if getattr(self, "_bg_item", None) and item is self._bg_item:
                continue
            self.scene.removeItem(item)

        # Get viewport dimensions (actual display size)
        width = self.viewport().width()
        height = self.viewport().height()

        if width <= 0 or height <= 0:
            return

        # Update scene rect to match viewport
        self.scene.setSceneRect(0, 0, width, height)

        # Scale from logical coordinates (1200x600) to actual display size
        scale_x = width / 1200.0
        scale_y = height / 600.0

        # Disaster visuals removed

        # Zeichne Nahrungsplätze (grüne Kreise)
        if food_sources_data:
            for food in food_sources_data:
                x = food["x"] * scale_x
                y = food["y"] * scale_y
                amount = food["amount"]
                max_amount = food["max_amount"]

                # Größe basierend auf Nahrungsmenge (10-30px)
                size = 10 + (amount / max_amount) * 20 if max_amount > 0 else 10

                # Farbe: Grün wenn voll, gelb wenn wenig
                if amount > max_amount * 0.5:
                    food_color = QColor(34, 139, 34, 180)  # Grün
                elif amount > 0:
                    food_color = QColor(218, 165, 32, 180)  # Gelb/Gold
                else:
                    food_color = QColor(139, 69, 19, 100)  # Braun (leer)

                border_color = QColor(0, 100, 0, 255)

                # Kreis für Nahrung
                food_circle = self.scene.addEllipse(
                    x - size / 2,
                    y - size / 2,
                    size,
                    size,
                    pen=QPen(border_color, 2),
                    brush=QBrush(food_color),
                )
                food_circle.setZValue(0)  # Hinter allem

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
                font = QFont("Minecraft", 13, QFont.Weight.Bold)
                font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
                text.setFont(font)

                # Zentriere Text
                text_width = text.boundingRect().width()
                text_height = text.boundingRect().height()
                text.setPos(x - text_width / 2, y - text_height / 2)
                text.setZValue(1)
                self.scene.addItem(text)

        # Fließender Dunkelheitseffekt basierend auf Tageszeit
        # transition_progress: 0.0 = Nacht, 1.0 = Tag
        # Berechne Dunkelheit: 0 bei Tag (hell), 120 bei Nacht (dunkel)
        darkness = int((1.0 - transition_progress) * 120)

        if darkness > 0:
            # Use width and height from scene rect (1200x600) for consistent coverage
            overlay = self.scene.addRect(
                0,
                0,
                width,
                height,
                pen=QPen(Qt.PenStyle.NoPen),
                brush=QBrush(QColor(0, 0, 0, darkness)),
            )
            overlay.setZValue(10)  # Über allem

    def clear_map(self):
        """Lösche Map."""
        self.scene.clear()
