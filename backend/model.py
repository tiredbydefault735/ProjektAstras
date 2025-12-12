"""
Simulation Model - Neu aufgebaut für smoothe, glitch-freie Bewegung
"""

import simpy
import random
import math


class Loner:
    """Einzelgänger - bewegt sich unabhängig."""

    def __init__(self, species, x, y, color):
        self.species = species
        self.x = x
        self.y = y
        self.color = color
        # Sehr langsame Geschwindigkeit
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)

    def update(self, width, height):
        """Bewege Loner."""
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
            speed = random.uniform(0.3, 0.7)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed


class Clan:
    """Ein Clan - bewegt sich als Gruppe."""

    def __init__(self, clan_id, species, x, y, population, color, max_members):
        self.clan_id = clan_id
        self.species = species
        self.x = x
        self.y = y
        self.population = population
        self.color = color
        self.max_members = max_members
        # Sehr langsame, sanfte Bewegung
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.3, 0.3)

    def update(self, width, height):
        """Bewege Clan langsam und smooth."""
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

        # Gelegentliche sanfte Richtungsänderung (selten!)
        if random.random() < 0.01:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.2, 0.4)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed


class SpeciesGroup:
    """Verwaltet alle Clans einer Spezies."""

    def __init__(
        self, env, name, start_population, color, max_members, map_width, map_height
    ):
        self.env = env
        self.name = name
        self.color = color
        self.max_members = max_members
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
                self.next_clan_id, name, x, y, start_population, color, max_members
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
        self.map_width = 1200
        self.map_height = 600
        self.logs = []
        self.max_logs = 50
        self.time = 0

    def add_log(self, message):
        """Log-Nachricht hinzufügen."""
        log_entry = f"[t={self.time}] {message}"
        self.logs.append(log_entry)
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs :]

    def setup(self, species_config, population_overrides):
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

        # Erstelle Gruppen
        for species_name, stats in species_config.items():
            start_pop = population_overrides.get(species_name, 0)
            color = color_map.get(species_name, (0.5, 0.5, 0.5, 1))

            group = SpeciesGroup(
                self.env,
                species_name,
                start_pop,
                color,
                stats["max_clan_members"],
                self.map_width,
                self.map_height,
            )
            self.groups.append(group)

        # Erstelle Einzelgänger (2-5 pro Spezies)
        for species_name, stats in species_config.items():
            color = color_map.get(species_name, (0.5, 0.5, 0.5, 1))
            num_loners = random.randint(2, 5)

            for _ in range(num_loners):
                x = random.uniform(50, self.map_width - 50)
                y = random.uniform(50, self.map_height - 50)
                loner = Loner(species_name, x, y, color)
                self.loners.append(loner)

        # Referenz für Logging
        self.env.sim_model = self

        total_pop = sum(sum(c.population for c in g.clans) for g in self.groups)
        self.add_log(
            f"Start: {len(self.groups)} Spezies, {total_pop} Mitglieder, {len(self.loners)} Einzelgänger"
        )

    def step(self):
        """Simulationsschritt."""
        # SimPy step
        target = self.env.now + 1
        self.env.run(until=target)
        self.time = int(self.env.now)

        # Update Loners
        for loner in self.loners:
            loner.update(self.map_width, self.map_height)

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

        return {
            "time": self.time,
            "groups": groups_data,
            "loners": loners_data,
            "logs": self.logs.copy(),
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
