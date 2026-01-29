"""
Temperature and transition helpers extracted from `model.py`.
Provides update_and_apply(sim) to update temps, regen and apply survival damage.
"""

from __future__ import annotations
import random
import math
import logging
from typing import TYPE_CHECKING
from config import *

if TYPE_CHECKING:
    from backend.model import SimulationModel

logger = logging.getLogger(__name__)


def update_and_apply(sim: SimulationModel) -> None:
    """Process environmental updates and apply effects to entities.

    Updates day/night cycle, changes base temperature, regenerates food, and applies
    temperature or starvation damage to loners and clans.

    @param sim: The main simulation model instance.
    """
    # Transition progress handling
    if sim.in_transition:
        sim.transition_timer += 1
        target_offset = (
            DAY_NIGHT_TEMP_DELTA if sim.transition_to_day else -DAY_NIGHT_TEMP_DELTA
        )
        progress = sim.transition_timer / sim.transition_duration
        sim.day_night_temp_offset = target_offset * progress

        if sim.transition_timer >= sim.transition_duration:
            sim.in_transition = False
            sim.transition_timer = 0
            sim.is_day = sim.transition_to_day
            sim.stats["is_day"] = sim.is_day
            sim.day_night_temp_offset = target_offset
            if sim.is_day:
                sim.add_log(("☀️ Es ist jetzt Tag!", {}))
            else:
                sim.add_log(("🌙 Es ist jetzt Nacht!", {}))

        sim.current_temperature = sim.base_temperature + sim.day_night_temp_offset
        sim.current_temperature = max(
            TEMPERATURE_MIN, min(TEMPERATURE_MAX, sim.current_temperature)
        )
        sim.stats["temperature"] = round(sim.current_temperature, TEMPERATURE_PRECISION)

    # Periodic base temperature change
    sim.temp_change_timer += 1
    if sim.temp_change_timer >= TEMP_CHANGE_INTERVAL:
        sim.temp_change_timer = 0
        temp_change = random.uniform(-TEMP_CHANGE_DELTA, TEMP_CHANGE_DELTA)
        sim.base_temperature += temp_change
        sim.base_temperature = max(
            TEMPERATURE_MIN, min(TEMPERATURE_MAX, sim.base_temperature)
        )
        sim.current_temperature = sim.base_temperature + sim.day_night_temp_offset
        sim.current_temperature = max(
            TEMPERATURE_MIN, min(TEMPERATURE_MAX, sim.current_temperature)
        )
        sim.stats["temperature"] = round(sim.current_temperature, TEMPERATURE_PRECISION)
        # sim.add_log(
        #     (
        #         "🌡️ Temperatur: {val}°C",
        #         {"val": round(sim.current_temperature, TEMPERATURE_PRECISION)},
        #     )
        # )

    # Food regeneration
    for food_source in sim.food_sources:
        regen = food_source.regenerate()
        if regen and hasattr(sim, "rnd_history"):
            sim.rnd_history.setdefault("regen", []).append(regen)
            if len(sim.rnd_history["regen"]) > RND_HISTORY_LIMIT:
                sim.rnd_history["regen"] = sim.rnd_history["regen"][-RND_HISTORY_LIMIT:]

    # Apply temperature and starvation damage to loners
    loners_to_remove = []
    for loner in sim.loners:
        # Ensure loners move each simulation step
        try:
            loner.update(
                sim.map_width,
                sim.map_height,
                sim.is_day,
                getattr(sim, "loner_speed_multiplier", 1.0),
            )
        except Exception:
            logger.exception("Error updating loner state")
            pass
        species_config = sim.species_config.get(loner.species, {})
        min_temp = species_config.get(
            "min_survival_temp", SPECIES_DEFAULT_MIN_SURVIVAL_TEMP
        )
        max_temp = species_config.get(
            "max_survival_temp", SPECIES_DEFAULT_MAX_SURVIVAL_TEMP
        )
        if sim.current_temperature < min_temp or sim.current_temperature > max_temp:
            temp_diff = (
                (min_temp - sim.current_temperature)
                if sim.current_temperature < min_temp
                else (sim.current_temperature - max_temp)
            )
            damage = (
                TEMP_DAMAGE_BASE_LONER
                + (temp_diff // TEMP_DEGREE_STEP) * TEMP_DAMAGE_PER_STEP_LONER
            )
            damage = max(LONER_DAMAGE_MIN, min(damage, LONER_DAMAGE_MAX))
            loner.hp -= damage
            if loner.hp <= 0:
                loners_to_remove.append(loner)
                sim.add_log(
                    (
                        "❄️ {species} Einzelgänger stirbt an Temperatur ({val}°C)!",
                        {
                            "species": loner.species,
                            "val": round(
                                sim.current_temperature, TEMPERATURE_PRECISION
                            ),
                        },
                    )
                )
                sim.stats["deaths"]["temperature"][loner.species] = (
                    sim.stats["deaths"]["temperature"].get(loner.species, 0) + 1
                )

        if loner.hunger_timer >= HUNGER_TIMER_DEATH:
            loners_to_remove.append(loner)
            sim.add_log(
                ("☠️ {species} Einzelgänger verhungert!", {"species": loner.species})
            )
            sim.stats["deaths"]["starvation"][loner.species] = (
                sim.stats["deaths"]["starvation"].get(loner.species, 0) + 1
            )

    for loner in loners_to_remove:
        if loner in sim.loners:
            sim.loners.remove(loner)

    # Apply temperature damage to clans
    for group in sim.groups:
        species_config = sim.species_config.get(group.name, {})
        min_temp = species_config.get(
            "min_survival_temp", SPECIES_DEFAULT_MIN_SURVIVAL_TEMP
        )
        max_temp = species_config.get(
            "max_survival_temp", SPECIES_DEFAULT_MAX_SURVIVAL_TEMP
        )
        if sim.current_temperature < min_temp or sim.current_temperature > max_temp:
            temp_diff = (
                (min_temp - sim.current_temperature)
                if sim.current_temperature < min_temp
                else (sim.current_temperature - max_temp)
            )
            damage = TEMP_DAMAGE_BASE_CLAN + (temp_diff // TEMP_DEGREE_STEP)
            damage = max(CLAN_DAMAGE_MIN, min(damage, CLAN_DAMAGE_MAX))
            for clan in group.clans:
                if not hasattr(clan, "temp_survival_roll"):
                    clan.temp_survival_roll = (
                        random.random() < CLAN_TEMP_SURVIVAL_CHANCE
                    )
                if not hasattr(clan, "last_cycle_state"):
                    clan.last_cycle_state = sim.is_day
                if clan.last_cycle_state != sim.is_day:
                    clan.last_cycle_state = sim.is_day
                    clan.temp_survival_roll = (
                        random.random() < CLAN_TEMP_SURVIVAL_CHANCE
                    )
                if clan.temp_survival_roll:
                    continue
                old_pop = clan.population
                if not clan.take_damage(damage, sim):
                    pass
                if old_pop > clan.population:
                    deaths = old_pop - clan.population
                    sim.stats["deaths"][group.name] = (
                        sim.stats["deaths"].get(group.name, 0) + deaths
                    )
                    if clan.population == 1:
                        try:
                            sim._pending_conversions.append((group, clan))
                        except Exception:
                            pass
