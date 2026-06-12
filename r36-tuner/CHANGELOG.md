# R36 Tuner Next — Changelog

## Unreleased

**Workspace / infrastructure:**

- Removed deprecated variants: `variants/screen/` (ELITE HYBRID v1.7) and `variants/gemini/` (Gemini 6.0–8.1).
- Added `tools/deployment/r36_ssh.py` — reusable SSH helper used by all deployment scripts to avoid quoting/encoding bugs.
- Refactored deployment scripts (`deploy_to_r36.py`, `push_script.py`, `push_to_r36.py`, `deploy_overlay.py`, `deploy_ui.py`) to use `r36_ssh.py`.
- Refactored key host-side research scripts to use `r36_ssh.py`: `tools/benchmarks/setup_glmark2.py`, `tools/benchmarks/terrain_test_quick.py`, `tools/undervolt/auto_sweep.py`, `tools/undervolt/voltage_sweep.py`, `tools/gpu/gpu_oc_setup.py`. Remaining benchmark/undervolt/gpu scripts still use raw paramiko and can be migrated gradually.
- Deep-cleaned temporary files: `assets/fb0.raw`, `assets/screenshot.*`, loose ISO in workspace root, `rk3326-r36s-linux.dtb.teacup_backup`, `overclock-r36s/`, `firmware/os-images/`, and old `src/ui/tuner_ui/tuner_ui` binary.
- Added automatic remote-services setup on the device: `r36-remote-services.service` starts SSH/SMB/Filebrowser at boot when network is available, plus a NetworkManager dispatcher that starts them if WiFi is connected later.
- Deployed experimental SDL2 UI (`src/ui/tuner_ui/main.c`) to `/opt/system/tuner_ui` with launchers `R36 Tuner UI.sh` and `launch_tuner.sh`.
- Merged session findings into `r36-tuner/docs/session-2026-06-11.md` and condensed `AGENTS.md`.
- Added `r36-tuner/docs/kernel-build.md` with permanent build notes for the patched teacupx kernel.
- Added `tools/README.md` as a quick index of host-side scripts.

**SDL2 UI (`src/ui/tuner_ui/main.c`):**

- Feat: Window title and header renamed from `R36 Tuner` to `R36 Tuner Next`; product subtitle left unchanged.
- Feat: Dynamic OS subtitle reads `/etc/hostname` and shows `RK3326 | DARKOSRE`, `RK3326 | DARKOS`, `RK3326 | ARKOS`, etc.
- Feat: ES/EN i18n system with `StringID` enum, `S(id)` macro, and persistence in `/etc/r36_tuner_ui_lang`. Default language is English; added a main-menu language selector.
- UI: `submenu()` now supports a `center` flag so most lists (governor, DTB tuning, voltage selectors, recovery) are vertically centered, while CPU/GPU max-frequency lists keep top alignment.
- UI: Confirmation screens replaced simple Yes/No dialogs with `confirm_screen()` showing a summary, optional data table, warnings, infos, and large Apply/Cancel buttons for CPU UV, CPU OC, GPU OC, RAM OC, restore, and reboot prompts.
- UI: OPP diagnostic screen renamed to `OPP Voltage Table`, converted to a read-only styled table, and now compares DTB on-disk voltages against kernel-active voltages in three columns: `Frequency | DTB (disk) | Kernel (now)`. Rows with mismatched voltages are highlighted.
- UI: Recovery screen converted from a fake selectable table to a read-only scrollable instructions view.
- Fix: Main menu item-height calculation adjusted so the new Language item is not cut off.
- Fix: `tools/deployment/deploy_ui.py` now stops any running `tuner_ui` process before overwriting `/opt/system/tuner_ui`.
- Fix: `tools/deployment/r36_ssh.py` tolerates `chmod: Operation not permitted` when the destination binary is busy/running, as long as the uploaded file already has the requested mode.

**Bug fixes:**

- Fix: RAM OC confirm dialog showed "9280 MHz" instead of "928 MHz" due to `${FREQ_HZ:0:4}` string slice (928000000[:4] = "9280"). Changed to `$(( FREQ_HZ / 1000000 ))`.
- Fix: RAM OC success dialog (post-patch reboot prompt) had the same `${FREQ_HZ:0:4}` truncation bug — a second independent instance. Fixed same way.
- Fix: CPU benchmark restored the governor after the run unconditionally, including writing `"N/A"` to `scaling_governor` if the governor could not be read at benchmark start. Added guard `[ -n "$GOV_PREV" ] && [ "$GOV_PREV" != "N/A" ]`.
- Fix: `InstallGlmark2Legacy` copied shaders from `/usr/share/glmark2/shaders/` without checking the directory exists. If `glmark2-data` was not installed, the glob silently produced nothing and `glmark2-es2-drm-legacy` would fail with an opaque error. Now shows a clear error dialog directing the user to run GPU Benchmark first.
- Fix: `InstallGlmark2` and `BenchmarkGPU` used `echo ark | sudo -S` to call `dpkg` and `bash`. The script already runs as root via `exec sudo` at startup — the `sudo -S` was redundant and briefly exposed the password in the process list. Replaced with direct calls.
- Fix: CPU OC first-apply voltage selector truncated half-millivolt steps — "1187 mV" instead of "1187.5 mV". Added fractional formatting (`frac % 1000 == 500`) consistent with all other voltage menus.
- Fix: CPU benchmark wrote `0` to the baseline file when `gcc` was unavailable and the binary could not be compiled. Baseline is now only written when `SCORE > 0`.
- Fix: GPU benchmark pending result dialog had a Spanish title ("RESULTADO") in an otherwise English UI. Changed to "RESULT".
- Fix: `val_mv` floor in the boot-service script raised from 800 mV to 950 mV, matching the actual PMIC hardware minimum for `vdd_arm`/`vdd_logic`. A manually crafted profile with sub-950 mV values could previously pass validation and be applied at boot.
- Fix: RAM OC menu now offers "Tune 924 MHz voltage" or "Add 1032 MHz [EXPERIMENTAL]" when 924 MHz OC is already active but 1032 MHz is not. Previously the menu went straight to voltage tuning with no way to add the second OPP.

