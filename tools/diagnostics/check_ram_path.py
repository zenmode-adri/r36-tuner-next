import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd):
    _, out, err = c.exec_command(cmd, timeout=10)
    return (out.read() + err.read()).decode(errors='replace').strip()

print(run("find /sys/class/devfreq/ -name 'cur_freq' 2>/dev/null | xargs ls -la 2>/dev/null"))
print("---")
print(run("cat /sys/class/devfreq/ff400000.dmc/cur_freq 2>&1"))
print(run("ls /sys/class/devfreq/ 2>&1"))
c.close()
