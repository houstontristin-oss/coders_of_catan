import arcade
import math
import os
import pyglet
from backend import CatanBoard

# Absolute path to folder containing frontend.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Window Settings ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Coders of Catan"

# --- Hex Settings ---
HEX_SIZE = 60  # radius from center to corner

# --- Board Center (screen pixels) ---
BOARD_CENTER_X = SCREEN_WIDTH / 2
BOARD_CENTER_Y = SCREEN_HEIGHT / 2

# --- HUD Dimensions ---
HUD_BOTTOM_HEIGHT = 80
HUD_PANEL_WIDTH   = 260
HUD_PANEL_HEIGHT  = 200
DICE_AREA_WIDTH   = 180
DICE_AREA_HEIGHT  = 120

# --- Sprite Settings ---
ICON_SIZE = 32
SPRITE_SCALE = ICON_SIZE / 512

# Maps resource names -> sprite file paths
RESOURCE_SPRITES = {
    "brick":  os.path.join(BASE_DIR, "sprites", "BW_icons", "brick-pile.png"),
    "ore":    os.path.join(BASE_DIR, "sprites", "BW_icons", "stone-pile.png"),
    "wheat":  os.path.join(BASE_DIR, "sprites", "BW_icons", "wheat.png"),
    "sheep":  os.path.join(BASE_DIR, "sprites", "BW_icons", "sheep.png"),
    "forest": os.path.join(BASE_DIR, "sprites", "BW_icons", "wood-pile.png"),
}

# --- HUD Colors ---
HUD_BG          = (30,  30,  50)
HUD_PANEL_BG    = (20,  20,  40)
BTN_TRADE       = (52,  152, 219)
BTN_BUILD       = (39,  174, 96)
BTN_BUILD_ACTIVE= (100, 220, 130)   # brighter green when build mode is ON
BTN_CARD        = (142, 68,  173)
BTN_ENDTURN     = (231, 76,  60)
TEXT_WHITE      = (255, 255, 255)
TEXT_LIGHT_GRAY = (180, 180, 180)
TEXT_GOLD       = (255, 215, 0)

# --- Resource Colors (hex tiles) ---
RESOURCE_COLORS = {
    "forest": (34,  139, 34),
    "wheat":  (255, 215, 0),
    "ore":    (112, 128, 144),
    "brick":  (178, 34,  34),
    "sheep":  (144, 238, 144),
    "desert": (210, 180, 140),
}

# --- Settlement cost ---
SETTLEMENT_COST = {"brick": 1, "forest": 1, "wheat": 1, "sheep": 1}

# --- Placeholder Player Data ---
# TODO: replace with Amanda/Apoorva's real Player objects
PLAYERS = [
    {"name": "Player 1", "color": (231, 76,  60),  "resources": {"brick": 1, "ore": 0, "wheat": 1, "sheep": 1, "forest": 1}, "vp": 0},
    {"name": "Player 2", "color": (39,  174, 96),  "resources": {"brick": 1, "ore": 0, "wheat": 1, "sheep": 1, "forest": 1}, "vp": 0},
    {"name": "Player 3", "color": (219, 118, 51),  "resources": {"brick": 1, "ore": 0, "wheat": 1, "sheep": 1, "forest": 1}, "vp": 0},
    {"name": "Player 4", "color": (142, 68,  173), "resources": {"brick": 1, "ore": 0, "wheat": 1, "sheep": 1, "forest": 1}, "vp": 0},
]

# --- Node hover / click radius (pixels) ---
NODE_SNAP_RADIUS = 18


# ---------------------------------------------------------------------------
# Helper: cubic tile coords -> screen pixels  (flat-top hex layout)
# ---------------------------------------------------------------------------
def cubic_to_pixel(cx, cz, hex_size, origin_x, origin_y):
    px = origin_x + hex_size * (3 / 2) * cx
    py = origin_y + hex_size * (math.sqrt(3) / 2 * cx + math.sqrt(3) * cz)
    return px, py


