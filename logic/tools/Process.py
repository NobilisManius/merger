from .Traversal import *
from ..models import elements, pins
from ..datatypes import Signature
from ..datatypes.expr import BooleanFormula
from ..exceptions import SimulationError
from functools import reduce
from operator import or_


class Process:
    """Circuit processing function factory

    Instances of this class are functions which perform some action on circuits
    The way circuits are processed depends on what arguments you pass when initialize Process instance
    In order to use Process instance fn, call it with arguments:
        fn(<circuit>, <input for processing>)

            ***Constructor***
    Processing function consists of 5 parts:

        1. initializer - callable
    This function is called when processing starts
    It receives same arguments as Process instance itself and must prepare circuit for processing

        2. iterator - generator
    This is traversal function. It receives circuit as arguments and yields its elements in specific order
    Core.tools.Traversal class may be useful for custom processing function creation

        3. processers - dict: {<type>: <action>, ...}
    Each element returned by iterator is then passed to processer of its type
    Processer returns iterable of pairs: (<element>, <result>) - its usage will be explained further
        Example:
    Assume iterator yields element of type Net
    If processers dict has key Net, then its respective value is a function to be called:
        processers[Net](element)
    Otherwise element is just skipped

        4. registrators - dict: {<type>: <action>, ...}
    Each pair (<element>, <result>) returned by any processer is passed to corresponding registrator
    Registrator takes 2 arguments: element and value. Its job is to write given value in a proper way

        5. observer - callable
    Finally, when processing is done, you might want to see some result immediately
    Process calls observer with circuit as argument and returns its output
    
            ***Basic configurations***
    Some basic processing functions are implemented in static methods:
        simulation - logic simulation with given inputs
        observability_back_propagation - back propagation of output ODC masks (all-ones by default)
    """
    def __init__(self,
                 initializer: 'callable',
                 iterator: 'callable',
                 processers: 'dict',
                 registrators: 'dict',
                 observer: 'callable'):
        self.initialize = initializer
        self.traverse = iterator
        self.processers = processers
        self.registrators = registrators
        self.observer = observer

    def __call__(self, circuit: 'Circuit', *args, **kwargs):
        self.initialize(circuit, *args, **kwargs)
        for el in self.traverse(circuit):
            process = self.processers.get(type(el))
            if not process:
                continue
            for el2, res in process(el):
                register = self.registrators.get(type(el2))
                if register:
                    register(el2, res)
        return self.observer(circuit)


def simulation(name: str= None, vector_length: int= 10000):
    """Return Process instance performing circuit's logic simulation on call
    name - simulation name
    vector_length - signature length
    faults - dictionary of stuck-at values on circuit nets
    Example:
        sim = Process.simulation(vector_length=1000)
        outputs = sim(circuit, inputs)

        inputs is {<input label>: <value>, ...}
        outputs is {<output label>: <value>, ...}
    """
    faults_ = {}

    def initialize(circuit, inputs, faults=None):
        faults_.clear()
        if faults is not None:
            faults_.update(faults)
        Signature.setlength(vector_length)
        circuit.initialize_process(name if name else 'simulation')
        for inp in circuit.inputs:
            pin = inp.to_
            pin.register_event(inputs[inp.label])
        if hasattr(circuit, 'clock_inps'):
            for inp in circuit.clock_inps:
                pin = inp.to_
                pin.register_event(0)

    def traverse(circuit):
        order = Traversal.topological_order(circuit)
        return order.no_numbers()

    def process_terminal(term):
        pin = term.to_
        if pin is None:
            return {}
        net = pin.to_
        yield (net, pin.pop_event())

    def process_gate(gate):
        inputs = {pin.label: pin()[-1] for pin in gate.inputs}
        for out, sign in gate(inputs).items():
            yield (out.to_, sign)

    def process_constant(const):
        yield from ((pin.to_, const()) for pin in const.fanout)

    def register_net(net, val):
        if net in faults_:
            val = faults_[net]
        pins = {net.driver}
        pins.update(net.outputs)
        for pin in pins:
            pin.register_event(val)

    def observe(circuit):
        return {out.label: out.from_()[-1] for out in circuit.outputs}

    processers = {elements.CombinationalGate: process_gate,
                  pins.Terminal: process_terminal,
                  elements.Constant: process_constant}
    registrators = {elements.Net: register_net}

    return Process(initialize, traverse, processers, registrators, observe)


