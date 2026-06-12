"""
Sweep autónomo: undervolt SOLO del OPP 1608 MHz (CPU OC).
1512 MHz @ 1175 mV ya estable — no se toca.
Test: C LCG benchmark 10s forzado a 1608 MHz + temp.
Criterio de fallo: crash SSH / score <5% del reference / temp >85C.
Al acabar, restaura al último voltaje estable.
"""

import paramiko, time, sys

HOST = '192.168.1.87'
DTB  = '/boot/rk3326-r36s-linux.dtb'
NODE = '/cpu0-opp-table/opp-1608000000'

START_UV      = 1337500   # primer paso (1350000 ya OK)
STEP_UV       = 12500
STOP_UV       = 1100000   # floor conservador (1512 ya estable a 1175 mV)
KNOWN_GOOD_UV = 1350000
BENCH_SECS    = 10

C_SRC = r"""
#include <stdio.h>
#include <time.h>
#include <stdint.h>
int main(){
    uint32_t x=12345;
    long long ops=0;
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    do{
        x=x*1664525+1013904223;
        x=x*1664525+1013904223;
        x=x*1664525+1013904223;
        x=x*1664525+1013904223;
        x=x*1664525+1013904223;
        x=x*1664525+1013904223;
        x=x*1664525+1013904223;
        x=x*1664525+1013904223;
        ops+=8;
        clock_gettime(CLOCK_MONOTONIC,&t1);
    }while((t1.tv_sec-t0.tv_sec)*1000+(t1.tv_nsec-t0.tv_nsec)/1000000 < BENCH_MS);
    printf("%lld\n",ops/1000/BENCH_SECS);
    return (int)x&0;
}
""".replace("BENCH_MS", str(BENCH_SECS * 1000)).replace("BENCH_SECS", str(BENCH_SECS))


def connect(retries=40, delay=5):
    print("  Esperando SSH", end='', flush=True)
    for _ in range(retries):
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(HOST, port=22, username='ark', password='ark', timeout=5)
            print(" OK", flush=True)
            return c
        except:
            print(".", end='', flush=True)
            time.sleep(delay)
    print(" TIMEOUT", flush=True)
    return None

def sudo(c, cmd, timeout=60):
    _, o, _ = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'")
    o.channel.settimeout(timeout)
    try:
        return o.read().decode('utf-8', errors='replace').strip()
    except:
        return ''

def compile_bench(c):
    sudo(c, f"cat > /tmp/cpubench.c << 'ENDC'\n{C_SRC}\nENDC")
    sudo(c, "gcc -O2 -o /tmp/r36_cpubench /tmp/cpubench.c")
    ok = sudo(c, "test -f /tmp/r36_cpubench && echo OK || echo FAIL")
    print(f"  bench compilado: {ok}", flush=True)

