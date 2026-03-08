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
        Core build pipeline.

        The standard Catan board has exactly 18 outer edges on its perimeter.
        With flat-top orientation (flat sides top/bottom), those 18 edges
        alternate between:
          - "face" edges  — the flat face of a border tile (9 total, these get ports)
          - "point" edges — edges at the pointy corners of the hex island (9 total)

        When sorted clockwise from 12 o'clock, the face edges always land on
        even indices (0, 2, 4, 6, 8, 10, 12, 14, 16). Picking every other edge
        starting at index 0 gives exactly the 9 real Catan port positions,
        uniformly spaced and flush against the island.
        """

        # Collect all outer edges (nodes touching fewer than 3 tiles = on the border)
        outer_edges = []
        for edge_id, edge_obj in self._board.edges.items():
            if any(len(n.tiles) < 3 for n in edge_obj.nodes):
                mx, my, x1, y1, x2, y2 = self._edge_pixel_cache[edge_id]
                dx = mx - BOARD_CENTER_X
                dy = my - BOARD_CENTER_Y
                angle_from_center = math.atan2(dy, dx)
                outer_edges.append((angle_from_center, mx, my, x1, y1, x2, y2))

        # Sort clockwise from 12 o'clock (top of screen)
        outer_edges.sort(
            key=lambda e: (-(e[0] - math.pi / 2)) % (2 * math.pi)
        )

        total = len(outer_edges)

        # Standard 19-tile flat-top board always produces 18 outer edges.
        # Face edges (the ones that get ports) sit at even indices when sorted
        # clockwise. Pick every other edge for the 9 port slots.
        if total == 18:
            port_edges = [outer_edges[i * 2] for i in range(9)]
        else:
            # Fallback for non-standard board sizes
            step = total / 9
            port_edges = [outer_edges[round(i * step) % total] for i in range(9)]

        # Build one ship + label per port
        for i, (angle_from_center, mx, my, x1, y1, x2, y2) in enumerate(port_edges):
            resource = port_pool[i]
            label    = f"2:1 {RESOURCE_ABBR[resource]}" if resource else "3:1"

            # Outward unit vector from board center through the edge midpoint
            dx     = mx - BOARD_CENTER_X
            dy     = my - BOARD_CENTER_Y
            dist   = math.hypot(dx, dy) or 1.0
            norm_x = dx / dist
            norm_y = dy / dist

            # Ship sits just outside the tile edge, flush against the island
            ship_x = mx + norm_x * (HEX_SIZE * 0.60)
            ship_y = my + norm_y * (HEX_SIZE * 0.60)

            # Label floats outward past the ship with clean separation
            SHIP_HALF = HEX_SIZE * 0.38   # approx half-height of sprite at scale=0.07
            LABEL_GAP = 10
            label_x = ship_x + norm_x * (SHIP_HALF + LABEL_GAP + 24)
            label_y = ship_y + norm_y * (SHIP_HALF + LABEL_GAP + 24)

            self._fallback_dots.append((ship_x, ship_y))

            # Label — always upright, no rotation
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

            # Ship sprite — angle=0, always upright (facing top of window)
            if self._ship_ok:
                ship          = arcade.Sprite(PORT_SHIP_SPRITE, scale=0.07)
                ship.center_x = ship_x
                ship.center_y = ship_y
                ship.angle    = 0
                self._port_sprite_list.append(ship)