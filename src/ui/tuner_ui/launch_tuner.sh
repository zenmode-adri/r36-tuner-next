#!/bin/bash
# launch_tuner.sh -- SDL2 Tuner UI launcher for dArkOSRE.
# Stops EmulationStation, runs the SDL2 UI, then restarts ES on exit.

# SDL2 environment required on this device.
export SDL_VIDEO_EGL_DRIVER=/lib/aarch64-linux-gnu/libEGL.so
export XDG_RUNTIME_DIR=/run/user/1000
export SDL_GAMECONTROLLERCONFIG_FILE=/opt/inttools/gamecontrollerdb.txt

LOG=/tmp/tuner_launch.log
: > "$LOG"
exec >> "$LOG" 2>&1

# Clean up ES and bring it back on exit.
cleanup() {
    echo "[launch_tuner] cleanup: restarting EmulationStation..."
    systemctl start emulationstation 2>/dev/null || true
    echo "[launch_tuner] cleanup: done"
}
trap cleanup EXIT SIGINT SIGTERM

# Stop EmulationStation. We avoid being killed by systemd by ensuring the ES
# service uses KillMode=process (only the ES process is stopped, not children).
echo "[launch_tuner] Stopping EmulationStation..."
systemctl stop emulationstation 2>/dev/null || true

# Wait for the ES process to actually go away; fall back to SIGKILL.
for i in $(seq 1 30); do
    if ! pgrep -x emulationstation > /dev/null 2>&1; then
        break
    fi
    sleep 0.2
done
pkill -9 -x emulationstation 2>/dev/null || true
sleep 0.5

# Clear the console framebuffer.
TERM=linux clear > /dev/tty1 2>/dev/null || true
chvt 1 2>/dev/null || true

echo "[launch_tuner] Launching /opt/system/tuner_ui..."
/opt/system/tuner_ui
echo "[launch_tuner] tuner_ui exited with code $?"

# cleanup() runs on EXIT and restarts EmulationStation.
