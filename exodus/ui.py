"""All screens. The logical canvas is 640x400 and scales to the window."""
import json
import os
import random
import sys
from pathlib import Path

import pygame

from . import data as D
from .sim import Game

W, H = 640, 400
INK = (244, 232, 196)
DIM = (204, 164, 104)
GOLD = (232, 188, 60)
PANEL = (32, 20, 28)
EDGE = (148, 96, 48)
RED = (224, 88, 64)
DAY_SECONDS = 0.4
WALK_EXTRA_SECONDS = 3.0  # added to every walking stretch between decisions
SAVE_SLOTS = 3


def asset_root():
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets"
    return Path(__file__).resolve().parent.parent / "assets"


def slug(name):
    return name.lower().replace("the ", "").replace(" ", "_").replace("-", "_")


def score_file():
    return Path(os.path.expanduser("~")) / ".the_exodus" / "scores.json"


def load_scores():
    try:
        return json.loads(score_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def save_score(tribe, score):
    scores = sorted(load_scores() + [{"tribe": tribe, "score": score}],
                    key=lambda s: -s["score"])[:8]
    try:
        score_file().parent.mkdir(parents=True, exist_ok=True)
        score_file().write_text(json.dumps(scores), encoding="utf-8")
    except OSError:
        pass
    return scores


def save_path(slot):
    return score_file().parent / f"save{slot}.json"


def write_save(game, slot):
    """Writes through a temporary file so a failed save never harms an old one."""
    path = save_path(slot)
    temp = path.with_suffix(".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp.write_text(json.dumps(game.to_dict()), encoding="utf-8")
        os.replace(temp, path)
        return True
    except OSError:
        return False


def read_save(slot):
    try:
        return Game.from_dict(json.loads(save_path(slot).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return None


def slot_label(slot):
    if not save_path(slot).exists():
        return f"Slot {slot}: empty"
    g = read_save(slot)
    return f"Slot {slot}: {g.tribe}, {g.place}, {g.date}" if g else f"Slot {slot}: damaged"


def load_menu(app):
    def back():
        app.go(TitleScreen(app))

    def pick(slot):
        def run():
            game = read_save(slot)
            if game is None:
                why = "That slot is empty." if not save_path(slot).exists() else "That save file is damaged."
                app.go(Menu(app, "Cannot Load", why, [("Back", lambda: app.go(load_menu(app)))], "rameses"))
                return
            app.game = game
            app.go(Camp(app))
        return run

    opts = [(slot_label(s), pick(s)) for s in range(1, SAVE_SLOTS + 1)] + [("Back", back)]
    return Menu(app, "Load a Saved Game", "Choose a journey to continue.", opts, "rameses")


def save_menu(app):
    g = app.game
    scene = slug(g.place)

    def to_camp():
        app.go(Camp(app))

    def store(slot):
        if write_save(g, slot):
            app.go(Menu(app, "Game Saved", slot_label(slot),
                        [("Back to camp", to_camp), ("Quit to title", lambda: app.go(TitleScreen(app)))], scene))
        else:
            app.go(Menu(app, "Could Not Save", "The save file could not be written.",
                        [("Back to camp", to_camp)], scene))

    def pick(slot):
        def run():
            if save_path(slot).exists():
                app.go(Menu(app, "Overwrite This Save?", slot_label(slot),
                            [("Yes, overwrite it", lambda: store(slot)),
                             ("No, go back", lambda: app.go(save_menu(app)))], scene))
            else:
                store(slot)
        return run

    opts = [(slot_label(s), pick(s)) for s in range(1, SAVE_SLOTS + 1)] + [("Back to camp", to_camp)]
    return Menu(app, "Save Game", "Choose a slot.", opts, scene)


class App:
    def __init__(self, headless=False):
        pygame.init()
        flags = pygame.RESIZABLE if not headless else 0
        pygame.display.set_caption("The Exodus")
        self.window = pygame.display.set_mode((W * 2, H * 2), flags)
        self.canvas = pygame.Surface((W, H))
        self.font = pygame.font.Font(None, 22)
        self.big = pygame.font.Font(None, 44)
        self.clock = pygame.time.Clock()
        self.images = {}
        self.game = None
        self.screen = None
        self.running = True
        self.go(TitleScreen(self))

    def go(self, screen):
        self.screen = screen

    def scene(self, name):
        return self.image("scenes", name, 2)

    def image(self, folder, name, scale=1):
        key = (folder, name, scale)
        if key not in self.images:
            img = pygame.image.load(str(asset_root() / folder / f"{name}.png")).convert_alpha()
            self.images[key] = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
        return self.images[key]

    def frame(self, name, index, count, scale=2):
        sheet = self.image("sprites", name, scale)
        w = sheet.get_width() // count
        return sheet.subsurface((index % count * w, 0, w, sheet.get_height()))

    def text(self, s, x, y, color=INK, font=None, center=False):
        img = (font or self.font).render(s, False, color)
        self.canvas.blit(img, (x - img.get_width() // 2 if center else x, y))

    def wrapped(self, s, x, y, width, color=INK):
        line = ""
        for word in s.split():
            test = (line + " " + word).strip()
            if self.font.size(test)[0] > width:
                self.text(line, x, y, color)
                y += 19
                line = word
            else:
                line = test
        if line:
            self.text(line, x, y, color)
            y += 19
        return y

    def to_canvas(self, pos):
        r = self.view_rect()
        return (pos[0] - r.x) * W // max(1, r.w), (pos[1] - r.y) * H // max(1, r.h)

    def view_rect(self):
        ww, wh = self.window.get_size()
        scale = max(1, min(ww // W, wh // H))
        return pygame.Rect((ww - W * scale) // 2, (wh - H * scale) // 2, W * scale, H * scale)

    def present(self):
        r = self.view_rect()
        self.window.fill((0, 0, 0))
        self.window.blit(pygame.transform.scale(self.canvas, r.size), r.topleft)
        pygame.display.flip()

    def step(self, dt, events=()):
        for e in events:
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.VIDEORESIZE:
                self.window = pygame.display.set_mode(e.size, pygame.RESIZABLE)
            else:
                self.screen.handle(e)
        self.screen.update(dt)
        self.canvas.fill(PANEL)
        self.screen.draw()
        self.present()

    def run(self):
        while self.running:
            dt = self.clock.tick(30) / 1000
            self.step(dt, pygame.event.get())
        pygame.quit()


class Screen:
    def __init__(self, app):
        self.app = app

    @property
    def g(self):
        return self.app.game

    def handle(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self):
        pass


class Menu(Screen):
    """Scene on top, text and numbered choices below."""

    def __init__(self, app, title, body, options, scene=None, ref=""):
        super().__init__(app)
        self.title, self.body, self.options, self.scene, self.ref = title, body, options, scene, ref
        self.sel = 0
        self.rows = []

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(self.options)
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(self.options)
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.options[self.sel][1]()
            elif pygame.K_1 <= e.key <= pygame.K_9 and e.key - pygame.K_1 < len(self.options):
                self.options[e.key - pygame.K_1][1]()
            elif e.key == pygame.K_0 and len(self.options) >= 10:
                self.options[9][1]()
        elif e.type == pygame.MOUSEMOTION:
            hit = self.hit(e.pos)
            if hit is not None:
                self.sel = hit
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            hit = self.hit(e.pos)
            if hit is not None:
                self.options[hit][1]()

    def hit(self, pos):
        p = self.app.to_canvas(pos)
        for i, rect in enumerate(self.rows):
            if rect.collidepoint(p):
                return i
        return None

    def draw(self):
        a = self.app
        top = 8
        if self.scene:
            a.canvas.blit(a.scene(self.scene), (0, 0), (0, 50, W, 150))
            top = 156
        a.text(self.title, 16, top, GOLD)
        if self.ref:
            a.text(self.ref, W - 16 - a.font.size(self.ref)[0], top, DIM)
        y = a.wrapped(self.body, 16, top + 21, W - 32) + 4 if self.body else top + 24
        self.rows = []
        two = len(self.options) > 5
        for i, (label, _) in enumerate(self.options):
            col = i // 6 if two else 0
            x = 16 + col * 304
            ry = y + (i % 6 if two else i) * 20
            rect = pygame.Rect(x - 4, ry - 2, 296 if two else W - 24, 19)
            self.rows.append(rect)
            if i == self.sel:
                pygame.draw.rect(a.canvas, (84, 52, 28), rect)
            key = str((i + 1) % 10) if i < 10 else "F5"
            a.text(f"{key}. {label}", x, ry, INK if i == self.sel else DIM)


class TitleScreen(Menu):
    def __init__(self, app):
        super().__init__(app, "Lead Israel out of Egypt", "A journey from Rameses to the edge of the Promised Land.",
                         [("Begin the journey", self.start), ("Load saved game", lambda: app.go(load_menu(app))),
                          ("High scores", self.scores), ("Quit", self.quit)],
                         "rameses")

    def start(self):
        self.app.go(tribe_menu(self.app))

    def scores(self):
        rows = load_scores()
        body = "   ".join(f"{s['tribe']} {s['score']}" for s in rows) or "No journeys finished yet."
        self.app.go(Menu(self.app, "High Scores", body, [("Back", lambda: self.app.go(TitleScreen(self.app)))], "rameses"))

    def quit(self):
        self.app.running = False

    def draw(self):
        super().draw()
        self.app.text("THE EXODUS", W // 2 + 2, 18, (16, 12, 20), self.app.big, True)
        self.app.text("THE EXODUS", W // 2, 16, GOLD, self.app.big, True)


def tribe_menu(app):
    def pick(tribe):
        def choose():
            app.game = Game(tribe)
            app.go(Menu(app, "The Night of the Passover",
                        "You travel with Moses, Aaron, and the elders. Buy what the people need "
                        "with the silver the Egyptians gave you.",
                        [("Go to the market", lambda: app.go(Store(app, leaving=True)))],
                        "rameses", "Exodus 12:35-36"))
        return choose
    opts = [(f"{t}: {v['silver']} silver, score x{v['score']}", pick(t)) for t, v in D.TRIBES.items()]
    return Menu(app, "Choose your tribe", "Less silver makes a harder journey and a higher score.", opts, "rameses")


class Store(Screen):
    ITEMS = ["oxen", "food", "water", "cloaks", "stones", "parts"]
    STEP = {"oxen": 1, "food": 25, "water": 10, "cloaks": 1, "stones": 10, "parts": 1}

    def __init__(self, app, leaving=False):
        super().__init__(app)
        self.leaving, self.sel, self.msg = leaving, 0, ""
        self.mult = 1.0 if leaving else self.g.price_mult()
        self.buttons = []

    def unit(self, item):
        return round(D.PRICES[item] * self.mult, 1)

    def leave(self):
        if self.g.oxen < 1:
            self.msg = "You need at least one ox to pull the carts."
            return
        self.app.go(Travel(self.app) if self.leaving else Camp(self.app))

    def adjust(self, item, sign):
        qty = self.STEP[item]
        if sign > 0:
            self.msg = "" if self.g.buy(item, qty, self.mult) else "Not enough silver."
        elif getattr(self.g, item) >= qty:
            setattr(self.g, item, getattr(self.g, item) - qty)
            self.g.silver += round(D.PRICES[item] * qty * self.mult)

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_UP:
                self.sel = (self.sel - 1) % (len(self.ITEMS) + 1)
            elif e.key == pygame.K_DOWN:
                self.sel = (self.sel + 1) % (len(self.ITEMS) + 1)
            elif self.sel < len(self.ITEMS) and e.key == pygame.K_RIGHT:
                self.adjust(self.ITEMS[self.sel], 1)
            elif self.sel < len(self.ITEMS) and e.key == pygame.K_LEFT:
                self.adjust(self.ITEMS[self.sel], -1)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE) and self.sel == len(self.ITEMS):
                self.leave()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            p = self.app.to_canvas(e.pos)
            for rect, action in self.buttons:
                if rect.collidepoint(p):
                    action()

    def draw(self):
        a, g = self.app, self.g
        a.text("Market" if self.leaving else f"Caravan at {g.place}", 16, 12, GOLD, a.big)
        a.text(f"Silver: {g.silver}", W - 150, 22, INK)
        a.text("Up/Down to choose, Left/Right or click - and + to change", 16, 48, DIM)
        self.buttons = []
        y = 78
        for i, item in enumerate(self.ITEMS):
            if i == self.sel:
                pygame.draw.rect(a.canvas, (84, 52, 28), (10, y - 3, W - 20, 25))
            a.text(D.ITEM_NAMES[item], 20, y)
            a.text(f"{self.unit(item)} each", 220, y, DIM)
            a.text(str(getattr(g, item)), 360, y)
            for label, x, sign in (("-", 450, -1), ("+", 500, 1)):
                rect = pygame.Rect(x, y - 2, 34, 21)
                pygame.draw.rect(a.canvas, EDGE, rect, 1)
                a.text(label, rect.centerx, y, INK, center=True)
                self.buttons.append((rect, (lambda it=item, s=sign: self.adjust(it, s))))
            y += 32
        rect = pygame.Rect(16, y + 10, 200, 26)
        pygame.draw.rect(a.canvas, (84, 52, 28) if self.sel == len(self.ITEMS) else PANEL, rect)
        pygame.draw.rect(a.canvas, EDGE, rect, 1)
        a.text("Leave the market", rect.centerx, rect.y + 6, INK, center=True)
        self.buttons.append((rect, self.leave))
        if self.msg:
            a.text(self.msg, 240, y + 16, RED)


def status_lines(g):
    return [f"Date: {g.date}", f"Health: {g.health}", f"People: {g.mood}",
            f"Pace: {g.pace}", f"Rations: {g.rations}",
            f"Food: {g.food}   Water: {g.water}", f"Next stop: {g.to_next} mi"]


class Travel(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.timer, self.anim, self.x = 0, 0, 120
        self.hold = WALK_EXTRA_SECONDS

    def handle(self, e):
        if (e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN)) or \
                (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1):
            self.app.go(Camp(self.app))

    def update(self, dt):
        self.anim += dt * 5
        if self.hold > 0:  # keep walking on screen before the next day can bring an event
            self.hold -= dt
            return
        self.timer += dt
        if self.timer >= DAY_SECONDS:
            self.timer = 0
            show_events(self.app, self.g.travel_day(), self)

    def draw(self):
        a, g = self.app, self.g
        next_stop = D.ROUTE[min(g.stop + 1, len(D.ROUTE) - 1)][0]
        a.canvas.blit(a.scene(slug(g.place)), (0, 0), (0, 40, W, 180))
        a.canvas.blit(a.frame("cart", int(self.anim), 2, 3), (250, 124))
        for i, name in enumerate(g.alive):
            a.canvas.blit(a.frame(name.lower(), 0, 1, 2), (360 + i * 32, 130))
        y = 190
        for i, line in enumerate(status_lines(g)):
            a.text(line, 16 + (i % 2) * 310, y + (i // 2) * 21)
        a.text(f"Traveling to {next_stop}. Press Space to stop.", 16, 370, GOLD)


def show_events(app, events, back):
    """Shows events one at a time, then returns to `back` or the right next screen."""
    g = app.game

    def after():
        if g.pending_river:
            app.go(river_menu(app))
        elif g.won or g.over:
            app.go(end_screen(app))
        elif arrived:
            app.go(Camp(app))
        else:
            if isinstance(back, Travel):
                back.hold = WALK_EXTRA_SECONDS
            app.go(back)

    arrived = any(ev.kind == "landmark" for ev in events)

    def show(i):
        if i >= len(events):
            after()
            return
        ev = events[i]
        scene = slug(ev.title) if ev.kind in ("landmark", "win") else slug(g.place)
        if ev.choices:
            def pick(idx):
                def run():
                    g.choose(ev, idx)
                    show(i + 1)
                return run
            opts = [(label, pick(n)) for n, (label, _) in enumerate(ev.choices)]
        else:
            opts = [("Continue", lambda: show(i + 1))]
        app.go(Menu(app, ev.title, ev.text, opts, scene, ev.ref))

    if events:
        show(0)
    elif g.pending_river or g.over:
        after()


def river_menu(app):
    g = app.game
    kind = g.pending_river

    def cross(method):
        def run():
            ev = g.cross_water(method)
            if g.sickness >= D.SICKNESS_DEAD:
                g.over = True
            app.go(Menu(app, ev.title, ev.text, [("Continue", lambda: app.go(end_screen(app) if g.over else Camp(app)))],
                        slug(g.place), ev.ref))
        return run

    opts = [("Moses stretches out his staff (always parts the water)", cross("split"))]
    body = "The water lies before Israel."
    if kind == "river":
        opts.append(("Ford it on foot (risky)", cross("ford")))
    return Menu(app, f"Crossing at {g.place}", body, opts, slug(g.place))


class Camp(Menu):
    def __init__(self, app):
        g = app.game
        options = [("Continue on the journey", lambda: app.go(Travel(app))),
                   ("Check supplies", self.supplies), ("Look at the route", self.route),
                   ("Change pace", self.pace), ("Change rations", self.rations),
                   ("Rest for 3 days", self.rest), ("Trade with a caravan", self.trade),
                   ("Talk to the people", self.talk), ("Buy from a caravan", lambda: app.go(Store(app))),
                   ("Hunt quail with slings", self.hunt), ("Save game", lambda: app.go(save_menu(app)))]
        super().__init__(app, f"{g.place}  -  {g.date}",
                         f"Health: {g.health}.  The people are {g.mood.lower()}.  Next stop in {g.to_next} miles.",
                         options, slug(g.place))

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_F5:
            self.app.go(save_menu(self.app))
        else:
            super().handle(e)

    def back(self):
        self.app.go(Camp(self.app))

    def info(self, title, body):
        self.app.go(Menu(self.app, title, body, [("Back", self.back)], slug(self.g.place)))

    def supplies(self):
        g = self.g
        self.info("Supplies", f"Silver {g.silver}.  Oxen {g.oxen}.  Food {g.food}.  Water {g.water}.  "
                              f"Cloaks {g.cloaks}.  Sling stones {g.stones}.  Cart parts {g.parts}.  "
                              f"Men of Israel: {g.people:,}.  Leaders: {', '.join(g.alive)}.")

    def route(self):
        names = [("> " if i == self.g.stop else "") + r[0] for i, r in enumerate(D.ROUTE)]
        self.info("The Route", ",  ".join(names))

    def pace(self):
        def set_pace(p):
            def run():
                self.g.pace = p
                self.back()
            return run
        self.app.go(Menu(self.app, "Pace", f"Current: {self.g.pace}. Faster travel wears the people down.",
                         [(p, set_pace(p)) for p in D.PACES], slug(self.g.place)))

    def rations(self):
        def set_r(r):
            def run():
                self.g.rations = r
                self.back()
            return run
        self.app.go(Menu(self.app, "Rations", f"Current: {self.g.rations}. Smaller rations harm health.",
                         [(r, set_r(r)) for r in D.RATIONS], slug(self.g.place)))

    def rest(self):
        events = self.g.rest(3)
        if self.g.over:
            show_events(self.app, events, self)
        else:
            self.info("Rest", f"The camp rests three days. Health is now {self.g.health.lower()}.")

    def trade(self):
        offer = self.g.trade_offer()
        give, gq, get, gt = offer

        def accept():
            done = self.g.accept_trade(offer)
            self.info("Trade", "The trade is made." if done else f"You do not have {gq} {D.ITEM_NAMES[give]}.")
        self.app.go(Menu(self.app, "A Caravan Offers a Trade",
                         f"They want {gq} {D.ITEM_NAMES[give]} and offer {gt} {D.ITEM_NAMES[get]}.",
                         [("Accept", accept), ("Decline", self.back)], slug(self.g.place)))

    def talk(self):
        tips = ["Keep water for the dry stretches between springs.",
                "When the people grumble, Moses should take it to the LORD.",
                "Manna falls six days. Rest on the Sabbath.",
                "Spare cart parts save days when a wheel breaks.",
                "Cloaks matter on cold desert nights."]
        self.info("The People Say", random.choice(tips))

    def hunt(self):
        if self.g.stones <= 0:
            self.info("Hunt", "You have no sling stones.")
        else:
            self.app.go(Hunt(self.app))


class Hunt(Screen):
    LENGTH = 25

    def __init__(self, app):
        super().__init__(app)
        self.t, self.hits, self.birds, self.spawn, self.aim = 0, 0, [], 0, (W // 2, 200)
        pygame.mouse.set_visible(False)

    def handle(self, e):
        if e.type == pygame.MOUSEMOTION:
            self.aim = self.app.to_canvas(e.pos)
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.finish()
        elif (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or \
                (e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE):
            self.fire()

    def fire(self):
        if self.g.stones <= 0:
            self.finish()
            return
        self.g.stones -= 1
        for b in self.birds:
            if abs(b[0] + 12 - self.aim[0]) < 18 and abs(b[1] + 7 - self.aim[1]) < 15:
                self.birds.remove(b)
                self.hits += 1
                break

    def update(self, dt):
        self.t += dt
        self.spawn -= dt
        if self.spawn <= 0:
            self.spawn = random.uniform(.35, .9)
            left = random.random() < .5
            self.birds.append([-24 if left else W, random.randint(16, 230), random.uniform(90, 190) * (1 if left else -1)])
        for b in self.birds:
            b[0] += b[2] * dt
        self.birds = [b for b in self.birds if -30 < b[0] < W + 30]
        if self.t >= self.LENGTH:
            self.finish()

    def finish(self):
        pygame.mouse.set_visible(True)
        gained = self.g.hunt_reward(self.hits)
        app = self.app
        next_screen = lambda: app.go(end_screen(app) if app.game.over else Camp(app))
        app.go(Menu(app, "Quail Hunt", f"You brought down {self.hits} quail, worth {gained} omers of food.",
                    [("Continue", next_screen)], slug(self.g.place)))

    def draw(self):
        a = self.app
        a.canvas.blit(a.scene(slug(self.g.place)), (0, 0), (0, 0, W, 272))
        frame = int(self.t * 8)
        for b in self.birds:
            img = a.frame("quail", frame, 2, 2)
            a.canvas.blit(pygame.transform.flip(img, b[2] < 0, False), (b[0], b[1]))
        aim = a.frame("aim", 0, 1, 2)
        a.canvas.blit(aim, (self.aim[0] - 9, self.aim[1] - 9))
        a.text(f"Time {max(0, int(self.LENGTH - self.t))}   Stones {self.g.stones}   Quail {self.hits}", 16, 300)
        a.text("Move the mouse and click to sling. Esc ends the hunt.", 16, 326, DIM)


def end_screen(app):
    g = app.game
    again = [("Return to title", lambda: app.go(TitleScreen(app)))]
    if g.won:
        score = g.score()
        best = save_score(g.tribe, score)[0]["score"]
        return Menu(app, "The Promised Land",
                    f"Israel stands at the Jordan. Joshua leads the people over.  Score: {score}.  Best: {best}.",
                    again, "mount_nebo", "Joshua 3:17")
    return Menu(app, "The March Has Failed", "The people could go no farther. Begin again and lead them to the end.",
                again, slug(g.place))
