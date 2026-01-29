"""Central configuration constants for ProjektAstras.

Place project-wide constants here to avoid magic numbers.
Import like: from config import WINDOW_WIDTH, SIM_TICK_MS
"""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent
LOCALE_DIR = PROJECT_ROOT / "i18n"
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_SAVE_PATH = PROJECT_ROOT / "data" / "save.json"

# UI / Window
WINDOW_START_X = 100
WINDOW_START_Y = 100
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600
FPS = 60
DEFAULT_FONT = "Arial"
DEFAULT_FONT_SIZE = 14
UI_FONT_FAMILY = "Minecraft"
LOG_FONT_FAMILY = "Consolas"
LOG_FONT_SIZE = 12

# UI File Paths
START_SCREEN_GIF_PATH = "ui/astras.gif"
SPECIES_DATA_PATH = "data/species.json"
DEFAULT_INFOGRAPHIC_PATH = "ui/icefang_info.png"

# UI Flag Icons
FLAG_ICON_EN_CANDIDATES = (
    "icons/flag_en.png",
    "icons/us_flag.png",
    "icons/flag_us.png",
)
FLAG_ICON_DE_CANDIDATES = (
    "icons/flag_de.png",
    "icons/german_flag.png",
    "icons/flag_deutsch.png",
)

# Log Colors
LOG_COLOR_DEATH = "#cc3333"
LOG_COLOR_COLD = "#99ddff"
LOG_COLOR_COLD_DEATH = "#ff9999"
LOG_COLOR_EAT = "#cd853f"
LOG_COLOR_JOIN = "#bb88ff"
LOG_COLOR_LEAVE = "#ff9944"
LOG_COLOR_COMBAT = "#ff6666"
LOG_COLOR_TEMP = "#66ccff"
LOG_COLOR_DAY = "#ffdd44"
LOG_COLOR_NIGHT = "#aa88ff"

# Colors (RGB tuples) - adapt to your UI library as needed
COLOR_BACKGROUND = (34, 34, 34)
COLOR_FOREGROUND = (240, 240, 240)
COLOR_ACCENT = (40, 160, 220)
DEFAULT_COLOR_HEX = "#ffffff"

# Region Textures
REGION_TEXTURES = {
    "Snowy Abyss": "textures/snowy_abyss.png",
    "Wasteland": "textures/wasteland.png",
    "Evergreen Forest": "textures/evergreen_forest.png",
    "Corrupted Caves": "textures/corrupted_caves.png",
}

# UI/Species Icons (defaults/fallback)
ICON_SPORES = "ui/spores.png"
ICON_CRUSHED = "ui/crushed_critters.png"
ICON_ICEFANG = "ui/icefang.png"
ICON_CORRUPTED = "ui/corrupted.png"

# Simulation / Timing
SIM_TICK_MS = 16  # ~60 updates per second (1000/60 ≈ 16.67)
SIM_DEFAULT_SPEED = 1.0
SIM_MAX_SPEED = 16.0
SIM_MIN_SPEED = 0.125

# Entities / Limits
DEFAULT_ENTITY_COUNT = 50
MAX_ENTITIES = 1000

# Internationalization
DEFAULT_LOCALE = "en"
AVAILABLE_LOCALES = ("en", "de")
I18N_JSON_GLOB = "*.json"

# Misc / App behavior
AUTOSAVE_INTERVAL_SEC = 300  # 5 minutes
NETWORK_TIMEOUT_SEC = 10
LOG_LEVEL = "INFO"


# Helper convenience
def get_locale_file(locale: str) -> Path:
    """Get the path to the localization file for a given locale.

    @param locale: The locale code (e.g., 'en', 'de').
    @return: Path object pointing to the locale JSON file.
    """
    return LOCALE_DIR / f"{locale}.json"


# Additional simulation / map / game constants
# Map / spawn
SPAWN_PADDING = 50
MAP_DEFAULT_HEIGHT = 600
MAP_DEFAULT_WIDTH = 1200

# Grid and spatial
GRID_CELL_SIZE = 150
GRID_CELL_SIZE_SQ = GRID_CELL_SIZE * GRID_CELL_SIZE

# Hunger / life
HUNGER_THRESHOLD_RANGE = (150, 260)
HUNGER_ALERT = 50
HUNGER_TIMER_DEATH = 300

