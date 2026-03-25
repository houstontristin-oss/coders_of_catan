"""
Contains Robber Resource Class
"""
import arcade
from .drawing import fill_rect, outline_rect
from .constants import (
    HUD_BOTTOM_HEIGHT, HUD_BG, SCREEN_WIDTH, TEXT_WHITE, BTN_ENDTURN, SCREEN_HEIGHT, BTN_TRADE,
    TEXT_GOLD
)

# ---------------------------------------------------------------------------
# Resource constants
# ---------------------------------------------------------------------------
_RESOURCES    = ["BRICK", "ORE", "WHEAT", "SHEEP", "WOOD"]
_RES_DISPLAY  = {"BRICK": "Brick", "ORE": "Ore", "WHEAT": "Wheat",
                 "SHEEP": "Sheep", "WOOD": "Wood"}
_RES_COLOR_KEY = {"BRICK": "brick", "ORE": "ore", "WHEAT": "wheat",
                  "SHEEP": "sheep", "WOOD": "forest"}

# ---------------------------------------------------------------------------
# Layout — columns
# ---------------------------------------------------------------------------
_COL_COUNT = 5
_BTN_W     = 30     # width of – / + buttons
_SPIN_W    = 40     # width of count box
_SWATCH_H  = 52     # coloured resource swatch
_BTN_H     = 34     # spinner row height
_COL_W     = _BTN_W * 2 + _SPIN_W          # 100 px per column
_COL_GAP   = 16                              # gap between columns
_PANEL_W   = _COL_COUNT * _COL_W + (_COL_COUNT - 1) * _COL_GAP   # 564 px
_PANEL_X   = (SCREEN_WIDTH - _PANEL_W) / 2  # horizontally centred

# ---------------------------------------------------------------------------
# Layout — vertical  (built bottom-up from the 70-px bottom bar)
# ---------------------------------------------------------------------------
_BAR_H       = 70   # matches PlayCardView bottom bar height

_SEND_BTN_H  = 44
_SEND_Y      = _BAR_H + 14                           # bottom of Send row

_RECV_SPIN_Y = _SEND_Y + _SEND_BTN_H + 36            # bottom of Receive spinners
_RECV_HEAD_Y = _RECV_SPIN_Y + _BTN_H + _SWATCH_H - 2 # "YOU RECEIVE" label y

_DIVIDER_Y   = _RECV_HEAD_Y + 22                      # separator line

_OFFT_SPIN_Y = _DIVIDER_Y + 30                        # bottom of Offer spinners
_OFFT_HEAD_Y = _OFFT_SPIN_Y + _BTN_H + _SWATCH_H - 2 # "YOUR OFFER" label y

