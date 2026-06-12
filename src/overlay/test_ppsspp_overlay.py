import paramiko, io, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd, timeout=15):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode(errors='replace').strip()
    e = err.read().decode(errors='replace').strip()
    return o, e

# 1. Check ppsspp.sh has the LD_PRELOAD
o, _ = run("grep -n 'LD_PRELOAD\|r36overlay' /usr/local/bin/ppsspp.sh")
print("=== ppsspp.sh LD_PRELOAD lines ===")
print(o or '(none found!)')

# 2. Fresh log
run("rm -f /tmp/r36overlay.log")

# 3. PPSSPP --version via SSH (tests constructor in PPSSPP context)
o, e = run(
    "LD_PRELOAD=/usr/local/lib/libr36overlay.so /opt/ppsspp/PPSSPPSDL --version 2>&1 | head -5",
    timeout=10
)
print("\n=== PPSSPP --version with overlay ===")
print(repr(o) if o else repr(e))

# 4. Check log after ppsspp --version
o, _ = run("cat /tmp/r36overlay.log 2>/dev/null")
print("\n=== Log after PPSSPP --version ===")
print(repr(o) or '(empty)')

# 5. eglSwapBuffers exported?
o, _ = run("nm -D /usr/local/lib/libr36overlay.so | grep -E 'SDL|egl'")
print("\n=== Exported hooks ===")
print(o)

c.close()
