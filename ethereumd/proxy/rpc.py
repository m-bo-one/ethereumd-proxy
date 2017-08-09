import ujson
import logging
import asyncio
import aiohttp
import async_timeout

from .base import ProxyMethod
from ..exceptions import BadResponseError


class RPCProxy(ProxyMethod):

    def __init__(self, host='127.0.0.1', port=8545, tls=False, timeout=60,
                 *, loop=None):
        self.host = host
        self.port = port
        self.tls = tls
        self._timeout = timeout
        self._id = 1
        self._loop = loop or asyncio.get_event_loop()
        self._log = logging.getLogger('rpc_proxy')

    async def _make_request(self, method, url, data):
        headers = {'Content-Type': 'application/json'}
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(self._timeout):
                async with session.request(method, url,
                                           data=data,
                                           headers=headers) as response:
                    return await response.json()

    async def _call(self, method, params=None, _id=None):
        params = params or []
        data = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': _id or self._id,
        }
        scheme = 'http'
        if self.tls:
            scheme += 's'
        url = '{}://{}:{}'.format(scheme, self.host, self.port)
        try:
            response = await self._make_request('post', url, ujson.dumps(data))
        except asyncio.TimeoutError as e:
            self._log.exception(e)
            return

        if not _id:
            self._id += 1

        try:
            return response['result']
        except KeyError:
            raise BadResponseError(response)


async def create_rpc_proxy(host='127.0.0.1', port=8545, tls=False, timeout=60,
                           *, loop=None):
    return RPCProxy(host, port, tls, timeout, loop=loop)
