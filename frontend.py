import arcade
import math

# Click detection / node highlighting — needs Apoorva
# Actual settlement and road sprites appearing on nodes/edges — needs Nick's edges to exist
# Wiring cubic_to_pixel to Nick's real board object — needs Nick's full 19-tile initialization

# --- Window Settings ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Coders of Catan"

# --- Hex Settings ---
HEX_SIZE = 65  # radius from center to corner

# --- Board Center (screen pixels) ---
BOARD_CENTER_X = SCREEN_WIDTH / 2
BOARD_CENTER_Y = SCREEN_HEIGHT / 2

# --- HUD Dimensions ---
HUD_BOTTOM_HEIGHT = 80
HUD_PANEL_WIDTH   = 260
HUD_PANEL_HEIGHT  = 160
DICE_AREA_WIDTH   = 180
DICE_AREA_HEIGHT  = 120

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

# --- Resource Colors ---
RESOURCE_COLORS = {
    "forest": (34,  139, 34),
    "wheat":  (255, 215, 0),
    "ore":    (112, 128, 144),
    "brick":  (178, 34,  34),
    "sheep":  (144, 238, 144),
    "desert": (210, 180, 140),
}

# All 19 Tiles: (cubic_x, cubic_y, cubic_z, resource)
# Cubic coordinates from the drawn up blueprint, with a standard Catan resource layout
TILE_DATA = [  # Temporary stand-in for Nick's board function
    # Top row (3 tiles)
    (-2,  0,  2, "forest"),
    (-2,  1,  1, "wheat"),
    (-2,  2,  0, "ore"),
    # Second row (4 tiles)
    (-1, -1,  2, "wheat"),
    (-1,  0,  1, "forest"),
    (-1,  1,  0, "brick"),
    (-1,  2, -1, "sheep"),
    # Middle row (5 tiles)
    ( 0, -2,  2, "forest"),
    ( 0, -1,  1, "brick"),
    ( 0,  0,  0, "desert"),  # center tile — always desert
    ( 0,  1, -1, "wheat"),
    ( 0,  2, -2, "sheep"),
    # Fourth row (4 tiles)
    ( 1, -2,  1, "ore"),
    ( 1, -1,  0, "sheep"),
    ( 1,  0, -1, "forest"),
    ( 1,  1, -2, "wheat"),
    # Bottom row (3 tiles)
    ( 2, -2,  0, "ore"),
    ( 2, -1, -1, "brick"),
    ( 2,  0, -2, "sheep"),
]

