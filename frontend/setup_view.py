"""
Contains SetupView Class
"""
import arcade
from .drawing import draw_board
from .constants import SCREEN_HEIGHT, SCREEN_WIDTH

class SetupView(arcade.View):
    """
    SetupView Class
    """
    def __init__(self, board, players, current_player, round): 
        super().__init__()
        self.board = board
        self.players = players
        self.current_player = current_player
        self.round = round
        self._build_text_objects()
        
    def _build_text_objects(self):
        player = self.players[self.current_player]
        self.txt_title = arcade.Text(f"{player.name}: Place your Settlement", SCREEN_WIDTH / 4, SCREEN_HEIGHT - 50, font_name="MedievalSharp", font_size=30, color=player.color)
        
    def on_draw(self):
        self.clear()
        # --- Draw the board --- 
        #TODO: Make a helper function from the code thats in CatanView to build a board with all the ports and numbers.
        draw_board(self.board)
        self.txt_title.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        #TODO: Add in click logic for players placing their 
        if self.round == 1 and self.current_player < len(self.players) - 1:
            self.current_player += 1
            self.window.show_view(SetupView(self.board, self.players, self.current_player, self.round))
        elif self.round == 1 and self.current_player == len(self.players) - 1:
            self.round += 1
            self.window.show_view(SetupView(self.board, self.players, self.current_player, self.round))
        elif self.round == 2 and self.current_player > 0:
            self.current_player -= 1
            self.window.show_view(SetupView(self.board, self.players, self.current_player, self.round))
        else:
            from .catan_view import CatanView
            self.window.show_view(CatanView(self.board, self.players, 0))
