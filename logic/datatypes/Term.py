from pyeda.inter import exprvar, point2term
from pyeda.boolalg.expr import Variable, Complement
from operator import attrgetter


class Term(tuple):
    """Tuple of PyEDA variables and complements

    -----------------------------------------------------------------------------------------------------------

            Creation methods
    - default constructor
    - from_str
    - from_dict
    - from_point

    Examples:
        a, b = map(pyeda.inter.exprvar, 'ab')
        Term(a, ~b)                                 # >>>(a, ~b)
        Term.from_str('a ~b')                       # >>>(a, ~b)
        Term.from_dict({'a': 1, 'b': 0})            # >>>(a, ~b)
        Term.from_point({a: 1, b: 0})               # >>>(a, ~b)

    -----------------------------------------------------------------------------------------------------------

            Type conversion
    - to_str
    - to_point

    Examples:
        t = Term(a, ~b)
        t.to_str()                                  # >>>'a ~b'
        t.to_point()                                # >>>{a: 1, b: 0}

    -----------------------------------------------------------------------------------------------------------

            Operations
    - >, >=, <, <=
    - + (union)
    - * (intersection)
    - expand
    - complements

    Examples:
        t1 = Term(a, b)
        t2 = Term(a, b, ~c)                         # t2's domain is a subset of t1's domain
        t3 = Term(~c, d)                            # t3's domain intersects t1's and t2's domains

        t1 > t2                                     # >>>True
        t2 < t1                                     # >>>True

        t1 > t3                                     # >>>False
        t1 < t3                                     # >>>False
        t2 < t3                                     # >>>False

        t1 + t2                                     # >>>(a, b)
        t1 + t3                                     # >>>ValueError (see __add__ method's description)
        t2 * t3                                     # >>>(a, b, ~c, d)

        t2.expand(b)                                # >>>(a, ~c)

        list(t1.complements())                      # >>>[(~a, b), (a, ~b)]
    """

    __slots__ = []

    def __new__(cls, *args: 'Variable | Complement'):
        if all(isinstance(arg, (Variable, Complement)) for arg in args):
            top = attrgetter('top')
            new = tuple.__new__(cls, sorted(args, key=top))
            return new
        raise ValueError('All members of term must be PyEDA variables or complements')

    @classmethod
    def from_str(cls, s: str) -> 'Term':
        """Create term from string representation
        Literals in s must be separated by one space
        Negated literals must have '~' before name

        Examples of valid strings: 'a b', 'a ~b', '~a0 ~a1 a2'
        """
        svars = s.split()
        lit = lambda name: exprvar(name.lstrip('~'))
        point = {lit(svar): svar[0] != '~' for svar in svars}
        return cls(*point2term(point))

    @classmethod
    def from_dict(cls, d: dict) -> 'Term':
        """Create term from dictionary
        Keys are literal names and values are 0 for negated and 1 for positive

        Example:
            from_dict({'a0': 1, 'a1': 0, 'a2': 0})      # >>>(a0, ~a1, ~a2)
        """
        point = {exprvar(name): val for name, val in d.items()}
        return cls(*point2term(point))

    @classmethod
    def from_point(cls, p: dict) -> 'Term':
        """Create term from dictionary
        Keys are PyEDA variables, values are 0 or 1

        Example:
            a0, a1, a2 = map(pyeda.inter.exprvar, 'abc')
            from_point({a0: 1, a1: 0, a2: 0})       # >>>(a0, ~a1, ~a2)
        """
        return cls(*point2term(p))

    def to_point(self) -> dict:
        """Convert to dictionary (the opposite of from_point)"""
        return dict(((lit, 1) if isinstance(lit, Variable) else (lit.inputs[0], 0) for lit in self))

    def to_str(self) -> str:
        """Convert to string representation (the opposite of from_str)"""
        return ' '.join(lit.name if isinstance(lit, Variable) else ('~' + lit.top.name) for lit in self)

    def expand(self, lit: 'Variable | Complement') -> 'Term':
        """Return the same term without given literal

        Example:
            t = Term(a, b, ~c)
            t.expand(~c)        # >>>(a, b)
        """
        new_vars = [v for v in self if v is not lit]
        if len(new_vars) == len(self):
            raise ValueError('Variable or Complement {} is not in term'.format(lit))
        return Term(*new_vars)

    def complements(self) -> 'Term':
        """Yield all complementary terms
        Complementary terms are the same terms with precisely one literal inverted

        Example:
            t = Term(a, b)
            list(t.complements())       # >>>[(~a, b), (a, ~b)]
        """
        literals = list(self)
        for i in range(len(self)):
            literals[i] = ~(literals[i])
            yield Term(*literals)
            literals[i] = ~(literals[i])

    def __bool__(self):
        """Empty term represents the whole boolean space, hence it must hold True value as opposed to empty tuple"""
        return True

    def __le__(self, other: 'Term'):
        """Return True if self domain is included in other's domain"""
        return len(set(self).intersection(other)) == len(other)

    def __lt__(self, other: 'Term'):
        """Return True if self domain is less than other's domain and included in it"""
        return (len(self) > len(other)) and (len(set(self).intersection(other)) == len(other))

    def __ge__(self, other: 'Term'):
        """Return True if other's domain is included in self domain"""
        return len(set(other).intersection(self)) == len(self)

    def __gt__(self, other: 'Term'):
        """Return True if other's domain is less than self domain and included in it"""
        return (len(self) < len(other)) and len(set(other).intersection(self)) == len(self)

    def __add__(self, other: 'Term'):
        """Return union of self and other's domains if it can be expressed as single term, otherwise raise ValueError

        Examples:
            (a, ~b) + (a, b)        # >>>(a,)
            (a, b, c) + (a, b)      # >>>(a, b)
            (a, ~b) + (b, c)        # >>>ValueError
        """
        if len(other) < len(self):
            litset1, litset2 = set(other), set(self)
        else:
            litset1, litset2 = set(self), set(other)
        diff = litset1.difference(litset2)

        if len(diff) == 0:
            return Term(*litset1)
        elif len(diff) == 1 and len(self) == len(other):
            lit, = diff
            if ~lit in litset2:
                litset1.remove(lit)
                return Term(*litset1)
        raise ValueError('Cannot express union of terms as a single term')

    def __mul__(self, other: 'Term'):
        """Return intersection of self and other's domains or None if complementary literals are included

        Examples:
            (a, b) * (b, ~c)        # >>>(a, b, ~c)
            (a, b, c) * (a, b)      # >>>(a, b, c)
            (a, ~b) * (a, b)        # >>>None
        """
        litset = set(self)
        for lit in other:
            if ~lit in litset:
                return None
            litset.add(lit)
        return Term(*litset)
