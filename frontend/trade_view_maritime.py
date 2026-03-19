"""
Contains TradeView Class
"""
import arcade
from .drawing import fill_rect, outline_rect
from .constants import *

TITLE_FONT_SIZE = 30

BTN_W = 150
BTN_H = 50
TRADE_BTN_LEFT = SCREEN_WIDTH - (BTN_W * 2) - 30
TRADE_BTN_TXT = SCREEN_WIDTH - (BTN_W * 2) + 42
TRADE_BTN_BOTTOM = (HUD_BOTTOM_HEIGHT - BTN_H) / 2

TRADE_SPRITE_SCALE = SPRITE_SCALE * 10
TRADE_SPRITE_W = 220
HALF = TRADE_SPRITE_W / 2

BRICK_TRADE_NUM_X = 128
SHEEP_TRADE_NUM_X = 128 + 256 *3
ORE_TRADE_NUM_X = 128 + 256
WHEAT_TRADE_NUM_X = 128 + 256*2
WOOD_TRADE_NUM_X = 128 + 256* 4

TRADE_NUM_Y = 625
FONT_SIZE_TRADE_NUM = 20

TRADE_RES_SPACING_X = 256
TRADE_RES_START_X = 128
OFFER_TRADE_RES_SPACING_Y = 500
GET_TRADE_RES_SPACING_Y = 250

