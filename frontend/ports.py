"""
ports.py — PortManager

Owns everything related to port rendering:
  - Randomizing which port type lands on which outer edge
  - Finding and clockwise-sorting outer edges
  - Computing ship pixel position and correct facing angle
  - Building the ship SpriteList and label Text objects
  - Exposing a single draw() method for CatanView to call
  - Exposing get_hover_nodes(x, y) so CatanView can highlight the two
    settlement nodes that can access each port on mouse-over

Usage (in CatanView.__init__, after pixel caches are built):
    from .ports import PortManager
    self.port_manager = PortManager(self.board, self._edge_pixel_cache)

In CatanView.on_draw():
    self.port_manager.draw()

In CatanView.on_mouse_motion():
    node_ids = self.port_manager.get_hover_nodes(x, y)
"""

import math
import random
import arcade

from .constants import (
    PORT_TYPES, PORT_SHIP_SPRITE, HEX_SIZE,
    BOARD_CENTER_X, BOARD_CENTER_Y,
    RESOURCE_ABBR, TEXT_GOLD
)

# How close the mouse must be to a ship centre (px) to trigger the hover
_PORT_HOVER_RADIUS = 52


class PortManager:
    """
    Manages all port state and rendering for a Catan board.

    Attributes:
        _ship_ok         : bool  — False if the ship sprite failed to load
        _port_sprite_list: arcade.SpriteList — one ship sprite per port
        _label_texts     : list[arcade.Text] — one Text object per port
        _fallback_dots   : list[tuple]       — (x, y) used when ship sprite missing
        _port_data       : list[dict]        — per-port metadata including node_ids
                           for hover detection
    """

    def __init__(self, board, edge_pixel_cache):
        self._board            = board
        self._edge_pixel_cache = edge_pixel_cache
        self._port_sprite_list = arcade.SpriteList()
        self._label_texts      = []
        self._fallback_dots    = []
        # Each entry: {'ship_x', 'ship_y', 'label_x', 'label_y',
        #              'node_ids': [node_id, node_id]}
        self._port_data        = []

        self._ship_ok = self._test_sprite()

        port_pool = list(PORT_TYPES)
        random.shuffle(port_pool)
        self._build(port_pool)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def draw(self):
        """Draw all port ships and labels. Call once per frame in on_draw()."""
        if self._ship_ok:
            self._port_sprite_list.draw()
        else:
            for (fx, fy) in self._fallback_dots:
                arcade.draw_circle_filled(fx, fy, 6, (15, 40, 90))
                arcade.draw_circle_outline(fx, fy, 6, TEXT_GOLD, 1)

        for txt in self._label_texts:
            txt.draw()

    def get_hover_nodes(self, mx, my):
        """
        Return the list of node_ids belonging to the port nearest (mx, my),
        if the mouse is within _PORT_HOVER_RADIUS pixels of that port's ship.
        Returns an empty list when no port is close enough.

        Parameters
        ----------
        mx, my : float — current mouse position in screen coordinates
        """
        for entry in self._port_data:
            dist = math.hypot(mx - entry["ship_x"], my - entry["ship_y"])
            if dist <= _PORT_HOVER_RADIUS:
                return entry["node_ids"]
        return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _test_sprite(self) -> bool:
        try:
            arcade.Sprite(PORT_SHIP_SPRITE, scale=0.07)
            return True
        except Exception:
            return False

    def _build(self, port_pool: list):
        """
        Core build pipeline — identical layout logic to the original, but now
        also stores the two node_ids that belong to each port edge so that
        CatanView can highlight them on hover.
        """
        # Collect all outer edges
        outer_edges = []
        for edge_id, edge_obj in self._board.edges.items():
            if all(len(n.tiles) < 3 for n in edge_obj.nodes):
                mx, my, x1, y1, x2, y2 = self._edge_pixel_cache[edge_id]
                dx = mx - BOARD_CENTER_X
                dy = my - BOARD_CENTER_Y
                angle_from_center = math.atan2(dy, dx)
                # Carry the edge_id so we can look up node_ids later
                outer_edges.append(
                    (angle_from_center, mx, my, x1, y1, x2, y2, edge_id)
                )

        # Sort clockwise from 12 o'clock
        outer_edges.sort(
            key=lambda e: (-(e[0] - math.pi / 2)) % (2 * math.pi)
        )

        total = len(outer_edges)
        if total == 18:
            port_edges = [outer_edges[i * 2] for i in range(9)]
        else:
            step = total / 9
            port_edges = [outer_edges[round(i * step) % total] for i in range(9)]

        for i, entry in enumerate(port_edges):
            angle_from_center, mx, my, x1, y1, x2, y2, edge_id = entry
            resource = port_pool[i]
            label    = f"2:1 {RESOURCE_ABBR[resource]}" if resource else "3:1"

            dx     = mx - BOARD_CENTER_X
            dy     = my - BOARD_CENTER_Y
            dist   = math.hypot(dx, dy) or 1.0
            norm_x = dx / dist
            norm_y = dy / dist

            ship_x = mx + norm_x * (HEX_SIZE * 0.60)
            ship_y = my + norm_y * (HEX_SIZE * 0.60)

            SHIP_HALF = HEX_SIZE * 0.38
            LABEL_GAP = 10
            label_x = ship_x + norm_x * (SHIP_HALF + LABEL_GAP + 24)
            label_y = ship_y + norm_y * (SHIP_HALF + LABEL_GAP + 24)

            self._fallback_dots.append((ship_x, ship_y))

            # Resolve the two node_ids for hover highlighting
            edge_obj  = self._board.edges[edge_id]
            node_ids  = [n.node_id for n in edge_obj.nodes]

            # Store per-port metadata
            self._port_data.append({
                "ship_x":   ship_x,
                "ship_y":   ship_y,
                "label_x":  label_x,
                "label_y":  label_y,
                "node_ids": node_ids,
                "resource": resource,
            })

            # Label text
            self._label_texts.append(
                arcade.Text(
                    label,
                    label_x, label_y,
                    (15, 40, 90, 255), 13,
                    bold=True,
                    anchor_x="center", anchor_y="center",
                    font_name="MedievalSharp"
                )
            )

            # Ship sprite
            if self._ship_ok:
                ship          = arcade.Sprite(PORT_SHIP_SPRITE, scale=0.07)
                ship.center_x = ship_x
                ship.center_y = ship_y
                ship.angle    = 0
                self._port_sprite_list.append(ship)