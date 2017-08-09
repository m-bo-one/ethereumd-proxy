import operator
import asyncio
from enum import IntEnum
from abc import abstractmethod

from ..exceptions import BadResponseError
from ..utils import hex_to_dec, wei_to_ether, ether_to_gwei, ether_to_wei


GAS_AMOUNT = 21000
GAS_PRICE = 20  # Gwei
DEFAUT_FEE = wei_to_ether(ether_to_gwei(GAS_PRICE) * GAS_AMOUNT)


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
        for key, funcs in cls._r.items():
            if 'category_' in key:
                yield (Category(int(key.replace('category_', ''))).name, funcs)


class ProxyMethod:

    async def help(self, command=None):
        """"help ( "command" )

List all commands, or get help for a specified command.

Arguments:
1. "command"     (string, optional) The command to get help on

Result:
"text"     (string) The help text
        """
        if command:
            func = getattr(ProxyMethod, command, None)
            if func:
                return func.__doc__
            return 'help: unknown command: %s' % command

        result = ""
        for category, funcs in Method.get_categories():
            result += "== %s ==\n" % category
            for func in funcs:
                doc = getattr(ProxyMethod, func).__doc__
                if not doc:
                    result += func + '\n'
                else:
                    result += doc.split('\n')[0] + '\n'
            result += "\n"
        result = result.rstrip('\n')
        return result

    @Method.registry(Category.Blockchain)
    async def getdifficulty(self):
        """getdifficulty

Returns the proof-of-work difficulty as a multiple of the minimum difficulty.

Result:
n.nnn       (numeric) the proof-of-work difficulty as a multiple of the minimum difficulty.

Examples:
> ethereum-cli getdifficulty
> curl -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "1.0", "id":"curltest", "method": "getdifficulty", "params": [] }'  http://127.0.0.01:9500/
        """
        return hex_to_dec(await self._call('eth_hashrate'))

    @Method.registry(Category.Wallet)
    async def getbalance(self, account="*", minconf=1, include_watchonly=True):
        """getbalance ( "account" minconf include_watchonly )

If account is not specified, returns the server's total available balance.
If account is specified (DEPRECATED), returns the balance in the account.
Note that the account "" is not the same as leaving the parameter out.
The server total may be different to the balance in the default "" account.

Arguments:
1. "account"         (string, optional) DEPRECATED. The account string may be given as a
                     specific account name to find the balance associated with wallet keys in
                     a named account, or as the empty string ("") to find the balance
                     associated with wallet keys not in any named account, or as "*" to find
                     the balance associated with all wallet keys regardless of account.
                     When this option is specified, it calculates the balance in a different
                     way than when it is not specified, and which can count spends twice when
                     there are conflicting pending transactions (such as those created by
                     the bumpfee command), temporarily resulting in low or even negative
                     balances. In general, account balance calculation is not considered
                     reliable and has resulted in confusing outcomes, so it is recommended to
                     avoid passing this argument.
2. minconf           (numeric, optional, default=1) Only include transactions confirmed at least this many times.
3. include_watchonly (bool, optional, default=false) DEPRECATED. Also include balance in watch-only addresses (see 'importaddress')

Result:
amount              (numeric) The total amount in BTC received for this account.

Examples:

The total amount in the wallet
> ethereum-cli getbalance

The total amount in the wallet at least 5 blocks confirmed
> ethereum-cli getbalance "*" 6

As a json rpc call
> curl -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "1.0", "id":"curltest", "method": "getbalance", "params": ["*", 6] }'  http://127.0.0.01:9500/
        """
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
        """settxfee amount

Set the transaction fee for transactions only. Overwrites the paytxfee parameter.

Arguments:
1. amount         (numeric or string, required) The transaction fee in ether

Result
true|false        (boolean) Returns true if successful

Examples:
> ethereum-cli settxfee 0.00042
> curl -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "1.0", "id":"curltest", "method": "settxfee", "params": [0.00042] }'  http://127.0.0.01:9500/
        """
        if isinstance(amount, (int, float)) and amount <= 0:
            raise BadResponseError({
                'error': {'code': -3, 'message': 'Amount out of range'}
            })
        try:
            self._paytxfee = float(amount)
        except Exception:
            return False
        else:
            return True

    @Method.registry(Category.Wallet)
    async def listaccounts(self, minconf=1, include_watchonly=True):
        """listaccounts ( minconf include_watchonly)

DEPRECATED. Returns Object that has account names as keys, account balances as values.

Arguments:
1. minconf             (numeric, optional, default=1) Only include transactions with at least this many confirmations
2. include_watchonly   (bool, optional, default=false) DEPRECATED. Include balances in watch-only addresses (see 'importaddress')

Result:
{                      (json object where keys are account names, and values are numeric balances
  "account": x.xxx,  (numeric) The property name is the account name, and the value is the total balance for the account.
  ...
}

Examples:

List account balances where there at least 1 confirmation
> ethereum-cli listaccounts

List account balances including zero confirmation transactions
> ethereum-cli listaccounts 0

List account balances for 6 or more confirmations
> ethereum-cli listaccounts 6

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
        """gettransaction "txid" ( include_watchonly )

