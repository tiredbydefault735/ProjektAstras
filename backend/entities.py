"""
Entity classes extracted from `backend/model.py`:
- FoodSource
- Loner
- Clan

These are plain data/behavior classes used by the simulation.
"""

import random
import math
from config import *


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
        """Stochastic, small food regeneration events."""
        if self.amount >= self.max_amount:
            return 0
        regen_prob = FOOD_REGEN_PROB
        if random.random() < regen_prob:
            regen_choices = REGEN_CHOICES
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
        self.hp = hp
        self.max_hp = hp
        self.vx = random.uniform(*LONER_VELOCITY_RANGE)
        self.vy = random.uniform(*LONER_VELOCITY_RANGE)
        self.food_intake = food_intake
        self.hunger_timer = hunger_timer
        self.can_cannibalize = can_cannibalize
        self.combat_strength = random.uniform(*COMBAT_STRENGTH_RANGE)
        self.hunger_threshold = random.randint(*HUNGER_THRESHOLD_RANGE)

    def update(self, width, height, is_day=True, speed_multiplier=1.0):
        self.hunger_timer += 1
        speed_modifier = 1.0 if is_day else NIGHT_SPEED_MODIFIER
        speed_modifier *= speed_multiplier
        self.x += self.vx * speed_modifier
        self.y += self.vy * speed_modifier
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
        if random.random() < RANDOM_MOVE_PROB:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(*LONER_SPEED_INIT_RANGE)
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
        self.hp_per_member = hp_per_member
        self.vx = random.uniform(*CLAN_VELOCITY_RANGE)
        self.vy = random.uniform(*CLAN_VELOCITY_RANGE)
        self.food_intake = food_intake
        self.hunger_timer = hunger_timer
        self.can_cannibalize = can_cannibalize
        self.seeking_food = False
        self.combat_strength = random.uniform(*COMBAT_STRENGTH_RANGE)
        self.hunger_threshold = random.randint(*LONER_HUNGER_RANGE)

    def total_hp(self):
        return self.population * self.hp_per_member

    def take_damage(self, damage, sim_model=None):
        if not hasattr(self, "_accum_damage"):
            self._accum_damage = 0
        self._accum_damage += damage
        deaths = 0
        if self.hp_per_member > 0:
            deaths = int(self._accum_damage // self.hp_per_member)
            if deaths > 0:
                removed = min(self.population, deaths)
                self.population -= removed
                deaths = removed
                self._accum_damage -= removed * self.hp_per_member
        if deaths > 0 and sim_model:
            sim_model.stats["deaths"]["combat"][self.species] = (
                sim_model.stats["deaths"]["combat"].get(self.species, 0) + deaths
            )
        return self.population > 0

    def distance_to_clan(self, other_clan):
        dx = self.x - other_clan.x
        dy = self.y - other_clan.y
        return dx * dx + dy * dy

    def distance_to_loner(self, loner):
        dx = self.x - loner.x
        dy = self.y - loner.y
        return dx * dx + dy * dy

    def distance_to_food(self, food_source):
        dx = self.x - food_source.x
        dy = self.y - food_source.y
        return dx * dx + dy * dy

    def move_towards(
        self,
        tx,
        ty,
        strength=MOVE_TOWARDS_DEFAULT_STRENGTH,
        max_speed=MOVE_TOWARDS_MAX_SPEED,
    ):
        dx = tx - self.x
        dy = ty - self.y
        dist_sq = dx * dx + dy * dy
        if dist_sq <= 0:
            return
        inv = 1.0 / math.sqrt(dist_sq)
        self.vx += (dx * inv) * strength
        self.vy += (dy * inv) * strength
        speed_sq = self.vx * self.vx + self.vy * self.vy
        if speed_sq > (max_speed * max_speed):
            s = max_speed / math.sqrt(speed_sq)
            self.vx *= s
            self.vy *= s

    def update(self, width, height, is_day=True, speed_multiplier=1.0):
        if not hasattr(self, "hunger_timer"):
            self.hunger_timer = 0
        self.hunger_timer += 1
        speed_modifier = 1.0 if is_day else NIGHT_SPEED_MODIFIER
        speed_modifier *= speed_multiplier
        self.x += self.vx * speed_modifier
        self.y += self.vy * speed_modifier
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
        if random.random() < RANDOM_MOVE_PROB:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(*LONER_SPEED_ALT_RANGE)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
        if self.hunger_timer >= getattr(self, "hunger_threshold", HUNGER_ALERT):
            self.seeking_food = True
