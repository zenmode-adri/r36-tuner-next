import paramiko, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark', timeout=10)

def sudo(cmd, timeout=15):
    _, out, _ = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

DTB  = '/boot/rk3326-r36s-linux.dtb'
NODE = '/gpu-opp-table/opp-600000000'
NEW_UV = 1050000

sudo(f'fdtput -t u {DTB} "{NODE}" opp-microvolt-L2 {NEW_UV}')
sudo(f'fdtput -t u {DTB} "{NODE}" opp-microvolt {NEW_UV}')
sudo('touch /boot/.r36_dtb_pending')
v = sudo(f'fdtget -t u {DTB} "{NODE}" opp-microvolt-L2')
print(f"DTB -> {v} uV ({int(v)/1000} mV)" if v.isdigit() else v)

shell = c.invoke_shell()
time.sleep(0.5)
shell.send("echo ark | sudo -S reboot\n")
time.sleep(3)
c.close()
print("Rebooting...")
