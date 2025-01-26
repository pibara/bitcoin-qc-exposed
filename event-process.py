#!/usr/bin/python3
import sys

for code in range(512, 1024):
    start = "{:04x}".format(code) 
    exposed = set()
    normalize = {}
    for file in sys.argv[1:]:
        with open(file) as inpfil:
            for line in inpfil:
                if "\n" in line:
                    cmd = line.split(" ")
                    if cmd[0] in ("ALIAS", "MULTI1"):
                        pubkey = cmd[3]
                        if pubkey.startswith(start):
                            addr = cmd[1]
                            normalized = cmd[2]
                            exposed.add(addr)
                            exposed.add(normalized)
                            if addr.startswith("1"):
                                normalize[addr] = normalized
                    elif cmd[0] == "PUBKEY":
                        pubkey = cmd[2]
                        if pubkey.startswith(start):
                            addr = cmd[1]
                            exposed.add(addr)
    addr_state = {}
    for file in sys.argv[1:]:
        with open(file) as inpfil:
            for line in inpfil:
                if "\n" in line:
                    cmd=line.split(" ")
                    if cmd[0] in ("RECV", "SPEND") and cmd[1] in exposed:
                        event = cmd[0]
                        addr = cmd[1]
                        tim = cmd[2]
                        amount = float(cmd[3])
                        block = cmd[4]
                        txno = cmd[5]
                        if addr in normalize:
                            addr = normalize[addr]
                        old_amount, old_firstuse, old_lastrecv, old_lastspend = addr_state.get(addr,[0.0, None, None, None])
                        firstuse = old_firstuse or tim
                        if event == "RECV":
                            amount = old_amount + amount
                            lastrecv = tim
                            lastspend = old_lastspend
                        else:
                            amount = old_amount - amount
                            lastrecv = old_lastrecv
                            lastspend = tim
                        addr_state[addr] = [amount, firstuse, lastrecv, lastspend]
    for addr, state in addr_state.items():
        if state[0] >= 0.001:
            print("EXPOSED", addr, state[0], state[1], state[2], state[3])






        