**Code quality:**

- Clarify: `apply_reg` in the boot service script had `[ -z "$dir" ] || ! val_mv "$mv" && return`. Due to `&&` having higher precedence than `||` in bash, the empty-dir case did not return on that line (returned on the next `[ ! -w ... ]` check instead). Rewrote as `{ [ -z "$dir" ] || ! val_mv "$mv"; } && return` — behaviour unchanged, intent now explicit.
- Refactor: extracted `CompileCPUBench()` helper. The LCG C source and `gcc` invocation were duplicated verbatim between `BenchmarkCPU` and `StressTestCPU`. Both functions now call `CompileCPUBench` — a single definition, same binary path, same behaviour.

## v4.3 — 2026-05-27

**Bug fix:**

- Fix: Bin detection now falls back to `pvtm-volt-sel=N` dmesg pattern for newer dArkOSRE kernels (04262026 and later) that no longer emit the `opp-binning: using OPP prop name` log line. Both detection paths write to the bin cache — works correctly on all kernel versions. Thanks to u/skyrent for the bug report.

## v4.2 — 2026-05-27

**New features:**

- Feat: CPU OC, GPU OC and RAM OC menus now detect whether the OPP node already exists in the DTB. If it does (OC was previously applied), the menu skips the info and setup screens and goes directly to a voltage selector showing the current voltage. This allows tuning the OC voltage at any time without re-reading the setup documentation. Applies to all three OC paths: CPU 1608 MHz, GPU 600 MHz, RAM 928 MHz.
- Feat: CPU benchmark result now shows a note when running at 1608 MHz explaining that scores at 1512 and 1608 MHz may be similar due to ALU pipeline ceiling, and that real benefit varies by workload (emulation).

**Research findings (no script changes):**

- Research: Seven synthetic benchmarks run to measure CPU 1512 MHz vs 1608 MHz performance difference: LCG 4-chain ALU, Coremark 1.0, Coremark + RAM OC (786 vs 924 MHz DMC), EMU branch random, EMU branch pattern, L1 pointer chasing (16 KB), and guest sim. None reliably measured the difference. LCG hits an ALU pipeline throughput ceiling at 1512 MHz. Coremark hits an L2 cache latency ceiling (latency is fixed in nanoseconds, not clock cycles — RAM OC confirmed to have 0% effect on Coremark). L1 pointer chasing showed +1.8% at 1608 vs 1512 MHz (theoretical maximum: +6.3%). Conclusion: the A35 in-order pipeline hits a ceiling before 1608 MHz on every synthetic workload tested. The CPU OC benefit is real but only observable in actual emulation (JIT recompilation, multi-thread frame timing) — not measurable with single-thread benchmarks.
- Research: DMC OC 928 MHz voltage sweep (opp-microvolt-L2, L2 bin, 128 MB memset+memcpy stress 30 s pinned at 924 MHz). Floor confirmed at **987.5 mV** (−87.5 mV vs conservative starting point of 1075 mV). 975 mV boots but crashes under full RAM stress. vdd_logic rail is shared between GPU and DMC — with GPU OC at 1025 mV and DMC OC at 987.5 mV, the rail is set by the GPU (1025 mV wins). Results are chip-specific (L2 bin, leakage=13).

## v4.1 — 2026-05-23

**Fixes and improvements:**

- Fix: Benchmark and DTB Tuning submenus now loop back to themselves after an action completes, instead of jumping to the main menu. Back button still exits to the main menu.
- Fix: Main menu now shows the shadow and blue backtitle bar, matching all other submenus (was using `--no-shadow` without `--backtitle`).
- Fix: Console font changed from `Lat7-TerminusBold22x11` to `Lat7-TerminusBold20x10`. The 22px font left an 18px black strip at the bottom of the 480px screen (480 ÷ 22 = 21.8 rows). The 20px font divides evenly (480 ÷ 20 = 24 rows) — no strip, and one extra line of screen space.
- Fix: Gamepad button presses between dialogs no longer print characters to the console or scroll the screen. `stty -echo` is applied on startup and restored on exit.
- Feat: RAM benchmark rewritten as a compiled C program (same pattern as CPU benchmark). Replaces `dd`/tmpfs with direct `memset` and `memcpy` on a 128 MB buffer, 3 seconds each. Eliminates kernel filesystem overhead and syscall-per-MB cost — measures actual memory subsystem bandwidth. Reports write (memset) and copy (memcpy) in MB/s, logged to history.

## v4.0 — 2026-05-23

**Startup splash:**

- Fix: show "R36 Tuner vX.X / Loading..." immediately after font loads, so the 2-second gamepad init wait has visible feedback instead of a blank screen.
- Perf: `DetectOPPBinProp` now checks the bin cache file first before calling `dmesg` — bin is a silicon property and never changes, so cache is always valid. Skips dmesg on every run after first boot.
- Perf: removed redundant `sudo` prefix from `chmod` and `setfont` in UI setup — script already runs as root via `exec sudo` at startup.

**UI polish:**

