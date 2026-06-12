import paramiko, time

HOST, PORT, USER, PASS = '192.168.1.87', 22, 'ark', 'ark'

C_SRC = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#define BUF (64*1024*1024)
#define DUR 2
int main() {
    char *a = malloc(BUF), *b = malloc(BUF);
    if (!a || !b) { puts("0\n0"); return 1; }
    memset(a, 0xAB, BUF);
    memset(b, 0x00, BUF);
    struct timespec t0, t1;
    long long n, ms;
    n = 0;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    do { memset(b, 0xCD, BUF); n += BUF;
         clock_gettime(CLOCK_MONOTONIC, &t1);
    } while (t1.tv_sec - t0.tv_sec < DUR);
    ms = (t1.tv_sec-t0.tv_sec)*1000+(t1.tv_nsec-t0.tv_nsec)/1000000;
    printf("%lld\n", n/1024/1024*1000/ms);
    n = 0;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    do { memcpy(b, a, BUF); n += BUF;
         clock_gettime(CLOCK_MONOTONIC, &t1);
    } while (t1.tv_sec - t0.tv_sec < DUR);
    ms = (t1.tv_sec-t0.tv_sec)*1000+(t1.tv_nsec-t0.tv_nsec)/1000000;
    printf("%lld\n", n/1024/1024*1000/ms);
    return 0;
}
"""

def run(c, cmd):
    _, out, err = c.exec_command(cmd)
    return out.read().decode().strip()

def sudo(c, cmd):
    _, out, err = c.exec_command(f"echo {PASS} | sudo -S bash -c '{cmd}'")
    out.read(); err.read()

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASS)

dmc = "/sys/class/devfreq/dmc"
print("Testing 928 MHz (64MB buf, 2s)...")

sudo(c, f"echo 528000000 > {dmc}/min_freq")
sudo(c, f"echo 928000000 > {dmc}/max_freq")
sudo(c, f"echo 928000000 > {dmc}/min_freq")
time.sleep(0.5)

cur = run(c, f"cat {dmc}/cur_freq")
print(f"Pinned at: {int(cur)//1000000} MHz")

# compile
stdin, out, _ = c.exec_command("cat > /tmp/r36_rambench2.c")
stdin.write(C_SRC.encode()); stdin.channel.shutdown_write(); out.read()
run(c, "gcc -O2 -o /tmp/r36_rambench2 /tmp/r36_rambench2.c")

result = run(c, "/tmp/r36_rambench2 2>/dev/null")
lines = result.strip().split('\n')
w  = int(lines[0]) if len(lines) > 0 and lines[0].isdigit() else 0
cp = int(lines[1]) if len(lines) > 1 and lines[1].isdigit() else 0
print(f"write={w} MB/s  copy={cp} MB/s")

# restore
sudo(c, f"echo 528000000 > {dmc}/min_freq")
sudo(c, f"echo 928000000 > {dmc}/max_freq")
print("Restored.")
c.close()
