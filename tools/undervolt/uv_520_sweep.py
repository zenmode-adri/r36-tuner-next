import os
"""
Sweep autónomo: bajar voltaje SOLO del OPP 520 MHz de la GPU.
Test on-screen (terrain 30s) con glmark2-legacy.
Detecta crash por fps=0, timeout, o no-boot.
Al acabar, restaura automáticamente al último voltaje estable.

Estado inicial: 1087.5 mV (estable, -12.5 mV UV uniforme stock).
Primer paso: 1075 mV → bajar de 12.5 en 12.5 mV.
"""

import paramiko, time, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

HOST     = '192.168.1.87'
DTB      = '/boot/rk3326-r36s-linux.dtb'
NODE_520 = '/gpu-opp-table/opp-520000000'
GLMARK   = os.path.join(ROOT, 'bin', 'glmark2-es2-drm-legacy')

START_UV      = 1075000   # primer paso (1087.5 ya OK)
STEP_UV       = 12500     # paso 12.5 mV
STOP_UV       = 950000    # floor PMIC vdd_logic
KNOWN_GOOD_UV = 1087500   # fallback si todo falla
TERRAIN_DUR   = 30        # segundos por test


# ── SSH ──────────────────────────────────────────────────

def connect(retries=40, delay=5):
    print("  Esperando SSH", end='', flush=True)
    for _ in range(retries):
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(HOST, port=22, username='ark', password='ark', timeout=5)
            print(" OK", flush=True)
            return c
        except Exception:
            print(".", end='', flush=True)
            time.sleep(delay)
    print(" TIMEOUT", flush=True)
    return None

def sudo(c, cmd, timeout=90):
    _, out, _ = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'")
    out.channel.settimeout(timeout)
    try:
        return out.read().decode('utf-8', errors='replace').strip()
    except Exception:
        return ''


# ── glmark2 ──────────────────────────────────────────────

def setup_glmark(c):
    print("  setup glmark2...", end='', flush=True)
    sudo(c, 'rm -rf /tmp/glmark2data')
    sudo(c, 'mkdir -p /tmp/glmark2data/shaders')
    sudo(c, 'ln -sf /usr/share/glmark2/models   /tmp/glmark2data/models')
    sudo(c, 'ln -sf /usr/share/glmark2/textures /tmp/glmark2data/textures')
    sudo(c, 'cp /usr/share/glmark2/shaders/* /tmp/glmark2data/shaders/')
    sudo(c, r'sed -i "s/MEDIUMP_OR_DEFAULT/mediump/g; s/HIGHP_OR_DEFAULT/highp/g" /tmp/glmark2data/shaders/*')
    sftp = c.open_sftp()
    sftp.put(GLMARK, '/tmp/glmark2-es2-drm-legacy')
    sftp.close()
    sudo(c, 'chmod +x /tmp/glmark2-es2-drm-legacy')
    print(" OK", flush=True)

def terrain_onscreen(c):
    """
    Para ES, fuerza GPU a 520 MHz, corre terrain on-screen 30s.
    Devuelve (fps: float, vdd_mv: float, temp_c: int).
    fps=0 → crash/hang.
    """
    sudo(c, 'systemctl stop emulationstation 2>/dev/null || pkill -x emulationstation 2>/dev/null || true')
    time.sleep(2)

    # Forzar 520 MHz (NO 600 MHz OC)
    sudo(c, 'echo performance            > /sys/class/devfreq/ff400000.gpu/governor')
    sudo(c, 'echo 520000000              > /sys/class/devfreq/ff400000.gpu/max_freq')

    time.sleep(1)
    cur_freq = sudo(c, 'cat /sys/class/devfreq/ff400000.gpu/cur_freq')
    print(f"  cur_freq={cur_freq} Hz", flush=True)

    raw = sudo(c,
        f'/tmp/glmark2-es2-drm-legacy --size 320x240 --data-path /tmp/glmark2data'
        f' -b terrain:duration={TERRAIN_DUR} 2>&1 | tail -12',
        timeout=TERRAIN_DUR + 45)

    vdd  = sudo(c, 'cat /sys/class/regulator/regulator.2/microvolts')
    temp = sudo(c, 'cat /sys/class/thermal/thermal_zone0/temp')

    # Restaurar GPU a OC normal
    sudo(c, 'echo simple_ondemand > /sys/class/devfreq/ff400000.gpu/governor')
    sudo(c, 'echo 600000000       > /sys/class/devfreq/ff400000.gpu/max_freq')
    sudo(c, 'systemctl start emulationstation 2>/dev/null || true')

    fps_lines = [l for l in raw.splitlines() if 'FPS:' in l]
    fps   = float(fps_lines[0].split('FPS:')[1].split()[0]) if fps_lines else 0.0
    vdd_mv = round(int(vdd) / 1000, 1) if vdd.isdigit() else -1
    temp_c = int(temp) // 1000 if temp.isdigit() else -1
    return fps, vdd_mv, temp_c


# ── DTB ──────────────────────────────────────────────────

