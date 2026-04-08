"""
Contains Robber Placement Class
"""
import random
import arcade

from .drawing import draw_board, fill_rect, outline_rect
from .constants import (SCREEN_WIDTH, SCREEN_HEIGHT, TEXT_GOLD, TEXT_WHITE,
                        HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y, ROBBER_SPRITE,
                        HUD_PANEL_WIDTH, DICE_AREA_WIDTH)
from .board_utils import cubic_to_pixel, node_to_pixel
from .setup_view import draw_road, draw_settlement
from .view_constants import (CATAN_ROBBER_SCALE_MULT, CATAN_BOARD_TOP_CULL_Y,
                             CATAN_HUD_LEFT_BLOCK_PAD, CATAN_HIGHLIGHT_RADIUS_HOVER,
                             CATAN_HIGHLIGHT_RADIUS_OUTLINE, CATAN_DICE_RIGHT_BLOCK_PAD)

class RobberPlaceView(arcade.View):
    """
    RobberPlaceView Class
    """
    def __init__(self, vm, board, players, current_player, die1, die2, port_manager):
        super().__init__()
        self.vm             = vm
        self.board          = board
        self.players        = players
        self.current_player = current_player
        self.die1           = die1
        self.die2           = die2
        self.port_manager   = port_manager

        # Build tile states
        self.hovered_tile   = None
        self.selected_tile  = None
        self.show_confirm   = False
        self.hovered_node   = None

        self._tile_pixel_cache = {}
        self._node_pixel_cache = {}
        self._edge_pixel_cache = {}

        self._build_node_pixel_cache()
        self._build_edge_pixel_cache()
        self._build_tile_pixel_cache()

        # --- Robber state ---
        self._robber_sprite     = None
        self._robber_list       = arcade.SpriteList()
        self._robber_sprite_ok  = False
        self._robber_tile       = None
        self._load_robber_sprite()

        # --- Theft state ---
        self.thief_mode     = False
        self.vic_players    = []
        self.show_vic       = False

    def _build_text_objects(self):
        player = self.players[self.current_player]
        self.txt_title = arcade.Text(f"{player.name}: Place the Robber", SCREEN_WIDTH / 3,
                                     SCREEN_HEIGHT - 50, font_name="MedievalSharp", font_size=30,
                                     color=player.color)
        # Confirm popup labels
        self.txt_popup_title = arcade.Text("", 0, 0, TEXT_GOLD, 10, bold=True,
                                           anchor_x="center", anchor_y="center",
                                           font_name="MedievalSharp")
        self.txt_popup_confirm = arcade.Text("", 0, 0, TEXT_WHITE, 9, bold=True,
                                             anchor_x="center", anchor_y="center",
                                             font_name="MedievalSharp")
        self.txt_popup_rob = arcade.Text("", 0, 0, TEXT_WHITE, 9, bold=True,
                                             anchor_x="center", anchor_y="center",
                                             font_name="MedievalSharp")

        self.txt_popup_cancel = arcade.Text("Cancel", 0, 0, TEXT_WHITE, 9, bold=True,
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

    def _build_tile_pixel_cache(self): #ask Tristan/Amanda about this
        for xyz, tile in self.board.tiles.items():
            cx, _, cz = xyz
            px, py = cubic_to_pixel(cx, cz, HEX_SIZE, BOARD_CENTER_X, BOARD_CENTER_Y)
            self._tile_pixel_cache[tile.tile_id] = (px, py)

    def _cancel_build(self):
        self.hovered_tile  = None
        self.selected_tile = None
        self.show_confirm  = False

    # -----------------------------------------------------------------------
    # Confirmation popup
    # -----------------------------------------------------------------------
    def _draw_confirm_popup(self):
        if not self.show_confirm:
            return
        if self.selected_tile:
            cx, cy = self._tile_pixel_cache[self.selected_tile.tile_id]
            cy += 18
            label = "Place Robber?"
        else:
            return

        popup_w = 160
        popup_h = 70
        pop_left = cx - popup_w / 2

        fill_rect(pop_left, cy, popup_w, popup_h, (20, 20, 40, 220))
        outline_rect(pop_left, cy, popup_w, popup_h, TEXT_GOLD, 2)
        self.txt_popup_title.text = label
        self.txt_popup_title.x = cx
        self.txt_popup_title.y = cy + popup_h - 14
        self.txt_popup_title.draw()

        btn_col = (39, 174, 96)
        fill_rect(pop_left + 8, cy + 8, 66, 30, btn_col)
        self.txt_popup_confirm.text = "Confirm"
        self.txt_popup_confirm.x = pop_left + 41
        self.txt_popup_confirm.y = cy + 23
        self.txt_popup_confirm.draw()

        fill_rect(pop_left + popup_w - 74, cy + 8, 66, 30, (180, 50, 50))
        self.txt_popup_cancel.x = pop_left + popup_w - 41
        self.txt_popup_cancel.y = cy + 23
        self.txt_popup_cancel.draw()

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

    def _place_robber(self, tile):
        player = self.players[self.current_player]
        for tile_r in self.board.tiles.values(): #defining current robber tile
            if tile_r.robber:
                self._robber_tile = tile_r
        if tile == self._robber_tile: #if player picks current robber tile
            print(f"{player.name} — must place robber on new tile.")
            #self.txt_title.text = (f"{player.name} — must place robber on new tile.")
            #self.txt_title.draw()
            self.show_confirm = False
            self.selected_tile = None
            return
        if self._robber_tile:
            self._robber_tile.robber = False #switch current robber tile robber status to false
        tile.robber = True #switch new robber tile robber status to true
        self._robber_tile = tile
        self._place_robber_on_tile()
        self._cancel_build()
        print(f"{player.name} moved the robber!")

        self.vic_players = self._get_victims(tile)

        if self.vic_players:
            self.thief_mode = True
            self.show_vic = True
            self.hovered_tile = None
        else:
            print("No victims found.")
            self._end_robber()

    def _computer_move_robber(self):
        best_tiles = {}
        max_player_count = 0
        robber_tile = None
        # Find the tile with the most players surrounding it
        for tile in self.board.tiles.values():
            if tile.robber:
                robber_tile = tile
            elif not tile.robber:
                player_count = 0
                for node in tile.nodes:
                    if node.player is not None and node.player != self.current_player:
                        player_count += 1
                    if node.building == "city":
                        player_count += 1
                if player_count > max_player_count:
                    max_player_count = player_count
                    best_tiles[tile] = tile.number
        # Account for if the tile number is better than another
        new_robber_tiles = []
        for tile, info in best_tiles.items():
            if info >= 5 and info <= 9:
                new_robber_tiles.append(tile)
        if len(new_robber_tiles) == 0:
            new_robber_tile = random.choice(list(best_tiles.keys()))
        else:
            new_robber_tile = random.choice(new_robber_tiles)

        # Move the robber to new_robber_tile
        if robber_tile is not None:
            robber_tile.robber = False
        new_robber_tile.robber = True

        # Steal from a player that on new_robber_tile
        to_steal_from = []
        for node in new_robber_tile.nodes:
            if node.player is not None:
                to_steal_from.append(node.player)
        to_steal_from = random.choice(to_steal_from)

        total_res = self.players[to_steal_from].get_total_resources()
        if total_res != 0:
            choice = random.randint(1, total_res)
            res_choice = None
            for res, amount in self.players[to_steal_from].resource_cards.items():
                if choice > amount:
                    choice -= amount
                else:
                    res_choice = res

            if res_choice is not None:
                self.players[to_steal_from].resource_cards[res_choice] -= 1
                self.players[self.current_player].resource_cards[res_choice] += 1


    # -----------------------------------------------------------------------
    # Theft function
    # -----------------------------------------------------------------------

    def _get_victims(self, tile):
        victim_list = set() #make sure a player isn't listed twice

        for node_id, node_obj in self.board.nodes.items():
            if tile in node_obj.tiles and node_obj.player is not None:
                if node_obj.player != self.current_player:
                    vic = self.players[node_obj.player]

                    if sum(vic.resource_cards.values()) > 0: #only rob people with cards
                        victim_list.add(node_obj.player)

        return victim_list

    def _rob_victim(self, victim_id):
        victim = self.players[victim_id]
        current = self.players[self.current_player]

        print(victim.resource_cards)
        print(current.resource_cards)

        total_res = sum(victim.resource_cards.values())

        if total_res == 0:
            print(f"{victim.name} has no resources.")

        choice = random.randint(1, total_res)

        total = 0
        for res, count in victim.resource_cards.items():
            total += count
            if choice <= total:
                stolen = res
                break

        victim.resource_cards[stolen] -= 1
        current.resource_cards[stolen] += 1
        print(f"{current.name} stole 1 {stolen} from {victim.name}")

        print(victim.resource_cards)
        print(current.resource_cards)

        self.show_vic = False
        self.thief_mode = False
        self._end_robber()


    def _end_robber(self):
        self.vm.go_to("catan",
            board=self.board, players=self.players, current_player=self.current_player,
            die1=self.die1, die2=self.die2, port_manager=self.port_manager, start_of_turn=True
        )

    def _draw_vic_popup(self):
        if not self.show_vic:
            return

        cx = SCREEN_WIDTH / 2
        cy = SCREEN_HEIGHT / 2

        popup_w = 220
        popup_h = 60 + 40 * len(self.vic_players)

        left = cx - popup_w / 2

        fill_rect(left, cy, popup_w, popup_h, (20,20,40,230))
        outline_rect(left, cy, popup_w, popup_h, TEXT_GOLD, 2)

        #Title
        self.txt_popup_rob.text = "Choose a player to rob"
        self.txt_popup_rob.font_size = 14
        self.txt_popup_rob.color = TEXT_GOLD
        self.txt_popup_rob.x = cx
        self.txt_popup_rob.y = cy + popup_h - 20
        self.txt_popup_rob.draw()

        #Buttons
        self.vic_buttons = []

        for i, vic in enumerate(self.vic_players):
            player = self.players[vic]

            bx = left + 20
            by = cy + popup_h - 70 - i * 40
            bw = popup_w - 40
            bh = 30

            fill_rect(bx, by, bw, bh, player.color)
            self.txt_popup_rob.text = player.name
            self.txt_popup_rob.font_size = 12
            self.txt_popup_rob.color = TEXT_WHITE
            self.txt_popup_rob.x = bx + bw / 2
            self.txt_popup_rob.y = by + 15
            self.txt_popup_rob.draw()

            self.vic_buttons.append((vic, bx, by, bw, bh))

    def on_show_view(self):
        self._build_text_objects()
        if self.players[self.current_player].computer:
            # computer moves the robber
            self._computer_move_robber()
            self.vm.go_to("computer_turn", board=self.board, players=self.players,
                          current_player=self.current_player, die1=self.die1,
                          die2=self.die2, port_manager=self.port_manager)
            return

    def on_draw(self):
        self.clear()

        # --- Draw the board ---
        draw_board(self.board)

        self.txt_title.draw()

        if self._robber_sprite_ok and self._robber_list:
            self._robber_list.draw()

        self._draw_placed_pieces()
        # Confirmation popup
        if self.show_confirm:
            self._draw_confirm_popup()

        if self.show_vic:
            self._draw_vic_popup()

        self._draw_robber_settle_highlights()

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

    def _draw_robber_settle_highlights(self):
        if self.thief_mode:
            return

        if not self.hovered_tile: #only highlight nodes on hovered tile
            return

        for node_id, node_obj in self.board.nodes.items():
            if self.hovered_tile not in node_obj.tiles:
                continue
            if node_obj.player is None: #only highlight occupied nodes
                continue

            npx, npy = self._node_pixel_cache[node_id]

            if npy < CATAN_BOARD_TOP_CULL_Y:
                continue
            if (npx < HUD_PANEL_WIDTH + CATAN_HUD_LEFT_BLOCK_PAD
                    or npx > SCREEN_WIDTH - DICE_AREA_WIDTH - CATAN_DICE_RIGHT_BLOCK_PAD):
                continue

            player_color = self.players[node_obj.player].color

            arcade.draw_circle_filled(npx, npy, CATAN_HIGHLIGHT_RADIUS_HOVER,
                                      (*player_color, 60))
            arcade.draw_circle_outline(npx, npy, CATAN_HIGHLIGHT_RADIUS_OUTLINE,
                                       (*player_color, 120), 3)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.show_confirm or self.show_vic:
            self.hovered_tile = None
            return

        self.hovered_tile = None

        for tile in self.board.tiles.values():
            px, py = self._tile_pixel_cache[tile.tile_id]
            if (x - px) ** 2 + (y - py) ** 2 <= (HEX_SIZE * 0.9) ** 2:
                self.hovered_tile = tile
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if self.show_vic:
            for vic, bx, by, bw, bh in self.vic_buttons:
                if bx <= x <= bx + bw and by <= y <= by + bh:
                    self._rob_victim(vic)
                    return
        # Confirmation popup for placing robber
        if self.show_confirm:
            if self.selected_tile:
                pcx, pcy = self._tile_pixel_cache[self.selected_tile.tile_id]
                pcy += 18
            else:
                self.show_confirm = False
                return

            popup_w = 160
            pop_left = pcx - popup_w / 2

            if (pop_left + 8 <= x <= pop_left + 74) and (pcy + 8 <= y <= pcy + 38):
                self._place_robber(self.selected_tile)
                self.txt_title.text = (f"{self.players[self.current_player].name}: " +
                                       "Place the Robber")

            if (pop_left+popup_w-74 <= x <= pop_left+popup_w-8) and (pcy+8 <= y <= pcy+38):
                self.selected_tile = None
                self.show_confirm  = False
                return
            self.selected_tile = None
            self.show_confirm  = False
            return

        if  self.hovered_tile:
            if self.hovered_tile == self._robber_tile:
                player = self.players[self.current_player]
                print(f"{player.name} — must place robber on a new tile.")
                return #can't pick same tile
            self.selected_tile = self.hovered_tile
            self.show_confirm  = True
            return
