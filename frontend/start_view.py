"""
Contains StartView class — start screen with sunset background, animated sun,
watercolor farmscape, and golden Catan-style title.
"""
import math
import random
import arcade
from backend.catan_board import CatanBoard
from backend.player import Player
from .constants import (SCREEN_HEIGHT, SCREEN_WIDTH,
                        TEXT_GOLD, RESOURCE_ABBR, ONE, SIX)
from .drawing import fill_rect, outline_rect
from .view_constants import *


# ---------------------------------------------------------------------------
# Internal drawing helpers — all pure arcade calls, no game state
def _draw_sunset_gradient():
    for (bottom_frac, top_frac, color) in START_GRAD_BANDS:
        y_bot = SCREEN_HEIGHT * bottom_frac
        y_top = SCREEN_HEIGHT * top_frac
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, y_bot, y_top, color)


def _draw_sun(time_s: float):
    """Draw the sun with slow pulsing glow and rotating rays."""
    pulse = 0.85 + 0.15 * math.sin(time_s * 1.1)
    glow_r = START_SUN_GLOW_RADIUS * pulse

    # Outer haze layers
    arcade.draw_circle_filled(START_SUN_X, START_SUN_Y, glow_r * 1.6,
                               (*START_SUN_GLOW_COLOR[:3], 28))
    arcade.draw_circle_filled(START_SUN_X, START_SUN_Y, glow_r * 1.2,
                               (*START_SUN_GLOW_COLOR[:3], 55))
    arcade.draw_circle_filled(START_SUN_X, START_SUN_Y, glow_r,
                               (*START_SUN_GLOW_COLOR[:3], 90))

    # Slowly rotating rays
    ray_angle_offset = time_s * 4.0
    for i in range(START_SUN_RAY_COUNT):
        angle = math.radians(i * (360 / START_SUN_RAY_COUNT) + ray_angle_offset)
        ray_pulse = 0.8 + 0.2 * math.sin(time_s * 2.0 + i * 0.7)
        inner_r = START_SUN_RADIUS * 1.08
        outer_r = inner_r + START_SUN_RAY_LEN * ray_pulse
        x1 = START_SUN_X + math.cos(angle) * inner_r
        y1 = START_SUN_Y + math.sin(angle) * inner_r
        x2 = START_SUN_X + math.cos(angle) * outer_r
        y2 = START_SUN_Y + math.sin(angle) * outer_r
        arcade.draw_line(x1, y1, x2, y2,
                         (*START_SUN_RAY_COLOR[:3], 160), START_SUN_RAY_WIDTH)

    # Core disc
    arcade.draw_circle_filled(START_SUN_X, START_SUN_Y,
                               START_SUN_RADIUS, START_SUN_COLOR)
    # Bright highlight spot
    arcade.draw_circle_filled(START_SUN_X + START_SUN_RADIUS * 0.22,
                               START_SUN_Y + START_SUN_RADIUS * 0.22,
                               START_SUN_RADIUS * 0.32,
                               (255, 255, 220, 120))


def _draw_horizon_water(time_s: float):
    W = SCREEN_WIDTH

    # Base water band
    arcade.draw_lrbt_rectangle_filled(
        0, W,
        START_WATER_BOTTOM_Y, START_WATER_TOP_Y,
        START_WATER_DARK_COLOR
    )
    arcade.draw_lrbt_rectangle_filled(
        0, W,
        START_WATER_BOTTOM_Y + 6, START_WATER_TOP_Y - 2,
        START_WATER_COLOR
    )

    # Soft wave lines
    for i in range(START_WATER_WAVE_COUNT):
        y_base = START_WATER_BOTTOM_Y + 10 + i * START_WATER_WAVE_SPACING
        prev = None
        for x in range(-20, W + 21, 14):
            y = y_base + math.sin(x / 55.0 + time_s * 1.3 + i * 0.8) * START_WATER_WAVE_AMPLITUDE
            if prev is not None:
                arcade.draw_line(
                    prev[0], prev[1], x, y,
                    START_WATER_FOAM_COLOR,
                    START_WATER_WAVE_THICKNESS
                )
            prev = (x, y)


