import os
import paramiko, time, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

HOST = '192.168.1.87'
USER = 'ark'
PASS = 'ark'

DTB       = '/boot/rk3326-r36s-linux.dtb'
DTB_BAK   = '/boot/rk3326-r36s-linux.dtb.bak'
DTB_SAVED = '/boot/rk3326-r36s-linux.dtb.oc_patched'

GLMARK_BIN  = '/tmp/glmark2-es2-drm-legacy'
GLMARK_DATA = '/tmp/glmark2data'
GLMARK      = f'{GLMARK_BIN} --off-screen --size 320x240 --data-path {GLMARK_DATA}'
GLMARK_LOCAL = os.path.join(ROOT, 'bin', 'glmark2-es2-drm-legacy')

# ── SSH helpers ────────────────────────────────────────────────────────────────

def connect(retries=36, delay=5):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for i in range(retries):
        try:
            c.connect(HOST, port=22, username=USER, password=PASS, timeout=10)
            print("  SSH connected.")
            return c
        except Exception as e:
            print(f"  Waiting for SSH... ({i+1}/{retries}) [{e}]")
            time.sleep(delay)
    print("ERROR: could not reconnect after reboot.")
    sys.exit(1)

def run(c, cmd, timeout=900):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    return out.read().decode(), err.read().decode()

def sudo(c, cmd, timeout=30):
    o, e = run(c, f'echo {PASS} | sudo -S bash -c "{cmd}"', timeout)
    return o, e

# ── Temperature ────────────────────────────────────────────────────────────────

def get_temp(c):
    o, _ = run(c, 'cat /sys/class/thermal/thermal_zone0/temp', 5)
    try: return int(o.strip()) // 1000
    except: return -1

def start_temp_log(c):
    run(c, 'rm -f /tmp/bench_temps.log', 5)
    run(c, "nohup sh -c 'while true; do cat /sys/class/thermal/thermal_zone0/temp; sleep 1; done' > /tmp/bench_temps.log 2>&1 &", 5)
    time.sleep(1)

