"""
Run batch simulations and report winner frequencies per region.
"""

import sys
import json
import time
import random
from pathlib import Path

# ensure repo root on path
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from utils import get_static_path
from backend.model import SimulationModel


def load_species_config():
    try:
        p = get_static_path("data/species.json")
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def build_populations(species_config, default_count=10):
    if not species_config:
        return {"Default": default_count}
    pops = {}
    for k in list(species_config.keys())[:4]:
        pops[k] = default_count
    if not pops:
        pops = {list(species_config.keys())[0]: default_count}
    return pops


def run_batch(runs_per_region=40, max_steps=3000, regions=None):
    if regions is None:
        regions = ["Default", "Evergreen_Forest", "Desert", "Tundra"]

    species_config = load_species_config()
    populations = build_populations(species_config)

    results = {}

    for region in regions:
        counts = {}
        print(f"\n=== Region: {region} (runs={runs_per_region}) ===")
        for r in range(runs_per_region):
            # use varying seed for each run for randomness
            seed = int(time.time() * 1000) ^ (r * 7919)
            random.seed(seed)

            sim = SimulationModel()
            try:
                sim.setup(
                    species_config,
                    populations,
                    5,
                    50,
                    20,
                    True,
                    region,
                    None,
                    rng_seed=seed,
                )
            except Exception as e:
                # fallback minimal
                sim.setup(
                    {},
                    {list(populations.keys())[0]: 10},
                    5,
                    50,
                    20,
                    True,
                    region,
                    None,
                    rng_seed=seed,
                )

            # run until one species remains or max_steps
            last_counts = {}
            for step in range(max_steps):
                out = sim.step()
                # count total per species
                cur = {}
                for g in sim.groups:
                    cur[g.name] = cur.get(g.name, 0) + sum(
                        c.population for c in g.clans
                    )
                for l in sim.loners:
                    cur[l.species] = cur.get(l.species, 0) + 1

                alive = [s for s, v in cur.items() if v > 0]
                last_counts = cur
                if len(alive) <= 1:
                    break

            if last_counts:
                maxv = max(last_counts.values())
                winners = [s for s, v in last_counts.items() if v == maxv]
                if len(winners) == 1:
                    win = winners[0]
                else:
                    win = "tie"
            else:
                win = "none"

            counts[win] = counts.get(win, 0) + 1
            if (r + 1) % max(1, runs_per_region // 8) == 0:
                print(
                    f"  run {r+1}/{runs_per_region}... current partial counts: {counts}"
                )

        results[region] = counts

    # print summary
    summary = {"runs_per_region": runs_per_region, "results": results}
    print("\n=== Summary ===")
    for region, cnts in results.items():
        total = sum(cnts.values())
        print(f"Region: {region} — total runs: {total}")
        for k, v in sorted(cnts.items(), key=lambda x: -x[1]):
            print(f"  {k}: {v} ({v/total:.2%})")

    out_path = Path(root) / "build" / "batch_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Results saved to: {out_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=40)
    parser.add_argument("--steps", type=int, default=3000)
    parser.add_argument("--regions", nargs="*", default=None)
    args = parser.parse_args()
    run_batch(args.runs, args.steps, args.regions)
