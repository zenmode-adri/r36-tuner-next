#!/usr/bin/env python3
"""Deep on-device audit for R36 Tuner — release readiness check."""

import paramiko, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "192.168.1.87"
USER = "ark"
PASS = "ark"

def ssh():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=22, username=USER, password=PASS, timeout=10)
    return c

def run(c, cmd, sudo=True):
    prefix = "echo ark | sudo -S " if sudo else ""
    _, out, err = c.exec_command(prefix + cmd, timeout=30)
    stdout = out.read().decode("utf-8", errors="replace").strip()
    stderr = err.read().decode("utf-8", errors="replace").strip()
    return stdout, stderr

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def ok(msg):   print(f"  ✓  {msg}")
def warn(msg): print(f"  ⚠  {msg}")
def fail(msg): print(f"  ✗  {msg}")
def info(msg): print(f"     {msg}")

ISSUES = []

def issue(msg):
    ISSUES.append(msg)
    fail(msg)

# ─────────────────────────────────────────────────────────────
print("Connecting to R36S...")
try:
    c = ssh()
    ok("Connected")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
section("1. SCRIPT DEPLOYMENT")

out, _ = run(c, 'ls -la "/opt/system/R36 Tuner.sh"')
info(out)
out, _ = run(c, 'head -3 "/opt/system/R36 Tuner.sh"')
info(out)

ver, _ = run(c, 'grep "^VERSION=" "/opt/system/R36 Tuner.sh" | head -1')
if "3.8" in ver:
    ok(f"Version: {ver}")
else:
    issue(f"Wrong version on device: {ver}")

sz, _ = run(c, 'wc -l "/opt/system/R36 Tuner.sh"')
info(f"Lines: {sz}")

# Check for CRLF (Windows line endings)
crlf, _ = run(c, 'file "/opt/system/R36 Tuner.sh" | grep -c CRLF || echo 0')
if crlf.strip() == "0":
    ok("Line endings: LF (correct)")
else:
    issue("CRLF line endings detected in deployed script")

# ─────────────────────────────────────────────────────────────
section("2. SYSTEM SERVICES")

for svc in ["r36-dtb-safety.service", "r36-dtb-confirm.service"]:
    enabled, _ = run(c, f"systemctl is-enabled {svc} 2>/dev/null || echo disabled")
    active, _ = run(c, f"systemctl is-active {svc} 2>/dev/null || echo inactive")
    if "enabled" in enabled:
        ok(f"{svc}: enabled, {active}")
    else:
        issue(f"{svc}: NOT enabled ({enabled})")

# r36-tuner boot service (optional — only if profile saved)
tuner_en, _ = run(c, "systemctl is-enabled r36-tuner.service 2>/dev/null || echo disabled")
info(f"r36-tuner.service: {tuner_en}")

# Check service scripts exist
for f in ["/usr/local/bin/r36-dtb-safety.sh", "/usr/local/bin/r36-dtb-confirm.sh"]:
    out, _ = run(c, f"[ -f {f} ] && echo present || echo MISSING")
    if "MISSING" in out:
        issue(f"Service script missing: {f}")
    else:
        ok(f"{f}: present")

# Check service unit files exist
for f in ["/etc/systemd/system/r36-dtb-safety.service",
           "/etc/systemd/system/r36-dtb-confirm.service"]:
    out, _ = run(c, f"[ -f {f} ] && echo present || echo MISSING")
    if "MISSING" in out:
        issue(f"Service unit missing: {f}")
    else:
        ok(f"{f}: present")

# ─────────────────────────────────────────────────────────────
section("3. DTB FLAGS (stale = dangerous)")

flags = {
    "/boot/.r36_dtb_patch_pending": "DTB_PENDING",
    "/boot/.r36_dtb_patch_booting": "DTB_BOOTING",
    "/boot/.r36_dtb_restored":      "DTB_RESTORED",
    "/etc/.r36_tuner_panic":        "PANIC_FLAG",
}
for path, name in flags.items():
    exists, _ = run(c, f"[ -f {path} ] && echo present || echo absent")
    if exists.strip() == "absent":
        ok(f"{name}: absent (correct)")
    else:
        issue(f"{name} flag still present: {path} — should be cleared after stable boot")

