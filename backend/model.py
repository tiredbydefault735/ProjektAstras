"""
Simulation Model - Neu aufgebaut für smoothe, glitch-freie Bewegung
"""

from __future__ import annotations
import simpy
import random
import math
import logging
from typing import TYPE_CHECKING, Optional, List, Dict, Any, Tuple, Union, Generator

from config import (
    SPAWN_PADDING,
    GRID_CELL_SIZE,
    GRID_CELL_SIZE_SQ,
    HUNGER_THRESHOLD_RANGE,
    HUNGER_ALERT,
    HUNGER_TIMER_DEATH,
    RND_HISTORY_LIMIT,
    DAY_NIGHT_CYCLE_DURATION,
    TRANSITION_DURATION,
    POP_HISTORY_STEP,
    MAX_LOGS,
    FOOD_DEFAULT_AMOUNT,
    DEFAULT_FOOD_PLACES,
    MAP_DEFAULT_HEIGHT,
    MAP_DEFAULT_WIDTH,
    TEMPERATURE_MIN,
    TEMPERATURE_MAX,
    SPECIES_DEFAULT_MIN_SURVIVAL_TEMP,
    SPECIES_DEFAULT_MAX_SURVIVAL_TEMP,
    FOOD_RANGE,
    FOOD_SEARCH_RADIUS,
    INTERACTION_RANGE,
    HUNT_RANGE,
    HUNT_LOG_COOLDOWN,
    FORMATION_RANGE,
    MAP_EDGE_PADDING,
    TEMP_CHANGE_INTERVAL,
    FOOD_REGEN_PROB,
    COMBAT_STRENGTH_RANGE,
    LONER_HUNGER_RANGE,
    MAX_CLANS_PER_SPECIES,
    BASE_TEMPERATURE_FALLBACK_RANGE,
    LONER_DAMAGE_MIN,
    LONER_DAMAGE_MAX,
    CLAN_DAMAGE_MIN,
    CLAN_DAMAGE_MAX,
    FOOD_HUNGER_STEP,
    SPAWN_THRESHOLD_HIGH,
    SPAWN_THRESHOLD_LOW,
    ATTACK_CHANCE_DAY,
    ATTACK_CHANCE_NIGHT,
    AGGRESSIVE_ATTACK_CHANCE_DAY,
    AGGRESSIVE_ATTACK_CHANCE_NIGHT,
    RND_HISTORY_TRIM_THRESHOLD,
    RND_HISTORY_TRIM_SIZE,
    FRIENDLY_STICK_CHANCE,
    LONER_VELOCITY_RANGE,
    CLAN_VELOCITY_RANGE,
    NIGHT_SPEED_MODIFIER,
    RANDOM_MOVE_PROB,
    REGEN_CHOICES,
    LONER_SPEED_INIT_RANGE,
    LONER_SPEED_ALT_RANGE,
    MAX_CLANS_DEFAULT,
    SPLIT_DENOM,
    SPLIT_BASE_CHANCE,
    SPLIT_POP_FRAC,
    FRIENDLY_GROWTH_CHANCE_DEFAULT,
    ICEFANG_GROWTH_CHANCE,
    FRIENDLY_BASE_GROWTH,
    JOIN_BASE_CHANCE,
    JOIN_HUNGRY_CHANCE,
    JOIN_HUNGER_THRESHOLD,
    FORMATION_PROBABILITY,
    REGION_DEFAULT_CHANCE,
    ICEFANG_BOOST_HP_MULT,
    ICEFANG_BOOST_COMBAT_MULT,
    ICEFANG_BOOST_HUNGER_DELTA,
    SPORES_BOOST_HP_MULT,
    SPORES_BOOST_COMBAT_MULT,
    SPORES_BOOST_HUNGER_DELTA,
    CRUSHED_BOOST_HP_MULT,
    CRUSHED_BOOST_COMBAT_MULT,
    CRUSHED_BOOST_HUNGER_DELTA,
    CORRUPTED_BOOST_HP_MULT,
    CORRUPTED_BOOST_COMBAT_MULT,
    CORRUPTED_BOOST_HUNGER_DELTA,
    ICEFANG_COLOR,
    CRUSHED_CRITTERS_COLOR,
    SPORES_COLOR,
    THE_CORRUPTED_COLOR,
    SPAWN_SINGLE_COUNT,
    CHASE_STRENGTH,
    CHASE_ATTACK_CHANCE_DAY,
    CHASE_ATTACK_CHANCE_NIGHT,
    MOVE_TOWARDS_DEFAULT_STRENGTH,
    MOVE_TOWARDS_MAX_SPEED,
    MOVE_STRENGTH_NEAREST_FOOD,
    MOVE_STRENGTH_FRIENDLY_STICK,
    MOVE_STRENGTH_FLEE,
    GAUSS_MU,
    GAUSS_SIGMA,
    GRID_CELL_MIN,
    SIM_STEP_TIMEOUT,
    DEFAULT_COLOR,
    FOOD_INTAKE_DEFAULT,
    LONER_SPAWN_RANGE,
    CLAN_DEATH_DIVISOR,
    DAY_NIGHT_TEMP_DELTA,
    TEMP_DAMAGE_BASE_LONER,
    TEMP_DAMAGE_PER_STEP_LONER,
    TEMP_DEGREE_STEP,
    TEMP_DAMAGE_BASE_CLAN,
    TEMPERATURE_PRECISION,
    LONER_SEARCH_BOOST,
    BASE_PREY_SPEED,
    BASE_FOOD_SPEED,
    HP_PER_FOOD,
    CLAN_SPLIT_DIVISOR,
    CLAN_TEMP_SURVIVAL_CHANCE,
    MAX_HP_FALLBACK,
    MIN_DIST_CLAMP,
    REPEL_STRENGTH,
    MIN_DEFENSE,
    FRIENDLY_STICK_STRENGTH,
    FOOD_PER_KILL,
    HUNGRY_THRESHOLD,
    SPEED_MULT_MIN,
    SPEED_MULT_MAX,
    START_POP_THRESHOLD,
    DEFAULT_HP,
    ICEFANG_HP_CAP,
    OTHER_HP_CAP,
    TEMP_CHANGE_DELTA,
    ATTACK_DAMAGE,
    LONER_HUNGER_SEEK,
)

