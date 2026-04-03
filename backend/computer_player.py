# pylint: disable=C0114,C0116, R0902
from .player import Player
class ComputerPlayer(Player):
    """Represents a computer layer for Catan

    This class is used to create ComputerPlayer objects and
    manage ComputerPlayer actions and inventory.

    Attributes:
        victory_points: total victory points
        resource_cards: resources in player's possession
        development_cards: development cards in player's possession
        total_roads: roads left player can build
        total_settlements: settlements left player can build
        total_cities: cities left player can build
        color: color of player
        name: name of player
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


    def exchange_resources(self, giving_resources:dict, receiving_resources:dict):
        """
        subtracts giving_resources and adds receiving_resources to current player
        dictionary organized {"BRICK": 0, "ORE": 0, "WHEAT": 0, "SHEEP": 0, "WOOD": 0}
        """
        for resource, amount in giving_resources.items():
            if self.resource_cards.get(resource, 0) >= amount:
                self.resource_cards[resource] -= amount
            else:
                raise ValueError("Player does not have enough resources to give.")
        for resource, amount in receiving_resources.items():
            self.resource_cards[resource] += amount

    def can_afford_trade(self, offered_resources:dict) -> bool:
        """
        checks players current resources against values in the dictionary
        organized {"BRICK": 0, "ORE": 0, "WHEAT": 0, "SHEEP": 0, "WOOD": 0}
        """
        for resource, amount in offered_resources.items():
            if self.resource_cards.get(resource, 0) < amount:
                return False
        return True

    def buy_dev_card(self): #buy dev cards
        if (self.resource_cards['WHEAT'] > 0 and self.resource_cards['SHEEP'] > 0
         and self.resource_cards['ORE'] > 0):
            pass

    def build_road(self, board, edge):

        #check if player has sufficient resources
        if self.resource_cards['WOOD'] > 0 and self.resource_cards['BRICK'] > 0:
            self.resource_cards['WOOD'] -= 1
            self.resource_cards['BRICK'] -= 1
            self.total_roads -= 1
            edge.place_road(board)
            # if a road can be placed, deduct resources and 1 from total_road, then place
            #if edge.is_valid_road_placement(board):
               # self.resource_cards['WOOD'] -= 1
                #self.resource_cards['BRICK'] -= 1
                #self.total_roads -= 1
                #edge.place_road(board)

    def build_road_setup(self, board, edge):
        if edge.is_valid_road_placement(board):
            self.total_roads -= 1
            edge.place_road(board)

    def build_settlement(self, board, node):

        # check if player has sufficient resources
        if (self.resource_cards['WOOD'] > 0 and self.resource_cards['BRICK'] > 0
                and self.resource_cards['WHEAT'] > 0 and self.resource_cards['SHEEP'] > 0):
            self.resource_cards['WOOD'] -= 1
            self.resource_cards['BRICK'] -= 1
            self.resource_cards['SHEEP'] -= 1
            self.resource_cards['WHEAT'] -= 1
            self.total_settlements -= 1
            node.place_settlement(board)

    def build_settlement_setup(self, board, node):
        if node.is_valid_settlement_placement(board):
            self.total_settlements -= 1
            node.place_settlement(board)

    def build_city(self, board, node):
        # check if player has sufficient resources
        if (self.resource_cards['WHEAT'] >= 2 and self.resource_cards['ORE'] >= 3
                and self.total_settlements>0):
            self.resource_cards['WHEAT'] -= 2
            self.resource_cards['ORE'] -= 3
            self.total_cities -= 1
            self.total_settlements += 1
            node.place_city(board)

    def get_total_resources(self):
        # returns the total number of resources cards a player has of any type
        return sum(self.resource_cards.values())

    def add_port(self, res):
        self.ports.append(res)
