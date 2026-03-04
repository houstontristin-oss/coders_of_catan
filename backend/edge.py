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
        self.player = None # player who owns edge/road

    #check if edge is a valid placement for road
    def is_valid_road_placement(self, player):
        #if road already occupied by a player
        if self.player:
            return False
        #determine if an edge of the two connected nodes is occupied by player
        flag = False
        for node in self.nodes:
            for edge in node.edges:
                if edge.player == player:
                    flag = True
        return flag
    #after checking valid road, place road
    def place_road(self, player):
        self.player = player

    def str(self):
        return f"|Edge:{self.edge_id}:{self.nodes}|"
