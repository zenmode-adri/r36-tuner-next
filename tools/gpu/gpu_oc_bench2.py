import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd, timeout=120):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode().strip()
    e = err.read().decode().strip()
    return o, e

def sudo(cmd, timeout=120):
    o, e = run(f'echo ark | sudo -S bash -c "{cmd}"', timeout=timeout)
    return o, e

# Setup glmark2data properly
print('=== Creating /tmp/glmark2data ===')
o, e = sudo('mkdir -p /tmp/glmark2data/shaders')
print(o, e)

o, e = sudo('cp /usr/share/glmark2/shaders/*.frag /usr/share/glmark2/shaders/*.vert /tmp/glmark2data/shaders/')
print('copy:', o or 'ok', e or '')

o, e = sudo(r"sed -i 's/MEDIUMP_OR_DEFAULT/mediump/g; s/HIGHP_OR_DEFAULT/highp/g' /tmp/glmark2data/shaders/*.frag /tmp/glmark2data/shaders/*.vert")
print('sed:', o or 'ok', e or '')

o, e = sudo('ln -sf /usr/share/glmark2/models /tmp/glmark2data/models; ln -sf /usr/share/glmark2/textures /tmp/glmark2data/textures')
print('links:', o or 'ok', e or '')

# Verify patch
o, _ = sudo('grep -c MEDIUMP_OR_DEFAULT /tmp/glmark2data/shaders/*.frag 2>/dev/null | grep -v ":0" | head -3')
print('MEDIUMP remaining:', o or 'none - good')

o, _ = sudo('ls /tmp/glmark2data/')
print('data dir:', o)

# Baseline at 520 MHz
print('\n=== Baseline terrain @ 520 MHz (15s) ===')
sudo('echo 520000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate')
o, e = sudo('/tmp/glmark2-es2-drm-legacy --off-screen --size 320x240 --data-path /tmp/glmark2data -b terrain:duration=15 2>&1 | tail -5', timeout=60)
print(o)

# OC to 600 MHz
print('\n=== OC terrain @ 600 MHz (15s) ===')
sudo('echo 600000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate')
o, e = sudo('cat /sys/kernel/debug/clk/clk_gpu/clk_rate')
print('clk confirmed:', o)
o, e = sudo('/tmp/glmark2-es2-drm-legacy --off-screen --size 320x240 --data-path /tmp/glmark2data -b terrain:duration=15 2>&1 | tail -5', timeout=60)
print(o)

# Restore
sudo('echo 520000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate')
print('\nRestored to 520 MHz')
c.close()
