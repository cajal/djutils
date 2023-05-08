from collections import OrderedDict
from .utils import key_hash


class Cache(OrderedDict):
    def __init__(self, maxsize=None):
        self.maxsize = float("inf") if maxsize is None else int(maxsize)

    def __setitem__(self, key, value):
        if len(self) >= self.maxsize:
            self.popitem(last=False)

        super().__setitem__(key, value)


class RowPropertyCache:
    def __init__(self, *tables, maxsize=None):
        self.cache = Cache(maxsize)
        self.tables = tables
        if self.tables:
            self.selective = True
        else:
            self.selective = False

    def get(self, row, method):
        cls = row.__class__
        if self.selective and cls not in self.tables:
            return method(row)

        key = key_hash(dict(row.fetch1("KEY"), _class=cls, _method=method))
        try:
            ret = self.cache[key]
        except KeyError:
            ret = method(row)
            self.cache[key] = ret
        return ret


rowproperty = None