logger = logging.getLogger(__name__)

# Entities are extracted to backend.entities to keep this file concise
from backend.entities import FoodSource, Loner, Clan


class SpeciesGroup:
    """Verwaltet alle Clans einer Spezies."""

    def __init__(
        self,
        env: simpy.Environment,
        name: str,
        start_population: int,
        color: str,
        max_members: int,
        hp_per_member: float,
        food_intake: float,
        can_cannibalize: bool,
        map_width: float,
        map_height: float,
    ) -> None:
        self.env: simpy.Environment = env
        self.name: str = name
        self.color: str = color
        self.max_members: int = max_members
        self.hp_per_member: float = hp_per_member
        self.food_intake: float = food_intake
        self.can_cannibalize: bool = can_cannibalize
        self.map_width: float = map_width
        self.map_height: float = map_height
        self.max_clans: int = MAX_CLANS_DEFAULT
        self.clans: List[Clan] = []
        self.next_clan_id: int = 0

        # Create initial clan if population > 0
        if start_population > 0:
            x = random.uniform(MAP_EDGE_PADDING, map_width - MAP_EDGE_PADDING)
            y = random.uniform(MAP_EDGE_PADDING, map_height - MAP_EDGE_PADDING)
            clan = Clan(
                str(self.next_clan_id),
                name,
                x,
                y,
                start_population,
                color,
                max_members,
                hp_per_member,
                food_intake,
                0,
                can_cannibalize,
            )
            self.clans.append(clan)
            self.next_clan_id += 1

        self.process = env.process(self.live())

    def live(self) -> Generator[simpy.events.Event, None, None]:
        while True:
            yield self.env.timeout(SIM_STEP_TIMEOUT)
            is_day = getattr(self.env, "sim_model", None) and getattr(
                self.env.sim_model, "is_day", True
            )

            # Use global clan speed multiplier from SimulationModel when available
            sim_model = getattr(self.env, "sim_model", None)
            clan_speed_mult = getattr(sim_model, "clan_speed_multiplier", 1.0)

            for clan in list(self.clans):
                clan.update(self.map_width, self.map_height, is_day, clan_speed_mult)

                # Hunger death
                if clan.hunger_timer >= HUNGER_TIMER_DEATH:
                    deaths = max(1, clan.population // CLAN_DEATH_DIVISOR)
                    clan.population = max(0, clan.population - deaths)

                if clan.population <= 0:
                    # mark for removal; actual removal occurs in check_clan_splits or parent
                    continue

                # occasional split handling delegated to check_clan_splits

            # Remove empty clans
            self.clans = [c for c in self.clans if c.population > 0]

            # Try splits
            self.check_clan_splits()

    def check_clan_splits(self) -> None:
        """Split clans when they exceed thresholds."""
        for clan in self.clans[:]:
            if len(self.clans) >= MAX_CLANS_PER_SPECIES:
                continue

            if clan.population > clan.max_members:
                split_chance = 1.0
            elif clan.population >= clan.max_members * SPLIT_POP_FRAC:
                progress = (clan.population - clan.max_members * SPLIT_POP_FRAC) / (
                    clan.max_members * SPLIT_POP_FRAC
                )
                split_chance = (
                    math.exp(-((1 - progress) ** 2) / SPLIT_DENOM) * SPLIT_BASE_CHANCE
                )
            else:
                continue

            if random.random() < split_chance:
                pop_half = clan.population // CLAN_SPLIT_DIVISOR
                clan.population = clan.population - pop_half
                new_x = clan.x + random.uniform(-SPAWN_PADDING, SPAWN_PADDING)
                new_y = clan.y + random.uniform(-SPAWN_PADDING, SPAWN_PADDING)
                new_x = max(SPAWN_PADDING, min(new_x, self.map_width - SPAWN_PADDING))
                new_y = max(SPAWN_PADDING, min(new_y, self.map_height - SPAWN_PADDING))
                new_clan = Clan(
                    str(self.next_clan_id),
                    clan.species,
                    new_x,
                    new_y,
                    pop_half,
                    clan.color,
                    clan.max_members,
                    clan.hp_per_member,
                    clan.food_intake,
                    0,
                    clan.can_cannibalize,
                )
                self.clans.append(new_clan)
                self.next_clan_id += 1

                if hasattr(self.env, "sim_model"):
                    try:
                        self.env.sim_model.add_log(
                            (
                                "✂️ {species} Clan #{old_id} teilt sich! → Clan #{new_id} (je {members} Mitglieder)",
                                {
                                    "species": self.name,
                                    "old_id": clan.clan_id,
                                    "new_id": new_clan.clan_id,
                                    "members": clan.population,
                                },
                            )
                        )
                        self.env.sim_model.add_log(
                            (
                                "🎉 Neue Population: Clan #{old_id} ({old_members}) + Clan #{new_id} ({new_members}) = {total} Mitglieder",
                                {
                                    "old_id": clan.clan_id,
                                    "old_members": clan.population,
                                    "new_id": new_clan.clan_id,
                                    "new_members": pop_half,
                                    "total": clan.population + pop_half,
                                },
                            )
                        )
                    except Exception:
                        pass

class SimulationModel:
    def add_log(self, message: Union[str, Tuple[str, Dict[str, Any]], Dict[str, Any]]) -> None:
        """Log-Nachricht hinzufügen.

        Accepts either:
          - a plain string (legacy), or
          - a tuple/list (msgid, params_dict) where msgid is a translation key
            present in the JSON catalog and params_dict contains simple values
            for formatting.

        Stored log entries are structured dicts so the frontend can translate
        and format them at display time using the JSON translations.
        """
        t = getattr(self, "time", 0)
        # ensure logs container exists
        if not hasattr(self, "logs"):
            self.logs: List[Dict[str, Any]] = []
        if not hasattr(self, "max_logs"):
            self.max_logs: int = MAX_LOGS

        entry = None
        try:
            # structured form: (msgid, params)
            if isinstance(message, (list, tuple)) and len(message) >= 1:
                msgid = message[0]
                params = (
                    message[1]
                    if len(message) > 1 and isinstance(message[1], dict)
                    else {}
                )
                entry = {"time": t, "msgid": str(msgid), "params": dict(params)}
            elif isinstance(message, dict) and "msgid" in message:
                entry = {
                    "time": t,
                    "msgid": str(message.get("msgid")),
                    "params": dict(message.get("params", {})),
                }
            else:
                # fallback: store raw string (legacy behavior)
                entry = {"time": t, "raw": str(message)}
        except Exception:
            # absolute fallback
            entry = {"time": t, "raw": str(message)}

        self.logs.append(entry)
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs :]

    def setup(
        self,
        species_config: Dict[str, Any],
        population_overrides: Dict[str, int],
        food_places: int = DEFAULT_FOOD_PLACES,
        food_amount: float = FOOD_DEFAULT_AMOUNT,
        start_temperature: Optional[float] = None,
        start_is_day: bool = True,
        region_name: Optional[str] = None,
        initial_food_positions: Optional[List[Dict[str, float]]] = None,
        rng_seed: Optional[int] = None,
    ) -> None:
        """Initialisiere Simulation."""

        # Re-initialize SimPy environment for each setup
        self.env = simpy.Environment()
        # allow group processes to reference back to this SimulationModel
        try:
            setattr(self.env, "sim_model", self)
        except Exception:
            pass
        # Ensure time exists before any logging
        self.time = 0
        self.groups: List[SpeciesGroup] = []
        self.loners: List[Loner] = []
        # Recent random draws for visualization (kept as short lists)
        self.rnd_history: Dict[str, List[Any]] = {
            "regen": [],  # food regeneration amounts
            "clan_growth": [],  # growth increments from friendly encounters
            "loner_spawn": [],  # spawn counts per spawn event
        }

        # Ensure map dimensions are always set before use
        self.map_width = MAP_DEFAULT_WIDTH
        self.map_height = MAP_DEFAULT_HEIGHT
        # Spatial grid for neighbor queries (uniform grid)
        # Cell size chosen near typical interaction radius to balance bucket counts
        self.grid_cell_size = GRID_CELL_SIZE
        self._grid = {}

        # Movement multipliers
        self.clan_speed_multiplier = 1.0
        self.loner_speed_multiplier = 1.0

        # Re-initialize statistics to ensure temperature is included and avoid AttributeError
        self.stats: Dict[str, Any] = {
            "species_counts": {},  # Initial counts per species
            "deaths": {
                "combat": {},  # Deaths by combat per species
                "starvation": {},  # Deaths by starvation per species
                "temperature": {},  # Deaths by temperature per species
            },
            "max_clans": 0,
            "food_places": 0,
            "population_history": {},  # Track population over time
        }

        # Temperatur-System initialisieren
        if start_temperature is not None:
            self.base_temperature = start_temperature  # Basis-Temperatur (Mittelwert)
            self.current_temperature = (
                start_temperature  # Vom Slider gesetzte Temperatur
            )
        else:
            self.base_temperature = random.uniform(
                *BASE_TEMPERATURE_FALLBACK_RANGE
            )  # Fallback
            self.current_temperature = self.base_temperature
        self.temp_change_timer = 0  # Timer für Temperatur-Änderungen
        self.day_night_temp_offset = 0  # Aktueller Tag/Nacht Offset

        # Tag/Nacht-Zyklus initialisieren
        self.is_day = start_is_day  # Start-Tageszeit aus UI
        self.day_night_timer = 0
        self.day_night_cycle_duration = DAY_NIGHT_CYCLE_DURATION
        self.transition_duration = TRANSITION_DURATION
        self.in_transition = False
        self.transition_timer = 0
        self.transition_to_day = True  # Zielzustand des Übergangs

        # Optionally seed the global RNG so initial placement is reproducible
        # when a seed is provided by the UI. This ensures frontend preview
        # and backend initialization can share the same placement when the
        # same seed is used.
        if rng_seed is not None:
            try:
                random.seed(rng_seed)
            except Exception:
                pass

        # Farben für Spezies
        color_map = {
            "Icefang": ICEFANG_COLOR,
            "Crushed_Critters": CRUSHED_CRITTERS_COLOR,
            "Spores": SPORES_COLOR,
            "The_Corrupted": THE_CORRUPTED_COLOR,
        }

        # Speichere Config für Interaktionen
        self.species_config = species_config

        # Region modifiers: per-region multipliers/deltas applied to species
        # Example keys: 'Evergreen_Forest', 'Desert', 'Snowy_Abyss', 'Wasteland', 'Corrupted_Caves'
        self.region_name = region_name or "Default"
        region_modifiers = {
            "Default": {},
            "Snowy_Abyss": {
                # Icefang native to Snowy Abyss
                "Icefang": {
                    "base": {"hp_mult": 1.0, "combat_mult": 1.0, "hunger_delta": 0},
                    "boost": {
                        "hp_mult": ICEFANG_BOOST_HP_MULT,
                        "combat_mult": ICEFANG_BOOST_COMBAT_MULT,
                        "hunger_delta": ICEFANG_BOOST_HUNGER_DELTA,
                    },
                    "chance": REGION_DEFAULT_CHANCE,
                }
            },
            "Evergreen_Forest": {
                # Spores native to Evergreen Forest
                "Spores": {
                    "base": {"hp_mult": 1.0, "combat_mult": 1.0, "hunger_delta": 0},
                    "boost": {
                        "hp_mult": SPORES_BOOST_HP_MULT,
                        "combat_mult": SPORES_BOOST_COMBAT_MULT,
                        "hunger_delta": SPORES_BOOST_HUNGER_DELTA,
                    },
                    "chance": REGION_DEFAULT_CHANCE,
                }
            },
            "Wasteland": {
                # Crushed_Critters native to Wasteland
                "Crushed_Critters": {
                    "base": {"hp_mult": 1.0, "combat_mult": 1.0, "hunger_delta": 0},
                    "boost": {
                        "hp_mult": CRUSHED_BOOST_HP_MULT,
                        "combat_mult": CRUSHED_BOOST_COMBAT_MULT,
                        "hunger_delta": CRUSHED_BOOST_HUNGER_DELTA,
                    },
                    "chance": REGION_DEFAULT_CHANCE,
                }
            },
            "Corrupted_Caves": {
                # The_Corrupted native to Corrupted Caves
                "The_Corrupted": {
                    "base": {"hp_mult": 1.0, "combat_mult": 1.0, "hunger_delta": 0},
                    "boost": {
                        "hp_mult": CORRUPTED_BOOST_HP_MULT,
                        "combat_mult": CORRUPTED_BOOST_COMBAT_MULT,
                        "hunger_delta": CORRUPTED_BOOST_HUNGER_DELTA,
                    },
                    "chance": REGION_DEFAULT_CHANCE,
                }
            },
        }
        self._region_mods: Dict[str, Any] = region_modifiers.get(self.region_name, {})

        # Baue Interaktionsmatrix aus species.json
        self.interaction_matrix = {}
        for species_name, stats in species_config.items():
            if "interactions" in stats:
                self.interaction_matrix[species_name] = stats["interactions"]

        # Determine requested total population from UI overrides. If the total
        # is small (<10) we start with only loners and avoid creating initial
        # clans so the simulation begins as loner-only until population grows.
        total_requested = (
            sum(int(v) for v in population_overrides.values())
            if population_overrides
            else 0
        )

        # Erstelle Gruppen
        for species_name, stats in species_config.items():
            # If total requested population is below threshold, create species
            # group without initial clan (start_pop=0). Otherwise create the
            # initial clan with the requested start population.
            start_pop = (
                population_overrides.get(species_name, 0)
                if total_requested >= START_POP_THRESHOLD
                else 0
            )
            color = color_map.get(species_name, DEFAULT_COLOR)
            # Cap hp per member to avoid extreme per-member HP values from data
            raw_hp = stats.get("hp", DEFAULT_HP)
            if species_name == "Icefang":
                hp = min(
                    raw_hp, ICEFANG_HP_CAP
                )  # Icefang are tough but not invulnerable
            else:
                hp = min(raw_hp, OTHER_HP_CAP)
            food_intake = stats.get("food_intake", FOOD_INTAKE_DEFAULT)
            # Spores und Corrupted können kannibalisieren
            can_cannibalize = species_name in ["Spores", "The_Corrupted"]

            group = SpeciesGroup(
                self.env,
                species_name,
                start_pop,
                color,
                stats["max_clan_members"],
                hp,
                food_intake,
                can_cannibalize,
                self.map_width,
                self.map_height,
            )
            # Apply region modifiers to newly created group's clans. Support
            # the new probabilistic 'boost' model as well as legacy flat dicts.
            mods = self._region_mods.get(species_name)
            if mods:
                # choose which modifier set to use: support new {'base','boost','chance'}
                if "boost" in mods or "base" in mods:
                    chance = float(mods.get("chance", 0.0))
                    use_boost = random.random() < chance
                    selected = mods.get("boost") if use_boost else mods.get("base", {})
                else:
                    # legacy format: mods is directly the flat dict
                    selected = mods

                for clan in group.clans:
                    # adjust per-member HP
                    if "hp_mult" in selected:
                        clan.hp_per_member = int(
                            max(1, clan.hp_per_member * selected["hp_mult"])
                        )
                    # adjust combat strength multiplier if present
                    if "combat_mult" in selected:
                        if hasattr(clan, "combat_strength"):
                            clan.combat_strength *= selected["combat_mult"]
                        else:
                            clan.combat_strength = (
                                random.uniform(*COMBAT_STRENGTH_RANGE)
                                * selected["combat_mult"]
                            )
                    # adjust hunger threshold (higher = seek food later)
                    if "hunger_delta" in selected:
                        clan.hunger_threshold = (
                            getattr(clan, "hunger_threshold", HUNGER_ALERT)
                            + selected["hunger_delta"]
                        )
            # Setze hunger_timer aller Clans auf 0
            for clan in group.clans:
                clan.hunger_timer = 0
            self.groups.append(group)

        # Erstelle Einzelgänger. If the user-requested total population is
        # small (<10) spawn exactly that many loners per species and do not
        # create clans on setup. Otherwise keep legacy behavior and spawn a
        # few loners (2-5) in addition to any initial clans.
        for species_name, stats in species_config.items():
            # Überspringe deaktivierte Spezies (Population = 0)
            if population_overrides.get(species_name, 0) == 0:
                continue

            color = color_map.get(species_name, DEFAULT_COLOR)
            hp = stats.get("hp", DEFAULT_HP)
            food_intake = stats.get("food_intake", FOOD_INTAKE_DEFAULT)
            can_cannibalize = species_name in ["Spores", "The_Corrupted"]

            if total_requested < START_POP_THRESHOLD:
                # spawn exactly the requested number of loners for this species
                num_loners = int(population_overrides.get(species_name, 0))
            else:
                num_loners = random.randint(*LONER_SPAWN_RANGE)

            for _ in range(num_loners):
                x = random.uniform(SPAWN_PADDING, self.map_width - SPAWN_PADDING)
                y = random.uniform(SPAWN_PADDING, self.map_height - SPAWN_PADDING)
                loner = Loner(
                    species_name, x, y, color, hp, food_intake, 0, can_cannibalize
                )
                # Apply region modifiers to loner if present (probabilistic boost supported)
                mods = self._region_mods.get(species_name)
                if mods:
                    if "boost" in mods or "base" in mods:
                        chance = float(mods.get("chance", 0.0))
                        use_boost = random.random() < chance
                        selected = (
                            mods.get("boost") if use_boost else mods.get("base", {})
                        )
                    else:
                        selected = mods

                    if "hp_mult" in selected:
                        loner.hp = int(max(1, loner.hp * selected["hp_mult"]))
                        loner.max_hp = loner.hp
                    if "combat_mult" in selected:
                        if hasattr(loner, "combat_strength"):
                            loner.combat_strength *= selected["combat_mult"]
                        else:
                            loner.combat_strength = random.uniform(
                                *COMBAT_STRENGTH_RANGE
                            ) * selected.get("combat_mult", 1.0)
                    if "hunger_delta" in selected:
                        loner.hunger_threshold = (
                            getattr(
                                loner, "hunger_threshold", HUNGER_THRESHOLD_RANGE[1]
                            )
                            + selected["hunger_delta"]
                        )

                self.loners.append(loner)

        # Erstelle Nahrungsplätze
        self.food_sources: List[FoodSource] = []
        if initial_food_positions:
            # Use provided positions (list of dicts with 'x' and 'y') to ensure
            # preview matches backend initialization exactly.
            for i in range(min(len(initial_food_positions), food_places)):
                pos = initial_food_positions[i]
                x = pos.get(
                    "x",
                    random.uniform(MAP_EDGE_PADDING, self.map_width - MAP_EDGE_PADDING),
                )
                y = pos.get(
                    "y",
                    random.uniform(
                        MAP_EDGE_PADDING, self.map_height - MAP_EDGE_PADDING
                    ),
                )
                amt = pos.get("amount", food_amount)
                fs = FoodSource(x, y, amt)
                self.food_sources.append(fs)
            # If fewer provided than requested, generate remaining randomly.
            for _ in range(len(self.food_sources), food_places):
                x = random.uniform(MAP_EDGE_PADDING, self.map_width - MAP_EDGE_PADDING)
                y = random.uniform(MAP_EDGE_PADDING, self.map_height - MAP_EDGE_PADDING)
                food_source = FoodSource(x, y, food_amount)
                self.food_sources.append(food_source)
        else:
            for _ in range(food_places):
                x = random.uniform(MAP_EDGE_PADDING, self.map_width - MAP_EDGE_PADDING)
                y = random.uniform(MAP_EDGE_PADDING, self.map_height - MAP_EDGE_PADDING)
                food_source = FoodSource(x, y, food_amount)
                self.food_sources.append(food_source)

        # Referenz für Logging (removed for SimPy compatibility)
        # self.env.sim_model = self

        total_pop = sum(sum(c.population for c in g.clans) for g in self.groups)
        self.add_log(
            (
                "Start: {species_count} Spezies, {total_pop} Mitglieder, {loner_count} Einzelgänger",
                {
                    "species_count": len(self.groups),
                    "total_pop": total_pop,
                    "loner_count": len(self.loners),
                },
            )
        )

        # Initialize statistics
        self.stats["food_places"] = food_places
        total_clans = sum(len(g.clans) for g in self.groups)
        self.stats["max_clans"] = total_clans
        self.stats["temperature"] = round(
            self.current_temperature, TEMPERATURE_PRECISION
        )
        self.stats["is_day"] = self.is_day

        # Count initial population per species
        for group in self.groups:
            species_name = group.name
            clan_pop = sum(c.population for c in group.clans)
            loner_pop = sum(1 for l in self.loners if l.species == species_name)
            self.stats["species_counts"][species_name] = clan_pop + loner_pop
            self.stats["deaths"]["combat"][species_name] = 0
            self.stats["deaths"]["starvation"][species_name] = 0
            self.stats["deaths"]["temperature"][species_name] = 0
    def _calculate_transition_progress(self) -> float:
        """Calculate transition progress: 0.0 = full night, 1.0 = full day."""
        if not self.in_transition:
            # Not in transition - return stable value
            return 1.0 if self.is_day else 0.0

        # During transition
        progress_ratio = self.transition_timer / self.transition_duration

        if self.transition_to_day:
            # Transitioning from night (0.0) to day (1.0)
            return progress_ratio
        else:
            # Transitioning from day (1.0) to night (0.0)
            return 1.0 - progress_ratio

    # --- Spatial grid helpers ---
    def _build_spatial_grid(self) -> None:
        # Delegate grid building to SpatialGrid helper
        from backend.spatial import SpatialGrid

        if (
            not hasattr(self, "_spatial")
            or getattr(self._spatial, "grid_cell_size", None) != self.grid_cell_size
        ):
            self._spatial = SpatialGrid(self.grid_cell_size)

        self._spatial.build(
            self.groups, self.loners, self.food_sources, self.grid_cell_size
        )
        self._grid = self._spatial.grid

    def _nearby_candidates(self, x: float, y: float, radius: float, kinds: Tuple[str, ...] = ("clans", "loners", "food")) -> List[Any]:
        # Delegate nearby-candidate lookup to SpatialGrid
        if not hasattr(self, "_spatial"):
            from backend.spatial import SpatialGrid

            self._spatial = SpatialGrid(self.grid_cell_size)
            self._spatial.build(
                self.groups, self.loners, self.food_sources, self.grid_cell_size
            )

        return self._spatial.nearby_candidates(x, y, radius, kinds)

    def _process_food_seeking(self) -> None:
        from backend.processors import process_food_seeking

        process_food_seeking(self)

    def _process_interactions(self) -> None:
        from backend.processors import process_interactions

        process_interactions(self)

    def step(self) -> Dict[str, Any]:

        # Spawn loners (delegated)
        try:
            from backend.spawn import spawn_loners

            spawn_loners(self)
        except Exception:
            # fallback: no-op but avoid breaking step
            pass
        """Simulationsschritt."""
        # SimPy step
        target = self.env.now + SIM_STEP_TIMEOUT
        self.env.run(until=target)
        self.time = int(self.env.now)
        # Container for conversions (clan -> loner) collected during this step
        self._pending_conversions: List[Any] = []

        # Track population history every POP_HISTORY_STEP steps
        if self.time % POP_HISTORY_STEP == 0:
            for species_name in self.species_config.keys():
                if species_name not in self.stats["population_history"]:
                    self.stats["population_history"][species_name] = []
                # Count current population for this species
                # Groups store species name in 'name' attribute
                count = sum(
                    sum(c.population for c in g.clans)
                    for g in self.groups
                    if g.name == species_name
                )
                count += sum(1 for l in self.loners if l.species == species_name)
                self.stats["population_history"][species_name].append(count)

        # Temperature, regeneration and survival handling (delegated)
        try:
            from backend.temperature import update_and_apply

            update_and_apply(self)
        except Exception:
            # keep step robust on delegate failures
            pass

        # Rebuild spatial grid and perform proximity-based processing
        self._build_spatial_grid()
        # Nahrungssuche für Clans
        self._process_food_seeking()

        # Prozessiere Interaktionen
        self._process_interactions()

        # Collect snapshot (delegated)
        try:
            from backend.stats import collect_simulation_snapshot

            snapshot = collect_simulation_snapshot(self)
        except Exception:
            snapshot = {
                "groups": [],
                "loners": [],
                "food_sources": [],
                "stats": getattr(self, "stats", {}).copy(),
            }

        return {
            "time": self.time,
            "groups": snapshot.get("groups", []),
            "loners": snapshot.get("loners", []),
            "food_sources": snapshot.get("food_sources", []),
            "logs": getattr(self, "logs", []).copy(),
            "is_day": self.is_day,
            "transition_progress": self._calculate_transition_progress(),
            "stats": snapshot.get("stats", {}),
            "rnd_samples": {
                k: list(v) for k, v in getattr(self, "rnd_history", {}).items()
            },
        }

    def _process_loner_clan_formation(self) -> None:
        from backend.processors import process_loner_clan_formation

        process_loner_clan_formation(self)

    def get_final_stats(self) -> Dict[str, Any]:
        """Get final statistics for end of simulation."""
        # Update max clans count
        current_clans = sum(len(g.clans) for g in self.groups)
        self.stats["max_clans"] = max(self.stats["max_clans"], current_clans)

        return {
            "species_counts": self.stats["species_counts"],
            "deaths": self.stats["deaths"],
            "max_clans": self.stats["max_clans"],
            "food_places": self.stats["food_places"],
            "population_history": self.stats["population_history"],
            "rnd_samples": {
                k: list(v) for k, v in getattr(self, "rnd_history", {}).items()
            },
        }

    def set_temperature(self, temp: float) -> None:
        """Set temperature."""
        pass

    def set_food_level(self, level: float) -> None:
        """Set food level."""
        pass

    def set_day_night(self, is_day: bool) -> None:
        """Set day/night."""
        pass

    def set_loner_speed(self, multiplier: float) -> None:
        """Set loner speed multiplier (0.5 to 2.0)."""
        self.loner_speed_multiplier = max(
            SPEED_MULT_MIN, min(SPEED_MULT_MAX, multiplier)
        )

    def set_clan_speed(self, multiplier: float) -> None:
        """Set clan speed multiplier (0.5 to 2.0)."""
        self.clan_speed_multiplier = max(
            SPEED_MULT_MIN, min(SPEED_MULT_MAX, multiplier)
        )
