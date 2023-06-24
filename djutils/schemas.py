import inspect
import datajoint as dj
from .populate import skip_missing
from .methods import setup_method
from .sets import setup_set
from .lists import setup_list
from .links import setup_link, setup_link_set, setup_link_list
from .filters import setup_filter, setup_filter_link, setup_filter_link_set


class Schema(dj.Schema):
    def lookup(self, cls, *, context=None):
        context = context or self.context or inspect.currentframe().f_back.f_locals
        cls = type(
            cls.__name__,
            (cls, dj.Lookup),
            dict(),
        )
        return self(cls, context=context)

    def computed(self, cls, *, context=None):
        context = context or self.context or inspect.currentframe().f_back.f_locals
        make = skip_missing(cls.make)
        cls = type(
            cls.__name__,
            (cls, dj.Computed),
            dict(make=make),
        )
        return self(cls, context=context)

    def method(self, cls):
        return setup_method(cls, self)

    def set(self, cls):
        return setup_set(cls, self)

    def list(self, cls):
        return setup_list(cls, self)

    def link(self, cls):
        return setup_link(cls, self)

    def linkset(self, cls):
        return setup_link_set(cls, self)

    def linklist(self, cls):
        return setup_link_list(cls, self)

    def lookupfilter(self, cls, *, context=None):
        context = context or self.context or inspect.currentframe().f_back.f_locals
        cls = setup_filter(cls)
        return self.lookup(cls, context=context)

    def methodfilter(self, cls):
        cls = setup_filter(cls)
        return self.method(cls)

    def filterlink(self, cls):
        return setup_filter_link(cls, self)

    def filterlinkset(self, cls):
        return setup_filter_link_set(cls, self)
