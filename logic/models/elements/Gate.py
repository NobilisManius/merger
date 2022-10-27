from .CircuitElementBase import CircuitElementBase
from .Constant import Constant
from ..virtual.Void import Void
import subprocess
import os


class Gate(CircuitElementBase):
    """Base class for gate in circuit (combinational or sequential)

        Provides methods to iterate neighbours in circuit:
    predecessors()
    successors()
    vicinity()

    Also supports methods defined in CircuitElementBase
    """
    def __str__(self):
        """Return string representation in Verilog format"""
        pins = []
        for pin in self.inputs:
            if pin.from_:
                pins.append('.{}({})'.format(pin.label, pin.from_.label))
        for pin in self.outputs:
            if pin.to_:
                pins.append('.{}({})'.format(pin.label, pin.to_.label))
        return '{} {} ( {} )'.format(str(self.model), self.label, ', '.join(pins))
    '''
    def __str__(self):
        """Return string representation in Verilog format"""
        pins = []
        for pin in self.outputs:
            if pin.to_:
                pins.append(pin.to_.label)
        for pin in self.inputs:
            if pin.from_:
                pins.append(pin.from_.label)
        model = self.model.split('_')[0]
        model = model.replace('2', '').lower()
        return '{} ({})'.format(model, ', '.join(pins))
    '''

    def predecessor(self, pin: 'PinBase') -> 'Gate | Terminal':
        """Return gate or input terminal preceding self in circuit

        pin - input pin that gets signal from predecessor
        """
        return pin.from_.driver.from_

    def predecessors(self, filter: 'callable'= lambda el: True) -> 'Gate | Terminal':
        """Yield gates and input terminals connected to self inputs

        filter - function of one argument: takes predecessor, returns True to yield and False to omit
        """
        for inp in self.inputs:
            net = inp.from_
            if net is None:
                continue
            pred = net.driver.from_
            if filter(pred):
                yield pred

    def successors(self, filter: 'callable'= lambda el: not isinstance(el, Void)) -> 'Gate | Terminal':
        """Yield gates and output terminals connected to self outputs

        filter - function of one argument: takes successor, returns True to yield and False to omit
        """
        for out in self.outputs:
            net = out.to_
            if net is None:
                continue
            for nout in net.outputs:
                succ = nout.to_
                if filter(succ):
                    yield succ

    def vicinity(self, filter: 'callable'= lambda el: not isinstance(el, (Constant, Void))) -> 'Gate | Terminal':
        """Yield gates and terminals connected to self

        filter - function of one argument: takes neighbour, returns True to yield and False to omit
        """
        yield from self.predecessors(filter)
        yield from self.successors(filter)


class CombinationalGate(Gate):
    """Combinational gate in circuit

    Supports logic simulation via __call__ method
    Suppose g1 is and2 gate with inputs I1 and I2 and output O, then simulating it is as simple as:
        g1({'I1': 0, 'I2': 1})              # >>>{<output pin>: 0}
    See __call__'s documentation for more info

    Provides method for mapping gate's function with some cell library using ABC
    """
    def __call__(self, signals: dict, register: bool= False) -> dict:
        """Perform logic simulation, return dictionary of values on output pins

        signals - input values: keys are pin labels and values are signals or signatures
        register - if True, then simulation results are automatically written to output pins

        Returned value:
            {<pin>: <val>, ...}
            <pin> - output pin instance
            <val> - corresponding signal or signature
        """
        res = {}
        for pin in self.outputs:
            l = pin.label
            res[pin] = self.model.pin[l].function(**signals)
            if register:
                pin.register_event(res[pin])
        return res

    # TODO: ABC, lib???
    def map(self, library: 'library', filename: str) -> None:
        """Map self function with given library using ABC, write resulting circuit to file

        library - object obtained by parsing Liberty file
        filename - path to output file
        """
        if os.path.exists(filename):
            os.remove(filename)
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        genlibfile = os.path.join(ABC_DIR, library.name + '.genlib')
        library.to_genlib(genlibfile)
        input_file = os.path.join(ABC_DIR, 'input.v')

        cmdfile = os.path.join(ABC_DIR, 'cmd.txt')
        with open(cmdfile, 'w') as f:
            f.write('read_library {}\n'.format(genlibfile))
            f.write('read {}\n'.format(input_file))
            f.write('map\n')
            f.write('write_verilog {}'.format(filename))

        sinp = 'module {} ( {} );\n' \
               '\tinput {};\n' \
               '\toutput {};\n\n'.format(self.label, ', '.join(self.model.pin),
                                         ', '.join(self.model.inputs),
                                         ', '.join(self.model.outputs))

        for label, pin in self.model.outputs.items():
            func = str(pin.function)
            sinp += '\tassign {} = {};\n'.format(label, func)
        sinp += 'endmodule\n'

        with open(input_file, 'w') as f:
            f.write(sinp)

        cmd = '{} -f {}'.format(os.path.join(ABC_DIR, 'abc.exe'), cmdfile)
        subprocess.run(cmd, shell=True)

        os.remove(input_file)
        os.remove(cmdfile)
        os.remove(genlibfile)

class SequentialGate(Gate):
    """Sequential gate in circuit"""
    pass
