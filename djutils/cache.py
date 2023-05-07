from collections import OrderedDict


class Cache(OrderedDict):
    def __init__(self, maxsize=None):
        self._maxsize = float("inf") if maxsize is None else int(maxsize)

    @property
    def maxsize(self):
        return self._maxsize

    @maxsize.setter
    def maxsize(self, maxsize):
        if maxsize is None:
            self._maxsize = float("inf")
            return

        if maxsize < self.maxsize:
            while len(self) > maxsize:
                self.popitem(last=False)

        self._maxsize = int(maxsize)

    def __setitem__(self, key, value):
        if len(self) >= self.maxsize:
            self.popitem(last=False)

        super().__setitem__(key, value)


rowproperty = None
