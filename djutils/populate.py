from .logging import logger
from .errors import MissingError


def skip_missing(make):
    """Decorator that skips make call if MissingError is raised"""

    def _make(self, key):

        try:
            make(self, key)

        except MissingError:
            logger.warn(f"Missing data. Not populating {key}")

    return _make


def setup_computed(cls, schema):
    make = skip_missing(cls.make)
    return type(cls.__name__, (cls, dj.Computed), dict(make=make))
