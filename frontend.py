import arcade
import math
import os
import pyglet
from backend.Player import Player
from backend.catan_board import CatanBoard

# TODO: Render 9 randomized ports around the board perimeter, visually correct, future-ready for backend trade logic.  This needs to be implemented in a way to ensure that im not stepping on the toes of those who are working on backend.py, main.py, and player.py
#   This should safely implement our port system without overwriting other existing systems or changing how the already coded game functions.  This is just a display of the ports, which should be ready for future implementation of the port logic
#   Ports must render:
#   1)  After tiles 2)  Before placed roads/settlements 3)  Ship sprites via SpriteList 4)  Text labels via pre-built Text objects
#   Store visual + future logical representation.
#   Do NOT implement trading logic yet.
#   Detect Coastline Edges (Compatible With Current Backend)
#   Use node tile counts (since Edge has no .tiles).  (IF THIS WORKS BEST)
#   Coastline rule:  if any(len(node.tiles) < 3 for node in edge_obj.nodes)
#   This defines boundary edges using existing backend structure.
#   Evenly Space 9 Ports  -  Steps:  Collect coastline edges.  For each, compute midpoint angle from board center:
#   angle = math.atan2(my - BOARD_CENTER_Y, mx - BOARD_CENTER_X)    -   Sort by angle ascending.
#   Select 9 evenly spaced edges:  step = len(outer_edges) / 9
#   selected = [outer_edges[round(i * step) % len(outer_edges)] for i in range(9)]
#   Randomize Port Types
#   Distribution must be:  5 × resource ports (brick, ore, wheat, sheep, forest)  -   4 × generic (None)
#   Align Ship Sprites Correctly
#   Ships must: 1) Align parallel to coast edge 2) Sit slightly in ocean  3) Face along edge direction
#   Create Text Labels
#   Label rule: label = f"2:1 {RESOURCE_ABBR[resource]}" if resource else "3:1"
#   Use prebuilt arcade.Text objects.   Font:  MedievalSharp
#   Bold,  TEXT_GOLD (Or whatever contrasts best with blue), Anchor center, text 12 size font
#

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Window Size  -  Trying to make it wider not taller for laptops
# ---------------------------------------------------------------------------
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 680
SCREEN_TITLE  = "Coders of Catan"

# ---------------------------------------------------------------------------
# Background image
# Change this filename to swap backgrounds — file must live in sprites/background/
# ---------------------------------------------------------------------------
BACKGROUND_IMAGE = os.path.join(BASE_DIR, "sprites", "background", "ocean_background.png")

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
    "brick":  "Brick",
    "ore":    "Ore",
    "wheat":  "Wheat",
    "sheep":  "Sheep",
    "forest": "Wood",
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

# ---------------------------------------------------------------------------
# Costs
# ---------------------------------------------------------------------------
SETTLEMENT_COST = {"BRICK": 1, "WOOD": 1, "WHEAT": 1, "SHEEP": 1}
ROAD_COST       = {"BRICK": 1, "WOOD": 1}

# Snap radii (pixels)
NODE_SNAP_RADIUS = 18
EDGE_SNAP_RADIUS = 14

# ---------------------------------------------------------------------------
# Placeholder players
# ---------------------------------------------------------------------------
PLAYERS = [
    {"name": "Player 1", "color": (231, 76,  60),  "resources": {"brick": 2, "ore": 0, "wheat": 1, "sheep": 1, "forest": 2}, "vp": 0},
    {"name": "Player 2", "color": (39,  174, 96),  "resources": {"brick": 2, "ore": 0, "wheat": 1, "sheep": 1, "forest": 2}, "vp": 0},
    {"name": "Player 3", "color": (219, 118, 51),  "resources": {"brick": 2, "ore": 0, "wheat": 1, "sheep": 1, "forest": 2}, "vp": 0},
    {"name": "Player 4", "color": (142, 68,  173), "resources": {"brick": 2, "ore": 0, "wheat": 1, "sheep": 1, "forest": 2}, "vp": 0},
]

PLAYERS_TWO = [
    Player((231, 76,  60), "Player 1"),
    Player((39, 174, 96), "Player 2"),
    Player((219, 118, 51), "Player 3"),
    Player((142, 68, 173), "Player 4"),
]

# ===========================================================================
# Coordinate helpers
# ===========================================================================
def cubic_to_pixel(cx, cz, hex_size=HEX_SIZE, origin_x=BOARD_CENTER_X, origin_y=BOARD_CENTER_Y):
    px = origin_x + hex_size * (3 / 2) * cx
    py = origin_y + hex_size * (math.sqrt(3) / 2 * cx + math.sqrt(3) * cz)
    return px, py

def node_to_pixel(node_id, hex_size=HEX_SIZE, origin_x=BOARD_CENTER_X, origin_y=BOARD_CENTER_Y):
    fx, fy, fz = node_id
    px = origin_x + hex_size * (3 / 2) * fx
    py = origin_y + hex_size * (math.sqrt(3) / 2 * fx + math.sqrt(3) * fz)
    return px, py

def get_hex_corners(center_x, center_y, size):
    corners = []
    for i in range(6):
        angle_rad = math.radians(60 * i)
        corners.append((center_x + size * math.cos(angle_rad),
                         center_y + size * math.sin(angle_rad)))
    return corners


# ===========================================================================
# Shape / drawing helpers
# ===========================================================================
def draw_settlement(cx, cy, size, color):
    half = size / 2
    pts  = [(cx-half, cy-half), (cx+half, cy-half),
            (cx+half, cy+half), (cx-half, cy+half)]
    arcade.draw_polygon_filled(pts, color)
    arcade.draw_polygon_outline(pts, arcade.color.BLACK, 2)

def draw_road(x1, y1, x2, y2, color, width=6):
    arcade.draw_line(x1, y1, x2, y2, arcade.color.WHITE, width + 4)
    arcade.draw_line(x1, y1, x2, y2, arcade.color.BLACK, width + 2)
    arcade.draw_line(x1, y1, x2, y2, color, width)

