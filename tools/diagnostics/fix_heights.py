#!/usr/bin/env python3
# Fix dialog heights in R36 Tuner Next.sh
# All replacements use exact string matching on the full line content.
# Encoding: UTF-8 (critical — previous crash was from default system codec)

import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
path = os.path.join(ROOT, 'r36-tuner', 'R36 Tuner Next.sh')

with open(path, encoding='utf-8') as f:
    content = f.read()

original = content

def r(old, new, ctx=""):
    global content
    count = content.count(old)
    if count == 0:
        print(f"MISS [{ctx}]: {repr(old[:80])}")
    elif count > 1:
        print(f"AMBIG [{ctx}] ({count}x): {repr(old[:80])}")
    else:
        content = content.replace(old, new)
        print(f"OK [{ctx}]")

# ── Static msgbox/yesno/menu fixes ────────────────────────────────────────────

# L363: GPU OPP not found in DTB  8->7
r('--msgbox "GPU OPP table not found in DTB.\\n\\nSearched: /gpu-opp-table and variants." 8 50',
  '--msgbox "GPU OPP table not found in DTB.\\n\\nSearched: /gpu-opp-table and variants." 7 50',
  "L363")

# L392: No OPP entries in GPU_OPP  6->5
r('--msgbox "No OPP entries found in ${GPU_OPP}" 6 50',
  '--msgbox "No OPP entries found in ${GPU_OPP}" 5 50',
  "L392")

# L434: GPU UV uniform menu  20->19  (3 text lines + 10 list = 6+3+10=19)
r('            --menu "Applied to ${N} OPPs  |  Step: 12.5 mV\\nFloor: 950 mV (vdd_logic PMIC min)\\nStart conservative — go down gradually." \\\n            20 62 10',
  '            --menu "Applied to ${N} OPPs  |  Step: 12.5 mV\\nFloor: 950 mV (vdd_logic PMIC min)\\nStart conservative — go down gradually." \\\n            19 62 10',
  "L434")

# L499: GPU fine tune offset menu  20->18  (2 text lines + 10 list = 6+2+10=18)
r('                --menu "Stock: ${stock_mv} mV  |  Floor: 950 mV (PMIC)\\nSelect offset:" \\\n                20 60 10',
  '                --menu "Stock: ${stock_mv} mV  |  Floor: 950 mV (PMIC)\\nSelect offset:" \\\n                18 60 10',
  "L499-GPU")

# L562: GPU patched yesno  11->10  (6 text lines)
r('--yesno "GPU patched successfully.\\nBackup: ${DTB}.bak\\n\\nSafety net active: if boot hangs,\\nnext boot auto-restores original DTB.\\n\\nReboot now?" 11 54',
  '--yesno "GPU patched successfully.\\nBackup: ${DTB}.bak\\n\\nSafety net active: if boot hangs,\\nnext boot auto-restores original DTB.\\n\\nReboot now?" 10 54',
  "L562")

# L566: GPU patch failed  6->5
r('--msgbox "Patch failed. Restoring backup..." 6 45 > "$CURR_TTY"\n        cp "${DTB}.bak" "$DTB"\n    fi\n}\n\n# ── CPU Tuning',
  '--msgbox "Patch failed. Restoring backup..." 5 45 > "$CURR_TTY"\n        cp "${DTB}.bak" "$DTB"\n    fi\n}\n\n# ── CPU Tuning',
  "L566-GPU-UV")

# L577: Cannot read CPU scaling_available_frequencies (CPUTuningMenu)  6->5
r('--title "CPU Tuning" \\\n            --msgbox "Cannot read $CPU_POLICY/scaling_available_frequencies" 6 55',
  '--title "CPU Tuning" \\\n            --msgbox "Cannot read $CPU_POLICY/scaling_available_frequencies" 5 55',
  "L577")

# L614: Cannot read CPU min freq  6->5
r('--title "CPU Min Frequency" \\\n            --msgbox "Cannot read $CPU_POLICY/scaling_available_frequencies" 6 55',
  '--title "CPU Min Frequency" \\\n            --msgbox "Cannot read $CPU_POLICY/scaling_available_frequencies" 5 55',
  "L614")

# L643: CPU min > max  6->5
r('--msgbox "Min freq cannot exceed max freq ($(( MAX_KHZ / 1000 )) MHz)." 6 52',
  '--msgbox "Min freq cannot exceed max freq ($(( MAX_KHZ / 1000 )) MHz)." 5 52',
  "L643")

# L659: CPU governor not found  7->6  (2 text lines)
r('--msgbox "Cannot read available governors from:\\n$CPU_POLICY/scaling_available_governors" 7 55',
  '--msgbox "Cannot read available governors from:\\n$CPU_POLICY/scaling_available_governors" 6 55',
  "L659")