def stop_temp_log(c):
    run(c, "pkill -f 'while true; do cat /sys/class/thermal' || true", 5)
    time.sleep(0.5)
    o, _ = run(c, 'cat /tmp/bench_temps.log', 10)
    vals = []
    for line in o.strip().split('\n'):
        line = line.strip()
        if line.isdigit():
            vals.append(int(line) // 1000)
    return vals

# ── Freq control ───────────────────────────────────────────────────────────────

def set_freqs(c, gpu_hz, cpu_khz, dmc_hz):
    label = f"GPU {gpu_hz//1000000} MHz  CPU {cpu_khz//1000} MHz  RAM {dmc_hz//1000000} MHz"
    print(f"  Setting freqs: {label}")
    sudo(c, f"echo performance > /sys/class/devfreq/ff400000.gpu/governor")
    sudo(c, f"echo {gpu_hz} > /sys/class/devfreq/ff400000.gpu/max_freq")
    sudo(c, f"echo performance > /sys/class/devfreq/dmc/governor")
    sudo(c, f"echo {dmc_hz} > /sys/class/devfreq/dmc/max_freq")
    sudo(c, f"echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor")
    sudo(c, f"echo 1008000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq")
    sudo(c, f"echo {cpu_khz} > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq")
    time.sleep(2)
    gpu_cur, _ = run(c, 'cat /sys/class/devfreq/ff400000.gpu/cur_freq', 5)
    dmc_cur, _ = run(c, 'cat /sys/class/devfreq/dmc/cur_freq', 5)
    cpu_cur, _ = run(c, 'cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq', 5)
    print(f"  Actual:        GPU {gpu_cur.strip()} Hz  DMC {dmc_cur.strip()} Hz  CPU {cpu_cur.strip()} kHz")

def verify_voltage(c, label):
    varm, _  = run(c, 'cat /sys/class/regulator/regulator.3/microvolts', 5)
    vlogic, _ = run(c, 'cat /sys/class/regulator/regulator.2/microvolts', 5)
    try:
        arm_mv   = int(varm.strip())   // 1000
        logic_mv = int(vlogic.strip()) // 1000
    except:
        arm_mv = logic_mv = -1
    print(f"  Voltages ({label}):  vdd_arm={arm_mv} mV  vdd_logic={logic_mv} mV")

# ── DTB swap ───────────────────────────────────────────────────────────────────

def swap_dtb_to_stock(c):
    print("\n  Saving patched DTB...")
    sudo(c, f"cp {DTB} {DTB_SAVED}")
    print("  Copying .bak (stock) to active DTB...")
    sudo(c, f"cp {DTB_BAK} {DTB}")
    sudo(c, "sync && sync")
    time.sleep(1)

def restore_patched_dtb(c):
    print("\n  Restoring patched DTB...")
    sudo(c, f"cp {DTB_SAVED} {DTB}")
    sudo(c, "sync && sync")
    time.sleep(1)

def reboot_and_wait(c, label):
    print(f"  Rebooting for {label}...")
    try:
        shell = c.invoke_shell()
        time.sleep(0.5)
        shell.send("echo ark | sudo -S reboot\n")
        time.sleep(3)
    except: pass
    c.close()
    time.sleep(20)
    print("  Waiting for device...")
    return connect()

# ── Glmark2 benchmark ──────────────────────────────────────────────────────────

def parse_glmark(output):
    score_m = re.search(r'glmark2 Score:\s*(\d+)', output)
    score = int(score_m.group(1)) if score_m else 0
    scenes = re.findall(r'\[(.+?)\] (.+?): FPS: (\d+)', output)
    return score, scenes

def run_bench(c, label):
    print(f"\n{'='*60}")
    print(f"BENCH: {label}")
    print(f"{'='*60}")

    temp_initial = get_temp(c)
    print(f"  Temp inicial: {temp_initial}C")

    start_temp_log(c)
    t0 = time.time()
    print("  Running full glmark2 suite (eta ~8 min)...")

    _, stdout, stderr = c.exec_command(GLMARK, timeout=900)
    lines = []
    for line in iter(stdout.readline, ''):
        line = line.rstrip()
        lines.append(line)
        if 'FPS:' in line or 'Score:' in line or 'Error' in line.title():
            print(f"  {line}", flush=True)
    out = '\n'.join(lines)
    err = stderr.read().decode()

    elapsed = time.time() - t0
    temps = stop_temp_log(c)

    score, scenes = parse_glmark(out)

    if temps:
        t_max = max(temps)
        t_avg = sum(temps) // len(temps)
    else:
        t_max = t_avg = -1

    print(f"  Score:        {score}")
    print(f"  Temp inicial: {temp_initial}C  media: {t_avg}C  maxima: {t_max}C")
    print(f"  Duracion:     {elapsed:.0f}s")

    if scenes:
        print("  Escenas:")
        for name, params, fps in scenes:
            print(f"    [{name}] {params}: {fps} fps")

    if err.strip():
        print(f"  STDERR: {err[:400]}")

    return score, temp_initial, t_avg, t_max, scenes

# ── Main ───────────────────────────────────────────────────────────────────────

def setup_glmark2(c):
    print("  Transfiriendo glmark2-es2-drm-legacy (985KB)...")
    with open(GLMARK_LOCAL, 'rb') as f:
        data = f.read()
    stdin, _, _ = c.exec_command(f'cat > {GLMARK_BIN}', timeout=30)
    stdin.write(data)
    stdin.channel.shutdown_write()
    time.sleep(1)
    sudo(c, f'chmod +x {GLMARK_BIN}')
    print("  Binario OK.")

    print("  Preparando /tmp/glmark2data con shaders parcheados...")
    sudo(c, f'rm -rf {GLMARK_DATA}')
    sudo(c, f'mkdir -p {GLMARK_DATA}/shaders')
    sudo(c, f'ln -sf /usr/share/glmark2/models   {GLMARK_DATA}/models')
    sudo(c, f'ln -sf /usr/share/glmark2/textures  {GLMARK_DATA}/textures')
    sudo(c, f'cp /usr/share/glmark2/shaders/* {GLMARK_DATA}/shaders/')
    sudo(c, f"sed -i 's/MEDIUMP_OR_DEFAULT/mediump/g; s/HIGHP_OR_DEFAULT/highp/g' {GLMARK_DATA}/shaders/*")
    o, _ = run(c, f'grep -rl MEDIUMP_OR_DEFAULT {GLMARK_DATA}/shaders/ | wc -l', 5)
    print(f"  Shaders parcheados (macros restantes: {o.strip()}, debe ser 0).")

def stop_es(c):
    print("  Stopping EmulationStation...")
    run(c, 'echo ark | sudo -S bash -c "systemctl stop emulationstation; sleep 2; pkill -9 emulationstation || true; sleep 1"', 30)
    time.sleep(3)

def start_es(c):
    print("  Starting EmulationStation...")
    run(c, 'echo ark | sudo -S systemctl start emulationstation', 15)

def main():
    print("Conectando a R36S...")
    c = connect()

    # ── TEST 1: STOCK (DTB actual = .bak) ─────────────────────────────────────
    setup_glmark2(c)
    stop_es(c)
    verify_voltage(c, "STOCK DTB")
    set_freqs(c, gpu_hz=520000000, cpu_khz=1512000, dmc_hz=786000000)

    r_st = run_bench(c, "STOCK  (GPU 520 / CPU 1512 / RAM 786 — voltajes stock)")

    # Cooldown antes de reboot
    print("\n  Cooldown 45s...")
    time.sleep(45)

    # ── Swap a DTB OC y reboot ────────────────────────────────────────────────
    print("\n  Activando DTB OC parcheado...")
    sudo(c, f"cp {DTB_SAVED} {DTB}")
    sudo(c, "sync && sync")
    c = reboot_and_wait(c, "OC DTB")

    # ── TEST 2: OC ────────────────────────────────────────────────────────────
    setup_glmark2(c)
    stop_es(c)
    verify_voltage(c, "OC DTB")
    set_freqs(c, gpu_hz=600000000, cpu_khz=1608000, dmc_hz=928000000)

    r_oc = run_bench(c, "FULL OC  (GPU 600 / CPU 1608 / RAM 924 — voltajes undervolted)")

    # ── Fin — OC DTB queda activo, arrancamos ES ──────────────────────────────
    start_es(c)
    c.close()

    # ── Resultado final ────────────────────────────────────────────────────────
    score_oc,  ti_oc,  tavg_oc,  tmax_oc,  scenes_oc = r_oc
    score_st,  ti_st,  tavg_st,  tmax_st,  scenes_st = r_st

    print("\n" + "="*60)
    print("COMPARACION FINAL  (sin thermal pad)")
    print("="*60)
    fmt = "{:30s} {:>10} {:>10} {:>12}"
    print(fmt.format("",              "OC",      "STOCK",   "DELTA"))
    print(fmt.format("Score",         str(score_oc), str(score_st),
                     f"{score_oc-score_st:+d} ({(score_oc/max(score_st,1)-1)*100:+.1f}%)"))
    print(fmt.format("Temp inicial",  f"{ti_oc}C",  f"{ti_st}C",   f"{ti_oc-ti_st:+d}C"))
    print(fmt.format("Temp media",    f"{tavg_oc}C", f"{tavg_st}C", f"{tavg_oc-tavg_st:+d}C"))
    print(fmt.format("Temp maxima",   f"{tmax_oc}C", f"{tmax_st}C", f"{tmax_oc-tmax_st:+d}C"))

    if scenes_oc and scenes_st:
        print("\nEscenas (fps OC vs stock):")
        oc_map = {(n,p): int(f) for n,p,f in scenes_oc}
        st_map = {(n,p): int(f) for n,p,f in scenes_st}
        all_keys = sorted(set(list(oc_map) + list(st_map)), key=lambda x: x[0]+x[1])
        print(f"  {'Escena':42s} {'OC':>6} {'Stock':>6} {'Delta':>8}")
        for k in all_keys:
            fo = oc_map.get(k, 0)
            fs = st_map.get(k, 0)
            label = f"[{k[0]}] {k[1]}"[:42]
            print(f"  {label:42s} {fo:>6} {fs:>6} {fo-fs:>+8}")

    print("\nNota: OC usa voltajes undervolted del DTB parcheado.")
    print("      Stock usa voltajes originales del DTB backup (.bak).")

if __name__ == '__main__':
    main()
