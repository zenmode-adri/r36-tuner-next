import paramiko, io

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd, timeout=10):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode(errors='replace').strip()
    e = err.read().decode(errors='replace').strip()
    return o, e

# Test 1: r36overlay + ls (constructor fires?)
o, e = run('LD_PRELOAD=/usr/local/lib/libr36overlay.so ls / 2>&1 | head -5')
print(f'r36overlay + ls stderr+stdout: {repr(o)}')

# Test 2: does /tmp/r36overlay.log exist after?
o2, _ = run('ls -la /tmp/r36overlay.log 2>&1')
print(f'log file: {repr(o2)}')

# Test 3: tiny + ls for comparison
o3, e3 = run('LD_PRELOAD=/tmp/tiny.so ls / 2>&1 | head -3')
print(f'tiny + ls: {repr(o3)}')

# Test 4: r36overlay + ls, capture stderr separately
_, so, se = c.exec_command('LD_PRELOAD=/usr/local/lib/libr36overlay.so ls /')
out_data = so.read().decode(errors='replace').strip().split('\n')[:3]
err_data = se.read().decode(errors='replace').strip()
print(f'r36overlay + ls STDOUT: {repr(out_data)}')
print(f'r36overlay + ls STDERR: {repr(err_data)}')

c.close()
