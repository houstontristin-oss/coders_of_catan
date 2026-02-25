import arcade
import math
import os
import pyglet
from backend import CatanBoard

# Absolute path to folder containing frontend.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Click detection / node highlighting — needs Apoorva
# Actual settlement and road sprites appearing on nodes/edges — needs Nick's edges to exist
# Wiring cubic_to_pixel to Nick's real board object — needs Nick's full 19-tile initialization

# --- Window Settings ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Coders of Catan"

# --- Hex Settings ---
HEX_SIZE = 60  # radius from center to corner

# --- Board Center (screen pixels) ---
BOARD_CENTER_X = SCREEN_WIDTH / 2
BOARD_CENTER_Y = SCREEN_HEIGHT / 2

# --- HUD Dimensions ---
HUD_BOTTOM_HEIGHT = 80
HUD_PANEL_WIDTH   = 260
HUD_PANEL_HEIGHT  = 200      # slightly taller to fit sprites
DICE_AREA_WIDTH   = 180
DICE_AREA_HEIGHT  = 120

# --- Sprite Settings ---
ICON_SIZE = 32   # 32x32px resource icons
SPRITE_SCALE = ICON_SIZE / 512  # source images are 512x512px

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
BTN_CARD        = (142, 68,  173)
BTN_ENDTURN     = (231, 76,  60)
TEXT_WHITE      = (255, 255, 255)
TEXT_LIGHT_GRAY = (180, 180, 180)
TEXT_GOLD       = (255, 215, 0)

# --- Resource Colors (still used for hex tiles on the board) ---
RESOURCE_COLORS = {
    "forest": (34,  139, 34),
    "wheat":  (255, 215, 0),
    "ore":    (112, 128, 144),
    "brick":  (178, 34,  34),
    "sheep":  (144, 238, 144),
    "desert": (210, 180, 140),
}

# --- Placeholder Player Data (will come from Apoorva's Player class later) ---
PLAYERS = [
    {"name": "Player 1", "color": (231, 76,  60),  "resources": {"brick": 0, "ore": 0, "wheat": 0, "sheep": 0, "forest": 0}, "vp": 0},
    {"name": "Player 2", "color": (39,  174, 96), "resources": {"brick": 0, "ore": 0, "wheat": 0, "sheep": 0, "forest": 0}, "vp": 0},
    {"name": "Player 3", "color": (219, 118, 51),  "resources": {"brick": 0, "ore": 0, "wheat": 0, "sheep": 0, "forest": 0}, "vp": 0},
    {"name": "Player 4", "color": (142, 68,  173), "resources": {"brick": 0, "ore": 0, "wheat": 0, "sheep": 0, "forest": 0}, "vp": 0},
]


# ---------------------------------------------------------------------------
# Helper: cubic tile coords -> screen pixels
# ---------------------------------------------------------------------------
def cubic_to_pixel(cx, cz, hex_size, origin_x, origin_y):
    """
    Flat-top hex layout conversion.
    When Nick's board is ready, loop over board.tiles.values() and pull
    cx/cz from each tile's .id tuple instead of TILE_DATA.
    """
    px = origin_x + hex_size * (3 / 2) * cx
    py = origin_y + hex_size * (math.sqrt(3) / 2 * cx + math.sqrt(3) * cz)
    return px, py


# ---------------------------------------------------------------------------
# Helper: 6 corners of a flat-top hex
# ---------------------------------------------------------------------------
def get_hex_corners(center_x, center_y, size):
    """
    Returns the 6 corner (x, y) points of a flat-top hexagon.
    Angles start at 0 degrees and go in 60 degree steps.
    """
    corners = []
    for i in range(6):
        angle_rad = math.radians(60 * i)
        corners.append((
            center_x + size * math.cos(angle_rad),
            center_y + size * math.sin(angle_rad),
        ))
    return corners


