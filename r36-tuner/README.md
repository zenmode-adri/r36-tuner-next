# R36 Tuner

[![GitHub release](https://img.shields.io/github/v/release/zenmode-adri/r36-tuner?style=flat-square)](https://github.com/zenmode-adri/r36-tuner/releases)
[![GitHub stars](https://img.shields.io/github/stars/zenmode-adri/r36-tuner?style=flat-square)](https://github.com/zenmode-adri/r36-tuner/stargazers)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy%20me%20a%20coffee-FF5E5B?logo=ko-fi&style=flat-square)](https://ko-fi.com/zenmodeadri)

Real-time CPU / GPU / DMC / Voltage tuning tool for R36S and compatible devices running [dArkOSRE-R36](https://github.com/southoz/dArkOSRE-R36) (RK3326 SoC).

## Features

- CPU max / min frequency and governor selection
- GPU max frequency selection
- DMC / RAM max frequency selection
- **DTB undervolt** — permanent voltage reduction via OPP table patch. Detects your chip bin (L0–L3) automatically and patches only the correct voltage table. Uniform mode or per-OPP fine-tune.
- **CPU OC to 1608 MHz** — unlocks 1608 MHz via DTB patch (no kernel recompile).
- **GPU OC to 600 MHz** — adds 600 MHz OPP via DTB patch.
- **RAM OC to 928 MHz** — adds 928 MHz OPP via DTB patch. ATF delivers 924 MHz (nearest PLL divisor).
- **DTB safety net** — early-boot systemd service detects if the previous boot hung after a DTB patch and restores the original backup before userspace starts.
- Real-time monitor (temp, freq, voltage) with overheat warning at ≥80°C
- Benchmarks: CPU (ALU int32 chains), RAM (128 MB memset/memcpy, compiled C), GPU (glmark2) — individually or all in sequence. Score history with baseline comparison.
- Save profile → applies at every boot via systemd service
- Fail-safe: panic flag detects boot hangs and auto-disables the profile

## Requirements

- Device: R36S or compatible clone (RK3326 / RK3326S SoC)
- OS: [dArkOSRE-R36](https://github.com/southoz/dArkOSRE-R36) by southoz
- Tools present in dArkOSRE: `dialog`, `gptokeyb`, `systemd`
- For DTB features: `device-tree-compiler` (`fdtget`/`fdtput`) — bundled in the script, no internet required

## Installation

Copy `R36 Tuner.sh` to `/opt/system/` on your device:

```bash
scp "R36 Tuner.sh" ark@<device-ip>:/opt/system/
ssh ark@<device-ip> "chmod +x '/opt/system/R36 Tuner.sh'"
```

Then launch it from the dArkOSRE system menu.

## DTB Undervolt

The RK3326 OPP framework owns all voltage regulators — runtime sysfs writes are reverted during frequency transitions. The only permanent undervolt is patching the voltage table in the Device Tree Binary.

The tuner detects your chip bin from `dmesg` (`pvtm-volt-sel`) and patches the correct property (`opp-microvolt-L2` for most units). Reboot required.

**Tested results on our unit (L2 bin):**

| Component | Stock @ max freq | Stable UV limit |
|-----------|-----------------|-----------------|
| CPU (vdd_arm) | 1300 mV @ 1512 MHz | **−125 mV → 1175 mV** ✅ |
| GPU (vdd_logic) | 1100 mV @ 520 MHz | **−12.5 mV uniform** (or up to −150 mV fine-tune per OPP) ✅ |
| RAM/DMC (vdd_logic) | — | use RAM OC menu ⚠️ (shares vdd_logic with GPU) |

> Your bin may differ — the tuner shows your active bin on startup. Full voltage tables in [docs/opp-research.md](docs/opp-research.md).

## GPU OC — 600 MHz

Adds a `opp-600000000` node to the GPU OPP table in the DTB. The GPU clock uses `gpll / 2 = 600 MHz` exactly — no clock driver changes needed.

**Results on our unit (L2 bin):** 520 MHz → 600 MHz = **+20% GPU compute** (terrain benchmark). Tested stable floor: **1025 mV** (−125 mV from initial OC voltage of 1150 mV). Your chip may differ.

> `vdd_logic` is shared between GPU and DMC. See [vdd_logic shared rail](#vdd_logic-shared-rail--gpu--ram-oc-voltage).

For full voltage sweep and clock analysis see [docs/opp-research.md](docs/opp-research.md).

## CPU OC — 1608 MHz

Unlocks 1608 MHz by patching `rockchip,avs-scale` from `4` to `0` in the DTB and adding an `opp-1608000000` node. The clock driver already contains 1608 MHz — it was being suppressed at boot.

**Tested voltage on our unit (L2 bin): 1187.5 mV.** Seven synthetic benchmarks showed 0–2% difference vs 1512 MHz — the A35 pipeline hits throughput and latency ceilings before 1608 MHz on single-thread workloads. Real benefit is in emulation: JIT recompilation and multi-thread frame timing. The bigger single win is undervolting 1512 MHz to 1175 mV.

For full benchmark breakdown see [docs/opp-research.md](docs/opp-research.md).

## RAM OC — 928 MHz

Adds a `opp-928000000` node to the DMC OPP table. ATF v0x105 accepts 928 MHz and delivers **924 MHz** (nearest PLL divisor). The `dmc_ondemand` governor scales up to 924 MHz under memory pressure.

**Results (L2 bin):**

| DMC freq | Write MB/s | Copy MB/s |
|----------|-----------|-----------|
| 786 MHz (stock) | 4768 | 1300 |
| **924 MHz (OC)** | **5516** | **1597** |

vs stock: write **+15.7%**, copy **+22.8%**. Tested stable floor on our unit (L2 bin): **987.5 mV**. Your chip may differ.

> `vdd_logic` is shared with GPU — see [vdd_logic shared rail](#vdd_logic-shared-rail--gpu--ram-oc-voltage).

For full ATF/DMC mechanism and bandwidth sweep see [docs/opp-research.md](docs/opp-research.md).

### ⚗️ Experimental — 1040 MHz OC (ATF delivers 1032 MHz)

> **Not available in the script yet. Under active testing — do not attempt manually.**

Preliminary bandwidth results on our unit (L2 bin, same methodology as above):

| DMC freq | Write MB/s | Copy MB/s |
|----------|-----------|-----------|
| 786 MHz (stock) | 4953 | 1539 |
| 924 MHz (current OC) | 5665 | 1653 |
| **1032 MHz (experimental)** | **6725** | **1810** |

vs stock: write **+35.8%**, copy **+17.6%**.

Hard constraint: 1032 MHz requires **1150 mV** on `vdd_logic` — the PMIC maximum for this rail. There is no undervolt margin, and it raises the shared rail above the GPU OC stable floor (1025 mV). Long-term stability and thermal impact are still being evaluated before this becomes an option in the script.

## vdd_logic Shared Rail — GPU & RAM OC Voltage

The GPU and DMC share the `vdd_logic` rail. The PMIC always sets it to the **highest voltage demanded by any consumer**.

- GPU OC at 1025 mV + DMC OC at 987.5 mV → rail = **1025 mV** (GPU wins)
- To lower the effective rail, **both** must be undervolted below the target
- Undervolting only one has no rail benefit if the other is higher

**Tested floors on our unit (L2 bin):**

| Component | OC freq | Voltage floor |
|-----------|---------|--------------|
| GPU | 600 MHz | **1025 mV** |
| DMC | 924 MHz | **987.5 mV** |

### Tuning OC voltage after first apply

Enter the **GPU OC / RAM OC** menu at any time — the tuner detects the existing OPP node and goes directly to a voltage selector. Select a new voltage, confirm, reboot. The DTB safety service protects against bad values.

## Performance Comparison — Full OC+UV vs Stock

Measured on the same unit (L2 bin), **without thermal pad**. glmark2-es2-drm 2021.02, off-screen 320×240.

| Configuration | GPU | CPU | DMC | vdd_arm | vdd_logic |
|---|---|---|---|---|---|
| **Stock** | 520 MHz | 1512 MHz | 786 MHz | ~1200 mV | ~1100 mV |
| **OC + UV** | 600 MHz | 1608 MHz | 924 MHz | 1187.5 mV | 1025 mV |

| Scene | Stock | OC+UV | Delta |
|---|---|---|---|
| build vbo=false | 505 | 564 | **+11.7%** |
| build vbo=true | 681 | 801 | **+17.6%** |
| texture linear | 1186 | 1317 | **+11.0%** |
| texture mipmap | 1240 | 1389 | **+12.0%** |
| shading blinn-phong | 437 | 500 | **+14.4%** |
| bump high-poly | 191 | 224 | **+17.3%** |
| effect2d box-5x5 | 198 | 227 | +14.6% |
| **terrain** | **15 fps** | **18 fps** | **+20.0%** |
| *average (20 scenes)* | — | — | **~+10%** |

**Thermal:** peak temp identical to stock (72°C) despite +15% GPU clock. UV offsets the extra heat.

> Results represent one chip (L2 bin). Silicon lottery applies.

## Emergency Recovery — Device Won't Boot

If a DTB patch causes a boot failure the safety service cannot catch:

1. Power off the R36S
2. Remove the system SD card and plug into a PC
3. On Windows, open the **FAT32 partition** (`/boot`). If not visible, use [DiskGenius](https://www.diskgenius.com/) (free)
4. Copy `rk3326-r36s-linux.dtb.bak` over `rk3326-r36s-linux.dtb`
5. Delete `.r36_dtb_patch_booting` if it exists
6. Eject, reinsert, boot

> The `.bak` file is created at the moment of first patching and never overwritten.

## Disclaimer

> **USE AT YOUR OWN RISK.**
>
> This tool patches the Device Tree Binary and writes to kernel sysfs interfaces to modify CPU, GPU, and RAM frequencies and voltages. Incorrect settings can cause **system instability, data corruption, or permanent hardware damage**.
>
> The authors take **no responsibility** for bricked devices, corrupted SD cards, or data loss. The fail-safe mechanisms reduce risk but do not eliminate it.
>
> Always start conservative (−25 mV CPU, −12.5 mV GPU) and verify stability before going further.

## Credits

UI scripting framework (TTY setup, `dialog`, `gptokeyb` integration, systemd service pattern) adapted from [ZRam Manager](https://github.com/southoz/dArkOSRE-R36) by [southoz](https://github.com/southoz).

Built for and tested on [dArkOSRE-R36](https://github.com/southoz/dArkOSRE-R36).

## License

[MIT](LICENSE)
