import paramiko, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def run(cmd):
    _, o, _ = c.exec_command('echo ark | sudo -S ' + cmd, timeout=10)
    return o.read().decode('utf-8', errors='replace').strip()

p = '/sys/class/devfreq/dmc'
print('governor:           ', run(f'cat {p}/governor'))
print('available_governors:', run(f'cat {p}/available_governors'))
print('cur_freq:           ', run(f'cat {p}/cur_freq'))
print('min_freq:           ', run(f'cat {p}/min_freq'))
print('max_freq:           ', run(f'cat {p}/max_freq'))
print('available_freq:     ', run(f'cat {p}/available_frequencies'))

# probar performance governor
print()
print('--- Probando performance governor ---')
run(f'bash -c "echo performance > {p}/governor"')
time.sleep(1)
print('governor post:  ', run(f'cat {p}/governor'))
print('cur_freq post:  ', run(f'cat {p}/cur_freq'))

# probar min=max=928
print()
print('--- Probando min=max=928000000 ---')
run(f'bash -c "echo dmc_ondemand > {p}/governor"')
run(f'bash -c "echo 928000000 > {p}/min_freq"')
run(f'bash -c "echo 928000000 > {p}/max_freq"')
time.sleep(1)
print('governor:  ', run(f'cat {p}/governor'))
print('min_freq:  ', run(f'cat {p}/min_freq'))
print('max_freq:  ', run(f'cat {p}/max_freq'))
print('cur_freq:  ', run(f'cat {p}/cur_freq'))

# restaurar
run(f'bash -c "echo 0 > {p}/min_freq"')
run(f'bash -c "echo 928000000 > {p}/max_freq"')
print()
print('Restaurado.')
c.close()
