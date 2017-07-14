import logging
import asyncio

from .conf import config


class Node:

    def __init__(self, *, loop=None):
        self.conf = {
            'datadir': config['node_path'],
            'port': 30304,
            'verbosity': 3,
            'rpc': False,
            'dev': True
        }
        if config.get('rpcconnect') and config.get('rpcport'):
            self.conf.update(
                rpc=True,
                rpcaddr=config['rpcconnect'],
                rpcport=config['rpcport'],
                rpcapi='eth,web3,personal',
                rpccorsdomain='*'
            )
        if config.get('ipcaddr'):
            self.conf['ipcdisable'] = False

        self._loop = loop or asyncio.get_event_loop()
        self._proc = None
        self._started = False

    @property
    def inline_conf(self):
        r = ''
        for i, data in enumerate(self.conf.items()):
            param, value = data
            indent = '' if i == 0 else ' '
            if isinstance(value, bool) and value:
                r += '{indent}--{param}'.format(indent=indent, param=param)
            else:
                r += '{indent}--{param} "{value}"'.format(indent=indent,
                                                          param=param,
                                                          value=value)
        return r

    @property
    def cmd_list(self):
        cmd_list = ['geth']
        for param, value in self.conf.items():
            if isinstance(value, bool) and value:
                cmd_list.append('--%s' % param)
            else:
                cmd_list.append('--%s' % param)
                cmd_list.append('%s' % value)
        return cmd_list

    async def start(self):
        try:
            self._proc = await asyncio.create_subprocess_exec(*self.cmd_list)
        except Exception as e:
            logging.exception(e)
            logging.error('Node don\'t started, abort.')
            self._loop.stop()

    def stop(self):
        self._proc.kill()
        self._proc = None
        self._started = False
