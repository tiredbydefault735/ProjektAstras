"""
Spawn helpers extracted from model.py to keep `SimulationModel.step` concise.
"""

from __future__ import annotations
import random
import logging
from typing import TYPE_CHECKING
from config import (
    SPAWN_PADDING,
    SPAWN_THRESHOLD_HIGH,
    SPAWN_THRESHOLD_LOW,
    SPAWN_SINGLE_COUNT,
    DEFAULT_COLOR,
    DEFAULT_COLOR_HEX,
    LONER_SPAWN_RANGE,
    LONER_SPAWN_RANGE as _LONER_SPAWN_RANGE,
    FOOD_INTAKE_DEFAULT,
    DEFAULT_FOOD_PLACES,
)

if TYPE_CHECKING:
    from backend.model import SimulationModel

logger = logging.getLogger(__name__)


def spawn_loners(sim: SimulationModel) -> None:
    """Spawn loners according to species_config and population overrides."""
    # Import Loner locally to avoid circular import at module import time
    from backend.entities import Loner

    for species_name, stats in sim.species_config.items():
        current_count = 0
        for g in sim.groups:
            if g.name == species_name:
                current_count += sum(c.population for c in g.clans)
        current_count += sum(1 for l in sim.loners if l.species == species_name)
        if current_count == 0:
            continue

        spawn_threshold = SPAWN_THRESHOLD_HIGH
        if species_name == "Icefang":
            spawn_threshold = SPAWN_THRESHOLD_LOW
        spawn_chance = random.uniform(0.0, 1.0)
        if spawn_chance < spawn_threshold:
            spawn_count = SPAWN_SINGLE_COUNT
            color_map = {
                "Icefang": getattr(sim, "ICEFANG_COLOR", None) or DEFAULT_COLOR_HEX,
                "Crushed_Critters": getattr(sim, "CRUSHED_CRITTERS_COLOR", None)
                or DEFAULT_COLOR_HEX,
                "Spores": getattr(sim, "SPORES_COLOR", None) or DEFAULT_COLOR_HEX,
                "The_Corrupted": getattr(sim, "THE_CORRUPTED_COLOR", None)
                or DEFAULT_COLOR_HEX,
            }
            color = color_map.get(species_name, DEFAULT_COLOR)
            hp = stats.get("hp", getattr(sim, "DEFAULT_HP", 1))
            food_intake = stats.get("food_intake", FOOD_INTAKE_DEFAULT)
            can_cannibalize = species_name in ["Spores", "The_Corrupted"]
            for _ in range(spawn_count):
                x = random.uniform(SPAWN_PADDING, sim.map_width - SPAWN_PADDING)
                y = random.uniform(SPAWN_PADDING, sim.map_height - SPAWN_PADDING)
                loner = Loner(
                    species_name, x, y, color, hp, food_intake, 0, can_cannibalize
                )
                sim.loners.append(loner)

            if hasattr(sim, "rnd_history"):
                sim.rnd_history.setdefault("loner_spawn", []).append(spawn_count)
                if len(sim.rnd_history["loner_spawn"]) > getattr(
                    sim, "RND_HISTORY_LIMIT", 100
                ):
                    sim.rnd_history["loner_spawn"] = sim.rnd_history["loner_spawn"][
                        -getattr(sim, "RND_HISTORY_LIMIT", 100) :
                    ]

            sim.add_log(
                (
                    "🔹 {count} neuer Einzelgänger der Spezies {species} ist erschienen!",
                    {"count": spawn_count, "species": species_name},
                )
            )