# --- Placeholder Player Data (will come from Apoorva's Player class later) ---
PLAYERS = [
    {"name": "Player 1", "color": (231, 76,  60),  "resources": {"brick": 0, "ore": 0, "wheat": 0, "sheep": 0, "forest": 0}, "vp": 0},
    {"name": "Player 2", "color": (52,  152, 219), "resources": {"brick": 0, "ore": 0, "wheat": 0, "sheep": 0, "forest": 0}, "vp": 0},
    {"name": "Player 3", "color": (39,  174, 96),  "resources": {"brick": 0, "ore": 0, "wheat": 0, "sheep": 0, "forest": 0}, "vp": 0},
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
# Helper: flat filled rect using Arcade 3.x lrbt syntax
# ---------------------------------------------------------------------------
def fill_rect(left, bottom, width, height, color):
    arcade.draw_lrbt_rectangle_filled(left, left + width, bottom, bottom + height, color)

def outline_rect(left, bottom, width, height, color, border=2):
    arcade.draw_lrbt_rectangle_outline(left, left + width, bottom, bottom + height, color, border)


# ---------------------------------------------------------------------------
# Draw: bottom HUD action bar — Trade / Build / Play Card / End Turn
# ---------------------------------------------------------------------------
def draw_bottom_bar(screen_width):
    # Background strip
    fill_rect(0, 0, screen_width, HUD_BOTTOM_HEIGHT, HUD_BG)

    btn_w, btn_h = 150, 50
    gap = 20
    bar_center_y = HUD_BOTTOM_HEIGHT / 2
    btn_bottom = bar_center_y - btn_h / 2

    total_w = 3 * btn_w + 2 * gap
    start_x = (screen_width - total_w) / 2

    buttons = [
        (start_x,                   BTN_TRADE,   "Trade"),
        (start_x + btn_w + gap,     BTN_BUILD,   "Build"),
        (start_x + 2*(btn_w + gap), BTN_CARD,    "Play Card"),
    ]

    for bx, color, label in buttons:
        fill_rect(bx, btn_bottom, btn_w, btn_h, color)
        arcade.draw_text(
            label,
            bx + btn_w / 2, bar_center_y,
            TEXT_WHITE, font_size=13, bold=True,
            anchor_x="center", anchor_y="center"
        )

    # End Turn — right side
    et_x = screen_width - btn_w - 20
    fill_rect(et_x, btn_bottom, btn_w, btn_h, BTN_ENDTURN)
    arcade.draw_text(
        "End Turn",
        et_x + btn_w / 2, bar_center_y,
        TEXT_WHITE, font_size=13, bold=True,
        anchor_x="center", anchor_y="center"
    )


# ---------------------------------------------------------------------------
# Draw: top-left player info panel
# ---------------------------------------------------------------------------
def draw_player_panel(player, screen_height):
    px = 10
    py = screen_height - HUD_PANEL_HEIGHT - 10

    fill_rect(px, py, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, HUD_PANEL_BG)
    outline_rect(px, py, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, player["color"])

    # Player name + color dot
    arcade.draw_circle_filled(px + 18, py + HUD_PANEL_HEIGHT - 22, 8, player["color"])
    arcade.draw_text(
        player["name"],
        px + 32, py + HUD_PANEL_HEIGHT - 22,
        TEXT_GOLD, font_size=14, bold=True, anchor_y="center"
    )

    # Victory points
    arcade.draw_text(
        f"Victory Points: {player['vp']}",
        px + 12, py + HUD_PANEL_HEIGHT - 48,
        TEXT_LIGHT_GRAY, font_size=11
    )

    # Resource counts — two columns
    resource_order  = ["brick", "ore", "wheat", "sheep", "forest"]
    resource_labels = {"brick": "Brick", "ore": "Ore", "wheat": "Wheat", "sheep": "Sheep", "forest": "Wood"}
    row_start_y = py + HUD_PANEL_HEIGHT - 72
    col_x = [px + 12, px + 12 + HUD_PANEL_WIDTH // 2]

    for i, res in enumerate(resource_order):
        rx = col_x[i % 2]
        ry = row_start_y - (i // 2) * 24
        arcade.draw_circle_filled(rx + 6, ry + 6, 6, RESOURCE_COLORS[res])
        arcade.draw_text(
            f"{resource_labels[res]}: {player['resources'][res]}",
            rx + 16, ry,
            TEXT_WHITE, font_size=10
        )


# ---------------------------------------------------------------------------
# Draw: top-right dice area (placeholder — Sprint 2 wires up animation)
# ---------------------------------------------------------------------------
def draw_dice_area(screen_width, screen_height):
    dx = screen_width - DICE_AREA_WIDTH - 10
    dy = screen_height - DICE_AREA_HEIGHT - 10

    fill_rect(dx, dy, DICE_AREA_WIDTH, DICE_AREA_HEIGHT, HUD_PANEL_BG)
    outline_rect(dx, dy, DICE_AREA_WIDTH, DICE_AREA_HEIGHT, TEXT_LIGHT_GRAY)

    arcade.draw_text(
        "Dice Roll",
        dx + DICE_AREA_WIDTH / 2, dy + DICE_AREA_HEIGHT - 18,
        TEXT_GOLD, font_size=12, bold=True, anchor_x="center"
    )

    # Two placeholder dice squares
    die_size = 44
    die_gap  = 14
    total_w  = 2 * die_size + die_gap
    die1_x   = dx + (DICE_AREA_WIDTH - total_w) / 2
    die_y    = dy + 24

    for i in range(2):
        ddx = die1_x + i * (die_size + die_gap)
        fill_rect(ddx, die_y, die_size, die_size, (60, 60, 90))
        arcade.draw_text(
            "?",
            ddx + die_size / 2, die_y + die_size / 2,
            TEXT_WHITE, font_size=20, bold=True,
            anchor_x="center", anchor_y="center"
        )

    arcade.draw_text(
        "Auto-rolls on turn start",
        dx + DICE_AREA_WIDTH / 2, dy + 8,
        TEXT_LIGHT_GRAY, font_size=9, anchor_x="center"
    )


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------
class CatanWindow(arcade.Window):

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.OCEAN_BOAT_BLUE)

        # Track whose turn it is (index into PLAYERS list)
        # TODO: wire up to Amanda's turn logic later
        self.current_player_index = 0

    def on_draw(self):
        self.clear()

        # --- Draw the board ---
        for (cx, cy, cz, resource) in TILE_DATA:
            # Convert cubic coords to screen pixels
            px, py = cubic_to_pixel(cx, cz, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
            corners = get_hex_corners(px, py, HEX_SIZE)
            arcade.draw_polygon_filled(corners, RESOURCE_COLORS[resource])
            arcade.draw_polygon_outline(corners, arcade.color.BLACK, 2)

        # --- Draw HUD ---
        current_player = PLAYERS[self.current_player_index]
        draw_player_panel(current_player, SCREEN_HEIGHT)
        draw_dice_area(SCREEN_WIDTH, SCREEN_HEIGHT)
        draw_bottom_bar(SCREEN_WIDTH)

    def on_mouse_press(self, x, y, button, modifiers):
        """
        Skeleton click handler.
        TODO: Apoorva will flesh out node/edge detection here.
        TODO: Wire End Turn button to Amanda's turn logic.
        """
        # End Turn button bounds
        if (SCREEN_WIDTH - 170 <= x <= SCREEN_WIDTH - 20) and (y <= HUD_BOTTOM_HEIGHT):
            self._end_turn()

    def _end_turn(self):
        """
        Advance to the next player.
        TODO: trigger resource production, dice roll animation, etc.
        """
        self.current_player_index = (self.current_player_index + 1) % len(PLAYERS)
        print(f"Turn ended. Now it's {PLAYERS[self.current_player_index]['name']}'s turn.")


def main():
    window = CatanWindow()
    arcade.run()


if __name__ == "__main__":
    main()