# Host-side Tools

Python/C helpers that run on the development host and talk to the R36S over SSH.

> **All SSH communication is done through `paramiko`.** Do not shell out to `ssh`, `scp`, or `sshpass` from internal tools — use `deployment/r36_ssh.py` for new scripts, or raw `paramiko` for legacy ones.

> Default device credentials are hardcoded in many scripts: `192.168.1.87`, user `ark`, password `ark`. These are development conveniences, not production secrets.

## Shared SSH helper

- **`deployment/r36_ssh.py`** — Reusable SSH/SFTP/sudo wrapper built on `paramiko`. New and refactored scripts use this to avoid quoting and encoding bugs. Legacy scripts still use raw `paramiko`; both are fine as long as the underlying transport is paramiko.

## Deployment

| Script | Purpose |
|---|---|
| `deployment/deploy_to_r36.py` | Upload and install `r36-tuner/R36 Tuner.sh` to `/opt/system/`. |
| `deployment/deploy_ui.py` | Upload `bin/tuner_ui` and launcher scripts to `/opt/system/`. |
| `deployment/deploy_overlay.py` | Upload `bin/libr36overlay*.so` to `/usr/local/lib/` and install launcher. |
| `deployment/push_script.py` / `push_to_r36.py` | One-off script push helpers (legacy, being consolidated into `deploy_to_r36.py`). |

## Diagnostics and Audits

| Script | Purpose |
|---|---|
| `diagnostics/audit_device.py` | Run 15 check sections over SSH and report pass/warn/fail. |
| `diagnostics/check_state.py` | Quick check of current CPU/GPU/DMC state and DTB status. |
| `diagnostics/check_dtb_backup.py` | Verify the original DTB backup exists and is intact. |
| `diagnostics/monitor.py` | Remote live monitor of temp/freq/voltage. |

Additional `diag*.py`, `check_*.py`, `fix_*.py`, and `patch_*.py` scripts are ad-hoc helpers created during bring-up and research.

## Benchmarks

| Script | Purpose |
|---|---|
| `benchmarks/setup_glmark2.py` | Install glmark2 and shader data on the device. |
| `benchmarks/terrain_test_quick.py` | Run on-screen terrain test for GPU stability checks. |
| `benchmarks/bench_coremark.py` | Run Coremark remotely. |
| `benchmarks/bench_emu.py` | Emulation inner-loop microbenchmark. |
| `benchmarks/bench_l1.py` | L1 cache pointer-chasing test. |
| `benchmarks/ram_bench_928.py` / `ram_bench_sweep.py` | RAM bandwidth tests at different DMC frequencies. |

## GPU Overclock Research

| Script | Purpose |
|---|---|
| `gpu/gpu_oc_setup.py` | Deploy GPU OC 600 MHz patch and related tests. |
| `gpu/gpu_oc_verify.py` / `gpu_oc_check*.py` | Verify GPU OC state after reboot. |
| `gpu/gpu_oc_bench*.py` | Various GPU benchmark iterations during 600 MHz validation. |
| `gpu/terrain_onscreen_1100mv.py` / `terrain_test_1100mv.py` | On-screen terrain stability tests. |
| `gpu/gpu_oc_cleanup.py` | Remove GPU OC patch and restore stock DTB. |

## Undervolt and Stress Sweeps

| Script | Purpose |
|---|---|
| `undervolt/auto_sweep.py` | Automated undervolt sweep with reboot and stability test. |
| `undervolt/voltage_sweep.py` | Manual/stepped voltage sweep helper. |
| `undervolt/uv_1608_sweep.py` | CPU 1608 MHz voltage sweep. |
| `undervolt/uv_520_sweep.py` | GPU 520 MHz undervolt sweep. |
| `undervolt/dmc_uv_auto.py` / `dmc_uv_step.py` | DMC/RAM undervolt sweeps. |
| `undervolt/stress_1608.py` / `sweep_1608.py` | CPU 1608 MHz stress variants. |

## Release

| Script | Purpose |
|---|---|
| `release/create_release.py` | Create a GitHub release via API. |
| `release/create_release_v42.py` | Version-specific release helper. |

## Miscellaneous

| Script | Purpose |
|---|---|
| `misc/reboot_r36.py` | Remote reboot helper. |
| `misc/explore_wifi.py` / `explore_wifi2.py` | WiFi driver/module exploration. |

## Notes

- Many scripts embed small C programs as strings and compile them remotely with `gcc -O2`.
- Sweeps that reboot the device write logs to `logs/` in the workspace root.
- When adding a new script, prefer importing `deployment.r36_ssh.py` instead of raw `paramiko`.
- Never call the `ssh`/`scp` CLI from internal tooling. Paramiko gives consistent credential handling, UTF-8 text I/O, and reliable sudo password injection.
