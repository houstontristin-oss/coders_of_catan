"""
Contains TradeView Class
"""
import arcade
from .drawing import fill_rect, outline_rect
from .constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TEXT_GOLD, TEXT_WHITE, BTN_TRADE, RESOURCE_COLORS, TEXT_LIGHT_GRAY,
    HUD_PANEL_BG, BTN_ENDTURN, LARGE_TEXT_SIZE
                        )

#TODO add a view board feature
#TODO add the trade receiving player's resources to the accept decline modal
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
_BTN_W     = 50     # width of – / + buttons
_SPIN_W    = 40     # width of count box
_SWATCH_H  = 52     # coloured resource swatch
_BTN_H     = 40     # spinner row height
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

class TradeViewBarter(arcade.View):
    """
    Barter (player-to-player) trade screen.
 
    States
    ------
    self._pending : None = showing offer builder
    self._pending : int  = waiting for player[_pending] to accept/decline
    """
    def __init__(self, vm, board, players, current_player, die1, die2, port_manager):
        super().__init__()
        self.vm             = vm
        self.board          = board
        self.players        = players
        self.current_player = current_player
        self.die1           = die1
        self.die2           = die2
        self.port_manager = port_manager
 
        self._offer   = {r: 0 for r in _RESOURCES}
        self._receive = {r: 0 for r in _RESOURCES}
        self._pending = None          # int index of receiving player, or None
        self._result_msg = ""

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
        arcade.set_background_color((14, 14, 30, 1))

        # Main dark panel (same as dev card view)
        fill_rect(0, _BAR_H, SCREEN_WIDTH, SCREEN_HEIGHT - _BAR_H, (16, 16, 36, 255))

        # Gold header bar at top
        fill_rect(0, SCREEN_HEIGHT - 58, SCREEN_WIDTH, 58, (18, 18, 48, 255))
        outline_rect(0, SCREEN_HEIGHT - 58, SCREEN_WIDTH, 1, (60, 60, 90, 200), 1)

        self._draw_bottom_bar()

        # Rebuild dynamic texts each frame
        self._dynamic_texts = []

        if self._pending is None: # draw buttons and resources
            self._draw_sections()
            self._draw_send_row()
        else:
            self._draw_pending_modal()

        if self._pending is None:
            for txt in self._static_texts: # holds all the +, −, resource name labels, section
                # headings, etc.
                txt.draw()
        for txt in self._dynamic_texts:
            txt.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if self._pending is not None:
            self._handle_modal_click(x, y)
            return

        # Back button (bottom-left, same position as PlayCardView)
        _PAD, _BTN_W_BAR, _BTN_H_BAR = 18, 180, 44
        if _PAD <= x <= _PAD + _BTN_W_BAR and _PAD <= y <= _PAD + _BTN_H_BAR:
            self.window.vm.go_back()
            return

        self._handle_spinner_click(x, y)
        self._handle_send_click(x, y)

    # ------------------------------------------------------------------
    # Static texts — built once in on_show_view
    # ------------------------------------------------------------------
    def _build_static_texts(self):
        self._static_texts = []
        player = self.players[self.current_player]

        # Title (matches PlayCardView title style exactly)
        self._static_texts.append(arcade.Text(
            f"{player.name}  —  Barter Trade",      # text to display
            SCREEN_WIDTH / 2, SCREEN_HEIGHT - 28,   # x location, y location
            TEXT_GOLD, 20, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))

        # Section headings
        self._static_texts.append(arcade.Text(
            "YOUR OFFER",
            _PANEL_X, _OFFT_HEAD_Y + 14,
            TEXT_GOLD, 11, bold=True,
            font_name="MedievalSharp",
        ))
        self._static_texts.append(arcade.Text(
            "YOU RECEIVE",
            _PANEL_X, _RECV_HEAD_Y + 14,
            TEXT_GOLD, 11, bold=True,
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
                TEXT_WHITE, LARGE_TEXT_SIZE, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))
            # Offer − and +
            self._static_texts.append(arcade.Text(
                "−", col_x + _BTN_W / 2,
                _OFFT_SPIN_Y + _BTN_H / 2,
                TEXT_WHITE, LARGE_TEXT_SIZE, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))
            self._static_texts.append(arcade.Text(
                "+", col_x + _BTN_W + _SPIN_W + _BTN_W / 2,
                _OFFT_SPIN_Y + _BTN_H / 2,
                TEXT_WHITE, LARGE_TEXT_SIZE, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))

            # Receive column — resource name
            self._static_texts.append(arcade.Text(
                _RES_DISPLAY[res],
                col_cx, _RECV_SPIN_Y + _BTN_H + _SWATCH_H * 0.6,
                TEXT_WHITE, LARGE_TEXT_SIZE, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))
            # Receive − and +
            self._static_texts.append(arcade.Text(
                "−", col_x + _BTN_W / 2,
                _RECV_SPIN_Y + _BTN_H / 2,
                TEXT_WHITE, LARGE_TEXT_SIZE, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))
            self._static_texts.append(arcade.Text(
                "+", col_x + _BTN_W + _SPIN_W + _BTN_W / 2,
                _RECV_SPIN_Y + _BTN_H / 2,
                TEXT_WHITE, LARGE_TEXT_SIZE, bold=True,
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
    # Draw helpers — called every frame
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

            # ---- RECEIVE section ----
            # Subtle dark swatch so columns are visually consistent
            fill_rect(col_x, _RECV_SPIN_Y + _BTN_H + 4,
                      _COL_W, _SWATCH_H, (30, 30, 55, 220))
            outline_rect(col_x, _RECV_SPIN_Y + _BTN_H + 4,
                         _COL_W, _SWATCH_H, (70, 70, 100, 160), 1)

            received  = self._receive[res]
            minus_col = (80, 80, 80) if received <= 0 else (180, 50, 50)
            fill_rect(col_x,                    _RECV_SPIN_Y, _BTN_W, _BTN_H, minus_col)
            fill_rect(col_x + _BTN_W,           _RECV_SPIN_Y, _SPIN_W, _BTN_H, HUD_PANEL_BG)
            fill_rect(col_x + _BTN_W + _SPIN_W, _RECV_SPIN_Y, _BTN_W, _BTN_H, (39, 174, 96))
            outline_rect(col_x, _RECV_SPIN_Y, _COL_W, _BTN_H, (70, 70, 100, 200), 1)

            self._dynamic_texts.append(arcade.Text(
                str(received),
                spin_cx, _RECV_SPIN_Y + _BTN_H / 2,
                TEXT_GOLD, 12, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))

        # Result message (e.g. "Player 2 declined.")
        if self._result_msg:
            self._dynamic_texts.append(arcade.Text(
                self._result_msg,
                SCREEN_WIDTH / 2, _SEND_Y + _SEND_BTN_H + 12,
                (255, 140, 100, 255), 11, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))

    def _draw_send_row(self):
        """One coloured 'Send to Player N' button per other player."""
        others      = [i for i in range(len(self.players)) if i != self.current_player]
        n           = len(others)
        if n == 0:
            return

        tradeable   = (any(v > 0 for v in self._offer.values()) and
                       any(v > 0 for v in self._receive.values()))
        btn_w       = 160
        gap         = 20
        total_w     = n * btn_w + (n - 1) * gap
        start_x     = (SCREEN_WIDTH - total_w) / 2

        for j, pidx in enumerate(others):
            bx = start_x + j * (btn_w + gap)
            p  = self.players[pidx]
            btn_color = (*p.color[:3], 220) if tradeable else (45, 45, 55, 220)
            border    = TEXT_GOLD           if tradeable else (70, 70, 90, 200)

            fill_rect(bx, _SEND_Y, btn_w, _SEND_BTN_H, btn_color)
            outline_rect(bx, _SEND_Y, btn_w, _SEND_BTN_H, border, 2)

            self._dynamic_texts.append(arcade.Text(
                f"Send to {p.name}",
                bx + btn_w / 2, _SEND_Y + _SEND_BTN_H / 2,
                TEXT_WHITE if tradeable else TEXT_LIGHT_GRAY, 11, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))

    def _draw_pending_modal(self):
        """
        Semi-transparent overlay + modal box asking the receiving player
        to accept or decline.  Matches the sub-popup style in PlayCardView.
        """
        # Dim backdrop (same as PlayCardView sub-popup)
        fill_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 130))

        modal_w = 500
        modal_h = 270
        mx = (SCREEN_WIDTH  - modal_w) / 2
        my = (SCREEN_HEIGHT - modal_h) / 2

        fill_rect(mx, my, modal_w, modal_h, (20, 20, 55, 250))
        outline_rect(mx, my, modal_w, modal_h, TEXT_GOLD, 2)

        receiver = self.players[self._pending]
        sender   = self.players[self.current_player]

        offer_parts   = [f"{v}× {_RES_DISPLAY[r]}"
                         for r, v in self._offer.items()   if v > 0]
        receive_parts = [f"{v}× {_RES_DISPLAY[r]}"
                         for r, v in self._receive.items() if v > 0]
        offer_str   = ", ".join(offer_parts)   or "nothing"
        receive_str = ", ".join(receive_parts) or "nothing"

        can_afford = receiver.can_afford_trade(self._receive)
        self._modal_can_afford = can_afford

        # Modal title
        self._dynamic_texts.append(arcade.Text(
            f"{receiver.name} — Trade Offer!",
            SCREEN_WIDTH / 2, my + modal_h - 30,
            TEXT_GOLD, 15, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))
        # Trade summary lines
        self._dynamic_texts.append(arcade.Text(
            f"{sender.name} gives:   {offer_str}",
            SCREEN_WIDTH / 2, my + modal_h - 72,
            TEXT_WHITE, 11,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))
        self._dynamic_texts.append(arcade.Text(
            f"{sender.name} wants:   {receive_str}",
            SCREEN_WIDTH / 2, my + modal_h - 100,
            TEXT_WHITE, 11,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))

        # Affordability warning
        if not can_afford:
            self._dynamic_texts.append(arcade.Text(
                "(You don't have enough resources to accept)",
                SCREEN_WIDTH / 2, my + modal_h - 130,
                (255, 120, 80), 9,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))

        # Accept button
        _PAD_BTN = 40
        _MBTN_W  = 180
        _MBTN_H  = 50
        accept_x = mx + _PAD_BTN
        accept_y = my + 28
        fill_rect(accept_x, accept_y, _MBTN_W, _MBTN_H,
                  (39, 174, 96) if can_afford else (45, 45, 55))
        outline_rect(accept_x, accept_y, _MBTN_W, _MBTN_H, (255, 255, 255, 60), 1)
        self._dynamic_texts.append(arcade.Text(
            "Accept" if can_afford else "Can't Afford",
            accept_x + _MBTN_W / 2, accept_y + _MBTN_H / 2,
            TEXT_WHITE, 13, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))

        # Decline button
        decline_x = mx + modal_w - _PAD_BTN - _MBTN_W
        decline_y = my + 28
        fill_rect(decline_x, decline_y, _MBTN_W, _MBTN_H, BTN_ENDTURN)
        outline_rect(decline_x, decline_y, _MBTN_W, _MBTN_H, (255, 255, 255, 60), 1)
        self._dynamic_texts.append(arcade.Text(
            "Decline",
            decline_x + _MBTN_W / 2, decline_y + _MBTN_H / 2,
            TEXT_WHITE, 13, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))

        # Store rects for click handler
        self._modal_accept_rect  = (accept_x,  accept_y,  _MBTN_W, _MBTN_H)
        self._modal_decline_rect = (decline_x, decline_y, _MBTN_W, _MBTN_H)

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

    def _handle_send_click(self, x, y):
        tradeable = (any(v > 0 for v in self._offer.values()) and
                     any(v > 0 for v in self._receive.values()))
        if not tradeable:
            return

        others  = [i for i in range(len(self.players)) if i != self.current_player]
        n       = len(others)
        btn_w   = 160
        gap     = 20
        total_w = n * btn_w + (n - 1) * gap
        start_x = (SCREEN_WIDTH - total_w) / 2

        for j, pidx in enumerate(others):
            bx = start_x + j * (btn_w + gap)
            if bx <= x <= bx + btn_w and _SEND_Y <= y <= _SEND_Y + _SEND_BTN_H:
                self._result_msg = ""
                self._pending    = pidx
                return

    def _handle_modal_click(self, x, y):
        if self._modal_accept_rect is None or self._modal_decline_rect is None:
            return

        ax, ay, aw, ah = self._modal_accept_rect
        dx, dy, dw, dh = self._modal_decline_rect

        if ax <= x <= ax + aw and ay <= y <= ay + ah: # accept button location
            if self._modal_can_afford:
                self._execute_trade()
            return

        if dx <= x <= dx + dw and dy <= y <= dy + dh: # decline button location
            self._result_msg = f"{self.players[self._pending].name} declined the trade."
            self._pending    = None

    # ------------------------------------------------------------------
    # Trade mofo
    # ------------------------------------------------------------------

    def _execute_trade(self):
        # handles the backend exchange of resources between players
        # redundently checks for valid resoure counts but it is checked in current structure of game
        sender   = self.players[self.current_player]
        receiver = self.players[self._pending]
        try:
            sender.exchange_resources(self._offer, self._receive)
            receiver.exchange_resources(self._receive, self._offer)
            print(f"Trade completed: {sender.name} with {receiver.name}")
        except ValueError as e:
            print(f"Trade failed: {e}")
            self._result_msg = "Trade failed — insufficient resources."
            self._pending    = None
            return
        
        self.window.vm.go_to("catan",
            board=self.board, players=self.players, current_player=self.current_player, 
            die1=self.die1, die2=self.die2, port_manager=self.port_manager
        )