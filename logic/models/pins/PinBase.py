class PinBase:
    """Base class for pin representation

    Provides interface for simulation data manipulation

    Call initialize_simulation() before processing: new item will be added to simulation_results list
    Call register_event() in order to write new event in current simulation

    Callable: returns events of the last (current) simulation

    Iterable: returns pairs (info, results) for all simulations
        Simulation info is taken from parent Circuit instance
    """
    STATE_Z = 1
    STATE_X = 2

    def __init__(self,
                 label: str,
                 model: 'PinModel'= None,
                 from_: 'Gate or Net'= None,
                 to_: 'Gate or Net'= None,
                 parent: 'Circuit'= None):
        self.model = model
        self.label = label
        self.from_ = from_
        self.to_ = to_
        self.parent = parent
        self.simulation_results = list()

        self.attach()

    def copy(self,
             label: str= None,
             from_: 'Gate or Net'= None,
             to_: 'Gate or Net'= None,
             parent: 'Circuit'= None) -> 'PinBase':
        """Copy pin another place"""
        if not label:
            label = self.label
        model = self.model
        copy = self.__class__(label, model, from_, to_, parent)
        return copy

    def attach(self) -> None:
        """Attach pin to its respective elements in circuit"""
        if hasattr(self.from_, 'attach_output_pin'):
            self.from_.attach_output_pin(self)
        if hasattr(self.to_, 'attach_input_pin'):
            self.to_.attach_input_pin(self)

    def detach(self) -> None:
        """Detach pin"""
        if hasattr(self.from_, 'detach_output_pin'):
            self.from_.detach_output_pin(self)
        if hasattr(self.to_, 'detach_input_pin'):
            self.to_.detach_input_pin(self)

    def initialize_simulation(self,
                              initializer: 'callable'= lambda self: [] if self.from_ else self.STATE_Z
                              ) -> None:
        """Append new item to simulation_results

        initializer - must take self as argument and return item to add
            If pin has a source of signal then empty event list is added by default, otherwise STATE_Z
        """
        self.simulation_results.append(initializer(self))

    def register_event(self, e: 'any') -> None:
        """Add simulation event to current event list

        e - any representation of simulation event
        """
        self.simulation_results[-1].append(e)

    def pop_event(self):
        """Return last event from last simulation and remove it from list"""
        return self.simulation_results[-1].pop()

    def __call__(self) -> list:
        """Return last (current) simulation result"""
        return self.simulation_results[-1]

    def __iter__(self) -> tuple:
        """Yield tuples (info, results) for all simulations"""
        return zip(self.parent.simulations, self.simulation_results)

    def __str__(self):
        return '{}:   {} -> {}'.format(self.label,
                                       self.from_.label if self.from_ else '',
                                       self.to_.label if self.to_ else '')
