"""
Processors extracted from model.py: food-seeking, interactions and loner->clan formation.
These functions operate on a SimulationModel instance passed as `sim`.
"""

from __future__ import annotations
import math
import random
import logging
from typing import TYPE_CHECKING
from config import *

# Import Loner/Clan types from entities to construct instances when needed
from backend.entities import Loner, Clan

if TYPE_CHECKING:
    from backend.model import SimulationModel

logger = logging.getLogger(__name__)


def process_food_seeking(sim: SimulationModel) -> None:
    """Nahrungssuche und Essen (extracted)."""
    # Clans suchen und essen Nahrung
    for group in sim.groups:
        for clan in group.clans:
            primary_prey_species = ["Icefang", "Crushed_Critters"]
            primary_prey_exists = any(
                (
                    g.name in primary_prey_species
                    and any(c.population > 0 for c in g.clans)
                )
                for g in sim.groups
            ) or any(l.species in primary_prey_species for l in sim.loners)

            if clan.can_cannibalize:
                nearest_prey = None
                nearest_prey_dist = float("inf")
                candidates = sim._nearby_candidates(
                    clan.x, clan.y, FOOD_SEARCH_RADIUS, ("clans", "loners")
                )
                for cand in candidates:
                    if cand is clan:
                        continue
                    cand_species = getattr(cand, "species", None)
                    if cand_species in primary_prey_species:
                        dx = clan.x - getattr(cand, "x", 0)
                        dy = clan.y - getattr(cand, "y", 0)
                        dist_sq = dx * dx + dy * dy
                        if dist_sq < nearest_prey_dist:
                            nearest_prey_dist = dist_sq
                            nearest_prey = cand

                if not nearest_prey and not primary_prey_exists:
                    candidates = sim._nearby_candidates(
                        clan.x, clan.y, FOOD_SEARCH_RADIUS, ("clans",)
                    )
                    for cand in candidates:
                        if cand is clan:
                            continue
                        cand_species = getattr(cand, "species", None)
                        if (
                            cand_species
                            and cand_species != clan.species
                            and getattr(cand, "can_cannibalize", False)
                        ):
                            dx = clan.x - cand.x
                            dy = clan.y - cand.y
                            dist_sq = dx * dx + dy * dy
                            if dist_sq < nearest_prey_dist:
                                nearest_prey_dist = dist_sq
                                nearest_prey = cand

                if nearest_prey and clan.hunger_timer >= HUNGER_ALERT:
                    clan.move_towards(
                        getattr(nearest_prey, "x", nearest_prey.x),
                        getattr(nearest_prey, "y", nearest_prey.y),
                        strength=CHASE_STRENGTH,
                    )

            nearest_food = None
            nearest_dist = float("inf")
            candidates = sim._nearby_candidates(
                clan.x, clan.y, FOOD_SEARCH_RADIUS, ("food",)
            )
            for food_source in candidates:
                if not food_source.is_depleted():
                    dx = clan.x - food_source.x
                    dy = clan.y - food_source.y
                    dist_sq = dx * dx + dy * dy
                    if dist_sq < nearest_dist:
                        nearest_dist = dist_sq
                        nearest_food = food_source

            if clan.seeking_food and nearest_food:
                clan.move_towards(
                    nearest_food.x, nearest_food.y, strength=MOVE_STRENGTH_NEAREST_FOOD
                )

            if nearest_food and nearest_dist < (FOOD_RANGE * FOOD_RANGE):
                consumed = nearest_food.consume(clan.food_intake)
                if consumed > 0:
                    clan.hunger_timer = max(
                        0, clan.hunger_timer - (consumed * FOOD_HUNGER_STEP)
                    )
                    clan.seeking_food = False
                    old_hp = clan.hp_per_member
                    species_stats = sim.species_config.get(group.name, {})
                    max_hp = species_stats.get("hp", MAX_HP_FALLBACK)
                    clan.hp_per_member = min(
                        clan.hp_per_member + (consumed * HP_PER_FOOD), max_hp
                    )
                    sim.add_log(
                        (
                            "🍽️ {species} Clan #{clan_id} isst {consumed} Food (+{hp_gain} HP)",
                            {
                                "species": group.name,
                                "clan_id": clan.clan_id,
                                "consumed": consumed,
                                "hp_gain": int(clan.hp_per_member - old_hp),
                            },
                        )
                    )

                    try:
                        growth_chance = FRIENDLY_GROWTH_CHANCE_DEFAULT
                        if group.name == "Icefang":
                            growth_chance = ICEFANG_GROWTH_CHANCE
                        if (
                            random.random() < growth_chance
                            and clan.population < clan.max_members
                        ):
                            mu = GAUSS_MU
                            sigma = GAUSS_SIGMA
                            increase = int(round(random.gauss(mu, sigma)))
                            increase = max(1, increase)
                            space = clan.max_members - clan.population
                            actual = min(increase, max(0, space))
                            if actual > 0:
                                clan.population += actual
                                sim.add_log(
                                    (
                                        "🌱 {species} Clan #{clan_id} wächst nach Essen (+{increase} Mitglieder)",
                                        {
                                            "species": group.name,
                                            "clan_id": clan.clan_id,
                                            "increase": actual,
                                        },
                                    )
                                )
                                if hasattr(sim, "rnd_history"):
                                    sim.rnd_history.setdefault(
                                        "clan_growth", []
                                    ).append(actual)
                                    if (
                                        len(sim.rnd_history["clan_growth"])
                                        > RND_HISTORY_LIMIT
                                    ):
                                        sim.rnd_history["clan_growth"] = (
                                            sim.rnd_history["clan_growth"][
                                                -RND_HISTORY_LIMIT:
                                            ]
                                        )
                    except Exception:
                        pass

    # Loners suchen und essen Nahrung
    for loner in sim.loners:
        primary_prey_species = ["Icefang", "Crushed_Critters"]
        primary_prey_exists = any(
            (g.name in primary_prey_species and any(c.population > 0 for c in g.clans))
            for g in sim.groups
        ) or any(l.species in primary_prey_species for l in sim.loners)

        if loner.can_cannibalize:
            nearest_prey = None
            nearest_prey_dist = float("inf")
            candidates = sim._nearby_candidates(
                loner.x, loner.y, FOOD_SEARCH_RADIUS, ("clans", "loners")
            )
            for cand in candidates:
                if cand is loner:
                    continue
                cand_species = getattr(cand, "species", None)
                if cand_species in primary_prey_species:
                    dx = loner.x - getattr(cand, "x", 0)
                    dy = loner.y - getattr(cand, "y", 0)
                    dist_sq = dx * dx + dy * dy
                    if dist_sq < nearest_prey_dist:
                        nearest_prey_dist = dist_sq
                        nearest_prey = cand

            if not nearest_prey and not primary_prey_exists:
                candidates = sim._nearby_candidates(
                    loner.x, loner.y, FOOD_SEARCH_RADIUS, ("clans", "loners")
                )
                for cand in candidates:
                    if cand is loner:
                        continue
                    cand_species = getattr(cand, "species", None)
                    if (
                        cand_species
                        and cand_species != loner.species
                        and getattr(cand, "can_cannibalize", False)
                    ):
                        dx = loner.x - getattr(cand, "x", 0)
                        dy = loner.y - getattr(cand, "y", 0)
                        dist_sq = dx * dx + dy * dy
                        if dist_sq < nearest_prey_dist:
                            nearest_prey_dist = dist_sq
                            nearest_prey = cand

            if nearest_prey and loner.hunger_timer >= LONER_HUNGER_SEEK:
                dx = nearest_prey.x - loner.x
                dy = nearest_prey.y - loner.y
                dist_sq = dx * dx + dy * dy
                if dist_sq > 0:
                    inv = 1.0 / math.sqrt(dist_sq)
                    # Preserve loner's current speed magnitude; only change direction.
                    current_speed = math.hypot(loner.vx, loner.vy)
                    if current_speed <= 0:
                        current_speed = random.uniform(*LONER_SPEED_INIT_RANGE)
                    loner.vx = (dx * inv) * current_speed
                    loner.vy = (dy * inv) * current_speed

        nearest_food = None
        nearest_dist = float("inf")
        candidates = sim._nearby_candidates(
            loner.x, loner.y, FOOD_SEARCH_RADIUS, ("food",)
        )
        for food_source in candidates:
            if not food_source.is_depleted():
                dx = loner.x - food_source.x
                dy = loner.y - food_source.y
                dist_sq = dx * dx + dy * dy
                if dist_sq < nearest_dist:
                    nearest_dist = dist_sq
                    nearest_food = food_source

        if loner.hunger_timer >= LONER_HUNGER_SEEK and nearest_food:
            dx = nearest_food.x - loner.x
            dy = nearest_food.y - loner.y
            dist_sq = dx * dx + dy * dy
            if dist_sq > 0:
                inv = 1.0 / math.sqrt(dist_sq)
                # Preserve loner's current speed magnitude; only change direction.
                current_speed = math.hypot(loner.vx, loner.vy)
                if current_speed <= 0:
                    current_speed = random.uniform(*LONER_SPEED_INIT_RANGE)
                loner.vx = (dx * inv) * current_speed
                loner.vy = (dy * inv) * current_speed

        if nearest_food and nearest_dist < (FOOD_RANGE * FOOD_RANGE):
            consumed = nearest_food.consume(loner.food_intake)
            if consumed > 0:
                loner.hunger_timer = max(
                    0, loner.hunger_timer - (consumed * FOOD_HUNGER_STEP)
                )
                old_hp = loner.hp
                loner.hp = min(loner.hp + (consumed * HP_PER_FOOD), loner.max_hp)
                sim.add_log(
                    (
                        "🍽️ {species} Einzelgänger isst {consumed} Food (+{hp_gain} HP)",
                        {
                            "species": loner.species,
                            "consumed": consumed,
                            "hp_gain": int(loner.hp - old_hp),
                        },
                    )
                )