# L697: GPU devfreq not found  7->6  (2 text lines)
r('--msgbox "GPU devfreq not found.\\nSearched: *gpu*  *mali*  *ff400000*" 7 52',
  '--msgbox "GPU devfreq not found.\\nSearched: *gpu*  *mali*  *ff400000*" 6 52',
  "L697")

# L704: Cannot read GPU available_frequencies  6->5
r('--msgbox "Cannot read $GPU_DEVFREQ/available_frequencies" 6 58',
  '--msgbox "Cannot read $GPU_DEVFREQ/available_frequencies" 5 58',
  "L704")

# L746: VoltageMenu runtime voltages  14->12  (8 text lines)
r('           --msgbox "Runtime voltages (read-only — OPP framework owns these rails):\\n\\nvdd_arm   — CPU cores  : ${ARM_MV} mV\\nvdd_logic — SoC / GPU  : ${LOGIC_MV} mV\\nvcc_ddr   — RAM        : ${DDR_MV} mV\\n\\nTo change voltages permanently:\\n  → DTB Tuning (previous menu)" \\\n           14 58',
  '           --msgbox "Runtime voltages (read-only — OPP framework owns these rails):\\n\\nvdd_arm   — CPU cores  : ${ARM_MV} mV\\nvdd_logic — SoC / GPU  : ${LOGIC_MV} mV\\nvcc_ddr   — RAM        : ${DDR_MV} mV\\n\\nTo change voltages permanently:\\n  → DTB Tuning (previous menu)" \\\n           12 58',
  "L746")

# L792: Emergency recovery msgbox  24->21  (17 text lines, terminal=21)
r('            --msgbox "IF DEVICE WON\'T BOOT after DTB undervolt:\\n\\n1. Power off the R36S\\n2. Remove the system SD card\\n3. Plug SD into PC via card reader\\n4. Open the FAT32 partition (= /boot)\\n   If not visible: use DiskGenius (free)\\n5. Inside /boot you will find:\\n     rk3326-r36s-linux.dtb      <- bad\\n     rk3326-r36s-linux.dtb.bak  <- original\\n6. Copy .bak over .dtb (overwrite)\\n7. Delete .r36_dtb_patch_booting if exists\\n8. Eject SD, reinsert, boot\\n\\nThe .bak is always the pre-patch original.\\nSafety service auto-restores if boot hangs\\nbut cannot act if kernel panics early." \\\n            24 62',
  '            --msgbox "IF DEVICE WON\'T BOOT after DTB undervolt:\\n\\n1. Power off the R36S\\n2. Remove the system SD card\\n3. Plug SD into PC via card reader\\n4. Open the FAT32 partition (= /boot)\\n   If not visible: use DiskGenius (free)\\n5. Inside /boot you will find:\\n     rk3326-r36s-linux.dtb      <- bad\\n     rk3326-r36s-linux.dtb.bak  <- original\\n6. Copy .bak over .dtb (overwrite)\\n7. Delete .r36_dtb_patch_booting if exists\\n8. Eject SD, reinsert, boot\\n\\nThe .bak is always the pre-patch original.\\nSafety service auto-restores if boot hangs\\nbut cannot act if kernel panics early." \\\n            21 62',
  "L792")

# L800: DTB restore yesno  11->10  (6 text lines)
r('--yesno "Restore original DTB from backup?\\n\\n${DTB}.bak → $DTB\\n\\nSafety service will also be disabled.\\nReboot required." 11 55',
  '--yesno "Restore original DTB from backup?\\n\\n${DTB}.bak → $DTB\\n\\nSafety service will also be disabled.\\nReboot required." 10 55',
  "L800")

# L815: Install dtc yesno  9->7  (3 text lines)
r('--yesno "device-tree-compiler not installed.\\n\\nInstall now? (~500KB, requires internet)" 9 55',
  '--yesno "device-tree-compiler not installed.\\n\\nInstall now? (~500KB, requires internet)" 7 55',
  "L815")

# L821: dtc install failed  6->5
r('--msgbox "Install failed. Check internet connection." 6 48',
  '--msgbox "Install failed. Check internet connection." 5 48',
  "L821")

# L830: DTB not found  6->5
r('--msgbox "DTB file not found in /boot/" 6 45',
  '--msgbox "DTB file not found in /boot/" 5 45',
  "L830")

# L854: OPP table not found  10->8  (4 text lines)
r('--msgbox "OPP table not found in DTB.\\n\\nRoot nodes scanned:\\n$ROOT_NODES" 10 60',
  '--msgbox "OPP table not found in DTB.\\n\\nRoot nodes scanned:\\n$ROOT_NODES" 8 60',
  "L854")

