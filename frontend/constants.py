"""
All magic numbers, colors, paths, costs, and configuration.
Every other file imports from here.
Things like HEX_SIZE, RESOURCE_COLORS, SETTLEMENT_COST, PORT_TYPES, BUILD_SETTLEMENT, etc.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Window Size  -  Trying to make it wider not taller for laptops
# ---------------------------------------------------------------------------
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 701
SCREEN_TITLE  = "Coders of Catan"

# ---------------------------------------------------------------------------
# Background image
# Change this filename to swap backgrounds — file must live in sprites/background/
# ---------------------------------------------------------------------------
BACKGROUND_IMAGE = os.path.join(BASE_DIR, "sprites", "background", "ocean_background.png")
BACKGROUND_IMAGE_SECRET = os.path.join(BASE_DIR, "sprites", "background", "background_secret.jpg")
# ---------------------------------------------------------------------------
# Hex & board layout
# ---------------------------------------------------------------------------
HEX_SIZE      = 58
BOARD_CENTER_X = SCREEN_WIDTH  / 2
BOARD_CENTER_Y = SCREEN_HEIGHT / 2 + 10

# ---------------------------------------------------------------------------
# HUD dimensions  — slim left panel, single column
# ---------------------------------------------------------------------------
HUD_BOTTOM_HEIGHT = 70
HUD_PANEL_WIDTH   = 155     # Change for resource columns (155 narrow --> 250 wide)
HUD_PANEL_HEIGHT  = 210
DICE_AREA_WIDTH   = 160
DICE_AREA_HEIGHT  = 110

# ---------------------------------------------------------------------------
# Sprite / icon settings
# ---------------------------------------------------------------------------
ICON_SIZE    = 22           # smaller icons to fit single-column panel (22)
SPRITE_SCALE = ICON_SIZE / 512

RESOURCE_SPRITES = {
    "brick":  os.path.join(BASE_DIR, "sprites", "BW_icons", "brick-pile.png"),
    "ore":    os.path.join(BASE_DIR, "sprites", "BW_icons", "stone-pile.png"),
    "wheat":  os.path.join(BASE_DIR, "sprites", "BW_icons", "wheat.png"),
    "sheep":  os.path.join(BASE_DIR, "sprites", "BW_icons", "sheep.png"),
    "forest": os.path.join(BASE_DIR, "sprites", "BW_icons", "wood-pile.png"),
}

PORT_SHIP_SPRITE = os.path.join(BASE_DIR, "sprites", "ports", "galley_ship.png")

# Six die-face sprites  (dice-1.png … dice-6.png)
DICE_SPRITES = {
    i: os.path.join(BASE_DIR, "sprites", "dice", "vector", f"dice-{i}.png")
    for i in range(1, 7)
}

# Robber token sprite
ROBBER_SPRITE = os.path.join(BASE_DIR, "sprites", "robber", "vector", "robber.png")

# Dice-roll animation settings
DICE_ROLL_DURATION   = 1.2   # total seconds the animation runs
DICE_ROLL_FLIP_RATE  = 0.07  # seconds between face-flips while rolling

# ---------------------------------------------------------------------------
# Colors in HUD
# ---------------------------------------------------------------------------
HUD_BG           = (30,  30,  50,  210)
HUD_PANEL_BG     = (20,  20,  40,  220)
BTN_TRADE        = (52,  152, 219)
BTN_BUILD        = (39,  174, 96)
BTN_BUILD_ACTIVE = (100, 220, 130)
BTN_CARD         = (142, 68,  173)
BTN_ENDTURN      = (231, 76,  60)
TEXT_WHITE       = (255, 255, 255)
TEXT_LIGHT_GRAY  = (180, 180, 180)
TEXT_GOLD        = (255, 215, 0)
TOKEN_RED        = (200, 50,  50)    # color for unique 6 and 8 number tokens

RESOURCE_COLORS = {
    "forest": (34,  139, 34),
    "wheat":  (255, 215, 0),
    "ore":    (112, 128, 144),
    "brick":  (178, 34,  34),
    "sheep":  (144, 238, 144),
    "desert": (210, 180, 140),
}

# Resource name -> display abbreviation shown on port labels
RESOURCE_ABBR = {
    "brick":  "BRICK",
    "ore":    "ORE",
    "wheat":  "WHEAT",
    "sheep":  "SHEEP",
    "forest": "WOOD",
}

# ---------------------------------------------------------------------------
# Catan number token distribution
# 18 tokens for 18 non-desert tiles:
#   2×1, 3×2, 4×2, 5×2, 6×2, 8×2, 9×2, 10×2, 11×2, 12×1
# ---------------------------------------------------------------------------
NUMBER_POOL = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]

# ---------------------------------------------------------------------------
# Port types assigned clockwise from the top around the board perimeter.
# None = 3:1 generic port, string = 2:1 specific resource port.
# The 9 slots are spaced evenly among the ~18 outer edges automatically.
PORT_TYPES = ["ore", None, "wheat", None, None, "brick", None, "sheep", "forest"]

# ---------------------------------------------------------------------------
# Build choices
# ---------------------------------------------------------------------------
BUILD_NONE       = None
BUILD_SETTLEMENT = "settlement"
BUILD_ROAD       = "road"
BUILD_CITY       = "city"
TRADE_NONE       = None

# ---------------------------------------------------------------------------
# Costs
# ---------------------------------------------------------------------------
SETTLEMENT_COST = {"BRICK": 1, "WOOD": 1, "WHEAT": 1, "SHEEP": 1}
ROAD_COST       = {"BRICK": 1, "WOOD": 1}

# Snap radii (pixels)
NODE_SNAP_RADIUS = 18
EDGE_SNAP_RADIUS = 14