class Player:
    def __init__(self):
        self.victory_points = 0
        self.resource_cards = {'WOOD':0, 'WHEAT':0, 'BRICK': 0, 'SHEEP': 0, 'ORE':0}
        self.development_cards # we'll come back to this
        self.total_roads = 15
        self.total_settlements = 5
        self.total_cities = 4

    def accept_trade(self): #option to accept a trade from a player
        pass

    def offer_trade(self): #offer a trade to another player
        pass

    def buy_dev_card(self): #buy dev cards
        if (self.resource_cards['WHEAT'] > 0 and self.resource_cards['SHEEP'] > 0
         and self.resource_cards['ORE'] > 0):
            pass
        pass

    def build_road(self, edge):

        #check if player has sufficient resources
        if self.resource_cards['WOOD'] > 0 and self.resource_cards['BRICK'] > 0:
            pass

        pass

    def build_settlement(self, node):

        # check if player has sufficient resources
        if (self.resource_cards['WOOD'] > 0 and self.resource_cards['BRICK'] > 0
                and self.resource_cards['WHEAT'] > 0 and self.resource_cards['SHEEP'] > 0):
            pass
        pass

    def build_city(self, settlement):

        # check if player has sufficient resources
        if self.resource_cards['WHEAT'] >= 2 and self.resource_cards['ORE'] >= 3:
            pass
        pass
