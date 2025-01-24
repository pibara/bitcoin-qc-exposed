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

def compress_pubkey(pubkey_hex):
    """If the hex pubkey is uncompressed, compress it"""
    if not pubkey_hex.startswith('04'):
        if len(pubkey_hex) != 66:
            raise RuntimeError("Compressed pubkey should be 33 bytes long")
        # return already compressed hex string
        return pubkey_hex
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


startblock = 0
if len(sys.argv) > 1:
    startblock = int(sys.argv[1])

# Call the cli tool once to find out where it is installed so we can get our .cookie file
res = subprocess.run(["bitcoin-core.cli", "getrpcinfo"], stdout=subprocess.PIPE)
# Get username and password from the bitcoin core .cookie file
with open(os.path.join(os.path.dirname(json.loads(res.stdout)["logpath"]),".cookie"), "r") as cookiefile:
    username, password =cookiefile.read().split(":")

# Create the JSON-RPC client
rpc = JsonRpc(username, password)
# Get the hash for the genesis block
bhash = rpc.getblockhash(startblock)
# initialize block counter
count = startblock
# Keep running untill we reach the last block
while bhash:
    # Get the block as JSON at maximum verbosity
    block = rpc.getblock(bhash, 3)
    # get the block time and convert it from unix time to ISO format
    tim =datetime.datetime.fromtimestamp(block["time"]).isoformat()
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
                    normalized = key_to_addr(compress_pubkey(pvout["asm"].split(" ")[0]))
                    if addr != normalized:
                        print("ALIAS", addr, normalized, compress_pubkey(pvout["asm"].split(" ")[0]), count, txno, "pubkey")
                    else:
                        print("PUBKEY", addr, compress_pubkey(pvout["asm"].split(" ")[0]), count, txno, "pubkey")
                    # Base output
                    print("SPEND", addr, tim, val, count, txno, "pubkey")
                # Normal legacy adresses and modern bech32 keyhash adresses
                elif pvout["type"] in ("pubkeyhash", "witness_v0_keyhash"):
                    # Extract the signature depending on adress type

                    if pvout["type"] == "witness_v0_keyhash":
                        pkey = compress_pubkey(vin["prevout"]["txinwitness"][1])
                    else:
                        pkey = compress_pubkey(vin["scriptSig"]["asm"].split(" ")[-1])
                    # Normalize from pubkey to "1" address
                    addr = key_to_addr(pkey)
                    if addr != pvout["address"]:
                        # Record the signature and '1' type address alias for the adress for if we need it. 
                        print("ALIAS", pvout["address"], addr, pkey, count, txno, pvout["type"])
                    else:
                        print("PUBKEY", pvout["address"], pkey, count, txno, pvout["type"])
                    # Base output
                    print("SPEND", pvout["address"], tim, val, count, txno, pvout["type"])
                # Scripthash adresses of different types
                elif pvout["type"] in ("scripthash", "witness_v0_scripthash", "witness_v1_taproot"):
                    # Get the public key used to sign with
                    if "txinwitness" in vin["prevout"] and len(vin["prevout"]["txinwitness"]) > 1:
                        pkey = compress_pubkey(vin["prevout"]["txinwitness"][1])
                        # Derive the "1" type adress that this pubkey would have
                        addr = key_to_addr(pkey)
                        # Record the signature and '1' type address alias for the adress for if we need it.
                        print("ALIAS", pvout["address"], addr, pkey, count, txno, pvout["type"])
                    # Special case, not sure why.
                    elif "scriptSig" in vin and vin["scriptSig"]["asm"].startswith("5121"):
                        pkey = vin["scriptSig"]["asm"][4:70]
                        addr = key_to_addr(pkey)
                        print("ALIAS", pvout["address"], addr, pkey, count, txno, pvout["type"], "special-01")
                    elif "scriptSig" in vin and len(vin["scriptSig"]["asm"]) < 10:
                        pass
                    else:
                        print("MISSING", count, txno, pvout["type"], vin)
                        raise RuntimeError("Missing pubkey")
                    # Base output
                    print("SPEND", pvout["address"], tim, val, count, txno, pvout["type"])
        # Itterate all outputs for this transaction
        for vout in tx["vout"]:
            # Get the new output script and value
            val = vout["value"]
            pvin = vout["scriptPubKey"]
            # Really old transactions use the uncompressed pubkey
            if pvin["type"] == "pubkey":
                # Compress the pubkey
                pkey = compress_pubkey(pvin["asm"].split(" ")[0])
                # Determine the '1' type address for this pubkey
                addr = key_to_addr(pkey)
                # Log that this pubkey belongs to this adress
                print("PUBKEY", addr, pkey, count, txno, "pubkey")
                # Basic output
                print("RECV", addr, tim, val, count, txno, "pubkey")
            elif pvin["type"] in ("pubkeyhash", "witness_v0_keyhash"):
                print("RECV", pvin["address"], tim, val, count, txno, pvin["type"])
            elif pvin["type"] in ("scripthash", "witness_v0_scripthash", "witness_v1_taproot"):
                print("9 RECV", pvin["address"], tim, val, count, txno, pvin["type"])
        txno += 1
    count += 1