# L904: No OPP entries in OPP_BASE  6->5
r('--msgbox "No OPP entries found in $OPP_BASE" 6 48',
  '--msgbox "No OPP entries found in $OPP_BASE" 5 48',
  "L904")

# L1006: CPU UV uniform menu  20->19  (3 text lines + 10 list = 19)
r('            --menu "Applied to all ${N} OPPs  |  Step: 12.5 mV\\nFloor: 950 mV (PMIC min)\\nStart conservative — go down gradually." \\\n            20 62 10',
  '            --menu "Applied to all ${N} OPPs  |  Step: 12.5 mV\\nFloor: 950 mV (PMIC min)\\nStart conservative — go down gradually." \\\n            19 62 10',
  "L1006")

# L1073: CPU fine tune offset menu  20->18  (2 text lines + 10 list = 18)
r('                --menu "Stock: ${stock_mv} mV  |  Floor: 950 mV (PMIC)\\nSelect offset:" \\\n                20 60 10',
  '                --menu "Stock: ${stock_mv} mV  |  Floor: 950 mV (PMIC)\\nSelect offset:" \\\n                18 60 10',
  "L1073-CPU")

# L1138: DTB patched yesno  11->10  (6 text lines)
r('--yesno "DTB patched successfully.\\nBackup: ${DTB}.bak\\n\\nSafety net active: if boot hangs, next boot\\nauto-restores original DTB.\\n\\nReboot now to apply?" 11 52',
  '--yesno "DTB patched successfully.\\nBackup: ${DTB}.bak\\n\\nSafety net active: if boot hangs, next boot\\nauto-restores original DTB.\\n\\nReboot now to apply?" 10 52',
  "L1138")

# L1142: CPU UV patch failed  6->5
r('--msgbox "Patch failed. Restoring backup..." 6 45 > "$CURR_TTY"\n        cp "${DTB}.bak" "$DTB"\n    fi\n}\n\n# ── CPU OC',
  '--msgbox "Patch failed. Restoring backup..." 5 45 > "$CURR_TTY"\n        cp "${DTB}.bak" "$DTB"\n    fi\n}\n\n# ── CPU OC',
  "L1142")

# L1184: CPU OC voltage menu  18->19  (was too small: 3 text lines + 10 list = 19)
r('        --menu "Stock 1512 MHz = ${STOCK_MV} mV (your chip)\\nStart high — go down gradually.\\nToo low = may not boot (safety service helps)." \\\n        18 62 10',
  '        --menu "Stock 1512 MHz = ${STOCK_MV} mV (your chip)\\nStart high — go down gradually.\\nToo low = may not boot (safety service helps)." \\\n        19 62 10',
  "L1184")

# L1195: CPU OC confirm yesno  15->13  (9 text lines)
r('--yesno "Apply CPU OC 1608 MHz @ ${VOLT_MV} mV\\n\\nDTB changes:\\n  + $OPP_BASE/opp-1608000000\\n    ${OPP_BIN_PROP} = ${VOLT_MV} ${VOLT_MV} ${VOLT_MV} mV\\n  + rockchip,avs-scale = 0\\n\\n${BAK_NOTE}\\nReboot required." 15 60',
  '--yesno "Apply CPU OC 1608 MHz @ ${VOLT_MV} mV\\n\\nDTB changes:\\n  + $OPP_BASE/opp-1608000000\\n    ${OPP_BIN_PROP} = ${VOLT_MV} ${VOLT_MV} ${VOLT_MV} mV\\n  + rockchip,avs-scale = 0\\n\\n${BAK_NOTE}\\nReboot required." 13 60',
  "L1195")

# L1219: CPU OC patched yesno  12->11  (7 text lines)
r('--yesno "1608 MHz OPP added @ ${VOLT_MV} mV\\nrockchip,avs-scale → 0\\nBackup: ${DTB}.bak\\n\\nSafety net active.\\n\\nReboot now to activate?" 12 52',
  '--yesno "1608 MHz OPP added @ ${VOLT_MV} mV\\nrockchip,avs-scale → 0\\nBackup: ${DTB}.bak\\n\\nSafety net active.\\n\\nReboot now to activate?" 11 52',
  "L1219")

# L1223: CPU OC patch failed  6->5
r('--msgbox "Patch failed. Restoring backup..." 6 45 > "$CURR_TTY"\n        cp "${DTB}.bak" "$DTB"\n    fi\n}\n\n# ── GPU OC',
  '--msgbox "Patch failed. Restoring backup..." 5 45 > "$CURR_TTY"\n        cp "${DTB}.bak" "$DTB"\n    fi\n}\n\n# ── GPU OC',
  "L1223")

