import logging
import os

import colorlog


def homify(path):
    return path.replace('~/', os.path.expanduser('~') + '/')


def hex_to_dec(x: str) -> int:
    '''
    Convert hex to decimal
    '''
    return int(x, 16)


def read_config_file(filename: str) -> {}:
    """
    Read a simple ``'='``-delimited config file.
    Raises :const:`IOError` if unable to open file, or :const:`ValueError`
    if an parse error occurs.
    """
    f = open(filename)
    try:
        cfg = {}
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    (key, value) = line.split('=', 1)
                    cfg[key] = value
                except ValueError:
                    pass  # Happens when line has no '=', ignore
    finally:
        f.close()
    return cfg


def create_default_logger(level=logging.DEBUG):
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s %(levelname)s "
        "%(name)s - %(module)s:%(funcName)s:%(lineno)d]"
        "%(reset)s %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    handler.setFormatter(formatter)
    handler.setLevel(level)
    logger = colorlog.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)
