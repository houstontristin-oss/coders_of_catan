"""
Catan view and other view constants subtracting dev card view
All magic numbers, colors, paths, costs, and configuration.
Every other file imports from here.
"""
from .constants import TEXT_WHITE, TEXT_GOLD, SCREEN_WIDTH, SCREEN_HEIGHT

# CatanView layout / HUD
CATAN_BTN_W = 120
CATAN_BTN_H = 38
CATAN_BTN_GAP = 8
CATAN_BTN_PAD = 14
CATAN_END_BTN_W = 130

CATAN_BUILD_SUBMENU_W = CATAN_BTN_W
CATAN_BUILD_SUBMENU_H = 120
CATAN_BUILD_SUBMENU_Y_OFFSET = 4
CATAN_BUILD_SUBMENU_BTN_INSET = 8
CATAN_BUILD_SUBMENU_BTN_H = 28
CATAN_BUILD_SUBMENU_ROW_STEP = 36

CATAN_CONFIRM_POPUP_W = 160
CATAN_CONFIRM_POPUP_H = 70
CATAN_CONFIRM_BTN_W = 66
CATAN_CONFIRM_BTN_H = 30
CATAN_CONFIRM_Y_OFFSET = 18
CATAN_CONFIRM_TITLE_Y_PAD = 14
CATAN_CONFIRM_BTN_CENTER_Y = 23
CATAN_CONFIRM_BTN_INSET = 8

CATAN_DICE_BOX_MARGIN = 10
CATAN_DIE_SIZE = 40
CATAN_DIE_GAP = 12
CATAN_DICE_Y_OFFSET = 20
CATAN_DICE_LABEL_TOP_PAD = 16
CATAN_DICE_TOTAL_Y = 7

# Miniboxes displaying total cards
CATAN_PLAYER_PANEL_MARGIN = 8
CATAN_PLAYER_MARKER_RADIUS = 7
CATAN_PLAYER_NAME_Y = 18
CATAN_PLAYER_ROW_H = 24
CATAN_RESOURCE_TEXT_X_OFFSET = 35
CATAN_RESOURCE_ROW_GAP = 8
CATAN_RESOURCE_ICON_X_OFFSET = 14
CATAN_RESOURCE_ICON_Y_OFFSET = 8
CATAN_RESOURCE_ICON_ROW_GAP = 8
CATAN_DEV_CARD_COUNT_Y_OFFSET = 10
CATAN_DEV_CARD_COUNT_COLOR = (180, 120, 255)

CATAN_SUMMARY_BOX_GAP = 8
CATAN_SUMMARY_BOX_W = 68
CATAN_SUMMARY_BOX_H = 74
CATAN_SUMMARY_BOX_TOP_INSET = 2
CATAN_SUMMARY_BOX_COUNT_Y_OFFSET = 18

CATAN_TEXT_SIZE_SUMMARY_LABEL = 10
CATAN_TEXT_SIZE_SUMMARY_COUNT = 16

CATAN_COLOR_SUMMARY_BG = (20, 20, 40, 220)
CATAN_COLOR_SUMMARY_TEXT = TEXT_WHITE
CATAN_COLOR_SUMMARY_COUNT = TEXT_GOLD

CATAN_TEXT_SIZE_BTN = 12
CATAN_TEXT_SIZE_CARD_BTN = 11
CATAN_TEXT_SIZE_DICE_LABEL = 11
CATAN_TEXT_SIZE_DICE_HINT = 8
CATAN_TEXT_SIZE_DICE_NUM = 18
CATAN_TEXT_SIZE_TOTAL = 9
CATAN_TEXT_SIZE_SUBMENU = 9
CATAN_TEXT_SIZE_POPUP_TITLE = 10
CATAN_TEXT_SIZE_POPUP_BTN = 9
CATAN_TEXT_SIZE_PLAYER_NAME = 12
CATAN_TEXT_SIZE_PLAYER_VP = 10
CATAN_TEXT_SIZE_RESOURCE = 10
CATAN_TEXT_SIZE_FREE_ROADS = 8

