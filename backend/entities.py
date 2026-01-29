"""
Entity classes extracted from `backend/model.py`:
- FoodSource
- Loner
- Clan

These are plain data/behavior classes used by the simulation.
"""

from __future__ import annotations
import random
import math
import logging
from typing import TYPE_CHECKING, Optional, Union

from config import *

if TYPE_CHECKING:
    from backend.model import SimulationModel

logger = logging.getLogger(__name__)


class FoodSource:
    """Represents a food source in the simulation.

    @ivar x: X-coordinate of the food source
    @ivar y: Y-coordinate of the food source
    @ivar amount: Current amount of food available
    @ivar max_amount: Maximum capacity of the food source
    @ivar regeneration_timer: Timer for regeneration events
    """

    def __init__(self, x: float, y: float, amount: float) -> None:
        """Initialize the food source.

        @param x: X-coordinate position
        @param y: Y-coordinate position
        @param amount: Initial food amount
        """
        self.x: float = x
        self.y: float = y
        self.amount: float = amount
        self.max_amount: float = amount
        self.regeneration_timer: int = 0

    def consume(self, requested_amount: float) -> float:
        """Consume a specified amount of food from the source.

        @param requested_amount: The amount of food requested to consume
        @return: The actual amount of food consumed
        """
        consumed = min(requested_amount, self.amount)
        self.amount -= consumed
        return consumed

    def regenerate(self) -> float:
        """Regenerate food amount stochastically.

        @return: The amount of food regenerated
        """
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

    def is_depleted(self) -> bool:
        """Check if the food source is empty.

        @return: True if amount is less than or equal to 0, False otherwise
        """
        return self.amount <= 0


