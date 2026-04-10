"""
Contains EndView Class
"""
import arcade
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT

class EndView(arcade.View):
    """
    EndView Class
    """
    def __init__(self, vm, players, current_player):
        super().__init__()
        self.vm = vm
        self.players = players
        self.winning_player = current_player

    def on_show_view(self):
        self._build_text_objects()

    def _build_text_objects(self):
        # set the color of the text to the players color and add the player number to the text
        self.txt_title = arcade.Text(f"Congratulations Player {self.winning_player + 1}!",
                                     SCREEN_WIDTH / 2, SCREEN_HEIGHT/2, font_size=30, bold=True,
                                     font_name="MedievalSharp",
                                     color = self.players[self.winning_player].color,
                                     anchor_x="center", anchor_y="center")
        self.txt_instructions = arcade.Text("Click anywhere to play again!",
                                            SCREEN_WIDTH / 2, SCREEN_HEIGHT/2 - 100, font_size=20,
                                            font_name="MedievalSharp",
                                            anchor_x="center", anchor_y="center")

    def on_draw(self):
        self.clear()
        self.txt_title.draw()
        self.txt_instructions.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        # Has to go back to start view to reset the board and players
        self.vm.go_to("start")
