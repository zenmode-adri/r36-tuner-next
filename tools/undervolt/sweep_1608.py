#!/usr/bin/env python3
"""
Sweep undervolt 1608 MHz: patch DTB + reboot + stress 60s por paso.
SSH persiste entre reboots (systemctl enable ssh).
"""

import paramiko
import time
import io
import sys

HOST = '192.168.1.87'
USER = 'ark'
PASS = 'ark'

START_MV   = 1187.5   # empezamos aquí (1200 ya confirmado estable)
STEP_MV    = 12.5
STOP_MV    = 1150
STRESS_SEC = 60
REBOOT_TIMEOUT = 120  # segundos esperando que vuelva SSH tras reboot

STRESS_C = r"""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <sys/wait.h>
#include <unistd.h>
#include <signal.h>

static volatile int running = 1;
static void handler(int s) { running = 0; }

static double stress_loop(void) {
    unsigned int x = 0xdeadbeef;
    double fp = 1.0;
    long long sum = 0;
    int branch = 0;
    while (running) {
        x = x * 1664525u + 1013904223u;
        sum += (long long)(x % 999983);
        fp = sqrt(fp + 1.0001) * 0.9999;
        fp += sin(fp) * cos(fp);
        branch = (x & 0xF) > 8 ? branch + 1 : branch - 1;
        if (branch > 1000) branch = 0;
        if (branch < -1000) branch = 0;
    }
    return fp + sum + branch;
}

int main(int argc, char **argv) {
    int duration = 60;
    if (argc > 1) duration = atoi(argv[1]);
    signal(SIGTERM, handler);
    signal(SIGALRM, handler);
    alarm(duration);
    for (int i = 1; i < 4; i++) {
        if (fork() == 0) { stress_loop(); exit(0); }
    }
    stress_loop();
    int status;
    while (wait(&status) > 0);
    printf("STRESS_DONE\n");
    return 0;
}
"""

def connect(timeout=10):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=22, username=USER, password=PASS, timeout=timeout)
    return c

