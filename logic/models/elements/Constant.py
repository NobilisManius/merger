class Constant:
    """Source of the constant signal"""
    def __init__(self, name, func, parent=None):
        self.name = name
        self.func = func
        self.parent = parent
        self.fanout = set()

    def copy(self, parent=None):
        """Return functional copy of self"""
        return Constant(self.name, self.func, parent)

    def __call__(self):
        """Return self value"""
        return self.func()

    def __str__(self):
        return self.name

    def predecessors(self):
        """Return empty list (for circuit traversal functions)"""
        return []

    def successors(self):
        """Yield gates and output terminals connected to self"""
        for pin in self.fanout:
            net = pin.to_
            yield from (pin.to_ for pin in net.outputs)

    def attach_output_pin(self, pin):
        """Add output pin"""
        self.fanout.add(pin)
        pin.from_ = self

    def detach_output_pin(self, pin):
        """Remove output pin"""
        self.fanout.remove(pin)
        pin.from_ = None
