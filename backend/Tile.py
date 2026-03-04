class Tile():
    # tiles represent the hexagonal piece that make up the full board
    def __init__(self, id:tuple, resource:str, number:int):
        self.id = id # e.g. (x,y,z) cubic coord
        self.resource = resource # terrain/resource tile yields
        self.number = number # number when dice rolled will yield resource
        self.nodes = [] # list of node objects
        self.edges = [] # list of edge objects
    
    def __str__(self):
        rtn_str = ""
        for node in self.nodes:
            rtn_str += str(node)

        return f"Tile:{self.id} | {self.resource} | {self.number}\n{rtn_str}" 