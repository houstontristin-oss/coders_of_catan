"""
Contains StartView class
"""
import math
import arcade
from backend.catan_board import CatanBoard
from backend.player import Player
from .setup_view import SetupView
from .constants import SCREEN_HEIGHT, SCREEN_WIDTH, TEXT_WHITE, TEXT_GOLD, BTN_ENDTURN
from .drawing import fill_rect, outline_rect

# ---------------------------------------------------------------------------
# Layout constants for the skip button
# ---------------------------------------------------------------------------
_SKIP_BTN_W  = 220
_SKIP_BTN_H  = 46
_SKIP_BTN_X  = SCREEN_WIDTH  - _SKIP_BTN_W - 20   # left edge
_SKIP_BTN_Y  = 20                                   # bottom edge


def _auto_place_setup(board, players):
    """
    Automatically place 2 settlements + 2 roads per player, following all
    standard Catan setup rules, then award each player the resources from
    their *second* settlement (cycle-2 rule).

    The algorithm:
      1. Score every unoccupied node by the sum of pip-values of its adjacent
         non-desert tiles (higher = more productive location).
      2. Pick the best available node for each player in snake order
         (P0→P3→P3→P0), enforcing the distance rule (no settlement within
         one edge of another) exactly as the real game requires.
      3. For each settlement place the highest-scoring adjacent free edge as
         the road.

    Parameters
    ----------
    board   : CatanBoard  — fully built board
    players : list[Player]
    """
    pip_map = {2:1, 3:2, 4:3, 5:4, 6:5, 8:5, 9:4, 10:3, 11:2, 12:1}

    def node_score(node):
        return sum(pip_map.get(t.number, 0) for t in node.tiles if t.resource != "desert")

    def distance_ok(node):
        """True when no adjacent node already has a settlement (distance rule)."""
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
        candidates = [
            n for n in board.nodes.values()
            if n.player is None and distance_ok(n)
        ]
        return max(candidates, key=node_score, default=None)

    def best_adjacent_edge(node, player_idx):
        free_edges = [e for e in node.edges if e.player is None]
        return max(free_edges, key=lambda e: sum(
            node_score(n) for n in e.nodes
        ), default=None)

    # Snake order: 0,1,2,3,3,2,1,0
    snake = [0, 1, 2, 3, 3, 2, 1, 0]
    second_settlement_nodes = {}   # player_idx -> node placed in second round

    for turn_idx, player_idx in enumerate(snake):
        node = best_free_node()
        if node is None:
            break
        place_settlement(node, player_idx)
        edge = best_adjacent_edge(node, player_idx)
        if edge:
            place_road(edge, player_idx)
        # Second round = turns 4-7 (indices 4..7)
        if turn_idx >= 4:
            second_settlement_nodes[player_idx] = node

    # Award cycle-2 starting resources
    resource_abbr = {
        "brick": "BRICK", "ore": "ORE", "wheat": "WHEAT",
        "sheep": "SHEEP", "forest": "WOOD",
    }
    for player_idx, node in second_settlement_nodes.items():
        for tile in node.tiles:
            if tile.resource != "desert":
                key = resource_abbr.get(tile.resource)
                if key:
                    players[player_idx].resource_cards[key] += 1


class StartView(arcade.View):
    """
    StartView class
    """
    def __init__(self):
        super().__init__()
        self._build_text_objects()

    def _build_text_objects(self):
        # Main title / instructions
        self.txt_title = arcade.Text(
            "Welcome to Catan!",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
            font_size=30, bold=True, font_name="MedievalSharp",
            anchor_x="center", anchor_y="center",
        )
        self.txt_instructions = arcade.Text(
            "Click anywhere to begin!",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80,
            font_size=20, font_name="MedievalSharp",
            anchor_x="center", anchor_y="center",
        )

        # Skip-setup button label
        btn_cx = _SKIP_BTN_X + _SKIP_BTN_W / 2
        btn_cy = _SKIP_BTN_Y + _SKIP_BTN_H / 2
        self.txt_skip = arcade.Text(
            "Skip Setup  ▶",
            btn_cx, btn_cy,
            TEXT_GOLD, 13,
            bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _draw_skip_button(self):
        """Draw the skip-setup button in the bottom-right corner."""
        # Dark navy background
        fill_rect(_SKIP_BTN_X, _SKIP_BTN_Y, _SKIP_BTN_W, _SKIP_BTN_H, (20, 20, 50, 230))
        # Gold border
        outline_rect(_SKIP_BTN_X, _SKIP_BTN_Y, _SKIP_BTN_W, _SKIP_BTN_H, TEXT_GOLD, 2)
        self.txt_skip.draw()

    def _skip_button_hit(self, x, y) -> bool:
        return (_SKIP_BTN_X <= x <= _SKIP_BTN_X + _SKIP_BTN_W and
                _SKIP_BTN_Y <= y <= _SKIP_BTN_Y + _SKIP_BTN_H)

    def _make_board_and_players(self):
        board = CatanBoard()
        board.make_board()
        players = [
            Player((231, 76,  60), "Player 1"),
            Player((39,  174, 96), "Player 2"),
            Player((219, 118, 51), "Player 3"),
            Player((142, 68,  173), "Player 4"),
        ]
        return board, players

    # ------------------------------------------------------------------
    # Arcade overrides
    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()
        self.txt_title.draw()
        self.txt_instructions.draw()
        self._draw_skip_button()

    def on_mouse_press(self, x, y, button, modifiers):
        board, players = self._make_board_and_players()

        # --- Skip setup: auto-place and jump straight to CatanView ---
        if self._skip_button_hit(x, y):
            _auto_place_setup(board, players)
            from .catan_view import CatanView
            self.window.show_view(CatanView(board, players, 0, None))
            return

        # --- Normal flow: go to SetupView ---
        self.window.show_view(SetupView(board, players, 0, 1, None))