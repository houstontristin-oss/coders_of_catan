"""
Contains TradeViewMaritime Class
"""
import arcade
from .drawing import fill_rect, outline_rect
from .constants import (HUD_BOTTOM_HEIGHT, SCREEN_WIDTH, TEXT_GOLD, TEXT_LIGHT_GRAY,
                        SCREEN_HEIGHT, TEXT_WHITE, RESOURCE_ABBR, RESOURCE_SPRITES,
                        HUD_BG, BTN_ENDTURN, BTN_BUILD)

TITLE_FONT_SIZE = 30
TEXT_RED = (238, 0, 0)
TRADE_BG_COLOR = (14, 14, 30, 1)

BTN_W = 150
BTN_H = 50
BTN_BOTTOM = (HUD_BOTTOM_HEIGHT - BTN_H) / 2

TRADE_BTN_LEFT = SCREEN_WIDTH - (BTN_W * 2) - 30
TRADE_BTN_TXT = SCREEN_WIDTH - (BTN_W * 2) + 42
TRADE_BTN_BOTTOM = (HUD_BOTTOM_HEIGHT - BTN_H) / 2
BAR_CENTER_Y = HUD_BOTTOM_HEIGHT / 2

CONFIRM_TXT_X = 20

TRADE_SPRITE_SCALE = 22/512 * 10
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

BASE_TRADE_AMOUNT = 4