# L1248: GPU OPP not found in DTB (DTBGPUOC)  6->5
r('--msgbox "GPU OPP table not found in DTB." 6 48',
  '--msgbox "GPU OPP table not found in DTB." 5 48',
  "L1248")

# L1278: GPU OC 600MHz yesno  20->18  (worst case STATE_MSG=3 lines + 11 fixed = 14 lines)
r('        --yesno "${STATE_MSG}Mechanism: gpll/2 = 600 MHz exactly\\n(no kernel recompile needed)\\n\\nvdd_logic is SHARED with SoC logic.\\nVoltage margin is tight — use conservative\\nvoltage, especially if also undervolting GPU.\\n\\nSafety service protects against boot hangs\\nbut NOT against early kernel panics.\\n\\nContinue?" 20 58',
  '        --yesno "${STATE_MSG}Mechanism: gpll/2 = 600 MHz exactly\\n(no kernel recompile needed)\\n\\nvdd_logic is SHARED with SoC logic.\\nVoltage margin is tight — use conservative\\nvoltage, especially if also undervolting GPU.\\n\\nSafety service protects against boot hangs\\nbut NOT against early kernel panics.\\n\\nContinue?" 18 58',
  "L1278")

# L1295: GPU OC voltage menu  18->19  (was too small: 3 text lines + 10 list = 19)
r('        --menu "Stock 520 MHz = ${STOCK_GPU_MV} mV (your chip)\\nStart high — go down gradually.\\nvdd_logic shared: too low = may not boot." \\\n        18 62 10',
  '        --menu "Stock 520 MHz = ${STOCK_GPU_MV} mV (your chip)\\nStart high — go down gradually.\\nvdd_logic shared: too low = may not boot." \\\n        19 62 10',
  "L1295")

# L1308: GPU OC confirm yesno  14->13  (9 text lines)
r('--yesno "Apply GPU OC 600 MHz @ ${VOLT_STR} mV\\n\\nDTB changes:\\n  + $GPU_OPP/opp-600000000\\n    opp-hz: 0 600000000\\n    ${GPU_BIN_PROP} = ${VOLT_STR} mV\\n\\n${BAK_NOTE}\\nReboot required." 14 58',
  '--yesno "Apply GPU OC 600 MHz @ ${VOLT_STR} mV\\n\\nDTB changes:\\n  + $GPU_OPP/opp-600000000\\n    opp-hz: 0 600000000\\n    ${GPU_BIN_PROP} = ${VOLT_STR} mV\\n\\n${BAK_NOTE}\\nReboot required." 13 58',
  "L1308")

# L1335: GPU OC patch failed  6->5
r('--msgbox "Patch failed. Restoring backup..." 6 45 > "$CURR_TTY"\n        cp "${DTB}.bak" "$DTB"\n    fi\n}\n\n# ── DMC',
  '--msgbox "Patch failed. Restoring backup..." 5 45 > "$CURR_TTY"\n        cp "${DTB}.bak" "$DTB"\n    fi\n}\n\n# ── DMC',
  "L1335")

# L1352: DMC OPP not found  6->5
r('--msgbox "DMC OPP table not found in DTB." 6 48',
  '--msgbox "DMC OPP table not found in DTB." 5 48',
  "L1352")

# L1381: DMC OC 928MHz yesno  22->19  (worst case STATE_MSG=3 lines + 12 fixed = 15 lines)
r('        --yesno "${STATE_MSG}ATF v0x105 confirmed to support this frequency.\\nKernel requests 928 MHz — ATF delivers 924 MHz\\n(nearest PLL divisor).\\n\\nvdd_logic SHARED with GPU. When GPU OC is active\\n(1150 mV), no extra voltage cost for DMC OC.\\n\\n+18% RAM bandwidth over 786 MHz.\\nBenefits: CPU JIT, texture reads, emulator loading.\\nGPU compute-bound workloads: no fps change.\\n\\nContinue?" 22 60',
  '        --yesno "${STATE_MSG}ATF v0x105 confirmed to support this frequency.\\nKernel requests 928 MHz — ATF delivers 924 MHz\\n(nearest PLL divisor).\\n\\nvdd_logic SHARED with GPU. When GPU OC is active\\n(1150 mV), no extra voltage cost for DMC OC.\\n\\n+18% RAM bandwidth over 786 MHz.\\nBenefits: CPU JIT, texture reads, emulator loading.\\nGPU compute-bound workloads: no fps change.\\n\\nContinue?" 19 60',
  "L1381")

