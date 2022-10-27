"""This module provides tools for work with arbitrary expressions and also class for boolean expression processing

ExpressionBase class provides basic methods for expression parsing and processes parentheses and commas only
Hence, the only thing you can create by calling ExpressionBase instances is nested tuple

In order to enable actual computation you must first create corresponding Operator instances (more info below)
Then you must create child class for ExpressionBase with its own operators and constants

-----------------------------------------------------------------------------------------------------------------------

            Parser features
- Whitespaces are ignored
- Any valid float numbers are recognized as constants
- Any other char sequences except parentheses, commas and operator symbols are recognized as literals
    Although it's better to use valid python variable names
- Literals store their value, so there's no need to re-assign unchanged values; init value for all literals is 0
- Commas create tuples
- Parentheses change operation order
- String representation of parsed expression is equivalent to initial expression
    However, redundant parentheses may disappear

-----------------------------------------------------------------------------------------------------------------------

            Operator initialization
Operator(name, symbol, function, precedence, operand_flags)
    name - any suitable string representation
    symbol - operator's symbol in expression, must be precisely one character
    function - callable object that performs corresponding action on operands and returns operation result
    precedence - operator's importance: operations with higher precedence are performed first
        please use values from 0 to 99 for precedence, otherwise parentheses may be processed incorrectly
    operand_flags - flags of presence of left and right operand, respectively
        default value is (1, 1), i.e. binary operator is created
        set (0, 1) for unary operator with operand on the right and (1, 0) if operand is on the left

See class BooleanFormula for example

-----------------------------------------------------------------------------------------------------------------------

            Creating your own algebra
Just create new class using ExpressionMeta and populate it with operators and constants!

Example:
    op_add = Operator('add', '+', operator.add, 0)
    op_sub = Operator('sub', '-', operator.sub, 0)
    op_mul = Operator('mul', '*', operator.mul, 1)
    op_div = Operator('div', '/', operator.truediv, 1)

    class ArithmeticExpression(metaclass=ExpressionMeta):
        operators = [op_add, op_sub, op_mul, op_div]
        constants = {'pi': 3.14}

    expr = ArithmeticExpression('pi / (3.14 + x), pi / (1.57 * y)')
    expr.compile()
    expr(x=0, y=1)                                                      # >>>(1.0, 2.0)
    expr(y=2)                                                           # >>>(1.0, 1.0)
"""


from .Signature import Signature
from operator import and_, or_, xor
from copy import copy
from pyeda.inter import ast2expr
import pyeda.boolalg.expr as edaxpr
import re


class Literal:
    """Variable in expression

    Contains its name and value

    Callable: returns self value
    """
    def __init__(self, name: str, val=None):
        self.name = name
        if val is not None:
            self.val = val
            return
        try:
            self.val = float(name)
        except ValueError:
            self.val = 0

    def set(self, val) -> None:
        """Set value"""
        self.val = val

    def __call__(self):
        """Return value"""
        return self.val

    def __str__(self):
        """Return name"""
        return self.name


class Group:
    """Sequence of operands in expression
    Group represents multiple values stacked together such as python tuple

    Fields:
        members - list of operands (each must be callable and have string representation)
        separator - char sequence separating members in string representation
        braces - first and last char for string representation of group
            group is closed for extension if braces are set and open otherwise

    Operators:
        +   Merges group with other group / operand (see __add__ method's documentation)

    Callable: returns tuple of values of self operands
    """
    def __init__(self, *members: 'callable', separator: str =', ', braces: str =''):
        self.members = list(members)
        self.separator = separator
        self.braces = braces

    def __add__(self, other: 'callable'):
        """Create new group containing self and other

        other - Group or valid operand

        If input group is open, then all its operands are included in output group,
        otherwise input group is included as a single operand
        """
        left = [self] if self.braces else [*self.members]
        if isinstance(other, Group):
            if other.braces:
                right = [other]
            else:
                right = [*other.members]
        else:
            right = [other]
        return Group(*left, *right, separator=self.separator, braces='')

    def __radd__(self, other: 'callable'):
        """Create new group containing other and self

        See __add__ method for details
        """
        left = [other]
        right = [self] if self.braces else [*self.members]
        return Group(*left, *right, separator=self.separator, braces='')

    def close(self, braces: str= '()') -> None:
        """Set braces and close group for extension"""
        self.braces = braces

    def __str__(self):
        return self.braces[:1] + self.separator.join([str(m) for m in self.members]) + self.braces[1:]

    def __call__(self) -> tuple:
        """Return tuple of values of self operands"""
        return tuple(m() for m in self.members)


