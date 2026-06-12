import os
import paramiko, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

HOST = '192.168.1.87'
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=22, username='ark', password='ark')

def sudo(cmd, timeout=90):
    _, out, _ = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

# 1. Verificar voltaje en DTB
print("=== DTB voltaje ===")
dtb_val = sudo('fdtget -t u /boot/rk3326-r36s-linux.dtb /gpu-opp-table/opp-600000000 opp-microvolt-L2')
print(f"  DTB opp-microvolt-L2: {dtb_val} uV ({int(dtb_val)/1000} mV)" if dtb_val.isdigit() else f"  {dtb_val}")

# 2. Setup glmark2data
print("\n=== Setup glmark2data ===")
sudo('rm -rf /tmp/glmark2data')
sudo('mkdir -p /tmp/glmark2data/shaders')
sudo('ln -sf /usr/share/glmark2/models /tmp/glmark2data/models')
sudo('ln -sf /usr/share/glmark2/textures /tmp/glmark2data/textures')
sudo('cp /usr/share/glmark2/shaders/* /tmp/glmark2data/shaders/')
sudo(r'sed -i "s/MEDIUMP_OR_DEFAULT/mediump/g; s/HIGHP_OR_DEFAULT/highp/g" /tmp/glmark2data/shaders/*')
mediump_remaining = sudo('grep -rl MEDIUMP_OR_DEFAULT /tmp/glmark2data/shaders/ | wc -l')
print(f"  Shaders parcheados OK (MEDIUMP restantes: {mediump_remaining})")

# 3. Transferir binario
print("\n=== Transfiriendo glmark2 legacy ===")
sftp = c.open_sftp()
sftp.put(os.path.join(ROOT, 'bin', 'glmark2-es2-drm-legacy'), '/tmp/glmark2-es2-drm-legacy')
sftp.close()
sudo('chmod +x /tmp/glmark2-es2-drm-legacy')
print("  OK")

# 4. Bloquear GPU a 600 MHz
print("\n=== Bloqueando GPU a 600 MHz ===")
sudo('echo 600000000 > /sys/class/devfreq/ff400000.gpu/max_freq')
sudo('echo performance > /sys/class/devfreq/ff400000.gpu/governor')
time.sleep(1)
cur_freq = sudo('cat /sys/class/devfreq/ff400000.gpu/cur_freq')
print(f"  cur_freq: {cur_freq} Hz")

# 5. Voltaje sysfs bajo carga (verificar despues del bench)
print("\n=== Corriendo terrain (20s) ===")
result = sudo('/tmp/glmark2-es2-drm-legacy --off-screen --size 320x240 --data-path /tmp/glmark2data -b terrain:duration=20 2>&1 | tail -8', timeout=60)
print(result)

# 6. Voltaje sysfs
vdd_logic = sudo('cat /sys/class/regulator/regulator.2/microvolts')
print(f"\n=== vdd_logic post-bench: {vdd_logic} uV ({int(vdd_logic)/1000} mV)" if vdd_logic.isdigit() else f"\n  {vdd_logic}")

# 7. Temperatura
temp_raw = sudo('cat /sys/class/thermal/thermal_zone0/temp')
temp_c = int(temp_raw) // 1000 if temp_raw.isdigit() else '?'
print(f"  Temp post: {temp_c} C")

# 8. Restaurar governor
sudo('echo simple_ondemand > /sys/class/devfreq/ff400000.gpu/governor')
sudo('echo 600000000 > /sys/class/devfreq/ff400000.gpu/max_freq')
print("\n  Governor restaurado")

c.close()
