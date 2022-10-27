from ...exceptions import ConnectivityError


class CircuitElementBase:
    """Base class for circuit elements: gates and nets

    Provides interface for adding and accessing pins

        Add pins:
    attach_input_pin()
    attach_output_pin()
    attach_pin()

        Remove pins:
    detach_input_pin()
    detach_output_pin()
    detach_pin()

        Create functional copy:
    copy()
    """
    def __init__(self,
                 label: str,
                 model=None,
                 pins: 'Iterable'= None,
                 parent: 'Circuit'= None,
                 ID: int= 0):
        """
        label - element name
        model - reference model from library
        pins - list of PinBase instances
        parent - Circuit instance which current element belongs to
        ID - index of element in circuit's list of elements
        """
        self.label = label
        self.model = model
        self.pins = {pin for pin in pins} if pins else set()
        self.inputs = set()
        self.outputs = set()
        for pin in self.pins:
            if pin.to_ == self:
                self.inputs.add(pin)
            elif pin.from_ == self:
                self.outputs.add(pin)
            else:
                raise ConnectivityError('Attempted to add unrelated pin {} to {}'.format(pin.label, self.label))
        self.parent = parent
        self.ID = ID

    def attach_input_pin(self, pin: 'PinBase') -> None:
        """Add input pin"""
        self.inputs.add(pin)
        self.pins.add(pin)
        pin.to_ = self

    def attach_output_pin(self, pin: 'PinBase') -> None:
        """Add output pin"""
        self.outputs.add(pin)
        self.pins.add(pin)
        pin.from_ = self

    def attach_pin(self, pin: 'PinBase') -> None:
        """Add pin, raise ConnectivityError if pin.to_ and pin.from_ are both not self"""
        if pin.to_ == self:
            self.attach_input_pin(pin)
        elif pin.from_ == self:
            self.attach_output_pin(pin)
        else:
            raise ConnectivityError('Attempted to add unrelated pin {} to {}'.format(pin.label, self.label))

    def detach_input_pin(self, pin: 'PinBase') -> None:
        """Remove input pin"""
        self.inputs.remove(pin)
        self.pins.remove(pin)
        pin.to_ = None

    def detach_output_pin(self, pin: 'PinBase') -> None:
        """Remove output pin"""
        self.outputs.remove(pin)
        self.pins.remove(pin)
        pin.from_ = None

    def detach_pin(self, pin: 'PinBase') -> None:
        """Remove pin, raise ConnectivityError if pin.to_ and pin.from_ are both not self"""
        if pin.to_ == self:
            self.detach_input_pin(pin)
        elif pin.from_ == self:
            self.detach_output_pin(pin)
        else:
            raise ConnectivityError('Attempted to remove unrelated pin {} to {}'.format(pin.label, self.label))

    def __str__(self):
        return self.label

    def copy(self,
             label: str= None,
             pins: 'Iterable'= None,
             parent: 'Circuit'= None):
        """Copy element to another place"""
        if not label:
            label = self.label
        model = self.model
        copy = self.__class__(label, model, pins, parent)
        return copy
