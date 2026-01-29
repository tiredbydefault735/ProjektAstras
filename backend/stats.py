"""
Simulation snapshot and stats helpers.
Extracted from `SimulationModel.step` to keep model small.
"""

from __future__ import annotations
import logging
from copy import deepcopy
from typing import TYPE_CHECKING, Dict, List, Any, Tuple, Union
import re
from config import DEFAULT_COLOR

if TYPE_CHECKING:
    from backend.model import SimulationModel

logger = logging.getLogger(__name__)


def _normalize_color(col: Any) -> Tuple[float, float, float, float]:
    """Normalize color to 4-tuple of floats (r,g,b,a) in 0..1.

    Accepts:
      - tuple/list of 3 or 4 floats (0..1) or ints (0..255)
      - hex string like '#rrggbb' or '#rrggbbaa'
      - fallback to DEFAULT_COLOR

    @param col: The color input (string, tuple, list, or None)
    @return: A normalized (r, g, b, a) tuple
    """
    if col is None:
        return DEFAULT_COLOR
    # tuple/list
    if isinstance(col, (list, tuple)):
        vals = list(col)
        if all(isinstance(x, (int, float)) for x in vals):
            # ints in 0-255 -> convert
            if any(isinstance(x, int) and x > 1 for x in vals):
                vals = [float(x) / 255.0 for x in vals]
            # pad to 4
            if len(vals) == 3:
                vals.append(1.0)
            return tuple(float(x) for x in vals[:4])  # type: ignore

    # hex string
    if isinstance(col, str):
        s = col.strip()
        m = re.match(r"^#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?$", s)
        if m:
            rgb = m.group(1)
            alpha = m.group(2) or "ff"
            r = int(rgb[0:2], 16) / 255.0
            g = int(rgb[2:4], 16) / 255.0
            b = int(rgb[4:6], 16) / 255.0
            a = int(alpha, 16) / 255.0
            return (r, g, b, a)

    # fallback
    return DEFAULT_COLOR


def collect_simulation_snapshot(sim: SimulationModel) -> Dict[str, Any]:
    """Collect groups/loners/food snapshot and update species_counts in sim.stats.

    @param sim: The simulation model instance
    @return: A dictionary containing the snapshot data
    """
    groups_data = []
    for group in sim.groups:
        clans_data = [
            {
                "x": clan.x,
                "y": clan.y,
                "population": clan.population,
                "color": clan.color,
                "clan_id": clan.clan_id,
            }
            for clan in group.clans
        ]
        groups_data.append(
            {"name": group.name, "clans": clans_data, "color": group.color}
        )

    loners_data = [
        {"x": l.x, "y": l.y, "color": l.color, "species": l.species} for l in sim.loners
    ]

    food_sources_data = [
        {"x": f.x, "y": f.y, "amount": f.amount, "max_amount": f.max_amount}
        for f in sim.food_sources
    ]

    # Update species counts in stats (safe best-effort)
    try:
        current_counts = {}
        for g in sim.groups:
            current_counts[g.name] = current_counts.get(g.name, 0) + sum(
                c.population for c in g.clans
            )
        for l in sim.loners:
            current_counts[l.species] = current_counts.get(l.species, 0) + 1
        for s in getattr(sim, "species_config", {}).keys():
            current_counts.setdefault(s, 0)
        sim.stats["species_counts"] = current_counts
    except Exception:
        pass

    # normalize colors to safe format for frontend
    for g in groups_data:
        g["color"] = _normalize_color(g.get("color"))
        for c in g.get("clans", []):
            c["color"] = _normalize_color(c.get("color"))
    for l in loners_data:
        l["color"] = _normalize_color(l.get("color"))

    return {
        "groups": groups_data,
        "loners": loners_data,
        "food_sources": food_sources_data,
        "stats": deepcopy(sim.stats),
    }
