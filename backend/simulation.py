"""SimulationModel: high-level orchestration moved from legacy model.py."""

import simpy
import random
import math
import time

from .entities.food_source import FoodSource
from .entities.loner import Loner
from .entities.clan import Clan
from .entities.species_group import SpeciesGroup


class SimulationModel:
    def add_log(self, message):
        """Log-Nachricht hinzufügen."""
        log_entry = f"[t={getattr(self, 'time', 0)}] {message}"
        if not hasattr(self, "logs"):
            self.logs = []
        if not hasattr(self, "max_logs"):
            self.max_logs = 300
        self.logs.append(log_entry)
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs :]

    def setup(
        self,
        species_config,
        population_overrides,
        food_places=5,
        food_amount=50,
        start_temperature=None,
        start_is_day=True,
        region_name=None,
    ):
        """Initialisiere Simulation."""

        # Re-initialize SimPy environment for each setup
        self.env = simpy.Environment()
        # Ensure time exists before any logging
        self.time = 0
        self.groups = []
        self.loners = []

        # Ensure map dimensions are always set before use
        self.map_width = 1200
        self.map_height = 600

        # Movement multipliers
        self.clan_speed_multiplier = 1.0
        self.loner_speed_multiplier = 1.0

        # Re-initialize statistics to ensure temperature is included and avoid AttributeError
        self.stats = {
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

        # Per-species movement multipliers (defaults to 1.0)
        # Initialized after species_config is assigned below.
        self.loner_speed_multipliers = {}
        self.clan_speed_multipliers = {}

        # Temperatur-System initialisieren
        if start_temperature is not None:
            self.base_temperature = start_temperature  # Basis-Temperatur (Mittelwert)
            self.current_temperature = (
                start_temperature  # Vom Slider gesetzte Temperatur
            )
        else:
            # Use a Normal distribution for realistic base temperature sampling
            # mean 0, sd 8, clamp to [-20, 20]
            self.base_temperature = max(-20, min(20, random.gauss(0, 8)))
            self.current_temperature = self.base_temperature
        self.temp_change_timer = 0  # Timer für Temperatur-Änderungen
        self.day_night_temp_offset = 0  # Aktueller Tag/Nacht Offset

        # Tag/Nacht-Zyklus initialisieren
        self.is_day = start_is_day  # Start-Tageszeit aus UI
        self.day_night_timer = 0
        self.day_night_cycle_duration = 300  # 30 Sekunden pro Zyklus (300 Steps)
        self.transition_duration = 50  # 5 Sekunden Übergang (50 Steps)
        self.in_transition = False
        self.transition_timer = 0
        self.transition_to_day = True  # Zielzustand des Übergangs

        # Farben für Spezies
        color_map = {
            "Icefang": (0.8, 0.9, 1, 1),
            "Crushed_Critters": (0.6, 0.4, 0.2, 1),
            "Spores": (0.2, 0.8, 0.2, 1),
            "The_Corrupted": (0.5, 0, 0.5, 1),
        }

        # Speichere Config für Interaktionen
        self.species_config = species_config

        # Initialize per-species multipliers now that species_config exists
        self.loner_speed_multipliers = {
            name: 1.0 for name in self.species_config.keys()
        }
        self.clan_speed_multipliers = {name: 1.0 for name in self.species_config.keys()}

        # Baue Interaktionsmatrix aus species.json
        self.interaction_matrix = {}
        for species_name, stats in species_config.items():
            if "interactions" in stats:
                self.interaction_matrix[species_name] = stats["interactions"]

        # Erstelle Gruppen
        for species_name, stats in species_config.items():
            start_pop = population_overrides.get(species_name, 0)
            color = color_map.get(species_name, (0.5, 0.5, 0.5, 1))
            hp = stats.get("hp", 25)  # Default 25 HP
            food_intake = stats.get("food_intake", 5)  # Default 5
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
            # Setze hunger_timer aller Clans auf 0
            for clan in group.clans:
                clan.hunger_timer = 0
            self.groups.append(group)

        # Erstelle Einzelgänger (2-5 pro Spezies) - NUR für aktivierte Spezies
        for species_name, stats in species_config.items():
            # Überspringe deaktivierte Spezies (Population = 0)
            if population_overrides.get(species_name, 0) == 0:
                continue

            color = color_map.get(species_name, (0.5, 0.5, 0.5, 1))
            hp = stats.get("hp", 25)
            food_intake = stats.get("food_intake", 5)
            can_cannibalize = species_name in ["Spores", "The_Corrupted"]
            # Sample initial loner count using a Normal distribution centered ~3.5
            # then clamp to a sensible integer range (1..6)
            num_loners = int(max(1, min(6, round(random.gauss(3.5, 1.0)))))

            for _ in range(num_loners):
                x = random.uniform(50, self.map_width - 50)
                y = random.uniform(50, self.map_height - 50)
                loner = Loner(
                    species_name, x, y, color, hp, food_intake, 0, can_cannibalize
                )
                self.loners.append(loner)

        # Erstelle Nahrungsplätze
        self.food_sources = []
        for _ in range(food_places):
            x = random.uniform(100, self.map_width - 100)
            y = random.uniform(100, self.map_height - 100)
            food_source = FoodSource(x, y, food_amount)
            self.food_sources.append(food_source)

        total_pop = sum(sum(c.population for c in g.clans) for g in self.groups)
        self.add_log(
            f"Start: {len(self.groups)} Spezies, {total_pop} Mitglieder, {len(self.loners)} Einzelgänger"
        )

        # Initialize statistics
        self.stats["food_places"] = food_places
        total_clans = sum(len(g.clans) for g in self.groups)
        self.stats["max_clans"] = total_clans
        self.stats["temperature"] = round(self.current_temperature, 1)
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

        # Expose back-reference so SpeciesGroup processes can access sim_model
        # (used inside SpeciesGroup.live to read day/night and per-species multipliers)
        try:
            self.env.sim_model = self
        except Exception:
            pass

        # Start a background process to update loners each SimPy step
        try:
            self.env.process(self._loner_process())
        except Exception:
            pass

    def _loner_process(self):
        """SimPy process that updates loners each step so they move autonomously.

        Uses per-species multipliers when available, otherwise falls back to the
        global multiplier.
        """
        while True:
            yield self.env.timeout(1)
            is_day = getattr(self, "is_day", True)
            # Update loners in-place
            for loner in list(self.loners):
                mult = self.loner_speed_multipliers.get(
                    loner.species, self.loner_speed_multiplier
                )
                try:
                    loner.update(self.map_width, self.map_height, is_day, mult)
                except Exception:
                    # Keep process resilient to unexpected entity errors
                    continue
                # Temperatur-Schaden prüfen
                try:
                    species_cfg = self.species_config.get(loner.species, {})
                    min_temp = species_cfg.get("min_survival_temp", -100)
                    max_temp = species_cfg.get("max_survival_temp", 100)

                    if (
                        self.current_temperature < min_temp
                        or self.current_temperature > max_temp
                    ):
                        if self.current_temperature < min_temp:
                            temp_diff = min_temp - self.current_temperature
                        else:
                            temp_diff = self.current_temperature - max_temp

                        # Loners take higher temperature damage: 6 HP + 3 HP per 5 degrees
                        damage = 6 + (temp_diff // 5) * 3
                        damage = max(6, min(damage, 40))
                        loner.hp -= damage
                        if loner.hp <= 0:
                            # remove loner and record death
                            try:
                                if loner in self.loners:
                                    self.loners.remove(loner)
                            except Exception:
                                pass
                            self.add_log(
                                f"❄️ {loner.species} Einzelgänger stirbt an Temperatur ({round(self.current_temperature,1)}°C)!"
                            )
                            self.stats["deaths"]["temperature"][loner.species] = (
                                self.stats["deaths"]["temperature"].get(
                                    loner.species, 0
                                )
                                + 1
                            )
                            continue
                except Exception:
                    pass

                # Hungertod: Nach 300 Steps (30 Sekunden)
                try:
                    if loner.hunger_timer >= 300:
                        try:
                            if loner in self.loners:
                                self.loners.remove(loner)
                        except Exception:
                            pass
                        self.add_log(f"☠️ {loner.species} Einzelgänger verhungert!")
                        self.stats["deaths"]["starvation"][loner.species] = (
                            self.stats["deaths"]["starvation"].get(loner.species, 0) + 1
                        )
                        continue
                except Exception:
                    pass

    def _calculate_transition_progress(self):
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

    def step(self):
        # Basic timing instrumentation to help identify hotspots.
        t_step_start = time.perf_counter()
        # (Simulation stepping code preserved from original model.py)
        # For brevity in the refactor commit, the full step implementation is
        # retained as in the original file. This file focuses on splitting
        # classes into separate modules while keeping behavior unchanged.
        # The full implementation remains in this method.

        # --- Random loner spawn logic ---
        # 1% chance per step per species to spawn a loner (adjust as needed)
        for species_name, stats in self.species_config.items():
            if random.random() < 0.01:
                color_map = {
                    "Icefang": (0.8, 0.9, 1, 1),
                    "Crushed_Critters": (0.6, 0.4, 0.2, 1),
                    "Spores": (0.2, 0.8, 0.2, 1),
                    "The_Corrupted": (0.5, 0, 0.5, 1),
                }
                color = color_map.get(species_name, (0.5, 0.5, 0.5, 1))
                hp = stats.get("hp", 25)
                food_intake = stats.get("food_intake", 5)
                can_cannibalize = species_name in ["Spores", "The_Corrupted"]
                # Determine number of loners to spawn using an Exponential distribution
                # (mean ~2 loners). Clamp to 1..5 to keep counts sensible.
                spawn_count = int(max(1, min(5, round(random.expovariate(0.5) + 1))))
                for _ in range(spawn_count):
                    x = random.uniform(50, self.map_width - 50)
                    y = random.uniform(50, self.map_height - 50)
                    loner = Loner(
                        species_name, x, y, color, hp, food_intake, 0, can_cannibalize
                    )
                    self.loners.append(loner)
                self.add_log(
                    f"🔹 {spawn_count} neue Einzelgänger der Spezies {species_name} sind erschienen!"
                )

        # SimPy step
        target = self.env.now + 1
        self.env.run(until=target)
        self.time = int(self.env.now)

        # Track population history every 10 steps
        if self.time % 10 == 0:
            t_count_start = time.perf_counter()
            for species_name in self.species_config.keys():
                if species_name not in self.stats["population_history"]:
                    self.stats["population_history"][species_name] = []
                # Count current population for this species
                count = sum(
                    sum(c.population for c in g.clans)
                    for g in self.groups
                    if g.name == species_name
                )
                count += sum(1 for l in self.loners if l.species == species_name)
                self.stats["population_history"][species_name].append(count)
            t_count_end = time.perf_counter()
            self._last_count_ms = (t_count_end - t_count_start) * 1000.0

        # Day/Night cycle and temperature dynamics
        # Ensure cycle timers exist
        try:
            self.day_night_timer = getattr(self, "day_night_timer", 0) + 1
        except Exception:
            self.day_night_timer = 0

        # Start a transition when the day/night timer reaches cycle duration
        if not getattr(
            self, "in_transition", False
        ) and self.day_night_timer >= getattr(self, "day_night_cycle_duration", 300):
            self.in_transition = True
            # Toggle target (if currently day, transition to night and vice versa)
            self.transition_to_day = not getattr(self, "is_day", True)
            self.transition_timer = 0
            self.day_night_timer = 0

        # Advance transition timer if in transition
        if getattr(self, "in_transition", False):
            self.transition_timer = getattr(self, "transition_timer", 0) + 1
            if self.transition_timer >= getattr(self, "transition_duration", 50):
                # Finish transition
                self.in_transition = False
                self.is_day = bool(self.transition_to_day)
                self.transition_timer = 0

            # Compute diurnal temperature offset: symmetric +/- delta around base_temperature
            # Compute diurnal temperature offset: keep base_temperature as the
            # user-set daytime baseline and only subtract a small amount at night.
            night_delta = getattr(self, "night_temp_delta", 3.0)
            # transition_progress: 0.0 = full night, 1.0 = full day
            progress = self._calculate_transition_progress()
            # Daytime: offset 0. Nighttime: offset -night_delta. Interpolate.
            night_target = -night_delta
            day_target = 0.0
            self.day_night_temp_offset = (
                night_target + (day_target - night_target) * progress
            )

        # Slow background temperature drift (seasonal variations)
        self.temp_change_timer = getattr(self, "temp_change_timer", 0) + 1
        if self.temp_change_timer >= getattr(self, "temp_change_interval", 600):
            # small random walk around base temperature
            try:
                drift = random.gauss(0, 0.5)
                self.base_temperature = max(-50, min(50, self.base_temperature + drift))
            except Exception:
                pass
            self.temp_change_timer = 0

        # Compose current temperature from base + diurnal offset
        try:
            self.current_temperature = float(self.base_temperature) + float(
                self.day_night_temp_offset
            )
        except Exception:
            # Fallback to base temperature
            self.current_temperature = getattr(self, "base_temperature", 0.0)

        # Build structured data for frontend rendering
        t_build_start = time.perf_counter()
        groups_out = []
        for g in self.groups:
            clans = []
            for c in g.clans:
                clans.append(
                    {
                        "clan_id": getattr(c, "clan_id", id(c)),
                        "x": getattr(c, "x", 0),
                        "y": getattr(c, "y", 0),
                        "population": getattr(c, "population", 0),
                        "color": getattr(c, "color", (0.5, 0.5, 0.5, 1)),
                    }
                )
            groups_out.append({"name": g.name, "clans": clans})

        loners_out = []
        for l in self.loners:
            loners_out.append(
                {
                    "x": getattr(l, "x", 0),
                    "y": getattr(l, "y", 0),
                    "color": getattr(l, "color", (0.5, 0.5, 0.5, 1)),
                    "species": getattr(l, "species", ""),
                }
            )

        foods_out = []
        for f in getattr(self, "food_sources", []):
            foods_out.append(
                {
                    "x": getattr(f, "x", 0),
                    "y": getattr(f, "y", 0),
                    "amount": getattr(f, "amount", 0),
                    "max_amount": getattr(f, "max_amount", getattr(f, "capacity", 50)),
                }
            )

        transition_progress = self._calculate_transition_progress()
        t_build_end = time.perf_counter()
        self._last_build_ms = (t_build_end - t_build_start) * 1000.0

        # Keep stats in sync each step for UI/log consistency
        try:
            self.stats["temperature"] = round(self.current_temperature, 1)
        except Exception:
            self.stats["temperature"] = None
        try:
            self.stats["is_day"] = bool(getattr(self, "is_day", True))
        except Exception:
            pass

        # record total step duration
        try:
            t_step_end = time.perf_counter()
            self._last_step_ms = (t_step_end - t_step_start) * 1000.0
            if not hasattr(self, "_step_history"):
                self._step_history = []
            self._step_history.append(self._last_step_ms)
            if len(self._step_history) > 200:
                self._step_history = self._step_history[-200:]
        except Exception:
            pass

        return {
            "time": self.time,
            "groups": groups_out,
            "loners": loners_out,
            "food_sources": foods_out,
            "logs": getattr(self, "logs", []).copy(),
            "is_day": getattr(self, "is_day", True),
            "transition_progress": transition_progress,
            "stats": self.stats.copy(),
        }

    def get_final_stats(self):
        """Get final statistics for end of simulation."""
        current_clans = sum(len(g.clans) for g in self.groups)
        self.stats["max_clans"] = max(self.stats.get("max_clans", 0), current_clans)

        return {
            "species_counts": self.stats["species_counts"],
            "deaths": self.stats["deaths"],
            "max_clans": self.stats["max_clans"],
            "food_places": self.stats["food_places"],
            "population_history": self.stats["population_history"],
        }

    def set_loner_speed(self, multiplier):
        """Set loner speed multiplier (0.5 to 2.0)."""
        # apply as global default and set per-species defaults as well
        m = max(0.2, min(2.0, multiplier))
        self.loner_speed_multiplier = m
        for k in list(self.loner_speed_multipliers.keys()):
            self.loner_speed_multipliers[k] = m

    def set_loner_speed_for_species(self, species, multiplier):
        """Set loner speed for a specific species (0.2 to 2.0)."""
        m = max(0.2, min(2.0, multiplier))
        self.loner_speed_multipliers[species] = m

    def set_clan_speed(self, multiplier):
        """Set clan speed multiplier (0.5 to 2.0)."""
        m = max(0.2, min(2.0, multiplier))
        self.clan_speed_multiplier = m
        for k in list(self.clan_speed_multipliers.keys()):
            self.clan_speed_multipliers[k] = m

    def set_clan_speed_for_species(self, species, multiplier):
        """Set clan speed for a specific species (0.2 to 2.0)."""
        m = max(0.2, min(2.0, multiplier))
        self.clan_speed_multipliers[species] = m
