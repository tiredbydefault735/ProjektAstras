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
        # For areal disasters
        self.area_center = None  # (x, y)
        self.area_radius = None

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
                # If areal, initialize area
                if d.get("type") == "areal":
                    # Center and radius can be set by simulation model
                    self.area_center = None
                    self.area_radius = None
                return (name, d)
        return None

    def step(self):
        """Advance disaster timer, spread areal disaster, and clear if finished."""
        if self.active_disaster:
            name, d = self.active_disaster
            # Spread areal disaster (20% chance per step)
            if d.get("type") == "areal" and self.area_center and self.area_radius:
                if random.random() < 0.2:
                    self.area_radius += random.uniform(5, 15)  # Spread by 5-15 units
            self.disaster_timer -= 1
            if self.disaster_timer <= 0:
                self.active_disaster = None
                self.area_center = None
                self.area_radius = None

    def get_active_disaster(self):
        return self.active_disaster

    def set_areal_area(self, center, radius):
        self.area_center = center
        self.area_radius = radius

    def get_areal_area(self):
        if self.area_center and self.area_radius:
            return {"center": self.area_center, "radius": self.area_radius}
        return None