class Operator:
    """Operator class

    Fields:
        name - operator name
        symbol - operation symbol in formulae
        function - callable, must take operand values and return operation result
        operand_flags - tuple of bool flags: (<left operand required>, <right operand required>)
        precedence - operator precedence: operations with higher precedence are performed first

    Callable: takes operand values, returns operation result
    """
    def __init__(self, name: str, symbol: 'char', function: 'callable', precedence: int, operand_flags: tuple=(1, 1)):
        self.name = name
        self.symbol = symbol
        self.operand_flags = operand_flags
        self.precedence = precedence
        self.function = function

    def __call__(self, *operands):
        """Return operation result"""
        return self.function(*operands)

    def __str__(self):
        return self.symbol


class Operation:
    """Operation class
    Refers to certain operation in expression

    Fields:
        operator - respective Operator instance
        operands - list of operands (each operand must be callable and have string representation)

    Callable: returns operation result
    """
    def __init__(self, operator: Operator, *operands: 'callable'):
        self.operator = operator
        self.operands = operands

        opl, opr = self.operator.operand_flags
        self._fmt = ('{}' + str(operator)) if not opr else \
                    (str(operator) + '{}') if not opl else \
                    ('{} ' + str(operator) + ' {}')

    def __call__(self):
        """Return operation result on values returned by operands"""
        return self.operator(*[op() for op in self.operands])

    def __str__(self):
        ops = []
        opl, opr = self.operator.operand_flags
        if opl:
            op = self.operands[0]
            if isinstance(op, Operation) and op.operator.precedence < self.operator.precedence:
                ops.append('({})'.format(op))
            else:
                ops.append('{}'.format(op))
        if opr:
            op = self.operands[-1]
            if isinstance(op, Operation) and op.operator.precedence <= self.operator.precedence:
                ops.append('({})'.format(op))
            else:
                ops.append('{}'.format(op))
        return self._fmt.format(*ops)


