import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.1.87', port=22, username='ark', password='ark')

cmds = [
    ("dmesg panel/backlight/pwm/drm/vop",
     "dmesg | grep -iE 'panel|backlight|pwm|drm|vop|lcd|mipi|dsi|spi.*display|display.*spi|rockchip' | head -60"),
    ("DTB compatible panel",
     "echo ark | sudo -S fdtget /boot/rk3326-r36s-linux.dtb /panel compatible 2>/dev/null || "
     "echo ark | sudo -S fdtget /boot/rk3326-r36s-linux.dtb /display-subsystem/port compatible 2>/dev/null || "
     "echo 'no /panel node'"),
    ("DTB backlight",
     "echo ark | sudo -S fdtget /boot/rk3326-r36s-linux.dtb /backlight compatible 2>/dev/null || echo 'no /backlight node'"),
    ("DTB nodes con panel",
     "echo ark | sudo -S fdtget -l /boot/rk3326-r36s-linux.dtb / 2>/dev/null | grep -iE 'panel|backlight|display|dsi|vop'"),
    ("kernel config panel drivers",
     "zcat /proc/config.gz 2>/dev/null | grep -iE 'DRM_PANEL|LCD|BACKLIGHT|MIPI|ROCKCHIP_DW_MIPI' | grep '=y'"),
]

for label, cmd in cmds:
    print(f"\n=== {label} ===")
    _, out, err = c.exec_command(cmd)
    print(out.read().decode('utf-8', errors='replace').strip())
    e = err.read().decode('utf-8', errors='replace').strip()
    if e:
        print(f"[stderr] {e}")

c.close()
