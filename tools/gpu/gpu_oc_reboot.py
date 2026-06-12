import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd, timeout=30):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    return out.read().decode().strip(), err.read().decode().strip()

def sudo(cmd, timeout=30):
    return run(f'echo ark | sudo -S bash -c \'{cmd}\'', timeout=timeout)

DTB = '/boot/rk3326-r36s-linux.dtb'
GPU_OPP = '/gpu-opp-table'

# Add generic opp-microvolt (for non-L2 bins) — conservative 1150 mV
o, e = sudo(f'fdtput -t u {DTB} {GPU_OPP}/opp-600000000 opp-microvolt 1150000')
print('opp-microvolt generic:', o or 'ok', e or '')

# Verify full node
print('\n=== Final 600 MHz node ===')
for prop in ['opp-hz', 'opp-microvolt', 'opp-microvolt-L2']:
    o, _ = sudo(f'fdtget -t u {DTB} {GPU_OPP}/opp-600000000 {prop} 2>/dev/null || echo N/A')
    print(f'  {prop}: {o}')

# Touch DTB_PENDING flag (same as script does)
o, e = sudo('touch /boot/.r36_dtb_pending')
print('\nDTB_PENDING flag:', o or 'ok', e or '')

# Check if safety service already installed
o, _ = sudo('systemctl is-enabled r36-dtb-safety 2>/dev/null || echo not-installed')
print('r36-dtb-safety:', o)

# Reboot
print('\n=== Rebooting... ===')
c.exec_command('echo ark | sudo -S reboot')
c.close()
print('Reboot sent. Reconnect after ~30s to verify 600 MHz in devfreq.')