# ---------------------------------------------------------------------------
# Helper: node ID (fractional cubic avg) -> screen pixels
#
# Each node id = average of 3 surrounding tile cubic coords, so
# multiplying back by 3 recovers the "sum", and we pass that through
# the same cubic_to_pixel formula divided by 3 — which simplifies to
# just calling cubic_to_pixel with the fractional id directly since the
# formula is linear.  In other words: node_pixel == cubic_to_pixel(fx, fz).
# ---------------------------------------------------------------------------
def node_to_pixel(node_id, hex_size, origin_x, origin_y):
    """
    Convert a node ID (fx, fy, fz) — which is the average of its surrounding
    tile cubic coordinates — into screen pixel (x, y).

    Because cubic_to_pixel is a linear function, applying it to the averaged
    coordinates gives exactly the average of the surrounding tile centers,
    which is precisely where the node lives visually on a flat-top hex grid.
    """
    fx, fy, fz = node_id
    px = origin_x + hex_size * (3 / 2) * fx
    py = origin_y + hex_size * (math.sqrt(3) / 2 * fx + math.sqrt(3) * fz)
    return px, py


# ---------------------------------------------------------------------------
# Helper: 6 corners of a flat-top hex
# ---------------------------------------------------------------------------
def get_hex_corners(center_x, center_y, size):
    corners = []
    for i in range(6):
        angle_rad = math.radians(60 * i)
        corners.append((
            center_x + size * math.cos(angle_rad),
            center_y + size * math.sin(angle_rad),
        ))
    return corners


# ---------------------------------------------------------------------------
# Helper: draw a small square rotated 0° (settlement) centered at (x, y)
# ---------------------------------------------------------------------------
def draw_settlement(cx, cy, size, color):
    half = size / 2
    points = [
        (cx - half, cy - half),
        (cx + half, cy - half),
        (cx + half, cy + half),
        (cx - half, cy + half),
    ]
    arcade.draw_polygon_filled(points, color)
    arcade.draw_polygon_outline(points, arcade.color.BLACK, 2)


