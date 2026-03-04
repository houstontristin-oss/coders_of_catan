"""
Contains StartView class
"""
import arcade
from backend.catan_board import CatanBoard
from backend.player import Player
from .setup_view import SetupView
from .constants import SCREEN_HEIGHT, SCREEN_WIDTH

class StartView(arcade.View):
    """
    StartView class
    """
    def __init__(self):
        super().__init__()
        self._build_text_objects()

    def _build_text_objects(self):
        # Build text objects
        self.txt_title = arcade.Text("Welcome to Catan!", SCREEN_WIDTH / 2, SCREEN_HEIGHT/2, font_size=30, bold=True, font_name="MedievalSharp")
        self.txt_instructions = arcade.Text("Click anywhere to begin!", SCREEN_WIDTH / 2, SCREEN_HEIGHT/2 - 100, font_size=20, font_name="MedievalSharp")

    def on_draw(self):
        self.clear()
        self.txt_title.draw()
        self.txt_instructions.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        # TODO: add buttons here for selection of number of players
        board = CatanBoard()
        board.make_board()
        # TODO: create players here
        players = [
            Player((231, 76,  60), "Player 1"),
            Player((39, 174, 96), "Player 2"),
            Player((219, 118, 51), "Player 3"),
            Player((142, 68, 173), "Player 4"),
        ]
        # show setupview starting with player at index 0 and round 1 of play
        self.window.show_view(SetupView(board, players, 0, 1))