# L1398: DMC OC voltage menu  18->19  (was too small: 3 text lines + 10 list = 19)
r('        --menu "Stock 786 MHz = ${STOCK_DMC_MV} mV (your chip)\\nStart high — go down gradually.\\nvdd_logic shared: too low = may not boot." \\\n        18 62 10',
  '        --menu "Stock 786 MHz = ${STOCK_DMC_MV} mV (your chip)\\nStart high — go down gradually.\\nvdd_logic shared: too low = may not boot." \\\n        19 62 10',
  "L1398")

# L1411: DMC OC confirm yesno  14->13  (9 text lines)
r('--yesno "Apply RAM OC 928 MHz (ATF: 924 MHz) @ ${VOLT_STR} mV\\n\\nDTB changes:\\n  + $DMC_OPP/opp-928000000\\n    opp-hz: 0 928000000\\n    ${DMC_BIN_PROP} = ${VOLT_STR} mV\\n\\n${BAK_NOTE}\\nReboot required." 14 58',
  '--yesno "Apply RAM OC 928 MHz (ATF: 924 MHz) @ ${VOLT_STR} mV\\n\\nDTB changes:\\n  + $DMC_OPP/opp-928000000\\n    opp-hz: 0 928000000\\n    ${DMC_BIN_PROP} = ${VOLT_STR} mV\\n\\n${BAK_NOTE}\\nReboot required." 13 58',
  "L1411")

# L1436: DMC OC patch failed  6->5
r('--msgbox "Patch failed. Restoring backup..." 6 45 > "$CURR_TTY"\n        cp "${DTB}.bak" "$DTB"\n    fi\n}\n\n# ── Real-Time Monitor',
  '--msgbox "Patch failed. Restoring backup..." 5 45 > "$CURR_TTY"\n        cp "${DTB}.bak" "$DTB"\n    fi\n}\n\n# ── Real-Time Monitor',
  "L1436")

# L1565: CPU results msgbox  10->9  (5 text lines)
r('        --msgbox "Config: ${MHZ} MHz  vdd_arm: ${MV} mV  gov: ${GOV}\\nTemp: ${TEMP}°C\\n\\nALU (int32) : ${SCORE_DISP}\\n${REL_DISP}" \\\n        10 62',
  '        --msgbox "Config: ${MHZ} MHz  vdd_arm: ${MV} mV  gov: ${GOV}\\nTemp: ${TEMP}°C\\n\\nALU (int32) : ${SCORE_DISP}\\n${REL_DISP}" \\\n        9 62',
  "L1565")

# L1645: glmark2 not found yesno  7->6  (2 text lines)
r('--yesno "glmark2-es2-drm not found.\\nInstall from bundled package (~20s)?" 7 52',
  '--yesno "glmark2-es2-drm not found.\\nInstall from bundled package (~20s)?" 6 52',
  "L1645")

# L1648: GPU bench install failed msgbox  7->6  (2 text lines)
r('--msgbox "Install failed.\\nManual install: apt install glmark2-es2-drm" 7 52',
  '--msgbox "Install failed.\\nManual install: apt install glmark2-es2-drm" 6 52',
  "L1648")

# L1652: GPU bench confirm yesno  10->9  (5 text lines)
r('--yesno "GPU benchmark (glmark2-es2-drm --off-screen).\\nDuration: ~1 min. Black screen — normal.\\nResult shown on next menu open.\\n\\nContinue?" 10 58',
  '--yesno "GPU benchmark (glmark2-es2-drm --off-screen).\\nDuration: ~1 min. Black screen — normal.\\nResult shown on next menu open.\\n\\nContinue?" 9 58',
  "L1652")

# L1712: Set baseline yesno  8->7  (3 text lines)
r('--yesno "Run CPU benchmark now and save result as baseline (100%)?\\n\\nThis will replace any existing baseline." 8 55',
  '--yesno "Run CPU benchmark now and save result as baseline (100%)?\\n\\nThis will replace any existing baseline." 7 55',
  "L1712")

# L1721: No scores msgbox  7->6  (2 text lines)
r('--msgbox "No scores recorded yet.\\nRun a CPU benchmark first." 7 50',
  '--msgbox "No scores recorded yet.\\nRun a CPU benchmark first." 6 50',
  "L1721")

# L1748: History cleared msgbox  7->6  (2 text lines)
r('--msgbox "Score history and baseline deleted.\\nNext benchmark run will set a new baseline." 7 52',
  '--msgbox "Score history and baseline deleted.\\nNext benchmark run will set a new baseline." 6 52',
  "L1748")

# L1757: CPU stress infobox  7->8  (was too small: 4 text lines needs 8)
r('        --infobox "Burning CPU for ${DURATION}s (5 min) via openssl...\\nSafety: auto-abort at 85°C\\n\\nLet it run — don\'t press anything." 7 52',
  '        --infobox "Burning CPU for ${DURATION}s (5 min) via openssl...\\nSafety: auto-abort at 85°C\\n\\nLet it run — don\'t press anything." 8 52',
  "L1757")

