#!/bin/bash
# Verification script for R36 Tuner v3.7 audit changes
# Run via SSH on device: bash verify_audit.sh

PASS=0; FAIL=0; WARN=0
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

ok()   { echo -e "${GREEN}[PASS]${NC} $1"; ((PASS++)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; ((FAIL++)); }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; ((WARN++)); }

DTB="/boot/rk3326-r36s-linux.dtb"
CPU_BENCH="/tmp/r36_cpubench"

echo "=========================================="
echo " R36 Tuner v3.7 — Audit Verification"
echo "=========================================="
echo ""

# ── 1. Pre-flight: hardware compatible string ──────────────────────────────────
echo "--- [1] Pre-flight: RK3326/PX30 hardware detection"
compat=$(strings /proc/device-tree/compatible 2>/dev/null | head -5 | tr '\n' ' ')
if strings /proc/device-tree/compatible 2>/dev/null | grep -qE "rockchip,(rk3326|px30)"; then
    ok "Compatible string matches rk3326/px30: $compat"
else
    fail "Compatible string mismatch — would trigger hardware warning: $compat"
fi

# ── 2. DetectOPPBinProp — dmesg path ──────────────────────────────────────────
echo ""
echo "--- [2] DetectOPPBinProp — dmesg path"
bin_dmesg=$(dmesg 2>/dev/null | grep -iE "cpu cpu0.*opp-binning.*using OPP prop name" | grep -o 'L[0-9]' | tail -1)
if [ -n "$bin_dmesg" ]; then
    ok "dmesg path: detected bin=$bin_dmesg → prop=opp-microvolt-${bin_dmesg}"
else
    warn "dmesg path: no bin found (ring buffer may have rotated — checking fallback)"
fi

# ── 3. DetectOPPBinProp — /proc/device-tree fallback ──────────────────────────
echo ""
echo "--- [3] DetectOPPBinProp — /proc/device-tree fallback"
bin_proc=""
for entry in /proc/device-tree/cpu0-opp-table/opp-1512000000 \
             /proc/device-tree/opp-table-0/opp-1512000000 \
             /proc/device-tree/cpu0-opp-table/opp-1296000000; do
    [ -d "$entry" ] || continue
    for f in "$entry"/opp-microvolt-L*; do
        [ -e "$f" ] && bin_proc=$(basename "$f" | grep -o 'L[0-9]') && break 2
    done
done
if [ -n "$bin_proc" ]; then
    ok "/proc/device-tree fallback: found bin=$bin_proc"
elif [ -n "$bin_dmesg" ]; then
    warn "/proc/device-tree fallback: no bin-specific prop found (OK if dmesg path works)"
else
    fail "/proc/device-tree fallback: neither dmesg nor /proc/device-tree found bin"
fi

# Active bin summary
active_bin="${bin_dmesg:-${bin_proc:-unknown}}"
echo "    → Active bin: $active_bin"

# ── 4. DMC_DEVFREQ path resolves correctly ────────────────────────────────────
echo ""
echo "--- [4] DMC_DEVFREQ path (FindDMCDevfreq)"
dmc_path=""
for candidate in /sys/class/devfreq/dmc /sys/class/devfreq/ff400000.gpu; do
    # dmc only
    :
done
for d in /sys/class/devfreq/*/; do
    name=$(cat "$d/device/of_node/name" 2>/dev/null || basename "$d")
    [[ "$name" == "dmc" ]] && dmc_path="$d" && break
done
[ -z "$dmc_path" ] && dmc_path=$(ls -d /sys/class/devfreq/dmc 2>/dev/null)

if [ -n "$dmc_path" ] && [ -d "$dmc_path" ]; then
    dmc_cur=$(cat "$dmc_path/cur_freq" 2>/dev/null)
    dmc_avail=$(cat "$dmc_path/available_frequencies" 2>/dev/null)
    ok "DMC devfreq found: $dmc_path — cur=${dmc_cur}Hz"
    if echo "$dmc_avail" | grep -q "928000000"; then
        ok "DMC OC 928MHz present in available_frequencies"
    else
        warn "DMC OC 928MHz NOT in available_frequencies (OC may not be active)"
    fi
else
    fail "DMC devfreq path not found"
fi

# ── 5. GPU devfreq path ────────────────────────────────────────────────────────
echo ""
echo "--- [5] GPU devfreq path"
gpu_path=""
for d in /sys/class/devfreq/*/; do
    avail=$(cat "$d/available_frequencies" 2>/dev/null)
    echo "$avail" | grep -q "400000000" && gpu_path="$d" && break
