NODE=geth
DATADIR1=./testnet
KEYSTORE1=$(DATADIR1)/keystore
LOG_FILE1=$(DATADIR1)/info.log
IPC_FILE1=$(DATADIR1)/geth.ipc
PID_FILE1=$(DATADIR1)/run.pid
PSWD_FILE=./pswd.txt
PSWD=$(shell cat $(PSWD_FILE))
JS_FILE=./utils.js
AMOUNT=1

BASE_ARGS=--dev \
	--nodiscover \
	--networkid=15 \
	--maxpeers=10 \
    --verbosity=3 \
    --preload $(JS_FILE)

ARGS1=--datadir=$(DATADIR1) \
	$(BASE_ARGS) \
	--port=30305 \
    --rpc \
    --rpcaddr="127.0.0.1" \
    --rpcport=8545 \
    --rpcapi="eth,web3,personal" \
    --rpccorsdomain="*" \
    --mine \
    --minerthreads=1

console:
	$(NODE) $(ARGS1) attach $(IPC_FILE1)

getinfo:
	$(NODE) $(ARGS1) --exec '"Node - 1:: Balance: " + getBalance(eth.coinbase) + " ETH"' attach $(IPC_FILE1)

sendfrom:
	$(NODE) $(ARGS1) --exec 'personal.unlockAccount(eth.coinbase, "$(PSWD)", 2); quickSend(eth.coinbase, "$(ADDRESS)", $(AMOUNT));' attach $(IPC_FILE1)

account:
	$(NODE) $(ARGS1) --password=$(PSWD_FILE) account new

start:
	mkdir -p $(DATADIR1)
	@if [ "$(shell ls -A $(KEYSTORE1))" = "" ]; then\
		$(MAKE) account;\
	fi
	nohup $(NODE) $(ARGS1) > $(LOG_FILE1) 2>&1 & echo $$! > $(PID_FILE1)

stop: $(PID_FILE1)
	-kill -9 `cat $<` && `rm $<`

clean:
	find $(DATADIR1)/* -not -name 'keystore' -delete
