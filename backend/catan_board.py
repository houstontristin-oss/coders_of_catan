import random
import backend.tile as Tile
import backend.node as Node
import backend.edge as Edge

class CatanBoard:
    """Catan Board handles all tiles, nodes, and edges of the catan board

    Attributes:
        tiles: a dictionary mapping tile IDs 
            (e.g., (x,y,z) cubic coordinates) to Tile objects
        nodes: a dictionary mapping node IDs 
            (e.g., (fx,fy,fz) fractional coordinates) to Node objects
        edges: a dictionary mapping edge IDs 
            (e.g.,((x1,y1,z1),(x2,y2,z2)) sorted tuple of node IDs) to Edge objs
    """
    def __init__(self):
        self.tiles = {} # {(x,y,z): TileObjects}
        self.nodes = {} # {(fx,fy,fz): Node Object}
        self.edges = {} # {((x1,x2,x3),(x2,y2,z2)) : Edge Object}

    def make_board(self):
        #make default board
        resource = ["sheep","sheep","sheep","sheep", "brick","brick","brick",
                    "ore", "ore","ore","wheat","wheat","wheat","wheat", 
                    "forest","forest","forest","forest", "desert"]
        number = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
        xyz = [(-2,  0,  2), (-2,  1,  1), (-2,  2,  0), (-1, -1,  2),
               (-1,  0,  1), (-1,  1,  0), (-1,  2, -1), (0, -2,  2),
               (0, -1,  1), (0,  0,  0), (0,  1, -1), (0,  2, -2), (1, -2,  1),
               (1, -1,  0), (1,  0, -1), (1,  1, -2), (2, -2,  0), (2, -1, -1),
               (2,  0, -2)]
        # randomize resource and number lists
        random.shuffle(resource)
        random.shuffle(number)
        #19 add tile calls
        for i in range(19):
            r = resource.pop()
            n = 0 if r == "desert" else number.pop()
            self.add_tile(xyz[i], r, n)

    def add_tile(self, xyz:tuple, resource:str, number:int):
        # add tile to registry
        new_tile = Tile.Tile(xyz, resource, number)
        if resource == "desert":
            new_tile.robber = True
        self.tiles[xyz] = new_tile
        tile_nodes = []
        x,y,z = xyz
        # Create Nodes for the Tile
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

            # Get or Create the Node if it's not yet in the system
            if node_id not in self.nodes:
                self.nodes[node_id] = Node.Node(node_id)

            # create a node object
            node_obj = self.nodes[node_id]

            # Cross-reference them
            tile_nodes.append(node_obj) # list of edges for edge creation
            new_tile.nodes.append(node_obj)
            node_obj.tiles.append(new_tile)

        # Create Edges for the Tile
        for i in range(6):
            # an edge connects two nodes
            n1 = tile_nodes[i]
            n2 = tile_nodes[(i + 1) % 6]

            # use two node ids as id for edge
            edge_id = tuple(sorted((n1.node_id, n2.node_id)))

            # Get or Create the edge if it's not yet in the system
            if edge_id not in self.edges:
                self.edges[edge_id] = Edge.Edge(edge_id)

            edge_obj = self.edges[edge_id]

            # Cross-refrerence them
            # NOTE not checked! im also not sure how necessary this is
            # just giving each node, edge, tile lists of connected ones for
            # potential use. - Nick
            edge_obj.tiles.append(new_tile)
            new_tile.edges.append(edge_obj)
            n1.edges.append(edge_obj)
            n2.edges.append(edge_obj)
            edge_obj.nodes.append(n1)
            edge_obj.nodes.append(n2)

    def __str__(self):
        tile_strings = []
        for tile_obj in self.tiles.values(): # .values() gets the Tile objects
            tile_strings.append(str(tile_obj))

        # Combine all tile strings separated by a dashed line
        divider = "\n" + "-"*30 + "\n"
        return f"=== Catan Board ===\n{divider.join(tile_strings)}"


if __name__ == "__main__":
    print("testing board")
    game_board = CatanBoard()
    # create tile at "center" of board with type dessert and of dice roll val 0
    game_board.add_tile((0,0,0), "dessert", 0)
    # add tile to the bottom left of center tile
    game_board.add_tile((1,-1,0), "forrest", 2)
    print(f"{game_board}")