def _draw_sheep():
    W = SCREEN_WIDTH
    H = START_FARM_HORIZON_Y

    cx = W * START_SHEEP_X_FRAC
    cy = H * START_SHEEP_Y_FRAC

    # Legs
    for lx in (-10, -4, 5, 11):
        arcade.draw_line(cx + lx, cy - 10, cx + lx, cy - 22, START_SHEEP_LEG_COLOR, 2)

    # Body
    arcade.draw_circle_filled(cx - 10, cy, 10, START_SHEEP_BODY_COLOR)
    arcade.draw_circle_filled(cx,      cy + 2, 12, START_SHEEP_BODY_COLOR)
    arcade.draw_circle_filled(cx + 11, cy, 10, START_SHEEP_BODY_COLOR)

    # Soft wool shadow
    arcade.draw_circle_filled(cx - 3, cy - 2, 10, START_SHEEP_WOOL_SHADOW)

    # Head
    arcade.draw_ellipse_filled(cx + 20, cy - 2, 13, 11, START_SHEEP_FACE_COLOR)

    # Ear
    arcade.draw_triangle_filled(
        cx + 23, cy + 4,
        cx + 29, cy + 8,
        cx + 24, cy + 1,
        START_SHEEP_FACE_COLOR
    )
    # Eye
    arcade.draw_circle_filled(cx + 23, cy, 1.4, (245, 245, 245, 255))


def _draw_farmscape(time_s: float):
    H = START_FARM_HORIZON_Y
    W = SCREEN_WIDTH

    # Ground fill — two-tone rolling fields
    arcade.draw_lrbt_rectangle_filled(0, W, 0, H * 0.30,
                                       START_FARM_FIELD_DARK_COLOR)
    arcade.draw_lrbt_rectangle_filled(0, W, H * 0.28, H * 0.68,
                                       START_FARM_FIELD_COLOR)
    _draw_horizon_water(time_s)

    # Rolling hill silhouettes at horizon (first layer)
    hill_pts = []
    steps = 60
    for s in range(steps + 1):
        fx = s / steps * W
        fy = H * 0.72 + math.sin(fx / 160.0) * 18 + math.sin(fx / 70.0) * 8
        hill_pts.append((fx, fy))
    hill_pts.append((W, 0))
    hill_pts.append((0, 0))
    arcade.draw_polygon_filled(hill_pts, (*START_FARM_FIELD_COLOR[:3], 160))

    # Second softer hill layer
    hill2_pts = []
    for s in range(steps + 1):
        fx = s / steps * W
        fy = (H * 0.80 + math.sin(fx / 200.0 + 1.2) * 14
              + math.sin(fx / 90.0 + 0.5) * 6)
        hill2_pts.append((fx, fy))
    hill2_pts.append((W, 0))
    hill2_pts.append((0, 0))
    arcade.draw_polygon_filled(hill2_pts, (*START_FARM_FIELD_DARK_COLOR[:3], 230))

    # Fence line
    fence_y = H * 0.52
    fence_color = (110, 70, 40, 240)
    post_gap = 55
    for px in range(20, W, post_gap):
        arcade.draw_line(px, fence_y - 10, px, fence_y + 12, fence_color, 3)
    arcade.draw_line(20, fence_y + 4, W - 20, fence_y + 4, fence_color, 2)
    arcade.draw_line(20, fence_y - 4, W - 20, fence_y - 4, fence_color, 2)

    # Barn (left-center)
    bx, by = W * 0.24, H * 0.10
    bw, bh = 110, 70
    arcade.draw_lrbt_rectangle_filled(bx, bx + bw, by, by + bh,
                                       START_FARM_BARN_COLOR)
    arcade.draw_lrbt_rectangle_outline(bx, bx + bw, by, by + bh,
                                        START_FARM_BARN_DARK_COLOR, 2)
    roof_pts = [(bx - 8, by + bh),
                (bx + bw / 2, by + bh + 44),
                (bx + bw + 8, by + bh)]
    arcade.draw_polygon_filled(roof_pts, START_FARM_ROOF_COLOR)
    arcade.draw_polygon_outline(roof_pts, START_FARM_BARN_DARK_COLOR, 2)
    dw, dh = 22, 32
    dx = bx + bw / 2 - dw / 2
    arcade.draw_lrbt_rectangle_filled(dx, dx + dw, by, by + dh,
                                       START_FARM_BARN_DARK_COLOR)
    arcade.draw_lrbt_rectangle_filled(bx + 12, bx + 32, by + bh - 28,
                                       by + bh - 14, (200, 220, 255, 255))
    arcade.draw_lrbt_rectangle_outline(bx + 12, bx + 32, by + bh - 28,
                                        by + bh - 14, START_FARM_BARN_DARK_COLOR, 2)

    # Silo (right of barn)
    silo_cx = bx + bw + 38
    silo_base_y = by
    silo_w = 40
    silo_h = 80
    arcade.draw_lrbt_rectangle_filled(
        silo_cx - silo_w / 2, silo_cx + silo_w / 2,
        silo_base_y, silo_base_y + silo_h, START_FARM_SILO_COLOR)
    arcade.draw_lrbt_rectangle_outline(
        silo_cx - silo_w / 2, silo_cx + silo_w / 2,
        silo_base_y, silo_base_y + silo_h, START_FARM_SILO_DARK_COLOR, 2)
    arcade.draw_ellipse_filled(silo_cx, silo_base_y + silo_h,
                                silo_w, silo_w * 0.4, START_FARM_SILO_DARK_COLOR)

    # Trees — rounded painterly canopy blobs
    tree_positions = [
        (W * 0.06,  H * 0.28, 26, 50),
        (W * 0.10,  H * 0.32, 22, 44),
        (W * 0.55,  H * 0.30, 28, 54),
        (W * 0.60,  H * 0.26, 24, 48),
        (W * 0.64,  H * 0.34, 20, 40),
        (W * 0.80,  H * 0.28, 30, 58),
        (W * 0.85,  H * 0.30, 24, 46),
        (W * 0.90,  H * 0.25, 20, 42),
        (W * 0.95,  H * 0.32, 18, 36),
    ]
    for tx, ty, tr, th in tree_positions:
        trunk_half_w = 3.5
        trunk_bot = ty
        trunk_top = ty + th * 0.44
        arcade.draw_lrbt_rectangle_filled(
            tx - trunk_half_w, tx + trunk_half_w,
            trunk_bot, trunk_top,
            (90, 55, 25, 245))
        arcade.draw_circle_filled(tx, ty + th * 0.72, tr * 1.0,
                                   (*START_FARM_TREE_DARK_COLOR[:3], 245))
        arcade.draw_circle_filled(tx - tr * 0.3, ty + th * 0.78, tr * 0.75,
                                   (*START_FARM_TREE_COLOR[:3], 245))
        arcade.draw_circle_filled(tx + tr * 0.25, ty + th * 0.82, tr * 0.65,
                                   (*START_FARM_TREE_COLOR[:3], 245))
        arcade.draw_circle_filled(tx, ty + th * 0.90, tr * 0.5,
                                   (200, 230, 140, 230))

    # Wheat field rows (right side)
    wf_x = W * 0.38
    wf_w = W * 0.16
    wf_y_base = H * 0.14
    wheat_color = (210, 170, 60, 180)
    for row in range(6):
        ry = wf_y_base + row * 12
        for stalk in range(int(wf_w / 9)):
            sx2 = wf_x + stalk * 9 + (row % 2) * 4
            arcade.draw_line(sx2, ry, sx2, ry + 14, wheat_color, 2)
            arcade.draw_circle_filled(sx2, ry + 16, 2.5, (230, 195, 80, 151))

    _draw_sheep()

    # Horizon glow — fades farmscape softly into sky
    for i in range(10):
        alpha = int(120 * (i / 10.0))
        y_strip = H - i * (H / 10.0)
        arcade.draw_lrbt_rectangle_filled(
            0, W, y_strip - H / 10.0, y_strip,
            (255, 160, 60, alpha)
        )


