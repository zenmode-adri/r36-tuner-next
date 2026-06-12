import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd, timeout=120):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    return out.read().decode().strip()

# Use InstallGlmark2Legacy() from the script itself to set up /tmp/glmark2data
print('=== InstallGlmark2Legacy via script ===')
# Source the script and call the function (skip the TUI parts)
setup_cmd = '''bash -c 'source "/opt/system/R36 Tuner.sh" 2>/dev/null; InstallGlmark2Legacy; echo "exit:$?"' '''
r = run(f'echo ark | sudo -S {setup_cmd}', timeout=60)
print(r[-500:] if len(r) > 500 else r)

print('\n=== /tmp/glmark2data ok? ===')
r = run('ls /tmp/glmark2data/ && grep -c MEDIUMP /tmp/glmark2data/shaders/*.frag 2>/dev/null | grep -v ":0" | wc -l')
print(r)

# Baseline at 520 MHz
print('\n=== terrain @ 520 MHz (15s) ===')
run('echo ark | sudo -S bash -c "echo 520000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate"')
r = run('echo ark | sudo -S /tmp/glmark2-es2-drm-legacy --off-screen --size 320x240 --data-path /tmp/glmark2data -b terrain:duration=15 2>&1 | tail -5', timeout=60)
print(r)

# OC 600 MHz
print('\n=== terrain @ 600 MHz (15s) ===')
run('echo ark | sudo -S bash -c "echo 600000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate"')
r = run('echo ark | sudo -S bash -c "cat /sys/kernel/debug/clk/clk_gpu/clk_rate"')
print('clk confirmed:', r)
r = run('echo ark | sudo -S /tmp/glmark2-es2-drm-legacy --off-screen --size 320x240 --data-path /tmp/glmark2data -b terrain:duration=15 2>&1 | tail -5', timeout=60)
print(r)

# Restore
run('echo ark | sudo -S bash -c "echo 520000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate"')
print('\nRestored 520 MHz')
c.close()
