"""
Contains TradeView Class
"""
import arcade
from .drawing import fill_rect
from .constants import *

class TradeViewBarter(arcade.View):
    """
    TradeViewBarter Class
    """
    def __init__(self, board, players, current_player):
        super().__init__()
        self.board= board
        self.players = players
        self.current_player = current_player
    
    def _build_text_objects(self):
        bar_center_y = HUD_BOTTOM_HEIGHT / 2
        btn_w = 150
        self.txt_back = arcade.Text("Back to Board",  SCREEN_WIDTH - btn_w * 0.5 - 20,    bar_center_y, TEXT_WHITE, 13, bold=True, anchor_x="center", anchor_y="center", font_name="MedievalSharp")

    def _draw_bottom_bar(self):
        fill_rect(0, 0, SCREEN_WIDTH, HUD_BOTTOM_HEIGHT, HUD_BG)

        btn_w, btn_h = 150, 50
        btn_bottom = (HUD_BOTTOM_HEIGHT - btn_h) / 2

        fill_rect(SCREEN_WIDTH - btn_w - 20, btn_bottom, btn_w, btn_h, BTN_ENDTURN)
        self.txt_back.draw()

    def offer_trade(self, receiving_player, offered_resources:dict, 
                    requested_resources:dict) -> bool:
        """
        Offer a trade to another player.

        Args:
            receiving_player: The player who is being offered the trade.
            offered_resources: A dictionary of resources being offered (e.g., {'WOOD': 2}).
            requested_resources: A dictionary of resources being requested (e.g., {'BRICK': 1}).

        Returns:
            bool: True if the trade was accepted, False otherwise.
        """
        print(f"{self.current_player.name} offers {offered_resources} to {receiving_player.name} in exchange for {requested_resources}.")

        if not receiving_player.can_afford_trade(requested_resources):
            # auto deny if receiving player doesnt have necessary resources
            print(f"{receiving_player.name} cannot afford the trade and automatically declines.")
            return False
        # check for computer player and auto-accept if so

        response = input(f"{receiving_player.name}, do you accept the trade? (yes/no): ").strip().lower()
        if response == 'yes':
            # Execute the trade
            self.current_player.exchange_resources(offered_resources, requested_resources)
            receiving_player.exchange_resources(requested_resources, offered_resources)
            return True
        else:
            print(f"{receiving_player.name} declined the trade.")
        return False
    
    def on_show_view(self):
        self._build_text_objects()

    def on_draw(self):
        self.clear()
        self._draw_bottom_bar()

    def on_mouse_press(self, x, y, button, modifiers):
        #NOTE: Would it be a good idea to make the btn_w and btn_h global variable?
        btn_w = 150
        if (SCREEN_WIDTH - btn_w - 20 <= x <= SCREEN_WIDTH - 20) and (y <= HUD_BOTTOM_HEIGHT):
            from .catan_view import CatanView
            self.window.show_view(CatanView(self.board, self.players, self.current_player))
