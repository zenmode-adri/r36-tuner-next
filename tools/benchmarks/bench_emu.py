#!/usr/bin/env python3
"""
bench_emu.py — test de scaling 1512 vs 1608 MHz.
Simula el inner loop de un emulador: switch de opcodes, 32 registros (L1),
branch-heavy. Midiendo MIPS (instrucciones emuladas por segundo).
"""
import paramiko, time

HOST, USER, PASS = '192.168.1.87', 'ark', 'ark'

EMU_SRC = r"""
#include <stdio.h>
#include <time.h>
#include <stdint.h>
#include <string.h>

/* Programa "ROM" de 256 opcodes — patron fijo, repetitivo como codigo real de juego.
   El branch predictor aprende el patron tras pocas repeticiones. */
#define ROM_SIZE 256
#define ITERS 500000000ULL

static const uint8_t ROM[ROM_SIZE] = {
    0,1,2,3,0,1,0,2, 3,0,1,2,0,0,1,3,  /* bucle tipico: ALU + load + branch */
    0,1,2,0,1,2,0,1, 2,0,1,2,0,1,2,0,
    3,3,0,1,0,3,2,1, 0,1,0,2,3,0,1,2,
    0,0,0,1,2,0,1,0, 0,1,2,3,0,1,2,0,
    1,2,0,1,0,2,1,0, 3,0,1,2,0,1,0,2,
    0,1,2,0,1,0,2,3, 0,1,0,2,0,1,2,0,
    0,1,2,3,0,1,2,3, 0,1,2,3,0,1,2,3,
    0,1,0,2,0,3,0,1, 2,0,1,0,2,0,3,1,
    0,1,2,3,0,1,0,2, 3,0,1,2,0,0,1,3,
    0,1,2,0,1,2,0,1, 2,0,1,2,0,1,2,0,
    3,3,0,1,0,3,2,1, 0,1,0,2,3,0,1,2,
    0,0,0,1,2,0,1,0, 0,1,2,3,0,1,2,0,
    1,2,0,1,0,2,1,0, 3,0,1,2,0,1,0,2,
    0,1,2,0,1,0,2,3, 0,1,0,2,0,1,2,0,
    0,1,2,3,0,1,2,3, 0,1,2,3,0,1,2,3,
    0,1,0,2,0,3,0,1, 2,0,1,0,2,0,3,1,
};

int main(void) {
    struct timespec t0, t1;
    uint32_t reg[8] = {1,2,3,4,5,6,7,8};
    uint32_t pc = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);

    for (uint64_t i = 0; i < ITERS; i++) {
        uint8_t op = ROM[pc & (ROM_SIZE-1)];
        uint32_t ra = pc & 7, rb = (pc+1) & 7;
        switch (op & 3) {
            case 0: reg[ra] += reg[rb]; break;
            case 1: reg[ra] ^= reg[rb]; break;
            case 2: reg[ra] = reg[ra] * 1664525u + 1013904223u; break;
            case 3: reg[ra] -= reg[rb]; break;
        }
        pc++;
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec) * 1e-9;
    double mips = ITERS / elapsed / 1e6;
    printf("MIPS=%.1f time=%.3fs (check=%u)\n", mips, elapsed, reg[0]);
    return 0;
}
"""

def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=22, username=USER, password=PASS)
    return c

def run(c, cmd, timeout=60):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

def sudo(c, cmd, timeout=60):
    return run(c, 'echo ark | sudo -S ' + cmd, timeout=timeout)

def set_freq(c, khz):
    sudo(c, f'bash -c "echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"')
    sudo(c, f'bash -c "echo {khz} > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq"')
    sudo(c, f'bash -c "echo {khz} > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq"')
    time.sleep(0.5)
    cur = run(c, 'cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq')
    return int(cur) // 1000

def restore_freq(c):
    sudo(c, 'bash -c "echo ondemand > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"')
    sudo(c, f'bash -c "echo 1608000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq"')
    sudo(c, f'bash -c "echo 408000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq"')

def compile_emu(c):
    # Write source
    stdin, stdout, _ = c.exec_command('cat > /tmp/emu_bench.c')
    stdin.write(EMU_SRC.encode())
    stdin.channel.shutdown_write()
    stdout.read()
    # Compile
    out = sudo(c, 'gcc -O2 -o /tmp/emu_bench /tmp/emu_bench.c -lrt 2>&1')
    ok = run(c, 'test -x /tmp/emu_bench && echo YES || echo NO')
    if 'YES' in ok:
        print('  compilado OK')
        return True
    print(f'  error gcc: {out}')
    return False

def bench(c, runs=3):
    scores = []
    for i in range(runs):
        out = run(c, '/tmp/emu_bench', timeout=30)
        # parse MIPS=NNN
        for tok in out.split():
            if tok.startswith('MIPS='):
                try:
                    scores.append(float(tok.split('=')[1]))
                except:
                    pass
        print(f'    run {i+1}: {out}')
    return scores

def main():
    print('Conectando...')
    c = connect()

    print('Compilando...')
    if not compile_emu(c):
        c.close(); return

    print('\nMatando EmulationStation...')
    sudo(c, 'systemctl stop emulationstation 2>/dev/null; sleep 1; pkill -9 emulationstation 2>/dev/null; sleep 2')
    print('  ES detenido.')

    results = {}
    for khz, label in [(1512000, '1512 MHz'), (1608000, '1608 MHz')]:
        print(f'\n--- {label} ---')
        real_mhz = set_freq(c, khz)
        print(f'  freq activa: {real_mhz} MHz')
        time.sleep(1)
        scores = bench(c, runs=5)
        results[label] = scores

    restore_freq(c)
    print('\nRestaurando EmulationStation...')
    sudo(c, 'systemctl start emulationstation 2>/dev/null')
    c.close()

    print('\n' + '='*50)
    print('RESUMEN')
    print('='*50)
    avgs = {}
    for label, scores in results.items():
        if scores:
            avg = sum(scores) / len(scores)
            avgs[label] = avg
            print(f'  {label}: {avg:.1f} MIPS  (runs: {[f"{s:.1f}" for s in scores]})')

    if '1512 MHz' in avgs and '1608 MHz' in avgs:
        delta = (avgs['1608 MHz'] - avgs['1512 MHz']) / avgs['1512 MHz'] * 100
        print(f'\n  1512 -> 1608 MHz: {delta:+.1f}%')

if __name__ == '__main__':
    main()
