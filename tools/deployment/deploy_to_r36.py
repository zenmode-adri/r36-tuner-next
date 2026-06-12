#!/usr/bin/env python3
"""deploy_to_r36.py — deploy r36-tuner/R36 Tuner Next.sh to the R36S."""

import os
import sys
import io

sys.path.insert(0, os.path.dirname(__file__))
from r36_ssh import connect

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(ROOT, "r36-tuner", "R36 Tuner Next.sh")
REMOTE = "/tmp/R36Tuner_update.sh"
DEST = "/opt/system/R36 Tuner Next.sh"
CHUNK = 524288  # 512 KB


def main():
    if not os.path.exists(SCRIPT):
        print(f"ERROR: {SCRIPT} not found")
        sys.exit(1)

    with connect() as r36:
        data = open(SCRIPT, "rb").read()
        total = len(data)
        print(f"Transferring {total:,} bytes in {(total + CHUNK - 1) // CHUNK} chunks...")

        for i, offset in enumerate(range(0, total, CHUNK)):
            chunk = data[offset : offset + CHUNK]
            cmd = f"cat > {REMOTE}" if i == 0 else f"cat >> {REMOTE}"
            stdin, stdout, stderr = r36.client.exec_command(cmd)
            stdin.write(chunk)
            stdin.channel.shutdown_write()
            stdout.read()
            pct = min(100, (offset + len(chunk)) * 100 // total)
            print(f"  chunk {i+1}: {pct}%", flush=True)

        print("Transfer done. Installing...")
        r36.run_sudo(f"cp {REMOTE} \"{DEST}\"")
        r36.run_sudo(f"chmod +x \"{DEST}\"")
        r36.run_sudo(f"rm -f {REMOTE}")

        out, _, _ = r36.run(f"ls -l \"{DEST}\"")
        print("Installed:", out)


if __name__ == "__main__":
    main()