def _draw_clouds(time_s: float):
    cloud_defs = [
        (0.08, 0.86, 12.0, 1.1),
        (0.30, 0.91, 8.0,  0.9),
        (0.55, 0.88, 14.0, 1.3),
        (0.75, 0.93, 9.0,  0.8),
        (0.90, 0.87, 11.0, 1.0),
    ]
    for base_x_frac, y_frac, speed, scale in cloud_defs:
        cx = (base_x_frac * SCREEN_WIDTH + time_s * speed) % (SCREEN_WIDTH + 200) - 100
        cy = SCREEN_HEIGHT * y_frac
        r = 28 * scale
        for ox, oy, rx, ry, a in [
            (0,          0,    r * 1.8, r * 0.7, 80),
            (-r * 0.7, r * 0.3, r * 1.1, r * 0.65, 65),
            ( r * 0.7, r * 0.3, r * 1.0, r * 0.60, 65),
        ]:
            arcade.draw_ellipse_filled(cx + ox, cy + oy, rx * 2, ry * 2,
                                        (*START_FARM_CLOUD_COLOR[:3], a))


def _draw_title():
    """Golden shadowed title and subtitle text."""
    # Drop shadow
    arcade.Text(
        "Coders of Catan",
        SCREEN_WIDTH / 2 + 3, START_TITLE_Y - 3,
        (60, 20, 0, 200), START_TITLE_FONT_SIZE,
        bold=True, font_name="MedievalSharp",
        anchor_x="center", anchor_y="center",
    ).draw()
    # Golden title
    arcade.Text(
        "Coders of Catan",
        SCREEN_WIDTH / 2, START_TITLE_Y,
        TEXT_GOLD, START_TITLE_FONT_SIZE,
        bold=True, font_name="MedievalSharp",
        anchor_x="center", anchor_y="center",
    ).draw()
    # Subtitle
    arcade.Text(
        "Click anywhere to begin",
        SCREEN_WIDTH / 2, START_SUBTITLE_Y,
        (184, 137, 44, 255), START_SUBTITLE_FONT_SIZE,
        font_name="MedievalSharp",
        anchor_x="center", anchor_y="center",
    ).draw()


