"""
Contains CatanView Class
"""
import math
import arcade
import random

from backend.catan_board import CatanBoard

from .play_card_view import PlayCardView
from .trade_view import TradeView
from .end_view import EndView
from .board_utils import cubic_to_pixel, node_to_pixel, get_hex_corners
from .ports import PortManager
from .drawing import fill_rect, outline_rect, draw_settlement, draw_city, draw_road, draw_board
from .constants import (
    BUILD_NONE, BACKGROUND_IMAGE, SCREEN_WIDTH, SCREEN_HEIGHT,
    BOARD_CENTER_X, BOARD_CENTER_Y, RESOURCE_ABBR, HEX_SIZE,
    RESOURCE_SPRITES, SPRITE_SCALE, TEXT_WHITE, TEXT_GOLD, TEXT_LIGHT_GRAY,
    HUD_BOTTOM_HEIGHT, HUD_BG, DICE_AREA_HEIGHT, DICE_AREA_WIDTH,
    HUD_PANEL_HEIGHT, HUD_PANEL_BG, HUD_PANEL_WIDTH, ICON_SIZE,
    BTN_BUILD, BTN_BUILD_ACTIVE, BTN_CARD, BTN_ENDTURN, BTN_TRADE,
    BUILD_SETTLEMENT, BUILD_ROAD, SETTLEMENT_COST, ROAD_COST, CITY_COST,
    RESOURCE_COLORS, NODE_SNAP_RADIUS, EDGE_SNAP_RADIUS,
    ROBBER_SPRITE, BUILD_CITY, ONE, SIX,
    DICE_SPRITES, DICE_ROLL_DURATION, DICE_ROLL_FLIP_RATE, USE_DICE_SPRITES,
    DEV_CARD_COST,
)


