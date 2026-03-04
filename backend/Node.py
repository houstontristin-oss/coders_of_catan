class Node():
    """
    node represents the axis between tiles where settlements can be placed
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

    #check if node is a valid placement for settlement
    def is_valid_settlement_placement(self, player):
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
        self.player = player
        #self.building = "settlement" 
        # NOTE: add check for if placement breaks another players longest road here
    
    # TODO: determine how to represent city
    def place_city(self, player):
        if self.player == player:
            pass
            #self.building = "city" #or another way to denote city