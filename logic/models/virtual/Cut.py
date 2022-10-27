class Cut:
    """Set of nets in parent Circuit"""
    @property
    def nets(self):
        return self.__nets.values()

    def __init__(self, parent: 'Circuit', name: str= None):
        self.name = name
        self.parent = parent
        self.__nets = {}

    def include(self, *nets) -> None:
        """Add nets to cut"""
        self.__nets.update((net.ID, net) for net in nets)

    def exclude(self, *nets) -> None:
        """Remove nets from cut"""
        for net in nets:
            del self.__nets[net.ID]
