"""
Contains Robber Placement Class
"""
import arcade

from .drawing import draw_board, fill_rect, outline_rect
from .constants import*
from .board_utils import cubic_to_pixel, node_to_pixel
from .setup_view import draw_road, draw_settlement
from .view_constants import *

class RobberPlaceView(arcade.View):
    """
    RobberPlaceView Class
    """
    def __init__(self, board, players, current_player, die1, die2):
        super().__init__()
        self.board= board
        self.players = players
        self.current_player = current_player
        self.die1 = die1
        self.die2 = die2

        # Build tile states
        self.hovered_tile = None
        self.selected_tile = None
        self.show_confirm = False

        self._tile_pixel_cache = {}
        self._node_pixel_cache = {}
        self._edge_pixel_cache = {}

        self._build_node_pixel_cache()
        self._build_edge_pixel_cache()
        self._build_tile_pixel_cache()

        # --- Robber state ---
        self._robber_sprite = None
        self._robber_list = arcade.SpriteList()
        self._robber_sprite_ok = False
        self._robber_tile = None
        self._load_robber_sprite()

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
                if self._robber_sprite_ok:
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
        self._robber_tile.robber = False #switch current robber tile robber status to false
        tile.robber = True #switch new robber tile robber status to true
        self._robber_tile = tile
        self._place_robber_on_tile()
        self._cancel_build()
        print(f"{player.name} moved the robber!")
        from .catan_view import CatanView
        self.window.show_view(CatanView(self.board, self.players, self.current_player,
                                        self.die1, self.die2))


    def on_show_view(self):
        self._build_text_objects()

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

    def on_mouse_motion(self, x, y, dx, dy):
        if self.show_confirm:
            return

        self.hovered_tile = None

        for tile in self.board.tiles.values():
            px, py = self._tile_pixel_cache[tile.tile_id]
            if (x - px) ** 2 + (y - py) ** 2 <= (HEX_SIZE * 0.9) ** 2:
                self.hovered_tile = tile
                break

    def on_mouse_press(self, x, y, button, modifiers):
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