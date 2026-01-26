"""
Central Configuration File for ProjektAstras
All magic numbers, file paths, and constants are defined here.
"""

# ========== MAP & WORLD DIMENSIONS ==========
MAP_WIDTH = 1200
MAP_HEIGHT = 600
GRID_CELL_SIZE = 150

# ========== WINDOW & UI DIMENSIONS ==========
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
WINDOW_X_POS = 100
WINDOW_Y_POS = 100

# ========== TIMING & SIMULATION CYCLES ==========
DAY_NIGHT_CYCLE_DURATION = 300  # Steps per day/night cycle
TRANSITION_DURATION = 50  # Steps for day/night transition
GRAPH_UPDATE_INTERVAL = 0.5  # Seconds between graph updates
MAX_SIMULATION_TIME = 300  # Maximum simulation time in seconds (5 minutes)

# ========== HUNGER & STARVATION ==========
# Clan hunger thresholds
CLAN_HUNGER_DEATH_THRESHOLD = 300  # Steps before starvation death
CLAN_HUNGER_MIN_THRESHOLD = 40  # Minimum hunger threshold (randomized range start)
CLAN_HUNGER_MAX_THRESHOLD = 90  # Maximum hunger threshold (randomized range end)

# Loner hunger thresholds
LONER_HUNGER_MIN_THRESHOLD = 150  # Minimum loner hunger threshold
LONER_HUNGER_MAX_THRESHOLD = 260  # Maximum loner hunger threshold

# ========== COMBAT & INTERACTION RANGES ==========
FOOD_RANGE = 20  # Distance to eat food
FOOD_SEARCH_RADIUS = 400  # Search radius for food
INTERACTION_RANGE = 100  # Combat/interaction distance
HUNT_RANGE = 400  # Active hunting range
HUNT_LOG_COOLDOWN = 100  # Log hunting every N steps
FORMATION_RANGE = 50  # Distance for loner formation into clans
ATTACK_DAMAGE = 6  # Base attack damage

# ========== TEMPERATURE & DAMAGE MECHANICS ==========
# Loner temperature damage
LONER_TEMP_DAMAGE_BASE = 6  # Base HP damage
LONER_TEMP_DAMAGE_PER_5DEG = 3  # Additional HP per 5 degrees
LONER_TEMP_DAMAGE_MAX = 40  # Maximum HP damage from temperature

# Clan temperature damage
CLAN_TEMP_DAMAGE_BASE = 2  # Base HP damage
CLAN_TEMP_DAMAGE_PER_5DEG = 1  # Additional HP per 5 degrees
CLAN_TEMP_DAMAGE_MAX = 12  # Maximum HP damage from temperature

# Health regeneration
HP_REGEN_PER_FOOD = 5  # HP regenerated per food unit

# ========== SPAWNING & POPULATION LIMITS ==========
MAX_CLANS_PER_SPECIES = 15  # Maximum clans allowed per species
SPAWN_THRESHOLD_NORMAL = 0.005  # Normal spawn chance (0.5%)
SPAWN_THRESHOLD_LOW_POP = 0.001  # Spawn chance when population < 10
FOOD_REGEN_PROBABILITY = 0.02  # 2% chance per step for food regeneration
REGEN_CHOICES = [1, 1, 1, 2, 2, 3]  # Small regeneration amounts (biased towards 1 and 2)

# ========== MOVEMENT SPEEDS & MODIFIERS ==========
# Velocity ranges
CLAN_VELOCITY_RANGE = 2.0  # Clan velocity randomization range
LONER_VELOCITY_RANGE = 2.5  # Loner velocity randomization range

# Speed modifiers
NIGHT_SPEED_MODIFIER = 0.7  # 70% speed at night
SPEED_CHANGE_CHANCE = 0.01  # Random direction change probability for clans
LONER_DIRECTION_CHANGE = 0.02  # Loner direction change probability
LONER_SEARCH_BOOST = 1.5  # Loner search radius multiplier

# ========== BOUNDARIES & SPAWNING ==========
SPAWN_MARGIN = 100  # Boundary margin for spawning (pixels from edge)
MOVEMENT_BOUNDARY = 50  # Keep entities within N pixels of edge
BOUNDARY_BOUNCE_MARGIN = 50  # Bounce distance from boundaries

# ========== GROWTH & GENETICS ==========
# Growth probabilities
GROWTH_CHANCE_BASE = 0.08  # Base growth from friendly encounters (8%)
GROWTH_CHANCE_HUNGRY = 0.02  # Growth when hungry (2%)
GROWTH_CHANCE_COMBAT_WIN = 0.03  # Growth from winning combat (3%)
GROWTH_CHANCE_RARE = 0.005  # Rare growth scenario (0.5%)

# Combat strength randomization
COMBAT_STRENGTH_MIN = 0.85
COMBAT_STRENGTH_MAX = 1.25

# Mutation parameters
MUTATION_MU = 1.0  # Normal mutation center
MUTATION_SIGMA = 0.8  # Mutation spread

# ========== JOIN/LEAVE MECHANICS ==========
LONER_JOIN_BASE_CHANCE = 0.03  # Base chance for loner to join clan (3%)
LONER_JOIN_HUNGRY_CHANCE = 0.15  # Join chance when hungry (15%)
CLAN_LEAVE_CHANCE = 0.1  # Chance for member to leave clan as loner (10%)
SPLIT_CHANCE_THRESHOLD = 1.0  # Force split threshold

# ========== REGION MODIFIERS ==========
REGION_NATIVE_HP_MULT = 1.18  # HP multiplier for native species in region
REGION_NATIVE_COMBAT_MULT_MIN = 1.12  # Min combat multiplier for natives
REGION_NATIVE_COMBAT_MULT_MAX = 1.18  # Max combat multiplier for natives
REGION_BOOST_CHANCE = 0.35  # Chance for region boost (35%)
REGION_HUNGER_DELTA_MIN = 6  # Min hunger delta for region
REGION_HUNGER_DELTA_MAX = 8  # Max hunger delta for region

# ========== MAX LIMITS & HISTORY ==========
MAX_LOG_ENTRIES = 300  # Maximum log entries to keep

# ========== FILE PATHS (Static Resources) ==========
# Data files
SPECIES_DATA_PATH = "data/species.json"
REGION_DATA_PATH = "data/region.json"

# UI assets
START_SCREEN_BACKGROUND = "ui/astras.gif"
FLAG_EN_PATHS = ["icons/flag_en.png", "icons/us_flag.png", "icons/flag_us.png"]
FLAG_DE_PATHS = ["icons/flag_de.png", "icons/german_flag.png", "icons/flag_deutsch.png"]

# ========== UI/DISPLAY CONSTANTS ==========
# Log display
LOG_FONT_FAMILY = "Consolas"
LOG_FONT_SIZE = 12

# Flag buttons
FLAG_BUTTON_WIDTH = 48
FLAG_BUTTON_HEIGHT = 32

# ========== COLOR PRESETS ==========
# Species color mapping (RGBA tuples)
COLOR_MAP = {
    "Icefang": (0.8, 0.9, 1, 1),
    "Crushed_Critters": (0.6, 0.4, 0.2, 1),
    "Spores": (0.2, 0.8, 0.2, 1),
    "The_Corrupted": (0.5, 0, 0.5, 1),
}
