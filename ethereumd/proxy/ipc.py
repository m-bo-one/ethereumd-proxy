import json
import logging
import asyncio

from .base import ProxyMethod
from ..exceptions import BadResponseError


class IPCProxy(ProxyMethod):

    def __init__(self, ipc_path, *, loop=None):
        self._id = 1
        self._log = logging.getLogger('ipc_proxy')
        self._loop = loop or asyncio.get_event_loop()
        self._lock = asyncio.Semaphore(1, loop=self._loop)

        self._ipc_path = ipc_path
        self._reader, self._writer = self._loop.run_until_complete(
            asyncio.open_unix_connection(self._ipc_path))

    async def _call(self, method, params=None, _id=None):
        params = params or []
        data = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': _id or self._id,
        }
        try:
            with (await self._lock):
                self._writer.write(json.dumps(data).encode('utf-8'))
                b = await self._reader.readline()
                if not b:
                    self._log.error('_receive: no data, connection refused.')
                    raise ConnectionError
                response = json.loads(b.decode('utf-8'))
        except BrokenPipeError:
            self._log.error('_call: pipe broken, connection refused.')
            raise

        if not _id:
            self._id += 1

        try:
            return response['result']
        except KeyError:
            raise BadResponseError(response)
