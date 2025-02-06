# Tools for a Bitcoin Quantum Computing Kanarie

This repo contains a set of simple tools that are meant to look at the idea of a kanarie service for BitCoin that might expose a future quantum computing blockchain heist. 

The idea is that all unspent outputs tied to a public key that is exposed on the blockchain are considered vulnerable to future generations of general purpose quantum computers, and monitoring transactions from these vulnerable public keys, especially long dormant public keys could expose an ongoing attack.

Please note that running the scripts in this repo will take a long time. Hours, usualy. Up to more than a day for the initial run for one of the scripts, possibly longer depending on your system specs. Syncing your bitcoin core node before you can run the scripts also will take days unless your internet connection is really fast.

## Disk storage requirements

The scripts will work with huge text files containing important logs that span the entire blockchain. If you want to run these scripts and a bitcoin node without gathering any debug info (so you can improve the scripts), make sure you have at least 2TB of free storage. Add an extra TB if you want to either run everything with debug logging on or if you want to run additional related nodes in the future. 

# Bitcoin node

The scripts in this repo expect a locally running bitcoin core node. The first script will communicate with the bitcoin core node to extract block data. So if you want to run these scripts, please first install and sync up your bitcoin core node first.

## btcqc1.py

This script communicates with your local bitcoin node and extracts events it deems relevant for the kanarie service. Each event is output on a single line to one of multiple output files. The script is normally run in incremental mode, but the first time you run it you should run it in **init** mode.

```
./btcqc1.py init
```

This first run is going to take a long time. On my system it takes almost two days to run in init mode. Incremental runs will take significantly shorter.

If you are interested in knowing what events the script is missing out on currently (some transactions can be hard to parse or may need aditional info outside of what the simple logic of this script can provide), you can ask the script to output debug events to a seperate file.

```
./btcqc1.py init debug
```

The script will connect to the local bitcoin node and ask for the last block block number. It will use this number to create a snapshot directory with a name that equates the block number. In this directory the script will write a number of files.

### stripped.log

The *stripped.log* output file will contain two types of events:

* RECV
* SPEND

A RECV event will look something like this:

```
RECV 1FYPDCP1uVnPgEE3gaDMbAApdv9XYX7Si5 2009-01-03T19:15:05 50.0 0 0 pubkey
```

A SPEND event will look something like this:

```
SPEND 12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S 2009-01-12T04:30:25 50.0 170 1 pubkey
```

The structure of the event ti simple:

* Event-type 
* Bitcoin Address
* Event time
* Ammount
* Block number
* Transaction number within block


### pubkey.log

The output file *pubkey.log* currently contains the following event types

* PUBKEY 
* ALIAS  
* MULTI1 

A sample of these event types:

```
PUBKEY 1FYPDCP1uVnPgEE3gaDMbAApdv9XYX7Si5 03678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb6 0 0 pubkey
ALIAS 12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S 13KiMqUJ7xD6MhUD2k7mKEoZMHDP9HdWwW 0311db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5c 170 1 pubkey
MULTI1 3A5XQWZPzG4GrpVeYFaDBZ1s4sXkYB69Wf 1PCURmYByxc5sVZ15m8S7c8F1bXkS9nyS6 0307ac6296168948c3f64ce22f51f6e5424f936c846f1d01223b3d9864f4d95566 177609 24 scripthash
```

Note that the structure of a pubkey event is a tiny bit different that of the other two. Also note the lack of timestamps from these events as timestamps would be redundant given that that info is already contained in matching SPEND events.

A PUBKEY event has the following structure:

* Event-type
* Address
* Public key (always the compressed pubkey)
* Block number
* Transaction number within the block

The ALIAS and MULTI1 events have a close but somewhat different structure with an extra address. ALIAS events are emitted when in early blocks uncompressed addresses were used. We consider these uncompressed addresses aliasses for the addresses that would exist if the public key had been compressed. If the pubkey is exposed it is exposed for both the address used in the SPEND event and for any future USOs using the same signing key but with a compressed pubkey.

* Event-type
* Address
* Compressed-pubkey alias for the address
* Public key (always the compressed pubkey)
* Block number
* Transaction number within the block 

There are also similar ALIAS entries involving witness\_v0\_keyhash addresses. Again there an ALIAS event will be emitted on exposure to disclose the fact that both addresses are exposed in the transaction, not just the witness\_v0\_keyhash address.