done
if [ -n "$gpu_path" ]; then
    gpu_cur=$(cat "$gpu_path/cur_freq" 2>/dev/null)
    gpu_avail=$(cat "$gpu_path/available_frequencies" 2>/dev/null | tr ' ' '\n' | awk '{printf "%d MHz\n", $1/1000000}' | tr '\n' ' ')
    ok "GPU devfreq found: $gpu_path — cur=$((gpu_cur/1000000))MHz — freqs: $gpu_avail"
    if cat "$gpu_path/available_frequencies" 2>/dev/null | grep -q "600000000"; then
        ok "GPU OC 600MHz present in available_frequencies"
    else
        warn "GPU OC 600MHz NOT in available_frequencies (OC may not be active)"
    fi
else
    fail "GPU devfreq path not found"
fi

# ── 6. CPU 1608 MHz in scaling_available_frequencies ──────────────────────────
echo ""
echo "--- [6] CPU OC 1608 MHz active"
cpu_freqs=$(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_available_frequencies 2>/dev/null)
if echo "$cpu_freqs" | grep -q "1608000"; then
    ok "1608 MHz present in scaling_available_frequencies"
else
    warn "1608 MHz NOT in scaling_available_frequencies (OC not active yet — needs DTB patch + reboot)"
fi
echo "    Freqs: $(echo $cpu_freqs | tr ' ' '\n' | awk '{printf "%d MHz  ", $1/1000}')"

# ── 7. DTB CPU OC: both opp-microvolt AND opp-microvolt-L2 present ────────────
echo ""
echo "--- [7] DTBCPUOC: dual opp-microvolt write (generic + bin-specific)"
if [ ! -f "$DTB" ]; then
    warn "DTB not found at $DTB — skipping"
elif ! command -v fdtget >/dev/null 2>&1; then
    warn "fdtget not available — skipping DTB checks"
else
    # Find CPU OPP table node
    opp_base=""
    for candidate in /cpu0-opp-table /opp-table-0 /cpu-opp-table /opp-table0 /opp-table; do
        fdtget "$DTB" "$candidate" compatible >/dev/null 2>&1 && opp_base="$candidate" && break
    done

    if [ -z "$opp_base" ]; then
        fail "Cannot find CPU OPP table in DTB"
    else
        ok "CPU OPP table found: $opp_base"

        # Check avs-scale = 0
        avs=$(fdtget -t u "$DTB" "$opp_base" "rockchip,avs-scale" 2>/dev/null)
        if [ "$avs" = "0" ]; then
            ok "rockchip,avs-scale = 0 (CPU OC OPPs not stripped at boot)"
        elif [ -z "$avs" ]; then
            warn "rockchip,avs-scale not found in DTB (may default to safe value)"
        else
            fail "rockchip,avs-scale = $avs (should be 0 for 1608MHz OPP to survive boot)"
        fi

        # Check 1608 OPP node exists and has both voltage props
        has_1608=0
        for node in opp-1608000000 "opp@1608000000"; do
            fdtget "$DTB" "$opp_base/$node" opp-hz >/dev/null 2>&1 && has_1608=1 && opp_1608_node="$node" && break
        done

        if [ $has_1608 -eq 1 ]; then
            ok "opp-1608000000 node present in DTB"

            # Generic opp-microvolt
            generic_uv=$(fdtget -t u "$DTB" "$opp_base/$opp_1608_node" opp-microvolt 2>/dev/null | awk '{print $1}')
            if [ -n "$generic_uv" ]; then
                ok "opp-microvolt (generic) present: $((generic_uv/1000)) mV"
            else
                fail "opp-microvolt (generic) MISSING from opp-1608000000"
            fi

            # Bin-specific
            if [ -n "$active_bin" ] && [ "$active_bin" != "unknown" ]; then
                bin_prop="opp-microvolt-${active_bin}"
                bin_uv=$(fdtget -t u "$DTB" "$opp_base/$opp_1608_node" "$bin_prop" 2>/dev/null | awk '{print $1}')
                if [ -n "$bin_uv" ]; then
                    ok "$bin_prop (bin-specific) present: $((bin_uv/1000)) mV"
                    [ "$bin_uv" -ge 1187500 ] && ok "Voltage >= 1187.5 mV floor (safe)" || \
                        fail "Voltage $((bin_uv/1000)) mV < 1187.5 mV floor — UNSAFE for 1608MHz"
                else
                    fail "$bin_prop MISSING from opp-1608000000"
                fi
            fi
        else
            warn "opp-1608000000 node not in DTB (CPU OC not applied)"
        fi

        # Check CPU UV voltages at 1296/1512 MHz
        echo "    CPU OPP voltages (${active_bin:-stock}):"
        for node in $(fdtget -l "$DTB" "$opp_base" 2>/dev/null | sort); do
            freq_hz="${node#opp-}"; freq_hz="${freq_hz#opp@}"
            mhz=$((freq_hz/1000000))
            [[ $mhz -lt 1000 || $mhz -gt 1620 ]] && continue
            prop="opp-microvolt-${active_bin}"
            uv=$(fdtget -t u "$DTB" "$opp_base/$node" "$prop" 2>/dev/null | awk '{print $1}')
            [ -z "$uv" ] && uv=$(fdtget -t u "$DTB" "$opp_base/$node" opp-microvolt 2>/dev/null | awk '{print $1}')
            [ -n "$uv" ] && echo "      $mhz MHz → $((uv/1000)) mV"
        done
    fi
