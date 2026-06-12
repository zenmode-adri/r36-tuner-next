#!/usr/bin/env python3
"""
Un paso del DMC UV sweep.
Uso: python dmc_uv_step.py <voltaje_uv_en_uV>
Ejemplo: python dmc_uv_step.py 1062500
"""
import paramiko, time, sys, threading

HOST, USER, PASS = '192.168.1.87', 'ark', 'ark'
DTB = '/boot/rk3326-r36s-linux.dtb'
NODE = '/dmc-opp-table/opp-928000000'
BIN_PROP = 'opp-microvolt-L2'
DTB_PENDING = '/boot/.r36_dtb_pending'

STRESS_C = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define BUF_MB 128
#define DURATION_S 30

int main(void) {
    size_t sz = BUF_MB * 1024 * 1024;
    char *a = malloc(sz);
    char *b = malloc(sz);
    if (!a || !b) { puts("malloc fail"); return 1; }

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long iters = 0;
    double elapsed = 0;

    while (elapsed < DURATION_S) {
        memset(a, (int)(iters & 0xff), sz);
        memcpy(b, a, sz);
        iters++;
        clock_gettime(CLOCK_MONOTONIC, &t1);
        elapsed = (t1.tv_sec - t0.tv_sec) + (t1.tv_nsec - t0.tv_nsec)*1e-9;
    }

    double mb = iters * BUF_MB * 2.0 / elapsed;
    printf("STABLE: %.0f MB/s over %.1fs (%lld iters)\n", mb, elapsed, iters);
    free(a); free(b);
    return 0;
}
"""

def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=22, username=USER, password=PASS)
    return c

def run(c, cmd, timeout=60):
    _, o, _ = c.exec_command(cmd, timeout=timeout)
    return o.read().decode('utf-8', errors='replace').strip()

def sudo(c, cmd, timeout=60):
    _, o, _ = c.exec_command('echo ark | sudo -S ' + cmd, timeout=timeout)
    return o.read().decode('utf-8', errors='replace').strip()

def write_file(c, path, data):
    if isinstance(data, str): data = data.encode()
    CHUNK = 524288
    for i, off in enumerate(range(0, len(data), CHUNK)):
        cmd = f'cat > {path}' if i == 0 else f'cat >> {path}'
        s, o, _ = c.exec_command(cmd)
        s.write(data[off:off+CHUNK]); s.channel.shutdown_write(); o.read()

def patch_and_reboot(volt_uv):
    print(f'Conectando para patch...')
    c = connect()
    print('OK')

    # leer voltaje actual
    cur = sudo(c, f'fdtget -t u {DTB} {NODE} {BIN_PROP} 2>/dev/null')
    print(f'  Voltaje actual: {cur} uV ({int(cur)//1000} mV)')
    print(f'  Voltaje nuevo:  {volt_uv} uV ({volt_uv//1000}.{(volt_uv%1000)//100*100//100 if volt_uv%1000 else 0} mV)')

    # patch
    sudo(c, f'fdtput -t u {DTB} {NODE} {BIN_PROP} {volt_uv}')
    sudo(c, f'fdtput -t u {DTB} {NODE} opp-microvolt {volt_uv}')
    sudo(c, 'sync')

    # verificar
    verify = sudo(c, f'fdtget -t u {DTB} {NODE} {BIN_PROP} 2>/dev/null')
    print(f'  Verificacion: {verify} uV')
    if str(volt_uv) not in verify:
        print('ERROR: patch no aplicado. Abortando.')
        c.close(); return False

    # safety flag
    sudo(c, f'touch {DTB_PENDING}')
    print(f'  Flag DTB_PENDING puesto.')
    print('Rebooteando...')

    shell = c.invoke_shell()
    time.sleep(0.5)
    shell.send('echo ark | sudo -S reboot\n')
    time.sleep(3)
    c.close()
    print()
    print('>> Activa WiFi/SSH en el device y avisa cuando este listo.')
    return True

def verify_and_stress():
    print('Conectando para verificar...')
    c = connect()
    print('OK')

    # check pending flag (si safety service actuo, .bak fue restaurado)
    pending = run(c, f'test -f {DTB_PENDING} && echo EXISTS || echo GONE')
    print(f'  DTB_PENDING: {pending}')
    if 'GONE' in pending:
        print('  ATENCION: flag borrado — safety service pudo haber actuado. Verificar DTB.')

    # voltaje activo en kernel
    volt_dtb = sudo(c, f'fdtget -t u {DTB} {NODE} {BIN_PROP} 2>/dev/null')
    print(f'  Voltaje en DTB activo: {volt_dtb} uV ({int(volt_dtb or 0)//1000} mV)')

    # compilar stress si no existe
    ok = run(c, 'test -x /tmp/dmc_stress && echo YES || echo NO')
    if 'NO' in ok:
        print('  Compilando stress RAM...')
        write_file(c, '/tmp/dmc_stress.c', STRESS_C)
        out = sudo(c, 'gcc -O2 -o /tmp/dmc_stress /tmp/dmc_stress.c -lrt 2>&1', timeout=30)
        if out: print(f'  gcc: {out}')

    # pinear DMC a 924 MHz
    p = '/sys/class/devfreq/dmc'
    sudo(c, f'bash -c "echo performance > {p}/governor"')
    sudo(c, f'bash -c "echo 928000000 > {p}/min_freq"')
    sudo(c, f'bash -c "echo 928000000 > {p}/max_freq"')
    time.sleep(0.5)
    dmc_cur = run(c, f'cat {p}/cur_freq')
    print(f'  DMC cur_freq: {dmc_cur} Hz')

    # stress 30s con monitor de temp
    print('  Corriendo stress RAM 30s...')
    stop = threading.Event()
    c2 = connect()
    temps = []

    def monitor():
        while not stop.wait(2):
            try:
                t = run(c2, 'cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null')
                if t: temps.append(int(t)//1000)
            except: break

    th = threading.Thread(target=monitor, daemon=True)
    th.start()

    result = sudo(c, '/tmp/dmc_stress', timeout=45)
    stop.set(); th.join(6); c2.close()

    print(f'  Resultado: {result}')
    if temps:
        print(f'  Temp: {min(temps)}-{max(temps)} C')

    # restaurar DMC
    sudo(c, f'bash -c "echo 0 > {p}/min_freq"')
    sudo(c, f'bash -c "echo 928000000 > {p}/max_freq"')
    sudo(c, f'bash -c "echo dmc_ondemand > {p}/governor"')

    stable = 'STABLE' in result
    print()
    if stable:
        print(f'>> ESTABLE a {volt_dtb} uV')
        print(f'>> Borrar flag: python dmc_uv_step.py clear')
        print(f'>> Siguiente paso: python dmc_uv_step.py {int(volt_dtb or 0) - 12500}')
    else:
        print('>> INESTABLE o crash — revertir a paso anterior.')

    c.close()

def clear_flag():
    c = connect()
    sudo(c, f'rm -f {DTB_PENDING}')
    print('Flag DTB_PENDING borrado.')
    c.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python dmc_uv_step.py <uV>|verify|clear')
        print('Ejemplo inicio: python dmc_uv_step.py 1062500')
        sys.exit(1)

    arg = sys.argv[1]
    if arg == 'verify':
        verify_and_stress()
    elif arg == 'clear':
        clear_flag()
    else:
        volt = int(arg)
        mv = volt / 1000
        print(f'=== DMC UV SWEEP: {mv} mV ===')
        patch_and_reboot(volt)
