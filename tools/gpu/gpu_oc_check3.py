import paramiko, struct

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

cmds = {
    'gpu max-volt':         'od -An -tu4 /proc/device-tree/gpu-opp-table/rockchip,max-volt 2>/dev/null',
    'clk_gpu_src parent':   'cat /sys/kernel/debug/clk/clk_gpu_src/clk_parent 2>/dev/null || cat /sys/kernel/debug/clk/clk_gpu_src/clk_possible_parents 2>/dev/null',
    'clk_gpu_src rate':     'cat /sys/kernel/debug/clk/clk_gpu_src/clk_rate 2>/dev/null',
    'clk_gpu rate':         'cat /sys/kernel/debug/clk/clk_gpu/clk_rate 2>/dev/null',
    'gpu write 600 test':   'echo 600000000 | sudo tee /sys/class/devfreq/ff400000.gpu/max_freq 2>&1; cat /sys/class/devfreq/ff400000.gpu/max_freq',
    'gpu write 600 cur':    'echo 600000000 | sudo tee /sys/class/devfreq/ff400000.gpu/max_freq 2>&1 && echo 600000000 | sudo tee /sys/class/devfreq/ff400000.gpu/min_freq 2>&1; cat /sys/class/devfreq/ff400000.gpu/cur_freq',
}

for label, cmd in cmds.items():
    _, out, _ = c.exec_command('echo ark | sudo -S sh -c \'' + cmd + '\' 2>/dev/null')
    result = out.read().decode().strip()
    print(f'=== {label} ===')
    print(result or '(empty)')
    print()

# Restore GPU max freq
c.exec_command('echo 520000000 | sudo tee /sys/class/devfreq/ff400000.gpu/max_freq > /dev/null 2>&1')
c.exec_command('echo 400000000 | sudo tee /sys/class/devfreq/ff400000.gpu/min_freq > /dev/null 2>&1')
c.close()
