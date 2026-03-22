"""
# Stateless draw helper functions that wrap arcade calls:
# draw_settlement(), draw_road(), draw_number_token(), fill_rect(), outline_rect(), draw_port_label().
# Nothing here knows about game state.
"""
import math
import arcade
from .constants import *
from .board_utils import cubic_to_pixel, get_hex_corners

def draw_settlement(cx, cy, size, color):
    half = size / 2
    pts  = [(cx-half, cy-half), (cx+half, cy-half),
            (cx+half, cy+half), (cx-half, cy+half)]
    arcade.draw_polygon_filled(pts, color)
    arcade.draw_polygon_outline(pts, arcade.color.BLACK, 2)

def draw_city(cx, cy, size, color):
    half = size / 2
    pts  = [(cx-half, cy-half), (cx+half, cy-half),
            (cx+half, cy+half), (cx-half, cy+half)]
    arcade.draw_polygon_filled(pts, color)
    arcade.draw_polygon_outline(pts, arcade.color.BLACK, 2)
    # Add a smaller inner square to distinguish from settlement
    inner_half = size / 4
    inner_pts  = [(cx-inner_half, cy-inner_half), (cx+inner_half, cy-inner_half),
                  (cx+inner_half, cy+inner_half), (cx-inner_half, cy+inner_half)]
    arcade.draw_polygon_filled(inner_pts, TEXT_GOLD)

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


_OUTER_NEIGHBOR_OFFSETS = [
    (1, -1, 0),
    (1, 0, -1),
    (0, 1, -1),
    (-1, 1, 0),
    (-1, 0, 1),
    (0, -1, 1),
]


def _tile_ring_radius(xyz):
    x, y, z = xyz
    return max(abs(x), abs(y), abs(z))


def _draw_wave_band(y_base, time_s, amplitude, wavelength, thickness, color, speed, phase_shift=0.0):
    """Draw one wide, gently curving horizontal sea band."""
    step = 22
    points = []

    for x in range(-40, SCREEN_WIDTH + 41, step):
        y = (
            y_base
            + math.sin((x / wavelength) + time_s * speed + phase_shift) * amplitude
            + math.sin((x / (wavelength * 0.55)) + time_s * (speed * 0.6) + phase_shift * 1.7) * (amplitude * 0.25)
        )
        points.append((x, y))

    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        arcade.draw_line(x1, y1, x2, y2, color, thickness)


def draw_ocean_background(time_s: float):
    """Draw a more oceanic background with long swell bands instead of floating ovals."""
    fill_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, OCEAN_BASE_COLOR)

    # Deeper lower-water wash
    arcade.draw_lrbt_rectangle_filled(
        0, SCREEN_WIDTH, 0, SCREEN_HEIGHT * 0.42, OCEAN_DEEP_COLOR
    )

    # Slight brighter upper-water wash
    arcade.draw_lrbt_rectangle_filled(
        0, SCREEN_WIDTH, SCREEN_HEIGHT * 0.52, SCREEN_HEIGHT, OCEAN_MID_COLOR
    )

    # Main long swell bands
    for i in range(OCEAN_BAND_COUNT):
        y = SCREEN_HEIGHT - 40 - i * OCEAN_BAND_SPACING
        _draw_wave_band(
            y_base=y,
            time_s=time_s,
            amplitude=OCEAN_BAND_AMPLITUDE,
            wavelength=OCEAN_BAND_WAVELENGTH,
            thickness=OCEAN_BAND_THICKNESS,
            color=OCEAN_BAND_COLOR,
            speed=OCEAN_BAND_PHASE_SPEED,
            phase_shift=i * 0.95,
        )

    # Fainter secondary ripples to break up the water
    for i in range(OCEAN_RIPPLE_COUNT):
        y = SCREEN_HEIGHT - 80 - i * OCEAN_RIPPLE_SPACING + math.sin(time_s * 0.35 + i) * 8
        _draw_wave_band(
            y_base=y,
            time_s=time_s + i * 0.4,
            amplitude=OCEAN_RIPPLE_AMPLITUDE,
            wavelength=OCEAN_RIPPLE_WAVELENGTH,
            thickness=OCEAN_RIPPLE_THICKNESS,
            color=OCEAN_RIPPLE_COLOR,
            speed=0.55,
            phase_shift=i * 1.35,
        )


