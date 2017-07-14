import os
import argparse

from .utils import read_config_file, homify


__all__ = [
    'config'
]

ETHEREUM_DEFAULT_FOLDERS = {
    'main': homify('~/.ethereum'),
    'testnet': homify('~/.ethereum/testnet'),
}
GETH_DEFAULT_PORT = 8454


def _argparse():
    parser = argparse.ArgumentParser(
        description='Ethereumd proxy RPC client version v0.1')
    parser.add_argument("-conf", type=str, default='ethereum.conf',
                        help="Specify configuration file "
                             "(default: ethereum.conf)")
    parser.add_argument("-datadir", type=str,
                        default=ETHEREUM_DEFAULT_FOLDERS['main'],
                        help="Specify data directory")
    args = parser.parse_args()
    return args


def _load_config(args):
    args.datadir = homify(args.datadir)
    if not os.path.exists(args.datadir):
        raise argparse.ArgumentTypeError(
            'Error: Specified data directory "%s" does not exist.' %
            args.datadir)
    if 'ethereum.conf' == args.conf or args.datadir:
        config_path = os.path.join(args.datadir, args.conf)
    else:
        config_path = homify(args.conf)
    try:
        config = read_config_file(config_path)
    except FileNotFoundError as e:
        raise argparse.ArgumentTypeError(
            'Error: Specified data conf "%s" does not exist.' %
            config_path)

    if not config.get('ethpconnect'):
        config['ethpconnect'] = '127.0.0.1'
    if not config.get('ethpport'):
        config['ethpport'] = 9575
    if not config.get('rpcconnect'):
        config['rpcconnect'] = '127.0.0.1'
    if not config.get('rpcport'):
        config['rpcport'] = GETH_DEFAULT_PORT

    if 'ipcconnect' in config:
        _ipc_path = homify(config['ipcconnect'])
        if os.path.isabs(_ipc_path):
            config['ipcconnect'] = _ipc_path
        else:
            config['ipcconnect'] = os.path.abspath(
                os.path.join(args.datadir, _ipc_path))

    config['walletnotify'] = homify(config.get('walletnotify', ''))
    config['blocknotify'] = homify(config.get('blocknotify', ''))
    config['datadir'] = args.datadir
    config['db'] = os.path.join(config['datadir'], 'ethdsync')
    config['config_path'] = os.path.dirname(config_path)

    return config


args = _argparse()
config = _load_config(args)
