import math
import random
import arcade

from backend.port import Port

from .constants import (
    PORT_TYPES,
    PORT_SHIP_SPRITE,
    HEX_SIZE,
    BOARD_CENTER_X,
    BOARD_CENTER_Y,
    RESOURCE_ABBR,
    TEXT_GOLD,
)
from .board_utils import get_edge_outward_normal, normalize_vector
from .drawing import draw_port_dock



# Hover still keys off ship center only
_PORT_HOVER_RADIUS = 52

# Visual tuning
_PORT_SHIP_SCALE = 0.07
_PORT_DOCK_START_OFFSET = HEX_SIZE * 0.10   # where dock leaves the island nodes
_PORT_DOCK_END_OFFSET   = HEX_SIZE * 0.48   # where dock reaches toward the ship
_PORT_SHIP_OFFSET       = HEX_SIZE * 1.18   # push ship farther into the water
_PORT_LABEL_OUTWARD     = HEX_SIZE * 0.72
_PORT_LABEL_SIDE        = HEX_SIZE * 0.12


class PortManager:
    """
    Handles port layout, port rendering, and hover lookup.
    """
    def __init__(self, board, edge_pixel_cache):
        self._board = board
        self._edge_pixel_cache = edge_pixel_cache
        self._port_sprite_list = arcade.SpriteList()
        self._label_texts = []
        self._fallback_dots = []
        self.port_data = []

        self._ship_ok = self._test_sprite()

        port_pool = list(PORT_TYPES)
        random.shuffle(port_pool)
        self._build(port_pool)

    # ------------------------------------------------------------------
    # Public API
    def draw(self):
        for entry in self.port_data:
            draw_port_dock(
                entry["x1"], entry["y1"],
                entry["x2"], entry["y2"],
                entry["dock_start_x1"], entry["dock_start_y1"],
                entry["dock_end_x1"],   entry["dock_end_y1"],
                entry["dock_start_x2"], entry["dock_start_y2"],
                entry["dock_end_x2"],   entry["dock_end_y2"],
            )

        if self._ship_ok:
            self._port_sprite_list.draw()
        else:
            for fx, fy in self._fallback_dots:
                arcade.draw_circle_filled(fx, fy, 6, (15, 40, 90))
                arcade.draw_circle_outline(fx, fy, 6, TEXT_GOLD, 1)

        for txt in self._label_texts:
            txt.draw()

    def get_hover_nodes(self, mx, my):
        for entry in self.port_data:
            if math.hypot(mx - entry["ship_x"], my - entry["ship_y"]) <= _PORT_HOVER_RADIUS:
                return entry["port"].get_port_nodes()
        return []

    # ------------------------------------------------------------------
    # Internal helpers
    def _test_sprite(self):
        try:
            arcade.Sprite(PORT_SHIP_SPRITE, scale=_PORT_SHIP_SCALE)
            return True
        except Exception:
            return False

    def _build(self, port_pool):
        outer_edges = []
        for edge_id, edge_obj in self._board.edges.items():
            # coastal edge = both endpoint nodes belong to fewer than 3 tiles
            if all(len(n.tiles) < 3 for n in edge_obj.nodes):
                mx, my, x1, y1, x2, y2 = self._edge_pixel_cache[edge_id]
                angle_from_center = math.atan2(my - BOARD_CENTER_Y, mx - BOARD_CENTER_X)
                outer_edges.append((angle_from_center, mx, my, x1, y1, x2, y2, edge_id))

        # clockwise from top
        outer_edges.sort(key=lambda e: (-(e[0] - math.pi / 2)) % (2 * math.pi))

        total = len(outer_edges)
        if total == 18:
            port_edges = [outer_edges[i * 2] for i in range(9)]
        else:
            step = total / 9
            port_edges = [outer_edges[round(i * step) % total] for i in range(9)]

        for i, entry in enumerate(port_edges):
            _, mx, my, x1, y1, x2, y2, edge_id = entry
            resource = port_pool[i]
            label = f"2:1 {RESOURCE_ABBR[resource]}" if resource else "3:1"

            norm_x, norm_y = get_edge_outward_normal(x1, y1, x2, y2)
            tan_x, tan_y = normalize_vector(-(y2 - y1), (x2 - x1))

            # make tangent stable so labels don't randomly flip
            if tan_x * (mx - BOARD_CENTER_X) + tan_y * (my - BOARD_CENTER_Y) < 0:
                tan_x *= -1
                tan_y *= -1

            # ship sits a fixed distance out to sea
            ship_x = mx + norm_x * _PORT_SHIP_OFFSET
            ship_y = my + norm_y * _PORT_SHIP_OFFSET

            # Each node gets its own dock that extends outward toward the ship.
            # The pier starts just off the coastal node and ends just short of
            # the ship sprite so the rails don't pierce through the hull.
            dock_start_x1 = x1 + norm_x * _PORT_DOCK_START_OFFSET
            dock_start_y1 = y1 + norm_y * _PORT_DOCK_START_OFFSET
            dock_end_x1   = x1 + norm_x * _PORT_DOCK_END_OFFSET
            dock_end_y1   = y1 + norm_y * _PORT_DOCK_END_OFFSET

            dock_start_x2 = x2 + norm_x * _PORT_DOCK_START_OFFSET
            dock_start_y2 = y2 + norm_y * _PORT_DOCK_START_OFFSET
            dock_end_x2   = x2 + norm_x * _PORT_DOCK_END_OFFSET
            dock_end_y2   = y2 + norm_y * _PORT_DOCK_END_OFFSET

            label_x = ship_x + norm_x * _PORT_LABEL_OUTWARD + tan_x * _PORT_LABEL_SIDE
            label_y = ship_y + norm_y * _PORT_LABEL_OUTWARD + tan_y * _PORT_LABEL_SIDE

            self._fallback_dots.append((ship_x, ship_y))

            edge_obj = self._board.edges[edge_id]
            node_ids = [n.node_id for n in edge_obj.nodes]

            self.port_data.append({
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "dock_start_x1": dock_start_x1,
                "dock_start_y1": dock_start_y1,
                "dock_end_x1":   dock_end_x1,
                "dock_end_y1":   dock_end_y1,
                "dock_start_x2": dock_start_x2,
                "dock_start_y2": dock_start_y2,
                "dock_end_x2":   dock_end_x2,
                "dock_end_y2":   dock_end_y2,
                "ship_x": ship_x,
                "ship_y": ship_y,
                "label_x": label_x,
                "label_y": label_y,
                "port": Port(node_ids, resource),
            })

            self._label_texts.append(
                arcade.Text(
                    label,
                    label_x,
                    label_y,
                    (245, 213, 57, 255),
                    14,
                    bold=True,
                    anchor_x="center",
                    anchor_y="center",
                    font_name="MedievalSharp",
                )
            )

            if self._ship_ok:
                ship = arcade.Sprite(PORT_SHIP_SPRITE, scale=_PORT_SHIP_SCALE)
                ship.center_x = ship_x
                ship.center_y = ship_y

                # All ships face straight up regardless of position on the board
                ship.angle = 0
                self._port_sprite_list.append(ship)