fi

# ── 8. DTBGPUOC: dual opp-microvolt write ─────────────────────────────────────
echo ""
echo "--- [8] DTBGPUOC: dual opp-microvolt write for GPU 600MHz node"
if [ -f "$DTB" ] && command -v fdtget >/dev/null 2>&1; then
    gpu_opp=""
    for candidate in /gpu-opp-table /gpu_opp_table /gpu-opp-table-0; do
        fdtget "$DTB" "$candidate" compatible >/dev/null 2>&1 && gpu_opp="$candidate" && break
    done

    if [ -n "$gpu_opp" ]; then
        # Check 600MHz node
        has_600=0
        for node in opp-600000000 "opp@600000000"; do
            fdtget "$DTB" "$gpu_opp/$node" opp-hz >/dev/null 2>&1 && has_600=1 && opp_600_node="$node" && break
        done

        if [ $has_600 -eq 1 ]; then
            ok "GPU opp-600000000 node present"
            generic_uv=$(fdtget -t u "$DTB" "$gpu_opp/$opp_600_node" opp-microvolt 2>/dev/null | awk '{print $1}')
            [ -n "$generic_uv" ] && ok "GPU opp-microvolt (generic): $((generic_uv/1000)) mV" || \
                fail "GPU opp-microvolt (generic) MISSING from opp-600000000"
            if [ -n "$active_bin" ] && [ "$active_bin" != "unknown" ]; then
                bin_uv=$(fdtget -t u "$DTB" "$gpu_opp/$opp_600_node" "opp-microvolt-${active_bin}" 2>/dev/null | awk '{print $1}')
                [ -n "$bin_uv" ] && ok "GPU opp-microvolt-${active_bin}: $((bin_uv/1000)) mV" || \
                    fail "GPU opp-microvolt-${active_bin} MISSING from opp-600000000"
            fi
        else
            warn "GPU opp-600000000 not in DTB (GPU OC not applied)"
        fi

        # GPU UV table
        echo "    GPU OPP voltages:"
        for node in $(fdtget -l "$DTB" "$gpu_opp" 2>/dev/null | sort); do
            freq_hz="${node#opp-}"; freq_hz="${freq_hz#opp@}"
            mhz=$((freq_hz/1000000))
            prop="opp-microvolt-${active_bin}"
            uv=$(fdtget -t u "$DTB" "$gpu_opp/$node" "$prop" 2>/dev/null | awk '{print $1}')
            [ -z "$uv" ] && uv=$(fdtget -t u "$DTB" "$gpu_opp/$node" opp-microvolt 2>/dev/null | awk '{print $1}')
            [ -n "$uv" ] && echo "      $mhz MHz → $((uv/1000)) mV"
        done
    else
        warn "GPU OPP table not found in DTB"
    fi
fi

# ── 9. StressTestCPU — C ALU benchmark (LCG) ──────────────────────────────────
echo ""
echo "--- [9] StressTestCPU: C ALU benchmark (LCG)"
if [ -x "$CPU_BENCH" ]; then
    ok "/tmp/r36_cpubench already compiled and ready"
    result=$("$CPU_BENCH" 2>/dev/null)
    echo "    Quick run: $result"
    echo "$result" | grep -qiE "Mop|op" && ok "Output looks valid (Mops/s)" || \
        warn "Output format unexpected: $result"
elif command -v gcc >/dev/null 2>&1; then
    ok "gcc available — BenchmarkCPU/StressTestCPU can compile on first run"
    echo "    $(gcc --version | head -1)"
else
    fail "gcc not found AND /tmp/r36_cpubench not cached — stress/benchmark will show error dialog"
fi

# fallback openssl
if command -v openssl >/dev/null 2>&1; then
    ok "openssl available (StressTestCPU fallback if gcc missing)"
