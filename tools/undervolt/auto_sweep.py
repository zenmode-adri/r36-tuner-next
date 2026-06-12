import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'deployment'))
from r36_ssh import get_client_with_retry

HOST = '192.168.1.87'
DTB  = '/boot/rk3326-r36s-linux.dtb'
NODE = '/gpu-opp-table/opp-600000000'

def connect(retries=24, delay=5):
    print("  Esperando SSH", end='', flush=True)
    try:
        c = get_client_with_retry(retries=retries, delay=delay)
        print(" OK")
        return c
    except Exception:
        print(" TIMEOUT")
        return None

def sudo(c, cmd, timeout=90):
    _, out, _ = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

def setup_glmark(c):
    sudo(c, 'rm -rf /tmp/glmark2data')
    sudo(c, 'mkdir -p /tmp/glmark2data/shaders')
    sudo(c, 'ln -sf /usr/share/glmark2/models /tmp/glmark2data/models')
    sudo(c, 'ln -sf /usr/share/glmark2/textures /tmp/glmark2data/textures')
    sudo(c, 'cp /usr/share/glmark2/shaders/* /tmp/glmark2data/shaders/')
    sudo(c, r'sed -i "s/MEDIUMP_OR_DEFAULT/mediump/g; s/HIGHP_OR_DEFAULT/highp/g" /tmp/glmark2data/shaders/*')
    sftp = c.open_sftp()
    sftp.put(os.path.join(ROOT, 'bin', 'glmark2-es2-drm-legacy'), '/tmp/glmark2-es2-drm-legacy')
    sftp.close()
    sudo(c, 'chmod +x /tmp/glmark2-es2-drm-legacy')

def run_terrain_onscreen(c):
    sudo(c, 'systemctl stop emulationstation 2>/dev/null || pkill -x emulationstation 2>/dev/null || true')
    time.sleep(2)
    sudo(c, 'echo 600000000 > /sys/class/devfreq/ff400000.gpu/max_freq')
    sudo(c, 'echo performance > /sys/class/devfreq/ff400000.gpu/governor')
    result = sudo(c, '/tmp/glmark2-es2-drm-legacy --size 320x240 --data-path /tmp/glmark2data -b terrain:duration=30 2>&1 | tail -5', timeout=75)
    vdd  = sudo(c, 'cat /sys/class/regulator/regulator.2/microvolts')
    temp = sudo(c, 'cat /sys/class/thermal/thermal_zone0/temp')
    sudo(c, 'echo simple_ondemand > /sys/class/devfreq/ff400000.gpu/governor')
    sudo(c, 'systemctl start emulationstation 2>/dev/null || true')
    fps_line = [l for l in result.splitlines() if 'FPS:' in l]
    fps  = fps_line[0].split('FPS:')[1].split()[0] if fps_line else '0'
    temp_c = int(temp) // 1000 if temp.isdigit() else '?'
    vdd_mv = int(vdd) / 1000 if vdd.isdigit() else '?'
    return fps, vdd_mv, temp_c

def patch_and_reboot(c, uv):
    sudo(c, f'fdtput -t u {DTB} "{NODE}" opp-microvolt-L2 {uv}')
    sudo(c, f'fdtput -t u {DTB} "{NODE}" opp-microvolt {uv}')
    sudo(c, 'touch /boot/.r36_dtb_pending')
    v = sudo(c, f'fdtget -t u {DTB} "{NODE}" opp-microvolt-L2')
    print(f"  DTB -> {v} uV ({int(v)/1000} mV)" if v.isdigit() else v)
    shell = c.invoke_shell()
    time.sleep(0.5)
    shell.send("echo ark | sudo -S reboot\n")
    time.sleep(3)
    try: c.close()
    except: pass
    time.sleep(20)

# DTB ya en 1025 mV — empezamos ahi, luego 1012.5, 1000
voltages_uv = [1025000, 1012500, 1000000]
results = {}

c = connect()
if c is None:
    print("No se pudo conectar"); exit(1)

setup_glmark(c)

for i, uv in enumerate(voltages_uv):
    mv = uv / 1000
    print(f"\n{'='*48}")
    print(f">>> Probando {mv} mV — MIRA LA PANTALLA <<<")

    if i > 0:
        patch_and_reboot(c, uv)
        c = connect()
        if c is None:
            print(f"  NO BOOT a {mv} mV")
            results[mv] = 'NO-BOOT'
            break
        setup_glmark(c)

    fps, vdd_mv, temp = run_terrain_onscreen(c)
    print(f"  FPS: {fps} | vdd_logic: {vdd_mv} mV | Temp: {temp}C")

    if fps == '0' or fps == '?':
        results[mv] = 'FAIL (0 fps)'
        print("  FALLO — parando sweep")
        break
    else:
        results[mv] = f"{fps} fps, {temp}C"
        print(f"  Dime si habia artifacts en pantalla")

print("\n=== RESUMEN ===")
for mv, r in results.items():
    print(f"  {mv} mV: {r}")

try: c.close()
except: pass
