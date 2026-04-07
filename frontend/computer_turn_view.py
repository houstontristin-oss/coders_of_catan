"""
Contains ComputerTurnView class 

Allows player when its 1 person versus 3 computer players so that the player can see the computer moves

Need to add AI player move log
play settlement, place road, place city all have examples of what I should do for the log implementation
Make a highlight of which computer AI is having their turn
I believe that to do down there states "Grey out these buttons once there are no more moves for computer player to make"
So I must have the "next move" button grey out when there are no more available moves for the AI to make on their turn
Indicating that the player must press skip turn.  Or even make a flag that changes the botton right button to next turn
when all moves are used up by the AI instead of having the "skip turn" button.  Since skip turn makes no sense
when you're at the end of the turn.
Ill look into the wrapping of the text in the log
"""
import arcade
import random

from .port_manager import PortManager

from backend.catan_board import CatanBoard

from .board_utils import cubic_to_pixel, node_to_pixel, get_hex_corners
from .drawing import fill_rect, outline_rect, draw_settlement, draw_road, draw_board, draw_city, draw_ocean_background
from .constants import *
from .view_constants import *

FAST_FORWARD = "Next Player"
NEXT_MOVE = "Next Move"
LOG_COLOR = (229,222,207)
GET_ROBBED = 7
NONE_PORT = 3
RES_PORT = 2
MARITIME_TRADE = 4

