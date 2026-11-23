"""All story content and tuning numbers for The Exodus.

Story text is a plain-language paraphrase; each entry cites its passage.
"""

MONTHS = ["Abib", "Ziv", "Sivan", "Tammuz", "Ab", "Elul",
          "Tishri", "Bul", "Kislev", "Tebeth", "Shebat", "Adar"]
DAYS_IN_MONTH = 30

LEADERS = ["Moses", "Aaron", "Hur", "Joshua", "Caleb"]

TRIBES = {
    "Judah": {"silver": 1600, "score": 1},
    "Levi": {"silver": 800, "score": 2},
    "Dan": {"silver": 600, "score": 3},
}

PRICES = {"oxen": 40, "food": 1, "cloaks": 10, "stones": 2, "parts": 10}
ITEM_NAMES = {"oxen": "Oxen", "food": "Food (omers)", "cloaks": "Cloaks",
              "stones": "Sling stones", "parts": "Cart parts", "water": "Water skins"}
PRICES["water"] = 3

PACES = {"Steady": (12, 0), "Strenuous": (18, 2), "Grueling": (24, 4)}
RATIONS = {"Filling": (3, 0), "Meager": (2, 2), "Bare bones": (1, 4)}
PARTY_SIZE = len(LEADERS)
WATER_PER_DAY = 5
SICKNESS_DEAD = 140
HUNT_CARRY_LIMIT = 100
START_PEOPLE = 600000

# name, miles from previous stop, passage, story, flags
ROUTE = [
    ("Rameses", 0, "Exodus 12:31-37",
     "After the tenth plague Pharaoh summons Moses and Aaron by night and tells "
     "them to go. Israel leaves with the silver and gold the Egyptians gave them, "
     "carrying unleavened dough.", {}),
    ("Succoth", 32, "Exodus 12:37; 13:19-22",
     "About 600,000 men on foot, plus women and children, reach Succoth. Moses "
     "carries the bones of Joseph. The LORD goes before them in a pillar of cloud "
     "by day and a pillar of fire by night.", {}),
    ("Etham", 20, "Exodus 13:20",
     "They camp at Etham on the edge of the wilderness.", {}),
    ("Pi-hahiroth", 25, "Exodus 14:1-12",
     "They camp by the sea. Pharaoh's chariots draw near, and the people cry out "
     "to Moses in terror.", {"anger": 25}),
    ("The Red Sea", 3, "Exodus 14:13-20",
     "Moses tells the people to stand firm and see the salvation of the LORD. The "
     "pillar of cloud moves behind Israel, between them and the Egyptians.",
     {"water": "sea"}),
    ("Marah", 45, "Exodus 15:22-26",
     "Three days without water, then only bitter water. The people grumble. The "
     "LORD shows Moses a tree; he throws it in and the water turns sweet.",
     {"anger": 20, "refill": True}),
    ("Elim", 10, "Exodus 15:27",
     "Twelve springs and seventy date palms. Israel camps beside the water.",
     {"refill": True, "heal": 40}),
    ("Wilderness of Sin", 40, "Exodus 16",
     "The whole congregation grumbles for the food of Egypt. That evening quail "
     "cover the camp, and in the morning there is manna. Gather it six days and "
     "rest on the Sabbath.", {"anger": 25, "manna": True}),
    ("Rephidim", 60, "Exodus 17",
     "No water, and the people nearly stone Moses. He strikes the rock at Horeb "
     "and water flows. Amalek attacks; Joshua fights while Aaron and Hur hold up "
     "Moses' hands until the sun sets, and Israel prevails.",
     {"anger": 30, "refill": True, "battle": 12}),
    ("Mount Sinai", 30, "Exodus 19-40; Numbers 10:11",
     "The LORD gives the Law on the mountain. While Moses is away, the people make "
     "a golden calf, and judgment falls. Moses intercedes, the covenant is renewed, "
     "and the tabernacle is built. The cloud lifts in the second year.",
     {"date": (2, 2, 20), "people": -3000, "heal": 60}),
    ("Taberah", 40, "Numbers 11:1-3",
     "The people complain, and fire from the LORD burns the edge of the camp until "
     "Moses prays.", {"anger": 15, "people": -500}),
    ("Kibroth-hattaavah", 15, "Numbers 11:4-34",
     "The people weep for meat. Quail come in great numbers, and a plague strikes "
     "those who craved.", {"anger": 15, "food": 80, "people": -1000}),
    ("Hazeroth", 30, "Numbers 11:35-12:16",
     "Miriam and Aaron speak against Moses. Miriam is struck with leprosy, Moses "
     "cries out for her, and the camp waits seven days.", {"wait": 7}),
    ("Kadesh", 90, "Numbers 13-14; 16; 20:1-13",
     "Twelve spies return, and ten spread fear. Only Joshua and Caleb trust the "
     "LORD. Israel must wander until that generation has died. Those who presume to "
     "go up are beaten back by the Amalekites and Canaanites. Korah rebels and "
     "perishes. In the fortieth year Miriam dies, and Moses strikes the rock at "
     "Meribah.", {"date": (40, 1, 10), "battle": 18, "refill": True, "generation": True}),
    ("Mount Hor", 60, "Numbers 20:22-29; 33:38",
     "Aaron's garments are placed on his son Eleazar, and Aaron dies on the "
     "mountaintop. Israel mourns him thirty days.",
     {"date": (40, 5, 1), "dies": "Aaron", "wait": 30}),
    ("Hormah", 25, "Numbers 21:1-3",
     "The Canaanite king of Arad attacks and takes captives. Israel makes a vow to "
     "the LORD, and the Canaanites are defeated.", {"battle": 20}),
    ("Brook Zered", 65, "Numbers 21:4-12",
     "The people speak against God and Moses, and fiery serpents bite them. Moses "
     "lifts up a bronze serpent, and all who look at it live.",
     {"anger": 20, "people": -800, "water": "river"}),
    ("River Arnon", 30, "Numbers 21:13-32",
     "Israel reaches the Arnon, the border of Moab, and defeats Sihon of the "
     "Amorites.", {"water": "river", "battle": 12}),
    ("Plains of Moab", 50, "Numbers 22:1; Deuteronomy 1:3",
     "Israel camps beside the Jordan opposite Jericho, and Moses teaches the people "
     "all the LORD has commanded.", {"date": (40, 11, 1), "refill": True}),
    ("Mount Nebo", 10, "Deuteronomy 34; Joshua 3",
     "The LORD shows Moses all the land. Moses dies there at 120 years old, his eye "
     "undimmed, and Joshua, full of the spirit of wisdom, leads Israel over the "
     "Jordan into the Promised Land.", {"dies": "Moses", "final": True}),
]

