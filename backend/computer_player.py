# pylint: disable = R0902

import random
from .player import Player

class ComputerPlayer(Player):
    """Represents a computer player for Catan

    This class is used to create ComputerPlayer objects and
    manage ComputerPlayer actions and inventory.

    Attributes:
        all of Player's attributes
        computer: returns bool
    """

    def __init__(self, color, name, board):
        super().__init__(color, name)
        self.computer = True
        self.board = board

    def can_afford_road(self):
        return bool(self.resource_cards['BRICK'] > 0 and self.resource_cards['WOOD'] > 0)

    def can_afford_settlement(self):
        return bool(self.resource_cards['BRICK'] > 0 and self.resource_cards['WOOD'] > 0 and
                    self.resource_cards['WHEAT'] > 0 and self.resource_cards['SHEEP'] > 0)

    def can_afford_city(self):
        return bool (self.resource_cards['WHEAT'] >= 2 and self.resource_cards['ORE'] >= 3)

    def can_afford_dev_card(self):
        return bool(self.resource_cards['WHEAT'] > 0 and self.resource_cards['ORE'] > 0 and
                    self.resource_cards['SHEEP'] > 0)

    # returns edge to place road at or None
    # Apr 6th - current versions is iterating the board incorrectly and also assumes edge.player / node.player
    # are player objects with .name, but in board code they are stored as player indices. Patched...
    def best_road_location(self):
        possible_roads = []

        for edge in self.board.edges.values():
            if edge.player is not None:
                continue

            for node in edge.nodes:
                # build off one of this AI's settlements/cities
                if node.player == self.player_index:
                    possible_roads.append(edge)
                    break

                # or build off one of this AI's existing roads
                for edge2 in node.edges:
                    if edge2.player == self.player_index:
                        possible_roads.append(edge)
                        break
                else:
                    continue
                break

        return random.choice(possible_roads) if possible_roads else None

    # returns node to place settlement at or None
    # Apr 6th -
    def best_settlement_location(self):
        possible_settlements = []

        for node in self.board.nodes.values():
            if node.building is not None:
                continue

            has_own_road = False
            blocked = False

            for edge in node.edges:
                if edge.player == self.player_index:
                    has_own_road = True

                for node2 in edge.nodes:
                    if node2 is not node and node2.building is not None:
                        blocked = True
                        break

                if blocked:
                    break

            if has_own_road and not blocked:
                possible_settlements.append(node)

        return random.choice(possible_settlements) if possible_settlements else None

    # returns node to place city at or None
    def best_city_location(self):
        possible_cities = []

        for node in self.board.nodes.values():
            if node.player == self.player_index and node.building == "settlement":
                possible_cities.append(node)

        return random.choice(possible_cities) if possible_cities else None

    # returns string of what dev card was played for log
    def play_dev_card(self):
        if self.can_afford_dev_card():
            pass

    # returns resource the player has the most of
    def max_resource(self):
        max_res = []
        max_amt = max(self.resource_cards.values())
        for res, amt in self.resource_cards.items():
            if max_amt == amt:
                max_res.append(res)
        return random.choice(max_res)

    # returns the resource with the minimum amount
    def min_resource(self):
        min_res = []
        min_amt = min(self.resource_cards.values())
        for res, amt in self.resource_cards.items():
            if min_amt == amt:
                min_res.append(res)
        return random.choice(min_res)
