import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd, timeout=30):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

def sudo(cmd, timeout=30):
    _, out, err = c.exec_command('echo ark | sudo -S ' + cmd, timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

ASM_SRC = r"""
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
    printf("%lld %lld\n", iters, elapsed_ns);
    return 0;
}
"""

# Write source
stdin2, stdout2, _ = c.exec_command('cat > /tmp/bench_asm.c')
stdin2.write(ASM_SRC.encode())
stdin2.channel.shutdown_write()
stdout2.read()

# Generate assembly
print('=== gcc -O1 assembly ===')
o = sudo('gcc -O1 -S -o /tmp/bench_asm.s /tmp/bench_asm.c && cat /tmp/bench_asm.s')
print(o)

# Also check if MUL or MADD
print('\n=== madd/mul count ===')
o2 = run('grep -cE "madd|mul" /tmp/bench_asm.s 2>/dev/null || echo not found')
print('lines with mul/madd:', o2)

o3 = run('grep -E "madd|mul|add" /tmp/bench_asm.s 2>/dev/null | head -20')
print(o3)

c.close()
