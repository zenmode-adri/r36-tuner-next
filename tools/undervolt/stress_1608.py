#!/usr/bin/env python3
"""
Stress test CPU @ 1608 MHz / 1200 mV
- Compila programa C agresivo en device (divide, FP, branches, todos los cores)
- Fuerza 1608 MHz performance
- 5 min test con monitoreo de temp cada 5s
- Reporta STABLE / CRASHED al final
"""

import paramiko
import time
import sys

HOST = '192.168.1.87'
USER = 'ark'
PASS = 'ark'

STRESS_C = r"""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <sys/wait.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>

static volatile int running = 1;
static void handler(int s) { running = 0; }

static double stress_loop(void) {
    unsigned int x = 0xdeadbeef;
    double fp = 1.0;
    long long sum = 0;
    int branch = 0;

    while (running) {
        /* entero: multiply + divide (lento en ARM) */
        x = x * 1664525u + 1013904223u;
        sum += (long long)(x % 999983);

        /* FP: sqrt + trig */
        fp = sqrt(fp + 1.0001) * 0.9999;
        fp += sin(fp) * cos(fp);

        /* branch mispredict pattern */
        branch = (x & 0xF) > 8 ? branch + 1 : branch - 1;
        if (branch > 1000) branch = 0;
        if (branch < -1000) branch = 0;
    }
    return fp + sum + branch;
}

int main(int argc, char **argv) {
    int ncores = 4;
    int duration = 300;
    if (argc > 1) duration = atoi(argv[1]);

    signal(SIGTERM, handler);
    signal(SIGALRM, handler);
    alarm(duration);

    /* fork ncores workers */
    for (int i = 1; i < ncores; i++) {
        if (fork() == 0) {
            double r = stress_loop();
            fprintf(stderr, "worker %d done: %.2f\n", i, r);
            exit(0);
        }
    }

    /* parent also runs */
    double r = stress_loop();
    fprintf(stderr, "worker 0 done: %.2f\n", r);

    /* wait all */
    int status;
    while (wait(&status) > 0);

    printf("STRESS_DONE\n");
    return 0;
}
"""

def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=22, username=USER, password=PASS, timeout=10)
    return c

def sudo(c, cmd, timeout=30):
    _, out, err = c.exec_command(f"echo {PASS} | sudo -S bash -c '{cmd}'", timeout=timeout)
    o = out.read().decode('utf-8', errors='replace').strip()
    e = err.read().decode('utf-8', errors='replace').strip()
    return o, e

def run(c, cmd, timeout=30):
    o, _ = sudo(c, cmd, timeout)
    return o

def get_temp(c):
    t = run(c, "cat /sys/class/thermal/thermal_zone0/temp", timeout=5)
    try:
        return int(t) // 1000
    except:
        return -1

def get_freq(c):
    f = run(c, "cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq", timeout=5)
    try:
        return int(f) // 1000
    except:
        return -1

def get_volt(c):
    v = run(c, "cat /sys/class/regulator/regulator.3/microvolts", timeout=5)
    try:
        return int(v) // 1000
    except:
        return -1

print("=" * 60)
print("CPU STRESS TEST — 1608 MHz / 1200 mV")
print("=" * 60)

# 1. Conectar
print("\n[1] Conectando SSH...", end=' ', flush=True)
try:
    c = connect()
    print("OK")
except Exception as e:
    print(f"FALLO: {e}")
    sys.exit(1)

# 2. Verificar DTB
print("[2] Verificando DTB 1608 MHz L2 voltage...", end=' ', flush=True)
dtb_volt = run(c, "fdtget -t u /boot/rk3326-r36s-linux.dtb /cpu0-opp-table/opp-1608000000 opp-microvolt-L2")
if dtb_volt:
    vals = dtb_volt.split()
    mv = int(vals[0]) // 1000 if vals else -1
    print(f"{mv} mV")
    if mv != 1200:
        print(f"  AVISO: esperado 1200 mV, encontrado {mv} mV")
else:
    print("ERROR: no se pudo leer DTB")

# 3. Verificar 1608 disponible
avail = run(c, "cat /sys/devices/system/cpu/cpufreq/policy0/scaling_available_frequencies")
if '1608000' in avail:
    print("[2b] 1608 MHz disponible en kernel: OK")
else:
    print("[2b] ERROR: 1608 MHz NO en scaling_available_frequencies")
    print(f"     Disponibles: {avail}")
    c.close()
    sys.exit(1)

# 4. Forzar 1608 MHz performance
print("[3] Forzando 1608 MHz (performance)...", end=' ', flush=True)
run(c, "echo 1008000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq")
run(c, "echo 1608000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq")
run(c, "echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor")
run(c, "echo 1608000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq")
time.sleep(0.5)
freq = get_freq(c)
volt = get_volt(c)
print(f"freq={freq} MHz  vdd_arm={volt} mV")

