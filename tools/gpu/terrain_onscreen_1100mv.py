import os
import paramiko, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark', timeout=10)

def sudo(cmd, timeout=90):
    _, out, _ = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

# Setup glmark2data
sudo('rm -rf /tmp/glmark2data')
sudo('mkdir -p /tmp/glmark2data/shaders')
sudo('ln -sf /usr/share/glmark2/models /tmp/glmark2data/models')
sudo('ln -sf /usr/share/glmark2/textures /tmp/glmark2data/textures')
sudo('cp /usr/share/glmark2/shaders/* /tmp/glmark2data/shaders/')
sudo(r'sed -i "s/MEDIUMP_OR_DEFAULT/mediump/g; s/HIGHP_OR_DEFAULT/highp/g" /tmp/glmark2data/shaders/*')

sftp = c.open_sftp()
sftp.put(os.path.join(ROOT, 'bin', 'glmark2-es2-drm-legacy'), '/tmp/glmark2-es2-drm-legacy')
sftp.close()
sudo('chmod +x /tmp/glmark2-es2-drm-legacy')

# Matar ES
print("Matando ES...")
sudo('systemctl stop emulationstation 2>/dev/null || pkill -x emulationstation 2>/dev/null || true')
time.sleep(2)

# Bloquear GPU 600 MHz
sudo('echo 600000000 > /sys/class/devfreq/ff400000.gpu/max_freq')
sudo('echo performance > /sys/class/devfreq/ff400000.gpu/governor')

vdd = sudo('cat /sys/class/regulator/regulator.2/microvolts')
print(f"vdd_logic: {vdd} uV ({int(vdd)/1000} mV)" if vdd.isdigit() else vdd)

print("Corriendo terrain ON-SCREEN (30s) — verifica pantalla...")
result = sudo('/tmp/glmark2-es2-drm-legacy --size 320x240 --data-path /tmp/glmark2data -b terrain:duration=30 2>&1 | tail -6', timeout=75)
print(result)

vdd2 = sudo('cat /sys/class/regulator/regulator.2/microvolts')
temp = sudo('cat /sys/class/thermal/thermal_zone0/temp')
temp_c = int(temp) // 1000 if temp.isdigit() else '?'
print(f"vdd_logic post: {vdd2} uV ({int(vdd2)/1000} mV)" if vdd2.isdigit() else vdd2)
print(f"Temp: {temp_c}C")

sudo('echo simple_ondemand > /sys/class/devfreq/ff400000.gpu/governor')
sudo('systemctl start emulationstation 2>/dev/null || true')
print("ES reiniciado")

c.close()
