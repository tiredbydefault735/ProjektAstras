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
    DEFAULT_COLOR,
    FOOD_INTAKE_DEFAULT,
    DEFAULT_HP,
    ICEFANG_COLOR,
    CRUSHED_CRITTERS_COLOR,
    SPORES_COLOR,
    THE_CORRUPTED_COLOR,
)

if TYPE_CHECKING:
    from backend.model import SimulationModel

logger = logging.getLogger(__name__)


def spawn_loners(sim: SimulationModel) -> None:
    """Spawn loners according to species_config and population overrides.

    @param sim: The simulation model instance
    """
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
            spawn_count = random.randint(2, 3)
            color_map = {
                "Icefang": ICEFANG_COLOR,
                "Crushed_Critters": CRUSHED_CRITTERS_COLOR,
                "Spores": SPORES_COLOR,
                "The_Corrupted": THE_CORRUPTED_COLOR,
            }
            color = color_map.get(species_name, DEFAULT_COLOR)
            hp = stats.get("hp", DEFAULT_HP)
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
                sim.rnd_history.setdefault("loner_spawn", []).append(
                    (sim.time, spawn_count)
                )
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
