# RK3326 OPP Voltage Research — R36S / dArkOSRE

Device: R36S · SoC: Rockchip RK3326 · PMIC: RK805  
OS: dArkOSRE-R36 by southoz · Chip bin: **L2** (pvtm-volt-sel=2, leakage=13)

---

## How OPP Binning Works

The Rockchip BSP kernel measures chip leakage (PVTM) at boot and picks a voltage bin:
`L0` (worst silicon) → `L1` → `L2` → `L3` (best silicon / lowest voltage needs).

The active bin is logged in dmesg:
```
dmesg | grep "opp-binning.*using OPP prop name"
```

**Patching `opp-microvolt` has zero effect.** The kernel uses `opp-microvolt-L2` (or whichever bin applies). Must patch the correct `opp-microvolt-L<N>` property.

---

## CPU OPP Table — `/cpu0-opp-table`

Rail: `vdd_arm` (DCDC_REG2) · DTB node format: `opp-<hz>` · Values: `[min, typ, max]` (3× u32 big-endian)

| MHz   | opp-microvolt | L0     | L1     | **L2** (active) | L3     |
|-------|---------------|--------|--------|-----------------|--------|
| 1008  | 1175 mV       | 1175   | 1125   | **1125**        | 1050   |
| 1200  | 1300 mV       | 1300   | 1275   | **1250**        | 1200   |
| 1248  | 1350 mV       | 1350   | 1300   | **1275**        | 1225   |
| 1296  | 1350 mV       | 1350   | 1350   | **1300**        | 1250   |
| 1512  | 1350 mV       | 1350   | 1350   | **1300**        | 1250   |

