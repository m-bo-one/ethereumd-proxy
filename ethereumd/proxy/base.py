import operator
import asyncio
from abc import abstractmethod

from ethereum.utils import denoms

from ethereumd.exceptions import BadResponseError
from ethereumd.utils import hex_to_dec


class ProxyMethod:

    @abstractmethod
    def _call(self, method, params=None, _id=None):
        pass

    async def _calculate_confirmations(self, response):
        return (hex_to_dec(await self._call('eth_blockNumber')) -
                hex_to_dec(response['number']))

    async def listaccounts(self, minconf=1):
        # NOTE: minconf nt work curently
        addresses = await self._call('eth_accounts')
        accounts = {}
        for i, address in enumerate(addresses):
            account = 'Account #{0}'.format(i)
            balance = (await self._call(
                       'eth_getBalance', [address, "latest"])) or 0
            if not isinstance(balance, (int, float)):
                balance = hex_to_dec(balance)
            accounts[account] = balance / denoms.ether

        return accounts

    async def _get_confirmations(self, block):
        last_block_number = await self._call('eth_blockNumber')
        if not last_block_number:
            raise RuntimeError('Blockchain not synced.')

        if not block['number']:
            return 0
        return (hex_to_dec(last_block_number) -
                hex_to_dec(block['number']))

    async def gettransaction(self, txid, watch_only=False):
        # TODO: Make workable watch_only flag
        transaction, addresses = await asyncio.gather(
            self._call('eth_getTransactionByHash', [txid]),
            self._call('eth_accounts')
        )
        if transaction is None:
            return

        trans_info = {
            'amount': float(hex_to_dec(transaction['value']) / denoms.ether),
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
                from_['fee'] = (tr_hash['gasPrice'] * tr_receipt['gasUsed'] /
                                denoms.ether)
            trans_info['details'].append(from_)
        return trans_info

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
