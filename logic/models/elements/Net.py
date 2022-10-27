from .CircuitElementBase import CircuitElementBase
from ..pins.Terminal import Terminal
from pyeda.inter import expr as edaxpr, exprvar
from copy import deepcopy


class Net(CircuitElementBase):
    """Net in circuit

    Input pin can be accessed via 'driver' field:
        net.driver

    Raises TypeError if more than one input pins are added
    """
    def __set_driver(self, pin: 'PinBase') -> None:
        if self.driver is None:
            self.driver = pin
        else:
            raise TypeError('Net {} cannot have more than one driver'.format(self.label))

    def __init__(self,
                 label: str,
                 model=None,
                 pins: 'Iterable'= None,
                 parent: 'Circuit'= None):
        """label - element name
        model - reference model from library
        pins - list of PinBase instances
        parent - Circuit instance which current element belongs to
        """
        CircuitElementBase.__init__(self, label, model, pins, parent)
        self.driver = None
        for pin in self.inputs:
            self.__set_driver(pin)

    def attach_input_pin(self, pin: 'PinBase') -> None:
        """Add input pin"""
        self.__set_driver(pin)
        self.inputs.add(pin)
        self.pins.add(pin)
        pin.to_ = self

    def detach_input_pin(self, pin: 'PinBase'= None) -> None:
        """Remove input pin"""
        self.driver = None
        CircuitElementBase.detach_input_pin(self, *self.inputs)

    def var(self) -> 'PyEDA Variable':
        """Return variable to represent self"""
        return exprvar(self.label)

    def expression(self, basis: 'iterable'= None, levels: int= 0) -> 'PyEDA Expression':
        """Return net's logic formula based on given support set

        basis - iterable<Net>, support set
            primary inputs are included in support set by default
        levels - maximum allowed depth
            0 or less value cancels depth limit (default)

            Examples
        Return function based on primary inputs:
        net.expression()

        Return function based on given cut (set of nets):
        net.expression(basis=cut)

        Return function extended for 2 logic levels:
        net.expression(levels=2)
        """
        basis = set(basis) if basis else set()
        basis.update(self.parent.inputs)
        levels -= 1

        driver = self.driver.from_
        if isinstance(driver, Terminal):
            return edaxpr(driver.label)
        elif not driver:
            return edaxpr(0)
        driver_func = deepcopy(self.driver.model.function)
        literal_map = {inp.label: inp.from_.label for inp in driver.inputs}
        driver_func.rename_literals(literal_map)
        expr = driver_func.to_pyeda_expr()

        if levels:
            pred_nets = {inp.from_ for inp in driver.inputs}
            fn_map = {exprvar(net.label): net.get_expr(basis, levels) for net in pred_nets if net not in basis}
            expr = expr.compose(fn_map)

        return expr
