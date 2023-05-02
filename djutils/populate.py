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
