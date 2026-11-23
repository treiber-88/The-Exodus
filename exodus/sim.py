"""Game rules with no graphics, so whole journeys can be simulated in tests."""
import random
from dataclasses import dataclass, field

from . import data as D


@dataclass
class Event:
    title: str
    text: str
    ref: str = ""
    choices: list = field(default_factory=list)
    kind: str = "notice"


class Game:
    def __init__(self, tribe="Judah", seed=None):
        self.rng = random.Random(seed)
        self.tribe = tribe
        self.silver = D.TRIBES[tribe]["silver"]
        self.oxen = self.food = self.cloaks = self.stones = self.parts = self.water = 0
        self.year, self.month, self.day = 1, 1, 15
        self.stop = 0
        self.to_next = D.ROUTE[1][1]
        self.miles = 0
        self.pace = "Steady"
        self.rations = "Filling"
        self.sickness = 0.0
        self.anger = 0.0
        self.people = D.START_PEOPLE
        self.alive = list(D.LEADERS)
        self.manna = False
        self.days_elapsed = 0
        self.over = False
        self.won = False
        self.pending_river = None

    # ---------- saving ----------
    SAVE_VERSION = 1
    INT_FIELDS = ("silver", "oxen", "food", "cloaks", "stones", "parts", "water", "year",
                  "month", "day", "stop", "to_next", "miles", "people", "days_elapsed")
    NUM_FIELDS = ("sickness", "anger")

    def to_dict(self):
        fields = {k: getattr(self, k) for k in self.INT_FIELDS + self.NUM_FIELDS}
        version, state, gauss = self.rng.getstate()
        return {"version": self.SAVE_VERSION, "tribe": self.tribe, "pace": self.pace,
                "rations": self.rations, "alive": list(self.alive), "manna": self.manna,
                "rng": [version, list(state), gauss], **fields}

    @classmethod
    def from_dict(cls, d):
        """Rebuilds a game, raising ValueError if the save is damaged."""
        try:
            if d["version"] != cls.SAVE_VERSION or d["tribe"] not in D.TRIBES:
                raise ValueError("unsupported save")
            if d["pace"] not in D.PACES or d["rations"] not in D.RATIONS:
                raise ValueError("bad settings")
            for k in cls.INT_FIELDS:
                if type(d[k]) is not int or d[k] < 0:
                    raise ValueError(k)
            for k in cls.NUM_FIELDS:
                if type(d[k]) not in (int, float) or not 0 <= d[k] < float("inf"):
                    raise ValueError(k)
            if not 0 <= d["stop"] < len(D.ROUTE) - 1 or not 1 <= d["month"] <= 12 \
                    or not 1 <= d["day"] <= D.DAYS_IN_MONTH or d["year"] < 1:
                raise ValueError("bad position")
            if type(d["manna"]) is not bool or not set(d["alive"]) <= set(D.LEADERS):
                raise ValueError("bad party")
            g = cls(d["tribe"])
            version, state, gauss = d["rng"]
            g.rng.setstate((version, tuple(state), gauss))
        except (KeyError, TypeError, IndexError) as exc:
            raise ValueError("damaged save") from exc
        for k in cls.INT_FIELDS + cls.NUM_FIELDS + ("pace", "rations", "manna"):
            setattr(g, k, d[k])
        g.alive = [name for name in D.LEADERS if name in d["alive"]]
        return g

    # ---------- shop ----------
    def buy(self, item, qty, price_mult=1.0):
        cost = round(D.PRICES[item] * qty * price_mult)
        if qty <= 0 or cost > self.silver:
            return False
        self.silver -= cost
        setattr(self, item, getattr(self, item) + qty)
        return True

    def price_mult(self):
        return 1.0 + self.stop * 0.05

    # ---------- status ----------
    @property
    def date(self):
        return f"{self.day} {D.MONTHS[self.month - 1]}, Year {self.year}"

    @property
    def place(self):
        return D.ROUTE[self.stop][0]

    @property
    def health(self):
        s = self.sickness
        return "Good" if s < 35 else "Fair" if s < 70 else "Poor" if s < 105 else "Very poor"

    @property
    def mood(self):
        a = self.anger
        return "Calm" if a < 25 else "Restless" if a < 50 else "Angry" if a < 75 else "Furious"

    def _tick_date(self):
        self.days_elapsed += 1
        self.day += 1
        if self.day > D.DAYS_IN_MONTH:
            self.day, self.month = 1, self.month + 1
            if self.month > 12:
                self.month, self.year = 1, self.year + 1

    def is_sabbath(self):
        return self.manna and self.days_elapsed % 7 == 6

    def _daily_needs(self, resting=False):
        eat = D.RATIONS[self.rations][0] * D.PARTY_SIZE
        if self.manna and not self.is_sabbath():
            # Gathered daily, with a double portion on the sixth day (Exodus 16:5, 22).
            self.food += eat * (2 if self.days_elapsed % 7 == 5 else 1)
        hungry = self.food < eat
        self.food = max(0, self.food - eat)
        thirsty = self.water < D.WATER_PER_DAY
        self.water = max(0, self.water - D.WATER_PER_DAY)

        self.sickness *= 0.9
        self.sickness += D.RATIONS[self.rations][1]
        if not resting:
            self.sickness += D.PACES[self.pace][1]
        if hungry:
            self.sickness += 11
            self.anger += 6
        if thirsty:
            self.sickness += 10
            self.anger += 7
        if self.cloaks < D.PARTY_SIZE and self.month in (10, 11, 12, 1):
            self.sickness += 2
        self.anger = max(0, self.anger + (-1.0 if resting else 0.3))
        if self.sickness >= D.SICKNESS_DEAD:
            self.over = True

    def apply(self, fx):
        for key, value in fx.items():
            if key in ("oxen", "food", "water", "parts", "stones", "cloaks"):
                setattr(self, key, max(0, getattr(self, key) + value))
            elif key == "sickness":
                self.sickness = max(0, self.sickness + value)
            elif key == "anger":
                self.anger = min(100, max(0, self.anger + value))
            elif key == "people":
                self.people = max(0, self.people + value)
            elif key == "lose_day":
                for _ in range(value):
                    self._tick_date()
                    self._daily_needs(resting=True)

    # ---------- travel ----------
    def speed(self):
        if self.oxen <= 0:
            return 0
        return max(1, round(D.PACES[self.pace][0] * min(1.0, 0.4 + self.oxen * 0.15)))

    def travel_day(self):
        """Advance one day. Returns the events the player must see."""
        events = []
        if self.over:
            return events
        if self.is_sabbath():
            self._tick_date()
            self._daily_needs(resting=True)
            events.append(Event("Sabbath", "The camp rests and gathers no manna today.", "Exodus 16:29-30"))
            return events
        if self.oxen <= 0:
            self.over = True
            events.append(Event("Stranded", "With no oxen left, the carts cannot move.", kind="lose"))
            return events

        self._tick_date()
        self._daily_needs()
        step = min(self.speed(), self.to_next)
        self.to_next -= step
        self.miles += step
        if self.over:
            events.append(self._lost())
            return events
        if self.to_next <= 0:
            events.extend(self._arrive())
            return events
        events.extend(self._random_incident())
        if self.over:
            events.append(self._lost())
        return events

    def rest(self, days=1):
        for _ in range(days):
            self._tick_date()
            self._daily_needs(resting=True)
            self.sickness = max(0, self.sickness - 4)
            if self.over:
                return [self._lost()]
        return []

    def _lost(self):
        self.over = True
        return Event("The March Has Failed",
                     "Weakened beyond strength, the people can go no farther. "
                     "Begin again and lead them to the end.", kind="lose")

    def _random_incident(self):
        roll = self.rng.random()
        if self.anger >= 100:
            self.anger = 60
            self.apply({"sickness": 30, "people": -2000, "lose_day": 2})
            return [Event("The Camp Is in Uproar",
                          "The people are ready to stone Moses. The march halts while the "
                          "elders restore order, and many are lost.", "Exodus 17:4")]
        if (self.anger >= 75 and roll < 0.5) or roll < 0.04 + self.anger / 700:
            hungry = self.food < D.PARTY_SIZE * 6
            pool = [g for g in D.GRUMBLES if g[1] == "any" or (hungry and g[1] == "hungry")]
            text = self.rng.choice(pool)[0]
            return [Event("The People Grumble", text, "Exodus 16:2; 17:2-3",
                          choices=D.ANGER_CHOICES, kind="anger")]
        if roll < 0.20:
            weights = [a[1] for a in D.ACCIDENTS]
            text, _, fx = self.rng.choices(D.ACCIDENTS, weights)[0]
            if "parts" in fx and self.parts <= 0:
                fx = {"lose_day": 4}
                text += " With no spare, repairs take four days."
            self.apply(fx)
            return [Event("On the Way", text)]
        return []

    def choose(self, event, index):
        self.apply(event.choices[index][1])

    def _arrive(self):
        self.stop += 1
        name, _, ref, story, flags = D.ROUTE[self.stop]
        if flags.get("water"):
            self.pending_river = flags["water"]
        for key in ("anger", "food", "people"):
            if key in flags:
                self.apply({key: flags[key]})
        if flags.get("refill"):
            self.water = max(self.water, 150)
        if flags.get("heal"):
            self.sickness = max(0, self.sickness - flags["heal"])
        if flags.get("manna"):
            self.manna = True
        if flags.get("battle"):
            self.sickness += flags["battle"] * (0.5 if self.stones >= 20 else 1)
            self.stones = max(0, self.stones - 10)
        # Scripture fixes these dates; a slow march never moves the calendar back.
        if flags.get("date") and flags["date"] > (self.year, self.month, self.day):
            self.year, self.month, self.day = flags["date"]
        if flags.get("wait"):
            self.apply({"lose_day": flags["wait"]})
        if flags.get("generation"):
            self.sickness = min(self.sickness, 30)
            self.oxen = max(self.oxen, 4)
            self.parts = max(self.parts, 2)
        if flags.get("dies") in self.alive:
            self.alive.remove(flags["dies"])
        if self.stop + 1 < len(D.ROUTE):
            self.to_next = D.ROUTE[self.stop + 1][1]
        if flags.get("final"):
            self.over = self.won = True
        kind = "win" if flags.get("final") else "landmark"
        return [Event(name, story, ref, kind=kind)]

    def cross_water(self, method):
        """method: 'split' always works; 'ford' risks loss on rivers."""
        kind, self.pending_river = self.pending_river, None
        if kind == "sea":
            return Event("The Waters Part", "Moses stretches out his hand. The LORD drives "
                         "the sea back, Israel crosses on dry ground, and the waters return "
                         "upon Pharaoh's army.", "Exodus 14:21-31")
        if method == "split":
            return Event("The Waters Part", "Moses raises his staff, the waters stand "
                         "apart, and everyone crosses on dry ground.")
        if self.rng.random() < 0.35:
            self.apply({"food": -40, "parts": -1, "sickness": 10})
            return Event("Trouble at the Ford", "A cart tips in the current. Food and parts are lost.")
        return Event("Forded", "The people wade across safely.")

    def trade_offer(self):
        """A passing caravan proposes a swap: (give item, qty, get item, qty)."""
        items = ["oxen", "food", "cloaks", "stones", "parts", "water"]
        lots = {"oxen": 1, "food": 50, "cloaks": 2, "stones": 20, "parts": 1, "water": 30}
        give, get = self.rng.sample(items, 2)
        return give, lots[give], get, lots[get]

    def accept_trade(self, offer):
        give, give_qty, get, get_qty = offer
        if getattr(self, give) < give_qty:
            return False
        setattr(self, give, getattr(self, give) - give_qty)
        setattr(self, get, getattr(self, get) + get_qty)
        return True

    def hunt_reward(self, birds):
        gained = min(D.HUNT_CARRY_LIMIT, birds * 8)
        self.food += gained
        self.apply({"lose_day": 1})
        return gained

    def score(self):
        base = self.people // 1000 + len(self.alive) * 50
        base += self.oxen * 4 + self.food // 25 + self.cloaks * 2 + self.parts * 2 + self.silver // 5
        base += {"Good": 500, "Fair": 300, "Poor": 150}.get(self.health, 50)
        return base * D.TRIBES[self.tribe]["score"]
