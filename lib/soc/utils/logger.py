import logging
import os
import time
import sys
LOGGER = None


def init_logging(stream_enabled = True):
    global LOGGER

    if LOGGER is None:
        HANDLER = logging.StreamHandler(stream=sys.stdout)
        FORMATTER = logging.Formatter('[%(levelname)s] %(filename)s - %(lineno)d - %(message)s')
        HANDLER.setFormatter(FORMATTER)

        if not os.path.exists('logs'):
            os.mkdir('logs')

        FILE_LOGGER = logging.FileHandler(os.path.join('logs',"log.txt"))
        FILE_FORMATTER = logging.Formatter('[%(levelname)s] | %(asctime)s | %(filename)s | - %(lineno)d - %(message)s')
        FILE_LOGGER.setFormatter(FILE_FORMATTER)

        LOGGER = logging.getLogger('soc tello')
        if stream_enabled is True:
            LOGGER.addHandler(HANDLER)
        LOGGER.addHandler(FILE_LOGGER)
        LOGGER.setLevel(logging.DEBUG)

        LOGGER.info("\n\n====================== New Log ===========================")
        LOGGER.info(time.asctime())

    return LOGGER