def _draw_skip_button(txt_skip):
    fill_rect(START_SKIP_BTN_X, START_SKIP_BTN_Y,
              START_SKIP_BTN_W, START_SKIP_BTN_H, (20, 20, 50, 230))
    outline_rect(START_SKIP_BTN_X, START_SKIP_BTN_Y,
                 START_SKIP_BTN_W, START_SKIP_BTN_H, TEXT_GOLD, 2)
    txt_skip.draw()


# ---------------------------------------------------------------------------
# Auto-setup helper
def _auto_place_setup(board, players):
    """
    Place 2 settlements + 2 roads per player in snake order and award
    second-settlement starting resources.
    """
    pip_map = {2:1, 3:2, 4:3, 5:4, 6:5, 8:5, 9:4, 10:3, 11:2, 12:1}

    def node_score(node):
        return sum(pip_map.get(t.number, 0)
                   for t in node.tiles if t.resource != "desert")

    def distance_ok(node):
        for edge in node.edges:
            for nbr in edge.nodes:
                if nbr is not node and nbr.player is not None:
                    return False
        return True

    def place_settlement(node, player_idx):
        node.player   = player_idx
        node.building = "settlement"
        players[player_idx].total_settlements -= 1
        players[player_idx].victory_points    += 1

    def place_road(edge, player_idx):
        edge.player = player_idx
        players[player_idx].total_roads -= 1

    def best_free_node():
        candidates = [n for n in board.nodes.values()
                      if n.player is None and distance_ok(n)]
        return max(candidates, key=node_score, default=None)

    def best_adjacent_edge(node, _player_idx):
        free_edges = [e for e in node.edges if e.player is None]
        return max(free_edges,
                   key=lambda e: sum(node_score(n) for n in e.nodes),
                   default=None)

    snake = [0, 1, 2, 3, 3, 2, 1, 0]
    second_settlement_nodes = {}

    for turn_idx, player_idx in enumerate(snake):
        node = best_free_node()
        if node is None:
            break
        place_settlement(node, player_idx)
        edge = best_adjacent_edge(node, player_idx)
        if edge:
            place_road(edge, player_idx)
        if turn_idx >= 4:
            second_settlement_nodes[player_idx] = node

    for player_idx, node in second_settlement_nodes.items():
        for tile in node.tiles:
            if tile.resource != "desert":
                key = RESOURCE_ABBR.get(tile.resource)
                if key:
                    players[player_idx].resource_cards[key] += 1


# ---------------------------------------------------------------------------
# StartView
class StartView(arcade.View):
    """Animated start screen — sunset sky, sun, farmscape, golden title."""

    def __init__(self, vm):
        super().__init__()
        self.vm = vm
        self._time = 0.0
        self._build_text_objects()

    def _build_text_objects(self):
        btn_cx = START_SKIP_BTN_X + START_SKIP_BTN_W / 2
        btn_cy = START_SKIP_BTN_Y + START_SKIP_BTN_H / 2
        self.txt_skip = arcade.Text(
            "Skip Setup  ▶",
            btn_cx, btn_cy,
            TEXT_GOLD, 13,
            bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

    # ------------------------------------------------------------------
    def on_update(self, delta_time: float):
        self._time += delta_time

    def on_draw(self):
        self.clear()
        _draw_sunset_gradient()      # 1. Sky
        _draw_clouds(self._time)     # 2. Drifting clouds
        _draw_sun(self._time)        # 3. Animated sun
        _draw_farmscape(self._time)            # 4. Farmscape (fades at horizon)
        _draw_title()                # 5. Title + subtitle
        _draw_skip_button(self.txt_skip)  # 6. Skip button

    # ------------------------------------------------------------------
    def _skip_button_hit(self, x, y) -> bool:
        return (START_SKIP_BTN_X <= x <= START_SKIP_BTN_X + START_SKIP_BTN_W and
                START_SKIP_BTN_Y <= y <= START_SKIP_BTN_Y + START_SKIP_BTN_H)

    def _make_board_and_players(self):
        board = CatanBoard()
        board.make_board()
        players = [
            Player((231, 76,  60),  "Player 1"),
            Player((39,  174, 96),  "Player 2"),
            Player((219, 118, 51),  "Player 3"),
            Player((142, 68,  173), "Player 4"),
        ]
        return board, players

    def on_mouse_press(self, x, y, button, modifiers):
        board, players = self._make_board_and_players()

        if self._skip_button_hit(x, y):
            _auto_place_setup(board, players)
            self.vm.go_to("catan",
                board=board, players=players, current_player=0, die1=random.randint(ONE, SIX),
                die2=random.randint(ONE, SIX), port_manager=None)
            return

        self.vm.go_to("gamemode", board=board)
