# Tools for a Bitcoin Quantum Computing Kanarie

This repo contains a set of simple tools that are meant to look at the idea of a kanarie service for BitCoin that might expose a future quantum computing blockchain heist. 

The idea is that all unspent outputs tied to a public key that is exposed on the blockchain are considered vulnerable to future generations of general purpose quantum computers, and monitoring transactions from these vulnerable public keys, especially long dormant public keys could expose an ongoing attack.

Please note that running the scripts in this repo will take a long time. Hours, usualy. Up to days for some scripts. Syncing your bitcoin core node before you can run the scripts also will take days unless your internet connection is really fast.

## Running a bitcoin node

The scripts in this repo expect a locally running bitcoin core node. The first and the last script will communicate with the bitcoin core node to extract block data. So if you want. 

## event-export.py

This script (currently being tested and patched) communicates with your local bitcoin node and extracts events it deems relevant for the kanarie service. Each event is output on a single line.

Currently the following event types are defined:

* PUBKEY 
* ALIAS  
* MULTI1 
* RECV
* SPEND
* MISSINGn / SKIP

You run this script like this:

```
./event-export.py 0 | tee events.txt
```

### PUBKEY

```
PUBKEY 1FYPDCP1uVnPgEE3gaDMbAApdv9XYX7Si5 03678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb6 0 0 pubkey
PUBKEY 1PKW9GWX2P2JhCSR17BXa4B8MJ4ozUjW9Y 0296b538e853519c726a2c91e61ec11600ae1390813a627c66fb8be7947be63c52 1 0 pubkey
PUBKEY 13JhbjHvD4AwYc6hvXkgjan9WkEcKD4XTB 037211a824f55b505228e4c3d5194c1fcfaa15a456abdf37f9b9d97a4040afc073 2 0 pubkey
PUBKEY 16sTJe2MXk2corPi5kReMQF9CAhrZMYDtc 0294b9d3e76c5b1629ecf97fff95d7a4bbdac87cc26099ada28066c6ff1eb91912 3 0 pubkey
```

### ALIAS

```
ALIAS 12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S 13KiMqUJ7xD6MhUD2k7mKEoZMHDP9HdWwW 0311db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5c 170 1 pubkey
ALIAS 12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S 13KiMqUJ7xD6MhUD2k7mKEoZMHDP9HdWwW 0311db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5c 181 1 pubkey
ALIAS 12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S 13KiMqUJ7xD6MhUD2k7mKEoZMHDP9HdWwW 0311db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5c 182 1 pubkey
ALIAS 12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S 13KiMqUJ7xD6MhUD2k7mKEoZMHDP9HdWwW 0311db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5c 183 1 pubkey
```

### MULTI1

```
MULTI1 3A5XQWZPzG4GrpVeYFaDBZ1s4sXkYB69Wf 1PCURmYByxc5sVZ15m8S7c8F1bXkS9nyS6 0307ac6296168948c3f64ce22f51f6e5424f936c846f1d01223b3d9864f4d95566 177609 24 scripthash
MULTI1 3A5XQWZPzG4GrpVeYFaDBZ1s4sXkYB69Wf 1HVJDd72T57LX1xq5ggNPHSxRv6iADuURD 03ac6ad514715bec8d5de1873b9bc873bb71773b51338b4d115f9938b6a029b7d1 177609 24 scripthash
MULTI1 3FArYwLzPwRBbh1yN3Fx6tBZ5rZBPdaMPt 1Jfv1gFEDL1efMka87JYbK7uVXi3shMS4e 032c6aa78662cc43a3bb0f8f850d0c45e18d0a49c61ec69db87e072c88d7a9b6e9 177618 78 scripthash
MULTI1 3FArYwLzPwRBbh1yN3Fx6tBZ5rZBPdaMPt 1JNoSoaBgDTvpbEWHAqoXkMs1yYBEqAt4V 0353581fd2fc745d17264af8cb8cd507d82c9658962567218965e750590e41c41e 177618 78 scripthash
MULTI1 3FArYwLzPwRBbh1yN3Fx6tBZ5rZBPdaMPt 13GeragZzUpos6i4Ve81k4DettzTXBwEZc 024fe45dd4749347d281fd5348f56e883ee3a00903af899301ac47ba90f904854f 177618 78 scripthash
MULTI1 3CK4fEwbMP7heJarmU4eqA3sMbVJyEnU3V 1Bt8XZ3RDUUsRmmqM26uCfNxQF6SEyrjvt 022afc20bf379bc96a2f4e9e63ffceb8652b2b6a097f63fbee6ecec2a49a48010e 177625 51 scripthash
MULTI1 3CK4fEwbMP7heJarmU4eqA3sMbVJyEnU3V 12ppVrt7pVMQnVpekHmrcEZ5vUnUcFfV6w 03a767c7221e9f15f870f1ad9311f5ab937d79fcaeee15bb2c722bca515581b4c0 177625 51 scripthash
```

