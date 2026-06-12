import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def sudo(cmd, timeout=15):
    _, out, _ = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

print("=== scaling_available_frequencies ===")
freqs = sudo('cat /sys/devices/system/cpu/cpufreq/policy0/scaling_available_frequencies')
print(freqs)

if '1704000' in freqs:
    print("\n✅ 1704 MHz ACTIVO — clock driver lo soporta!")
    print("\n=== vdd_arm idle ===")
    print(sudo('cat /sys/class/regulator/regulator.3/microvolts'))
    print("\n=== Probar set 1704 MHz ===")
    sudo('echo 1704000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq')
    sudo('echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor')
    import time; time.sleep(1)
    cur = sudo('cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq')
    vdd = sudo('cat /sys/class/regulator/regulator.3/microvolts')
    print(f"  cur_freq  = {cur} kHz")
    print(f"  vdd_arm   = {int(vdd)//1000} mV")
    sudo('echo schedutil > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor')
    print("\nListo. Proceder con sweep de voltaje.")
else:
    print("\n❌ 1704 MHz NO aparece — clock driver no tiene esta tasa")
    print("El OPP fue ignorado. DTB seguro, no hay que revertir.")
    print("OPPs disponibles:", freqs)

c.close()
