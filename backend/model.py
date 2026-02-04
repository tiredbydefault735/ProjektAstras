"""
Simulation Model - Neu aufgebaut für smoothe, glitch-freie Bewegung
"""

from __future__ import annotations
import simpy
import random
import math
import logging
from typing import Optional, List, Dict, Any, Tuple, Union, Generator

from config import (
    SPAWN_PADDING,
    GRID_CELL_SIZE,
    HUNGER_THRESHOLD_RANGE,
    HUNGER_ALERT,
    HUNGER_TIMER_DEATH,
    DAY_NIGHT_CYCLE_DURATION,
    TRANSITION_DURATION,
    POP_HISTORY_STEP,
    MAX_LOGS,
    FOOD_DEFAULT_AMOUNT,
    DEFAULT_FOOD_PLACES,
    MAP_DEFAULT_HEIGHT,
    MAP_DEFAULT_WIDTH,
    MAP_EDGE_PADDING,
    COMBAT_STRENGTH_RANGE,
    MAX_CLANS_PER_SPECIES,
    BASE_TEMPERATURE_FALLBACK_RANGE,
    MAX_CLANS_DEFAULT,
    SPLIT_DENOM,
    SPLIT_BASE_CHANCE,
    SPLIT_POP_FRAC,
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
    SIM_STEP_TIMEOUT,
    DEFAULT_COLOR,
    FOOD_INTAKE_DEFAULT,
    LONER_SPAWN_RANGE,
    CLAN_DEATH_DIVISOR,
    TEMPERATURE_PRECISION,
    CLAN_SPLIT_DIVISOR,
    SPEED_MULT_MIN,
    SPEED_MULT_MAX,
    START_POP_THRESHOLD,
    DEFAULT_HP,
    ICEFANG_HP_CAP,
    OTHER_HP_CAP,
)

logger = logging.getLogger(__name__)

from backend.entities import FoodSource, Loner, Clan