class TradeViewMaritime(arcade.View):
    """
    TradeViewMaritime Class
    """
    def __init__(self, board, players, current_player):
        super().__init__()
        self.board= board
        self.players = players
        self.current_player = current_player

        self.offer_highlights = {}
        self.get_highlights = {}

        self.offer_selected = {}
        self.get_selected = {}

        self.trade_success = False
        self.valid_trade = False

    def _build_text_objects(self):
        bar_center_y = HUD_BOTTOM_HEIGHT / 2
        
        # Setup Texts
        self.txt_title = arcade.Text("Maritime Trade", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 25, TEXT_WHITE, bold=True, font_name="MedievalSharp", anchor_x="center", anchor_y="center", font_size=TITLE_FONT_SIZE)

        self.txt_back = arcade.Text("Back to Board",  SCREEN_WIDTH - BTN_W * 0.5 - 20, bar_center_y, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")

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
        for lower_res, upper_res in RESOURCE_ABBR.items():
            sprite = arcade.Sprite(RESOURCE_SPRITES[lower_res], scale=TRADE_SPRITE_SCALE)
            self.offer_resource_icons[upper_res] = sprite
            self.offer_icon_sprite_list.append(sprite)

        self.get_resource_icons   = {}
        self.get_icon_sprite_list = arcade.SpriteList()
        for lower_res, upper_res in RESOURCE_ABBR.items():
            sprite = arcade.Sprite(RESOURCE_SPRITES[lower_res], scale=TRADE_SPRITE_SCALE)
            self.get_resource_icons[upper_res] = sprite
            self.get_icon_sprite_list.append(sprite)

    def _draw_bottom_bar(self):
        fill_rect(0, 0, SCREEN_WIDTH, HUD_BOTTOM_HEIGHT, HUD_BG)

        btn_w, btn_h = 150, 50
        btn_bottom = (HUD_BOTTOM_HEIGHT - btn_h) / 2

        fill_rect(SCREEN_WIDTH - btn_w - 20, btn_bottom, btn_w, btn_h, BTN_ENDTURN)
        self.txt_back.draw()

    def _draw_trade_buttons(self):
        #4:1 Trade button
        fill_rect(TRADE_BTN_LEFT, TRADE_BTN_BOTTOM, BTN_W, BTN_H, BTN_BUILD  if self.valid_trade else TEXT_LIGHT_GRAY)
        self.txt_trade.draw()

    def _draw_resource_numbers(self):
        self.txt_sheep.draw()
        self.txt_ore.draw()
        self.txt_wheat.draw()
        self.txt_wood.draw()
        self.txt_brick.draw()

    def _check_valid_trade(self):
        valid_offer = False
        valid_get = False

        # Make sure the player has enough resources to make the trade
        for res, selected in self.offer_selected.items():
            if selected:
                valid_offer = self.players[self.current_player].can_afford_trade({res: 4}) 

        # Make sure a selection has been made on the bottom row
        for res, selected in self.get_selected.items():
            if selected:
                valid_get = True

        self.valid_trade = valid_offer and valid_get

    def on_show_view(self):
        self._build_text_objects()
        self._load_resource_icons()

    def on_draw(self):
        self.clear()
        self.txt_title.draw()
        # Draw top row in correct spots
        spacing_x = TRADE_RES_START_X
        for sprite in self.offer_resource_icons.values():
            sprite.center_x = spacing_x
            sprite.center_y = OFFER_TRADE_RES_SPACING_Y
            spacing_x += TRADE_RES_SPACING_X

        # Draw bottom row in correct spots
        spacing_x = TRADE_RES_START_X
        for sprite in self.get_resource_icons.values():
            sprite.center_x = spacing_x
            sprite.center_y = GET_TRADE_RES_SPACING_Y
            spacing_x += TRADE_RES_SPACING_X

        self.offer_icon_sprite_list.draw()
        self.get_icon_sprite_list.draw()

        # Highlights for first row (Resource to offer up)
        for res, highlight in self.offer_highlights.items():
            if highlight:
                sprite = self.offer_resource_icons[res]
                outline_rect(sprite.center_x - HALF, sprite.center_y - HALF, TRADE_SPRITE_W, TRADE_SPRITE_W, TEXT_GOLD, 2)

        # Higlights for Second row (Resource to get)
        for res, highlight in self.get_highlights.items():
            if highlight:
                sprite = self.get_resource_icons[res]
                outline_rect(sprite.center_x - HALF, sprite.center_y - HALF, TRADE_SPRITE_W, TRADE_SPRITE_W, TEXT_GOLD, 2)

        # Selection for first row (Resource to offer up)
        for res, selection in self.offer_selected.items():
            if selection:
                sprite = self.offer_resource_icons[res]
                outline_rect(sprite.center_x - HALF, sprite.center_y - HALF, TRADE_SPRITE_W, TRADE_SPRITE_W, TEXT_GOLD, 2)

        # Selection for Second row (Resource to get)
        for res, selection in self.get_selected.items():
            if selection:
                sprite = self.get_resource_icons[res]
                outline_rect(sprite.center_x - HALF, sprite.center_y - HALF, TRADE_SPRITE_W, TRADE_SPRITE_W, TEXT_GOLD, 2)

        self._check_valid_trade()

        if self.trade_success:
            self._build_text_objects()
            self.trade_success = False
            self._draw_trade_buttons()
            self.offer_selected = {}
            self.get_selected = {}
            
        self._draw_resource_numbers()
        self._draw_bottom_bar()
        self._draw_trade_buttons()

    def on_mouse_motion(self, x, y, dx, dy):
        # Highlights for top row
        for res, sprite in self.offer_resource_icons.items():
            if(sprite.center_x - HALF <= x <= sprite.center_x + HALF) and (sprite.center_y - HALF <= y <= sprite.center_y + HALF):
                self.offer_highlights[res] = True
            else:
                self.offer_highlights[res] = False

        # Highlights for second row
        for res, sprite in self.get_resource_icons.items():
            if(sprite.center_x - HALF <= x <= sprite.center_x + HALF) and (sprite.center_y - HALF <= y <= sprite.center_y + HALF):
                self.get_highlights[res] = True
            else:
                self.get_highlights[res] = False

        
    def on_mouse_press(self, x, y, button, modifiers):
        # Back to Board Button
        if (SCREEN_WIDTH - BTN_W - 20 <= x <= SCREEN_WIDTH - 20) and (y <= HUD_BOTTOM_HEIGHT):
            from .catan_view import CatanView
            self.window.show_view(CatanView(self.board, self.players, self.current_player))

        # Accept Trade Button
        if(TRADE_BTN_LEFT <= x <= TRADE_BTN_LEFT + BTN_W) and (y <= HUD_BOTTOM_HEIGHT) and self.valid_trade:
            for offer_res, offer_selection in self.offer_selected.items():
                for get_res, get_selection  in self.get_selected.items():
                    if offer_selection and get_selection:
                        self.players[self.current_player].exchange_resources({offer_res: 4}, {get_res: 1})
                        
                        self.trade_success = True
            
        # Offer Trade Buttons
        for res, sprite in self.offer_resource_icons.items():
            if(sprite.center_x - HALF <= x <= sprite.center_x + HALF) and (sprite.center_y - HALF <= y <= sprite.center_y + HALF):
                self.offer_selected = {}
                self.offer_selected[res] = True

         # Get Trade Buttons
        for res, sprite in self.get_resource_icons.items():
            if(sprite.center_x - HALF <= x <= sprite.center_x + HALF) and (sprite.center_y - HALF <= y <= sprite.center_y + HALF):
                self.get_selected = {}
                self.get_selected[res] = True

       