def resimulation(vector_length: int= 10000):
    """Simulate circuit with slightly changed input, omit computation when possible
    Return dictionary of nets with switched value:
        {<Net obj>: (<old val>, <new val>)}
    """
    faults_ = {}
    resim_required = set()
    switched_inputs = set()
    switched_nets = {}
    simID_ = 0

    def initialize(circuit, inputs, simID, faults=None):
        nonlocal simID_
        simID_ = simID
        switched_nets.clear()
        switched_inputs.clear()
        switched_inputs.update(map(circuit.inputs.by_name, inputs))
        faults_.clear()
        if faults is not None:
            faults_.update(faults)
            switched_inputs.update(net.driver.from_ for net in faults)
        resim_required.clear()
        Signature.setlength(vector_length)

        for inp in circuit.inputs:
            if inp.label not in inputs:
                continue
            resim_required.update(inp.successors())
            pin = inp.to_
            old_val = pin.simulation_results[simID][-1]
            new_val = inputs[inp.label]
            pin.simulation_results[simID][-1] = new_val
            switched_nets[inp.to_.to_] = (old_val, new_val)

    def traverse(circuit):
        return fanout_topological(circuit, switched_inputs).no_numbers()

    def register_net(net, val):
        if net in faults_:
            val = faults_[net]
        old_val = net.driver.simulation_results[simID_][-1]
        switched = old_val != val
        pins = {net.driver}
        pins.update(net.outputs)
        for pin in pins:
            pin.simulation_results[simID_][-1] = val
        if switched:
            resim_required.update(pin.to_ for pin in net.outputs)
            switched_nets[net] = (old_val, val)

    def process_gate(gate):
        if gate not in resim_required:
            yield from ((out.to_, out.simulation_results[simID_][-1]) for out in gate.outputs)
            return
        inputs = {pin.label: pin.simulation_results[simID_][-1] for pin in gate.inputs}
        for out, sign in gate(inputs).items():
            yield (out.to_, sign)

    def process_terminal(term):
        pin = term.to_
        if pin is None:
            return {}
        net = pin.to_
        yield (net, pin.simulation_results[simID_][-1])

    def process_constant(const):
        yield from ((pin.to_, const()) for pin in const.fanout)

    def observe(circuit):
        return switched_nets

    processers = {elements.CombinationalGate: process_gate,
                  pins.Terminal: process_terminal,
                  elements.Constant: process_constant}
    registrators = {elements.Net: register_net}

    return Process(initialize, traverse, processers, registrators, observe)