def draw_shoreline_shimmer(board, time_s: float):
    """Draw foam only on the true outer coastline, not inward-facing gaps."""
    tile_coords = set(board.tiles.keys())
    max_ring = max(_tile_ring_radius(xyz) for xyz in tile_coords)

    for xyz, tile in board.tiles.items():
        cx, _, cz = xyz
        px, py = cubic_to_pixel(cx, cz, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
        corners = get_hex_corners(px, py, HEX_SIZE)
        tile_ring = _tile_ring_radius(xyz)

        for side_index, offset in enumerate(_OUTER_NEIGHBOR_OFFSETS):
            neighbor_xyz = (cx + offset[0], xyz[1] + offset[1], cz + offset[2])

            # If a tile exists there, this is not coastline.
            if neighbor_xyz in tile_coords:
                continue

            # Only allow shimmer on edges that face outward from the island's
            # maximum ring. This prevents flashing on inward-facing gaps.
            neighbor_ring = _tile_ring_radius(neighbor_xyz)
            if SHORE_OUTER_RING_ONLY and neighbor_ring <= tile_ring:
                continue
            if SHORE_OUTER_RING_ONLY and tile_ring < max_ring - 1:
                continue

            x1, y1 = corners[side_index]
            x2, y2 = corners[(side_index + 1) % 6]

            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2

            vec_x = mid_x - px
            vec_y = mid_y - py
            length = math.hypot(vec_x, vec_y) or 1.0
            off_x = vec_x / length * SHORE_FOAM_OFFSET
            off_y = vec_y / length * SHORE_FOAM_OFFSET

            phase = (
                time_s * SHORE_FOAM_PULSE_SPEED
                + side_index * 0.9
                + cx * 0.45
                + cz * 0.45
            )

            foam_alpha = int(
                SHORE_FOAM_COLOR[3] * (0.55 + 0.45 * math.sin(phase))
            )
            hi_alpha = int(
                SHORE_FOAM_HIGHLIGHT_COLOR[3] * (0.48 + 0.52 * math.sin(phase + 0.8))
            )

            arcade.draw_line(
                x1 + off_x,
                y1 + off_y,
                x2 + off_x,
                y2 + off_y,
                (*SHORE_FOAM_COLOR[:3], foam_alpha),
                SHORE_FOAM_WIDTH,
            )

            arcade.draw_line(
                x1 + off_x,
                y1 + off_y,
                x2 + off_x,
                y2 + off_y,
                (*SHORE_FOAM_HIGHLIGHT_COLOR[:3], hi_alpha),
                SHORE_FOAM_HIGHLIGHT_WIDTH,
            )


def draw_shoreline_shimmer(board, time_s: float):
    """Draw a faint foam shimmer only along the outer ring of land hexes."""
    tile_coords = set(board.tiles.keys())

    for xyz, tile in board.tiles.items():
        cx, _, cz = xyz
        px, py = cubic_to_pixel(cx, cz, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
        corners = get_hex_corners(px, py, HEX_SIZE)

        for side_index, offset in enumerate(_OUTER_NEIGHBOR_OFFSETS):
            neighbor_xyz = (cx + offset[0], xyz[1] + offset[1], cz + offset[2])

            # Only shimmer on edges exposed to the ocean
            if neighbor_xyz in tile_coords:
                continue

            x1, y1 = corners[side_index]
            x2, y2 = corners[(side_index + 1) % 6]

            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2

            # Push the foam slightly outward away from the tile center
            vec_x = mid_x - px
            vec_y = mid_y - py
            length = math.hypot(vec_x, vec_y) or 1.0
            off_x = vec_x / length * SHORE_FOAM_OFFSET
            off_y = vec_y / length * SHORE_FOAM_OFFSET

            phase = (
                time_s * SHORE_FOAM_PULSE_SPEED
                + side_index * 0.85
                + cx * 0.55
                + cz * 0.55
            )

            foam_alpha = int(
                SHORE_FOAM_COLOR[3] * (0.58 + 0.42 * math.sin(phase))
            )
            hi_alpha = int(
                SHORE_FOAM_HIGHLIGHT_COLOR[3] * (0.50 + 0.50 * math.sin(phase + 0.9))
            )

            arcade.draw_line(
                x1 + off_x,
                y1 + off_y,
                x2 + off_x,
                y2 + off_y,
                (*SHORE_FOAM_COLOR[:3], foam_alpha),
                SHORE_FOAM_WIDTH,
            )

            arcade.draw_line(
                x1 + off_x,
                y1 + off_y,
                x2 + off_x,
                y2 + off_y,
                (*SHORE_FOAM_HIGHLIGHT_COLOR[:3], hi_alpha),
                SHORE_FOAM_HIGHLIGHT_WIDTH,
            )


_HEX_SPRITE_CACHE = {}

def _get_hex_sprite(resource_name: str):
    """Load and cache a hex texture sprite for a given resource."""
    path = HEX_TILE_SPRITES.get(resource_name)
    if not path:
        return None

    sprite = _HEX_SPRITE_CACHE.get(resource_name)
    if sprite is None:
        try:
            sprite = arcade.Sprite(path)
            _HEX_SPRITE_CACHE[resource_name] = sprite
        except Exception:
            _HEX_SPRITE_CACHE[resource_name] = None
            return None

    return sprite


def draw_board(board):
    for xyz, tile in board.tiles.items():
        cx, _, cz = xyz
        px, py = cubic_to_pixel(cx, cz, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
        corners = get_hex_corners(px, py, HEX_SIZE)

        sprite = _get_hex_sprite(tile.resource)

        if sprite is not None:
            # Uniform scaling preserves the image proportions better than forcing
            # width/height independently.
            sprite.scale = HEX_TILE_SCALE
            sprite.center_x = px
            sprite.center_y = py + HEX_TILE_Y_OFFSET
            arcade.draw_sprite(sprite)

        else:
            # Fallback to the old flat color if a sprite is missing
            arcade.draw_polygon_filled(corners, RESOURCE_COLORS[tile.resource])

        arcade.draw_polygon_outline(corners, arcade.color.BLACK, HEX_TILE_OUTLINE_WIDTH)

        # Number token (skip desert, which has number=0)
        if tile.number > 0:
            draw_number_token(px, py, tile.number)