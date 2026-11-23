"""Checks saving, loading, damaged files, and the longer walking scenes, off-screen."""
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame

from exodus import ui
from exodus.sim import Game


def advance(g, days):
    for _ in range(days):
        if g.over:
            break
        for ev in g.travel_day():
            if ev.choices:
                g.choose(ev, 0)
        if g.pending_river:
            g.cross_water("split")


def new_game(seed):
    g = Game("Judah", seed)
    for item, qty in (("oxen", 8), ("food", 400), ("water", 60), ("cloaks", 10), ("stones", 40), ("parts", 4)):
        assert g.buy(item, qty)
    return g


# A loaded game must continue exactly as the original would have.
for seed in range(100):
    a = new_game(seed)
    advance(a, 10 + seed % 40)
    if a.over:
        continue
    b = Game.from_dict(json.loads(json.dumps(a.to_dict())))
    assert a.to_dict() == b.to_dict()
    advance(a, 400)
    advance(b, 400)
    assert a.to_dict() == b.to_dict(), seed
    assert a.won == b.won and a.over == b.over

with tempfile.TemporaryDirectory() as tmp:
    ui.score_file = lambda: Path(tmp) / "scores.json"
    app = ui.App(headless=True)

    def key(k):
        app.step(0.01, [pygame.event.Event(pygame.KEYDOWN, key=k, unicode="", mod=0)])

    # Save from camp with F5, then load it from the title screen.
    app.game = new_game(7)
    advance(app.game, 12)
    saved = app.game.to_dict()
    app.go(ui.Camp(app))
    key(pygame.K_F5)
    key(pygame.K_1)
    assert app.screen.title == "Game Saved"
    key(pygame.K_2)
    assert isinstance(app.screen, ui.TitleScreen)
    app.game = None
    key(pygame.K_2)
    key(pygame.K_1)
    assert isinstance(app.screen, ui.Camp) and app.game.to_dict() == saved

    # An occupied slot asks first, and "no" leaves it unchanged.
    app.game.food += 1
    key(pygame.K_F5)
    key(pygame.K_1)
    assert app.screen.title == "Overwrite This Save?"
    key(pygame.K_2)
    assert ui.read_save(1).to_dict() == saved

    # Damaged files are reported and never crash the game.
    for bad in ("not json", "[]", "{}", json.dumps({**saved, "stop": 999}), json.dumps({**saved, "rng": [1]})):
        ui.save_path(2).write_text(bad, encoding="utf-8")
        assert ui.read_save(2) is None, bad
        assert ui.slot_label(2) == "Slot 2: damaged"
    app.go(ui.load_menu(app))
    key(pygame.K_2)
    assert app.screen.title == "Cannot Load"

    # Walking lasts three seconds longer, on entry and after a roadside event.
    app.game = new_game(3)
    travel = ui.Travel(app)
    app.go(travel)
    start = app.game.days_elapsed
    for _ in range(int(ui.WALK_EXTRA_SECONDS / .05) - 1):
        travel.update(.05)
    assert app.game.days_elapsed == start, "a day passed during the extra walk"
    for _ in range(int((ui.DAY_SECONDS + .2) / .05)):
        travel.update(.05)
    assert app.game.days_elapsed > start, "walking never resumed"
    travel.hold = 0
    ui.show_events(app, [ui.Game.travel_day.__globals__["Event"]("On the Way", "Test")], travel)
    app.screen.options[0][1]()
    assert app.screen is travel and travel.hold == ui.WALK_EXTRA_SECONDS
    pygame.quit()

print("save and walking tests ok")
