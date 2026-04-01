from frontend.constants import RESOURCE_ABBR
THREE_FOR_ONE = 3
TWO_FOR_ONE = 2

class Port:
    """
    Port class contains the port information for trading with the bank
    """
    def __init__(self, node_ids, resource):
        self.node_ids = node_ids # tuple containing both node ids for the port
        if resource is not None:
            self.resource = RESOURCE_ABBR[resource]
            self.amount = TWO_FOR_ONE
        else:
            self.resource = resource
            self.amount = THREE_FOR_ONE

    def get_port_info(self):
        #returns port resource and amount
        return self.resource, self.amount

    def get_port_nodes(self):
        return self.node_ids

    def __str__(self):
        return f"{self.amount}:1 {self.resource}"
