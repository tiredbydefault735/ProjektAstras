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

    def consume(self, requested_amount):
        """Konsumiere Nahrung, gibt tatsächlich konsumierte Menge zurück."""
        consumed = min(requested_amount, self.amount)
        self.amount -= consumed
        return consumed

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
        # Schnellere Geschwindigkeit
        self.vx = random.uniform(-1.2, 1.2)
        self.vy = random.uniform(-1.2, 1.2)
        # Nahrungssystem
        self.food_intake = food_intake  # Wie viel Food benötigt wird
        self.hunger_timer = (
            hunger_timer  # Sekunden seit letzter Nahrung (1 Step = 0.1s)
        )
        self.can_cannibalize = can_cannibalize  # Kann andere Arachs essen

    def update(self, width, height):
        """Bewege Loner."""
        # Hunger erhöhen
        self.hunger_timer += 1

        self.x += self.vx
        self.y += self.vy

        # Bounce an Rändern
        if self.x < 10 or self.x > width - 10:
            self.vx = -self.vx
            self.x = max(10, min(width - 10, self.x))
        if self.y < 10 or self.y > height - 10:
            self.vy = -self.vy
            self.y = max(10, min(height - 10, self.y))

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
        # Schnellere Bewegung
        self.vx = random.uniform(-1.0, 1.0)
        self.vy = random.uniform(-1.0, 1.0)
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
            max_speed = 2.0
            current_speed = math.sqrt(self.vx * self.vx + self.vy * self.vy)
            if current_speed > max_speed:
                self.vx = (self.vx / current_speed) * max_speed
                self.vy = (self.vy / current_speed) * max_speed

    def update(self, width, height):
        """Bewege Clan langsam und smooth."""
        # Hunger erhöhen (jeder Step = 0.1 Sekunden)
        self.hunger_timer += 1

        # Nach 50 Steps (5 Sekunden) wird Food gesucht
        if self.hunger_timer >= 50:
            self.seeking_food = True

        self.x += self.vx
        self.y += self.vy

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
        self.max_clans = 4
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

            # Update alle Clans
            for clan in self.clans:
                clan.update(self.map_width, self.map_height)

                # Hungertod: Nach 100 Steps (10 Sekunden) sterben Mitglieder
                if clan.hunger_timer >= 100:
                    deaths = max(1, clan.population // 5)  # 20% der Population stirbt
                    clan.population -= deaths
                    if hasattr(self.env, "sim_model"):
                        self.env.sim_model.add_log(
                            f"☠️ {self.name} Clan #{clan.clan_id}: {deaths} Mitglied(er) verhungert!"
                        )
                        self.env.sim_model.stats["deaths"]["starvation"][self.name] = (
                            self.env.sim_model.stats["deaths"]["starvation"].get(
                                self.name, 0
                            )
                            + deaths
                        )

                # Langsames Population-Wachstum
                if random.random() < 0.05:
                    change = random.randint(-1, 2)
                    clan.population += change
                    clan.population = max(0, min(clan.population, clan.max_members))

            # Clan-Splitting wenn zu groß
            self.check_clan_splits()

            # Entferne leere Clans
            self.clans = [c for c in self.clans if c.population > 0]

    def check_clan_splits(self):
        """Teile Clans wenn sie zu groß werden."""
        for clan in self.clans[:]:
            if clan.population > self.max_members and len(self.clans) < self.max_clans:
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
                        f"{self.name} Clan #{clan.clan_id} → Clan #{new_clan.clan_id} (je {clan.population})"
                    )