- Fix: Real-Time Monitor rewritten with pure ASCII box drawing (Unicode box characters rendered as double-width on tty1, causing line wrap and misalignment). Box is now centered based on actual terminal dimensions (`stty size`). Each line positioned with absolute ANSI cursor escape sequences. Trend indicators changed from Unicode arrows (↑↓→) to ASCII (`^` `v` `~`).
- Fix: Extra blank row removed from CPU Max Freq, CPU Min Freq, CPU Governor, GPU Max Freq, and Benchmark menus (dialog height was COUNT+7; corrected to COUNT+6).
- Fix: CPU Max Freq menu subtitle "Voltage auto via OPP | Voltage menu for undervolt" removed — subtitle is now "★ = current".
- Fix: "GPU Tuning" renamed to "GPU Max Freq" in the main menu and all error dialogs.

## v3.9 — 2026-05-23

**Bug fixes found during release audit:**

- Fix: GPU benchmark score log showed wrong MHz value. The runner script used `cat /sys/class/devfreq/*/max_freq | head -1` — the glob expands alphabetically, returning `dmc` (924 MHz) before `ff400000.gpu` (600 MHz). Score logs now correctly show `GPU=600MHz` instead of `GPU=924MHz`. Changed to a name-pattern loop matching `*gpu*|*mali*|*ff400000*`.
- Fix: `ValidateUndervolt()` showed empty temperature fields (`Temp: min °C  avg °C  peak °C`) when CPU stress test aborted due to thermal throttle. `StressTestCPU` now exports the partial temperature stats (min/avg/peak collected up to the abort point) before returning with exit code 1.

## v3.8 — 2026-05-23

**OPP bin detection rewritten — important reliability fix:**

- Fix: `DetectOPPBinProp()` now uses a three-tier fallback instead of guessing from `/proc/device-tree`. Previous fallback iterated L0→L3 and took the first bin that existed in the DTB — since all bins are present in the DTB, this always returned L0 regardless of the active bin. On a chip with bin L2 (like the R36S L2/leakage=13), patching with L0 voltage tables is incorrect. New priority order: **(1)** dmesg (authoritative — kernel logs actual bin at boot) → **(2)** cache file `/etc/r36_tuner_bin` (persists across dmesg rotation) → **(3)** generic `opp-microvolt` with abort (safe, no wrong-bin patch).
- Fix: When bin is detected from dmesg, it is now saved to `/etc/r36_tuner_bin`. On future script runs where the dmesg ring buffer has rotated, the cached value is used. A single clean boot is enough to populate the cache permanently.
- Fix: If neither dmesg nor the cache file can provide the bin (e.g. first run on a device with a rotated dmesg), all five patching paths (CPU UV, GPU UV, CPU OC, GPU OC, RAM OC) now abort with a clear message: *"Reboot the device — bin will be detected and cached automatically."* No changes are made. Previously, the wrong bin (L0) would be silently patched.
- Fix: CPU OC, GPU OC and RAM OC info screens now show the bin-not-detected warning inline with the status (instead of blocking before the screen). If the OC is not yet active and the bin is unknown, the dialog shows `[OK]` instead of `[Yes]/[No]` — the user sees the current OC state but cannot apply a patch until they reboot. If the OC is already active, no warning is shown.
- Fix: glmark2 legacy binary now installed to `/usr/local/bin/glmark2-es2-drm-legacy` and shader data to `/usr/local/share/glmark2data/` (persistent). Previously extracted to `/tmp/` on every session — cleared on each reboot, causing a re-extraction delay on first GPU benchmark use after every boot.

## v3.7 — 2026-05-23

**Reliability fixes from full code audit — all users should update:**

- Fix: OPP bin detection now has `/proc/device-tree` fallback when dmesg ring buffer has rotated (long uptime). Previously, if the `pvtm-volt-sel` message was no longer in dmesg, all DTB patches silently wrote `opp-microvolt` instead of the bin-specific `opp-microvolt-LX` — kernel ignores `opp-microvolt` when binning is active, so patches had no effect. New `DetectOPPBinProp()` function used in all 5 patching paths (CPU UV, GPU UV, CPU OC, GPU OC, RAM OC).
- Fix: CPU OC 1608 MHz now writes both bin-specific (`opp-microvolt-LX`) and generic (`opp-microvolt`) voltage properties on the new OPP node, consistent with GPU OC and RAM OC. Prevents silent OPP failure on kernels that fall back to the generic property.
- Fix: CPU Stress Test now uses the C ALU benchmark (same LCG code as CPU benchmark) instead of `openssl speed sha256`. OpenSSL SHA256 uses ARMv8 hardware crypto — it bypasses the ALU pipeline and does not trigger voltage-related instability. Real-world effect: a 1175 mV / 1608 MHz configuration that fails the C stress in 15s was passing the SHA256 stress for the full 5 minutes. Stress test now catches marginal voltages correctly.
- Fix: CPU Stress Test now fails with a clear error message if neither gcc (for C benchmark) nor openssl is available, instead of running an empty loop and reporting STABLE.
- Fix: DMC OC status detection and active-frequency check now use the dynamic `$DMC_DEVFREQ` path instead of the hardcoded `/sys/class/devfreq/dmc/` string. Prevents `[ACTIVE]` display from breaking if the devfreq node name differs.
- Fix: glmark2 legacy binary extraction now includes SHA256 integrity check after base64 decode. A corrupt extraction (truncated binary) no longer silently executes as root.
- Fix: CPU benchmark now shows a clear error message when gcc is not installed, instead of silently returning N/A.
- New: hardware pre-flight warning at startup if `/proc/device-tree/compatible` does not contain `rockchip,rk3326` or `rockchip,px30` — alerts users who might run the script on an unsupported device.

**UI fixes:**
- Fix: GPU UV menu title showed "Stock 520 MHz = ? mV" — variable scope error (`$OPP_BIN_PROP` used where `$GPU_BIN_PROP` was needed)
- Fix: ViewProfile dialog height corrected (content was clipped on some configurations)
- Fix: main menu height corrected after removing unused header row and Voltage Info entry
- Fix: all dialog box heights audited and corrected across the script

