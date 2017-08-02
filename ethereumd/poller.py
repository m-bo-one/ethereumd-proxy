import asyncio
import logging
import functools

from .exceptions import BadResponseError


def alertnotify(func_or_none=None, *, exceptions=(Exception,)):

    if not func_or_none:
        return functools.partial(alertnotify, exceptions=exceptions)

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not self.has_alertnotify:
                return await func(self, *args, **kwargs)

            try:
                return await func(self, *args, **kwargs)
            except exceptions as e:
                err_msg = 'Error from: %s' % e
                cmd = self._cmds['alertnotify'] % err_msg
                cmdp = await asyncio.create_subprocess_exec(
                    *cmd.split(),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )
                stdout, _ = await cmdp.communicate()
                if stdout:
                    logging.warning('ALERTNOTIFY: %s', stdout)
                logging.warning('Send alertnotify error msg "%s"', err_msg)
        return wrapper

    return decorator(func_or_none)


class Poller:
    """Poller to RPC.
    """

    _pollFilter = {
        'latest': 'eth_newBlockFilter',
        'pending': 'eth_newPendingTransactionFilter',
    }

    def __init__(self, proxy, cmds=None, *, loop=None):
        self._log = logging.getLogger('poller')
        self._proxy = proxy
        self._cmds = cmds or {}
        self._loop = loop or asyncio.get_event_loop()
        self._queue = {
            'default': asyncio.Queue(maxsize=100, loop=self._loop)
        }
        self._ctask = asyncio.ensure_future(self.poll(),
                                            loop=self._loop)

    @property
    def has_blocknotify(self):
        return bool(self._cmds.get('blocknotify', False))

    @property
    def has_walletnotify(self):
        return bool(self._cmds.get('walletnotify', False))

    @property
    def has_alertnotify(self):
        return bool(self._cmds.get('alertnotify', False))

    def stop(self):
        self._ctask.cancel()

    @property
    def defqueue(self):
        return self._queue['default']

    async def poll(self):
        while True:
            coro = await self.defqueue.get()
            await coro

    @alertnotify(exceptions=(ConnectionError, TimeoutError, BadResponseError))
    async def blocknotify(self):
        bhashes = await self._poll_with_reconnect('latest')
        if not bhashes:
            return
        self._log.info('New blocks: %s', bhashes)
        accounts = await self._proxy._call('eth_accounts')
        for bhash in bhashes:
            block = await self._proxy._call('eth_getBlockByHash',
                                            [bhash, False])
            for txid in block['transactions']:
                if (await self._is_account_trans(txid, accounts)):
                    await self.defqueue \
                        .put(self._exec_command('walletnotify', txid))
                    break
            self._log.info('Block: %s' % bhash)
            await self.defqueue.put(self._exec_command('blocknotify', bhash))

    @alertnotify(exceptions=(ConnectionError, TimeoutError, BadResponseError))
    async def walletnotify(self):
        txids = await self._poll_with_reconnect('pending')
        if not txids:
            return
        self._log.info('New transactions: %s', txids)
        accounts = await self._proxy._call('eth_accounts')

        async def _tr_sender(txid):
            if (await self._is_account_trans(txid, accounts)):
                self._log.info('Trans: %s' % txid)
                await self.defqueue \
                    .put(self._exec_command('walletnotify', txid))

        await asyncio.gather(*(_tr_sender(txid) for txid in txids))

    async def _is_account_trans(self, txid, accounts=None):
        accounts = accounts or (await self._proxy._call('eth_accounts'))
        trans = await self._proxy._call('eth_getTransactionByHash',
                                        [txid])
        if not trans:
            self._log.warning('Something happened with transaction %s',
                              txid)
            return False

        for direction in ('from', 'to'):
            if trans[direction] in accounts:
                account = trans[direction]
                self._log.info('Found transaction for account "%s"',
                               account)
                return True

        return False

    async def _exec_command(self, cmd_name, data):
        try:
            cmd = self._cmds[cmd_name] % data
        except KeyError:
            cmd = None
            self._log.warning('%s command not found', cmd_name)

        if not cmd:
            return False

        try:
            cmdp = await asyncio.create_subprocess_exec(
                *cmd.split(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await cmdp.communicate()
            if stdout:
                self._log.warning('%s: %s', cmd_name.upper(), stdout)
        except Exception as e:
            self._log.error('%s command exec error.', cmd_name)
            self._log.exception(e)
            return False
        else:
            self._log.info('%s successfully notified.', cmd_name)
            return True

    async def _build_filter(self, fname: str) -> str:
        quantity = await self._proxy._call(self._pollFilter[fname])
        setattr(self, '_%s' % fname, quantity)
        return quantity

    async def _poll_with_reconnect(self, fname) -> []:
        """Function for auto-filter reconnecting.
        """
        try:
            quantity = getattr(self, '_%s' % fname)
            return await self._proxy._call('eth_getFilterChanges', [quantity])
        except AttributeError:
            self._log.warn('Filter "%s" not initialized, created new one.',
                           fname)
        except BadResponseError:
            self._log.warn('Filter "%s" droped, created new one.',
                           fname)

        await self._build_filter(fname)
        return await self._poll_with_reconnect(fname)