class ComputerTurnView(arcade.View):
    def __init__(self,
        vm,
        board,
        players,
        current_player,
        die1,
        die2,
        port_manager,
        shared_deck=None,):

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

        # --- Human Player ---
        self.human = self.players[0]
        for p in self.players:
            if not p.computer:
                self.human = p
                break

        # --- Computer Move Options ---
        self.moves = ['Trade', 'Build', 'DevCard']

        # --- Turn log state ---
        self._log_messages = []
        self._log_line_texts = []
        self._log_max_lines = 16

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
        self._road_card_sprite = arcade.Sprite(ROAD_CARD_SPRITE, scale=CARD_SCALE, center_y=ARMY_ROAD_SPRITE_Y1, center_x=ARMY_ROAD_SPRITE_X)
        self._army_card_sprite = arcade.Sprite(ARMY_CARD_SPRITE, scale=CARD_SCALE, center_y=ARMY_ROAD_SPRITE_Y2, center_x=ARMY_ROAD_SPRITE_X)
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

            fill_rect(left, bottom, CATAN_SUMMARY_BOX_W, CATAN_SUMMARY_BOX_H, CATAN_COLOR_SUMMARY_BG)
            outline_rect(left, bottom, CATAN_SUMMARY_BOX_W, CATAN_SUMMARY_BOX_H, player.color, 2)

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
        player = self.players[self.current_player]
        self.txt_log_title = arcade.Text(f"{player.name}'s Turn Log:", CATAN_PLAYER_PANEL_MARGIN + 5, 400, HUD_PANEL_BG, CATAN_TEXT_SIZE_RESOURCE, font_name="MedievalSharp",)
        self.txt_log = arcade.Text("", CATAN_PLAYER_PANEL_MARGIN + 5, 380, HUD_PANEL_BG, CATAN_TEXT_SIZE_RESOURCE, font_name="MedievalSharp", multiline=True, width=HUD_PANEL_WIDTH)

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
                  CATAN_BTN_PAD, CATAN_END_BTN_W, CATAN_BTN_H, BTN_ENDTURN if len(self.moves) != 0 else TEXT_LIGHT_GRAY)
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
    def _draw_cards(self):
        player = self.players[self.current_player]
        if self._army_card_sprite not in self._card_list and player.largest_army:
            self._army_card_sprite.center_y = ARMY_ROAD_SPRITE_Y1 if not player.longest_road else ARMY_ROAD_SPRITE_Y2
            self._card_list.append(self._army_card_sprite)
        if self._road_card_sprite not in self._card_list and player.longest_road:
            self._card_list.append(self._road_card_sprite)
        self._card_list.draw()

    # -----------------------------------------------------------------------
    # Log Scroll
    def _draw_log_reactangle(self):
        fill_rect(CATAN_PLAYER_PANEL_MARGIN, CARD_PAD, HUD_PANEL_WIDTH, 400, LOG_COLOR)
        outline_rect(CATAN_PLAYER_PANEL_MARGIN, CARD_PAD, HUD_PANEL_WIDTH, 400, HUD_PANEL_BG)
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
        self._draw_bottom_bar()
        self._draw_log_reactangle()
        self._draw_cards()
        self.txt_log.draw()

    # -----------------------------------------------------------------------
    # Mouse press
    def on_mouse_press(self, x, y, button, modifiers):
        # End Turn
        end_left = SCREEN_WIDTH - CATAN_BTN_PAD - CATAN_END_BTN_W
        if len(self.moves) != 0:
            # TODO: Grey out these buttons once there are no more moves for computer player to make
            if (end_left - CATAN_BTN_W <= x < end_left) and  (CATAN_BTN_PAD <= y <= CATAN_BTN_PAD + CATAN_BTN_H):
                self._make_move()

        if (end_left <= x <= end_left + CATAN_END_BTN_W) and (CATAN_BTN_PAD <= y <= CATAN_BTN_PAD + CATAN_BTN_H):
            self._fast_forward()
            self._end_turn()
            return

    # Make Move Function for computer to make a singular move
    def _make_move(self):
        move = self.moves.pop(0)
        player = self.players[self.current_player]
        move_success = False
        while not move_success and move is not None:
            if move == "Trade":
                needed_resources = self._no_resource_access()
                # NOTE: should be turned to a while once confirmed that trading works
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
                        self.txt_log.text += f"Used {port} to trade for {get_from_port}\n"
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
                        # ask for 1, 2, or 3 of a resource in return
                        amt_to_get = random.randint(1, 3)

                        to_trade = {res_to_trade: amt_to_offer}
                        to_get = {res_to_get: amt_to_get}
                        if player_to_trade_with and player_to_trade_with.can_afford_trade(to_get):
                            if player_to_trade_with == self.human:
                                # TODO (Nick): Show computer player pop up to confirm or deny
                                pass
                            else:
                                accept = random.randint(0,1)
                                if accept:
                                    player.exchange_resources(to_trade, to_get)
                                    player_to_trade_with.exchange_resources(to_get, to_trade)
                                    self.txt_log.text += f"{player.name} traded {to_trade} with {player_to_trade_with.name} for {to_get}\n"
                                    move_success = True
                    else:
                        to_trade = player.max_resource()
                        if player.resource_cards[to_trade] >= MARITIME_TRADE:
                            get_trade = player.min_resource()
                            player.exchange_resources({to_trade: MARITIME_TRADE}, {get_trade: 1})
                            self.txt_log.text += f"{player.name} completed a 4 {to_trade}: 1 {get_trade}\n"
                            move_success = True

            if move == "Build":
                #place a city
                city_node = player.best_city_location()
                if city_node is not None:
                    if player.can_afford_city():
                        self._place_city(city_node)
                        move_success = True
                #place a settlement
                settle_node = player.best_settlement_location()
                if settle_node is not None:
                    if player.can_afford_settlement():
                        self._place_settlement(settle_node)
                        move_success = True
                #place a road
                if player.can_afford_road():
                    road_edge = player.best_road_location()
                    if road_edge is not None:
                        self._place_road(road_edge)
                        move_success = True
                # buy a dev card because 
                if player.can_afford_dev_card():
                    self._buy_dev_card()
                    self.txt_log.text += f"{player.name} bought a Dev Card\n"
                    move_success = True

            if move == "DevCard":
                #TODO: make knight dev cards do something (Nick)
                #play a card first if computer has
                if len(player.development_cards) != 0:
                    card = random.choice(player.development_cards)
                    if card["just_bought"] == False:
                        player.development_cards.remove(card)
                        self.txt_log.text += f"Played a {card['type']} card\n"
                        move_success = True

            if not move_success:
                try:
                    move = self.moves.pop(0)
                except IndexError:
                    move = None
                    self.txt_log.text += f"{player.name} cannot make any more moves\n"

    # Fast Forward Function for computer to make many moves until either done or need human player input
    def _fast_forward(self):
        while len(self.moves) > 0:
            self._make_move()


    # -----------------------------------------------------------------------
    # Placement
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
        self.txt_log.text += f"{player.name} built a settlement\n"
        self._build_player_texts()
        print(f"{player.name} built a settlement! VP: {player.victory_points}")

    def _place_city(self, node):
        player = self.players[self.current_player]
        player.build_city(CatanBoard, node)
        node.building = "city"
        player.victory_points += 1
        self.txt_log.text += f"{player.name} upgraded to a city\n"
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
        self.txt_log.text += f"{player.name} built a road\n"
        self._build_player_texts()
        print(f"{player.name} built a road!")
        self._check_longest_road(edge)


    def _check_longest_road(self, edge):
        player = self.players[self.current_player]
        #check if player has longest road
        edge_lists = {edge.nodes[0]: [edge]}
        for node, edge_list in edge_lists.items():
            for e in edge_list:
                for node in e.nodes:
                    # do not keep searching if another player has a settlement on the node
                    if node.player == self.current_player or node.player is None:
                        paths = 0
                        for neighbor_edge in node.edges:
                            if neighbor_edge.player == self.current_player:
                                paths += 1
                        if paths == 3:
                            edge_lists[node] = edge_list.copy()
                            print(edge_lists)

                for node in e.nodes:
                    if node.player == self.current_player or node.player is None:
                        if node in edge_lists.keys():
                            if node.edges[0] not in edge_lists[node] and node.edges[0].player == self.current_player:
                                edge_lists[node].append(node.edges[0])
                            if node.edges[1] not in edge_lists[node] and node.edges[1].player == self.current_player:
                                edge_lists[node].append(node.edges[1])
                            if node.edges[2] not in edge_lists[edge.nodes[len(edge_lists.keys()) - 1]] and node.edges[2].player == self.current_player:
                                edge_lists[edge.nodes[len(edge_lists.keys()) - 1]].append(node.edges[2])
                        else:
                            for neighbor_edge in node.edges:
                                # check if the edge has been explored before and if the player owns another edge
                                if neighbor_edge not in edge_lists[edge.nodes[len(edge_lists.keys()) - 1]] and neighbor_edge is not e and neighbor_edge.player == self.current_player:
                                    edge_lists[edge.nodes[len(edge_lists.keys()) - 1]].append(neighbor_edge)
                print(edge_lists)

        for edge_list in edge_lists.values():
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

        if player.longest_road:
            self.txt_log.text += f"{player.name} built the Longest Road\n"


    def _place_road_free(self, edge):
        """Place a road using a free-road grant from Road Building card."""
        edge.player       = self.current_player
        self._free_roads -= 1
        self.players[self.current_player].total_roads -= 1
        self._build_player_texts()
        print(f"{self.players[self.current_player].name} placed a free road! ({self._free_roads} remaining)")
        self._check_longest_road(edge)


    # -----------------------------------------------------------------------
    # Buy Dev Card
    def _buy_dev_card(self):
        card_type = self._deck.pop()
        self.players[self.current_player].development_cards.append({"type": card_type, "just_bought": True})

        if card_type == "victory_point":
            self.players[self.current_player].victory_points += 1
    
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
        for tile in self.board.tiles.values():
            if tile.number == roll and not tile.robber:
                resource = RESOURCE_ABBR[tile.resource]
                for node in tile.nodes:
                    if node.player is not None:
                        player = self.players[node.player]
                        player.resource_cards[resource] += (
                            1 if node.building == "settlement" else 2
                        )


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
                        get_rid_of = random.randint(0, amount if amount < amt_to_discard else amt_to_discard)
                        amt_to_discard -= get_rid_of
                        giving_resources[resource] += get_rid_of
                while amt_to_discard > 0:
                    for resource, amount in player.resource_cards.items():
                        if amt_to_discard > 0:
                            get_rid_of = random.randint(0, amount - giving_resources[resource] if amount - giving_resources[resource] < amt_to_discard else amt_to_discard)
                            amt_to_discard -= get_rid_of
                            giving_resources[resource] += get_rid_of

                player.exchange_resources(giving_resources, {})
                print(f"ROBBER! {player.name} discarded {giving_resources}")

    # -----------------------------------------------------------------------
    # End turn
    def _end_turn(self):
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
        if self._free_roads < 0:
            self._free_roads = 0

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

        self._give_resources()

        if self.players[self.current_player].computer:
            self.vm.go_to(
                    "computer_turn",
                    board=self.board,
                    players=self.players,
                    current_player=self.current_player,
                    die1=self.die1,
                    die2=self.die2,
                    port_manager=self.port_manager,
            )
            return
        else:
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
        print(f"Turn ended. Now it's {self.players[self.current_player].name}'s turn. Rolled {self.die1 + self.die2}.")
