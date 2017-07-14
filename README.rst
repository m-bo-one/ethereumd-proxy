|tag| |license|

ethereumd-proxy
===============

Python client for go-ethereum node using the JSON-RPC or IPC interface.

Why?
----

Create a similar to bitcoind node with similar as possible API methods and signals
like walletnotfy, blocknotify, alertnotify.

Installation
------------

Python 3.5+ required. (Ethereum is new technology so only new python version supporting).

First you need Geth (1.6+) (for listening node):

* Geth (https://github.com/ethereum/go-ethereum);

After install dependencies:

.. code:: bash

   $ pip install -r requirements.txt

To run it use:

.. code:: bash

   $ python ethereum-proxy.py -datadir=<path_to_your_dir_with_ethereum.conf>

Available command list:

.. code:: bash

   $ python ethereum-proxy.py -h

Implemented JSON-RPC methods
----------------------------

* gettransaction
* getblock
* listaccounts

Planned add more methods as soon as posible.

Sample ethereum.conf
--------------------

.. code:: bash

    #
    # ETHEREUMD-PROXY options (for controlling a running proxy process)
    #

    # Local server address for ethereumd-proxy RPC:
    #ethpconnect=127.0.0.1

    # Local server port for ethereumd-proxy RPC:
    #ethpport=9575

    #
    # JSON-RPC options (for controlling a running Ethereum/geth process)
    #

    # You can use go-ethereum to send commands to Ethereum/geth
    # running on another host using this option:
    #rpcconnect=127.0.0.1

    # Listen for RPC connections on this TCP port:
    #rpcport=8545

    # Listen for RPC connections on this unix/ipc socket:
    # NOTE: You can use relative path from -datadir
    #ipcconnect=~/.ethereum/geth/geth.ipc

    #
    # Signals options (for controlling a script management process)
    #

    # Execute command when a wallet transaction changes (%s in cmd is replaced by TxID)
    #walletnotify=
    # Execute command when the best block changes (%s in cmd is replaced by block hash)
    #blocknotify=
    # Execute command when a relevant alert is received (%s in cmd is replaced by message)
    # TODO: add notification of long fork
    #alertnotify=

TODO
----
* Add more RPC methods;
* Add tests for every RPC method and signal;
* Track orphaned blocks;
* Add console command call;


.. |tag| image:: https://img.shields.io/badge/tag-v0.1a-yellowgreen.svg
    :target: https://github.com/DeV1doR/ethereumd-proxy
    :alt: Release v0.1a

.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://opensource.org/licenses/MIT  
    :alt: MIT License
