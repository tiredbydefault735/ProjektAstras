"""
Simulation Model - Neu aufgebaut für smoothe, glitch-freie Bewegung
"""

import simpy
import random
import math


class FoodSource:
    """Nahrungsplatz auf der Map."""

    def __init__(self, x, y, amount):
        self.x = x
        self.y = y
        self.amount = amount
        self.max_amount = amount
        self.regeneration_timer = 0

    def consume(self, requested_amount):
        """Konsumiere Nahrung, gibt tatsächlich konsumierte Menge zurück."""
        consumed = min(requested_amount, self.amount)
        self.amount -= consumed
        return consumed

    def regenerate(self):
        """Stochastic, small food regeneration events.

        Instead of infrequent large bursts, regenerate small amounts at a
        low per-step probability so the distribution is more comparable to
        clan growth and loner spawns (smaller magnitudes, similar sparsity).
        """
        # If already full, nothing to do
        if self.amount >= self.max_amount:
            return 0

        # Per-step chance to regenerate a small amount (2% default)
        regen_prob = 0.02
        if random.random() < regen_prob:
            # Small regen amounts biased towards 1 and 2
            regen_choices = [1, 1, 1, 2, 2, 3]
            regen = random.choice(regen_choices)
            regen = max(1, regen)
            self.amount = min(self.amount + regen, self.max_amount)
            return regen

        return 0

    def is_depleted(self):
        """Ist die Nahrung aufgebraucht?"""
        return self.amount <= 0


class Loner:
    """Einzelgänger - bewegt sich unabhängig."""

    def __init__(
        self, species, x, y, color, hp, food_intake, hunger_timer, can_cannibalize
    ):
        self.species = species
        self.x = x
        self.y = y
        self.color = color
        self.hp = hp  # Gesundheit
        self.max_hp = hp
        # Loners sind schneller als Clans!
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(-2.5, 2.5)
        # Nahrungssystem
        self.food_intake = food_intake  # Wie viel Food benötigt wird
        self.hunger_timer = (
            hunger_timer  # Sekunden seit letzter Nahrung (1 Step = 0.1s)
        )
        self.can_cannibalize = can_cannibalize  # Kann andere Arachs essen
        # Randomized combat strength (affects damage dealt/received)
        self.combat_strength = random.uniform(0.85, 1.25)
        # Randomized hunger threshold for loners (when they start seeking food)
        self.hunger_threshold = random.randint(150, 260)

    def update(self, width, height, is_day=True, speed_multiplier=1.0):
        """Bewege Loner."""
        # Hunger erhöhen
        self.hunger_timer += 1

        # Bei Nacht: Langsamere Bewegung (70% Geschwindigkeit)
        speed_modifier = 1.0 if is_day else 0.7
        # Apply global speed multiplier
        speed_modifier *= speed_multiplier
        self.x += self.vx * speed_modifier
        self.y += self.vy * speed_modifier

        # Bounce an Rändern (wie Clans)
        if self.x < 0:
            self.x = 0
            self.vx = abs(self.vx)
        elif self.x > width:
            self.x = width
            self.vx = -abs(self.vx)
        if self.y < 0:
            self.y = 0
            self.vy = abs(self.vy)
        elif self.y > height:
            self.y = height
            self.vy = -abs(self.vy)

        # Gelegentliche Richtungsänderung
        if random.random() < 0.02:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.8, 1.5)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed


class Clan:
    """Ein Clan - bewegt sich als Gruppe."""

    def __init__(
        self,
        clan_id,
        species,
        x,
        y,
        population,
        color,
        max_members,
        hp_per_member,
        food_intake,
        hunger_timer,
        can_cannibalize,
    ):
        self.clan_id = clan_id
        self.species = species
        self.x = x
        self.y = y
        self.population = population
        self.color = color
        self.max_members = max_members
        self.hp_per_member = hp_per_member  # HP pro Mitglied
        # Clans sind langsamer als Loners
        self.vx = random.uniform(-2.0, 2.0)
        self.vy = random.uniform(-2.0, 2.0)
        # Nahrungssystem
        self.food_intake = food_intake
        self.hunger_timer = hunger_timer  # Sekunden seit letzter Nahrung
        self.can_cannibalize = can_cannibalize
        self.seeking_food = False  # Aktive Nahrungssuche?
        # Randomized combat strength (affects damage dealt/received)
        self.combat_strength = random.uniform(0.85, 1.25)
        # Randomized hunger threshold for clans (when they start seeking food)
        self.hunger_threshold = random.randint(40, 90)

    def total_hp(self):
        """Gesamte HP des Clans."""
        return self.population * self.hp_per_member

    def take_damage(self, damage, sim_model=None):
        """Nimmt Schaden und reduziert Population wenn nötig."""
        # Accumulate damage over time so multiple small hits can kill members.
        if not hasattr(self, "_accum_damage"):
            self._accum_damage = 0

        self._accum_damage += damage
        deaths = 0

        if self.hp_per_member > 0:
            deaths = int(self._accum_damage // self.hp_per_member)
            if deaths > 0:
                # remove deaths but not below zero
                removed = min(self.population, deaths)
                self.population -= removed
                deaths = removed
                # subtract accounted damage
                self._accum_damage -= removed * self.hp_per_member

        # Track combat deaths
        if deaths > 0 and sim_model:
            sim_model.stats["deaths"]["combat"][self.species] = (
                sim_model.stats["deaths"]["combat"].get(self.species, 0) + deaths
            )

        return self.population > 0  # True wenn noch lebt

    def distance_to_clan(self, other_clan):
        """Distanz zu anderem Clan."""
        dx = self.x - other_clan.x
        dy = self.y - other_clan.y
        # return squared distance to avoid sqrt where only comparisons are needed
        return dx * dx + dy * dy

    def distance_to_loner(self, loner):
        """Distanz zu Einzelgänger."""
        dx = self.x - loner.x
        dy = self.y - loner.y
        return dx * dx + dy * dy

    def distance_to_food(self, food_source):
        """Squared distance to a food source."""
        dx = self.x - food_source.x
        dy = self.y - food_source.y
        return dx * dx + dy * dy

    def move_towards(self, tx, ty, strength=0.5, max_speed=3.0):
        """Adjust velocity to move towards target (tx,ty)."""
        dx = tx - self.x
        dy = ty - self.y
        dist_sq = dx * dx + dy * dy
        if dist_sq <= 0:
            return
        inv = 1.0 / math.sqrt(dist_sq)
        self.vx += (dx * inv) * strength
        self.vy += (dy * inv) * strength

        # Limit speed
        speed_sq = self.vx * self.vx + self.vy * self.vy
        if speed_sq > (max_speed * max_speed):
            s = max_speed / math.sqrt(speed_sq)
            self.vx *= s
            self.vy *= s

    def update(self, width, height, is_day=True, speed_multiplier=1.0):
        """Update clan position, hunger and basic behavior."""
        # Increase hunger
        if not hasattr(self, "hunger_timer"):
            self.hunger_timer = 0
        self.hunger_timer += 1

        # Day/night speed modifier (clans slightly slower at night)
        speed_modifier = 1.0 if is_day else 0.7
        speed_modifier *= speed_multiplier

        # Move
        self.x += self.vx * speed_modifier
        self.y += self.vy * speed_modifier

        # Bounce on edges
        if self.x < 0:
            self.x = 0
            self.vx = abs(self.vx)
        elif self.x > width:
            self.x = width
            self.vx = -abs(self.vx)
        if self.y < 0:
            self.y = 0
            self.vy = abs(self.vy)
        elif self.y > height:
            self.y = height
            self.vy = -abs(self.vy)

        # Occasional direction change
        if random.random() < 0.01:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.4, 1.0)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed

        # If very hungry, seek food (use per-clan randomized threshold)
        if self.hunger_timer >= getattr(self, "hunger_threshold", 50):
            self.seeking_food = True


