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
    ROBBER_SPRITE, BUILD_CITY, ONE, SIX
)


class CatanView(arcade.View):
    """
    CatanView Class
    """
    def __init__(self, board, players, current_player, die1, die2):
        super().__init__()
        self.board = board
        self.players = players
        # Track whose turn it is (index into PLAYERS list)
        self.current_player = current_player
        self.die1 = die1
        self.die2 = die2

        # Build mode state
        self.build_mode    = False
        self.build_choice  = BUILD_NONE
        self.hovered_node  = None
        self.hovered_edge  = None
        self.selected_node = None
        self.selected_edge = None
        self.show_confirm  = False

        # --- Robber state ---
        self._robber_sprite    = None
        self._robber_list      = arcade.SpriteList()
        self._robber_sprite_ok = False
        self._robber_tile      = None       # Tile the robber currently sits on
        self._load_robber_sprite()

        # --- Port hover state ---
        self._hovered_port_nodes = []       # list of (px,py) pixel coords to highlight

        # Pixel caches (populated after make_board)
        self._node_pixel_cache = {}
        self._edge_pixel_cache = {}
        self.port_manager = None   # built after pixel caches are ready

        # Load background
        self._load_background()

    #     # Load HUD icons and ship sprite
    # def on_show_view(self):
        # --- Pre-build all Text objects (avoids draw_text performance warning) ---
        self._build_text_objects()

        # --- Load resource icon sprites ---
        self._load_resource_icons()

        # Build the board (number tokens assigned inside)
        self._assign_number_tokens()

        # Build pixel caches
        self._build_node_pixel_cache()
        self._build_edge_pixel_cache()

        # Build port manager (randomizes port layout each game)
        self.port_manager = PortManager(self.board, self._edge_pixel_cache)

        # Build HUD text objects last (needs board to be ready)
        self._build_text_objects()

    # -----------------------------------------------------------------------
    # Robber sprite
    # -----------------------------------------------------------------------
    def _load_robber_sprite(self):
        """Load the robber sprite and park it on the desert tile at start."""
        try:
            self._robber_sprite    = arcade.Sprite(ROBBER_SPRITE)
            self._robber_list      = arcade.SpriteList()
            self._robber_list.append(self._robber_sprite)
            self._robber_sprite_ok = True
        except Exception:
            self._robber_sprite_ok = False
        self._place_robber_on_desert()

    def _place_robber_on_desert(self):
        """Find the desert tile and position the robber sprite over it."""
        from .board_utils import cubic_to_pixel
        for xyz, tile in self.board.tiles.items():
            if tile.resource == "desert":
                self._robber_tile = tile
                if self._robber_sprite_ok:
                    cx, _, cz = xyz
                    px, py    = cubic_to_pixel(cx, cz, HEX_SIZE,
                                               BOARD_CENTER_X, BOARD_CENTER_Y)
                    # Scale so the sprite fits inside the hex comfortably
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
        """Load the background image, or fall back to a solid color."""
        try:
            self.bg_sprite = arcade.Sprite(BACKGROUND_IMAGE)
            self.bg_sprite.center_x = SCREEN_WIDTH  / 2
            self.bg_sprite.center_y = SCREEN_HEIGHT / 2
            # Scale to fill the window exactly
            scale_x = SCREEN_WIDTH  / self.bg_sprite.width
            scale_y = SCREEN_HEIGHT / self.bg_sprite.height
            self.bg_sprite.scale = max(scale_x, scale_y)
            self.bg_list = arcade.SpriteList()
            self.bg_list.append(self.bg_sprite)
        except Exception:
            self.bg_sprite = None
            self.bg_list   = None
            arcade.set_background_color(arcade.color.OCEAN_BOAT_BLUE)

    # -----------------------------------------------------------------------
    # Number token assignment
    # -----------------------------------------------------------------------
    def _assign_number_tokens(self):
        """
        Assign the official Catan number pool to non-desert tiles.
        The pool is already shuffled in make_board() alongside resources,
        but we need to attach the numbers to tile objects here so the
        frontend can read them for rendering.

        Because make_board() already assigns tile.number (0 for desert,
        random draw for others), we just need to verify desert tiles have 0
        and all others have a valid number.  Nothing extra needed here —
        we read tile.number directly in on_draw().
        """
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
        # ---------------------------------------------------------------------------
        # New layout:
        #   Bottom-left  — vertical stack: Trade, Build, Play Card  (floating, no bar)
        #   Bottom-right — End Turn button (floating red pill)
        # ---------------------------------------------------------------------------
        _BW  = 120   # button width
        _BH  = 38    # button height
        _GAP = 8     # gap between stacked buttons
        _PAD = 14    # padding from screen edge

        # Bottom of the lowest button sits _PAD above the screen bottom
        # Stack order bottom-to-top: Trade, Build, Play Card
        trade_bottom = _PAD
        build_bottom = trade_bottom + _BH + _GAP
        card_bottom  = build_bottom + _BH + _GAP

        self.txt_trade = arcade.Text(
            "Trade",
            _PAD + _BW / 2, trade_bottom + _BH / 2,
            TEXT_WHITE, 12, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_build = arcade.Text(
            "Build",
            _PAD + _BW / 2, build_bottom + _BH / 2,
            TEXT_WHITE, 12, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_card = arcade.Text(
            "Play Card",
            _PAD + _BW / 2, card_bottom + _BH / 2,
            TEXT_WHITE, 12, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

        # End Turn — bottom-right corner
        _EW = 130
        self.txt_end = arcade.Text(
            "End Turn",
            SCREEN_WIDTH - _PAD - _EW / 2, _PAD + _BH / 2,
            TEXT_WHITE, 12, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )

        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - 10
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - 10
        self.txt_dice_label = arcade.Text(
            "Dice Roll",
            dx + DICE_AREA_WIDTH / 2, dy + DICE_AREA_HEIGHT - 16,
            TEXT_GOLD, 11, bold=True, anchor_x="center",
            font_name="MedievalSharp",
        )
        self.txt_dice_hint = arcade.Text(
            "Auto-rolls on turn start",
            dx + DICE_AREA_WIDTH / 2, dy + 7,
            TEXT_LIGHT_GRAY, 8, anchor_x="center",
            font_name="MedievalSharp",
        )

        # Build submenu labels (positions updated at draw time)
        self.txt_submenu_settlement = arcade.Text(
            "", 0, 0, TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_submenu_city = arcade.Text(
            "", 0, 0, TEXT_WHITE, 9, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_submenu_road = arcade.Text(
            "", 0, 0, TEXT_WHITE, 9, bold=True,
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
        self._build_dice_texts()

    def _build_dice_texts(self):
        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - 10
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - 10
        self.txt_die1 = arcade.Text(
            f"{self.die1}",
            dx + (DICE_AREA_WIDTH - 2*40 - 12) / 2 + 20, dy + 22 + 20,
            TEXT_WHITE, 18, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
        self.txt_die2 = arcade.Text(
            f"{self.die2}",
            dx + (DICE_AREA_WIDTH - 2*40 - 12) / 2 + 20 + 54, dy + 22 + 20,
            TEXT_WHITE, 18, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp",
        )
    def _build_player_texts(self):
        """
        Build/rebuild Text objects for the current player panel.
        Called on init and every time _end_turn() fires.
        """
        """Single-column player info panel."""
        player    = self.players[self.current_player]
        panel_x   = 8
        panel_top = SCREEN_HEIGHT - 8   # top of panel in screen coords
        row_h     = 24                  # vertical spacing per row

        # Name
        self.txt_player_name = arcade.Text(
            player.name,
            panel_x + HUD_PANEL_WIDTH // 2,
            panel_top - 18,
            TEXT_GOLD, 12, bold=True,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp"
        )
        # VP
        self.txt_player_vp = arcade.Text(
            f"Victory Points: {player.victory_points}",
            panel_x + HUD_PANEL_WIDTH // 2 + 10,
            panel_top - 18 - row_h,
            TEXT_LIGHT_GRAY, 10,
            anchor_x="center", anchor_y="center",
            font_name="MedievalSharp"
        )

        # Resources — single column, icon + "Label: N" per row
        order  = ["BRICK", "ORE", "WHEAT", "SHEEP", "WOOD"]
        labels = {"BRICK":"Brick","ORE":"Ore","WHEAT":"Wheat","SHEEP":"Sheep","WOOD":"Wood"}

        self.txt_resources = []
        for i, res in enumerate(order):
            ry = panel_top - 18 - row_h * 2 - i * (ICON_SIZE + 4) - ICON_SIZE // 2
            self.txt_resources.append(
                arcade.Text(
                    f"{labels[res]}: {player.resource_cards.get(res)}",
                    panel_x + ICON_SIZE + 35, ry,
                    TEXT_WHITE, 9,
                    anchor_y="center",
                    font_name="MedievalSharp"
                )
            )

    # -----------------------------------------------------------------------
    # Affordability
    # -----------------------------------------------------------------------
    def _can_afford(self, cost_dict):
        res = self.players[self.current_player].resource_cards
        return all(res.get(r, 0) >= amt for r, amt in cost_dict.items())

    # -----------------------------------------------------------------------
    # HUD draw helpers
    # -----------------------------------------------------------------------
    def _draw_bottom_bar(self):
        # No full-width bar — each button floats independently
        _BW  = 120
        _BH  = 38
        _GAP = 8
        _PAD = 14

        trade_bottom = _PAD
        build_bottom = trade_bottom + _BH + _GAP
        card_bottom  = build_bottom + _BH + _GAP

        build_col = BTN_BUILD_ACTIVE if self.build_mode else BTN_BUILD

        # Draw pill backgrounds with a thin dark shadow for legibility
        for bottom, color in [
            (trade_bottom, BTN_TRADE),
            (build_bottom, build_col),
            (card_bottom,  BTN_CARD),
        ]:
            # Subtle dark shadow
            fill_rect(_PAD + 2, bottom - 2, _BW, _BH, (0, 0, 0, 100))
            fill_rect(_PAD, bottom, _BW, _BH, color)
            outline_rect(_PAD, bottom, _BW, _BH, (255, 255, 255, 60), 1)

        # End Turn button — bottom-right
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

        _BW  = 120
        _BH  = 38
        _GAP = 8
        _PAD = 14
        _YDIFF = 36 # vertical offset to stack city and settlement buttons above road

        build_bottom = _PAD + _BH + _GAP   # bottom of the Build button
        build_top    = build_bottom + _BH   # top of the Build button

        menu_w = _BW
        menu_h = 120 # height to fit 3 buttons stacked with some gap
        bx     = _PAD
        by     = build_top + 4              # pop up just above Build button

        fill_rect(bx, by, menu_w, menu_h, HUD_PANEL_BG)
        outline_rect(bx, by, menu_w, menu_h, TEXT_GOLD, 2)

        c_col = (255, 102, 0) if self._can_afford(CITY_COST) else (70, 70, 70)
        fill_rect(bx + 8, by + (8 + (2*_YDIFF)), menu_w - 16, 28, c_col)
        self.txt_submenu_city.text = "City"
        self.txt_submenu_city.x    = bx + menu_w / 2
        self.txt_submenu_city.y    = by + (22 + (2*_YDIFF))
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
        """Slim single-column panel in top-left."""
        player  = self.players[self.current_player]
        panel_x = 8
        panel_y = SCREEN_HEIGHT - HUD_PANEL_HEIGHT - 8

        fill_rect(panel_x, panel_y, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, HUD_PANEL_BG)
        outline_rect(panel_x, panel_y, HUD_PANEL_WIDTH, HUD_PANEL_HEIGHT, player.color)

        # Color dot
        arcade.draw_circle_filled(panel_x + 14, panel_y + HUD_PANEL_HEIGHT - 18, 7, player.color)

        self.txt_player_name.draw()
        self.txt_player_vp.draw()

        # Resource icons + labels, single column
        order    = ["brick", "ore", "wheat", "sheep", "forest"]
        panel_top = SCREEN_HEIGHT - 8
        row_h     = 24

        for i, res in enumerate(order):
            ry = panel_top - 25 - row_h * 2 - i * (ICON_SIZE + 5)
            sprite = self.resource_icons[res]
            sprite.center_x = panel_x + ICON_SIZE // 2 + 4
            sprite.center_y = ry

        self.icon_sprite_list.draw()

        for txt in self.txt_resources:
            txt.draw()

    def _draw_dice_area(self):
        dx = SCREEN_WIDTH - DICE_AREA_WIDTH - 10
        dy = SCREEN_HEIGHT - DICE_AREA_HEIGHT - 10

        fill_rect(dx, dy, DICE_AREA_WIDTH, DICE_AREA_HEIGHT, HUD_PANEL_BG)
        outline_rect(dx, dy, DICE_AREA_WIDTH, DICE_AREA_HEIGHT, TEXT_LIGHT_GRAY)

        self.txt_dice_label.draw()
        self.txt_dice_hint.draw()

        die_size = 40
        die_gap  = 12
        die1_x   = dx + (DICE_AREA_WIDTH - 2*die_size - die_gap) / 2
        die_y    = dy + 20

        fill_rect(die1_x,                   die_y, die_size, die_size, (60,60,90))
        fill_rect(die1_x+die_size+die_gap,  die_y, die_size, die_size, (60,60,90))
        self.txt_die1.draw()
        self.txt_die2.draw()

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
            can    = self._can_afford(ROAD_COST)
            label  = "Build Road?"
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
        fill_rect(pop_left+8,          cy+8, 66, 30, btn_col)
        self.txt_popup_confirm.text = "Confirm" if can else "No Res."
        self.txt_popup_confirm.x    = pop_left + 41
        self.txt_popup_confirm.y    = cy + 23
        self.txt_popup_confirm.draw()

        fill_rect(pop_left+popup_w-74, cy+8, 66, 30, (180, 50, 50))
        self.txt_popup_cancel.x = pop_left + popup_w - 41
        self.txt_popup_cancel.y = cy + 23
        self.txt_popup_cancel.draw()

    # -----------------------------------------------------------------------
    # Port hover highlights
    # -----------------------------------------------------------------------
    def _draw_port_hover_highlights(self):
        """Glow the two nodes that belong to the currently-hovered port edge."""
        if not self._hovered_port_nodes:
            return
        for px, py in self._hovered_port_nodes:
            # Outer soft glow ring
            arcade.draw_circle_filled(px, py, 16, (255, 215, 0, 55))
            arcade.draw_circle_filled(px, py, 11, (255, 215, 0, 120))
            arcade.draw_circle_outline(px, py, 12, TEXT_GOLD, 2)

    # -----------------------------------------------------------------------
    # on_draw
    # -----------------------------------------------------------------------
    def on_draw(self):
        self.clear()

        # Background
        if self.bg_list:
            self.bg_list.draw()

        # Draw Board
        draw_board(self.board)

        # Ports drawn after tiles — ships sit on outer tile edges, labels clear outward
        self._draw_ports()

        # Ghost highlights
        if self.build_choice == BUILD_SETTLEMENT:
            self._draw_node_highlights()
        elif self.build_choice == BUILD_CITY:
            self._draw_city_highlights()
        elif self.build_choice == BUILD_ROAD:
            self._draw_edge_highlights()

        # Placed pieces
        self._draw_placed_pieces()

        # Robber — drawn on top of the desert tile (or wherever it's been moved)
        if self._robber_sprite_ok and self._robber_list:
            self._robber_list.draw()

        # Port node hover highlights
        self._draw_port_hover_highlights()

        # Confirmation popup
        if self.show_confirm:
            self._draw_confirm_popup()

        # HUD on top of everything
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
                d = math.hypot(x-npx, y-npy)
                if d < NODE_SNAP_RADIUS and d < closest_dist:
                    node = self.board.nodes[node_id]
                    if node.player is None:
                        closest, closest_dist = node, d
            self.hovered_node = closest
        elif self.build_choice == BUILD_CITY:
            closest, closest_dist = None, float("inf")
            for node_id, (npx, npy) in self._node_pixel_cache.items():
                d = math.hypot(x-npx, y-npy)
                if d < NODE_SNAP_RADIUS and d < closest_dist:
                    node = self.board.nodes[node_id]
                    if node.player == self.current_player:
                        closest, closest_dist = node, d
            self.hovered_node = closest
        elif self.build_choice == BUILD_ROAD:
            closest, closest_dist = None, float("inf")
            for edge_id, (mx, my, *_) in self._edge_pixel_cache.items():
                d = math.hypot(x-mx, y-my)
                if d < EDGE_SNAP_RADIUS and d < closest_dist:
                    edge = self.board.edges[edge_id]
                    if edge.player is None:
                        closest, closest_dist = edge, d
            self.hovered_edge = closest

        # --- Port hover: check if mouse is near any port ship/label ---
        self._hovered_port_nodes = []
        if self.port_manager:
            port_nodes = self.port_manager.get_hover_nodes(x, y)
            if port_nodes:
                self._hovered_port_nodes = [
                    self._node_pixel_cache[nid]
                    for nid in port_nodes
                    if nid in self._node_pixel_cache
                ]

    def on_mouse_press(self, x, y, button, modifiers):
        """
        Click handler — button layout matches new floating vertical stack.
        """
        _BW  = 120
        _BH  = 38
        _GAP = 8
        _PAD = 14
        _EW  = 130

        trade_bottom = _PAD
        build_bottom = trade_bottom + _BH + _GAP
        card_bottom  = build_bottom + _BH + _GAP

        # --- End Turn (bottom-right) ---
        end_left = SCREEN_WIDTH - _PAD - _EW
        if (end_left <= x <= end_left + _EW) and (_PAD <= y <= _PAD + _BH):
            self._end_turn()
            return

        # --- Build button ---
        if (_PAD <= x <= _PAD + _BW) and (build_bottom <= y <= build_bottom + _BH):
            if self.build_mode:
                self._cancel_build()
            else:
                self.build_mode   = True
                self.build_choice = BUILD_NONE
            return

        # --- Build submenu (pops up above the Build button) ---
        if self.build_mode and self.build_choice == BUILD_NONE:
            build_top = build_bottom + _BH
            by        = build_top + 4
            bx        = _PAD
            menu_w    = _BW
            # City row
            if (bx + 8 <= x <= bx + menu_w - 8) and (by + 80 <= y <= by + 108):
                if self._can_afford(CITY_COST):
                    self.build_choice = BUILD_CITY
                return
            # Settlement row
            if (bx + 8 <= x <= bx + menu_w - 8) and (by + 44 <= y <= by + 72):
                if self._can_afford(SETTLEMENT_COST):
                    self.build_choice = BUILD_SETTLEMENT
                return
            # Road row
            if (bx + 8 <= x <= bx + menu_w - 8) and (by + 8 <= y <= by + 36):
                if self._can_afford(ROAD_COST):
                    self.build_choice = BUILD_ROAD
                return

        # --- Confirmation popup ---
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

            if (pop_left+8 <= x <= pop_left+74) and (pcy+8 <= y <= pcy+38):
                if self.build_choice == BUILD_SETTLEMENT and self._can_afford(SETTLEMENT_COST):
                    self._place_settlement(self.selected_node)
                elif self.build_choice == BUILD_CITY and self._can_afford(CITY_COST):
                    self._place_city(self.selected_node)
                elif self.build_choice == BUILD_ROAD and self._can_afford(ROAD_COST):
                    self._place_road(self.selected_edge)
                return
            if (pop_left+popup_w-74 <= x <= pop_left+popup_w-8) and (pcy+8 <= y <= pcy+38):
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

        # --- Trade button ---
        if (_PAD <= x <= _PAD + _BW) and (trade_bottom <= y <= trade_bottom + _BH):
            self.window.show_view(TradeView(self.board, self.players, self.current_player, self.die1, self.die2))
            return

        # --- Play Card button ---
        if (_PAD <= x <= _PAD + _BW) and (card_bottom <= y <= card_bottom + _BH):
            self.window.show_view(PlayCardView(self.board, self.players, self.current_player, self.die1, self.die2))
            return
    # -----------------------------------------------------------------------
    # Placement
    # -----------------------------------------------------------------------
    def _place_settlement(self, node):
        player = self.players[self.current_player]
        player.build_settlement(CatanBoard, node)
        node.player = self.current_player
        node.building = "settlement"
        player.victory_points += 1
        self._cancel_build()
        self._build_player_texts()
        print(f"{player.name} built a settlement! Victory Points: {player.victory_points}")

       # player = PLAYERS[self.current_player]
       # for res, amt in SETTLEMENT_COST.items():
      #      player["resources"][res] -= amt
      #  node.player   = self.current_player
      #  node.building = "settlement"
       # player["vp"] += 1
       # self._cancel_build()
        #self._build_player_texts()
       # print(f"{player['name']} built a settlement! Victory Points: {player['vp']}")

    def _place_city(self, node):
        player = self.players[self.current_player]
        player.build_city(CatanBoard, node)
        node.building = "city"
        player.victory_points += 1
        self._cancel_build()
        self._build_player_texts()
        print(f"{player.name} upgraded to a city! Victory Points: {player.victory_points}")

       # player = PLAYERS[self.current_player]
       # for res, amt in CITY_COST.items():
       #     player["resources"][res] -= amt
       # node.building = "city"
       # player["vp"] += 1
       # self._cancel_build()
       # self._build_player_texts()
       # print(f"{player['name']} upgraded to a city! Victory Points: {player['vp']}")

    def _place_road(self, edge):
        player = self.players[self.current_player]
        idx = self.current_player
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
            self.show_confirm = False
            self.selected_edge = None
            return
        player.build_road(CatanBoard, edge)
        edge.player = self.current_player
        self._cancel_build()
        self._build_player_texts()
        print(f"{player.name} built a road!")

        #player = PLAYERS[self.current_player]
       # idx    = self.current_player
       # connected = False
       # for node in edge.nodes:
       #     if node.player == idx:
       #         connected = True
        #        break
        #    for neighbour_edge in node.edges:
        #        if neighbour_edge is not edge and neighbour_edge.player == idx:
         #           connected = True
         #           break
         #   if connected:
          #      break
       # if not connected:
           # print(f"{player['name']} — road must connect to your settlement or existing road.")
           # self.show_confirm  = False
           # self.selected_edge = None
           # return
      #  for res, amt in ROAD_COST.items():
          #  player["resources"][res] -= amt
       # edge.player = self.current_player
       # self._cancel_build()
       # self._build_player_texts()
       # print(f"{player['name']} built a road!")

    def _cancel_build(self):
        self.build_mode    = False
        self.build_choice  = BUILD_NONE
        self.hovered_node  = None
        self.hovered_edge  = None
        self.selected_node = None
        self.selected_edge = None
        self.show_confirm  = False

    def _give_resources(self):
        #Give players resources based on die1 and die2
        roll = self.die1 + self.die2
        for tile in self.board.tiles.values():
            if tile.number == roll:
                resource = RESOURCE_ABBR[tile.resource]
                for node in tile.nodes:
                    if node.player != None:
                        player = self.players[node.player]
                        player.resource_cards[resource] += 1

    def _end_turn(self):
        self.current_player = (self.current_player + 1) % len(self.players)
        self._cancel_build()

        # roll dice for next player
        self.die1 = random.randint(ONE, SIX)
        self.die2 = random.randint(ONE, SIX)
        #TODO: Check if roll is a 7
        self._give_resources()

        #build texts for next player
        self._build_player_texts()
        self._build_dice_texts()

        print(f"Turn ended. Now it's {self.players[self.current_player].name}'s turn.")
        if self.players[self.current_player].victory_points == 10:
            self.window.show_view(EndView(self.players, self.current_player))
