"""This module provides adjustable Liberty parser

    Functions for parsing:
load() - read Liberty
dump() - write Liberty

-----------------------------------------------------------------------------------------------------------------------

            Data structure

1. Groups are represented as class instances
2. Groups's fields (attributes and nested groups) are represented as class instance's attributes
3. Complex attributes with multiple values are represented as tuples
4. Quoted text in complex attributes is recognized as single value; quotes are removed
5. If the same attribute is repeated several times then the list is created
6. For nested groups, list or dictionary is created depending on whether these groups have names

    Given the following Liberty file:
library (lib) {
  simple_attr : simple_val;
  complex_attr : (complex1, complex2);
  complex_attr : ("complex3, complex4", "complex5, complex6");
  group1 () {
    attr : val;
  }
  group1 () {
    attr : val;
  }
  group2 (name1) {
    attr : val;
  }
  group2 (name2) {
    attr : val;
  }
}

    load() function will return instance of automatically generated class library with attributes:
simple_attr = 'simple_val'
complex_attr = [('complex1', 'complex2'), ('"complex3, complex4"', '"complex5, complex6"')]
group1 = [<group1 object>, <group1 object>]
group2 = {'name1': <group2 object>, 'name2': <group2 object>}
name = 'lib'

-----------------------------------------------------------------------------------------------------------------------

            Customization

Behaviour of the load() function can be changed by importing the configuration file
    which provides custom classes for groups
Custom classes are created via GroupMeta metaclass
    It provides the following features:
1. Managing the list of parsed fields
2. Using individual functions for attribute parsing
3. Managing group instance initialization and post-processing
4. Managing class itself, i.e. its methods, attributes, etc

See GroupMeta's documentation and example of configuration file at doc/templates/liberty.py for more information
"""


from itertools import count
from functools import partial
import re


_CUSTOM_GROUPS = {}
_DEFAULT_GROUPS = {}


def _isComplex(s):
    return s[0] == '('


def _parse_tuple(s):
    s = s[1:-1]
    start = 0
    inside = False
    skip = False
    toks = []
    for i, ch in enumerate(s):
        if skip:
            if ch == ',':
                start = i + 1
                skip = False
            continue
        if ch == '"':
            if not inside:
                start = i + 1
                inside = True
            else:
                toks.append(s[start:i])
                start = i + 1
                inside = False
                skip = True
        elif ch == ',':
            if not inside:
                toks.append(s[start:i])
                start = i + 1
    if not skip:
        toks.append(s[start:])
    return tuple(toks)


def _parse_simple(a):
    return a.strip(r'"')


def _parse_attr_default(a):
    return a


def _parse_group_default(type_, name, attrs_gen):
    Group = _DEFAULT_GROUPS.get(type_,
                                type(type_, (_LibertyGroup,), {'_name': type_,
                                                               '_parse_flags': (1, 1),
                                                               '_parse_functions': {}}))
    _DEFAULT_GROUPS[type_] = Group
    return Group(name, attrs_gen)


