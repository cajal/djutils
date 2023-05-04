import datajoint as dj
from operator import mul
from functools import reduce
from .utils import class_property


class KeysMeta(type):
    """Keys Metaclass"""

    def __and__(cls, arg):
        return cls() & arg


class Keys(metaclass=KeysMeta):
    """Derived Keys"""

    @class_property
    def key_source(self):
        return reduce(mul, [key.proj() for key in self.keys])

    def __init__(self, keys=None):
        self._keys = [] if keys is None else list(keys)

    @property
    def key(self):
        if self._keys:
            return self.key_source & dj.AndList(self._keys)
        else:
            return self.key_source

    def __and__(self, key):
        return self.__class__(self._keys + [key])

    def __len__(self):
        return len(self.key)

    def __bool__(self):
        return len(self.key) > 0

    def _repr_html_(self):
        return self.key._repr_html_()


def keys(cls):
    keys = tuple(cls.keys)
    return type(cls.__name__, (cls, Keys), dict(keys=keys))
