# pylint: disable=C0114,C0116, R0902
from .player import Player
class ComputerPlayer(Player):
    """Represents a computer player for Catan

    This class is used to create ComputerPlayer objects and
    manage ComputerPlayer actions and inventory.

    Attributes:
        all of Player's attributes
        computer: returns bool
    """
    """to add to computer player class to make this easier
            - can_place_settlement() : returns node to place settlement at or None
            - can_afford_road() : returns bool
            - best_road_location() : returns edge to place road on
            - can_afford_settlement() : returns bool
            - can_afford_city() : returns bool
            - best_city_location() : returns node to make into a city
            - can_afford_dev_card() : returns bool
            - play_dev_card() : returns str of what dev card was played for log
            - 
    """
    def __init__(self, color, name):
        super().__init__(color, name)
        self.computer = True


    def can_place_settlement(self):
        pass

    def can_afford_road(self):
        pass

    def can_afford_settlement(self):
        pass

    def can_afford_city(self):
        pass

    def best_city_location(self):
        pass

    def best_road_location(self):
        pass

    def can_afford_dev_card(self):
        pass