Get detailed information about in-wallet transaction <txid>

Arguments:
1. "txid"                  (string, required) The transaction id
2. "include_watchonly"     (bool, optional, default=false) DEPRECATED. Whether to include watch-only addresses in balance calculation and details[]

Result:
{
  "amount" : x.xxx,        (numeric) The transaction amount in BTC
  "fee": x.xxx,            (numeric) The amount of the fee in BTC. This is negative and only available for the
                              'send' category of transactions.
  "confirmations" : n,     (numeric) The number of confirmations
  "blockhash" : "hash",  (string) The block hash
  "blockindex" : xx,       (numeric) The index of the transaction in the block that includes it
  "blocktime" : ttt,       (numeric) The time in seconds since epoch (1 Jan 1970 GMT)
  "txid" : "transactionid",   (string) The transaction id.
  "time" : ttt,            (numeric) The transaction time in seconds since epoch (1 Jan 1970 GMT)
  "timereceived" : ttt,    (numeric) The time received in seconds since epoch (1 Jan 1970 GMT)
  "details" : [
    {
      "account" : "accountname",      (string) DEPRECATED. The account name involved in the transaction, can be "" for the default account.
      "address" : "address",          (string) The ethereum address involved in the transaction
      "category" : "send|receive",    (string) The category, either 'send' or 'receive'
      "amount" : x.xxx,                 (numeric) The amount in BTC
      "label" : "label",              (string) A comment for the address/transaction, if any
      "vout" : n,                       (numeric) the vout value
      "fee": x.xxx,                     (numeric) The amount of the fee in BTC. This is negative and only available for the
                                           'send' category of transactions.
      "abandoned": xxx                  (bool) 'true' if the transaction has been abandoned (inputs are respendable). Only available for the
                                           'send' category of transactions.
    }
    ,...
  ],
  "hex" : "data"         (string) Raw data for transaction
}

Examples:
> ethereum-cli gettransaction "0xa4cb352eaff243fc962db84c1ab9e180bf97857adda51e2a417bf8015f05def3"
> ethereum-cli gettransaction "0xa4cb352eaff243fc962db84c1ab9e180bf97857adda51e2a417bf8015f05def3" true
> curl -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "1.0", "id":"curltest", "method": "gettransaction", "params": ["0xa4cb352eaff243fc962db84c1ab9e180bf97857adda51e2a417bf8015f05def3"] }'  http://127.0.0.01:9500/
        """
        # TODO: Make workable include_watchonly flag
        transaction, addresses = await asyncio.gather(
            self._call('eth_getTransactionByHash', [txid]),
            self._call('eth_accounts')
        )
        if transaction is None:
            raise BadResponseError({
                'error': {
                    'code': -5,
                    'message': 'Invalid or non-wallet transaction id'
                }
            })

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

    @Method.registry(Category.Wallet)
    async def sendtoaddress(self, address, amount, comment=None,
                            comment_to=None, subtractfeefromamount=False):
        """sendtoaddress "address" amount ( "comment" "comment_to" subtractfeefromamount )

Send an amount to a given address from coinbase.

Arguments:
1. "address"            (string, required) The ethereum address to send to.
2. "amount"             (numeric or string, required) The amount in ETH to send. eg 0.1
3. "comment"            (string, optional) DEPRECATED. A comment used to store what the transaction is for.
                             This is not part of the transaction, just kept in your wallet.
4. "comment_to"         (string, optional) DEPRECATED. A comment to store the name of the person or organization
                             to which you're sending the transaction. This is not part of the
                             transaction, just kept in your wallet.
5. subtractfeefromamount  (boolean, optional, default=false) The fee will be deducted from the amount being sent.
                             The recipient will receive less bitcoins than you enter in the amount field.

Result:
"txid"                  (string) The transaction id.

