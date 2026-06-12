# AGENTS.md — R36 Tuner Workspace

> Agent-focused reference. `r36-tuner/CHANGELOG.md` is the live project history. `r36-tuner/README.md` documents the legacy Bash-only script; the current effort is the SDL2/TTF UI in `src/ui/tuner_ui/`.

## 1. Project Overview

Hardware tuning suite for the R36S handheld (Rockchip RK3326 / PX30, dArkOSRE-R36). Primary deliverable: `r36-tuner/R36 Tuner.sh`, a self-contained Bash script. This workspace contains the host-side toolchain (Python, C, firmware, deployment scripts).

> **Terminology:** When the user says "la consola" or "the console", they mean the R36S device itself.

> **Critical kernel discovery (2026-06-11):** On the stock dArkOSRE-R36 kernel (`rg351` branch), CPU frequencies above 1296 MHz are reported by `cpufreq` and the PLL reaches the requested rate, but the silicon does not actually run faster. Real CPU overclocking above 1296 MHz requires a patched kernel that disables Rockchip's binning restrictions. The workspace includes research and build notes for the teacupx `linux-r36s` (`rg351` branch) kernel with out-of-tree RTL8188FU/RTL8723BU drivers. See `r36-tuner/docs/kernel-build.md`.

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Device runtime | Bash 4+, `dialog`, `systemd`, `fdtget`/`fdtput` |
| Host tooling | Python 3 + `paramiko` (all host→device SSH is done through paramiko; no `ssh`/`sshpass` CLI tools are used) |
| Compiled code | C, SDL2, OpenGL ES 2.0, GBM/DRM |
| Kernel/firmware | DTB, kernel `Image`, Debian `.deb` |
| VCS | Git (repo under `r36-tuner/.git/`) |

No top-level build system. Build with direct `gcc` / `aarch64-linux-gnu-gcc` invocations.

## 3. Repository Layout

```
r36-tuner/          Main product: R36 Tuner.sh, README, CHANGELOG, docs/opp-research.md
src/ui/tuner_ui/    SDL2/TTF graphical UI (experimental, Spanish strings)
src/overlay/        LD_PRELOAD overlay (r36_overlay.c)
src/benchmark/      dmc_bench.c, dmc_stress.c
tools/deployment/   deploy_to_r36.py, deploy_ui.py, deploy_overlay.py + r36_ssh.py helper
tools/benchmarks/   bench_*.py, ram_bench_*.py, setup_glmark2.py
tools/diagnostics/  audit_device.py, check_*.py, fix_*.py
tools/undervolt/    auto_sweep.py, voltage_sweep.py, uv_*.py
tools/gpu/          gpu_oc_*.py, terrain_*.py
tools/release/      create_release.py
tools/misc/         explore_wifi.py, reboot_r36.py
bin/                Compiled binaries: libr36overlay*.so, fdtget/put, tuner_ui, glmark2-es2-drm-legacy
firmware/kernels/   Reference/test kernel images (darkosre_kernel.img, kernel_new.img, kernel_rg351p*.img); see docs/kernel-build.md for build notes
firmware/dtb/       rk3326-r36s-linux.dtb
packages/glmark2/   glmark2 .deb packages
packages/*.deb      Host dev dependencies
assets/roms/        Game ROMs
logs/               Sweep logs
```

## 4. Build

```bash
# CPU/RAM benchmark
gcc -O2 -o dmc_bench src/benchmark/dmc_bench.c

# Overlay (cross)
aarch64-linux-gnu-gcc -shared -fPIC -O2 -o bin/libr36overlay.so src/overlay/r36_overlay.c -ldl -lGLESv2

# SDL2 UI (cross or on device)
aarch64-linux-gnu-gcc -O2 -o bin/tuner_ui src/ui/tuner_ui/main.c -lSDL2 -lSDL2_ttf
```

## 4.1 Kernel / Firmware Research

Kernel research and build artifacts are documented in `r36-tuner/docs/kernel-build.md`.

Key files:
- `firmware/kernels/` — reference kernel `Image` files for testing.
- `firmware/dtb/` — reference `rk3326-r36s-linux.dtb`.
- `~/linux-r36s/` (WSL2) — teacupx kernel source tree used for the patched build.
- `/opt/toolchains/gcc-linaro-6.3.1/` — Linaro GCC 6.3.1 toolchain used to build the patched kernel.

## 5. Deployment

All host → device communication is done through **paramiko** (Python SSH library). Use **`tools/deployment/r36_ssh.py`** as the reusable wrapper for connect, sudo, and SFTP upload. It avoids quoting/encoding bugs and keeps credentials and session handling in one place.

