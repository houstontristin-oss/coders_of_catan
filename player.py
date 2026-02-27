import arcade.color


class Player:
    def __init__(self, color):
        self.victory_points = 0
        self.resource_cards = {'WOOD':0, 'WHEAT':0, 'BRICK': 0, 'SHEEP': 0, 'ORE':0}
        self.development_cards = [] # we'll come back to this
        self.total_roads = 15
        self.total_settlements = 5
        self.total_cities = 4
        self.color = color

    def accept_trade(self): #option to accept a trade from a player
        pass

    def offer_trade(self): #offer a trade to another player
        pass

    def buy_dev_card(self): #buy dev cards
        if (self.resource_cards['WHEAT'] > 0 and self.resource_cards['SHEEP'] > 0
         and self.resource_cards['ORE'] > 0):
            pass
        pass

    def build_road(self, board, edge):

        #check if player has sufficient resources
        if self.resource_cards['WOOD'] > 0 and self.resource_cards['BRICK'] > 0:
            # if a road can be placed, deduct resources and 1 from total_road, then place
            if edge.is_valid_road_placement(board):
                self.resource_cards['WOOD'] -= 1
                self.resource_cards['BRICK'] -= 1
                self.total_roads -= 1
                edge.place_road(board)

        pass

    def build_settlement(self, board, node):

        # check if player has sufficient resources
        if (self.resource_cards['WOOD'] > 0 and self.resource_cards['BRICK'] > 0
                and self.resource_cards['WHEAT'] > 0 and self.resource_cards['SHEEP'] > 0):
            # if a settlement can be placed, deduct resources and 1 from total_settlements, then place
            if node.is_valid_settlement_placement(board):
                self.resource_cards['WOOD'] -= 1
                self.resource_cards['BRICK'] -= 1
                self.resource_cards['SHEEP'] -= 1
                self.resource_cards['WHEAT'] -= 1
                self.total_settlements -= 1
                node.place_settlement(board)
        pass

    def build_city(self, settlement):

        # check if player has sufficient resources
        if self.resource_cards['WHEAT'] >= 2 and self.resource_cards['ORE'] >= 3:
            pass
        pass