class CatanView(arcade.View):
    """
    CatanView Class

    Extra parameters (all optional, forwarded from PlayCardView when returning):
        shared_deck          : list[str] | None  — the game-wide dev-card deck
        bought_card_this_turn: bool — player already bought a dev card this turn
        played_card_this_turn: bool — player already played a dev card this turn
        free_roads           : int  — free roads remaining from Road Building card
    """
    def __init__(
        self,
        board,
        players,
        current_player,
        die1,
        die2,
        shared_deck=None,
        bought_card_this_turn=False,
        played_card_this_turn=False,
        free_roads=0,
    ):
        super().__init__()
        self.board          = board
        self.players        = players
        self.current_player = current_player
        self.die1           = die1
        self.die2           = die2

        # Dev-card session state (preserved across CatanView <-> PlayCardView round-trips)
        self._shared_deck           = shared_deck   # None = PlayCardView will build it on first open
        self._bought_card_this_turn = bought_card_this_turn
        self._played_card_this_turn = played_card_this_turn
        self._free_roads            = free_roads    # free road placements remaining

        # Build mode state
        self.build_mode    = False
        self.build_choice  = BUILD_NONE
        self.hovered_node  = None
        self.hovered_edge  = None
        self.selected_node = None
        self.selected_edge = None
        self.show_confirm  = False

        # --- Dice animation state ---
        self._dice_animating  = False
        self._dice_anim_timer = 0.0
        self._dice_flip_timer = 0.0
        self._anim_die1       = die1   # face showing during animation
        self._anim_die2       = die2
        self._dice_sprites    = {}     # face value (1-6) -> arcade.Sprite | None
        self._load_dice_sprites()

        # --- Robber state ---
        self._robber_sprite    = None
        self._robber_list      = arcade.SpriteList()
        self._robber_sprite_ok = False
        self._robber_tile      = None
        self._load_robber_sprite()

        # --- Port hover state ---
        self._hovered_port_nodes = []

        # Pixel caches
        self._node_pixel_cache = {}
        self._edge_pixel_cache = {}
        self.port_manager      = None

        self._load_background()
        self._build_text_objects()
        self._load_resource_icons()
        self._assign_number_tokens()
        self._build_node_pixel_cache()
        self._build_edge_pixel_cache()
        self.port_manager = PortManager(self.board, self._edge_pixel_cache)
        self._build_text_objects()   # rebuild after caches ready

    # -----------------------------------------------------------------------
    # Dice sprites
    # -----------------------------------------------------------------------
    def _load_dice_sprites(self):
        """Load the six die-face sprites into a SpriteList for batch drawing."""
        self._dice_sprite_list = arcade.SpriteList()
        for face in range(1, 7):
            path = DICE_SPRITES.get(face)
            try:
                spr = arcade.Sprite(path)
                self._dice_sprites[face] = spr
                self._dice_sprite_list.append(spr)
            except Exception:
                self._dice_sprites[face] = None

    def _start_dice_animation(self):
        self._dice_animating  = True
        self._dice_anim_timer = DICE_ROLL_DURATION
        self._dice_flip_timer = DICE_ROLL_FLIP_RATE

    # -----------------------------------------------------------------------
    # Robber sprite
    # -----------------------------------------------------------------------
    def _load_robber_sprite(self):
        try:
            self._robber_sprite = arcade.Sprite(ROBBER_SPRITE)
            self._robber_list   = arcade.SpriteList()
            self._robber_list.append(self._robber_sprite)
            self._robber_sprite_ok = True
        except Exception:
            self._robber_sprite_ok = False
        self._place_robber_on_desert()

    def _place_robber_on_desert(self):
        from .board_utils import cubic_to_pixel
        for xyz, tile in self.board.tiles.items():
            if tile.resource == "desert":
                self._robber_tile = tile
                if self._robber_sprite_ok:
                    cx, _, cz = xyz
                    px, py    = cubic_to_pixel(cx, cz, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
                    target_h  = HEX_SIZE * 1.1
                    scale     = target_h / self._robber_sprite.height
                    self._robber_sprite.scale    = scale
                    self._robber_sprite.center_x = px
                    self._robber_sprite.center_y = py
                break

    # -----------------------------------------------------------------------
    # Background
    # -----------------------------------------------------------------------
    def _load_background(self):
        try:
            self.bg_sprite          = arcade.Sprite(BACKGROUND_IMAGE)
            self.bg_sprite.center_x = SCREEN_WIDTH  / 2
            self.bg_sprite.center_y = SCREEN_HEIGHT / 2
            scale_x                 = SCREEN_WIDTH  / self.bg_sprite.width
            scale_y                 = SCREEN_HEIGHT / self.bg_sprite.height
            self.bg_sprite.scale    = max(scale_x, scale_y)
            self.bg_list            = arcade.SpriteList()
            self.bg_list.append(self.bg_sprite)
        except Exception:
            self.bg_sprite = None
            self.bg_list   = None
            arcade.set_background_color(arcade.color.OCEAN_BOAT_BLUE)

    # -----------------------------------------------------------------------
    # Number token assignment
    # -----------------------------------------------------------------------
    def _assign_number_tokens(self):
        pass   # tile.number is already set by backend.make_board()

    # -----------------------------------------------------------------------
    # Caches
    # -----------------------------------------------------------------------
    def _build_node_pixel_cache(self):
        for node_id in self.board.nodes:
            px, py = node_to_pixel(node_id)
            self._node_pixel_cache[node_id] = (px, py)

    def _build_edge_pixel_cache(self):
        for edge_id in self.board.edges:
            n1_id, n2_id = edge_id
            x1, y1 = self._node_pixel_cache[n1_id]
            x2, y2 = self._node_pixel_cache[n2_id]
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            self._edge_pixel_cache[edge_id] = (mx, my, x1, y1, x2, y2)

    # -----------------------------------------------------------------------
    # Sprites
    # -----------------------------------------------------------------------
    def _load_resource_icons(self):
        self.resource_icons   = {}
        self.icon_sprite_list = arcade.SpriteList()
        for res in ["brick", "ore", "wheat", "sheep", "forest"]:
            sprite = arcade.Sprite(RESOURCE_SPRITES[res], scale=SPRITE_SCALE)
            self.resource_icons[res] = sprite
            self.icon_sprite_list.append(sprite)

    # -----------------------------------------------------------------------
    # Text objects
    # -----------------------------------------------------------------------
    def _build_text_objects(self):
        _BW  = 120
        _BH  = 38
        _GAP = 8
        _PAD = 14

        trade_bottom = _PAD
        build_bottom = trade_bottom + _BH + _GAP
        card_bottom  = build_bottom + _BH + _GAP

        self.txt_trade = arcade.Text(
            "Trade", _PAD + _BW / 2, trade_bottom + _BH / 2,
            TEXT_WHITE, 12, bold=True, anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_build = arcade.Text(
            "Build", _PAD + _BW / 2, build_bottom + _BH / 2,
            TEXT_WHITE, 12, bold=True, anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_card = arcade.Text(
            "Dev Cards", _PAD + _BW / 2, card_bottom + _BH / 2,
            TEXT_WHITE, 11, bold=True, anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

        _EW = 130
        self.txt_end = arcade.Text(
            "End Turn", SCREEN_WIDTH - _PAD - _EW / 2, _PAD + _BH / 2,
            TEXT_WHITE, 12, bold=True, anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - 10
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - 10
        self.txt_dice_label = arcade.Text(
            "Dice Roll", dx + DICE_AREA_WIDTH / 2, dy + DICE_AREA_HEIGHT - 16,
            TEXT_GOLD, 11, bold=True, anchor_x="center",
            font_name="MedievalSharp",
        )
        self.txt_dice_hint = arcade.Text(
            "Auto-rolls on turn start",
            dx + DICE_AREA_WIDTH / 2, dy + 7,
            TEXT_LIGHT_GRAY, 8, anchor_x="center",
            font_name="MedievalSharp",
        )

        self.txt_submenu_settlement = arcade.Text(
            "", 0, 0, TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center", font_name="MedievalSharp",
        )
        self.txt_submenu_city = arcade.Text(
            "", 0, 0, TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center", font_name="MedievalSharp",
        )
        self.txt_submenu_road = arcade.Text(
            "", 0, 0, TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center", font_name="MedievalSharp",
        )

        self.txt_popup_title = arcade.Text(
            "", 0, 0, TEXT_GOLD, 10, bold=True,
            anchor_x="center", anchor_y="center", font_name="MedievalSharp",
        )
        self.txt_popup_confirm = arcade.Text(
            "", 0, 0, TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center", font_name="MedievalSharp",
        )
        self.txt_popup_cancel = arcade.Text(
            "Cancel", 0, 0, TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center", font_name="MedievalSharp",
        )

        self._build_player_texts()
        self._build_dice_texts()

    def _build_dice_texts(self):
        """Pre-build the fallback number Text objects for the dice area."""
        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - 10
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - 10
        die_size = 40
        die_gap  = 12
        die1_x   = dx + (DICE_AREA_WIDTH - 2 * die_size - die_gap) / 2
        die_y    = dy + 20

        self.txt_die1 = arcade.Text(
            f"{self.die1}",
            die1_x + die_size / 2, die_y + die_size / 2,
            TEXT_WHITE, 18, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_die2 = arcade.Text(
            f"{self.die2}",
            die1_x + die_size + die_gap + die_size / 2, die_y + die_size / 2,
            TEXT_WHITE, 18, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

    def _build_player_texts(self):
        player    = self.players[self.current_player]
        panel_x   = 8
        panel_top = SCREEN_HEIGHT - 8
        row_h     = 24

        self.txt_player_name = arcade.Text(
            player.name,
            panel_x + HUD_PANEL_WIDTH // 2, panel_top - 18,
            TEXT_GOLD, 12, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_player_vp = arcade.Text(
            f"Victory Points: {player.victory_points}",
            panel_x + HUD_PANEL_WIDTH // 2 + 10, panel_top - 18 - row_h,
            TEXT_LIGHT_GRAY, 10,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

        order  = ["BRICK", "ORE", "WHEAT", "SHEEP", "WOOD"]
        labels = {"BRICK": "Brick", "ORE": "Ore", "WHEAT": "Wheat",
                  "SHEEP": "Sheep", "WOOD": "Wood"}

        self.txt_resources = []
        for i, res in enumerate(order):
            ry = panel_top - 18 - row_h * 2 - i * (ICON_SIZE + 4) - ICON_SIZE // 2
            self.txt_resources.append(
                arcade.Text(
                    f"{labels[res]}: {player.resource_cards.get(res)}",
                    panel_x + ICON_SIZE + 35, ry,
                    TEXT_WHITE, 9,
                    anchor_y="center",
                    font_name="MedievalSharp",
                )
            )

        # Dev-card count badge at the bottom of the panel
        n_cards = len(player.development_cards)
        self.txt_dev_card_count = arcade.Text(
            f"Dev Cards: {n_cards}",
            panel_x + HUD_PANEL_WIDTH // 2, panel_top - 18 - row_h * 2 - (ICON_SIZE + 4) * 5 - 8,
            (180, 120, 255), 9,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

    # -----------------------------------------------------------------------
    # Affordability
    # -----------------------------------------------------------------------
    def _can_afford(self, cost_dict):
        res = self.players[self.current_player].resource_cards
        return all(res.get(r, 0) >= amt for r, amt in cost_dict.items())

    # -----------------------------------------------------------------------
    # on_update — dice animation tick
    # -----------------------------------------------------------------------
    def on_update(self, delta_time):
        if not self._dice_animating:
            return

        self._dice_anim_timer -= delta_time
        self._dice_flip_timer -= delta_time

        if self._dice_flip_timer <= 0:
            self._dice_flip_timer = DICE_ROLL_FLIP_RATE
            self._anim_die1 = random.randint(ONE, SIX)
            self._anim_die2 = random.randint(ONE, SIX)

        if self._dice_anim_timer <= 0:
            # Animation finished — lock to real values
            self._dice_animating = False
            self._anim_die1 = self.die1
            self._anim_die2 = self.die2
            # Update fallback text too
            self.txt_die1.text = str(self.die1)
            self.txt_die2.text = str(self.die2)

    # -----------------------------------------------------------------------
    # HUD draw helpers
    # -----------------------------------------------------------------------
    def _draw_bottom_bar(self):
        _BW  = 120
        _BH  = 38
        _GAP = 8
        _PAD = 14

        trade_bottom = _PAD
        build_bottom = trade_bottom + _BH + _GAP
        card_bottom  = build_bottom + _BH + _GAP

        build_col = BTN_BUILD_ACTIVE if self.build_mode else BTN_BUILD

        for bottom, color in [
            (trade_bottom, BTN_TRADE),
            (build_bottom, build_col),
            (card_bottom,  BTN_CARD),
        ]:
            fill_rect(_PAD + 2, bottom - 2, _BW, _BH, (0, 0, 0, 100))
            fill_rect(_PAD, bottom, _BW, _BH, color)
            outline_rect(_PAD, bottom, _BW, _BH, (255, 255, 255, 60), 1)

        # Free-roads indicator on the "Dev Cards" button
        if self._free_roads > 0:
            arcade.Text(
                f"Free roads: {self._free_roads}",
                _PAD + _BW / 2, card_bottom + _BH + 6,
                (100, 255, 100), 8, bold=True,
                anchor_x="center", anchor_y="bottom",
                font_name="MedievalSharp",
            ).draw()

        _EW = 130
        fill_rect(SCREEN_WIDTH - _PAD - _EW + 2, _PAD - 2, _EW, _BH, (0, 0, 0, 100))
        fill_rect(SCREEN_WIDTH - _PAD - _EW, _PAD, _EW, _BH, BTN_ENDTURN)
        outline_rect(SCREEN_WIDTH - _PAD - _EW, _PAD, _EW, _BH, (255, 255, 255, 60), 1)

        self.txt_trade.draw()
        self.txt_build.draw()
        self.txt_card.draw()
        self.txt_end.draw()

    def _draw_build_submenu(self):
        if not self.build_mode or self.build_choice != BUILD_NONE:
            return

        _BW    = 120
        _BH    = 38
        _GAP   = 8
        _PAD   = 14
        _YDIFF = 36

        build_bottom = _PAD + _BH + _GAP
        build_top    = build_bottom + _BH
        menu_w = _BW
        menu_h = 120
        bx     = _PAD
        by     = build_top + 4

        fill_rect(bx, by, menu_w, menu_h, HUD_PANEL_BG)
        outline_rect(bx, by, menu_w, menu_h, TEXT_GOLD, 2)

        c_col = (255, 102, 0) if self._can_afford(CITY_COST) else (70, 70, 70)
        fill_rect(bx + 8, by + (8 + 2 * _YDIFF), menu_w - 16, 28, c_col)
        self.txt_submenu_city.text = "City"
        self.txt_submenu_city.x    = bx + menu_w / 2
        self.txt_submenu_city.y    = by + (22 + 2 * _YDIFF)
        self.txt_submenu_city.draw()

        s_col = (39, 174, 96) if self._can_afford(SETTLEMENT_COST) else (70, 70, 70)
        fill_rect(bx + 8, by + (8 + _YDIFF), menu_w - 16, 28, s_col)
        self.txt_submenu_settlement.text = "Settlement"
        self.txt_submenu_settlement.x    = bx + menu_w / 2
        self.txt_submenu_settlement.y    = by + (22 + _YDIFF)
        self.txt_submenu_settlement.draw()

        r_col = (52, 152, 219) if self._can_afford(ROAD_COST) else (70, 70, 70)
        fill_rect(bx + 8, by + 8, menu_w - 16, 28, r_col)
        self.txt_submenu_road.text = "Road"
        self.txt_submenu_road.x    = bx + menu_w / 2
        self.txt_submenu_road.y    = by + 22
        self.txt_submenu_road.draw()

    def _draw_player_panel(self):
        player  = self.players[self.current_player]
        panel_x = 8
        panel_y = SCREEN_HEIGHT - HUD_PANEL_HEIGHT - 8

        fill_rect(panel_x, panel_y, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, HUD_PANEL_BG)
        outline_rect(panel_x, panel_y, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, player.color)

        arcade.draw_circle_filled(panel_x + 14, panel_y + HUD_PANEL_HEIGHT - 18, 7, player.color)

        self.txt_player_name.draw()
        self.txt_player_vp.draw()

        order     = ["brick", "ore", "wheat", "sheep", "forest"]
        panel_top = SCREEN_HEIGHT - 8
        row_h     = 24

        for i, res in enumerate(order):
            ry = panel_top - 25 - row_h * 2 - i * (ICON_SIZE + 5)
            sprite          = self.resource_icons[res]
            sprite.center_x = panel_x + ICON_SIZE // 2 + 4
            sprite.center_y = ry

        self.icon_sprite_list.draw()
        for txt in self.txt_resources:
            txt.draw()
        self.txt_dev_card_count.draw()

    def _draw_dice_area(self):
        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - 10
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - 10

        fill_rect(dx, dy, DICE_AREA_WIDTH, DICE_AREA_HEIGHT, HUD_PANEL_BG)
        outline_rect(dx, dy, DICE_AREA_WIDTH, DICE_AREA_HEIGHT, TEXT_LIGHT_GRAY)

        self.txt_dice_label.draw()

        die_size = 40
        die_gap  = 12
        die1_x   = dx + (DICE_AREA_WIDTH - 2 * die_size - die_gap) / 2
        die_y    = dy + 20

        face1 = self._anim_die1 if self._dice_animating else self.die1
        face2 = self._anim_die2 if self._dice_animating else self.die2

        if USE_DICE_SPRITES and self._dice_sprites.get(face1) and self._dice_sprites.get(face2):
            # Use die-face sprites
            spr1 = self._dice_sprites[face1]
            spr2 = self._dice_sprites[face2]
            target = die_size

            spr1.scale    = target / max(spr1.width, spr1.height)
            spr1.center_x = die1_x + die_size / 2
            spr1.center_y = die_y  + die_size / 2

            spr2.scale    = target / max(spr2.width, spr2.height)
            spr2.center_x = die1_x + die_size + die_gap + die_size / 2
            spr2.center_y = die_y  + die_size / 2

            # White backgrounds so the sprites are legible on dark panel
            fill_rect(die1_x,                        die_y, die_size, die_size, (248, 248, 248))
            fill_rect(die1_x + die_size + die_gap,   die_y, die_size, die_size, (248, 248, 248))

            # Draw both dice via a small SpriteList (arcade 3.x removed Sprite.draw())
            _tmp = arcade.SpriteList()
            _tmp.append(spr1)
            _tmp.append(spr2)
            _tmp.draw()

            # Shake effect during animation
            if self._dice_animating:
                alpha = int(180 * (self._dice_anim_timer / DICE_ROLL_DURATION))
                outline_rect(die1_x,                       die_y, die_size, die_size, (255, 215, 0, alpha), 2)
                outline_rect(die1_x + die_size + die_gap,  die_y, die_size, die_size, (255, 215, 0, alpha), 2)
        else:
            # Fallback: coloured squares with numbers
            fill_rect(die1_x,                       die_y, die_size, die_size, (60, 60, 90))
            fill_rect(die1_x + die_size + die_gap,  die_y, die_size, die_size, (60, 60, 90))

            arcade.Text(
                str(face1),
                die1_x + die_size / 2, die_y + die_size / 2,
                TEXT_WHITE, 18, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ).draw()
            arcade.Text(
                str(face2),
                die1_x + die_size + die_gap + die_size / 2, die_y + die_size / 2,
                TEXT_WHITE, 18, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ).draw()

        # Total roll label (only when not animating)
        if not self._dice_animating:
            arcade.Text(
                f"Total: {self.die1 + self.die2}",
                dx + DICE_AREA_WIDTH / 2, dy + 7,
                TEXT_LIGHT_GRAY, 9, anchor_x="center",
                font_name="MedievalSharp",
            ).draw()

    # -----------------------------------------------------------------------
    # Port drawing
    # -----------------------------------------------------------------------
    def _draw_ports(self):
        self.port_manager.draw()

    # -----------------------------------------------------------------------
    # Board pieces (always drawn)
    # -----------------------------------------------------------------------
    def _draw_placed_pieces(self):
        for edge_id, edge_obj in self.board.edges.items():
            if edge_obj.player is not None:
                mx, my, x1, y1, x2, y2 = self._edge_pixel_cache[edge_id]
                draw_road(x1, y1, x2, y2, self.players[edge_obj.player].color)

        for node_id, node_obj in self.board.nodes.items():
            if node_obj.player is not None:
                npx, npy = self._node_pixel_cache[node_id]
                if node_obj.building == "settlement":
                    draw_settlement(npx, npy, 14, self.players[node_obj.player].color)
                if node_obj.building == "city":
                    draw_city(npx, npy, 18, self.players[node_obj.player].color)

    # -----------------------------------------------------------------------
    # Ghost highlights
    # -----------------------------------------------------------------------
    def _draw_node_highlights(self):
        player_color = self.players[self.current_player].color
        for node_id, node_obj in self.board.nodes.items():
            if not node_obj.is_valid_settlement_placement(self.current_player):
                continue
            npx, npy = self._node_pixel_cache[node_id]
            if npy < 10:
                continue
            if npx < HUD_PANEL_WIDTH + 5 or npx > SCREEN_WIDTH - DICE_AREA_WIDTH - 15:
                continue
            if node_obj is self.hovered_node:
                arcade.draw_circle_filled(npx, npy, 12, (*player_color, 180))
                arcade.draw_circle_outline(npx, npy, 14, player_color, 3)
            else:
                arcade.draw_circle_filled(npx, npy, 8, (255, 255, 255, 60))
                arcade.draw_circle_outline(npx, npy, 8, (255, 255, 255, 120), 1)

    def _draw_city_highlights(self):
        player_color = self.players[self.current_player].color
        for node_id, node_obj in self.board.nodes.items():
            if not node_obj.is_valid_city_placement(self.current_player):
                continue
            npx, npy = self._node_pixel_cache[node_id]
            if npy < 10:
                continue
            if npx < HUD_PANEL_WIDTH + 5 or npx > SCREEN_WIDTH - DICE_AREA_WIDTH - 15:
                continue
            if node_obj is self.hovered_node:
                arcade.draw_circle_filled(npx, npy, 12, (*player_color, 180))
                arcade.draw_circle_outline(npx, npy, 14, player_color, 3)
            else:
                arcade.draw_circle_filled(npx, npy, 8, (255, 255, 255, 60))
                arcade.draw_circle_outline(npx, npy, 8, (255, 255, 255, 120), 1)

    def _draw_edge_highlights(self):
        player_color = self.players[self.current_player].color
        for edge_id, edge_obj in self.board.edges.items():
            if edge_obj.player is not None:
                continue
            mx, my, x1, y1, x2, y2 = self._edge_pixel_cache[edge_id]
            if my < 10:
                continue
            if edge_obj is self.hovered_edge:
                arcade.draw_line(x1, y1, x2, y2, (*player_color, 200), 6)
                arcade.draw_circle_filled(mx, my, 7, (*player_color, 220))
            else:
                arcade.draw_line(x1, y1, x2, y2, (255, 255, 255, 50), 3)

    # -----------------------------------------------------------------------
    # Confirmation popup
    # -----------------------------------------------------------------------
    def _draw_confirm_popup(self):
        if not self.show_confirm:
            return
        if self.build_choice == BUILD_SETTLEMENT and self.selected_node:
            cx, cy = self._node_pixel_cache[self.selected_node.node_id]
            cy    += 18
            can    = self._can_afford(SETTLEMENT_COST)
            label  = "Build Settlement?"
        elif self.build_choice == BUILD_CITY and self.selected_node:
            cx, cy = self._node_pixel_cache[self.selected_node.node_id]
            cy    += 18
            can    = self._can_afford(CITY_COST)
            label  = "Build City?"
        elif self.build_choice == BUILD_ROAD and self.selected_edge:
            mx, my, *_ = self._edge_pixel_cache[self.selected_edge.edge_id]
            cx, cy = mx, my + 18
            # Free roads count as affordable
            can    = self._free_roads > 0 or self._can_afford(ROAD_COST)
            label  = "Build Road? (FREE)" if self._free_roads > 0 else "Build Road?"
        else:
            return

        popup_w  = 160
        popup_h  = 70
        pop_left = cx - popup_w / 2

        fill_rect(pop_left, cy, popup_w, popup_h, (20, 20, 40, 220))
        outline_rect(pop_left, cy, popup_w, popup_h, TEXT_GOLD, 2)
        self.txt_popup_title.text = label
        self.txt_popup_title.x    = cx
        self.txt_popup_title.y    = cy + popup_h - 14
        self.txt_popup_title.draw()

        btn_col = (39, 174, 96) if can else (80, 80, 80)
        fill_rect(pop_left + 8,         cy + 8, 66, 30, btn_col)
        self.txt_popup_confirm.text = "Confirm" if can else "No Res."
        self.txt_popup_confirm.x    = pop_left + 41
        self.txt_popup_confirm.y    = cy + 23
        self.txt_popup_confirm.draw()

        fill_rect(pop_left + popup_w - 74, cy + 8, 66, 30, (180, 50, 50))
        self.txt_popup_cancel.x = pop_left + popup_w - 41
        self.txt_popup_cancel.y = cy + 23
        self.txt_popup_cancel.draw()

    # -----------------------------------------------------------------------
    # Port hover highlights
    # -----------------------------------------------------------------------
    def _draw_port_hover_highlights(self):
        if not self._hovered_port_nodes:
            return
        for px, py in self._hovered_port_nodes:
            arcade.draw_circle_filled(px, py, 16, (255, 215, 0, 55))
            arcade.draw_circle_filled(px, py, 11, (255, 215, 0, 120))
            arcade.draw_circle_outline(px, py, 12, TEXT_GOLD, 2)

    # -----------------------------------------------------------------------
    # on_draw
    # -----------------------------------------------------------------------
    def on_draw(self):
        self.clear()

        if self.bg_list:
            self.bg_list.draw()

        draw_board(self.board)
        self._draw_ports()

        if self.build_choice == BUILD_SETTLEMENT:
            self._draw_node_highlights()
        elif self.build_choice == BUILD_CITY:
            self._draw_city_highlights()
        elif self.build_choice == BUILD_ROAD:
            self._draw_edge_highlights()

        self._draw_placed_pieces()

        if self._robber_sprite_ok and self._robber_list:
            self._robber_list.draw()

        self._draw_port_hover_highlights()

        if self.show_confirm:
            self._draw_confirm_popup()

        self._draw_player_panel()
        self._draw_dice_area()
        self._draw_bottom_bar()
        self._draw_build_submenu()

    # -----------------------------------------------------------------------
    # Mouse motion
    # -----------------------------------------------------------------------
    def on_mouse_motion(self, x, y, dx, dy):
        if self.show_confirm:
            return
        if self.build_choice == BUILD_SETTLEMENT:
            closest, closest_dist = None, float("inf")
            for node_id, (npx, npy) in self._node_pixel_cache.items():
                d = math.hypot(x - npx, y - npy)
                if d < NODE_SNAP_RADIUS and d < closest_dist:
                    node = self.board.nodes[node_id]
                    if node.player is None:
                        closest, closest_dist = node, d
            self.hovered_node = closest
        elif self.build_choice == BUILD_CITY:
            closest, closest_dist = None, float("inf")
            for node_id, (npx, npy) in self._node_pixel_cache.items():
                d = math.hypot(x - npx, y - npy)
                if d < NODE_SNAP_RADIUS and d < closest_dist:
                    node = self.board.nodes[node_id]
                    if node.player == self.current_player:
                        closest, closest_dist = node, d
            self.hovered_node = closest
        elif self.build_choice == BUILD_ROAD:
            closest, closest_dist = None, float("inf")
            for edge_id, (mx, my, *_) in self._edge_pixel_cache.items():
                d = math.hypot(x - mx, y - my)
                if d < EDGE_SNAP_RADIUS and d < closest_dist:
                    edge = self.board.edges[edge_id]
                    if edge.player is None:
                        closest, closest_dist = edge, d
            self.hovered_edge = closest

        self._hovered_port_nodes = []
        if self.port_manager:
            port_nodes = self.port_manager.get_hover_nodes(x, y)
            if port_nodes:
                self._hovered_port_nodes = [
                    self._node_pixel_cache[nid]
                    for nid in port_nodes
                    if nid in self._node_pixel_cache
                ]

    # -----------------------------------------------------------------------
    # Mouse press
    # -----------------------------------------------------------------------
    def on_mouse_press(self, x, y, button, modifiers):
        _BW  = 120
        _BH  = 38
        _GAP = 8
        _PAD = 14
        _EW  = 130

        trade_bottom = _PAD
        build_bottom = trade_bottom + _BH + _GAP
        card_bottom  = build_bottom + _BH + _GAP

        # End Turn
        end_left = SCREEN_WIDTH - _PAD - _EW
        if (end_left <= x <= end_left + _EW) and (_PAD <= y <= _PAD + _BH):
            self._end_turn()
            return

        # Build button
        if (_PAD <= x <= _PAD + _BW) and (build_bottom <= y <= build_bottom + _BH):
            if self.build_mode:
                self._cancel_build()
            else:
                self.build_mode   = True
                self.build_choice = BUILD_NONE
            return

        # Build submenu
        if self.build_mode and self.build_choice == BUILD_NONE:
            build_top = build_bottom + _BH
            by        = build_top + 4
            bx        = _PAD
            menu_w    = _BW
            if (bx + 8 <= x <= bx + menu_w - 8) and (by + 80 <= y <= by + 108):
                if self._can_afford(CITY_COST):
                    self.build_choice = BUILD_CITY
                return
            if (bx + 8 <= x <= bx + menu_w - 8) and (by + 44 <= y <= by + 72):
                if self._can_afford(SETTLEMENT_COST):
                    self.build_choice = BUILD_SETTLEMENT
                return
            if (bx + 8 <= x <= bx + menu_w - 8) and (by + 8 <= y <= by + 36):
                if self._free_roads > 0 or self._can_afford(ROAD_COST):
                    self.build_choice = BUILD_ROAD
                return

        # Confirmation popup
        if self.show_confirm:
            if self.build_choice == BUILD_SETTLEMENT and self.selected_node:
                pcx, pcy = self._node_pixel_cache[self.selected_node.node_id]
                pcy     += 18
            elif self.build_choice == BUILD_CITY and self.selected_node:
                pcx, pcy = self._node_pixel_cache[self.selected_node.node_id]
                pcy     += 18
            elif self.build_choice == BUILD_ROAD and self.selected_edge:
                mx, my, *_ = self._edge_pixel_cache[self.selected_edge.edge_id]
                pcx, pcy   = mx, my + 18
            else:
                self.show_confirm = False
                return

            popup_w  = 160
            pop_left = pcx - popup_w / 2

            if (pop_left + 8 <= x <= pop_left + 74) and (pcy + 8 <= y <= pcy + 38):
                if self.build_choice == BUILD_SETTLEMENT and self._can_afford(SETTLEMENT_COST):
                    self._place_settlement(self.selected_node)
                elif self.build_choice == BUILD_CITY and self._can_afford(CITY_COST):
                    self._place_city(self.selected_node)
                elif self.build_choice == BUILD_ROAD:
                    if self._free_roads > 0:
                        self._place_road_free(self.selected_edge)
                    elif self._can_afford(ROAD_COST):
                        self._place_road(self.selected_edge)
                return
            if (pop_left + popup_w - 74 <= x <= pop_left + popup_w - 8) and (pcy + 8 <= y <= pcy + 38):
                self.selected_node = None
                self.selected_edge = None
                self.show_confirm  = False
                return
            self.selected_node = None
            self.selected_edge = None
            self.show_confirm  = False
            return

        if self.build_choice == BUILD_SETTLEMENT and self.hovered_node:
            self.selected_node = self.hovered_node
            self.show_confirm  = True
            return
        if self.build_choice == BUILD_CITY and self.hovered_node:
            self.selected_node = self.hovered_node
            self.show_confirm  = True
            return
        if self.build_choice == BUILD_ROAD and self.hovered_edge:
            self.selected_edge = self.hovered_edge
            self.show_confirm  = True
            return

        # Trade button
        if (_PAD <= x <= _PAD + _BW) and (trade_bottom <= y <= trade_bottom + _BH):
            self.window.show_view(
                TradeView(self.board, self.players, self.current_player, self.die1, self.die2)
            )
            return

        # Dev Cards button
        if (_PAD <= x <= _PAD + _BW) and (card_bottom <= y <= card_bottom + _BH):
            self.window.show_view(
                PlayCardView(
                    self.board, self.players, self.current_player,
                    self.die1, self.die2,
                    shared_deck=self._shared_deck,
                    bought_this_turn=self._bought_card_this_turn,
                    played_card_this_turn=self._played_card_this_turn,
                    free_roads=self._free_roads,
                )
            )
            return

    # -----------------------------------------------------------------------
    # Placement
    # -----------------------------------------------------------------------
    def _place_settlement(self, node):
        player = self.players[self.current_player]
        player.build_settlement(CatanBoard, node)
        node.player   = self.current_player
        node.building = "settlement"
        player.victory_points += 1
        self._cancel_build()
        self._build_player_texts()
        print(f"{player.name} built a settlement! VP: {player.victory_points}")

    def _place_city(self, node):
        player = self.players[self.current_player]
        player.build_city(CatanBoard, node)
        node.building = "city"
        player.victory_points += 1
        self._cancel_build()
        self._build_player_texts()
        print(f"{player.name} upgraded to a city! VP: {player.victory_points}")

    def _place_road(self, edge):
        player    = self.players[self.current_player]
        idx       = self.current_player
        connected = False
        for node in edge.nodes:
            if node.player == idx:
                connected = True
                break
            for neighbor_edge in node.edges:
                if neighbor_edge is not edge and neighbor_edge.player == idx:
                    connected = True
                    break
            if connected:
                break
        if not connected:
            print(f"{player.name} — road must connect to your settlement or existing road.")
            self.show_confirm  = False
            self.selected_edge = None
            return
        player.build_road(CatanBoard, edge)
        edge.player = self.current_player
        self._cancel_build()
        self._build_player_texts()
        print(f"{player.name} built a road!")

    def _place_road_free(self, edge):
        """Place a road using a free-road grant from Road Building card."""
        edge.player       = self.current_player
        self._free_roads -= 1
        self.players[self.current_player].total_roads -= 1
        self._cancel_build()
        self._build_player_texts()
        print(f"{self.players[self.current_player].name} placed a free road! ({self._free_roads} remaining)")

    def _cancel_build(self):
        self.build_mode    = False
        self.build_choice  = BUILD_NONE
        self.hovered_node  = None
        self.hovered_edge  = None
        self.selected_node = None
        self.selected_edge = None
        self.show_confirm  = False

    # -----------------------------------------------------------------------
    # Resource distribution
    # -----------------------------------------------------------------------
    def _give_resources(self):
        roll = self.die1 + self.die2
        for tile in self.board.tiles.values():
            if tile.number == roll:
                resource = RESOURCE_ABBR[tile.resource]
                for node in tile.nodes:
                    if node.player is not None:
                        player = self.players[node.player]
                        player.resource_cards[resource] += (
                            1 if node.building == "settlement" else 2
                        )

    # -----------------------------------------------------------------------
    # End turn
    # -----------------------------------------------------------------------
    def _end_turn(self):
        if self.players[self.current_player].victory_points >= 10:
            self.window.show_view(EndView(self.players, self.current_player))
            return

        # Clear "just_bought" flag on all cards so they can be played next turn
        for card in self.players[self.current_player].development_cards:
            card["just_bought"] = False

        self.current_player = (self.current_player + 1) % len(self.players)
        self._cancel_build()

        # Reset per-turn dev-card flags for the new player
        self._bought_card_this_turn  = False
        self._played_card_this_turn  = False
        # NOTE: free_roads intentionally carries over if a Road Building card was
        # played and not fully used (edge case — keep count until exhausted)
        if self._free_roads < 0:
            self._free_roads = 0

        # Roll dice and start animation
        self.die1 = random.randint(ONE, SIX)
        self.die2 = random.randint(ONE, SIX)
        self._start_dice_animation()

        # TODO (Apoorva): check if roll == 7 and trigger robber phase

        self._give_resources()
        self._build_player_texts()
        self._build_dice_texts()

        print(f"Turn ended. Now it's {self.players[self.current_player].name}'s turn. Rolled {self.die1 + self.die2}.")