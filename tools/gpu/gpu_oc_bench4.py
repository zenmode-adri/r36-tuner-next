import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd, timeout=90):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    return out.read().decode().strip(), err.read().decode().strip()

def sudo(cmd, timeout=90):
    return run(f'echo ark | sudo -S bash -c \'{cmd}\'', timeout=timeout)

# Setup /tmp/glmark2data — exact copy of InstallGlmark2Legacy() logic
print('=== Setup glmark2data ===')
sudo('rm -rf /tmp/glmark2data')
sudo('mkdir -p /tmp/glmark2data/shaders')
sudo('ln -sf /usr/share/glmark2/models /tmp/glmark2data/models')
sudo('ln -sf /usr/share/glmark2/textures /tmp/glmark2data/textures')
sudo('cp /usr/share/glmark2/shaders/* /tmp/glmark2data/shaders/')
sudo(r'sed -i "s/MEDIUMP_OR_DEFAULT/mediump/g; s/HIGHP_OR_DEFAULT/highp/g" /tmp/glmark2data/shaders/*')

# Verify
o, _ = sudo('ls /tmp/glmark2data/ && grep -rl MEDIUMP_OR_DEFAULT /tmp/glmark2data/shaders/ | wc -l')
print('dir:', o)  # should show 0 remaining MEDIUMP files

# Baseline @ 520 MHz
print('\n=== terrain @ 520 MHz (15s) ===')
sudo('echo 520000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate')
o, e = sudo('/tmp/glmark2-es2-drm-legacy --off-screen --size 320x240 --data-path /tmp/glmark2data -b terrain:duration=15 2>&1 | tail -5', timeout=60)
print(o)

# OC @ 600 MHz
print('\n=== terrain @ 600 MHz (15s) ===')
sudo('echo 600000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate')
o, _ = sudo('cat /sys/kernel/debug/clk/clk_gpu/clk_rate')
print('clk confirmed:', o)
o, e = sudo('/tmp/glmark2-es2-drm-legacy --off-screen --size 320x240 --data-path /tmp/glmark2data -b terrain:duration=15 2>&1 | tail -5', timeout=60)
print(o)

# Restore
sudo('echo 520000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate')
print('\nRestored 520 MHz')

c.close()
