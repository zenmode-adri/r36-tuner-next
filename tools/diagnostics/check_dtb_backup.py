import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def sudo(cmd, timeout=15):
    _, out, err = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

dtb      = '/boot/rk3326-r36s-linux.dtb'
bak      = '/boot/rk3326-r36s-linux.dtb.bak'
oc_patch = '/boot/rk3326-r36s-linux.dtb.oc_patched'

print("=== DTB files in /boot ===")
print(sudo(f'ls -lh {dtb} {bak} {oc_patch} 2>/dev/null || echo "(some missing)"'))

print("\n=== MD5 sums ===")
print(sudo(f'md5sum {dtb} {bak} {oc_patch} 2>/dev/null'))

print("\n=== avs-scale actual (1608 OPP presente?) ===")
print(sudo(f'fdtget -t u {dtb} /cpu0-opp-table rockchip,avs-scale 2>/dev/null'))

print("\n=== scaling_available_frequencies ===")
print(sudo('cat /sys/devices/system/cpu/cpufreq/policy0/scaling_available_frequencies'))

print("\n=== pending/booting flags ===")
print(sudo('ls -la /boot/.r36_* 2>/dev/null || echo "(ninguno)"'))

c.close()
