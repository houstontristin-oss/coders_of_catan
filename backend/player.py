# pylint: disable= R0902
class Player:
    """Represents a player for Catan

    This class is used to create Player objects and
    manage Player actions and inventory.

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
    def __init__(self, color, name):
        self.victory_points = 0
        self.resource_cards = {'WOOD':0, 'WHEAT':0, 'BRICK': 0, 'SHEEP': 0, 'ORE':0}
        self.development_cards = []
        self.total_roads = 15
        self.total_settlements = 5
        self.total_cities = 4
        self.ports = []
        self.color = color
        self.name = name
        self.knight_count = 0
        self.largest_army = False
        self.road_length = 0
        self.longest_road = False
        self.computer = False


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

    def get_total_cards(self):
        # total hand size = resource cards + development cards currently held
        return self.get_total_resources() + len(self.development_cards)

    def add_port(self, res):
        self.ports.append(res)