```bash
python tools/deployment/deploy_to_r36.py      # main script
python tools/deployment/deploy_ui.py          # SDL2 UI
python tools/deployment/deploy_overlay.py     # overlay .so
```

Manual fallback (for humans only; internal tools use paramiko):
```bash
scp "r36-tuner/R36 Tuner.sh" ark@<ip>:/opt/system/
ssh ark@<ip> "chmod +x '/opt/system/R36 Tuner.sh'"
```

> Internally, always prefer `r36_ssh.py` / paramiko over shelling out to `ssh`/`scp`. This ensures consistent credential handling, UTF-8 encoding, and reliable sudo password injection.

## 6. Code Conventions

- **Bash**: shebang `#!/bin/bash`, self-elevates with `exec sudo`, `snake_case` functions, UPPER_SNAKE_CASE globals, `dialog` UI, dynamic sysfs discovery. User-facing text is English.
- **C**: 4-space indent. SDL2 UI strings/comments are Spanish; overlay uses `dlsym` for GLES2.
- **Python**: PEP 8-ish. Hardcoded device IP `192.168.1.87`, user `ark`, pass `ark` in host scripts. Prefer `r36_ssh.py` for new scripts.

## 7. Testing

- On-device benchmarks and stress tests inside `R36 Tuner.sh`.
- Host audits: `tools/diagnostics/audit_device.py`.
- Sweeps: `tools/undervolt/auto_sweep.py`, `tools/undervolt/voltage_sweep.py`.

## 8. Safety

- DTB `.bak` created once and never overwritten.
- `r36-dtb-safety.service` / `r36-dtb-confirm.service` auto-restore on boot hang.
- Panic flag in boot profile disables a crashing profile.
- Voltage floor: 950 mV for `vdd_arm`/`vdd_logic`.
- Thermal abort at 85°C.
- OPP bin detection from `dmesg`, cached in `/etc/r36_tuner_bin`.

## 9. Release Process

1. Bump `VERSION` in `r36-tuner/R36 Tuner.sh`.
2. Update `r36-tuner/CHANGELOG.md`.
3. Deploy and test on device.
4. Run `tools/diagnostics/audit_device.py`.
5. Tag and release via `tools/release/create_release.py`. Artifact: `R36 Tuner.sh` only.

## 10. Quick Reference

| Task | Command |
|---|---|
| Deploy main script | `python tools/deployment/deploy_to_r36.py` |
| Deploy SDL2 UI | `python tools/deployment/deploy_ui.py` |
| Deploy overlay | `python tools/deployment/deploy_overlay.py` |
| Audit device | `python tools/diagnostics/audit_device.py` |
| Compile overlay | `aarch64-linux-gnu-gcc -shared -fPIC -O2 -o bin/libr36overlay.so src/overlay/r36_overlay.c -ldl -lGLESv2` |
| Compile SDL2 UI | `aarch64-linux-gnu-gcc -O2 -o bin/tuner_ui src/ui/tuner_ui/main.c -lSDL2 -lSDL2_ttf` |
| Run sweep | `python tools/undervolt/auto_sweep.py` |
| Create release | `python tools/release/create_release.py` |

## 11. SDL2 UI

Experimental SDL2/TTF frontend in `src/ui/tuner_ui/main.c` (Spanish UI strings). Launcher: `src/ui/tuner_ui/launch_tuner.sh` (stops EmulationStation, runs UI, restarts ES). `tools/deployment/deploy_ui.py` uploads the binary plus launcher to `/opt/system/`.

Required env:
```bash
export SDL_VIDEO_EGL_DRIVER=/lib/aarch64-linux-gnu/libEGL.so
export XDG_RUNTIME_DIR=/run/user/1000
export SDL_GAMECONTROLLERCONFIG_FILE=/opt/inttools/gamecontrollerdb.txt
```

## 12. User Connection Commands

When the user says anything like **"conectate"**, **"conectate a la consola"**, **"conectate a la R36"**, **"connect to the console"**, or any similar request to connect to the device, **do it immediately via paramiko** using the project defaults:

- Host: `192.168.1.87`
- User: `ark`
- Password: `ark`

Do **not** ask for credentials first, do **not** use the `ssh`/`scp` CLI, and do **not** run `ping` as a prerequisite. Just open the paramiko SSH connection and run a quick verification command (e.g. `uname -a; whoami; hostname`). Then report success and ask what to do next.

If the connection fails, then ask for the correct IP/credentials.

---

*Last updated: 2026-06-11 — added section 12 (User Connection Commands).
