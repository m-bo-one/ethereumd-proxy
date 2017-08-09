import asyncio
import subprocess
import os
import time
from urllib.request import urlopen
from urllib.error import URLError

from ethereumd.proxy import create_rpc_proxy, create_ipc_proxy


NODE_PORT = 30375
RPC_PORT = 12523
BOX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'box')
UNIX_PATH = os.path.join(BOX_DIR, 'testnet', 'geth.ipc')


def is_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


# TODO: replace from proxy call in future
async def quick_unlock_account(proxy, duration=5):
    return await proxy._call('personal_unlockAccount', [
        (await proxy._call('eth_accounts'))[0],
        'admin',
        duration
    ])


def setup_proxies(fn):

    async def _wrapper(self, event_loop, *args, **kwargs):
        self.proxies = []
        self.loop = asyncio.get_event_loop()
        self.rpc_proxy = await create_rpc_proxy(port=RPC_PORT,
                                                loop=event_loop)
        self.proxies.append(self.rpc_proxy)
        self.ipc_proxy = await create_ipc_proxy(ipc_path=UNIX_PATH,
                                                loop=event_loop)
        self.proxies.append(self.ipc_proxy)
        return await fn(self, *args, **kwargs)

    return _wrapper


class BaseTestRunner:

    run_with_node = False

    @staticmethod
    def _start_node():
        process = subprocess.Popen([
            'make', '-C', BOX_DIR, 'start',
            'NODE_PORT=%s' % NODE_PORT,
            'RPC_PORT=%s' % RPC_PORT],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        stdout, _ = process.communicate()
        assert process.returncode == 0, stdout.decode('utf-8')

    @staticmethod
    def _wait_until_node_start(max_tries=5):
        base_uri = 'http://127.0.0.1:%s' % RPC_PORT
        tried = 0
        while tried < max_tries:
            try:
                return urlopen(base_uri)
            except URLError:
                tried += 1
                print('Waiting for node connection, max tries left: %d' %
                      (max_tries - tried))
                time.sleep(1)
        assert False, 'Node not started on %s' % base_uri

    @classmethod
    def setup_class(cls):
        # TODO: Maybe better to mock?
        if cls.run_with_node:
            cls._start_node()
            cls._wait_until_node_start()

    @classmethod
    def teardown_class(cls):
        if cls.run_with_node:
            process = subprocess.Popen(['make', '-C', BOX_DIR, 'stop'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
            process.wait()
            process = subprocess.Popen(['make', '-C', BOX_DIR, 'destroy'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
            process.wait()
