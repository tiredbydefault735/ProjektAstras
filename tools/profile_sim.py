"""
Profile the SimulationModel stepping loop using cProfile and print top hotspots.
Run this with your Python executable.
"""

import sys
import json
import cProfile
import pstats
import io
from pathlib import Path

# ensure repo root is on path
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import config
from utils import get_static_path
from backend.model import SimulationModel


def load_species_config():
    try:
        p = get_static_path(config.SPECIES_DATA_PATH)
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def build_populations(species_config, default_count=10):
    if not species_config:
        return {"Default": default_count}
    pops = {}
    # species_config may be mapping from id->data
    for k in list(species_config.keys())[:4]:
        pops[k] = default_count
    if not pops:
        pops = {list(species_config.keys())[0]: default_count}
    return pops


def run_steps(steps=2000):
    species_config = load_species_config()
    populations = build_populations(species_config)
    sim = SimulationModel()
    # parameters similar to UI: species_config, populations, food_places, food_amount, start_temp, start_is_day, region_key
    try:
        sim.setup(species_config, populations, 5, 50, 20, True, "Wasteland")
    except Exception as e:
        print("Warning: sim.setup failed, trying minimal init:", e)
        try:
            sim.setup({}, {"Default": 10}, 5, 50, 20, True, "Wasteland")
        except Exception:
            pass

    # warm-up
    for _ in range(10):
        sim.step()

    def loop():
        for i in range(steps):
            sim.step()

    pr = cProfile.Profile()
    pr.enable()
    loop()
    pr.disable()

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).strip_dirs().sort_stats("cumtime")
    ps.print_stats(30)
    print(s.getvalue())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=2000)
    args = parser.parse_args()
    print(f"Profiling SimulationModel.step() for {args.steps} steps...")
    run_steps(args.steps)
