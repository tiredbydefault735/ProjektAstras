import simpy
import random


class ArachfaraGroup:
    def __init__(self, env, name, start_population, stats, color):
        self.env = env
        self.name = name
        self.population = start_population
        self.stats = stats  # Hier speichern wir das ganze Dictionary (min_temp, etc.)
        self.color = color
        self.food = 100
        self.process = env.process(self.live())

    def live(self):
        while True:
            yield self.env.timeout(1)

            # Hier könnten wir später auf stats zugreifen:
            # if current_temp < self.stats['min_survival_temp']: sterben()

            self.food -= int(self.population * 0.05)

            # Einfache Begrenzung durch max_clan_members aus der JSON
            limit = self.stats["max_clan_members"]

            if random.random() < 0.2:
                change = random.randint(-2, 4)
                self.population += change

            # Hard Limits (0 bis Max Clan Members)
            if self.population < 0:
                self.population = 0
            if self.population > limit:
                self.population = limit  # Das Limit aus der JSON greift hier!
            if self.food < 0:
                self.food = 0


class SimulationModel:
    def __init__(self):
        self.env = simpy.Environment()
        self.groups = []

    def setup(self, species_config, population_overrides):
        """
        species_config: Der Inhalt der Species.json
        population_overrides: Ein Dictionary mit Start-Populationen aus der GUI
                              z.B. {"Icefang": 5, "Spores": 10}
        """
        self.groups = []

        # Wir definieren hier feste Farben für die Spezies (könnte man auch ins JSON packen)
        # In model.py -> setup()
        color_map = {
            "Icefang": (0.8, 0.9, 1, 1),  # Eisblau
            "Crushed_Critters": (0.6, 0.4, 0.2, 1),  # Braun
            "Spores": (0.2, 0.8, 0.2, 1),  # Grün
            "The_Corrupted": (0.5, 0, 0.5, 1),  # Lila
        }

        # Wir iterieren durch die JSON-Daten
        for species_name, stats in species_config.items():

            # 1. Start-Population ermitteln (GUI-Wert oder 0 falls leer)
            start_pop = population_overrides.get(species_name, 0)

            # 2. Farbe wählen (Default Grau, falls Name nicht in color_map)
            color = color_map.get(species_name, (0.5, 0.5, 0.5, 1))

            # 3. Gruppe erstellen
            new_group = ArachfaraGroup(self.env, species_name, start_pop, stats, color)
            self.groups.append(new_group)

        print(f"Simulation initialisiert mit {len(self.groups)} Spezies.")

    def step(self):
        # ... (bleibt gleich wie vorher) ...
        target = self.env.now + 1
        self.env.run(until=target)
        groups_data = []
        for g in self.groups:
            groups_data.append(
                {
                    "name": g.name,
                    "population": g.population,
                    "food": g.food,
                    "color": g.color,
                }
            )
        return {"time": self.env.now, "groups": groups_data}
