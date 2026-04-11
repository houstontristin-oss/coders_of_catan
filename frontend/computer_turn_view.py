"""
Contains ComputerTurnView class 

Allows player when its 1 person versus 3 computer players so that the
player can see the computer moves

"""
import random
import arcade

from backend.catan_board import CatanBoard
from .port_manager import PortManager

from .board_utils import cubic_to_pixel, node_to_pixel
from .drawing import (fill_rect, outline_rect, draw_settlement,
                      draw_road, draw_board, draw_city, draw_ocean_background,
                      draw_die_face, draw_speaker_button)
from .constants import (DICE_ROLL_DURATION, DICE_ROLL_FLIP_RATE, DEV_CARD_DECK,
                        DICE_SPRITES, ROAD_CARD_SPRITE, ARMY_CARD_SPRITE,
                        ROBBER_SPRITE, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y,
                        USE_OCEAN_BACKGROUND, OCEAN_BASE_COLOR, BACKGROUND_IMAGE,
                        RESOURCE_SPRITES, SPRITE_SCALE, DICE_AREA_WIDTH,
                        DICE_AREA_HEIGHT, TEXT_LIGHT_GRAY, HUD_PANEL_HEIGHT,
                        HUD_PANEL_WIDTH, BTN_ENDTURN, ICON_SIZE, HUD_PANEL_BG,
                        ONE, SIX, USE_DICE_SPRITES, CARD_PAD, DEV_KEY_VP, DEV_KEY_K,
                        DEV_KEY_YOP, DEV_KEY_M, DEV_KEY_RB, RESOURCE_ABBR, SCREEN_HEIGHT,
                        SCREEN_WIDTH, TEXT_WHITE, TEXT_GOLD, PROB)
from .view_constants import (CARD_SCALE, ARMY_ROAD_SPRITE_Y1, ARMY_ROAD_SPRITE_X,
                             ARMY_ROAD_SPRITE_Y2, CATAN_ROBBER_SCALE_MULT, CATAN_BTN_PAD,
                             CATAN_END_BTN_W, CATAN_BTN_H, CATAN_TEXT_SIZE_BTN,
                             CATAN_DICE_BOX_MARGIN, CATAN_LABEL_DICE_ROLL,
                             CATAN_DICE_LABEL_TOP_PAD, CATAN_TEXT_SIZE_DICE_LABEL,
                             CATAN_LABEL_DICE_HINT, CATAN_DICE_TOTAL_Y,
                             CATAN_TEXT_SIZE_DICE_HINT, CATAN_DIE_SIZE, CATAN_DIE_GAP,
                             CATAN_DICE_Y_OFFSET, CATAN_TEXT_SIZE_DICE_NUM,
                             CATAN_PLAYER_PANEL_MARGIN, CATAN_SUMMARY_BOX_GAP,
                             CATAN_SUMMARY_BOX_TOP_INSET, CATAN_SUMMARY_BOX_W,
                             CATAN_SUMMARY_BOX_H, CATAN_COLOR_SUMMARY_BG,
                             CATAN_COLOR_SUMMARY_TEXT, CATAN_SUMMARY_BOX_COUNT_Y_OFFSET,
                             CATAN_COLOR_SUMMARY_COUNT, CATAN_TEXT_SIZE_SUMMARY_COUNT,
                             CATAN_PLAYER_NAME_Y, CATAN_TEXT_SIZE_PLAYER_NAME,
                             CATAN_PLAYER_ROW_H, CATAN_TEXT_SIZE_PLAYER_VP,
                             CATAN_RESOURCE_ROW_GAP, CATAN_RESOURCE_TEXT_X_OFFSET,
                             CATAN_TEXT_SIZE_RESOURCE, CATAN_DEV_CARD_COUNT_Y_OFFSET,
                             CATAN_DEV_CARD_COUNT_COLOR, CATAN_COLOR_DROP_SHADOW,
                             CATAN_COLOR_BTN_OUTLINE, CATAN_PLAYER_MARKER_RADIUS,
                             CATAN_RESOURCE_ICON_ROW_GAP, CATAN_RESOURCE_ICON_X_OFFSET,
                             CATAN_RESOURCE_ICON_Y_OFFSET, CATAN_COLOR_DIE_BG,
                             CATAN_COLOR_SHAKE_OUTLINE, CATAN_TEXT_SIZE_TOTAL,
                             CATAN_SETTLEMENT_DRAW_SIZE, CATAN_CITY_DRAW_SIZE, CATAN_BTN_W,
                             LONGEST_ROAD_VP, ROADS_NEEDED, CATAN_MUTE_BTN_W, CATAN_MUTE_BTN_H,
                             CATAN_MUTE_BTN_PAD)

FAST_FORWARD = "Next Player"
NEXT_MOVE = "Next Move"
LOG_COLOR = (229,222,207)
GET_ROBBED = 7
NONE_PORT = 3
RES_PORT = 2
MARITIME_TRADE = 4