class SpeciesGroup:
    """Manages all clans of a specific species.

    @ivar env: The SimPy environment
    @ivar name: Name of the species
    @ivar color: Color representation
    @ivar max_members: Max members per clan
    @ivar hp_per_member: HP per clan member
    @ivar food_intake: Food intake per member
    @ivar can_cannibalize: Whether species can cannibalize
    @ivar map_width: Width of the map
    @ivar map_height: Height of the map
    @ivar max_clans: Maximum number of clans allowed
    @ivar clans: List of active clans
    @ivar next_clan_id: Counter for generating clan IDs
    """

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
        """Initialize the species group.

        @param env: SimPy environment
        @param name: Species name
        @param start_population: Initial population count
        @param color: Species color
        @param max_members: Max clan size
        @param hp_per_member: Health per member
        @param food_intake: Food consumption rate
        @param can_cannibalize: Cannibalism flag
        @param map_width: Map width
        @param map_height: Map height
        """
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

    def live(self) -> Generator[simpy.Event, None, None]:
        """Lifecycle process for the species group.

        Updates all clans in the group at each simulation step.

        @return: A generator for SimPy events
        """
        while True:
            yield self.env.timeout(SIM_STEP_TIMEOUT)
            sim_model = getattr(self.env, "sim_model", None)
            is_day = bool(sim_model.is_day) if sim_model else True

            clan_speed_mult = getattr(sim_model, "clan_speed_multiplier", 1.0)

            if sim_model and hasattr(sim_model, "species_config"):
                species_stats = sim_model.species_config.get(self.name, {})
                species_mult = species_stats.get("clan_speed_mult", 1.0)
                clan_speed_mult *= species_mult

            for clan in list(self.clans):
                clan.update(self.map_width, self.map_height, is_day, clan_speed_mult)

                if clan.hunger_timer >= HUNGER_TIMER_DEATH:
                    deaths = max(1, clan.population // CLAN_DEATH_DIVISOR)
                    clan.population = max(0, clan.population - deaths)

                if clan.population <= 0:
                    continue

            self.clans = [c for c in self.clans if c.population > 0]

            self.check_clan_splits()

    def check_clan_splits(self) -> None:
        """Split clans when they exceed population thresholds.

        Splits occur when population exceeds SPLIT_POP_FRAC * max_members, with probability
        increasing to 100% when population > max_members. New clans spawn nearby with half
        the population. Stops at MAX_CLANS_PER_SPECIES limit.
        """
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

                sim_model = getattr(self.env, "sim_model", None)
                if sim_model:
                    try:
                        sim_model.add_log(
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
                        sim_model.add_log(
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
                        logger.exception("Failed to log clan split")
                        pass


class SimulationModel:
    """Main model controlling the simulation state and logic.

    @ivar env: SimPy environment
    @ivar time: Current simulation time
    @ivar groups: List of species groups
    @ivar loners: List of independent loner entities
    @ivar food_sources: List of food sources
    @ivar rnd_history: History of random values for analysis
    @ivar map_width: Width of the simulation area
    @ivar map_height: Height of the simulation area
    @ivar grid_cell_size: Size of spatial grid cells
    @ivar stats: Statistics dictionary
    @ivar base_temperature: Base environmental temperature
    @ivar current_temperature: Current effective temperature
    @ivar is_day: Day/Night flag
    """

    def add_log(
        self, message: Union[str, Tuple[str, Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """Add a log entry to the simulation logs.

        @param message: The message to log. Can be a string, a tuple (msgid, params),
                        or a dict with 'msgid' and 'params'.
        """
        t = getattr(self, "time", 0)
        if not hasattr(self, "logs"):
            self.logs: List[Dict[str, Any]] = []
        if not hasattr(self, "max_logs"):
            self.max_logs: int = MAX_LOGS

        entry = None
        try:
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
                entry = {"time": t, "raw": str(message)}
        except Exception:
            logger.exception("Error processing log message")
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
        """Initialize simulation environment and entities.

        @param species_config: Configuration dictionary for species
        @param population_overrides: Dictionary mapping species names to initial population counts
        @param food_places: Number of food sources to generate
        @param food_amount: Amount of food per source
        @param start_temperature: Initial temperature (optional)
        @param start_is_day: Initial time of day (True for day)
        @param region_name: Name of the region for modifiers
        @param initial_food_positions: Optional list of fixed food positions
        @param rng_seed: Random number generator seed
        """

        self.env = simpy.Environment()
        try:
            setattr(self.env, "sim_model", self)
        except Exception:
            logger.exception("Failed to set sim_model on environment")
            pass
        self.time = 0
        self.groups: List[SpeciesGroup] = []
        self.loners: List[Loner] = []
        self.rnd_history: Dict[str, List[Any]] = {
            "regen": [],
            "clan_growth": [],
            "loner_spawn": [],
        }

        self.map_width = MAP_DEFAULT_WIDTH
        self.map_height = MAP_DEFAULT_HEIGHT
        self.grid_cell_size = GRID_CELL_SIZE
        self._grid = {}

        self.clan_speed_multiplier = 1.0
        self.loner_speed_multiplier = 1.0

        self.stats: Dict[str, Any] = {
            "species_counts": {},
            "deaths": {
                "combat": {},
                "starvation": {},
                "temperature": {},
            },
            "max_clans": 0,
            "food_places": 0,
            "population_history": {},
        }

        if start_temperature is not None:
            self.base_temperature = start_temperature
            self.current_temperature = start_temperature
        else:
            self.base_temperature = random.uniform(*BASE_TEMPERATURE_FALLBACK_RANGE)
            self.current_temperature = self.base_temperature
        self.temp_change_timer = 0
        self.day_night_temp_offset = 0

        self.is_day = start_is_day
        self.day_night_timer = 0
        self.day_night_cycle_duration = DAY_NIGHT_CYCLE_DURATION
        self.transition_duration = TRANSITION_DURATION
        self.in_transition = False
        self.transition_timer = 0
        self.transition_to_day = True

        if rng_seed is not None:
            try:
                random.seed(rng_seed)
            except Exception:
                logger.exception(f"Failed to set random seed: {rng_seed}")
                pass
        else:
            random.seed()

        # Farben für Spezies
        color_map = {
            "Icefang": ICEFANG_COLOR,
            "Crushed_Critters": CRUSHED_CRITTERS_COLOR,
            "Spores": SPORES_COLOR,
            "The_Corrupted": THE_CORRUPTED_COLOR,
        }

        self.species_config = species_config

        self.region_name = region_name or "Default"
        region_modifiers = {
            "Default": {},
            "Snowy_Abyss": {
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

        self.interaction_matrix = {}
        for species_name, stats in species_config.items():
            if "interactions" in stats:
                self.interaction_matrix[species_name] = stats["interactions"]

        total_requested = (
            sum(int(v) for v in population_overrides.values())
            if population_overrides
            else 0
        )

        for species_name, stats in species_config.items():
            start_pop = (
                population_overrides.get(species_name, 0)
                if total_requested >= START_POP_THRESHOLD
                else 0
            )
            color = color_map.get(species_name, DEFAULT_COLOR)
            raw_hp = stats.get("hp", DEFAULT_HP)
            if species_name == "Icefang":
                hp = min(raw_hp, ICEFANG_HP_CAP)
            else:
                hp = min(raw_hp, OTHER_HP_CAP)
            food_intake = stats.get("food_intake", FOOD_INTAKE_DEFAULT)
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

            mods = self._region_mods.get(species_name)
            if mods:
                if "boost" in mods or "base" in mods:
                    chance = float(mods.get("chance", 0.0))
                    use_boost = random.random() < chance
                    selected = mods.get("boost") if use_boost else mods.get("base", {})
                else:
                    selected = mods

                for clan in group.clans:
                    if "hp_mult" in selected:
                        clan.hp_per_member = int(
                            max(1, clan.hp_per_member * selected["hp_mult"])
                        )
                    if "combat_mult" in selected:
                        if hasattr(clan, "combat_strength"):
                            clan.combat_strength *= selected["combat_mult"]
                        else:
                            clan.combat_strength = (
                                random.uniform(*COMBAT_STRENGTH_RANGE)
                                * selected["combat_mult"]
                            )
                    if "hunger_delta" in selected:
                        clan.hunger_threshold = (
                            getattr(clan, "hunger_threshold", HUNGER_ALERT)
                            + selected["hunger_delta"]
                        )
            for clan in group.clans:
                clan.hunger_timer = 0
            self.groups.append(group)

        for species_name, stats in species_config.items():
            if population_overrides.get(species_name, 0) == 0:
                continue

            color = color_map.get(species_name, DEFAULT_COLOR)
            hp = stats.get("hp", DEFAULT_HP)
            food_intake = stats.get("food_intake", FOOD_INTAKE_DEFAULT)
            can_cannibalize = species_name in ["Spores", "The_Corrupted"]

            if total_requested < START_POP_THRESHOLD:
                num_loners = int(population_overrides.get(species_name, 0))
            else:
                num_loners = random.randint(*LONER_SPAWN_RANGE)

            for _ in range(num_loners):
                x = random.uniform(SPAWN_PADDING, self.map_width - SPAWN_PADDING)
                y = random.uniform(SPAWN_PADDING, self.map_height - SPAWN_PADDING)
                loner = Loner(
                    species_name, x, y, color, hp, food_intake, 0, can_cannibalize
                )
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

        self.food_sources: List[FoodSource] = []
        if initial_food_positions:
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

        total_pop = sum(sum(c.population for c in g.clans) for g in self.groups)

        self.stats["food_places"] = food_places
        total_clans = sum(len(g.clans) for g in self.groups)
        self.stats["max_clans"] = total_clans
        self.stats["temperature"] = round(
            self.current_temperature, TEMPERATURE_PRECISION
        )
        self.stats["is_day"] = self.is_day

        for group in self.groups:
            species_name = group.name
            clan_pop = sum(c.population for c in group.clans)
            loner_pop = sum(1 for l in self.loners if l.species == species_name)
            self.stats["species_counts"][species_name] = clan_pop + loner_pop
            self.stats["deaths"]["combat"][species_name] = 0
            self.stats["deaths"]["starvation"][species_name] = 0
            self.stats["deaths"]["temperature"][species_name] = 0

    def _calculate_transition_progress(self) -> float:
        """Calculate transition progress between day and night.

        @return: Progress value (0.0 = full night, 1.0 = full day)
        """
        if not self.in_transition:
            return 1.0 if self.is_day else 0.0

        progress_ratio = self.transition_timer / self.transition_duration

        if self.transition_to_day:
            return progress_ratio
        else:
            return 1.0 - progress_ratio

    # --- Spatial grid helpers ---
    def _build_spatial_grid(self) -> None:
        """Rebuild the spatial grid with current entity positions.

        Delegates to backend.spatial.SpatialGrid.
        """
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

    def _nearby_candidates(
        self,
        x: float,
        y: float,
        radius: float,
        kinds: Tuple[str, ...] = ("clans", "loners", "food"),
    ) -> List[Any]:
        """Find candidates near a given position.

        @param x: Center X coordinate
        @param y: Center Y coordinate
        @param radius: Search radius
        @param kinds: Tuple of strings specifying what to look for ("clans", "loners", "food")
        @return: List of found entities
        """
        if not hasattr(self, "_spatial"):
            from backend.spatial import SpatialGrid

            self._spatial = SpatialGrid(self.grid_cell_size)
            self._spatial.build(
                self.groups, self.loners, self.food_sources, self.grid_cell_size
            )

        return self._spatial.nearby_candidates(x, y, radius, kinds)

    def _process_food_seeking(self) -> None:
        """Execute food seeking behavior for clans.

        Delegates to backend.processors.process_food_seeking.
        """
        from backend.processors import process_food_seeking

        process_food_seeking(self)

    def _process_interactions(self) -> None:
        """Execute interaction logic between entities.

        Delegates to backend.processors.process_interactions.
        """
        from backend.processors import process_interactions

        process_interactions(self)

    def step(self) -> Dict[str, Any]:
        """Execute one simulation step.

        Advanced the SimPy environment, updates entities, processes interactions,
        and collects statistics.

        @return: Dictionary containing the current state snapshot and statistics
        """
        try:
            from backend.spawn import spawn_loners

            spawn_loners(self)
        except Exception:
            logger.exception("Error during loner spawning")
            pass
        """Simulationsschritt."""
        target = self.env.now + SIM_STEP_TIMEOUT
        self.env.run(until=target)
        self.time = int(self.env.now)
        self._pending_conversions: List[Any] = []

        if self.time % POP_HISTORY_STEP == 0:
            for species_name in self.species_config.keys():
                if species_name not in self.stats["population_history"]:
                    self.stats["population_history"][species_name] = []
                count = sum(
                    sum(c.population for c in g.clans)
                    for g in self.groups
                    if g.name == species_name
                )
                count += sum(1 for l in self.loners if l.species == species_name)
                self.stats["population_history"][species_name].append(count)

        try:
            from backend.temperature import update_and_apply

            update_and_apply(self)
        except Exception:
            logger.exception("Error during temperature update")
            pass

        self._build_spatial_grid()
        self._process_food_seeking()

        self._process_interactions()

        try:
            from backend.stats import collect_simulation_snapshot

            snapshot = collect_simulation_snapshot(self)
        except Exception:
            logger.exception("Error collecting simulation snapshot")
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
        """Process logic for loners forming new clans.

        Delegates to backend.processors.process_loner_clan_formation.
        """
        from backend.processors import process_loner_clan_formation

        process_loner_clan_formation(self)

    def get_final_stats(self) -> Dict[str, Any]:
        """Retrieve final statistics at the end of simulation.

        @return: Dictionary of simulation statistics including species counts,
                 deaths, max clans, etc.
        """
        current_clans = sum(len(g.clans) for g in self.groups)
        self.stats["max_clans"] = max(self.stats["max_clans"], current_clans)

        if hasattr(self, "groups") and hasattr(self, "loners"):
            for group in self.groups:
                species_name = group.name
                clan_pop = sum(c.population for c in group.clans)
                loner_pop = sum(1 for l in self.loners if l.species == species_name)
                self.stats["species_counts"][species_name] = clan_pop + loner_pop

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
        """Set the simulation base temperature.

        @param temp: New temperature value
        """
        self.base_temperature = temp
        self.current_temperature = self.base_temperature + self.day_night_temp_offset
        self.stats["temperature"] = round(
            self.current_temperature, TEMPERATURE_PRECISION
        )

    def set_food_level(self, level: float) -> None:
        """Set the food level.

        @param level: New food level
        """
        pass

    def set_day_night(self, is_day: bool) -> None:
        """Set the time of day.

        @param is_day: True for day, False for night
        """
        pass

    def set_loner_speed(self, multiplier: float) -> None:
        """Set loner speed multiplier.

        @param multiplier: Speed multiplier (clamped between limits)
        """
        self.loner_speed_multiplier = max(
            SPEED_MULT_MIN, min(SPEED_MULT_MAX, multiplier)
        )

    def set_clan_speed(self, multiplier: float) -> None:
        """Set clan speed multiplier.

        @param multiplier: Speed multiplier (clamped between limits)
        """
        self.clan_speed_multiplier = max(
            SPEED_MULT_MIN, min(SPEED_MULT_MAX, multiplier)
        )