class ExpressionBase:
    """Base class for any expression parser
    Handles parentheses and commas only
    Use ExpressionMeta metaclass to create your own algebra and enable actual computation
    See example in module documentation and BooleanFormula class

    -----------------------------------------------------------------------------------------------------------

            Fields
    formula - initial expression
    literals - dictionary of literals: keys are string representations and values are Literal instances
        Empty by default, filled automatically by compile method
    result - callable: returns evaluation result using current literal values
        None until compile method is called

            Attributes
    _constants - dict of available constants and their respective values
    _operators - dict of available operators by their string representations

    We recommend to use metaclass instead of derivation to create child class
        so that you don't need to directly modify protected attributes _constants and _operators

    -----------------------------------------------------------------------------------------------------------

            Computation
    In order to compute something you must create expression instance and compile it
    Once compiled, expression instance can be called as function multiple times with different inputs

    Example:
        expr = ExpressionBase('(a, (b, c), d)')
        expr.compile()
        expr(a=1, b=2, c=3, d=4)                        # >>>(1, (2, 3), 4)
        expr(d=3, c=1, b=0, a='x')                      # >>>('x', (0, 1), 3)

    Expression itself does not require its inputs to be of the certain type
    However, errors may occur if your custom operators in child class don't support provided input type

    -----------------------------------------------------------------------------------------------------------

            Format change
    - rename_literals
    - change_operator

    change_operator doesn't work with parentheses and commas,
        so suppose for example that you have child class with interchangeable operators & and *
    Tale note that both old and new operators must be supported by your child class

    Example:
        expr = ExpressionChild('(a, (b * c), d)')
        expr.compile()
        expr.rename_literals({'a': x, 'b': y})
        str(expr)                                       # >>>'(x, (y * c), d)'
        expr.change_operator('*', '&')
        str(expr)                                       # >>>'(x, (y & c), d)'
    """
    _constants = {}
    _operator_stack = []
    _operand_stack = []

    @staticmethod
    def _rb(x):
        __class__._operators['('].precedence = 100
        return x

    @staticmethod
    def _lb(x):
        __class__._operators['('].precedence = -3
        if isinstance(x, Group):
            x.close('()')
        return x

    @staticmethod
    def _gr(x, y):
        if isinstance(x, Group) or isinstance(y, Group):
            return x + y
        else:
            return Group(x, y)

    _special_symbols = {'(': _lb.__func__,
                        ')': _rb.__func__,
                        ',': _gr.__func__}

    _operators = {'(': Operator('lb', '(', None, -3, (0, 1)),
                  ')': Operator('rb', ')', None, -2, (1, 0)),
                  ',': Operator('comma', ',', None, -1)}

    def __init__(self, s: str):
        self.formula = re.sub('\s+', '', s)
        self.literals = {}
        self.result = None

    def _push_literal(self, name):
        if name not in self.literals:
            self.literals[name] = self._constants.get(name, Literal(name))
        return self.literals[name]

    def _parse(self):
        tokens = []
        prev_pos = -1

        def check(p1, p2=None):
            l = self.formula[p1:p2].strip()
            if l:
                tokens.append(l)
                self._push_literal(l)

        for pos, ch in enumerate(self.formula):
            if ch in self._operators:
                check(prev_pos + 1, pos)
                tokens.append(ch)
                prev_pos = pos
        check(prev_pos + 1)

        return tokens

    def compile(self) -> None:
        """Parse self formula and break it into set of operations, enable __call__ method"""
        tokens = self._parse()

        def apply_operator():
            op = self._operator_stack[-1]
            operands = []
            for opflag in reversed(op.operand_flags):
                if opflag:
                    operands.append(self._operand_stack.pop())
            if op.symbol in self._special_symbols:
                self._operand_stack.append(self._special_symbols[op.symbol](*reversed(operands)))
            else:
                self._operand_stack.append(Operation(op, *reversed(operands)))
            self._operator_stack.pop()

        for tok in tokens:
            if tok in self._operators:
                op = self._operators[tok]
                prec = op.precedence
                opleft, opright = op.operand_flags

                if opleft:
                    while self._operator_stack:
                        prev_op = self._operator_stack[-1]
                        if prev_op.precedence >= prec:
                            apply_operator()
                        else:
                            break

                self._operator_stack.append(op)
                if not opright:
                    apply_operator()
            else:
                self._operand_stack.append(self._constants[tok] if tok in self._constants
                                           else self.literals[tok])

        while self._operator_stack:
            apply_operator()

        self.result = self._operand_stack[0]
        self._operand_stack.clear()

    def change_operator(self, old: str, new: str) -> None:
        """Change operator old to operator new
        Operators must be both binary or both unary

        old, new - string representations of respective operators

        Expression must be compiled first!
        """
        old_ = self._operators[old]
        new_ = self._operators[new]
        if sum(old_.operand_flags) != sum(new_.operand_flags):
            raise ValueError('Operators {} and {} have different number of operands'.format(old, new))

        def change_recursive(operation):
            if str(operation.operator) == old:
                operation.__init__(new_, *operation.operands)
            for operand in operation.operands:
                if isinstance(operand, Operation):
                    change_recursive(operand)

        if isinstance(self.result, Operation):
            change_recursive(self.result)
        self.formula = str(self.result)

    def rename_literals(self, lit_map: dict) -> None:
        """Rename literals according to lit_map = {<old name>: <new name>, ...}
        Dictionary keys don't have to cover all literals

        Expression must be compiled first!
        """
        for old, new in lit_map.items():
            if old in self.literals:
                lit = self.literals.pop(old)
                lit.name = new
                self.literals[new] = lit
        self.formula = str(self.result)

    def __call__(self, **kwargs):
        """Return expression evaluation result

        kwargs - literal values
            Literal that does not receive any input keeps its previous value
            KeyError is raised if unknown literal is passed

        Expression must be compiled first!
        """
        for l, val in kwargs.items():
            if l in self.literals:
                self.literals[l].set(val)
        return self.result()

    def __str__(self):
        return self.formula