def process_interactions(sim: SimulationModel) -> None:
    """Prozessiere alle Interaktionen zwischen Clans und Loners (extracted)."""
    if not hasattr(sim, "hunt_log_timer"):
        sim.hunt_log_timer = {}

    primary_prey_species = ["Icefang", "Crushed_Critters"]
    primary_prey_exists = any(
        (g.name in primary_prey_species and any(c.population > 0 for c in g.clans))
        for g in sim.groups
    ) or any(l.species in primary_prey_species for l in sim.loners)

    for i, group1 in enumerate(sim.groups):
        for j, group2 in enumerate(sim.groups):
            if i > j:
                continue

            for clan1 in group1.clans:
                for clan2 in group2.clans:
                    if group1 is group2 and clan1.clan_id >= clan2.clan_id:
                        continue
                    dist_sq = clan1.distance_to_clan(clan2)

                    interaction = sim.interaction_matrix.get(group1.name, {}).get(
                        group2.name, "Neutral"
                    )

                    if (
                        clan1.can_cannibalize
                        and clan2.can_cannibalize
                        and group1.name != group2.name
                    ):
                        if not primary_prey_exists:
                            interaction = "Aggressiv"

                    if (
                        group1.name == group2.name
                        and dist_sq < GRID_CELL_SIZE_SQ
                        and interaction != "Freundlich"
                    ):
                        dx = clan1.x - clan2.x
                        dy = clan1.y - clan2.y
                        dist_val = math.sqrt(dist_sq)
                        dist_calc = max(dist_val, MIN_DIST_CLAMP)
                        repel_strength = REPEL_STRENGTH
                        clan1.vx += (dx / dist_calc) * repel_strength
                        clan1.vy += (dy / dist_calc) * repel_strength
                    elif interaction == "Aggressiv" and dist_sq < (
                        HUNT_RANGE * HUNT_RANGE
                    ):
                        clan1.move_towards(
                            clan2.x, clan2.y, strength=MOVE_STRENGTH_FLEE
                        )
                        hunt_key = f"{group1.name}_{clan1.clan_id}_hunts_{group2.name}_{clan2.clan_id}"
                        if (
                            hunt_key not in sim.hunt_log_timer
                            or sim.time - sim.hunt_log_timer[hunt_key]
                            >= HUNT_LOG_COOLDOWN
                        ):
                            sim.hunt_log_timer[hunt_key] = sim.time
                            sim.add_log(
                                (
                                    "🎯 {attacker} Clan #{att_id} jagt {target} Clan #{tgt_id}! (Distanz: {dist}px)",
                                    {
                                        "attacker": group1.name,
                                        "att_id": clan1.clan_id,
                                        "target": group2.name,
                                        "tgt_id": clan2.clan_id,
                                        "dist": int(math.sqrt(dist_sq)),
                                    },
                                )
                            )

                    if dist_sq < (INTERACTION_RANGE * INTERACTION_RANGE):
                        if interaction == "Aggressiv":
                            attack_chance = (
                                ATTACK_CHANCE_DAY if sim.is_day else ATTACK_CHANCE_NIGHT
                            )
                            predators = ["Spores", "The_Corrupted", "Crushed_Critters"]
                            if group2.name == "Icefang" and group1.name in predators:
                                attack_chance = (
                                    AGGRESSIVE_ATTACK_CHANCE_DAY
                                    if sim.is_day
                                    else AGGRESSIVE_ATTACK_CHANCE_NIGHT
                                )
                            if random.random() < attack_chance:
                                old_pop = clan2.population
                                atk = getattr(clan1, "combat_strength", 1.0)
                                df = getattr(clan2, "combat_strength", 1.0)
                                damage = max(
                                    1,
                                    int(
                                        round(
                                            ATTACK_DAMAGE * atk / max(MIN_DEFENSE, df)
                                        )
                                    ),
                                )
                                alive = clan2.take_damage(damage, sim)
                                if old_pop > clan2.population:
                                    killed = old_pop - clan2.population
                                    sim.add_log(
                                        (
                                            "⚔️ {attacker} Clan #{att_id} → {target} Clan #{tgt_id} (-{killed} Mitglied)",
                                            {
                                                "attacker": group1.name,
                                                "att_id": clan1.clan_id,
                                                "target": group2.name,
                                                "tgt_id": clan2.clan_id,
                                                "killed": killed,
                                            },
                                        )
                                    )
                                    if clan1.can_cannibalize:
                                        food_gained = killed * FOOD_PER_KILL
                                        clan1.hunger_timer = max(
                                            0,
                                            clan1.hunger_timer
                                            - (food_gained * FOOD_HUNGER_STEP),
                                        )
                                        sim.add_log(
                                            (
                                                "🍖 {species} Clan #{clan_id} frisst {killed} Arach(s) (+{food} Food)",
                                                {
                                                    "species": group1.name,
                                                    "clan_id": clan1.clan_id,
                                                    "killed": killed,
                                                    "food": food_gained,
                                                },
                                            )
                                        )
                                    if not alive:
                                        sim.add_log(
                                            (
                                                "💀 {species} Clan #{clan_id} vernichtet!",
                                                {
                                                    "species": group2.name,
                                                    "clan_id": clan2.clan_id,
                                                },
                                            )
                                        )
                                    else:
                                        if clan2.population == 1:
                                            try:
                                                sim._pending_conversions.append(
                                                    (group2, clan2)
                                                )
                                            except Exception:
                                                pass

                        elif interaction == "Freundlich":
                            if group1.name == group2.name:
                                growth_chance = FRIENDLY_BASE_GROWTH
                                if group1.name == "Icefang":
                                    growth_chance = ICEFANG_GROWTH_CHANCE
                                if random.random() < growth_chance:
                                    if clan1.population < clan1.max_members:
                                        mu = GAUSS_MU
                                        sigma = GAUSS_SIGMA
                                        increase = int(round(random.gauss(mu, sigma)))
                                        increase = max(1, increase)
                                        space = clan1.max_members - clan1.population
                                        actual = min(increase, max(0, space))
                                        if actual > 0:
                                            clan1.population += actual
                                            sim.add_log(
                                                (
                                                    "🤝 {a} & {b}: Freundliche Begegnung (+{inc} Mitglied(er)) at positions ({x1},{y1}) & ({x2},{y2})",
                                                    {
                                                        "a": group1.name,
                                                        "b": group2.name,
                                                        "inc": actual,
                                                        "x1": int(clan1.x),
                                                        "y1": int(clan1.y),
                                                        "x2": int(clan2.x),
                                                        "y2": int(clan2.y),
                                                    },
                                                )
                                            )
                                            if hasattr(sim, "rnd_history"):
                                                sim.rnd_history.setdefault(
                                                    "clan_growth", []
                                                ).append(actual)
                                                if (
                                                    len(sim.rnd_history["clan_growth"])
                                                    > RND_HISTORY_TRIM_THRESHOLD
                                                ):
                                                    sim.rnd_history["clan_growth"] = (
                                                        sim.rnd_history["clan_growth"][
                                                            -RND_HISTORY_TRIM_SIZE:
                                                        ]
                                                    )
                            else:
                                try:
                                    if random.random() < FRIENDLY_STICK_CHANCE:
                                        clan1.move_towards(
                                            clan2.x,
                                            clan2.y,
                                            strength=MOVE_STRENGTH_FRIENDLY_STICK,
                                        )
                                        clan2.move_towards(
                                            clan1.x,
                                            clan1.y,
                                            strength=MOVE_STRENGTH_FRIENDLY_STICK,
                                        )
                                except Exception:
                                    pass

                        elif interaction == "Ängstlich":
                            dx = clan1.x - clan2.x
                            dy = clan1.y - clan2.y
                            dist_sq_local = dx * dx + dy * dy
                            if dist_sq_local > 0:
                                inv = 1.0 / math.sqrt(dist_sq_local)
                                clan1.vx += (dx * inv) * FRIENDLY_STICK_STRENGTH
                                clan1.vy += (dy * inv) * FRIENDLY_STICK_STRENGTH

    loners_to_remove = []
    for group in sim.groups:
        for clan in group.clans:
            for loner in sim.loners:
                dist_sq = clan.distance_to_loner(loner)
                interaction = sim.interaction_matrix.get(group.name, {}).get(
                    loner.species, "Neutral"
                )

                if interaction == "Aggressiv" and dist_sq < (HUNT_RANGE * HUNT_RANGE):
                    clan.move_towards(loner.x, loner.y, strength=CHASE_STRENGTH)
                    hunt_key = f"{group.name}_{clan.clan_id}_hunts_loner_{loner.species}_{id(loner)}"
                    if (
                        hunt_key not in sim.hunt_log_timer
                        or sim.time - sim.hunt_log_timer[hunt_key] >= HUNT_LOG_COOLDOWN
                    ):
                        sim.hunt_log_timer[hunt_key] = sim.time
                        sim.add_log(
                            (
                                "🎯 {attacker} Clan #{att_id} jagt {loner_species} Einzelgänger! (Distanz: {dist}px)",
                                {
                                    "attacker": group.name,
                                    "att_id": clan.clan_id,
                                    "loner_species": loner.species,
                                    "dist": int(math.sqrt(dist_sq)),
                                },
                            )
                        )

                if dist_sq < (INTERACTION_RANGE * INTERACTION_RANGE):
                    if interaction == "Aggressiv":
                        attack_chance = (
                            CHASE_ATTACK_CHANCE_DAY
                            if sim.is_day
                            else CHASE_ATTACK_CHANCE_NIGHT
                        )
                        if random.random() < attack_chance:
                            atk = getattr(clan, "combat_strength", 1.0)
                            df = getattr(loner, "combat_strength", 1.0)
                            damage = max(
                                1,
                                int(round(ATTACK_DAMAGE * atk / max(MIN_DEFENSE, df))),
                            )
                            loner.hp -= damage
                            if loner.hp <= 0:
                                loners_to_remove.append(loner)
                                sim.add_log(
                                    (
                                        "⚔️ {attacker} Clan #{att_id} tötet {loner_species} Einzelgänger",
                                        {
                                            "attacker": group.name,
                                            "att_id": clan.clan_id,
                                            "loner_species": loner.species,
                                        },
                                    )
                                )
                                sim.stats["deaths"]["combat"][loner.species] = (
                                    sim.stats["deaths"]["combat"].get(loner.species, 0)
                                    + 1
                                )
                                if clan.can_cannibalize:
                                    food_gained = FOOD_PER_KILL
                                    clan.hunger_timer = max(
                                        0,
                                        clan.hunger_timer
                                        - (food_gained * FOOD_HUNGER_STEP),
                                    )
                                    sim.add_log(
                                        (
                                            "🍖 {species} Clan #{clan_id} frisst {loner_species} (+{food} Food)",
                                            {
                                                "species": group.name,
                                                "clan_id": clan.clan_id,
                                                "loner_species": loner.species,
                                                "food": food_gained,
                                            },
                                        )
                                    )

                    elif interaction == "Freundlich":
                        join_chance = JOIN_BASE_CHANCE
                        if loner.hunger_timer >= JOIN_HUNGER_THRESHOLD:
                            join_chance = JOIN_HUNGRY_CHANCE
                        if (
                            random.random() < join_chance
                            and loner.species == group.name
                        ):
                            clan.population += 1
                            loners_to_remove.append(loner)
                            reason = (
                                "hungrig"
                                if loner.hunger_timer >= HUNGRY_THRESHOLD
                                else "freundlich"
                            )
                            sim.add_log(
                                (
                                    "👥 {species} Einzelgänger ({reason}) tritt {group} Clan #{clan_id} bei ({old} → {new})",
                                    {
                                        "species": loner.species,
                                        "reason": reason,
                                        "group": group.name,
                                        "clan_id": clan.clan_id,
                                        "old": clan.population - 1,
                                        "new": clan.population,
                                    },
                                )
                            )
                            if clan.population > clan.max_members:
                                group.check_clan_splits()

    for loner in loners_to_remove:
        if loner in sim.loners:
            sim.loners.remove(loner)

    sim._process_loner_clan_formation()

    try:
        if hasattr(sim, "_pending_conversions") and sim._pending_conversions:
            for group, clan in list(sim._pending_conversions):
                try:
                    if clan in group.clans and clan.population == 1:
                        loner = Loner(
                            clan.species,
                            clan.x,
                            clan.y,
                            clan.color,
                            clan.hp_per_member,
                            clan.food_intake,
                            0,
                            clan.can_cannibalize,
                        )
                        sim.loners.append(loner)
                        try:
                            group.clans.remove(clan)
                        except Exception:
                            pass
                        sim.add_log(
                            (
                                "⚠️ Clan #{clan_id} von {group} reduzierte sich auf 1 und wurde zu Einzelgänger konvertiert.",
                                {"clan_id": clan.clan_id, "group": group.name},
                            )
                        )
                except Exception:
                    pass
            sim._pending_conversions = []
    except Exception:
        pass