def patch(c, uv):
    """Parcha SOLO opp-520000000. Escribe 3 valores (min typ max)."""
    vals = f'{uv} {uv} {uv}'
    sudo(c, f'fdtput -t u {DTB} "{NODE_520}" opp-microvolt-L2 {vals}')
    sudo(c, f'fdtput -t u {DTB} "{NODE_520}" opp-microvolt     {vals}')
    sudo(c, 'touch /boot/.r36_dtb_pending')
    v = sudo(c, f'fdtget -t u {DTB} "{NODE_520}" opp-microvolt-L2')
    print(f"  DTB L2 -> [{v}]", flush=True)

def reboot_device(c):
    shell = c.invoke_shell()
    time.sleep(0.5)
    shell.send("echo ark | sudo -S reboot\n")
    time.sleep(3)
    try: c.close()
    except: pass
    time.sleep(28)   # esperar kernel + systemd

def restore_and_reboot(last_good_uv, reason=''):
    print(f"\n  Restaurando a {last_good_uv/1000} mV ({reason})...", flush=True)
    c2 = connect()
    if c2 is None:
        print("  No se pudo conectar para restaurar — restaura manualmente", flush=True)
        return
    patch(c2, last_good_uv)
    reboot_device(c2)
    c3 = connect()
    if c3:
        print(f"  Restaurado OK — dispositivo en {last_good_uv/1000} mV", flush=True)
        try: c3.close()
        except: pass
    else:
        print("  Dispositivo no responde tras restaurar", flush=True)


# ── MAIN ─────────────────────────────────────────────────

c = connect()
if c is None:
    print("Sin conexión al R36"); sys.exit(1)

cur_raw = sudo(c, f'fdtget -t u {DTB} "{NODE_520}" opp-microvolt-L2')
print(f"opp-520000000 L2 actual en DTB: [{cur_raw}]")
setup_glmark(c)

voltages = list(range(START_UV, STOP_UV - 1, -STEP_UV))
print(f"\nPlan sweep: {[v/1000 for v in voltages]} mV")
print(f"(1087.5 mV ya confirmado STABLE — empezamos en {START_UV/1000} mV)\n")

header = f"{'mV':>10} | {'FPS':>5} | {'vdd_logic':>10} | {'Temp':>6} | Estado"
sep    = "-" * 56
print(header)
print(sep)

results    = {}
last_good  = KNOWN_GOOD_UV
crashed    = False

for uv in voltages:
    mv = uv / 1000
    print(f"\n>>> Patcheando {mv} mV...", flush=True)
    patch(c, uv)
    reboot_device(c)

    c = connect()
    if c is None:
        print(f"{mv:>10} | {'---':>5} | {'---':>10} | {'---':>6} | NO-BOOT (panic)")
        results[mv] = 'NO-BOOT'
        crashed = True
        break

    setup_glmark(c)
    fps, vdd_mv, temp_c = terrain_onscreen(c)

    if fps < 5:
        estado = 'CRASH'
        print(f"{mv:>10} | {fps:>5.1f} | {vdd_mv:>10} | {temp_c:>5}C | {estado}")
        results[mv] = f'CRASH ({fps:.0f}fps)'
        crashed = True
        break
    elif fps < 14:
        estado = 'LOW'
        print(f"{mv:>10} | {fps:>5.1f} | {vdd_mv:>10} | {temp_c:>5}C | {estado} (sospechoso)")
        results[mv] = f'{fps:.0f}fps | {temp_c}C | LOW'
        last_good = uv
    else:
        estado = 'STABLE'
        last_good = uv
        print(f"{mv:>10} | {fps:>5.1f} | {vdd_mv:>10} | {temp_c:>5}C | {estado}")
        results[mv] = f'{fps:.0f}fps | {temp_c}C'

try: c.close()
except: pass

# Restaurar si hubo crash (quedarse en el último bueno)
if crashed:
    restore_and_reboot(last_good, reason=f'último estable')

# Tabla final
print(f"\n{'='*56}")
print("RESUMEN — GPU 520 MHz voltage sweep (on-screen terrain)")
print(f"{'='*56}")
print(f"  Referencia: 1087.5 mV = STABLE (confirmado prev.)")
print(header)
print(sep)
ref_mv = 1087.5
print(f"{ref_mv:>10} | {'15':>5} | {'---':>10} | {'---':>6} | STABLE (baseline)")
for mv, r in results.items():
    print(f"{mv:>10} | {r}")
print(sep)
if results:
    stable_mvs = [mv for mv, r in results.items() if 'STABLE' in r or ('fps' in r and 'CRASH' not in r and 'NO-BOOT' not in r)]
    if stable_mvs:
        floor = min(stable_mvs)
        print(f"  Floor estable este chip: {floor} mV")
        print(f"  UV total vs stock (1100 mV): -{1100 - floor:.1f} mV")
    crashed_mvs = [mv for mv, r in results.items() if 'CRASH' in r or 'NO-BOOT' in r]
    if crashed_mvs:
        print(f"  Primer fallo: {min(crashed_mvs)} mV")
print(f"{'='*56}")
