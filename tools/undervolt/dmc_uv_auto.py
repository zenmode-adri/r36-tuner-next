#!/usr/bin/env python3
"""
Auto-sweep DMC UV: patch -> reboot -> espera SSH -> stress -> siguiente paso.
Guarda historial completo de voltaje/MB/s/temp.
"""
import paramiko, time, sys, threading

HOST, USER, PASS = '192.168.1.87', 'ark', 'ark'
DTB = '/boot/rk3326-r36s-linux.dtb'
NODE = '/dmc-opp-table/opp-928000000'
BIN_PROP = 'opp-microvolt-L2'
DTB_PENDING = '/boot/.r36_dtb_pending'

STRESS_C = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#define BUF_MB 128
#define DURATION_S 30
int main(void) {
    size_t sz = BUF_MB * 1024 * 1024;
    char *a = malloc(sz); char *b = malloc(sz);
    if (!a || !b) { puts("malloc fail"); return 1; }
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long iters = 0; double elapsed = 0;
    while (elapsed < DURATION_S) {
        memset(a, (int)(iters & 0xff), sz);
        memcpy(b, a, sz);
        iters++;
        clock_gettime(CLOCK_MONOTONIC, &t1);
        elapsed = (t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)*1e-9;
    }
    double mb = iters*BUF_MB*2.0/elapsed;
    printf("STABLE: %.0f MB/s over %.1fs\n", mb, elapsed);
    free(a); free(b); return 0;
}
"""

def connect(timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(HOST, port=22, username=USER, password=PASS, timeout=5)
            return c
        except Exception:
            time.sleep(10)
    return None

def run(c, cmd, timeout=60):
    _, o, _ = c.exec_command(cmd, timeout=timeout)
    return o.read().decode('utf-8', errors='replace').strip()

def sudo(c, cmd, timeout=60):
    _, o, _ = c.exec_command('echo ark | sudo -S ' + cmd, timeout=timeout)
    return o.read().decode('utf-8', errors='replace').strip()

def write_file(c, path, data):
    if isinstance(data, str): data = data.encode()
    CHUNK = 524288
    for i, off in enumerate(range(0, len(data), CHUNK)):
        cmd = f'cat > {path}' if i == 0 else f'cat >> {path}'
        s, o, _ = c.exec_command(cmd)
        s.write(data[off:off+CHUNK]); s.channel.shutdown_write(); o.read()

def patch_and_reboot(c, volt_uv):
    cur = sudo(c, f'fdtget -t u {DTB} {NODE} {BIN_PROP} 2>/dev/null')
    print(f'  {int(cur)//1000} mV -> {volt_uv//1000}.{volt_uv%1000//100*100//100 if volt_uv%1000 else 0} mV')
    sudo(c, f'fdtput -t u {DTB} {NODE} {BIN_PROP} {volt_uv}')
    sudo(c, f'fdtput -t u {DTB} {NODE} opp-microvolt {volt_uv}')
    sudo(c, 'sync')
    verify = sudo(c, f'fdtget -t u {DTB} {NODE} {BIN_PROP} 2>/dev/null')
    if str(volt_uv) not in verify:
        print('  ERROR: patch no aplicado'); return False
    sudo(c, f'touch {DTB_PENDING}')
    shell = c.invoke_shell()
    time.sleep(0.5)
    shell.send('echo ark | sudo -S reboot\n')
    time.sleep(3)
    c.close()
    return True

def run_stress(c):
    ok = run(c, 'test -x /tmp/dmc_stress && echo YES || echo NO')
    if 'NO' in ok:
        write_file(c, '/tmp/dmc_stress.c', STRESS_C)
        sudo(c, 'gcc -O2 -o /tmp/dmc_stress /tmp/dmc_stress.c -lrt 2>&1', timeout=30)

    p = '/sys/class/devfreq/dmc'
    sudo(c, f'bash -c "echo performance > {p}/governor"')
    sudo(c, f'bash -c "echo 928000000 > {p}/min_freq"')
    sudo(c, f'bash -c "echo 928000000 > {p}/max_freq"')
    time.sleep(0.5)

    stop = threading.Event()
    c2 = connect(timeout=10)
    temps = []
    def monitor():
        while not stop.wait(2):
            try:
                t = run(c2, 'cat /sys/class/thermal/thermal_zone0/temp')
                if t: temps.append(int(t)//1000)
            except: break
    th = threading.Thread(target=monitor, daemon=True)
    th.start()

    result = sudo(c, '/tmp/dmc_stress', timeout=45)
    stop.set(); th.join(6)
    if c2: c2.close()

    sudo(c, f'bash -c "echo 0 > {p}/min_freq"')
    sudo(c, f'bash -c "echo 928000000 > {p}/max_freq"')
    sudo(c, f'bash -c "echo dmc_ondemand > {p}/governor"')
    sudo(c, f'rm -f {DTB_PENDING}')

    mb = None
    if 'STABLE' in result:
        try: mb = float(result.split()[1])
        except: pass

    temp_str = f'{min(temps)}-{max(temps)}C' if temps else '?'
    return mb, temp_str, result

def main():
    start_volt = int(sys.argv[1]) if len(sys.argv) > 1 else 1050000
    results = []
    volt = start_volt

    print(f'Auto-sweep DMC UV desde {volt//1000} mV descendiendo de 12.5 en 12.5 mV')
    print(f'Stop automatico al primer crash.')
    print()

    while volt >= 950000:
        print(f'{"="*50}')
        print(f'PASO: {volt/1000:.1f} mV')
        print(f'{"="*50}')

        # patch + reboot
        c = connect(timeout=30)
        if not c:
            print('ERROR: no se puede conectar para patch'); break
        ok = patch_and_reboot(c, volt)
        if not ok: break

        # esperar reboot + SSH
        print(f'  Esperando reboot...', end='', flush=True)
        time.sleep(20)
        print(' conectando...', end='', flush=True)
        c = connect(timeout=90)
        if not c:
            print()
            print(f'  CRASH o SSH no disponible a {volt/1000:.1f} mV -> LIMITE ALCANZADO')
            results.append({'volt': volt, 'stable': False, 'mb': None, 'temp': 'CRASH'})
            break
        print(' OK')

        # stress
        print(f'  Stress 128MB 30s...', end=' ', flush=True)
        try:
            mb, temp_str, raw = run_stress(c)
            c.close()
        except Exception as e:
            print(f'\n  EXCEPTION: {e}')
            results.append({'volt': volt, 'stable': False, 'mb': None, 'temp': 'CRASH'})
            break

        stable = mb is not None
        results.append({'volt': volt, 'stable': stable, 'mb': mb, 'temp': temp_str})

        if stable:
            print(f'ESTABLE  {mb:.0f} MB/s  {temp_str}')
            volt -= 12500
        else:
            print(f'INESTABLE: {raw[:100]}')
            break

    print()
    print(f'{"="*60}')
    print('RESULTADOS DMC UV SWEEP')
    print(f'{"="*60}')
    for r in results:
        mv = r["volt"] / 1000
        status = 'ESTABLE' if r['stable'] else 'CRASH/FAIL'
        mb_str = f'{r["mb"]:.0f} MB/s' if r['mb'] else '---'
        print(f'  {mv:.1f} mV: {status}  {mb_str}  {r["temp"]}')

    stable_results = [r for r in results if r['stable']]
    if stable_results:
        floor = min(r['volt'] for r in stable_results)
        print(f'\n  Floor estable: {floor/1000:.1f} mV')

if __name__ == '__main__':
    main()
