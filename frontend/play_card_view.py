"""
Contains PlayCardView Class

Responsibilities
----------------
* Show the current player's development-card inventory as face-up card sprites.
* Allow buying a new dev card (costs ORE + WHEAT + SHEEP, drawn from shared deck).
* Allow playing one card per turn — but NOT a card bought this same turn.
* Enforce "one card played per turn" rule.
* Card effects are delegated to the DevCard subclasses in dev_base.py:
    - Knight        : sets pending_robber flag, sends back to board
    - Road Building : grants 2 free roads, sends back to board
    - Year of Plenty: opens resource picker popup (apply_resource x2)
    - Monopoly      : opens resource picker popup (apply_steal x1)
    - Victory Point : never manually played; VP granted at buy time

All layout/visual constants live in constants.py.
All dev-card game logic lives in dev_base.py.
"""

import random
import arcade

from .drawing import fill_rect, outline_rect
from .constants import *
from backend.dev_base import *


class PlayCardView(arcade.View):
    """
    Development-card management screen.

    Parameters
    ----------
    board                 : CatanBoard
    players               : list[Player]
    current_player        : int
    die1, die2            : int   — current dice values (passed through)
    shared_deck           : list[str] | None
                            Game-wide dev-card deck.  Pass None only once;
                            always re-pass the same list so it empties over time.
    bought_this_turn      : bool
    played_card_this_turn : bool
    free_roads            : int   — free roads remaining from Road Building card
    """

    def __init__(
        self,
        board,
        players,
        current_player,
        die1,
        die2,
        shared_deck=None,
        bought_this_turn=False,
        played_card_this_turn=False,
        free_roads=0,
    ):
        super().__init__()
        self.board             = board
        self.players           = players
        self.current_player    = current_player
        self.die1              = die1
        self.die2              = die2
        self.bought_this_turn  = bought_this_turn
        self._played_this_turn = played_card_this_turn
        self.free_roads        = free_roads

        # Shared persistent deck
        if shared_deck is None:
            self._deck = list(DEV_CARD_DECK)
            random.shuffle(self._deck)
        else:
            self._deck = shared_deck

        # UI state
        self._hovered_card  = None
        self._selected_card = None

        # Sub-popup state
        self._sub_popup  = None   # None | ACTION_POPUP_YOP | ACTION_POPUP_MONOPOLY
        self._yop_picked = 0      # resources already picked in Year of Plenty (0-2)

        # Notification banner
        self._notification = ""
        self._notif_timer  = 0.0

        # Sprite cache  card_type -> arcade.Sprite | None
        self._card_sprites     = {}
        self._card_sprite_list = arcade.SpriteList()
        self._load_card_sprites()
        self._build_text_objects()

    # ------------------------------------------------------------------
    # Sprite loading
    def _load_card_sprites(self):
        """
        Load one sprite per card type into a SpriteList for batch drawing.
        Falls back gracefully if a sprite file is missing.
        """
        self._card_sprite_list = arcade.SpriteList()
        for card_type, path in DEV_CARD_SPRITES.items():
            try:
                spr       = arcade.Sprite(path)
                spr.scale = min(CARD_W / spr.width, CARD_H / spr.height)
                self._card_sprites[card_type] = spr
                self._card_sprite_list.append(spr)
            except Exception:
                self._card_sprites[card_type] = None

    # ------------------------------------------------------------------
    # Text objects  (pre-built to avoid per-frame allocation)
    def _build_text_objects(self):
        player = self.players[self.current_player]

        self.txt_title = arcade.Text(
            f"{player.name}  —  Development Cards",
            SCREEN_WIDTH / 2, CARD_HEADER_Y,
            TEXT_GOLD, 20, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_deck = arcade.Text(
            f"Deck: {len(self._deck)} cards remaining",
            SCREEN_WIDTH / 2, CARD_DECK_Y,
            TEXT_LIGHT_GRAY, 11,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_back = arcade.Text(
            CARD_BACK_LABEL,
            CARD_PAD + CARD_BACK_BTN_W / 2, CARD_PAD + CARD_BTN_H / 2,
            TEXT_WHITE, CARD_BACK_TEXT_SIZE, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_buy = arcade.Text(
            CARD_BUY_LABEL,
            SCREEN_WIDTH / 2, CARD_PAD + CARD_BTN_H / 2,
            TEXT_WHITE, CARD_BUY_TEXT_SIZE, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_play = arcade.Text(
            CARD_PLAY_LABEL,
            SCREEN_WIDTH - CARD_PAD - CARD_PLAY_BTN_W / 2, CARD_PAD + CARD_BTN_H / 2,
            TEXT_WHITE, CARD_PLAY_TEXT_SIZE, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_notif = arcade.Text(
            "", SCREEN_WIDTH / 2, CARD_NOTIF_Y,
            (255, 120, 80), 13, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_empty = arcade.Text(
            "You have no development cards yet.",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
            TEXT_LIGHT_GRAY, 15,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_hint = arcade.Text(
            "Click a card to select it, then press Play.",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 36,
            (100, 100, 130), 10,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_played_warn = arcade.Text(
            "✓ Card played this turn",
            SCREEN_WIDTH - CARD_PAD - CARD_BTN_W / 2, CARD_PAD + CARD_BTN_H + 13,
            (130, 220, 130), 9,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

    # ------------------------------------------------------------------
    # Helpers
    def _can_buy_card(self) -> bool:
        if not self._deck:
            return False
        p = self.players[self.current_player]
        return all(
            p.resource_cards.get(res, 0) >= amt
            for res, amt in DEV_CARD_COST.items()
        )

    def _can_play_card(self, idx: int) -> bool:
        """Delegate to the DevCard's own can_play() logic."""
        p = self.players[self.current_player]
        if idx is None or not (0 <= idx < len(p.development_cards)):
            return False
        card_obj = DevCard.from_dict(p.development_cards[idx])
        return card_obj.can_play({"played_this_turn": self._played_this_turn})

    def _notify(self, msg: str) -> None:
        self._notification = msg
        self._notif_timer  = CARD_NOTIF_TIMER

    def _card_rect(self, i: int) -> tuple:
        """Return (left, bottom, w, h) pixel rect for the i-th card."""
        player  = self.players[self.current_player]
        n       = len(player.development_cards)
        total_w = n * CARD_W + max(0, n - 1) * CARD_GAP
        start_x = SCREEN_WIDTH / 2 - total_w / 2
        left    = start_x + i * (CARD_W + CARD_GAP)
        bottom  = CARD_TOP - CARD_H
        return left, bottom, CARD_W, CARD_H

    # ------------------------------------------------------------------
    # Arcade callbacks
    def on_show_view(self):
        self._build_text_objects()

    def on_update(self, delta_time: float):
        if self._notif_timer > 0:
            self._notif_timer -= delta_time
            if self._notif_timer <= 0:
                self._notification = ""

    def on_draw(self):
        self.clear()
        arcade.set_background_color((14, 14, 30))

        fill_rect(0, CARD_BOTTOM_BAR_H, SCREEN_WIDTH,
                  SCREEN_HEIGHT - CARD_BOTTOM_BAR_H, (16, 16, 36, 255))

        # Header
        self.txt_title.draw()
        self.txt_deck.text = f"Deck: {len(self._deck)} cards remaining"
        self.txt_deck.draw()

        # Card area
        player = self.players[self.current_player]
        if not player.development_cards:
            self.txt_empty.draw()
            self.txt_hint.draw()
        else:
            self._draw_cards(player.development_cards)

        self._draw_bottom_bar()

        if self._sub_popup:
            self._draw_sub_popup()

        if self._notification:
            self.txt_notif.text = self._notification
            self.txt_notif.draw()

    # ------------------------------------------------------------------
    # Drawing helpers
    def _draw_cards(self, cards: list):
        # Pass 1 — backgrounds and sprite positions
        for i, card in enumerate(cards):
            left, bottom, w, h = self._card_rect(i)
            card_obj    = DevCard.from_dict(card)
            is_selected = (i == self._selected_card)
            is_hovered  = (i == self._hovered_card)

            lift = CARD_LIFT_SELECTED if is_selected else (
                   CARD_LIFT_HOVERED  if is_hovered  else 0)
            cb   = bottom + lift

            fill_rect(left, cb, w, h, card_obj.tint)

            spr = self._card_sprites.get(card["type"]) or self._card_sprites.get("back")
            if spr:
                spr.center_x = left + w / 2
                spr.center_y = cb   + h * CARD_SPRITE_Y_FRAC

        # Batch-draw all sprites
        self._card_sprite_list.draw()

        # Pass 2 — borders, labels, badges
        for i, card in enumerate(cards):
            left, bottom, w, h = self._card_rect(i)
            card_obj    = DevCard.from_dict(card)
            is_selected = (i == self._selected_card)
            is_hovered  = (i == self._hovered_card)

            lift = CARD_LIFT_SELECTED if is_selected else (
                   CARD_LIFT_HOVERED  if is_hovered  else 0)
            cb   = bottom + lift

            # Card-face title (small, bottom of the art area)
            arcade.Text(
                card_obj.label,
                left + w / 2, cb + 10,
                TEXT_WHITE, 8, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ).draw()

            # Border
            if is_selected:
                outline_rect(left, cb, w, h, TEXT_GOLD, CARD_BORDER_SEL)
            elif is_hovered:
                outline_rect(left, cb, w, h, (220, 220, 255, 180), CARD_BORDER_HOV)
            else:
                outline_rect(left, cb, w, h, (70, 70, 100, 200), CARD_BORDER_IDLE)

            # Label below card
            arcade.Text(
                card_obj.label,
                left + w / 2, bottom - 16,
                TEXT_GOLD if is_selected else TEXT_LIGHT_GRAY,
                9, bold=is_selected,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ).draw()

            # Tooltip on hover (not selected)
            if is_hovered and not is_selected and card_obj.description:
                arcade.Text(
                    card_obj.description,
                    left + w / 2, bottom - 30,
                    (160, 160, 200), 8,
                    anchor_x="center", anchor_y="center",
                    font_name="MedievalSharp",
                ).draw()

            # "NEW" badge for just-bought cards
            if card_obj.just_bought:
                arcade.draw_lrbt_rectangle_filled(
                    left, left + CARD_BADGE_W,
                    cb + h - CARD_BADGE_H, cb + h,
                    (200, 60, 60, 220),
                )
                arcade.Text(
                    "NEW",
                    left + CARD_BADGE_W / 2, cb + h - CARD_BADGE_H / 2,
                    TEXT_WHITE, 8, bold=True,
                    anchor_x="center", anchor_y="center",
                    font_name="MedievalSharp",
                ).draw()

    def _draw_bottom_bar(self):
        fill_rect(0, 0, SCREEN_WIDTH, CARD_BOTTOM_BAR_H, (18, 18, 42, 245))
        outline_rect(0, CARD_BOTTOM_BAR_H - 3, SCREEN_WIDTH, 3, (60, 60, 90, 200), 1)

        # Back button
        fill_rect(CARD_PAD, CARD_PAD, CARD_BACK_BTN_W, CARD_BTN_H, BTN_TRADE)
        outline_rect(CARD_PAD, CARD_PAD, CARD_BACK_BTN_W, CARD_BTN_H, (255, 255, 255, 60), 1)
        self.txt_back.draw()

        # Buy button
        buy_color = BTN_BUILD if self._can_buy_card() else BTN_DISABLED
        bx = int(SCREEN_WIDTH / 2 - CARD_BUY_BTN_W / 2)
        fill_rect(bx, CARD_PAD, CARD_BUY_BTN_W, CARD_BTN_H, buy_color)
        outline_rect(bx, CARD_PAD, CARD_BUY_BTN_W, CARD_BTN_H, (255, 255, 255, 60), 1)
        self.txt_buy.draw()

        # Play button
        can_play = (self._selected_card is not None
                    and self._can_play_card(self._selected_card))
        ply_color = BTN_CARD if can_play else BTN_DISABLED
        px = SCREEN_WIDTH - CARD_PAD - CARD_PLAY_BTN_W
        fill_rect(px, CARD_PAD, CARD_PLAY_BTN_W, CARD_BTN_H, ply_color)
        outline_rect(px, CARD_PAD, CARD_PLAY_BTN_W, CARD_BTN_H, (255, 255, 255, 60), 1)
        self.txt_play.draw()

        if self._played_this_turn:
            self.txt_played_warn.draw()

    def _draw_sub_popup(self):
        """Resource picker overlay for Year of Plenty and Monopoly."""
        ppx = SCREEN_WIDTH  / 2 - CARD_POPUP_W / 2
        ppy = SCREEN_HEIGHT / 2 - CARD_POPUP_H / 2

        fill_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 130))
        fill_rect(ppx, ppy, CARD_POPUP_W, CARD_POPUP_H, (20, 20, 55, 250))
        outline_rect(ppx, ppy, CARD_POPUP_W, CARD_POPUP_H, TEXT_GOLD, 2)

        if self._sub_popup == ACTION_POPUP_YOP:
            title = f"Year of Plenty — pick a resource ({self._yop_picked}/2)"
        else:
            title = "Monopoly — choose a resource to steal from all players"

        arcade.Text(
            title,
            SCREEN_WIDTH / 2, ppy + CARD_POPUP_H - 22,
            TEXT_GOLD, 11, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ).draw()

        resources = list(CARD_RES_NAMES.keys())
        total_bw  = (len(resources) * CARD_POPUP_BTN_W
                     + (len(resources) - 1) * CARD_POPUP_BTN_GAP)
        start     = SCREEN_WIDTH / 2 - total_bw / 2
        by        = ppy + CARD_POPUP_H / 2 - CARD_POPUP_BTN_H / 2 + 4

        for j, res in enumerate(resources):
            bx = start + j * (CARD_POPUP_BTN_W + CARD_POPUP_BTN_GAP)
            fill_rect(bx, by, CARD_POPUP_BTN_W, CARD_POPUP_BTN_H, (50, 90, 150))
            outline_rect(bx, by, CARD_POPUP_BTN_W, CARD_POPUP_BTN_H, TEXT_GOLD, 1)
            arcade.Text(
                CARD_RES_NAMES[res],
                bx + CARD_POPUP_BTN_W / 2, by + CARD_POPUP_BTN_H / 2,
                TEXT_WHITE, 10, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ).draw()

        arcade.Text(
            "[ Cancel ]",
            SCREEN_WIDTH / 2, ppy + 14,
            TEXT_LIGHT_GRAY, 9,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ).draw()

    # ------------------------------------------------------------------
    # Mouse callbacks
    def on_mouse_motion(self, x, y, dx, dy):
        if self._sub_popup:
            return
        player = self.players[self.current_player]
        self._hovered_card = None
        for i in range(len(player.development_cards)):
            left, bottom, w, h = self._card_rect(i)
            lift = CARD_LIFT_SELECTED if i == self._selected_card else 0
            if left <= x <= left + w and bottom + lift <= y <= bottom + lift + h:
                self._hovered_card = i
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if self._sub_popup:
            self._handle_sub_popup_click(x, y)
            return

        bx_buy = int(SCREEN_WIDTH / 2 - CARD_BUY_BTN_W / 2)
        bx_play = SCREEN_WIDTH - CARD_PAD - CARD_PLAY_BTN_W

        if CARD_PAD <= x <= CARD_PAD + CARD_BACK_BTN_W and CARD_PAD <= y <= CARD_PAD + CARD_BTN_H:
            self._go_back()
            return

        if bx_buy <= x <= bx_buy + CARD_BUY_BTN_W and CARD_PAD <= y <= CARD_PAD + CARD_BTN_H:
            self._buy_card()
            return

        if bx_play <= x <= bx_play + CARD_PLAY_BTN_W and CARD_PAD <= y <= CARD_PAD + CARD_BTN_H:
            self._play_selected_card()
            return

        player = self.players[self.current_player]
        for i in range(len(player.development_cards)):
            left, bottom, w, h = self._card_rect(i)
            lift = CARD_LIFT_SELECTED if i == self._selected_card else 0
            if left <= x <= left + w and bottom + lift <= y <= bottom + lift + h:
                self._selected_card = i if self._selected_card != i else None
                return

    def _handle_sub_popup_click(self, x, y):
        ppy       = SCREEN_HEIGHT / 2 - CARD_POPUP_H / 2
        resources = list(CARD_RES_NAMES.keys())
        total_bw  = (len(resources) * CARD_POPUP_BTN_W
                     + (len(resources) - 1) * CARD_POPUP_BTN_GAP)
        start     = SCREEN_WIDTH / 2 - total_bw / 2
        by        = ppy + CARD_POPUP_H / 2 - CARD_POPUP_BTN_H / 2 + 4

        for j, res in enumerate(resources):
            bx = start + j * (CARD_POPUP_BTN_W + CARD_POPUP_BTN_GAP)
            if bx <= x <= bx + CARD_POPUP_BTN_W and by <= y <= by + CARD_POPUP_BTN_H:
                if self._sub_popup == ACTION_POPUP_YOP:
                    YearOfPlentyCard.apply_resource(
                        self.players[self.current_player], res
                    )
                    self._yop_picked += 1
                    if self._yop_picked >= 2:
                        self._notify("Year of Plenty: received 2 resources!")
                        self._sub_popup  = None
                        self._yop_picked = 0
                    else:
                        self._notify(
                            f"Picked {CARD_RES_NAMES[res]}. Pick one more resource."
                        )
                elif self._sub_popup == ACTION_POPUP_MONOPOLY:
                    stolen = MonopolyCard.apply_steal(
                        self.players, self.current_player, res
                    )
                    self._notify(
                        f"Monopoly: stole {stolen} {CARD_RES_NAMES[res]} "
                        f"from all players!"
                    )
                    self._sub_popup = None
                return

        # Cancel area
        if ppy <= y <= ppy + 28 and abs(x - SCREEN_WIDTH / 2) < 55:
            self._sub_popup = None

    # ------------------------------------------------------------------
    # Actions
    def _buy_card(self):
        if not self._can_buy_card():
            msg = ("The development card deck is empty!"
                   if not self._deck
                   else "Not enough resources!  (need Ore + Wheat + Sheep)")
            self._notify(msg)
            return

        p = self.players[self.current_player]
        for res, amt in DEV_CARD_COST.items():
            p.resource_cards[res] -= amt

        card_type = self._deck.pop()
        p.development_cards.append({"type": card_type, "just_bought": True})

        if card_type == "victory_point":
            p.victory_points += 1
            self._notify(f"Drew a Victory Point card!  ({p.victory_points} VP total)")
        else:
            card_obj = DevCard.from_dict({"type": card_type, "just_bought": True})
            self._notify(f"Drew a {card_obj.label}!")

        self.bought_this_turn = True
        self._build_text_objects()

    def _play_selected_card(self):
        if self._selected_card is None:
            self._notify("Select a card first by clicking on it.")
            return
        if not self._can_play_card(self._selected_card):
            p    = self.players[self.current_player]
            card = p.development_cards[self._selected_card]
            if self._played_this_turn:
                self._notify("You already played a card this turn.")
            elif card.get("just_bought"):
                self._notify("You can't play a card the same turn you bought it.")
            else:
                self._notify("That card cannot be played right now.")
            return

        p         = self.players[self.current_player]
        card_dict = p.development_cards.pop(self._selected_card)
        card_obj  = DevCard.from_dict(card_dict)
        self._selected_card    = None
        self._played_this_turn = True

        game_state = {
            "player":           p,
            "players":          self.players,
            "current_player":   self.current_player,
            "played_this_turn": True,
            "free_roads":       self.free_roads,
        }

        action = card_obj.apply(game_state)
        self.free_roads = game_state.get("free_roads", self.free_roads)

        if action == ACTION_BACK_TO_BOARD:
            if isinstance(card_obj, KnightCard):
                self._notify("Knight played! Return to the board to move the robber.")
            elif isinstance(card_obj, RoadBuildingCard):
                self._notify("Road Building! You may place 2 free roads on the board.")
            self._go_back()
            return
        elif action == ACTION_POPUP_YOP:
            self._sub_popup  = ACTION_POPUP_YOP
            self._yop_picked = 0
            return
        elif action == ACTION_POPUP_MONOPOLY:
            self._sub_popup = ACTION_POPUP_MONOPOLY
            return

        self._build_text_objects()

    def _go_back(self):
        from .catan_view import CatanView
        self.window.show_view(
            CatanView(
                self.board,
                self.players,
                self.current_player,
                self.die1,
                self.die2,
                shared_deck=self._deck,
                bought_card_this_turn=self.bought_this_turn,
                played_card_this_turn=self._played_this_turn,
                free_roads=self.free_roads,
            )
        )