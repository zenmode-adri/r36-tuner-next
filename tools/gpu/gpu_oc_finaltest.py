import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def sudo(cmd, timeout=120):
    _, out, _ = c.exec_command(f'echo ark | sudo -S bash -c \'{cmd}\'', timeout=timeout)
    return out.read().decode().strip()

# Setup glmark2data
sudo('rm -rf /tmp/glmark2data')
sudo('mkdir -p /tmp/glmark2data/shaders')
sudo('ln -sf /usr/share/glmark2/models /tmp/glmark2data/models')
sudo('ln -sf /usr/share/glmark2/textures /tmp/glmark2data/textures')
sudo('cp /usr/share/glmark2/shaders/* /tmp/glmark2data/shaders/')
sudo(r'sed -i "s/MEDIUMP_OR_DEFAULT/mediump/g; s/HIGHP_OR_DEFAULT/highp/g" /tmp/glmark2data/shaders/*')

# Transfer binary
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sftp = c.open_sftp()
sftp.put(os.path.join(ROOT, 'bin', 'glmark2-es2-drm-legacy'), '/tmp/glmark2-es2-drm-legacy')
sftp.close()
sudo('chmod +x /tmp/glmark2-es2-drm-legacy')

CMD = '/tmp/glmark2-es2-drm-legacy --off-screen --size 320x240 --data-path /tmp/glmark2data -b terrain:duration=20 2>&1 | tail -5'

# Lock to 520 MHz baseline
print('=== Baseline @ 520 MHz (lock via max_freq) ===')
sudo('echo 520000000 > /sys/class/devfreq/ff400000.gpu/max_freq')
sudo('echo performance > /sys/class/devfreq/ff400000.gpu/governor')
print('cur_freq:', sudo('cat /sys/class/devfreq/ff400000.gpu/cur_freq'))
print(sudo(CMD, timeout=60))

# Unlock to 600 MHz
print('\n=== OC @ 600 MHz ===')
sudo('echo 600000000 > /sys/class/devfreq/ff400000.gpu/max_freq')
sudo('echo performance > /sys/class/devfreq/ff400000.gpu/governor')
print('cur_freq:', sudo('cat /sys/class/devfreq/ff400000.gpu/cur_freq'))
print(sudo(CMD, timeout=60))

# Restore governor
sudo('echo simple_ondemand > /sys/class/devfreq/ff400000.gpu/governor')
sudo('echo 600000000 > /sys/class/devfreq/ff400000.gpu/max_freq')

print('\n=== Temperature after test ===')
print(sudo('cat /sys/class/thermal/thermal_zone0/temp'))

c.close()
