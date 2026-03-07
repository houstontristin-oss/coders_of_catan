class Edge():
    """edge represents the straight where 2 tiles intersect, a.k.a. roads

    Attributes:
        id: a tuple of the two connected nodes (e.g., (node1, node2))
        nodes: a list of the two surrounding nodes
        tiles: a list of the two adjacent tiles
        player: the player who owns the edge/road (None if unoccupied)
    """
    def __init__(self, edge_id:tuple):
        self.edge_id = edge_id # e.g., tuple of 2 connected nodes
        self.nodes = [] # list of surrounding nodes (expected len 2)
        self.tiles = [] # list of adjacent tiles (expected len 2)
        self.player = None # player who owns edge/road ex. '1', '2', '3', '4'

    def is_valid_road_placement(self, player):
        """
        During building, road needs to connect to an 
        existing road or settlement of the current player.
        
        Args:
            player: The player index (e.g., '1', '2', '3', '4') 
                    for whom we are checking the road placement.
        
        Returns:
            bool: True if the road can be placed, False otherwise.
        """
        if self.player: # if its currenltly occupied, can't place road
            return False
        for node in self.nodes: # find if an edge of the two connected nodes is occupied by player
            for edge in node.edges:
                if edge.player == player:
                    return True
        return False

    def is_valid_setup_road_placement(self, node_obj):
        """
        During setup, road just needs to connect to the current player's settlement.
        
        Args:
            node_obj: The node object to check for connection.
        
        Returns:
            bool: True if the road can be placed, False otherwise.
        """
        if self.player is not None: # edge not owned yet
            return False
        for node in self.nodes:
            if node == node_obj:
                # check if edge is connected to the node where the player is placing a settlement
                return True
        return False

    def place_road(self, player):
        #after checking valid road, place road
        self.player = player

    def str(self):
        return f"|Edge:{self.edge_id}:{self.nodes}|"
