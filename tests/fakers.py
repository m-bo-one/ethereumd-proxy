from ethereumd.exceptions import BadResponseError


def fake_call(methods='*'):

    def _allowed_method(method):
        if '*' == methods:
            return True
        elif '-' == methods:
            return False
        elif (isinstance(methods, (list, tuple)) and
              method in [m[1:] for m in methods if '-' in m]):
            return False
        elif isinstance(methods, (list, tuple)) and method in methods:
            return True
        return True

    def _wrapper(method, params=None, _id=None):
        params = params or []
        if method == 'eth_accounts':
            return (["0xf5041fe398062cd63b62bd9b5df9942d30c9b8ca"]
                    if _allowed_method(method) else [])
        elif method == 'eth_getTransactionByHash':
            if len(params) < 1:
                raise BadResponseError({
                    'jsonrpc': '2.0',
                    'error': {
                        'message': 'missing value for required argument %s' %
                        len(params),
                        'code': -32602
                    },
                    'id': 1
                })
            return {
                'blockHash': '0x6d18d84c577f99f8073c80ad5200c3da0e5a64de98b4c07cb2d84a8786682360',
                'blockNumber': '0x63a',
                'from': '0xf5041fe398062cd63b62bd9b5df9942d30c9b8ca',
                'gas': '0x15f90',
                'gasPrice': '0x0',
                'hash': params[0],
                'input': '0x',
                'nonce': '0x39',
                'r': '0x1b1316134fca8c9c0a82e884b9c96a8746a6b636c93d31abeab7dab290ba3bcb',
                's': '0x64f4f8b5e19b3a7dedc92c16e0c5b1a5b49240cb42960001e69ab70e7d3005e4',
                'to': '0x85521e2663efd02fef594a9b90b0dbe3aec590ac',
                'transactionIndex': '0x0',
                'v': '0xa95',
                'value': '0xde0b6b3a7640000'
            } if _allowed_method(method) else None
        elif method == 'eth_getBlockByHash':
            if len(params) < 2:
                raise BadResponseError({
                    'jsonrpc': '2.0',
                    'error': {
                        'message': 'missing value for required argument %s' %
                        len(params),
                        'code': -32602
                    },
                    'id': 1
                })
            return {
                'difficulty': '0x3cd85',
                'extraData': '0xd783010606846765746887676f312e382e31856c696e7578',
                'gasLimit': '0x47e7c4',
                'gasUsed': '0x5208',
                'hash': params[0],
                'logsBloom': '0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
                'miner': '0xf5041fe398062cd63b62bd9b5df9942d30c9b8ca',
                'mixHash': '0x048ee8d2ad79623956c5fe5f11056e92693fc89bbbce90dc67d80010e7daebd0',
                'nonce': '0x64ace968fdc0f3a4',
                'number': '0x63a',
                'parentHash': '0x01dd4dd0522d5f526c62d5fded6db9ff99583ae6b3acf5f7fafd9fa66446be1a',
                'receiptsRoot': '0x42bc6d46087014a68b0d8a0db658e00ed254f752e27afb5091b28e4466177b4e',
                'sha3Uncles': '0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347',
                'size': '0x288',
                'stateRoot': '0xd8563b7fab1224c1606edbccc807aef3a6578e6ace89c1d72b6ab3d44208edde',
                'timestamp': '0x5981bf5e',
                'totalDifficulty': '0x11f5bb1f',
                'transactions': [],
                'transactionsRoot': '0x95bc25f9816a11ccc1b136d5655fc24824dce14c06a4aa0602f02441085347f4',
                'uncles': []
            } if _allowed_method(method) else None
        elif method == 'eth_newBlockFilter':
            return ('0x6f4111062b3db311e6521781f4ef0046'
                    if _allowed_method(method) else None)
        elif method == 'eth_newPendingTransactionFilter':
            return ('0x967e6ebd52c48adce994057695090fe'
                    if _allowed_method(method) else None)
        elif method == 'eth_getFilterChanges':
            if len(params) < 1:
                raise BadResponseError({
                    'jsonrpc': '2.0',
                    'error': {
                        'message': 'missing value for required argument %s' %
                        len(params),
                        'code': -32602
                    },
                    'id': 1
                })
            return (['0x9c864dd0e7fdcfb3bd7197020ac311cbacef1aa29b49791223427bbedb6d36ad']
                    if _allowed_method(method) else [])
        else:
            raise BadResponseError({
                'jsonrpc': '2.0',
                'error': {
                    'message': 'The method %s does not exist/is not available' %
                    method,
                    'code': -32601
                },
                'id': 1}
            )
    return _wrapper
