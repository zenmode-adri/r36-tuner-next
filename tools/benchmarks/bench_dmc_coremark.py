#!/usr/bin/env python3
"""
Coremark a CPU 1608 MHz fija, DMC 786 MHz (stock) vs 924 MHz (OC).
Objetivo: confirmar si RAM es el bottleneck del techo Coremark a 1512/1608 MHz.

Uso: python -u bench_dmc_coremark.py
"""
import paramiko, time, threading

HOST, USER, PASS = '192.168.1.87', 'ark', 'ark'

def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=22, username=USER, password=PASS)
    return c

def run(c, cmd, timeout=60):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

def sudo(c, cmd, timeout=60):
    _, out, _ = c.exec_command('echo ark | sudo -S ' + cmd, timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

def set_cpu(c, khz):
    sudo(c, f'bash -c "echo {khz} > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq"')
    sudo(c, f'bash -c "echo {khz} > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq"')
    sudo(c, 'bash -c "echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"')
    time.sleep(0.5)
    cur = run(c, 'cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq')
    print(f'  CPU: {cur} kHz')

def set_dmc(c, hz):
    path = '/sys/class/devfreq/dmc'
    sudo(c, f'bash -c "echo performance > {path}/governor"')
    sudo(c, f'bash -c "echo {hz} > {path}/min_freq"')
    sudo(c, f'bash -c "echo {hz} > {path}/max_freq"')
    time.sleep(0.5)
    cur = run(c, f'cat {path}/cur_freq')
    print(f'  DMC cur={cur} Hz (target {hz})')

def restore(c):
    sudo(c, 'bash -c "echo ondemand > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"')
    path = '/sys/class/devfreq/dmc'
    avail = run(c, f'cat {path}/available_frequencies')
    max_hz = max(int(x) for x in avail.split()) if avail else 928000000
    sudo(c, f'bash -c "echo 0 > {path}/min_freq"')
    sudo(c, f'bash -c "echo {max_hz} > {path}/max_freq"')
    sudo(c, f'bash -c "echo dmc_ondemand > {path}/governor"')
    print(f'  Restaurado: CPU ondemand, DMC dmc_ondemand')

def parse_coremark(output):
    for line in output.split('\n'):
        if 'Iterations/Sec' in line:
            try: return float(line.split()[-1])
            except: pass
        if 'CoreMark 1.0' in line and ':' in line:
            try:
                part = line.split('CoreMark 1.0')[1].lstrip(' :')
                return float(part.split()[0])
            except: pass
    return None

def run_coremark(c, runs=3, label=''):
    results = []
    for i in range(runs):
        print(f'  [{label}] run {i+1}/{runs}...', end=' ', flush=True)

        stop = threading.Event()
        c2 = connect()
        temps = []

        def monitor():
            while not stop.wait(timeout=2):
                try:
                    t = run(c2, 'cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 0')
                    temps.append(int(t or 0) // 1000)
                except: break

        th = threading.Thread(target=monitor, daemon=True)
        th.start()

        o = sudo(c, '/tmp/coremark_bin 0x0 0x0 0x66 0', timeout=60)
        stop.set()
        th.join(timeout=6)
        c2.close()

        score = parse_coremark(o)
        if score:
            temp_str = f'  {min(temps)}-{max(temps)}°C' if temps else ''
            print(f'{score:.2f} iter/s{temp_str}')
            results.append(score)
        else:
            print(f'FAIL\n  output: {o[:300]}')
    return results

def main():
    print('Conectando...')
    c = connect()
    print('OK')

    # Verificar Coremark compilado
    ok = run(c, 'test -x /tmp/coremark_bin && echo YES || echo NO')
    if 'NO' in ok:
        print('ERROR: /tmp/coremark_bin no existe. Correr bench_coremark.py primero para compilarlo.')
        c.close()
        return

    # Verificar DMC disponible
    avail = run(c, 'cat /sys/class/devfreq/dmc/available_frequencies 2>/dev/null')
    if not avail:
        print('ERROR: no se puede leer DMC devfreq.')
        c.close()
        return
    print(f'DMC available: {avail}')

    print(f'\nCPU fija a 1608 MHz durante todo el test.')

    tests = [
        (786000000, '786 MHz (stock)'),
        (928000000, '928 MHz (OC)'),
    ]

    all_scores = {}

    try:
        set_cpu(c, 1608000)

        for hz, label in tests:
            print(f'\n{"="*50}')
            print(f'DMC {label}')
            print(f'{"="*50}')
            set_dmc(c, hz)
            time.sleep(1)
            scores = run_coremark(c, runs=3, label=label)
            all_scores[label] = scores

    finally:
        restore(c)
        c.close()

    print(f'\n{"="*60}')
    print('RESULTADO: Coremark @ CPU 1608 MHz')
    print(f'{"="*60}')
    for label, scores in all_scores.items():
        if scores:
            avg = sum(scores) / len(scores)
            print(f'  DMC {label}: {avg:.1f} iter/s  (runs: {[f"{s:.1f}" for s in scores]})')

    if len(all_scores) == 2:
        labels = list(all_scores.keys())
        s1 = sum(all_scores[labels[0]]) / len(all_scores[labels[0]])
        s2 = sum(all_scores[labels[1]]) / len(all_scores[labels[1]])
        delta = (s2 - s1) / s1 * 100
        print(f'\n  Delta 786->928 MHz: {delta:+.1f}%')
        if abs(delta) < 2:
            print('  -> RAM NO es el bottleneck de Coremark (latencia L2/L1, no bandwidth)')
        elif delta > 2:
            print('  -> RAM SI contribuye al bottleneck de Coremark')
        else:
            print('  -> DMC OC empeora rendimiento (timing tables suboptimas)')

if __name__ == '__main__':
    main()
