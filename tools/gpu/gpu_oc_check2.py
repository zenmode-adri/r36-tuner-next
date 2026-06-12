import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

cmds = {
    'gpu devfreq attrs':    'ls /sys/class/devfreq/ff400000.gpu/',
    'gpu devfreq all':      'for f in /sys/class/devfreq/ff400000.gpu/*; do echo "$f: $(cat $f 2>/dev/null)"; done',
    'clk_gpu_src debugfs':  'ls /sys/kernel/debug/clk/clk_gpu_src/ 2>/dev/null',
    'clk_gpu_src min_rate': 'cat /sys/kernel/debug/clk/clk_gpu_src/clk_min_rate 2>/dev/null || echo no-min',
    'clk_gpu_src max_rate': 'cat /sys/kernel/debug/clk/clk_gpu_src/clk_max_rate 2>/dev/null || echo no-max',
    'clk_gpu debugfs':      'ls /sys/kernel/debug/clk/clk_gpu/ 2>/dev/null',
    'clk_gpu max_rate':     'cat /sys/kernel/debug/clk/clk_gpu/clk_max_rate 2>/dev/null || echo no-max',
    'proc dt gpu-opp nodes':'ls /proc/device-tree/gpu-opp-table/ 2>/dev/null',
    'gpu opp hz values':    'for f in /proc/device-tree/gpu-opp-table/opp-*/opp-hz; do printf "%s: " "$f"; od -An -tu4 "$f" 2>/dev/null; done',
    'gpu avs-scale':        'od -An -tu4 /proc/device-tree/gpu-opp-table/rockchip,avs-scale 2>/dev/null || echo not-found',
    'gpu compatible':       'cat /proc/device-tree/gpu-opp-table/compatible 2>/dev/null | tr -d "\\0"',
}

for label, cmd in cmds.items():
    _, out, _ = c.exec_command('echo ark | sudo -S sh -c \'' + cmd + '\' 2>/dev/null')
    result = out.read().decode().strip()
    print(f'=== {label} ===')
    print(result or '(empty)')
    print()

c.close()
