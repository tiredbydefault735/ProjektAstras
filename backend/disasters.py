import json
import random
import os


class DisasterManager:
    def __init__(self, region, disaster_file=None):
        if disaster_file is None:
            disaster_file = os.path.join(
                os.path.dirname(__file__), "../static/data/disasters.json"
            )
        with open(disaster_file, encoding="utf-8") as f:
            self.disasters = json.load(f)
        self.region = region
        self.active_disaster = None
        self.disaster_timer = 0

    def maybe_trigger_disaster(self):
        """Randomly trigger a disaster for the current region. Shuffle so all have a fair chance."""
        candidates = [
            (name, d)
            for name, d in self.disasters.items()
            if self.region in d.get("regions", [])
        ]
        random.shuffle(candidates)
        for name, d in candidates:
            if random.random() < d.get("probability", 0):
                self.active_disaster = (name, d)
                self.disaster_timer = d.get("duration", 1)
                return (name, d)
        return None

    def step(self):
        """Advance disaster timer and clear if finished."""
        if self.active_disaster:
            self.disaster_timer -= 1
            if self.disaster_timer <= 0:
                self.active_disaster = None

    def get_active_disaster(self):
        return self.active_disaster
