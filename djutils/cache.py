from collections import OrderedDict
from datajoint import Table
from .derived import Keys
from .utils import key_hash


class Cache(OrderedDict):
    """Cache"""

    def __init__(self, maxsize=None):
        self.maxsize = float("inf") if maxsize is None else int(maxsize)

    def __setitem__(self, key, value):
        if len(self) >= self.maxsize:
            self.popitem(last=False)

        super().__setitem__(key, value)


class RowPropertyCache(Cache):
    """Row Property Cache"""

    def get(self, row, method):
        cls = row.__class__

        if issubclass(cls, Table):
            key = key_hash(dict(row.fetch1("KEY"), _class=id(cls), _method=id(method)))
        elif issubclass(cls, Keys):
            key = key_hash(dict(row.key.fetch1("KEY"), _class=id(cls), _method=id(method)))
        else:
            raise TypeError("Cached row property only works on subclasses of datajoint.Table or djutils.Keys")

        try:
            ret = self[key]
        except KeyError:
            ret = method(row)
            self[key] = ret
        return ret


rowproperty = None
