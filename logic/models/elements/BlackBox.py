from .Gate import CombinationalGate
from ...datatypes.expr import BooleanFormula
from collections import namedtuple


def BlackBox(inputs: list, outputs: dict, label: str= '') -> CombinationalGate:
    """Return CombinationalGate with specified output functions:
        its model is 'BlackBox' which supports simulation but does not provide any technology-based information

    inputs - input labels
    outputs - output functions (str) by corresponding labels
    label - gate's label

    Example:
        and2_bb = BlackBox(['A1', 'A2'], {'Z': 'A1 & A2'}, label='g1')
    """
    input_models = {}
    output_models = {}
    pin_models = {}
    PinModel = namedtuple('PinModel', ['direction', 'name', 'function'])
    GateModel = namedtuple('GateModel', ['area', 'ff', 'name', 'inputs', 'outputs', 'pin'])

    for inp in inputs:
        pin = PinModel(direction='input',
                       name=inp,
                       function=None)
        input_models[inp] = pin
        pin_models[inp] = pin
    for out, func in outputs.items():
        func = BooleanFormula(func)
        func.compile()
        pin = PinModel(direction='output',
                       name=out,
                       function=func)
        output_models[out] = pin
        pin_models[out] = pin

    cell = GateModel(area=0,
                     ff={},
                     name='BlackBox',
                     inputs=input_models,
                     outputs=output_models,
                     pin=pin_models)

    return CombinationalGate(label=label, model=cell)
