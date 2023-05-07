from functools import wraps
from contextlib import contextmanager
from .utils import key_hash
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
            key = key_hash(dict(self.fetch1("KEY"), _class=self.__class__, _method=method.__name__))
            try:
                ret = cache.rowproperty[key]
            except KeyError:
                ret = method(self)
                cache.rowproperty[key] = ret
            return ret

    return property(_method)


@contextmanager
def cache_rowproperty(maxsize=None):
    """Temporariliy enables cacheing of row properties"""

    if cache.rowproperty is None:
        no_cache = True
        cache.rowproperty = cache.Cache(maxsize)
    else:
        no_cache = False
        _maxsize = cache.rowproperty.maxsize
        cache.rowproperty.maxsize = maxsize

    try:
        yield
    finally:
        if no_cache:
            cache.rowproperty = None
        else:
            cache.rowproperty.maxsize = _maxsize
