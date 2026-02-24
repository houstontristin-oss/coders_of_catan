# Catan Backend File

# graph representation
class Tile():
    # tiles represent the hexagonal piece that make up the full board
    def __init__(self, id:list, resource:str, number:int):
        self.id = id # e.g. (x,y,z) cubic coord
        self.resource = resource # terrain/resource tile yields
        self.number = number # number when dice rolled will yield resource
        self.nodes = [] # list of node objects
        self.edges = [] # list of edge objects
    
    def __str__(self):
        return f"Tile:{self.id} | {self.resource} | {self.number}"

class Node():
    # node represents the axis between tiles where settlements can be placed
    def __init__(self, id:tuple):
        self.id = id # e.g. tuple of the averages of the surrounding node's ids
        self.tiles = [] # List of tile objects
        self.edges = [] # list of edge objects
        self.building = None # e.g., settlement/city
        self.player = None # player who owns node/settle/city

    def __str__(self):
        tile_str = ""
        for tile in self.tiles:
            tile_str += tile.id + ", "

        return f"Node: {self.id} | tile"

class Edge():
    # edge represents the straight where 2 tiles intersect, a.k.a. roads
    def __init__(self, id:tuple):
        self.id = id # e.g., tuple of 2 connected nodes
        self.nodes = [] #list of surrounding nodes
        self.player = None # player who owns edge/road

class CatanBoard:
    def __init__(self):
        self.tiles = {} # {(x,y,z): TileObjects}
        self.nodes = {} # {(fx,fy,fz): Node Object

    
    def add_tile(self, x, y, z, resource, number):
        ''' 
        TODO create tile based off given cubic coords, this should also create
        all 6 nodes around the tile if they do not yet exist in the boards list
        '''
        # add tile to registry
        new_tile = Tile(x,y,z, resource, number)
        self.tiles[(x,y,z)] = new_tile
        # define the 6 neighbor offsets for cube coordinates
        neighbor_offsets = [
            (1, -1, 0), (1, 0, -1), (0, 1, -1),
            (-1, 1, 0), (-1, 0, 1), (0, -1, 1)
        ]
        for i in range(6):
            # A node is at the intersection of the current tile & two neighbors
            n1 = neighbor_offsets[i]
            n2 = neighbor_offsets[(i + 1) % 6]
            
            # Use the average of 3 tile centers as the unique Node ID
            fx = round((x + (x+n1[0]) + (x+n2[0])) / 3.0, 3)
            fy = round((y + (y+n1[1]) + (y+n2[1])) / 3.0, 3)
            fz = round((z + (z+n1[2]) + (z+n2[2])) / 3.0, 3)
            node_id = (fx, fy, fz)

            # Get or Create the Node if its not yet in the system
            if node_id not in self.nodes:
                self.nodes[node_id] = Node(node_id)
            
            # create a node object
            node_obj = self.nodes[node_id]

            # Cross-reference them
            new_tile.nodes.append(node_obj)
            node_obj.tiles.append(new_tile)

    def __str__(self):
        return f""


if __name__ == "__main__":
    print("testing board")