# L1764: Thermal abort msgbox  9->8  (4 text lines)
r('--msgbox "THERMAL ABORT at ${T}°C\\n\\nUndervolt may be unstable at this load.\\nTry a smaller offset." 9 50',
  '--msgbox "THERMAL ABORT at ${T}°C\\n\\nUndervolt may be unstable at this load.\\nTry a smaller offset." 8 50',
  "L1764")

# L1793-1794: Validate UV yesno  14->13  (9 text lines)
r('        --yesno "Run full undervolt validation?\\n\\nDTB: ${DTB_ST}\\n\\nSteps:\\n  1. CPU Benchmark  (~60s)\\n  2. CPU Stress test (~5 min)\\n\\nTotal: ~6 minutes. Do not interrupt." \\\n        14 52',
  '        --yesno "Run full undervolt validation?\\n\\nDTB: ${DTB_ST}\\n\\nSteps:\\n  1. CPU Benchmark  (~60s)\\n  2. CPU Stress test (~5 min)\\n\\nTotal: ~6 minutes. Do not interrupt." \\\n        13 52',
  "L1793")

# L1811-1813: Validation complete msgbox  11->9  (5 text lines)
r('        --msgbox "${VERDICT}\\n\\n${MHZ} MHz  |  ${MV} mV\\nDTB: ${DTB_ST}\\nTemp: min ${STRESS_MIN_TEMP}°C  avg ${STRESS_AVG_TEMP}°C  peak ${STRESS_MAX_TEMP}°C" \\\n        11 54',
  '        --msgbox "${VERDICT}\\n\\n${MHZ} MHz  |  ${MV} mV\\nDTB: ${DTB_ST}\\nTemp: min ${STRESS_MIN_TEMP}°C  avg ${STRESS_AVG_TEMP}°C  peak ${STRESS_MAX_TEMP}°C" \\\n        9 54',
  "L1813")

# L1849-1850: GPU UV result msgbox  15->13  (9 text lines)
r('            --msgbox "Terrain on-screen: ${FPS} fps\\nGPU: ${GPU_MHZ} MHz  |  Temp: ${TEMP}°C\\nDTB: ${DTB_ST}\\nVerdict: ${VERDICT}\\n\\nBaseline stock: ~15 fps off-screen / ~14 fps on-screen\\nArtifacts / freeze / crash = unstable.\\n\\nSaved to history." \\\n            15 56',
  '            --msgbox "Terrain on-screen: ${FPS} fps\\nGPU: ${GPU_MHZ} MHz  |  Temp: ${TEMP}°C\\nDTB: ${DTB_ST}\\nVerdict: ${VERDICT}\\n\\nBaseline stock: ~15 fps off-screen / ~14 fps on-screen\\nArtifacts / freeze / crash = unstable.\\n\\nSaved to history." \\\n            13 56',
  "L1850")

# L1854: GPU UV failed msgbox  9->7  (3 text lines)
r('--msgbox "glmark2 terrain failed.\\n\\n${ERR}" 9 56',
  '--msgbox "glmark2 terrain failed.\\n\\n${ERR}" 7 56',
  "L1854")

# L1866: Benchmark menu  22->17  (1 text line + 10 items = 6+1+10=17)
r('                    --menu "Select test to run" \\\n                    22 62 10',
  '                    --menu "Select test to run" \\\n                    17 62 10',
  "L1866")

# L1899-1901: Save profile yesno  22->17  (13 text lines)
r('        --yesno "Save current tuning as boot profile?\\n\\nCPU max   : $(GetCPUMaxMHz) MHz\\nCPU min   : $(GetCPUMinMHz) MHz\\nGPU max   : $(GetGPUMaxMHz) MHz\\nDMC max   : $(GetDMCMaxMHz) MHz\\nvdd_arm   : $(GetRegVoltMV "$VDD_ARM") mV\\nvdd_logic : $(GetRegVoltMV "$VDD_LOGIC") mV\\nvcc_ddr   : $(GetRegVoltMV "$VCC_DDR") mV\\nGovernor  : $(GetGOV)\\n\\nFail-safe : panic flag active at boot\\nAutostart : $BOOT_ACTIVE" \\\n        22 55',
  '        --yesno "Save current tuning as boot profile?\\n\\nCPU max   : $(GetCPUMaxMHz) MHz\\nCPU min   : $(GetCPUMinMHz) MHz\\nGPU max   : $(GetGPUMaxMHz) MHz\\nDMC max   : $(GetDMCMaxMHz) MHz\\nvdd_arm   : $(GetRegVoltMV "$VDD_ARM") mV\\nvdd_logic : $(GetRegVoltMV "$VDD_LOGIC") mV\\nvcc_ddr   : $(GetRegVoltMV "$VCC_DDR") mV\\nGovernor  : $(GetGOV)\\n\\nFail-safe : panic flag active at boot\\nAutostart : $BOOT_ACTIVE" \\\n        17 55',
  "L1901")

