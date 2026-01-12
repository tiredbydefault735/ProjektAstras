import sys
from pathlib import Path

# ensure project root is on sys.path so `backend` package imports resolve
root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(root))

from backend.simulation import SimulationModel
import time

# minimal species config
cfg = {
    "Icefang": {"max_clan_members": 12, "hp": 25, "food_intake": 5},
    "Crushed_Critters": {"max_clan_members": 10, "hp": 25, "food_intake": 5},
    "Spores": {"max_clan_members": 8, "hp": 20, "food_intake": 4},
    "The_Corrupted": {"max_clan_members": 10, "hp": 30, "food_intake": 6},
}

sim = SimulationModel()
sim.setup(cfg, {k: 20 for k in cfg.keys()}, food_places=12, food_amount=100)

steps = 120
print(f"Running {steps} steps (headless)...")
for i in range(steps):
    res = sim.step()
    last = getattr(sim, "_last_step_ms", None)
    build = getattr(sim, "_last_build_ms", None)
    disaster = getattr(sim, "_last_disaster_ms", None)
    count = getattr(sim, "_last_count_ms", None)
    print(
        f"step {i+1:03d}: total_ms={last:.3f} build_ms={build:.3f} disaster_ms={disaster if disaster is not None else 0:.3f} count_ms={count if count is not None else 0:.3f}"
    )
    # small sleep to avoid burning CPU in this measurement loop
    time.sleep(0.01)

if hasattr(sim, "_step_history"):
    hist = sim._step_history
    print("\nSummary:")
    print(f"avg_step_ms = {sum(hist)/len(hist):.3f}")
    print(f"max_step_ms = {max(hist):.3f}")
    print(f"last_draw_ms (if any) = {getattr(sim, 'map_widget_draw_ms', None)}")
else:
    print("No timing history available")