def error_observability(simulation_ID=0):
    """Return Process instance for error propagation

    simulation_ID - index of corresponding simulation

    Warning: simulation must precede error propagation!

    Example:
        sim = Process.simulation(vector_length=1000)
        err_obs = error_observability(simulation_ID=0)
        sim(circuit, inputs)
        out_errors = err_obs(circuit, errors)

        inputs is {<input label>: <value>, ...}
        errors is {<gate instance> | <input terminal instance>: <value>, ...}
        out_errors is {<output label>: <value>, ...}

    Signatures of erroneous gates are obtained by XORing their error-free signatures with respective error values
    Similarly, output errors are computed as <error-free signature> ^ <faulty signature>
    """
    errors = {}

    def get(pin):
        return pin.simulation_results[simulation_ID][-1]

    def reg(pin, val):
        pin.simulation_results[simulation_ID].append(val)

    def pop(pin):
        return pin.simulation_results[simulation_ID].pop()

    def initialize(circuit, errors_):
        nonlocal errors
        errors = errors_

    def traverse(circuit):
        order = fanout_topological(circuit, set(errors))
        return order.no_numbers()

    def process_gate(gate):
        if gate in errors:
            for out in gate.outputs:
                err_sign = get(out) ^ errors[gate]
                yield out.to_, err_sign
        else:
            inputs = {pin.label: pop(pin) if len(pin.simulation_results[simulation_ID]) > 1
                      else get(pin) for pin in gate.inputs}
            for out in gate.outputs:
                func = out.model.function
                yield out.to_, func(**inputs)

    def process_terminal(term):
        pin = term.to_
        if pin is None:
            return {}
        net = pin.to_
        err_sign = get(pin) ^ errors[pin.from_]
        yield (net, err_sign)

    def register_net(net, val):
        for pin in net.outputs:
            reg(pin, val)

    def observe(circuit):
        return {out.label: pop(out.from_) ^ get(out.from_) for out in circuit.outputs
                if len(out.from_.simulation_results[simulation_ID]) > 1}

    processers = {elements.CombinationalGate: process_gate,
                  pins.Terminal: process_terminal}

    registrators = {elements.Net: register_net}

    return Process(initialize, traverse, processers, registrators, observe)


def observability_simulation(name: str= None, simulation_ID=0):
    """Return Process instance computing ODC by error simulation
    name - process name
    simulation_ID - index of corresponding simulation
    Warning: logic simulation must precede ODC computation!
    Example:
        sim = Process.simulation(vector_length=1000)
        odcsim = Process.observability_simulation()
        sim(circuit, inputs)
        odcsim(circuit)
        inputs is {<input label>: <value>, ...}
    """
    circuit = None
    def initialize(circuit_):
        nonlocal circuit
        circuit = circuit_
        circuit.initialize_process(name if name else 'ODC simulation')
        for out in circuit.outputs:
            pin = out.from_
            pin.register_event(Signature.all_ones)

    def traverse(circuit):
        order = Traversal.reverse_topological_order(circuit)
        return order.no_numbers()

    def process_terminal(term):
        pin = term.to_
        if pin is None:
            return {}
        net = pin.to_
        if len(net.outputs) == 1:
            dest, = net.outputs
            yield pin, dest()[0]
        else:
            err_obs = error_observability(simulation_ID)
            errors = err_obs(circuit, {term: Signature.all_ones})
            yield pin, reduce(or_, errors.values(), 0)

    def process_gate(gate):
        if len(gate.outputs) == 1:
            out_pin, = gate.outputs
            net = out_pin.to_
            if not net:
                yield out_pin, 0
                for inp in gate.inputs:
                    yield inp, 0
                return
            if len(net.outputs) == 1:
                dest, = net.outputs
                out_odc = dest()[0]
            else:
                err_obs = error_observability(simulation_ID)
                errors = err_obs(circuit, {gate: Signature.all_ones})
                out_odc = reduce(or_, errors.values(), 0)
            yield out_pin, out_odc
            inputs = {pin.label: pin.simulation_results[simulation_ID][-1] for pin in gate.inputs}
            inputs[out_pin.label] = out_odc
            for pin in gate.inputs:
                odc_func = gate.model.inputs[pin.label].odc_function
                odc = odc_func(**inputs)
                yield pin, odc
        else:
            raise TypeError('Multi-output gates are not supported')

    def register_pin(pin, val):
        pin.register_event(val)

    def observe(circuit):
        return {inp.label: inp.to_()[0] for inp in circuit.inputs}

    processers = {elements.CombinationalGate: process_gate,
                  pins.Terminal: process_terminal}
    registrators = {pins.PinBase: register_pin}

    return Process(initialize, traverse, processers, registrators, observe)
