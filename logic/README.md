# Installation

1. Clone this repository
2. Install pyeda wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/

Python 3.7+ is required.

# Features

## Verilog parser

Current parser works with synthesized Verilog. 
Use Circuit class to read or write your circuit:

    from logic import Circuit
    circuit = Circuit.from_verilog("path_to_circuit.v")
    circuit.to_verilog("path_to_output_circuit.v")

_to_verilog()_ method renames all wires by default to avoid collisions, 
use _rename=False_ to keep the original names.

## Liberty parser

In order to perform simulations or some form of analysis, library data is needed.
Use Liberty parser to read your .lib file:

    from logic import Liberty
    lib = Liberty.load("path_to_library.lib")

Most of the data contained in .lib file might be redundant for your goal, 
so you might want to customize the parser. 
For that you'll need to set up your desired library structure in separate file
and import it before parsing:

    from logic import Liberty
    import logic.doc.templates.liberty
    lib = Liberty.load("path_to_library.lib")

Use example in _doc/templates/liberty.py_ and read the docstrings in _models/Liberty.py_
for more info on customization.