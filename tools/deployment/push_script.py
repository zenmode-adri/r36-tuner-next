#!/usr/bin/env python3
"""push_script.py — deploy R36 Tuner.sh with size verification."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from r36_ssh import connect

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOCAL = os.path.join(ROOT, "r36-tuner", "R36 Tuner.sh")
REMOTE_TMP = "/tmp/R36Tuner_update.sh"
REMOTE_FINAL = "/opt/system/R36 Tuner.sh"
CHUNK = 524288


def main():
    if not os.path.exists(LOCAL):
        print(f"ERROR: {LOCAL} not found")
        sys.exit(1)

    with open(LOCAL, "rb") as f:
        data = f.read()
    print(f"Transfiriendo {len(data) / 1024 / 1024:.1f} MB...")

    with connect() as r36:
        for i, off in enumerate(range(0, len(data), CHUNK)):
            cmd = f"cat > {REMOTE_TMP}" if i == 0 else f"cat >> {REMOTE_TMP}"
            stdin, stdout, _ = r36.client.exec_command(cmd)
            stdin.write(data[off : off + CHUNK])
            stdin.channel.shutdown_write()
            stdout.read()
            print(f"  chunk {i+1}/{(len(data) + CHUNK - 1) // CHUNK}")

        out, _, _ = r36.run(f"wc -c < {REMOTE_TMP}")
        remote_size = int(out.strip())
        print(f"Remoto: {remote_size} bytes, local: {len(data)} bytes")

        if remote_size != len(data):
            print("ERROR: tamaños no coinciden")
            sys.exit(1)

        out, err, code = r36.run_sudo(
            f"cp {REMOTE_TMP} \"{REMOTE_FINAL}\" && chmod +x \"{REMOTE_FINAL}\""
        )
        if code != 0:
            print("ERR:", err)
            sys.exit(1)
        print("Instalado en", REMOTE_FINAL)


if __name__ == "__main__":
    main()
