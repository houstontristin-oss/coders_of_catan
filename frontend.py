import arcade
import math
import os
import pyglet
from backend import CatanBoard

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Window Settings ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Coders of Catan"

# --- Hex Settings ---
HEX_SIZE = 60

# --- Board Center ---
BOARD_CENTER_X = SCREEN_WIDTH / 2
BOARD_CENTER_Y = SCREEN_HEIGHT / 2

# --- HUD Dimensions ---
HUD_BOTTOM_HEIGHT = 80
HUD_PANEL_WIDTH   = 260
HUD_PANEL_HEIGHT  = 200
DICE_AREA_WIDTH   = 180
DICE_AREA_HEIGHT  = 120

# --- Sprite Settings ---
ICON_SIZE    = 32
SPRITE_SCALE = ICON_SIZE / 512

RESOURCE_SPRITES = {
    "brick":  os.path.join(BASE_DIR, "sprites", "BW_icons", "brick-pile.png"),
    "ore":    os.path.join(BASE_DIR, "sprites", "BW_icons", "stone-pile.png"),
    "wheat":  os.path.join(BASE_DIR, "sprites", "BW_icons", "wheat.png"),
    "sheep":  os.path.join(BASE_DIR, "sprites", "BW_icons", "sheep.png"),
    "forest": os.path.join(BASE_DIR, "sprites", "BW_icons", "wood-pile.png"),
}

# --- Colors ---
HUD_BG           = (30,  30,  50)
HUD_PANEL_BG     = (20,  20,  40)
BTN_TRADE        = (52,  152, 219)
BTN_BUILD        = (39,  174, 96)
BTN_BUILD_ACTIVE = (100, 220, 130)
BTN_CARD         = (142, 68,  173)
BTN_ENDTURN      = (231, 76,  60)
TEXT_WHITE       = (255, 255, 255)
TEXT_LIGHT_GRAY  = (180, 180, 180)
TEXT_GOLD        = (255, 215, 0)

RESOURCE_COLORS = {
    "forest": (34,  139, 34),
    "wheat":  (255, 215, 0),
    "ore":    (112, 128, 144),
    "brick":  (178, 34,  34),
    "sheep":  (144, 238, 144),
    "desert": (210, 180, 140),
}

# --- Costs ---
SETTLEMENT_COST = {"brick": 1, "forest": 1, "wheat": 1, "sheep": 1}
ROAD_COST       = {"brick": 1, "forest": 1}

# --- Snap radii ---
NODE_SNAP_RADIUS = 18
EDGE_SNAP_RADIUS = 14

# --- Placeholder players (1 settlement + 1 road worth of resources each) ---
PLAYERS = [
    {"name": "Player 1", "color": (231, 76,  60),  "resources": {"brick": 2, "ore": 0, "wheat": 1, "sheep": 1, "forest": 2}, "vp": 0},
    {"name": "Player 2", "color": (39,  174, 96),  "resources": {"brick": 2, "ore": 0, "wheat": 1, "sheep": 1, "forest": 2}, "vp": 0},
    {"name": "Player 3", "color": (219, 118, 51),  "resources": {"brick": 2, "ore": 0, "wheat": 1, "sheep": 1, "forest": 2}, "vp": 0},
    {"name": "Player 4", "color": (142, 68,  173), "resources": {"brick": 2, "ore": 0, "wheat": 1, "sheep": 1, "forest": 2}, "vp": 0},
]

# Build sub-menu choices
BUILD_NONE       = None
BUILD_SETTLEMENT = "settlement"
BUILD_ROAD       = "road"


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------
def cubic_to_pixel(cx, cz, hex_size, origin_x, origin_y):
    px = origin_x + hex_size * (3 / 2) * cx
    py = origin_y + hex_size * (math.sqrt(3) / 2 * cx + math.sqrt(3) * cz)
    return px, py

def node_to_pixel(node_id, hex_size, origin_x, origin_y):
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


