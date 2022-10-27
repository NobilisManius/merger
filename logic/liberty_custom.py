"""Import this before loading Liberty files to apply customization

        Example:
from logic import Liberty
lib = Liberty.load(<path to lib>)           # default parser

import liberty_custom
lib = Liberty.load(<path to lib>)           # customized parser
lib = Liberty.load(<path to lib>)           # customized parser again

Liberty.set_default_parser()
lib = Liberty.load(<path to lib>)           # default parser

from importlib import reload
reload(liberty_custom)
lib = Liberty.load(<path to lib>)           # customized parser
"""

from logic.models.Liberty import GroupMeta, method
from logic.datatypes.expr import BooleanFormula


class library(metaclass=GroupMeta):
    class_name = 'Library'
    parse_fields = {'name', 'date', 'cell',
                    'capacitive_load_unit'}

    def name(s):
        return s.strip()

    def capacitive_load_unit(val, unit):
        return float(val), unit

    def default(s):
        return '"{}"'.format(s.strip())


class cell(metaclass=GroupMeta):
    class_name = 'CellModel'

    parse_fields = {'area', 'pin', 'ff', 'test_cell'}

    area = float

    def pin(self, pin_name, pin_inst):
        if pin_inst.direction == 'input':
            self.inputs[pin_name] = pin_inst
        elif pin_inst.direction == 'output':
            self.outputs[pin_name] = pin_inst
            if hasattr(pin_inst, 'function'):
                pin_inst.function.compile()

    def ff(self, ff_name, ff_inst):
        if hasattr(ff_inst, 'next_state'):
            ff_inst.next_state.compile()
        if hasattr(ff_inst, 'preset'):
            ff_inst.preset.compile()
        if hasattr(ff_inst, 'clear'):
            ff_inst.clear.compile()

    def __init__(self, name, gen):
        self.inputs = {}
        self.outputs = {}
        self.ff = {}


class test_cell(metaclass=GroupMeta):
    class_name = 'TestCellModel'

    parse_all = True

    def pin(self, pin_name, pin_inst):
        if hasattr(pin_inst, 'function'):
            pin_inst.function.compile()

    def ff(self, ff_name, ff_inst):
        if hasattr(ff_inst, 'next_state'):
            ff_inst.next_state.compile()
        if hasattr(ff_inst, 'preset'):
            ff_inst.preset.compile()
        if hasattr(ff_inst, 'clear'):
            ff_inst.clear.compile()



class pin(metaclass=GroupMeta):
    class_name = 'PinModel'

    parse_fields = {'direction',
                    'capacitance',
                    'fall_capacitance',
                    'rise_capacitance',
                    'fall_capacitance_range',
                    'rise_capacitance_range',
                    'max_capacitance',
                    'function',
                    'signal_type',
                    'nextstate_type'}

    nextstate_type = str
    direction = str
    function = BooleanFormula
    signal_type = str
    default = float


class ff(metaclass=GroupMeta):
    """Trigger info"""
    parse_all_attributes = True

    next_state = BooleanFormula
    preset = BooleanFormula
    clear = BooleanFormula
    default = str