# L1907-1908: Profile saved msgbox  12->11  (7 text lines)
r('        --msgbox "Profile saved!\\n\\nFile    : /etc/r36_tuner.ini\\nService : r36-tuner.service  ✓ enabled\\n\\nFail-safe active: if boot hangs, next boot\\nautomatically disables the profile." 12 55',
  '        --msgbox "Profile saved!\\n\\nFile    : /etc/r36_tuner.ini\\nService : r36-tuner.service  ✓ enabled\\n\\nFail-safe active: if boot hangs, next boot\\nautomatically disables the profile." 11 55',
  "L1908")

# L1920-1922: Profile reset msgbox  9->8  (4 text lines)
r('        --msgbox "Profile deleted.\\nBoot service disabled.\\n\\nSystem will boot with kernel defaults." \\\n        9 50',
  '        --msgbox "Profile deleted.\\nBoot service disabled.\\n\\nSystem will boot with kernel defaults." \\\n        8 50',
  "L1921")

# L1927-1928: No profile saved msgbox  8->7  (3 text lines)
r('--msgbox "No profile saved.\\n\\n$CONFIG_FILE not found." 8 50',
  '--msgbox "No profile saved.\\n\\n$CONFIG_FILE not found." 7 50',
  "L1928")

# L2004-2006: Boot profile failed yesno  11->9  (5 text lines)
r('        --yesno "Last boot: profile caused a hang and was auto-disabled.\\n\\nFailed config: ${CONFIG_FILE}.failed\\n\\nDelete the failed config file?" \\\n        11 62',
  '        --yesno "Last boot: profile caused a hang and was auto-disabled.\\n\\nFailed config: ${CONFIG_FILE}.failed\\n\\nDelete the failed config file?" \\\n        9 62',
  "L2006")

# L2014-2016: DTB UV auto-restored msgbox  10->9  (5 text lines)
r('        --msgbox "Previous DTB undervolt caused instability.\\nOriginal DTB was restored automatically.\\n\\nSafety service has been disabled.\\nTry a smaller voltage offset next time." \\\n        10 58',
  '        --msgbox "Previous DTB undervolt caused instability.\\nOriginal DTB was restored automatically.\\n\\nSafety service has been disabled.\\nTry a smaller voltage offset next time." \\\n        9 58',
  "L2016")

# ── Dynamic height fixes ───────────────────────────────────────────────────────

# GPU UV mode menu: add MODE_H before dialog, use $MODE_H
# Before: "local PATCH_MODE\n    PATCH_MODE=$(dialog ... --menu "${TABLE}\nSelect mode:" \n        26 60 2 \"
r('    local PATCH_MODE\n    PATCH_MODE=$(dialog --backtitle "$BACKTITLE" --title "[ GPU UNDERVOLT — MODO ]" \\\n        --ok-label "Select" --cancel-label "Back" \\\n        --menu "${TABLE}\\nSelect mode:" \\\n        26 60 2',
  '    local MODE_H=$(( N + 13 )); [ -f "${DTB}.bak" ] && MODE_H=$(( MODE_H + 1 ))\n    local PATCH_MODE\n    PATCH_MODE=$(dialog --backtitle "$BACKTITLE" --title "[ GPU UNDERVOLT — MODO ]" \\\n        --ok-label "Select" --cancel-label "Back" \\\n        --menu "${TABLE}\\nSelect mode:" \\\n        $MODE_H 60 2',
  "GPU-UV-mode-dyn")

# GPU fine tune select: 20 -> dynamic N+8
r('            FT_SEL=$(dialog --backtitle "$BACKTITLE" --title "[ GPU FINE TUNE — SELECT OPP ]" \\\n                --ok-label "Tune" --cancel-label "Cancel" \\\n                --menu "Select frequency to tune:" \\\n                20 65 $(( N + 1 ))',
  '            FT_SEL=$(dialog --backtitle "$BACKTITLE" --title "[ GPU FINE TUNE — SELECT OPP ]" \\\n                --ok-label "Tune" --cancel-label "Cancel" \\\n                --menu "Select frequency to tune:" \\\n                $(( N + 8 )) 65 $(( N + 1 ))',
  "GPU-FT-select-dyn")

