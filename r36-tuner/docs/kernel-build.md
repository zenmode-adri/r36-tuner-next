# Patched Kernel Build — R36S / RK3326

Notes for building and deploying a patched R36S kernel that enables real CPU overclocking above 1296 MHz.

## Background

On the stock dArkOSRE-R36 kernel (`rg351` branch), CPU frequencies above 1296 MHz are reported by `cpufreq` and the PLL reaches the requested rate, but the silicon does not actually run faster. The restriction comes from Rockchip binning code that was not ported from the `odroidgoA-4.4.y` branch.

The teacupx kernel (`linux-r36s`, branch `rg351`) patches the kernel to bypass the binning restriction and adds intermediate OPPs between 1296 MHz and 1512 MHz. We built it from source with the out-of-tree WiFi/BT drivers that dArkOSRE normally carries on its stock kernel.

## Kernel source

- **Upstream reference:** https://github.com/teacupx/overclock-r36s
- **Kernel source:** https://github.com/teacupx/linux-r36s (branch `rg351`)
- **Local tree:** `~/linux-r36s/` (WSL2)
- **What it does:**
  - Bypasses the RK3326 binning restriction that caps effective CPU frequency at 1296 MHz.
  - Raises `max-volt` to 1400 mV for `vdd_arm`.
  - Adds intermediate OPPs from 1368 MHz up to 1512 MHz.

## Toolchain

- **Source:** GitLab `firefly-linux/prebuilts/gcc/linux-x86/aarch64/gcc-linaro-6.3.1-2017.05-x86_64_aarch64-linux-gnu.git`
- **Local path:** `/opt/toolchains/gcc-linaro-6.3.1/`
- **Version:** Linaro GCC 6.3.1 20170404

The kernel build is sensitive to the compiler version. GCC 9/13 introduced errors with several out-of-tree Realtek drivers, so the older Linaro toolchain is used.

## Build issues resolved

1. **Empty `fs/exfat` submodule**
   - Fix: `git submodule update --init --recursive`

2. **Qualcomm `gcc-wrapper.py`**
   - A wrapper script that promotes warnings to errors. It was renamed during early experiments with GCC 9, but it was not needed once the Linaro 6.3.1 toolchain was selected.

3. **RTL8723BU module conflict**
   - `CONFIG_RTL8723BU=m` pointed to two directories: `ew-7611ulb/` and `rockchip_wlan/rtl8723bu/`, causing a module name collision.
   - Fix: disabled `ew-7611ulb` in `drivers/net/wireless/Makefile`.

4. **Broken Realtek drivers with GCC 9/13**
   - `RTL8812AU` and `RTL8821CU` failed to compile with newer GCC.
   - Fix: removed them from `rg351p_tweaked_defconfig` (not needed for R36S).

## Build commands

```bash
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
export PATH=/opt/toolchains/gcc-linaro-6.3.1/bin/:$PATH
cd ~/linux-r36s
make rg351p_tweaked_defconfig
make -j$(nproc)
```

**Output:**
- `arch/arm64/boot/Image` — 13 MB
- `vmlinux` — 17 MB
- 553 `.ko` modules
- Kernel version string: `Linux version 4.4.189`

## Deployment

Backups created on the device before flashing:

| File | Purpose |
|---|---|
| `/boot/image.backup_20260609` | Previous kernel image |
| `/boot/rk3326-r36s-linux.dtb.original` | Original stock DTB |
| `/boot/rk3326-r36s-linux.dtb.teacupx_pre` | DTB before teacupx patching |
| `/lib/modules/4.4.189.backup_20260609` | Previous kernel modules |

Files deployed:
- `/boot/image` — new compiled kernel (md5 `f7c8b8c6...`)
- `/lib/modules/4.4.189/` — new modules, including `rockchip_wlan/rtl8723bu/8723bu.ko`

> Always keep the backups on the device and a fresh copy of the original DTB on the host before modifying the DTB further.

## WiFi / Bluetooth drivers

The R36S uses Realtek out-of-tree drivers that dArkOSRE adds to its stock kernel:

- **WiFi:** Realtek RTL8188FU → driver `rtl8188fu`
- **Bluetooth:** Realtek RTL8723BU → driver `8723bu`

In our build:
- `RTL8188FU` — built-in (`=y`) inside `Image`
- `RTL8723BU` — module (`=m`) at `rockchip_wlan/rtl8723bu/8723bu.ko`

## Verification

After booting the patched kernel with `boot.ini` options:

```
max_cpufreq=1512 cpufreq.default_governor=powersave
```

the available frequencies include:

```
1008000 1200000 1248000 1296000 1368000 1416000 1440000 1464000 1488000 1512000
```

ALU benchmark (LCG 4-chain, 10 s, governor `performance`):

| Frequency | Real MHz | Mops/10s | vs 1008 MHz |
|---|---|---|---|
| 1008 MHz | 1008 | 163.6 | 100% |
| 1296 MHz | 1296 | 211.4 | +29.2% |
| 1368 MHz | 1368 | 223.1 | +36.4% |
| 1512 MHz | 1512 | 231.0 | +41.2% |

Before the patched kernel, 1296 → 1512 MHz showed only ~+1.2% real improvement. With the patched kernel the gap is +9.3%, confirming the OC is now real.

## Next steps / open items

- Test 1608 MHz by adding the `opp-1608000000` node with R36 Tuner. The clock driver already supports it.
- Evaluate stability and thermals of the new intermediate OPPs under emulation loads.
- Document any DTB voltage adjustments needed for the patched kernel's higher `max-volt`.

## References

- teacupx/overclock-r36s: https://github.com/teacupx/overclock-r36s
- teacupx/linux-r36s (`rg351` branch): https://github.com/teacupx/linux-r36s
- Reddit thread: https://www.reddit.com/r/R36S/comments/1tyh3tn/r36s_cpu_oc_was_fake_above_1296_mhz_here_is_a/