class TradeViewMaritime(arcade.View):
    """
    TradeViewMaritime Class
    Handles standard 4:1 trades and allows players to use their ports with 3:1 or 2:1 trades
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

        self.offer_highlights   = {}
        self.get_highlights     = {}

        self.offer_selected     = {}
        self.get_selected       = {}

        self.trade_success  = False
        self.valid_trade    = False

        #Dictionary {'resource': Bool, ...} to determine if a player can afford to trade a resource
        self.affordable_trades = {}

        # Dictionary containing amount of a resource a player needs to make a trade
        self.trade_amount = {"base": BASE_TRADE_AMOUNT} # base starts as 4:1 trade

    def _build_dynamic_text_objects(self):
        # To update resources for each player in between every accepted trade
        # Texts for resource counts
        self.txt_sheep = arcade.Text(
            f"Sheep: {self.players[self.current_player].resource_cards["SHEEP"]}",
            SHEEP_TRADE_NUM_X, TRADE_NUM_Y, TEXT_GOLD, bold=True, anchor_x="center",
            anchor_y="center", font_name="MedievalSharp", font_size=FONT_SIZE_TRADE_NUM)
        self.txt_brick = arcade.Text(
            f"Brick: {self.players[self.current_player].resource_cards["BRICK"]}",
            BRICK_TRADE_NUM_X, TRADE_NUM_Y, TEXT_GOLD, bold=True, anchor_x="center",
            anchor_y="center", font_name="MedievalSharp", font_size=FONT_SIZE_TRADE_NUM)
        self.txt_ore = arcade.Text(
            f"Ore: {self.players[self.current_player].resource_cards["ORE"]}",
            ORE_TRADE_NUM_X, TRADE_NUM_Y, TEXT_GOLD, bold=True, anchor_x="center",
            anchor_y="center", font_name="MedievalSharp", font_size=FONT_SIZE_TRADE_NUM)
        self.txt_wheat = arcade.Text(
            f"Wheat: {self.players[self.current_player].resource_cards["WHEAT"]}",
            WHEAT_TRADE_NUM_X, TRADE_NUM_Y, TEXT_GOLD, bold=True, anchor_x="center",
            anchor_y="center", font_name="MedievalSharp", font_size=FONT_SIZE_TRADE_NUM)
        self.txt_wood = arcade.Text(
            f"Wood: {self.players[self.current_player].resource_cards["WOOD"]}",
            WOOD_TRADE_NUM_X, TRADE_NUM_Y, TEXT_GOLD, bold=True, anchor_x="center",
            anchor_y="center", font_name="MedievalSharp", font_size=FONT_SIZE_TRADE_NUM)

        # Need to be able to reset Trade confirmation Text
        self.txt_confirm = arcade.Text("Not a Valid Trade", CONFIRM_TXT_X, BAR_CENTER_Y,
                                       TEXT_LIGHT_GRAY, font_size=FONT_SIZE_TRADE_NUM, bold=True,
                                       anchor_y="center", anchor_x="left",
                                       font_name="MedievalSharp")

    def _build_static_text_objects(self):
        # Setup Texts
        self.txt_title = arcade.Text(f"{self.players[self.current_player].name} — Maritime Trade",
                                     SCREEN_WIDTH / 2, SCREEN_HEIGHT - 25, TEXT_WHITE, bold=True,
                                     font_name="MedievalSharp", anchor_x="center",
                                     anchor_y="center", font_size=TITLE_FONT_SIZE)

        self.txt_back = arcade.Text("Back to Board",  SCREEN_WIDTH - BTN_W * 0.5 - 20,
                                    BAR_CENTER_Y, TEXT_WHITE, 13, bold=True,
                                    anchor_x="center", anchor_y="center",
                                    font_name="MedievalSharp")

        # Button Text
        self.txt_trade = arcade.Text("Accept Trade", TRADE_BTN_TXT , BAR_CENTER_Y,
                                     TEXT_WHITE, bold=True, anchor_y="center", anchor_x="center",
                                     font_name="MedievalSharp")

        # Always 1 resource in return from a maritime trade
        self.txt_get_trade_amount = arcade.Text("1", x=TRADE_RES_START_X,
                                                y=GET_TRADE_RES_SPACING_Y, color=TEXT_RED,
                                                bold=True, font_size=50,
                                                font_name="MedievalSharp", anchor_x="center",
                                                anchor_y="center")

    def _load_resource_icons(self):
        # Sprite handling for resource icons
        # top row of resources player is offering up
        self.offer_resource_icons   = {}
        self.offer_icon_sprite_list = arcade.SpriteList()
        for lower_res, upper_res in RESOURCE_ABBR.items():
            sprite = arcade.Sprite(RESOURCE_SPRITES[lower_res], scale=TRADE_SPRITE_SCALE)
            self.offer_resource_icons[upper_res] = sprite
            self.offer_icon_sprite_list.append(sprite)

        # bottom row of resource player recieves from bank/port
        self.get_resource_icons   = {}
        self.get_icon_sprite_list = arcade.SpriteList()
        for lower_res, upper_res in RESOURCE_ABBR.items():
            sprite = arcade.Sprite(RESOURCE_SPRITES[lower_res], scale=TRADE_SPRITE_SCALE)
            self.get_resource_icons[upper_res] = sprite
            self.get_icon_sprite_list.append(sprite)

    def _draw_bottom_bar(self):
        # draws the bottom bar and the back to board button
        fill_rect(0, 0, SCREEN_WIDTH, HUD_BOTTOM_HEIGHT, HUD_BG)

        fill_rect(SCREEN_WIDTH - BTN_W - 20, BTN_BOTTOM, BTN_W, BTN_H, BTN_ENDTURN)
        self.txt_back.draw()

    def _draw_trade_button(self):
        #Accept Trade button
        fill_rect(TRADE_BTN_LEFT, TRADE_BTN_BOTTOM, BTN_W, BTN_H,
                  BTN_BUILD  if self.valid_trade else TEXT_LIGHT_GRAY)
        self.txt_trade.draw()

    def _draw_resource_numbers(self):
        # draws all of the texts for the player resource amounts
        self.txt_sheep.draw()
        self.txt_ore.draw()
        self.txt_wheat.draw()
        self.txt_wood.draw()
        self.txt_brick.draw()

    def _load_trade_amount_numbers(self):
        #check if player has a port: if so, update the trade amount for that or all resources
        for port in self.players[self.current_player].ports:
            res, amount = port.get_port_info()
            if res is None:
                self.trade_amount["base"] = amount
            else:
                self.trade_amount[res] = amount

        self.txt_offer_trade_amount = arcade.Text(f"{self.trade_amount["base"]}",
                                                  x=TRADE_RES_START_X, y=OFFER_TRADE_RES_SPACING_Y,
                                                  color=TEXT_RED, bold=True, font_size=50,
                                                  font_name="MedievalSharp", anchor_x="center",
                                                  anchor_y="center")

    def _get_trade_amount(self, res):
        # update the trade amount to reflects the ports the player has
        # used to build text objects
        if res in self.trade_amount.keys():
            return self.trade_amount[res]
        return self.trade_amount["base"]

    def _check_valid_trade(self):
        valid_offer = False
        valid_get = False
        confirm_str = ""

        # Make sure the player has enough resources to make the trade
        for res, selected in self.offer_selected.items():
            if selected:
                valid_offer = self.affordable_trades[res]
                confirm_str += f"You Offer {self._get_trade_amount(res)} {res.capitalize()} "

        # Make sure a selection has been made on the bottom row
        for res, selected in self.get_selected.items():
            if selected:
                valid_get = True
                confirm_str += f"to Recieve 1 {res.capitalize()}"

        self.valid_trade = valid_offer and valid_get
        # Update confirmation text on the bottom bar
        if self.valid_trade:
            self.txt_confirm.text = confirm_str
            self.txt_confirm.color = TEXT_GOLD
        else:
            self.txt_confirm.text = "Not a Valid Trade"
            self.txt_confirm.color = TEXT_LIGHT_GRAY

    def _afford_trade(self):
        #check if player can afford any trades
        player = self.players[self.current_player]
        for res in RESOURCE_ABBR.values():
            trade_amount = player.trade_amount[res]
            self.affordable_trades[res] = player.can_afford_trade({res: trade_amount})

    def on_show_view(self):
        self._build_static_text_objects()
        self._build_dynamic_text_objects()
        self._load_resource_icons()
        self._load_trade_amount_numbers()
        self._afford_trade()

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
                self.txt_offer_trade_amount.x = sprite.center_x
                self.txt_offer_trade_amount.y = sprite.center_y
                self.txt_offer_trade_amount.text = f"{self._get_trade_amount(res)}"
                if self.affordable_trades[res]:
                    outline_rect(sprite.center_x - HALF, sprite.center_y - HALF, TRADE_SPRITE_W,
                                 TRADE_SPRITE_W, TEXT_GOLD, 2)
                    self.txt_offer_trade_amount.color = TEXT_RED
                else:
                    outline_rect(sprite.center_x - HALF, sprite.center_y - HALF, TRADE_SPRITE_W,
                                 TRADE_SPRITE_W, TEXT_LIGHT_GRAY, 2)
                    self.txt_offer_trade_amount.color = TEXT_LIGHT_GRAY
                self.txt_offer_trade_amount.draw()

        # Higlights for Second row (Resource to get)
        for res, highlight in self.get_highlights.items():
            if highlight:
                sprite = self.get_resource_icons[res]
                self.txt_get_trade_amount.x = sprite.center_x
                self.txt_get_trade_amount.y = sprite.center_y
                if True in self.affordable_trades.values():
                    #if the player can afford at least one trade
                    outline_rect(sprite.center_x - HALF, sprite.center_y - HALF,
                                 TRADE_SPRITE_W, TRADE_SPRITE_W, TEXT_GOLD, 2)
                    self.txt_get_trade_amount.color = TEXT_RED
                else:
                    #if the player cannot afford any trades the bottom highlights are also grey
                    outline_rect(sprite.center_x - HALF, sprite.center_y - HALF, TRADE_SPRITE_W,
                                 TRADE_SPRITE_W, TEXT_LIGHT_GRAY, 2)
                    self.txt_get_trade_amount.color = TEXT_LIGHT_GRAY

                self.txt_get_trade_amount.draw()

        # Selection for first row (Resource to offer up)
        for res, selection in self.offer_selected.items():
            if selection:
                sprite = self.offer_resource_icons[res]
                self.txt_offer_trade_amount.x = sprite.center_x
                self.txt_offer_trade_amount. y = sprite.center_y
                self.txt_offer_trade_amount.text = f"{self._get_trade_amount(res)}"
                if self.affordable_trades[res]:
                    outline_rect(sprite.center_x - HALF, sprite.center_y - HALF, TRADE_SPRITE_W,
                                 TRADE_SPRITE_W, TEXT_GOLD, 2)
                    self.txt_offer_trade_amount.color = TEXT_RED
                else:
                    outline_rect(sprite.center_x - HALF, sprite.center_y - HALF, TRADE_SPRITE_W,
                                 TRADE_SPRITE_W, TEXT_LIGHT_GRAY, 2)
                    self.txt_offer_trade_amount.color = TEXT_LIGHT_GRAY
                self.txt_offer_trade_amount.draw()


        # Selection for Second row (Resource to get)
        for res, selection in self.get_selected.items():
            if selection:
                sprite = self.get_resource_icons[res]
                self.txt_get_trade_amount.x = sprite.center_x
                self.txt_get_trade_amount. y = sprite.center_y
                if True in self.affordable_trades.values():
                    #if the player can afford at least one trade
                    outline_rect(sprite.center_x - HALF, sprite.center_y - HALF, TRADE_SPRITE_W,
                                 TRADE_SPRITE_W, TEXT_GOLD, 2)
                    self.txt_get_trade_amount.color = TEXT_RED
                else:
                    #if the player cannot afford any trades the bottom highlights are also grey
                    outline_rect(sprite.center_x - HALF, sprite.center_y - HALF, TRADE_SPRITE_W,
                                 TRADE_SPRITE_W, TEXT_LIGHT_GRAY, 2)
                    self.txt_get_trade_amount.color = TEXT_LIGHT_GRAY
                self.txt_get_trade_amount.draw()

        self._check_valid_trade()

        # reset the board
        if self.trade_success:
            #reload to check if player cannot afford any more trades
            self._afford_trade()
            self._build_dynamic_text_objects()
            self.trade_success = False
            self.offer_selected = {}
            self.get_selected = {}

        self._draw_resource_numbers()
        self._draw_bottom_bar()
        self._draw_trade_button()

        # draw confirmation text on the bottom bar
        self.txt_confirm.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        # Highlights for top row
        for res, sprite in self.offer_resource_icons.items():
            if((sprite.center_x - HALF <= x <= sprite.center_x + HALF) and
                    (sprite.center_y - HALF <= y <= sprite.center_y + HALF)):
                self.offer_highlights[res] = True
            else:
                self.offer_highlights[res] = False

        # Highlights for second row
        for res, sprite in self.get_resource_icons.items():
            if((sprite.center_x - HALF <= x <= sprite.center_x + HALF) and
                    (sprite.center_y - HALF <= y <= sprite.center_y + HALF)):
                self.get_highlights[res] = True
            else:
                self.get_highlights[res] = False


    def on_mouse_press(self, x, y, button, modifiers):
        # Back to Board Button
        if (SCREEN_WIDTH - BTN_W - 20 <= x <= SCREEN_WIDTH - 20) and (y <= HUD_BOTTOM_HEIGHT):
            self.vm.go_back()

        # Accept Trade Button
        if((TRADE_BTN_LEFT <= x <= TRADE_BTN_LEFT + BTN_W) and
                (y <= HUD_BOTTOM_HEIGHT) and self.valid_trade):
            for offer_res, offer_selection in self.offer_selected.items():
                for get_res, get_selection  in self.get_selected.items():
                    if offer_selection and get_selection:
                        self.players[self.current_player].exchange_resources(
                            {offer_res: self._get_trade_amount(offer_res)}, {get_res: 1})

                        self.trade_success = True

        # Offer Trade Buttons
        for res, sprite in self.offer_resource_icons.items():
            if((sprite.center_x - HALF <= x <= sprite.center_x + HALF) and
                    (sprite.center_y - HALF <= y <= sprite.center_y + HALF)):
                self.offer_selected = {}
                self.offer_selected[res] = True

        # Get Trade Buttons
        for res, sprite in self.get_resource_icons.items():
            if((sprite.center_x - HALF <= x <= sprite.center_x + HALF) and
                    (sprite.center_y - HALF <= y <= sprite.center_y + HALF)):
                self.get_selected = {}
                self.get_selected[res] = True