## v3.6 — 2026-05-22

**Bug fixes and UI polish:**

- Fix: GPU OC voltage menu showed "Stock 520 MHz = ? mV" — was reading undefined variable `$OPP_BIN_PROP` instead of `$GPU_BIN_PROP` (display-only bug, patch logic was correct)
- Fix: Benchmark history header showed wrong unit "MB/s" for CPU score (correct: Mops/10s)
- Fix: Benchmark menu item 1 label said "sha256" — benchmark is int ALU (C, LCG), sha256 was removed in v2.9
- Safety: added `sync` after all DTB fdtput operations (5 functions) — prevents losing patch data if device loses power before manual reboot
- UI: all user-facing text unified to English

## v3.5 — 2026-05-21

**Full voltage range in all OC/UV menus — no hardcoded limits:**

- CPU OC 1608 MHz voltage: expanded from 4 options (1275–1350 mV) to full hardware range 950–1350 mV in 12.5 mV steps
- GPU OC 600 MHz voltage: expanded to full vdd_logic range 950–1150 mV in 12.5 mV steps
- CPU UV uniform offset: expanded to -200 mV → +50 mV in 12.5 mV steps (was -125 → +50 mV)
- CPU UV fine-tune per-freq: same full range
- GPU UV uniform offset: same full range
- GPU UV fine-tune per-OPP: same full range
- All menus now show your chip's current stock voltage as reference point
- PMIC floor corrected: 950 mV (was 700 mV) — matches real hardware minimum for vdd_arm and vdd_logic
- No recommended voltages — silicon lottery applies. Start high, go down gradually.

**Research: CPU OC 1608 MHz — voltage sweep (L2 bin, leakage=13):**

- Sweep performed with real C stress (4 cores, ALU+FP+branch, 300s)
- 1200 mV: stable 300s | 1187.5 mV: stable 300s | 1175 mV: stable 60s but fails 300s | 1162.5 mV: crash <10s
- Confirmed floor: **1187.5 mV** (-112.5 mV vs stock 1300 mV) for sustained load
- Battery droop effect: low battery → higher internal resistance → voltage sag under load → instability at borderline voltages. Charge fully before sweeping.
- These are ONE chip's results — your chip may differ (silicon lottery)

**Research: GPU UV fine-tune — 480 MHz and 520 MHz (L2 bin):**

- 520 MHz: stable down to **950 mV** (PMIC floor = -150 mV vs stock 1100 mV) — tested on-screen terrain, no artifacts
- 480 MHz: stable at **962.5 mV** (same as 400 MHz OPP) — tested on-screen terrain, no artifacts
- Key insight: uniform UV was limited by 400 MHz OPP hitting PMIC floor during boot. Fine-tuning 480/520 MHz independently allows deeper UV since those OPPs are only used post-boot.
- 400 MHz: floor remains 962.5 mV (boot stability — other SoC components on vdd_logic need ≥962.5 mV during init)

**Recommended flow:**

- For overclocking: enable CPU OC 1608 MHz + GPU OC 600 MHz + RAM OC 928 MHz at safe voltages first, then reduce gradually until you find your chip's stable limit
- For battery savings / thermals: use CPU Undervolt and GPU Undervolt on stock frequencies
- Always reboot and stress-test after each voltage change

## v3.4 — 2026-05-21

**Research: GPU OC 600 MHz — complete voltage sweep (L2 bin):**

- Full undervolt sweep from 1150 mV down to 1012.5 mV in 12.5 mV steps (on-screen, ES stopped, 30–90s terrain)
- Confirmed stable limit: **1025 mV** (−125 mV from PMIC max) — 15 fps on-screen, no artifacts
- Artifacts at: 1012.5 mV (rendering errors, fps drop to 13) — do not use
- Total undervolt: −125 mV — same silicon margin as CPU UV on this L2 chip
- Key insight: OC has much more voltage headroom than stock GPU UV because the 600 MHz OPP is isolated — patching it does NOT lower the 400/480/520 MHz OPPs (stock UV was limited by 400 MHz OPP approaching PMIC floor)
- Crash behavior at 1012.5 mV: device boots fine (GPU starts at 400 MHz), artifacts appear only when devfreq scales to 600 MHz under load — safety service does NOT trigger
- Recovery at any failed voltage: patch DTB via SSH without reboot (`fdtput` to restore 1025 mV)
- Updated `docs/opp-research.md` with complete sweep table and analysis

## v3.3 — 2026-05-21

**Feat: RAM OC 928 MHz — `DTBDMCOC()` integrated into DTB menu:**

- DMC OC confirmed working: ATF v0x105 supports 928 MHz — delivers 924 MHz (nearest PLL divisor)
- New menu item "RAM OC 928 MHz" in DTB Tuning submenu
- Menu item shows `[ACTIVE]` if 928 MHz is present in DMC `available_frequencies`
- `DTBDMCOC()`: adds `opp-928000000` to `/dmc-opp-table`; no equivalent of `avs-scale` needed
- Voltage selector: 1075 / 1062.5 / 1050 mV. vdd_logic is shared with GPU — no extra voltage cost when GPU OC is active at 1150 mV
- +18% RAM bandwidth over stock 786 MHz. Benefit: CPU JIT, texture reads, emulator loading times
- GPU compute-bound workloads (terrain): no fps change (confirmed). Mixed emulation workloads: real benefit
- Same backup/safety-service/reboot flow as all other DTB patches

**Note: prior docs incorrectly stated "RAM OC not possible via DTB":**

- ATF owns the *frequency switching*, but the kernel *exposes available frequencies from the DTB OPP table*
- Adding an OPP node → kernel requests it → ATF executes the switch. Confirmed working.

