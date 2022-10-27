class Void:
    """Hanging pins attach here"""
    __slots__ = ['parent', 'outputs']

    def __init__(self, parent=None, *args: 'PinBase'):
        self.outputs = set(args)
        self.parent = parent

    def __iter__(self):
        yield from self.outputs

    def attach_output_pin(self, pin: 'PinBase') -> None:
        self.outputs.add(pin)

    def detach_output_pin(self, pin: 'PinBase') -> None:
        self.outputs.remove(pin)

    def __bool__(self):
        return False

    def __call__(self, *args, **kwargs):
        return 0
