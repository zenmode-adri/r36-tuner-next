#!/usr/bin/env python3
"""push_to_r36.py — quick deploy of R36 Tuner.sh to multiple locations."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from r36_ssh import connect

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOCAL = os.path.join(ROOT, "r36-tuner", "R36 Tuner.sh")
REMOTE_TMP = "/tmp/R36Tuner_update.sh"


def main():
    if not os.path.exists(LOCAL):
        print(f"ERROR: {LOCAL} not found")
        sys.exit(1)

    with connect() as r36:
        r36.put(LOCAL, REMOTE_TMP, sudo=False)
        out, err, code = r36.run_sudo(
            f"cp {REMOTE_TMP} \"/opt/system/R36 Tuner.sh\" && "
            f"cp {REMOTE_TMP} \"/usr/local/bin/R36 Tuner.sh\" && "
            f"chmod +x \"/opt/system/R36 Tuner.sh\" \"/usr/local/bin/R36 Tuner.sh\" && "
            f"rm -f {REMOTE_TMP} && echo done"
        )
        print(out)
        if code != 0:
            print("ERR:", err)
            sys.exit(1)


if __name__ == "__main__":
    main()
