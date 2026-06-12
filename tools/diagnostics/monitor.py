import paramiko, time, sys

HOST, USER, PASS = '192.168.1.87', 'ark', 'ark'

def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=22, username=USER, password=PASS, timeout=10)
    return c

def run(c, cmd):
    _, out, _ = c.exec_command(cmd, timeout=5)
    return out.read().decode().strip()

print("Conectando...")
try:
    c = connect()
    print("Conectado. Ctrl+C para salir.\n")
except Exception as e:
    print(f"No hay SSH: {e}")
    sys.exit(1)

while True:
    try:
        temp = int(run(c, 'cat /sys/class/thermal/thermal_zone0/temp')) // 1000
        cpu  = run(c, 'cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq')
        gpu  = run(c, 'cat /sys/class/devfreq/ff400000.gpu/cur_freq')
        varm = int(run(c, 'cat /sys/class/regulator/regulator.3/microvolts')) // 1000
        vlog = int(run(c, 'cat /sys/class/regulator/regulator.2/microvolts')) // 1000
        glm  = run(c, "ps aux | grep glmark2 | grep -v grep | awk '{print $11}' | head -1")
        status = f"glmark2 CORRIENDO" if glm else "sin glmark2"
        print(f"  {time.strftime('%H:%M:%S')}  temp={temp}°C  CPU={int(cpu)//1000}MHz  GPU={int(gpu)//1000000}MHz  varm={varm}mV  vlogic={vlog}mV  [{status}]")
    except Exception as e:
        print(f"  {time.strftime('%H:%M:%S')}  ERROR: {e} — reconectando...")
        try:
            c.close()
        except: pass
        time.sleep(3)
        try:
            c = connect()
            print("  Reconectado.")
        except:
            print("  Sin SSH todavía.")
    time.sleep(2)
