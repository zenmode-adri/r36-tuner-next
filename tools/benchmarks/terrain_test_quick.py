import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'deployment'))
from r36_ssh import get_client

c = get_client()

def sudo(cmd, timeout=90):
    _, out, _ = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

print("Conectado OK")

# Verificar voltaje DTB
dtb_val = sudo('fdtget -t u /boot/rk3326-r36s-linux.dtb /gpu-opp-table/opp-600000000 opp-microvolt-L2')
print(f"DTB: {dtb_val} uV ({int(dtb_val)/1000} mV)" if dtb_val.isdigit() else f"DTB: {dtb_val}")

# Setup glmark2data
sudo('rm -rf /tmp/glmark2data')
sudo('mkdir -p /tmp/glmark2data/shaders')
sudo('ln -sf /usr/share/glmark2/models /tmp/glmark2data/models')
sudo('ln -sf /usr/share/glmark2/textures /tmp/glmark2data/textures')
sudo('cp /usr/share/glmark2/shaders/* /tmp/glmark2data/shaders/')
sudo(r'sed -i "s/MEDIUMP_OR_DEFAULT/mediump/g; s/HIGHP_OR_DEFAULT/highp/g" /tmp/glmark2data/shaders/*')
print("Shaders OK")

# Transferir binario
sftp = c.open_sftp()
sftp.put(os.path.join(ROOT, 'bin', 'glmark2-es2-drm-legacy'), '/tmp/glmark2-es2-drm-legacy')
sftp.close()
sudo('chmod +x /tmp/glmark2-es2-drm-legacy')

# Bloquear GPU 600 MHz
sudo('echo 600000000 > /sys/class/devfreq/ff400000.gpu/max_freq')
sudo('echo performance > /sys/class/devfreq/ff400000.gpu/governor')
print("GPU 600 MHz bloqueada")

# Terrain off-screen
print("Corriendo terrain off-screen (20s)...")
result = sudo('/tmp/glmark2-es2-drm-legacy --off-screen --size 320x240 --data-path /tmp/glmark2data -b terrain:duration=20 2>&1 | tail -5', timeout=60)
print(result)

vdd = sudo('cat /sys/class/regulator/regulator.2/microvolts')
temp = sudo('cat /sys/class/thermal/thermal_zone0/temp')
temp_c = int(temp) // 1000 if temp.isdigit() else '?'
print(f"vdd_logic: {vdd} uV ({int(vdd)/1000} mV)" if vdd.isdigit() else vdd)
print(f"Temp: {temp_c} C")

sudo('echo simple_ondemand > /sys/class/devfreq/ff400000.gpu/governor')
sudo('echo 600000000 > /sys/class/devfreq/ff400000.gpu/max_freq')
c.close()
