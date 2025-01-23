#!/usr/bin/python3
import subprocess
import json
import os
import httpx
import functools
import datetime
import base58
import bech32
import ecdsa
from mbedtls import hashlib
from ecdsa import SECP256k1

def compress_pubkey(pubkey_hex):
    """If the hex pubkey is uncompressed, compress it"""
    if pubkey_hex.startswith('04'):
        # chop off prefix indicating uncompressed if it is there
        pubkey_hex = pubkey_hex[2:]
    else:
        # return already compressed hex string
        return pubkey_hex
    # hex to binary
    pubkey_bytes = bytes.fromhex(pubkey_hex)
    # chop up in its two parts x and y
    x = int.from_bytes(pubkey_bytes[:32], byteorder='big')
    y = int.from_bytes(pubkey_bytes[32:], byteorder='big')
    # do the compression as by spec
    prefix = b'\x02' if y % 2 == 0 else b'\x03' 
    compressed = prefix + x.to_bytes(32, byteorder='big')
    # return as hex again
    return compressed.hex()

def key_to_addr(hexkey):
    """Convert hex key to a "1" type legacy bitcoin address"""
    # compress if needed
    chexkey = compress_pubkey(hexkey)
    # hex to binary
    key = bytes.fromhex(chexkey)
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
res = subprocess.run(["bitcoin-core.cli", "getrpcinfo"], stdout=subprocess.PIPE)
# Get username and password from the bitcoin core .cookie file
with open(os.path.join(os.path.dirname(json.loads(res.stdout)["logpath"]),".cookie"), "r") as cookiefile:
    username, password =cookiefile.read().split(":")

# Create the JSON-RPC client
rpc = JsonRpc(username, password)
# Get the hash for the genesis block
bhash = rpc.getblockhash(0)
# initialize block counter
count = 0
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
                    addr = key_to_addr(pvout["asm"].split(" ")[0])
                    # Base output
                    print("SPEND", addr, tim, count, txno, val, "pubkey")
                # Normal legacy adresses and modern bech32 keyhash adresses
                elif pvout["type"] in ("pubkeyhash", "witness_v0_keyhash"):
                    addr = pvout["address"]
                    # If it's a new 'bc' type bech32 address, convert to find the '1' adress with the same pubkey.
                    if addr.startswith("bc"):
                        addr = base58.b58encode(bytes(bech32.bech32_decode(addr)[1])).decode()
                    # Extract the signature depending on adress type
                    if pvout["type"] == "witness_v0_keyhash":
                        pkey = vin["prevout"]["txinwitness"][1]
                    else:
                        pkey = vin["scriptSig"]["asm"].split(" ")[-1]
                    # Record the signature and '1' type address alias for the adress for if we need it. 
                    print("ALIAS", pvout["address"], addr, pkey)
                    # Base output
                    print("SPEND", pvout["address"], tim, count, txno, val, "keyhash")
                # Scripthash adresses of different types
                elif pvout["type"] in ("scripthash", "witness_v0_scripthash", "witness_v1_taproot"):
                    # Get the public key used to sign with
                    pkey = vin["prevout"]["txinwitness"][1]
                    # Derive the "1" type adress that this pubkey would have
                    addr = key_to_addr(pkey)
                    # Record the signature and '1' type address alias for the adress for if we need it.
                    print("ALIAS", pvout["address"], addr, pkey)
                    # Base output
                    print("SPEND", pvout["address"], tim, count, txno, val, "scripthash")
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
                print("PUBKEY", addr, pkey)
                # Basic output
                print("RECV", addr, tim, count, txno, val, "pubkey")
            elif pvin["type"] in ("pubkeyhash", "witness_v0_keyhash"):
                print("RECV", pvin["address"], tim, count, txno, val, "keyhash")
            elif pvin["type"] in ("scripthash", "witness_v0_scripthash", "witness_v1_taproot"):
                print("RECV", pvin["address"], tim, count, txno, val, "scripthash")
        txno += 1
    count += 1