Examples:
> ethereum-cli sendtoaddress "0xc729d1e61e94e0029865d759327667a6abf0cdc5" 0.1
> ethereum-cli sendtoaddress "0xc729d1e61e94e0029865d759327667a6abf0cdc5" 0.1 "donation" "seans outpost"
> ethereum-cli sendtoaddress "0xc729d1e61e94e0029865d759327667a6abf0cdc5" 0.1 "" "" true
> curl -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "1.0", "id":"curltest", "method": "sendtoaddress", "params": ["0xc729d1e61e94e0029865d759327667a6abf0cdc5", 0.1, "donation", "seans outpost"] }'  http://127.0.0.01:9500/
        """
        # TODO: Add subtractfeefromamount logic
        # TODO: Add amount and address validation
        gas, coinbase_address = await asyncio.gather(
            self._paytxfee_to_etherfee(),
            self._call('eth_coinbase')
        )
        return await self._call('eth_sendTransaction', [{
            'from': coinbase_address,  # from ???
            'to': address,  # to
            'gas': hex(gas['gas_amount']),  # gas amount
            'gasPrice': hex(gas['gas_price']),  # gas price
            'value': hex(ether_to_wei(float(amount))),  # value
        }])

    @Method.registry(Category.Blockchain)
    async def getblockcount(self):
        """getblockcount

Returns the number of blocks in the longest blockchain.

Result:
n    (numeric) The current block count

Examples:
> ethereum-cli getblockcount
> curl -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "1.0", "id":"curltest", "method": "getblockcount", "params": [] }'  http://127.0.0.01:9500/
        """
        # TODO: What happen when no blocks in db?
        return hex_to_dec(await self._call('eth_blockNumber'))

    @Method.registry(Category.Blockchain)
    async def getbestblockhash(self):
        """getbestblockhash

Returns the hash of the best (tip) block in the longest blockchain.

Result:
"hex"      (string) the block hash hex encoded

Examples:
> ethereum-cli getbestblockhash 
> curl -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "1.0", "id":"curltest", "method": "getbestblockhash", "params": [] }'  http://127.0.0.01:9500/
        """
        # TODO: What happen when no blocks in db?
        block = await self._call('eth_getBlockByNumber', ['latest', False])
        if block is None:
            raise BadResponseError({
                'error': {'code': -5, 'message': 'Block not found'}
            })
        return block['hash']

    @Method.registry(Category.Blockchain)
    async def getblock(self, blockhash, verbose=True):
        """getblock "blockhash" ( verbose )

If verbose is false, returns a string that is serialized, hex-encoded data for block 'hash'.
If verbose is true, returns an Object with information about block <hash>.

Arguments:
1. "blockhash"          (string, required) The block hash
2. verbose                (boolean, optional, default=true) true for a json object, false for the hex encoded data

Result (for verbose = true):
{
  "hash" : "hash",     (string) the block hash (same as provided)
  "confirmations" : n,   (numeric) The number of confirmations, or -1 if the block is not on the main chain
  "size" : n,            (numeric) The block size
  "strippedsize" : n,    (numeric) The block size excluding witness data
  "weight" : n           (numeric) The block weight
  "height" : n,          (numeric) The block height or index
  "version" : n,         (numeric) The block version
  "versionHex" : "00000000", (string) The block version formatted in hexadecimal
  "merkleroot" : "xxxx", (string) The merkle root
  "tx" : [               (array of string) The transaction ids
     "transactionid"     (string) The transaction id
     ,...
  ],
  "time" : ttt,          (numeric) The block time in seconds since epoch (Jan 1 1970 GMT)
  "mediantime" : ttt,    (numeric) The median block time in seconds since epoch (Jan 1 1970 GMT)
  "nonce" : n,           (numeric) The nonce
  "bits" : "1d00ffff", (string) The bits
  "difficulty" : x.xxx,  (numeric) The difficulty
  "chainwork" : "xxxx",  (string) Expected number of hashes required to produce the chain up to this block (in hex)
  "previousblockhash" : "hash",  (string) The hash of the previous block
  "nextblockhash" : "hash"       (string) The hash of the next block
}

Result (for verbose=false):
"data"             (string) A string that is serialized, hex-encoded data for block 'hash'.

Examples:
> ethereum-cli getblock "0x8b22f9aa6c27231fb4acc587300abadd259f501ba99ef18d11e9e4dfa741eb39"
> curl -X POST -H 'Content-Type: application/json' -d '{"jsonrpc": "1.0", "id":"curltest", "method": "getblock", "params": ["0x8b22f9aa6c27231fb4acc587300abadd259f501ba99ef18d11e9e4dfa741eb39"] }'  http://127.0.0.01:9500/
        """
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

    async def _paytxfee_to_etherfee(self):
        try:
            gas_price = self._paytxfee / GAS_AMOUNT
        except AttributeError:
            gas_price = hex_to_dec(await self._call('eth_gasPrice'))
        finally:
            return {
                'gas_amount': GAS_AMOUNT,
                'gas_price': ether_to_gwei(gas_price),
            }

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
