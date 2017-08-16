import logging
import asyncio
import os

from sanic import Sanic, response
from sanic.handlers import ErrorHandler
from sanic.server import serve

from apscheduler.schedulers.asyncio import AsyncIOScheduler


from .proxy import create_rpc_proxy, create_ipc_proxy
from .poller import Poller
from .utils import create_default_logger
from .exceptions import BadResponseError


create_default_logger(logging.WARNING)


class SentryErrorHandler(ErrorHandler):

    def default(self, request, exception):
        if exception is None:
            return logging.error('SANIC SENTRY: unknown error occurred')
        logging.error('SANIC SENTRY: %s', exception)
        return super().default(request, exception)

    def log(self, message, level='error'):
        pass


class RPCServer:

    def __init__(self, ethpconnect='127.0.0.1', ethpport=9500,
                 rpcconnect='127.0.0.1', rpcport=8545,
                 ipcconnect=None, blocknotify=None, walletnotify=None,
                 alertnotify=None, *, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._app = Sanic(__name__,
                          log_config=None,
                          error_handler=SentryErrorHandler())
        self._host = ethpconnect
        self._port = ethpport
        self._rpc_host = rpcconnect
        self._rpc_port = rpcport
        self._unix_socket = ipcconnect
        self._blocknotify = blocknotify
        self._walletnotify = walletnotify
        self._alertnotify = alertnotify
        self._log = logging.getLogger('rpc_server')
        self.routes()

    @property
    def cmds(self):
        cmds = {}
        if self._blocknotify:
            cmds['blocknotify'] = self._blocknotify
        if self._walletnotify:
            cmds['walletnotify'] = self._walletnotify
        if self._alertnotify:
            cmds['alertnotify'] = self._alertnotify
        return cmds

    def before_server_start(self):
        @self._app.listener('before_server_start')
        async def initialize_scheduler(app, loop):
            if self._unix_socket:
                self._proxy = await create_ipc_proxy(self._unix_socket,
                                                     loop=loop)
            else:
                self._proxy = await create_rpc_proxy(self._rpc_host,
                                                     self._rpc_port,
                                                     loop=loop)
            self._poller = Poller(self._proxy, self.cmds, loop=loop)
            self._scheduler = AsyncIOScheduler({'event_loop': loop})
            if self._poller.has_blocknotify:
                self._scheduler.add_job(self._poller.blocknotify, 'interval',
                                        id='blocknotify',
                                        seconds=1)
            if self._poller.has_walletnotify:
                self._scheduler.add_job(self._poller.walletnotify, 'interval',
                                        id='walletnotify',
                                        seconds=1)
            if self._scheduler.get_jobs():
                self._scheduler.start()

    def routes(self):
        self._app.add_route(self.handler_index, '/',
                            methods=['POST'])
        self._app.add_route(self.handler_log, '/_log/',
                            methods=['GET', 'POST'])

    @property
    def _greeting(self):
        try:
            import ethereum_cli  # noqa
        except ImportError:
            return
        dirname = os.path.join(os.path.dirname(ethereum_cli.__file__), 'motd')
        with open(dirname) as motd:
            return '\033[91m' + motd.read() + '\033[0m'

    async def handler_index(self, request):
        data = request.json
        try:
            result = (await getattr(self._proxy, data['method'])
                      (*data['params']))
        except AttributeError as e:
            return response.json({
                'id': data['id'],
                'result': None,
                'error': {
                    'message': 'Method not found',
                    'code': -32601
                }
            })
        except TypeError as e:
            return response.json({
                'id': data['id'],
                'result': None,
                'error': {
                    'message': e.args[0],
                    'code': -1
                }
            })
        except BadResponseError as e:
            return response.json({
                'id': data['id'],
                'result': None,
                'error': e.args[0]['error']
            })
        else:
            return response.json({
                'id': data['id'],
                'result': result,
                'error': None
            })

    async def handler_log(self, request):
        self._log.warning('\nRequest args: %s;\nRequest body: %s',
                          request.args, request.body)
        return response.json({'status': 'OK'})

    def run(self):
        self.before_server_start()
        # TODO: Fix it
        # self._log.info(self._greeting)
        server_settings = self._app._helper(
            host=self._host,
            port=self._port,
            debug=True,
            loop=self._loop,
            backlog=100,
            run_async=True,
            has_log=False)
        self._loop.run_until_complete(serve(**server_settings))
        try:
            self._log.warning('Starting server on http://%s:%s/...',
                              self._host, self._port)
            self._loop.run_forever()
        except Exception:
            self._log.warning('Stoping server...')
            self._poller.stop()
