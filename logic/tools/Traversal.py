from copy import copy
from itertools import repeat, chain
from random import sample, choices


class Traversal:
    """Circuit traversal iterable factory

            ***Intro***
    Class instance is iterable: pairs (<element>, <step>) are returned
    Iteration is based on BFS algorithm driven by specified rules
        To get only elements use:
    order = Traversal(<configuration>)
    for el in order.no_numbers():
        <some code>

            ***Constructor***
        1. initial_front - iterable or generator
    Contains elements to be traversed on 0th step (they are returned too!)

        2. initial_marks - dictionary or iterable or generator
    If not dictionary, it must be valid input for dictionary constructor
    Marks are used to manipulate traversal by enabling or disabling paths

        3. search_function - callable
    This function is used to get element's neighbours
    search_function is called for each element in front at current step and its outputs are passed to mark_function

        4. mark_function - callable
    This function gets element and its current mark as arguments, returns new mark
    New mark is then determine whether path through element will be open or closed at the next step

        5. filter - callable
    Gets element and its mark returned by mark_function, returns True if path is open and False otherwise

        6. action - callable or None
    If not None, it's called for each element in path
    Might be useful for simple tasks like text output. Please use Core.tools.Process class for more complex tasks

            ***Basic configurations***
    Some basic processing functions are implemented in static methods:
        topological_order
        reverse_topological_order
    """
    def __init__(self,
                 initial_front: 'iterable | callable',
                 initial_marks: 'iterable | callable',
                 search_function: 'callable',
                 mark_function: 'callable',
                 filter: 'callable',
                 action: 'callable'= None):
        self.initial_front = set(initial_front() if callable(initial_front) else initial_front)
        self.initial_marks = dict(list(initial_marks()) if callable(initial_marks) else initial_marks)

        def search(front):
            for el in front:
                yield from search_function(el)

        def mark(front, marks):
            for el in self.search(front):
                new_mark = mark_function(el, marks.get(el))
                marks[el] = new_mark
                yield el, new_mark

        self.search = search
        self.mark = mark
        self.filter = filter
        self.action = action

    def __iter__(self):
        """Yield pairs (element, step)"""
        front = copy(self.initial_front)
        marks = copy(self.initial_marks)
        step = 0

        while front:
            yield from zip(front, repeat(step))
            if self.action:
                for el in front:
                    self.action(el)
            front = set(el for el, new_mark in self.mark(front, marks) if self.filter(el, new_mark))
            step += 1

    def no_numbers(self) -> 'generator':
        """Yield elements only"""
        for el, i in self:
            yield el

    @staticmethod
    def topological_order(circuit: 'Circuit') -> 'Traversal':
        """Create Traversal instance iterating circuit's terminals and gates in topological order

        Example:
            top_order = Traversal.topological_order(circuit)
            for el, i in top_order:
                <some code>
        """
        front = set(circuit.inputs).union(circuit._Circuit__constants.values())
        marks = [(gate, sum(bool(pred) for pred in gate.predecessors())) for gate in circuit.gates]
        search = lambda el: el.successors()
        mark = lambda el, old: old - 1 if old else 0
        filter = lambda gate, m: m == 0
        return Traversal(front, marks, search, mark, filter)

    @staticmethod
    def reverse_topological_order(circuit: 'Circuit') -> 'Traversal':
        """Create Traversal instance iterating circuit's terminals and gates in reverse topological order

        Example:
            rev_order = Traversal.reverse_topological_order(circuit)
            for el, i in rev_order:
                <some code>
        """
        front = circuit.outputs
        marks = [(gate, sum(len(out.to_.outputs) for out in gate.outputs if out.to_)) for gate in circuit.gates]
        marks.extend(((inp, len(inp.to_.to_.outputs) if inp.to_.to_ else 0) for inp in circuit.inputs))
        search = lambda el: el.predecessors()
        mark = lambda el, old: old - 1 if old else 0
        filter = lambda gate, m: m == 0
        return Traversal(front, marks, search, mark, filter)

    @staticmethod
    def random(circuit: 'Circuit'):
        """Yield all circuit gates in random order"""
        yield from sample(circuit.gates, len(circuit.gates))

    @staticmethod
    def random_with_replacement(circuit: 'Circuit', n: int, weights: dict= None):
        """Yield n random gates in circuit

        weights - {<Gate instance>: <weight>, ...}
        """
        if weights:
            gates, weights = zip(*((gate, weights[gate]) for gate in circuit.gates))
        else:
            gates = circuit.gates
        yield from choices(gates, weights, k=n)

    @staticmethod
    def random_nets(circuit: 'Circuit'):
        """Yield all circuit nets in random order"""
        yield from sample(circuit.nets, len(circuit.nets))

    @staticmethod
    def random_nets_with_replacement(circuit: 'Circuit', n: int, weights: dict= None):
        """Yield n random nets in circuit

        weights - {<Net instance>: <weight>, ...}
        """
        if weights:
            nets, weights = zip(*((net, weights[net]) for net in circuit.nets))
        else:
            nets = circuit.nets
        yield from choices(nets, weights, k=n)

    @staticmethod
    def initialize_all(circuit: 'Circuit') -> None:
        """Create all specific Traversal instances for circuit, write to circuit.order namespace

        Examples:
            Traversal.initialize_all(circuit)
            for el, i in circuit.order.topological:
                <some code>
            for el in circuit.order.reverse_topological.no_numbers():
                <some code>
            for el in circuit.order.random():
                <some code>
        """
        order = type('Traversal methods namespace', (), {})
        order.topological = Traversal.topological_order(circuit)
        order.reverse_topological = Traversal.reverse_topological_order(circuit)
        order.random = Traversal.random
        order.random_with_replacement = Traversal.random_with_replacement
        circuit.order = order


def fanin_reverse_topological(circuit: 'Circuit', front) -> Traversal:
    fanin = set(front)
    front_ = set(front)
    while front_:
        next_ = set()
        for gate in front_:
            next_.update((pred for pred in gate.predecessors() if pred not in fanin))
        fanin.update(next_)
        front_ = next_
    marks = [(gate, sum(bool(sucs) for sucs in gate.successors() if sucs in fanin))
             for gate in chain(circuit.gates, circuit.inputs)]
    search = lambda el: (p for p in el.predecessors() if p not in front)
    mark = lambda el, old: old - 1
    filter = lambda gate, m: m == 0
    return Traversal(front, marks, search, mark, filter)


def fanout_topological(circuit: 'Circuit', front) -> Traversal:
    fanout = set(front)
    front_ = set(front)
    while front_:
        next_ = set()
        for gate in front_:
            next_.update((sucs for sucs in gate.successors() if sucs not in fanout))
        fanout.update(next_)
        front_ = next_
    marks = [(gate, sum(bool(pred) for pred in gate.predecessors() if pred in fanout))
             for gate in chain(circuit.gates, circuit.outputs)]
    search = lambda el: (s for s in el.successors() if s not in front)
    mark = lambda el, old: old - 1
    filter = lambda gate, m: m == 0
    return Traversal(front, marks, search, mark, filter)