else
    warn "openssl not found (stress fallback unavailable — only ALU bench will work)"
fi

# ── 10. glmark2 legacy — binary integrity check ────────────────────────────────
echo ""
echo "--- [10] glmark2 legacy SHA256 integrity check"
LEGACY_BIN="/usr/local/bin/glmark2-es2-drm-legacy"
EXPECTED_HASH="52c861733bf1c195e086867d3ccb29f76feb9169ac46b7255f64393d4ba55b98"
if [ -x "$LEGACY_BIN" ]; then
    actual=$(sha256sum "$LEGACY_BIN" 2>/dev/null | awk '{print $1}')
    if [ "$actual" = "$EXPECTED_HASH" ]; then
        ok "glmark2 legacy binary present, SHA256 matches"
    else
        fail "glmark2 legacy binary present BUT SHA256 mismatch"
        echo "    Expected: $EXPECTED_HASH"
        echo "    Got:      $actual"
    fi
else
    warn "glmark2 legacy not extracted yet (/tmp/glmark2-es2-drm-legacy missing)"
    echo "    → Will be extracted + verified on first GPU benchmark/validate run"
    # Check it's embedded in the script
    script_path="/opt/system/R36 Tuner.sh"
    if grep -q "__GLMARK2_LEGACY_START__" "$script_path" 2>/dev/null; then
        ok "GLMARK2_LEGACY embedded in deployed script"
    else
        warn "Cannot verify embedding — script not at /opt/system/R36 Tuner.sh or markers missing"
    fi
fi

# ── 11. Runtime sanity — current hardware state ────────────────────────────────
echo ""
echo "--- [11] Runtime state summary"
temp=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
cpu_cur=$(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq 2>/dev/null)
cpu_gov=$(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor 2>/dev/null)
vdd_arm_dir=$(ls -d /sys/class/regulator/regulator.*/name 2>/dev/null | \
    xargs grep -l "vdd_arm" 2>/dev/null | head -1 | sed 's|/name||')
vdd_logic_dir=$(ls -d /sys/class/regulator/regulator.*/name 2>/dev/null | \
    xargs grep -l "vdd_logic" 2>/dev/null | head -1 | sed 's|/name||')
arm_mv=$([ -n "$vdd_arm_dir" ] && awk '{printf "%d", $1/1000}' "$vdd_arm_dir/microvolts" 2>/dev/null || echo "N/A")
logic_mv=$([ -n "$vdd_logic_dir" ] && awk '{printf "%d", $1/1000}' "$vdd_logic_dir/microvolts" 2>/dev/null || echo "N/A")

echo "    Temp:      $((temp/1000))°C"
echo "    CPU cur:   $((cpu_cur/1000)) MHz  ($cpu_gov)"
echo "    CPU max:   $(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq 2>/dev/null | awk '{printf "%d", $1/1000}') MHz"
echo "    vdd_arm:   ${arm_mv} mV"
echo "    vdd_logic: ${logic_mv} mV"
[ -n "$dmc_path" ] && echo "    DMC cur:   $(($(cat "$dmc_path/cur_freq" 2>/dev/null)/1000000)) MHz"
[ -n "$gpu_path" ] && echo "    GPU cur:   $(($(cat "$gpu_path/cur_freq" 2>/dev/null)/1000000)) MHz"

# ── 12. Safety service state ───────────────────────────────────────────────────
echo ""
echo "--- [12] DTB safety services"
for svc in r36-dtb-safety r36-dtb-confirm; do
    state=$(systemctl is-enabled "$svc" 2>/dev/null || echo "not-found")
    active=$(systemctl is-active "$svc" 2>/dev/null || echo "unknown")
    if [ "$state" = "enabled" ]; then
        ok "$svc: enabled ($active)"
    else
        warn "$svc: $state ($active)"
    fi
done
pending="/boot/.r36_dtb_patch_pending"
[ -f "$pending" ] && warn "Pending flag exists: $pending (DTB change unconfirmed)" || \
    ok "No DTB pending flag (clean state)"

# ── Summary ────────────────────────────────────────────────────────────────────
echo ""
echo "=========================================="
echo " Results: ${GREEN}${PASS} PASS${NC}  ${RED}${FAIL} FAIL${NC}  ${YELLOW}${WARN} WARN${NC}"
echo "=========================================="
[ $FAIL -gt 0 ] && echo -e "${RED}ACTION REQUIRED: fix FAIL items above${NC}"
[ $FAIL -eq 0 ] && echo -e "${GREEN}All critical checks passed${NC}"
