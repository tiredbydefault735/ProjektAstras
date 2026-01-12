"""SpeciesGroup entity."""

import random
import math
from .clan import Clan


class SpeciesGroup:
    """Verwaltet alle Clans einer Spezies."""

    # Disaster-related helpers removed

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

            # Update alle Clans using per-species multipliers when available
            for clan in self.clans:
                speed_mult = 1.0
                if hasattr(self.env, "sim_model") and getattr(self.env, "sim_model"):
                    sim = self.env.sim_model
                    speed_mult = sim.clan_speed_multipliers.get(
                        self.name, sim.clan_speed_multiplier
                    )
                clan.update(
                    self.map_width,
                    self.map_height,
                    is_day,
                    speed_mult,
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
