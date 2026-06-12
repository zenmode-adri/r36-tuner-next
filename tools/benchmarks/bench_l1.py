#!/usr/bin/env python3
"""
L1-resident pointer chasing benchmark.
Array 16KB (4096 x uint32) cabe en L1 (32KB en A35).
Cada paso = arr[idx] -> serial dependency -> no prefetch -> mide L1 load latency.
L1 latency = ~4 ciclos de CPU -> escala con freq (~6% entre 1512 y 1608 MHz).
"""
import paramiko, time, threading

HOST, USER, PASS = '192.168.1.87', 'ark', 'ark'

SRC = r"""
#include <stdio.h>
#include <stdint.h>
#include <time.h>

#define N 4096
#define STEPS 400000000LL

static uint32_t arr[N];

int main(void) {
    /* fill with pseudo-random indices — no sequential pattern */
    uint32_t v = 0xdeadbeef;
    for (int i = 0; i < N; i++) {
        v = v * 1664525u + 1013904223u;
        arr[i] = v % N;
    }

    /* warm up: pull entire arr into L1 */
    volatile uint32_t idx = 0;
    for (int i = 0; i < N * 8; i++) idx = arr[idx];

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long long i = 0; i < STEPS; i++) idx = arr[idx];
    clock_gettime(CLOCK_MONOTONIC, &t1);

    if (idx == 0xdeadbeef) printf("x");  /* prevent DCE */

    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec)*1e-9;
    printf("%.2f Msteps/s  elapsed=%.3fs\n", STEPS / elapsed / 1e6, elapsed);
    return 0;
}
"""

def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=22, username=USER, password=PASS)
    return c

def run(c, cmd, timeout=30):
    _, o, _ = c.exec_command(cmd, timeout=timeout)
    return o.read().decode('utf-8', errors='replace').strip()

def sudo(c, cmd, timeout=30):
    _, o, _ = c.exec_command('echo ark | sudo -S ' + cmd, timeout=timeout)
    return o.read().decode('utf-8', errors='replace').strip()

def write_file(c, path, data):
    if isinstance(data, str): data = data.encode()
    CHUNK = 524288
    for i, off in enumerate(range(0, len(data), CHUNK)):
        cmd = f'cat > {path}' if i == 0 else f'cat >> {path}'
        s, o, _ = c.exec_command(cmd)
        s.write(data[off:off+CHUNK]); s.channel.shutdown_write(); o.read()

def set_cpu(c, khz):
    sudo(c, f'bash -c "echo {khz} > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq"')
    sudo(c, f'bash -c "echo {khz} > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq"')
    sudo(c, 'bash -c "echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"')
    time.sleep(0.5)
    cur = run(c, 'cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq')
    print(f'  CPU: {cur} kHz')

def run_bench(c, runs=4, label=''):
    results = []
    for i in range(runs):
        print(f'  [{label}] run {i+1}/{runs}...', end=' ', flush=True)
        o = sudo(c, '/tmp/r36_l1bench', timeout=30)
        try:
            score = float(o.split()[0])
            print(o)
            results.append(score)
        except:
            print(f'FAIL: {o[:200]}')
    return results

def main():
    print('Conectando...')
    c = connect()
    print('OK')

    # compilar si no existe
    ok = run(c, 'test -x /tmp/r36_l1bench && echo YES || echo NO')
    if 'NO' in ok:
        print('Compilando...')
        write_file(c, '/tmp/r36_l1bench.c', SRC)
        out = sudo(c, 'gcc -O1 -o /tmp/r36_l1bench /tmp/r36_l1bench.c -lrt 2>&1', timeout=30)
        if out: print(f'  gcc: {out}')
        ok2 = run(c, 'test -x /tmp/r36_l1bench && echo YES || echo NO')
        if 'NO' in ok2:
            print('ERROR compilando'); c.close(); return
        print('  Compilado OK')

    freqs = [(1008000, '1008 MHz'), (1512000, '1512 MHz'), (1608000, '1608 MHz')]
    all_scores = {}

    try:
        for khz, label in freqs:
            print(f'\n{"="*50}')
            print(f'CPU {label}')
            print(f'{"="*50}')
            set_cpu(c, khz)
            time.sleep(1)
            scores = run_bench(c, runs=3, label=label)
            all_scores[label] = scores
    finally:
        sudo(c, 'bash -c "echo ondemand > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"')
        c.close()

    print(f'\n{"="*60}')
    print('RESULTADO — L1 pointer chasing (16KB array)')
    print(f'{"="*60}')
    avgs = {}
    for label, _ in freqs:
        sc = all_scores.get(label, [])
        if sc:
            avg = sum(sc) / len(sc)
            avgs[label] = avg
            mhz = int(label.split()[0])
            cyc = mhz / avg  # cycles per step
            print(f'  {label}: {avg:.1f} Msteps/s  ({cyc:.2f} cycles/step)')

    print()
    labels = [l for _, l in freqs if l in avgs]
    for i in range(1, len(labels)):
        a, b = labels[i-1], labels[i]
        delta = (avgs[b] - avgs[a]) / avgs[a] * 100
        mhz_a, mhz_b = int(a.split()[0]), int(b.split()[0])
        clk_delta = (mhz_b - mhz_a) / mhz_a * 100
        eff = delta / clk_delta * 100 if clk_delta else 0
        print(f'  {a} -> {b}: {delta:+.1f}% score  ({clk_delta:+.1f}% clock)  eficiencia {eff:.0f}%')

    if '1512 MHz' in avgs and '1608 MHz' in avgs:
        d = (avgs['1608 MHz'] - avgs['1512 MHz']) / avgs['1512 MHz'] * 100
        print(f'\n  1512->1608: {d:+.1f}%  (teorico +6.3% si puro L1 latency)')

if __name__ == '__main__':
    main()
