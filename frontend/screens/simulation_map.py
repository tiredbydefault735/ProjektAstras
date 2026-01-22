"""
SimulationMapWidget - Neu: Direktes Rendering für glitch-freie Darstellung
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsTextItem
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap
from PyQt6.QtCore import Qt, QTimer


import os
from pathlib import Path

from utils import get_static_path
import math
import random


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

        # Align scene to top-left to avoid centered offsets when the view
        # or scene are resized or not yet laid out.
        try:
            self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        except Exception:
            pass

        # Region image mapping
        # Use get_static_path so resources work when frozen with PyInstaller
        self.region_images = {
            "Snowy Abyss": get_static_path("textures/snowy_abyss.png"),
            "Wasteland": get_static_path("textures/wasteland.png"),
            "Evergreen Forest": get_static_path("textures/evergreen_forest.png"),
            "Corrupted Caves": get_static_path("textures/corrupted_caves.png"),
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
        self._crushed_icon_path = None
        self._icefang_icon_path = None
        self._corrupted_icon_path = None

    def _find_spores_icon(self):
        """Return the path to the spores icon (case-insensitive search)."""
        if self._spores_icon_path:
            return self._spores_icon_path
        ui_dir = get_static_path("ui")
        try:
            for p in Path(ui_dir).iterdir():
                if p.name.lower() == "spores.png":
                    if p.exists():
                        self._spores_icon_path = p
                        return p
        except Exception:
            pass
        # Fallback to the canonical lowercase name
        candidate = get_static_path("ui/spores.png")
        if candidate.exists():
            self._spores_icon_path = candidate
            return candidate
        return None

    def _find_crushed_icon(self):
        """Return the path to the crushed_critters icon (case-insensitive search)."""
        if getattr(self, "_crushed_icon_path", None):
            return self._crushed_icon_path
        ui_dir = get_static_path("ui")
        try:
            for p in Path(ui_dir).iterdir():
                if p.name.lower() == "crushed_critters.png":
                    if p.exists():
                        self._crushed_icon_path = p
                        return p
        except Exception:
            pass
        candidate = get_static_path("ui/crushed_critters.png")
        if candidate.exists():
            self._crushed_icon_path = candidate
            return candidate
        return None

    def _find_icefang_icon(self):
        """Return the path to the icefang icon (case-insensitive search)."""
        if getattr(self, "_icefang_icon_path", None):
            return self._icefang_icon_path
        ui_dir = get_static_path("ui")
        try:
            for p in Path(ui_dir).iterdir():
                if p.name.lower() == "icefang.png":
                    if p.exists():
                        self._icefang_icon_path = p
                        return p
        except Exception:
            pass
        candidate = get_static_path("ui/icefang.png")
        if candidate.exists():
            self._icefang_icon_path = candidate
            return candidate
        return None

    def _find_corrupted_icon(self):
        """Return the path to the corrupted icon (case-insensitive search)."""
        if getattr(self, "_corrupted_icon_path", None):
            return self._corrupted_icon_path
        ui_dir = get_static_path("ui")
        try:
            for p in Path(ui_dir).iterdir():
                if p.name.lower() == "corrupted.png":
                    if p.exists():
                        self._corrupted_icon_path = p
                        return p
        except Exception:
            pass
        candidate = get_static_path("ui/corrupted.png")
        if candidate.exists():
            self._corrupted_icon_path = candidate
            return candidate
        return None

    def set_region(self, region_name):
        """Set the current region and update background image."""
        self.current_region = region_name
        image_path = self.region_images.get(region_name)
        if image_path and Path(image_path).exists():
            self.bg_pixmap = QPixmap(str(image_path))
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
            # Ensure background sits at scene origin and scene rect matches
            # the viewport so items use (0,0) origin consistently.
            self._bg_item.setZValue(-100)
            self._bg_item.setPos(0, 0)
            self.scene.addItem(self._bg_item)
            try:
                self.scene.setSceneRect(0, 0, width, height)
            except Exception:
                pass
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
            try:
                self.scene.setSceneRect(0, 0, width, height)
            except Exception:
                pass

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

        # Zeichne Nahrungsplätze: prefer image icons if available, fallback to
        # colored circles when images are missing.
        if food_sources_data:
            for food in food_sources_data:
                x = food["x"] * scale_x
                y = food["y"] * scale_y
                amount = food.get("amount", 0)
                max_amount = food.get("max_amount", 1) or 1

                # Fixed visual size for food icons: do not shrink when amount is low.
                # Use a sensible base size; rendering scales it up later for visibility.
                size = 24

                # choose image based on fullness: full, half, empty
                try:
                    if amount <= 0:
                        img_candidate = get_static_path("ui/food_empty.png")
                    elif amount > max_amount * 0.5:
                        img_candidate = get_static_path("ui/food_full.png")
                    else:
                        img_candidate = get_static_path("ui/food_half.png")

                    if img_candidate and Path(img_candidate).exists():
                        pm = QPixmap(str(img_candidate))
                        if not pm.isNull():
                            # scale food icons larger for visibility (2.5x)
                            scaled_size = max(1, int(size * 2.5))
                            scaled = pm.scaled(
                                scaled_size,
                                scaled_size,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )
                            pix = self.scene.addPixmap(scaled)
                            pix.setOffset(
                                x - scaled.width() / 2, y - scaled.height() / 2
                            )
                            pix.setZValue(0)
                            continue
                except Exception:
                    # fall through to circle drawing
                    pass

                # Fallback: Farbe: Grün wenn voll, gelb wenn wenig, braun wenn leer
                if amount > max_amount * 0.5:
                    food_color = QColor(34, 139, 34, 180)  # Grün
                elif amount > 0:
                    food_color = QColor(218, 165, 32, 180)  # Gelb/Gold
                else:
                    food_color = QColor(139, 69, 19, 100)  # Braun (leer)

                border_color = QColor(0, 100, 0, 255)

                # Kreis für Nahrung (scale up by 2.5)
                draw_size = max(1, int(size * 2.5))
                food_circle = self.scene.addEllipse(
                    x - draw_size / 2,
                    y - draw_size / 2,
                    draw_size,
                    draw_size,
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

                # Visual size: make clan size reflect the clan's population
                # (member count) but keep it capped to avoid extreme sizes.
                # This keeps visual meaning while preventing layout breakage.
                try:
                    # base size plus per-member increment
                    base = 40
                    per_member = 4
                    size = int(base + max(0, int(pop)) * per_member)
                    # enforce sensible min/max
                    size = max(48, min(180, size))
                except Exception:
                    size = 80

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

                # Try to draw a species icon (Spores, Crushed_Critters, Icefang) if available
                drawn_with_icon = False
                try:
                    species_name = group.get("name", "")
                    if species_name == "Spores":
                        icon_path = self._find_spores_icon()
                    elif species_name == "Crushed_Critters":
                        icon_path = self._find_crushed_icon()
                    elif species_name == "Icefang":
                        icon_path = self._find_icefang_icon()
                    elif species_name == "The_Corrupted":
                        icon_path = self._find_corrupted_icon()
                    else:
                        icon_path = None

                    if icon_path and Path(icon_path).exists():
                        pm = QPixmap(str(icon_path))
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
                    # Store the (maximum) display size seen for this species
                    # so loners can be sized relative to the largest clan.
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

                # Default loner visual size (fixed by default).
                # Previously loner size was derived from the largest clan
                # display size for the species (so it scaled with member counts).
                # Keep a fixed default to avoid loners changing size with clan population.
                display_size = 12
                try:
                    # Optional: allow scaling with clan size when explicitly enabled
                    # (set `_scale_loners_with_clans = True` on the view).
                    if getattr(self, "_scale_loners_with_clans", False):
                        if (
                            hasattr(self, "_species_clan_size")
                            and species in self._species_clan_size
                        ):
                            clan_size = self._species_clan_size.get(species, 12)
                            # Loners should be about 50% of clan display size
                            display_size = max(6, int(clan_size * 0.5))
                except Exception:
                    pass

                # Cap loner size so individuals never grow excessively large
                display_size = max(45, min(display_size, 60))

                # Try to draw an icon for Spores/Crushed_Critters/Icefang loners
                drawn_icon = False
                try:
                    if species == "Spores":
                        icon_path = self._find_spores_icon()
                    elif species == "Crushed_Critters":
                        icon_path = self._find_crushed_icon()
                    elif species == "Icefang":
                        icon_path = self._find_icefang_icon()
                    elif species == "The_Corrupted":
                        icon_path = self._find_corrupted_icon()
                    else:
                        icon_path = None

                    if icon_path and Path(icon_path).exists():
                        pm = QPixmap(str(icon_path))
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

    def preview_food_sources(
        self, num, amount, max_amount=100, transition_progress=1.0
    ):
        """Render a preview of `num` food sources on the map using logical
        coordinates. This places icons in a simple grid so users can see where
        food will appear before the simulation starts.
        """
        try:
            # If viewport not yet laid out, retry shortly to avoid misplacement
            width = self.viewport().width()
            height = self.viewport().height()
            if width <= 0 or height <= 0:
                QTimer.singleShot(
                    80,
                    lambda: self.preview_food_sources(
                        num, amount, max_amount, transition_progress
                    ),
                )
                return

            if not num or num <= 0:
                # clear only non-background items
                self.draw_groups([], [], [], transition_progress)
                return

            food_sources = []
            cols = int(math.ceil(math.sqrt(num)))
            rows = int(math.ceil(num / cols))
            # logical map size is 1200x600
            spacing_x = 1200.0 / (cols + 1)
            spacing_y = 600.0 / (rows + 1)
            placed = []
            for i in range(num):
                col = i % cols
                row = i // cols
                # center of cell
                cx = (col + 1) * spacing_x
                cy = (row + 1) * spacing_y

                # jitter up to ~40% of cell spacing to avoid overlap and grid look
                max_jx = spacing_x * 0.4
                max_jy = spacing_y * 0.4
                attempt = 0
                while True:
                    jx = random.uniform(-max_jx, max_jx)
                    jy = random.uniform(-max_jy, max_jy)
                    x = cx + jx
                    y = cy + jy

                    # clamp into logical map bounds with small margin
                    x = min(max(x, 16), 1200 - 16)
                    y = min(max(y, 16), 600 - 16)

                    # simple overlap avoidance: ensure not too close to existing
                    ok = True
                    for px, py in placed:
                        if (px - x) ** 2 + (py - y) ** 2 < (48**2):
                            ok = False
                            break
                    attempt += 1
                    if ok or attempt > 8:
                        placed.append((x, y))
                        break

                food_sources.append(
                    {"x": x, "y": y, "amount": amount, "max_amount": max_amount}
                )

            # Draw preview (no clans/loners)
            self.draw_groups([], [], food_sources, transition_progress)
        except Exception:
            pass
