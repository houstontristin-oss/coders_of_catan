class Tile:
    """tiles represent the hexagonal piece that make up the full board
    
    Attributes:
        id: a tuple representing the tile's position on the board 
            (e.g., (x,y,z) cubic coordinates)
        resource: the type of resource the tile produces 
            (e.g., "wood", "brick", "sheep", "wheat", "ore", "desert")
        number: the number associated with the tile that determines when it 
            produces resources (e.g., 2-12, with 7 being the robber)
        nodes: a list of node objects that are adjacent to the tile 
            (i.e., the corners of the tile)
        edges: a list of edge objects that are adjacent to the tile 
            (i.e., the sides of the tile)
    """
    def __init__(self, tile_id:tuple, resource:str, number:int):
        self.tile_id = tile_id # e.g. (x,y,z) cubic coord
        self.resource = resource # terrain/resource tile yields
        self.number = number # number when dice rolled will yield resource
        self.nodes = [] # list of node objects
        self.edges = [] # list of edge objects

    def __repr__(self):
        return self.__str__()
    def __str__(self):
        rtn_str = ""
        for node in self.nodes:
            rtn_str += str(node)

        return f"Tile:{self.tile_id} | {self.resource} | {self.number}\n{rtn_str}"
