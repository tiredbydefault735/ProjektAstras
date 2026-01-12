"""Clan entity."""

import random
import math


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
