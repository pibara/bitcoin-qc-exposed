#!/usr/bin/python3
import subprocess
import json
import os
import sys
import httpx
import functools
import datetime
import base58
import ecdsa
from mbedtls import hashlib
from ecdsa import SECP256k1
import argparse

def compress_pubkey(pubkey_hex):
    """If the hex pubkey is uncompressed, compress it"""
    if pubkey_hex[:2] in ('02', '03'):
        if len(pubkey_hex) != 66:
            raise RuntimeError("Compressed pubkey should be 33 bytes long")
        # return already compressed hex string
        return pubkey_hex
    if not pubkey_hex.startswith('04'):
        raise RuntimeError("Pubkey should start with 02/03/04")
    if len(pubkey_hex) != 130:
        raise RuntimeError("Unompressed pubkey should be 65 bytes long")
    x = pubkey_hex[2:66]  # x-coordinate in hex
    y = int(pubkey_hex[66:], 16)  # Convert y-coordinate to integer
    if y % 2 == 0:
        pubkey_compressed = '02' + x
    else:
        pubkey_compressed = '03' + x
    return pubkey_compressed

def key_to_addr(hexkey, ignore_size=False):
    """Convert hex key to a "1" type legacy bitcoin address"""
    # compress if needed
    if len(hexkey) != 66:
        if len(hexkey) != 130:
            raise RuntimeError("Pubkey should be 33 or 65 bytes long")
        if not ignore_size:
            raise RuntimeError("ignore_size should be set for 65 byte long pubkeys")
    # hex to binary
    key = bytes.fromhex(hexkey)
    # sha256 + ripemd160 hashing as by spec
    hash1 = hashlib.sha256()
    hash2 = hashlib.new('ripemd160')
    hash1.update(key)
    hash2.update(hash1.digest())
    # prefix with bitcoin 00 header
    core = b"\x00" + hash2.digest()
    # hash twice for integrity hash
    hash3 = hashlib.sha256()
    hash4 = hashlib.sha256()
    hash3.update(core)
    hash4.update(hash3.digest())
    # return with integrity hash appended to get a full legacy bitcoin address.
    return base58.b58encode(core + hash4.digest()[:4]).decode()

class JsonRpc:
    """Trivial synchounous JSON-RPC client for bitcoin core node"""
    def __init__(self, user, passw):
        """Constructor"""
        # create basi auth object from username and password
        auth = httpx.BasicAuth(username=user, password=passw)
        # Create a http client
        self._client = httpx.Client(auth=auth)
        # initialize JSON-RPC id
        self._id = 0

    def _method(self, method, *args):
        """Gereric pass-through JSON-RPC method invocation"""
        # increment the JSON-RPC call id so it is unique
        self._id += 1
        # Construct the JSON-RPC request
        request = json.dumps({"jsonrpc": "1.0", "id": self._id, "method": method, "params": list(args)})
        # Call with a large timeout
        response = self._client.post("http://127.0.0.1:8332/",  data=request, timeout=120.0).json()
        # Return results if OKm raise exception otherwise
        if response["error"] is None:
            return response["result"]
        raise RuntimeError(response["error"])

    def __getattr__(self, method):
        """Accept any possible method and assume it is a valid JSON-RPC method"""
        return functools.partial(self._method, method) 

# Call the cli tool once to find out where it is installed so we can get our .cookie file
print("Looking for bitcoin-core.cli work dir")
res = subprocess.run(["bitcoin-core.cli", "getrpcinfo"], stdout=subprocess.PIPE)
# Get username and password from the bitcoin core .cookie file
print("Getting RPC password")
with open(os.path.join(os.path.dirname(json.loads(res.stdout)["logpath"]),".cookie"), "r") as cookiefile:
    username, password =cookiefile.read().split(":")