> Values from official [dArkOSRE-R36](https://github.com/southoz/dArkOSRE-R36) DTB.  
> `max` col in [min, typ, max] tuple is the voltage ceiling; kernel uses `min`/`typ`.  
> Constraint: vdd_arm min=950 mV, max=1350 mV.

### CPU Undervolt Test Results (L2 bin)

| Offset  | L2 @ 1296/1512 MHz | Result                         |
|---------|--------------------|--------------------------------|
| 0 mV    | 1300 mV (stock)    | Stable (baseline)              |
| −25 mV  | 1275 mV            | ✅ Stable                      |
| −125 mV | 1175 mV            | ✅ Stable — confirmed long-term |
| −137.5 mV | 1162.5 mV        | ❌ Freeze at "starting ui"     |
| −150 mV | 1150 mV            | ❌ Black screen (kernel crash) |

**Confirmed stable limit: −125 mV → 1125 mV** at 1296/1512 MHz.

Safety service (`r36-dtb-safety`) catches freeze/hang cases (before=basic.target).  
If kernel crashes before basic.target → safety service cannot act → manual SD recovery needed.

---

## GPU OPP Table — `/gpu-opp-table`

GPU: Mali-G31 (Bifrost) · Rail: `vdd_logic` (DCDC_REG1, **shared with SoC logic**)  
DTB node format: `opp-<hz>` · Values: single u32 big-endian (not 3-tuple like CPU)

| MHz   | opp-microvolt | L0     | L1     | **L2** (active) | L3     |
|-------|---------------|--------|--------|-----------------|--------|
| 400   | 1050 mV       | 1050   | 1025   | **975**         | 950    |
| 480   | 1125 mV       | 1125   | 1100   | **1050**        | 1000   |
| 520   | 1150 mV       | 1150   | 1150   | **1100**        | 1050   |
| **600** | **1150 mV** | **1150** | **1150** | **1025**     | **—** |

> Constraint: vdd_logic min=950 mV, max=1150 mV. Rail is **shared** between GPU and all SoC logic — undervolt margin is much tighter than CPU.  
> `rockchip,max-volt = 1175000 µV` — OPP framework enforces this ceiling on all entries.  
> 600 MHz row: added via OC patch (see GPU OC section below). 1150 mV is the PMIC hard limit.

### GPU Undervolt Test Results (L2 bin)

| Offset   | L2 @ 520 MHz | Result                                |
|----------|--------------|---------------------------------------|
| 0 mV     | 1100 mV      | Stable (baseline)                     |
| −12.5 mV | 1087.5 mV    | ✅ Stable — glmark2 terrain 14fps     |
| −25 mV   | 1075 mV      | ❌ Kernel crash before basic.target   |

**Confirmed stable limit: −12.5 mV → 1087.5 mV** (all 3 OPPs patched uniformly).  
Baseline glmark2 terrain score (stock, no ES): ~17fps off-screen. Undervolted: **14fps** (no crash).

Safety service **cannot** recover GPU undervolt crashes (kernel dies too early).  
Always keep `/boot/rk3326-r36s-linux.dtb.bak` — restoring from SD is the only recovery.

---

## GPU Benchmark Reference

Binary: `glmark2-es2-drm` (2021.02, cross-compiled arm64, custom GBM patches)  
Command for stability test (no EmulationStation):
```bash
systemctl stop emulationstation
/tmp/glmark2-es2-drm-legacy --data-path /tmp/glmark2data --size 320x240 -b terrain:duration=30
systemctl start emulationstation
```

Key scores (off-screen, ES stopped):
| Condition           | terrain fps | Notes                        |
|---------------------|-------------|------------------------------|
| Stock (520 MHz)     | ~17         | baseline                     |
| GPU −12.5 mV UV     | 14–16       | stable, undervolted          |
| GPU OC 600 MHz      | **18**      | +20% vs UV baseline, stable  |

---

## GPU OC — 600 MHz (confirmed working)

**600 MHz is achievable via DTB only — no kernel recompile needed.**

### Clock driver analysis

No GPU rate table exists in `drivers/clk/rockchip/clk-px30.c`. The GPU uses a composite
clock (`clk_gpu_src`) with parent `gpll` (1200 MHz) and an integer divider:

```
gpll (1200 MHz) / 2 = 600 MHz  ✓
```

Unlike the CPU (which needed `rockchip,avs-scale=0` to unblock higher OPPs), the GPU OPP
table has no such restriction. The only limit is what OPP nodes exist in the DTB.

Confirmed by writing `600000000` to `/sys/kernel/debug/clk/clk_gpu/clk_rate` — the clock
driver accepted it immediately, confirming hardware capability.

### DTB change required

Add one node to `/gpu-opp-table`:

```
fdtput -c  /boot/rk3326-r36s-linux.dtb /gpu-opp-table/opp-600000000
fdtput -t u /boot/rk3326-r36s-linux.dtb /gpu-opp-table/opp-600000000 opp-hz 0 600000000
fdtput -t u /boot/rk3326-r36s-linux.dtb /gpu-opp-table/opp-600000000 opp-microvolt 1150000
fdtput -t u /boot/rk3326-r36s-linux.dtb /gpu-opp-table/opp-600000000 opp-microvolt-L2 1150000
```

Voltage used: **1150 mV** — PMIC hard limit for `vdd_logic`. Within `rockchip,max-volt = 1175 mV`.

After reboot, `available_frequencies` shows `600000000 520000000 480000000 400000000` and
devfreq correctly manages the new OPP with proper voltage.

### Benchmark results (L2 bin, on-screen, ES stopped)

| Condition           | Freq    | Voltage   | terrain fps on-screen |
|---------------------|---------|-----------|----------------------|
| Undervolted (stock) | 520 MHz | 1087.5 mV | 14–15                |
| GPU OC (initial)    | 600 MHz | 1150 mV   | 15                   |
| GPU OC (optimized)  | 600 MHz | **1025 mV** | **15**             |

**+20% FPS vs stock UV** (18 fps off-screen). Stable long-term at ~50°C.

### Voltage sweep — complete (L2 bin, on-screen, 30–90s terrain)

Started at PMIC max (1150 mV) and reduced in 12.5 mV steps each reboot:

| Voltage | FPS on-screen | Artifacts | Result |
|---------|---------------|-----------|--------|
| 1150 mV | 15 | No | Stable |
| 1112.5 mV | 15 | No | Stable |
| 1100 mV | 15 | No | Stable |
| 1087.5 mV | 15 | No | Stable |
| 1062.5 mV | 15 | No | Stable |
| 1037.5 mV | 15 | No | Stable |
| **1025 mV** | **15** | **No** | **✅ Stable — confirmed limit** |
| 1012.5 mV | 13 | **Yes** | ❌ Artifacts — do not use |

**Total undervolt: −125 mV** from initial OC voltage (1150 mV → 1025 mV).  
Same silicon margin as CPU UV (also −125 mV on this L2 chip).

**Important:** unlike the stock GPU UV (−12.5 mV limit), the OC voltage sweep has much more
headroom because:
1. The 600 MHz OPP is a separate node — patching it does NOT lower the 400/480/520 MHz OPPs.
2. The stock UV limit was caused by the 400 MHz OPP approaching the PMIC floor (950 mV),
   not by 520 MHz itself needing 1087.5 mV minimum.

**Crash behavior at 1012.5 mV:** visual artifacts (rendering errors), FPS drop to 13.
The device boots normally because the GPU starts at 400 MHz — the crash only occurs when
devfreq scales to 600 MHz under load. Safety service does NOT trigger (boot succeeds).
Recovery: patch DTB back to 1025 mV without reboot (`fdtput` over SSH), no SD card needed.

---

## CPU OC — 1608 MHz (confirmed working)

**1608 MHz is achievable via DTB only — no kernel recompile needed.**

Earlier testing showed the kernel ignoring the 1608 MHz OPP. Root cause was `rockchip,avs-scale=4` in `/cpu0-opp-table`, not the clock driver.

### Mechanism: AVS (Adaptive Voltage Scaling)

`rockchip,avs=1` + `rockchip,avs-scale=4` in the DTB causes the kernel to call
`rockchip_adjust_opp_table(dev, scale_to_rate(4))` = `rockchip_adjust_opp_table(dev, 1512 MHz)`,
which **actively removes all OPPs above 1512 MHz** from the table at boot.

Fix: set `rockchip,avs-scale=0`. The condition `opp_scale(0) < avs_scale(0)` = FALSE → no OPPs removed.

The PX30 clock driver (`drivers/clk/rockchip/clk-px30.c`) already contains 1608 MHz in both
`px30_cpuclk_rates` and `px30_pll_rates` (RK3326 = PX30 same SoC, same driver).

### DTB changes required

1. Add OPP node to `/cpu0-opp-table`:
   ```
   opp-1608000000 { opp-hz = /bits/ 64 <1608000000>; opp-microvolt-L2 = <1350000 1350000 1350000>; }
   ```
2. Change `rockchip,avs-scale` from `4` to `0` in `/cpu0-opp-table`.

Voltage used: **1187.5 mV** (L2 bin, confirmed stable). Conservative starting point is 1350 mV (same as 1512 MHz stock L2); tuner lets user reduce from there.

### Benchmark results — ALU (LCG C, 10s)

| MHz  | Mops | vs 1008 MHz |
|------|------|-------------|
| 1008 | 1500 | 100%        |
| 1200 | 1730 | +15%        |
| 1248 | 1780 | +19%        |
| 1296 | 1920 | +28%        |
| 1512 | 1870 | +25%        |
| 1608 | 1900 | +27%        |

**Sweet spot: 1512 MHz @ 1175 mV (undervolted).** Seven synthetic benchmarks showed 0–2% difference between 1512 and 1608 MHz — ALU throughput saturates at 1512 MHz, Coremark is L2-latency-bound (RAM OC has zero effect on it), L1 pointer chasing shows only +1.8% (theoretical +6.3%). The 1608 MHz benefit is real but only observable in emulation (JIT, multi-thread frame timing) — not in single-thread synthetic tests.
GPU benchmark (terrain) is identical at all CPU frequencies — GPU-limited, not CPU-limited.

### GPU OC

Not tested. `vdd_logic` (shared rail) has an absolute max of 1150 mV — the L0 520 MHz OPP
already uses 1150 mV, leaving zero headroom to add a higher-frequency OPP at a safe voltage.
Possible only if GPU can clock higher at current voltage (1100 mV L2), which is unknown.

---

## RAM / DMC

### DMC OPP table — all bins (mV)

Node: `/dmc-opp-table` · Rail: `vdd_logic` (shared with GPU and SoC logic)  
`rockchip,max-volt = 1150000` · ATF version: `0x105` · Bin active: **L2**

| MHz | L0   | L1   | **L2**   | L3   |
|-----|------|------|----------|------|
| 528 | 975  | 975  | **950**  | 950  |
| 666 | 1050 | 1000 | **975**  | 950  |
| 786 | 1100 | 1050 | **1025** | 1000 |
| **928** | — | — | **987.5** | — |

> 928 MHz row added via OC patch (see DMC OC section below).  
> OPP node values: `opp-microvolt-L2 = 987500`. Confirmed stable floor (L2 bin): **987.5 mV** — see DMC UV sweep below.  
> ATF delivers **924 MHz** (nearest PLL divisor to the requested 928 MHz).

### DMC Undervolt — not worth it

The DMC shares `vdd_logic` with the GPU. The PMIC sets the rail to the maximum demanded by any consumer. When GPU OC is active at 1025 mV, DMC receives that same voltage regardless of its own OPP entry. To effectively lower the rail, both GPU and DMC voltages must be reduced — see [README: vdd_logic shared rail](../README.md#vdd_logic-shared-rail--gpu--ram-oc-voltage). Patching DMC voltage lower than GPU OC has no rail benefit but does set the DMC floor for when GPU OC is not active.

### DMC OC — 928 MHz (confirmed working)

**Previous documentation incorrectly stated "RAM OC not possible via DTB."**

The correct model: ATF owns the *frequency switching* (register writes, DDR training). The kernel DMC devfreq driver determines *which frequencies to expose* from the DTB OPP table. Adding an OPP node causes the kernel to request that frequency via ATF SMC call.

**ATF v0x105 has timing support for 928 MHz LPDDR4.** Confirmed:

1. Added `opp-928000000` node to `/dmc-opp-table`
2. After reboot: `available_frequencies` = `528000000 666000000 786000000 928000000`
3. Set `governor = performance` → `cur_freq = 924000000` — system stable, no hang
4. Ran glmark2 terrain under sustained DMC 924 MHz + GPU 600 MHz — stable, no crash

**DTB changes:**

```bash
fdtput -c  /boot/rk3326-r36s-linux.dtb /dmc-opp-table/opp-928000000
fdtput -t u /boot/rk3326-r36s-linux.dtb /dmc-opp-table/opp-928000000 opp-hz 0 928000000
fdtput -t u /boot/rk3326-r36s-linux.dtb /dmc-opp-table/opp-928000000 opp-microvolt-L2 987500
fdtput -t u /boot/rk3326-r36s-linux.dtb /dmc-opp-table/opp-928000000 opp-microvolt 987500
```

**Benchmark results (terrain off-screen, GPU OC 600 MHz active):**

| Condition | DMC freq | terrain fps | Conclusion |
|-----------|----------|-------------|------------|
| GPU OC only | 786 MHz | 18 | baseline |
| GPU OC + DMC OC | 924 MHz | 18 | terrain = compute-bound |

**RAM bandwidth sweep (128 MB memset + memcpy, compiled C, CPU pinned 1512 MHz, L2 bin):**

| DMC freq | Write MB/s | Copy MB/s | Write delta | Copy delta |
|----------|-----------|-----------|-------------|------------|
| 528 MHz | 3178 | 1176 | base | base |
| 666 MHz | 4044 | 1184 | +27% | +1% |
| 786 MHz | 4768 | 1300 | +50% | +11% |
| **924 MHz** | **5516** | **1597** | **+74%** | **+36%** |

vs stock 786 MHz: write **+15.7%**, copy **+22.8%**. Write scales nearly linearly (pure bus throughput); copy scales less (read+write share the bus). Coremark shows 0% improvement with DMC OC — confirmed L2 latency-bound, not bandwidth-bound.

terrain shows no change because Mali-G31 at 600 MHz is ALU-saturated. Expected benefits in real workloads:
- **Emulation JIT**: CPU reads guest code + emulator state from RAM constantly → real speedup
- **Texture sampling (UMA)**: Mali-G31 reads textures from system RAM each frame → more bandwidth available
- **Loading times**: ROM decompression, save states, asset streaming → pure bandwidth
- **Sustained performance**: CPU + GPU competing for same bus → more headroom for both

**Voltage note:** GPU OC is at 1025 mV (L2 bin confirmed stable floor), DMC OC at 987.5 mV — rail = 1025 mV (GPU wins). Both OCs coexist without conflict. See DMC UV sweep below for full floor data.

### DMC UV Sweep — 928 MHz OPP (L2 bin)

Automated sweep: CPU 1608 MHz, DMC pinned at 924 MHz (`governor=performance`), 128 MB memset+memcpy stress 30 s per step. Starting point: 1075 mV (conservative).

| Voltage | Result | MB/s |
|---------|--------|------|
| 1075 mV | Stable (base) | — |
| 1062.5 mV | ✅ Stable | 2585 |
| 1050.0 mV | ✅ Stable | 2516 |
| 1037.5 mV | ✅ Stable | 2606 |
| 1025.0 mV | ✅ Stable | 2543 |
| 1012.5 mV | ✅ Stable | 2639 |
| 1000.0 mV | ✅ Stable | 2636 |
| **987.5 mV** | **✅ Stable** | **2662** |
| 975.0 mV | ❌ Crash mid-stress | — |

**Confirmed floor: 987.5 mV** (−87.5 mV vs 1075 mV). 975 mV boots OK but crashes under sustained 128 MB RAM stress.

> Temps across steps are not comparable — tests were chained without cooldown between reboots. Rising temps at lower voltages reflect accumulated heat, not voltage effect.

---

## Real-World Gaming Impact — God of War: Ghost of Sparta (PSP / PPSSPP)

Measured in-game via LD_PRELOAD overlay (FPS sampled every second, 10s average per step).  
Device: L2 bin · CPU fixed at 1608 MHz throughout.

### RAM frequency sweep (GPU fixed at 600 MHz)

| DMC freq | FPS avg | Delta vs stock |
|----------|---------|----------------|
| 528 MHz  | 21.2    | baseline       |
| 666 MHz  | 22.9    | +8%            |
| 786 MHz  | 25.6    | +21%           |
| 924 MHz  | 26.7    | +26%           |
| **1032 MHz** | **28.6** | **+35%**   |

### GPU frequency sweep (RAM fixed at 1032 MHz)

| GPU freq | FPS avg | Delta vs 400 MHz |
|----------|---------|------------------|
| 400 MHz  | 24.5    | baseline         |
| 480 MHz  | 26.6    | +9%              |
| 520 MHz  | 26.0    | +6%              |
| **600 MHz** | **28.0** | **+14%**      |

> 480 → 520 MHz shows no gain (within variance). Meaningful steps: 400→480 and 520→600.

### Component impact summary

| Tuning change | FPS gain | Relative impact |
|---------------|----------|-----------------|
| RAM 528 → 1032 MHz | +7.4 FPS | **highest** |
| GPU 400 → 600 MHz  | +3.5 FPS | medium |
| CPU 1200 → 1608 MHz | ~+3 FPS | low |

**RAM dominates in PSP emulation.** CPU and GPU share a UMA bus — every frame the JIT engine writes recompiled code, the GPU reads textures, and the CPU reads guest instructions, all competing for the same physical memory. Bandwidth is the real bottleneck, not compute.

GPU terrain benchmark (synthetic, off-screen) shows **zero** sensitivity to RAM frequency — the Mali-G31 shader is ALU-saturated at 600 MHz. Real-world UMA workloads are a different story.

---

## DTB File Info

```
/boot/rk3326-r36s-linux.dtb        (active — patch target)
/boot/rk3326-r36s-linux.dtb.bak    (original stock — never overwrite)
```

Read a property:
```bash
fdtget -t u /boot/rk3326-r36s-linux.dtb /gpu-opp-table/opp-520000000 opp-microvolt-L2
```

Write a property:
```bash
fdtput -t u /boot/rk3326-r36s-linux.dtb /gpu-opp-table/opp-520000000 opp-microvolt-L2 <value_uv>
```

Verify kernel-loaded value (after reboot):
```bash
python3 -c "import struct; d=open('/proc/device-tree/gpu-opp-table/opp-520000000/opp-microvolt-L2','rb').read(); print(struct.unpack('>I',d[:4])[0])"
```