class _LibertyGroup:
    _ATTRIBUTE = 0
    _GROUP = 1

    def _try_add_prop(self, name, val):
        func = self._parse_functions.get(name)
        if not (self._parse_flags[0] or name in self._fields):
            if func is None or not self._parse_flags[2]:
                return
        elif func is None:
            func = self._parse_functions.get('default', _parse_attr_default)
        val = _parse_tuple(val) if _isComplex(val) else (_parse_simple(val),)
        if isinstance(func, tuple):
            cur_val = tuple(f(v) for f, v in zip(func, val))
        else:
            try:
                cur_val = (func(*val),)
            except TypeError:
                cur_val = tuple(map(func, val))
        if len(cur_val) == 1:
            cur_val = cur_val[0]

        prev_val = self.__dict__.get(name)
        if prev_val is None:
            self.__dict__[name] = cur_val
        elif isinstance(prev_val, list):
            prev_val.append(cur_val)
        else:
            self.__dict__[name] = [prev_val, cur_val]

    def _try_add_group(self, group, name, attrs_gen):
        cls = _CUSTOM_GROUPS.get(group)
        if not (self._parse_flags[1] or group in self._fields):
            if cls is None or not self._parse_flags[2]:
                self._skip(attrs_gen)
                return
        elif not cls:
            cls = partial(_parse_group_default, group)

        group_obj = cls(name, attrs_gen)
        if name:
            if group not in self.__dict__:
                self.__dict__[group] = {}
            self.__dict__[group][name] = group_obj
        else:
            if group not in self.__dict__:
                self.__dict__[group] = []
            self.__dict__[group].append(group_obj)

        if group in self._parse_functions:
            self._parse_functions[group](self, name, group_obj)

    @classmethod
    def _skip(cls, attrs_gen):
        for type_, name, val in attrs_gen:
            if type_ == cls._ATTRIBUTE:
                continue
            elif type_ == cls._GROUP:
                cls._skip(attrs_gen)
            else:
                return

    def __init__(self, name: str, attrs_gen: 'generator'):
        """Generator must yield 3 values: type, name and value
            type is 0 for attribute and 1 for group
            name is property's name or group's type
            value is property's value or group's name
        """
        self.name = name

        for type_, name, val in attrs_gen:
            if type_ == self._ATTRIBUTE:
                self._try_add_prop(name, val)
            elif type_ == self._GROUP:
                self._try_add_group(name, val, attrs_gen)
            else:
                break

    def __str__(self):
        return self.name

    def dump(self, f: 'file', indent: str) -> None:
        opener = indent + '{} ({})'.format(self._name, self.name) + ' {\n'
        closer = indent + '}\n'
        indent = indent + ' ' * 2
        
        def dump_groups(gs):
            for g in gs:
                g.dump(f, indent)
        
        def dump_attrs(n, as_):
            for a in as_:
                if isinstance(a, tuple):
                    fmtstr = indent + '{} \t(' + \
                             ((', \\\n' + indent + ' ' * len(n) + ' \t ').join(['"{}"'] * len(a)) if ',' in a[0]
                              else ','.join(['{}'] * len(a))) + ');\n'
                else:
                    fmtstr = indent + '{} : {};\n'
                    a = (a,)
                f.write(fmtstr.format(n, *a))
        
        f.write(opener)
        for n, a in self.__dict__.items():
            if n.startswith('_') or callable(a) or n == 'name':
                continue
            if isinstance(a, dict):
                dump_groups(a.values())
            elif isinstance(a, list):
                if isinstance(a[0], _LibertyGroup):
                    dump_groups(a)
                else:
                    dump_attrs(n, a)
            else:
                dump_attrs(n, [a])
        f.write(closer)


