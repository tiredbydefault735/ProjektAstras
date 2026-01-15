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

        # Cache for icon lookup to handle case differences across filesystems
        self._spores_icon_path = None

    def _find_spores_icon(self):
        """Return the path to the spores icon (case-insensitive search)."""
        if self._spores_icon_path:
            return self._spores_icon_path
        ui_dir = os.path.join("static", "ui")
        try:
            for fname in os.listdir(ui_dir):
                if fname.lower() == "spores.png":
                    candidate = os.path.join(ui_dir, fname)
                    if os.path.exists(candidate):
                        self._spores_icon_path = candidate
                        return candidate
        except Exception:
            pass
        # Fallback to the canonical lowercase name (works on case-insensitive FS)
        candidate = os.path.join("static", "ui", "spores.png")
        if os.path.exists(candidate):
            self._spores_icon_path = candidate
            return candidate
        return None

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

                # If this group is Spores and an icon exists, draw the spores image scaled to clan size
                drawn_with_icon = False
                try:
                    if group.get("name", "") == "Spores":
                        icon_path = self._find_spores_icon()
                        if icon_path and os.path.exists(icon_path):
                            pm = QPixmap(icon_path)
                            if not pm.isNull():
                                scaled = pm.scaled(
                                    int(size),
                                    int(size),
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation,
                                )
                                pix = self.scene.addPixmap(scaled)
                                pix.setOffset(
                                    x - scaled.width() / 2, y - scaled.height() / 2
                                )
                                pix.setZValue(0)
                                drawn_with_icon = True
                except Exception:
                    drawn_with_icon = False

                if not drawn_with_icon:
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

                # Population als Text (overlay)
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

                # record display size for species so loners can be sized relative to clan
                try:
                    if not hasattr(self, "_species_clan_size"):
                        self._species_clan_size = {}
                    species_name = group.get("name", "")
                    prev = self._species_clan_size.get(species_name, 0)
                    self._species_clan_size[species_name] = max(prev, size)
                except Exception:
                    pass

        # Zeichne Loners (kleinere Kreise oder icons) AFTER clans so we can size them relative to clans
        if loners_data:
            for loner in loners_data:
                x = loner["x"] * scale_x
                y = loner["y"] * scale_y

                species = loner.get("species", "")
                color = loner["color"]
                rgb_color = QColor(
                    int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255
                )

                # Default loner visual size (12x12)
                display_size = 12
                try:
                    if (
                        hasattr(self, "_species_clan_size")
                        and species in self._species_clan_size
                    ):
                        clan_size = self._species_clan_size.get(species, 12)
                        # Loners are 10% of clan size
                        display_size = max(4, int(clan_size * 0.4))
                except Exception:
                    pass

                # If spores species and icon exists, draw icon scaled to display_size
                drawn_icon = False
                try:
                    if species == "Spores":
                        icon_path = self._find_spores_icon()
                        if icon_path and os.path.exists(icon_path):
                            pm = QPixmap(icon_path)
                            if not pm.isNull():
                                scaled = pm.scaled(
                                    int(display_size),
                                    int(display_size),
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation,
                                )
                                pix = self.scene.addPixmap(scaled)
                                pix.setOffset(
                                    x - scaled.width() / 2, y - scaled.height() / 2
                                )
                                pix.setZValue(2)
                                drawn_icon = True
                except Exception:
                    drawn_icon = False

                if not drawn_icon:
                    border_color = QColor(50, 50, 50, 255)
                    circle = self.scene.addEllipse(
                        x - display_size / 2,
                        y - display_size / 2,
                        display_size,
                        display_size,
                        pen=QPen(border_color, 2),
                        brush=QBrush(rgb_color),
                    )
                    circle.setZValue(2)

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