# Rng/history limits
RND_HISTORY_LIMIT = 500

# Day/night timing (in simulation steps)
DAY_NIGHT_CYCLE_DURATION = 300
TRANSITION_DURATION = 50

# Population / logging
POP_HISTORY_STEP = 10
MAX_LOGS = 300

# Food / resources
FOOD_DEFAULT_AMOUNT = 50
# Default number of food places to generate when none are provided
DEFAULT_FOOD_PLACES = 5

# Temperature bounds
TEMPERATURE_MIN = -80
TEMPERATURE_MAX = 50

# Species defaults
SPECIES_DEFAULT_MIN_SURVIVAL_TEMP = -100
SPECIES_DEFAULT_MAX_SURVIVAL_TEMP = 100

# Random ranges
RANDOM_SPEED_RANGE = (0.4, 1.0)

# Frontend / UI layout defaults
MIN_PANEL_HEIGHT = 300
RIGHT_COLUMN_MIN_WIDTH = 300
MAX_SIMULATION_TIME = 300  # seconds

# Additional UI layout constants
MAP_MIN_WIDTH = 600
MAP_MIN_HEIGHT = 400
PANEL_STACK_MIN_HEIGHT = 400
LIVE_PLOT_MIN_HEIGHT = 240
LOG_MIN_HEIGHT = 80
CONTENT_MARGIN = 20
BUTTON_FIXED_WIDTH = 100
UPDATE_TIMER_INTERVAL_MS = 100

# Backend simulation constants
FOOD_RANGE = 20
FOOD_SEARCH_RADIUS = 400
INTERACTION_RANGE = 100
HUNT_RANGE = 400
HUNT_LOG_COOLDOWN = 100
FORMATION_RANGE = 50
MAP_EDGE_PADDING = 100
TEMP_CHANGE_INTERVAL = 200
TEMP_CHANGE_DELTA = 3.0
ATTACK_DAMAGE = 6
LONER_HUNGER_SEEK = 200
FOOD_REGEN_PROB = 0.03
COMBAT_STRENGTH_RANGE = (0.85, 1.25)
LONER_HUNGER_RANGE = (40, 90)
MAX_CLANS_PER_SPECIES = 15
BASE_TEMPERATURE_FALLBACK_RANGE = (-20, 20)

# Damage clamps
LONER_DAMAGE_MIN = 6
LONER_DAMAGE_MAX = 40
CLAN_DAMAGE_MIN = 2
CLAN_DAMAGE_MAX = 12

# Hunger/time conversion: 1 food = X steps
FOOD_HUNGER_STEP = 10

# Spawn thresholds
SPAWN_THRESHOLD_HIGH = 0.008
SPAWN_THRESHOLD_LOW = 0.002

# Attack chance tuning
ATTACK_CHANCE_DAY = 0.3
ATTACK_CHANCE_NIGHT = 0.15
AGGRESSIVE_ATTACK_CHANCE_DAY = 0.6
AGGRESSIVE_ATTACK_CHANCE_NIGHT = 0.35

# History trimming thresholds
RND_HISTORY_TRIM_THRESHOLD = 200
RND_HISTORY_TRIM_SIZE = 500

# Friendly stick chance
FRIENDLY_STICK_CHANCE = 0.5

# Movement / velocity ranges
LONER_VELOCITY_RANGE = (-2.5, 2.5)
CLAN_VELOCITY_RANGE = (-2.0, 2.0)

# Night speed modifier (percent of day speed)
NIGHT_SPEED_MODIFIER = 0.7

# RNG / movement tuning
RANDOM_MOVE_PROB = 0.02
REGEN_CHOICES = [1, 1, 1, 2, 2, 3]
LONER_SPEED_INIT_RANGE = (0.8, 1.5)
LONER_SPEED_ALT_RANGE = (0.4, 1.0)

# Defaults and limits
MAX_CLANS_DEFAULT = 8

# Split / clan-splitting tuning
SPLIT_DENOM = 0.5
SPLIT_BASE_CHANCE = 0.15
SPLIT_POP_FRAC = 0.5

