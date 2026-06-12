import paramiko, struct

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

cmds = {
    'gpll rate':            'cat /sys/kernel/debug/clk/gpll/clk_rate 2>/dev/null',
    'cpll rate':            'cat /sys/kernel/debug/clk/cpll/clk_rate 2>/dev/null',
    'npll rate':            'cat /sys/kernel/debug/clk/npll/clk_rate 2>/dev/null',
    'all pll rates':        'for pll in gpll cpll npll usb480m; do r=$(cat /sys/kernel/debug/clk/$pll/clk_rate 2>/dev/null); echo "$pll: $r"; done',
    'gpu possible parents': 'cat /sys/kernel/debug/clk/clk_gpu_src/clk_possible_parents 2>/dev/null',
    'gpu max-volt decoded': 'python3 -c "import struct; d=open(\'/proc/device-tree/gpu-opp-table/rockchip,max-volt\',\'rb\').read(); print(struct.unpack(\'>I\',d[:4])[0])" 2>/dev/null',
    'pvtm-voltage-sel':     'od -An -tu4 /proc/device-tree/gpu-opp-table/rockchip,pvtm-voltage-sel 2>/dev/null | head -5',
    'gpu opp voltages L2':  'for f in /proc/device-tree/gpu-opp-table/opp-*/opp-microvolt-L2; do printf "%s: " "$f"; python3 -c "import struct; d=open(\'$f\',\'rb\').read(); print([struct.unpack(\'>I\',d[i:i+4])[0] for i in range(0,len(d),4)])" 2>/dev/null; done',
    # Try to force 600MHz via clk debugfs
    'clk_gpu force 600':    'echo 600000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate 2>&1; cat /sys/kernel/debug/clk/clk_gpu/clk_rate',
}

for label, cmd in cmds.items():
    _, out, _ = c.exec_command('echo ark | sudo -S sh -c \'' + cmd + '\' 2>/dev/null')
    result = out.read().decode().strip()
    print(f'=== {label} ===')
    print(result or '(empty)')
    print()

# Restore
c.exec_command('echo 400000000 > /sys/kernel/debug/clk/clk_gpu/clk_rate 2>/dev/null')
c.close()
