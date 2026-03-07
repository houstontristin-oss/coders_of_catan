"""
ports.py — PortManager

Owns everything related to port rendering:
  - Randomizing which port type lands on which outer edge
  - Finding and clockwise-sorting outer edges
  - Computing ship pixel position and correct facing angle
  - Building the ship SpriteList and label Text objects
  - Exposing a single draw() method for CatanView to call

Usage (in CatanView.__init__, after pixel caches are built):
    from .ports import PortManager
    self.port_manager = PortManager(self.board, self._edge_pixel_cache)

In CatanView.on_draw():
    self.port_manager.draw()
"""

import math
import random
import arcade

from .constants import (
    PORT_TYPES, PORT_SHIP_SPRITE, HEX_SIZE,
    BOARD_CENTER_X, BOARD_CENTER_Y,
    RESOURCE_ABBR, TEXT_GOLD
)


class PortManager:
    """
    Manages all port state and rendering for a Catan board.

    Attributes:
        _ship_ok         : bool  — False if the ship sprite failed to load
        _port_sprite_list: arcade.SpriteList — one ship sprite per port
        _label_texts     : list[arcade.Text] — one Text object per port
        _fallback_dots   : list[tuple]       — (x, y) used when ship sprite missing
    """

    def __init__(self, board, edge_pixel_cache):
        """
        Parameters
        ----------
        board            : CatanBoard  — fully built board (nodes/edges populated)
        edge_pixel_cache : dict        — {edge_id: (mx, my, x1, y1, x2, y2)}
                           built by CatanView._build_edge_pixel_cache()
        """
        self._board            = board
        self._edge_pixel_cache = edge_pixel_cache
        self._port_sprite_list = arcade.SpriteList()
        self._label_texts      = []
        self._fallback_dots    = []   # (x, y) per port, used if sprite missing

        # Test whether the ship sprite asset exists
        self._ship_ok = self._test_sprite()

        # Shuffle port types so each game gets a different layout
        port_pool = list(PORT_TYPES)   # copy so we don't mutate the constant
        random.shuffle(port_pool)

        # Build everything
        self._build(port_pool)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def draw(self):
        """Draw all port ships and labels. Call once per frame in on_draw()."""
        if self._ship_ok:
            self._port_sprite_list.draw()
        else:
            # Fallback: small anchor-dot so ports are still visible
            for (fx, fy) in self._fallback_dots:
                arcade.draw_circle_filled(fx, fy, 6, (15, 40, 90))
                arcade.draw_circle_outline(fx, fy, 6, TEXT_GOLD, 1)

        for txt in self._label_texts:
            txt.draw()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _test_sprite(self) -> bool:
        """Return True if the ship sprite file loads without error."""
        try:
            arcade.Sprite(PORT_SHIP_SPRITE, scale=0.07)
            return True
        except Exception:
            return False

    def _build(self, port_pool: list):
        """
        Core build pipeline:
          1. Collect all outer edges
          2. Sort them clockwise from the top of the board
          3. Pick 9 evenly-spaced ones
          4. Assign shuffled port types
          5. Compute ship position and correct facing angle
          6. Create sprite + Text objects
        """

        # Step 1: collect outer edges
        # An outer edge is one where at least one endpoint node touches
        # fewer than 3 tiles (i.e. it sits on the board boundary).
        outer_edges = []
        for edge_id, edge_obj in self._board.edges.items():
            if any(len(n.tiles) < 3 for n in edge_obj.nodes):
                mx, my, x1, y1, x2, y2 = self._edge_pixel_cache[edge_id]
                dx = mx - BOARD_CENTER_X
                dy = my - BOARD_CENTER_Y
                angle_from_center = math.atan2(dy, dx)
                outer_edges.append((angle_from_center, mx, my, x1, y1, x2, y2))

        # Step 2: sort clockwise starting from the top
        # math.atan2 increases counter-clockwise; negate + offset so
        # 12-o-clock (angle = pi/2) sorts first and we go clockwise.
        outer_edges.sort(
            key=lambda e: (-(e[0] - math.pi / 2)) % (2 * math.pi)
        )

        # Step 3: pick 9 evenly-spaced edges
        total      = len(outer_edges)
        step       = total / 9
        port_edges = [outer_edges[round(i * step) % total] for i in range(9)]

        # Steps 4-6: assign ports and build render objects
        for i, (angle_from_center, mx, my, x1, y1, x2, y2) in enumerate(port_edges):
            resource = port_pool[i]
            label    = f"2:1 {RESOURCE_ABBR[resource]}" if resource else "3:1"

            # Outward unit vector from board center through edge midpoint
            dx     = mx - BOARD_CENTER_X
            dy     = my - BOARD_CENTER_Y
            dist   = math.hypot(dx, dy) or 1.0
            norm_x = dx / dist
            norm_y = dy / dist

            # Ship sits just outside the tile edge in the water
            ship_x = mx + norm_x * (HEX_SIZE * 0.65)
            ship_y = my + norm_y * (HEX_SIZE * 0.65)

            # Label floats a bit further out still
            label_x = mx + norm_x * (HEX_SIZE * 1.15)
            label_y = my + norm_y * (HEX_SIZE * 1.15)

            # Correct sprite rotation:
            # We want the ship bow to point INWARD toward the board.
            # Compute the edge's own direction, then pick whichever
            # perpendicular to it faces inward (toward the center).
            edge_dx    = x2 - x1
            edge_dy    = y2 - y1
            edge_angle = math.atan2(edge_dy, edge_dx)

            # Two candidate perpendicular angles (90 degrees each way from edge)
            perp1 = edge_angle + math.pi / 2
            perp2 = edge_angle - math.pi / 2

            # Inward direction is opposite the outward normal
            inward_angle = math.atan2(-norm_y, -norm_x)

            def _angle_diff(a, b):
                d = (a - b) % (2 * math.pi)
                return d if d <= math.pi else d - 2 * math.pi

            if abs(_angle_diff(perp1, inward_angle)) <= abs(_angle_diff(perp2, inward_angle)):
                facing_angle = perp1
            else:
                facing_angle = perp2

            # Arcade angles: 0 = right, counter-clockwise positive.
            # Subtract 90 because our ship sprite's forward direction is up.
            sprite_angle = math.degrees(facing_angle) - 90

            # Store fallback dot position
            self._fallback_dots.append((ship_x, ship_y))

            # Build label Text object
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

            # Build ship sprite
            if self._ship_ok:
                ship           = arcade.Sprite(PORT_SHIP_SPRITE, scale=0.07)
                ship.center_x  = ship_x
                ship.center_y  = ship_y
                ship.angle     = sprite_angle
                self._port_sprite_list.append(ship)