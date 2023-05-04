from functools import wraps
from .links import setup_link
from .sets import setup_set


def decorate_filter(filt, filt_type):
    """Decorator verifies filter keys"""

    @wraps(filt)
    def _filt(self, key):

        if not (isinstance(key, filt_type) or key is filt_type):
            raise TypeError(f"Filter input must be {filt_type.__name__} instance or class.")

        key = filt(self, key)

        if not (isinstance(key, filt_type) or key is filt_type):
            raise TypeError(f"Filter output must be {filt_type.__name__} instance or class.")

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
        for key in self.members.fetch("KEY", order_by="member_id"):
            tuples = (self.filter_link & key).filter(tuples)

        return tuples


def setup_filter(cls):
    filt = decorate_filter(cls.filter, cls.filter_type)
    return type(
        cls.__name__,
        (cls, Filter),
        dict(filter=filt),
    )


def setup_filter_link(cls, schema):

    filts = tuple(cls.filters)

    for filt in filts:
        if not issubclass(filt, Filter):
            raise TypeError("Provided filter is not a subclass of Filter.")

    for filt in filts[1:]:
        if filt.filter_type != filts[0].filter_type:
            raise TypeError("Filter type mismatch.")

    cls = type(
        cls.__name__,
        (cls, FilterLink),
        dict(links=filts),
    )
    return setup_link(cls, schema)


def setup_filter_link_set(cls, schema):

    if not issubclass(cls.filter_link, FilterLink):
        raise TypeError("Provided filter_link is not a subclass of FilterLink.")

    cls = type(
        cls.__name__,
        (cls, FilterLinkSet),
        dict(keys=[cls.filter_link]),
    )
    return setup_set(cls, schema)
