# -*- coding:utf-8 -*-

import logging

"""
CRITICAL
ERROR
WARNING
INFO
DEBUG
NOTSET
"""

LOGGING_LEVEL = logging.INFO
# LOGGING_LEVEL = logging.DEBUG

logging.basicConfig(
    format='[%(asctime)-15s] %(levelname)7s >> (%(filename)s:%(lineno)d, %(funcName)s())\n%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(LOGGING_LEVEL)

__all___ = [
    'LOGGER'
]
