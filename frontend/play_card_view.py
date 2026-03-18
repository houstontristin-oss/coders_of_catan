"""
Contains PlayCardView Class

Responsibilities
----------------
* Show the current player's development-card inventory as face-up card sprites.
* Allow buying a new dev card (costs ORE + WHEAT + SHEEP, drawn from shared deck).
* Allow playing one card per turn — but NOT a card bought this same turn.
* Enforce "one card played per turn" rule.
* Card effects handled here:
    - Knight       : sets pending_robber flag on player (Apoorva's task hooks in)
    - Road Building: grants 2 free roads (passed back to CatanView via free_roads)
    - Year of Plenty: player picks 2 resources via in-screen popup
    - Monopoly     : player picks a resource, steals all of it from every other player
    - Victory Point: auto-counts toward VP (stored, never manually played)
    - Card HUD: controls vanity and geometry of the card inventory
"""

import random
import arcade

from .drawing import fill_rect, outline_rect
from .constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    HUD_BG, HUD_PANEL_BG, TEXT_WHITE, TEXT_GOLD, TEXT_LIGHT_GRAY,
    BTN_ENDTURN, BTN_BUILD, BTN_CARD, BTN_TRADE,
    DEV_CARD_SPRITES, DEV_CARD_DECK, DEV_CARD_COST,
    RESOURCE_ABBR,
)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
_CARD_W   = 90       # rendered card width  (px)
_CARD_H   = 130      # rendered card height (px)
_CARD_GAP = 14       # horizontal gap between cards
_CARD_TOP = SCREEN_HEIGHT - 80    # y of card tops

_BTN_W = 180
_BTN_H = 44
_PAD   = 18

# Resource key -> display name (for Year of Plenty / Monopoly pickers)
_RES_NAMES = {
    "WOOD":  "Wood",
    "BRICK": "Brick",
    "WHEAT": "Wheat",
    "SHEEP": "Sheep",
    "ORE":   "Ore",
}

# Card type -> human-readable label
_CARD_LABELS = {
    "knight":         "Knight",
    "road_building":  "Road Building",
    "year_of_plenty": "Year of Plenty",
    "monopoly":       "Monopoly",
    "victory_point":  "Vic. Point",
}

# Card type -> one-line description shown on hover
_CARD_DESC = {
    "knight":         "Move the robber",
    "road_building":  "Place 2 free roads",
    "year_of_plenty": "Take 2 resources",
    "monopoly":       "Steal one resource type",
    "victory_point":  "+1 Victory Point (auto)",
}

# Card background tints (RGBA)
_CARD_TINTS = {
    "knight":         (160,  60,  60, 255),
    "road_building":  ( 52, 100, 200, 255),
    "year_of_plenty": (200, 160,  30, 255),
    "monopoly":       (100,  40, 160, 255),
    "victory_point":  ( 30, 160, 100, 255),
}