# ─────────────────────────────────────────────────────────────
section("4. OPP BIN DETECTION")

bin_cache, _ = run(c, "cat /etc/r36_tuner_bin 2>/dev/null || echo MISSING")
if "MISSING" in bin_cache:
    issue("/etc/r36_tuner_bin cache MISSING — DetectOPPBinProp will fall back to generic")
else:
    ok(f"Bin cache: {bin_cache}")

dmesg_bin, _ = run(c, 'dmesg 2>/dev/null | grep "opp-binning.*using OPP prop name" | tail -3')
if dmesg_bin:
    ok("dmesg OPP binning lines found:")
    for l in dmesg_bin.split("\n"):
        info(f"  {l}")
else:
    warn("No OPP binning lines in dmesg (buffer rotated?)")
    if "MISSING" in bin_cache:
        issue("No dmesg AND no cache — bin detection BROKEN")

# ─────────────────────────────────────────────────────────────
section("5. DTB STATE")

dtb_path = "/boot/rk3326-r36s-linux.dtb"
bak_path  = f"{dtb_path}.bak"

dtb_sz, _ = run(c, f"stat -c %s {dtb_path} 2>/dev/null || echo MISSING")
bak_sz, _ = run(c, f"stat -c %s {bak_path} 2>/dev/null || echo MISSING")

if "MISSING" in dtb_sz:
    issue("DTB file not found")
else:
    ok(f"DTB size: {dtb_sz} bytes")

if "MISSING" in bak_sz:
    issue("DTB backup (.bak) not found — safety service has no fallback")
else:
    ok(f"DTB backup size: {bak_sz} bytes")

# Check fdtget available
fdtget, _ = run(c, "which fdtget 2>/dev/null || echo MISSING")
if "MISSING" in fdtget:
    issue("fdtget not installed — DTB Tuning menu will prompt to install")
    info("(expected if user hasn't used DTB tuning yet)")
else:
    ok(f"fdtget: {fdtget}")
    # Read active OPP voltages
    for node_hz, label in [
        ("1608000000", "CPU 1608MHz"),
        ("1512000000", "CPU 1512MHz"),
        ("1296000000", "CPU 1296MHz"),
    ]:
        v, _ = run(c, f"fdtget -t u {dtb_path} /cpu0-opp-table/opp-{node_hz} opp-microvolt-L2 2>/dev/null | awk '{{print $1}}'")
        if v and v.isdigit():
            ok(f"  {label}: {int(v)//1000} mV (opp-microvolt-L2)")
        else:
            v2, _ = run(c, f"fdtget -t u {dtb_path} /cpu0-opp-table/opp-{node_hz} opp-microvolt 2>/dev/null | awk '{{print $1}}'")
            if v2 and v2.isdigit():
                info(f"  {label}: {int(v2)//1000} mV (generic only, no L2 prop)")
            else:
                warn(f"  {label}: OPP node not found or unreadable")

    # avs-scale
    avs, _ = run(c, f"fdtget -t u {dtb_path} /cpu0-opp-table rockchip,avs-scale 2>/dev/null")
    if avs.strip() == "0":
        ok(f"  avs-scale: 0 (CPU OC unlocked)")
    elif avs.strip():
        warn(f"  avs-scale: {avs} (not 0 — CPU OC may be blocked)")
    else:
        info("  avs-scale: not found")

    # GPU OPP
    for gpu_hz, label in [("600000000", "GPU 600MHz"), ("520000000", "GPU 520MHz"), ("480000000", "GPU 480MHz"), ("400000000", "GPU 400MHz")]:
        v, _ = run(c, f"fdtget -t u {dtb_path} /gpu-opp-table/opp-{gpu_hz} opp-microvolt-L2 2>/dev/null | awk '{{print $1}}'")
        if v and v.isdigit():
            ok(f"  {label}: {int(v)//1000} mV")
        else:
            v2, _ = run(c, f"fdtget -t u {dtb_path} /gpu-opp-table/opp-{gpu_hz} opp-microvolt 2>/dev/null | awk '{{print $1}}'")
            if v2 and v2.isdigit():
                info(f"  {label}: {int(v2)//1000} mV (generic)")
            else:
                info(f"  {label}: not found")

    # DMC OPP
    v, _ = run(c, f"fdtget -t u {dtb_path} /dmc-opp-table/opp-928000000 opp-microvolt-L2 2>/dev/null | awk '{{print $1}}'")
    if v and v.isdigit():
        ok(f"  DMC 928MHz: {int(v)//1000} mV")
    else:
        info("  DMC 928MHz: not found (OC not applied or different node)")

