"""
Spatial grid helper extracted from model.py to keep single-responsibility.
Provides a uniform grid for neighbor queries and simple nearby candidate lookup.
"""

from config import GRID_CELL_MIN


class SpatialGrid:
    def __init__(self, grid_cell_size=None):
        self.grid_cell_size = grid_cell_size or GRID_CELL_MIN
        self.grid = {}

    def build(self, groups, loners, food_sources, grid_cell_size=None):
        """Builds a uniform spatial grid mapping (cell_x,cell_y) -> {'clans','loners','food'}"""
        self.grid = {}
        cs = max(GRID_CELL_MIN, int(grid_cell_size or self.grid_cell_size))

        def _add(entity, kind, x, y):
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

    def nearby_candidates(self, x, y, radius, kinds=("clans", "loners", "food")):
        """Return candidate entities within grid cells overlapping a radius around (x,y).
        Note: returned candidates are a superset; caller must check exact distance if needed.
        """
        cs = getattr(self, "_cell_size", max(GRID_CELL_MIN, int(self.grid_cell_size)))
        r = max(0, int(radius))
        min_cx = int((x - r)) // cs
        max_cx = int((x + r)) // cs
        min_cy = int((y - r)) // cs
        max_cy = int((y + r)) // cs

        out = []
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                cell = self.grid.get((cx, cy))
                if not cell:
                    continue
                for k in kinds:
                    out.extend(cell.get(k, []))

        return out
