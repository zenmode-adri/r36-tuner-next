import paramiko, io
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark', timeout=10)

content = b'#!/bin/bash\nTERM=linux clear > /dev/tty1 2>/dev/null\nexec SDL_VIDEO_EGL_DRIVER=/lib/aarch64-linux-gnu/libEGL.so XDG_RUNTIME_DIR=/run/user/1000 SDL_GAMECONTROLLERCONFIG_FILE=/opt/inttools/gamecontrollerdb.txt /opt/system/tuner_ui > /tmp/tuner_launch.log 2>&1\n'

sftp = c.open_sftp()
with sftp.open('/tmp/launch_tuner_new.sh', 'wb') as f:
    f.write(content)
sftp.close()

_,out,err = c.exec_command('echo ark | sudo -S cp /tmp/launch_tuner_new.sh /opt/system/launch_tuner.sh && sudo chmod +x /opt/system/launch_tuner.sh && echo DONE')
print(out.read().decode().strip())

_,out,_ = c.exec_command('cat /opt/system/launch_tuner.sh')
print(out.read().decode())
c.close()
