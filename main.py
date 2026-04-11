"""
Catan using python arcade
"""
import arcade
import pyglet
from frontend.constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE
from frontend.view_manager import ViewManager

def main():
    """
    Main Runner for Catan
    """
    pyglet.font.add_file('fonts/MedievalSharp-Regular.ttf')
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.background_color = arcade.color.OCEAN_BOAT_BLUE
    vm = ViewManager(window)
    window.vm = vm
    vm.go_to("start")
    arcade.run()

if __name__ == "__main__":
    main()
