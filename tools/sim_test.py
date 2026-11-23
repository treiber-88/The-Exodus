"""Plays many full journeys with a simple bot and checks story invariants."""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from exodus import data as D
from exodus.sim import Game


def play(seed, tribe):
    g = Game(tribe, seed)
    budget = {"Judah": (8, 400, 10, 40, 4, 60), "Levi": (6, 250, 6, 20, 2, 40), "Dan": (4, 150, 5, 20, 2, 50)}[tribe]
    for item, qty in zip(("oxen", "food", "cloaks", "stones", "parts", "water"), budget):
        assert g.buy(item, qty), (tribe, item)
    seen = [g.place]
    for _ in range(5000):
        if g.over:
            break
        if g.sickness > 80:
            g.rest(3)
        for ev in g.travel_day():
            if ev.choices:
                g.choose(ev, 0)
            if ev.kind in ("landmark", "win"):
                seen.append(ev.title)
        if g.pending_river:
            g.cross_water("split")
            assert g.pending_river is None
    assert g.over, "journey never ended"
    if g.won:
        assert seen == [r[0] for r in D.ROUTE], seen
        assert "Moses" not in g.alive and "Aaron" not in g.alive
        assert "Joshua" in g.alive and "Caleb" in g.alive
        assert g.year == 40
    return g


def reckless(seed):
    """Fastest pace, least food, almost no supplies, ignores every complaint."""
    g = Game("Dan", seed)
    for item, qty in (("oxen", 4), ("food", 40), ("water", 15)):
        assert g.buy(item, qty)
    g.pace, g.rations = "Grueling", "Bare bones"
    for _ in range(5000):
        if g.over:
            break
        for ev in g.travel_day():
            if ev.choices:
                g.choose(ev, 3)
        if g.pending_river:
            g.cross_water("ford")
    return g


results = Counter()
for tribe in D.TRIBES:
    for seed in range(300):
        g = play(seed, tribe)
        results[tribe, "won" if g.won else "lost"] += 1
for key in sorted(results):
    print(key, results[key])
print("reckless wins:", sum(reckless(s).won for s in range(300)), "of 300")
