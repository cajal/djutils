import datajoint as dj
from operator import mul
from functools import reduce, wraps
from .utils import class_property
from .errors import RestrictionError


class key_property:
    """Decorator that ensures that keys are restricted to a single item before returning property"""

    def __init__(self, *keys):
        self.keys = list(keys)

    def __call__(self, method):
        @wraps(method)
        def _method(instance):

            if isinstance(instance, Keys):
                restriction = instance.key
            elif isinstance(instance, dj.Table):
                restriction = instance
            else:
                raise TypeError("key_property can only be applied to Keys or UserTable methods")

            for key in self.keys:
                if len(key & restriction) != 1:
                    raise RestrictionError(f"Contains multiple tuples of {key.__name__}.")

            return method(instance)

        return property(_method)


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