class SimulationModel:
    """Haupt-Simulation."""

    def __init__(self):
        self.env = simpy.Environment()
        self.groups = []
        self.loners = []
        self.food_sources = []
        self.map_width = 1200
        self.map_height = 600
        self.logs = []
        self.max_logs = 50
        self.time = 0

        # Statistics tracking
        self.stats = {
            "species_counts": {},  # Initial counts per species
            "deaths": {
                "combat": {},  # Deaths by combat per species
                "starvation": {},  # Deaths by starvation per species
            },
            "max_clans": 0,
            "food_places": 0,
        }

    def add_log(self, message):
        """Log-Nachricht hinzufügen."""
        log_entry = f"[t={self.time}] {message}"
        self.logs.append(log_entry)
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs :]

    def setup(
        self, species_config, population_overrides, food_places=5, food_amount=50
    ):
        """Initialisiere Simulation."""
        self.groups = []
        self.loners = []

        # Farben für Spezies
        color_map = {
            "Icefang": (0.8, 0.9, 1, 1),
            "Crushed_Critters": (0.6, 0.4, 0.2, 1),
            "Spores": (0.2, 0.8, 0.2, 1),
            "The_Corrupted": (0.5, 0, 0.5, 1),
        }

        # Speichere Config für Interaktionen
        self.species_config = species_config

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
            self.groups.append(group)

        # Erstelle Einzelgänger (2-5 pro Spezies)
        for species_name, stats in species_config.items():
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

        # Referenz für Logging
        self.env.sim_model = self

        total_pop = sum(sum(c.population for c in g.clans) for g in self.groups)
        self.add_log(
            f"Start: {len(self.groups)} Spezies, {total_pop} Mitglieder, {len(self.loners)} Einzelgänger"
        )

        # Initialize statistics
        self.stats["food_places"] = food_places
        total_clans = sum(len(g.clans) for g in self.groups)
        self.stats["max_clans"] = total_clans

        # Count initial population per species
        for group in self.groups:
            species_name = group.name
            clan_pop = sum(c.population for c in group.clans)
            loner_pop = sum(1 for l in self.loners if l.species == species_name)
            self.stats["species_counts"][species_name] = clan_pop + loner_pop
            self.stats["deaths"]["combat"][species_name] = 0
            self.stats["deaths"]["starvation"][species_name] = 0

    def step(self):
        """Simulationsschritt."""
        # SimPy step
        target = self.env.now + 1
        self.env.run(until=target)
        self.time = int(self.env.now)

        # Update Loners und prüfe auf Hungertod
        loners_to_remove = []
        for loner in self.loners:
            loner.update(self.map_width, self.map_height)

            # Hungertod: Nach 100 Steps (10 Sekunden)
            if loner.hunger_timer >= 100:
                loners_to_remove.append(loner)
                self.add_log(f"☠️ {loner.species} Einzelgänger verhungert!")
                self.stats["deaths"]["starvation"][loner.species] = (
                    self.stats["deaths"]["starvation"].get(loner.species, 0) + 1
                )

        # Entferne verhungerte Loners
        for loner in loners_to_remove:
            if loner in self.loners:
                self.loners.remove(loner)

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

        return {
            "time": self.time,
            "groups": groups_data,
            "loners": loners_data,
            "food_sources": food_sources_data,
            "logs": self.logs.copy(),
        }

    def _process_food_seeking(self):
        """Nahrungssuche und Essen."""
        FOOD_RANGE = 20  # Wie nah ein Clan sein muss um zu essen

        # Clans suchen und essen Nahrung
        for group in self.groups:
            for clan in group.clans:
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
                        self.add_log(
                            f"🍽️ {group.name} Clan #{clan.clan_id} isst {consumed} Food"
                        )

        # Loners suchen und essen Nahrung
        for loner in self.loners:
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

            # Wenn hungrig (>= 50 Steps), suche Nahrung
            if loner.hunger_timer >= 50 and nearest_food:
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
                    self.add_log(f"🍽️ {loner.species} Einzelgänger isst {consumed} Food")

    def _process_interactions(self):
        """Prozessiere alle Interaktionen zwischen Clans und Loners."""
        ATTACK_DAMAGE = 3  # Fester Attack-Wert
        INTERACTION_RANGE = 100  # Reichweite für Interaktionen
        HUNT_RANGE = 300  # Reichweite für aktive Jagd

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

                        # AKTIVE JAGD: Bewege dich zum Ziel wenn aggressiv
                        if interaction == "Aggressiv" and dist < HUNT_RANGE:
                            # Jage das Ziel aktiv
                            clan1.move_towards(clan2.x, clan2.y, strength=0.25)

                        # Angriff nur in Nahkampfreichweite
                        if dist < INTERACTION_RANGE:
                            if interaction == "Aggressiv":
                                # Clan1 greift Clan2 an - HÖHERE Chance
                                if (
                                    random.random() < 0.3
                                ):  # 30% Chance pro Step (war 15%)
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

                    # AKTIVE JAGD auf Loners
                    if interaction == "Aggressiv" and dist < HUNT_RANGE:
                        clan.move_towards(loner.x, loner.y, strength=0.2)

                    if dist < INTERACTION_RANGE:
                        if interaction == "Aggressiv":
                            # Clan greift Loner an - HÖHERE Chance
                            if random.random() < 0.4:  # 40% Chance (war 20%)
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
                                and clan.population < clan.max_members
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
                                    f"👥 {loner.species} Einzelgänger ({reason}) tritt {group.name} Clan #{clan.clan_id} bei"
                                )

        # Entferne getötete Loners
        for loner in loners_to_remove:
            if loner in self.loners:
                self.loners.remove(loner)

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