class PlayCardView(arcade.View):
    """
    Development-card management screen.

    Parameters
    ----------
    board               : CatanBoard
    players             : list[Player]
    current_player      : int
    die1, die2          : int   — current dice values (passed through untouched)
    shared_deck         : list[str] | None
                          The game-wide dev-card deck.  Pass None only on the
                          very first call; after that always pass the same list
                          so the deck actually empties over time.
    bought_this_turn    : bool  — True if player already bought a card this turn
    played_card_this_turn : bool — True if player already played a card this turn
    free_roads          : int   — free roads remaining from Road Building card
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
        self.board              = board
        self.players            = players
        self.current_player     = current_player
        self.die1               = die1
        self.die2               = die2
        self.bought_this_turn   = bought_this_turn
        self._played_this_turn  = played_card_this_turn
        self.free_roads         = free_roads

        # Shared persistent deck
        if shared_deck is None:
            self._deck = list(DEV_CARD_DECK)
            random.shuffle(self._deck)
        else:
            self._deck = shared_deck

        # UI state
        self._hovered_card  = None
        self._selected_card = None

        # Sub-popup state (Year of Plenty / Monopoly)
        self._sub_popup     = None   # None | "year_of_plenty" | "monopoly"
        self._yop_picked    = 0      # resources already picked in YoP (0-2)

        # Notification banner
        self._notification  = ""
        self._notif_timer   = 0.0

        # Sprite cache  card_type -> arcade.Sprite | None
        self._card_sprites  = {}
        self._load_card_sprites()
        self._build_text_objects()

    # ------------------------------------------------------------------
    # Sprite loading
    # ------------------------------------------------------------------
    def _load_card_sprites(self):
        """
        Load one sprite per card type.  Keep them in a SpriteList so they
        can be batch-drawn (arcade 3.x removed individual Sprite.draw()).
        """
        self._card_sprite_list = arcade.SpriteList()
        for card_type, path in DEV_CARD_SPRITES.items():
            try:
                spr       = arcade.Sprite(path)
                spr.scale = min(_CARD_W / spr.width, _CARD_H / spr.height)
                self._card_sprites[card_type] = spr
                self._card_sprite_list.append(spr)
            except Exception:
                self._card_sprites[card_type] = None

    # ------------------------------------------------------------------
    # Text objects
    # ------------------------------------------------------------------
    def _build_text_objects(self):
        player = self.players[self.current_player]

        self.txt_title = arcade.Text(
            f"{player.name}  —  Development Cards",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT - 30,
            TEXT_GOLD, 20, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_deck = arcade.Text(
            f"Deck: {len(self._deck)} cards remaining",
            SCREEN_WIDTH / 2, SCREEN_HEIGHT - 58,
            TEXT_LIGHT_GRAY, 11,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_back = arcade.Text(
            "← Back to Board",
            _PAD + _BTN_W / 2, _PAD + _BTN_H / 2,
            TEXT_WHITE, 12, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_buy = arcade.Text(
            "Buy Card  (Ore+Wheat+Sheep)",
            SCREEN_WIDTH / 2, _PAD + _BTN_H / 2,
            TEXT_WHITE, 11, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_play = arcade.Text(
            "▶  Play Selected Card",
            SCREEN_WIDTH - _PAD - _BTN_W / 2, _PAD + _BTN_H / 2,
            TEXT_WHITE, 12, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_notif = arcade.Text(
            "", SCREEN_WIDTH / 2, 100,
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _can_buy_card(self):
        if not self._deck:
            return False
        p = self.players[self.current_player]
        return (
            p.resource_cards.get("ORE",   0) >= DEV_CARD_COST["ORE"]
            and p.resource_cards.get("WHEAT", 0) >= DEV_CARD_COST["WHEAT"]
            and p.resource_cards.get("SHEEP", 0) >= DEV_CARD_COST["SHEEP"]
        )

    def _can_play_card(self, idx):
        p = self.players[self.current_player]
        if idx is None or idx < 0 or idx >= len(p.development_cards):
            return False
        if self._played_this_turn:
            return False
        card = p.development_cards[idx]
        if card.get("just_bought"):
            return False          # can't play the turn you bought it
        if card["type"] == "victory_point":
            return False          # VP cards are never manually played
        return True

    def _notify(self, msg):
        self._notification = msg
        self._notif_timer  = 3.5

    def _card_rect(self, i):
        """Return (left, bottom, w, h) pixel rect for the i-th card."""
        player  = self.players[self.current_player]
        n       = len(player.development_cards)
        total_w = n * _CARD_W + max(0, n - 1) * _CARD_GAP
        start_x = SCREEN_WIDTH / 2 - total_w / 2
        left    = start_x + i * (_CARD_W + _CARD_GAP)
        bottom  = _CARD_TOP - _CARD_H
        return left, bottom, _CARD_W, _CARD_H

    # ------------------------------------------------------------------
    # Arcade callbacks
    # ------------------------------------------------------------------
    def on_show_view(self):
        self._build_text_objects()

    def on_update(self, delta_time):
        if self._notif_timer > 0:
            self._notif_timer -= delta_time
            if self._notif_timer <= 0:
                self._notification = ""

    def on_draw(self):
        self.clear()
        arcade.set_background_color((14, 14, 30))

        # Background panel
        fill_rect(0, 70, SCREEN_WIDTH, SCREEN_HEIGHT - 70, (16, 16, 36, 255))

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

        # Bottom bar
        self._draw_bottom_bar()

        # Sub-popup overlay
        if self._sub_popup:
            self._draw_sub_popup()

        # Notification
        if self._notification:
            self.txt_notif.text = self._notification
            self.txt_notif.draw()

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------
    def _draw_cards(self, cards):
        # ---- Pass 1: backgrounds + position sprites ----
        for i, card in enumerate(cards):
            left, bottom, w, h = self._card_rect(i)
            ctype       = card["type"]
            is_selected = (i == self._selected_card)
            just_bought = card.get("just_bought", False)

            lift = 14 if is_selected else (5 if (i == self._hovered_card) else 0)
            cb   = bottom + lift

            tint = _CARD_TINTS.get(ctype, (60, 60, 90, 255))
            if just_bought:
                tint = (60, 60, 65, 220)
            fill_rect(left, cb, w, h, tint)

            spr = self._card_sprites.get(ctype) or self._card_sprites.get("back")
            if spr:
                spr.center_x = left + w / 2
                spr.center_y = cb   + h * 0.6

        # ---- Draw all card sprites in one batch ----
        self._card_sprite_list.draw()

        # ---- Pass 2: overlays (borders, labels, badges) ----
        for i, card in enumerate(cards):
            left, bottom, w, h = self._card_rect(i)
            ctype       = card["type"]
            is_selected = (i == self._selected_card)
            is_hovered  = (i == self._hovered_card)
            just_bought = card.get("just_bought", False)

            lift = 14 if is_selected else (5 if is_hovered else 0)
            cb   = bottom + lift

            # Card title at bottom of card face
            arcade.Text(
                _CARD_LABELS.get(ctype, ctype),
                left + w / 2, cb + 10,
                TEXT_WHITE, 8, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ).draw()

            # Border
            if is_selected:
                outline_rect(left, cb, w, h, TEXT_GOLD, 3)
            elif is_hovered:
                outline_rect(left, cb, w, h, (220, 220, 255, 180), 2)
            else:
                outline_rect(left, cb, w, h, (70, 70, 100, 200), 1)

            # Label below card
            arcade.Text(
                _CARD_LABELS.get(ctype, ctype),
                left + w / 2, bottom - 16,
                TEXT_GOLD if is_selected else TEXT_LIGHT_GRAY,
                9, bold=is_selected,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ).draw()

            # Description tooltip on hover
            if is_hovered and not is_selected and ctype in _CARD_DESC:
                arcade.Text(
                    _CARD_DESC[ctype],
                    left + w / 2, bottom - 30,
                    (160, 160, 200), 8,
                    anchor_x="center", anchor_y="center",
                    font_name="MedievalSharp",
                ).draw()

            # "NEW" badge
            if just_bought:
                arcade.draw_lrbt_rectangle_filled(
                    left, left + 38, cb + h - 18, cb + h, (200, 60, 60, 220)
                )
                arcade.Text(
                    "NEW",
                    left + 19, cb + h - 9,
                    TEXT_WHITE, 8, bold=True,
                    anchor_x="center", anchor_y="center",
                    font_name="MedievalSharp",
                ).draw()

    def _draw_bottom_bar(self):
        fill_rect(0, 0, SCREEN_WIDTH, 70, (18, 18, 42, 245))
        outline_rect(0, 67, SCREEN_WIDTH, 3, (60, 60, 90, 200), 1)

        # Back
        fill_rect(_PAD, _PAD, _BTN_W, _BTN_H, BTN_TRADE)
        outline_rect(_PAD, _PAD, _BTN_W, _BTN_H, (255, 255, 255, 60), 1)
        self.txt_back.draw()

        # Buy
        can_buy   = self._can_buy_card()
        buy_color = BTN_BUILD if can_buy else (45, 45, 55)
        bx = int(SCREEN_WIDTH / 2 - _BTN_W / 2)
        fill_rect(bx, _PAD, _BTN_W, _BTN_H, buy_color)
        outline_rect(bx, _PAD, _BTN_W, _BTN_H, (255, 255, 255, 60), 1)
        self.txt_buy.draw()

        # Play
        can_play  = self._selected_card is not None and self._can_play_card(self._selected_card)
        ply_color = BTN_CARD if can_play else (45, 45, 55)
        px = SCREEN_WIDTH - _PAD - _BTN_W
        fill_rect(px, _PAD, _BTN_W, _BTN_H, ply_color)
        outline_rect(px, _PAD, _BTN_W, _BTN_H, (255, 255, 255, 60), 1)
        self.txt_play.draw()

        # "Already played" warning
        if self._played_this_turn:
            arcade.Text(
                "✓ Card played this turn",
                SCREEN_WIDTH - _PAD - _BTN_W / 2, _PAD + _BTN_H + 13,
                (130, 220, 130), 9,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ).draw()

    def _draw_sub_popup(self):
        """Resource picker overlay for Year of Plenty and Monopoly."""
        pw, ph = 370, 180
        ppx = SCREEN_WIDTH  / 2 - pw / 2
        ppy = SCREEN_HEIGHT / 2 - ph / 2

        # Dark backdrop
        fill_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 130))
        fill_rect(ppx, ppy, pw, ph, (20, 20, 55, 250))
        outline_rect(ppx, ppy, pw, ph, TEXT_GOLD, 2)

        if self._sub_popup == "year_of_plenty":
            title = f"Year of Plenty — pick a resource ({self._yop_picked}/2)"
        else:
            title = "Monopoly — choose a resource to steal from all players"

        arcade.Text(
            title,
            SCREEN_WIDTH / 2, ppy + ph - 22,
            TEXT_GOLD, 11, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ).draw()

        resources = list(_RES_NAMES.keys())
        btn_w, btn_h, gap = 60, 36, 8
        total_bw = len(resources) * btn_w + (len(resources) - 1) * gap
        start    = SCREEN_WIDTH / 2 - total_bw / 2
        by       = ppy + ph / 2 - btn_h / 2 + 4

        for j, res in enumerate(resources):
            bx = start + j * (btn_w + gap)
            fill_rect(bx, by, btn_w, btn_h, (50, 90, 150))
            outline_rect(bx, by, btn_w, btn_h, TEXT_GOLD, 1)
            arcade.Text(
                _RES_NAMES[res],
                bx + btn_w / 2, by + btn_h / 2,
                TEXT_WHITE, 10, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ).draw()

        # Cancel
        arcade.Text(
            "[ Cancel ]",
            SCREEN_WIDTH / 2, ppy + 14,
            TEXT_LIGHT_GRAY, 9,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ).draw()

    # ------------------------------------------------------------------
    # Mouse callbacks
    # ------------------------------------------------------------------
    def on_mouse_motion(self, x, y, dx, dy):
        if self._sub_popup:
            return
        player = self.players[self.current_player]
        self._hovered_card = None
        for i in range(len(player.development_cards)):
            left, bottom, w, h = self._card_rect(i)
            lift = 14 if i == self._selected_card else 0
            if left <= x <= left + w and bottom + lift <= y <= bottom + lift + h:
                self._hovered_card = i
                break

    def on_mouse_press(self, x, y, button, modifiers):
        # --- Sub-popup intercepts all clicks ---
        if self._sub_popup:
            self._handle_sub_popup_click(x, y)
            return

        player  = self.players[self.current_player]
        bx_buy  = int(SCREEN_WIDTH / 2 - _BTN_W / 2)
        bx_play = SCREEN_WIDTH - _PAD - _BTN_W

        # Back
        if _PAD <= x <= _PAD + _BTN_W and _PAD <= y <= _PAD + _BTN_H:
            self._go_back()
            return

        # Buy
        if bx_buy <= x <= bx_buy + _BTN_W and _PAD <= y <= _PAD + _BTN_H:
            self._buy_card()
            return

        # Play
        if bx_play <= x <= bx_play + _BTN_W and _PAD <= y <= _PAD + _BTN_H:
            self._play_selected_card()
            return

        # Card selection / deselection
        for i in range(len(player.development_cards)):
            left, bottom, w, h = self._card_rect(i)
            lift = 14 if i == self._selected_card else 0
            if left <= x <= left + w and bottom + lift <= y <= bottom + lift + h:
                self._selected_card = i if self._selected_card != i else None
                return

    def _handle_sub_popup_click(self, x, y):
        pw, ph  = 370, 180
        ppy     = SCREEN_HEIGHT / 2 - ph / 2
        resources = list(_RES_NAMES.keys())
        btn_w, btn_h, gap = 60, 36, 8
        total_bw = len(resources) * btn_w + (len(resources) - 1) * gap
        start    = SCREEN_WIDTH / 2 - total_bw / 2
        by       = ppy + ph / 2 - btn_h / 2 + 4

        for j, res in enumerate(resources):
            bx = start + j * (btn_w + gap)
            if bx <= x <= bx + btn_w and by <= y <= by + btn_h:
                if self._sub_popup == "year_of_plenty":
                    self.players[self.current_player].resource_cards[res] += 1
                    self._yop_picked += 1
                    if self._yop_picked >= 2:
                        self._notify("Year of Plenty: received 2 resources!")
                        self._sub_popup   = None
                        self._yop_picked  = 0
                    else:
                        self._notify(f"Picked {_RES_NAMES[res]}. Pick one more resource.")
                elif self._sub_popup == "monopoly":
                    stolen = 0
                    for pi, p in enumerate(self.players):
                        if pi != self.current_player:
                            amt = p.resource_cards.get(res, 0)
                            p.resource_cards[res] = 0
                            stolen += amt
                    self.players[self.current_player].resource_cards[res] += stolen
                    self._notify(f"Monopoly: stole {stolen} {_RES_NAMES[res]} from all players!")
                    self._sub_popup = None
                return

        # Cancel button area
        if ppy <= y <= ppy + 28 and abs(x - SCREEN_WIDTH / 2) < 55:
            self._sub_popup = None

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _buy_card(self):
        if not self._can_buy_card():
            if not self._deck:
                self._notify("The development card deck is empty!")
            else:
                self._notify("Not enough resources!  (need Ore + Wheat + Sheep)")
            return

        p = self.players[self.current_player]
        for res, amt in DEV_CARD_COST.items():
            p.resource_cards[res] -= amt

        card_type  = self._deck.pop()
        card_entry = {"type": card_type, "just_bought": True}
        p.development_cards.append(card_entry)

        if card_type == "victory_point":
            p.victory_points += 1
            self._notify(f"Drew a Victory Point card!  ({p.victory_points} VP total)")
        else:
            self._notify(f"Drew a {_CARD_LABELS.get(card_type, card_type)}!")

        self.bought_this_turn = True
        self._build_text_objects()

    def _play_selected_card(self):
        if self._selected_card is None:
            self._notify("Select a card first by clicking on it.")
            return
        if not self._can_play_card(self._selected_card):
            if self._played_this_turn:
                self._notify("You already played a card this turn.")
            elif self.players[self.current_player].development_cards[self._selected_card].get("just_bought"):
                self._notify("You can't play a card the same turn you bought it.")
            else:
                self._notify("That card cannot be played right now.")
            return

        p     = self.players[self.current_player]
        card  = p.development_cards.pop(self._selected_card)
        ctype = card["type"]
        self._selected_card   = None
        self._played_this_turn = True

        if ctype == "knight":
            # Signal to Apoorva's robber system
            p.__dict__["pending_robber"] = True
            self._notify("Knight played! Return to the board to move the robber.")

        elif ctype == "road_building":
            self.free_roads = 2
            self._notify("Road Building! You may place 2 free roads on the board.")
            self._go_back()
            return

        elif ctype == "year_of_plenty":
            self._sub_popup  = "year_of_plenty"
            self._yop_picked = 0
            return

        elif ctype == "monopoly":
            self._sub_popup = "monopoly"
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