# GPU UV confirm: add CONFIRM_H, use $CONFIRM_H
r('    dialog --backtitle "$BACKTITLE" --title "[ GPU UNDERVOLT — CONFIRM ]" \\\n        --yesno "$PREVIEW" 18 58',
  '    local CONFIRM_H=$(( N + 6 )); [ -n "$GPU_BIN" ] && CONFIRM_H=$(( CONFIRM_H + 2 ))\n    dialog --backtitle "$BACKTITLE" --title "[ GPU UNDERVOLT — CONFIRM ]" \\\n        --yesno "$PREVIEW" $CONFIRM_H 58',
  "GPU-UV-confirm-dyn")

# GovernorMenu: add GOV_COUNT, make dynamic
r('    local SEL\n    SEL=$(dialog --backtitle "$BACKTITLE" \\\n                 --title "[ CPU GOVERNOR ]" \\\n                 --default-item "$CUR_GOV" \\\n                 --menu "★ = active  |  Save Profile to persist at boot" \\\n                 15 62 8',
  '    local GOV_COUNT=$(( ${#CHOICES[@]} / 2 ))\n    local SEL\n    SEL=$(dialog --backtitle "$BACKTITLE" \\\n                 --title "[ CPU GOVERNOR ]" \\\n                 --default-item "$CUR_GOV" \\\n                 --menu "★ = active  |  Save Profile to persist at boot" \\\n                 $(( GOV_COUNT + 7 )) 62 $GOV_COUNT',
  "GOV-menu-dyn")

# DTBUndervoltMenu top-level: add DTB_ITEMS, make dynamic
r('    local ACTION\n    ACTION=$(dialog --backtitle "$BACKTITLE" --title "[ DTB TUNING ]" \\\n        --ok-label "Select" --cancel-label "Back" \\\n        --menu "OPP voltage patch and frequency unlock — reboot required" \\\n        20 62 9',
  '    local DTB_ITEMS=$(( 7 + ${#RESTORE_OPT[@]} / 2 ))\n    local ACTION\n    ACTION=$(dialog --backtitle "$BACKTITLE" --title "[ DTB TUNING ]" \\\n        --ok-label "Select" --cancel-label "Back" \\\n        --menu "OPP voltage patch and frequency unlock — reboot required" \\\n        $(( DTB_ITEMS + 7 )) 62 $DTB_ITEMS',
  "DTB-menu-dyn")

# CPU UV mode menu: add MODE_H before dialog
r('    local PATCH_MODE\n    PATCH_MODE=$(dialog --backtitle "$BACKTITLE" --title "[ DTB UNDERVOLT — PATCH ]" \\\n        --ok-label "Select" --cancel-label "Back" \\\n        --menu "${TABLE}\\nSelect patch mode:" \\\n        26 60 2',
  '    local MODE_H=$(( ${#NODES[@]} + 13 )); [ -f "${DTB}.bak" ] && MODE_H=$(( MODE_H + 1 ))\n    local PATCH_MODE\n    PATCH_MODE=$(dialog --backtitle "$BACKTITLE" --title "[ DTB UNDERVOLT — PATCH ]" \\\n        --ok-label "Select" --cancel-label "Back" \\\n        --menu "${TABLE}\\nSelect patch mode:" \\\n        $MODE_H 60 2',
  "CPU-UV-mode-dyn")

# CPU fine tune select: 20 -> dynamic N+8
r('            FT_SEL=$(dialog --backtitle "$BACKTITLE" --title "[ FINE TUNE — SELECT FREQUENCY ]" \\\n                --ok-label "Tune" --cancel-label "Cancel" \\\n                --menu "Select frequency to adjust:" \\\n                20 65 $(( N + 1 ))',
  '            FT_SEL=$(dialog --backtitle "$BACKTITLE" --title "[ FINE TUNE — SELECT FREQUENCY ]" \\\n                --ok-label "Tune" --cancel-label "Cancel" \\\n                --menu "Select frequency to adjust:" \\\n                $(( N + 8 )) 65 $(( N + 1 ))',
  "CPU-FT-select-dyn")

# CPU UV confirm: add CONFIRM_H, use $CONFIRM_H
r('    dialog --backtitle "$BACKTITLE" --title "[ DTB UNDERVOLT — CONFIRM ]" \\\n        --yesno "$PREVIEW" 22 58',
  '    local CONFIRM_H=$(( N + 6 )); [ -n "$BIN_LEVEL" ] && CONFIRM_H=$(( CONFIRM_H + 2 ))\n    dialog --backtitle "$BACKTITLE" --title "[ DTB UNDERVOLT — CONFIRM ]" \\\n        --yesno "$PREVIEW" $CONFIRM_H 58',
  "CPU-UV-confirm-dyn")

# ── Write result ──────────────────────────────────────────────────────────────
if content == original:
    print("\nNo changes made!")
else:
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"\nDone. File written.")
