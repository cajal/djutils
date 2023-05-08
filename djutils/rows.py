from functools import wraps
from .errors import RestrictionError
from . import cache


def rowmethod(method):
    """Decorator that ensures that the table is restricted to a single row before calling method"""

    @wraps(method)
    def _method(self, *args, **kwargs):

        if len(self) != 1:
            raise RestrictionError("Table must be restricted to single row.")

        return method(self, *args, **kwargs)

    return _method


def rowproperty(method):
    """Decorator that ensures that the table is restricted to a single row before returning property"""

    @wraps(method)
    def _method(self):

        if len(self) != 1:
            raise RestrictionError("Table must be restricted to single row.")

        if cache.rowproperty is None:
            return method(self)
        else:
            return cache.rowproperty.get(self, method)

    return property(_method)
