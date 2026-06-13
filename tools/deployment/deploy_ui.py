#!/usr/bin/env python3
"""deploy_ui.py — compile and deploy the SDL2 Tuner UI to the R36S."""

import base64
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

import paramiko

sys.path.insert(0, os.path.dirname(__file__))
from r36_ssh import connect

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TUNER_SH = os.path.join(ROOT, "r36-tuner", "R36 Tuner.sh")
SRC_C = os.path.join(ROOT, "src", "ui", "tuner_ui", "main.c")
LAUNCHER_SRC = os.path.join(ROOT, "src", "ui", "tuner_ui", "R36 Tuner Next.sh")
LOCAL_BIN = os.path.join(ROOT, "bin", "tuner_ui")
REMOTE_BIN = "/opt/system/tuner_ui"
REMOTE_LAUNCHER = "/opt/system/R36 Tuner Next.sh"
REMOTE_TMP = "/tmp/tuner_ui_deploy"
LOCAL_GLMARK2_LEGACY = os.path.join(ROOT, "bin", "glmark2-es2-drm-legacy")
REMOTE_GLMARK2_LEGACY = "/usr/local/bin/glmark2-es2-drm-legacy"


def log(msg):
    print(f"[deploy_ui] {msg}")


def run_local(cmd, check=True):
    log(f"local: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0 and check:
        log(f"local command failed: {result.stderr.strip()}")
        sys.exit(1)
    return result


def find_cross_compiler():
    cc = shutil.which("aarch64-linux-gnu-gcc")
    if cc:
        return cc
    try:
        result = subprocess.run(
            ["wsl", "bash", "-c", "which aarch64-linux-gnu-gcc"],
            capture_output=True, text=True, check=False, encoding="utf-8"
        )
        if result.returncode == 0:
            path = result.stdout.strip()
            if path:
                return path
    except FileNotFoundError:
        pass
    return None


def compile_local():
    os.makedirs(os.path.dirname(LOCAL_BIN), exist_ok=True)
    cc = find_cross_compiler()
    if not cc:
        return False
    try:
        result = run_local(
            [cc, "-O2", "-o", LOCAL_BIN, SRC_C, "-lSDL2", "-lSDL2_ttf"],
            check=False,
        )
    except (FileNotFoundError, OSError) as e:
        log(f"cross-compiler found but cannot execute ({e}), will try remote")
        return False
    if result.returncode != 0 or not os.path.exists(LOCAL_BIN):
        log("cross-compile failed, will try remote")
        return False
    log(f"cross-compiled: {LOCAL_BIN} ({os.path.getsize(LOCAL_BIN)} bytes)")
    return True


def compile_remote(r36):
    log("cross-compiler not found; compiling on R36S...")
    r36.client.exec_command(f"mkdir -p {REMOTE_TMP}")
    sftp = r36.client.open_sftp()
    sftp.put(SRC_C, f"{REMOTE_TMP}/main.c")
    sftp.close()

    out, err, code = r36.run(
        f"gcc -O2 -o {REMOTE_TMP}/tuner_ui {REMOTE_TMP}/main.c -lSDL2 -lSDL2_ttf",
        timeout=120,
    )
    if out:
        log(f"remote compile stdout: {out}")
    if err:
        log(f"remote compile stderr: {err}")
    if code != 0:
        log("remote compilation failed")
        sys.exit(1)

    sftp = r36.client.open_sftp()
    sftp.get(f"{REMOTE_TMP}/tuner_ui", LOCAL_BIN)
    sftp.close()
    log(f"remote compiled binary pulled: {LOCAL_BIN}")


def verify(r36, path):
    out, _, _ = r36.run(f'ls -l "{path}"')
    if not out or "No such" in out:
        log(f"verification FAILED: {path}")
        return False
    log(f"verified: {out}")
    return True


def stop_ui(r36):
    """Kill any running tuner_ui process so the binary can be overwritten."""
    out, err, code = r36.run("pgrep -x tuner_ui || true")
    pids = [p for p in (out or "").strip().splitlines() if p.strip().isdigit()]
    if not pids:
        return
    log(f"stopping running tuner_ui processes: {', '.join(pids)}")
    r36.run_sudo("kill -TERM $(pgrep -x tuner_ui) 2>/dev/null || true")
    import time
    for _ in range(20):
        out, _, _ = r36.run("pgrep -x tuner_ui || true")
        if not out.strip():
            return
        time.sleep(0.25)
    r36.run_sudo("kill -KILL $(pgrep -x tuner_ui) 2>/dev/null || true")
    time.sleep(0.25)


def setup_glmark2_data(r36):
    """Set up /usr/local/share/glmark2data/ on the device from the .deb embedded in R36 Tuner.sh.

    Uses dpkg -x (no postinst scripts) to avoid the ldconfig/start-stop-daemon PATH
    issue that breaks dpkg -i on dArkOSRE.  Idempotent: skips if shaders already present.
    """
    out, _, _ = r36.run("test -d /usr/local/share/glmark2data/shaders && echo OK || echo MISSING")
    if out.strip() == "OK":
        log("glmark2 data already set up, skipping")
        return

    log("extracting glmark2-data.deb from R36 Tuner.sh...")
    with open(TUNER_SH, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()

    b64_lines = []
    inside = False
    for line in lines:
        if line == "# __GLMARK2_DATA_START__":
            inside = True
            continue
        if line == "# __GLMARK2_DATA_END__":
            break
        if inside:
            b64_lines.append(line)

    if not b64_lines:
        log("WARNING: glmark2-data section not found in R36 Tuner.sh — skipping data setup")
        return

    data_deb = base64.b64decode("".join(b64_lines))
    log(f"extracted {len(data_deb):,} bytes")

    with tempfile.NamedTemporaryFile(suffix=".deb", delete=False) as tmp:
        tmp.write(data_deb)
        tmp_local = tmp.name

    try:
        log("uploading glmark2-data.deb (~6 MB)...")
        sftp = r36.client.open_sftp()
        sftp.put(tmp_local, "/tmp/glmark2-data.deb")
        sftp.close()
    finally:
        os.unlink(tmp_local)

    log("setting up /usr/local/share/glmark2data/...")
    # Use double-quotes in sed to avoid single-quote conflicts with shlex.quote.
    cmd = (
        "dpkg -x /tmp/glmark2-data.deb /tmp/glmark2data-x && "
        "mkdir -p /usr/local/share/glmark2data/shaders && "
        "cp -rn /tmp/glmark2data-x/usr/share/glmark2/models /usr/local/share/glmark2data/ && "
        "cp -rn /tmp/glmark2data-x/usr/share/glmark2/textures /usr/local/share/glmark2data/ && "
        "cp /tmp/glmark2data-x/usr/share/glmark2/shaders/* /usr/local/share/glmark2data/shaders/ && "
        'sed -i "s/MEDIUMP_OR_DEFAULT/mediump/g; s/HIGHP_OR_DEFAULT/highp/g" '
        "    /usr/local/share/glmark2data/shaders/* && "
        "rm -rf /tmp/glmark2data-x /tmp/glmark2-data.deb"
    )
    # Wrap in bash -c so the full chain runs as root, not just the first token.
    _, err, code = r36.run_sudo(f"bash -c {shlex.quote(cmd)}", timeout=60)
    if code != 0:
        log(f"WARNING: glmark2 data setup failed: {err}")
    else:
        log("glmark2 data ready at /usr/local/share/glmark2data/")


def main():
    if not os.path.exists(SRC_C):
        log(f"source not found: {SRC_C}")
        sys.exit(1)
    if not os.path.exists(LAUNCHER_SRC):
        log(f"launcher not found: {LAUNCHER_SRC}")
        sys.exit(1)
    has_legacy = os.path.exists(LOCAL_GLMARK2_LEGACY)
    if not has_legacy:
        log(f"legacy glmark2 binary not found ({LOCAL_GLMARK2_LEGACY}) — skipping legacy upload")

    log("connecting to R36S...")
    with connect() as r36:
        if not compile_local():
            compile_remote(r36)

        stop_ui(r36)

        log("uploading tuner_ui binary...")
        r36.put(LOCAL_BIN, REMOTE_BIN, mode="755")

        log("uploading launcher script...")
        r36.put(LAUNCHER_SRC, REMOTE_LAUNCHER, mode="755")

        if has_legacy:
            log("uploading legacy glmark2 binary...")
            r36.put(LOCAL_GLMARK2_LEGACY, REMOTE_GLMARK2_LEGACY, mode="755")
            setup_glmark2_data(r36)

        ok = verify(r36, REMOTE_BIN) and verify(r36, REMOTE_LAUNCHER)

        r36.run(f"rm -rf {REMOTE_TMP}")

    if ok:
        log("deploy complete.")
        print(f'\nLaunch on the R36S with:\n  "{REMOTE_LAUNCHER}"')
    else:
        log("deploy finished with verification errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
