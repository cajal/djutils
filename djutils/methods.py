import datajoint as dj
from functools import wraps
from .errors import RestrictionError


def definition(name, comment):
    return """
    {name}                  : varchar(128)          # {comment}
    """.format(
        name=name,
        comment=comment,
    )


def decorate_method(method, name):
    """Decorator that ensures that the table contains the method tuple before calling the method"""

    @wraps(method)
    def _method(self, *args, **kwargs):

        if name not in self.fetch(self.name):
            raise RestrictionError(f"Table restriction does not include '{name}'")

        return method(self, *args, **kwargs)

    return _method


def decorate_property(prop, name):
    """Decorator that ensures that the table contains the method tuple before returning the property"""

    @wraps(prop)
    def _property(self):

        if name not in self.fetch(self.name):
            raise RestrictionError(f"Table restriction does not include '{name}'")

        return prop.fget(self)

    return property(_property)


def setup_method(cls, schema):

    contents = []
    methods = {}

    for x in dir(cls):

        if x.startswith("_"):
            continue

        attr = getattr(cls, x)

        if callable(attr):
            attr = decorate_method(attr, x)

        elif isinstance(attr, property):
            attr = decorate_property(attr, x)

        else:
            continue

        contents.append([x])
        methods[x] = attr

    attr = dict(
        definition=definition(cls.name, getattr(cls, "comment", cls.name)),
        contents=contents,
        **methods,
    )

    cls = type(cls.__name__, (cls, dj.Lookup), attr)
    cls = schema(cls)

    return cls