CATAN_LABEL_TRADE = "Trade"
CATAN_LABEL_BUILD = "Build"
CATAN_LABEL_DEV_CARDS = "Dev Cards"
CATAN_LABEL_END_TURN = "End Turn"
CATAN_LABEL_DICE_ROLL = "Dice Roll"
CATAN_LABEL_DICE_HINT = "Auto-rolls on turn start"
CATAN_LABEL_CANCEL = "Cancel"
CATAN_LABEL_CITY = "City"
CATAN_LABEL_SETTLEMENT = "Settlement"
CATAN_LABEL_ROAD = "Road"

CATAN_COLOR_DROP_SHADOW = (0, 0, 0, 100)
CATAN_COLOR_BTN_OUTLINE = (255, 255, 255, 60)
CATAN_COLOR_DISABLED = (70, 70, 70)
CATAN_COLOR_CITY_BTN = (255, 102, 0)
CATAN_COLOR_SETTLEMENT_BTN = (39, 174, 96)
CATAN_COLOR_ROAD_BTN = (52, 152, 219)
CATAN_COLOR_POPUP_BG = (20, 20, 40, 220)
CATAN_COLOR_POPUP_CANCEL = (180, 50, 50)
CATAN_COLOR_POPUP_NO_RES = (80, 80, 80)
CATAN_COLOR_FREE_ROADS = (100, 255, 100)
CATAN_COLOR_DIE_BG = (248, 248, 248)
CATAN_COLOR_DIE_FALLBACK = (60, 60, 90)
CATAN_COLOR_SHAKE_OUTLINE = (255, 215, 0)
CATAN_COLOR_GHOST_FILL = (255, 255, 255, 60)
CATAN_COLOR_GHOST_OUTLINE = (255, 255, 255, 120)
CATAN_COLOR_PORT_HOVER_OUTER = (255, 215, 0, 55)
CATAN_COLOR_PORT_HOVER_INNER = (255, 215, 0, 120)

CATAN_HIGHLIGHT_RADIUS_HOVER = 12
CATAN_HIGHLIGHT_RADIUS_OUTLINE = 14
CATAN_HIGHLIGHT_RADIUS_IDLE = 8
CATAN_EDGE_HIGHLIGHT_WIDTH = 6
CATAN_EDGE_IDLE_WIDTH = 3
CATAN_EDGE_HOVER_DOT_RADIUS = 7
CATAN_PORT_HOVER_OUTER_RADIUS = 16
CATAN_PORT_HOVER_INNER_RADIUS = 11
CATAN_PORT_HOVER_OUTLINE_RADIUS = 12

CATAN_BOARD_TOP_CULL_Y = 10
CATAN_HUD_LEFT_BLOCK_PAD = 5
CATAN_DICE_RIGHT_BLOCK_PAD = 15

CATAN_SETTLEMENT_DRAW_SIZE = 14
CATAN_CITY_DRAW_SIZE = 18
CATAN_ROBBER_SCALE_MULT = 1.1

# ===========================================================================
# StartView constants
# ===========================================================================

# Skip button (bottom-right corner)
START_SKIP_BTN_W  = 220
START_SKIP_BTN_H  = 46
START_SKIP_BTN_X  = SCREEN_WIDTH  - START_SKIP_BTN_W - 20   # left edge
START_SKIP_BTN_Y  = 20                                        # bottom edge

# ---------------------------------------------------------------------------
# Sun — slightly right of center, sitting in the upper sky
START_SUN_X           = SCREEN_WIDTH  * 0.65
START_SUN_Y           = SCREEN_HEIGHT * 0.80
START_SUN_RADIUS      = 52
START_SUN_GLOW_RADIUS = 90
START_SUN_COLOR       = (255, 230, 120)        # warm golden-white disc
START_SUN_GLOW_COLOR  = (255, 180, 60, 90)     # amber haze
START_SUN_RAY_COUNT   = 16
START_SUN_RAY_LEN     = 38                     # extra length added to inner radius
START_SUN_RAY_WIDTH   = 2
START_SUN_RAY_COLOR   = (255, 220, 100, 160)

# ---------------------------------------------------------------------------
# Sunset gradient bands — listed bottom to top (bottom_frac, top_frac, RGBA)
# Gives a warm orange-red-peach-yellow sky.
START_GRAD_BANDS = [
    (0.00, 0.10, (130,  40,  10, 255)),   # deep red-brown near the ground
    (0.08, 0.25, (190,  70,  20, 255)),   # burnt orange
    (0.22, 0.42, (230, 110,  40, 255)),   # rich orange
    (0.38, 0.58, (245, 150,  60, 255)),   # warm orange
    (0.54, 0.70, (250, 185,  80, 255)),   # golden amber
    (0.66, 0.80, (252, 210, 110, 255)),   # pale gold
    (0.76, 0.90, (253, 225, 145, 255)),   # warm cream-yellow
    (0.86, 1.00, (200, 130,  80, 255)),   # dusty rose at horizon top
]