def draw_number_token(cx, cy, number):
    """Draw a classic Catan number token — cream circle with number inside.
    6 and 8 are drawn in red (high-probability numbers)."""
    is_hot   = number in (6, 8)
    bg_color = (240, 220, 170)          # cream
    txt_col  = TOKEN_RED if is_hot else (20, 20, 20)
    radius   = 14

    arcade.draw_circle_filled(cx, cy, radius, bg_color)
    arcade.draw_circle_outline(cx, cy, radius, (100, 80, 40), 2)

    # Probability dots below the number (pips)
    # Standard Catan pip counts: 2→1, 3→2, 4→3, 5→4, 6→5, 8→5, 9→4, 10→3, 11→2, 12→1
    pip_map = {2:1, 3:2, 4:3, 5:4, 6:5, 8:5, 9:4, 10:3, 11:2, 12:1}
    pips    = pip_map.get(number, 0)
    pip_r   = 1.5
    pip_gap = 4
    pip_total_w = pips * (pip_r * 2) + (pips - 1) * (pip_gap - pip_r * 2)
    pip_start_x = cx - pip_total_w / 2 + pip_r

    for i in range(pips):
        px = pip_start_x + i * pip_gap
        arcade.draw_circle_filled(px, cy - 7, pip_r, txt_col)

    arcade.Text(
        str(number),
        cx, cy + 2,
        txt_col, 11,
        bold=True,
        anchor_x="center", anchor_y="center",
        font_name="MedievalSharp"
    ).draw()

def fill_rect(left, bottom, width, height, color):
    arcade.draw_lrbt_rectangle_filled(left, left + width, bottom, bottom + height, color)

def outline_rect(left, bottom, width, height, color, border=2):
    arcade.draw_lrbt_rectangle_outline(left, left + width, bottom, bottom + height, color, border)

def draw_port_label(label_x, label_y, label):
    """Port label with a dark pill background so it's always legible."""
    font_size = 13
    pad_x     = 10
    pad_y     = 6
    text_w    = len(label) * 8 + pad_x * 2
    text_h    = font_size + pad_y * 2
    left      = label_x - text_w / 2
    bottom    = label_y - text_h / 2

    arcade.draw_lrbt_rectangle_filled(left, left + text_w, bottom, bottom + text_h, (10, 10, 30, 230))
    arcade.draw_lrbt_rectangle_outline(left, left + text_w, bottom, bottom + text_h, TEXT_GOLD, 1)
    arcade.Text(
        label,
        label_x, label_y,
        (15, 40, 90, 255), font_size,   # dark navy — high contrast on light blue
        bold=True,
        anchor_x="center", anchor_y="center",
        font_name="MedievalSharp"
    ).draw()