class Loner:
    """Represents a solitary entity in the simulation.

    @ivar species: Species name of the loner
    @ivar x: X-coordinate position
    @ivar y: Y-coordinate position
    @ivar color: Color representation for UI
    @ivar hp: Current health points
    @ivar max_hp: Maximum health points
    @ivar vx: Velocity in x-direction
    @ivar vy: Velocity in y-direction
    @ivar food_intake: Food value obtained when eating
    @ivar hunger_timer: Timer to track hunger state
    @ivar can_cannibalize: Whether the loner can eat its own species
    """

    def __init__(
        self,
        species: str,
        x: float,
        y: float,
        color: str,
        hp: float,
        food_intake: float,
        hunger_timer: int,
        can_cannibalize: bool,
    ) -> None:
        """Initialize a new Loner entity.

        @param species: The species identifier
        @param x: Initial X position
        @param y: Initial Y position
        @param color: Visual color of the entity
        @param hp: Initial health points
        @param food_intake: Amount of food consumed per action
        @param hunger_timer: Initial state of hunger
        @param can_cannibalize: Flag indicating cannibalism capability
        """
        self.species: str = species
        self.x: float = x
        self.y: float = y
        self.color: str = color
        self.hp: float = hp
        self.max_hp: float = hp
        self.vx: float = random.uniform(*LONER_VELOCITY_RANGE)
        self.vy: float = random.uniform(*LONER_VELOCITY_RANGE)
        self.food_intake: float = food_intake
        self.hunger_timer: float = hunger_timer
        self.can_cannibalize: bool = can_cannibalize
        self.combat_strength: float = random.uniform(*COMBAT_STRENGTH_RANGE)
        self.hunger_threshold: int = random.randint(*HUNGER_THRESHOLD_RANGE)

    def update(
        self,
        width: float,
        height: float,
        is_day: bool = True,
        speed_multiplier: float = 1.0,
    ) -> None:
        """Update the loner's position and state.

        @param width: Width of the simulation area
        @param height: Height of the simulation area
        @param is_day: Boolean flag indicating if it is day time
        @param speed_multiplier: Factor to adjust movement speed
        """
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
    """Represents a group of entities moving together.

    @ivar clan_id: Unique identifier for the clan
    @ivar species: Species of the clan members
    @ivar x: X-coordinate of the clan center
    @ivar y: Y-coordinate of the clan center
    @ivar population: Current number of members
    @ivar color: Visual color of the clan
    @ivar max_members: Maximum allowed population
    @ivar hp_per_member: Health points per individual member
    @ivar vx: Velocity in x-direction
    @ivar vy: Velocity in y-direction
    @ivar food_intake: Food consumption rate
    @ivar hunger_timer: Timer for hunger state
    @ivar can_cannibalize: Whether clan practices cannibalism
    @ivar seeking_food: State flag for food seeking behavior
    """

    def __init__(
        self,
        clan_id: str,
        species: str,
        x: float,
        y: float,
        population: int,
        color: str,
        max_members: int,
        hp_per_member: float,
        food_intake: float,
        hunger_timer: int,
        can_cannibalize: bool,
    ) -> None:
        """Initialize a new Clan entity.

        @param clan_id: Unique identifier for the clan
        @param species: Species name
        @param x: Initial X position
        @param y: Initial Y position
        @param population: Initial number of members
        @param color: Visual color
        @param max_members: Maximum allowed population
        @param hp_per_member: Health points per individual member
        @param food_intake: Food consumption rate
        @param hunger_timer: Initial hunger state
        @param can_cannibalize: Whether the clan practices cannibalism
        """
        self.clan_id: str = clan_id
        self.species: str = species
        self.x: float = x
        self.y: float = y
        self.population: int = population
        self.color: str = color
        self.max_members: int = max_members
        self.hp_per_member: float = hp_per_member
        self.vx: float = random.uniform(*CLAN_VELOCITY_RANGE)
        self.vy: float = random.uniform(*CLAN_VELOCITY_RANGE)
        self.food_intake: float = food_intake
        self.hunger_timer: int = hunger_timer
        self.can_cannibalize: bool = can_cannibalize
        self.seeking_food: bool = False
        self.combat_strength: float = random.uniform(*COMBAT_STRENGTH_RANGE)
        self.hunger_threshold: int = random.randint(*LONER_HUNGER_RANGE)

    def total_hp(self) -> float:
        """Calculate the total health points of the clan.

        @return: Total HP (population * hp_per_member)
        """
        return self.population * self.hp_per_member

    def take_damage(
        self, damage: float, sim_model: Optional[SimulationModel] = None
    ) -> bool:
        """Apply damage to the clan, reducing population if necessary.

        @param damage: Amount of damage to apply
        @param sim_model: Optional reference to the simulation model for stats
        @return: True if the clan survives, False if population reaches 0
        """
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

    def distance_to_clan(self, other_clan: Clan) -> float:
        """Calculate squared distance to another clan.

        @param other_clan: The other clan entity
        @return: Squared Euclidean distance
        """
        dx = self.x - other_clan.x
        dy = self.y - other_clan.y
        return dx * dx + dy * dy

    def distance_to_loner(self, loner: Loner) -> float:
        """Calculate squared distance to a loner.

        @param loner: The loner entity
        @return: Squared Euclidean distance
        """
        dx = self.x - loner.x
        dy = self.y - loner.y
        return dx * dx + dy * dy

    def distance_to_food(self, food_source: FoodSource) -> float:
        """Calculate squared distance to a food source.

        @param food_source: The food source entity
        @return: Squared Euclidean distance
        """
        dx = self.x - food_source.x
        dy = self.y - food_source.y
        return dx * dx + dy * dy

    def move_towards(
        self,
        tx: float,
        ty: float,
        strength: float = MOVE_TOWARDS_DEFAULT_STRENGTH,
        max_speed: float = MOVE_TOWARDS_MAX_SPEED,
    ) -> None:
        """Adjust velocity to move towards a target position.

        @param tx: Target X coordinate
        @param ty: Target Y coordinate
        @param strength: Strength of the steering force
        @param max_speed: Maximum speed limit
        """
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

    def update(
        self,
        width: float,
        height: float,
        is_day: bool = True,
        speed_multiplier: float = 1.0,
    ) -> None:
        """Update clan position and state.

        @param width: Simulation area width
        @param height: Simulation area height
        @param is_day: Is it currently day time
        @param speed_multiplier: Movement speed adjustment factor
        """
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