if freq != 1608:
    print(f"  AVISO: freq esperada 1608, actual {freq}")

# 5. Subir y compilar stress C en device
print("[4] Subiendo y compilando stress C...", end=' ', flush=True)
import io
sftp = c.open_sftp()
sftp.putfo(io.BytesIO(STRESS_C.encode()), '/tmp/cpustress.c')
sftp.close()

compile_out, compile_err = sudo(c, "gcc -O2 -o /tmp/cpustress /tmp/cpustress.c -lm && echo COMPILED", timeout=30)
if "COMPILED" in compile_out:
    print("OK")
else:
    print(f"FALLO\n  stdout: {compile_out}\n  stderr: {compile_err}")
    # Restaurar governor antes de salir
    run(c, "echo schedutil > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor")
    c.close()
    sys.exit(1)

# 6. Lanzar stress (5 min = 300s) en background, redirigir output
print("[5] Lanzando stress 4 cores x 300s...")
print("    Monitoreando cada 5s — Ctrl+C para abortar\n")

# Lanzar en background con nohup
_, out, err = c.exec_command(
    f"echo {PASS} | sudo -S bash -c "
    f"'nohup /tmp/cpustress 300 > /tmp/cpustress.out 2>&1 & echo PID:$!'",
    timeout=10
)
pid_line = out.read().decode().strip()
pid = None
for line in pid_line.split('\n'):
    if line.startswith('PID:'):
        pid = line.split(':')[1].strip()
        break
print(f"    PID del stress: {pid}")

# 7. Monitoreo de temperatura
start = time.time()
duration = 300
temps = []
freqs_log = []
crashed = False

print(f"\n  {'Tiempo':>6}  {'Freq':>7}  {'VddArm':>8}  {'Temp':>6}  {'Estado'}")
print(f"  {'-'*6}  {'-'*7}  {'-'*8}  {'-'*6}  {'-'*10}")

try:
    while True:
        elapsed = time.time() - start
        if elapsed > duration + 10:
            break

        try:
            t = get_temp(c)
            f = get_freq(c)
            v = get_volt(c)
        except Exception as ex:
            print(f"\n  !! CONEXION PERDIDA @ {elapsed:.0f}s: {ex}")
            crashed = True
            break

        temps.append(t)
        freqs_log.append(f)

        # Verificar si el proceso sigue vivo
        if pid:
            alive = run(c, f"kill -0 {pid} 2>/dev/null && echo alive || echo dead", timeout=5)
            estado = "running" if "alive" in alive else "done"
        else:
            estado = "running"

        marker = ""
        if t >= 80:
            marker = " !! HOT"
        elif t >= 70:
            marker = " ! warm"

        if f < 1600 and elapsed > 5:
            marker += " FREQ_DROP"

        print(f"  {elapsed:>5.0f}s  {f:>5} MHz  {v:>5} mV  {t:>4}°C  {estado}{marker}", flush=True)

        # Verificar si terminó
        if estado == "done" and elapsed > 10:
            # Verificar output
            out_data = run(c, "cat /tmp/cpustress.out", timeout=5)
            if "STRESS_DONE" in out_data:
                print(f"\n  Stress completado tras {elapsed:.0f}s")
            break

        if t >= 85:
            print(f"\n  !! ABORTANDO: temperatura {t}°C >= 85°C")
            if pid:
                run(c, f"kill {pid}", timeout=5)
            break

        time.sleep(5)

except KeyboardInterrupt:
    print("\n  Interrumpido por usuario")
    if pid:
        try:
            run(c, f"kill {pid}", timeout=5)
        except:
            pass

# 8. Resultado
print("\n" + "=" * 60)

if crashed:
    print("RESULTADO: CRASHED — conexion SSH perdida durante stress")
    print("           -> 1200 mV INESTABLE a 1608 MHz bajo carga real")
elif temps:
    max_t = max(temps)
    avg_t = sum(temps) / len(temps)
    min_f = min(freqs_log) if freqs_log else 0
    print(f"RESULTADO: {'STABLE' if not crashed else 'FAILED'}")
    print(f"  Temperatura: avg={avg_t:.1f}°C  peak={max_t}°C")
    print(f"  Frecuencia mínima registrada: {min_f} MHz")
    if min_f < 1600:
        print("  AVISO: hubo throttling (freq < 1600 MHz)")
    if max_t < 75 and min_f >= 1600:
        print("  -> 1200 mV ESTABLE. Podemos intentar bajar más (1187.5 mV)")
    elif max_t < 80:
        print("  -> 1200 mV ESTABLE con temp aceptable")
    else:
        print("  -> 1200 mV ESTABLE pero temp alta — no bajar más voltaje")

# 9. Restaurar governor
print("\n[6] Restaurando governor schedutil...", end=' ', flush=True)
try:
    run(c, "echo 1008000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq")
    run(c, "echo schedutil > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor")
    print("OK")
except:
    print("(error)")

c.close()
