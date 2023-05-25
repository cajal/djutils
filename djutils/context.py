from contextlib import contextmanager
from . import cache


@contextmanager
def cache_rowproperty(*tables, maxsize=None):
    """Enables cacheing of row properties

    Parameters
    ----------
    tables : subclass(dj.UserTable) | subclass(djutils.derived.Keys)
        if no tables are provided, the the row properties of all tables are cached.
        if tables are provided, then the row properties of provided tables only are cached.
    maxsize : int | none
        maximum number of cache elements
    """
    old_cache = cache.rowproperty
    try:
        cache.rowproperty = cache.RowPropertyCache(*tables, maxsize=maxsize)
        yield
    finally:
        cache.rowproperty = old_cache
