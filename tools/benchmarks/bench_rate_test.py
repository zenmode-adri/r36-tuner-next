#!/usr/bin/env python3
"""
Investigacion: timing artifact en BenchmarkCPU?
Hipotesis: tv_sec truncation → runtime varía ±1s → tasa real distorsionada.
Fix: imprimir ops + elapsed_ns, calcular Mops/s real.
"""
import paramiko, time, sys

HOST, USER, PASS = '192.168.1.87', 'ark', 'ark'

BENCH_SRC = r"""
#include <stdio.h>
#include <time.h>
#include <stdint.h>

int main() {
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    uint32_t a=1, b=2, c=3, d=4;
    long long iters = 0;
    int i;
    do {
        for (i = 0; i < 10000000; i++) {
            a = a * 1664525u + 1013904223u;
            b = b * 1664525u + 1013904223u;
            c = c * 1664525u + 1013904223u;
            d = d * 1664525u + 1013904223u;
        }
        iters += 40000000;
        clock_gettime(CLOCK_MONOTONIC, &t1);
    } while ((t1.tv_sec - t0.tv_sec) < 30);
    if (a ^ b ^ c ^ d == 0) iters++;
    long long elapsed_ns = (t1.tv_sec - t0.tv_sec) * 1000000000LL + (t1.tv_nsec - t0.tv_nsec);
    /* ops  elapsed_ns */
    printf("%lld %lld\n", iters, elapsed_ns);
    return 0;
}
"""

SETFREQ = """#!/bin/bash
# setfreq.sh <khz>
FREQ=$1
echo powersave > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
echo "$FREQ" > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq
echo "$FREQ" > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq
echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
sleep 0.5
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq
"""

def run(c, cmd, timeout=90):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode('utf-8', errors='replace').strip()
    e = err.read().decode('utf-8', errors='replace').strip()
    return o, e

def run_sudo(c, cmd, timeout=90):
    return run(c, f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)

def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=22, username=USER, password=PASS)
    return c

def setup(c):
    print("Compilando bench diagnóstico...")
    # Write source
    stdin2, stdout2, _ = c.exec_command("cat > /tmp/bench_diag.c")
    stdin2.write(BENCH_SRC.encode())
    stdin2.channel.shutdown_write()
    stdout2.read()

    o, e = run_sudo(c, "gcc -O1 -o /tmp/bench_diag /tmp/bench_diag.c 2>&1")
    if e and 'error' in e.lower():
        print(f"  ERROR compilando: {e}")
        sys.exit(1)
    print("  OK")

    # Write setfreq helper
    stdin3, stdout3, _ = c.exec_command("cat > /tmp/setfreq2.sh")
    stdin3.write(SETFREQ.encode())
    stdin3.channel.shutdown_write()
    stdout3.read()
    run_sudo(c, "chmod +x /tmp/setfreq2.sh")

def set_freq(c, khz):
    o, _ = run_sudo(c, f"bash /tmp/setfreq2.sh {khz}")
    actual = o.strip().split('\n')[-1]
    print(f"  freq actual: {actual} kHz  (target: {khz})")
    return actual

def run_bench(c, runs=3):
    results = []
    for i in range(runs):
        print(f"  run {i+1}/{runs}...", end=' ', flush=True)

        # Monitor freq from parallel connection during bench
        c2 = connect()
        freq_samples = []

        def monitor_freq():
            for _ in range(10):
                time.sleep(3)
                o2, _ = run_sudo(c2, "cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq")
                freq_samples.append(o2.strip())

        import threading
        t = threading.Thread(target=monitor_freq, daemon=True)
        t.start()

        o, e = run_sudo(c, "/tmp/bench_diag", timeout=45)
        t.join(timeout=5)
        c2.close()

        if o:
            parts = o.strip().split()
            iters = int(parts[0])
            elapsed_ns = int(parts[1])
            elapsed_s = elapsed_ns / 1e9
            rate = iters / elapsed_ns * 1000.0  # Mops/s
            unique_freqs = sorted(set(freq_samples))
            print(f"  ops={iters//1_000_000}M  elapsed={elapsed_s:.3f}s  rate={rate:.1f} Mops/s  freq_during={unique_freqs}")
            results.append({'ops': iters, 'elapsed_ns': elapsed_ns, 'elapsed_s': elapsed_s, 'rate': rate, 'freqs': unique_freqs})
        else:
            print(f"  ERROR: {e!r}")
    return results

def restore_freq(c):
    run_sudo(c, "echo ondemand > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor")
    o, _ = run_sudo(c, "cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq")
    print(f"  governor restaurado, freq: {o.strip()} kHz")

def main():
    print("Conectando...")
    c = connect()
    print("  OK")

    setup(c)

    freqs = [
        (1008000, "1008 MHz"),
        (1512000, "1512 MHz"),
        (1608000, "1608 MHz"),
    ]

    all_results = {}

    for khz, label in freqs:
        print(f"\n{'='*50}")
        print(f"TEST: {label}")
        print(f"{'='*50}")
        set_freq(c, khz)
        time.sleep(1)
        r = run_bench(c, runs=3)
        all_results[label] = r

    restore_freq(c)
    c.close()

    print(f"\n{'='*60}")
    print("RESUMEN — TASA REAL (Mops/s)")
    print(f"{'='*60}")

    avg_rates = {}
    for label, results in all_results.items():
        if not results:
            continue
        rates = [r['rate'] for r in results]
        elapsed = [r['elapsed_s'] for r in results]
        ops = [r['ops'] // 1_000_000 for r in results]
        avg_r = sum(rates) / len(rates)
        avg_rates[label] = avg_r
        print(f"\n{label}:")
        print(f"  ops (Mops)    : {ops}")
        print(f"  elapsed (s)   : {[f'{e:.3f}' for e in elapsed]}")
        print(f"  rate (Mops/s) : {[f'{r:.1f}' for r in rates]}")
        print(f"  avg rate      : {avg_r:.1f} Mops/s")

    labels = list(avg_rates.keys())
    print(f"\nScaling por paso:")
    for i, label in enumerate(labels):
        r = avg_rates[label]
        mhz = int(label.split()[0])
        cycles_per_op = mhz / r
        print(f"  {label}: {r:.1f} Mops/s  ({cycles_per_op:.3f} cycles/op)")
        if i > 0:
            prev_label = labels[i-1]
            prev_r = avg_rates[prev_label]
            prev_mhz = int(prev_label.split()[0])
            rate_scaling = (r - prev_r) / prev_r * 100
            clock_scaling = (mhz - prev_mhz) / prev_mhz * 100
            eff = rate_scaling / clock_scaling * 100 if clock_scaling else 0
            print(f"    vs {prev_label}: rate {rate_scaling:+.1f}%  clock {clock_scaling:+.1f}%  eff {eff:.0f}%")

    print(f"\nJitter timing (tv_sec artifact):")
    for label, results in all_results.items():
        elapsed = [r['elapsed_s'] for r in results]
        if elapsed:
            jitter = max(elapsed) - min(elapsed)
            print(f"  {label}: {min(elapsed):.3f}s-{max(elapsed):.3f}s  jitter={jitter:.3f}s ({jitter/30*100:.1f}%)")

if __name__ == '__main__':
    main()
