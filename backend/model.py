"""Compatibility shim for legacy imports.

This module re-exports the refactored classes so existing imports from
`backend.model` continue to work while the codebase is split into
smaller modules under `backend.entities` and `backend.simulation`.
"""

from .simulation import SimulationModel
from .entities.food_source import FoodSource
from .entities.loner import Loner
from .entities.clan import Clan
from .entities.species_group import SpeciesGroup

__all__ = [
    "SimulationModel",
    "FoodSource",
    "Loner",
    "Clan",
    "SpeciesGroup",
]
