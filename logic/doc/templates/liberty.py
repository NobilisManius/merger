"""Import this before loading Liberty files to apply customization

        Example:
from logic import Liberty
lib = Liberty.load(<path to lib>)           # default parser

import logic.doc.templates.liberty
lib = Liberty.load(<path to lib>)           # customized parser
lib = Liberty.load(<path to lib>)           # customized parser again

Liberty.set_default_parser()
lib = Liberty.load(<path to lib>)           # default parser

from importlib import reload
reload(logic.doc.templates.liberty)
lib = Liberty.load(<path to lib>)           # customized parser
"""

from logic.models.Liberty import GroupMeta, method
from logic.datatypes.expr import BooleanFormula


"""
Customize parser behaviour via classes

Step 1. Add class for group which behaviour you want to customize
    Class name must be equal to group's name (case sensitive)
    Use metaclass GroupMeta to enable configuration API
"""
class library(metaclass=GroupMeta):
    """"""
    """
    Step 2. Change settings
        Here are all available settings and their defaults
        Take not that default group parser reads all its contents, 
            custom group on contrary is empty by default!
    """
    class_name = 'library'                      # change actual class's name
    parse_fields = {'name', 'date', 'cell',     # list attributes and groups you want to parse inside this group
                    'capacitive_load_unit'}
    parse_all_attributes = False                # ... or enable parsing all attributes
    parse_all_groups = False                    # ... or all groups
    parse_all = False                           # ... or both at once
    parse_enabled_only = False                  # restrict parsed fields to those you enabled above
                                                # by default, all fields with specified parser are read in addition
                                                # i.e. parse_fields setting is redundant if you specify parser functions

    """
    Step 3. Add parser functions
        Remember not to include self in arguments as those are not class methods
        For complex attributes provide one of the following:
            - one function of several arguments
            - one function of one argument to parse each value
            - tuple of functions of one argument for all values
    """
    def name(s):
        return s.strip()

    # first way
    def capacitive_load_unit(val, unit):
        return int(val), unit

    # second way
    capacitive_load_unit = str

    # third way
    capacitive_load_unit = (int, str)

    """
    You can also add default function for attribute parsing
    It will be used inside this group instead of default function defined in LogiC.Liberty
    """

    def default(s):
        return '"{}"'.format(s.strip())

    """
    Step 4. Add postprocess functions for nested groups
        Arguments must be self, group's name and group's class instance
        Function will be called after nested group is parsed and added to data structure
    """
    def cell(self, name, inst):
        print('Cell {} parsed!'.format(name))

    """
    Step 5. Add ordinary class methods
        Use @method decorator for methods which don't start with _
        You don't need the decorator for protected and "magic" methods
        
        Use __init__ method for preprocessing
        __init__ always takes 3 agruments: self, group's name and generator used for parser
        Please don't touch the generator as this may break parser
    """
    def __init__(self, name, gen):
        print('Library {} initialized!'.format(name))

    @method
    def pop(self, cell):
        """Pop cell from cell list and return it"""
        return self.cell.pop(cell)


"""Add more classes"""


class cell(metaclass=GroupMeta):
    class_name = 'CellModel'

    area = float

    def pin(self, pin_name, pin_inst):
        if pin_inst.direction == 'input':
            self.inputs[pin_name] = pin_inst
        elif pin_inst.direction == 'output':
            self.outputs[pin_name] = pin_inst

    def __init__(self, name, gen):
        self.inputs = {}
        self.outputs = {}
        print('Cell {} initialized!'.format(name))


class pin(metaclass=GroupMeta):
    class_name = 'PinModel'

    function = BooleanFormula
    direction = str.strip
