import inspect
import datajoint as dj
from .populate import skip_missing
from .links import setup_link
from .sets import setup_set
from .methods import setup_method


class Schema(dj.Schema):
    def lookup(self, cls):
        context = self.context or inspect.currentframe().f_back.f_locals
        cls = type(
            cls.__name__,
            (cls, dj.Lookup),
            dict(),
        )
        return self(cls, context=context)

    def computed(self, cls):
        context = self.context or inspect.currentframe().f_back.f_locals
        make = skip_missing(cls.make)
        cls = type(
            cls.__name__,
            (cls, dj.Computed),
            dict(make=make),
        )
        return self(cls, context=context)

    def link(self, cls):
        return setup_link(cls, self)

    def set(self, cls):
        return setup_set(cls, self)

    def method(self, cls):
        return setup_method(cls, self)