class RobberResView(arcade.View):
    """
    RobberResView Class
    """
    def __init__(self, board, players, current_player, die1, die2):
        super().__init__()
        self.board= board
        self.players = players
        self.current_player = current_player
        self.die1 = die1
        self.die2 = die2
        self._resources = {r: 0 for r in _RESOURCES}

        # Text buckets — static built once, dynamic rebuilt each frame
        self._static_texts  = []
        self._dynamic_texts = []

        # Modal button rects  (set during draw, read during click)
        self._modal_accept_rect  = None
        self._modal_decline_rect = None
        self._modal_can_afford   = False

    # ------------------------------------------------------------------
    # Arcade lifecycle
    # ------------------------------------------------------------------
    def on_show_view(self):
        self._build_static_texts()

    def on_draw(self):
        self.clear()
        self._draw_bottom_bar()

        arcade.set_background_color((14, 14, 30))

        # Main dark panel (same as dev card view)
        fill_rect(0, _BAR_H, SCREEN_WIDTH, SCREEN_HEIGHT - _BAR_H, (16, 16, 36, 255))

        # Gold header bar at top
        fill_rect(0, SCREEN_HEIGHT - 58, SCREEN_WIDTH, 58, (18, 18, 48, 255))
        outline_rect(0, SCREEN_HEIGHT - 58, SCREEN_WIDTH, 1, (60, 60, 90, 200), 1)

    # ------------------------------------------------------------------
    # Static Texts - built once in show view
    # ------------------------------------------------------------------

    def _build_static_texts(self):
        self._static_texts = []
        player = self.players[self.current_player]

        # Title (matches PlayCardView title style exactly)
        self._static_texts.append(arcade.Text(
            f"A 7 Was Rolled, {player.name} Must Discard",      # text to display
            SCREEN_WIDTH / 2, SCREEN_HEIGHT - 28,   # x location, y location
            TEXT_GOLD, 20, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))

        # explanation of rolling a 7 rule
        self._static_texts.append(arcade.Text(
            f"since you have more than 7 cards, you must discard half of your cards rounding down",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT - 52,   # x location, y location
            TEXT_WHITE, 10, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))

        # Per-column static labels and +/– symbols
        for i, res in enumerate(_RESOURCES):
            col_x  = _PANEL_X + i * (_COL_W + _COL_GAP)
            col_cx = col_x + _COL_W / 2

            # Offer column — resource name inside swatch
            self._static_texts.append(arcade.Text(
                _RES_DISPLAY[res],
                col_cx, _OFFT_SPIN_Y + _BTN_H + _SWATCH_H * 0.6,
                TEXT_WHITE, 9, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))
            # Offer − and +
            self._static_texts.append(arcade.Text(
                "−", col_x + _BTN_W / 2,
                _OFFT_SPIN_Y + _BTN_H / 2,
                TEXT_WHITE, 16, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))
            self._static_texts.append(arcade.Text(
                "+", col_x + _BTN_W + _SPIN_W + _BTN_W / 2,
                _OFFT_SPIN_Y + _BTN_H / 2,
                TEXT_WHITE, 16, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))

        # Back button label (bottom-left, same as PlayCardView)
        _PAD, _BTN_W_BAR, _BTN_H_BAR = 18, 180, 44
        self._static_texts.append(arcade.Text(
            "← Back to Board",
            _PAD + _BTN_W_BAR / 2, _PAD + _BTN_H_BAR / 2,
            TEXT_WHITE, 12, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))

    # ------------------------------------------------------------------
    # Draw Helpers - called every frame
    # ------------------------------------------------------------------
    def _draw_bottom_bar(self):
        """Identical structure to PlayCardView._draw_bottom_bar."""
        fill_rect(0, 0, SCREEN_WIDTH, _BAR_H, (18, 18, 42, 245))
        outline_rect(0, _BAR_H - 3, SCREEN_WIDTH, 3, (60, 60, 90, 200), 1)

        _PAD, _BTN_W_BAR, _BTN_H_BAR = 18, 180, 44
        fill_rect(_PAD, _PAD, _BTN_W_BAR, _BTN_H_BAR, BTN_TRADE)
        outline_rect(_PAD, _PAD, _BTN_W_BAR, _BTN_H_BAR, (255, 255, 255, 60), 1)
    
    def _draw_sections(self):
        """Draw offer + receive swatches, spinners, and dynamic counter labels."""
        player = self.players[self.current_player]

        # Horizontal divider between sections
        arcade.draw_line(
            _PANEL_X, _DIVIDER_Y,
            _PANEL_X + _PANEL_W, _DIVIDER_Y,
            (60, 60, 90, 180), 1,
        )

        for i, res in enumerate(_RESOURCES):
            col_x   = _PANEL_X + i * (_COL_W + _COL_GAP)
            col_cx  = col_x + _COL_W / 2
            spin_cx = col_x + _BTN_W + _SPIN_W / 2
            have    = player.resource_cards.get(res, 0)

            # ---- OFFER section ----
            swatch_color = RESOURCE_COLORS[_RES_COLOR_KEY[res]]
            fill_rect(col_x, _OFFT_SPIN_Y + _BTN_H + 4,
                      _COL_W, _SWATCH_H, swatch_color)
            outline_rect(col_x, _OFFT_SPIN_Y + _BTN_H + 4,
                         _COL_W, _SWATCH_H, (0, 0, 0, 120), 1)

            # "Have: N" at base of swatch
            self._dynamic_texts.append(arcade.Text(
                f"Have: {have}",
                col_cx, _OFFT_SPIN_Y + _BTN_H + 10,
                TEXT_LIGHT_GRAY, 8,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))

            offered   = self._offer[res]
            minus_col = (80, 80, 80) if offered <= 0    else (180, 50, 50)
            plus_col  = (80, 80, 80) if offered >= have else (39, 174, 96)
            fill_rect(col_x,                    _OFFT_SPIN_Y, _BTN_W, _BTN_H, minus_col)
            fill_rect(col_x + _BTN_W,           _OFFT_SPIN_Y, _SPIN_W, _BTN_H, HUD_PANEL_BG)
            fill_rect(col_x + _BTN_W + _SPIN_W, _OFFT_SPIN_Y, _BTN_W, _BTN_H, plus_col)
            outline_rect(col_x, _OFFT_SPIN_Y, _COL_W, _BTN_H, (70, 70, 100, 200), 1)

            self._dynamic_texts.append(arcade.Text(
                str(offered),
                spin_cx, _OFFT_SPIN_Y + _BTN_H / 2,
                TEXT_GOLD, 12, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))

    # ------------------------------------------------------------------
    # Click handlers
    # ------------------------------------------------------------------
    def _handle_spinner_click(self, x, y):
        player = self.players[self.current_player]

        for i, res in enumerate(_RESOURCES):
            col_x = _PANEL_X + i * (_COL_W + _COL_GAP)

            # Offer row
            if _OFFT_SPIN_Y <= y <= _OFFT_SPIN_Y + _BTN_H:
                if col_x <= x <= col_x + _BTN_W:
                    if self._offer[res] > 0:
                        self._offer[res] -= 1
                elif col_x + _BTN_W + _SPIN_W <= x <= col_x + _COL_W:
                    if self._offer[res] < player.resource_cards.get(res, 0):
                        self._offer[res] += 1

            # Receive row
            if _RECV_SPIN_Y <= y <= _RECV_SPIN_Y + _BTN_H:
                if col_x <= x <= col_x + _BTN_W:
                    if self._receive[res] > 0:
                        self._receive[res] -= 1
                elif col_x + _BTN_W + _SPIN_W <= x <= col_x + _COL_W:
                    self._receive[res] += 1


    def on_mouse_press(self, x, y, button, modifiers):
        #NOTE: Would it be a good idea to make the btn_w and btn_h global variable?
        btn_w = 150
        if (SCREEN_WIDTH - btn_w - 20 <= x <= SCREEN_WIDTH - 20) and (y <= HUD_BOTTOM_HEIGHT):
            from .catan_view import CatanView
            self.window.show_view(CatanView(self.board, self.players, self.current_player, self.die1, self.die2))
