import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

def sudo(cmd, timeout=15):
    _, out, _ = c.exec_command(f"echo ark | sudo -S bash -c '{cmd}'", timeout=timeout)
    return out.read().decode('utf-8', errors='replace').strip()

# Buscar WiFi Manager script
print("=== Buscando WiFi Manager ===")
print(sudo('find /opt /usr/local /home -name "*wifi*" -o -name "*Wifi*" -o -name "*WiFi*" 2>/dev/null | head -20'))

print("\n=== /opt/system ===")
print(sudo('ls /opt/system/ 2>/dev/null || echo "no existe"'))

print("\n=== Buscando Enable Remote Services ===")
print(sudo('grep -rl "Remote Services\\|remote_services\\|enable.*ssh\\|sshd" /opt /usr/local /etc/init.d 2>/dev/null | head -10'))

print("\n=== Estado sshd ===")
print(sudo('systemctl is-enabled ssh 2>/dev/null; systemctl is-active ssh 2>/dev/null'))

print("\n=== Que hace Enable Remote Services ===")
print(sudo('grep -r "RemoteServices\\|remote.*serv\\|enable.*ssh\\|Start.*SSH" /opt 2>/dev/null | head -20'))

c.close()
