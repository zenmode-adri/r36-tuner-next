# R36 Tuner Next — Changelog

## v1.8 — 2026-06-17

### teacupx boot.ini integration

- New **CPU OC (boot.ini)** entry in DTB Tuning menu — appears only when `/boot/boot.ini` is detected (teacupx kernel installed)
- Frequency selector: 1368 / 1416 / 1440 / 1464 / 1488 / 1512 MHz with current value highlighted
- Writes `max_cpufreq=` to boot.ini; appends the key if not already present
- Confirm screen before any write; takes effect on next reboot

### GPU benchmark EGL fix

- Fixed GPU benchmark on Panel 4 v22 (and any device where `libEGL.so` points to Mesa/Panfrost): runner script now uses the Mali blob directly, matching the v1.7 launcher fix

### teacupx battery warning

The teacupx DTB has two battery miscalibrations on dArkOSRE-R36: it ships the RG351P OCV table (wrong cell chemistry, 4.0V vs 4.2V), and sets the low-battery cutoff to 3000 mV instead of 3300 mV. The battery percentage will be inaccurate, and the device runs to the absolute cell minimum before shutting down — leaving no margin against deep discharge from standby current after power-off. See README for details.

### Internal hardening

- OPP voltage scan now rejects out-of-range values from `fdtget` — prevents "0 mV" entries in the voltage table if fdtget returns an empty or malformed value
- DTB backup and voltage patch code deduplicated into shared helpers
- Chip bin (L0–L3) now visible in DTB confirm screens
- More specific error messages for backup and patch failures
- Magic number constants for all frequency and voltage thresholds

---

## v1.1 — 2026-06-15

### Self-contained launcher (no WiFi / no apt needed)

- `R36 Tuner Next.sh` is now a self-extracting archive (~10 MB): `fdtget`, `fdtput`, `r36_cpubench`, `r36_rambench`, `glmark2-es2-drm-legacy` and glmark2 data are all embedded as base64 payloads
- On first launch, tools are extracted to `/usr/local/bin/` and `/usr/local/share/glmark2data/`. A stamp file prevents re-extraction on subsequent launches
- Users need no internet connection, no `apt`, no `gcc` — drag `tuner_ui` + `R36 Tuner Next.sh` to the SD card and launch

### CPU Fine-Tune

- New **CPU Fine-Tune** screen in DTB Tuning menu: select individual CPU OPP frequencies (1008 / 1200 / 1248 / 1296 / 1512 MHz) and set a specific voltage for each one independently
- Complements the existing uniform undervolt: use UV for a quick all-OPP offset, Fine-Tune for precise per-frequency floors
- Voltage picker pre-selected at the current DTB value; step size 12.5 mV, floor 950 mV
- Patches the bin-specific `opp-microvolt-Lx` property (3-tuple) for the selected OPP only; all other OPPs untouched
- Same backup / safety net / confirm flow as all other DTB patches
- Fixed: OPP list was shown lowest-first; now shows highest frequency first (1512 MHz at top)

### RAM OC 1032 MHz [EXPERIMENTAL]

- New option in the RAM OC menu once 928 MHz is already active: apply a second OPP node at 1040 MHz (ATF delivers **1032 MHz**, nearest PLL divisor)
- Requires **1150 mV** on `vdd_logic` — the PMIC hard ceiling for this rail; no undervolt margin is possible at this frequency
- Voltage picker available: user can choose any value from floor to 1150 mV at their own risk (hardware cannot be damaged — `vdd_logic` is the SoC DMC controller supply, not the RAM chip supply)
- Remove options: remove only the 1032 MHz node, or remove all RAM OC (restores stock 786 MHz)
- Measured PPSSPP improvement vs stock 786 MHz: +12% FPS average (God of War: Ghost of Sparta, L2 bin)

## v1.0 — 2026-06-14

Initial release of the SDL2 native UI for R36S / RK3326.

### GPU benchmark

- Off-screen mode via `glmark2-es2-drm --off-screen` — no DRM master needed, ES stays alive, tuner_ui stays alive during the benchmark
- Live progress screen while benchmark runs: scene counter (`Scene X/4: name`), spinner, animated progress bar (fills per completed scene), elapsed timer. Press `[B]` to cancel
- GPU min_freq pinned to max_freq during the run so devfreq governor cannot scale down
- Score file (`/home/ark/.r36_tuner_ui_scores.log`) chowned to `ark` after write by the root systemd service, so subsequent CPU/RAM writes from `tuner_ui` (runs as `ark`) do not silently fail
- Result screen matches CPU/RAM style: large score, GPU MHz, temperature columns (Initial / Average / Peak)

### DTB safety net

- Hardened `r36-dtb-safety.sh`: fixed inverted logic that restored the original DTB backup on every successful boot, silently removing GPU/CPU/RAM OC after the second reboot
- Now correctly: `BOOTING` present → clear both flags + sync + exit; `PENDING` present → mv to `BOOTING` + sync + exit
- Added `sync` after flag removal; clears both `BOOTING` and `PENDING` if they coexist

### RAM benchmark

- Fixed `cur_freq` → `max_freq` for DDR MHz display. With `simple_ondemand` governor, `cur_freq` drops to base when tuner_ui is idle, so it showed ~400 MHz even with 900 MHz OC active
- Result screen: buttons now render below all text — `btn_y = max(panel_bottom_fixed, cy + 4)` prevents overlap when content height exceeds panel space

### CPU OC

- Corrected all "1608 MHz" labels to "CPU OC (teacupx)" throughout the UI
- Added warning screen before first apply: stock dArkOSRE kernel caps at ~1296 MHz regardless of DTB patch; real OC above 1296 MHz requires [teacupx kernel](https://github.com/teacupx/overclock-r36s) (max 1512 MHz)
- Menu description updated: "DTB patch + avs-scale (teacupx required)"
- DTB patch mechanics unchanged: `opp-1608000000` node + `rockchip,avs-scale=0`

### Earlier SDL2 UI features (all in this release)

- Native CPU benchmark: 30s integer ALU chain (LCG ×4), compiled C, async with live temperature sampling. Score in Mops/30s with CPU MHz tag
- Native RAM benchmark: 128 MB memset + memcpy bandwidth test, compiled C. Write and copy MB/s, DDR MHz, temperatures
- Score history: results saved to `/home/ark/.r36_tuner_ui_scores.log` with date, type badge (CPU/RAM/GPU), detail and temperature range. Clear History action via `[Select]`
- CPU max freq screen: detects whether frequencies above 1296 MHz are real (teacupx) or software-only (stock). Tags fake entries `(fake)`; `1296 MHz` entry tagged `silicon max` when stock kernel detected
- DTB tuning: CPU undervolt, GPU OC 600 MHz, RAM OC 928 MHz, OPP voltage table viewer, emergency recovery screen, one-tap restore
- OPP voltage table: reads DTB on-disk voltages vs kernel-active voltages, highlights mismatches
- Score history type badge distinguishes CPU (blue) / RAM (purple) / GPU (orange)
- Confirmation screens with data table, warnings and infos for all DTB patches
- i18n: English / Spanish, persisted in `/etc/r36_tuner_ui_lang`
- Real-time monitor: CPU temp, GPU MHz, RAM MHz. Overheat warning at ≥ 80 °C
- Save profile → applies at every boot via systemd service
- Fail-safe: panic flag detects boot hangs and auto-disables the profile
