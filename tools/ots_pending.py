#!/usr/bin/env python3
"""Print the .ots files under a directory that do not yet carry a Bitcoin attestation (still pending)."""
import os, sys
BTC = bytes.fromhex("0588960d73d71901")
for root, _, files in os.walk(sys.argv[1]):
    for f in sorted(files):
        if f.endswith(".ots"):
            p = os.path.join(root, f)
            if BTC not in open(p, "rb").read():
                print(p)
