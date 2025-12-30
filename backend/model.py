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
        """Regeneriere Nahrung über Zeit (alle 50 Steps = 5 Sekunden)."""
        self.regeneration_timer += 1
        if self.regeneration_timer >= 50:
            self.regeneration_timer = 0
            if self.amount < self.max_amount:
                self.amount = min(self.amount + 5, self.max_amount)

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

    def total_hp(self):
        """Gesamte HP des Clans."""
        return self.population * self.hp_per_member

    def take_damage(self, damage, sim_model=None):
        """Nimmt Schaden und reduziert Population wenn nötig."""
        remaining_damage = damage
        deaths = 0
        while remaining_damage > 0 and self.population > 0:
            if remaining_damage >= self.hp_per_member:
                # Töte ein Mitglied
                self.population -= 1
                deaths += 1
                remaining_damage -= self.hp_per_member
            else:
                # Teilschaden (wird ignoriert, nur volle Member sterben)
                remaining_damage = 0

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
        return math.sqrt(dx * dx + dy * dy)

    def distance_to_loner(self, loner):
        """Distanz zu Einzelgänger."""
        dx = self.x - loner.x
        dy = self.y - loner.y
        return math.sqrt(dx * dx + dy * dy)

    def distance_to_food(self, food_source):
        """Distanz zu Nahrungsquelle."""
        dx = self.x - food_source.x
        dy = self.y - food_source.y
        return math.sqrt(dx * dx + dy * dy)

    def move_towards(self, target_x, target_y, strength=0.3):
        """Bewege Clan sanft in Richtung eines Ziels."""
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > 0:
            # Normalisiere Richtung und füge zur Velocity hinzu
            self.vx += (dx / dist) * strength
            self.vy += (dy / dist) * strength

            # Begrenze maximale Geschwindigkeit (verhindert Glitching)
            max_speed = 4.0
            current_speed = math.sqrt(self.vx * self.vx + self.vy * self.vy)
            if current_speed > max_speed:
                self.vx = (self.vx / current_speed) * max_speed
                self.vy = (self.vy / current_speed) * max_speed

    def update(self, width, height, is_day=True, speed_multiplier=1.0):
        """Bewege Clan langsam und smooth."""
        # Hunger erhöhen (jeder Step = 0.1 Sekunden)
        self.hunger_timer += 1

        # Nach 200 Steps (20 Sekunden) wird Food gesucht
        if self.hunger_timer >= 200:
            self.seeking_food = True

        # Bei Nacht: Langsamere Bewegung (70% Geschwindigkeit)
        speed_modifier = 1.0 if is_day else 0.7
        # Apply global speed multiplier
        speed_modifier *= speed_multiplier
        self.x += self.vx * speed_modifier
        self.y += self.vy * speed_modifier

        # Bounce an Rändern (mit Margin von 30px)
        if self.x < 30:
            self.x = 30
            self.vx = abs(self.vx)
        elif self.x > width - 30:
            self.x = width - 30
            self.vx = -abs(self.vx)

        if self.y < 30:
            self.y = 30
            self.vy = abs(self.vy)
        elif self.y > height - 30:
            self.y = height - 30
            self.vy = -abs(self.vy)

        # Sehr leichtes Dampening für natürliche Bewegung
        self.vx *= 0.98
        self.vy *= 0.98

        # Gelegentliche Richtungsänderung
        if random.random() < 0.01:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.7, 1.2)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed


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
        self.max_clans = 8  # Erhöht für mehr Splits
        self.clans = []
        self.next_clan_id = 0

        # Erstelle initialen Clan
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
                0,  # hunger_timer startet bei 0
                can_cannibalize,
            )
            self.clans.append(clan)
            self.next_clan_id += 1

        self.process = env.process(self.live())

    def live(self):
        """Haupt-Simulation-Loop."""
        while True:
            yield self.env.timeout(1)

            # Hole Tag/Nacht Status vom Model
            is_day = getattr(self.env, "sim_model", None) and getattr(
                self.env.sim_model, "is_day", True
            )

            # Update alle Clans
            for clan in self.clans:
                # Use default speed multiplier (1.0) since sim_model is not available here
                clan.update(
                    self.map_width,
                    self.map_height,
                    is_day,
                    1.0,
                )

                # Hungertod: Nach 300 Steps (30 Sekunden) sterben Mitglieder
                if clan.hunger_timer >= 300:
                    deaths = max(1, clan.population // 10)  # 10% der Population stirbt
                    clan.population -= deaths
                    # Logging and stats update must be handled in SimulationModel

                # Clan mit 1 Mitglied wird zum Einzelgänger
                if clan.population == 1:
                    # Logging and loner creation must be handled in SimulationModel
                    clan.population = 0  # Markiere zum Entfernen

                # Einzelgänger-Abspaltung: 2% Chance wenn Clan > 3 Mitglieder
                elif clan.population > 3 and random.random() < 0.02:
                    clan.population -= 1
                    # Logging and loner creation must be handled in SimulationModel

            # Clan-Splitting mit Gaußscher Normalverteilung
            self.check_clan_splits()

            # Entferne leere Clans
            self.clans = [c for c in self.clans if c.population > 0]

    def check_clan_splits(self):
        """Teile Clans wenn sie zu groß werden (Gaußsche Normalverteilung)."""
        for clan in self.clans[:]:
            if len(self.clans) >= 15:
                continue  # Max 15 Clans

            # Pflicht-Split bei Überschreitung von max_members
            if clan.population > clan.max_members:
                split_chance = 1.0  # 100% Split
            # Gaußsche Normalverteilung: Split-Wahrscheinlichkeit steigt ab 50% von max_members
            elif clan.population >= clan.max_members * 0.5:
                # Berechne wie nah wir an max_members sind (0.0 bis 1.0)
                progress = (clan.population - clan.max_members * 0.5) / (
                    clan.max_members * 0.5
                )
                # Gaußsche Funktion: exp(-((x-1)^2) / 0.5)
                # Je näher an max_members, desto höher die Wahrscheinlichkeit
                import math

                split_chance = (
                    math.exp(-((1 - progress) ** 2) / 0.5) * 0.15
                )  # Max 15% Chance
            else:
                continue  # Zu klein für Split

            # Prüfe ob Split erfolgt
            if random.random() < split_chance:
                # Split
                pop_half = clan.population // 2
                clan.population = clan.population - pop_half

                # Neuer Clan in der Nähe
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
                    0,  # neuer Clan startet ohne Hunger
                    clan.can_cannibalize,
                )
                self.clans.append(new_clan)
                self.next_clan_id += 1

                if hasattr(self.env, "sim_model"):
                    self.env.sim_model.add_log(
                        f"✂️ {self.name} Clan #{clan.clan_id} teilt sich! → Clan #{new_clan.clan_id} (je {clan.population} Mitglieder)"
                    )
                    self.env.sim_model.add_log(
                        f"🎉 Neue Population: Clan #{clan.clan_id} ({clan.population}) + Clan #{new_clan.clan_id} ({pop_half}) = {clan.population + pop_half} Mitglieder"
                    )