GRUMBLES = [
    ("The people are angry because they are hungry.", "hungry"),
    ("The people are angry, and who knows why.", "any"),
    ("The people say it was better to be slaves in Egypt.", "any"),
    ("The people remember the fish, leeks and onions of Egypt.", "hungry"),
    ("The people ask whether the LORD is among them at all.", "any"),
]

ANGER_CHOICES = [
    ("Moses cries out to the LORD", {"anger": -35}),
    ("Hand out extra food (20 omers)", {"anger": -25, "food": -20}),
    ("Aaron and the elders calm them", {"anger": -15}),
    ("Press on and ignore them", {"anger": 10, "sickness": 6}),
]

# text, weight, effects
ACCIDENTS = [
    ("An ox has wandered off.", 3, {"oxen": -1}),
    ("A cart wheel has broken.", 3, {"parts": -1, "lose_day": 1}),
    ("A sandstorm stops the march.", 3, {"lose_day": 2}),
    ("A water skin has split.", 3, {"water": -15}),
    ("Thieves took food in the night.", 2, {"food": -30}),
    ("A scorpion stung one of the elders' household.", 2, {"sickness": 12}),
    ("Fever is spreading through the camp.", 3, {"sickness": 18, "people": -200}),
    ("A cold desert night. Those without cloaks suffer.", 2, {"sickness": 8}),
    ("A traveler shares a spring with you.", 2, {"water": 25}),
    ("You find a stray ox.", 1, {"oxen": 1}),
]