class ComputerTurnView(arcade.View):
    """Represents the screen view of a computer player's turn

        This class is used to create a view specific to a computer player

        Attributes:
            vm: a view manager
            board: the current game board
            players: all players in the game
            current_player: player whose turn it is currently
            die1: first die for rolling
            die2: cities second die for rolling
            port_manager: color of player
            shared_deck: name of player
        """
    def __init__(self,
        vm,
        board,
        players,
        current_player,
        die1,
        die2,
        port_manager,
        shared_deck=None,
        ):

        # --- Computer Move Options ---
        self.moves = ['Trade', 'Build', 'DevCard']

        # --- Turn log state ---
        self._log_messages = []
        self._log_line_texts = []
        self._log_max_lines = 18
        self._turn_fully_revealed = False


        super().__init__()
        self.vm = vm
        self.board = board
        self.players = players
        self.current_player = current_player
        self.die1 = die1
        self.die2 = die2
        self.port_manager = port_manager
        self._free_roads = 0
        self._bought_card_this_turn = False
        self._played_card_this_turn = False

        # --- Trade modal state ---
        self._trade_pending          = False
        self._trade_offer            = {r: 0 for r in ["BRICK", "ORE", "WHEAT", "SHEEP", "WOOD"]}
        self._trade_receive          = {r: 0 for r in ["BRICK", "ORE", "WHEAT", "SHEEP", "WOOD"]}
        self._trade_computer_player  = None   # the computa player making the offer
        self._modal_accept_rect      = None
        self._modal_decline_rect     = None
        self._modal_can_afford       = False
        self._dynamic_texts          = []

        # --- Human Player ---
        self.human = self.players[0]
        for p in self.players:
            if not p.computer:
                self.human = p
                break

        self._dice_animating  = True
        self._dice_anim_timer = DICE_ROLL_DURATION
        self._dice_flip_timer = DICE_ROLL_FLIP_RATE
        self._anim_die1       = die1   # face showing during animation
        self._anim_die2       = die2
        self._dice_sprites    = {}     # face value (1-6) -> arcade.Sprite | None
        self._load_dice_sprites()

        # --- Shared persistent deck ---
        if shared_deck is None:
            self._deck = list(DEV_CARD_DECK)
            random.shuffle(self._deck)
        else:
            self._deck = shared_deck

        # --- Robber state ---
        self._robber_sprite    = None
        self._robber_list      = arcade.SpriteList()
        self._robber_sprite_ok = False
        self._robber_tile      = None
        self._load_robber_sprite()

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
        self._build_node_pixel_cache()
        self._build_edge_pixel_cache()
        self._build_tile_pixel_cache()

        if self.port_manager is None:
            self.port_manager = PortManager(self.board, self._edge_pixel_cache)

        self._build_text_objects()  # rebuild after caches ready
        self._refresh_log_text()

        player = self.players[self.current_player]
        self._add_log(f"{player.name}'s turn begins.", player.color)
        self._add_log(f"{player.name} rolled a {self.die1 + self.die2}.", player.color)

    # -----------------------------------------------------------------------
    # Dice sprites
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
        for tile in self.board.tiles.values():
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
    # Caches
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
    def _load_resource_icons(self):
        self.resource_icons   = {}
        self.icon_sprite_list = arcade.SpriteList()
        for res in ["brick", "ore", "wheat", "sheep", "forest"]:
            sprite = arcade.Sprite(RESOURCE_SPRITES[res], scale=SPRITE_SCALE)
            self.resource_icons[res] = sprite
            self.icon_sprite_list.append(sprite)

    # -----------------------------------------------------------------------
    # Text objects
    def _build_text_objects(self):
        self.txt_fast = arcade.Text(
            FAST_FORWARD,
            SCREEN_WIDTH - CATAN_BTN_PAD - CATAN_END_BTN_W / 2,
            CATAN_BTN_PAD + CATAN_BTN_H / 2,
            TEXT_WHITE, CATAN_TEXT_SIZE_BTN, bold=True, anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_next = arcade.Text(
            NEXT_MOVE,
            SCREEN_WIDTH - CATAN_BTN_PAD * 2 - CATAN_END_BTN_W * 1.5,
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


        self._build_player_texts()
        self._build_dice_texts()
        self._build_log_texts()


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

        self._build_player_texts()


    def _get_ai_summary_players(self):
        """
        Settler vs. AI mode:
        always show the AI players in fixed order.
        """
        ai_players = []
        for idx, player in enumerate(self.players):
            if player.computer:
                ai_players.append((idx, player))
        return ai_players


    def _draw_player_summary_boxes(self):
        """
        Draw compact AI summary boxes to the right of the human player's panel.
        """
        panel_x = CATAN_PLAYER_PANEL_MARGIN
        panel_y = SCREEN_HEIGHT - HUD_PANEL_HEIGHT - CATAN_PLAYER_PANEL_MARGIN

        start_x = panel_x + HUD_PANEL_WIDTH + CATAN_SUMMARY_BOX_GAP
        top_y = panel_y + HUD_PANEL_HEIGHT - CATAN_SUMMARY_BOX_TOP_INSET

        ai_players = self._get_ai_summary_players()

        for i, (player_idx, player) in enumerate(ai_players):
            left = start_x + i * (CATAN_SUMMARY_BOX_W + CATAN_SUMMARY_BOX_GAP)
            bottom = top_y - CATAN_SUMMARY_BOX_H

            fill_rect(left, bottom, CATAN_SUMMARY_BOX_W, CATAN_SUMMARY_BOX_H,
                      CATAN_COLOR_SUMMARY_BG)

            is_current_ai = player_idx == self.current_player

            if is_current_ai:
                outline_rect(left, bottom, CATAN_SUMMARY_BOX_W, CATAN_SUMMARY_BOX_H, TEXT_GOLD, 4)
            else:
                outline_rect(left, bottom, CATAN_SUMMARY_BOX_W, CATAN_SUMMARY_BOX_H,
                             player.color, 2)

            arcade.Text(
                player.name,
                left + CATAN_SUMMARY_BOX_W / 2,
                bottom + CATAN_SUMMARY_BOX_H - 18,
                CATAN_COLOR_SUMMARY_TEXT,
                9,
                bold=True,
                anchor_x="center",
                anchor_y="center",
                font_name="MedievalSharp",
            ).draw()

            arcade.Text(
                str(player.get_total_cards()),
                left + CATAN_SUMMARY_BOX_W / 2,
                bottom + CATAN_SUMMARY_BOX_COUNT_Y_OFFSET,
                CATAN_COLOR_SUMMARY_COUNT,
                CATAN_TEXT_SIZE_SUMMARY_COUNT,
                bold=True,
                anchor_x="center",
                anchor_y="center",
                font_name="MedievalSharp",
            ).draw()

            arcade.draw_circle_filled(
                left + 10,
                bottom + CATAN_SUMMARY_BOX_H - 10,
                5,
                player.color,
            )

    def _draw_pending_modal(self):
        # modal for barter trade popup
        _RES_DISPLAY = {"BRICK": "Brick", "ORE": "Ore", "WHEAT": "Wheat",
                        "SHEEP": "Sheep", "WOOD": "Wood"}

        fill_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 130))

        modal_w, modal_h = 500, 270
        mx = (SCREEN_WIDTH  - modal_w) / 2
        my = (SCREEN_HEIGHT - modal_h) / 2

        fill_rect(mx, my, modal_w, modal_h, (20, 20, 55, 250))
        outline_rect(mx, my, modal_w, modal_h, TEXT_GOLD, 2)

        sender   = self._trade_computer_player
        receiver = self.human

        offer_str   = ", ".join(f"{v}× {_RES_DISPLAY[r]}"
                                for r, v in self._trade_offer.items()   if v > 0) or "nothing"
        receive_str = ", ".join(f"{v}× {_RES_DISPLAY[r]}"
                                for r, v in self._trade_receive.items() if v > 0) or "nothing"

        can_afford = receiver.can_afford_trade(self._trade_receive)
        self._modal_can_afford = can_afford

        self._dynamic_texts = []

        self._dynamic_texts.append(arcade.Text(
            f"{receiver.name} — Trade Offer!",
            SCREEN_WIDTH / 2, my + modal_h - 30,
            TEXT_GOLD, 15, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))
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

        if not can_afford:
            self._dynamic_texts.append(arcade.Text(
                "(You don't have enough resources to accept)",
                SCREEN_WIDTH / 2, my + modal_h - 130,
                (255, 120, 80), 9,
                anchor_x="center", anchor_y="center",
                font_name="MedievalSharp",
            ))

        _PAD_BTN, _MBTN_W, _MBTN_H = 40, 180, 50
        accept_x, accept_y = mx + _PAD_BTN, my + 28
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

        decline_x, decline_y = mx + modal_w - _PAD_BTN - _MBTN_W, my + 28
        fill_rect(decline_x, decline_y, _MBTN_W, _MBTN_H, BTN_ENDTURN)
        outline_rect(decline_x, decline_y, _MBTN_W, _MBTN_H, (255, 255, 255, 60), 1)
        self._dynamic_texts.append(arcade.Text(
            "Decline",
            decline_x + _MBTN_W / 2, decline_y + _MBTN_H / 2,
            TEXT_WHITE, 13, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        ))

        self._modal_accept_rect  = (accept_x,  accept_y,  _MBTN_W, _MBTN_H)
        self._modal_decline_rect = (decline_x, decline_y, _MBTN_W, _MBTN_H)

        for txt in self._dynamic_texts:
            txt.draw()


    def _build_player_texts(self):
        panel_x   = CATAN_PLAYER_PANEL_MARGIN
        panel_top = SCREEN_HEIGHT - CATAN_PLAYER_PANEL_MARGIN

        self.txt_player_name = arcade.Text(
            self.human.name,
            panel_x + HUD_PANEL_WIDTH // 2, panel_top - CATAN_PLAYER_NAME_Y,
            TEXT_GOLD, CATAN_TEXT_SIZE_PLAYER_NAME, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_player_vp = arcade.Text(
            f"Victory Points: {self.human.victory_points}",
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
                    f"{labels[res]}: {self.human.resource_cards.get(res)}",
                    panel_x + ICON_SIZE + CATAN_RESOURCE_TEXT_X_OFFSET, ry,
                    TEXT_WHITE, CATAN_TEXT_SIZE_RESOURCE,
                    anchor_y="center",
                    font_name="MedievalSharp",
                )
            )

        n_cards = len(self.human.development_cards)
        self.txt_dev_card_count = arcade.Text(
            f"Dev Cards: {n_cards}",
            panel_x + HUD_PANEL_WIDTH // 2,
            (panel_top - CATAN_PLAYER_NAME_Y - CATAN_PLAYER_ROW_H * 2
             - (ICON_SIZE + CATAN_RESOURCE_ROW_GAP) * 5 - CATAN_DEV_CARD_COUNT_Y_OFFSET),
            CATAN_DEV_CARD_COUNT_COLOR, CATAN_TEXT_SIZE_RESOURCE,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

    def _build_log_texts(self):
        self.txt_log_title = arcade.Text(
            "AI Move Log:",
            CATAN_PLAYER_PANEL_MARGIN + 8,
            450,
            HUD_PANEL_BG,
            CATAN_TEXT_SIZE_RESOURCE,
            font_name="MedievalSharp",
        )
        self.txt_log = arcade.Text(
            "",
            CATAN_PLAYER_PANEL_MARGIN + 6,
            380,
            HUD_PANEL_BG,
            CATAN_TEXT_SIZE_RESOURCE,
            font_name="MedievalSharp",
            multiline=True,
            width = HUD_PANEL_WIDTH - 16
        )

    def _refresh_log_text(self):
        self._log_line_texts = []

        x = CATAN_PLAYER_PANEL_MARGIN + 8
        y = 435
        log_width = HUD_PANEL_WIDTH - 16
        base_line_height = 22

        for message, color in self._log_messages:
            txt = arcade.Text(
                message,
                x,
                y,
                color,
                CATAN_TEXT_SIZE_RESOURCE,
                font_name="MedievalSharp",
                width=log_width,
                multiline=True,
                anchor_x="left",
                anchor_y="top",
            )
            self._log_line_texts.append(txt)

            estimated_lines = max(1, (len(message) // 24) + 1) if message else 1
            y -= estimated_lines * base_line_height


    def _add_log(self, message: str, color=None):
        if color is None:
            color = HUD_PANEL_BG

        self._log_messages.append((message, color))

        if len(self._log_messages) > self._log_max_lines:
            del self._log_messages[:-self._log_max_lines]

        self._refresh_log_text()


    def _get_log_color_for_player(self, player_name: str):
        for player in self.players:
            if player.name == player_name:
                return player.color
        return HUD_PANEL_BG

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
    def _draw_bottom_bar(self):
        fill_rect(SCREEN_WIDTH - CATAN_BTN_PAD - CATAN_END_BTN_W + 2,
                  CATAN_BTN_PAD - 2, CATAN_END_BTN_W, CATAN_BTN_H,
                  CATAN_COLOR_DROP_SHADOW)
        fill_rect(SCREEN_WIDTH - CATAN_BTN_PAD - CATAN_END_BTN_W,
                  CATAN_BTN_PAD, CATAN_END_BTN_W, CATAN_BTN_H, BTN_ENDTURN)
        outline_rect(SCREEN_WIDTH - CATAN_BTN_PAD - CATAN_END_BTN_W,
                     CATAN_BTN_PAD, CATAN_END_BTN_W, CATAN_BTN_H,
                     CATAN_COLOR_BTN_OUTLINE, 1)
        fill_rect(SCREEN_WIDTH - CATAN_BTN_PAD * 2 - CATAN_END_BTN_W * 2,
                  CATAN_BTN_PAD, CATAN_END_BTN_W, CATAN_BTN_H,
                  BTN_ENDTURN if len(self.moves) != 0 else TEXT_LIGHT_GRAY)
        outline_rect(SCREEN_WIDTH - CATAN_BTN_PAD * 2 - CATAN_END_BTN_W * 2,
                     CATAN_BTN_PAD, CATAN_END_BTN_W, CATAN_BTN_H,
                     CATAN_COLOR_BTN_OUTLINE, 1)

        self.txt_fast.draw()
        self.txt_next.draw()

    def _draw_player_panel(self):
        panel_x = CATAN_PLAYER_PANEL_MARGIN
        panel_y = SCREEN_HEIGHT - HUD_PANEL_HEIGHT - CATAN_PLAYER_PANEL_MARGIN

        fill_rect(panel_x, panel_y, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, HUD_PANEL_BG)
        outline_rect(panel_x, panel_y, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, self.human.color)

        arcade.draw_circle_filled(
            panel_x + CATAN_PLAYER_MARKER_RADIUS * 2,
            panel_y + HUD_PANEL_HEIGHT - CATAN_PLAYER_NAME_Y,
            CATAN_PLAYER_MARKER_RADIUS, self.human.color
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

            spr1.scale = CATAN_DIE_SIZE / max(spr1.width, spr1.height)
            spr1.center_x = die1_x + CATAN_DIE_SIZE / 2
            spr1.center_y = die_y + CATAN_DIE_SIZE / 2

            spr2.scale = CATAN_DIE_SIZE / max(spr2.width, spr2.height)
            spr2.center_x = die1_x + CATAN_DIE_SIZE + CATAN_DIE_GAP + CATAN_DIE_SIZE / 2
            spr2.center_y = die_y + CATAN_DIE_SIZE / 2

            fill_rect(die1_x, die_y, CATAN_DIE_SIZE, CATAN_DIE_SIZE, CATAN_COLOR_DIE_BG)
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
            shake_alpha = (int(180 * (self._dice_anim_timer / DICE_ROLL_DURATION))
                           if self._dice_animating else 0)

            draw_die_face(
                die1_x,
                die_y,
                CATAN_DIE_SIZE,
                face1,
                shaking=self._dice_animating,
                shake_alpha=shake_alpha,
            )

            draw_die_face(
                die1_x + CATAN_DIE_SIZE + CATAN_DIE_GAP,
                die_y,
                CATAN_DIE_SIZE,
                face2,
                shaking=self._dice_animating,
                shake_alpha=shake_alpha,
            )

        if not self._dice_animating:
            arcade.Text(
                f"Total: {self.die1 + self.die2}",
                dx + DICE_AREA_WIDTH / 2, dy + CATAN_DICE_TOTAL_Y,
                TEXT_LIGHT_GRAY, CATAN_TEXT_SIZE_TOTAL, anchor_x="center",
                font_name="MedievalSharp",
            ).draw()


    # -----------------------------------------------------------------------
    # Largest Army and Longest Road drawing
    def _draw_cards(self):
        player = self.players[self.current_player]
        if self._army_card_sprite not in self._card_list and player.largest_army:
            self._army_card_sprite.center_y = (ARMY_ROAD_SPRITE_Y1 if not player.longest_road
                                               else ARMY_ROAD_SPRITE_Y2)
            self._card_list.append(self._army_card_sprite)
        if self._road_card_sprite not in self._card_list and player.longest_road:
            self._card_list.append(self._road_card_sprite)
        self._card_list.draw()

    # -----------------------------------------------------------------------
    # Log Scroll
    def _draw_log_reactangle(self):
        fill_rect(CATAN_PLAYER_PANEL_MARGIN, CARD_PAD, HUD_PANEL_WIDTH, 450, LOG_COLOR)
        outline_rect(CATAN_PLAYER_PANEL_MARGIN, CARD_PAD, HUD_PANEL_WIDTH, 450, HUD_PANEL_BG)
        self.txt_log_title.draw()

    # -----------------------------------------------------------------------
    # Port drawing
    def _draw_ports(self):
        self.port_manager.draw()

    # -----------------------------------------------------------------------
    # Board pieces (always drawn)
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

    def _get_mute_button_rect(self):
        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - CATAN_DICE_BOX_MARGIN
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - CATAN_DICE_BOX_MARGIN

        left = SCREEN_WIDTH - CATAN_MUTE_BTN_W - CATAN_DICE_BOX_MARGIN
        bottom = dy - CATAN_MUTE_BTN_H - CATAN_MUTE_BTN_PAD

        return left, bottom, CATAN_MUTE_BTN_W, CATAN_MUTE_BTN_H

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

        self._draw_placed_pieces()

        if self._robber_sprite_ok and self._robber_list:
            self._robber_list.draw()

        self._draw_player_panel()
        self._draw_player_summary_boxes()
        self._draw_dice_area()

        mute_left, mute_bottom, mute_w, mute_h = self._get_mute_button_rect()
        draw_speaker_button(
            mute_left,
            mute_bottom,
            mute_w,
            mute_h,
            self.vm.music.muted,
        )

        self._draw_bottom_bar()
        self._draw_log_reactangle()
        self._draw_cards()
        for txt in self._log_line_texts:
            txt.draw()
        if self._trade_pending:
            self._draw_pending_modal()

    # -----------------------------------------------------------------------
    # Mouse press
    def on_mouse_press(self, x, y, button, modifiers):
        mute_left, mute_bottom, mute_w, mute_h = self._get_mute_button_rect()
        if (mute_left <= x <= mute_left + mute_w and
                mute_bottom <= y <= mute_bottom + mute_h):
            self.vm.music.toggle_mute()
            return
        # barter trade
        if self._trade_pending:
            self._handle_modal_click(x, y)
            return
        # End Turn
        end_left = SCREEN_WIDTH - CATAN_BTN_PAD - CATAN_END_BTN_W
        if len(self.moves) != 0:
            if ((end_left - CATAN_BTN_W <= x < end_left) and
                    (CATAN_BTN_PAD <= y <= CATAN_BTN_PAD + CATAN_BTN_H)):
                self._make_move()

        if ((end_left <= x <= end_left + CATAN_END_BTN_W) and
                (CATAN_BTN_PAD <= y <= CATAN_BTN_PAD + CATAN_BTN_H)):
            if not self._turn_fully_revealed:
                self._fast_forward()
            else:
                self._end_turn()
            return

    # Make Move Function for computer to make a singular move
    def _make_move(self):
        if not self.moves:
            return
        move = self.moves.pop(0)
        player = self.players[self.current_player]
        move_success = False
        while not move_success and move is not None:
            if move == "Trade":
                needed_resources = self._no_resource_access()
                if player.get_total_resources() > GET_ROBBED:
                    if len(player.ports) != 0:
                        port = random.choice(player.ports)
                        get_from_port = player.min_resource()
                        trade_amt = RES_PORT
                        give_to_port = port.resource
                        if port.resource is not None:
                            trade_amt = NONE_PORT
                            give_to_port = player.max_resource()
                        player.exchange_resources({give_to_port: trade_amt}, {get_from_port: 1})
                        self._add_log(f"{player.name} used "
                                      f"{port} to trade for 1 {get_from_port}.", player.color)
                        move_success = True

                    elif len(needed_resources) != 0:
                        # find resource of the most amount
                        res_to_trade = player.max_resource()
                        # pick a random number between
                        amt_to_offer = random.randint(1, player.resource_cards[res_to_trade])
                        res_to_get = random.choice(needed_resources)

                        # Find player with the most cards to offer trade to
                        player_to_trade_with = None
                        max_res = 0
                        for p in self.players:
                            if p != player and p.get_total_resources() > max_res:
                                player_to_trade_with = p
                                max_res = p.get_total_resources()
                        # ask for 1, or 2 of a resource in return
                        amt_to_get = random.randint(1, 2)

                        to_trade = {res_to_trade: amt_to_offer}
                        to_get = {res_to_get: amt_to_get}
                        if player_to_trade_with and player_to_trade_with.can_afford_trade(to_get):
                            if player_to_trade_with == self.human:
                                self._trade_offer           = to_trade
                                self._trade_receive         = to_get
                                self._trade_computer_player = player
                                self._trade_pending         = True
                                return   # modal click resumes move processing

                            accept = random.randint(0,1) # 50% chance other comp will accept
                            if accept:
                                player.exchange_resources(to_trade, to_get)
                                player_to_trade_with.exchange_resources(to_get, to_trade)
                                self._add_log(
                                    f"{player.name} traded {amt_to_offer} {res_to_trade} "
                                    f"for {amt_to_get} {res_to_get}.", player.color)
                                move_success = True
                    else:
                        to_trade = player.max_resource()
                        if player.resource_cards[to_trade] >= MARITIME_TRADE:
                            get_trade = player.min_resource()
                            player.exchange_resources({to_trade: MARITIME_TRADE}, {get_trade: 1})
                            self._add_log(f"{player.name} maritime traded, giving 4 {to_trade} "
                                          f"for 1 {get_trade}.", player.color)
                            move_success = True
                            if len(self.moves) == 0:
                                self._turn_fully_revealed = True

            if move == "Build":
                # place free road
                while self._free_roads > 0:
                    road_edge = player.best_road_location()
                    if road_edge is not None:
                        self._place_road_free(road_edge)
                        move_success = True

                # place a city
                city_node = player.best_city_location()
                if city_node is not None:
                    if player.can_afford_city():
                        self._place_city(city_node)
                        move_success = True
                # place a settlement
                settle_node = player.best_settlement_location()
                if settle_node is not None:
                    if player.can_afford_settlement():
                        self._place_settlement(settle_node)
                        move_success = True
                else:
                    # place a road
                    if player.can_afford_road():
                        road_edge = player.best_road_location()
                        if road_edge is not None:
                            self._place_road(road_edge)
                            move_success = True
                    # buy a dev card because
                    if player.can_afford_dev_card():
                        self._buy_dev_card()
                        self._add_log(f"{player.name} bought a development card.", player.color)
                        move_success = True

            elif move == "DevCard":
                # Filter to cards that are playable this turn (not just bought, not VP cards)
                playable_cards = [
                    card for card in player.development_cards
                    if not card["just_bought"] and card["type"] != DEV_KEY_VP
                ]

                if not playable_cards or self._played_card_this_turn:
                    return

                card = random.choice(playable_cards)

                if card["type"] == DEV_KEY_VP:
                    # vp already added to total, dont need to keep the card since it cant be
                    # played
                    player.development_cards.remove(card)
                    move_success = True
                elif card["type"] == DEV_KEY_K:
                    # Move robber to a high-value tile the computer isn't adjacent to
                    self._play_knight(player, card)
                    move_success = True
                elif card["type"] == DEV_KEY_YOP:
                    # Take the 2 resources the computer has least of
                    res1 = player.min_resource()
                    player.resource_cards[res1] += 1
                    player.development_cards.remove(card)
                    res2 = player.min_resource()          # re-check after first grant
                    player.resource_cards[res2] += 1
                    self._add_log(f"{player.name} played Year of Plenty and "
                                  f"gained 1 {res1} and 1 {res2}.", player.color)
                    move_success = True
                elif card["type"] == DEV_KEY_M:
                    # Steal whatever resource the computer has least of from all opponents
                    target_res = player.min_resource()
                    for opponent in self.players:
                        if opponent is not player:
                            stolen = opponent.resource_cards.get(target_res, 0)
                            opponent.resource_cards[target_res] = 0
                            player.resource_cards[target_res] += stolen
                    player.development_cards.remove(card)
                    self._add_log(f"{player.name} played Monopoly on {target_res} and "
                                  f"collected all available {target_res} "
                                  f"cards from opponents.", player.color)
                    move_success = True
                elif card["type"] == DEV_KEY_RB:
                    # gives comp two roads to build for free, handled by build logic
                    player.development_cards.remove(card)
                    self.moves.append("Build") # add ability to build again
                    self._add_log(f"{player.name} played Road Building and "
                                  f"gained 2 free roads.", player.color)
                    move_success = True
                else:
                    print("computer_turn_view.py: Unrecognised dev card type:", card["type"])
                self._played_card_this_turn = True
                self._build_player_texts()

            if not move_success:
                try:
                    move = self.moves.pop(0)
                except IndexError:
                    move = None
                    self._add_log(f"{player.name} cannot make any more moves this turn.",
                                  player.color)

    # Fast Forward Function for computer to make many moves
    # until either done or need human player input
    def _fast_forward(self):
        while len(self.moves) > 0 and not self._trade_pending:
            self._make_move()

        if len(self.moves) == 0:
            self._turn_fully_revealed = True

    def _handle_modal_click(self, x, y):
        # barter trade modal handler
        if self._modal_accept_rect is None or self._modal_decline_rect is None:
            return

        ax, ay, aw, ah = self._modal_accept_rect
        dx, dy, dw, dh = self._modal_decline_rect

        if ax <= x <= ax + aw and ay <= y <= ay + ah: # accept button location
            if self._modal_can_afford:
                self._execute_trade()
            return

        # Change to reflect self. requirement for text
        if dx <= x <= dx + dw and dy <= y <= dy + dh: # decline button location
            self._result_msg = f"{self.players[self._trade_pending].name} declined the trade."
            self._trade_pending    = None

    # -----------------------------------------------------------------------
    # Placement
    def _place_settlement(self, node):
        player = self.players[self.current_player]
        player.build_settlement(CatanBoard, node)
        node.player   = self.current_player
        node.building = "settlement"
        for port in self.port_manager.port_data:
            node_ids = port["port"].get_port_nodes()
            if node.node_id in node_ids:
                player.ports.append(port["port"])
        player.victory_points += 1
        self._add_log(f"{player.name} built a settlement.", player.color)
        self._build_player_texts()
        print(f"{player.name} built a settlement! VP: {player.victory_points}")

    def _place_city(self, node):
        player = self.players[self.current_player]
        player.build_city(CatanBoard, node)
        node.building = "city"
        player.victory_points += 1
        self._add_log(f"{player.name} upgraded to a city!", player.color)
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
        player.build_road(CatanBoard, edge)
        edge.player = self.current_player
        self._add_log(f"{player.name} built a road!", player.color)
        self._build_player_texts()
        print(f"{player.name} built a road!")
        self._check_longest_road(edge)


    def _check_longest_road(self, edge):
        player = self.players[self.current_player]
        #check if player has longest road
        edge_lists = [[edge]]
        for edge_list in edge_lists:
            for e in edge_list:
                for node in e.nodes:
                    # do not keep searching if another player has a settlement on the node
                    if node.player == self.current_player or node.player is None:
                        branches = 0
                        for neighbor_edge in node.edges:
                            #check if edge has been explored before & if player owns another edge
                            if (neighbor_edge not in edge_list and
                                    neighbor_edge is not e and
                                    neighbor_edge.player == self.current_player):
                                branches += 1
                                edge_list.append(neighbor_edge)
                        if branches == 2:
                            split_edge = edge_list.pop(-1) # remove edge from previous branch
                            edge_lists.append(edge_list[:-1] + [split_edge]) # create new edge list
        max_length = 0
        for edge_list in edge_lists:
            length = len(edge_list) - (len(edge_lists) - 1)
            max_length = max(max_length, length)
        player.road_length = max_length

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

        if player.longest_road:
            self._add_log(f"{player.name} built the Longest Road.", player.color)


    def _place_road_free(self, edge):
        """Place a road using a free-road grant from Road Building card."""
        edge.player       = self.current_player
        self._free_roads -= 1
        self.players[self.current_player].total_roads -= 1
        self._build_player_texts()
        print(f"{self.players[self.current_player].name} placed a free road! "
              f"({self._free_roads} remaining)")
        self._check_longest_road(edge)
        player = self.players[self.current_player]
        self._add_log(f"{player.name} built a free road.", player.color)

    # -----------------------------------------------------------------------
    # Dev Card
    def _buy_dev_card(self):
        card_type = self._deck.pop()
        self.players[self.current_player].development_cards.append({"type": card_type,
                                                                    "just_bought": True})

        if card_type == DEV_KEY_VP:
            self.players[self.current_player].victory_points += 1

    def _play_knight(self, player, card):
        best_tile = None
        best_score = -1

        winning_player = max(self.players, key=lambda p: p.victory_points) # used in picking tile
        # select best tile to place robber on
        for xyz, tile in self.board.tiles.items():
            if tile.robber or tile.resource == "desert":
                continue
            # skip tiles comp player is adjacent to
            computer_adjacent = any(
                node.player == self.current_player for node in tile.nodes
            )
            if computer_adjacent:
                continue

            # Prefer high-probability numbers, value is number of pips on each number tile
            prob = PROB.get(tile.number, 0)
            # Count distinct opponents with a settlement/city on this tile
            opponent_nodes = [
                node for node in tile.nodes
                if node.player is not None and node.player != self.current_player
            ]
            num_opponents = len(set(node.player for node in opponent_nodes))

            # Bonus if the winning player borders this tile
            winning_player_adjacent = any(
                node.player == self.players.index(winning_player)
                for node in tile.nodes
            )
            winner_bonus = 2 if winning_player_adjacent else 0

            score = prob + num_opponents + winner_bonus
            if score > best_score:
                best_score = score
                best_tile = (xyz, tile)

        if best_tile is None:
            # Fallback: any non-desert, non-current tile
            for xyz, tile in self.board.tiles.items():
                if not tile.robber and tile.resource != "desert":
                    best_tile = (xyz, tile)
                    break

        if best_tile:
            # Move robber from current tile
            for _, t in self.board.tiles.items():
                t.robber = False
            xyz, tile = best_tile
            tile.robber = True
            self._place_robber_on_tile()

            # Steal from avaiable victim
            victims = [
                self.players[node.player]
                for node in tile.nodes
                if node.player is not None and node.player != self.current_player
            ]
            if victims:
                victim = max(victims, key=lambda p: p.get_total_resources())
                stolen_res = victim.random_resource()
                if victim.resource_cards[stolen_res] > 0:
                    victim.resource_cards[stolen_res] -= 1
                    player.resource_cards[stolen_res] += 1
                    self._add_log(f"{player.name} played Knight and stole {stolen_res} from "
                                  f"{victim.name}.", player.color)
            else:
                self._add_log(f"{player.name} played Knight and moved the robber.", player.color)
            # Check for largest army and update
            player.knight_count += 1
            if player.knight_count >= 3:
                holder = next((p for p in self.players if p.largest_army), None)
                if holder is None:
                    player.largest_army = True
                    player.victory_points += 2
                elif player.knight_count > holder.knight_count:
                    holder.largest_army = False
                    holder.victory_points -= 2
                    player.largest_army = True
                    player.victory_points += 2

        player.development_cards.remove(card)

    # -----------------------------------------------------------------------
    # Trading Helper functions
    # returns a list of resources that the player does not have access to from their settlements
    # -----------------------------------------------------------------------
    def _no_resource_access(self):
        # find all res they have access to
        accessible_res = []
        for tile in self.board.tiles.values():
            for node in tile.nodes:
                if node.player == self.current_player:
                    accessible_res.append(tile.resource)
        # make list of uppercase res they cant access
        no_access_res = []
        for lower_res, upper_res in RESOURCE_ABBR.items():
            if lower_res not in accessible_res:
                no_access_res.append(upper_res)

        return no_access_res

    # -----------------------------------------------------------------------
    # Resource distribution
    def _give_resources(self):
        roll = self.die1 + self.die2
        any_resources_given = False

        for tile in self.board.tiles.values():
            if tile.number == roll and not tile.robber:
                resource = RESOURCE_ABBR[tile.resource]
                for node in tile.nodes:
                    if node.player is not None:
                        player = self.players[node.player]
                        gain = 1 if node.building == "settlement" else 2
                        player.resource_cards[resource] += gain
                        any_resources_given = True

        return any_resources_given


    # -----------------------------------------------------------------------
    # Computer Players Discarding half their hand when a 7 is rolled
    def _comp_robber_discard(self):
        #From RobberResView, we need a way for the computer to pick a new spot for the robber
        # do not show RobberResView if its only computer players that need to discard resources
        for player in self.players:
            if player.computer and player.get_total_resources() > GET_ROBBED:
                # discard half of the comp players resources
                giving_resources = {}
                amt_to_discard = player.get_total_resources() // 2
                for resource, amount in player.resource_cards.items():
                    giving_resources[resource] = 0
                    if amt_to_discard > 0:
                        get_rid_of = random.randint(0, amount
                        if amount < amt_to_discard else amt_to_discard)
                        amt_to_discard -= get_rid_of
                        giving_resources[resource] += get_rid_of
                while amt_to_discard > 0:
                    for resource, amount in player.resource_cards.items():
                        if amt_to_discard > 0:
                            get_rid_of = random.randint(0, amount - giving_resources[resource]
                            if amount - giving_resources[resource] < amt_to_discard
                            else amt_to_discard)
                            amt_to_discard -= get_rid_of
                            giving_resources[resource] += get_rid_of

                player.exchange_resources(giving_resources, {})
                print(f"ROBBER! {player.name} discarded {giving_resources}")

    # -----------------------------------------------------------------------
    # End turn
    def _end_turn(self):
        player = self.players[self.current_player]
        self._add_log(f"{player.name}'s turn ends.", player.color)
        self._add_log("", HUD_PANEL_BG)
        if self.players[self.current_player].victory_points >= 10:
            self.vm.go_to("end", self.players, self.current_player)
            return

        # Clear "just_bought" flag on all cards so they can be played next turn
        for card in self.players[self.current_player].development_cards:
            card["just_bought"] = False

        self.current_player = (self.current_player + 1) % len(self.players)
        self._card_list = arcade.SpriteList()


        # Reset per-turn dev-card flags for the new player
        self._bought_card_this_turn  = False
        self._played_card_this_turn  = False
        # NOTE: free_roads intentionally carries over if a Road Building card was
        # played and not fully used (edge case — keep count until exhausted)
        self._free_roads = max(self._free_roads, 0)

        # Roll dice and start animation
        self.die1 = random.randint(ONE, SIX)
        self.die2 = random.randint(ONE, SIX)

        #checks if roll is 7 and initiates robber placement phase
        if self.die1 + self.die2 == GET_ROBBED:
            self._comp_robber_discard()
            #once the computer has discarded cards, the player may have to too so go to robber res
            for player in self.players:
                print(f"{player.name}: {player.resource_cards}")
            self.vm.go_to(
                    "robber_res",
                    board=self.board,
                    players=self.players,
                    current_player=self.current_player,
                    die1=self.die1,
                    die2=self.die2,
                    port_manager=self.port_manager)
            return

        resources_given = self._give_resources()
        roller = self.players[self.current_player]

        if resources_given:
            self._add_log(f"{roller.name} collected resources from the roll.", roller.color)
        else:
            self._add_log(f"{roller.name} collected no resources from the roll.", roller.color)

        if self.players[self.current_player].computer:
            self.vm.go_to(
                "computer_turn",
                board=self.board,
                players=self.players,
                current_player=self.current_player,
                die1=self.die1,
                die2=self.die2,
                port_manager=self.port_manager,
                shared_deck=self._deck,
            )
            return

        self.vm.go_to(
            "catan",
            board=self.board,
            players=self.players,
            current_player=self.current_player,
            die1=self.die1,
            die2=self.die2,
            port_manager=self.port_manager,
            start_of_turn=True,
        )
        return

    def _execute_trade(self):
        computer = self._trade_computer_player
        human    = self.human
        try:
            computer.exchange_resources(self._trade_offer,   self._trade_receive)
            human.exchange_resources(self._trade_receive, self._trade_offer)
            self._add_log(f"{computer.name} traded with {human.name}.", computer.color)
            self._build_player_texts()
            print(f"Trade completed: {computer.name} with {human.name}")
        except ValueError as e:
            print(f"Trade failed: {e}")
        finally:
            self._trade_pending         = False
            self._trade_offer           = {}
            self._trade_receive         = {}
            self._trade_computer_player = None
