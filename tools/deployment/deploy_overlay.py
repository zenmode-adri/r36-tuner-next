#!/usr/bin/env python3
"""deploy_overlay.py — deploy the LD_PRELOAD overlay shared library."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from r36_ssh import connect

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SO_LOCAL = os.path.join(ROOT, "bin", "libr36overlay_new.so")
SO_DEST = "/usr/local/lib/libr36overlay.so"


def main():
    if not os.path.exists(SO_LOCAL):
        print(f"ERROR: {SO_LOCAL} not found")
        sys.exit(1)

    with connect() as r36:
        r36.put(SO_LOCAL, SO_DEST, mode="755")
        out, _, _ = r36.run(f"ls -lh {SO_DEST}")
        print("Installed:", out)

        # Quick load test.
        _, so, se = r36.client.exec_command(f"LD_PRELOAD={SO_DEST} ls / 2>&1")
        err_d = se.read().decode("utf-8", errors="replace").strip()
        so.read()
        print("Load test stderr:", repr(err_d[:80]))


if __name__ == "__main__":
    main()
