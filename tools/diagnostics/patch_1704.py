import paramiko, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def sudo(cmd, timeout=20):
    _, out, err = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)
    o = out.read().decode('utf-8', errors='replace').strip()
    e = err.read().decode('utf-8', errors='replace').strip()
    return o, e

DTB      = '/boot/rk3326-r36s-linux.dtb'
BAK      = '/boot/rk3326-r36s-linux.dtb.bak'
OC1704   = '/boot/rk3326-r36s-linux.dtb.oc_1704'
NODE     = '/cpu0-opp-table/opp-1704000000'
PENDING  = '/boot/.r36_dtb_pending'

# 1. Backup sanity check
print("=== Backup check ===")
o, _ = sudo(f'ls -lh {BAK} 2>/dev/null')
print(o or "ERROR: .bak NO EXISTE — abortando")
if not o:
    c.close()
    exit(1)

# 2. Limpiar flag stale de May 21
print("\n=== Limpiando flag stale ===")
o, _ = sudo(f'rm -f {PENDING} && echo "ok"')
print(o)

# 3. Snapshot del DTB actual antes de tocar nada
print("\n=== Guardando snapshot pre-1704 ===")
o, _ = sudo(f'cp {DTB} {OC1704}.pre && echo "ok"')
print(o)

# 4. Verificar avs-scale=0
print("\n=== avs-scale actual ===")
o, _ = sudo(f'fdtget -t u {DTB} /cpu0-opp-table rockchip,avs-scale')
print(f"avs-scale = {o}")
if o.strip() != '0':
    print("ERROR: avs-scale != 0 — abortando")
    c.close()
    exit(1)

# 5. Añadir nodo opp-1704000000
print("\n=== Añadiendo opp-1704000000 ===")
cmds = [
    f'fdtput -c {DTB} {NODE}',
    f'fdtput -t u {DTB} {NODE} opp-hz 0 1704000000',
    f'fdtput -t u {DTB} {NODE} opp-microvolt 1350000 1350000 1350000',
    f'fdtput -t u {DTB} {NODE} opp-microvolt-L2 1350000 1350000 1350000',
]
for cmd in cmds:
    o, e = sudo(cmd)
    if e and 'sudo' not in e.lower():
        print(f"  ERR [{cmd}]: {e}")
    else:
        print(f"  OK: {cmd.split('fdtput')[-1][:60]}")

# 6. Verificar que el nodo quedó bien
print("\n=== Verificacion nodo 1704 ===")
o, _ = sudo(f'fdtget -t u {DTB} {NODE} opp-hz')
print(f"  opp-hz = {o}")
o, _ = sudo(f'fdtget -t u {DTB} {NODE} opp-microvolt-L2')
print(f"  opp-microvolt-L2 = {o}")

# 7. Guardar copia oc_1704
print("\n=== Guardando .oc_1704 ===")
o, _ = sudo(f'cp {DTB} {OC1704} && echo "ok"')
print(o)

# 8. Tamaño final
print("\n=== Tamaño DTB ===")
o, _ = sudo(f'ls -lh {DTB}')
print(o)

# 9. Set pending flag + sync
print("\n=== Sync + pending flag ===")
sudo(f'touch {PENDING}')
sudo('sync && sync')
print("sync ok")

# 10. Reboot
print("\n=== Rebooting... ===")
shell = c.invoke_shell()
time.sleep(0.5)
shell.send("echo ark | sudo -S reboot\n")
time.sleep(3)
c.close()
print("Device rebooting — activa WiFi/SSH y corre check_1704.py")
