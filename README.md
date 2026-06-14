# R36 Tuner Next

[![GitHub release](https://img.shields.io/github/v/release/zenmode-adri/r36-tuner-next?style=flat-square)](https://github.com/zenmode-adri/r36-tuner-next/releases)
[![GitHub stars](https://img.shields.io/github/stars/zenmode-adri/r36-tuner-next?style=flat-square)](https://github.com/zenmode-adri/r36-tuner-next/stargazers)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support-FF5E5B?logo=ko-fi&style=flat-square)](https://ko-fi.com/zenmodeadri)
Graphical tuner for R36S and compatible RK3326 devices running [dArkOSRE-R36](https://github.com/southoz/dArkOSRE-R36). Native SDL2 UI — no terminal, no dialog boxes. Runs directly from the dArkOSRE system menu.

---

## Features

### Frequencies & Governor
- CPU max / min frequency and governor selection
- GPU max frequency selection (Mali-G31 MP2)
- RAM / DMC max frequency selection

### DTB Tuning (permanent, reboot required)
- **CPU undervolt** — patches `vdd_arm` OPP table. Auto-detects chip bin (L0–L3) and patches the correct voltage property. Uniform offset or per-frequency fine-tune.
- **CPU OC 1608 MHz** — adds a 1608 MHz OPP via DTB patch and sets `rockchip,avs-scale=0`. The dArkOSRE kernel clock driver already includes 1608 MHz; the stock DTB removes it at boot via `avs-scale=4`. No kernel recompile needed.
- **GPU OC 600 MHz** — adds a 600 MHz OPP node to the Mali-G31 table.
- **RAM OC 928 MHz** — adds a 928 MHz OPP to the DMC table. ATF delivers 924 MHz (nearest PLL divisor).
- **DTB safety net** — early-boot systemd service confirms the patched DTB survived the boot and clears the watchdog flag. If the device won't boot, original DTB is restored manually via SD card (instructions in-app).
- **OPP voltage table** — read-only view comparing on-disk DTB voltages vs kernel-active voltages, with mismatch highlighting.
- **One-tap restore** — reverts DTB to the original backup from inside the app.

### Benchmarks
- **CPU** — 30s integer ALU chain (LCG × 4), compiled C, async with live temperature sampling. Score in Mops/30s, logged with CPU MHz and temperature.
- **RAM** — 128 MB memset + memcpy bandwidth test, compiled C. Shows write and copy MB/s, DDR MHz, temperatures.
- **GPU** — glmark2 off-screen (build / texture / shading / terrain). Runs in background via systemd service, live progress screen (scene counter, progress bar, timer). Score logged with GPU MHz and temperatures.
- **Score history** — all results saved to `/home/ark/.r36_tuner_ui_scores.log` with date, type badge, detail and temperature range.

### Monitor & UX
- Real-time monitor: CPU temp, GPU MHz, RAM MHz
- Overheat warning at ≥ 80 °C
- English / Spanish i18n, persisted across sessions
- Confirmation screens with voltage tables and shared-rail warnings before applying DTB patches
- **CPU silicon detection** — detects if frequencies above 1296 MHz are real (teacupx kernel) or software-only (stock kernel). Tags fake OC entries accordingly.

---

## Requirements

- **Device:** R36S or compatible RK3326 / RK3326S clone
- **OS:** [dArkOSRE-R36](https://github.com/southoz/dArkOSRE-R36) by southoz
- **Dependencies in dArkOSRE:** `SDL2`, `SDL2_ttf`, `systemd`, `device-tree-compiler` (`fdtget` / `fdtput`)
- **GPU benchmark:** `glmark2-es2-drm` (`apt install glmark2-es2-drm`)

---

## Installation

```bash
scp "R36 Tuner Next.sh" ark@<device-ip>:/opt/system/
scp tuner_ui ark@<device-ip>:/opt/system/
ssh ark@<device-ip> "chmod +x '/opt/system/R36 Tuner Next.sh' /opt/system/tuner_ui"
```

Or use the deployment script (requires Python + paramiko on host):

```bash
python tools/deployment/deploy_ui.py
```

Then launch **R36 Tuner Next** from the dArkOSRE system menu.

---

## DTB OC / UV — What Gets Patched

The RK3326 OPP framework owns all voltage regulators — runtime sysfs writes are reverted during frequency transitions. The only way to make changes permanent is patching the Device Tree Binary on the boot partition.

The tuner auto-detects your chip bin from `dmesg` (`pvtm-volt-sel`) and patches the matching `opp-microvolt-Lx` property. A `.dtb.bak` backup is created on first patch and never overwritten.

### Tested results (L2 bin)

| Component | Stock | OC + UV |
|-----------|-------|---------|
| CPU (vdd_arm) | 1300 mV @ 1512 MHz | 1187.5 mV @ 1608 MHz |
| GPU (vdd_logic) | 1100 mV @ 520 MHz | 1025 mV @ 600 MHz |
| RAM (vdd_logic) | — @ 786 MHz | 987.5 mV @ 924 MHz |

> Results represent one chip. Silicon lottery applies — always validate stability after each change.

### vdd_logic shared rail

GPU and RAM share the `vdd_logic` rail. The PMIC always sets it to the highest voltage demanded by either consumer. To lower the effective rail both must be undervolted below the target.

### glmark2 off-screen results (320×240, L2 bin, no thermal pad)

Results are from a **full OC+UV run** (CPU 1608 MHz + GPU 600 MHz + RAM 924 MHz + undervolts) vs stock. Not a GPU-only comparison.

| Scene | Stock | Full OC+UV | Delta |
|-------|-------|-----------|-------|
| terrain | 15 fps | 18 fps | +20% |
| average (full suite, 20 scenes) | — | — | ~+10% |

---

## Emergency Recovery

If a DTB patch causes a hard boot failure (kernel panic before systemd):

1. Power off the R36S
2. Remove the system SD card, connect to PC
3. Open the **FAT32 partition** (`/boot`) — on Windows use [DiskGenius](https://www.diskgenius.com/) if not visible
4. Copy `rk3326-r36s-linux.dtb.bak` → `rk3326-r36s-linux.dtb`
5. Delete `.r36_dtb_patch_booting` if it exists
6. Eject, reinsert SD, boot

The `.bak` is created on first patch and never overwritten.

---

## Disclaimer

> **USE AT YOUR OWN RISK.**
>
> This tool patches the Device Tree Binary and writes to kernel sysfs interfaces to modify CPU, GPU, and RAM frequencies and voltages. Incorrect settings can cause system instability, data corruption, or permanent hardware damage.
>
> The authors take no responsibility for bricked devices, corrupted SD cards, or data loss.

---

## Credits

Built for [dArkOSRE-R36](https://github.com/southoz/dArkOSRE-R36) by [southoz](https://github.com/southoz).

## License

[MIT](LICENSE)
