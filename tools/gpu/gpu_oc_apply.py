import paramiko, struct

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
BIN_PROP = 'opp-microvolt-L2'
VOLT_UV = 1150000  # max PMIC vdd_logic

# 1. Inspect existing OPP nodes
print('=== Existing GPU OPP node properties (opp-520000000) ===')
o, _ = sudo(f'fdtget -l {DTB} {GPU_OPP}/opp-520000000')
print(o)

print('\n=== opp-520000000 values ===')
for prop in ['opp-hz', 'opp-microvolt', 'opp-microvolt-L0', 'opp-microvolt-L1', 'opp-microvolt-L2', 'opp-microvolt-L3']:
    o, _ = sudo(f'fdtget -t u {DTB} {GPU_OPP}/opp-520000000 {prop} 2>/dev/null || echo N/A')
    print(f'  {prop}: {o}')

print('\n=== rockchip,max-volt decoded ===')
o, _ = sudo(f'python3 -c "import struct; d=open(\'{DTB}\',\'rb\').read(); idx=d.find(b\'opp-600\'); print(idx)"')
# Just read via fdtget
o, _ = sudo(f'fdtget -t u {DTB} {GPU_OPP} rockchip,max-volt 2>/dev/null || echo N/A')
print('max-volt (uV):', o)

# 2. Check backup
print('\n=== Backup status ===')
o, _ = sudo(f'ls -lh {DTB}.bak 2>/dev/null || echo NO BACKUP')
print(o)

# 3. Check if opp-600000000 already exists
print('\n=== 600 MHz node exists? ===')
o, _ = sudo(f'fdtget {DTB} {GPU_OPP}/opp-600000000 opp-hz 2>/dev/null && echo YES || echo NO')
print(o)

# 4. Apply patch
print('\n=== Applying GPU OC 600 MHz @ 1150 mV ===')

# Create node
o, e = sudo(f'fdtput -c {DTB} {GPU_OPP}/opp-600000000')
print('create node:', o or 'ok', e or '')

# opp-hz 64-bit: high=0, low=600000000
o, e = sudo(f'fdtput -t u {DTB} {GPU_OPP}/opp-600000000 opp-hz 0 600000000')
print('opp-hz:', o or 'ok', e or '')

# Voltage — check if single value or multi
# GPU uses single u32 (not 3-tuple like CPU) based on opp-research.md
o, e = sudo(f'fdtput -t u {DTB} {GPU_OPP}/opp-600000000 {BIN_PROP} {VOLT_UV}')
print(f'{BIN_PROP}:', o or 'ok', e or '')

# Verify
print('\n=== Verify new node ===')
o, _ = sudo(f'fdtget -t u {DTB} {GPU_OPP}/opp-600000000 opp-hz')
print('opp-hz:', o)
o, _ = sudo(f'fdtget -t u {DTB} {GPU_OPP}/opp-600000000 {BIN_PROP}')
print(f'{BIN_PROP}:', o)

# List all nodes
o, _ = sudo(f'fdtget -l {DTB} {GPU_OPP} | grep opp-')
print('all gpu opps:', o)

print('\n=== Ready to reboot? Check above then reboot manually. ===')
print('If OK: echo ark | sudo -S reboot')

c.close()
