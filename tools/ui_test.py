"""Drives the real screens off-screen through a full journey and saves screenshots."""
import os
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame

from exodus import ui

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
ui.score_file = lambda: OUT / "scores.json"
app = ui.App(headless=True)


def shot(name):
    app.step(0.01)
    pygame.image.save(app.canvas, str(OUT / f"{name}.png"))


def press(key):
    app.step(0.01, [pygame.event.Event(pygame.KEYDOWN, key=key, unicode="", mod=0)])


shot("1_title")
press(pygame.K_1)
shot("2_tribe")
press(pygame.K_1)
press(pygame.K_1)
store = app.screen
for item, qty in (("oxen", 8), ("food", 400), ("water", 60), ("cloaks", 10), ("stones", 40), ("parts", 4)):
    assert app.game.buy(item, qty)
shot("3_store")
store.leave()
shot("4_travel")
seen = set()
for _ in range(60000):
    s = app.screen
    if isinstance(s, ui.Travel):
        app.step(ui.DAY_SECONDS + .01)
    elif isinstance(s, ui.Camp):
        if "camp" not in seen:
            seen.add("camp")
            shot("5_camp")
        if app.game.sickness > 80:
            s.rest()
        else:
            s.options[0][1]()
    elif isinstance(s, ui.Menu):
        if s.title.startswith("Crossing") and "river" not in seen:
            seen.add("river")
            shot("6_crossing")
        if s.title == "The People Grumble" and "anger" not in seen:
            seen.add("anger")
            shot("7_anger")
        if s.title in ("The Promised Land", "The March Has Failed"):
            shot("8_end")
            print("ended:", s.title, app.game.date, "score", app.game.score())
            break
        s.options[0][1]()
    else:
        raise SystemExit(f"unexpected screen {s}")
else:
    raise SystemExit("journey never ended")

app.game = ui.Game("Judah", 1)
app.game.stones = 20
hunt = ui.Hunt(app)
app.go(hunt)
for _ in range(40):
    app.step(.05)
shot("9_hunt")
hunt.finish()
print("ui journey ok", sorted(seen))
