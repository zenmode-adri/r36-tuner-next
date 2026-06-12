import paramiko, io

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd, timeout=15):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode(errors='replace').strip()
    e = err.read().decode(errors='replace').strip()
    return o, e

# 1. Check ELF init_array in deployed .so
o, _ = run("readelf -d /usr/local/lib/libr36overlay.so | grep -E 'NEEDED|INIT|FINI|GNU'")
print("=== ELF dynamic section ===")
print(o)

# 2. Check nm -D for exported symbols
o, _ = run("nm -D /usr/local/lib/libr36overlay.so | grep -E ' T | t '")
print("\n=== Exported text symbols ===")
print(o)

# 3. Does ldd show deps?
o, e = run("ldd /usr/local/lib/libr36overlay.so")
print("\n=== ldd ===")
print(o or e)

# 4. Test: write to file (not fd 2)
o, e = run(
    "rm -f /tmp/ovl.log; "
    "LD_PRELOAD=/usr/local/lib/libr36overlay.so ls /tmp > /dev/null 2>&1; "
    "ls -la /tmp/r36overlay.log 2>&1; "
    "cat /tmp/r36overlay.log 2>/dev/null | head -3"
)
print("\n=== Log file after ls ===")
print(o)

# 5. strace write syscalls
o, e = run(
    "strace -e trace=write -f LD_PRELOAD=/usr/local/lib/libr36overlay.so ls / 2>&1 | grep -E 'write|R36|TINY' | head -20",
    timeout=15
)
print("\n=== strace write ===")
print(o or e or '(empty)')

c.close()