class SpeciesGroup:
    """Verwaltet alle Clans einer Spezies."""

    def __init__(
        self,
        env,
        name,
        start_population,
        color,
        max_members,
        hp_per_member,
        food_intake,
        can_cannibalize,
        map_width,
        map_height,
    ):
        self.env = env
        self.name = name
        self.color = color
        self.max_members = max_members
        self.hp_per_member = hp_per_member
        self.food_intake = food_intake
        self.can_cannibalize = can_cannibalize
        self.map_width = map_width
        self.map_height = map_height
        self.max_clans = 8
        self.clans = []
        self.next_clan_id = 0

        # Create initial clan if population > 0
        if start_population > 0:
            x = random.uniform(100, map_width - 100)
            y = random.uniform(100, map_height - 100)
            clan = Clan(
                self.next_clan_id,
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

    def live(self):
        while True:
            yield self.env.timeout(1)
            is_day = getattr(self.env, "sim_model", None) and getattr(
                self.env.sim_model, "is_day", True
            )

            # Use global clan speed multiplier from SimulationModel when available
            try:
                clan_speed_mult = getattr(
                    self.env, "sim_model", None
                ).clan_speed_multiplier
            except Exception:
                clan_speed_mult = 1.0

            for clan in list(self.clans):
                clan.update(self.map_width, self.map_height, is_day, clan_speed_mult)

                # Hunger death
                if clan.hunger_timer >= 300:
                    deaths = max(1, clan.population // 10)
                    clan.population = max(0, clan.population - deaths)

                if clan.population <= 0:
                    # mark for removal; actual removal occurs in check_clan_splits or parent
                    continue

                # occasional split handling delegated to check_clan_splits

            # Remove empty clans
            self.clans = [c for c in self.clans if c.population > 0]

            # Try splits
            self.check_clan_splits()

    def check_clan_splits(self):
        """Split clans when they exceed thresholds."""
        for clan in self.clans[:]:
            if len(self.clans) >= 15:
                continue

            if clan.population > clan.max_members:
                split_chance = 1.0
            elif clan.population >= clan.max_members * 0.5:
                progress = (clan.population - clan.max_members * 0.5) / (
                    clan.max_members * 0.5
                )
                split_chance = math.exp(-((1 - progress) ** 2) / 0.5) * 0.15
            else:
                continue

            if random.random() < split_chance:
                pop_half = clan.population // 2
                clan.population = clan.population - pop_half
                new_x = clan.x + random.uniform(-50, 50)
                new_y = clan.y + random.uniform(-50, 50)
                new_x = max(50, min(new_x, self.map_width - 50))
                new_y = max(50, min(new_y, self.map_height - 50))
                new_clan = Clan(
                    self.next_clan_id,
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
    def add_log(self, message):
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
            self.logs = []
        if not hasattr(self, "max_logs"):
            self.max_logs = 300

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
        species_config,
        population_overrides,
        food_places=5,
        food_amount=50,
        start_temperature=None,
        start_is_day=True,
        region_name=None,
        initial_food_positions=None,
        rng_seed=None,
    ):
        """Initialisiere Simulation."""

        # Re-initialize SimPy environment for each setup
        self.env = simpy.Environment()
        # allow group processes to reference back to this SimulationModel
        try:
            self.env.sim_model = self
        except Exception:
            pass
        # Ensure time exists before any logging
        self.time = 0
        self.groups = []
        self.loners = []
        # Recent random draws for visualization (kept as short lists)
        self.rnd_history = {
            "regen": [],  # food regeneration amounts
            "clan_growth": [],  # growth increments from friendly encounters
            "loner_spawn": [],  # spawn counts per spawn event
        }

        # Ensure map dimensions are always set before use
        self.map_width = 1200
        self.map_height = 600
        # Spatial grid for neighbor queries (uniform grid)
        # Cell size chosen near typical interaction radius to balance bucket counts
        self.grid_cell_size = 150
        self._grid = {}

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

        # Temperatur-System initialisieren
        if start_temperature is not None:
            self.base_temperature = start_temperature  # Basis-Temperatur (Mittelwert)
            self.current_temperature = (
                start_temperature  # Vom Slider gesetzte Temperatur
            )
        else:
            self.base_temperature = random.uniform(-20, 20)  # Fallback
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
            "Icefang": (0.8, 0.9, 1, 1),
            "Crushed_Critters": (0.6, 0.4, 0.2, 1),
            "Spores": (0.2, 0.8, 0.2, 1),
            "The_Corrupted": (0.5, 0, 0.5, 1),
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
                    "boost": {"hp_mult": 1.18, "combat_mult": 1.12, "hunger_delta": 8},
                    "chance": 0.35,
                }
            },
            "Evergreen_Forest": {
                # Spores native to Evergreen Forest
                "Spores": {
                    "base": {"hp_mult": 1.0, "combat_mult": 1.0, "hunger_delta": 0},
                    "boost": {"hp_mult": 1.2, "combat_mult": 1.15, "hunger_delta": 8},
                    "chance": 0.35,
                }
            },
            "Wasteland": {
                # Crushed_Critters native to Wasteland
                "Crushed_Critters": {
                    "base": {"hp_mult": 1.0, "combat_mult": 1.0, "hunger_delta": 0},
                    "boost": {"hp_mult": 1.18, "combat_mult": 1.1, "hunger_delta": 6},
                    "chance": 0.35,
                }
            },
            "Corrupted_Caves": {
                # The_Corrupted native to Corrupted Caves
                "The_Corrupted": {
                    "base": {"hp_mult": 1.0, "combat_mult": 1.0, "hunger_delta": 0},
                    "boost": {"hp_mult": 1.22, "combat_mult": 1.18, "hunger_delta": 8},
                    "chance": 0.35,
                }
            },
        }
        self._region_mods = region_modifiers.get(self.region_name, {})

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
                if total_requested >= 10
                else 0
            )
            color = color_map.get(species_name, (0.5, 0.5, 0.5, 1))
            # Cap hp per member to avoid extreme per-member HP values from data
            raw_hp = stats.get("hp", 25)
            if species_name == "Icefang":
                hp = min(raw_hp, 40)  # Icefang are tough but not invulnerable
            else:
                hp = min(raw_hp, 70)
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
                                random.uniform(0.85, 1.25) * selected["combat_mult"]
                            )
                    # adjust hunger threshold (higher = seek food later)
                    if "hunger_delta" in selected:
                        clan.hunger_threshold = (
                            getattr(clan, "hunger_threshold", 50)
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

            color = color_map.get(species_name, (0.5, 0.5, 0.5, 1))
            hp = stats.get("hp", 25)
            food_intake = stats.get("food_intake", 5)
            can_cannibalize = species_name in ["Spores", "The_Corrupted"]

            if total_requested < 10:
                # spawn exactly the requested number of loners for this species
                num_loners = int(population_overrides.get(species_name, 0))
            else:
                num_loners = random.randint(2, 5)

            for _ in range(num_loners):
                x = random.uniform(50, self.map_width - 50)
                y = random.uniform(50, self.map_height - 50)
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
                                0.85, 1.25
                            ) * selected.get("combat_mult", 1.0)
                    if "hunger_delta" in selected:
                        loner.hunger_threshold = (
                            getattr(loner, "hunger_threshold", 200)
                            + selected["hunger_delta"]
                        )

                self.loners.append(loner)

        # Erstelle Nahrungsplätze
        self.food_sources = []
        if initial_food_positions:
            # Use provided positions (list of dicts with 'x' and 'y') to ensure
            # preview matches backend initialization exactly.
            for i in range(min(len(initial_food_positions), food_places)):
                pos = initial_food_positions[i]
                x = pos.get("x", random.uniform(100, self.map_width - 100))
                y = pos.get("y", random.uniform(100, self.map_height - 100))
                amt = pos.get("amount", food_amount)
                fs = FoodSource(x, y, amt)
                self.food_sources.append(fs)
            # If fewer provided than requested, generate remaining randomly.
            for _ in range(len(self.food_sources), food_places):
                x = random.uniform(100, self.map_width - 100)
                y = random.uniform(100, self.map_height - 100)
                food_source = FoodSource(x, y, food_amount)
                self.food_sources.append(food_source)
        else:
            for _ in range(food_places):
                x = random.uniform(100, self.map_width - 100)
                y = random.uniform(100, self.map_height - 100)
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

    # --- Spatial grid helpers ---
    def _build_spatial_grid(self):
        """Rebuild a uniform spatial grid mapping (cell_x,cell_y) -> {'clans', 'loners', 'food'}"""
        self._grid = {}
        cs = max(8, int(self.grid_cell_size))

        def _add(entity, kind, x, y):
            cx = int(x) // cs
            cy = int(y) // cs
            key = (cx, cy)
            cell = self._grid.get(key)
            if cell is None:
                cell = {"clans": [], "loners": [], "food": []}
                self._grid[key] = cell
            cell[kind].append(entity)

        # Insert clans
        for group in self.groups:
            for clan in group.clans:
                _add(clan, "clans", clan.x, clan.y)

        # Insert loners
        for loner in self.loners:
            _add(loner, "loners", loner.x, loner.y)

        # Insert food sources
        for f in self.food_sources:
            _add(f, "food", f.x, f.y)

    def _nearby_candidates(self, x, y, radius, kinds=("clans", "loners", "food")):
        """Return candidate entities within grid cells overlapping a radius around (x,y).
        Note: returned candidates are a superset; caller must check exact distance if needed.
        """
        cs = max(8, int(self.grid_cell_size))
        r = max(0, int(radius))
        min_cx = int((x - r)) // cs
        max_cx = int((x + r)) // cs
        min_cy = int((y - r)) // cs
        max_cy = int((y + r)) // cs

        out = []
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                cell = self._grid.get((cx, cy))
                if not cell:
                    continue
                for k in kinds:
                    out.extend(cell.get(k, []))

        return out

    def step(self):

        # --- Random loner spawn logic ---
        # --- Random loner spawn logic ---
        # Verwende Gleichverteilung für Spawn-Anzahl und -Positionen.
        # Pro Spezies: mit 1% Wahrscheinlichkeit spawnt eine zufällige, uniform verteilte Anzahl (1-2) Loners.
        for species_name, stats in self.species_config.items():
            # Skip spawning for species that are currently extinct (no clans and no loners)
            current_count = 0
            for g in self.groups:
                if g.name == species_name:
                    current_count += sum(c.population for c in g.clans)
            current_count += sum(1 for l in self.loners if l.species == species_name)
            if current_count == 0:
                continue

            # Reduce overall spawn frequency to give species a chance to die out
            spawn_threshold = 0.005
            # Icefang spawn even more rarely
            if species_name == "Icefang":
                spawn_threshold = 0.001
            spawn_chance = random.uniform(0.0, 1.0)
            if spawn_chance < spawn_threshold:
                # Spawn a single loner to keep overall pressure low
                spawn_count = 1
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
                for _ in range(spawn_count):
                    # Position ist gleichverteilt im inneren Bereich der Map
                    x = random.uniform(50, self.map_width - 50)
                    y = random.uniform(50, self.map_height - 50)
                    loner = Loner(
                        species_name, x, y, color, hp, food_intake, 0, can_cannibalize
                    )
                    self.loners.append(loner)
                # record spawn event
                if hasattr(self, "rnd_history"):
                    self.rnd_history.setdefault("loner_spawn", []).append(spawn_count)
                    if len(self.rnd_history["loner_spawn"]) > 500:
                        self.rnd_history["loner_spawn"] = self.rnd_history[
                            "loner_spawn"
                        ][-500:]
                # UI log
                self.add_log(
                    (
                        "🔹 {count} neuer Einzelgänger der Spezies {species} ist erschienen!",
                        {"count": spawn_count, "species": species_name},
                    )
                )
                # Terminal debug log for quick diagnostics
                try:
                    tnow = getattr(self, "time", getattr(self.env, "now", 0))
                    print(
                        f"[t={tnow}] DEBUG: Spawn event: {spawn_count} {species_name} at approx positions around ({int(x)},{int(y)})"
                    )
                except Exception:
                    pass
        """Simulationsschritt."""
        # SimPy step
        target = self.env.now + 1
        self.env.run(until=target)
        self.time = int(self.env.now)
        # Container for conversions (clan -> loner) collected during this step
        self._pending_conversions = []

        # Track population history every 10 steps
        if self.time % 10 == 0:
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

        # Tag/Nacht-Zyklus: Wechsel alle 30 Sekunden (300 Steps)
        self.day_night_timer += 1

        # Starte Übergang wenn Zyklus endet
        if (
            self.day_night_timer >= self.day_night_cycle_duration
            and not self.in_transition
        ):
            self.day_night_timer = 0
            self.in_transition = True
            self.transition_timer = 0
            self.transition_to_day = not self.is_day

            if self.transition_to_day:
                self.add_log(("🌅 Sonnenaufgang...", {}))
            else:
                self.add_log(("🌆 Sonnenuntergang...", {}))

        # Übergangs-Logik
        if self.in_transition:
            self.transition_timer += 1

            # Graduelle Temperaturänderung (10°C über transition_duration verteilt)
            # Ziel: +5°C für Tag, -5°C für Nacht (symmetrisch um base_temperature)
            target_offset = 5.0 if self.transition_to_day else -5.0
            progress = self.transition_timer / self.transition_duration
            self.day_night_temp_offset = target_offset * progress

            # Beende Übergang
            if self.transition_timer >= self.transition_duration:
                self.in_transition = False
                self.transition_timer = 0
                self.is_day = self.transition_to_day
                self.stats["is_day"] = self.is_day
                self.day_night_temp_offset = target_offset  # Setze finalen Offset

                if self.is_day:
                    self.add_log(("☀️ Es ist jetzt Tag!", {}))
                else:
                    self.add_log(("🌙 Es ist jetzt Nacht!", {}))

            # Berechne aktuelle Temperatur: Basis + Tag/Nacht Offset
            self.current_temperature = (
                self.base_temperature + self.day_night_temp_offset
            )

            # Begrenze Temperatur
            self.current_temperature = max(-80, min(50, self.current_temperature))
            self.stats["temperature"] = round(self.current_temperature, 1)

        # Temperatur-System: Ändere Basis-Temperatur alle 200 Steps (~20 Sekunden)
        self.temp_change_timer += 1
        if self.temp_change_timer >= 200:
            self.temp_change_timer = 0
            # Zufällige Basis-Temperatur-Änderung (-3 bis +3 Grad)
            temp_change = random.uniform(-3, 3)
            self.base_temperature += temp_change
            # Begrenze Basis-Temperatur auf -80 bis +50 Grad
            self.base_temperature = max(-80, min(50, self.base_temperature))
            # Aktualisiere current_temperature mit neuem Offset
            self.current_temperature = (
                self.base_temperature + self.day_night_temp_offset
            )
            self.current_temperature = max(-80, min(50, self.current_temperature))
            self.stats["temperature"] = round(self.current_temperature, 1)
            self.add_log(
                ("🌡️ Temperatur: {val}°C", {"val": round(self.current_temperature, 1)})
            )

        # Nahrungsregeneration
        for food_source in self.food_sources:
            regen = food_source.regenerate()
            if regen and hasattr(self, "rnd_history"):
                self.rnd_history.setdefault("regen", []).append(regen)
                # keep history short
                if len(self.rnd_history["regen"]) > 500:
                    self.rnd_history["regen"] = self.rnd_history["regen"][-500:]

        # Update Loners und prüfe auf Hungertod und Temperatur-Schaden
        loners_to_remove = []
        for loner in self.loners:
            loner.update(
                self.map_width,
                self.map_height,
                self.is_day,
                self.loner_speed_multiplier,
            )

            # Temperatur-Schaden prüfen
            species_config = self.species_config.get(loner.species, {})
            min_temp = species_config.get("min_survival_temp", -100)
            max_temp = species_config.get("max_survival_temp", 100)

            if (
                self.current_temperature < min_temp
                or self.current_temperature > max_temp
            ):
                # LONERS: Viel höherer Temperatur-Schaden (3x schneller als Clans)
                if self.current_temperature < min_temp:
                    temp_diff = min_temp - self.current_temperature
                else:
                    temp_diff = self.current_temperature - max_temp

                # Erhöhter Schaden für Einzelgänger: 6 HP + 3 HP pro 5 Grad
                # Bei 30 Grad Unterschied: 6 + 18 = 24 HP pro Step
                damage = 6 + (temp_diff // 5) * 3
                damage = max(6, min(damage, 40))  # Min 6, Max 40 HP pro Step

                loner.hp -= damage
                if loner.hp <= 0:
                    loners_to_remove.append(loner)
                    self.add_log(
                        (
                            "❄️ {species} Einzelgänger stirbt an Temperatur ({val}°C)!",
                            {
                                "species": loner.species,
                                "val": round(self.current_temperature, 1),
                            },
                        )
                    )
                    self.stats["deaths"]["temperature"][loner.species] = (
                        self.stats["deaths"]["temperature"].get(loner.species, 0) + 1
                    )

            # Hungertod: Nach 300 Steps (30 Sekunden)
            if loner.hunger_timer >= 300:
                loners_to_remove.append(loner)
                self.add_log(
                    ("☠️ {species} Einzelgänger verhungert!", {"species": loner.species})
                )
                self.stats["deaths"]["starvation"][loner.species] = (
                    self.stats["deaths"]["starvation"].get(loner.species, 0) + 1
                )

        # Entferne verhungerte Loners
        for loner in loners_to_remove:
            if loner in self.loners:
                self.loners.remove(loner)

        # Temperatur-Schaden für Clans
        for group in self.groups:
            species_config = self.species_config.get(group.name, {})
            min_temp = species_config.get("min_survival_temp", -100)
            max_temp = species_config.get("max_survival_temp", 100)

            if (
                self.current_temperature < min_temp
                or self.current_temperature > max_temp
            ):
                # CLANS: Niedrigerer Temperatur-Schaden + 20% Überlebenschance
                if self.current_temperature < min_temp:
                    temp_diff = min_temp - self.current_temperature
                else:
                    temp_diff = self.current_temperature - max_temp

                # Normaler Schaden für Clans: 2 HP + 1 HP pro 5 Grad
                # Bei 30 Grad Unterschied: 2 + 6 = 8 HP pro Step
                damage = 2 + (temp_diff // 5)
                damage = max(2, min(damage, 12))  # Min 2, Max 12 HP pro Step

                # Wende Schaden auf alle Clans dieser Gruppe an
                for clan in group.clans:
                    # 20% Chance pro Tag/Nacht-Zyklus zu überleben
                    # Wenn wir am Anfang eines Zyklus sind, würfeln wir
                    if not hasattr(clan, "temp_survival_roll"):
                        clan.temp_survival_roll = random.random() < 0.2
                    if not hasattr(clan, "last_cycle_state"):
                        clan.last_cycle_state = self.is_day

                    # Reset bei Zyklus-Wechsel
                    if clan.last_cycle_state != self.is_day:
                        clan.last_cycle_state = self.is_day
                        clan.temp_survival_roll = random.random() < 0.2

                    # Wenn Clan die Überlebens-Chance gewonnen hat, überspringe Schaden
                    if clan.temp_survival_roll:
                        continue
                    old_pop = clan.population
                    if not clan.take_damage(damage, self):
                        # Clan ist tot - wird später entfernt
                        pass
                    # Logge wenn Mitglieder sterben
                    if old_pop > clan.population:
                        deaths = old_pop - clan.population
                        self.stats["deaths"]["temperature"][group.name] = (
                            self.stats["deaths"]["temperature"].get(group.name, 0)
                            + deaths
                        )
                        # If a clan shrank to 1 member, schedule conversion to a loner
                        if clan.population == 1:
                            try:
                                self._pending_conversions.append((group, clan))
                            except Exception:
                                pass

        # Rebuild spatial grid and perform proximity-based processing
        self._build_spatial_grid()
        # Nahrungssuche für Clans
        self._process_food_seeking()

        # Prozessiere Interaktionen
        self._process_interactions()

        # Sammle Daten
        groups_data = []
        for group in self.groups:
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
                {
                    "name": group.name,
                    "clans": clans_data,
                    "color": group.color,
                }
            )

        loners_data = [
            {"x": l.x, "y": l.y, "color": l.color, "species": l.species}
            for l in self.loners
        ]

        food_sources_data = [
            {"x": f.x, "y": f.y, "amount": f.amount, "max_amount": f.max_amount}
            for f in self.food_sources
        ]

        # Update current species counts so UI can react (extinction detection)
        try:
            current_counts = {}
            # Count clans
            for g in self.groups:
                current_counts[g.name] = current_counts.get(g.name, 0) + sum(
                    c.population for c in g.clans
                )
            # Count loners
            for l in self.loners:
                current_counts[l.species] = current_counts.get(l.species, 0) + 1
            # Ensure all known species keys exist (keep zeros for disabled species)
            for s in self.species_config.keys():
                current_counts.setdefault(s, 0)
            self.stats["species_counts"] = current_counts
        except Exception:
            pass

        return {
            "time": self.time,
            "groups": groups_data,
            "loners": loners_data,
            "food_sources": food_sources_data,
            "logs": self.logs.copy(),
            "is_day": self.is_day,
            "transition_progress": self._calculate_transition_progress(),
            "stats": self.stats.copy(),
            "rnd_samples": {
                k: list(v) for k, v in getattr(self, "rnd_history", {}).items()
            },
        }

    def _process_food_seeking(self):
        """Nahrungssuche und Essen."""
        FOOD_RANGE = 20  # Wie nah ein Clan sein muss um zu essen
        # Use grid to limit food candidate checks
        FOOD_SEARCH_RADIUS = 400
        # Multiplier applied to loner acceleration when actively searching for food
        # This gives loners a noticeable speed/acceleration boost while homing in.
        LONER_SEARCH_BOOST = 1.5

        # Clans suchen und essen Nahrung
        for group in self.groups:
            for clan in group.clans:
                # Cannibals (Corrupted & Spores) prefer arach prey but will
                # fall back to food sources when no prey is available.
                primary_prey_species = ["Icefang", "Crushed_Critters"]
                primary_prey_exists = any(
                    (
                        g.name in primary_prey_species
                        and any(c.population > 0 for c in g.clans)
                    )
                    for g in self.groups
                ) or any(l.species in primary_prey_species for l in self.loners)

                # If clan can cannibalize, try to find nearest primary prey (clan or loner)
                if clan.can_cannibalize:
                    nearest_prey = None
                    nearest_prey_dist = float("inf")
                    candidates = self._nearby_candidates(
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

                    # If no primary prey nearby and none exist globally, allow hunting other cannibals
                    if not nearest_prey and not primary_prey_exists:
                        candidates = self._nearby_candidates(
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

                    # If hungry, pursue prey
                    if nearest_prey and clan.hunger_timer >= 50:
                        clan.move_towards(
                            getattr(nearest_prey, "x", nearest_prey.x),
                            getattr(nearest_prey, "y", nearest_prey.y),
                            strength=0.6,
                        )

                # Finde nächste Nahrungsquelle (begrenzte Suche via Grid)
                nearest_food = None
                nearest_dist = float("inf")
                candidates = self._nearby_candidates(
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

                # Wenn hungrig (>= 50 Steps = 5 Sekunden), suche aktiv Nahrung
                if clan.seeking_food and nearest_food:
                    clan.move_towards(nearest_food.x, nearest_food.y, strength=0.5)

                # Wenn nah genug, esse
                if nearest_food and nearest_dist < (FOOD_RANGE * FOOD_RANGE):
                    consumed = nearest_food.consume(clan.food_intake)
                    if consumed > 0:
                        # Reset hunger timer: 1 food = 10 Sekunden = 100 Steps
                        clan.hunger_timer = max(0, clan.hunger_timer - (consumed * 10))
                        clan.seeking_food = False
                        # HP-Regeneration: Pro Food +5 HP pro Mitglied (bis max HP)
                        old_hp = clan.hp_per_member
                        species_stats = self.species_config.get(group.name, {})
                        max_hp = species_stats.get("hp", 50)
                        clan.hp_per_member = min(
                            clan.hp_per_member + (consumed * 5),
                            max_hp,
                        )
                        self.add_log(
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

                        # Optional: probabilistisches Wachstum nach Essen
                        try:
                            growth_chance = 0.08
                            if group.name == "Icefang":
                                growth_chance = 0.02
                            if (
                                random.random() < growth_chance
                                and clan.population < clan.max_members
                            ):
                                mu = 1.0
                                sigma = 0.8
                                increase = int(round(random.gauss(mu, sigma)))
                                increase = max(1, increase)
                                space = clan.max_members - clan.population
                                actual = min(increase, max(0, space))
                                if actual > 0:
                                    clan.population += actual
                                    self.add_log(
                                        (
                                            "🌱 {species} Clan #{clan_id} wächst nach Essen (+{increase} Mitglieder)",
                                            {
                                                "species": group.name,
                                                "clan_id": clan.clan_id,
                                                "increase": actual,
                                            },
                                        )
                                    )
                                    if hasattr(self, "rnd_history"):
                                        self.rnd_history.setdefault(
                                            "clan_growth", []
                                        ).append(actual)
                                        if len(self.rnd_history["clan_growth"]) > 500:
                                            self.rnd_history["clan_growth"] = (
                                                self.rnd_history["clan_growth"][-500:]
                                            )
                        except Exception:
                            pass

        # Loners suchen und essen Nahrung
        for loner in self.loners:
            # Cannibal loners prefer primary prey but will fall back to food
            primary_prey_species = ["Icefang", "Crushed_Critters"]
            primary_prey_exists = any(
                (
                    g.name in primary_prey_species
                    and any(c.population > 0 for c in g.clans)
                )
                for g in self.groups
            ) or any(l.species in primary_prey_species for l in self.loners)

            if loner.can_cannibalize:
                nearest_prey = None
                nearest_prey_dist = float("inf")
                candidates = self._nearby_candidates(
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
                    candidates = self._nearby_candidates(
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

                if nearest_prey and loner.hunger_timer >= 200:
                    dx = nearest_prey.x - loner.x
                    dy = nearest_prey.y - loner.y
                    dist_sq = dx * dx + dy * dy
                    if dist_sq > 0:
                        inv = 1.0 / math.sqrt(dist_sq)
                        # Immediately set loner velocity toward prey with boosted speed
                        mult = (
                            getattr(self, "loner_speed_multiplier", 1.0)
                            * LONER_SEARCH_BOOST
                        )
                        base_prey_speed = 3.5
                        vx_target = (dx * inv) * (base_prey_speed * mult)
                        vy_target = (dy * inv) * (base_prey_speed * mult)
                        loner.vx = vx_target
                        loner.vy = vy_target

            # Use grid to limit checks for loners (food fallback)
            nearest_food = None
            nearest_dist = float("inf")
            candidates = self._nearby_candidates(
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

            # Wenn hungrig (>= 200 Steps), suche Nahrung
            if loner.hunger_timer >= 200 and nearest_food:
                dx = nearest_food.x - loner.x
                dy = nearest_food.y - loner.y
                dist_sq = dx * dx + dy * dy
                if dist_sq > 0:
                    inv = 1.0 / math.sqrt(dist_sq)
                    # Immediately set loner velocity toward food with boosted speed
                    mult = (
                        getattr(self, "loner_speed_multiplier", 1.0)
                        * LONER_SEARCH_BOOST
                    )
                    base_food_speed = 3.0
                    vx_target = (dx * inv) * (base_food_speed * mult)
                    vy_target = (dy * inv) * (base_food_speed * mult)
                    loner.vx = vx_target
                    loner.vy = vy_target

            # Wenn nah genug, esse
            if nearest_food and nearest_dist < (FOOD_RANGE * FOOD_RANGE):
                consumed = nearest_food.consume(loner.food_intake)
                if consumed > 0:
                    loner.hunger_timer = max(0, loner.hunger_timer - (consumed * 10))
                    # HP-Regeneration: Pro Food +5 HP (bis max HP)
                    old_hp = loner.hp
                    loner.hp = min(loner.hp + (consumed * 5), loner.max_hp)
                    self.add_log(
                        (
                            "🍽️ {species} Einzelgänger isst {consumed} Food (+{hp_gain} HP)",
                            {
                                "species": loner.species,
                                "consumed": consumed,
                                "hp_gain": int(loner.hp - old_hp),
                            },
                        )
                    )

    def _process_interactions(self):
        """Prozessiere alle Interaktionen zwischen Clans und Loners."""
        ATTACK_DAMAGE = 6  # Fester Attack-Wert (higher to overcome high HP per member)
        INTERACTION_RANGE = 100  # Reichweite für Interaktionen
        HUNT_RANGE = 400  # Reichweite für aktive Jagd (erhöht)
        HUNT_LOG_COOLDOWN = 100  # Nur alle 100 Steps loggen

        # Tracking für Jagd-Logs (verhindert Spam)
        if not hasattr(self, "hunt_log_timer"):
            self.hunt_log_timer = {}

        # Clan vs Clan Interaktionen
        # Determine if primary prey species still exist anywhere (global check)
        primary_prey_species = ["Icefang", "Crushed_Critters"]
        primary_prey_exists = any(
            (g.name in primary_prey_species and any(c.population > 0 for c in g.clans))
            for g in self.groups
        ) or any(l.species in primary_prey_species for l in self.loners)

        for i, group1 in enumerate(self.groups):
            for j, group2 in enumerate(self.groups):
                # Include same-group checks (i == j) so same-species interactions
                # like 'Freundlich' can occur. Skip only strictly earlier indices
                # to avoid duplicate pair processing.
                if i > j:
                    continue

                for clan1 in group1.clans:
                    for clan2 in group2.clans:
                        # When comparing clans within the same group, avoid
                        # self-comparison and duplicate symmetric pairs by
                        # only processing when clan1.clan_id < clan2.clan_id.
                        if group1 is group2 and clan1.clan_id >= clan2.clan_id:
                            continue
                        dist_sq = clan1.distance_to_clan(clan2)

                        # Hole Interaktionstyp aus Matrix
                        interaction = self.interaction_matrix.get(group1.name, {}).get(
                            group2.name, "Neutral"
                        )

                        # SPEZIAL: Corrupted & Spores kämpfen gegeneinander nur wenn
                        # keine primären Arach-Beute mehr existiert.
                        if (
                            clan1.can_cannibalize
                            and clan2.can_cannibalize
                            and group1.name != group2.name
                        ):
                            if not primary_prey_exists:
                                # If primary prey are globally extinct, cannibals fight each other
                                interaction = "Aggressiv"
                            else:
                                # Prefer hunting primary prey; do not force inter-cannibal aggression here
                                pass

                        # Clans derselben Spezies stoßen sich ab (Territorialverhalten)
                        # Exception: wenn die Interaktion explizit 'Freundlich' ist,
                        # lassen wir Clans nahe zusammenkommen (ermöglicht Wachstum).
                        if (
                            group1.name == group2.name
                            and dist_sq < (150 * 150)
                            and interaction != "Freundlich"
                        ):
                            # Bewege sich vom anderen Clan weg
                            dx = clan1.x - clan2.x
                            dy = clan1.y - clan2.y
                            # need actual distance for normalization
                            dist_val = math.sqrt(dist_sq)
                            dist_calc = max(
                                dist_val, 0.1
                            )  # Verhindere Division durch 0
                            repel_strength = 0.3
                            clan1.vx += (dx / dist_calc) * repel_strength
                            clan1.vy += (dy / dist_calc) * repel_strength
                        # AKTIVE JAGD: Bewege dich zum Ziel wenn aggressiv
                        elif interaction == "Aggressiv" and dist_sq < (
                            HUNT_RANGE * HUNT_RANGE
                        ):
                            # Jage das Ziel aktiv mit höherer Stärke
                            clan1.move_towards(clan2.x, clan2.y, strength=0.4)

                            # Logge Jagd (aber nicht zu oft)
                            hunt_key = f"{group1.name}_{clan1.clan_id}_hunts_{group2.name}_{clan2.clan_id}"
                            if (
                                hunt_key not in self.hunt_log_timer
                                or self.time - self.hunt_log_timer[hunt_key]
                                >= HUNT_LOG_COOLDOWN
                            ):
                                self.hunt_log_timer[hunt_key] = self.time
                                # compute readable distance for log
                                self.add_log(
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

                        # Angriff nur in Nahkampfreichweite
                        if dist_sq < (INTERACTION_RANGE * INTERACTION_RANGE):
                            if interaction == "Aggressiv":
                                # Clan1 greift Clan2 an - Bei Nacht reduzierte Kampfchance
                                attack_chance = 0.3 if self.is_day else 0.15
                                # If the target is Icefang and attacker is a natural predator,
                                # increase the chance so predators can contest large Icefang clans.
                                predators = [
                                    "Spores",
                                    "The_Corrupted",
                                    "Crushed_Critters",
                                ]
                                if (
                                    group2.name == "Icefang"
                                    and group1.name in predators
                                ):
                                    attack_chance = 0.6 if self.is_day else 0.35
                                if random.random() < attack_chance:
                                    old_pop = clan2.population
                                    # scale damage by attacker/defender combat strength
                                    atk = getattr(clan1, "combat_strength", 1.0)
                                    df = getattr(clan2, "combat_strength", 1.0)
                                    damage = max(
                                        1,
                                        int(round(ATTACK_DAMAGE * atk / max(0.5, df))),
                                    )
                                    alive = clan2.take_damage(damage, self)
                                    if old_pop > clan2.population:
                                        killed = old_pop - clan2.population
                                        self.add_log(
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

                                        # Kannibalismus: Spores und Corrupted bekommen 2 Food pro Kill
                                        if clan1.can_cannibalize:
                                            food_gained = killed * 2
                                            clan1.hunger_timer = max(
                                                0,
                                                clan1.hunger_timer - (food_gained * 10),
                                            )
                                            self.add_log(
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
                                            self.add_log(
                                                (
                                                    "💀 {species} Clan #{clan_id} vernichtet!",
                                                    {
                                                        "species": group2.name,
                                                        "clan_id": clan2.clan_id,
                                                    },
                                                )
                                            )
                                        else:
                                            # If the attacked clan is still alive but shrank to 1 member,
                                            # schedule conversion to a loner (processed after interactions)
                                            if clan2.population == 1:
                                                try:
                                                    self._pending_conversions.append(
                                                        (group2, clan2)
                                                    )
                                                except Exception:
                                                    pass

                            elif interaction == "Freundlich":
                                # 'Freundlich' behavior differs based on species:
                                # - If same species: allow the friendly-growth path (rare).
                                # - If different species: do NOT merge or grow; instead
                                #   clans may 'stick' together (move closer) about 50% of the time.
                                if group1.name == group2.name:
                                    # Friendly growth only for same-species encounters
                                    # Reduce base friendly-growth to make results less deterministic
                                    growth_chance = 0.03
                                    # Reduce Icefang self-growth further to limit dominance
                                    if group1.name == "Icefang":
                                        growth_chance = 0.005
                                    if random.random() < growth_chance:
                                        if clan1.population < clan1.max_members:
                                            # Ziehe inkrementell Mitglieder aus einer Normalverteilung
                                            mu = 1.0
                                            sigma = 0.8
                                            increase = int(
                                                round(random.gauss(mu, sigma))
                                            )
                                            increase = max(1, increase)
                                            # Nicht über max_members hinauswachsen
                                            space = clan1.max_members - clan1.population
                                            actual = min(increase, max(0, space))
                                            if actual > 0:
                                                clan1.population += actual
                                                self.add_log(
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
                                                # terminal debug print
                                                try:
                                                    tnow = getattr(
                                                        self,
                                                        "time",
                                                        getattr(self.env, "now", 0),
                                                    )
                                                    print(
                                                        f"[t={tnow}] DEBUG: Friendly growth: +{actual} {group1.name} (clan#{clan1.clan_id}) near clan#{clan2.clan_id})"
                                                    )
                                                except Exception:
                                                    pass
                                                if hasattr(self, "rnd_history"):
                                                    self.rnd_history.setdefault(
                                                        "clan_growth", []
                                                    ).append(actual)
                                                    if (
                                                        len(
                                                            self.rnd_history[
                                                                "clan_growth"
                                                            ]
                                                        )
                                                        > 200
                                                    ):
                                                        self.rnd_history[
                                                            "clan_growth"
                                                        ] = self.rnd_history[
                                                            "clan_growth"
                                                        ][
                                                            -500:
                                                        ]
                                else:
                                    # Different-species 'friendly' — do not merge. 50% chance
                                    # to gently stick (move toward each other), otherwise ignore.
                                    try:
                                        if random.random() < 0.5:
                                            clan1.move_towards(
                                                clan2.x, clan2.y, strength=0.2
                                            )
                                            clan2.move_towards(
                                                clan1.x, clan1.y, strength=0.2
                                            )
                                    except Exception:
                                        pass

                            elif interaction == "Ängstlich":
                                # Fliehe vom Ziel weg
                                dx = clan1.x - clan2.x
                                dy = clan1.y - clan2.y
                                dist_sq_local = dx * dx + dy * dy
                                if dist_sq_local > 0:
                                    inv = 1.0 / math.sqrt(dist_sq_local)
                                    clan1.vx += (dx * inv) * 0.4
                                    clan1.vy += (dy * inv) * 0.4

        # Clan vs Loner Interaktionen
        loners_to_remove = []
        for group in self.groups:
            for clan in group.clans:
                for loner in self.loners:
                    dist_sq = clan.distance_to_loner(loner)

                    interaction = self.interaction_matrix.get(group.name, {}).get(
                        loner.species, "Neutral"
                    )

                    # AKTIVE JAGD auf Loners (HÖHERE PRIORITÄT als Clans!)
                    if interaction == "Aggressiv" and dist_sq < (
                        HUNT_RANGE * HUNT_RANGE
                    ):
                        # Loners sind bevorzugte Ziele - 2x stärkere Verfolgung!
                        clan.move_towards(
                            loner.x, loner.y, strength=0.7
                        )  # War 0.35, jetzt 0.7

                        # Logge Jagd (aber nicht zu oft)
                        hunt_key = f"{group.name}_{clan.clan_id}_hunts_loner_{loner.species}_{id(loner)}"
                        if (
                            hunt_key not in self.hunt_log_timer
                            or self.time - self.hunt_log_timer[hunt_key]
                            >= HUNT_LOG_COOLDOWN
                        ):
                            self.hunt_log_timer[hunt_key] = self.time
                            self.add_log(
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
                            # Clan greift Loner an - ERHÖHTE Angriffschance für Loners!
                            attack_chance = (
                                0.6 if self.is_day else 0.3
                            )  # War 0.4/0.2, jetzt 0.6/0.3
                            if random.random() < attack_chance:
                                # scale damage by attacker/defender combat strength
                                atk = getattr(clan, "combat_strength", 1.0)
                                df = getattr(loner, "combat_strength", 1.0)
                                damage = max(
                                    1, int(round(ATTACK_DAMAGE * atk / max(0.5, df)))
                                )
                                loner.hp -= damage
                                if loner.hp <= 0:
                                    loners_to_remove.append(loner)
                                    self.add_log(
                                        (
                                            "⚔️ {attacker} Clan #{att_id} tötet {loner_species} Einzelgänger",
                                            {
                                                "attacker": group.name,
                                                "att_id": clan.clan_id,
                                                "loner_species": loner.species,
                                            },
                                        )
                                    )
                                    self.stats["deaths"]["combat"][loner.species] = (
                                        self.stats["deaths"]["combat"].get(
                                            loner.species, 0
                                        )
                                        + 1
                                    )

                                    # Kannibalismus: Spores und Corrupted bekommen 2 Food pro Loner
                                    if clan.can_cannibalize:
                                        clan.hunger_timer = max(
                                            0, clan.hunger_timer - 20
                                        )  # 2 Food = 20 Steps
                                        self.add_log(
                                            (
                                                "🍖 {species} Clan #{clan_id} frisst {loner_species} (+2 Food)",
                                                {
                                                    "species": group.name,
                                                    "clan_id": clan.clan_id,
                                                    "loner_species": loner.species,
                                                },
                                            )
                                        )

                        elif interaction == "Freundlich":
                            # Loner kann Clan beitreten
                            # Höhere Chance wenn hungrig (>50 steps ohne Essen)
                            join_chance = 0.03  # 3% Basis-Chance
                            if loner.hunger_timer >= 50:
                                join_chance = 0.15  # 15% wenn hungrig

                            if (
                                random.random() < join_chance
                                and loner.species == group.name  # Nur gleiche Spezies
                            ):
                                clan.population += 1
                                loners_to_remove.append(loner)
                                reason = (
                                    "hungrig"
                                    if loner.hunger_timer >= 50
                                    else "freundlich"
                                )
                                self.add_log(
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

                                # Prüfe ob Clan jetzt splitten sollte
                                if clan.population > clan.max_members:
                                    group.check_clan_splits()

        # Entferne getötete Loners
        for loner in loners_to_remove:
            if loner in self.loners:
                self.loners.remove(loner)

        # Clan-Bildung: 2+ Einzelgänger derselben Spezies können sich zusammenschließen
        self._process_loner_clan_formation()

        # Process any scheduled clan -> loner conversions collected during this step
        try:
            if hasattr(self, "_pending_conversions") and self._pending_conversions:
                for group, clan in list(self._pending_conversions):
                    try:
                        if clan in group.clans and clan.population == 1:
                            # Create a loner from the last remaining clan member
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
                            self.loners.append(loner)
                            try:
                                group.clans.remove(clan)
                            except Exception:
                                pass
                            self.add_log(
                                (
                                    "⚠️ Clan #{clan_id} von {group} reduzierte sich auf 1 und wurde zu Einzelgänger konvertiert.",
                                    {"clan_id": clan.clan_id, "group": group.name},
                                )
                            )
                    except Exception:
                        pass
                self._pending_conversions = []
        except Exception:
            pass

    def _process_loner_clan_formation(self):
        """Einzelgänger können sich zu einem neuen Clan zusammenschließen."""
        FORMATION_RANGE = 50  # Wie nah Loners sein müssen

        # Gruppiere Loners nach Spezies
        species_loners = {}
        for loner in self.loners:
            if loner.species not in species_loners:
                species_loners[loner.species] = []
            species_loners[loner.species].append(loner)

        # Prüfe für jede Spezies ob Clan-Bildung möglich ist
        for species_name, loners_list in species_loners.items():
            if len(loners_list) < 2:
                continue  # Mindestens 2 Loners nötig

            # Finde Gruppe dieser Spezies
            group = None
            for g in self.groups:
                if g.name == species_name:
                    group = g
                    break

            if not group or len(group.clans) >= 15:
                continue  # Keine Gruppe oder zu viele Clans

            # Prüfe Loner-Paare auf Nähe
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

                # Wenn 2+ Loners nah beieinander sind: 5% Chance für Clan-Bildung
                if len(nearby_loners) >= 2 and random.random() < 0.05:
                    # Erstelle neuen Clan
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

                    # Entferne Loners
                    for loner in nearby_loners:
                        if loner in self.loners:
                            self.loners.remove(loner)
                        checked_loners.append(loner)

                    self.add_log(
                        (
                            "🤝 {count} {species} Einzelgänger schließen sich zu Clan #{clan_id} zusammen!",
                            {
                                "count": len(nearby_loners),
                                "species": species_name,
                                "clan_id": new_clan.clan_id,
                            },
                        )
                    )
                    break  # Nur ein Clan pro Durchlauf pro Spezies

    def get_final_stats(self):
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

    def set_temperature(self, temp):
        """Set temperature."""
        pass

    def set_food_level(self, level):
        """Set food level."""
        pass

    def set_day_night(self, is_day):
        """Set day/night."""
        pass

    def set_loner_speed(self, multiplier):
        """Set loner speed multiplier (0.5 to 2.0)."""
        self.loner_speed_multiplier = max(0.5, min(2.0, multiplier))

    def set_clan_speed(self, multiplier):
        """Set clan speed multiplier (0.5 to 2.0)."""
        self.clan_speed_multiplier = max(0.5, min(2.0, multiplier))
