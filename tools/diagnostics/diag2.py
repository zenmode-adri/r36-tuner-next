import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark', timeout=10)
_,out,_ = c.exec_command('cat \"/opt/system/R36 Tuner Next.sh\" 2>&1')
print('LAUNCHER:', out.read().decode())
c.close()
