import os
import sys
import time
import base64

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'deployment'))
from r36_ssh import get_client_with_retry

p = lambda *a: print(*a, flush=True)

# ── Extraer debs del script ────────────────────────────────────────────────────
p('Leyendo R36 Tuner.sh...')
script = open(os.path.join(ROOT, 'r36-tuner', 'R36 Tuner.sh'), 'r', encoding='utf-8', errors='replace').read().splitlines()
p(f'  {len(script)} lineas leidas')

def extract_section(lines, start_marker, end_marker):
    data = []
    inside = False
    for l in lines:
        if l == start_marker: inside = True; continue
        if l == end_marker: break
        if inside: data.append(l)
    return base64.b64decode(''.join(data))

p('Extrayendo glmark2 BIN...')
bin_deb = extract_section(script, '# __GLMARK2_BIN_START__', '# __GLMARK2_BIN_END__')
p(f'  BIN: {len(bin_deb):,} bytes')

p('Extrayendo glmark2 DATA...')
data_deb = extract_section(script, '# __GLMARK2_DATA_START__', '# __GLMARK2_DATA_END__')
p(f'  DATA: {len(data_deb):,} bytes')

bin_path  = os.path.join(ROOT, 'packages', 'glmark2', 'glmark2-bin.tmp.deb')
data_path = os.path.join(ROOT, 'packages', 'glmark2', 'glmark2-data.tmp.deb')
with open(bin_path,  'wb') as f: f.write(bin_deb)
with open(data_path, 'wb') as f: f.write(data_deb)
p('Debs guardados localmente.')

# ── Conectar ───────────────────────────────────────────────────────────────────
p('\nConectando SSH (con retries)...')
c = get_client_with_retry(retries=30, delay=5)
c.get_transport().set_keepalive(10)
p('  Conectado.')

# ── Helpers ────────────────────────────────────────────────────────────────────
def run(cmd, t=30):
    _, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    return out, err

def sudo(cmd, t=60):
    out, err = run(f'echo ark | sudo -S bash -c "{cmd}"', t)
    return out, err

def sudo_stream(cmd, t=120):
    p(f'  $ {cmd}')
    _, stdout, stderr = c.exec_command(f'echo ark | sudo -S bash -c "{cmd}"', timeout=t, get_pty=True)
    for line in iter(stdout.readline, ''):
        print('  ' + line.rstrip(), flush=True)

# ── Parar ES para liberar RAM antes del upload ────────────────────────────────
p('\nParando EmulationStation (libera RAM para el upload)...')
sudo('systemctl stop emulationstation 2>/dev/null; sleep 2; pkill -9 emulationstation 2>/dev/null || true', 15)
time.sleep(2)
o, _ = run('free -m | grep Mem')
p(f'  RAM: {o}')

# ── Transferir debs ────────────────────────────────────────────────────────────
p('\nTransfiriendo debs al R36...')
sftp = c.open_sftp()
p('  Subiendo glmark2-bin.deb...')
sftp.put(bin_path,  '/tmp/glmark2-bin.deb')
p(f'  OK ({len(bin_deb):,} bytes)')
sftp.close()
p('  Subiendo glmark2-data.deb (via stdin pipe)...')
stdin, stdout, stderr = c.exec_command('cat > /tmp/glmark2-data.deb', timeout=120)
with open(data_path, 'rb') as f:
    sent = 0
    while True:
        chunk = f.read(65536)
        if not chunk: break
        stdin.write(chunk)
        sent += len(chunk)
        if sent % (1024*1024) == 0:
            p(f'  {sent//1024//1024} MB / {len(data_deb)//1024//1024} MB...')
stdin.close()
stdout.read()
p(f'  OK ({len(data_deb):,} bytes)')

os.remove(bin_path)
os.remove(data_path)
p('  Archivos locales limpiados.')

# ── Instalar ───────────────────────────────────────────────────────────────────
p('\nInstalando glmark2-data (6 MB, puede tardar)...')
sudo_stream('dpkg -i /tmp/glmark2-data.deb', t=120)

p('\nInstalando glmark2-bin...')
sudo_stream('dpkg -i /tmp/glmark2-bin.deb', t=60)

o, _ = run('which glmark2-es2-drm')
p(f'\nglmark2 instalado en: {o}')
if not o:
    p('ERROR: glmark2 no encontrado tras instalacion. Abortando.')
    c.close()
    sys.exit(1)

# ── Test rapido (1 escena, 3 segundos) ────────────────────────────────────────
p('\nTest rapido glmark2 (3s build scene)...')
o, e = run('glmark2-es2-drm --off-screen --size 320x240 -b build:duration=3 2>&1', t=30)
p(o if o else '(sin output)')
if e: p('STDERR:', e)

# ── Restaurar DTB parcheado ───────────────────────────────────────────────────
p('\nVerificando DTBs...')
o, _ = run('ls -la /boot/rk3326-r36s-linux.dtb*')
p(o)

p('Restaurando DTB parcheado (.oc_patched -> activo)...')
sudo('cp /boot/rk3326-r36s-linux.dtb.oc_patched /boot/rk3326-r36s-linux.dtb')
sudo('sync && sync')
o, _ = run('ls -la /boot/rk3326-r36s-linux.dtb')
p(f'  DTB activo: {o}')

p('\nRebooteando para aplicar DTB OC...')
shell = c.invoke_shell()
time.sleep(0.5)
shell.send('echo ark | sudo -S reboot\n')
time.sleep(3)
c.close()
p('Reboot lanzado.')
p('\n=> Espera ~40s y corre bench_compare.py')
