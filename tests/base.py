import subprocess
import os
import time
from urllib.request import urlopen
from urllib.error import URLError

from ethereumd.proxy import RPCProxy


NODE_PORT = 30375
RPC_PORT = 12523
BOX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'box')


def is_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


class BaseTestRunner:

    run_with = []  # available: node, proxy

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
        if 'node' in cls.run_with:
            cls._start_node()
            cls._wait_until_node_start()
        if 'proxy' in cls.run_with:
            cls.proxy = RPCProxy(port=RPC_PORT)

    @classmethod
    def teardown_class(cls):
        if 'node' in cls.run_with:
            process = subprocess.Popen(['make', '-C', BOX_DIR, 'stop'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
            process.wait()
            process = subprocess.Popen(['make', '-C', BOX_DIR, 'destroy'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
            process.wait()
