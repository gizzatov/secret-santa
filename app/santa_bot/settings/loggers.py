import os
import sys

from loguru import logger

DEBUG = os.getenv('DEBUG') == '1'
LOG_LEVEL = 'DEBUG' if DEBUG else 'INFO'


logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL)
