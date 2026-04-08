"""
All magic numbers, colors, paths, costs, and configuration.
Every other file imports from here.
Things like HEX_SIZE, RESOURCE_COLORS, SETTLEMENT_COST, PORT_TYPES, BUILD_SETTLEMENT, etc.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Window Size -
SCREEN_WIDTH  = 1400
SCREEN_HEIGHT = 750
SCREEN_TITLE  = "Coders of Catan"

# ---------------------------------------------------------------------------
# Background image
# Change this filename to swap backgrounds — file must live in sprites/background/
BACKGROUND_IMAGE = os.path.join(BASE_DIR, "sprites", "background", "picture.png")

# ---------------------------------------------------------------------------
BACKGROUND_IMAGE = os.path.join(BASE_DIR, "sprites", "background", "ocean_background.png")
BACKGROUND_IMAGE_SECRET = os.path.join(BASE_DIR, "sprites", "background", "background_secret.jpg")
# Animated ocean background
USE_OCEAN_BACKGROUND = True

# Base water tones
OCEAN_BASE_COLOR = (70, 145, 201, 1)
OCEAN_DEEP_COLOR = (52, 118, 178)
OCEAN_MID_COLOR = (84, 160, 214)
OCEAN_BAND_COLOR = (255, 255, 255, 18)
OCEAN_RIPPLE_COLOR = (220, 245, 255, 12)

# Large rolling sea bands
OCEAN_BAND_COUNT = 7
OCEAN_BAND_SPACING = 92
OCEAN_BAND_THICKNESS = 18
OCEAN_BAND_AMPLITUDE = 18
OCEAN_BAND_WAVELENGTH = 170
OCEAN_BAND_SCROLL_SPEED = 22.0
OCEAN_BAND_PHASE_SPEED = 0.85

# Secondary faint ripples
OCEAN_RIPPLE_COUNT = 5
OCEAN_RIPPLE_SPACING = 125
OCEAN_RIPPLE_THICKNESS = 8
OCEAN_RIPPLE_AMPLITUDE = 10
OCEAN_RIPPLE_WAVELENGTH = 110
OCEAN_RIPPLE_SCROLL_SPEED = 13.0

# Shoreline shimmer
SHORE_FOAM_COLOR = (255, 255, 255, 74)
SHORE_FOAM_HIGHLIGHT_COLOR = (220, 245, 255, 134)
SHORE_FOAM_WIDTH = 6
SHORE_FOAM_HIGHLIGHT_WIDTH = 2
SHORE_FOAM_OFFSET = 8
SHORE_FOAM_PULSE_SPEED = 2.1
SHORE_OUTER_RING_ONLY = True


# ---------------------------------------------------------------------------
# Hex & board layout
HEX_SIZE      = 58
BOARD_CENTER_X = SCREEN_WIDTH  / 2
BOARD_CENTER_Y = SCREEN_HEIGHT / 2 + 10

# ---------------------------------------------------------------------------
# HUD dimensions  — slim left panel, single column
HUD_BOTTOM_HEIGHT = 70
HUD_PANEL_WIDTH   = 155     # Change for resource columns (155 narrow --> 250 wide)
HUD_PANEL_HEIGHT  = 250
DICE_AREA_WIDTH   = 160
DICE_AREA_HEIGHT  = 110

# ---------------------------------------------------------------------------
# Sprite / icon settings
ICON_SIZE    = 24           # smaller icons to fit single-column panel (22)
SPRITE_SCALE = ICON_SIZE / 512

RESOURCE_SPRITES = {
    "brick":  os.path.join(BASE_DIR, "sprites", "BW_icons", "brick-pile.png"),
    "ore":    os.path.join(BASE_DIR, "sprites", "BW_icons", "stone-pile.png"),
    "wheat":  os.path.join(BASE_DIR, "sprites", "BW_icons", "wheat.png"),
    "sheep":  os.path.join(BASE_DIR, "sprites", "BW_icons", "sheep.png"),
    "forest": os.path.join(BASE_DIR, "sprites", "BW_icons", "wood-pile.png"),
}

# Hex tile art sprites
_HEX = os.path.join(BASE_DIR, "sprites", "hexes")

HEX_TILE_SPRITES = {
    "wheat":  os.path.join(_HEX, "wheat_field.png"),
    "forest": os.path.join(_HEX, "wood_forest.png"),
    "brick":  os.path.join(_HEX, "brick_hill.png"),
    "desert": os.path.join(_HEX, "desert.png"),
    "ore":    os.path.join(_HEX, "ore_mountain.png"),
    "sheep":  os.path.join(_HEX, "sheep_pasture.png"),
}

HEX_TILE_SCALE = 0.235
HEX_TILE_Y_OFFSET = -1
HEX_TILE_OUTLINE_WIDTH = 2

PORT_SHIP_SPRITE = os.path.join(BASE_DIR, "sprites", "ports", "galley_ship.png")

# Six die-face sprites  (dice-1.png … dice-6.png)
DICE_SPRITES = {
    i: os.path.join(BASE_DIR, "sprites", "dice", "vector", f"dice-{i}.png")
    for i in range(1, 7)
}

# Robber token sprite
ROBBER_SPRITE = os.path.join(BASE_DIR, "sprites", "robber", "vector", "robber.png")

# Largest Army and Longest Road
ARMY_CARD_SPRITE = os.path.join(BASE_DIR, "sprites", "special_cards", "army_card.png")
ROAD_CARD_SPRITE = os.path.join(BASE_DIR, "sprites", "special_cards", "road_card.png")

# Dice-roll animation settings
DICE_ROLL_DURATION   = 1.2   # total seconds the animation runs
DICE_ROLL_FLIP_RATE  = 0.07  # seconds between face-flips while rolling

DEV_KEY_K  = "knight"
DEV_KEY_RB = "road_building"
DEV_KEY_VP = "victory_point"
DEV_KEY_YOP= "year_of_plenty"
DEV_KEY_M  = "monopoly"


# Development card sprites  (discovery folder)
_DISC = os.path.join(BASE_DIR, "sprites", "discovery")
DEV_CARD_SPRITES = {
    "knight":         os.path.join(_DISC, "dcs__knight.png"),
    "monopoly":       os.path.join(_DISC, "dcs__monopoly.png"),
    "road_building":  os.path.join(_DISC, "dcs__roadBuilding.png"),
    "year_of_plenty": os.path.join(_DISC, "dcs__yearOfPlenty.png"),
    "university":     os.path.join(_DISC, "dcs__university.png"),
    "victory_point":  os.path.join(_DISC, "dcs__university.png"),
    "back":           os.path.join(_DISC, "dcs__back.png"),
}

# Full Catan dev-card deck composition (25 cards total)
DEV_CARD_DECK = (
    ["knight"] * 14 +
    ["victory_point"] * 5 +
    ["road_building"] * 2 +
    ["year_of_plenty"] * 2 +
    ["monopoly"] * 2
)

# Cost to buy a development card
DEV_CARD_COST = {"ORE": 1, "WHEAT": 1, "SHEEP": 1}

# ---------------------------------------------------------------------------
# Dev card visuals  (used by dev_base.py card classes)
# One entry per card type for label, tooltip description, and RGBA tint.
DEV_CARD_LABELS = {
    "knight":         "Knight",
    "road_building":  "Road Building",
    "year_of_plenty": "Year of Plenty",
    "monopoly":       "Monopoly",
    "victory_point":  "Victory Point",
}

ACTION_NONE           = "none"
ACTION_BACK_TO_BOARD  = "back_to_board"
ACTION_POPUP_YOP      = "popup_yop"
ACTION_POPUP_MONOPOLY = "popup_monopoly"

DEV_CARD_DESCRIPTIONS = {
    "knight":         "Move the robber & optionally steal a resource",
    "road_building":  "Place 2 free roads anywhere connected to your network",
    "year_of_plenty": "Take any 2 resources from the bank",
    "monopoly":       "Steal all of one resource type from every other player",
    "victory_point":  "+1 Victory Point (revealed at end of game)",
}

DEV_CARD_TINTS = {
    "knight":         (160,  60,  60, 255),
    "road_building":  ( 52, 100, 200, 255),
    "year_of_plenty": (200, 160,  30, 255),
    "monopoly":       (100,  40, 160, 255),
    "victory_point":  ( 30, 160, 100, 255),
    "just_bought":    ( 60,  60,  65, 220),   # greyed-out tint for newly drawn cards
}

CARD_DESC_TEXT_SIZE = 11
CARD_DESC_TEXT_Y_OFFSET = 25
CARD_DESC_TEXT_COLOR = (244, 158, 118)

# ---------------------------------------------------------------------------
# PlayCardView layout
CARD_W             = 170          # rendered dev card width  (px)
CARD_H             = 250         # rendered dev card height (px)
CARD_GAP           = 14          # horizontal gap between cards
CARD_TOP           = SCREEN_HEIGHT - 120   # y of card tops (distance from bottom)

CARD_BTN_W         = 180         # bottom-bar button width
CARD_BTN_H         = 44          # bottom-bar button height
CARD_PAD           = 18          # outer padding around bottom bar buttons

CARD_BOTTOM_BAR_H  = 70          # height of the bottom action bar
CARD_HEADER_Y      = SCREEN_HEIGHT - 30   # y of the view title text
CARD_DECK_Y        = SCREEN_HEIGHT - 58   # y of the deck-count subtitle

CARD_POPUP_W       = 370         # resource-picker popup width
CARD_POPUP_H       = 180         # resource-picker popup height
CARD_POPUP_BTN_W   = 60          # each resource button width inside popup
CARD_POPUP_BTN_H   = 36          # each resource button height inside popup
CARD_POPUP_BTN_GAP = 8           # gap between resource buttons in popup

CARD_NOTIF_Y       = 100         # y of the notification banner text
CARD_NOTIF_TIMER   = 3.5         # seconds the notification stays on screen

CARD_LIFT_SELECTED = 14          # px a selected card is raised
CARD_LIFT_HOVERED  = 5           # px a hovered card is raised

CARD_BADGE_W       = 38          # "NEW" badge width  (px)
CARD_BADGE_H       = 18          # "NEW" badge height (px)

CARD_BORDER_SEL    = 3           # selected card border thickness
CARD_BORDER_HOV    = 2           # hovered  card border thickness
CARD_BORDER_IDLE   = 1           # idle     card border thickness

CARD_SPRITE_Y_FRAC = 0.5         # fraction up the card where the sprite is centred

# Bottom-bar button labels
CARD_BACK_LABEL = "← Back to Board"
CARD_BUY_LABEL  = "Buy Card  (Ore+Wheat+Sheep)"
CARD_PLAY_LABEL = "▶  Play Selected Card"

# Bottom-bar text sizes
CARD_BACK_TEXT_SIZE = 12
CARD_BUY_TEXT_SIZE  = 12
CARD_PLAY_TEXT_SIZE = 12

# Optional: separate widths if one button needs more room
CARD_BACK_BTN_W = 180
CARD_BUY_BTN_W  = 280
CARD_PLAY_BTN_W = 180

# Resource key -> display name used in Year of Plenty / Monopoly popup
CARD_RES_NAMES = {
    "WOOD":  "Wood",
    "BRICK": "Brick",
    "WHEAT": "Wheat",
    "SHEEP": "Sheep",
    "ORE":   "Ore",
}

# ----------------------------------------------------------------
# Dark menu layouts
TOP_BAR_HEIGHT = 64
LARGE_TEXT_SIZE = 20

# ---------------------------------------------------------------------------
# Colors in HUD
HUD_BG           = (30,  30,  50,  210)
HUD_PANEL_BG     = (20,  20,  40,  220)
BTN_TRADE        = (52,  152, 219)
BTN_BUILD        = (39,  174, 96)
BTN_BUILD_ACTIVE = (100, 220, 130)
BTN_CARD         = (142, 68,  173)
BTN_ENDTURN      = (231, 76,  60)
BTN_DISABLED     = (45,  45,  55)    # greyed-out color for any inactive button
TEXT_WHITE       = (255, 255, 255)
TEXT_LIGHT_GRAY  = (180, 180, 180)
TEXT_GOLD        = (255, 215, 0)
TOKEN_RED        = (200, 50,  50)    # color for unique 6 and 8 number tokens

RESOURCE_COLORS = {
    "forest": (32, 138, 36),
    "wheat":  (255, 215, 75),
    "ore":    (112, 128, 144),
    "brick":  (178, 74, 34),
    "sheep":  (230, 223, 193),
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


# Catan number token distribution
# 18 tokens for 18 non-desert tiles:
#   2×1, 3×2, 4×2, 5×2, 6×2, 8×2, 9×2, 10×2, 11×2, 12×1
NUMBER_POOL = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]


# Port types assigned clockwise from the top around the board perimeter.
# None = 3:1 generic port, string = 2:1 specific resource port.
# The 9 slots are spaced evenly among the ~18 outer edges automatically.
PORT_TYPES = ["ore", None, "wheat", None, None, "brick", None, "sheep", "forest"]


# Build choices
BUILD_NONE       = None
BUILD_SETTLEMENT = "settlement"
BUILD_ROAD       = "road"
BUILD_CITY       = "city"
TRADE_NONE       = None

# Costs
SETTLEMENT_COST = {"BRICK": 1, "WOOD": 1, "WHEAT": 1, "SHEEP": 1}
ROAD_COST       = {"BRICK": 1, "WOOD": 1}
CITY_COST       = {"ORE": 3, "WHEAT": 2}


# Snap radii (pixels)
NODE_SNAP_RADIUS = 18
EDGE_SNAP_RADIUS = 14


# Dice constants
ONE = 1
SIX = 6


# Set True to render dice-face sprites instead of plain colored squares
USE_DICE_SPRITES = True

GET_ROBBED = 7
