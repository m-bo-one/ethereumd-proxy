from collections import Mapping

import pytest


from ethereumd.proxy.base import DEFAUT_FEE, GAS_PRICE
from ethereumd.utils import hex_to_dec
from ethereumd.exceptions import BadResponseError

from .base import BaseTestRunner, is_hex, setup_proxies


class TestBaseProxy(BaseTestRunner):

    run_with_node = True

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_help(self):
        for proxy in self.proxies:
            response = await proxy.help()
            assert isinstance(response, str)

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_known_help_commend(self):
        for proxy in self.proxies:
            response = await proxy.help('getdifficulty')
            assert isinstance(response, str)
            assert proxy.getdifficulty.__doc__ == response

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_unknown_help_commend(self):
        for proxy in self.proxies:
            response = await proxy.help('do_not_know_command')
            assert isinstance(response, str)
            assert 'unknown command' in response

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_getbalance(self):
        for proxy in self.proxies:
            response = await proxy.getbalance()
            assert isinstance(response, (int, float))

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_getdifficulty(self):
        for proxy in self.proxies:
            response = await proxy.getdifficulty()
            assert isinstance(response, (int, float))

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_settxfee_as_dont_called(self):
        for proxy in self.proxies:
            gas_price = hex_to_dec(await proxy._call('eth_gasPrice'))
            gas = await proxy._paytxfee_to_etherfee()
            assert gas_price == gas['gas_price']

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_settxfee_when_negative_tax(self):
        for proxy in self.proxies:
            with pytest.raises(BadResponseError) as excinfo:
                await proxy.settxfee(-1)
            assert '-3' in str(excinfo)

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_settxfee_invalid_amount(self):
        for proxy in self.proxies:
            response = await proxy.settxfee('3243as')
            assert response is False

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_settxfee_with_custom_fee(self):
        for proxy in self.proxies:
            response = await proxy.settxfee(DEFAUT_FEE)
            assert response is True
            gas = await proxy._paytxfee_to_etherfee()
            assert GAS_PRICE == gas['gas_price']

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_listaccounts(self):
        for proxy in self.proxies:
            response = await proxy.listaccounts()
            assert isinstance(response, Mapping)
            # default 1 account on start
            assert len(response) == 1

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_gettransaction_not_exist(self):
        for proxy in self.proxies:
            txhash = '0xc0c90cf2ea02dd40263f04f699366ba9b2f74f3a3d69f8050e50876802f4a5a8'
            with pytest.raises(BadResponseError) as excinfo:
                await proxy.gettransaction(txhash)
            assert '-5' in str(excinfo)

    # @pytest.mark.asyncio
    # @setup_proxies
    # async def test_call_sendtoaddress(self):
    #     for proxy in self.proxies:
    #         await quick_unlock_account(proxy)
    #         response = await proxy.sendtoaddress(
    #             '0x69ea6b31ef305d6b99bb2d4c9d99456fa108b02a', 0.1)
    #         assert isinstance(response, str)

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_getblockcount(self):
        for proxy in self.proxies:
            response = await proxy.getblockcount()
            assert isinstance(response, int)

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_getbestblockhash(self):
        for proxy in self.proxies:
            response = await proxy.getbestblockhash()
            assert is_hex(response)

    @pytest.mark.asyncio
    @setup_proxies
    async def test_call_getblock(self):
        for proxy in self.proxies:
            bhash = '0x12b5f772e7764cdfd140d098db6fcee56bfbc0cb2dcac67aadfb8755b1b56f6d'
            with pytest.raises(BadResponseError) as excinfo:
                await proxy.getblock(bhash)
            assert '-5' in str(excinfo)