def process_loner_clan_formation(sim: SimulationModel) -> None:
    """Einzelgänger können sich zu einem neuen Clan zusammenschließen (extracted)."""
    species_loners = {}
    for loner in sim.loners:
        species_loners.setdefault(loner.species, []).append(loner)

    for species_name, loners_list in species_loners.items():
        if len(loners_list) < 2:
            continue
        group = None
        for g in sim.groups:
            if g.name == species_name:
                group = g
                break
        if not group or len(group.clans) >= MAX_CLANS_PER_SPECIES:
            continue

        checked_loners = []
        for i, loner1 in enumerate(loners_list):
            if loner1 in checked_loners:
                continue
            nearby_loners = [loner1]
            for j, loner2 in enumerate(loners_list):
                if i >= j or loner2 in checked_loners:
                    continue
                dx = loner1.x - loner2.x
                dy = loner1.y - loner2.y
                dist_sq = dx * dx + dy * dy
                if dist_sq < (FORMATION_RANGE * FORMATION_RANGE):
                    nearby_loners.append(loner2)

            if len(nearby_loners) >= 2 and random.random() < FORMATION_PROBABILITY:
                center_x = sum(l.x for l in nearby_loners) / len(nearby_loners)
                center_y = sum(l.y for l in nearby_loners) / len(nearby_loners)
                new_clan = Clan(
                    group.next_clan_id,
                    species_name,
                    center_x,
                    center_y,
                    len(nearby_loners),
                    nearby_loners[0].color,
                    group.max_members,
                    nearby_loners[0].hp,
                    group.food_intake,
                    0,
                    nearby_loners[0].can_cannibalize,
                )
                group.clans.append(new_clan)
                group.next_clan_id += 1
                for loner in nearby_loners:
                    if loner in sim.loners:
                        sim.loners.remove(loner)
                    checked_loners.append(loner)
                sim.add_log(
                    (
                        "🤝 {count} {species} Einzelgänger schließen sich zu Clan #{clan_id} zusammen!",
                        {
                            "count": len(nearby_loners),
                            "species": species_name,
                            "clan_id": new_clan.clan_id,
                        },
                    )
                )
                break
