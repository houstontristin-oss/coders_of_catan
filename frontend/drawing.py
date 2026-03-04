"""
# Stateless draw helper functions that wrap arcade calls:
# draw_settlement(), draw_road(), draw_number_token(), fill_rect(), outline_rect(), draw_port_label().
# Nothing here knows about game state.
"""
import arcade
from .constants import TOKEN_RED, TEXT_GOLD, HEX_SIZE, RESOURCE_COLORS, BOARD_CENTER_X, BOARD_CENTER_Y
from .board_utils import cubic_to_pixel, get_hex_corners

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
            cx, _, cz = xyz
            px, py = cubic_to_pixel(cx, cz, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
            corners = get_hex_corners(px, py, HEX_SIZE)
            arcade.draw_polygon_filled(corners, RESOURCE_COLORS[tile.resource])
            arcade.draw_polygon_outline(corners, arcade.color.BLACK, 2)
            # Number token (skip desert, which has number=0)
            if tile.number > 0:
                draw_number_token(px, py, tile.number)