# ---------------------------------------------------------------------------
# Helper: flat filled/outlined rect using Arcade 3.x lrbt syntax
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

        # Track whose turn it is (index into PLAYERS list)
        # TODO: wire up to Amanda's turn logic later
        self.current_player_index = 0

        # --- Pre-build all Text objects (avoids draw_text performance warning) ---
        self._build_text_objects()

        # --- Load resource icon sprites ---
        self._load_resource_icons()

        self.board = CatanBoard()
        self.board.make_board()

    def _load_resource_icons(self):
        """
        Load each BW resource icon as an arcade.Sprite inside a SpriteList.
        Arcade 3.x requires sprites to live in a SpriteList to be drawn.
        """
        self.resource_icons = {}
        self.icon_sprite_list = arcade.SpriteList()
        resource_order = ["brick", "ore", "wheat", "sheep", "forest"]
        for res in resource_order:
            sprite = arcade.Sprite(RESOURCE_SPRITES[res], scale=SPRITE_SCALE)
            self.resource_icons[res] = sprite
            self.icon_sprite_list.append(sprite)

    def _build_text_objects(self):
        """
        Pre-create all arcade.Text objects used in the HUD.
        Call _update_text_objects() whenever the active player changes.
        """
        # Bottom bar button labels (static — never change)
        bar_center_y = HUD_BOTTOM_HEIGHT / 2
        btn_w = 150
        gap   = 20
        total_w = 3 * btn_w + 2 * gap
        start_x = (SCREEN_WIDTH - total_w) / 2

        self.txt_trade = arcade.Text("Trade",     start_x + btn_w * 0.5,              bar_center_y, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_build = arcade.Text("Build",     start_x + btn_w * 1.5 + gap,        bar_center_y, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_card  = arcade.Text("Play Card", start_x + btn_w * 2.5 + gap * 2,    bar_center_y, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_end   = arcade.Text("End Turn",  SCREEN_WIDTH - btn_w * 0.5 - 20,    bar_center_y, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")

        # Dice area label (static)
        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - 10
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - 10
        self.txt_dice_label   = arcade.Text("Dice Roll",            dx + DICE_AREA_WIDTH / 2, dy + DICE_AREA_HEIGHT - 18, TEXT_GOLD,       12, bold=True, anchor_x="center", font_name="MedievalSharp")
        self.txt_dice_hint    = arcade.Text("Auto-rolls on turn start", dx + DICE_AREA_WIDTH / 2, dy + 8,               TEXT_LIGHT_GRAY,  9,            anchor_x="center", font_name="MedievalSharp")
        self.txt_die1         = arcade.Text("?", dx + (DICE_AREA_WIDTH - 2*44 - 14) / 2 + 22,      dy + 24 + 22,        TEXT_WHITE,       20, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")
        self.txt_die2         = arcade.Text("?", dx + (DICE_AREA_WIDTH - 2*44 - 14) / 2 + 22 + 58, dy + 24 + 22,        TEXT_WHITE,       20, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")

        # Player panel — these change per player so we build them now and update later
        self._build_player_texts()

    def _build_player_texts(self):
        """
        Build/rebuild Text objects for the current player panel.
        Called on init and every time _end_turn() fires.
        """
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

        # Resource count labels — two columns, one per resource
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
    # Draw helpers
    # ---------------------------------------------------------------------------
    def _draw_bottom_bar(self):
        fill_rect(0, 0, SCREEN_WIDTH, HUD_BOTTOM_HEIGHT, HUD_BG)

        btn_w, btn_h = 150, 50
        gap = 20
        total_w = 3 * btn_w + 2 * gap
        start_x = (SCREEN_WIDTH - total_w) / 2
        btn_bottom = (HUD_BOTTOM_HEIGHT - btn_h) / 2

        fill_rect(start_x,                   btn_bottom, btn_w, btn_h, BTN_TRADE)
        fill_rect(start_x + btn_w + gap,     btn_bottom, btn_w, btn_h, BTN_BUILD)
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

        # Color dot next to name
        arcade.draw_circle_filled(px + 18, py + HUD_PANEL_HEIGHT - 22, 8, player["color"])

        self.txt_player_name.draw()
        self.txt_player_vp.draw()

        # Resource icons + count labels — two columns
        resource_order = ["brick", "ore", "wheat", "sheep", "forest"]
        col_x = [px + 12, px + 12 + HUD_PANEL_WIDTH // 2]
        row_start_y = py + HUD_PANEL_HEIGHT - 90

        for i, res in enumerate(resource_order):
            icon_x = col_x[i % 2] + ICON_SIZE / 2
            icon_y = row_start_y - (i // 2) * (ICON_SIZE + 6) + ICON_SIZE / 2

            # Position and draw the sprite
            sprite = self.resource_icons[res]
            sprite.center_x = icon_x
            sprite.center_y = icon_y
            pass  # drawn via sprite_list below

        # Draw all resource icons via SpriteList (required in Arcade 3.x)
        self.icon_sprite_list.draw()

        # Draw count labels separately (pre-built Text objects)
        for txt in self.txt_resources:
            txt.draw()

    def _draw_dice_area(self):
        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - 10
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - 10

        fill_rect(dx, dy, DICE_AREA_WIDTH, DICE_AREA_HEIGHT, HUD_PANEL_BG)
        outline_rect(dx, dy, DICE_AREA_WIDTH, DICE_AREA_HEIGHT, TEXT_LIGHT_GRAY)

        self.txt_dice_label.draw()
        self.txt_dice_hint.draw()

        # Two placeholder dice squares
        die_size = 44
        die_gap  = 14
        total_w  = 2 * die_size + die_gap
        die1_x   = dx + (DICE_AREA_WIDTH - total_w) / 2
        die_y    = dy + 24

        fill_rect(die1_x,              die_y, die_size, die_size, (60, 60, 90))
        fill_rect(die1_x + die_size + die_gap, die_y, die_size, die_size, (60, 60, 90))

        self.txt_die1.draw()
        self.txt_die2.draw()

    # ---------------------------------------------------------------------------
    # Arcade event loop
    # ---------------------------------------------------------------------------
    def on_draw(self):
        self.clear()

        # --- Draw the board ---
        for xyz, tile in self.board.tiles.items():
            cx, cy, cz = xyz
            px, py = cubic_to_pixel(cx, cz, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
            corners = get_hex_corners(px, py, HEX_SIZE)
            arcade.draw_polygon_filled(corners, RESOURCE_COLORS[tile.resource])
            arcade.draw_polygon_outline(corners, arcade.color.BLACK, 2)

        # --- Draw HUD ---
        self._draw_player_panel()
        self._draw_dice_area()
        self._draw_bottom_bar()

    def on_mouse_press(self, x, y, button, modifiers):
        """
        Skeleton click handler.
        TODO: Apoorva will flesh out node/edge detection here.
        TODO: Wire End Turn button to Amanda's turn logic.
        """
        btn_w = 150
        if (SCREEN_WIDTH - btn_w - 20 <= x <= SCREEN_WIDTH - 20) and (y <= HUD_BOTTOM_HEIGHT):
            self._end_turn()

    def _end_turn(self):
        """
        Advance to the next player.
        TODO: trigger resource production, dice roll animation, etc.
        """
        self.current_player_index = (self.current_player_index + 1) % len(PLAYERS)
        # Rebuild player text objects for the new active player
        self._build_player_texts()
        print(f"Turn ended. Now it's {PLAYERS[self.current_player_index]['name']}'s turn.")


def main():
    window = CatanWindow()
    arcade.run()


if __name__ == "__main__":
    main()