def run_bench(c):
    # Forzar 1608 MHz
    sudo(c, "echo 1608000 > /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq")
    sudo(c, "echo 1608000 > /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq")
    sudo(c, "echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    time.sleep(1)
    freq = sudo(c, "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
    vdd  = sudo(c, "cat /sys/class/regulator/regulator.3/microvolts")  # vdd_arm
    try:
        score = sudo(c, "/tmp/r36_cpubench", timeout=BENCH_SECS + 15)
    except:
        score = '0'
    temp  = sudo(c, "cat /sys/class/thermal/thermal_zone0/temp")
    # Restaurar
    sudo(c, "echo 1008000 > /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq")
    sudo(c, "echo 1608000 > /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq")
    sudo(c, "echo schedutil > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    mops  = int(score) if score.isdigit() else 0
    temp_c = int(temp) // 1000 if temp.isdigit() else -1
    vdd_mv = int(vdd) / 1000 if vdd.isdigit() else -1
    freq_mhz = int(freq) // 1000 if freq.isdigit() else -1
    return mops, vdd_mv, temp_c, freq_mhz

def patch(c, uv):
    vals = f'{uv} {uv} {uv}'
    sudo(c, f'fdtput -t u {DTB} "{NODE}" opp-microvolt-L2 {vals}')
    sudo(c, f'fdtput -t u {DTB} "{NODE}" opp-microvolt     {vals}')
    sudo(c, 'touch /boot/.r36_dtb_pending')
    v = sudo(c, f'fdtget -t u {DTB} "{NODE}" opp-microvolt-L2')
    print(f"  DTB L2 -> [{v}]", flush=True)

def reboot_device(c):
    shell = c.invoke_shell()
    time.sleep(0.5)
    shell.send("echo ark | sudo -S reboot\n")
    time.sleep(3)
    try: c.close()
    except: pass
    time.sleep(35)

def restore(uv):
    print(f"\n  Restaurando a {uv/1000} mV...", flush=True)
    c2 = connect()
    if c2 is None: return
    patch(c2, uv)
    reboot_device(c2)
    c3 = connect()
    if c3:
        print(f"  Restaurado OK", flush=True)
        try: c3.close()
        except: pass


# ── MAIN ─────────────────────────────────────────────────

c = connect()
if c is None:
    print("Sin conexión"); sys.exit(1)

cur = sudo(c, f'fdtget -t u {DTB} "{NODE}" opp-microvolt-L2')
print(f"opp-1608000000 L2 actual: [{cur}]")
compile_bench(c)

# Referencia a 1350 mV (sin reboot, ya estamos ahí)
print("\nReferencia @ 1350 mV (sin patch)...")
ref_score, ref_vdd, ref_temp, ref_freq = run_bench(c)
print(f"  Ref: {ref_score} Mops | {ref_freq} MHz | {ref_vdd} mV | {ref_temp}C")

voltages = list(range(START_UV, STOP_UV - 1, -STEP_UV))
print(f"\nSweep: {[v/1000 for v in voltages]} mV")
print(f"\n{'mV':>10} | {'Mops':>6} | {'vs ref':>7} | {'vdd_arm':>8} | {'Temp':>5} | Estado")
print("-" * 60)
print(f"{'1350.0':>10} | {ref_score:>6} | {'ref':>7} | {ref_vdd:>8} | {ref_temp:>4}C | STABLE (baseline)")

results    = {}
last_good  = KNOWN_GOOD_UV
crashed    = False

for uv in voltages:
    mv = uv / 1000
    print(f"\n>>> Patch {mv} mV...", flush=True)
    patch(c, uv)
    reboot_device(c)

    c = connect()
    if c is None:
        print(f"{'':>10}   NO-BOOT (panic durante boot)")
        results[mv] = 'NO-BOOT'
        crashed = True
        break

    compile_bench(c)
    mops, vdd_mv, temp_c, freq_mhz = run_bench(c)

    if mops == 0:
        estado = 'CRASH'
        crashed = True
        print(f"{mv:>10} | {'0':>6} | {'---':>7} | {vdd_mv:>8} | {temp_c:>4}C | {estado}")
        results[mv] = f'CRASH (0 Mops)'
        break
    elif temp_c > 85:
        estado = 'TEMP!'
        print(f"{mv:>10} | {mops:>6} | {mops/ref_score*100:>6.1f}% | {vdd_mv:>8} | {temp_c:>4}C | {estado}")
        results[mv] = f'{mops} Mops | {temp_c}C | OVERHEAT'
        last_good = uv
    elif mops < ref_score * 0.94:
        estado = 'LOW'
        pct = mops / ref_score * 100
        print(f"{mv:>10} | {mops:>6} | {pct:>6.1f}% | {vdd_mv:>8} | {temp_c:>4}C | {estado} (sospechoso)")
        results[mv] = f'{mops} Mops | {temp_c}C | LOW'
        last_good = uv
    else:
        estado = 'STABLE'
        pct = mops / ref_score * 100
        last_good = uv
        print(f"{mv:>10} | {mops:>6} | {pct:>6.1f}% | {vdd_mv:>8} | {temp_c:>4}C | {estado}")
        results[mv] = f'{mops} Mops | {temp_c}C'

try: c.close()
except: pass

if crashed:
    restore(last_good)

# Tabla final
print(f"\n{'='*60}")
print("RESUMEN — CPU OC 1608 MHz voltage sweep")
print(f"{'='*60}")
print(f"{'mV':>10} | {'Mops':>6} | {'vs ref':>7} | Estado")
print("-" * 50)
print(f"{'1350.0':>10} | {ref_score:>6} | {'ref':>7} | STABLE (baseline)")
for mv, r in results.items():
    mops_str = r.split(' Mops')[0] if 'Mops' in r else '---'
    try:
        pct = f"{int(mops_str)/ref_score*100:.1f}%"
    except:
        pct = '---'
    print(f"{mv:>10} | {mops_str:>6} | {pct:>7} | {r}")
print(f"{'='*60}")
if last_good != KNOWN_GOOD_UV:
    print(f"Floor estable: {last_good/1000} mV (-{(KNOWN_GOOD_UV-last_good)/1000:.1f} mV vs stock OC)")
