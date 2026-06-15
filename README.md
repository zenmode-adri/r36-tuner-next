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
- **CPU undervolt** — patches `vdd_arm` OPP table. Auto-detects chip bin (L0–L3) and patches the correct voltage property. Uniform offset across all OPPs.
- **CPU fine-tune** — per-OPP voltage adjustment: select a specific frequency step (1008 / 1200 / 1248 / 1296 / 1512 MHz) and set its voltage independently. Pairs with undervolt for precise per-frequency floors.
- **CPU OC** — requires [teacupx kernel](https://github.com/teacupx/overclock-r36s) (installed separately). Once active, the tuner lets you adjust CPU voltages to find a stable floor. Max real freq with teacupx: 1512 MHz.
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
| CPU (vdd_arm) | 1300 mV @ 1296 MHz | 1175 mV — OC requires [teacupx](https://github.com/teacupx/overclock-r36s) |
| GPU (vdd_logic) | 1100 mV @ 520 MHz | 1025 mV @ 600 MHz |
| RAM (vdd_logic) | ~1025 mV @ 786 MHz | 987.5 mV @ 924 MHz |

> Results represent one chip. Silicon lottery applies — always validate stability after each change.
> Full OPP voltage tables for all bins (L0–L3): [docs/opp-research.md](https://github.com/zenmode-adri/r36-tuner/blob/master/docs/opp-research.md)

### vdd_logic shared rail

GPU and RAM share the `vdd_logic` rail. The PMIC always sets it to the **highest voltage demanded by any consumer**.

- GPU OC at 1025 mV + DMC OC at 987.5 mV → rail = **1025 mV** (GPU wins)
- To lower the effective rail, **both** must be undervolted below the target
- Undervolting only one has no rail benefit if the other is higher

**Tested voltage floors (L2 bin):**

| Component | OC freq | Voltage floor |
|-----------|--------:|--------------:|
| GPU | 600 MHz | **1025 mV** |
| DMC | 924 MHz | **987.5 mV** |

**Tuning voltage after first apply:** enter the GPU OC / RAM OC menu at any time — the tuner detects the existing OPP node and goes directly to a voltage selector. Select a new voltage, confirm, reboot.

### RAM OC 1032 MHz — [EXPERIMENTAL]

Available in the RAM OC menu once 924 MHz is already active. ATF delivers **1032 MHz** (nearest PLL divisor).

**Hard constraint:** requires **1150 mV** on `vdd_logic` — the PMIC hard limit for this rail. No undervolt margin is possible. If GPU OC is also active (stable floor: 1025 mV), the shared rail gets pinned at 1150 mV, eliminating the GPU UV savings.

Real-world impact measured in PPSSPP (God of War: Ghost of Sparta, L2 bin):

| DMC freq | FPS avg | vs stock 786 MHz |
|----------|--------:|-----------------:|
| 786 MHz (stock) | 25.6 | — |
| 924 MHz | 26.7 | +4% |
| **1032 MHz** | **28.6** | **+12%** |

RAM dominates PSP emulation performance — CPU and GPU share a UMA bus, and bandwidth is the bottleneck. Full sweep data in [docs/opp-research.md](https://github.com/zenmode-adri/r36-tuner/blob/master/docs/opp-research.md).

### glmark2 off-screen results

> Platform: 320×240, L2 bin, glmark2-es2-drm 2021.02 (4 scenes: build / texture / shading / terrain) — measured 2026-06-14. Best of three OC runs.

| Config | Score | GPU MHz | Peak temp |
|--------|------:|--------:|----------:|
| Stock | 560 pts | 520 MHz | 51 °C |
| GPU OC (600 MHz) | **620 pts** | **600 MHz** | 51 °C |
| Delta | **+10.7%** | | = |

> **Cooling note:** test unit has thermal pad + active fan. Stock-cooled units will run hotter.
> Applying GPU undervolt via the tuner offsets the extra heat from OC — peak temps stay close to stock.

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