def draw_board(board):
    for xyz, tile in board.tiles.items():
            cx, cy, cz = xyz
            px, py = cubic_to_pixel(cx, cz, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
            corners = get_hex_corners(px, py, HEX_SIZE)
            arcade.draw_polygon_filled(corners, RESOURCE_COLORS[tile.resource])
            arcade.draw_polygon_outline(corners, arcade.color.BLACK, 2)

# ---------------------------------------------------------------------------
# Start View
# ---------------------------------------------------------------------------
class StartView(arcade.View):
    def on_show_view(self):
        self._build_text_objects()

    def _build_text_objects(self):
        #TODO: set the title to be in the middle of the screen
        self.txt_title = arcade.Text("Welcome to Catan!", SCREEN_WIDTH / 2, SCREEN_HEIGHT/2, font_size=30, bold=True, font_name="MedievalSharp")
        self.txt_instructions = arcade.Text("Click anywhere to begin!", SCREEN_WIDTH / 2, SCREEN_HEIGHT/2 - 100, font_size=20, font_name="MedievalSharp")

    def on_draw(self):
        self.clear()
        self.txt_title.draw()
        self.txt_instructions.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        # TODO: add buttons here for selection of number of players
        self.board = CatanBoard()
        self.board.make_board()
        # TODO: create players here
        self.players = PLAYERS
        # show setupview starting with player at index 0 and round 1 of play
        self.window.show_view(SetupView(self.board, self.players, 0, 1))


# ---------------------------------------------------------------------------
# Main View
# ---------------------------------------------------------------------------
class CatanView(arcade.View):
    def __init__(self, board, players, current_player):
        super().__init__()
        self.board = board
        self.players = players
        # Track whose turn it is (index into PLAYERS list)
        self.current_player = current_player

        # Build mode state
        self.build_mode    = False
        self.build_choice  = BUILD_NONE
        self.hovered_node  = None
        self.hovered_edge  = None
        self.selected_node = None
        self.selected_edge = None
        self.show_confirm  = False

        # Pixel caches (populated after make_board)
        self._node_pixel_cache = {}
        self._edge_pixel_cache = {}
        self._port_render_data = []   # list of (ship_x, ship_y, angle, label)
        self.txt_port_labels = []

        # Load background
        self._load_background()

        # Load HUD icons and ship sprite
    def on_show_view(self):        
        # --- Pre-build all Text objects (avoids draw_text performance warning) ---
        self._build_text_objects()

        # --- Load resource icon sprites ---
        self._load_resource_icons()
        self._load_port_sprite()

        # Build the board (number tokens assigned inside)
        self._assign_number_tokens()

        # Build pixel caches
        self._build_node_pixel_cache()
        self._build_edge_pixel_cache()
        self._build_port_render_data()

        # Build HUD text objects last (needs board to be ready)
        self._build_text_objects()

    # -----------------------------------------------------------------------
    # Background
    # -----------------------------------------------------------------------
    def _load_background(self):
        """Load the background image, or fall back to a solid color."""
        try:
            self.bg_sprite = arcade.Sprite(BACKGROUND_IMAGE)
            self.bg_sprite.center_x = SCREEN_WIDTH  / 2
            self.bg_sprite.center_y = SCREEN_HEIGHT / 2
            # Scale to fill the window exactly
            scale_x = SCREEN_WIDTH  / self.bg_sprite.width
            scale_y = SCREEN_HEIGHT / self.bg_sprite.height
            self.bg_sprite.scale = max(scale_x, scale_y)
            self.bg_list = arcade.SpriteList()
            self.bg_list.append(self.bg_sprite)
        except Exception:
            self.bg_sprite = None
            self.bg_list   = None
            arcade.set_background_color(arcade.color.OCEAN_BOAT_BLUE)

    # -----------------------------------------------------------------------
    # Number token assignment
    # -----------------------------------------------------------------------
    def _assign_number_tokens(self):
        """
        Assign the official Catan number pool to non-desert tiles.
        The pool is already shuffled in make_board() alongside resources,
        but we need to attach the numbers to tile objects here so the
        frontend can read them for rendering.

        Because make_board() already assigns tile.number (0 for desert,
        random draw for others), we just need to verify desert tiles have 0
        and all others have a valid number.  Nothing extra needed here —
        we read tile.number directly in on_draw().
        """
        pass   # tile.number is already set by backend.make_board()

    # -----------------------------------------------------------------------
    # Port rendering data
    # -----------------------------------------------------------------------
    def _build_port_render_data(self):
        """
        Find all outer edges (edges where at least one endpoint node touches
        only 1 tile — meaning it's on the board boundary), sort them
        clockwise by angle from board center, pick 9 evenly-spaced ones,
        and assign port types to them.
        """
        self._port_render_data = []

        # --- Step 1: find all outer edges ---
        outer_edges = []
        for edge_id, edge_obj in self.board.edges.items():
            # An outer edge has at least one node that touches only 1 tile
            if any(len(n.tiles) < 3 for n in edge_obj.nodes):
                mx, my, x1, y1, x2, y2 = self._edge_pixel_cache[edge_id]
                # Compute angle of midpoint from board center
                dx = mx - BOARD_CENTER_X
                dy = my - BOARD_CENTER_Y
                angle_from_center = math.atan2(dy, dx)
                outer_edges.append((angle_from_center, mx, my, x1, y1, x2, y2))

        # --- Step 2: sort clockwise from top (top = angle pi/2, going clockwise) ---
        # atan2 goes counter-clockwise, so we negate and offset to start at top
        outer_edges.sort(key=lambda e: (-(e[0] - math.pi/2)) % (2 * math.pi))

        # --- Step 3: pick 9 evenly-spaced edges from the sorted outer ring ---
        total      = len(outer_edges)
        step       = total / 9
        port_edges = [outer_edges[round(i * step) % total] for i in range(9)]

        # --- Step 4: build render data ---
        for i, (angle_from_center, mx, my, x1, y1, x2, y2) in enumerate(port_edges):
            resource = PORT_TYPES[i]
            label    = f"2:1 {RESOURCE_ABBR[resource]}" if resource else "3:1"

            # Push ship outward into the water past the tile edge
            dx   = mx - BOARD_CENTER_X
            dy   = my - BOARD_CENTER_Y
            dist = math.hypot(dx, dy) or 1
            norm_x = dx / dist
            norm_y = dy / dist

            ship_x = mx + norm_x * (HEX_SIZE * 0.65)
            ship_y = my + norm_y * (HEX_SIZE * 0.65)

            label_x = mx + norm_x * (HEX_SIZE * 1.1)
            label_y = my + norm_y * (HEX_SIZE * 1.1)

            # Sprite angle: face inward toward the board center
            # atan2(dy,dx) gives angle of outward direction from board center.
            # Arcade rotates counter-clockwise from "right", so subtract 90 to align top.
            sprite_angle = math.degrees(math.atan2(dy, dx)) - 90
            self._port_render_data.append((ship_x, ship_y, sprite_angle, label, label_x, label_y))

            # Pre-build Text object for this port label (avoids draw_text perf warning)
            self.txt_port_labels.append(
                arcade.Text(
                    label,
                    label_x, label_y,
                    (15, 40, 90, 255), 13,
                    bold=True,
                    anchor_x="center", anchor_y="center",
                    font_name="MedievalSharp"
                )
            )

            # Add sprite to SpriteList once at init (Arcade 3.x requirement)
            if self._ship_ok:
                ship = arcade.Sprite(PORT_SHIP_SPRITE, scale=0.07)
                ship.center_x = ship_x
                ship.center_y = ship_y
                ship.angle    = sprite_angle
                self.port_sprite_list.append(ship)

    # -----------------------------------------------------------------------
    # Caches
    # -----------------------------------------------------------------------
    def _build_node_pixel_cache(self):
        for node_id in self.board.nodes:
            px, py = node_to_pixel(node_id)
            self._node_pixel_cache[node_id] = (px, py)

    def _build_edge_pixel_cache(self):
        for edge_id in self.board.edges:
            n1_id, n2_id = edge_id
            x1, y1 = self._node_pixel_cache[n1_id]
            x2, y2 = self._node_pixel_cache[n2_id]
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            self._edge_pixel_cache[edge_id] = (mx, my, x1, y1, x2, y2)

    # -----------------------------------------------------------------------
    # Sprites
    # -----------------------------------------------------------------------
    def _load_resource_icons(self):
        self.resource_icons   = {}
        self.icon_sprite_list = arcade.SpriteList()
        for res in ["brick", "ore", "wheat", "sheep", "forest"]:
            sprite = arcade.Sprite(RESOURCE_SPRITES[res], scale=SPRITE_SCALE)
            self.resource_icons[res] = sprite
            self.icon_sprite_list.append(sprite)

    def _load_port_sprite(self):
        """
        Try to load the ship image.  Actual sprites are added to the
        SpriteList in _build_port_render_data() once port positions are known.
        """
        self.port_sprite_list = arcade.SpriteList()
        try:
            _test = arcade.Sprite(PORT_SHIP_SPRITE, scale=0.07)
            self._ship_ok = True
        except Exception:
            self._ship_ok = False

    # -----------------------------------------------------------------------
    # Text objects
    # -----------------------------------------------------------------------
    def _build_text_objects(self):
        bar_cy  = HUD_BOTTOM_HEIGHT / 2
        btn_w   = 130
        gap     = 15
        total_w = 3 * btn_w + 2 * gap
        sx      = (SCREEN_WIDTH - total_w) / 2

        self.txt_trade = arcade.Text("Trade",     sx+btn_w*0.5,           bar_cy, TEXT_WHITE, 12, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_build = arcade.Text("Build",     sx+btn_w*1.5+gap,       bar_cy, TEXT_WHITE, 12, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_card  = arcade.Text("Play Card", sx+btn_w*2.5+gap*2,     bar_cy, TEXT_WHITE, 12, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_end   = arcade.Text("End Turn",  SCREEN_WIDTH-btn_w*0.5-15, bar_cy, TEXT_WHITE, 12, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")

        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - 10
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - 10
        self.txt_dice_label = arcade.Text("Dice Roll",               dx+DICE_AREA_WIDTH/2, dy+DICE_AREA_HEIGHT-16, TEXT_GOLD,      11, bold=True, anchor_x="center", font_name="MedievalSharp")
        self.txt_dice_hint  = arcade.Text("Auto-rolls on turn start",dx+DICE_AREA_WIDTH/2, dy+7,                  TEXT_LIGHT_GRAY, 8,             anchor_x="center", font_name="MedievalSharp")
        self.txt_die1       = arcade.Text("?", dx+(DICE_AREA_WIDTH-2*40-12)/2+20,     dy+22+20, TEXT_WHITE, 18, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_die2       = arcade.Text("?", dx+(DICE_AREA_WIDTH-2*40-12)/2+20+54,  dy+22+20, TEXT_WHITE, 18, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")

        # Build submenu labels (x/y updated at draw time via .x / .y)
        self.txt_submenu_settlement = arcade.Text("Settlement", 0, 0, TEXT_WHITE, 9, bold=True,
                                                   anchor_x="center", anchor_y="center",
                                                   font_name="MedievalSharp")
        self.txt_submenu_road       = arcade.Text("Road",       0, 0, TEXT_WHITE, 9, bold=True,
                                                   anchor_x="center", anchor_y="center",
                                                   font_name="MedievalSharp")

        # Confirm popup labels
        self.txt_popup_title   = arcade.Text("", 0, 0, TEXT_GOLD,  10, bold=True,
                                              anchor_x="center", anchor_y="center",
                                              font_name="MedievalSharp")
        self.txt_popup_confirm = arcade.Text("", 0, 0, TEXT_WHITE,  9, bold=True,
                                              anchor_x="center", anchor_y="center",
                                              font_name="MedievalSharp")
        self.txt_popup_cancel  = arcade.Text("Cancel", 0, 0, TEXT_WHITE, 9, bold=True,
                                              anchor_x="center", anchor_y="center",
                                              font_name="MedievalSharp")

        # Port labels (rebuilt when port data changes)
        self.txt_port_labels = []

        self._build_player_texts()

    def _build_player_texts(self):
        """
        Build/rebuild Text objects for the current player panel.
        Called on init and every time _end_turn() fires.
        """
        player = PLAYERS_TWO[self.current_player] #Single-column player info panel.

        player    = PLAYERS_TWO[self.current_player]
        panel_x   = 8
        panel_top = SCREEN_HEIGHT - 8   # top of panel in screen coords
        row_h     = 24                  # vertical spacing per row

        # Name
        self.txt_player_name = arcade.Text(
            player.name,
            panel_x + HUD_PANEL_WIDTH // 2,
            panel_top - 18,
            TEXT_GOLD, 12, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp"
        )
        # VP
        self.txt_player_vp = arcade.Text(
            f"Victory Points: {player.victory_points}",
            panel_x + HUD_PANEL_WIDTH // 2 + 10,
            panel_top - 18 - row_h,
            TEXT_LIGHT_GRAY, 10,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp"
        )

        # Resources — single column, icon + "Label: N" per row
        order  = ["BRICK", "ORE", "WHEAT", "SHEEP", "WOOD"]
        labels = {"BRICK":"Brick","ORE":"Ore","WHEAT":"Wheat","SHEEP":"Sheep","WOOD":"Wood"}

        self.txt_resources = []
        for i, res in enumerate(order):
            ry = panel_top - 18 - row_h * 2 - i * (ICON_SIZE + 4) - ICON_SIZE // 2
            self.txt_resources.append(
                arcade.Text(
                    f"{labels[res]}: {player.resource_cards.get(res)}",
                    panel_x + ICON_SIZE + 35, ry,
                    TEXT_WHITE, 9,
                    anchor_y="center",
                    font_name="MedievalSharp"
                )
            )

    # -----------------------------------------------------------------------
    # Affordability
    # -----------------------------------------------------------------------
    def _can_afford(self, cost_dict):
        res = PLAYERS_TWO[self.current_player].resource_cards
        return all(res.get(r, 0) >= amt for r, amt in cost_dict.items())

    # -----------------------------------------------------------------------
    # HUD draw helpers
    # -----------------------------------------------------------------------
    def _draw_bottom_bar(self):
        fill_rect(0, 0, SCREEN_WIDTH, HUD_BOTTOM_HEIGHT, HUD_BG)

        btn_w   = 130
        btn_h   = 46
        gap     = 15
        total_w = 3 * btn_w + 2 * gap
        sx      = (SCREEN_WIDTH - total_w) / 2
        btn_bot = (HUD_BOTTOM_HEIGHT - btn_h) / 2

        build_col = BTN_BUILD_ACTIVE if self.build_mode else BTN_BUILD

        fill_rect(sx,                    btn_bot, btn_w, btn_h, BTN_TRADE)
        fill_rect(sx+btn_w+gap,          btn_bot, btn_w, btn_h, build_col)
        fill_rect(sx+2*(btn_w+gap),      btn_bot, btn_w, btn_h, BTN_CARD)
        fill_rect(SCREEN_WIDTH-btn_w-15, btn_bot, btn_w, btn_h, BTN_ENDTURN)

        self.txt_trade.draw()
        self.txt_build.draw()
        self.txt_card.draw()
        self.txt_end.draw()

    def _draw_build_submenu(self):
        if not self.build_mode or self.build_choice != BUILD_NONE:
            return

        btn_w  = 130
        gap    = 15
        sx     = (SCREEN_WIDTH - 3*btn_w - 2*gap) / 2
        bx     = sx + btn_w + gap
        by     = HUD_BOTTOM_HEIGHT
        menu_w = btn_w

        fill_rect(bx, by, menu_w, 80, HUD_PANEL_BG)
        outline_rect(bx, by, menu_w, 80, TEXT_GOLD, 2)

        s_col = (39, 174, 96) if self._can_afford(SETTLEMENT_COST) else (70, 70, 70)
        fill_rect(bx+8, by+44, menu_w-16, 28, s_col)
        self.txt_submenu_settlement.x = bx + menu_w / 2
        self.txt_submenu_settlement.y = by + 58
        self.txt_submenu_settlement.draw()

        r_col = (52, 152, 219) if self._can_afford(ROAD_COST) else (70, 70, 70)
        fill_rect(bx+8, by+8, menu_w-16, 28, r_col)
        self.txt_submenu_road.x = bx + menu_w / 2
        self.txt_submenu_road.y = by + 22
        self.txt_submenu_road.draw()

    def _draw_player_panel(self):
        player = PLAYERS[self.current_player]
        """Slim single-column panel in top-left."""
        player  = PLAYERS_TWO[self.current_player]
        panel_x = 8
        panel_y = SCREEN_HEIGHT - HUD_PANEL_HEIGHT - 8

        fill_rect(panel_x, panel_y, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, HUD_PANEL_BG)
        outline_rect(panel_x, panel_y, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, player.color)

        # Color dot
        arcade.draw_circle_filled(panel_x + 14, panel_y + HUD_PANEL_HEIGHT - 18, 7, player.color)

        self.txt_player_name.draw()
        self.txt_player_vp.draw()

        # Resource icons + labels, single column
        order    = ["brick", "ore", "wheat", "sheep", "forest"]
        panel_top = SCREEN_HEIGHT - 8
        row_h     = 24

        for i, res in enumerate(order):
            ry = panel_top - 25 - row_h * 2 - i * (ICON_SIZE + 5)
            sprite = self.resource_icons[res]
            sprite.center_x = panel_x + ICON_SIZE // 2 + 4
            sprite.center_y = ry

        self.icon_sprite_list.draw()

        for txt in self.txt_resources:
            txt.draw()

    def _draw_dice_area(self):
        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - 10
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - 10

        fill_rect(dx, dy, DICE_AREA_WIDTH, DICE_AREA_HEIGHT, HUD_PANEL_BG)
        outline_rect(dx, dy, DICE_AREA_WIDTH, DICE_AREA_HEIGHT, TEXT_LIGHT_GRAY)

        self.txt_dice_label.draw()
        self.txt_dice_hint.draw()

        die_size = 40
        die_gap  = 12
        die1_x   = dx + (DICE_AREA_WIDTH - 2*die_size - die_gap) / 2
        die_y    = dy + 20

        fill_rect(die1_x,                   die_y, die_size, die_size, (60,60,90))
        fill_rect(die1_x+die_size+die_gap,  die_y, die_size, die_size, (60,60,90))
        self.txt_die1.draw()
        self.txt_die2.draw()

    # -----------------------------------------------------------------------
    # Port drawing
    # -----------------------------------------------------------------------
    def _draw_ports(self):
        # Ship sprites sit on the tile edge — drawn via SpriteList
        if self._ship_ok:
            self.port_sprite_list.draw()

        # Labels drawn via pre-built Text objects (no draw_text performance hit)
        for txt in self.txt_port_labels:
            if not self._ship_ok:
                # fallback dot at ship position stored alongside label
                pass
            txt.draw()

    # -----------------------------------------------------------------------
    # Board pieces (always drawn)
    # -----------------------------------------------------------------------
    def _draw_placed_pieces(self):
        for edge_id, edge_obj in self.board.edges.items():
            if edge_obj.player is not None:
                mx, my, x1, y1, x2, y2 = self._edge_pixel_cache[edge_id]
                draw_road(x1, y1, x2, y2, PLAYERS_TWO[edge_obj.player].color)

        for node_id, node_obj in self.board.nodes.items():
            if node_obj.player is not None:
                npx, npy = self._node_pixel_cache[node_id]
                draw_settlement(npx, npy, 14, PLAYERS_TWO[node_obj.player].color)

    # -----------------------------------------------------------------------
    # Ghost highlights
    # -----------------------------------------------------------------------
    def _draw_node_highlights(self):
        player_color = PLAYERS_TWO[self.current_player].color
        for node_id, node_obj in self.board.nodes.items():
            if node_obj.player is not None:
                continue
            npx, npy = self._node_pixel_cache[node_id]
            if npy < HUD_BOTTOM_HEIGHT + 5:
                continue
            if npx < HUD_PANEL_WIDTH + 5 or npx > SCREEN_WIDTH - DICE_AREA_WIDTH - 15:
                continue
            if node_obj is self.hovered_node:
                arcade.draw_circle_filled(npx, npy, 12, (*player_color, 180))
                arcade.draw_circle_outline(npx, npy, 14, player_color, 3)
            else:
                arcade.draw_circle_filled(npx, npy, 8, (255, 255, 255, 60))
                arcade.draw_circle_outline(npx, npy, 8, (255, 255, 255, 120), 1)

    def _draw_edge_highlights(self):
        player_color = PLAYERS_TWO[self.current_player].color
        for edge_id, edge_obj in self.board.edges.items():
            if edge_obj.player is not None:
                continue
            mx, my, x1, y1, x2, y2 = self._edge_pixel_cache[edge_id]
            if my < HUD_BOTTOM_HEIGHT + 5:
                continue
            if edge_obj is self.hovered_edge:
                arcade.draw_line(x1, y1, x2, y2, (*player_color, 200), 6)
                arcade.draw_circle_filled(mx, my, 7, (*player_color, 220))
            else:
                arcade.draw_line(x1, y1, x2, y2, (255, 255, 255, 50), 3)

    # -----------------------------------------------------------------------
    # Confirmation popup
    # -----------------------------------------------------------------------
    def _draw_confirm_popup(self):
        if not self.show_confirm:
            return
        if self.build_choice == BUILD_SETTLEMENT and self.selected_node:
            cx, cy = self._node_pixel_cache[self.selected_node.node_id]
            cy    += 18
            can    = self._can_afford(SETTLEMENT_COST)
            label  = "Build Settlement?"
        elif self.build_choice == BUILD_ROAD and self.selected_edge:
            mx, my, *_ = self._edge_pixel_cache[self.selected_edge.edge_id]
            cx, cy = mx, my + 18
            can    = self._can_afford(ROAD_COST)
            label  = "Build Road?"
        else:
            return

        popup_w  = 160
        popup_h  = 70
        pop_left = cx - popup_w / 2

        fill_rect(pop_left, cy, popup_w, popup_h, (20, 20, 40, 220))
        outline_rect(pop_left, cy, popup_w, popup_h, TEXT_GOLD, 2)
        self.txt_popup_title.text = label
        self.txt_popup_title.x    = cx
        self.txt_popup_title.y    = cy + popup_h - 14
        self.txt_popup_title.draw()

        btn_col = (39, 174, 96) if can else (80, 80, 80)
        fill_rect(pop_left+8,          cy+8, 66, 30, btn_col)
        self.txt_popup_confirm.text = "Confirm" if can else "No Res."
        self.txt_popup_confirm.x    = pop_left + 41
        self.txt_popup_confirm.y    = cy + 23
        self.txt_popup_confirm.draw()

        fill_rect(pop_left+popup_w-74, cy+8, 66, 30, (180, 50, 50))
        self.txt_popup_cancel.x = pop_left + popup_w - 41
        self.txt_popup_cancel.y = cy + 23
        self.txt_popup_cancel.draw()

    # -----------------------------------------------------------------------
    # on_draw
    # -----------------------------------------------------------------------
    def on_draw(self):
        self.clear()

        # Background
        if self.bg_list:
            self.bg_list.draw()

        # Hex tiles
        for xyz, tile in self.board.tiles.items():
            cx, cy, cz = xyz
            px, py = cubic_to_pixel(cx, cz)
            corners = get_hex_corners(px, py, HEX_SIZE)
            arcade.draw_polygon_filled(corners, RESOURCE_COLORS[tile.resource])
            arcade.draw_polygon_outline(corners, arcade.color.BLACK, 2)

            # Number token (skip desert, which has number=0)
            if tile.number > 0:
                draw_number_token(px, py, tile.number)

        # Ports drawn after tiles — ships sit on outer tile edges, labels clear outward
        self._draw_ports()

        # Ghost highlights
        if self.build_choice == BUILD_SETTLEMENT:
            self._draw_node_highlights()
        elif self.build_choice == BUILD_ROAD:
            self._draw_edge_highlights()

        # Placed pieces
        self._draw_placed_pieces()

        # Confirmation popup
        if self.show_confirm:
            self._draw_confirm_popup()

        # HUD on top of everything
        self._draw_player_panel()
        self._draw_dice_area()
        self._draw_bottom_bar()
        self._draw_build_submenu()

# -----------------------------------------------------------------------
# Mouse motion
# -----------------------------------------------------------------------
    def on_mouse_motion(self, x, y, dx, dy):
        if self.show_confirm:
            return
        if self.build_choice == BUILD_SETTLEMENT:
            closest, closest_dist = None, float("inf")
            for node_id, (npx, npy) in self._node_pixel_cache.items():
                d = math.hypot(x-npx, y-npy)
                if d < NODE_SNAP_RADIUS and d < closest_dist:
                    node = self.board.nodes[node_id]
                    if node.player is None:
                        closest, closest_dist = node, d
            self.hovered_node = closest
        elif self.build_choice == BUILD_ROAD:
            closest, closest_dist = None, float("inf")
            for edge_id, (mx, my, *_) in self._edge_pixel_cache.items():
                d = math.hypot(x-mx, y-my)
                if d < EDGE_SNAP_RADIUS and d < closest_dist:
                    edge = self.board.edges[edge_id]
                    if edge.player is None:
                        closest, closest_dist = edge, d
            self.hovered_edge = closest

    def on_mouse_press(self, x, y, button, modifiers):
        """
        Skeleton click handler.
        TODO: Apoorva will flesh out node/edge detection here.
        TODO: Wire End Turn button to Amanda's turn logic.
        """
        btn_w = 150
        gap = 20
        total_w = 3 * btn_w + 2 * gap
        sx = (SCREEN_WIDTH - total_w) / 2
        # End Turn
        if (SCREEN_WIDTH-btn_w-15 <= x <= SCREEN_WIDTH-15) and (y <= HUD_BOTTOM_HEIGHT):
            self._end_turn()
            return

        # Build button
        build_left = sx + btn_w + gap
        if (build_left <= x <= build_left + btn_w) and (y <= HUD_BOTTOM_HEIGHT):
            if self.build_mode:
                self._cancel_build()
            else:
                self.build_mode   = True
                self.build_choice = BUILD_NONE
            return

        # Sub-menu
        if self.build_mode and self.build_choice == BUILD_NONE:
            bx     = sx + btn_w + gap
            by     = HUD_BOTTOM_HEIGHT
            menu_w = btn_w
            if (bx+8 <= x <= bx+menu_w-8) and (by+44 <= y <= by+72):
                if self._can_afford(SETTLEMENT_COST):
                    self.build_choice = BUILD_SETTLEMENT
                return
            if (bx+8 <= x <= bx+menu_w-8) and (by+8 <= y <= by+36):
                if self._can_afford(ROAD_COST):
                    self.build_choice = BUILD_ROAD
                return

        # Confirmation popup
        if self.show_confirm:
            if self.build_choice == BUILD_SETTLEMENT and self.selected_node:
                pcx, pcy = self._node_pixel_cache[self.selected_node.node_id]
                pcy     += 18
            elif self.build_choice == BUILD_ROAD and self.selected_edge:
                mx, my, *_ = self._edge_pixel_cache[self.selected_edge.edge_id]
                pcx, pcy   = mx, my + 18
            else:
                self.show_confirm = False
                return

            popup_w  = 160
            pop_left = pcx - popup_w / 2

            if (pop_left+8 <= x <= pop_left+74) and (pcy+8 <= y <= pcy+38):
                if self.build_choice == BUILD_SETTLEMENT and self._can_afford(SETTLEMENT_COST):
                    self._place_settlement(self.selected_node)
                elif self.build_choice == BUILD_ROAD and self._can_afford(ROAD_COST):
                    self._place_road(self.selected_edge)
                return
            if (pop_left+popup_w-74 <= x <= pop_left+popup_w-8) and (pcy+8 <= y <= pcy+38):
                self.selected_node = None
                self.selected_edge = None
                self.show_confirm  = False
                return
            self.selected_node = None
            self.selected_edge = None
            self.show_confirm  = False
            return

        if self.build_choice == BUILD_SETTLEMENT and self.hovered_node:
            self.selected_node = self.hovered_node
            self.show_confirm  = True
            return
        if self.build_choice == BUILD_ROAD and self.hovered_edge:
            self.selected_edge = self.hovered_edge
            self.show_confirm  = True
            return
        #Trade View
        if (sx <= x <= sx + btn_w) and (y <= HUD_BOTTOM_HEIGHT):
            self.window.show_view(TradeView(self.board, self.players, self.current_player))
        #Play Card View
        if (sx + 2*(btn_w + gap) <= x <= sx + 2*(btn_w + gap) + btn_w) and (y <= HUD_BOTTOM_HEIGHT):
            self.window.show_view(PlayCardView(self.board, self.players, self.current_player))
    # -----------------------------------------------------------------------
    # Placement
    # -----------------------------------------------------------------------
    def _place_settlement(self, node):
        player = PLAYERS_TWO[self.current_player]
        player.build_settlement(CatanBoard, node)
        node.player = self.current_player
        node.building = "settlement"
        player.victory_points += 1
        self._cancel_build()
        self._build_player_texts()
        print(f"{player.name} built a settlement! Victory Points: {player.victory_points}")

       # player = PLAYERS[self.current_player]
       # for res, amt in SETTLEMENT_COST.items():
      #      player["resources"][res] -= amt
      #  node.player   = self.current_player
      #  node.building = "settlement"
       # player["vp"] += 1
       # self._cancel_build()
        #self._build_player_texts()
       # print(f"{player['name']} built a settlement! Victory Points: {player['vp']}")

    def _place_road(self, edge):
        player = PLAYERS_TWO[self.current_player]
        idx = self.current_player
        connected = False
        for node in edge.nodes:
            if node.player == idx:
                connected = True
                break
            for neighbor_edge in node.edges:
                if neighbor_edge is not edge and neighbor_edge.player == idx:
                    connected = True
                    break
            if connected:
                break
        if not connected:
            print(f"{player.name} — road must connect to your settlement or existing road.")
            self.show_confirm = False
            self.selected_edge = None
            return
        player.build_road(CatanBoard, edge)
        edge.player = self.current_player
        self._cancel_build()
        self._build_player_texts()
        print(f"{player.name} built a road!")

        #player = PLAYERS[self.current_player]
       # idx    = self.current_player
       # connected = False
       # for node in edge.nodes:
       #     if node.player == idx:
       #         connected = True
        #        break
        #    for neighbour_edge in node.edges:
        #        if neighbour_edge is not edge and neighbour_edge.player == idx:
         #           connected = True
         #           break
         #   if connected:
          #      break
       # if not connected:
           # print(f"{player['name']} — road must connect to your settlement or existing road.")
           # self.show_confirm  = False
           # self.selected_edge = None
           # return
      #  for res, amt in ROAD_COST.items():
          #  player["resources"][res] -= amt
       # edge.player = self.current_player
       # self._cancel_build()
       # self._build_player_texts()
       # print(f"{player['name']} built a road!")

    def _cancel_build(self):
        self.build_mode    = False
        self.build_choice  = BUILD_NONE
        self.hovered_node  = None
        self.hovered_edge  = None
        self.selected_node = None
        self.selected_edge = None
        self.show_confirm  = False

    def _end_turn(self):
        self.current_player = (self.current_player + 1) % len(PLAYERS_TWO)
        self._cancel_build()
        self._build_player_texts()
        print(f"Turn ended. Now it's {PLAYERS_TWO[self.current_player].name}'s turn.")

        # TODO: check for VPs to end game
        # if self.players[self.current_player].vp == 10:
            # self.window.show_view(EndView())
        print(f"Turn ended. Now it's {PLAYERS[self.current_player]['name']}'s turn.")

"""
TODO: Determine how we want trading to work
also maybe break into more functions for ex building the board could be a global helper function
"""
# ---------------------------------------------------------------------------
# Setup View
# ---------------------------------------------------------------------------
class SetupView(arcade.View):
    def __init__(self, board, players, current_player, round): 
        super().__init__()
        self.board = board
        self.players = players
        self.current_player = current_player
        self.round = round

    def _build_text_objects(self):
        player = self.players[self.current_player]
        self.txt_title = arcade.Text(f"{player["name"]}: Place your Settlement", SCREEN_WIDTH / 4, SCREEN_HEIGHT - 50, font_name="MedievalSharp", font_size=30, color=player["color"])

    def on_show_view(self):
        self._build_text_objects()

    def on_draw(self):
        self.clear()
        # --- Draw the board --- 
        #TODO: Make a helper function from the code thats in CatanView to build a board with all the ports and numbers.
        draw_board(self.board)
        self.txt_title.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        #TODO: Add in click logic for players placing their 
        if self.round == 1 and self.current_player < len(self.players) - 1:
            self.current_player += 1
            self.window.show_view(SetupView(self.board, self.players, self.current_player, self.round))
        elif self.round == 1 and self.current_player == len(self.players) - 1:
            self.round += 1
            self.window.show_view(SetupView(self.board, self.players, self.current_player, self.round))
        elif self.round == 2 and self.current_player > 0:
            self.current_player -= 1
            self.window.show_view(SetupView(self.board, self.players, self.current_player, self.round))
        else:
            self.window.show_view(CatanView(self.board, self.players, 0))
        
# ---------------------------------------------------------------------------
# Trade View
# ---------------------------------------------------------------------------
class TradeView(arcade.View):
    def __init__(self, board, players, current_player):
        super().__init__()
        self.board= board
        self.players = players
        self.current_player = current_player
    
    def _build_text_objects(self):
        bar_center_y = HUD_BOTTOM_HEIGHT / 2
        btn_w = 150
        self.txt_back = arcade.Text("Back to Board",  SCREEN_WIDTH - btn_w * 0.5 - 20,    bar_center_y, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")

    def _draw_bottom_bar(self):
        fill_rect(0, 0, SCREEN_WIDTH, HUD_BOTTOM_HEIGHT, HUD_BG)

        btn_w, btn_h = 150, 50
        btn_bottom = (HUD_BOTTOM_HEIGHT - btn_h) / 2

        fill_rect(SCREEN_WIDTH - btn_w - 20, btn_bottom, btn_w, btn_h, BTN_ENDTURN)
        self.txt_back.draw()

    def on_show_view(self):
        self._build_text_objects()

    def on_draw(self):
        self.clear()
        self._draw_bottom_bar()

    def on_mouse_press(self, x, y, button, modifiers):
        #NOTE: Would it be a good idea to make the btn_w and btn_h global variable?
        btn_w = 150
        if (SCREEN_WIDTH - btn_w - 20 <= x <= SCREEN_WIDTH - 20) and (y <= HUD_BOTTOM_HEIGHT):
            self.window.show_view(CatanView(self.board, self.players, self.current_player))

# ---------------------------------------------------------------------------
# Play Card View
# ---------------------------------------------------------------------------
class PlayCardView(arcade.View):
    def __init__(self, board, players, current_player):
        super().__init__()
        self.board= board
        self.players = players
        self.current_player = current_player
    
    def _build_text_objects(self):
        bar_center_y = HUD_BOTTOM_HEIGHT / 2
        btn_w = 150
        self.txt_back = arcade.Text("Back to Board",  SCREEN_WIDTH - btn_w * 0.5 - 20,    bar_center_y, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")

    def _draw_bottom_bar(self):
        fill_rect(0, 0, SCREEN_WIDTH, HUD_BOTTOM_HEIGHT, HUD_BG)

        btn_w, btn_h = 150, 50
        btn_bottom = (HUD_BOTTOM_HEIGHT - btn_h) / 2

        fill_rect(SCREEN_WIDTH - btn_w - 20, btn_bottom, btn_w, btn_h, BTN_ENDTURN)
        self.txt_back.draw()

    def on_show_view(self):
        self._build_text_objects()

    def on_draw(self):
        self.clear()
        self._draw_bottom_bar()

    def on_mouse_press(self, x, y, button, modifiers):
        #NOTE: Would it be a good idea to make the btn_w and btn_h global variable?
        btn_w = 150
        if (SCREEN_WIDTH - btn_w - 20 <= x <= SCREEN_WIDTH - 20) and (y <= HUD_BOTTOM_HEIGHT):
            self.window.show_view(CatanView(self.board, self.players, self.current_player))

# ---------------------------------------------------------------------------
# End View
# ---------------------------------------------------------------------------
class EndView(arcade.View):
    def __init__(self, players, current_player):
        super().__init__()
        self.players = players
        self.winning_player = current_player

    def on_show_view(self):
        self._build_text_objects()

    def _build_text_objects(self):
        #TODO: set the title to be in the middle of the screen and figure out how to customize to winning player
        # set the color of the text to the players color and add the player number to the text
        self.txt_title = arcade.Text(f"Congratulations Player {self.winning_player}!", SCREEN_WIDTH / 2, SCREEN_HEIGHT/2, font_size=30, bold=True, font_name="MedievalSharp")  #color = self.players[self.winning_player].color
        self.txt_instructions = arcade.Text("Click anywhere to play again!", SCREEN_WIDTH / 2, SCREEN_HEIGHT/2 - 100, font_size=20, font_name="MedievalSharp")

    def on_draw(self):
        self.clear()
        self.txt_title.draw()
        self.txt_instructions.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        self.window.show_view(StartView()) # Has to go back to start view to reset the board and players

def main():
    pyglet.font.add_file('fonts/MedievalSharp-Regular.ttf')
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.background_color = arcade.color.OCEAN_BOAT_BLUE
    window.show_view(StartView())
    arcade.run()

if __name__ == "__main__":
    main()