## v3.2 — 2026-05-21

**Feat: GPU OC 600 MHz — integrated into DTB menu (`DTBGPUOC()`):**

- New menu item "GPU OC 600 MHz" in DTB Tuning submenu
- Menu item shows `[ACTIVE]` suffix if 600 MHz is already in GPU `available_frequencies`
- `DTBGPUOC()`: adds `opp-600000000` to `/gpu-opp-table` — no `rockchip,avs-scale` needed (GPU has none)
- `opp-hz`: 0 600000000 (64-bit, gpll/2 = 600 MHz exactly)
- Voltage selector: 950–1150 mV in 12.5 mV steps. Start at 1150 mV (PMIC vdd_logic max), reduce gradually.
- Writes both `opp-microvolt-L2` (binned) and generic `opp-microvolt` for compatibility
- Same safety net: backup preserved, safety service, reboot prompt
- State detection: ACTIVE / OPP in DTB pending reboot / not patched

## v3.1 — 2026-05-21

**Discovery: GPU OC 600 MHz — confirmed stable via DTB only:**

- GPU composite clock uses `gpll (1200 MHz) / 2 = 600 MHz` — no rate table in driver, no kernel changes needed
- Unlike CPU OC, GPU has no `rockchip,avs-scale` — adding `opp-600000000` to `/gpu-opp-table` is sufficient
- Voltage: 1150 mV (`opp-microvolt-L2`) — PMIC hard limit for `vdd_logic`, within `rockchip,max-volt = 1175 mV`
- Result: **18 fps** terrain off-screen vs 15–16 fps @ 520 MHz undervolted (**+20%**), stable at 62°C
- devfreq correctly exposes `600000000` in `available_frequencies` after reboot
- Updated `docs/opp-research.md` and `README.md` with GPU OC findings and voltage table

## v3.0 — 2026-05-20

**Feat: CPU OC 1608 MHz — re-added to DTB menu with correct mechanism:**

- Previous implementation (v1.8) added the OPP node but did not clear `rockchip,avs-scale=4`, which caused the kernel to strip all OPPs >1512 MHz at boot
- New `DTBCPUOC()` function: adds `opp-1608000000` node AND sets `rockchip,avs-scale=0`
- Voltage selector: 950–1350 mV in 12.5 mV steps. Start high, reduce gradually.
- Silicon lottery warning: not all R36S units will be stable at the same voltage
- Menu item shows `[ACTIVE]` suffix if 1608 MHz is already in `scaling_available_frequencies`
- Same safety net as undervolt: backup preserved, safety service active, reboot prompt

## v2.9 — 2026-05-20

**Discovery: CPU OC 1608 MHz works via DTB — no kernel recompile needed:**

- Root cause of the v1.8 failure identified: `rockchip,avs-scale=4` in `/cpu0-opp-table` caused the kernel to call `rockchip_adjust_opp_table(dev, 1512 MHz)` at boot, actively stripping all OPPs above 1512 MHz
- Fix: set `rockchip,avs-scale=0` + add `opp-1608000000` node — clock driver already had 1608 MHz in `px30_cpuclk_rates`/`px30_pll_rates`
- Benchmark: 1608 MHz = +27% vs 1008 MHz, but only +1.6% over 1512 MHz — sweet spot remains 1512 MHz undervolted
- Updated `docs/opp-research.md` and `README.md` with correct findings

**Feat: CPU benchmark replaced with compiled C ALU benchmark:**

- Previous SHA256 (hardware crypto, memory-bound) and Python sieve (interpreter-bound) did not scale with CPU frequency
- New benchmark: LCG integer loop compiled with `gcc -O2` on first use, cached at `/tmp/r36_cpubench`
- Pure ALU, fits in registers — scales linearly with MHz (confirmed: 1008→1608 MHz = +27%)
- Runs 10s, reports Mops (millions of operations/10s)
- Forces `performance` governor before measuring, restores original after

**Feat: GPU Undervolt Validation now uses on-screen terrain test:**

- `ValidateGPUUndervolt` replaced off-screen glmark2 with on-screen terrain via glmark2 2021.02 legacy binary
- On-screen rendering detects visual artifacts, color corruption, and GPU instability that off-screen cannot catch
- glmark2 2021.02 (arm64, patched for Mali GBM) embedded as base64 — ~960KB stripped
- New `InstallGlmark2Legacy()` extracts and caches binary on first use
- Result screen shows fps, baseline (stock ~17fps), and STABLE/UNSTABLE verdict

**Fix: glmark2 2021.02 shader compatibility with glmark2-data 2023.01:**

- `glmark2-data 2023.01` shaders use `MEDIUMP_OR_DEFAULT`/`HIGHP_OR_DEFAULT` macros undefined in the 2021.02 binary → Mali compiler error, 0 fps
- `InstallGlmark2Legacy()` creates `/tmp/glmark2data/` with patched shader copies and symlinks to models/textures
- Terrain on-screen confirmed: **14 fps** at -12.5 mV GPU undervolt

**Fix: ValidateGPUUndervolt — EmulationStation stop/start required sudo:**

- `systemctl stop/start emulationstation` failed with "Interactive authentication required" when called without sudo
- Fixed: both calls now use `echo ark | sudo -S systemctl ...`

**bin/glmark2-es2-drm-legacy — pre-compiled binary added to repo:**

- glmark2 2021.02 cross-compiled for arm64 (AArch64, Cortex-A35), stripped — 985752 bytes
- Target: R36S / RK3326 / dArkOSRE (Mali-G31 GBM, legacy KMS, OpenGL ES 3.2)
- Toolchain: Ubuntu 24.04, aarch64-linux-gnu-g++
- Patches: `#include <utility>` (GCC 13); GBM format from EGL `NATIVE_VISUAL_ID`; `flip()` via `drmModeSetCrtc`
- BuildID: `8afd801061043c089ef1881c7e61974f71535d24`

