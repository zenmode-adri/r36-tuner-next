import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd, timeout=15):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode(errors='replace').strip()
    e = err.read().decode(errors='replace').strip()
    return o, e

# 1. All text symbols near 0x8e0 to identify what the init_array points to
o, _ = run("nm /usr/local/lib/libr36overlay.so | grep ' t ' | sort | head -30")
print("=== local text symbols (sorted) ===")
print(o)

# 2. nm all sorted, look near 0x8e0
o, _ = run("nm /usr/local/lib/libr36overlay.so | awk '{print $1, $2, $3}' | sort | grep -E '^0+8[89abcde]'")
print("\n=== symbols near 0x8e0 ===")
print(o or '(none)')

# 3. Full nm, check for overlay_init specifically
o, _ = run("nm /usr/local/lib/libr36overlay.so | grep overlay_init")
print("\n=== overlay_init in nm ===")
print(o or '(NOT FOUND)')

# 4. Check number of entries in .init_array + .init section bytes
o, _ = run("objdump -d --section=.init /usr/local/lib/libr36overlay.so 2>&1 | head -20")
print("\n=== .init disasm ===")
print(o)

# 5. objdump -d around 0x8e0
o, _ = run("objdump -d /usr/local/lib/libr36overlay.so 2>&1 | awk '/^[0-9a-f]/{addr=strtonum(\"0x\"$1)} addr>=0x880 && addr<=0x980' | head -40")
print("\n=== disasm around 0x8e0 ===")
print(o or '(empty)')

c.close()
