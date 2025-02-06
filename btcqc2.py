#!/usr/bin/python3
import sys
import os

processed = set()
if os.path.exists("runs.var") and (len(sys.argv)<2 or sys.argv[1] != "init"):
    with open("runs.var") as runsfil:
        for run in runsfil:
            if run.endswith("\n"):
                run=run[:-1]
                processed.add(run)
    run_ids = [""]
elif len(sys.argv) < 2 or sys.argv[1] != "init":
    print("ABORT: No runs.var file found and not run with 'init' argument")
    sys.exit(1)
else:
    run_ids = ["020-021",
               "022-023",
               "024-025",
               "026-027",
               "028-029",
               "02a-02b",
               "02c-02d",
               "02e-02f",
               "030-031",
               "032-033",
               "034-035",
               "036-037",
               "038-039",
               "03a-03b",
               "03c-03d",
               "03e-03f"]

for run_id in run_ids:
    print(run_id)
    if run_id:
        prefixes = run_id.split("-")
    else:
        prefixes = []
    for blockrun in sorted([int(f) 
                          for f in os.listdir(".")
                          if f.isdecimal() 
                          and f not in processed 
                          and os.path.isdir(os.path.join(".",f))]):
        rundir = os.path.join(".", str(blockrun))
        exposed = set()
        normalize = {}
        print(run_id, "Looking for newly exposed addresses in", rundir)
        with open(os.path.join(rundir, "pubkey.log")) as tfil:
          for line in tfil:
              if "\n" in line:
                  cmd = line.split(" ")
                  if cmd[0] in ("ALIAS", "MULTI"):
                      if not run_id or cmd[3][:3] in prefixes:
                          exposed.add(cmd[1])
                          exposed.add(cmd[2])
                          if cmd[1].startswith("1"):
                              normalize[cmd[1]] = cmd[2] 
                  elif cmd[0] == "PUBKEY":
                      if not run_id or cmd[2][:3] in prefixes:
                          exposed.add(cmd[1])
        print(run_id,"Found", len(exposed), "addresses, including normalized ones in", rundir)
        addr_state = {}
        for prevrun in [str(y) for y in sorted([int(x) for x in processed])]:
            for efilepath in [os.path.join(prevrun, f) for f in os.listdir(prevrun) if f.startswith("exposed")]:
                with open(efilepath) as efile:
                    for line in efile:
                        if "\n" in line:
                            cmd = line[:-1].split(" ")
                            if cmd[0] == "EXPOSED" and cmd[1] in exposed:
                                addr_state[cmd[1]] = cmd[2:]
        print(run_id, "Found existing exposed data on", len(addr_state), "addresses")
        rescan = exposed - set(addr_state.keys())
        print(run_id, "Rescanning", len(rescan),"addresses out of", len(exposed))
        for prevrun in [str(y) for y in sorted([int(x) for x in processed])] + [str(blockrun)]:
            with open(os.path.join(".", prevrun,"stripped.log")) as stripped:
                for line in stripped:
                    if line.endswith("\n"):
                        line = line[:-1]
                        cmd = line.split(" ")
                        if cmd[0].isdecimal() and len(cmd[0]) == 1:
                            cmd = cmd[1:]
                        if cmd[0] in ("RECV", "SPEND") and cmd[1] in rescan:
                            event = cmd[0]
                            addr = cmd[1]
                            tim = cmd[2]
                            amount = float(cmd[3])
                            block = int(cmd[4])
                            txno = int(cmd[5])
                            if addr in normalize:
                                addr = normalize[addr]
                            old_amount, old_firstuse, old_lastrecv, old_lastspend = addr_state.get(addr, [0.0, None, None, None])

                            firstuse = old_firstuse or tim
                            if event == "RECV":
                                amount = float(old_amount) + amount
                                lastrecv = tim
                                lastspend = old_lastspend
                            else:
                                amount = float(old_amount) - amount
                                lastrecv = old_lastrecv
                                lastspend = tim
                            addr_state[addr] = [amount, firstuse, lastrecv, lastspend]
        print("-", run_id, "Found", len(addr_state), "exposed addresses")
        cnt = 0
        with open(os.path.join(rundir ,"exposed" + run_id + ".log"), "w") as outp:
            for addr, state in addr_state.items():
                if float(state[0]) >= 0.001:
                    print("EXPOSED", addr, state[0], state[1], state[2], state[3], file=outp)
                    cnt += 1
        print("   +",run_id,  cnt, "contain at least 0.001 bitcoin")

processed.add(str(blockrun))
with open("runs.var", "w") as runs_out:
    for run in [str(x) for x in sorted([int(y) for y in processed])]:
        runs_out.write(run)
        runs_out.write("\n")
