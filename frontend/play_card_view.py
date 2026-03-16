"""
Contains PlayerCardView Class
"""
import arcade
from .drawing import fill_rect
from .constants import HUD_BOTTOM_HEIGHT, HUD_BG, SCREEN_WIDTH, TEXT_WHITE, BTN_ENDTURN

class PlayCardView(arcade.View):
    """
    PlayerCardView Class
    """
    def __init__(self, board, players, current_player, die1, die2):
        super().__init__()
        self.board= board
        self.players = players
        self.current_player = current_player
        self.die1 = die1
        self.die2 = die2
    
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
            self.window.show_view(CatanView(self.board, self.players, self.current_player, self.die1, self.die2))
