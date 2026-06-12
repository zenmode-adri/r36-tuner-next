import paramiko

HOST = '192.168.1.87'
USER = 'ark'
PASS = 'ark'
DTB  = '/boot/rk3326-r36s-linux.dtb'
NODE = '/gpu-opp-table/opp-600000000'
PROP = 'opp-microvolt-L2'
NEW_UV = 1100000

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=22, username=USER, password=PASS)

def run(cmd, timeout=15):
    _, out, err = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)
    o = out.read().decode().strip()
    e = err.read().decode().strip()
    return o, e

def sudo(cmd, timeout=15):
    o, _ = run(cmd, timeout)
    return o

# 1. Verificar estado actual
print("=== Estado actual ===")
cur = sudo(f'fdtget -t u {DTB} "{NODE}" {PROP} 2>/dev/null || echo "NODE_NOT_FOUND"')
print(f"  {PROP} actual: {cur}")

cur_gen = sudo(f'fdtget -t u {DTB} "{NODE}" opp-microvolt 2>/dev/null || echo "not found"')
print(f"  opp-microvolt actual: {cur_gen}")

cur_hz = sudo(f'fdtget -t u {DTB} "{NODE}" opp-hz 2>/dev/null || echo "not found"')
print(f"  opp-hz: {cur_hz}")

if 'NODE_NOT_FOUND' in cur:
    print("ERROR: nodo opp-600000000 no existe en DTB — GPU OC no aplicado")
    c.close()
    exit(1)

# 2. Patch a 1100000 uV
print(f"\n=== Parchando {NODE} -> {NEW_UV} uV ({NEW_UV/1000} mV) ===")
out, err = run(f'fdtput -t u {DTB} "{NODE}" {PROP} {NEW_UV}')
print(f"  L2 patch: {'OK' if not err else 'ERR: '+err}")

out, err = run(f'fdtput -t u {DTB} "{NODE}" opp-microvolt {NEW_UV}')
print(f"  generic patch: {'OK' if not err else 'ERR: '+err}")

# 3. Verificar que quedó bien
new_val = sudo(f'fdtget -t u {DTB} "{NODE}" {PROP}')
print(f"  Verificación {PROP}: {new_val}")

# 4. DTB_PENDING + reboot
sudo('touch /boot/.r36_dtb_pending')
print("\n  DTB_PENDING set ✓")

print("\n=== Rebooting ===")
c.exec_command("echo ark | sudo -S reboot")
c.close()
print("Hecho. Avísame cuando el R36 arranque y tengas SSH activo.")
