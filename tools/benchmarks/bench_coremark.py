#!/usr/bin/env python3
"""
Coremark benchmark en R36S a 1008/1512/1608 MHz.
Coremark = estandar industria ARM embedded: list, matrix, state machine, CRC.
Mucho mas representativo de cargas reales (emulacion) que LCG MADD.

Uso: python -u bench_coremark.py
"""
import paramiko, time, threading

HOST, USER, PASS = '192.168.1.87', 'ark', 'ark'

# Archivos de Coremark que necesitamos del repo oficial
COREMARK_FILES = [
    'core_list_join.c',
    'core_matrix.c',
    'core_state.c',
    'core_util.c',
    'coremark.h',
    'core_main.c',
    'posix/core_portme.c',
    'posix/core_portme.h',
    'posix/core_portme_posix_overrides.h',
]
COREMARK_BASE = 'https://raw.githubusercontent.com/eembc/coremark/main/'

def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=22, username=USER, password=PASS)
    return c

def run(c, cmd, timeout=60):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    o = out.read().decode('utf-8', errors='replace').strip()
    e = err.read().decode('utf-8', errors='replace').strip()
    return o, e

def sudo(c, cmd, timeout=60):
    _, out, err = c.exec_command('echo ark | sudo -S ' + cmd, timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

def write_file(c, remote_path, content):
    if isinstance(content, str):
        content = content.encode()
    CHUNK = 524288
    for i, off in enumerate(range(0, len(content), CHUNK)):
        cmd = f'cat > {remote_path}' if i == 0 else f'cat >> {remote_path}'
        stdin3, stdout3, _ = c.exec_command(cmd)
        stdin3.write(content[off:off+CHUNK])
        stdin3.channel.shutdown_write()
        stdout3.read()

def set_freq(c, khz):
    sudo(c, f'bash -c "echo {khz} > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq"')
    sudo(c, f'bash -c "echo {khz} > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq"')
    sudo(c, 'bash -c "echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"')
    time.sleep(0.5)
    o, _ = run(c, 'cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq')
    print(f'  freq: {o.strip()} kHz')

def restore_freq(c):
    sudo(c, 'bash -c "echo ondemand > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"')

def compile_coremark(c):
    print('Transfiriendo Coremark (Windows -> device via SSH)...')
    _transfer_coremark_offline(c)

    print('Compilando...')
    compile_sh = r"""#!/bin/sh
cd /tmp/coremark
exec gcc -O2 -o /tmp/coremark_bin \
    core_main.c core_list_join.c core_matrix.c core_state.c core_util.c \
    posix/core_portme.c \
    -I. -Iposix \
    '-DFLAGS_STR="gcc -O2"' \
    -DITERATIONS=0 \
    -DPERFORMANCE_RUN=1 \
    -lrt
"""
    write_file(c, '/tmp/coremark_compile.sh', compile_sh)
    o3 = sudo(c, 'bash /tmp/coremark_compile.sh 2>&1', timeout=90)
    if o3:
        print(f'  gcc output: {o3[:400]}')

    o4, _ = run(c, 'test -x /tmp/coremark_bin && echo YES || echo NO')
    if 'YES' in o4:
        print('  Compilado OK -> /tmp/coremark_bin')
        return True
    else:
        print('  ERROR: no se creo el binario')
        return False

def _transfer_coremark_offline(c):
    import urllib.request
    print('  Descargando desde GitHub en Windows...')
    sudo(c, 'bash -c "rm -rf /tmp/coremark && mkdir -p /tmp/coremark/posix && chmod 777 /tmp/coremark /tmp/coremark/posix"')
    for fname in COREMARK_FILES:
        url = COREMARK_BASE + fname
        print(f'    {fname}...', end=' ', flush=True)
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                content = resp.read()
            dst = '/tmp/coremark/' + fname
            write_file(c, dst, content)
            print('OK')
        except Exception as e:
            print(f'FAIL: {e}')

def parse_coremark_output(output):
    itersec = None
    for line in output.split('\n'):
        if 'Iterations/Sec' in line:
            try:
                itersec = float(line.split()[-1])
            except:
                pass
        if 'CoreMark 1.0' in line and ':' in line:
            try:
                after_colon = line.split('CoreMark 1.0')[1].lstrip(' :')
                itersec = float(after_colon.split()[0])
            except:
                pass
    return itersec

def run_coremark(c, runs=3):
    results = []
    for i in range(runs):
        print(f'  run {i+1}/{runs}...', end=' ', flush=True)

        stop_event = threading.Event()
        c2 = connect()
        freq_samples = []
        temp_samples = []

        def monitor():
            while not stop_event.wait(timeout=2):
                try:
                    o2, _ = run(c2, 'cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq')
                    freq_samples.append(o2.strip())
                    t2, _ = run(c2, 'cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 0')
                    temp_samples.append(int(t2.strip() or 0) // 1000)
                except Exception:
                    break

        t = threading.Thread(target=monitor, daemon=True)
        t.start()

        o = sudo(c, '/tmp/coremark_bin 0x0 0x0 0x66 0', timeout=60)
        stop_event.set()
        t.join(timeout=6)
        c2.close()

        score = parse_coremark_output(o)
        if score:
            mhz_samples = sorted(set(freq_samples))
            temp_str = f'  temp={min(temp_samples)}-{max(temp_samples)}°C' if temp_samples else ''
            print(f'{score:.2f} iter/s  freqs={mhz_samples}{temp_str}')
            results.append({'score': score, 'freqs': mhz_samples, 'temps': temp_samples})
        else:
            print(f'\n  output:\n{o[:400]}')
    return results

def main():
    print('Conectando...')
    c = connect()
    print('OK')

    # Compilar si no existe
    o, _ = run(c, 'test -x /tmp/coremark_bin && echo YES || echo NO')
    if 'NO' in o:
        if not compile_coremark(c):
            c.close()
            return
    else:
        print('Coremark ya compilado en /tmp/coremark_bin')

    freqs = [
        (1008000, '1008 MHz'),
        (1512000, '1512 MHz'),
        (1608000, '1608 MHz'),
    ]

    all_results = {}
    for khz, label in freqs:
        print(f'\n{"="*50}')
        print(f'TEST: {label}')
        print(f'{"="*50}')
        set_freq(c, khz)
        time.sleep(1)
        r = run_coremark(c, runs=2)
        all_results[label] = r

    restore_freq(c)
    c.close()

    print(f'\n{"="*60}')
    print('RESUMEN COREMARK')
    print(f'{"="*60}')
    scores = {}
    for label in freqs:
        label = label[1]
        results = all_results.get(label, [])
        if results:
            vals = [r['score'] for r in results if 'score' in r]
            if vals:
                avg = sum(vals) / len(vals)
                mhz = int(label.split()[0])
                scores[label] = avg
                print(f'  {label}: {avg:.1f} iter/s  ({avg/mhz:.3f} CM/MHz)')

    print(f'\nScaling:')
    labels = [l[1] for l in freqs if l[1] in scores]
    for i in range(1, len(labels)):
        prev, curr = labels[i-1], labels[i]
        rate_diff = (scores[curr] - scores[prev]) / scores[prev] * 100
        mhz_prev = int(prev.split()[0])
        mhz_curr = int(curr.split()[0])
        clk_diff = (mhz_curr - mhz_prev) / mhz_prev * 100
        eff = rate_diff / clk_diff * 100 if clk_diff else 0
        print(f'  {prev} -> {curr}: {rate_diff:+.1f}% score  {clk_diff:+.1f}% clock  {eff:.0f}% eficiencia')

if __name__ == '__main__':
    main()