class SimulationModel:
    # --- Areal Disaster Grid System ---
    def init_grid(self, cell_size=40):
        """Initialize a grid for areal disasters. cell_size in pixels."""
        self.cell_size = cell_size
        self.grid_width = int(self.map_width // cell_size)
        self.grid_height = int(self.map_height // cell_size)
        # Each cell: 0 = unaffected, 1 = affected by disaster
        self.disaster_grid = [
            [0 for _ in range(self.grid_width)] for _ in range(self.grid_height)
        ]
        self.areal_disaster_origin = None  # (x, y) in grid coords
        self.areal_disaster_sigma = 2  # Default spread (cells)

    def start_areal_disaster(self, x, y, sigma=2):
        """Begin an areal disaster at (x, y) in map coordinates."""
        if not hasattr(self, "disaster_grid"):
            self.init_grid()
        gx, gy = int(x // self.cell_size), int(y // self.cell_size)
        self.areal_disaster_origin = (gx, gy)
        self.areal_disaster_sigma = sigma
        self.update_areal_disaster_grid()

    def update_areal_disaster_grid(self):
        """Update the grid using a tiled (checkerboard) pattern for wildfire."""
        if self.areal_disaster_origin is None:
            return
        if not hasattr(self, "disaster_grid") or self.disaster_grid is None:
            self.init_grid(self.cell_size if hasattr(self, "cell_size") else 40)
        # Tiled checkerboard pattern: alternate affected/unaffected cells
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                self.disaster_grid[y][x] = 1 if (x + y) % 2 == 0 else 0

    def is_cell_affected(self, x, y):
        """Check if a map coordinate (x, y) is in an affected cell."""
        if not hasattr(self, "disaster_grid") or self.disaster_grid is None:
            return False
        gx, gy = int(x // self.cell_size), int(y // self.cell_size)
        if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
            return self.disaster_grid[gy][gx] == 1
        return False

    """Haupt-Simulation."""

    def __init__(self):
        self.env = simpy.Environment()
        self.groups = []
        self.loners = []
        self.food_sources = []
        self.map_width = 1200
        self.map_height = 600
        self.logs = []
        self.max_logs = 300  # Increased from 50 for longer history
        self.time = 0

        # Speed multipliers (1.0 = normal speed)
        self.loner_speed_multiplier = 1.0
        self.clan_speed_multiplier = 1.0

        # Disaster system
        from backend.disasters import DisasterManager

        self.disaster_manager = None  # Will be set in setup()
        self.disaster_events = []  # Track disaster events (start, end, name, time)
        self.current_disaster_event = None

        # Statistics tracking
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
            "disasters": [],  # List of disaster events for stats dialog
        }

    def add_log(self, message):
        """Log-Nachricht hinzufügen."""
        log_entry = f"[t={self.time}] {message}"
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
        self.groups = []
        self.loners = []

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

        # Re-initialize statistics to ensure temperature is included
        self.stats["deaths"]["temperature"] = {}

        # Farben für Spezies
        color_map = {
            "Icefang": (0.8, 0.9, 1, 1),
            "Crushed_Critters": (0.6, 0.4, 0.2, 1),
            "Spores": (0.2, 0.8, 0.2, 1),
            "The_Corrupted": (0.5, 0, 0.5, 1),
        }

        # Speichere Config für Interaktionen
        self.species_config = species_config

        # Initialize disaster manager for this region
        if region_name:
            from backend.disasters import DisasterManager

            self.disaster_manager = DisasterManager(region=region_name)
        else:
            self.disaster_manager = None

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
            num_loners = random.randint(2, 5)

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

        # Referenz für Logging (removed for SimPy compatibility)
        # self.env.sim_model = self

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

        # --- Natural Disaster Logic ---
        active_disaster = None
        disaster_effects = None
        if self.disaster_manager:
            # Try to trigger a new disaster if none is active
            if not self.disaster_manager.get_active_disaster():
                triggered = self.disaster_manager.maybe_trigger_disaster()
                if triggered:
                    name, d = triggered
                    self.add_log(
                        f"⚠️ Naturkatastrophe: {d['name']} beginnt! (Dauer: {d.get('duration', 1)}s)"
                    )
                    # Track start of disaster event
                    self.current_disaster_event = {
                        "name": d["name"],
                        "start": self.time,
                        "end": None,
                    }
                    active_disaster = d
                    disaster_effects = d.get("effects", {})
            else:
                # Advance disaster timer
                self.disaster_manager.step()
                # If disaster just ended, log it and track end
                if (
                    self.current_disaster_event
                    and not self.disaster_manager.get_active_disaster()
                ):
                    self.add_log("✅ Die Naturkatastrophe ist vorbei.")
                    self.current_disaster_event["end"] = self.time
                    self.disaster_events.append(self.current_disaster_event)
                    self.current_disaster_event = None
                else:
                    # Disaster is still active
                    ad = self.disaster_manager.get_active_disaster()
                    if ad:
                        _, d = ad
                        active_disaster = d
                        disaster_effects = d.get("effects", {})

        # Apply disaster effects if any
        if disaster_effects:
            # --- Areal disaster grid for Wildfire (Waldbrand) ---
            if active_disaster and active_disaster.get("name") == "Waldbrand":
                # If not already started, pick a random origin and start grid
                if (
                    not hasattr(self, "disaster_grid")
                    or self.disaster_grid is None
                    or self.areal_disaster_origin is None
                ):
                    # Pick a random origin in map coordinates
                    x = random.uniform(0, self.map_width)
                    y = random.uniform(0, self.map_height)
                    self.init_grid(cell_size=40)
                    self.start_areal_disaster(x, y, sigma=2)
                else:
                    # Optionally, animate spread (not implemented here)
                    self.update_areal_disaster_grid()
            else:
                # For non-areal disasters, provide a blank grid (all 0s) so overlay is only visible for areal disasters
                self.init_grid(cell_size=40)
                for y in range(self.grid_height):
                    for x in range(self.grid_width):
                        self.disaster_grid[y][x] = 0
                self.areal_disaster_origin = None

            # Population damage (only in affected grid cells for areal disasters)
            pop_damage = disaster_effects.get("population_damage")
            if pop_damage:
                # Reduce lethality: halve the effect for all disasters, cap at 5% per step
                pop_damage = min(0.05, pop_damage * 0.5)
                for group in self.groups:
                    for clan in group.clans:
                        affected = True
                        # For Wildfire, only affect if in grid
                        if (
                            active_disaster
                            and active_disaster.get("name") == "Waldbrand"
                        ):
                            affected = self.is_cell_affected(clan.x, clan.y)
                        if clan.population > 0 and affected:
                            deaths = max(1, int(clan.population * pop_damage))
                            old_pop = clan.population
                            clan.population -= deaths
                            if clan.population < 0:
                                clan.population = 0
                            if old_pop > clan.population:
                                self.stats["deaths"].setdefault(
                                    "disaster", {}
                                ).setdefault(group.name, 0)
                                self.stats["deaths"]["disaster"][group.name] += (
                                    old_pop - clan.population
                                )
                                self.add_log(
                                    f"☠️ {group.name} Clan #{clan.clan_id} verliert {old_pop - clan.population} Mitglieder durch Katastrophe!"
                                )
            # Health drain (flat HP loss per step)
            health_drain = disaster_effects.get("health_drain")
            if health_drain:
                for group in self.groups:
                    for clan in group.clans:
                        if hasattr(clan, "hp_per_member") and clan.population > 0:
                            clan.hp_per_member = max(
                                1, clan.hp_per_member - health_drain
                            )
            # Movement speed multiplier
            move_mult = disaster_effects.get("movement_speed")
            if move_mult:
                self.clan_speed_multiplier = move_mult
                self.loner_speed_multiplier = move_mult
            else:
                self.clan_speed_multiplier = 1.0
                self.loner_speed_multiplier = 1.0
            # Food destruction (percentage of food lost per step)
            food_destruction = disaster_effects.get("food_destruction")
            if food_destruction:
                for food in self.food_sources:
                    destroyed = int(food.amount * food_destruction)
                    if destroyed > 0:
                        food.amount = max(0, food.amount - destroyed)
                        self.add_log(
                            f"🔥 {destroyed} Nahrung durch Katastrophe zerstört!"
                        )
            # Food contamination (percentage of food made unusable)
            food_contamination = disaster_effects.get("food_contamination")
            if food_contamination:
                for food in self.food_sources:
                    contaminated = int(food.amount * food_contamination)
                    if contaminated > 0:
                        food.amount = max(0, food.amount - contaminated)
                        self.add_log(
                            f"☣️ {contaminated} Nahrung durch Katastrophe kontaminiert!"
                        )
            # Temperature modifier (additive)
            temp_mod = disaster_effects.get("temperature_modifier")
            if temp_mod:
                self.current_temperature += temp_mod
                self.add_log(
                    f"🌡️ Temperatur durch Katastrophe verändert: {temp_mod:+}°C"
                )
            # TODO: Implement more effects as needed (area_blocked, movement_blocked, water_scarcity, etc.)

        # Update stats with current disaster events for UI/stats dialog
        # Copy all finished events, and if a disaster is active, add it as running
        self.stats["disasters"] = list(self.disaster_events)
        if self.current_disaster_event:
            # Show running disaster with no end
            self.stats["disasters"] = self.stats["disasters"] + [
                dict(self.current_disaster_event)
            ]

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
                x = random.uniform(50, self.map_width - 50)
                y = random.uniform(50, self.map_height - 50)
                loner = Loner(
                    species_name, x, y, color, hp, food_intake, 0, can_cannibalize
                )
                self.loners.append(loner)
                self.add_log(
                    f"🔹 Ein neuer Einzelgänger der Spezies {species_name} ist erschienen!"
                )
        """Simulationsschritt."""
        # SimPy step
        target = self.env.now + 1
        self.env.run(until=target)
        self.time = int(self.env.now)

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
                self.add_log(f"🌅 Sonnenaufgang...")
            else:
                self.add_log(f"🌆 Sonnenuntergang...")

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
                    self.add_log(f"☀️ Es ist jetzt Tag!")
                else:
                    self.add_log(f"🌙 Es ist jetzt Nacht!")

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
            self.add_log(f"🌡️ Temperatur: {round(self.current_temperature, 1)}°C")

        # Nahrungsregeneration
        for food_source in self.food_sources:
            food_source.regenerate()

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
                        f"❄️ {loner.species} Einzelgänger stirbt an Temperatur ({round(self.current_temperature, 1)}°C)!"
                    )
                    self.stats["deaths"]["temperature"][loner.species] = (
                        self.stats["deaths"]["temperature"].get(loner.species, 0) + 1
                    )

            # Hungertod: Nach 300 Steps (30 Sekunden)
            if loner.hunger_timer >= 300:
                loners_to_remove.append(loner)
                self.add_log(f"☠️ {loner.species} Einzelgänger verhungert!")
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

        # Add areal disaster grid for visualization if present
        disaster_grid = None
        if hasattr(self, "disaster_grid") and self.disaster_grid:
            disaster_grid = self.disaster_grid
        return {
            "time": self.time,
            "groups": groups_data,
            "loners": loners_data,
            "food_sources": food_sources_data,
            "logs": self.logs.copy(),
            "is_day": self.is_day,
            "transition_progress": self._calculate_transition_progress(),
            "stats": self.stats.copy(),
            "disaster_grid": disaster_grid,
        }

    def _process_food_seeking(self):
        """Nahrungssuche und Essen."""
        FOOD_RANGE = 20  # Wie nah ein Clan sein muss um zu essen

        # Clans suchen und essen Nahrung
        for group in self.groups:
            for clan in group.clans:
                # Kannibalen (Corrupted & Spores) essen keine Nahrung - nur Jagd!
                if clan.can_cannibalize:
                    continue

                # Finde nächste Nahrungsquelle
                nearest_food = None
                nearest_dist = float("inf")

                for food_source in self.food_sources:
                    if not food_source.is_depleted():
                        dist = clan.distance_to_food(food_source)
                        if dist < nearest_dist:
                            nearest_dist = dist
                            nearest_food = food_source

                # Wenn hungrig (>= 50 Steps = 5 Sekunden), suche aktiv Nahrung
                if clan.seeking_food and nearest_food:
                    clan.move_towards(nearest_food.x, nearest_food.y, strength=0.5)

                # Wenn nah genug, esse
                if nearest_food and nearest_dist < FOOD_RANGE:
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
                            f"🍽️ {group.name} Clan #{clan.clan_id} isst {consumed} Food (+{clan.hp_per_member - old_hp} HP)"
                        )

                        # Kein automatisches Wachstum beim Essen mehr
                        # Clans wachsen nur durch Einzelgänger-Anschluss

        # Loners suchen und essen Nahrung
        for loner in self.loners:
            # Kannibalen (Corrupted & Spores) essen keine Nahrung - nur Jagd!
            if loner.can_cannibalize:
                continue

            nearest_food = None
            nearest_dist = float("inf")

            for food_source in self.food_sources:
                if not food_source.is_depleted():
                    dx = loner.x - food_source.x
                    dy = loner.y - food_source.y
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest_food = food_source

            # Wenn hungrig (>= 200 Steps), suche Nahrung
            if loner.hunger_timer >= 200 and nearest_food:
                dx = nearest_food.x - loner.x
                dy = nearest_food.y - loner.y
                dist_calc = math.sqrt(dx * dx + dy * dy)
                if dist_calc > 0:
                    loner.vx += (dx / dist_calc) * 0.5
                    loner.vy += (dy / dist_calc) * 0.5

            # Wenn nah genug, esse
            if nearest_food and nearest_dist < FOOD_RANGE:
                consumed = nearest_food.consume(loner.food_intake)
                if consumed > 0:
                    loner.hunger_timer = max(0, loner.hunger_timer - (consumed * 10))
                    # HP-Regeneration: Pro Food +5 HP (bis max HP)
                    old_hp = loner.hp
                    loner.hp = min(loner.hp + (consumed * 5), loner.max_hp)
                    self.add_log(
                        f"🍽️ {loner.species} Einzelgänger isst {consumed} Food (+{loner.hp - old_hp} HP)"
                    )

    def _process_interactions(self):
        """Prozessiere alle Interaktionen zwischen Clans und Loners."""
        ATTACK_DAMAGE = 2  # Fester Attack-Wert (reduziert für längeres Überleben)
        INTERACTION_RANGE = 100  # Reichweite für Interaktionen
        HUNT_RANGE = 400  # Reichweite für aktive Jagd (erhöht)
        HUNT_LOG_COOLDOWN = 100  # Nur alle 100 Steps loggen

        # Tracking für Jagd-Logs (verhindert Spam)
        if not hasattr(self, "hunt_log_timer"):
            self.hunt_log_timer = {}

        # Clan vs Clan Interaktionen
        for i, group1 in enumerate(self.groups):
            for j, group2 in enumerate(self.groups):
                if i >= j:
                    continue  # Vermeide doppelte Checks

                for clan1 in group1.clans:
                    for clan2 in group2.clans:
                        dist = clan1.distance_to_clan(clan2)

                        # Hole Interaktionstyp aus Matrix
                        interaction = self.interaction_matrix.get(group1.name, {}).get(
                            group2.name, "Neutral"
                        )

                        # SPEZIAL: Corrupted & Spores kämpfen gegeneinander wenn keine Hauptbeute da
                        # Wenn clan1 ein Kannibal ist (Corrupted/Spores) und clan2 auch...
                        if (
                            clan1.can_cannibalize
                            and clan2.can_cannibalize
                            and group1.name != group2.name
                        ):  # Verschiedene Kannibalen-Arten
                            # Prüfe ob Hauptbeute (Icefang/Crushed_Critters) in Reichweite ist
                            has_primary_prey = False
                            for other_group in self.groups:
                                if other_group.name in ["Icefang", "Crushed_Critters"]:
                                    for other_clan in other_group.clans:
                                        prey_dist = clan1.distance_to_clan(other_clan)
                                        if prey_dist < HUNT_RANGE:
                                            has_primary_prey = True
                                            break
                                if has_primary_prey:
                                    break

                            # Keine Hauptbeute da? Dann kämpfen sie gegeneinander!
                            if not has_primary_prey:
                                interaction = "Aggressiv"

                        # Clans derselben Spezies stoßen sich ab (Territorialverhalten)
                        if group1.name == group2.name and dist < 150:
                            # Bewege sich vom anderen Clan weg
                            dx = clan1.x - clan2.x
                            dy = clan1.y - clan2.y
                            dist_calc = max(dist, 0.1)  # Verhindere Division durch 0
                            repel_strength = 0.3
                            clan1.vx += (dx / dist_calc) * repel_strength
                            clan1.vy += (dy / dist_calc) * repel_strength
                        # AKTIVE JAGD: Bewege dich zum Ziel wenn aggressiv
                        elif interaction == "Aggressiv" and dist < HUNT_RANGE:
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
                                self.add_log(
                                    f"🎯 {group1.name} Clan #{clan1.clan_id} jagt {group2.name} Clan #{clan2.clan_id}! (Distanz: {int(dist)}px)"
                                )

                        # Angriff nur in Nahkampfreichweite
                        if dist < INTERACTION_RANGE:
                            if interaction == "Aggressiv":
                                # Clan1 greift Clan2 an - Bei Nacht reduzierte Kampfchance
                                attack_chance = (
                                    0.3 if self.is_day else 0.15
                                )  # 30% Tag, 15% Nacht
                                if random.random() < attack_chance:
                                    old_pop = clan2.population
                                    alive = clan2.take_damage(ATTACK_DAMAGE, self)
                                    if old_pop > clan2.population:
                                        killed = old_pop - clan2.population
                                        self.add_log(
                                            f"⚔️ {group1.name} Clan #{clan1.clan_id} → {group2.name} Clan #{clan2.clan_id} (-{killed} Mitglied)"
                                        )

                                        # Kannibalismus: Spores und Corrupted bekommen 2 Food pro Kill
                                        if clan1.can_cannibalize:
                                            food_gained = killed * 2
                                            clan1.hunger_timer = max(
                                                0,
                                                clan1.hunger_timer - (food_gained * 10),
                                            )
                                            self.add_log(
                                                f"🍖 {group1.name} Clan #{clan1.clan_id} frisst {killed} Arach(s) (+{food_gained} Food)"
                                            )

                                        if not alive:
                                            self.add_log(
                                                f"💀 {group2.name} Clan #{clan2.clan_id} vernichtet!"
                                            )

                            elif interaction == "Freundlich":
                                # Freundliche Begegnung - Population Bonus (selten)
                                if random.random() < 0.02:
                                    if clan1.population < clan1.max_members:
                                        clan1.population += 1
                                        self.add_log(
                                            f"🤝 {group1.name} & {group2.name}: Freundliche Begegnung (+1 Mitglied)"
                                        )

                            elif interaction == "Ängstlich":
                                # Fliehe vom Ziel weg
                                dx = clan1.x - clan2.x
                                dy = clan1.y - clan2.y
                                dist_calc = math.sqrt(dx * dx + dy * dy)
                                if dist_calc > 0:
                                    clan1.vx += (dx / dist_calc) * 0.4
                                    clan1.vy += (dy / dist_calc) * 0.4

        # Clan vs Loner Interaktionen
        loners_to_remove = []
        for group in self.groups:
            for clan in group.clans:
                for loner in self.loners:
                    dist = clan.distance_to_loner(loner)

                    interaction = self.interaction_matrix.get(group.name, {}).get(
                        loner.species, "Neutral"
                    )

                    # AKTIVE JAGD auf Loners (HÖHERE PRIORITÄT als Clans!)
                    if interaction == "Aggressiv" and dist < HUNT_RANGE:
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
                                f"🎯 {group.name} Clan #{clan.clan_id} jagt {loner.species} Einzelgänger! (Distanz: {int(dist)}px)"
                            )

                    if dist < INTERACTION_RANGE:
                        if interaction == "Aggressiv":
                            # Clan greift Loner an - ERHÖHTE Angriffschance für Loners!
                            attack_chance = (
                                0.6 if self.is_day else 0.3
                            )  # War 0.4/0.2, jetzt 0.6/0.3
                            if random.random() < attack_chance:
                                loner.hp -= ATTACK_DAMAGE
                                if loner.hp <= 0:
                                    loners_to_remove.append(loner)
                                    self.add_log(
                                        f"⚔️ {group.name} Clan #{clan.clan_id} tötet {loner.species} Einzelgänger"
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
                                            f"🍖 {group.name} Clan #{clan.clan_id} frisst {loner.species} (+2 Food)"
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
                                    f"👥 {loner.species} Einzelgänger ({reason}) tritt {group.name} Clan #{clan.clan_id} bei ({clan.population - 1} → {clan.population})"
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
                    dist = math.sqrt(dx * dx + dy * dy)

                    if dist < FORMATION_RANGE:
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
                        f"🤝 {len(nearby_loners)} {species_name} Einzelgänger schließen sich zu Clan #{new_clan.clan_id} zusammen!"
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
