import paramiko, time

HOST, PORT, USER, PASS = '192.168.1.87', 22, 'ark', 'ark'

C_SRC = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#define BUF (128*1024*1024)
#define DUR 3
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

# Find DMC devfreq path
dmc = run(c, "ls /sys/class/devfreq/ | grep -E 'dmc|ff600000' | head -1")
dmc = f"/sys/class/devfreq/{dmc}"
print(f"DMC devfreq: {dmc}")

# Get available frequencies
avail = run(c, f"cat {dmc}/available_frequencies 2>/dev/null || cat {dmc}/freq_table 2>/dev/null")
freqs = sorted([int(x) for x in avail.split()])
print(f"Available freqs: {[f//1000000 for f in freqs]} MHz")

# Save original state
orig_max = run(c, f"cat {dmc}/max_freq")
orig_min = run(c, f"cat {dmc}/min_freq")
orig_gov = run(c, f"cat {dmc}/governor 2>/dev/null || echo dmc_ondemand")
print(f"Stock state: max={int(orig_max)//1000000} MHz  min={int(orig_min)//1000000} MHz  gov={orig_gov}\n")

# Compile benchmark
print("Compiling RAM benchmark on device...")
stdin, out, err = c.exec_command("cat > /tmp/r36_rambench.c")
stdin.write(C_SRC.encode())
stdin.channel.shutdown_write()
out.read()
compile_err = run(c, "gcc -O2 -o /tmp/r36_rambench /tmp/r36_rambench.c 2>&1")
if compile_err:
    print(f"Compile error: {compile_err}")
    c.close()
    exit(1)
print("Compiled OK\n")

results = []

for freq in freqs:
    mhz = freq // 1000000
    print(f"Testing {mhz} MHz ...", end=' ', flush=True)

    # Pin frequency: set min first (if going up) or max first (if going down)
    # Safe order: always set min to lowest, set max to target, then set min to target
    sudo(c, f"echo {freqs[0]} > {dmc}/min_freq")
    sudo(c, f"echo {freq} > {dmc}/max_freq")
    sudo(c, f"echo {freq} > {dmc}/min_freq")
    time.sleep(0.3)

    cur = run(c, f"cat {dmc}/cur_freq")
    out = run(c, "/tmp/r36_rambench 2>/dev/null")
    lines = out.strip().split('\n')
    w = int(lines[0]) if len(lines) > 0 and lines[0].isdigit() else 0
    cp = int(lines[1]) if len(lines) > 1 and lines[1].isdigit() else 0
    print(f"cur={int(cur)//1000000} MHz  write={w} MB/s  copy={cp} MB/s")
    results.append((mhz, w, cp))

# Restore
print("\nRestoring original state...")
sudo(c, f"echo {freqs[0]} > {dmc}/min_freq")
sudo(c, f"echo {orig_max} > {dmc}/max_freq")
sudo(c, f"echo {orig_min} > {dmc}/min_freq")

print("\n--- RESULTS SUMMARY ---")
print(f"{'Freq':>8}  {'Write':>10}  {'Copy':>10}  {'Write%':>7}  {'Copy%':>7}")
base_w, base_cp = results[0][1], results[0][2]
for mhz, w, cp in results:
    pw = f"+{w*100//base_w-100}%" if base_w > 0 else "N/A"
    pc = f"+{cp*100//base_cp-100}%" if base_cp > 0 else "N/A"
    print(f"{mhz:>6} MHz  {w:>8} MB/s  {cp:>8} MB/s  {pw:>7}  {pc:>7}")

c.close()
