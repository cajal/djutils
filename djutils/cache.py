from collections import OrderedDict
from datajoint import Table
from .derived import Keys
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
            for table in self.tables:
                if not issubclass(table, (Table, Keys)):
                    raise TypeError("Cached table must either be a subclass of datajoint.Table or djutils.Keys")
        else:
            self.selective = False

    def get(self, row, method):
        cls = row.__class__

        if self.selective and cls not in self.tables:
            return method(row)

        if issubclass(cls, Table):
            key = key_hash(dict(row.fetch1("KEY"), _class=cls, _method=method))
        elif issubclass(cls, Keys):
            key = key_hash(dict(row.key.fetch1("KEY"), _class=cls, _method=method))
        else:
            raise TypeError("Cached row property only works on subclasses of datajoint.Table or djutils.Keys")

        try:
            ret = self.cache[key]
        except KeyError:
            ret = method(row)
            self.cache[key] = ret
        return ret


rowproperty = None
