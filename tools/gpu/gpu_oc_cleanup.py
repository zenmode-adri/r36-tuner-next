import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def sudo(cmd, timeout=15):
    _, out, _ = c.exec_command(f'echo ark | sudo -S bash -c \'{cmd}\'', timeout=timeout)
    return out.read().decode().strip()

print(sudo('rm -f /boot/.r36_dtb_pending && echo flag cleared'))
c.close()
