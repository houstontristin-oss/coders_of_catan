class Node:
    """
    node represents the axis between tiles where settlements can be placed

    Args:
        node_id (tuple): a unique identifier for the node, e.g. the average of 
        the surrounding tile's coordinates
    """
    def __init__(self, node_id:tuple):
        self.node_id = node_id # e.g. tuple of the averages of the surrounding node's ids
        self.tiles = [] # List of tile objects
        self.edges = [] # list of edge objects
        self.building = None # e.g., settlement/city
        self.player = None # player who owns node/settle/city ex. '1', '2', '3', '4'

    def __str__(self):
        return f"Node: {self.node_id}"
    def __repr__(self):
        return self.__str__()

    def is_valid_setup_placement(self):
        """
        During setup, a settlement just needs:
            1. The node to be unoccupied
            2. No adjacent settlements (distance rule)

        Returns:
            bool: True if the settlement can be placed, False otherwise.
        """
        if self.building:
            return False
        for edge in self.edges:
            for node in edge.nodes:
                if node is not self and node.player is not None:
                    return False
        return True

    def is_valid_settlement_placement(self, player):
        """
        Check if current node is a valid placement for a settlement for the given player.

        A settlement can be placed on a node if:
            1. The node is not already occupied by another settlement or city.
            2. There are no adjacent settlements (i.e., no other settlements on 
            directly connected nodes).
            3. The player has a road connected to this node.
        
        Args: 
            player: The player who is attempting to place the settlement.
        """
        # node must be unoccupied
        if self.building:
            return False

        has_own_road = False
        for edge in self.edges:
            # track whether the player has a road here
            if edge.player == player:
                has_own_road = True

            # no adjacent settlements allowed
            for node in edge.nodes:
                if node is not self and node.building is not None:
                    return False

        return has_own_road

    def is_valid_city_placement(self, player):
        """
        Check if current node is a valid placement for a city for the given player.

        A city can be placed on a node if:
            1. The node already has a settlement owned by the same player. 

        Args: 
            player: The player who is attempting to place the city.
        """
        return self.player == player and self.building == "settlement"

    def place_settlement(self, player):
        """
        Place a settlement on the node if the placement is valid.
        aka assign the player to the node and set building to settlement

        Args:
            player: The player who is placing the settlement.

        Returns:
            bool: True if the settlement was placed successfully, False otherwise.
        """
        if self.is_valid_settlement_placement(player):
            self.player = player
            self.building = "settlement"
            return True
        return False
        # NOTE: add check for if placement breaks another players longest road here

    def place_city(self, player):
        """assign player to node if they have a settlement there, 
        and upgrade to city
        
        A city can be placed on a node if:
            1. The node already has a settlement owned by the same player. 

        Args:
            player: The player who is placing the city.
        """
        if self.player == player and self.building == "settlement":
            self.building = "city"
            return True
        return False
