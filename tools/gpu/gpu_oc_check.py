import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

cmds = {
    'devfreq avail freqs': 'find /sys/class/devfreq -name available_frequencies 2>/dev/null | xargs -I{} sh -c "echo {}; cat {}"',
    'debugfs clk gpu':     'ls /sys/kernel/debug/clk/ 2>/dev/null | grep -i gpu',
    'clk summary gpu':     'cat /sys/kernel/debug/clk/clk_summary 2>/dev/null | grep -i gpu',
    'gpu devfreq path':    'ls /sys/class/devfreq/ 2>/dev/null',
    'gpu cur max freq':    'cat /sys/class/devfreq/*/cur_freq /sys/class/devfreq/*/max_freq 2>/dev/null',
    'dmesg gpu opp':       'dmesg 2>/dev/null | grep -iE "gpu|mali|opp" | grep -v "^\[" | head -20',
    'dmesg gpu opp2':      'dmesg 2>/dev/null | grep -iE "gpu.*opp|opp.*gpu|mali.*freq|gpu.*freq" | head -20',
}

for label, cmd in cmds.items():
    _, out, _ = c.exec_command('echo ark | sudo -S sh -c \'' + cmd + '\' 2>/dev/null')
    result = out.read().decode().strip()
    print(f'=== {label} ===')
    print(result or '(empty)')
    print()

c.close()
