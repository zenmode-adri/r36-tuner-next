import paramiko, time
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark', timeout=10)
# binario
_,out,_ = c.exec_command('ls -la /opt/system/tuner_ui')
print('BIN:', out.read().decode().strip())
# es_systems.cfg entrada tuner
_,out,_ = c.exec_command('grep -A5 tuner /etc/emulationstation/es_systems.cfg')
print('ES CFG:', out.read().decode().strip())
# intentar lanzar solo para ver stderr (NO en background, solo 2s)
_,out,err = c.exec_command('SDL_VIDEO_EGL_DRIVER=/lib/aarch64-linux-gnu/libEGL.so XDG_RUNTIME_DIR=/run/user/1000 SDL_GAMECONTROLLERCONFIG_FILE=/opt/inttools/gamecontrollerdb.txt timeout 2 /opt/system/tuner_ui 2>&1; echo EXIT:True')
time.sleep(3)
print('LAUNCH:', out.read().decode().strip())
c.close()
