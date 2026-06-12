import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark', timeout=10)

# launcher con log en vez de /dev/null
new_launcher = '''#!/bin/bash
TERM=linux clear > /dev/tty1 2>/dev/null
exec SDL_VIDEO_EGL_DRIVER=/lib/aarch64-linux-gnu/libEGL.so XDG_RUNTIME_DIR=/run/user/1000 SDL_GAMECONTROLLERCONFIG_FILE=/opt/inttools/gamecontrollerdb.txt /opt/system/tuner_ui > /tmp/tuner_launch.log 2>&1
'''

_,out,_ = c.exec_command('echo ark | sudo -S tee /opt/system/R36 Tuner Next.sh > /dev/null << \'EOF\'\n' + new_launcher + '\nEOF\n')
import time; time.sleep(1)

# escribirlo via stdin
stdin, stdout, stderr = c.exec_command('echo ark | sudo -S bash -c "cat > /opt/system/R36 Tuner Next.sh"')
stdin.write(new_launcher.encode())
stdin.channel.shutdown_write()
stdout.read()

_,out,_ = c.exec_command('cat /opt/system/R36 Tuner Next.sh')
print('NUEVO LAUNCHER:')
print(out.read().decode())
c.close()
