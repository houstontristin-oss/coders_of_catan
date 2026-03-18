# pylint: disable=C0114,C0116
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
        self.resource_cards = {'WOOD':100, 'WHEAT':100, 'BRICK': 100, 'SHEEP': 100, 'ORE':100}
        self.development_cards = [] # we'll come back to this
        self.total_roads = 15
        self.total_settlements = 5
        self.total_cities = 4
        self.color = color
        self.name = name

    def exchange_resources(self, giving_resources:dict, receiving_resources:dict): 
        # exchange resources between players for maritime and barter trades
        for resource, amount in giving_resources.items():
            if self.resource_cards.get(resource, 0) >= amount:
                self.resource_cards[resource] -= amount
            else:
                raise ValueError("Player does not have enough resources to give.")
        for resource, amount in receiving_resources.items():
            self.resource_cards[resource] += amount

    def can_afford_trade(self, offered_resources:dict) -> bool:
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

    def build_city(self, settlement):

        # check if player has sufficient resources
        if (self.resource_cards['WHEAT'] >= 2 and self.resource_cards['ORE'] >= 3
                and self.total_settlements>0):
            pass