## v2.8 — 2026-05-20

**Menu cleanup — removed stale/dead entries:**

- OC Experiment (1608 MHz) removed from DTB menu — kernel was ignoring the OPP due to `avs-scale` (root cause found and fixed in v3.0)
- DMC / RAM Tuning removed from main menu — ATF owns DMC frequency switching, sysfs writes have no effect (DTB OPP approach discovered in v3.3)
- Voltage Info converted to read-only — OPP framework reverts all runtime writes, display only
- GPU Info removed from Benchmark — internal debug tool, not useful for end users
- Main menu: 13 → 12 items

**Dead code removal:**

- Removed orphaned functions: `DTBOCApply`, `DMCTuningMenu`, `SetVoltForReg`, `ApplyVolt`, `GPUInfo`, `GetDMCAvail`
- Removed OC_PENDING startup check and variable
- -258 lines of dead code

## v2.7 — 2026-05-19

**Feat: GPU UV menu — Uniform and Fine Tune modes (same as CPU):**

- Mode selector: Uniform (same offset for all OPPs) / Fine Tune (per OPP)
- 12.5 mV steps, range -125 mV to +50 mV
- Preview before confirming: shows all OPPs with voltage before → after
- Patches only the active bin (GPU_BIN_PROP), same as CPU
- Correctly preserves multi-value props (min/typ/max) via loop

**Fix: GPU OPP table verified from real device:**

- Confirmed 3 OPPs: 400 MHz (975 mV L2) / 480 MHz (1050 mV L2) / 520 MHz (1100 mV L2)

## v2.6 — 2026-05-19

**Critical fix: `DTBGPUUndervoltMenu` was patching only `opp-400000000`:**

- GPU has 3 OPPs: 400 MHz (975 mV L2), 480 MHz (1050 mV L2), 520 MHz (1100 mV L2)
- Bug: alphabetical sort selected `opp-400000000` first → GPU at max freq (520 MHz) was never patched → undervolt had no effect at normal workloads
- Fix: reads all OPPs into arrays, patches all (same offset)
- Menu now shows full table of all 3 OPPs with current voltages

## v2.5 — 2026-05-19

**Fix: `GetDTBStatus()` now detects GPU undervolt in addition to CPU:**

- Before: only compared CPU OPP 1512 MHz voltage — if only GPU was patched, status showed "stock"
- Now: also compares `/gpu-opp-table/opp-520000000` with backup
- Combined format: "CPU -125mV (1175mV) | GPU -25mV (1075mV)"
- Correct status shown in main menu item 7 and in Validate GPU UV

## v2.4 — 2026-05-19

**Feat: ValidateGPUUndervolt — off-screen terrain test ~30s:**

- New item in BenchmarkMenu: "Validate GPU UV — terrain ~30s + recommendation"
- Runs only the terrain scene off-screen (~30s), parses real fps
- Shows result + recommendation: test with a real game (RetroArch, PPSSPP, DraStic)
- Saves entry to history (`GPU-UV X fps`)

**Fix: GPU UV confirm dialog showed wrong offset:**

- `${OFFSET_UV/1000/}` (string replace) → `$(( OFFSET_UV / 1000 ))` (arithmetic)
- Example: -125 mV was showing as "-125000 mV"

**Discovery: glmark2 on-screen requires legacy KMS cross-compile:**

- glmark2 2023 (bundled) uses atomic KMS — RK3326 only supports legacy KMS → on-screen rendering not possible with the 2023 binary
- Solution: cross-compiled glmark2 2021.02 on Windows via WSL + `aarch64-linux-gnu-gcc 13.3` toolchain
- 2021.02 uses `drmModeSetCrtc()` (legacy KMS) instead of atomic → compatible with RK3326
- Source fix required: `#include <utility>` missing in `libmatrix/program.h` (GCC 13 incompatibility)
- Resulted in arm64 ELF binary, integrated in v2.9

## v2.3 — 2026-05-19

**Improvement: GPU benchmark — reduce duration from 5 min to ~1 min:**

- Uses 4 representative scenes: build, texture, shading, terrain
- `-b scene:duration=15` per scene instead of ~30s default
- Result shows FPS per scene + final score

**Improvement: GPU benchmark — glmark2-es2-drm --off-screen (real GPU measurement):**

- Replaced fake Python pbuffer benchmark (measured ctypes overhead, not GPU) with `glmark2-es2-drm --off-screen --size 320x240`
- Real score: ~401 pts (full scene suite)
- Rationale for `--off-screen`: glmark2 2023 uses atomic KMS; RK3326 BSP only supports legacy KMS → `--off-screen` avoids modesetting failure
- Embedded binary updated: `glmark2-es2-wayland 2023.01` → `glmark2-es2-drm 2023.01+dfsg-1 arm64`
- Embedded data updated: `glmark2-data 2014.03` → `glmark2-data 2023.01+dfsg-1`

## v2.2 — 2026-05-19

**Improvement: GPU benchmark — redesigned to work with EmulationStation active:**

- The Mali-G31 GBM driver blocks `open()` on card0/renderD128 while ES holds DRM master
- Solution: launch benchmark as a systemd service (`r36-gpu-bench.service`) with its own cgroup under `/system.slice/` — independent of ES
- Flow: confirm → create service → ES stops → `chvt 1` + `sleep 1` (fbcon recovers display) → EGL/GBM benchmark on card0 → ES restarts

## v2.1 — 2026-05-16

**Fix: missing shebang `#!/bin/bash`:**

