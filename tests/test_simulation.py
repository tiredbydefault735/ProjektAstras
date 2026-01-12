import unittest
from backend.model import SimulationModel


class TestSimulationBehavior(unittest.TestCase):
    def test_loner_temperature_and_hunger(self):
        sim = SimulationModel()
        species_config = {
            "Icefang": {
                "max_clan_members": 6,
                "hp": 20,
                "food_intake": 3,
                "min_survival_temp": -10,
                "max_survival_temp": 40,
            }
        }
        pops = {"Icefang": 1}
        sim.setup(
            species_config,
            pops,
            food_places=0,
            food_amount=0,
            start_temperature=100,
            start_is_day=True,
        )
        # Run a few steps to cause loner temperature deaths
        for _ in range(5):
            sim.step()
        # After steps, temperature deaths should be recorded
        self.assertIn("Icefang", sim.stats["deaths"]["temperature"])
        self.assertGreaterEqual(sim.stats["deaths"]["temperature"]["Icefang"], 1)

    def test_clan_temperature_and_hunger(self):
        sim = SimulationModel()
        species_config = {
            "Icefang": {
                "max_clan_members": 6,
                "hp": 20,
                "food_intake": 3,
                "min_survival_temp": -10,
                "max_survival_temp": 40,
            }
        }
        pops = {"Icefang": 5}
        sim.setup(
            species_config,
            pops,
            food_places=0,
            food_amount=0,
            start_temperature=100,
            start_is_day=True,
        )
        # Run some steps to trigger clan temp/hunger deaths
        for _ in range(10):
            sim.step()
        # Ensure temperature or starvation deaths recorded
        t_deaths = sim.stats["deaths"]["temperature"].get("Icefang", 0)
        s_deaths = sim.stats["deaths"]["starvation"].get("Icefang", 0)
        self.assertTrue(t_deaths + s_deaths >= 1)


if __name__ == "__main__":
    unittest.main()
