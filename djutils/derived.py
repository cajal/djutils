from datajoint import Table, AndList
from operator import mul
from functools import reduce, wraps
from .errors import RestrictionError


class keyproperty:
    """Decorator that ensures that keys are restricted to a single item before returning property"""

    def __init__(self, *keys):
        self.keys = list(keys)

    def __call__(self, method):
        @wraps(method)
        def _method(instance):

            if isinstance(instance, Keys):
                restriction = instance.key
            elif isinstance(instance, Table):
                restriction = instance
            else:
                raise TypeError("keyproperty only works on subclasses of djutils.Keys or datajoint.Table")

            for key in self.keys:
                if len(key & restriction) != 1:
                    raise RestrictionError(f"{key.__name__} must be restricted to a single tuple.")

            return method(instance)

        return property(_method)


class keymethod:
    """Decorator that ensures that keys are restricted to a single item before calling method"""

    def __init__(self, *keys):
        self.keys = list(keys)

    def __call__(self, method):
        @wraps(method)
        def _method(instance, *args, **kwargs):

            if isinstance(instance, Keys):
                restriction = instance.key
            elif isinstance(instance, Table):
                restriction = instance
            else:
                raise TypeError("keymethod only works on subclasses of djutils.Keys or datajoint.Table")

            for key in self.keys:
                if len(key & restriction) != 1:
                    raise RestrictionError(f"{key.__name__} must be restricted to a single tuple.")

            return method(instance, *args, **kwargs)

        return _method


class KeysMeta(type):
    """Keys Metaclass"""

    def __and__(cls, arg):
        return cls() & arg

    def __getattribute__(cls, name):
        if name in ["keys", "key_source", "primary_key"]:
            return cls().__getattribute__(name)
        else:
            return super().__getattribute__(name)


class Keys(metaclass=KeysMeta):
    """Derived Keys"""

    def __init__(self, restriction=[]):
        self.restriction = AndList(restriction)
        self._key = None
        self._item = None

    @property
    def key_source(self):
        return reduce(mul, [key.proj() for key in self.keys])

    @property
    def key(self):
        if self._key is None:
            self._key = (self.key_source & self.restriction).proj()
        return self._key

    @property
    def item(self):
        if self._item is None:
            self._item = self.key.fetch1()
        return self._item

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
        return f"{len(self):,} x {self.primary_key}"


def keys(cls):
    assert isinstance(cls.keys, property)
    return type(cls.__name__, (cls, Keys), dict())
