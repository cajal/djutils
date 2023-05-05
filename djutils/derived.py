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
                raise TypeError("key_property can only be applied to Keys or Table methods")

            for key in self.keys:
                if len(key & restriction) != 1:
                    raise RestrictionError(f"Contains multiple tuples of {key.__name__}.")

            return method(instance)

        return property(_method)



class KeysMeta(type):
    """Keys Metaclass"""

    def __and__(cls, arg):
        return cls() & arg

    def __getattribute__(cls, name):
        if name in ["key_source", "primary_key"]:
            return cls().__getattribute__(name)
        else:
            return super().__getattribute__(name)


class Keys(metaclass=KeysMeta):
    """Derived Keys"""

    def __init__(self, restriction=[]):
        self.restriction = dj.AndList(restriction)
        self._key = None

    @property
    def key(self):
        if self._key is None:
            self._key = (self.key_source & self.restriction).proj()
        return self._key

    @property
    def primary_key(self):
        return self.key_source.primary_key

    def __and__(self, key):
        return self.__class__([*self.restriction, key])

    def __len__(self):
        return len(self.key)

    def __bool__(self):
        return len(self.key) > 0

    def __repr__(self):
        return f"{len(self):,} x {self.key.primary_key}"


def keys(cls):
    assert isinstance(cls.key_source, property)
    return type(cls.__name__, (cls, Keys), dict(keys=keys))
