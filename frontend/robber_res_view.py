"""
Contains Robber Resource Class
"""
import random
import arcade

from .drawing import fill_rect, outline_rect
from .constants import (
    SCREEN_WIDTH, TEXT_WHITE, BTN_ENDTURN, SCREEN_HEIGHT, TEXT_GOLD,
    RESOURCE_COLORS, TEXT_LIGHT_GRAY, HUD_PANEL_BG, TOP_BAR_HEIGHT,
    LARGE_TEXT_SIZE, GET_ROBBED
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
_BTN_W     = 60     # width of – / + buttons
_SPIN_W    = 40     # width of count box
_SWATCH_H  = 80     # coloured resource swatch
_BTN_H     = 52     # spinner row height
_COL_W     = _BTN_W * 2 + _SPIN_W          # 100 px per column
_COL_GAP   = 16                              # gap between columns
_PANEL_W   = _COL_COUNT * _COL_W + (_COL_COUNT - 1) * _COL_GAP   # 564 px
_PANEL_X   = (SCREEN_WIDTH - _PANEL_W) / 2  # horizontally centred

# ---------------------------------------------------------------------------
# Layout — vertical  (built bottom-up from the 70-px bottom bar)
# ---------------------------------------------------------------------------
BG_COLOR = (14, 14, 30, 1)
_BAR_H       = 70   # matches PlayCardView bottom bar height

_DISCARD_BTN_H  = 44
_DISCARD_Y      = _BAR_H + 14                           # bottom of discard buttom

_DIVIDER_Y   = _DISCARD_Y + _DISCARD_BTN_H + 22    # seperator line

_OFFT_SPIN_Y = _DIVIDER_Y + 30                        # bottom of Discard spinners
_OFFT_HEAD_Y = _OFFT_SPIN_Y + _BTN_H + _SWATCH_H - 2 # "DISCARD" label y

_CARD_COUNT_TEXT = _OFFT_HEAD_Y + 30
_SMALL_TEXT_SIZE = 10
_MED_TEXT_SIZE = 16


class RobberResView(arcade.View):
    """
    RobberResView Class
    """
    def __init__(self, vm, board, players, current_player, die1, die2, port_manager):
        super().__init__()
        self.vm = vm
        self.board= board
        self.players = players
        self.current_player = current_player # will stay as the player whose turn it is
        self.die1 = die1
        self.die2 = die2
        self.port_manager = port_manager
        self._pending = None          # int index of discarding player, or None

        # Build ordered queue: roller first, then wrap around, skip anyone under 8 cards
        turn_order = [current_player] + [(current_player + j) % len(players)
                                         for j in range(1, len(players))]
        self._discard_queue = [i for i in turn_order if players[i].get_total_resources() >= 8 and
                               not players[i].computer]

        self._queue_index = 0   # which position in the queue we're currently on
        self._active_discarder = self._discard_queue[0] if self._discard_queue else None
        self._resources = {r: 0 for r in _RESOURCES}

        # Text buckets — static built once, dynamic rebuilt each frame
        self._static_texts  = []
        self._dynamic_texts = []

        # Modal button rects  (set during draw, read during click)
        self._modal_accept_rect  = None
        self._modal_decline_rect = None
        self._modal_can_afford   = False

    # -----------------------------------------------------------------------
    # Computer Players Discarding half their hand when a 7 is rolled
    # -----------------------------------------------------------------------
    def _comp_robber_discard(self):
        for i in range(len(self.players)):
            # print(f"{self.players[i].name}: {self.players[i].computer} :
            # {self.players[i].get_total_resources()}: {self.players[i].development_cards}")
            if self.players[i].computer and self.players[i].get_total_resources() > GET_ROBBED:
                # discard half of the comp players resources
                giving_resources = {}
                amt_to_discard = self.players[i].get_total_resources() // 2
                for resource, amount in self.players[i].resource_cards.items():
                    giving_resources[resource] = 0
                    if amt_to_discard > 0:
                        get_rid_of = random.randint(0, amount if amount < amt_to_discard
                        else amt_to_discard)
                        amt_to_discard -= get_rid_of
                        giving_resources[resource] += get_rid_of
                while amt_to_discard > 0:
                    for resource, amount in self.players[i].resource_cards.items():
                        if amt_to_discard > 0:
                            get_rid_of = random.randint(0, amount - giving_resources[resource]
                            if (amount - giving_resources[resource] < amt_to_discard)
                            else amt_to_discard)
                            amt_to_discard -= get_rid_of
                            giving_resources[resource] += get_rid_of

                self.players[i].exchange_resources(giving_resources, {})
                print(f"ROBBER! {self.players[i].name} discarded {giving_resources}")

    # ------------------------------------------------------------------
    # Arcade lifecycle
    # ------------------------------------------------------------------
    def on_show_view(self):
        self._comp_robber_discard()
        if self._discard_queue == []:
            # checks to make sure than there are players who need to discard
            self.vm.go_to("robber_place",
                board=self.board, players=self.players, current_player=self.current_player,
                die1=self.die1, die2=self.die2, port_manager=self.port_manager
            )
            return

        self._build_static_texts()

    def on_draw(self):
        self.clear()
        self._draw_bottom_bar()

        arcade.set_background_color(BG_COLOR)

        # Main dark panel (same as dev card view)
        fill_rect(0, _BAR_H, SCREEN_WIDTH, SCREEN_HEIGHT - _BAR_H, (16, 16, 36, 255))

        # Gold header bar at top
        fill_rect(0, SCREEN_HEIGHT-TOP_BAR_HEIGHT, SCREEN_WIDTH, TOP_BAR_HEIGHT, (18, 18, 48, 255))
        outline_rect(0, SCREEN_HEIGHT-TOP_BAR_HEIGHT, SCREEN_WIDTH, 1, (60, 60, 90, 200), 1)

        # Rebuild dynamic texts each frame
        self._dynamic_texts = []

        if self._pending is None: # draw buttons and resources
            self._draw_sections()
            self._draw_discard_button()
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

        self._handle_spinner_click(x, y)
        self._handle_discard_click(x, y)

    # ------------------------------------------------------------------
    # Static Texts - built once in show view
    # ------------------------------------------------------------------

    def _build_static_texts(self):
        self._static_texts = []
        player = self.players[self._active_discarder]

        # Title (matches PlayCardView title style exactly)
        self._static_texts.append(arcade.Text(
            f"A 7 Was Rolled, {player.name} Must Discard",      # text to display
            SCREEN_WIDTH / 2, SCREEN_HEIGHT - 28,   # x location, y location
            TEXT_GOLD, LARGE_TEXT_SIZE, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))

        total = player.get_total_resources()
        must_discard = total // 2
        self._static_texts.append(arcade.Text(
            f"You have {total} cards — you must discard {must_discard}",
            SCREEN_WIDTH / 2, _CARD_COUNT_TEXT,   # x location, y location
            TEXT_WHITE, LARGE_TEXT_SIZE, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))

        # explanation of rolling a 7 rule
        self._static_texts.append(arcade.Text(
            "since you have more than 7 cards, you must discard half of your cards rounding down",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT - 52,   # x location, y location
            TEXT_WHITE, _SMALL_TEXT_SIZE, bold=True,
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

    # ------------------------------------------------------------------
    # Draw Helpers - called every frame
    # ------------------------------------------------------------------
    def _draw_bottom_bar(self):
        """Identical structure to PlayCardView._draw_bottom_bar."""
        fill_rect(0, 0, SCREEN_WIDTH, _BAR_H, (18, 18, 42, 245))
        outline_rect(0, _BAR_H - 3, SCREEN_WIDTH, 3, (60, 60, 90, 200), 1)

    def _draw_sections(self):
        """Draw offer + receive swatches, spinners, and dynamic counter labels."""
        player = self.players[self._active_discarder]

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

            # ---- DISCARD section ----
            swatch_color = RESOURCE_COLORS[_RES_COLOR_KEY[res]]
            fill_rect(col_x, _OFFT_SPIN_Y + _BTN_H + 4,
                      _COL_W, _SWATCH_H, swatch_color)
            outline_rect(col_x, _OFFT_SPIN_Y + _BTN_H + 4,
                         _COL_W, _SWATCH_H, (0, 0, 0, 120), 1)

            # "Have: N" at base of swatch
            self._dynamic_texts.append(arcade.Text(
                f"Have: {have}",
                col_cx, _OFFT_SPIN_Y + _BTN_H + 16,
                TEXT_LIGHT_GRAY, _MED_TEXT_SIZE,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))

            offered   = self._resources[res]
            minus_col = (80, 80, 80) if offered <= 0    else (180, 50, 50)
            plus_col  = (80, 80, 80) if offered >= have else (39, 174, 96)
            fill_rect(col_x,                    _OFFT_SPIN_Y, _BTN_W, _BTN_H, minus_col)
            fill_rect(col_x + _BTN_W,           _OFFT_SPIN_Y, _SPIN_W, _BTN_H, HUD_PANEL_BG)
            fill_rect(col_x + _BTN_W + _SPIN_W, _OFFT_SPIN_Y, _BTN_W, _BTN_H, plus_col)
            outline_rect(col_x, _OFFT_SPIN_Y, _COL_W, _BTN_H, (70, 70, 100, 200), 1)

            self._dynamic_texts.append(arcade.Text(
                str(offered),
                spin_cx, _OFFT_SPIN_Y + _BTN_H / 2,
                TEXT_GOLD, LARGE_TEXT_SIZE, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))

    def _draw_discard_button(self):
        btn_w       = 160
        start_x     = (SCREEN_WIDTH - btn_w) / 2

        player = self.players[self._active_discarder]
        total_cards = player.get_total_resources()
        required_discard = total_cards // 2
        current_selection = sum(self._resources.values())

        fill_color = (200, 50,  50) if required_discard == current_selection else (80, 80, 80)
        fill_rect(start_x, _DISCARD_Y, btn_w, _DISCARD_BTN_H, fill_color)
        outline_rect(start_x, _DISCARD_Y, btn_w, _DISCARD_BTN_H, (255, 255, 255, 60), 2)

        self._dynamic_texts.append(arcade.Text(
                "Discard",
                start_x + btn_w / 2, _DISCARD_Y + _DISCARD_BTN_H / 2,
                TEXT_WHITE, 12, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))

    def _draw_pending_modal(self):
        """
        Semi-transparent overlay + modal box asking the player
        to confirm or cancel.  Matches the sub-popup style in tradeviewbarter.
        """
        # Dim backdrop (same as tradeviewbarter sub-popup)
        fill_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 130))

        modal_w = 500
        modal_h = 270
        mx = (SCREEN_WIDTH  - modal_w) / 2
        my = (SCREEN_HEIGHT - modal_h) / 2

        fill_rect(mx, my, modal_w, modal_h, (20, 20, 55, 250))
        outline_rect(mx, my, modal_w, modal_h, TEXT_GOLD, 2)

        player = self.players[self._pending]

        resource_parts   = [f"{v}× {_RES_DISPLAY[r]}"
                         for r, v in self._resources.items()   if v > 0]
        resource_str   = ", ".join(resource_parts)   or "nothing"

        can_afford = player.can_afford_trade(self._resources)
        self._modal_can_afford = can_afford

        # Modal title
        self._dynamic_texts.append(arcade.Text(
            f"{player.name} Gets rid of",
            SCREEN_WIDTH / 2, my + modal_h - 30,
            TEXT_GOLD, LARGE_TEXT_SIZE, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))
        # Trade summary lines
        self._dynamic_texts.append(arcade.Text(
            f"{player.name} loses:   {resource_str}",
            SCREEN_WIDTH / 2, my + modal_h - 72,
            TEXT_WHITE, _MED_TEXT_SIZE,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))

        # Affordability warning
        if not can_afford:
            self._dynamic_texts.append(arcade.Text(
                "(You don't have enough resources to discard)",
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
            "Confirm?" if can_afford else "Can't Afford",
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
            "Cancel",
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
        player = self.players[self._active_discarder]

        for i, res in enumerate(_RESOURCES):
            col_x = _PANEL_X + i * (_COL_W + _COL_GAP)

            # Offer row
            if _OFFT_SPIN_Y <= y <= _OFFT_SPIN_Y + _BTN_H:
                if col_x <= x <= col_x + _BTN_W:
                    if self._resources[res] > 0:
                        self._resources[res] -= 1
                elif col_x + _BTN_W + _SPIN_W <= x <= col_x + _COL_W:
                    if self._resources[res] < player.resource_cards.get(res, 0):
                        self._resources[res] += 1

    def _handle_discard_click(self, x, y):
        # Define the button bounds (must match _draw_discard_button)
        btn_w = 160
        start_x = (SCREEN_WIDTH - btn_w) / 2

        # Check if click is inside the Discard button
        if start_x <= x <= start_x + btn_w and _DISCARD_Y <= y <= _DISCARD_Y + _DISCARD_BTN_H:
            player = self.players[self._active_discarder]

            # Calculate how many they MUST discard (half hand, rounded down)
            total_cards = sum(player.resource_cards.values())
            required_discard = total_cards // 2
            current_selection = sum(self._resources.values())

            # 3. Validation: Only proceed if they selected the right amount
            if current_selection == required_discard:
                # Set pending to current player to trigger the confirmation modal
                self._pending = self._active_discarder
            else:
                # Optional: You could add a message here saying "You must select X cards"
                print(f"Invalid discard amount: {current_selection}/{required_discard}")

    def _handle_modal_click(self, x, y):
        if self._modal_accept_rect is None:
            return

        ax, ay, aw, ah = self._modal_accept_rect
        dx, dy, dw, dh = self._modal_decline_rect

        if ax <= x <= ax + aw and ay <= y <= ay + ah: # accept button location
            if self._modal_can_afford:
                self._execute_trade()
            return

        if dx <= x <= dx + dw and dy <= y <= dy + dh: # decline button location
            self._result_msg = f"{self.players[self._pending].name} Canceled."
            self._pending    = None
    # ------------------------------------------------------------------
    # Logic Handlers
    # ------------------------------------------------------------------
    def _advance_queue(self):
        """Move to the next player who needs to discard, or exit if done."""
        self._queue_index += 1
        self._resources = {r: 0 for r in _RESOURCES}  # reset spinner

        if self._queue_index < len(self._discard_queue):
            self._active_discarder = self._discard_queue[self._queue_index]
            self._pending = None
            self._build_static_texts()  # rebuild title for new player
        else:
            # Everyone's done — move to robber placement
            self.vm.go_to("robber_place",
                board=self.board, players=self.players, current_player=self.current_player,
                die1=self.die1, die2=self.die2, port_manager=self.port_manager
            )

    def _execute_trade(self):
        player = self.players[self._active_discarder]
        player.exchange_resources(self._resources, {})
        self._pending = None
        self._advance_queue()