print("Initiating RPC")
# Create the JSON-RPC client
rpc = JsonRpc(username, password)
blocks = rpc.getblockchaininfo()["blocks"]
print("Parsing commandline arguments")
parser = argparse.ArgumentParser(sys.argv[0])
parser.add_argument("--blockfilein", default="", help="file to read starting block from")
parser.add_argument("--blockfileout", default="", help="file to write ending block plus one to")
subparsers = parser.add_subparsers(dest="cmd", help='export or filter')
export_parser = subparsers.add_parser("export")
filter_parser = subparsers.add_parser('filter')
export_parser.add_argument("--startblock", type=int, default=0, help="block to start")
filter_parser.add_argument("--startblock", type=int, default=blocks - 144 + 1, help="block to start")
export_parser.add_argument("--out", default="events.log", help="text file to send event lines to")
filter_parser.add_argument("--out", default="filtered.log", help="text file to send event lines to")
filter_parser.add_argument("--exposedfilein", default="exposed.log", help="file to read exposed addresses and meta data from") 
filter_parser.add_argument("--taskblocks", type=int, default=144, help="number of blocks to run the filter run over")
args = parser.parse_args(sys.argv[1:])
if args.cmd is None:
    parser.print_help()
    sys.exit(1)
print("Running in", args.cmd, "mode")
count = args.startblock
print("Opening output file:", args.out)
out  = open(args.out, "w")
print("When done, block number will be written to", args.out)
outfile_block = args.blockfileout
lookup = {}
taskblocks = 1000000000
if args.cmd == "filter":
    expdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "881340")
    for efilepath in [os.path.join(expdir, f) for f in os.listdir(expdir) if os.path.isfile(os.path.join(expdir, f))]:
        print("Processing", efilepath)
        with open(efilepath) as efile:
            for line in efile:
                line = line[:-1]
                cmd=line.split(" ")
                if cmd[0] == "EXPOSED":
                    lookup[cmd[1]] = cmd[2:]
    print("Imported", len(lookup), "exposed addresses")
    taskblocks = args.taskblocks
    print("Stopping after", taskblocks, "blocks")
print("Triggers on", len(lookup),"addresses") 
if args.blockfilein:
    with open(args.blockfilein) as infil:
        count = int(infil.read()) + 1
        print("Read start block from", args.blockfilein, ":", count)