def sudo(c, cmd, timeout=30):
    _, out, err = c.exec_command(f"echo {PASS} | sudo -S bash -c '{cmd}'", timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

def get_temp(c):
    try:
        return int(sudo(c, "cat /sys/class/thermal/thermal_zone0/temp", 5)) // 1000
    except: return -1

def get_freq(c):
    try:
        return int(sudo(c, "cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq", 5)) // 1000
    except: return -1

def get_volt_mv(c):
    try:
        return int(sudo(c, "cat /sys/class/regulator/regulator.3/microvolts", 5)) / 1000
    except: return -1

def reboot(c):
    shell = c.invoke_shell()
    time.sleep(0.5)
    shell.send(f"echo {PASS} | sudo -S reboot\n")
    time.sleep(3)
    try: c.close()
    except: pass

def wait_for_ssh(timeout=REBOOT_TIMEOUT):
    print(f"  Esperando SSH (max {timeout}s)...", end='', flush=True)
    start = time.time()
    while time.time() - start < timeout:
        try:
            c = connect(timeout=5)
            elapsed = time.time() - start
            print(f" reconectado en {elapsed:.0f}s", flush=True)
            return c
        except:
            print('.', end='', flush=True)
            time.sleep(5)
    print(" TIMEOUT", flush=True)
    return None

def setup_stress(c):
    sftp = c.open_sftp()
    sftp.putfo(io.BytesIO(STRESS_C.encode()), '/tmp/cpustress.c')
    sftp.close()
    r = sudo(c, "gcc -O2 -o /tmp/cpustress /tmp/cpustress.c -lm && echo OK", timeout=30)
    return "OK" in r

def force_1608(c):
    sudo(c, "echo 1008000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq")
    sudo(c, "echo 1608000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq")
    sudo(c, "echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor")
    sudo(c, "echo 1608000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq")
    time.sleep(0.5)

def run_stress(c, seconds):
    _, out, _ = c.exec_command(
        f"echo {PASS} | sudo -S bash -c "
        f"'nohup /tmp/cpustress {seconds} > /tmp/cpustress.out 2>&1 & echo PID:$!'",
        timeout=10
    )
    pid = None
    for line in out.read().decode().split('\n'):
        if line.startswith('PID:'):
            pid = line.split(':')[1].strip()

    start = time.time()
    temps = []
    while True:
        elapsed = time.time() - start
        try:
            t = get_temp(c)
            f = get_freq(c)
        except Exception as ex:
            print(f"    !! SSH caído @ {elapsed:.0f}s — CRASH", flush=True)
            return False, 999

        temps.append(t)
        print(f"    {elapsed:>4.0f}s  {f} MHz  {t}°C", flush=True)

        if t >= 85:
            print(f"    !! ABORT: {t}°C >= 85°C", flush=True)
            if pid:
                try: sudo(c, f"kill {pid}", 5)
                except: pass
            return False, t

        if elapsed >= seconds + 5:
            break
        time.sleep(5)

    return True, max(temps) if temps else 0

# ── MAIN ────────────────────────────────────────────────────────────────────

voltages = []
mv = START_MV
while mv >= STOP_MV - 0.1:
    voltages.append(mv)
    mv -= STEP_MV

total_steps = len(voltages)
print("=" * 55, flush=True)
print(f"SWEEP 1608 MHz: {START_MV} → {STOP_MV} mV  ({total_steps} pasos, {STRESS_SEC}s + reboot cada uno)", flush=True)
print(f"Tiempo estimado: ~{total_steps * 4} min", flush=True)
print("=" * 55, flush=True)

print("\nConectando...", end=' ', flush=True)
try:
    c = connect()
    print("OK", flush=True)
except Exception as e:
    print(f"FALLO: {e}", flush=True)
    sys.exit(1)

last_stable_mv = 1200.0
crashed_at = None

for i, mv in enumerate(voltages):
    uv = int(mv * 1000)
    print(f"\n[{i+1}/{total_steps}] ── {mv} mV ──────────────────────────", flush=True)

    # 1. Patch DTB
    print(f"  Parchando DTB → {mv} mV...", end=' ', flush=True)
    sudo(c, f"fdtput -t u /boot/rk3326-r36s-linux.dtb /cpu0-opp-table/opp-1608000000 opp-microvolt-L2 {uv} {uv} {uv}")
    print("OK", flush=True)

    # 2. Reboot
    print(f"  Rebooting...", flush=True)
    reboot(c)
    time.sleep(10)  # esperar que empiece el shutdown

    # 3. Esperar SSH
    c = wait_for_ssh()
    if c is None:
        print(f"  !! No volvió SSH — posible boot failure @ {mv} mV", flush=True)
        crashed_at = mv
        break

    # 4. Compilar stress
    print("  Compilando stress...", end=' ', flush=True)
    if not setup_stress(c):
        print("FALLO compilación", flush=True)
        break
    print("OK", flush=True)

    # 5. Forzar 1608 MHz y verificar voltaje real
    force_1608(c)
    real_mv = get_volt_mv(c)
    freq = get_freq(c)
    print(f"  freq={freq} MHz  vdd_arm={real_mv} mV (pedido {mv} mV)", flush=True)

    # 6. Stress
    print(f"  Stress {STRESS_SEC}s:", flush=True)
    stable, peak = run_stress(c, STRESS_SEC)

    if stable:
        print(f"  → STABLE  peak={peak}°C", flush=True)
        last_stable_mv = mv
    else:
        print(f"  → FAILED  peak={peak}°C", flush=True)
        crashed_at = mv
        break

# ── Resultado final ──────────────────────────────────────────────────────────
print(f"\n{'='*55}", flush=True)
print(f"LÍMITE ESTABLE: {last_stable_mv} mV", flush=True)
if crashed_at:
    print(f"FALLÓ EN:       {crashed_at} mV", flush=True)
else:
    print(f"(todos los pasos OK — podría ir más bajo)", flush=True)

# Asegurar que el DTB queda en el último voltaje estable
if c:
    try:
        uv_final = int(last_stable_mv * 1000)
        print(f"\nDejando DTB en {last_stable_mv} mV...", end=' ', flush=True)
        sudo(c, f"fdtput -t u /boot/rk3326-r36s-linux.dtb /cpu0-opp-table/opp-1608000000 opp-microvolt-L2 {uv_final} {uv_final} {uv_final}")
        print("OK — efectivo en próximo reboot", flush=True)
        sudo(c, "echo 1008000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq")
        sudo(c, "echo schedutil > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor")
        c.close()
    except:
        pass