class GroupMeta(type):
    """Metaclass for creating custom group classes

            Syntax:
    class <group> (metaclass=GroupMeta):
        <settings>
        <attribute parse functions>
        <nested group postprocessing functions>
        <class methods>

    <group> must be identic to the group you want to parse

    Custom group instances are empty by default - change settings and/or provide custom parse functions for attributes
        and custom classes for nested groups to populate your instances with data

    -------------------------------------------------------------------------------------------------------------------

                Settings

    Settings are varibles which influence the way the class (and therefore its instances) are created

    List of available settings with default values:
        class_name = <group>    - the name given to class, must be str (<group> is used by default)
        parse_fields = set()    - attributes and nested groups which are forced to be read and added to data structure
                                  default parser or group class is used if custom one is not provided
        parse_all_attributes = False    - if True, then all attributes are added to data structure
        parse_all_groups = False        - if True, then all nested groups are added to data structure
        parse_all = False               - if True, then two previous settings are switched to True
        parse_enabled_only = False      - disables custom fields which are not allowed by settings above
                                          by default any field that has custom parser function/class is read

    -------------------------------------------------------------------------------------------------------------------

                Attributes

    Any callables defined in class created by GroupMeta are either attribute parsers or nested group postprocessers
    Exception is when the callable's name starts with _

            1. Simple attributes
    def <attribute> (val):
        ...
        return parsed_val

    val is string read from Liberty file without quotes

            2. Complex attributes
    Complex attribute's values are unpacked before parser function call (quotes are also removed)
    There are three ways to parse these values

    First one is to provide parser function of multiple arguments:

    def <attribute> (*vals):        # or val1, val2, ..., valn if you know the exact number
        ...
        return parsed_val           # or multiple vals

    Second one is to provide function of single argument to process each value separately:

    def <attribute> (val):
        ...
        return parsed_val

    Third one is to provide tuple of functions, each for its corresponding value:

    <attribute> = (int, str)

    -------------------------------------------------------------------------------------------------------------------

                Group instance processing

            1. Postprocess
    Postprocessing functions are called after group's parsing

    def <group> (self, name, inst):
        ...

    self is just regular self
    name is group's name specified in parentheses in Liberty file
    inst is group's class instance

            2. Preprocess
    Use group's __init__ method to do something with its instance before parsing:

    def __init__(self, name, gen):
        ...

    name is current group's name
    gen is generator used internally for further initialization
        alternating gen or exhausting it will cause errors in parser's work

    -------------------------------------------------------------------------------------------------------------------

                Class methods

    Methods can be defined using @method decorator:

    @method
    def func(self, *args):
        ...

    However, if your function's name starts with _, @method decorator is not needed
    """
    def __new__(mcs, name, bases, attrs):
        attrs['_fields'] = set(attrs.pop('parse_fields')) if 'parse_fields' in attrs else set()
        flags = [0, 0, 1]
        if 'parse_all_attributes' in attrs:
            if attrs.pop('parse_all_attributes'):
                flags[0] = 1
        if 'parse_all_groups' in attrs:
            if attrs.pop('parse_all_groups'):
                flags[1] = 1
        if 'parse_all' in attrs:
            if attrs.pop('parse_all'):
                flags[:2] = 1, 1
        if 'parse_enabled_only' in attrs:
            if attrs.pop('parse_enabled_only'):
                flags[2] = 0
        attrs['_parse_flags'] = tuple(flags)

        fns = {}
        for n, a in attrs.items():
            if n.startswith('_'):
                continue
            if hasattr(a, 'isMethod'):
                del a.isMethod
                continue
            if callable(a):
                fns[n] = a
            elif isinstance(a, tuple) and callable(a[0]):
                fns[n] = a
        for n in fns:
            del attrs[n]
        attrs['_parse_functions'] = fns

        class_name = attrs.pop('class_name') if 'class_name' in attrs else name
        attrs['_name'] = name

        bases = (_LibertyGroup,) + bases
        group = type.__new__(mcs, class_name, bases, attrs)
        _CUSTOM_GROUPS[name] = group
        return group

    def __call__(cls, *args, **kwargs):
        obj = cls.__new__(cls, *args, **kwargs)
        if cls.__init__ is not _LibertyGroup.__init__:
            cls.__init__(obj, *args, **kwargs)
        _LibertyGroup.__init__(obj, *args, **kwargs)
        return obj


def method(f: 'function') -> 'function':
    """Decorator for class methods"""
    f.isMethod = True
    return f


def set_default_parser() -> None:
    """Undo customization"""
    _CUSTOM_GROUPS.clear()


def load(filename: str) -> 'library':
    """Parse file in Liberty format, return library instance"""
    with open(filename) as library_file:
        library_string = library_file.read()

    library_string = re.sub('\w*\\\w*', '', library_string)
    library_string = re.sub('\s+', ' ', library_string)
    comment = re.compile('/\*.*?\*/')
    library_string = comment.sub('', library_string)

    def parse_attr(s):
        try:
            name, val = s.split(':', maxsplit=1)
        except ValueError:
            lb = s.find('(')
            rb = s.find(')')
            name = s[:lb]
            val = s[lb:rb + 1]
        return 0, name.strip(), val.strip()

    def parse_group(s):
        s = s[:-1].strip()
        lb = s.find('(')
        return 1, s[:lb].strip(), s[lb + 1:-1].strip().replace('"','')

    pos = 0

    def generate():
        nonlocal pos
        for nextpos in count(start=pos):
            if nextpos == len(library_string):
                return
            ch = library_string[nextpos]
            if ch == '}':
                yield -1, -1, -1
                pos = nextpos + 1
            elif ch == '{':
                yield parse_group(library_string[pos:nextpos])
                pos = nextpos + 1
            elif ch == ';':
                yield parse_attr(library_string[pos:nextpos])
                pos = nextpos + 1

    gen = generate()

    for type_, name, val in gen:
        if type_ == 1:
            if name in _CUSTOM_GROUPS:
                return _CUSTOM_GROUPS[name](val, gen)
            elif name == 'library':
                return _parse_group_default(name, val, gen)


def dump(lib: 'library', filename: str) -> None:
    """Write library to file"""
    with open(filename, 'w') as f:
        f.write('/**/\n')
        lib.dump(f, '')