- The BOM/CRLF fix commit (7379122) rebuilt the file without the opening `#!`
- Kernel could not determine the interpreter → black screen on launch
- Fix: restored `#!/bin/bash` on line 1

**Fix: GPU benchmark — replaced glmark2-es2-fbdev with glmark2-es2-drm:**

- dArkOSRE uses libmali GBM variant (`libmali-bifrost-g31-rxp0-gbm.so`) + DRM/KMS
- No fbdev EGL backend exists → `glmark2-es2-fbdev` failed with `eglGetDisplay() error 0x3000`
- Fix: embedded `glmark2-es2-drm` (Debian Bookworm arm64, v2023.01)
- DRM confirmed: `/dev/dri/card0`, `renderD128`; framebuffer: 640×480
- GPU benchmark now detects real framebuffer resolution via `/sys/class/graphics/fb0/virtual_size`

**Improvement: GPU Info in Benchmark menu:**

- New option "GPU Info" — shows DRM, framebuffer, EGL/Mali libs, `/dev/mali0`

## v2.0 — 2026-05-16

**Fix: script failed to launch on device:**

- PowerShell introduced UTF-8 BOM and CRLF when writing the base64 — bash on Linux rejected the shebang
- Fix: rebuilt with UTF-8 no-BOM, pure LF

**Fix: wrong architecture (armhf → arm64):**

- dArkOSRE is arm64 (confirmed by kernel `Image` in /boot, not `zImage`)
- Replaced glmark2-es2-fbdev armhf binary with arm64 build

**Feat: glmark2-es2-fbdev bundled (no WiFi required):**

- glmark2-es2-fbdev and data files embedded in the script as base64
- Launching GPU benchmark without glmark2 installed → prompts to install
- Auto-installs via `dpkg -i` from embedded data, no internet needed
- Self-extracts via `awk` + `base64 -d` + `dpkg -i` — no external dependencies

## v1.9 — 2026-05-16

**Feat: GPU Undervolt (DTB):**

- New option in DTB menu: "GPU Undervolt — patch GPU OPP (vdd_logic)"
- RK3326 Mali-G31 OPP at 520 MHz — stock L2: 1100 mV
- Patches all bins (L0/L1/L2/L3 + generic) with the same relative offset
- GPU bin detected from dmesg; falls back to CPU bin (same L2 on this device)
- Automatic discovery of GPU OPP node in DTB (`/gpu-opp-table` + scan)
- Safety service reused; backup protected same as CPU undervolt

## v1.8 — 2026-05-16

**Feat: OC Experiment — 1608 MHz:**

- New option in DTB Undervolt menu: "OC Experiment — 1608 MHz [EXPERIMENTAL]"
- Adds `opp-1608000000` OPP node to DTB at stock 1512 MHz voltage (1300 mV L2)
- At startup, the script checks whether the kernel accepted the frequency via `scaling_available_frequencies`
- Shows message: "1608 MHz ACCEPTED" if present, "1608 MHz IGNORED (clock driver cap)" if not
- Note: `rockchip,avs-scale` was not cleared in this version — kernel stripped the OPP at boot regardless. Root cause found and fixed in v3.0.
- Safety service reused: auto-restores DTB if boot fails

## v1.7 — 2026-05-16

**Feat: DTB status in main menu:**

- Item 7 shows active voltage delta: `stock`, `-125mV (1175mV)`, etc.
- Detected by comparing current DTB vs .bak at the 1512 MHz OPP
- Updated every time the main menu is re-entered

**Feat: Validate Undervolt — guided flow:**

- CPU benchmark (60s) → 5 min stress → STABLE/FAILED verdict in one step
- Final summary shows active DTB, MHz, mV and temperatures (min/avg/peak)

**Feat: Stress test temperature statistics:**

- Now records min, average and peak over the 5-minute run
- Result: `min 42°C  avg 48°C  peak 54°C`

**Feat: Monitor temperature trend:**

- ↑↓→ arrow next to temperature: indicates rising, falling or stable trend
- ±1°C threshold to filter noise in stable readings

## v1.6 — 2026-05-16

**Feat: Benchmark — scrollable and clearable history:**

- View History uses `dialog --textbox` (navigable with gamepad, all entries)
- New "Clear History" option — clears log and baseline with confirmation

## v1.5 — 2026-05-16

**Feat: CPU Stress — 5-minute duration:**

- Increased from 60s to 300s to detect real thermal instability under sustained load
- Thermal abort at 85°C retained

## v1.4 — 2026-05-16

**Feat: CPU benchmark — 60s duration:**

- `openssl speed -seconds 60 sha256` instead of the default (~10s)
- Allows temperature to stabilize — useful for comparing thermals with/without undervolt
- More accurate score (more iterations averaged)

## v1.3 — 2026-05-16

**Fix: black screen when launching tuner after DTB auto-restore:**

- gptokeyb started AFTER startup checks → "DTB auto-restored" dialog appeared without active gamepad → msgbox with no way to close it → script hung on black screen
- Fix: gptokeyb now starts before startup checks (+ sleep 1 to allow input)
- Same bug affected the "boot profile failed" warning

## v1.2 — 2026-05-16

**Feat: DTB Undervolt — Fine Tune mode:**

- New patch mode: "Fine tune" → per-frequency selector
- Each OPP entry (1008/1200/1248/1296/1416/1512 MHz) has its own independent offset
- Allows -150 mV at low frequencies and -125 mV at the high end if that's the limit
- Menu shows the current state of each frequency during editing (offset + resulting voltage)
- Existing "Uniform" mode kept as a separate option

**Feat: 12.5 mV step size (PMIC RK805 minimum):**

- Both modes (Uniform and Fine Tune) use 12.5 mV steps instead of 25 mV
- Internally in µV for exact precision without floating-point arithmetic
- Range: -125 mV to +50 mV in 12.5 mV steps

