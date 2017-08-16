|release| |coverage| |license|

ethereumd-proxy
===============

Proxy client-server for Ethereum node using JSON-RPC interface.

Why?
----
Mostly popular cryptocurrencies usually are forks of Bitcoin and all of them support Bitcoin protocol for communication with their full nodes. Ethereum go hard by own way and made own API for that. This library is a proxy to Ethereum node which implement many API methods like in bitcoind. Also it have signals like blocknotify and walletnotify.
All these features are implemented by ethereumd-proxy using polling and other techniques behind the scene.

Installation
------------

Python 3.5+ required.

First you need Geth/Parity or any other ethereum node (for listening). Tested on Geth 1.6.7 and used in production.

Installation

.. code:: bash

   $ pip install ethereumd-proxy

Usage
-----
It is the same as bitcoin-cli. Except it is not a node runner, just simple proxy for listening actual node.

Available command list:

.. code:: bash

   $ ethereum-cli -help

To start proxy server use:

.. code:: bash

   $ ethereum-cli -datadir=<path_to_your_dir_with_node_and_ethereum.conf> -daemon

To stop server:

.. code:: bash

   $ ethereum-cli -datadir=<path_to_your_dir_with_node_and_ethereum.conf> stop



Implemented JSON-RPC methods
----------------------------

Wallet
------
* getbalance
* settxfee
* listaccounts
* gettransaction
* sendtoaddress

Blockchain
----------
* getdifficulty
* getblockcount
* getbestblockhash
* getblock

Planned add more methods as soon as possible. Read help of some method first before use!

Sample of ethereum.conf
-----------------------

.. code:: bash

    #
    # ETHEREUMD-PROXY options (for controlling a running proxy process)
    #

    # Local server address for ethereumd-proxy RPC:
    #ethpconnect=127.0.0.1

    # Local server port for ethereumd-proxy RPC:
    #ethpport=9500

    #
    # JSON-RPC options (for controlling a running ethereum process)
    #

    # You can use go-ethereum to send commands to ethereum
    # running on another host using this option:
    #rpcconnect=127.0.0.1

    # Listen for RPC connections on this TCP port:
    #rpcport=8545

    # Listen for RPC connections on this unix/ipc socket:
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

Copy it to your datadir folder or use direct path to it.

Changes
=======

0.1.2 (2017-08-09)
------------------

* Increased testcov to 77%;
* Added more tests for methods;
* Fix error with alernotify;

0.1.1 (2017-07-31)
------------------

* Added tests and codecov;

0.1 (2017-07-25)
----------------

* Added cli for proxy RPC server;
* Some bug fixes in API;
* Added new RPC methods:

  * getbalance;
  * settxfee;
  * listaccounts;
  * gettransaction;
  * getdifficulty;
  * getblockcount;
  * getbestblockhash;
  * getblock;
  * sendtoaddress;


0.1a (2017-07-22)
-----------------

* Initial release
* Added RPC methods:

  * gettransaction;
  * getblock;
  * listaccounts;

TODO
----
* Add more RPC methods;
* Add tests for every RPC method and signal;
* Track orphaned blocks;


.. |release| image:: https://img.shields.io/badge/release-v0.1.2-brightgreen.svg
    :target: https://github.com/DeV1doR/ethereumd-proxy/releases/tag/v0.1.2
    :alt: Release

.. |coverage| image:: https://codecov.io/gh/DeV1doR/ethereumd-proxy/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/DeV1doR/ethereumd-proxy
    :alt: Test coverage

.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT License