maxblock = count + taskblocks
# Get the hash for the genesis block
bhash = rpc.getblockhash(count)
# initialize block counter
# Keep running untill we reach the last block
while bhash and count < maxblock:
    # Get the block as JSON at maximum verbosity
    block = rpc.getblock(bhash, 3)
    # get the block time and convert it from unix time to ISO format
    tim =datetime.datetime.fromtimestamp(block["time"]).isoformat()
    print("Processing block", count, tim)
    # Get the block hash for the next round in this while loop
    bhash=None
    if "nextblockhash" in block:
        bhash = block["nextblockhash"]
    # initialize transaction counter within this block
    txno = 0
    # Itterate all transactions in this block
    for tx in block["tx"]:
        # Itterates all inputs for this transaction
        for vin in tx["vin"]:
            # If the input is USO, process it.
            if "prevout" in vin:
                # Get the previous output script and value
                pvout = vin["prevout"]["scriptPubKey"]
                val = vin["prevout"]["value"] 
                # Really old transactions use the uncompressed pubkey
                if pvout["type"] == "pubkey":
                    # Normalize from pubkey to "1" address
                    addr = key_to_addr(pvout["asm"].split(" ")[0], ignore_size=True)
                    if addr in lookup:
                        exposed_state = lookup[addr]
                        print("TRIGGER", addr, tim, val, count, txno, "pubkey",
                                exposed_state[0], exposed_state[1], exposed_state[2], exposed_state[3], file=out)
                    normalized = key_to_addr(compress_pubkey(pvout["asm"].split(" ")[0]))
                    if addr != normalized:
                        if normalized in lookup:
                            exposed_state = lookup[normalized]
                            print("TRIGGER", addr, tim, val, count, txno, "pubkey",
                                    exposed_state[0], exposed_state[1], exposed_state[2], exposed_state[3], file=out)
                        print("ALIAS", addr, normalized, compress_pubkey(pvout["asm"].split(" ")[0]), count, txno, "pubkey",
                                file=out)
                    else:
                        print("PUBKEY", addr, compress_pubkey(pvout["asm"].split(" ")[0]), count, txno, "pubkey",
                                file=out)
                    # Base output
                    print("SPEND", addr, tim, val, count, txno, "pubkey", file=out)
                # Normal legacy adresses and modern bech32 keyhash adresses
                elif pvout["type"] in ("pubkeyhash", "witness_v0_keyhash"):
                    # Extract the signature depending on adress type
                    if pvout["type"] == "witness_v0_keyhash":
                        if "txinwitness" in vin["prevout"]:
                            pkey = compress_pubkey(vin["prevout"]["txinwitness"][1])
                        else:
                            pkey = compress_pubkey(vin["txinwitness"][1])
                    else:
                        pkey = compress_pubkey(vin["scriptSig"]["asm"].split(" ")[-1])
                    # Normalize from pubkey to "1" address
                    addr = key_to_addr(pkey)
                    if addr in lookup:
                        exposed_state = lookup[addr]
                        print("TRIGGER", addr, tim, val, count, txno, "pubkey",
                                exposed_state[0], exposed_state[1], exposed_state[2], exposed_state[3], file=out)
                    if addr != pvout["address"]:
                        # Record the signature and '1' type address alias for the adress for if we need it. 
                        print("ALIAS", pvout["address"], addr, pkey, count, txno, pvout["type"], file=out)
                    else:
                        print("PUBKEY", pvout["address"], pkey, count, txno, pvout["type"], file=out)
                    # Base output
                    print("SPEND", pvout["address"], tim, val, count, txno, pvout["type"], file=out)
                # Scripthash adresses of different types
                elif pvout["type"] in ("scripthash", "witness_v0_scripthash", "witness_v1_taproot"):
                    # Get the public key used to sign with
                    if "txinwitness" in vin["prevout"] and len(vin["prevout"]["txinwitness"]) > 1:
                        pkey = compress_pubkey(vin["prevout"]["txinwitness"][1])
                        # Derive the "1" type adress that this pubkey would have
                        addr = key_to_addr(pkey)
                        if addr in lookup:
                            exposed_state = lookup[addr]
                            print("TRIGGER", addr, tim, val, count, txno, "pubkey",
                                    exposed_state[0], exposed_state[1], exposed_state[2], exposed_state[3], file=out)
                        # Record the signature and '1' type address alias for the adress for if we need it.
                        print("ALIAS", pvout["address"], addr, pkey, count, txno, pvout["type"], file=out)
                    # Special case, not sure why.
                    elif "scriptSig" in vin and vin["scriptSig"]["asm"].startswith("5121"):
                        pkey = vin["scriptSig"]["asm"][4:70]
                        addr = key_to_addr(pkey)
                        if addr in lookup:
                            exposed_state = lookup[addr]
                            print("TRIGGER", addr, tim, val, count, txno, "pubkey",
                                    exposed_state[0], exposed_state[1], exposed_state[2], exposed_state[3], file=out)
                        print("ALIAS", pvout["address"], addr, pkey, count, txno, pvout["type"], "special-01", file=out)
                    elif "scriptSig" in vin and len(vin["scriptSig"]["asm"]) < 10:
                        print("SKIP-PUBKEY", pvout["address"], None, None, count, txno, pvout["type"], "special-02", file=out)
                        pass
                    elif "scriptSig" in vin and vin["scriptSig"]["asm"].split(" ")[-1][:2] in ("51", "52","53","54","58", "41", "21"):
                        keys_string = vin["scriptSig"]["asm"].split(" ")[-1]
                        if vin["scriptSig"]["asm"].split(" ")[-1][:2] not in ("41", "21"):
                            keys_string = keys_string[2:]
                        keys = []
                        while keys_string[:2] in ("21", "41"):
                            if keys_string[:2] == "21":
                                new_key = keys_string[2:68]
                                if len(new_key) == 66 and new_key[:2] in ("02", "03"):
                                    keys.append(new_key)
                                keys_string = keys_string[68:]
                            else:
                                new_key = keys_string[2:132]
                                if len(new_key) == 130 and new_key[:2] == "04":
                                    keys.append(new_key)
                                keys_string = keys_string[132:]
                        if len(keys_string) > 2:
                            print("MISSING3", pvout["address"], None, None, count, txno, pvout["type"], keys_string, file=out)
                        if len(keys) == 0: 
                            print("MISSING2", pvout["address"], None, None, count, txno, pvout["type"], vin, file=out)
                            #raise RuntimeError("Missmatch on multisig")
                        elif len(keys) == 1:
                            key = keys[0]
                            key2 = compress_pubkey(key)
                            addr = key_to_addr(key2)
                            if addr in lookup:
                                exposed_state = lookup[addr]
                                print("TRIGGER", addr, tim, val, count, txno, "pubkey",
                                        exposed_state[0], exposed_state[1], exposed_state[2], exposed_state[3], file=out)
                            print("ALIAS", pvout["address"], addr, key2, count, txno, pvout["type"], "special-03", file=out)
                            if key != key2:
                                addr2 = key_to_addr(key, ignore_size=True)
                                if addr2 in lookup:
                                    exposed_state = lookup[addr2]
                                    print("TRIGGER", addr, tim, val, count, txno, "pubkey",
                                            exposed_state[0], exposed_state[1], exposed_state[2], exposed_state[3], file=out)
                                print("ALIAS", addr, key_to_addr(key, ignore_size=True), key2, count, txno, pvout["type"], "special-03", file=out)
                        else:
                            for key in keys:
                                key2 = compress_pubkey(key)
                                addr = key_to_addr(key2)
                                print("MULTI1", pvout["address"], addr, key2, count, txno, pvout["type"], file=out)
                                if addr in lookup:
                                    exposed_state = lookup[addr]
                                    print("TRIGGER", addr, tim, val, count, txno, "pubkey",
                                            exposed_state[0], exposed_state[1], exposed_state[2], exposed_state[3], file=out)
                                if key != key2:
                                    addr2 = key_to_addr(key, ignore_size=True)
                                    if addr2 in lookup:
                                        exposed_state = lookup[addr2]
                                        print("TRIGGER", addr, tim, val, count, txno, "pubkey",
                                                exposed_state[0], exposed_state[1], exposed_state[2], exposed_state[3], file=out)
                                    print("ALIAS", addr, key_to_addr(key, ignore_size=True), key2, count, txno, pvout["type"], file=out)
                    elif "scriptSig" in vin and len(vin["scriptSig"]["hex"]) < 66:
                        print("MISSING1", pvout["address"], None, None, count, txno, pvout["type"], vin, file=out)
                    else:
                        print("MISSING0", pvout["address"], None, None, count, txno, pvout["type"], vin, file=out)
                        #raise RuntimeError("Missing pubkey")
                    # Base output
                    if pvout["address"] in lookup:
                        exposed_state = lookup[pvout["address"]]
                        print("TRIGGER", pvout["address"], tim, val, count, txno, "pubkey",
                                exposed_state[0], exposed_state[1], exposed_state[2], exposed_state[3], file=out)
                    print("SPEND", pvout["address"], tim, val, count, txno, pvout["type"], file=out)
        # Itterate all outputs for this transaction
        for vout in tx["vout"]:
            # Get the new output script and value
            val = vout["value"]
            pvin = vout["scriptPubKey"]
            # Really old transactions use the uncompressed pubkey
            if pvin["type"] == "pubkey":
                pubkey = pvin["asm"].split(" ")[0]
                if pubkey[:2] in ("02", "03", "04"):
                    pkey = compress_pubkey(pubkey)
                    # Determine the '1' type address for this pubkey
                    addr = key_to_addr(pkey)
                    # Log that this pubkey belongs to this adress
                    print("PUBKEY", addr, pkey, count, txno, "pubkey", file=out)
                    # Basic output
                    print("RECV", addr, tim, val, count, txno, "pubkey", file=out)
                else:
                    print("SKIP", None, tim, val, count, txno, "pubkey", file=out)
            elif pvin["type"] in ("pubkeyhash", "witness_v0_keyhash"):
                print("RECV", pvin["address"], tim, val, count, txno, pvin["type"], file=out)
            elif pvin["type"] in ("scripthash", "witness_v0_scripthash", "witness_v1_taproot"):
                print("RECV", pvin["address"], tim, val, count, txno, pvin["type"], file=out)
        txno += 1
    count += 1
if args.blockfileout:
    print("Writing last block number to", args.blockfileout)
    with open(args.blockfileout, "w") as bfo:
        bfo.write(str(count) + "\n")
print("Done")
