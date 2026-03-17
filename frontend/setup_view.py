"""
Contains SetupView Class
"""
import math
import random

import arcade

from backend.catan_board import CatanBoard
from .drawing import draw_board, draw_road, draw_settlement, fill_rect, outline_rect
from .board_utils import node_to_pixel
from .constants import (SCREEN_HEIGHT, SCREEN_WIDTH, HUD_BOTTOM_HEIGHT, HUD_PANEL_WIDTH,
DICE_AREA_WIDTH, BUILD_SETTLEMENT, BUILD_ROAD, TEXT_WHITE, TEXT_GOLD,EDGE_SNAP_RADIUS,
NODE_SNAP_RADIUS, RESOURCE_ABBR, ONE, SIX)

class SetupView(arcade.View):
    """
    SetupView Class
    """
    def __init__(self, board, players, current_player, cycle):
        super().__init__()
        self.board = board # CatanBoard instance
        self.players = players # list of Player instances
        self.current_player = current_player # index of current player in players list
        self.cycle = cycle # 1 for first round of placements, 2 for second round of placements
        self.last_placed_settlement = None # track last placed settlement for edge verification
        # during road placement in setup

        #Build node states
        self.build_choice  = BUILD_SETTLEMENT
        self.hovered_node  = None
        self.hovered_edge  = None
        self.selected_node = None
        self.selected_edge = None
        self.show_confirm  = False

        self._node_pixel_cache = {}
        self._edge_pixel_cache = {}
         # Build pixel caches
        self._build_node_pixel_cache()
        self._build_edge_pixel_cache()

        self._build_text_objects()

    def _build_text_objects(self):
        player = self.players[self.current_player]
        self.txt_title = arcade.Text(f"{player.name}: Place your Settlement", SCREEN_WIDTH / 4,
                                     SCREEN_HEIGHT - 50, font_name="MedievalSharp", font_size=30,
                                     color=player.color)
        # Confirm popup labels
        self.txt_popup_title   = arcade.Text("", 0, 0, TEXT_GOLD,  10, bold=True,
                                              anchor_x="center", anchor_y="center",
                                              font_name="MedievalSharp")
        self.txt_popup_confirm = arcade.Text("", 0, 0, TEXT_WHITE,  9, bold=True,
                                              anchor_x="center", anchor_y="center",
                                              font_name="MedievalSharp")
        self.txt_popup_cancel  = arcade.Text("Cancel", 0, 0, TEXT_WHITE, 9, bold=True,
                                              anchor_x="center", anchor_y="center",
                                              font_name="MedievalSharp")

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
    # Board pieces (always drawn)
    # -----------------------------------------------------------------------
    def _draw_placed_pieces(self):
        for edge_id, edge_obj in self.board.edges.items():
            if edge_obj.player is not None:
                _, _, x1, y1, x2, y2 = self._edge_pixel_cache[edge_id]
                draw_road(x1, y1, x2, y2, self.players[edge_obj.player].color)

        for node_id, node_obj in self.board.nodes.items():
            if node_obj.player is not None:
                npx, npy = self._node_pixel_cache[node_id]
                draw_settlement(npx, npy, 14, self.players[node_obj.player].color)

    # -----------------------------------------------------------------------
    # Ghost highlights
    # TODO: Make only valid settlement and road placements highlighted
    # NOTE: Currently if you place a road on a not valid spot during setup it will disappear and if
    # you place a settlement on a not valid spot it will violate the rules
    # -----------------------------------------------------------------------
    def _draw_node_highlights(self):
        player_color = self.players[self.current_player].color
        for node_id, node_obj in self.board.nodes.items():
            if not node_obj.is_valid_setup_placement():  # skip invalid nodes
                continue
            npx, npy = self._node_pixel_cache[node_id]
            if npy < HUD_BOTTOM_HEIGHT + 5:
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
            if not edge_obj.is_valid_setup_road_placement(self.last_placed_settlement):
                # skip invalid edges
                continue
            mx, my, x1, y1, x2, y2 = self._edge_pixel_cache[edge_id]
            if my < HUD_BOTTOM_HEIGHT + 5:
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
            label  = "Build Settlement?"
        elif self.build_choice == BUILD_ROAD and self.selected_edge:
            mx, my, *_ = self._edge_pixel_cache[self.selected_edge.edge_id]
            cx, cy = mx, my + 18
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

        btn_col = (39, 174, 96)
        fill_rect(pop_left+8,          cy+8, 66, 30, btn_col)
        self.txt_popup_confirm.text = "Confirm"
        self.txt_popup_confirm.x    = pop_left + 41
        self.txt_popup_confirm.y    = cy + 23
        self.txt_popup_confirm.draw()

        fill_rect(pop_left+popup_w-74, cy+8, 66, 30, (180, 50, 50))
        self.txt_popup_cancel.x = pop_left + popup_w - 41
        self.txt_popup_cancel.y = cy + 23
        self.txt_popup_cancel.draw()

    # -----------------------------------------------------------------------
    # Placement
    # -----------------------------------------------------------------------
    def _place_settlement(self, node):
        player = self.players[self.current_player]
        player.build_settlement_setup(CatanBoard, node)
        node.player = self.current_player
        node.building = "settlement"
        self.last_placed_settlement = node # can be used to verify correct road placement in setup
        player.victory_points += 1
        self._cancel_build()
        print(f"{player.name} built a settlement! Victory Points: {player.victory_points}")

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
        player.build_road_setup(CatanBoard, edge)
        edge.player = self.current_player
        self._cancel_build()
        print(f"{player.name} built a road!")

    def _cancel_build(self):
        self.build_choice  = BUILD_SETTLEMENT
        self.hovered_node  = None
        self.hovered_edge  = None
        self.selected_node = None
        self.selected_edge = None
        self.show_confirm  = False

    def on_draw(self):
        self.clear()
        # --- Draw the board ---
        draw_board(self.board)
        self.txt_title.draw()

        # Ghost highlights
        if self.build_choice == BUILD_SETTLEMENT:
            self._draw_node_highlights()
        elif self.build_choice == BUILD_ROAD:
            self._draw_edge_highlights()

        # Placed pieces
        self._draw_placed_pieces()

        # Confirmation popup
        if self.show_confirm:
            self._draw_confirm_popup()

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
                    if node.player is None and node.is_valid_setup_placement():
                        closest, closest_dist = node, d
            self.hovered_node = closest
        elif self.build_choice == BUILD_ROAD:
            closest, closest_dist = None, float("inf")
            for edge_id, (mx, my, *_) in self._edge_pixel_cache.items():
                d = math.hypot(x-mx, y-my)
                if d < EDGE_SNAP_RADIUS and d < closest_dist:
                    edge = self.board.edges[edge_id]
                    if (edge.player is None and
                    edge.is_valid_setup_road_placement(self.last_placed_settlement)):
                        closest, closest_dist = edge, d
            self.hovered_edge = closest

    def on_mouse_press(self, x, y, button, modifiers):
        # Confirmation popup for players placing their settlements and roads in a cycle
        if self.show_confirm:
            if self.build_choice == BUILD_SETTLEMENT and self.selected_node:
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
                if self.build_choice == BUILD_SETTLEMENT:
                    if self.cycle == 2: # distribute resources for second settlement placements
                        for tile in self.selected_node.tiles:
                            if tile.resource != 'desert':
                                resource = RESOURCE_ABBR[tile.resource]
                                self.players[self.current_player].resource_cards[resource.upper()] += 1
                    self._place_settlement(self.selected_node)
                    self.build_choice = BUILD_ROAD
                    self.txt_title.text = (f"{self.players[self.current_player].name}: " +
                                            "Place your Road")
                elif self.build_choice == BUILD_ROAD:
                    self._place_road(self.selected_edge)
                    if self.current_player == 3 and self.cycle == 1:
                        self.cycle = 2
                    elif self.cycle == 1:
                        self.current_player += 1
                    elif self.cycle == 2 and self.current_player > 0:
                        self.current_player -= 1
                    elif self.cycle == 2 and self.current_player == 0:
                        from .catan_view import CatanView
                        #setup dice for first player
                        die1 = random.randint(ONE, SIX)
                        die2 = random.randint(ONE, SIX)
                        #give resources
                        roll = die1 + die2
                        for tile in self.board.tiles.values():
                            if tile.number == roll:
                                resource = RESOURCE_ABBR[tile.resource]
                                for node in tile.nodes:
                                    if node.player != None:
                                        player = self.players[node.player]
                                        player.resource_cards[resource] += 1
                                        
                        self.window.show_view(CatanView(self.board, self.players, 0, die1, die2))
                        return

                    self.window.show_view(SetupView(self.board, self.players, 
                                                    self.current_player, self.cycle))
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
        if self.build_choice == BUILD_ROAD and self.hovered_edge:
            self.selected_edge = self.hovered_edge
            self.show_confirm  = True
            return