## v1.1 — 2026-05-16

**Feat: CPU Stress Test:**

- New option in Benchmark: 60s sustained load via `openssl sha256` loop
- Automatic thermal abort at 85°C with warning
- Shows MHz, mV and peak temperature on completion — validates undervolt stability

**Feat: Benchmark cleanup:**

- Removed gzip: bottleneck was `/dev/urandom` (slow RNG), not CPU — results were not representative
- Removed AES-256: uses same ARMv8 crypto instructions as SHA256, redundant metric
- CPU benchmark = SHA256 only: clean, reproducible, consistent

**Fix: Diagnose:**

- Diagnose showed `opp-microvolt` (generic table ignored by kernel) instead of `opp-microvolt-L2`
- Now shows actual values for the active bin both on disk and in kernel
- Header indicates which property is being read

## v1.0 — 2026-05-16

First stable public release.

- File renamed from `R36 Tuner v2.0.sh` to `R36 Tuner.sh` — version is tracked inside the script
- Versioning reset to 1.0: the 2.x numbering was internal development only, this is the first public release
- Includes everything from internal phases v2.0–v2.4: CPU/GPU/DMC tuning, voltage menu, DTB undervolt with OPP bin detection, safety service anti-bootloop, benchmarks with history and baseline, boot profile with panic-flag, real-time monitor

---

## Development history (pre-release)

Internal development snapshots that preceded the v1.0 public release.

### v2.4 (pre-release) — 2026-05-16

**DTB undervolt — safety service:**

- `SetupDTBSafetyService()`: installs two systemd services after applying a DTB patch
  - `r36-dtb-safety.service` (before=basic.target): if it detects a `BOOTING` flag from the previous boot → auto-restores `.bak` before userspace starts
  - `r36-dtb-confirm.service` (after=multi-user.target): if boot reached this point, clears the `BOOTING` flag (undervolt confirmed stable)
- `TeardownDTBSafetyService()`: cleans up services and flags on restore or after auto-recovery
- On tuner startup: detects `DTB_RESTORED` and alerts the user
- Backup preserves the **original** DTB: `.bak` only created if it doesn't exist — successive patches never overwrite the original

**DTB menu — restructured as submenu:**

- Diagnose and Help were buried at the end of the offset list (required scrolling)
- Now: top-level submenu with `Patch / Diagnose / Emergency Recovery / Restore` — all options visible immediately
- Offset selector only appears when choosing Patch

**Emergency Recovery:**

- New option in DTB menu: step-by-step instructions to recover the device from a PC if it won't boot
- Same information added to README in a dedicated section

### v2.3 (pre-release) — 2026-05-16

**DTB undervolt — OPP binning support:**

- Detects active bin from dmesg (`pvtm-volt-sel`) → patches `opp-microvolt-L2` (or the correct level) instead of `opp-microvolt`, which the kernel ignores when binning is active
- Table in menu 7 shows active bin voltages, not generic values
- Diagnose shows filtered dmesg (opp/volt/dvfs) as a second screen

**Benchmark — relative score and history:**

- SHA256 now in MB/s (was KB/s with large decimals)
- First run auto-sets baseline (100%)
- Subsequent runs show % vs baseline with delta +/-
- Each run saved to `/etc/r36_tuner_scores.log` with date, MHz, mV, governor, temp
- New benchmark menu options: Set Baseline, View History (last 20 runs)

### v2.2 (pre-release) — 2026-05-16

**DTB Undervolt fixes — verified against real dArkOSRE DTB:**

- DTB OPP discovery: added `/opp-table-0` candidate; fallback scan now detects both `opp@*` and `opp-*` child naming styles
- OPP entries: filter and freq extraction now handle `opp-<hz>` (dash) format used by RK3326 mainline — was root cause of "no OPP entries found"
- Restored `-t u` flag on `fdtget` calls — required to parse u32 arrays; without it returns binary garbage
- Confirmed real DTB structure: `/cpu0-opp-table` with entries at 1008/1200/1248/1296/1416/1512 MHz; `opp-microvolt` is 3-value `[min, typ, max]`

### v2.1 (pre-release) — 2026-05-15

**Bug fixes:**

- `PROF_STATUS` now calls `systemctl is-enabled` — no longer shows `✓ on` when service file exists but is disabled
- Boot script validates `CPU_GOV` against `scaling_available_governors` before writing — prevents invalid governor writes
- `BenchmarkCPU` openssl grep changed to `grep -i "sha256" | grep -v "^Doing" | tail -1` — compatible with OpenSSL 1.x and 3.x output formats

**New features:**

- `CPU Min Freq` menu — set `scaling_min_freq` for real eco mode (floor frequency when idle)
- `View Saved Profile` — read `/etc/r36_tuner.ini` directly from the menu
- `CPU_MIN_KHZ` persisted in boot profile and applied at startup
- Monitor now shows CPU min freq row
- `gptokeyb` path detected dynamically via `command -v` — falls back to `/opt/inttools/` if not in PATH

### v2.0 (pre-release) — 2026-05-15

First full-featured build.

- CPU Governor selector (performance / schedutil / ondemand / conservative / powersave)
- Governor persisted in boot profile and applied at startup via systemd
- Startup detection of failed boot profiles — warns user and offers cleanup
- Overheat warning in live monitor at ≥80°C
- Benchmark "Run All" mode — CPU + RAM + GPU in sequence
- `*mali*` added to GPU devfreq discovery (wider hardware compatibility)
- Profile status indicator in main menu (`✓ on` / `off`)

### Earlier iterations

Exploratory versions establishing sysfs paths, regulator discovery, voltage write safety, and dialog UI patterns. Contained known instabilities in voltage handling — not suitable for public release.