### RECV

```
RECV 1FYPDCP1uVnPgEE3gaDMbAApdv9XYX7Si5 2009-01-03T19:15:05 50.0 0 0 pubkey
RECV 1PKW9GWX2P2JhCSR17BXa4B8MJ4ozUjW9Y 2009-01-09T03:54:25 50.0 1 0 pubkey
RECV 13JhbjHvD4AwYc6hvXkgjan9WkEcKD4XTB 2009-01-09T03:55:44 50.0 2 0 pubkey
RECV 16sTJe2MXk2corPi5kReMQF9CAhrZMYDtc 2009-01-09T04:02:53 50.0 3 0 pubkey
```

### SPEND

```
SPEND 12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S 2009-01-12T04:30:25 50.0 170 1 pubkey
SPEND 12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S 2009-01-12T07:02:13 40.0 181 1 pubkey
SPEND 12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S 2009-01-12T07:12:16 30.0 182 1 pubkey
SPEND 12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S 2009-01-12T07:34:22 29.0 183 1 pubkey
SPEND 13HtsYzne8xVPdGDnmJX8gHgBZerAfJGEf 2009-01-12T08:16:40 1.0 187 1 pubkey
SPEND 1LzBzVqEeuQyjD2mRWHes3dgWrT9titxvq 2009-01-12T15:21:00 1.0 221 1 pubkey
SPEND 12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S 2009-01-12T21:04:20 28.0 248 1 pubkey
SPEND 18SH9vwx24L5cTabfkgtGMjF8A56pD9AUJ 2009-01-14T21:40:55 50.0 496 1 pubkey
SPEND 15NUwyBYrZcnUgTagsm1A7M2yL2GntpuaZ 2009-01-14T21:40:55 1.0 496 1 pubkey
SPEND 1ByLSV2gLRcuqUmfdYcpPQH8Npm8cccsFg 2009-01-14T21:40:55 10.0 496 1 pubkey
```

### MISSING1 / MISSING2 / MISSING3 / SKIP

```
MISSING3 3CK4fEwbMP7heJarmU4eqA3sMbVJyEnU3V None None 203376 50 scripthash 52ae
MISSING3 3CK4fEwbMP7heJarmU4eqA3sMbVJyEnU3V None None 203376 219 scripthash 52ae
MISSING3 3DARyyGK1Z1RyYPcPHSkgXhRjqa2fSDycb None None 203912 4 scripthash 52ae
```


### MISSING0

```
MISSING0 3Db2yLjibuyS9r1JZ4p1mQXr3ZBMA1Zhf6 None None 284029 17 scripthash {'txid': 'ae8196ac3a815ea30f34149c812ea48609819f0fc7a7b6f2799a39e32e78a498', 'vout': 0, 'scriptSig': {'asm': '30450220087ede38729e6d35e4f515505018e659222031273b7366920f393ee3ab17bc1e022100ca43164b757d1a6d1235f13200d4b5f76dd8fda4ec9fc28546b2df5b1211e8df[SINGLE] 0275983913e60093b767e85597ca9397fb2f418e57f998d6afbbc536116085b1cb -4524', 'hex': '4830450220087ede38729e6d35e4f515505018e659222031273b7366920f393ee3ab17bc1e022100ca43164b757d1a6d1235f13200d4b5f76dd8fda4ec9fc28546b2df5b1211e8df03210275983913e60093b767e85597ca9397fb2f418e57f998d6afbbc536116085b1cb02ac91'}, 'prevout': {'generated': False, 'height': 284024, 'value': 0.001, 'scriptPubKey': {'asm': 'OP_HASH160 827fe37ec405346ad4e995323cea83559537b89e OP_EQUAL', 'desc': 'addr(3Db2yLjibuyS9r1JZ4p1mQXr3ZBMA1Zhf6)#8zeh7xyw', 'hex': 'a914827fe37ec405346ad4e995323cea83559537b89e87', 'address': '3Db2yLjibuyS9r1JZ4p1mQXr3ZBMA1Zhf6', 'type': 'scripthash'}}, 'sequence': 4294967295}
```

## event-process.py

This script, that takes a long time to run, will take the output files from the event-export.py file, and process it to create an output file with lines that look like this:

```
EXPOSED 1GSn6DXfX1fUsVk8VcC2RtR1SJYrS4eM9z 0.73249349 2012-04-22T12:05:13 2012-06-04T18:17:17 2012-06-04T18:17:17
```

The output is limited to adressed with a balances of 0.001 bitcoin or more that have had their public key exposed.

After the balance three timestamps are recorded.

* The time this adress was first seen
* The time of the last RECV event for this address.
* The time of the last SPEND event for this address.

Please note that the address used here is the **normalized** address. This is mostly relevant for old pubkeys and adresses that were created using uncompressed adresses.
