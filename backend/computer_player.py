# pylint: disable = R0902

from .player import Player

class ComputerPlayer(Player):
    """Represents a computer player for Catan

    This class is used to create ComputerPlayer objects and
    manage ComputerPlayer actions and inventory.

    Attributes:
        all of Player's attributes
        computer: returns bool
    """

    def __init__(self, color, name):
        super().__init__(color, name)
        self.computer = True

    def can_afford_road(self):
        return bool(self.resource_cards['BRICK'] > 0 and self.resource_cards['WOOD'] > 0)

    def can_afford_settlement(self):
        return bool(self.resource_cards['BRICK'] > 0 and self.resource_cards['WOOD'] > 0 and
                    self.resource_cards['WHEAT'] > 0 and self.resource_cards['SHEEP'] > 0)

    def can_afford_city(self):
        return bool (self.resource_cards['WHEAT'] >= 2 and self.resource_cards['ORE'] >= 3)

    def can_afford_dev_card(self):
        return bool(self.resource_cards['WHEAT'] >= 0 and self.resource_cards['ORE'] >= 0 and
                    self.resource_cards['SHEEP'] > 0)

    # returns edge to place road at or None
    def best_road_location(self):
        if self.can_afford_road():
            pass

    # returns node to place settlement at or None
    def best_settlement_location(self):
        if self.can_afford_settlement():
            pass

    # returns node to place city at or None
    def best_city_location(self):
        if self.can_afford_city():
            pass

    # returns string of what dev card was played for log
    def play_dev_card(self):
        if self.can_afford_dev_card():
            pass