# ---------------------------------------------------------------------------
# Helper: flat filled/outlined rect
# ---------------------------------------------------------------------------
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

        # --- Build mode state ---
        self.build_mode    = False       # True when player clicked "Build"
        self.hovered_node  = None        # Node object the mouse is near (or None)
        self.selected_node = None        # Node the player clicked to confirm on
        self.show_confirm  = False       # True when confirmation popup is visible

        # Pre-cache node pixel positions so we don't recompute every frame
        self._node_pixel_cache = {}      # node_id -> (px, py)

        self._build_text_objects()
        self._load_resource_icons()

        self.board = CatanBoard()
        self.board.make_board()

        # Build the pixel cache now that the board exists
        self._build_node_pixel_cache()

    # ---------------------------------------------------------------------------
    # Pre-compute all node pixel positions once after make_board()
    # ---------------------------------------------------------------------------
    def _build_node_pixel_cache(self):
        for node_id, node_obj in self.board.nodes.items():
            px, py = node_to_pixel(node_id, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
            self._node_pixel_cache[node_id] = (px, py)

    # ---------------------------------------------------------------------------
    # Resource icons
    # ---------------------------------------------------------------------------
    def _load_resource_icons(self):
        self.resource_icons = {}
        self.icon_sprite_list = arcade.SpriteList()
        resource_order = ["brick", "ore", "wheat", "sheep", "forest"]
        for res in resource_order:
            sprite = arcade.Sprite(RESOURCE_SPRITES[res], scale=SPRITE_SCALE)
            self.resource_icons[res] = sprite
            self.icon_sprite_list.append(sprite)

    # ---------------------------------------------------------------------------
    # Text objects
    # ---------------------------------------------------------------------------
    def _build_text_objects(self):
        bar_center_y = HUD_BOTTOM_HEIGHT / 2
        btn_w = 150
        gap   = 20
        total_w = 3 * btn_w + 2 * gap
        start_x = (SCREEN_WIDTH - total_w) / 2

        self.txt_trade = arcade.Text("Trade",     start_x + btn_w * 0.5,              bar_center_y, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_build = arcade.Text("Build",     start_x + btn_w * 1.5 + gap,        bar_center_y, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_card  = arcade.Text("Play Card", start_x + btn_w * 2.5 + gap * 2,    bar_center_y, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_end   = arcade.Text("End Turn",  SCREEN_WIDTH - btn_w * 0.5 - 20,    bar_center_y, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")

        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - 10
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - 10
        self.txt_dice_label = arcade.Text("Dice Roll",               dx + DICE_AREA_WIDTH / 2, dy + DICE_AREA_HEIGHT - 18, TEXT_GOLD,       12, bold=True, anchor_x="center", font_name="MedievalSharp")
        self.txt_dice_hint  = arcade.Text("Auto-rolls on turn start",dx + DICE_AREA_WIDTH / 2, dy + 8,                    TEXT_LIGHT_GRAY,  9,            anchor_x="center", font_name="MedievalSharp")
        self.txt_die1       = arcade.Text("?", dx + (DICE_AREA_WIDTH - 2*44 - 14) / 2 + 22,       dy + 24 + 22, TEXT_WHITE, 20, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_die2       = arcade.Text("?", dx + (DICE_AREA_WIDTH - 2*44 - 14) / 2 + 22 + 58,  dy + 24 + 22, TEXT_WHITE, 20, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")

        self._build_player_texts()

    def _build_player_texts(self):
        player = PLAYERS[self.current_player_index]
        px = 10
        py = SCREEN_HEIGHT - HUD_PANEL_HEIGHT - 10

        self.txt_player_name = arcade.Text(
            player["name"],
            px + 32, py + HUD_PANEL_HEIGHT - 22,
            TEXT_GOLD, 14, bold=True, anchor_y="center", font_name="MedievalSharp"
        )
        self.txt_player_vp = arcade.Text(
            f"Victory Points: {player['vp']}",
            px + 12, py + HUD_PANEL_HEIGHT - 50,
            TEXT_LIGHT_GRAY, 10
        )

        resource_order  = ["brick", "ore", "wheat", "sheep", "forest"]
        resource_labels = {"brick": "Brick", "ore": "Ore", "wheat": "Wheat", "sheep": "Sheep", "forest": "Wood"}
        col_x = [px + 12 + ICON_SIZE + 6, px + 12 + HUD_PANEL_WIDTH // 2 + ICON_SIZE + 6]
        row_start_y = py + HUD_PANEL_HEIGHT - 80

        self.txt_resources = []
        for i, res in enumerate(resource_order):
            rx = col_x[i % 2]
            ry = row_start_y - (i // 2) * (ICON_SIZE + 6)
            self.txt_resources.append(
                arcade.Text(
                    f"{resource_labels[res]}: {player['resources'][res]}",
                    rx, ry,
                    TEXT_WHITE, 10, anchor_y="center", font_name="MedievalSharp"
                )
            )

    # ---------------------------------------------------------------------------
    # Utility: does the current player have enough resources to build a settlement?
    # ---------------------------------------------------------------------------
    def _can_afford_settlement(self):
        res = PLAYERS[self.current_player_index]["resources"]
        return all(res.get(r, 0) >= amt for r, amt in SETTLEMENT_COST.items())

    # ---------------------------------------------------------------------------
    # Draw helpers
    # ---------------------------------------------------------------------------
    def _draw_bottom_bar(self):
        fill_rect(0, 0, SCREEN_WIDTH, HUD_BOTTOM_HEIGHT, HUD_BG)

        btn_w, btn_h = 150, 50
        gap = 20
        total_w = 3 * btn_w + 2 * gap
        start_x = (SCREEN_WIDTH - total_w) / 2
        btn_bottom = (HUD_BOTTOM_HEIGHT - btn_h) / 2

        # Build button turns brighter when mode is active
        build_color = BTN_BUILD_ACTIVE if self.build_mode else BTN_BUILD

        fill_rect(start_x,                   btn_bottom, btn_w, btn_h, BTN_TRADE)
        fill_rect(start_x + btn_w + gap,     btn_bottom, btn_w, btn_h, build_color)
        fill_rect(start_x + 2*(btn_w + gap), btn_bottom, btn_w, btn_h, BTN_CARD)
        fill_rect(SCREEN_WIDTH - btn_w - 20, btn_bottom, btn_w, btn_h, BTN_ENDTURN)

        self.txt_trade.draw()
        self.txt_build.draw()
        self.txt_card.draw()
        self.txt_end.draw()

    def _draw_player_panel(self):
        player = PLAYERS[self.current_player_index]
        px = 10
        py = SCREEN_HEIGHT - HUD_PANEL_HEIGHT - 10

        fill_rect(px, py, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, HUD_PANEL_BG)
        outline_rect(px, py, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, player["color"])

        arcade.draw_circle_filled(px + 18, py + HUD_PANEL_HEIGHT - 22, 8, player["color"])

        self.txt_player_name.draw()
        self.txt_player_vp.draw()

        resource_order = ["brick", "ore", "wheat", "sheep", "forest"]
        col_x = [px + 12, px + 12 + HUD_PANEL_WIDTH // 2]
        row_start_y = py + HUD_PANEL_HEIGHT - 90

        for i, res in enumerate(resource_order):
            icon_x = col_x[i % 2] + ICON_SIZE / 2
            icon_y = row_start_y - (i // 2) * (ICON_SIZE + 6) + ICON_SIZE / 2
            sprite = self.resource_icons[res]
            sprite.center_x = icon_x
            sprite.center_y = icon_y

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
        total_w  = 2 * die_size + die_gap
        die1_x   = dx + (DICE_AREA_WIDTH - total_w) / 2
        die_y    = dy + 24

        fill_rect(die1_x,                        die_y, die_size, die_size, (60, 60, 90))
        fill_rect(die1_x + die_size + die_gap,   die_y, die_size, die_size, (60, 60, 90))

        self.txt_die1.draw()
        self.txt_die2.draw()

    # ---------------------------------------------------------------------------
    # Draw node highlights during build mode
    # ---------------------------------------------------------------------------
    def _draw_node_highlights(self):
        """
        In build mode, draw a small semi-transparent circle at every node.
        The hovered node gets a brighter, larger ring in the current player color.
        Nodes already occupied are shown in a dim red to indicate they're taken.
        """
        player_color = PLAYERS[self.current_player_index]["color"]

        for node_id, node_obj in self.board.nodes.items():
            npx, npy = self._node_pixel_cache[node_id]

            # Skip nodes that are off-screen (inside HUD areas)
            if npy < HUD_BOTTOM_HEIGHT + 5 or npy > SCREEN_HEIGHT - 10:
                continue
            if npx < HUD_PANEL_WIDTH + 5 or npx > SCREEN_WIDTH - DICE_AREA_WIDTH - 15:
                continue

            if node_obj.player is not None:
                # Already occupied — draw the existing settlement
                owner_idx = node_obj.player  # stored as player index (int) for now
                owner_color = PLAYERS[owner_idx]["color"]
                draw_settlement(npx, npy, 14, owner_color)

            elif node_obj is self.hovered_node:
                # Hovered node — bright outline + filled circle
                arcade.draw_circle_filled(npx, npy, 12, (*player_color, 180))
                arcade.draw_circle_outline(npx, npy, 14, player_color, 3)

            else:
                # Normal valid node — subtle white ghost circle
                arcade.draw_circle_filled(npx, npy, 8, (255, 255, 255, 60))
                arcade.draw_circle_outline(npx, npy, 8, (255, 255, 255, 120), 1)

    # ---------------------------------------------------------------------------
    # Draw confirmation popup above the selected node
    # ---------------------------------------------------------------------------
    def _draw_confirm_popup(self):
        if not self.selected_node or not self.show_confirm:
            return

        npx, npy = self._node_pixel_cache[self.selected_node.id]
        can_afford = self._can_afford_settlement()

        popup_w, popup_h = 160, 70
        pop_left   = npx - popup_w / 2
        pop_bottom = npy + 18  # sit just above the node dot

        # Background
        fill_rect(pop_left, pop_bottom, popup_w, popup_h, (20, 20, 40, 220))
        outline_rect(pop_left, pop_bottom, popup_w, popup_h, TEXT_GOLD, 2)

        # Title
        arcade.draw_text(
            "Build Settlement?",
            npx, pop_bottom + popup_h - 14,
            TEXT_GOLD, 10, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp"
        )

        # Confirm button
        btn_color = (39, 174, 96) if can_afford else (80, 80, 80)
        fill_rect(pop_left + 8, pop_bottom + 8, 66, 30, btn_color)
        arcade.draw_text(
            "Confirm" if can_afford else "No Res.",
            pop_left + 8 + 33, pop_bottom + 23,
            TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp"
        )

        # Cancel button
        fill_rect(pop_left + popup_w - 74, pop_bottom + 8, 66, 30, (180, 50, 50))
        arcade.draw_text(
            "Cancel",
            pop_left + popup_w - 74 + 33, pop_bottom + 23,
            TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp"
        )

    # ---------------------------------------------------------------------------
    # Arcade event loop
    # ---------------------------------------------------------------------------
    def on_draw(self):
        self.clear()

        # --- Draw the board tiles ---
        for xyz, tile in self.board.tiles.items():
            cx, cy, cz = xyz
            px, py = cubic_to_pixel(cx, cz, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
            corners = get_hex_corners(px, py, HEX_SIZE)
            arcade.draw_polygon_filled(corners, RESOURCE_COLORS[tile.resource])
            arcade.draw_polygon_outline(corners, arcade.color.BLACK, 2)

        # --- Draw node highlights (only in build mode) ---
        if self.build_mode:
            self._draw_node_highlights()

        # --- Draw confirmation popup if a node was clicked ---
        if self.show_confirm:
            self._draw_confirm_popup()

        # --- Draw HUD ---
        self._draw_player_panel()
        self._draw_dice_area()
        self._draw_bottom_bar()

    # ---------------------------------------------------------------------------
    # Mouse motion — update hovered node in build mode
    # ---------------------------------------------------------------------------
    def on_mouse_motion(self, x, y, dx, dy):
        if not self.build_mode or self.show_confirm:
            return

        closest      = None
        closest_dist = float("inf")

        for node_id, (npx, npy) in self._node_pixel_cache.items():
            dist = math.hypot(x - npx, y - npy)
            if dist < NODE_SNAP_RADIUS and dist < closest_dist:
                closest      = self.board.nodes[node_id]
                closest_dist = dist

        self.hovered_node = closest

    # ---------------------------------------------------------------------------
    # Mouse press
    # ---------------------------------------------------------------------------
    def on_mouse_press(self, x, y, button, modifiers):
        btn_w = 150
        gap   = 20
        total_w = 3 * btn_w + 2 * gap
        start_x = (SCREEN_WIDTH - total_w) / 2
        btn_bottom = (HUD_BOTTOM_HEIGHT - 50) / 2

        # --- End Turn button ---
        if (SCREEN_WIDTH - btn_w - 20 <= x <= SCREEN_WIDTH - 20) and (y <= HUD_BOTTOM_HEIGHT):
            self._end_turn()
            return

        # --- Build button ---
        build_left = start_x + btn_w + gap
        if (build_left <= x <= build_left + btn_w) and (y <= HUD_BOTTOM_HEIGHT):
            self.build_mode   = not self.build_mode
            self.hovered_node  = None
            self.selected_node = None
            self.show_confirm  = False
            return

        # --- Handle confirmation popup clicks ---
        if self.show_confirm and self.selected_node:
            npx, npy = self._node_pixel_cache[self.selected_node.id]
            popup_w  = 160
            pop_left = npx - popup_w / 2
            pop_bottom = npy + 18

            # Confirm button bounds
            if (pop_left + 8 <= x <= pop_left + 74) and (pop_bottom + 8 <= y <= pop_bottom + 38):
                if self._can_afford_settlement():
                    self._place_settlement(self.selected_node)
                return

            # Cancel button bounds
            if (pop_left + popup_w - 74 <= x <= pop_left + popup_w - 8) and (pop_bottom + 8 <= y <= pop_bottom + 38):
                self.selected_node = None
                self.show_confirm  = False
                return

            # Clicked outside popup — cancel
            self.selected_node = None
            self.show_confirm  = False
            return

        # --- Click on a node while in build mode ---
        if self.build_mode and self.hovered_node and not self.show_confirm:
            node = self.hovered_node
            # Only allow clicking on empty nodes
            if node.player is None:
                self.selected_node = node
                self.show_confirm  = True
            return

    # ---------------------------------------------------------------------------
    # Place a settlement on the selected node
    # ---------------------------------------------------------------------------
    def _place_settlement(self, node):
        player_idx = self.current_player_index
        player     = PLAYERS[player_idx]

        # Deduct resources
        for res, amt in SETTLEMENT_COST.items():
            player["resources"][res] -= amt

        # Mark the node as owned (store player index for now;
        # TODO: swap for real Player object when Amanda/Apoorva wire in)
        node.player   = player_idx
        node.building = "settlement"

        # Update victory points
        player["vp"] += 1

        # Reset build mode UI
        self.show_confirm  = False
        self.selected_node = None
        self.hovered_node  = None
        self.build_mode    = False

        # Rebuild HUD text so resource counts + VP update immediately
        self._build_player_texts()

        print(f"{player['name']} built a settlement! VP: {player['vp']}")

    # ---------------------------------------------------------------------------
    # End turn
    # ---------------------------------------------------------------------------
    def _end_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(PLAYERS)
        # Cancel any in-progress build action
        self.build_mode    = False
        self.hovered_node  = None
        self.selected_node = None
        self.show_confirm  = False
        self._build_player_texts()
        print(f"Turn ended. Now it's {PLAYERS[self.current_player_index]['name']}'s turn.")


def main():
    window = CatanWindow()
    arcade.run()


if __name__ == "__main__":
    main()