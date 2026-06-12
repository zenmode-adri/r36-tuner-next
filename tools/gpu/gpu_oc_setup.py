import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'deployment'))
from r36_ssh import get_client

c = get_client()

def run(cmd, timeout=30):
    _, out, err = c.exec_command('echo ark | sudo -S sh -c \'' + cmd + '\'', timeout=timeout)
    return out.read().decode().strip()

# Check what glmark2 is available
print('=== glmark2 binaries on device ===')
print(run('which glmark2-es2-drm 2>/dev/null || echo not-in-path; ls /usr/bin/glmark2* 2>/dev/null; ls /tmp/glmark2* 2>/dev/null'))

print('\n=== /usr/share/glmark2 exists? ===')
print(run('ls /usr/share/glmark2/shaders/ 2>/dev/null | head -5 || echo not-found'))

print('\n=== /tmp/glmark2data exists? ===')
print(run('ls /tmp/glmark2data/shaders/ 2>/dev/null | head -5 || echo not-found'))

# Transfer legacy binary from repo
local_bin = os.path.join(ROOT, 'bin', 'glmark2-es2-drm-legacy')
if os.path.exists(local_bin):
    print(f'\n=== Transferring {os.path.getsize(local_bin)} bytes binary ===')
    sftp = c.open_sftp()
    sftp.put(local_bin, '/tmp/glmark2-es2-drm-legacy')
    sftp.close()
    print(run('chmod +x /tmp/glmark2-es2-drm-legacy && ls -lh /tmp/glmark2-es2-drm-legacy'))
else:
    print(f'\nBinary not found at {local_bin}')

c.close()