# Friendly / growth / join tuning
FRIENDLY_GROWTH_CHANCE_DEFAULT = 0.08
ICEFANG_GROWTH_CHANCE = 0.02
FRIENDLY_BASE_GROWTH = 0.03
JOIN_BASE_CHANCE = 0.03
JOIN_HUNGRY_CHANCE = 0.15
JOIN_HUNGER_THRESHOLD = 50
FORMATION_PROBABILITY = 0.05

# Spawn helpers
SPAWN_SINGLE_COUNT = 1

# Chase / attack tuning
CHASE_STRENGTH = 0.7
CHASE_ATTACK_CHANCE_DAY = 0.6
CHASE_ATTACK_CHANCE_NIGHT = 0.3

# Movement defaults
MOVE_TOWARDS_DEFAULT_STRENGTH = 0.5
MOVE_TOWARDS_MAX_SPEED = 3.0
MOVE_STRENGTH_NEAREST_FOOD = 0.5
MOVE_STRENGTH_FRIENDLY_STICK = 0.2
MOVE_STRENGTH_FLEE = 0.4

# Gaussian growth params
GAUSS_MU = 1.0
GAUSS_SIGMA = 0.8

# Grid / spatial
GRID_CELL_MIN = 8

# Simulation step timeout
SIM_STEP_TIMEOUT = 1

# Population thresholds
START_POP_THRESHOLD = 10

# Default HP caps
DEFAULT_HP = 25
ICEFANG_HP_CAP = 40
OTHER_HP_CAP = 70
# Region modifier defaults
REGION_DEFAULT_CHANCE = 0.35

# Default food intake per loner/clan member
FOOD_INTAKE_DEFAULT = 5

# Spawn / population
LONER_SPAWN_RANGE = (2, 5)

# Clan death / split tuning
CLAN_DEATH_DIVISOR = 10

# Day/Night transition delta (degrees applied as +/-)
DAY_NIGHT_TEMP_DELTA = 5.0

# Temperature damage tuning
TEMP_DAMAGE_BASE_LONER = 6
TEMP_DAMAGE_PER_STEP_LONER = 3
TEMP_DEGREE_STEP = 5
TEMP_DAMAGE_BASE_CLAN = 2

# Rounding precision for temperature displays
TEMPERATURE_PRECISION = 1

# Default fallback color (RGBA)
DEFAULT_COLOR = (0.5, 0.5, 0.5, 1)

# Additional tuning constants discovered during refactor
LONER_SEARCH_BOOST = 1.5
BASE_PREY_SPEED = 3.5
BASE_FOOD_SPEED = 3.0
HP_PER_FOOD = 5
CLAN_SPLIT_DIVISOR = 2
CLAN_TEMP_SURVIVAL_CHANCE = 0.2
MAX_HP_FALLBACK = 50

# Small tuning constants
MIN_DIST_CLAMP = 0.1
REPEL_STRENGTH = 0.3
MIN_DEFENSE = 0.5
FRIENDLY_STICK_STRENGTH = 0.4
FOOD_PER_KILL = 2
HUNGRY_THRESHOLD = 50
# Bounds for speed multipliers
SPEED_MULT_MIN = 0.5
SPEED_MULT_MAX = 2.0

# Icefang region boost
ICEFANG_BOOST_HP_MULT = 1.18
ICEFANG_BOOST_COMBAT_MULT = 1.12
ICEFANG_BOOST_HUNGER_DELTA = 8

# Spores region boost
SPORES_BOOST_HP_MULT = 1.2
SPORES_BOOST_COMBAT_MULT = 1.15
SPORES_BOOST_HUNGER_DELTA = 8

# Crushed_Critters (Wasteland) region boost
CRUSHED_BOOST_HP_MULT = 1.18
CRUSHED_BOOST_COMBAT_MULT = 1.1
CRUSHED_BOOST_HUNGER_DELTA = 6

# The_Corrupted region boost
CORRUPTED_BOOST_HP_MULT = 1.22
CORRUPTED_BOOST_COMBAT_MULT = 1.18
CORRUPTED_BOOST_HUNGER_DELTA = 8

# Species default display colors (RGBA floats)
ICEFANG_COLOR = (0.8, 0.9, 1, 1)
CRUSHED_CRITTERS_COLOR = (0.6, 0.4, 0.2, 1)
SPORES_COLOR = (0.2, 0.8, 0.2, 1)
THE_CORRUPTED_COLOR = (0.5, 0, 0.5, 1)
