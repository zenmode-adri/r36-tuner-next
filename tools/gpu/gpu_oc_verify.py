import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def sudo(cmd, timeout=30):
    _, out, _ = c.exec_command(f'echo ark | sudo -S bash -c \'{cmd}\'', timeout=timeout)
    return out.read().decode().strip()

print('=== GPU available_frequencies ===')
print(sudo('cat /sys/class/devfreq/ff400000.gpu/available_frequencies'))

print('\n=== GPU max_freq ===')
print(sudo('cat /sys/class/devfreq/ff400000.gpu/max_freq'))

print('\n=== DTB pending flag ===')
print(sudo('ls /boot/.r36_dtb_pending 2>/dev/null && echo EXISTS || echo CLEARED'))

print('\n=== dmesg GPU OPP ===')
print(sudo('dmesg | grep -i "gpu.*opp\|opp.*gpu\|600000000\|mali.*freq" | head -10'))

c.close()
