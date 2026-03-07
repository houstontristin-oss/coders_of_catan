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
        self.player = None # player who owns node/settle/city

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
        A settlement can be placed on a node if:
            1. The node is not already occupied by another settlement or city.
            2. There are no adjacent settlements (i.e., no other settlements on 
            directly connected nodes).
        
        Args: 
            player: The player who is attempting to place the settlement.
        """
        if self.building:
            return False
        #loop through edges for edge cases
        flag = False
        for edge in self.edges:
            #determine there is an edge the player owns connected to the node
            if edge.player == player:
                flag = True
            #determine there is not another settlement within one edge of the node
            for node in edge.nodes:
                if node.player:
                    flag = False
        return flag

    #after checking valid placement, actually place settlement
    def place_settlement(self, player):
        """
        Place a settlement on the node if the placement is valid.

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
