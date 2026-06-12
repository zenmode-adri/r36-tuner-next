import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark', timeout=10)

def sudo(cmd, timeout=10):
    _, out, _ = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

dtb = sudo('fdtget -t u /boot/rk3326-r36s-linux.dtb /gpu-opp-table/opp-600000000 opp-microvolt-L2')
vdd = sudo('cat /sys/class/regulator/regulator.2/microvolts')
pending = sudo('ls /boot/.r36_dtb_pending 2>/dev/null && echo EXISTS || echo gone')

print(f"DTB opp-600MHz: {dtb} uV ({int(dtb)/1000} mV)" if dtb.isdigit() else f"DTB: {dtb}")
print(f"vdd_logic: {vdd} uV ({int(vdd)/1000} mV)" if vdd.isdigit() else f"vdd_logic: {vdd}")
print(f"DTB_PENDING: {pending}")

c.close()
