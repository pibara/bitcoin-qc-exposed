#!/usr/bin/python3
import os
import json
import math
import dateutil.parser as parser

def meta_from_stripped(rdir):
    spath = os.path.join(rdir,"stripped.log")
    rval = {}
    rval["start"] = None
    rval["end"] = None
    rval["volume"] = 0.0
    with open(spath) as sfil:
        for line in sfil:
            if line.startswith("RECV "):
                if line.endswith("\n"):
                    line =  line[:-1]
                parts = line.split(" ")
                if rval["start"] is None:
                    rval["start"] = parts[2]
                rval["end"] = parts[2]
                rval["volume"] += float(parts[3])
    return rval

def meta_from_trigger(rdir, startiso):


    start = int((parser.parse(startiso.split("T")[0] + "T00:00:00").timestamp()/86400) + 0.01)
    bykey = {}
    tpath = os.path.join(rdir, "trigger.log")
    with open(tpath) as tfil:
        for line in tfil:
            if line.startswith("TRIGGER "):
                if line.endswith("\n"):
                    line = line[:-1]
                cmd,key,ttim,amount,block, tx, src, balance, extime, rtim, stim = line.split(" ")
                if key not in bykey:
                    psiso = stim
                    if stim == "None":
                        psiso = extime
                    age = start - int((parser.parse(psiso.split("T")[0] + "T00:00:00").timestamp()/86400) + 0.01)
                    bykey[key] = [0.0, extime.split("-")[0], 0, age]
                bykey[key][0] += float(amount)
                bykey[key][2] += 1
    rval = {}
    rval["volume"] = 0.0
    rval["years"] = {}
    rval["top"] = {}
    for year in range(2009, 2026):
        rval["years"][str(year)] = {}
        rval["years"][str(year)]["TOTAL"] = 0.0
    rval["years"]["TOTAL"] = {}
    rval["years"]["TOTAL"]["TOTAL"] = 0.0
    for key,val in bykey.items():
        if val[0] >= 0.001:
            rval["top"][key] = {}
            rval["top"][key]["volume"] = val[0]
            rval["top"][key]["exposed"] = val[1]
            rval["top"][key]["count"] = val[2]
            rval["top"][key]["dormant"] = val[3]
        amm = str(math.pow(10,math.floor(math.log10(val[0]))))
        if amm not in rval["years"][val[1]]:
            rval["years"][val[1]][amm] = 0.0
        if amm not in rval["years"]["TOTAL"]:
            rval["years"]["TOTAL"][amm] = 0.0
        rval["years"][val[1]][amm] += val[0]
        rval["years"]["TOTAL"][amm] += val[0]
        rval["years"][val[1]]["TOTAL"] += val[0]
        rval["years"]["TOTAL"]["TOTAL"] += val[0]
        rval["volume"] += val[0]
    return rval

def meta_to_md(rdir, meta):
    reportpath = os.path.join(rdir, "report.MD")
    with open(reportpath, "w") as report:
        percentage = str(int(1000*meta["triggers"]["volume"]/meta["volume"])/10)+"%"
        texp = meta["triggers"]["volume"]
        print("# Bitcoin QC Kanarie run from", meta["start"], "till", meta["end"], file=report)
        print(file=report)
        print("This is a report of recent transactions comming from reused addresses.", file=report)
        print("The goal of this report is to act as a kanarie service for future quantum computing heists.", file=report)
        print("At current levels of key-reuse, these reports seem useless.", file=report)
        print("While awareness is high, it seems not high enough for this kanarie posta to be usefull yet", file=report)
        print(file=report)
        print("## Overview", file=report)
        print("A percentage of", percentage,"of thr total volume came from previously exposed addresses.", file=report)
        print(file=report)
        print("Of these exposed addresses, the following table gives an overview. The columns show the order of magnitude of volume transfered per address", file=report)
        print("The rows show the year the given adresses first had their public keys exposed. The cells show the percentage of exposed volume per combination.", file=report)
        print(file=report)
        header = "|   | TOTAL |"
        heade2 = "| --- | --- |"
        for floorlog in range(5, -4, -1):
            header += " " + str(math.pow(10,floorlog)) + " |"
            heade2 += " --- |"
        print(header, file=report)
        print(heade2, file=report)
        for year in range(2009, 2027):
            if year == 2026:
                year = "TOTAL"
            yearmeta = meta["triggers"]["years"][str(year)]
            yeartotal = str(int(yearmeta["TOTAL"] * 10000 / texp)/100)+"%"
            line = "| " + str(year) + " | " +  yeartotal + " |"
            for floorlog in range(5, -4, -1):
                val = str(int(yearmeta.get(str(math.pow(10,floorlog)), 0.0)*10000/texp)/100) + "%"
                line += " " + val + " |"
            print(line, file=report)
        print(file=report)
        print("## Top addresses", file=report)
        tvol = 0.0
        print("| volume part | exposure year | count | dormant for |  address |", file=report)
        print("| --- | --- | --- | --- | --- |", file=report)
        for key, val in meta["triggers"]["top"].items():
            volume = int(val["volume"]*10000/texp)/100
            tvol += volume
            exposed = val["exposed"]
            cnt = val["count"] 
            dormant = val["dormant"]
            if volume >= 1:
                print("|", str(volume) +"% |", exposed, "|", cnt, "|", dormant, "days | [" + key + "](https://www.blockchain.com/explorer/addresses/btc/" + key + ") |", file=report)

        print(file=report)
        print("Total:", int(tvol*100)/100, "% of exposed address volume.", file=report)
        print("## Long dormant addresses", file=report)
        print("The below is a sample of relatively high volume exposed adresses that were dormant for mor than a whole year.", file=report) 
        print("| volume part | exposure year | count | dormant for |  address |", file=report)
        print("| --- | --- | --- | --- | --- |", file=report)
        for key, val in meta["triggers"]["top"].items():
            volume = int(val["volume"]*10000/texp)/100
            exposed = val["exposed"]
            cnt = val["count"]
            dormant = val["dormant"]
            if dormant > 365 and volume >= 0.01:
                print("|", str(volume) +"% |", exposed, "|", cnt, "|", dormant, "days | [" + key + "](https://www.blockchain.com/explorer/addresses/btc/" + key + ") |", file=report)
        print("# Code", file=report)
        print("This post was generated with [these scripts](https://github.com/pibara/bitcoin-qc-exposed). Merge requests are highly welcomed.", file=report)

def make_report(rdir, rfilpath):
    print("Making report for", rdir)
    meta1 = meta_from_stripped(rdir)
    meta1["triggers"] = meta_from_trigger(rdir, meta1["start"])
    meta_to_md(rdir, meta1)

with open("runs.var") as runs:
    count = 0
    for line in runs:
        if count > 0:
            rundir = os.path.join(".", str(int(line)))
            reportfil = os.path.join(rundir, "report.MD")
            if not os.path.exists(reportfil):
                make_report(rundir, reportfil)
        count += 1

