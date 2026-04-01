"""
Contains CatanView Class
    Parameters:
        All mighty viewing file


    Need to change Build and Trade button boolean to be false while other button is true to avoid
    having both menus open at the same time
"""

import random
import math
import arcade
from .port_manager import PortManager
from backend import node
from backend.catan_board import CatanBoard
from .board_utils import cubic_to_pixel, node_to_pixel, get_hex_corners
from .drawing import (fill_rect, outline_rect, draw_settlement, draw_road,
                      draw_board, draw_city, draw_ocean_background)
from .constants import *
from .view_constants import *  # noqa: F401,F403
from .computer_turn_view import ComputerTurnView

CARD_SCALE = 0.25
ARMY_ROAD_SPRITE_X = SCREEN_WIDTH - 70
ARMY_ROAD_SPRITE_Y1 = SCREEN_HEIGHT / 2 + 150
ARMY_ROAD_SPRITE_Y2 = SCREEN_HEIGHT / 2

ROADS_NEEDED = 5
LONGEST_ROAD_VP = 2

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
        vm,
        board,
        players,
        current_player,
        die1,
        die2,
        port_manager,
        shared_deck=None,
        bought_card_this_turn=False,
        played_card_this_turn=False,
        free_roads=0,
        start_of_turn=False,
    ):
        super().__init__()
        self.vm             = vm
        self.board          = board
        self.players        = players
        self.current_player = current_player
        self.port_manager = port_manager
        self.die1 = die1
        self.die2 = die2

        #Dev-card session state (preserved across CatanView <-> PlayCardView round-trips)
        self._shared_deck           = shared_deck   #None = PlayCardView will build it on first open
        self._bought_card_this_turn = bought_card_this_turn
        self._played_card_this_turn = played_card_this_turn
        self._free_roads            = free_roads    # free road placements remaining

        # Build mode state
        self.build_mode    = False
        self.build_choice  = BUILD_NONE
        self.trade_mode = False
        self.trade_choice = None
        self.hovered_node  = None
        self.hovered_edge  = None
        self.selected_node = None
        self.selected_edge = None
        self.show_confirm  = False

        # --- Dice animation state ---
        self._dice_animating  = False
        self._dice_anim_timer = 0.0
        self._dice_flip_timer = 0.0
        if start_of_turn:
            self._dice_animating  = True
            self._dice_anim_timer = DICE_ROLL_DURATION
            self._dice_flip_timer = DICE_ROLL_FLIP_RATE
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

        # --- Ocean animation ---
        self._ocean_time = 0.0

        # Pixel caches
        self._node_pixel_cache = {}
        self._edge_pixel_cache = {}
        self._tile_pixel_cache = {}

        self._load_background()
        self._build_text_objects()
        self._load_resource_icons()
        self._load_card_sprites()
        self._assign_number_tokens()
        self._build_node_pixel_cache()
        self._build_edge_pixel_cache()
        self._build_tile_pixel_cache()

        if self.port_manager == None:
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

    # -----------------------------------------------------------------------
    # Longest Road and Largest Army sprite
    # -----------------------------------------------------------------------
    def _load_card_sprites(self):
        self._road_card_sprite = arcade.Sprite(ROAD_CARD_SPRITE, scale=CARD_SCALE,
                                               center_y=ARMY_ROAD_SPRITE_Y1,
                                               center_x=ARMY_ROAD_SPRITE_X)
        self._army_card_sprite = arcade.Sprite(ARMY_CARD_SPRITE, scale=CARD_SCALE,
                                               center_y=ARMY_ROAD_SPRITE_Y2,
                                               center_x=ARMY_ROAD_SPRITE_X)
        self._card_list   = arcade.SpriteList()

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
        self._place_robber_on_tile()

    def _place_robber_on_desert(self):
        for xyz, tile in self.board.tiles.items():
            if tile.resource == "desert":
                tile.robber = True
                print("setting desert robber to true")
                self._place_robber_on_tile()
                break

    def _place_robber_on_tile(self):
        for xyz, tile in self.board.tiles.items():
            if tile.robber:
                self._robber_tile = tile
                if self._robber_sprite_ok and self._robber_sprite:
                    cx, _, cz = xyz
                    px, py = cubic_to_pixel(cx, cz, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
                    target_h  = HEX_SIZE * CATAN_ROBBER_SCALE_MULT
                    texture_height = self._robber_sprite.texture.height
                    scale = target_h / texture_height
                    self._robber_sprite.scale = scale
                    self._robber_sprite.center_x = px
                    self._robber_sprite.center_y = py
                break

    # -----------------------------------------------------------------------
    # Background
    # -----------------------------------------------------------------------
    def _load_background(self):
        self.bg_sprite = None
        self.bg_list = None

        if USE_OCEAN_BACKGROUND:
            arcade.set_background_color(OCEAN_BASE_COLOR)
            return

        try:
            self.bg_sprite = arcade.Sprite(BACKGROUND_IMAGE)
            self.bg_sprite.center_x = SCREEN_WIDTH / 2
            self.bg_sprite.center_y = SCREEN_HEIGHT / 2
            scale_x = SCREEN_WIDTH / self.bg_sprite.width
            scale_y = SCREEN_HEIGHT / self.bg_sprite.height
            self.bg_sprite.scale = max(scale_x, scale_y)
            self.bg_list = arcade.SpriteList()
            self.bg_list.append(self.bg_sprite)
        except Exception:
            self.bg_sprite = None
            self.bg_list = None
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

    def _build_tile_pixel_cache(self):
        for xyz, tile in self.board.tiles.items():
            cx, _, cz = xyz
            px, py = cubic_to_pixel(cx, cz, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
            self._tile_pixel_cache[tile.tile_id] = (px, py)

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
        trade_bottom = CATAN_BTN_PAD
        build_bottom = trade_bottom + CATAN_BTN_H + CATAN_BTN_GAP
        card_bottom  = build_bottom + CATAN_BTN_H + CATAN_BTN_GAP

        self.txt_trade = arcade.Text(
            CATAN_LABEL_TRADE, CATAN_BTN_PAD + CATAN_BTN_W / 2, trade_bottom + CATAN_BTN_H / 2,
            TEXT_WHITE, CATAN_TEXT_SIZE_BTN, bold=True, anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_build = arcade.Text(
            CATAN_LABEL_BUILD, CATAN_BTN_PAD + CATAN_BTN_W / 2, build_bottom + CATAN_BTN_H / 2,
            TEXT_WHITE, CATAN_TEXT_SIZE_BTN, bold=True, anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_card = arcade.Text(
            CATAN_LABEL_DEV_CARDS, CATAN_BTN_PAD + CATAN_BTN_W / 2, card_bottom + CATAN_BTN_H / 2,
            TEXT_WHITE, CATAN_TEXT_SIZE_CARD_BTN, bold=True, anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

        self.txt_end = arcade.Text(
            CATAN_LABEL_END_TURN,
            SCREEN_WIDTH - CATAN_BTN_PAD - CATAN_END_BTN_W / 2,
            CATAN_BTN_PAD + CATAN_BTN_H / 2,
            TEXT_WHITE, CATAN_TEXT_SIZE_BTN, bold=True, anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - CATAN_DICE_BOX_MARGIN
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - CATAN_DICE_BOX_MARGIN
        self.txt_dice_label = arcade.Text(
            CATAN_LABEL_DICE_ROLL, dx + DICE_AREA_WIDTH / 2,
            dy + DICE_AREA_HEIGHT - CATAN_DICE_LABEL_TOP_PAD,
            TEXT_GOLD, CATAN_TEXT_SIZE_DICE_LABEL, bold=True, anchor_x="center",
            font_name="MedievalSharp",
        )
        self.txt_dice_hint = arcade.Text(
            CATAN_LABEL_DICE_HINT,
            dx + DICE_AREA_WIDTH / 2, dy + CATAN_DICE_TOTAL_Y,
            TEXT_LIGHT_GRAY, CATAN_TEXT_SIZE_DICE_HINT, anchor_x="center",
            font_name="MedievalSharp",
        )

        self.txt_submenu_settlement = arcade.Text(
            "", 0, 0, TEXT_WHITE, CATAN_TEXT_SIZE_SUBMENU, bold=True,
            anchor_x="center", anchor_y="center", font_name="MedievalSharp",
        )
        self.txt_submenu_city = arcade.Text(
            "", 0, 0, TEXT_WHITE, CATAN_TEXT_SIZE_SUBMENU, bold=True,
            anchor_x="center", anchor_y="center", font_name="MedievalSharp",
        )
        self.txt_submenu_road = arcade.Text(
            "", 0, 0, TEXT_WHITE, CATAN_TEXT_SIZE_SUBMENU, bold=True,
            anchor_x="center", anchor_y="center", font_name="MedievalSharp",
        )

        self.txt_popup_title = arcade.Text(
            "", 0, 0, TEXT_GOLD, CATAN_TEXT_SIZE_POPUP_TITLE, bold=True,
            anchor_x="center", anchor_y="center", font_name="MedievalSharp",
        )
        self.txt_popup_confirm = arcade.Text(
            "", 0, 0, TEXT_WHITE, CATAN_TEXT_SIZE_POPUP_BTN, bold=True,
            anchor_x="center", anchor_y="center", font_name="MedievalSharp",
        )
        self.txt_popup_cancel = arcade.Text(
            CATAN_LABEL_CANCEL, 0, 0, TEXT_WHITE, CATAN_TEXT_SIZE_POPUP_BTN, bold=True,
            anchor_x="center", anchor_y="center", font_name="MedievalSharp",
        )

        self._build_player_texts()
        self._build_dice_texts()

    def _build_dice_texts(self):
        """Pre-build the fallback number Text objects for the dice area."""
        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - CATAN_DICE_BOX_MARGIN
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - CATAN_DICE_BOX_MARGIN
        die1_x = dx + (DICE_AREA_WIDTH - 2 * CATAN_DIE_SIZE - CATAN_DIE_GAP) / 2
        die_y  = dy + CATAN_DICE_Y_OFFSET

        self.txt_die1 = arcade.Text(
            f"{self.die1}",
            die1_x + CATAN_DIE_SIZE / 2, die_y + CATAN_DIE_SIZE / 2,
            TEXT_WHITE, CATAN_TEXT_SIZE_DICE_NUM, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_die2 = arcade.Text(
            f"{self.die2}",
            die1_x + CATAN_DIE_SIZE + CATAN_DIE_GAP + CATAN_DIE_SIZE / 2,
            die_y + CATAN_DIE_SIZE / 2,
            TEXT_WHITE, CATAN_TEXT_SIZE_DICE_NUM, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

        # Build submenu labels (positions updated at draw time)
        self.txt_submenu_settlement = arcade.Text(
            "", 0, 0, TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_submenu_road = arcade.Text(
            "", 0, 0, TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

        # Trade submenu labels (positions updated at draw time)
        self.txt_submenu_maritime = arcade.Text(
            "Maritime Trade", 0, 0, TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_submenu_barter = arcade.Text(
            "Barter Trade", 0, 0, TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

        # Confirm popup labels
        self.txt_popup_title = arcade.Text(
            "", 0, 0, TEXT_GOLD, 10, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_popup_confirm = arcade.Text(
            "", 0, 0, TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_popup_cancel = arcade.Text(
            "Cancel", 0, 0, TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

        self._build_player_texts()

    def _build_player_texts(self):
        player    = self.players[self.current_player]
        panel_x   = CATAN_PLAYER_PANEL_MARGIN
        panel_top = SCREEN_HEIGHT - CATAN_PLAYER_PANEL_MARGIN

        self.txt_player_name = arcade.Text(
            player.name,
            panel_x + HUD_PANEL_WIDTH // 2, panel_top - CATAN_PLAYER_NAME_Y,
            TEXT_GOLD, CATAN_TEXT_SIZE_PLAYER_NAME, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_player_vp = arcade.Text(
            f"Victory Points: {player.victory_points}",
            panel_x + HUD_PANEL_WIDTH // 2 + 10,
            panel_top - CATAN_PLAYER_NAME_Y - CATAN_PLAYER_ROW_H,
            TEXT_LIGHT_GRAY, CATAN_TEXT_SIZE_PLAYER_VP,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

        order  = ["BRICK", "ORE", "WHEAT", "SHEEP", "WOOD"]
        labels = {"BRICK": "Brick", "ORE": "Ore", "WHEAT": "Wheat",
                  "SHEEP": "Sheep", "WOOD": "Wood"}

        self.txt_resources = []
        for i, res in enumerate(order):
            ry = (panel_top - CATAN_PLAYER_NAME_Y - CATAN_PLAYER_ROW_H * 2
                  - i * (ICON_SIZE + CATAN_RESOURCE_ROW_GAP) - ICON_SIZE // 2)
            self.txt_resources.append(
                arcade.Text(
                    f"{labels[res]}: {player.resource_cards.get(res)}",
                    panel_x + ICON_SIZE + CATAN_RESOURCE_TEXT_X_OFFSET, ry,
                    TEXT_WHITE, CATAN_TEXT_SIZE_RESOURCE,
                    anchor_y="center",
                    font_name="MedievalSharp",
                )
            )

        n_cards = len(player.development_cards)
        self.txt_dev_card_count = arcade.Text(
            f"Dev Cards: {n_cards}",
            panel_x + HUD_PANEL_WIDTH // 2,
            (panel_top - CATAN_PLAYER_NAME_Y - CATAN_PLAYER_ROW_H * 2
             - (ICON_SIZE + CATAN_RESOURCE_ROW_GAP) * 5 - CATAN_DEV_CARD_COUNT_Y_OFFSET),
            CATAN_DEV_CARD_COUNT_COLOR, CATAN_TEXT_SIZE_RESOURCE,
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
    def on_update(self, delta_time):
        # Ocean animation should always advance, even when dice are idle
        self._ocean_time += delta_time

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
        trade_bottom = CATAN_BTN_PAD
        build_bottom = trade_bottom + CATAN_BTN_H + CATAN_BTN_GAP
        card_bottom  = build_bottom + CATAN_BTN_H + CATAN_BTN_GAP

        build_col = BTN_BUILD_ACTIVE if self.build_mode else BTN_BUILD

        for bottom, color in [
            (trade_bottom, BTN_TRADE),
            (build_bottom, build_col),
            (card_bottom,  BTN_CARD),
        ]:
            fill_rect(CATAN_BTN_PAD + 2, bottom - 2, CATAN_BTN_W, CATAN_BTN_H,
                      CATAN_COLOR_DROP_SHADOW)
            fill_rect(CATAN_BTN_PAD, bottom, CATAN_BTN_W, CATAN_BTN_H, color)
            outline_rect(CATAN_BTN_PAD, bottom, CATAN_BTN_W, CATAN_BTN_H,
                         CATAN_COLOR_BTN_OUTLINE, 1)

        # Free-roads indicator on the "Dev Cards" button
        if self._free_roads > 0:
            arcade.Text(
                f"Free roads: {self._free_roads}",
                CATAN_BTN_PAD + CATAN_BTN_W / 2, card_bottom + CATAN_BTN_H + 6,
                CATAN_COLOR_FREE_ROADS, CATAN_TEXT_SIZE_FREE_ROADS, bold=True,
                anchor_x="center", anchor_y="bottom",
                font_name="MedievalSharp",
            ).draw()

        fill_rect(SCREEN_WIDTH - CATAN_BTN_PAD - CATAN_END_BTN_W + 2,
                  CATAN_BTN_PAD - 2, CATAN_END_BTN_W, CATAN_BTN_H,
                  CATAN_COLOR_DROP_SHADOW)
        fill_rect(SCREEN_WIDTH - CATAN_BTN_PAD - CATAN_END_BTN_W,
                  CATAN_BTN_PAD, CATAN_END_BTN_W, CATAN_BTN_H, BTN_ENDTURN)
        outline_rect(SCREEN_WIDTH - CATAN_BTN_PAD - CATAN_END_BTN_W,
                     CATAN_BTN_PAD, CATAN_END_BTN_W, CATAN_BTN_H,
                     CATAN_COLOR_BTN_OUTLINE, 1)

        self.txt_trade.draw()
        self.txt_build.draw()
        self.txt_card.draw()
        self.txt_end.draw()

    def _draw_build_submenu(self):
        if not self.build_mode or self.build_choice != BUILD_NONE:
            return

        build_bottom = CATAN_BTN_PAD + CATAN_BTN_H + CATAN_BTN_GAP
        build_top    = build_bottom + CATAN_BTN_H
        bx           = CATAN_BTN_PAD
        by           = build_top + CATAN_BUILD_SUBMENU_Y_OFFSET

        fill_rect(bx, by, CATAN_BUILD_SUBMENU_W, CATAN_BUILD_SUBMENU_H, HUD_PANEL_BG)
        outline_rect(bx, by, CATAN_BUILD_SUBMENU_W, CATAN_BUILD_SUBMENU_H, TEXT_GOLD, 2)

        c_col = CATAN_COLOR_CITY_BTN if self._can_afford(CITY_COST) else CATAN_COLOR_DISABLED
        fill_rect(bx + CATAN_BUILD_SUBMENU_BTN_INSET,
                  by + (CATAN_BUILD_SUBMENU_BTN_INSET + 2 * CATAN_BUILD_SUBMENU_ROW_STEP),
                  CATAN_BUILD_SUBMENU_W - CATAN_BUILD_SUBMENU_BTN_INSET * 2,
                  CATAN_BUILD_SUBMENU_BTN_H, c_col)
        self.txt_submenu_city.text = CATAN_LABEL_CITY
        self.txt_submenu_city.x    = bx + CATAN_BUILD_SUBMENU_W / 2
        self.txt_submenu_city.y    = by + (CATAN_BUILD_SUBMENU_BTN_INSET + 14
                                           + 2 * CATAN_BUILD_SUBMENU_ROW_STEP)
        self.txt_submenu_city.draw()

        s_col = (CATAN_COLOR_SETTLEMENT_BTN if self._can_afford(SETTLEMENT_COST)
                 else CATAN_COLOR_DISABLED)
        fill_rect(bx + CATAN_BUILD_SUBMENU_BTN_INSET,
                  by + (CATAN_BUILD_SUBMENU_BTN_INSET + CATAN_BUILD_SUBMENU_ROW_STEP),
                  CATAN_BUILD_SUBMENU_W - CATAN_BUILD_SUBMENU_BTN_INSET * 2,
                  CATAN_BUILD_SUBMENU_BTN_H, s_col)
        self.txt_submenu_settlement.text = CATAN_LABEL_SETTLEMENT
        self.txt_submenu_settlement.x    = bx + CATAN_BUILD_SUBMENU_W / 2
        self.txt_submenu_settlement.y    = by + (CATAN_BUILD_SUBMENU_BTN_INSET + 14
                                                 + CATAN_BUILD_SUBMENU_ROW_STEP)
        self.txt_submenu_settlement.draw()

        r_col = CATAN_COLOR_ROAD_BTN if self._can_afford(ROAD_COST) else CATAN_COLOR_DISABLED
        fill_rect(bx + CATAN_BUILD_SUBMENU_BTN_INSET,
                  by + CATAN_BUILD_SUBMENU_BTN_INSET,
                  CATAN_BUILD_SUBMENU_W - CATAN_BUILD_SUBMENU_BTN_INSET * 2,
                  CATAN_BUILD_SUBMENU_BTN_H, r_col)
        self.txt_submenu_road.text = CATAN_LABEL_ROAD
        self.txt_submenu_road.x    = bx + CATAN_BUILD_SUBMENU_W / 2
        self.txt_submenu_road.y    = by + CATAN_BUILD_SUBMENU_BTN_INSET + 14
        self.txt_submenu_road.draw()

    def _draw_trade_submenu(self):
        if not self.trade_mode or self.trade_choice != TRADE_NONE:
            return

        _BW  = 120
        _BH  = 38
        _PAD = 14

        trade_bottom = _PAD               # bottom of the Trade button
        trade_top    = trade_bottom + _BH # top of the Trade button

        menu_w = _BW
        menu_h = 80
        bx     = _PAD
        by     = trade_top + 4            # pop up just above Trade button

        fill_rect(bx, by, menu_w, menu_h, HUD_PANEL_BG)
        outline_rect(bx, by, menu_w, menu_h, TEXT_GOLD, 2)

        # Maritime Trade — top row
        fill_rect(bx + 8, by + 44, menu_w - 16, 28, (52, 152, 219))
        self.txt_submenu_maritime.x = bx + menu_w / 2
        self.txt_submenu_maritime.y = by + 58
        self.txt_submenu_maritime.draw()

        # Barter Trade — bottom row
        fill_rect(bx + 8, by + 8, menu_w - 16, 28, (39, 174, 96))
        self.txt_submenu_barter.x = bx + menu_w / 2
        self.txt_submenu_barter.y = by + 22
        self.txt_submenu_barter.draw()

    def _draw_player_panel(self):
        player  = self.players[self.current_player]
        panel_x = CATAN_PLAYER_PANEL_MARGIN
        panel_y = SCREEN_HEIGHT - HUD_PANEL_HEIGHT - CATAN_PLAYER_PANEL_MARGIN

        fill_rect(panel_x, panel_y, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, HUD_PANEL_BG)
        outline_rect(panel_x, panel_y, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, player.color)

        arcade.draw_circle_filled(
            panel_x + CATAN_PLAYER_MARKER_RADIUS * 2,
            panel_y + HUD_PANEL_HEIGHT - CATAN_PLAYER_NAME_Y,
            CATAN_PLAYER_MARKER_RADIUS, player.color
        )

        self.txt_player_name.draw()
        self.txt_player_vp.draw()

        order     = ["brick", "ore", "wheat", "sheep", "forest"]
        panel_top = SCREEN_HEIGHT - CATAN_PLAYER_PANEL_MARGIN

        for i, res in enumerate(order):
            ry = (panel_top - CATAN_PLAYER_NAME_Y - CATAN_PLAYER_ROW_H * 2
                  - i * (ICON_SIZE + CATAN_RESOURCE_ICON_ROW_GAP))
            sprite          = self.resource_icons[res]
            sprite.center_x = panel_x + ICON_SIZE // 2 + CATAN_RESOURCE_ICON_X_OFFSET
            sprite.center_y = ry - CATAN_RESOURCE_ICON_Y_OFFSET

        self.icon_sprite_list.draw()
        for txt in self.txt_resources:
            txt.draw()
        self.txt_dev_card_count.draw()

    def _draw_dice_area(self):
        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - CATAN_DICE_BOX_MARGIN
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - CATAN_DICE_BOX_MARGIN

        fill_rect(dx, dy, DICE_AREA_WIDTH, DICE_AREA_HEIGHT, HUD_PANEL_BG)
        outline_rect(dx, dy, DICE_AREA_WIDTH, DICE_AREA_HEIGHT, TEXT_LIGHT_GRAY)

        self.txt_dice_label.draw()

        die1_x = dx + (DICE_AREA_WIDTH - 2 * CATAN_DIE_SIZE - CATAN_DIE_GAP) / 2
        die_y  = dy + CATAN_DICE_Y_OFFSET

        face1 = self._anim_die1 if self._dice_animating else self.die1
        face2 = self._anim_die2 if self._dice_animating else self.die2

        if USE_DICE_SPRITES and self._dice_sprites.get(face1) and self._dice_sprites.get(face2):
            spr1 = self._dice_sprites[face1]
            spr2 = self._dice_sprites[face2]

            spr1.scale    = CATAN_DIE_SIZE / max(spr1.width, spr1.height)
            spr1.center_x = die1_x + CATAN_DIE_SIZE / 2
            spr1.center_y = die_y  + CATAN_DIE_SIZE / 2

            spr2.scale    = CATAN_DIE_SIZE / max(spr2.width, spr2.height)
            spr2.center_x = die1_x + CATAN_DIE_SIZE + CATAN_DIE_GAP + CATAN_DIE_SIZE / 2
            spr2.center_y = die_y  + CATAN_DIE_SIZE / 2

            fill_rect(die1_x,                              die_y,
                      CATAN_DIE_SIZE, CATAN_DIE_SIZE, CATAN_COLOR_DIE_BG)
            fill_rect(die1_x + CATAN_DIE_SIZE + CATAN_DIE_GAP, die_y,
                      CATAN_DIE_SIZE, CATAN_DIE_SIZE, CATAN_COLOR_DIE_BG)

            _tmp = arcade.SpriteList()
            _tmp.append(spr1)
            _tmp.append(spr2)
            _tmp.draw()

            if self._dice_animating:
                alpha = int(180 * (self._dice_anim_timer / DICE_ROLL_DURATION))
                outline_rect(die1_x, die_y,
                             CATAN_DIE_SIZE, CATAN_DIE_SIZE,
                             (*CATAN_COLOR_SHAKE_OUTLINE, alpha), 2)
                outline_rect(die1_x + CATAN_DIE_SIZE + CATAN_DIE_GAP, die_y,
                             CATAN_DIE_SIZE, CATAN_DIE_SIZE,
                             (*CATAN_COLOR_SHAKE_OUTLINE, alpha), 2)
        else:
            fill_rect(die1_x, die_y,
                      CATAN_DIE_SIZE, CATAN_DIE_SIZE, CATAN_COLOR_DIE_FALLBACK)
            fill_rect(die1_x + CATAN_DIE_SIZE + CATAN_DIE_GAP, die_y,
                      CATAN_DIE_SIZE, CATAN_DIE_SIZE, CATAN_COLOR_DIE_FALLBACK)

            arcade.Text(
                str(face1),
                die1_x + CATAN_DIE_SIZE / 2, die_y + CATAN_DIE_SIZE / 2,
                TEXT_WHITE, CATAN_TEXT_SIZE_DICE_NUM, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ).draw()
            arcade.Text(
                str(face2),
                die1_x + CATAN_DIE_SIZE + CATAN_DIE_GAP + CATAN_DIE_SIZE / 2,
                die_y + CATAN_DIE_SIZE / 2,
                TEXT_WHITE, CATAN_TEXT_SIZE_DICE_NUM, bold=True,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ).draw()

        if not self._dice_animating:
            arcade.Text(
                f"Total: {self.die1 + self.die2}",
                dx + DICE_AREA_WIDTH / 2, dy + CATAN_DICE_TOTAL_Y,
                TEXT_LIGHT_GRAY, CATAN_TEXT_SIZE_TOTAL, anchor_x="center",
                font_name="MedievalSharp",
            ).draw()

    # -----------------------------------------------------------------------
    # Largest Army and Longest Road drawing
    # -----------------------------------------------------------------------
    def _draw_cards(self):
        player = self.players[self.current_player]
        if self._army_card_sprite not in self._card_list and player.largest_army:
            self._army_card_sprite.center_y = ARMY_ROAD_SPRITE_Y1 if not player.longest_road else ARMY_ROAD_SPRITE_Y2
            self._card_list.append(self._army_card_sprite)
        if self._road_card_sprite not in self._card_list and player.longest_road:
            self._card_list.append(self._road_card_sprite)
        self._card_list.draw()

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
                    draw_settlement(npx, npy, CATAN_SETTLEMENT_DRAW_SIZE,
                                    self.players[node_obj.player].color)
                if node_obj.building == "city":
                    draw_city(npx, npy, CATAN_CITY_DRAW_SIZE,
                              self.players[node_obj.player].color)

    # -----------------------------------------------------------------------
    # Ghost highlights
    # -----------------------------------------------------------------------
    def _draw_node_highlights(self):
        player_color = self.players[self.current_player].color
        for node_id, node_obj in self.board.nodes.items():
            if not node_obj.is_valid_settlement_placement(self.current_player):
                continue
            npx, npy = self._node_pixel_cache[node_id]
            if npy < CATAN_BOARD_TOP_CULL_Y:
                continue
            if (npx < HUD_PANEL_WIDTH + CATAN_HUD_LEFT_BLOCK_PAD
                    or npx > SCREEN_WIDTH - DICE_AREA_WIDTH - CATAN_DICE_RIGHT_BLOCK_PAD):
                continue
            if node_obj is self.hovered_node:
                arcade.draw_circle_filled(npx, npy, CATAN_HIGHLIGHT_RADIUS_HOVER,
                                          (*player_color, 180))
                arcade.draw_circle_outline(npx, npy, CATAN_HIGHLIGHT_RADIUS_OUTLINE,
                                           player_color, 3)
            else:
                arcade.draw_circle_filled(npx, npy, CATAN_HIGHLIGHT_RADIUS_IDLE,
                                          CATAN_COLOR_GHOST_FILL)
                arcade.draw_circle_outline(npx, npy, CATAN_HIGHLIGHT_RADIUS_IDLE,
                                           CATAN_COLOR_GHOST_OUTLINE, 1)

    def _draw_city_highlights(self):
        player_color = self.players[self.current_player].color
        for node_id, node_obj in self.board.nodes.items():
            if not node_obj.is_valid_city_placement(self.current_player):
                continue
            npx, npy = self._node_pixel_cache[node_id]
            if npy < CATAN_BOARD_TOP_CULL_Y:
                continue
            if (npx < HUD_PANEL_WIDTH + CATAN_HUD_LEFT_BLOCK_PAD
                    or npx > SCREEN_WIDTH - DICE_AREA_WIDTH - CATAN_DICE_RIGHT_BLOCK_PAD):
                continue
            if node_obj is self.hovered_node:
                arcade.draw_circle_filled(npx, npy, CATAN_HIGHLIGHT_RADIUS_HOVER,
                                          (*player_color, 180))
                arcade.draw_circle_outline(npx, npy, CATAN_HIGHLIGHT_RADIUS_OUTLINE,
                                           player_color, 3)
            else:
                arcade.draw_circle_filled(npx, npy, CATAN_HIGHLIGHT_RADIUS_IDLE,
                                          CATAN_COLOR_GHOST_FILL)
                arcade.draw_circle_outline(npx, npy, CATAN_HIGHLIGHT_RADIUS_IDLE,
                                           CATAN_COLOR_GHOST_OUTLINE, 1)

    def _draw_edge_highlights(self):
        player_color = self.players[self.current_player].color
        for edge_id, edge_obj in self.board.edges.items():
            if edge_obj.player is not None:
                continue
            mx, my, x1, y1, x2, y2 = self._edge_pixel_cache[edge_id]
            if my < CATAN_BOARD_TOP_CULL_Y:
                continue
            if edge_obj is self.hovered_edge:
                arcade.draw_line(x1, y1, x2, y2, (*player_color, 200),
                                 CATAN_EDGE_HIGHLIGHT_WIDTH)
                arcade.draw_circle_filled(mx, my, CATAN_EDGE_HOVER_DOT_RADIUS,
                                          (*player_color, 220))
            else:
                arcade.draw_line(x1, y1, x2, y2, CATAN_COLOR_GHOST_FILL,
                                 CATAN_EDGE_IDLE_WIDTH)

    # -----------------------------------------------------------------------
    # Confirmation popup
    # -----------------------------------------------------------------------
    def _draw_confirm_popup(self):
        if not self.show_confirm:
            return
        if self.build_choice == BUILD_SETTLEMENT and self.selected_node:
            cx, cy = self._node_pixel_cache[self.selected_node.node_id]
            cy    += CATAN_CONFIRM_Y_OFFSET
            can    = self._can_afford(SETTLEMENT_COST)
            label  = "Build Settlement?"
        elif self.build_choice == BUILD_CITY and self.selected_node:
            cx, cy = self._node_pixel_cache[self.selected_node.node_id]
            cy    += CATAN_CONFIRM_Y_OFFSET
            can    = self._can_afford(CITY_COST)
            label  = "Build City?"
        elif self.build_choice == BUILD_ROAD and self.selected_edge:
            mx, my, *_ = self._edge_pixel_cache[self.selected_edge.edge_id]
            cx, cy = mx, my + CATAN_CONFIRM_Y_OFFSET
            can    = self._free_roads > 0 or self._can_afford(ROAD_COST)
            label  = "Build Road? (FREE)" if self._free_roads > 0 else "Build Road?"
        else:
            return

        pop_left = cx - CATAN_CONFIRM_POPUP_W / 2

        fill_rect(pop_left, cy, CATAN_CONFIRM_POPUP_W, CATAN_CONFIRM_POPUP_H,
                  CATAN_COLOR_POPUP_BG)
        outline_rect(pop_left, cy, CATAN_CONFIRM_POPUP_W, CATAN_CONFIRM_POPUP_H,
                     TEXT_GOLD, 2)
        self.txt_popup_title.text = label
        self.txt_popup_title.x    = cx
        self.txt_popup_title.y    = cy + CATAN_CONFIRM_POPUP_H - CATAN_CONFIRM_TITLE_Y_PAD
        self.txt_popup_title.draw()

        btn_col = CATAN_COLOR_SETTLEMENT_BTN if can else CATAN_COLOR_POPUP_NO_RES
        fill_rect(pop_left + CATAN_CONFIRM_BTN_INSET, cy + CATAN_CONFIRM_BTN_INSET,
                  CATAN_CONFIRM_BTN_W, CATAN_CONFIRM_BTN_H, btn_col)
        self.txt_popup_confirm.text = "Confirm" if can else "No Res."
        self.txt_popup_confirm.x    = pop_left + CATAN_CONFIRM_BTN_INSET + CATAN_CONFIRM_BTN_W / 2
        self.txt_popup_confirm.y    = cy + CATAN_CONFIRM_BTN_CENTER_Y
        self.txt_popup_confirm.draw()

        fill_rect(pop_left + CATAN_CONFIRM_POPUP_W - CATAN_CONFIRM_BTN_INSET - CATAN_CONFIRM_BTN_W,
                  cy + CATAN_CONFIRM_BTN_INSET,
                  CATAN_CONFIRM_BTN_W, CATAN_CONFIRM_BTN_H,
                  CATAN_COLOR_POPUP_CANCEL)
        self.txt_popup_cancel.x = (pop_left + CATAN_CONFIRM_POPUP_W
                                   - CATAN_CONFIRM_BTN_INSET - CATAN_CONFIRM_BTN_W / 2)
        self.txt_popup_cancel.y = cy + CATAN_CONFIRM_BTN_CENTER_Y
        self.txt_popup_cancel.draw()

    # -----------------------------------------------------------------------
    # Port hover highlights
    # -----------------------------------------------------------------------
    def _draw_port_hover_highlights(self):
        if not self._hovered_port_nodes:
            return
        for px, py in self._hovered_port_nodes:
            arcade.draw_circle_filled(px, py, CATAN_PORT_HOVER_OUTER_RADIUS,
                                      CATAN_COLOR_PORT_HOVER_OUTER)
            arcade.draw_circle_filled(px, py, CATAN_PORT_HOVER_INNER_RADIUS,
                                      CATAN_COLOR_PORT_HOVER_INNER)
            arcade.draw_circle_outline(px, py, CATAN_PORT_HOVER_OUTLINE_RADIUS,
                                       TEXT_GOLD, 2)

    # -----------------------------------------------------------------------
    # on_draw

    def on_draw(self):
        self.clear()

        if USE_OCEAN_BACKGROUND:
            draw_ocean_background(self._ocean_time)
        elif self.bg_list:
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
        self._draw_trade_submenu()
        self._draw_cards()

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
                    if (node.player is None and
                        node.is_valid_settlement_placement(self.current_player)):
                        closest, closest_dist = node, d
            self.hovered_node = closest
        elif self.build_choice == BUILD_CITY:
            closest, closest_dist = None, float("inf")
            for node_id, (npx, npy) in self._node_pixel_cache.items():
                d = math.hypot(x - npx, y - npy)
                if d < NODE_SNAP_RADIUS and d < closest_dist:
                    node = self.board.nodes[node_id]
                    if node.is_valid_city_placement(self.current_player):
                        closest, closest_dist = node, d
            self.hovered_node = closest
        elif self.build_choice == BUILD_ROAD:
            closest, closest_dist = None, float("inf")
            for edge_id, (mx, my, *_) in self._edge_pixel_cache.items():
                d = math.hypot(x - mx, y - my)
                if d < EDGE_SNAP_RADIUS and d < closest_dist:
                    edge = self.board.edges[edge_id]
                    if edge.is_valid_road_placement(self.current_player):
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
        trade_bottom = CATAN_BTN_PAD
        build_bottom = trade_bottom + CATAN_BTN_H + CATAN_BTN_GAP
        card_bottom  = build_bottom + CATAN_BTN_H + CATAN_BTN_GAP

        # End Turn
        end_left = SCREEN_WIDTH - CATAN_BTN_PAD - CATAN_END_BTN_W
        if ((end_left <= x <= end_left + CATAN_END_BTN_W) and
                (CATAN_BTN_PAD <= y <= CATAN_BTN_PAD + CATAN_BTN_H)):
            self._end_turn()
            return

        # --- Trade button ---
        if ((CATAN_BTN_PAD <= x <= CATAN_BTN_PAD + CATAN_BTN_W) and
                (trade_bottom <= y <= trade_bottom + CATAN_BTN_H)):
            if self.trade_mode:
                self._cancel_trade()
            else:
                self.trade_mode   = True
                self.trade_choice = TRADE_NONE
            return

        # --- Trade submenu (pops up above the Trade button) ---
        if self.trade_mode and self.trade_choice == TRADE_NONE:
            trade_top = trade_bottom + CATAN_BTN_H  # top of Trade button
            by        = trade_top + 4        # bottom of the popup panel
            bx        = CATAN_BTN_PAD
            menu_w    = CATAN_BTN_W
            # Maritime Trade — top row of popup (by+44 .. by+72)
            if (bx + 8 <= x <= bx + menu_w - 8) and (by + 44 <= y <= by + 72):
                self._cancel_trade()
                self.window.vm.go_to("maritime_trade",
                    board=self.board, players=self.players, current_player=self.current_player, 
                    die1=self.die1, die2=self.die2, port_manager=self.port_manager
                )
                return
            # Barter Trade — bottom row of popup (by+8 .. by+36)
            if (bx + 8 <= x <= bx + menu_w - 8) and (by + 8 <= y <= by + 36):
                self._cancel_trade()
                self.window.vm.go_to("barter_trade",
                    board=self.board, players=self.players, current_player=self.current_player, 
                    die1=self.die1, die2=self.die2, port_manager=self.port_manager
                )
                return

        # Build button
        if ((CATAN_BTN_PAD <= x <= CATAN_BTN_PAD + CATAN_BTN_W) and
                (build_bottom <= y <= build_bottom + CATAN_BTN_H)):
            if self.build_mode:
                self._cancel_build()
            else:
                self.build_mode   = True
                self.build_choice = BUILD_NONE
            return

        # Build submenu
        if self.build_mode and self.build_choice == BUILD_NONE:
            build_top = build_bottom + CATAN_BTN_H
            by        = build_top + CATAN_BUILD_SUBMENU_Y_OFFSET
            bx        = CATAN_BTN_PAD
            btn_left  = bx + CATAN_BUILD_SUBMENU_BTN_INSET
            btn_right = bx + CATAN_BUILD_SUBMENU_W - CATAN_BUILD_SUBMENU_BTN_INSET
            if (btn_left <= x <= btn_right) and (by + 80 <= y <= by + 108):
                if self._can_afford(CITY_COST):
                    self.build_choice = BUILD_CITY
                return
            if (btn_left <= x <= btn_right) and (by + 44 <= y <= by + 72):
                if self._can_afford(SETTLEMENT_COST):
                    self.build_choice = BUILD_SETTLEMENT
                return
            if (btn_left <= x <= btn_right) and (by + 8 <= y <= by + 36):
                if self._free_roads > 0 or self._can_afford(ROAD_COST):
                    self.build_choice = BUILD_ROAD
                return

        # Confirmation popup
        if self.show_confirm:
            if self.build_choice == BUILD_SETTLEMENT and self.selected_node:
                pcx, pcy = self._node_pixel_cache[self.selected_node.node_id]
                pcy     += CATAN_CONFIRM_Y_OFFSET
            elif self.build_choice == BUILD_CITY and self.selected_node:
                pcx, pcy = self._node_pixel_cache[self.selected_node.node_id]
                pcy     += CATAN_CONFIRM_Y_OFFSET
            elif self.build_choice == BUILD_ROAD and self.selected_edge:
                mx, my, *_ = self._edge_pixel_cache[self.selected_edge.edge_id]
                pcx, pcy   = mx, my + CATAN_CONFIRM_Y_OFFSET
            else:
                self.show_confirm = False
                return

            pop_left     = pcx - CATAN_CONFIRM_POPUP_W / 2
            confirm_left = pop_left + CATAN_CONFIRM_BTN_INSET
            confirm_right= confirm_left + CATAN_CONFIRM_BTN_W
            cancel_right = pop_left + CATAN_CONFIRM_POPUP_W - CATAN_CONFIRM_BTN_INSET
            cancel_left  = cancel_right - CATAN_CONFIRM_BTN_W
            btn_top      = pcy + CATAN_CONFIRM_BTN_INSET + CATAN_CONFIRM_BTN_H
            btn_bottom   = pcy + CATAN_CONFIRM_BTN_INSET

            if (confirm_left <= x <= confirm_right) and (btn_bottom <= y <= btn_top):
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
            if (cancel_left <= x <= cancel_right) and (btn_bottom <= y <= btn_top):
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


        # Dev Cards button
        if (CATAN_BTN_PAD <= x <= CATAN_BTN_PAD + CATAN_BTN_W) and (card_bottom <= y <= card_bottom + CATAN_BTN_H):
            self.window.vm.go_to("play_card",
                board=self.board, players=self.players, current_player=self.current_player,
                die1=self.die1, die2=self.die2, port_manager=self.port_manager,
                shared_deck=self._shared_deck,
                bought_this_turn=self._bought_card_this_turn,
                played_card_this_turn=self._played_card_this_turn,
                free_roads=self._free_roads,
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
        for port in self.port_manager._port_data:
            node_ids = port["port"].get_port_nodes()
            if node.node_id in node_ids:
                player.ports.append(port["port"])
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
        self._check_longest_road(edge)

    def _check_longest_road(self, edge):
        player = self.players[self.current_player]
        #check if player has longest road
        edge_list = [edge]
        for e in edge_list:
            for node in e.nodes:
                # do not keep searching if another player has a settlement on the node
                if node.player == self.current_player or node.player is None:
                    for neighbor_edge in node.edges:
                        #check if edge has been explored before & if player owns another edge
                        if (neighbor_edge not in edge_list and
                                neighbor_edge is not e and
                                neighbor_edge.player == self.current_player):
                            edge_list.append(neighbor_edge)

        if player.road_length < len(edge_list):
            player.road_length = len(edge_list)

        #if player has played more than 5 connected roads
        if player.road_length >= ROADS_NEEDED:
            # loop through opponents to see if any have the largest army card
            holder_of_card = None
            for opponent in self.players:
                print(f"{player.name}: {opponent.road_length} cont. roads")
                if opponent.longest_road:
                    holder_of_card = opponent
                    # If no one holds the card yet
            if holder_of_card is None:
                player.longest_road = True
                player.victory_points += LONGEST_ROAD_VP
            # if someone holds the card, strip them of their title and give player the card
            elif holder_of_card != player and player.road_length > holder_of_card.road_length:
                holder_of_card.longest_road = False
                holder_of_card.victory_points -= LONGEST_ROAD_VP
                player.longest_road = True
                player.victory_points += LONGEST_ROAD_VP

    def _place_road_free(self, edge):
        """Place a road using a free-road grant from Road Building card."""
        edge.player       = self.current_player
        self._free_roads -= 1
        self.players[self.current_player].total_roads -= 1
        self._cancel_build()
        self._build_player_texts()
        print(f"{self.players[self.current_player].name} placed a free road! "
              f"({self._free_roads} remaining)")
        self._check_longest_road(edge)

    def _cancel_build(self):
        self.build_mode    = False
        self.build_choice  = BUILD_NONE
        self.hovered_node  = None
        self.hovered_edge  = None
        self.selected_node = None
        self.selected_edge = None
        self.show_confirm  = False

    def _cancel_trade(self):
        self.trade_mode    = False
        self.trade_choice  = TRADE_NONE
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
            self.window.vm.go_to("end", players=self.players, current_player=self.current_player)
            return

        # Clear "just_bought" flag on all cards so they can be played next turn
        for card in self.players[self.current_player].development_cards:
            card["just_bought"] = False

        self.current_player = (self.current_player + 1) % len(self.players)
        self._cancel_build()
        self._cancel_trade()
        self._card_list = arcade.SpriteList()

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

        #checks if roll is 7 and initiates robber placement phase
        if self.die1 + self.die2 == 7:
            self.window.vm.go_to("robber_res", 
                board=self.board, players=self.players, current_player=self.current_player, 
                die1=self.die1, die2=self.die2, port_manager=self.port_manager,
            )
            return

        self._give_resources()
        if self.players[self.current_player].computer:
            self.window.vm.go_to("computer_turn",
                board=self.board,
                players=self.players,
                current_player=self.current_player,
                die1=self.die1,
                die2=self.die2,
                port_manager=self.port_manager,
            )
        else:
            self.window.vm.go_to("catan",
                board=self.board,
                players=self.players,
                current_player=self.current_player,
                die1=self.die1,
                die2=self.die2,
                port_manager=self.port_manager,
                start_of_turn=True,
            )
