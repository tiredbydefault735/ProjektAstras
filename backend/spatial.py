"""
Spatial grid helper extracted from model.py to keep single-responsibility.
Provides a uniform grid for neighbor queries and simple nearby candidate lookup.
"""

from __future__ import annotations
import logging
from typing import Dict, List, Tuple, Optional, Any, TYPE_CHECKING, Iterable, Union

from config import GRID_CELL_MIN

if TYPE_CHECKING:
    from backend.entities import Clan, Loner, FoodSource
    from backend.model import SpeciesGroup

logger = logging.getLogger(__name__)


class SpatialGrid:
    """Manages a spatial grid for efficient entity queries.

    @ivar grid_cell_size: Size of the grid cells
    @ivar grid: Dictionary mapping coordinate tuples to lists of entities
    @ivar _cell_size: Internal cell size used for current grid
    """

    def __init__(self, grid_cell_size: Optional[int] = None) -> None:
        """Initialize the spatial grid.

        @param grid_cell_size: Size of the grid cells in pixels
        """
        self.grid_cell_size: int = grid_cell_size or GRID_CELL_MIN
        # Grid maps (x, y) tuple to a dict of lists
        self.grid: Dict[Tuple[int, int], Dict[str, List[Any]]] = {}
        self._cell_size: int = self.grid_cell_size

    def build(
        self,
        groups: List[SpeciesGroup],
        loners: List[Loner],
        food_sources: List[FoodSource],
        grid_cell_size: Optional[int] = None,
    ) -> None:
        """Builds a uniform spatial grid mapping (cell_x,cell_y) -> {'clans','loners','food'}

        @param groups: List of species groups containing clans
        @param loners: List of loner entities
        @param food_sources: List of food source entities
        @param grid_cell_size: Optional override for cell size
        """
        self.grid = {}
        cs = max(GRID_CELL_MIN, int(grid_cell_size or self.grid_cell_size))

        def _add(entity: Any, kind: str, x: float, y: float) -> None:
            cx = int(x) // cs
            cy = int(y) // cs
            key = (cx, cy)
            cell = self.grid.get(key)
            if cell is None:
                cell = {"clans": [], "loners": [], "food": []}
                self.grid[key] = cell
            cell[kind].append(entity)

        for group in groups:
            for clan in group.clans:
                _add(clan, "clans", clan.x, clan.y)

        for loner in loners:
            _add(loner, "loners", loner.x, loner.y)

        for f in food_sources:
            _add(f, "food", f.x, f.y)

        # remember used cell size for nearby calculations
        self._cell_size = cs

    def nearby_candidates(
        self,
        x: float,
        y: float,
        radius: float,
        kinds: Iterable[str] = ("clans", "loners", "food"),
    ) -> List[Any]:
        """Return candidate entities within grid cells overlapping a radius around (x,y).

        Note: returned candidates are a superset; caller must check exact distance if needed.

        @param x: Center X coordinate
        @param y: Center Y coordinate
        @param radius: Search radius
        @param kinds: Types of entities to retrieve
        @return: List of potential candidate entities
        """
        cs = getattr(self, "_cell_size", max(GRID_CELL_MIN, int(self.grid_cell_size)))
        r = max(0, int(radius))
        min_cx = int((x - r)) // cs
        max_cx = int((x + r)) // cs
        min_cy = int((y - r)) // cs
        max_cy = int((y + r)) // cs

        out: List[Any] = []
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                cell = self.grid.get((cx, cy))
                if not cell:
                    continue
                for k in kinds:
                    out.extend(cell.get(k, []))

        return out
