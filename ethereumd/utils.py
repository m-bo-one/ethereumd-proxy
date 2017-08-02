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


def wei_to_ether(wei):
    '''
    Convert wei to ether
    '''
    return 1.0 * wei / 10**18


def ether_to_wei(ether):
    '''
    Convert ether to wei
    '''
    return int(ether * 10**18)


def ether_to_gwei(ether):
    '''
    Convert ether to Gwei
    '''
    return int(ether * 10**9)


def create_default_logger(level=logging.DEBUG,
                          fname='/tmp/ethereumd-proxy.log'):
    handler = logging.FileHandler(fname)
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
    return logger