For MULTI1 the reasoning is similar. If a SPEND is done using multisig, the signatures used that expose the multisig address not only expose the multi sig address, but also any '1' address that directly derives from the signing key used.

### debug.log

If you run the script with *debug* argument, an additional file will get added containing MISSINGn and SKIP events. Discussion of these events falls outside of the scope of this readme.

## Incremental mode

After our seccond script (that we will discuss later) has been run, we will run btcqc1.py only in incremental mode.

```
./btcqc1.py
```

Doing this will do two things. It will run the same logic as initial mode, but only for the new blocks, creating a new snapshot dir in the process, and it will look for use in SPEND events of addresses that were set on the watch-list by the previous run of our second script.

If such an event occurs, it is written to an additional file:

### trigger.log

The *trigger.log* file of incremental runs will contain TRIGGER events. There are emitted when new SPEND transactions on watch-list addresses are detected.
Here is an example.

```
TRIGGER 1KWhgos1nynvVQ9g88VUYAtiyWtgNkiD6z 2025-02-01T03:53:47 5.0 881710 187 pubkey 20.602152290000003 2010-07-23T23:47:34 2021-02-15T20:34:59 2018-01-30T01:19:33
```

The structure of this event is as follows:

* Event-type
* Address
* Time of trigger event
* Amount
* Block number
* Transaction number within the block
* -
* Total amount at address before the SPEND
* Time this address was first seen on the chain 
* Last moment this address received funds
* Last time this address spent funds 


So for the example event, the key with addess 1KWhgos1nynvVQ9g88VUYAtiyWtgNkiD6z was used to spent 5.0 bitcoin out of the about 20.6 bitcoin the address held on the previous snapshot. This address (or its uncompressed equivalent) was seen first on the blockchain on june 23 2010,  the last time it was passive (RECV) part of a transaction was on february 15 2021, and the last time the address was actively part of a transaction (SPEND) was january 30 2018.

If we were 10 years into the future, this TRIGGER event might be part of a quantum blockchain heist, right now QC hasn't by far come to the level where transactions like this would be suspect, and the amount and size of TRIGGER events now in 2025 is a clear sign that we have a long way to go in terms of awareness. But we hope these scripts could help a bit with the awareness part.  

# btcqc2.py

The second script in this script collection is *btcqc2.py*. Like *btcqc1.py* this script has a **init** option that should be used on the first run. Without that option the script runs in incremental mode.

```
./btcqc2.py init
```

The first run for this script, assuming modern SSDs and a decent CPU, should take a few hours on the first run. What the script primaraly does in **init** mode is go through the event files generated by btcqc1.py, and find all addresses that both have their public key exposed on the blockchain AND still have unspent putputs of at least 0.01 BTC. The idea is that when QC becomes advanced enough to slice through a ECDSA public keys in hours up to weeks, smaller funds keys won't likely become a target of such attacks.

Because on the initial run the amount of public keys to keep track off will be huge, too huge probably to keep in memory, the initial run will in fact be 16 distinct runs where the public key address space is divided between runs using the first three characters of the compressed pubkey.

The script in **init** mode will generate 16 output files named **exposed020-021.log** up to **exposed03e-03f.log**, representing the part of the pubkey address space covered by the file.

Each of the files will contain lines like this:

```
EXPOSED 13yNg5QcCSXZTCVY5VucfqNqm6nQQETXfo 2500.0 2016-07-25T04:08:19 2016-08-08T23:26:35 2016-09-01T03:37:17
```

This line is buils up as follows:

* Eventy-type
* Address
* Amount of USO still bound to the address
* Moment this key (or its uncompressed alias) was first used
* Last moment this address received funds
* Last moment this address spent funds.

The TRIGGER events discussed with the btcqc1.py are derived from the EXPOSED events.
After (and only after) btcqc2.py has been run in init mode once, will btcqc1.py be able to run in incremental mode. In fact, btcqc2.py should be run after every run of btcqc1.py to ensure the next incremental run of btcqc1.py will run correctly.


Just like btcqc1.py, btcqc2.py can be run in incremental mode. Doing so will create update expose.log files based on only those pubkeys exposed in the increment.

```
./btcqc2.py
``` 

The btcqc2.py will maintain the *runs.var* file to keep track of snapshot dirs with completed btcqc2.py runs.

# Comming up

From this we want to create a 3th script for generating increment kanarie reports.
