from .PinBase import PinBase


class Terminal(PinBase):
    """Circuit I/O

    Behaviour is same as pin's except terminal itself can have attached pins
    P.S. Also it can have ID
    """
    def attach_input_pin(self, pin: 'PinBase') -> None:
        self.from_ = pin

    def attach_output_pin(self, pin: 'PinBase') -> None:
        self.to_ = pin

    def attach_pin(self, pin: 'PinBase') -> None:
        if pin.to_ == self:
            self.attach_input_pin(pin)
        elif pin.from_ == self:
            self.attach_output_pin(pin)

    def detach_input_pin(self, pin=None) -> None:
        self.from_ = None

    def detach_output_pin(self, pin=None) -> None:
        self.to_ = None

    def detach_pin(self, pin: 'PinBase') -> None:
        if self.from_ == pin:
            self.detach_input_pin()
        else:
            self.detach_output_pin()

    def successors(self, filter=lambda el: True):
        """Generate terminal's successors in circuit
        For compatibility with gates
        """
        if self.to_:
            net = self.to_.to_
            for nout in net.outputs:
                succ = nout.to_
                if filter(succ):
                    yield succ

    def predecessors(self, filter=lambda el: True):
        """Generate terminal's predecessor in circuit (typically it has only one predecessor)
        For compatibility with gates
        """
        if self.from_:
            net = self.from_.from_
            pred = net.driver.from_
            if filter(pred):
                yield pred

    def vicinity(self, filter=lambda el: True):
        """Generate terminal's neighbours in circuit
        For compatibility with gates
        """
        if self.from_:
            yield from self.predecessors(filter)
        elif self.to_:
            yield from self.successors(filter)
