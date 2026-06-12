import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def sudo(cmd, timeout=30):
    _, out, _ = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

# Leer WiFi Manager
print("=== Wi-Fi.Manager.4.2.sh ===")
print(sudo('cat /opt/system/Wi-Fi.Manager.4.2.sh'))

c.close()
