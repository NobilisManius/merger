from ...datatypes import IDDict
from ..elements.Gate import Gate
from ..pins.Terminal import Terminal
from ..Circuit import Circuit
from ...tools import Traversal
from itertools import chain
from sys import maxsize as maxint


class Location:
    """Transparent subcircuit / white box

    Provides tools for grouping gates in circuit and manipulating its structure locally
    Circuit remains unaffected until location's structure is changed

    Provides context managers TempInclude, TempExclude and TempAlter for temporary alteration
    Example:
        loc = Location(<name>, <parent circuit>)
        <some actions>
        with loc.TempInclude(gate1, gate2, ...):
            <gates are included here>
        <gates are excluded here>
    Example 2:
        loc = Location(<name>, <parent circuit>)
        <some actions>
        with loc.TempAlter(include=[igate1, ...], exclude=[egate1, ...]):
            <location is altered here>
        <location is returned to previous state here>
    """

    class TempInclude:
        def __init__(self, *gates):
            self.gates = gates

        def __enter__(self):
            self.loc.include(*self.gates)

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.loc.exclude(*self.gates)

    class TempExclude:
        def __init__(self, *gates):
            self.gates = gates

        def __enter__(self):
            self.loc.exclude(*self.gates)

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.loc.include(*self.gates)

    class TempAlter:
        def __init__(self, include=None, exclude=None):
            self.include = include if include else []
            self.exclude = exclude if exclude else []

        def __enter__(self):
            self.loc.include(*self.include)
            self.loc.exclude(*self.exclude)

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.loc.include(*self.exclude)
            self.loc.exclude(*self.include)

    @property
    def gates(self):
        return self.__gates.values()

    def __init__(self, name: str, parent: 'Circuit'):
        self.name = name
        self.parent = parent
        self.__gates = {}
        self.__internal_nets = {}
        self.__edge_nets = {}
        self.__inputs = {}
        self.__outputs = {}
        self.inputs = IDDict()
        self.outputs = IDDict()

        self.TempInclude = type('TempInclude', (Location.TempInclude,), {'loc': self})
        self.TempExclude = type('TempExclude', (Location.TempExclude,), {'loc': self})
        self.TempAlter = type('TempAlter', (Location.TempAlter,), {'loc': self})

    def __check_connectivity(self, net: 'Net') -> '(bool, bool)':
        connected = False
        isedge = False

        incident = [net.driver.from_]
        incident.extend(out.to_ for out in net.outputs)
        for el in incident:
            if isinstance(el, Gate) and el in self:
                connected = True
            else:
                isedge = True
        return connected, isedge

    def __update_edge_nets(self) -> None:
        for netID in list(self.__edge_nets):
            net = self.parent.nets[netID]
            connected, isedge = self.__check_connectivity(net)
            if connected:
                if isedge:
                    continue
                self.__internal_nets[netID] = net
            del self.__edge_nets[netID]

    def __update_internal_nets(self) -> None:
        for netID in list(self.__internal_nets):
            net = self.parent.nets[netID]
            connected, isedge = self.__check_connectivity(net)
            if isedge:
                del self.__internal_nets[netID]
                if connected:
                    self.__edge_nets[netID] = net

    def __update_terminals(self) -> None:
        for net in self.__edge_nets.values():
            pin = net.driver
            driver = pin.from_
            if not isinstance(driver, Gate) or driver not in self:
                if pin not in self.__inputs:
                    inp = Terminal('', parent=self)
                    inp.to_ = pin
                    self.__inputs[pin] = inp
                    self.inputs.add(inp)
            for pin in net.outputs:
                dest = pin.to_
                if not isinstance(dest, Gate) or dest not in self:
                    if pin not in self.__outputs:
                        out = Terminal('', parent=self)
                        out.from_ = pin
                        self.__outputs[pin] = out
                        self.outputs.add(out)
        for out in list(self.outputs):
            pin = out.from_
            if isinstance(pin.to_, Gate) and pin.to_ in self or pin.from_.ID not in self.__edge_nets:
                del self.__outputs[pin]
                self.outputs.remove(out)
        for inp in list(self.inputs):
            pin = inp.to_
            if isinstance(pin.from_, Gate) and pin.from_ in self or pin.to_.ID not in self.__edge_nets:
                del self.__inputs[pin]
                self.inputs.remove(inp)

    def __name_terminals(self) -> None:
        self.inputs.rename_items_by_ID(prefix='I', field='label')
        self.outputs.rename_items_by_ID(prefix='O', field='label')

    def __detach(self) -> None:
        for net in self.__edge_nets.values():
            if isinstance(net.driver.from_, Gate) and net.driver.from_ in self:
                net.detach_input_pin()
            for pin in list(net.outputs):
                if isinstance(pin.to_, Gate) and pin.to_ in self:
                    net.detach_output_pin(pin)

    def include(self, *gates: 'Gate') -> None:
        """Add gates to location"""
        for gate in gates:
            if gate.ID in self.__gates:
                continue
            self.__gates[gate.ID] = gate

            for inp in gate.inputs:
                w = inp.from_
                self.__edge_nets[w.ID] = w
            for out in gate.outputs:
                w = out.to_
                self.__edge_nets[w.ID] = w
        self.__update_edge_nets()
        self.__update_terminals()

    def exclude(self, *gates: 'Gate') -> None:
        """Remove gates from location"""
        for gate in gates:
            if gate.ID not in self.__gates:
                continue
            del self.__gates[gate.ID]
        self.__update_edge_nets()
        self.__update_internal_nets()
        self.__update_terminals()

    def to_circuit(self) -> 'Circuit':
        """Return Circuit copying location's structure"""
        self.__name_terminals()
        circuit = Circuit(name=self.name, library=self.parent.library)
        gateIDmap = {}
        netIDmap = {}

        def gate_image(gate):
            imageID = gateIDmap[gate.ID]
            return circuit.gates[imageID]

        def net_image(net):
            imageID = netIDmap[net.ID]
            return circuit.nets[imageID]

        for gateID, gate in self.__gates.items():
            newID = circuit.gates.add(gate.copy(parent=circuit))
            gateIDmap[gateID] = newID
        for netID, net in chain(self.__internal_nets.items(), self.__edge_nets.items()):
            newID = circuit.nets.add(net.copy(parent=circuit))
            netIDmap[netID] = newID

        for gate in self.gates:
            gate_new = gate_image(gate)
            for pin in gate.inputs:
                net_new = net_image(pin.from_)
                pin.copy(from_=net_new, to_=gate_new, parent=circuit)
            for pin in gate.outputs:
                net_new = net_image(pin.to_)
                pin.copy(from_=gate_new, to_=net_new, parent=circuit)

        for inp in self.inputs:
            pin = inp.to_
            net_new = net_image(pin.to_)
            inp_new = Terminal(inp.label, parent=circuit)
            circuit.inputs.add(inp_new)
            pin.copy(from_=inp_new, to_=net_new, parent=circuit)
        for out in self.outputs:
            pin = out.from_
            net_new = net_image(pin.from_)
            out_new = Terminal(out.label, parent=circuit)
            circuit.outputs.add(out_new)
            pin.copy(from_=net_new, to_=out_new, parent=circuit)

        return circuit

    def to_verilog(self, filename: str, rename=True) -> None:
        """Write self structure to verilog file
        Same as Circuit's method
        """
        circuit = self.to_circuit()
        circuit.to_verilog(filename, rename)

    def from_circuit(self, circuit: 'Circuit', pin_map: dict= None) -> None:
        """Copy circuit's structure to location

        pin_map represents mapping from circuit terminal labels (keys) to location terminal labels (values)
            None by default: corresponding terminals must have equal labels in this case
        """
        if pin_map is None:
            pin_map = {pin.label: pin.label for pin in chain(self.inputs, self.outputs)}

        loc_labelIDmap = {pin.label: pin.ID for pin in chain(self.inputs, self.outputs)}

        gateIDmap = {}
        netIDmap = {}

        def gate_image(gate):
            imageID = gateIDmap[gate.ID]
            return self.parent.gates[imageID]

        def net_image(net):
            imageID = netIDmap[net.ID]
            return self.parent.nets[imageID]

        for cir_inp in circuit.inputs:
            cir_label = cir_inp.label
            loc_label = pin_map[cir_label]
            loc_ID = loc_labelIDmap[loc_label]
            loc_inp = self.inputs[loc_ID]
            cir_net = cir_inp.to_.to_
            loc_net = loc_inp.to_.to_
            netIDmap[cir_net.ID] = loc_net.ID
        for cir_out in circuit.outputs:
            cir_label = cir_out.label
            loc_label = pin_map[cir_label]
            loc_ID = loc_labelIDmap[loc_label]
            loc_out = self.outputs[loc_ID]
            cir_net = cir_out.from_.from_
            loc_net = loc_out.from_.from_
            netIDmap[cir_net.ID] = loc_net.ID

        self.__detach()
        self.parent.gates.remove(*self.gates)
        self.parent.nets.remove(*self.__internal_nets.values())
        self.__gates = {}
        self.__internal_nets = {}

        for gate in circuit.gates:
            gate_new = gate.copy(parent=self.parent)
            loc_ID = self.parent.gates.add(gate_new)
            cir_ID = gate.ID
            self.__gates[loc_ID] = gate_new
            gateIDmap[cir_ID] = loc_ID

        for net in circuit.nets:
            if net.ID in netIDmap:
                continue
            net_new = net.copy(parent=self.parent)
            loc_ID = self.parent.nets.add(net_new)
            cir_ID = net.ID
            self.__internal_nets[loc_ID] = net_new
            netIDmap[cir_ID] = loc_ID

        for gate in circuit.gates:
            gate_new = gate_image(gate)
            for inp in gate.inputs:
                net_new = net_image(inp.from_)
                inp.copy(from_=net_new, to_=gate_new, parent=self.parent)
            for out in gate.outputs:
                net_new = net_image(out.to_)
                out.copy(from_=gate_new, to_=net_new, parent=self.parent)

    def from_verilog(self, filename: str, pin_map: dict= None) -> None:
        """Load structure from verilog file
        Same as from_circuit with other source format
        Source circuit must be flat
        """
        circuit = Circuit.from_verilog(filename, library=self.parent.library)
        self.from_circuit(circuit, pin_map)

    def __contains__(self, item: 'Gate'):
        return item.ID in self.__gates

    def topological_order(self) -> 'Traversal':
        """Return Traversal instance for topological-order iteration"""
        front = set(self.inputs)
        marks = [(gate, sum(bool(pred) for pred in gate.predecessors())) for gate in self.gates]
        search = lambda el: el.successors(filter=lambda g: g in self.gates)
        mark = lambda el, old: old - 1 if old else 0
        filter = lambda gate, m: m == 0
        return Traversal(front, marks, search, mark, filter)

    def reverse_topological_order(self) -> 'Traversal':
        """Return Traversal instance for reverse-topological-order iteration"""
        front = self.outputs
        marks = [(gate, sum(len(out.to_.outputs) for out in gate.outputs if out.to_)) for gate in self.gates]
        search = lambda el: el.predecessors(filter=lambda g: g in self.gates)
        mark = lambda el, old: old - 1 if old else 0
        filter = lambda gate, m: m == 0
        return Traversal(front, marks, search, mark, filter)

    @classmethod
    def clusterize(cls,
                   name: str,
                   parent: 'Circuit',
                   starter: 'Gate',
                   decision_function: 'callable',
                   stop_function: 'callable',
                   include_cost_function: 'callable'= lambda loc, gate: 0,
                   exclude_cost_function: 'callable'= lambda loc, gate: maxint,
                   discard_last: bool= False) -> 'Location':
        """Form cluster using specified rules, return Location

        name - location's name
        parent - parent circuit
        starter - first gate in cluster
        decision_function(loc, inc_gen, exc_gen) - must return 2 lists: added and removed gates, respectively
            loc - current Location instance
            inc_gen - generator, yields (gate, include_cost) pairs for nearest gates
            exc_gen - generator, yields (gate, exclude_cost) pairs for gates in cluster
        stop_function(loc) - must return True if clusterization should be stopped and False otherwise
            loc - current Location instance
        include_cost_function(loc, gate) - must return cost of adding gate to cluster
            returns 0 by default
        exclude_cost_function(loc, gate) - must return cost of removing gate from cluster
            returns 2 ** 31 - 1 by default
        discard_last - flag: if True, then last change made by decision_function is revoked when stop_function triggers
        """
        loc = cls(name, parent)
        loc.include(starter)
        nearest = set()
        inc_cost = {}
        exc_cost = {}

        def get_inc_cost(gate):
            if gate not in inc_cost:
                inc_cost[gate] = include_cost_function(loc, gate)
            return inc_cost[gate]

        def get_exc_cost(gate):
            if gate not in exc_cost:
                exc_cost[gate] = exclude_cost_function(loc, gate)
            return exc_cost[gate]

        def flush_cost(changed):
            for gate in changed:
                if gate in inc_cost:
                    del inc_cost[gate]
                elif gate in exc_cost:
                    del exc_cost[gate]

        def update_nearest(added, removed):
            nearest.difference_update(added)
            flush_cost(added)

            added_vicinity = set()
            for gate in added:
                added_vicinity.update(gate.vicinity(filter=lambda g: isinstance(g, Gate)))
            flush_cost(added_vicinity)
            added_vicinity.difference_update(loc.gates)
            nearest.update(added_vicinity)

            nearest.difference_update(removed)
            removed_vicinity = set(removed)
            for gate in removed:
                removed_vicinity.update(gate.vicinity())
            flush_cost(removed_vicinity)
            removed_vicinity.difference_update(loc.gates)

            for gate in removed_vicinity:
                if any(neigh in loc for neigh in gate.vicinity(filter=lambda g: isinstance(g, Gate))):
                    nearest.add(gate)

        update_nearest(added=[starter], removed=[])

        added, removed = [], []
        while not stop_function(loc):
            added, removed = decision_function(loc,
                                               ((gate, get_inc_cost(gate)) for gate in nearest),
                                               ((gate, get_exc_cost(gate)) for gate in loc.gates))
            if len(added) == len(removed) == 0:
                break
            loc.include(*added)
            loc.exclude(*removed)
            update_nearest(added, removed)

        if discard_last:
            loc.exclude(*added)
            loc.include(*removed)

        return loc
