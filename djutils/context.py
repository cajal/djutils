from contextlib import contextmanager
from . import cache


@contextmanager
def cache_rowproperty(maxsize=None):
    """Enables cacheing of row properties

    Parameters
    ----------
    maxsize : int | none
        maximum number of cache elements
    """
    prev = cache.rowproperty

    if prev is None:
        cache.rowproperty = cache.RowPropertyCache(maxsize=maxsize)

    try:
        yield
    finally:
        cache.rowproperty = prev