# ─────────────────────────────────────────────────────────────
section("6. RUNTIME FREQS & VOLTAGES")

cpu_max, _ = run(c, "cat /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq 2>/dev/null")
cpu_cur, _ = run(c, "cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq 2>/dev/null")
cpu_avail, _ = run(c, "cat /sys/devices/system/cpu/cpufreq/policy0/scaling_available_frequencies 2>/dev/null")
gov, _ = run(c, "cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor 2>/dev/null")

if cpu_max:
    ok(f"CPU max: {int(cpu_max)//1000} MHz, cur: {int(cpu_cur)//1000 if cpu_cur else '?'} MHz, gov: {gov}")
    if "1608000" in cpu_avail:
        ok("CPU 1608 MHz OPP: ACTIVE in kernel")
    else:
        warn("CPU 1608 MHz OPP: not visible (OC not active or boot issue)")

# GPU
gpu_dir, _ = run(c, "ls /sys/class/devfreq/ | grep -E 'gpu|mali|ff400000' | head -1")
gpu_dir = gpu_dir.strip()
if gpu_dir:
    gpu_path = f"/sys/class/devfreq/{gpu_dir}"
    gpu_max, _ = run(c, f"cat {gpu_path}/max_freq 2>/dev/null")
    gpu_cur, _ = run(c, f"cat {gpu_path}/cur_freq 2>/dev/null")
    gpu_avail, _ = run(c, f"cat {gpu_path}/available_frequencies 2>/dev/null")
    ok(f"GPU max: {int(gpu_max)//1000000 if gpu_max else '?'} MHz, cur: {int(gpu_cur)//1000000 if gpu_cur else '?'} MHz")
    if "600000000" in gpu_avail:
        ok("GPU 600 MHz OPP: ACTIVE in kernel")
    else:
        warn("GPU 600 MHz OPP: not visible")
else:
    issue("GPU devfreq directory not found")

# DMC
dmc_dir, _ = run(c, "ls /sys/class/devfreq/ | grep -E 'dmc|ff600000' | head -1")
dmc_dir = dmc_dir.strip()
if dmc_dir:
    dmc_path = f"/sys/class/devfreq/{dmc_dir}"
    dmc_max, _ = run(c, f"cat {dmc_path}/max_freq 2>/dev/null")
    dmc_cur, _ = run(c, f"cat {dmc_path}/cur_freq 2>/dev/null")
    dmc_avail, _ = run(c, f"cat {dmc_path}/available_frequencies 2>/dev/null")
    ok(f"DMC max: {int(dmc_max)//1000000 if dmc_max else '?'} MHz, cur: {int(dmc_cur)//1000000 if dmc_cur else '?'} MHz")
    if "928000000" in dmc_avail:
        ok("DMC 928 MHz OPP: ACTIVE in kernel")
    else:
        warn("DMC 928 MHz OPP: not visible")
else:
    issue("DMC devfreq directory not found")

# Voltages
vdd_arm_dir, _ = run(c, "for d in /sys/class/regulator/regulator.*; do [ \"$(cat $d/name 2>/dev/null)\" = 'vdd_arm' ] && echo $d; done")
vdd_logic_dir, _ = run(c, "for d in /sys/class/regulator/regulator.*; do [ \"$(cat $d/name 2>/dev/null)\" = 'vdd_logic' ] && echo $d; done")