# ---------------------------------------------------------------------------
# Shape drawing helpers
# ---------------------------------------------------------------------------
def draw_settlement(cx, cy, size, color):
    """Small filled square = settlement."""
    half = size / 2
    pts  = [(cx-half, cy-half), (cx+half, cy-half),
            (cx+half, cy+half), (cx-half, cy+half)]
    arcade.draw_polygon_filled(pts, color)
    arcade.draw_polygon_outline(pts, arcade.color.BLACK, 2)

def draw_road(x1, y1, x2, y2, color, width=5):
    """Thick line between two node pixel positions = road."""
    arcade.draw_line(x1, y1, x2, y2, color, width)
    arcade.draw_line(x1, y1, x2, y2, arcade.color.BLACK, 1)

def fill_rect(left, bottom, width, height, color):
    arcade.draw_lrbt_rectangle_filled(left, left + width, bottom, bottom + height, color)

def outline_rect(left, bottom, width, height, color, border=2):
    arcade.draw_lrbt_rectangle_outline(left, left + width, bottom, bottom + height, color, border)


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------
class CatanWindow(arcade.Window):

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.OCEAN_BOAT_BLUE)
        pyglet.font.add_file('fonts/MedievalSharp-Regular.ttf')

        self.current_player_index = 0

        # Build mode state
        self.build_mode      = False
        self.build_choice    = BUILD_NONE
        self.hovered_node    = None
        self.hovered_edge    = None
        self.selected_node   = None
        self.selected_edge   = None
        self.show_confirm    = False

        # Pixel caches
        self._node_pixel_cache = {}   # node_id  -> (px, py)
        self._edge_pixel_cache = {}   # edge_id  -> (mx, my, x1, y1, x2, y2)

        self._build_text_objects()
        self._load_resource_icons()

        self.board = CatanBoard()
        self.board.make_board()

        self._build_node_pixel_cache()
        self._build_edge_pixel_cache()

    # ---------------------------------------------------------------------------
    # Caches
    # ---------------------------------------------------------------------------
    def _build_node_pixel_cache(self):
        for node_id in self.board.nodes:
            px, py = node_to_pixel(node_id, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
            self._node_pixel_cache[node_id] = (px, py)

    def _build_edge_pixel_cache(self):
        """
        For each edge store the midpoint (for snap detection) and both
        endpoint pixel coords (for drawing the road line).
        """
        for edge_id in self.board.edges:
            n1_id, n2_id = edge_id
            x1, y1 = self._node_pixel_cache[n1_id]
            x2, y2 = self._node_pixel_cache[n2_id]
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            self._edge_pixel_cache[edge_id] = (mx, my, x1, y1, x2, y2)

    # ---------------------------------------------------------------------------
    # Resource icons
    # ---------------------------------------------------------------------------
    def _load_resource_icons(self):
        self.resource_icons   = {}
        self.icon_sprite_list = arcade.SpriteList()
        for res in ["brick", "ore", "wheat", "sheep", "forest"]:
            sprite = arcade.Sprite(RESOURCE_SPRITES[res], scale=SPRITE_SCALE)
            self.resource_icons[res] = sprite
            self.icon_sprite_list.append(sprite)

    # ---------------------------------------------------------------------------
    # Text objects
    # ---------------------------------------------------------------------------
    def _build_text_objects(self):
        bar_cy  = HUD_BOTTOM_HEIGHT / 2
        btn_w   = 150
        gap     = 20
        total_w = 3 * btn_w + 2 * gap
        sx      = (SCREEN_WIDTH - total_w) / 2

        self.txt_trade = arcade.Text("Trade",     sx+btn_w*0.5,           bar_cy, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_build = arcade.Text("Build",     sx+btn_w*1.5+gap,       bar_cy, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_card  = arcade.Text("Play Card", sx+btn_w*2.5+gap*2,     bar_cy, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_end   = arcade.Text("End Turn",  SCREEN_WIDTH-btn_w*0.5-20, bar_cy, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")

        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - 10
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - 10
        self.txt_dice_label = arcade.Text("Dice Roll",               dx+DICE_AREA_WIDTH/2, dy+DICE_AREA_HEIGHT-18, TEXT_GOLD,      12, bold=True, anchor_x="center", font_name="MedievalSharp")
        self.txt_dice_hint  = arcade.Text("Auto-rolls on turn start",dx+DICE_AREA_WIDTH/2, dy+8,                  TEXT_LIGHT_GRAY, 9,             anchor_x="center", font_name="MedievalSharp")
        self.txt_die1       = arcade.Text("?", dx+(DICE_AREA_WIDTH-2*44-14)/2+22,     dy+24+22, TEXT_WHITE, 20, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_die2       = arcade.Text("?", dx+(DICE_AREA_WIDTH-2*44-14)/2+22+58,  dy+24+22, TEXT_WHITE, 20, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")

        self._build_player_texts()

    def _build_player_texts(self):
        player = PLAYERS[self.current_player_index]
        px = 10
        py = SCREEN_HEIGHT - HUD_PANEL_HEIGHT - 10

        self.txt_player_name = arcade.Text(player["name"], px+32, py+HUD_PANEL_HEIGHT-22,
                                           TEXT_GOLD, 14, bold=True, anchor_y="center", font_name="MedievalSharp")
        self.txt_player_vp   = arcade.Text(f"Victory Points: {player['vp']}", px+12, py+HUD_PANEL_HEIGHT-50,
                                           TEXT_LIGHT_GRAY, 10)

        labels    = {"brick":"Brick","ore":"Ore","wheat":"Wheat","sheep":"Sheep","forest":"Wood"}
        order     = ["brick", "ore", "wheat", "sheep", "forest"]
        col_x     = [px+12+ICON_SIZE+6, px+12+HUD_PANEL_WIDTH//2+ICON_SIZE+6]
        row_start = py+HUD_PANEL_HEIGHT-80

        self.txt_resources = []
        for i, res in enumerate(order):
            rx = col_x[i % 2]
            ry = row_start - (i // 2) * (ICON_SIZE + 6)
            self.txt_resources.append(
                arcade.Text(f"{labels[res]}: {player['resources'][res]}", rx, ry,
                            TEXT_WHITE, 10, anchor_y="center", font_name="MedievalSharp")
            )

    # ---------------------------------------------------------------------------
    # Affordability
    # ---------------------------------------------------------------------------
    def _can_afford(self, cost_dict):
        res = PLAYERS[self.current_player_index]["resources"]
        return all(res.get(r, 0) >= amt for r, amt in cost_dict.items())

    # ---------------------------------------------------------------------------
    # HUD draw helpers
    # ---------------------------------------------------------------------------
    def _draw_bottom_bar(self):
        fill_rect(0, 0, SCREEN_WIDTH, HUD_BOTTOM_HEIGHT, HUD_BG)

        btn_w, btn_h = 150, 50
        gap     = 20
        total_w = 3 * btn_w + 2 * gap
        sx      = (SCREEN_WIDTH - total_w) / 2
        btn_bot = (HUD_BOTTOM_HEIGHT - btn_h) / 2

        build_col = BTN_BUILD_ACTIVE if self.build_mode else BTN_BUILD

        fill_rect(sx,                    btn_bot, btn_w, btn_h, BTN_TRADE)
        fill_rect(sx+btn_w+gap,          btn_bot, btn_w, btn_h, build_col)
        fill_rect(sx+2*(btn_w+gap),      btn_bot, btn_w, btn_h, BTN_CARD)
        fill_rect(SCREEN_WIDTH-btn_w-20, btn_bot, btn_w, btn_h, BTN_ENDTURN)

        self.txt_trade.draw()
        self.txt_build.draw()
        self.txt_card.draw()
        self.txt_end.draw()

    def _draw_build_submenu(self):
        """
        Floats above the Build button when build_mode is True and
        no specific build type has been chosen yet.
        """
        if not self.build_mode or self.build_choice != BUILD_NONE:
            return

        btn_w  = 150
        gap    = 20
        sx     = (SCREEN_WIDTH - 3*btn_w - 2*gap) / 2
        bx     = sx + btn_w + gap      # left edge of Build button
        by     = HUD_BOTTOM_HEIGHT     # sits just above the bottom bar
        menu_w = btn_w

        fill_rect(bx, by, menu_w, 80, HUD_PANEL_BG)
        outline_rect(bx, by, menu_w, 80, TEXT_GOLD, 2)

        # Settlement row
        s_col = (39, 174, 96) if self._can_afford(SETTLEMENT_COST) else (70, 70, 70)
        fill_rect(bx+8, by+44, menu_w-16, 28, s_col)
        arcade.draw_text("Settlement", bx+menu_w/2, by+58,
                         TEXT_WHITE, 10, bold=True,
                         anchor_x="center", anchor_y="center",
                         font_name="MedievalSharp")

        # Road row
        r_col = (52, 152, 219) if self._can_afford(ROAD_COST) else (70, 70, 70)
        fill_rect(bx+8, by+8, menu_w-16, 28, r_col)
        arcade.draw_text("Road", bx+menu_w/2, by+22,
                         TEXT_WHITE, 10, bold=True,
                         anchor_x="center", anchor_y="center",
                         font_name="MedievalSharp")

    def _draw_player_panel(self):
        player = PLAYERS[self.current_player_index]
        px = 10
        py = SCREEN_HEIGHT - HUD_PANEL_HEIGHT - 10

        fill_rect(px, py, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, HUD_PANEL_BG)
        outline_rect(px, py, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, player["color"])
        arcade.draw_circle_filled(px+18, py+HUD_PANEL_HEIGHT-22, 8, player["color"])

        self.txt_player_name.draw()
        self.txt_player_vp.draw()

        order  = ["brick", "ore", "wheat", "sheep", "forest"]
        col_x  = [px+12, px+12+HUD_PANEL_WIDTH//2]
        row_sy = py+HUD_PANEL_HEIGHT-90

        for i, res in enumerate(order):
            sprite = self.resource_icons[res]
            sprite.center_x = col_x[i%2] + ICON_SIZE/2
            sprite.center_y = row_sy - (i//2)*(ICON_SIZE+6) + ICON_SIZE/2

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

        die_size = 44
        die_gap  = 14
        die1_x   = dx + (DICE_AREA_WIDTH - 2*die_size - die_gap) / 2
        die_y    = dy + 24

        fill_rect(die1_x,                   die_y, die_size, die_size, (60,60,90))
        fill_rect(die1_x+die_size+die_gap,  die_y, die_size, die_size, (60,60,90))
        self.txt_die1.draw()
        self.txt_die2.draw()

    # ---------------------------------------------------------------------------
    # Board piece drawing (ALWAYS drawn, every frame)
    # ---------------------------------------------------------------------------
    def _draw_placed_pieces(self):
        """Draw all roads and settlements that have been placed so far."""
        for edge_id, edge_obj in self.board.edges.items():
            if edge_obj.player is not None:
                mx, my, x1, y1, x2, y2 = self._edge_pixel_cache[edge_id]
                draw_road(x1, y1, x2, y2, PLAYERS[edge_obj.player]["color"])

        for node_id, node_obj in self.board.nodes.items():
            if node_obj.player is not None:
                npx, npy = self._node_pixel_cache[node_id]
                draw_settlement(npx, npy, 14, PLAYERS[node_obj.player]["color"])

    # ---------------------------------------------------------------------------
    # Ghost highlights
    # ---------------------------------------------------------------------------
    def _draw_node_highlights(self):
        player_color = PLAYERS[self.current_player_index]["color"]

        for node_id, node_obj in self.board.nodes.items():
            if node_obj.player is not None:
                continue                          # already shown by _draw_placed_pieces

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
        player_color = PLAYERS[self.current_player_index]["color"]

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

    # ---------------------------------------------------------------------------
    # Confirmation popup
    # ---------------------------------------------------------------------------
    def _draw_confirm_popup(self):
        if not self.show_confirm:
            return

        if self.build_choice == BUILD_SETTLEMENT and self.selected_node:
            cx, cy = self._node_pixel_cache[self.selected_node.id]
            cy    += 18
            can    = self._can_afford(SETTLEMENT_COST)
            label  = "Build Settlement?"
        elif self.build_choice == BUILD_ROAD and self.selected_edge:
            mx, my, *_ = self._edge_pixel_cache[self.selected_edge.id]
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

        arcade.draw_text(label, cx, cy+popup_h-14,
                         TEXT_GOLD, 10, bold=True,
                         anchor_x="center", anchor_y="center",
                         font_name="MedievalSharp")

        btn_col = (39, 174, 96) if can else (80, 80, 80)
        fill_rect(pop_left+8,          cy+8, 66, 30, btn_col)
        arcade.draw_text("Confirm" if can else "No Res.",
                         pop_left+41, cy+23,
                         TEXT_WHITE, 9, bold=True,
                         anchor_x="center", anchor_y="center",
                         font_name="MedievalSharp")

        fill_rect(pop_left+popup_w-74, cy+8, 66, 30, (180, 50, 50))
        arcade.draw_text("Cancel",
                         pop_left+popup_w-41, cy+23,
                         TEXT_WHITE, 9, bold=True,
                         anchor_x="center", anchor_y="center",
                         font_name="MedievalSharp")

    # ---------------------------------------------------------------------------
    # on_draw
    # ---------------------------------------------------------------------------
    def on_draw(self):
        self.clear()

        # Hex tiles
        for xyz, tile in self.board.tiles.items():
            cx, cy, cz = xyz
            px, py = cubic_to_pixel(cx, cz, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
            corners = get_hex_corners(px, py, HEX_SIZE)
            arcade.draw_polygon_filled(corners, RESOURCE_COLORS[tile.resource])
            arcade.draw_polygon_outline(corners, arcade.color.BLACK, 2)

        # Ghost highlights (only during active build choice)
        if self.build_choice == BUILD_SETTLEMENT:
            self._draw_node_highlights()
        elif self.build_choice == BUILD_ROAD:
            self._draw_edge_highlights()

        # Placed pieces — ALWAYS drawn so settlements/roads persist
        self._draw_placed_pieces()

        # Confirmation popup
        if self.show_confirm:
            self._draw_confirm_popup()

        # HUD on top of everything
        self._draw_player_panel()
        self._draw_dice_area()
        self._draw_bottom_bar()
        self._draw_build_submenu()

    # ---------------------------------------------------------------------------
    # Mouse motion
    # ---------------------------------------------------------------------------
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

    # ---------------------------------------------------------------------------
    # Mouse press
    # ---------------------------------------------------------------------------
    def on_mouse_press(self, x, y, button, modifiers):
        btn_w   = 150
        gap     = 20
        total_w = 3 * btn_w + 2 * gap
        sx      = (SCREEN_WIDTH - total_w) / 2

        # ---- End Turn ----
        if (SCREEN_WIDTH-btn_w-20 <= x <= SCREEN_WIDTH-20) and (y <= HUD_BOTTOM_HEIGHT):
            self._end_turn()
            return

        # ---- Build button — toggle submenu ----
        build_left = sx + btn_w + gap
        if (build_left <= x <= build_left + btn_w) and (y <= HUD_BOTTOM_HEIGHT):
            if self.build_mode:
                self._cancel_build()
            else:
                self.build_mode   = True
                self.build_choice = BUILD_NONE
            return

        # ---- Build sub-menu (Settlement / Road choice) ----
        if self.build_mode and self.build_choice == BUILD_NONE:
            bx     = sx + btn_w + gap
            by     = HUD_BOTTOM_HEIGHT
            menu_w = btn_w

            # Settlement row  (top half of sub-menu)
            if (bx+8 <= x <= bx+menu_w-8) and (by+44 <= y <= by+72):
                if self._can_afford(SETTLEMENT_COST):
                    self.build_choice = BUILD_SETTLEMENT
                return

            # Road row  (bottom half of sub-menu)
            if (bx+8 <= x <= bx+menu_w-8) and (by+8 <= y <= by+36):
                if self._can_afford(ROAD_COST):
                    self.build_choice = BUILD_ROAD
                return

        # ---- Confirmation popup ----
        if self.show_confirm:
            # Figure out popup anchor
            if self.build_choice == BUILD_SETTLEMENT and self.selected_node:
                pcx, pcy = self._node_pixel_cache[self.selected_node.id]
                pcy     += 18
            elif self.build_choice == BUILD_ROAD and self.selected_edge:
                mx, my, *_ = self._edge_pixel_cache[self.selected_edge.id]
                pcx, pcy   = mx, my + 18
            else:
                self.show_confirm = False
                return

            popup_w  = 160
            pop_left = pcx - popup_w / 2

            # Confirm button
            if (pop_left+8 <= x <= pop_left+74) and (pcy+8 <= y <= pcy+38):
                if self.build_choice == BUILD_SETTLEMENT and self._can_afford(SETTLEMENT_COST):
                    self._place_settlement(self.selected_node)
                elif self.build_choice == BUILD_ROAD and self._can_afford(ROAD_COST):
                    self._place_road(self.selected_edge)
                return

            # Cancel button
            if (pop_left+popup_w-74 <= x <= pop_left+popup_w-8) and (pcy+8 <= y <= pcy+38):
                self.selected_node = None
                self.selected_edge = None
                self.show_confirm  = False
                return

            # Click outside popup — dismiss
            self.selected_node = None
            self.selected_edge = None
            self.show_confirm  = False
            return

        # ---- Click a node (settlement mode) ----
        if self.build_choice == BUILD_SETTLEMENT and self.hovered_node:
            self.selected_node = self.hovered_node
            self.show_confirm  = True
            return

        # ---- Click an edge (road mode) ----
        if self.build_choice == BUILD_ROAD and self.hovered_edge:
            self.selected_edge = self.hovered_edge
            self.show_confirm  = True
            return

    # ---------------------------------------------------------------------------
    # Placement
    # ---------------------------------------------------------------------------
    def _place_settlement(self, node):
        player = PLAYERS[self.current_player_index]
        for res, amt in SETTLEMENT_COST.items():
            player["resources"][res] -= amt
        node.player   = self.current_player_index
        node.building = "settlement"
        player["vp"] += 1
        self._cancel_build()
        self._build_player_texts()
        print(f"{player['name']} built a settlement! VP: {player['vp']}")

    def _place_road(self, edge):
        player = PLAYERS[self.current_player_index]
        for res, amt in ROAD_COST.items():
            player["resources"][res] -= amt
        edge.player = self.current_player_index
        self._cancel_build()
        self._build_player_texts()
        print(f"{player['name']} built a road!")

    def _cancel_build(self):
        self.build_mode    = False
        self.build_choice  = BUILD_NONE
        self.hovered_node  = None
        self.hovered_edge  = None
        self.selected_node = None
        self.selected_edge = None
        self.show_confirm  = False

    # ---------------------------------------------------------------------------
    # End turn
    # ---------------------------------------------------------------------------
    def _end_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(PLAYERS)
        self._cancel_build()
        self._build_player_texts()
        print(f"Turn ended. Now it's {PLAYERS[self.current_player_index]['name']}'s turn.")


def main():
    window = CatanWindow()
    arcade.run()


if __name__ == "__main__":
    main()