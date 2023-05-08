from contextlib import contextmanager
from . import cache


@contextmanager
def cache_rowproperty(*tables, maxsize=None):
    """Enables cacheing of row properties

    Parameters
    ----------
    tables : type(dj.UserTable)
        if no tables are provided, the the row properties of all tables are cached.
        if tables are provided, then the row properties of provided tables only are cached.
    maxsize : int | none
        maximum number of cache elements
    """
    assert cache.rowproperty is None, "Row properties are already being cached."

    cache.rowproperty = cache.RowPropertyCache(*tables, maxsize=maxsize)
    try:
        yield
    finally:
        cache.rowproperty = None
