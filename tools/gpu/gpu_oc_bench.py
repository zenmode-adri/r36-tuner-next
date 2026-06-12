import paramiko, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd, timeout=120):
    _, out, err = c.exec_command('echo ark | sudo -S sh -c \'' + cmd + '\'', timeout=timeout)
    return out.read().decode().strip()

# Setup /tmp/glmark2data/ with patched shaders
print('=== Setting up glmark2data ===')
setup = '''
mkdir -p /tmp/glmark2data/shaders
cp /usr/share/glmark2/shaders/*.frag /usr/share/glmark2/shaders/*.vert /tmp/glmark2data/shaders/ 2>/dev/null
sed -i 's/MEDIUMP_OR_DEFAULT/mediump/g; s/HIGHP_OR_DEFAULT/highp/g' /tmp/glmark2data/shaders/*.frag /tmp/glmark2data/shaders/*.vert 2>/dev/null
ln -sf /usr/share/glmark2/models /tmp/glmark2data/models 2>/dev/null
ln -sf /usr/share/glmark2/textures /tmp/glmark2data/textures 2>/dev/null
ls /tmp/glmark2data/
'''
print(run(setup))

# Baseline at 520 MHz
print('\n=== Baseline terrain @ 520 MHz (15s) ===')
r = run('echo 520000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate && cat /sys/kernel/debug/clk/clk_gpu/clk_rate')
print('clk_rate:', r)
r = run('/tmp/glmark2-es2-drm-legacy --off-screen --size 320x240 --data-path /tmp/glmark2data -b terrain:duration=15 2>&1 | tail -5', timeout=60)
print(r)

# OC to 600 MHz
print('\n=== OC terrain @ 600 MHz (15s) ===')
r = run('echo 600000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate && cat /sys/kernel/debug/clk/clk_gpu/clk_rate')
print('clk_rate:', r)
r = run('/tmp/glmark2-es2-drm-legacy --off-screen --size 320x240 --data-path /tmp/glmark2data -b terrain:duration=15 2>&1 | tail -5', timeout=60)
print(r)

# Restore
print('\n=== Restore 520 MHz ===')
print(run('echo 520000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate && cat /sys/kernel/debug/clk/clk_gpu/clk_rate'))

c.close()
