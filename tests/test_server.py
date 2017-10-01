from collections import namedtuple
import json
from asynctest.mock import patch
import pytest

from ethereumd.server import RPCServer
from ethereumd.proxy import EthereumProxy

from aioethereum.errors import BadResponseError

from .base import BaseTestRunner


Request = namedtuple('Request', ['json'])


class TestServer(BaseTestRunner):

    run_with_node = True

    async def init_server(self, loop):
        server = RPCServer()
        with patch('ethereumd.poller.Poller.poll'):
            await server.before_server_start()(None, loop)
        return server

    @pytest.mark.asyncio
    async def test_server_handler_index_success_call(self, event_loop):
        server = await self.init_server(event_loop)
        data = {
            'jsonrpc': '2.0',
            'method': 'getblockcount',
            'params': [],
            'id': 'test',
        }
        request = Request(json=data)
        response = await server.handler_index(request)
        parsed = json.loads(response.body)
        assert parsed['error'] is None
        assert isinstance(parsed['result'], int)

    @pytest.mark.asyncio
    async def test_server_handler_index_invalid_rpc_data(self, event_loop):
        server = await self.init_server(event_loop)
        data = {
            'jsonrpc': '2.0',
            'method': 'getblockcount',
            'id': 'test',
        }
        request = Request(json=data)
        response = await server.handler_index(request)
        parsed = json.loads(response.body)
        assert parsed['error']['code'] == -32602
        assert parsed['error']['message'] == 'Invalid rpc 2.0 structure'
        assert parsed['result'] is None

    @pytest.mark.asyncio
    async def test_server_handler_index_attr_error_call(self, event_loop):
        server = await self.init_server(event_loop)
        data = {
            'jsonrpc': '2.0',
            'method': 'getblockcount',
            'params': [],
            'id': 'test',
        }
        request = Request(json=data)

        def _raise_error():
            raise AttributeError('bla bla method not found')
        with patch.object(EthereumProxy, 'getblockcount',
                          side_effect=_raise_error):
            response = await server.handler_index(request)
        parsed = json.loads(response.body)
        assert parsed['error']['code'] == -32601
        assert parsed['error']['message'] == 'Method not found'
        assert parsed['result'] is None

    @pytest.mark.asyncio
    async def test_server_handler_index_type_error_call(self, event_loop):
        server = await self.init_server(event_loop)
        data = {
            'jsonrpc': '2.0',
            'method': 'getblockcount',
            'params': [],
            'id': 'test',
        }
        request = Request(json=data)

        def _raise_error():
            raise TypeError('test')
        with patch.object(EthereumProxy, 'getblockcount',
                          side_effect=_raise_error):
            response = await server.handler_index(request)
        parsed = json.loads(response.body)
        assert parsed['error']['code'] == -1
        assert parsed['error']['message'] == 'test'
        assert parsed['result'] is None

    @pytest.mark.asyncio
    async def test_server_handler_index_bad_response_call(self, event_loop):
        server = await self.init_server(event_loop)
        data = {
            'jsonrpc': '2.0',
            'method': 'getblockcount',
            'params': [],
            'id': 'test',
        }
        request = Request(json=data)

        def _raise_error():
            raise BadResponseError('test', code=-99999999)
        with patch.object(EthereumProxy, 'getblockcount',
                          side_effect=_raise_error):
            response = await server.handler_index(request)
        parsed = json.loads(response.body)
        assert parsed['error']['code'] == -99999999
        assert parsed['error']['message'] == 'test'
        assert parsed['result'] is None
