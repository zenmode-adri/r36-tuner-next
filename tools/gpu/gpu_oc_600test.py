import paramiko, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd, timeout=120):
    _, out, err = c.exec_command('echo ark | sudo -S sh -c \'' + cmd + '\'', timeout=timeout)
    return out.read().decode().strip(), err.read().decode().strip()

# Current state
print('=== Current GPU state ===')
print(run('cat /sys/class/devfreq/ff400000.gpu/cur_freq /sys/class/devfreq/ff400000.gpu/max_freq')[0])

# Current vdd_logic voltage
print('\n=== vdd_logic voltage ===')
print(run('cat /sys/class/regulator/*/name /sys/class/regulator/*/voltage_now 2>/dev/null | paste - - | grep -i logic')[0])
# Alternative
print(run('for d in /sys/class/regulator/regulator.*/; do name=$(cat $d/name 2>/dev/null); v=$(cat $d/voltage_now 2>/dev/null); echo "$name: $v"; done | grep -i logic')[0])

# Force 600 MHz via clk debugfs
print('\n=== Force 600 MHz via debugfs ===')
r, e = run('echo 600000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate && cat /sys/kernel/debug/clk/clk_gpu/clk_rate')
print('clk_rate after write:', r)
print('cur_freq devfreq:', run('cat /sys/class/devfreq/ff400000.gpu/cur_freq')[0])

# Run terrain off-screen at 600 MHz
print('\n=== terrain @ 600 MHz (20s) ===')
bench_cmd = '/tmp/glmark2-es2-drm-legacy --off-screen --size 320x240 -b terrain:duration=20 2>&1 | tail -5'
r, _ = run(bench_cmd, timeout=60)
print(r)

# Restore to 520 MHz
run('echo 520000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate')
print('\n=== Restored to 520 MHz ===')
print(run('cat /sys/kernel/debug/clk/clk_gpu/clk_rate')[0])

c.close()
