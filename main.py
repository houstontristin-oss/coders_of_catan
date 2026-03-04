"""
Catan using python arcade
"""
import arcade
import pyglet
from frontend.constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE
from frontend.start_view import StartView

def main():
    """
    Main Runner for Catan
    """
    pyglet.font.add_file('fonts/MedievalSharp-Regular.ttf')
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.background_color = arcade.color.OCEAN_BOAT_BLUE
    window.show_view(StartView())
    arcade.run()

if __name__ == "__main__":
    main()
