import datajoint as dj
from .errors import RestrictionError


def definition(name, comment):
    return """
    {name}_method               : varchar(128)          # {comment}
    """.format(
        name=name,
        comment=comment,
    )


class Method(dj.Lookup):
    def __getattr__(self, name):

        if name in self._methods:

            if name not in self.fetch(f"{self.name}_method"):
                raise RestrictionError(f"Table restriction does not include {name}")

            return getattr(self, f"_{name}")

        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


def method(schema):
    def decorate(cls):
        cls = setup(cls, schema)
        return cls

    return decorate


def setup(cls, schema):

    name = str(cls.name)
    comment = str(cls.comment)

    methods = filter(lambda x: not x.startswith("_"), dir(cls))
    methods = set(methods) - {"name", "comment"}
    methods = tuple(methods)

    attr = dict(
        definition=definition(name, comment),
        name=name,
        comment=comment,
        contents=[[method] for method in methods],
        _methods=methods,
    )
    for method in methods:
        attr[f"_{method}"] = getattr(cls, method)

    cls = type(cls.__name__, (Method,), attr)
    cls = schema(cls)

    return cls
