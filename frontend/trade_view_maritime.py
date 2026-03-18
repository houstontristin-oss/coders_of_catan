"""
Contains TradeView Class
"""
import arcade
from .drawing import fill_rect
from .constants import *

BTN_W = 150
BTN_H = 50
TRADE_BTN_LEFT = SCREEN_WIDTH - (BTN_W * 2) - 30
TRADE_BTN_TXT = SCREEN_WIDTH - (BTN_W * 2) + 42
TRADE_BTN_BOTTOM = (HUD_BOTTOM_HEIGHT - BTN_H) / 2

class TradeViewMaritime(arcade.View):
    """
    TradeViewMaritime Class
    """
    def __init__(self, board, players, current_player):
        super().__init__()
        self.board= board
        self.players = players
        self.current_player = current_player
    
    def _build_text_objects(self):
        bar_center_y = HUD_BOTTOM_HEIGHT / 2
        TITLE_FONT_SIZE = 30
        # Setup Texts
        self.txt_title = arcade.Text("Maritime Trade", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 25, TEXT_WHITE, bold=True, font_name="MedievalSharp", anchor_x="center", anchor_y="center", font_size=TITLE_FONT_SIZE)

        self.txt_back = arcade.Text("Back to Board",  SCREEN_WIDTH - BTN_W * 0.5 - 20, bar_center_y, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")

        BRICK_TRADE_NUM_X = 128
        SHEEP_TRADE_NUM_X = 128 + 256 *3
        ORE_TRADE_NUM_X = 128 + 256
        WHEAT_TRADE_NUM_X = 128 + 256*2
        WOOD_TRADE_NUM_X = 128 + 256* 4

        TRADE_NUM_Y = 625
        FONT_SIZE_TRADE_NUM = 20
        # Texts for resource counts
        self.txt_sheep = arcade.Text(f"Sheep: {self.players[self.current_player].resource_cards["SHEEP"]}", SHEEP_TRADE_NUM_X, TRADE_NUM_Y, TEXT_GOLD, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp", font_size=FONT_SIZE_TRADE_NUM)
        self.txt_brick = arcade.Text(f"Brick: {self.players[self.current_player].resource_cards["BRICK"]}", BRICK_TRADE_NUM_X, TRADE_NUM_Y, TEXT_GOLD, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp", font_size=FONT_SIZE_TRADE_NUM)
        self.txt_ore = arcade.Text(f"Ore: {self.players[self.current_player].resource_cards["ORE"]}", ORE_TRADE_NUM_X, TRADE_NUM_Y, TEXT_GOLD, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp", font_size=FONT_SIZE_TRADE_NUM)
        self.txt_wheat = arcade.Text(f"Wheat: {self.players[self.current_player].resource_cards["WHEAT"]}", WHEAT_TRADE_NUM_X, TRADE_NUM_Y, TEXT_GOLD, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp", font_size=FONT_SIZE_TRADE_NUM)
        self.txt_wood = arcade.Text(f"Wood: {self.players[self.current_player].resource_cards["WOOD"]}", WOOD_TRADE_NUM_X, TRADE_NUM_Y, TEXT_GOLD, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp", font_size=FONT_SIZE_TRADE_NUM)


        # Button Texts
        self.txt_trade = arcade.Text("Accept Trade", TRADE_BTN_TXT , bar_center_y, TEXT_WHITE, bold=True, anchor_y="center", anchor_x="center", font_name="MedievalSharp")

    # -----------------------------------------------------------------------
    # Sprites
    # -----------------------------------------------------------------------
    def _load_resource_icons(self):
        self.offer_resource_icons   = {}
        self.offer_icon_sprite_list = arcade.SpriteList()
        for res in ["brick", "ore", "wheat", "sheep", "forest"]:
            sprite = arcade.Sprite(RESOURCE_SPRITES[res], scale=SPRITE_SCALE * 10)
            self.offer_resource_icons[res] = sprite
            self.offer_icon_sprite_list.append(sprite)

        self.get_resource_icons   = {}
        self.get_icon_sprite_list = arcade.SpriteList()
        for res in ["brick", "ore", "wheat", "sheep", "forest"]:
            sprite = arcade.Sprite(RESOURCE_SPRITES[res], scale=SPRITE_SCALE * 10)
            self.get_resource_icons[res] = sprite
            self.get_icon_sprite_list.append(sprite)

    def _draw_bottom_bar(self):
        fill_rect(0, 0, SCREEN_WIDTH, HUD_BOTTOM_HEIGHT, HUD_BG)

        btn_w, btn_h = 150, 50
        btn_bottom = (HUD_BOTTOM_HEIGHT - btn_h) / 2

        fill_rect(SCREEN_WIDTH - btn_w - 20, btn_bottom, btn_w, btn_h, BTN_ENDTURN)
        self.txt_back.draw()

    def _draw_trade_buttons(self):
        #4:1 Trade button
        fill_rect(TRADE_BTN_LEFT, TRADE_BTN_BOTTOM, BTN_W, BTN_H, BTN_BUILD)
        self.txt_trade.draw()


    def _draw_resource_numbers(self):
        self.txt_sheep.draw()
        self.txt_ore.draw()
        self.txt_wheat.draw()
        self.txt_wood.draw()
        self.txt_brick.draw()

    def on_show_view(self):
        self._build_text_objects()
        self._load_resource_icons()

    def on_draw(self):
        self.clear()
        self.txt_title.draw()

        TRADE_RES_SPACING_X = 256
        TRADE_RES_START_X = 128
        spacing_x = TRADE_RES_START_X
        OFFER_TRADE_RES_SPACING_Y = 500
        for sprite in self.offer_resource_icons.values():
            sprite.center_x = spacing_x
            sprite.center_y = OFFER_TRADE_RES_SPACING_Y
            spacing_x += TRADE_RES_SPACING_X

        GET_TRADE_RES_SPACING_Y = 250
        spacing_x = TRADE_RES_START_X
        for sprite in self.get_resource_icons.values():
            sprite.center_x = spacing_x
            sprite.center_y = GET_TRADE_RES_SPACING_Y
            spacing_x += TRADE_RES_SPACING_X

        self.offer_icon_sprite_list.draw()
        self.get_icon_sprite_list.draw()

        self._draw_resource_numbers()
        self._draw_bottom_bar()
        self._draw_trade_buttons()
        
    def on_mouse_press(self, x, y, button, modifiers):
        if (SCREEN_WIDTH - BTN_W - 20 <= x <= SCREEN_WIDTH - 20) and (y <= HUD_BOTTOM_HEIGHT):
            from .catan_view import CatanView
            self.window.show_view(CatanView(self.board, self.players, self.current_player))

        if(TRADE_BTN_LEFT <= x <= TRADE_BTN_LEFT + BTN_W) and (y <= HUD_BOTTOM_HEIGHT):
            #TEMPORARY
            print("BUTTON CLICKED")
