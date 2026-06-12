import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark', timeout=10)

def sudo(cmd, timeout=15):
    _, out, _ = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

DTB  = '/boot/rk3326-r36s-linux.dtb'
NODE = '/gpu-opp-table/opp-600000000'

sudo(f'fdtput -t u {DTB} "{NODE}" opp-microvolt-L2 1025000')
sudo(f'fdtput -t u {DTB} "{NODE}" opp-microvolt 1025000')
sudo('rm -f /boot/.r36_dtb_pending')

v = sudo(f'fdtget -t u {DTB} "{NODE}" opp-microvolt-L2')
print(f"Restaurado: {v} uV ({int(v)/1000} mV)")
c.close()