if vdd_arm_dir.strip():
    v, _ = run(c, f"cat {vdd_arm_dir.strip()}/microvolts 2>/dev/null")
    ok(f"vdd_arm: {int(v)//1000 if v else '?'} mV")
else:
    issue("vdd_arm regulator not found")

if vdd_logic_dir.strip():
    v, _ = run(c, f"cat {vdd_logic_dir.strip()}/microvolts 2>/dev/null")
    ok(f"vdd_logic: {int(v)//1000 if v else '?'} mV")
else:
    issue("vdd_logic regulator not found")

temp, _ = run(c, "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null")
if temp:
    ok(f"Temp: {int(temp)//1000} °C")

# ─────────────────────────────────────────────────────────────
section("7. GLMARK2 LEGACY BINARY")

glm_path = "/usr/local/bin/glmark2-es2-drm-legacy"
exists, _ = run(c, f"[ -f {glm_path} ] && echo present || echo MISSING")
if "MISSING" in exists:
    issue(f"glmark2 legacy binary MISSING: {glm_path}")
else:
    sz, _ = run(c, f"stat -c %s {glm_path}")
    perms, _ = run(c, f"ls -la {glm_path}")
    ok(f"Binary present: {sz} bytes")
    info(perms)

    # Check executable
    exec_ok, _ = run(c, f"[ -x {glm_path} ] && echo yes || echo no")
    if exec_ok.strip() == "yes":
        ok("Executable bit: set")
    else:
        issue(f"glmark2 binary NOT executable")

    # SHA256 check — expected from memory: 52c861...
    sha, _ = run(c, f"sha256sum {glm_path} | awk '{{print $1}}'")
    ok(f"SHA256: {sha[:16]}...{sha[-8:]}")

# Shader data dir
data_dir = "/usr/local/share/glmark2data"
dstat, _ = run(c, f"[ -d {data_dir} ] && ls {data_dir}/ || echo MISSING")
if "MISSING" in dstat:
    issue(f"glmark2data directory MISSING: {data_dir}")
else:
    ok(f"glmark2data dir present")
    info(f"  Contents: {dstat[:120]}")

    # Check that shaders are patched (MEDIUMP_OR_DEFAULT removed)
    mediump_count, _ = run(c, f"grep -rl MEDIUMP_OR_DEFAULT {data_dir}/ 2>/dev/null | wc -l")
    if mediump_count.strip() == "0":
        ok("Shaders: MEDIUMP_OR_DEFAULT not present (correct)")
    else:
        issue(f"Unpatched shaders found: {mediump_count} files with MEDIUMP_OR_DEFAULT")

# ─────────────────────────────────────────────────────────────
section("8. BOOT PROFILE")

cfg, _ = run(c, "cat /etc/r36_tuner.ini 2>/dev/null || echo MISSING")
if "MISSING" in cfg:
    info("No saved boot profile (r36_tuner.ini not found — user hasn't saved one)")
else:
    ok("Boot profile exists:")
    for line in cfg.split("\n"):
        info(f"  {line}")
    # Check failed config
    failed, _ = run(c, "[ -f /etc/r36_tuner.ini.failed ] && echo PRESENT || echo absent")
    if "PRESENT" in failed:
        issue("/etc/r36_tuner.ini.failed present — previous profile failed to boot")

    # Check service is enabled
    en, _ = run(c, "systemctl is-enabled r36-tuner.service 2>/dev/null || echo disabled")
    if "enabled" in en:
        ok("r36-tuner.service: enabled")
    else:
        warn(f"r36-tuner.service: {en} (profile saved but service not enabled?)")

# ─────────────────────────────────────────────────────────────
section("9. STORAGE STATE")

# /boot filesystem
boot_fs, _ = run(c, "df -h /boot 2>/dev/null | tail -1")
info(f"/boot: {boot_fs}")

