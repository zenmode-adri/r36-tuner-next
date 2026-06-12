import paramiko, io

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd, timeout=15):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode(errors='replace').strip()
    e = err.read().decode(errors='replace').strip()
    return o, e

# 1. Actual bytes in .init_array section
o, e = run("readelf -x .init_array /usr/local/lib/libr36overlay.so 2>&1")
print("=== .init_array hex dump ===")
print(o or e)

# 2. nm -n (all symbols, including static)
o, e = run("nm /usr/local/lib/libr36overlay.so | grep -iE 'init|ctor|overlay' 2>&1")
print("\n=== nm init/ctor symbols ===")
print(o or e or '(none)')

# 3. LD_DEBUG on ls
o, e = run(
    "LD_DEBUG=all LD_PRELOAD=/usr/local/lib/libr36overlay.so ls / 2>&1 | grep -E 'r36|calling|init' | head -20"
)
print("\n=== LD_DEBUG calling init ===")
print(o or e or '(empty)')

# 4. Does strace exist?
o, e = run("which strace 2>&1; strace --version 2>&1 | head -1")
print("\n=== strace available? ===")
print(o or e or '(no)')

# 5. LD_DEBUG symbols for our lib
o, e = run(
    "LD_DEBUG=symbols LD_PRELOAD=/usr/local/lib/libr36overlay.so ls / 2>&1 | grep r36overlay | head -20"
)
print("\n=== LD_DEBUG symbols for r36overlay ===")
print(o or e or '(empty)')

c.close()
