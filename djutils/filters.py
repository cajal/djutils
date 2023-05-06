from functools import wraps
from .links import setup_link, setup_link_set


def decorate_filter(filt, ftype):
    """Decorator verifies filter keys"""

    @wraps(filt)
    def _filt(self, key):

        if not (isinstance(key, ftype) or key is ftype):
            raise TypeError(f"Filter input must be {ftype.__name__} instance or class.")

        key = filt(self, key)

        if not (isinstance(key, ftype) or key is ftype):
            raise TypeError(f"Filter output must be {ftype.__name__} instance or class.")

        return key

    return _filt


class Filter:
    """Filter"""

    pass


class FilterLink:
    """Filter Link"""

    def filter(self, tuples):
        """Filter tuples via link

        Parameters
        ----------
        tuples : dj.UserTable
            tuples to be filtered

        Parameters
        ----------
        dj.UserTable
            restricted tuples
        """
        return self.link.filter(tuples)


class FilterLinkSet:
    """Filter Link Set"""

    def filter(self, tuples):
        """Filter tuples via links

        Parameters
        ----------
        tuples : dj.UserTable
            tuples to be filtered

        Parameters
        ----------
        dj.UserTable
            restricted tuples
        """
        for key in self.members.fetch("KEY", order_by=self.link.primary_key):

            tuples = (self.link & key).filter(tuples)

        return tuples


def setup_filter(cls):
    filt = decorate_filter(cls.filter, cls.ftype)
    return type(
        cls.__name__,
        (cls, Filter),
        dict(filter=filt),
    )


def setup_filter_link(cls, schema):

    for filt in cls.links:
        if not issubclass(filt, Filter):
            raise TypeError("Provided filter is not a subclass of Filter.")

    for filt in cls.links[1:]:
        if filt.ftype != cls.links[0].ftype:
            raise TypeError("Filter type mismatch.")

    cls = type(cls.__name__, (cls, FilterLink), dict())
    return setup_link(cls, schema)


def setup_filter_link_set(cls, schema):

    if not issubclass(cls.link, FilterLink):
        raise TypeError("Provided filter_link is not a subclass of FilterLink.")

    cls = type(cls.__name__, (cls, FilterLinkSet), dict())
    return setup_link_set(cls, schema)