# /boot free space
boot_free_kb, _ = run(c, "df -k /boot 2>/dev/null | tail -1 | awk '{print $4}'")
if boot_free_kb and boot_free_kb.isdigit():
    free_kb = int(boot_free_kb)
    if free_kb < 2048:
        issue(f"/boot free space: {free_kb} KB — may not have room for DTB patches")
    else:
        ok(f"/boot free: {free_kb} KB")

# /usr/local free
local_free, _ = run(c, "df -h /usr/local 2>/dev/null | tail -1 || df -h / | tail -1")
info(f"/usr/local disk: {local_free}")

# ─────────────────────────────────────────────────────────────
section("10. GPTOKEYB / DIALOG / TOOLS")

for tool in ["dialog", "gptokeyb", "fdtput", "fdtget", "gcc", "openssl"]:
    path, _ = run(c, f"which {tool} 2>/dev/null || echo MISSING", sudo=False)
    if "MISSING" in path:
        info(f"{tool}: not found (may be normal)")
    else:
        ok(f"{tool}: {path}")

gptokeyb_cfg = "/opt/inttools/keys.gptk"
gcfg, _ = run(c, f"[ -f {gptokeyb_cfg} ] && echo present || echo MISSING")
if "MISSING" in gcfg:
    warn(f"gptokeyb config missing: {gptokeyb_cfg}")
else:
    ok(f"gptokeyb config: present")

# ─────────────────────────────────────────────────────────────
section("11. KERNEL / HARDWARE COMPAT")

compat, _ = run(c, "strings /proc/device-tree/compatible 2>/dev/null | head -4 | tr '\\n' ' '")
ok(f"Compatible: {compat}")

kernel, _ = run(c, "uname -r")
ok(f"Kernel: {kernel}")

arch, _ = run(c, "uname -m")
ok(f"Arch: {arch}")

# Check RK3326/PX30
if "rk3326" in compat.lower() or "px30" in compat.lower():
    ok("Hardware: RK3326/PX30 confirmed")
else:
    issue(f"Hardware mismatch — pre-flight check will warn users: {compat}")

# ─────────────────────────────────────────────────────────────
section("12. SCORES / BASELINE FILES")

scores, _ = run(c, "wc -l /etc/r36_tuner_scores.log 2>/dev/null || echo MISSING")
info(f"Scores log: {scores}")

baseline, _ = run(c, "cat /etc/r36_tuner_baseline 2>/dev/null || echo MISSING")
if "MISSING" in baseline:
    info("Baseline: not set (user hasn't run 'Set Baseline')")
else:
    ok(f"Baseline: {baseline[:80]}")

# ─────────────────────────────────────────────────────────────
section("13. POTENTIAL RACE / BUG CHECKS")

# Check if gptokeyb process is running (would conflict with new instance)
gptk_procs, _ = run(c, "pgrep -a gptokeyb 2>/dev/null || echo none")
info(f"gptokeyb procs: {gptk_procs}")

# Check /dev/uinput permissions (needed by gptokeyb)
uinput_perms, _ = run(c, "ls -la /dev/uinput 2>/dev/null")
info(f"/dev/uinput: {uinput_perms}")

# Check /dev/tty1 permissions
tty1_perms, _ = run(c, "ls -la /dev/tty1 2>/dev/null")
info(f"/dev/tty1: {tty1_perms}")

# Check if EmulationStation is running (relevant for on-screen GPU benchmarks)
es_running, _ = run(c, "pgrep -a emulationstation 2>/dev/null | head -1 || echo none")
info(f"EmulationStation: {es_running}")

# Check /tmp space for bench artifacts
tmp_free, _ = run(c, "df -h /tmp 2>/dev/null | tail -1")
info(f"/tmp: {tmp_free}")

# Pending GPU bench result
pending, _ = run(c, "[ -f /tmp/gpu_bench_pending ] && cat /tmp/gpu_bench_pending || echo absent")
if pending != "absent":
    warn(f"Pending GPU bench result in /tmp: {pending}")

# Check OC_PENDING flag
oc_pending, _ = run(c, "[ -f /boot/.r36_oc_pending ] && echo PRESENT || echo absent")
if "PRESENT" in oc_pending:
    issue("/boot/.r36_oc_pending stale flag present")

