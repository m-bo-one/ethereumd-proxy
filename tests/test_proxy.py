import subprocess
import os
import time
from collections import Mapping
from urllib.request import urlopen
from urllib.error import URLError

import pytest


from ethereumd.proxy import RPCProxy
from ethereumd.proxy.base import DEFAUT_FEE, GAS_PRICE
from ethereumd.utils import hex_to_dec
from ethereumd.exceptions import BadResponseError


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


class TestBaseProxy:

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
        cls._start_node()
        cls._wait_until_node_start()
        cls.proxy = RPCProxy(port=RPC_PORT)

    @classmethod
    def teardown_class(cls):
        process = subprocess.Popen(['make', '-C', BOX_DIR, 'stop'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        process.wait()
        process = subprocess.Popen(['make', '-C', BOX_DIR, 'destroy'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        process.wait()

    @pytest.mark.asyncio
    async def test_call_help(self):
        response = await self.proxy.help()
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_call_getdifficulty(self):
        response = await self.proxy.getdifficulty()
        assert isinstance(response, (int, float))

    @pytest.mark.asyncio
    async def test_call_settxfee(self):
        gas_price = hex_to_dec(await self.proxy._call('eth_gasPrice'))
        gas = await self.proxy._paytxfee_to_etherfee()
        assert gas_price == gas['gas_price']

    @pytest.mark.asyncio
    async def test_call_settxfee_with_custom_fee(self):
        response = await self.proxy.settxfee(DEFAUT_FEE)
        assert response is True
        gas = await self.proxy._paytxfee_to_etherfee()
        assert GAS_PRICE == gas['gas_price']

    @pytest.mark.asyncio
    async def test_call_listaccounts(self):
        response = await self.proxy.listaccounts()
        assert isinstance(response, Mapping)
        # default 1 account on start
        assert len(response) == 1

    @pytest.mark.asyncio
    async def test_call_gettransaction_not_exist(self):
        txhash = '0xc0c90cf2ea02dd40263f04f699366ba9b2f74f3a3d69f8050e50876802f4a5a8'
        try:
            await self.proxy.gettransaction(txhash)
        except BadResponseError as e:
            assert e.args[0]['error']['code'] == -5  # does not exists
        else:
            assert False, "Transaction must not be exists."

    @pytest.mark.asyncio
    async def test_call_getblockcount(self):
        response = await self.proxy.getblockcount()
        assert isinstance(response, int)

    @pytest.mark.asyncio
    async def test_call_getbestblockhash(self):
        response = await self.proxy.getbestblockhash()
        assert is_hex(response)

    @pytest.mark.asyncio
    async def test_call_getblock(self):
        bhash = '0x12b5f772e7764cdfd140d098db6fcee56bfbc0cb2dcac67aadfb8755b1b56f6d'
        try:
            await self.proxy.getblock(bhash)
        except BadResponseError as e:
            assert e.args[0]['error']['code'] == -5  # does not exists
        else:
            assert False, "Block must not be exists."
