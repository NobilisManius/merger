import re


class IDDict:
    """Container for items stored by ID

    Calculates ID for each added object and writes it to object's 'ID' property
    Property 'ID' of added objects must be open for writing

    Iterable: yields stored objects

    -----------------------------------------------------------------------------------------------------------

            Editing methods:
    - add()
    - remove()
    - clear()

            Access to items:
    - operator [] - by ID
    - by_name()
    - search()

            Unique renaming:
    - rename_items_by_ID()
    """
    __slots__ = ['dict', 'name_dict', '__ID']

    def __init__(self, *items: object):
        self.dict = {}
        self.name_dict = {}
        self.__ID = 0
        if items:
            self.add(*items)

    def __getitem__(self, ID: int):
        return self.dict[ID]

    def by_name(self, name: str):
        """Return item by its name or None

        Warning: this function works only after _update_name_dict call and before any consequent changes
            Use _update_name_dict method with caution (see its documentation for more info)
        """
        return self.name_dict.get(name)

    def __iter__(self):
        return (item for item in self.dict.values())

    def __len__(self):
        return len(self.dict)

    def add(self, *items: object) -> int:
        """Add items"""
        for item in items:
            self.dict[self.__ID] = item
            item.ID = self.__ID
            self.__ID += 1
        return self.__ID - 1

    def remove(self, *items: object) -> None:
        """Remove items"""
        for item in items:
            del self.dict[item.ID]

    def rename_items_by_ID(self, prefix: str, field: str= 'label') -> None:
        """Give each stored object name which is concatenation of prefix and string representation of its unique ID,
            update name_dict (there must be no collisions after renaming)

        field - item's property used to store its name (this property must be open for writing)
        """
        for item in self:
            item.__setattr__(field, prefix + str(item.ID))
        self._update_name_dict(field)

    def search(self, regex: str, field: str= 'label'):
        """Yield all items with name matching given regular expression

        field - item's property used to store its name
        """
        regex = re.compile(regex + '$')
        def match(gate):
            return regex.match(gate.__getattribute__(field))
        return filter(match, self.dict.values())

    def _update_name_dict(self, field: str= 'label'):
        """Update name_dict which enables fast access to items by name
        All names must be unique, otherwise name_dict will be incorrect

        field - item's property used to store its name
        """
        self.name_dict = {item.__getattribute__(field): item for item in self.dict.values()}

    def clear(self):
        """Delete all internal information"""
        self.dict = {}
        self.name_dict = {}
        self.__ID = 0
