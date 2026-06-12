#!/usr/bin/env python3
"""
Diagnóstico 2: medir clock_gettime latency + ver assembly del bench
"""
import paramiko, time

HOST, USER, PASS = '192.168.1.87', 'ark', 'ark'

CLKTEST_SRC = r"""
#include <stdio.h>
#include <time.h>

int main() {
    struct timespec t, t0, t1;
    /* warm up */
    for (int i = 0; i < 10; i++) clock_gettime(CLOCK_MONOTONIC, &t);

    /* time 10000 calls */
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int i = 0; i < 10000; i++) {
        clock_gettime(CLOCK_MONOTONIC, &t);
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    long long ns = (t1.tv_sec - t0.tv_sec) * 1000000000LL + (t1.tv_nsec - t0.tv_nsec);
    printf("clock_gettime x10000: %lld ns total = %.1f ns/call\n", ns, (double)ns / 10000.0);

    /* also check if VDSO is mapped */
    return 0;
}
"""

def run(c, cmd, timeout=30):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode('utf-8', errors='replace').strip()
    e = err.read().decode('utf-8', errors='replace').strip()
    return o, e

def run_sudo(c, cmd, timeout=30):
    return run(c, f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)

def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=22, username=USER, password=PASS)
    return c

def main():
    c = connect()
    print("Conectado")

    # 1. Check VDSO
    print("\n--- VDSO check ---")
    o, _ = run(c, "cat /proc/self/maps 2>/dev/null | grep vdso || echo 'no vdso found'")
    print(o)

    # 2. Compile clock_gettime latency test
    print("\n--- Compilando clktest ---")
    stdin2, stdout2, _ = c.exec_command("cat > /tmp/clktest.c")
    stdin2.write(CLKTEST_SRC.encode())
    stdin2.channel.shutdown_write()
    stdout2.read()
    run_sudo(c, "gcc -O1 -o /tmp/clktest /tmp/clktest.c")
    print("  OK")

    # Run at 1008, 1512, 1608 MHz
    for khz, label in [(1008000, "1008 MHz"), (1512000, "1512 MHz"), (1608000, "1608 MHz")]:
        run_sudo(c, f"echo {khz} > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq")
        run_sudo(c, f"echo {khz} > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq")
        run_sudo(c, "echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor")
        time.sleep(0.5)
        o, _ = run_sudo(c, "/tmp/clktest")
        print(f"  {label}: {o}")

    # 3. Assembly of bench_diag inner loop
    print("\n--- Assembly del bench_diag (inner loop region) ---")
    o, _ = run(c, "objdump -d /tmp/bench_diag 2>/dev/null | head -80")
    print(o)

    # 4. Check if bench_diag uses MADD or MUL+ADD
    print("\n--- Instrucciones mul/madd en bench_diag ---")
    o, _ = run(c, "objdump -d /tmp/bench_diag 2>/dev/null | grep -E '(madd|mul|add)' | head -30")
    print(o)

    # 5. Count instructions in inner loop
    print("\n--- Full disassembly del main ---")
    o, _ = run(c, "objdump -d /tmp/bench_diag 2>/dev/null | grep -A 60 '<main>'")
    print(o)

    # 6. Check background processes that might cause interference at 1512 MHz
    print("\n--- Top processes ---")
    o, _ = run(c, "ps aux --sort=-%cpu 2>/dev/null | head -15")
    print(o)

    # 7. CPU topology / thermal zone
    print("\n--- CPU thermal zones ---")
    o, _ = run(c, "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null")
    print("temps:", o)

    # 8. Available frequencies
    print("\n--- Available CPU frequencies ---")
    o, _ = run(c, "cat /sys/devices/system/cpu/cpufreq/policy0/scaling_available_frequencies")
    print(o)

    # Restore
    run_sudo(c, "echo ondemand > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor")
    c.close()

if __name__ == '__main__':
    main()
