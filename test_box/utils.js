var checkAllBalances = function() {
    var totalBal = 0;
    for (var acctNum in eth.accounts) {
        var acct = eth.accounts[acctNum];
        var acctBal = web3.fromWei(eth.getBalance(acct), "ether");
        totalBal += parseFloat(acctBal);
        console.log("  eth.accounts[" + acctNum + "]: \t" + acct + " \tbalance: " + acctBal + " ether");
    }
    console.log("  Total balance: " + totalBal + " ether");
};

var getBalance = function(address) {
    return web3.fromWei(eth.getBalance(address), "ether");
};

var quickSend = function(from, to, value) {
    return eth.sendTransaction({from: from, to: to, value: web3.toWei(value, "ether")});
};

var sendAndPrint = function(from, to, value) {
    var txid = quickSend(from, to, value);
    return eth.getTransaction(txid);
};