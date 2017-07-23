import operator
import asyncio
from enum import IntEnum
from abc import abstractmethod

from ..exceptions import BadResponseError
from ..utils import hex_to_dec, wei_to_ether, ether_to_gwei


class Category(IntEnum):
    Blockchain = 0
    Control = 1
    Generating = 2
    Mining = 3
    Network = 4
    Rawtransactions = 5
    Util = 6
    Wallet = 7


class Method:
    _r = {}

    @classmethod
    def registry(cls, category):
        def decorator(fn):
            cls._r.setdefault('category_%s' % int(category), []) \
                .append(fn.__name__)
            return fn
        return decorator

    @classmethod
    def get_categories(cls):
        return dict((Category(int(key.replace('category_', ''))).name, funcs)
                    for key, funcs in cls._r.items()
                    if 'category_' in key)


class ProxyMethod:

    async def help(self):
        categories = Method.get_categories()
        result = ""
        for category, funcs in categories.items():
            result += "== %s ==\n" % category
            for func in funcs:
                doc = getattr(ProxyMethod, func).__doc__
                if not doc:
                    result += func + '\n'
                else:
                    result += doc.split('\n')[0] + '\n'
            result += "\n"
        return result

    @Method.registry(Category.Blockchain)
    async def getdifficulty(self):
        return hex_to_dec(await self._call('eth_hashrate'))

    @Method.registry(Category.Wallet)
    async def getbalance(self, minconf=1, include_watchonly=True):
        # NOTE: minconf nt work curently
        addresses = await self._call('eth_accounts')

        async def _get_balance(address):
            balance = (await self._call(
                       'eth_getBalance', [address, "latest"])) or 0
            if not isinstance(balance, (int, float)):
                balance = hex_to_dec(balance)
            return wei_to_ether(balance)

        return sum(await asyncio.gather(*(_get_balance(address)
                                          for address in addresses)))

    @Method.registry(Category.Wallet)
    async def settxfee(self, amount):
        amount = float(amount)
        self._gas_amount = amount / 21000
        self._gas_price = ether_to_gwei(self._gas_amount)
        return True

    @Method.registry(Category.Wallet)
    async def listaccounts(self, minconf=1, include_watchonly=True):
        """listaccounts ( minconf include_watchonly)

DEPRECATED. Returns Object that has account names as keys, account balances as values.

Arguments:
1. minconf             (numeric, optional, default=1) Only include transactions with at least this many confirmations
2. include_watchonly   (bool, optional, default=false) Include balances in watch-only addresses (see 'importaddress')

Result:
{                      (json object where keys are account names, and values are numeric balances
  "account": x.xxx,  (numeric) The property name is the account name, and the value is the total balance for the account.
  ...
}

Examples:

List account balances where there at least 1 confirmation
> ethereumd-cli listaccounts

List account balances including zero confirmation transactions
> ethereumd-cli listaccounts 0

List account balances for 6 or more confirmations
> ethereumd-cli listaccounts 6

As json rpc call
> curl -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "1.0", "id":"curltest", "method": "listaccounts", "params": [6] }'  http://127.0.0.01:9500/
        """
        # NOTE: minconf nt work curently
        addresses = await self._call('eth_accounts')
        accounts = {}
        for i, address in enumerate(addresses):
            account = 'Account #{0}'.format(i)
            balance = (await self._call(
                       'eth_getBalance', [address, "latest"])) or 0
            if not isinstance(balance, (int, float)):
                balance = hex_to_dec(balance)
            accounts[account] = wei_to_ether(balance)

        return accounts

    @Method.registry(Category.Wallet)
    async def gettransaction(self, txid, include_watchonly=False):
        # TODO: Make workable include_watchonly flag
        transaction, addresses = await asyncio.gather(
            self._call('eth_getTransactionByHash', [txid]),
            self._call('eth_accounts')
        )
        if transaction is None:
            return

        trans_info = {
            'amount': wei_to_ether(hex_to_dec(transaction['value'])),
            'confirmations': 0,
            'trusted': None,
            "walletconflicts": [],
            'txid': transaction['hash'],
            'time': None,
            'timereceived': None,
            'details': [],
            'hex': transaction['input']
        }
        if transaction['blockHash']:
            block = await self.getblock(transaction['blockHash'])
            trans_info['confirmations'] = block['confirmations']
        if transaction['to'] in addresses:
            trans_info['details'].append({
                'account': '',
                'address': transaction['to'],
                'category': 'receive',
                'amount': trans_info['amount'],
                'label': '',
                'vout': 1
            })
        if transaction['from'] in addresses:
            from_ = {
                'account': '',
                'address': transaction['from'],
                'category': 'send',
                'amount': operator.neg(trans_info['amount']),
                'vout': 1,
                'fee': None,
                'abandoned': False
            }
            if transaction['blockHash']:
                tr_hash, tr_receipt = await asyncio.gather(
                    self._call('eth_getTransactionByHash', [txid]),
                    self._call('eth_getTransactionReceipt', [txid])
                )
                from_['fee'] = (tr_hash['gasPrice'] *
                                wei_to_ether(tr_receipt['gasUsed']))
            trans_info['details'].append(from_)
        return trans_info

    @Method.registry(Category.Blockchain)
    async def getblockcount(self):
        return hex_to_dec(await self._call('eth_blockNumber'))

    @Method.registry(Category.Blockchain)
    async def getbestblockhash(self):
        block = await self._call('eth_getBlockByNumber', ['latest', False])
        if block is None:
            raise BadResponseError({
                'error': {'code': -5, 'message': 'Block not found'}
            })
        return block['hash']

    @Method.registry(Category.Blockchain)
    async def getblock(self, blockhash, verbose=True):
        block = await self._call('eth_getBlockByHash', [blockhash, False])
        if block is None:
            raise BadResponseError({
                'error': {'code': -5, 'message': 'Block not found'}
            })
        if not verbose:
            return block['hash']

        return {
            'hash': block['hash'],
            'confirmations': (await self._get_confirmations(block)),
            'strippedsize': None,
            'size': None,
            'weight': None,
            'height': None,
            'version': None,
            'versionHex': None,
            'merkleroot': None,
            'tx': block['transactions'],
            'time': hex_to_dec(block['timestamp']),
            'mediantime': None,
            'nonce': hex_to_dec(block['nonce']),
            'bits': None,
            'difficulty': hex_to_dec(block['totalDifficulty']),
            'chainwork': None,
            'previousblockhash': block['parentHash']
        }

    # ABSTRACT METHODS

    @abstractmethod
    def _call(self, method, params=None, _id=None):
        pass

    # UTILS METHODS

    async def _calculate_confirmations(self, response):
        return (hex_to_dec(await self._call('eth_blockNumber')) -
                hex_to_dec(response['number']))

    async def _get_confirmations(self, block):
        last_block_number = await self._call('eth_blockNumber')
        if not last_block_number:
            raise RuntimeError('Blockchain not synced.')

        if not block['number']:
            return 0
        return (hex_to_dec(last_block_number) -
                hex_to_dec(block['number']))
