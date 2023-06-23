from functools import reduce
from operator import mul
from .errors import MissingError


def merge(table, *others, missing_error=True):
    """Merges table with others

    Parameters
    ----------
    table : datatjoint.UserTable
        table to merge with others
    others : tuple[datajoint.UserTable]
        other tables to merge
    missing_error : bool
        whether to raise MissingError if tuples are missing

    Returns
    -------
    datajoint.UserTable
        table merged to others
    """
    merged = reduce(mul, others, table)

    if table.proj() - merged.proj():
        raise MissingError()

    return merged


def unique(table, attribute):
    """Unique attribute from table

    Parameters
    ----------
    table : datatjoint.UserTable
        table to fetch from
    * attributes : str
        attributes to fetch

    Returns
    -------
    ...
        Unique attribute from table
    """
    (ret,) = set(table.fetch(attribute))
    return ret
