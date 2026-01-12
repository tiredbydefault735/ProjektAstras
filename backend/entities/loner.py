"""Loner entity."""

import random
import math


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