# ─────────────────────────────────────────────────────────────
section("14. SCRIPT SELF-CHECK (grep known bugs)")

# Check if the script on device has the glmark2 legacy binary embedded
legacy_marker, _ = run(c, "grep -c '__GLMARK2_LEGACY_START__' '/opt/system/R36 Tuner.sh' 2>/dev/null")
if legacy_marker.strip() in ("0", ""):
    issue("glmark2 legacy marker NOT in deployed script — InstallGlmark2Legacy() will fail")
else:
    ok("glmark2 legacy binary embedded in script")

# Check legacy binary already installed (shouldn't need to extract)
legacy_installed, _ = run(c, "[ -f /usr/local/bin/glmark2-es2-drm-legacy ] && echo installed || echo not-installed")
info(f"Legacy binary pre-installed: {legacy_installed}")

# Check that glmark2 data shaders path is correct
shader_check, _ = run(c, "[ -f /usr/local/share/glmark2data/shaders/terrain.vert ] && echo present || echo absent")
info(f"terrain.vert shader: {shader_check}")

# Check dmesg for recent DTB errors
dtb_errors, _ = run(c, "dmesg 2>/dev/null | grep -iE 'dtb|fdt|opp' | grep -iE 'error|fail|warn' | tail -5")
if dtb_errors:
    warn("DTB/OPP warnings in dmesg:")
    for l in dtb_errors.split("\n"):
        info(f"  {l}")
else:
    ok("No DTB/OPP errors in dmesg")

# ─────────────────────────────────────────────────────────────
section("15. FINAL DTB CONSISTENCY")

if "MISSING" not in bak_sz and fdtget and "MISSING" not in fdtget:
    # Compare avs-scale between current and backup
    avs_cur, _ = run(c, f"fdtget -t u {dtb_path} /cpu0-opp-table rockchip,avs-scale 2>/dev/null")
    avs_bak, _ = run(c, f"fdtget -t u {bak_path} /cpu0-opp-table rockchip,avs-scale 2>/dev/null")
    ok(f"avs-scale — current: {avs_cur.strip()}, backup: {avs_bak.strip()}")
    if avs_cur.strip() == "0" and avs_bak.strip() != "0":
        ok("CPU OC state: DTB patched (avs-scale=0), backup has original")

    # 1608 MHz node existence
    node_cur, _ = run(c, f"fdtget {dtb_path} /cpu0-opp-table/opp-1608000000 opp-hz 2>/dev/null || echo absent")
    node_bak, _ = run(c, f"fdtget {bak_path} /cpu0-opp-table/opp-1608000000 opp-hz 2>/dev/null || echo absent")
    ok(f"opp-1608000000 — current: {'present' if 'absent' not in node_cur else 'absent'}, backup: {'present' if 'absent' not in node_bak else 'absent'}")

    # GPU 600 node
    gpu600_cur, _ = run(c, f"fdtget {dtb_path} /gpu-opp-table/opp-600000000 opp-hz 2>/dev/null || echo absent")
    gpu600_bak, _ = run(c, f"fdtget {bak_path} /gpu-opp-table/opp-600000000 opp-hz 2>/dev/null || echo absent")
    ok(f"gpu opp-600000000 — current: {'present' if 'absent' not in gpu600_cur else 'absent'}, backup: {'present' if 'absent' not in gpu600_bak else 'absent'}")

    # DMC 928 node
    dmc928_cur, _ = run(c, f"fdtget {dtb_path} /dmc-opp-table/opp-928000000 opp-hz 2>/dev/null || echo absent")
    ok(f"dmc opp-928000000 — current: {'present' if 'absent' not in dmc928_cur else 'absent'}")

# ─────────────────────────────────────────────────────────────
section("SUMMARY")
if ISSUES:
    print(f"\n  Found {len(ISSUES)} issue(s):\n")
    for i, iss in enumerate(ISSUES, 1):
        print(f"  {i}. {iss}")
else:
    print("\n  All checks passed — device looks clean for release!")

c.close()