# ---------------------------------------------------------------------------
# Title text
START_TITLE_Y          = SCREEN_HEIGHT * 0.82
START_TITLE_FONT_SIZE  = 52
START_SUBTITLE_Y       = SCREEN_HEIGHT * 0.74
START_SUBTITLE_FONT_SIZE = 16

# ---------------------------------------------------------------------------
# Farmscape — everything below this y-fraction belongs to the farm
START_FARM_HORIZON_Y       = SCREEN_HEIGHT * 0.40   # horizon divides sky & land

# Ground / field tones (RGBA)
START_FARM_FIELD_COLOR      = (100, 145,  55, 250)   # mid-green pasture
START_FARM_FIELD_DARK_COLOR = ( 65, 100,  35, 250)   # deeper shadow grass

# Tree canopy tones
START_FARM_TREE_COLOR       = ( 80, 140,  50, 255)   # leafy mid-green
START_FARM_TREE_DARK_COLOR  = ( 50,  95,  30, 255)   # deep forest shadow

# Silo tones
START_FARM_SILO_COLOR       = (210, 200, 180, 254)   # pale concrete
START_FARM_SILO_DARK_COLOR  = (140, 120,  90, 255)   # weathered shadow

# Barn tones
START_FARM_BARN_COLOR       = (180,  45,  30, 255)   # classic red barn
START_FARM_BARN_DARK_COLOR  = ( 90,  20,  10, 255)   # dark timber trim
START_FARM_ROOF_COLOR       = ( 70,  50,  35, 255)   # dark shingle roof

# Cloud tones (warm peachy-white for sunset)
START_FARM_CLOUD_COLOR      = (255, 205, 160, 80)    # warm peach cloud tint

# ---------------------------------------------------------------------------
# Horizon water
START_WATER_TOP_Y            = START_FARM_HORIZON_Y * 0.88
START_WATER_BOTTOM_Y         = START_FARM_HORIZON_Y * 0.62
START_WATER_COLOR            = (72, 132, 190, 150)
START_WATER_DARK_COLOR       = (48, 96, 145, 165)
START_WATER_FOAM_COLOR       = (240, 250, 255, 95)
START_WATER_WAVE_COUNT       = 4
START_WATER_WAVE_AMPLITUDE   = 5
START_WATER_WAVE_SPACING     = 12
START_WATER_WAVE_THICKNESS   = 2

# ---------------------------------------------------------------------------
# Sheep
START_SHEEP_X_FRAC           = 0.72
START_SHEEP_Y_FRAC           = 0.18
START_SHEEP_BODY_COLOR       = (244, 239, 230, 245)
START_SHEEP_WOOL_SHADOW      = (220, 212, 198, 220)
START_SHEEP_FACE_COLOR       = (82, 70, 58, 245)
START_SHEEP_LEG_COLOR        = (70, 56, 44, 245)

START_SHADOW_COLOR = (45, 25, 10, 70)
START_SHADOW_X_OFFSET = -8
START_SHADOW_Y_OFFSET = -8
START_SHADOW_Y_SCALE = 0.35

# Longest Road and Largest Army Constants
CARD_SCALE = 0.25
ARMY_ROAD_SPRITE_X = SCREEN_WIDTH - 70
ARMY_ROAD_SPRITE_Y1 = SCREEN_HEIGHT / 2 + 150
ARMY_ROAD_SPRITE_Y2 = SCREEN_HEIGHT / 2

ROADS_NEEDED = 5
LONGEST_ROAD_VP = 2

# StartView mute button
START_MUTE_BTN_W = 48
START_MUTE_BTN_H = 48
START_MUTE_BTN_X = 20
START_MUTE_BTN_Y = 20

# Board-view mute button
CATAN_MUTE_BTN_W = 42
CATAN_MUTE_BTN_H = 42
CATAN_MUTE_BTN_PAD = 10
