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

    def __init__(self, restriction=[]):
        self.restriction = dj.AndList(restriction)
        self._key = None

    @property
    def key(self):
        if self._key is None:
            self._key = self.key_source & self.restriction
        return self._key

    def __and__(self, key):
        return self.__class__([*self.restriction, key])

    def __len__(self):
        return len(self.key)

    def __bool__(self):
        return len(self.key) > 0

    def __repr__(self):
        return f"{len(self):,} x {self.key.primary_key}"


def keys(cls):
    keys = tuple(cls.keys)
    return type(cls.__name__, (cls, Keys), dict(keys=keys))