class ExpressionMeta(type):
    """Provides interface for safe ExpressionBase derivation without modifying its protected attributes
    See module documentation and BooleanFormula class for examples
    """
    def __new__(mcs, name, bases, attrs):
        bases = bases + (ExpressionBase,)
        if 'operators' in attrs:
            ops = copy(ExpressionBase._operators)
            ops.update((op.symbol, op) for op in attrs.pop('operators'))
            attrs['_operators'] = ops
        if 'constants' in attrs:
            cs = copy(ExpressionBase._constants)
            cs.update((name, Literal(name, val)) for name, val in attrs.pop('constants').items())
            attrs['_constants'] = cs
        Expr = type.__new__(mcs, name, bases, attrs)
        return Expr


class BooleanFormula(metaclass=ExpressionMeta):
    """Boolean formula class

    -----------------------------------------------------------------------------------------------------------

    Allowed operations:
        &   bitwise logic AND
        |   bitwise logic OR
        ^   bitwise logic XOR
        !   bitwise inversion (right operand)
        '   bitwise inversion (left operand)

    Allowed constants:
        0   logic 0
        1   logic 1 (according to signature length)

    Example:
        f = BooleanFormula('a & b')
        f.compile()
        f(a=1, b=0)                                    # >>>0
        f(a=1, b=1)                                    # >>>1

        g = BooleanFormula('x ^ 1')
        g.compile()
        g(x=1)                                         # >>>0

    -----------------------------------------------------------------------------------------------------------

            Type conversion
    - from_pyeda_expr
    - to_pyeda_expr

    Example:
        a, b = map(pyeda.inter.exprvar, 'ab')
        f = BooleanFormula.from_pyeda_expr(a & b)
        str(f)                                          # >>>'a & b'
        f.to_pyeda_expr()                               # >>>And(a, b)

    Warning: PyEDA operators are restricted to And, Or, Xor and Not
    """
    operators = [Operator('not', '!', Signature.invert, 3, (0, 1)),
                 Operator('not', '\'', Signature.invert, 3, (1, 0)),
                 Operator('and', '&', and_, 2),
                 Operator('xor', '^', xor, 1),
                 Operator('or', '|', or_, 0),
                 Operator('and', '*', and_, 2),
                 Operator('or', '+', or_, 0)]
    constants = {'0': 0,
                 '1': Signature.all_ones}

    _pyeda_operations = {'And': operators[2],
                         'Or': operators[4],
                         'Xor': operators[3],
                         'Not': operators[0]}

    def __call__(self, **kwargs):
        self._constants['1'].set(Signature.all_ones)
        return ExpressionBase.__call__(self, **kwargs)

    @classmethod
    def _to_pyeda_ast(cls, expr):
        """Auxiliary"""
        if isinstance(expr, Literal):
            if expr.name in cls._constants:
                return ('const', int(expr.name))
            return ('var', (expr.name), ())
        elif isinstance(expr, Operation):
            return (expr.operator.name, *[cls._to_pyeda_ast(op) for op in expr.operands])

    def to_pyeda_expr(self) -> 'pyeda.boolalg.expr.Expression':
        """Convert expression to PyEDA format"""
        return ast2expr(self._to_pyeda_ast(self.result))

    def _from_pyeda_expr(self, expr):
        """Auxiliary"""
        if isinstance(expr, edaxpr.Variable):
            lit = self._push_literal(expr.name)
            return lit
        elif isinstance(expr, edaxpr.Complement):
            lit = self._push_literal(expr.inputs[0].name)
            return Operation(self._operators['!'], lit)
        elif expr.NAME in self._pyeda_operations:
            operands = [self._from_pyeda_expr(operand) for operand in expr.xs]
            while len(operands) > 2:
                operands.append(Operation(self._pyeda_operations[expr.NAME], operands.pop(), operands.pop()))
            return Operation(self._pyeda_operations[expr.NAME], *operands)
        else:
            raise ValueError('Cannot convert operator {}'.format(expr.NAME))

    @classmethod
    def from_pyeda_expr(cls, expr: 'pyeda.boolalg.expr.Expression'):
        """Convert PyEDA expression to cls"""
        ex = BooleanFormula('')
        ex.result = ex._from_pyeda_expr(expr)
        ex.formula = str(ex.result)
        return ex
