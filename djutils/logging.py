import logging
import sys

logger = logging.getLogger("djutils")
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
