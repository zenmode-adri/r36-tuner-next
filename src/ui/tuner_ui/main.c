#include <SDL2/SDL.h>
#include <SDL2/SDL_ttf.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <signal.h>
#include <dirent.h>
#include <time.h>
#include <sys/stat.h>

/* ── Paths ──────────────────────────────────────────────────────────────── */
#define FONT_BOLD  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
#define FONT_NORM  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
#define CPU_POLICY      "/sys/devices/system/cpu/cpufreq/policy0"
#define OC_DETECT_CACHE "/tmp/r36_oc_detected"
#define GPU_DEVFREQ "/sys/class/devfreq/ff400000.gpu"
#define DMC_DEVFREQ "/sys/class/devfreq/dmc"
#define CPU_TEMP   "/sys/class/thermal/thermal_zone0/temp"
#define DTB_PENDING_FLAG "/boot/.r36_dtb_patch_pending"
#define BIN_CACHE_FILE   "/etc/r36_tuner_bin"
#define OPP_FLOOR_UV     950000
#define LANG_FILE        "/etc/r36_tuner_ui_lang"

/* ── Internationalization ───────────────────────────────────────────────── */
#define LANG_EN 0
#define LANG_ES 1

typedef enum {
    STR_BACK,
    STR_SELECT,
    STR_APPLY,
    STR_CANCEL,
    STR_CONFIRM,
    STR_REBOOT,
    STR_LATER,
    STR_NAVIGATE,
    STR_EXIT,
    STR_YES,
    STR_NO,
    STR_ACTIVE,
    STR_CURRENT,
    STR_ACTUAL,
    STR_CPU,
    STR_GPU,
    STR_RAM,
    STR_TEMP,
    STR_CPU_GOVERNOR,
    STR_CPU_MAX_FREQ,
    STR_GPU_MAX_FREQ,
    STR_DTB_TUNING,
    STR_BENCHMARK,
    STR_MONITOR,
    STR_LANGUAGE,
    STR_PERFORMANCE_DESC,
    STR_SCHEDUTIL_DESC,
    STR_ONDEMAND_DESC,
    STR_CONSERVATIVE_DESC,
    STR_POWERSAVE_DESC,
    STR_CUSTOM_DESC,
    STR_CPU_MAX_FREQ_DESC,
    STR_CURRENT_MAX_FREQ,
    STR_CORTEX_A35,
    STR_GPU_MAX_FREQ_DESC,
    STR_CURRENT_MAX_FREQ_GPU,
    STR_MALI_G31,
    STR_DTB_TUNING_DESC,
    STR_BENCHMARK_DESC,
    STR_MONITOR_DESC,
    STR_LANGUAGE_DESC,
    STR_ENGLISH,
    STR_SPANISH,
    STR_CPU_UNDERVOLT,
    STR_CPU_OC_1608,
    STR_GPU_OC_600,
    STR_RAM_OC_928,
    STR_DIAG_OPP,
    STR_DIAG_OPP_TITLE,
    STR_DIAG_OPP_EXPL1,
    STR_DIAG_OPP_EXPL2,
    STR_DIAG_DTB_COL,
    STR_DIAG_KERNEL_COL,
    STR_DIAG_NO_ACTIVE,
    STR_RECOVERY,
    STR_RESTORE_ORIGINAL,
    STR_RECOVERY_STEP1,
    STR_RECOVERY_STEP2,
    STR_RECOVERY_STEP3,
    STR_RECOVERY_STEP4,
    STR_RECOVERY_STEP5,
    STR_RECOVERY_STEP6,
    STR_RECOVERY_STEP7,
    STR_RECOVERY_SAFETY,
    STR_RECOVERY_PANIC,
    STR_BIN_OK,
    STR_BIN_MISSING,
    STR_PATCH_OPP_DTDB,
    STR_UNLOCK_1608_DTB,
    STR_ADD_OPP_600,
    STR_ADD_OPP_928,
    STR_VIEW_OPP_TABLE,
    STR_IF_DEVICE_WONT_BOOT,
    STR_REVERT_BACKUP,
    STR_NO_BACKUP,
    STR_BACKUP_FAILED,
    STR_DTB_NOT_FOUND,
    STR_BIN_NOT_DETECTED,
    STR_READING_OPP,
    STR_OPP_NOT_FOUND,
    STR_TABLE_NOT_FOUND,
    STR_PATCHING_DTB,
    STR_PATCH_FAILED_RESTORE,
    STR_PATCH_SUCCESS,
    STR_SAFETY_NET_ACTIVE,
    STR_REBOOT_NOW,
    STR_OC_PATCHED,
    STR_RESTORED,
    STR_RESTORE_FAILED,
    STR_REQUIRES_REBOOT,
    STR_BACKUP_CREATED,
    STR_SAFETY_NET_RESTORE,
    STR_SHARED_RAIL_WARN,
    STR_KERNEL_PANIC_NOTE,
    STR_RESTORE_ORIGINAL_SUMMARY,
    STR_SAFETY_NET_DISABLED,
    STR_DTB_ORIGINAL_RESTORED,
    STR_NO_CHANGES,
    STR_FREQUENCY,
    STR_ACTUAL_COL,
    STR_NEW_COL,
    STR_PARAMETER,
    STR_VALUE,
    STR_AVS_UNLOCKED,
    STR_SHARED_RAIL,
    STR_VCC_DDR_RAIL,
    STR_MHZ,
    STR_MILLIVOLTS,
    STR_REALTIME,
    STR_CPU_FMT,
    STR_GPU_FMT,
    STR_RAM_FMT,
    STR_TEMP_FMT,
    STR_TERRAIN_GLMARK2,
    STR_STOPPING_ES,
    STR_DPAD_NAVIGATE,
    STR_A_SELECT,
    STR_B_BACK,
    STR_DPAD_SELECT,
    STR_A_CONFIRM,
    STR_B_CANCEL,
    STR_DPAD_OFFSET,
    STR_A_SELECT_B_BACK,
    STR_DPAD_VOLTAGE,
    STR_A_APPLY_B_BACK,
    STR_DTB_PATCHED,
    STR_BENCHMARK_CPU,
    STR_BENCHMARK_RAM,
    STR_BENCHMARK_GPU,
    STR_BENCHMARK_HISTORY,
    STR_BENCHMARK_CPU_TITLE,
    STR_BENCHMARK_CPU_RUNNING,
    STR_BENCHMARK_CPU_PLEASE_WAIT,
    STR_BENCHMARK_CPU_RESULT,
    STR_BENCHMARK_CPU_SCORE,
    STR_BENCHMARK_CPU_MOPS,
    STR_BENCHMARK_CPU_TEMP,
    STR_BENCHMARK_CPU_GCC_MISSING,
    STR_BENCHMARK_CPU_SET_BASELINE,
    STR_BENCHMARK_CPU_VS_BASELINE,
    STR_BENCHMARK_CPU_BACK,
    STR_BENCHMARK_CPU_RUN_AGAIN,
    STR_BENCHMARK_RAM_TITLE,
    STR_BENCHMARK_RAM_RUNNING,
    STR_BENCHMARK_RAM_WRITE,
    STR_BENCHMARK_RAM_COPY,
    STR_BENCHMARK_RAM_RESULT,
    STR_BENCHMARK_RAM_MBPS,
    STR_BENCHMARK_RAM_GCC_MISSING,
    STR_BENCHMARK_GPU_TITLE,
    STR_BENCHMARK_GPU_NOT_INSTALLED,
    STR_BENCHMARK_GPU_INSTALL,
    STR_BENCHMARK_GPU_INSTALLING,
    STR_BENCHMARK_GPU_RUNNING,
    STR_BENCHMARK_GPU_PENDING,
    STR_BENCHMARK_GPU_RESULT,
    STR_BENCHMARK_GPU_PTS,
    STR_BENCHMARK_GPU_FAILED,
    STR_BENCHMARK_GPU_BLACK_SCREEN,
    STR_BENCHMARK_GPU_REOPEN,
    STR_BENCHMARK_HISTORY_TITLE,
    STR_BENCHMARK_HISTORY_EMPTY,
    STR_BENCHMARK_HISTORY_CLEAR,
    STR_BENCHMARK_NOT_IMPLEMENTED,
    STR_NODE_ACTIVE,
    STR_CONTINUE,
    STR_CPU_FREQ_FAKE_TAG,
    STR_CPU_FREQ_FAKE_DESC,
    STR_CPU_FREQ_SET_FAKE,
    STR_CPU_FREQ_SILICON_MAX,
    STR_CPU_OC_STOCK_WARN,
    STR_CPU_OC_NEEDS_KERNEL,
    STR_CPU_OC_KERNEL_MAX,
    STR_CPU_FINETUNE,
    STR_CPU_FINETUNE_DESC,
    STR_RAM_OC_1032,
    STR_RAM_OC_1032_DESC,
    STR_RAM_OC_1032_WARN1,
    STR_RAM_OC_1032_WARN2,
    STR_RAM_OC_1032_WARN3,
    STR_RAM_OC_1032_REMOVE,
    STR_RAM_OC_REMOVE,
    STR_RAM_OC_REMOVE_DESC,
    STR_TUNE_924_VOLT,
    STR_COUNT
} StringID;

typedef struct { const char *en; const char *es; } I18nEntry;

static const I18nEntry I18N[STR_COUNT] = {
    [STR_BACK] = { "Back", "Atras" },
    [STR_SELECT] = { "Select", "Seleccionar" },
    [STR_APPLY] = { "Apply", "Aplicar" },
    [STR_CANCEL] = { "Cancel", "Cancelar" },
    [STR_CONFIRM] = { "CONFIRM", "CONFIRMAR" },
    [STR_REBOOT] = { "Reboot", "Reboot" },
    [STR_LATER] = { "Later", "Mas tarde" },
    [STR_NAVIGATE] = { "Navigate", "Navegar" },
    [STR_EXIT] = { "Exit", "Salir" },
    [STR_YES] = { "Yes", "Si" },
    [STR_NO] = { "No", "No" },
    [STR_ACTIVE] = { "ACTIVE", "ACTIVO" },
    [STR_CURRENT] = { "Current", "Actual" },
    [STR_ACTUAL] = { "Actual", "Actual" },
    [STR_CPU] = { "CPU", "CPU" },
    [STR_GPU] = { "GPU", "GPU" },
    [STR_RAM] = { "RAM", "RAM" },
    [STR_TEMP] = { "TEMP", "TEMP" },
    [STR_CPU_GOVERNOR] = { "CPU Governor", "CPU Governor" },
    [STR_CPU_MAX_FREQ] = { "CPU Max Freq", "CPU Max Freq" },
    [STR_GPU_MAX_FREQ] = { "GPU Max Freq", "GPU Max Freq" },
    [STR_DTB_TUNING] = { "DTB Tuning", "DTB Tuning" },
    [STR_BENCHMARK] = { "Benchmark", "Benchmark" },
    [STR_MONITOR] = { "Monitor", "Monitor" },
    [STR_LANGUAGE] = { "Language", "Idioma" },
    [STR_PERFORMANCE_DESC] = { "Always max freq — best for games", "Siempre max freq — mejor para juegos" },
    [STR_SCHEDUTIL_DESC] = { "Scheduler scaling (balanced)", "Escalado por scheduler (balanceado)" },
    [STR_ONDEMAND_DESC] = { "Load-based scaling — default", "Escalado por carga — default" },
    [STR_CONSERVATIVE_DESC] = { "Gradual scaling — power saving", "Escalado gradual — ahorro energia" },
    [STR_POWERSAVE_DESC] = { "Always min freq", "Siempre min freq" },
    [STR_CUSTOM_DESC] = { "Custom", "Custom" },
    [STR_CPU_MAX_FREQ_DESC] = { "Cortex-A35 @ %d MHz", "Cortex-A35 @ %d MHz" },
    [STR_CURRENT_MAX_FREQ] = { "Current max freq", "Frecuencia maxima actual" },
    [STR_CORTEX_A35] = { "RK3326 Cortex-A35", "RK3326 Cortex-A35" },
    [STR_GPU_MAX_FREQ_DESC] = { "Mali-G31 MP2 @ %d MHz", "Mali-G31 MP2 @ %d MHz" },
    [STR_CURRENT_MAX_FREQ_GPU] = { "Current GPU max freq", "Frecuencia maxima GPU actual" },
    [STR_MALI_G31] = { "Mali-G31 MP2", "Mali-G31 MP2" },
    [STR_DTB_TUNING_DESC] = { "Undervolt / OC via device tree (reboot required)", "Undervolt / OC via device tree (requiere reinicio)" },
    [STR_BENCHMARK_DESC] = { "glmark2 terrain + CPU/RAM tests", "glmark2 terrain + CPU/RAM tests" },
    [STR_MONITOR_DESC] = { "CPU %.0fC | GPU %d MHz | RAM %d MHz", "CPU %.0fC | GPU %d MHz | RAM %d MHz" },
    [STR_LANGUAGE_DESC] = { "English / Espanol", "English / Espanol" },
    [STR_ENGLISH] = { "English", "English" },
    [STR_SPANISH] = { "Spanish", "Espanol" },
    [STR_CPU_UNDERVOLT] = { "CPU Undervolt", "CPU Undervolt" },
    [STR_CPU_OC_1608] = { "CPU OC (teacupx)", "CPU OC (teacupx)" },
    [STR_GPU_OC_600] = { "GPU OC 600 MHz", "GPU OC 600 MHz" },
    [STR_RAM_OC_928] = { "RAM OC 928 MHz", "RAM OC 928 MHz" },
    [STR_DIAG_OPP] = { "OPP Voltages", "Voltajes OPP" },
    [STR_DIAG_OPP_TITLE] = { "OPP Voltage Table", "Tabla de Voltajes OPP" },
    [STR_DIAG_OPP_EXPL1] = { "Voltages stored in the DTB and currently used by the kernel.", "Voltajes guardados en el DTB y los que usa el kernel ahora." },
    [STR_DIAG_OPP_EXPL2] = { "CPU frequency (bin-specific table).", "frecuencia de CPU (segun tu bin)." },
    [STR_DIAG_DTB_COL] = { "DTB (disk)", "DTB (disco)" },
    [STR_DIAG_KERNEL_COL] = { "Kernel (now)", "Kernel (ahora)" },
    [STR_DIAG_NO_ACTIVE] = { "--", "--" },
    [STR_RECOVERY] = { "Recovery", "Recuperacion" },
    [STR_RESTORE_ORIGINAL] = { "Restore Original", "Restaurar Original" },
    [STR_RECOVERY_STEP1] = { "1. Power off the R36S", "1. Apagar el R36S" },
    [STR_RECOVERY_STEP2] = { "2. Remove the system SD card", "2. Sacar SD del sistema" },
    [STR_RECOVERY_STEP3] = { "3. Connect SD to PC via reader", "3. Conectar SD a PC via lector" },
    [STR_RECOVERY_STEP4] = { "4. Open FAT32 partition (/boot)", "4. Abrir particion FAT32 (/boot)" },
    [STR_RECOVERY_STEP5] = { "5. Copy .dtb.bak over .dtb", "5. Copiar .dtb.bak sobre .dtb" },
    [STR_RECOVERY_STEP6] = { "6. Delete .r36_dtb_patch_booting", "6. Borrar .r36_dtb_patch_booting" },
    [STR_RECOVERY_STEP7] = { "7. Reinsert SD and boot", "7. Reinsertar SD y bootear" },
    [STR_RECOVERY_SAFETY] = { "Safety service auto-restores if boot hangs.", "Safety service auto-restaura si boot se cuelga." },
    [STR_RECOVERY_PANIC] = { "(does not protect kernel panics)", "(no protege panics del kernel)" },
    [STR_BIN_OK] = { "bin OK", "bin OK" },
    [STR_BIN_MISSING] = { "!bin", "!bin" },
    [STR_PATCH_OPP_DTDB] = { "Patch OPP voltages via DTB", "Patch voltajes OPP via DTB" },
    [STR_UNLOCK_1608_DTB] = { "DTB patch + avs-scale (teacupx required)", "DTB patch + avs-scale (requiere teacupx)" },
    [STR_ADD_OPP_600] = { "Add 600 MHz OPP (Mali-G31)", "Agregar OPP 600 MHz (Mali-G31)" },
    [STR_ADD_OPP_928] = { "Add 928 MHz OPP (DMC)", "Agregar OPP 928 MHz (DMC)" },
    [STR_VIEW_OPP_TABLE] = { "View current OPP table on disk", "Ver tabla OPP actual en disco" },
    [STR_IF_DEVICE_WONT_BOOT] = { "Instructions if device won't boot", "Instrucciones si el dispositivo no bootea" },
    [STR_REVERT_BACKUP] = { "Revert DTB to original backup", "Revertir DTB al backup original" },
    [STR_NO_BACKUP] = { "No backup available", "Sin backup disponible" },
    [STR_BACKUP_FAILED] = { "Backup failed. Aborting.", "Backup fallido. Abortando." },
    [STR_DTB_NOT_FOUND] = { "DTB not found in /boot/", "DTB no encontrado en /boot/" },
    [STR_BIN_NOT_DETECTED] = { "Bin not detected. Reboot device and try again.", "Bin no detectado. Reiniciar dispositivo e intentar de nuevo." },
    [STR_READING_OPP] = { "Reading OPP table...", "Leyendo tabla OPP..." },
    [STR_OPP_NOT_FOUND] = { "No OPP entries found in DTB.", "No se encontraron entradas OPP en el DTB." },
    [STR_TABLE_NOT_FOUND] = { "OPP table not found in DTB.", "Tabla OPP no encontrada en DTB." },
    [STR_PATCHING_DTB] = { "Patching DTB...", "Parcheando DTB..." },
    [STR_PATCH_FAILED_RESTORE] = { "Patch failed. Restoring backup...", "Patch fallido. Restaurando backup..." },
    [STR_PATCH_SUCCESS] = { "Patch applied successfully.", "DTB parcheado exitosamente." },
    [STR_SAFETY_NET_ACTIVE] = { "Safety net active (auto-restore if boot fails).", "Safety net activo (auto-restore si boot falla)." },
    [STR_REBOOT_NOW] = { "Reboot now?", "Reboot ahora?" },
    [STR_OC_PATCHED] = { "OC PATCHED", "OC PARCHEADO" },
    [STR_RESTORED] = { "RESTORED", "RESTAURADO" },
    [STR_RESTORE_FAILED] = { "Restore failed.", "Restauracion fallida." },
    [STR_REQUIRES_REBOOT]   = { "Requires reboot.", "Requiere reinicio." },
    [STR_BACKUP_CREATED]    = { "Backup .bak will be created if missing.", "Se creara backup .bak si no existe." },
    [STR_SAFETY_NET_RESTORE]= { "Safety net will restore DTB if boot fails.", "Safety net restaurara DTB si el boot falla." },
    [STR_SHARED_RAIL_WARN]  = { "! GPU and RAM share vdd_logic — voltage affects both.", "! GPU y RAM comparten vdd_logic — voltaje afecta ambos." },
    [STR_KERNEL_PANIC_NOTE] = { "(does not protect kernel panics)", "(no protege kernel panics)" },
    [STR_RESTORE_ORIGINAL_SUMMARY] = { "Revert to original backup", "Revertir al backup original" },
    [STR_SAFETY_NET_DISABLED] = { "Safety net will also be disabled.", "Safety net tambien se desactivara." },
    [STR_DTB_ORIGINAL_RESTORED] = { "Original DTB restored.", "DTB original restaurado." },
    [STR_NO_CHANGES] = { "0 mV (no changes)", "0 mV (no cambios)" },
    [STR_FREQUENCY] = { "Frequency", "Frecuencia" },
    [STR_ACTUAL_COL] = { "Actual", "Actual" },
    [STR_NEW_COL] = { "New", "Nuevo" },
    [STR_PARAMETER] = { "Parameter", "Parametro" },
    [STR_VALUE] = { "Value", "Valor" },
    [STR_AVS_UNLOCKED] = { "0 (unlocked)", "0 (desbloqueado)" },
    [STR_SHARED_RAIL] = { "vdd_logic shared with SoC", "vdd_logic compartido con SoC" },
    [STR_VCC_DDR_RAIL] = { "DMC / vcc_ddr", "DMC / vcc_ddr" },
    [STR_MHZ] = { "MHz", "MHz" },
    [STR_MILLIVOLTS] = { "mV", "mV" },
    [STR_REALTIME] = { "Real-time", "Tiempo real" },
    [STR_CPU_FMT] = { "%d / %d MHz  |  %.1fC  [%s]", "%d / %d MHz  |  %.1fC  [%s]" },
    [STR_GPU_FMT] = { "%d / %d MHz  |  Mali-G31 MP2", "%d / %d MHz  |  Mali-G31 MP2" },
    [STR_RAM_FMT] = { "DDR @ %d MHz", "DDR @ %d MHz" },
    [STR_TEMP_FMT] = { "%.1f C", "%.1f C" },
    [STR_TERRAIN_GLMARK2] = { "glmark2 terrain", "glmark2 terrain" },
    [STR_STOPPING_ES] = { "Stopping EmulationStation...", "Deteniendo EmulationStation..." },
    [STR_DPAD_NAVIGATE] = { "[DPAD] Navigate", "[DPAD] Navegar" },
    [STR_A_SELECT] = { "[A] Select", "[A] Seleccionar" },
    [STR_B_BACK] = { "[B] Back", "[B] Atras" },
    [STR_DPAD_SELECT] = { "[DPAD] Select", "[DPAD] Seleccionar" },
    [STR_A_CONFIRM] = { "[A] Confirm", "[A] Confirmar" },
    [STR_B_CANCEL] = { "[B] Cancel", "[B] Cancelar" },
    [STR_DPAD_OFFSET] = { "[DPAD] Offset", "[DPAD] Offset" },
    [STR_A_SELECT_B_BACK] = { "[A] Select  [B] Back", "[A] Seleccionar  [B] Atras" },
    [STR_DPAD_VOLTAGE] = { "[DPAD] Voltage", "[DPAD] Voltaje" },
    [STR_A_APPLY_B_BACK] = { "[A] Apply  [B] Back", "[A] Aplicar  [B] Atras" },
    [STR_DTB_PATCHED] = { "DTB PATCHED", "DTB PARCHEADO" },
    [STR_BENCHMARK_CPU] = { "CPU Benchmark", "Benchmark CPU" },
    [STR_BENCHMARK_RAM] = { "RAM Benchmark", "Benchmark RAM" },
    [STR_BENCHMARK_GPU] = { "GPU Benchmark", "Benchmark GPU" },
    [STR_BENCHMARK_HISTORY] = { "Score History", "Historial de puntuaciones" },
    [STR_BENCHMARK_CPU_TITLE] = { "CPU Benchmark", "Benchmark CPU" },
    [STR_BENCHMARK_CPU_RUNNING] = { "Running integer ALU benchmark...", "Ejecutando benchmark ALU entero..." },
    [STR_BENCHMARK_CPU_PLEASE_WAIT] = { "Please wait ~30s", "Espera ~30s" },
    [STR_BENCHMARK_CPU_RESULT] = { "Result", "Resultado" },
    [STR_BENCHMARK_CPU_SCORE] = { "Score", "Puntuacion" },
    [STR_BENCHMARK_CPU_MOPS] = { "Mops/30s", "Mops/30s" },
    [STR_BENCHMARK_CPU_TEMP] = { "Temperature", "Temperatura" },
    [STR_BENCHMARK_CPU_GCC_MISSING] = { "Benchmark binary missing. Re-run launcher.", "Binario no encontrado. Relanza el launcher." },
    [STR_BENCHMARK_CPU_SET_BASELINE] = { "Baseline set", "Linea base guardada" },
    [STR_BENCHMARK_CPU_VS_BASELINE] = { "vs baseline", "vs linea base" },
    [STR_BENCHMARK_CPU_BACK] = { "Back", "Atras" },
    [STR_BENCHMARK_CPU_RUN_AGAIN] = { "Run Again", "Repetir" },
    [STR_BENCHMARK_RAM_TITLE] = { "RAM Benchmark", "Benchmark RAM" },
    [STR_BENCHMARK_RAM_RUNNING] = { "Measuring memory bandwidth...", "Midiendo ancho de banda..." },
    [STR_BENCHMARK_RAM_WRITE] = { "Write", "Escritura" },
    [STR_BENCHMARK_RAM_COPY] = { "Copy", "Copia" },
    [STR_BENCHMARK_RAM_RESULT] = { "Result", "Resultado" },
    [STR_BENCHMARK_RAM_MBPS] = { "MB/s", "MB/s" },
    [STR_BENCHMARK_RAM_GCC_MISSING] = { "Benchmark binary missing. Re-run launcher.", "Binario no encontrado. Relanza el launcher." },
    [STR_BENCHMARK_GPU_TITLE] = { "GPU Benchmark", "Benchmark GPU" },
    [STR_BENCHMARK_GPU_NOT_INSTALLED] = { "glmark2 legacy not found.", "glmark2 legacy no encontrado." },
    [STR_BENCHMARK_GPU_INSTALL] = { "Install glmark2 legacy?", "Instalar glmark2 legacy?" },
    [STR_BENCHMARK_GPU_INSTALLING] = { "Preparing glmark2...", "Preparando glmark2..." },
    [STR_BENCHMARK_GPU_RUNNING] = { "Running glmark2 off-screen...", "Ejecutando glmark2 off-screen..." },
    [STR_BENCHMARK_GPU_PENDING] = { "Benchmark running in background (~1 min).", "Benchmark corriendo en segundo plano (~1 min)." },
    [STR_BENCHMARK_GPU_RESULT] = { "GPU Result", "Resultado GPU" },
    [STR_BENCHMARK_GPU_PTS] = { "pts", "pts" },
    [STR_BENCHMARK_GPU_FAILED] = { "GPU benchmark failed.", "Benchmark GPU fallido." },
    [STR_BENCHMARK_GPU_BLACK_SCREEN] = { "Runs off-screen in background (~1 min). Continue?", "Corre off-screen en segundo plano (~1 min). Continuar?" },
    [STR_BENCHMARK_GPU_REOPEN] = { "Come back here to see the result.", "Vuelve aqui para ver el resultado." },
    [STR_BENCHMARK_HISTORY_TITLE] = { "Score History", "Historial de puntuaciones" },
    [STR_BENCHMARK_HISTORY_EMPTY] = { "No scores recorded yet.", "Aun no hay puntuaciones." },
    [STR_BENCHMARK_HISTORY_CLEAR] = { "Clear History", "Borrar historial" },
    [STR_BENCHMARK_NOT_IMPLEMENTED] = { "Not implemented yet", "No implementado aun" },
    [STR_NODE_ACTIVE] = { "active", "activo" },
    [STR_CONTINUE] = { "Continue", "Continuar" },
    [STR_CPU_FREQ_FAKE_TAG]    = { "stock=1296", "stock=1296" },
    [STR_CPU_FREQ_FAKE_DESC]   = { "stock kernel: silicon stays at 1296 MHz", "kernel stock: silicio queda en 1296 MHz" },
    [STR_CPU_FREQ_SET_FAKE]    = { "SET (fake)", "CONF (falso)" },
    [STR_CPU_FREQ_SILICON_MAX] = { "kernel max", "max kernel" },
    [STR_CPU_OC_STOCK_WARN] = { "Stock kernel: 1296 MHz is the real hardware limit.", "Kernel stock: 1296 MHz es el limite real del hardware." },
    [STR_CPU_OC_NEEDS_KERNEL] = { "Real OC above 1296 MHz requires teacupx patched kernel", "OC real sobre 1296 MHz requiere kernel parcheado de teacupx" },
    [STR_CPU_OC_KERNEL_MAX] = { "Patched kernel max: 1512 MHz  (github.com/teacupx/overclock-r36s)", "Max kernel parcheado: 1512 MHz  (github.com/teacupx/overclock-r36s)" },
    [STR_CPU_FINETUNE]       = { "CPU Fine-Tune", "CPU Fine-Tune" },
    [STR_CPU_FINETUNE_DESC]  = { "Per-OPP voltage adjustment", "Ajuste de voltaje por OPP" },
    [STR_RAM_OC_1032]        = { "RAM OC 1032 MHz [EXP]", "RAM OC 1032 MHz [EXP]" },
    [STR_RAM_OC_1032_DESC]   = { "Add 1040 MHz OPP — ATF delivers 1032 MHz", "Agrega OPP 1040 MHz — ATF entrega 1032 MHz" },
    [STR_RAM_OC_1032_WARN1]  = { "vdd_logic rail fixed at chosen voltage — GPU OC UV savings lost above 1025 mV", "Rail vdd_logic fijado al voltaje elegido — ahorro UV GPU perdido sobre 1025 mV" },
    [STR_RAM_OC_1032_WARN2]  = { "Instability crashes device but cannot damage RAM hardware", "Inestabilidad cuelga el device pero no puede dañar la RAM" },
    [STR_RAM_OC_1032_WARN3]  = { "Stability depends on your RAM chip — if unstable, revert to 924 MHz", "Estabilidad depende de tu chip RAM — si inestable, vuelve a 924 MHz" },
    [STR_RAM_OC_1032_REMOVE] = { "Remove 1032 MHz OC", "Eliminar OC 1032 MHz" },
    [STR_RAM_OC_REMOVE]      = { "Remove RAM OC", "Eliminar RAM OC" },
    [STR_RAM_OC_REMOVE_DESC] = { "Restore stock 786 MHz max — removes 924 and 1032 MHz OPPs", "Restaurar max stock 786 MHz — elimina OPPs 924 y 1032 MHz" },
    [STR_TUNE_924_VOLT]      = { "Tune 924 MHz voltage", "Ajustar voltaje 924 MHz" },
};

static int current_lang = LANG_EN;

static const char *S(StringID id) {
    if (id < 0 || id >= STR_COUNT) return "";
    return (current_lang == LANG_EN) ? I18N[id].en : I18N[id].es;
}

static void save_language(void) {
    FILE *f = fopen(LANG_FILE, "w");
    if (f) {
        fprintf(f, "%d\n", current_lang);
        fclose(f);
    }
}

static void load_language(void) {
    FILE *f = fopen(LANG_FILE, "r");
    if (f) {
        int v;
        if (fscanf(f, "%d", &v) == 1 && (v == LANG_EN || v == LANG_ES))
            current_lang = v;
        fclose(f);
    }
}

/* ── Globals ────────────────────────────────────────────────────────────── */
static SDL_Window         *win;
static SDL_Renderer       *ren;
static TTF_Font           *fnt_big, *fnt_med, *fnt_sm;
static SDL_GameController *gc;
static int W, H;
static volatile sig_atomic_t running = 1;

static void signal_handler(int sig) {
    (void)sig;
    running = 0;
}

static char cur_gov[32];
static int  cur_cpu_max_mhz;
static int  cur_gpu_mhz;
static float cur_cpu_temp;
static int  cur_ram_mhz;
static char os_subtitle[64] = "RK3326";

/* ── Sysfs helpers ──────────────────────────────────────────────────────── */
static char _rdbuf[1024];
static const char *read_file(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) { _rdbuf[0] = 0; return _rdbuf; }
    size_t n = fread(_rdbuf, 1, sizeof(_rdbuf)-1, f);
    fclose(f);
    _rdbuf[n] = 0;
    while (n > 0 && (_rdbuf[n-1]=='\n'||_rdbuf[n-1]==' '||_rdbuf[n-1]=='\t')) _rdbuf[--n]=0;
    return _rdbuf;
}
static int read_int(const char *path) { return atoi(read_file(path)); }
static int write_file(const char *path, const char *val) {
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "echo '%s' | sudo tee '%s' > /dev/null 2>&1", val, path);
    return system(cmd);
}

static void refresh_state(void) {
    char p[256];
    snprintf(p,sizeof(p),"%s/scaling_governor",CPU_POLICY);
    strncpy(cur_gov, read_file(p), sizeof(cur_gov)-1);
    cur_gov[sizeof(cur_gov)-1] = 0;
    snprintf(p,sizeof(p),"%s/scaling_max_freq",CPU_POLICY);
    cur_cpu_max_mhz = read_int(p) / 1000;
    snprintf(p,sizeof(p),"%s/cur_freq",GPU_DEVFREQ);
    cur_gpu_mhz = read_int(p) / 1000000;
    cur_cpu_temp = read_int(CPU_TEMP) / 1000.0f;
    snprintf(p,sizeof(p),"%s/cur_freq",DMC_DEVFREQ);
    cur_ram_mhz = read_int(p) / 1000000;
}

static void detect_os(void) {
    FILE *f = fopen("/etc/hostname", "r");
    char host[64] = {0};
    if (f) {
        if (fgets(host, sizeof(host), f)) {
            size_t n = strlen(host);
            while (n > 0 && (host[n-1]=='\n' || host[n-1]=='\r' || host[n-1]==' ' || host[n-1]=='\t'))
                host[--n] = 0;
        }
        fclose(f);
    }

    char lower[64];
    strncpy(lower, host, sizeof(lower)-1);
    lower[sizeof(lower)-1] = 0;
    for (int i = 0; lower[i]; i++) {
        if (lower[i] >= 'A' && lower[i] <= 'Z') lower[i] += 'a' - 'A';
    }

    const char *os_name = NULL;
    if (strstr(lower, "darkosre"))      os_name = "DARKOSRE";
    else if (strstr(lower, "darkos"))   os_name = "DARKOS";
    else if (strstr(lower, "arkos"))    os_name = "ARKOS";

    if (os_name) {
        snprintf(os_subtitle, sizeof(os_subtitle), "RK3326 | %s", os_name);
    } else if (host[0]) {
        snprintf(os_subtitle, sizeof(os_subtitle), "RK3326 | %s", host);
    }
}

/* ── Draw helpers ───────────────────────────────────────────────────────── */
static void setcol(Uint8 r,Uint8 g,Uint8 b){SDL_SetRenderDrawColor(ren,r,g,b,255);}
static void fillrect(int x,int y,int w,int h){SDL_Rect r={x,y,w,h};SDL_RenderFillRect(ren,&r);}

static void rounded(int x,int y,int w,int h,int rad,Uint8 r,Uint8 g,Uint8 b){
    setcol(r,g,b);
    SDL_Rect mid={x,y+rad,w,h-2*rad}; SDL_RenderFillRect(ren,&mid);
    SDL_Rect top={x+rad,y,w-2*rad,rad}; SDL_RenderFillRect(ren,&top);
    SDL_Rect bot={x+rad,y+h-rad,w-2*rad,rad}; SDL_RenderFillRect(ren,&bot);
    for(int dy=0;dy<rad;dy++){
        int dx=rad-(int)SDL_sqrtf((float)(rad*rad-dy*dy));
        SDL_RenderDrawLine(ren,x+dx,y+dy,x+w-dx,y+dy);
        SDL_RenderDrawLine(ren,x+dx,y+h-1-dy,x+w-dx,y+h-1-dy);
    }
}

static void txt(TTF_Font *f,const char *s,int x,int y,Uint8 r,Uint8 g,Uint8 b){
    if(!s||!s[0])return;
    SDL_Color c={r,g,b,255};
    SDL_Surface *sur=TTF_RenderUTF8_Blended(f,s,c); if(!sur)return;
    SDL_Texture *tex=SDL_CreateTextureFromSurface(ren,sur);
    SDL_Rect dst={x,y,sur->w,sur->h}; SDL_RenderCopy(ren,tex,NULL,&dst);
    SDL_DestroyTexture(tex); SDL_FreeSurface(sur);
}
static int txtw(TTF_Font *f,const char *s){int w=0;TTF_SizeUTF8(f,s,&w,NULL);return w;}
static void txtr(TTF_Font *f,const char *s,int rx,int y,Uint8 r,Uint8 g,Uint8 b){
    txt(f,s,rx-txtw(f,s),y,r,g,b);
}

static void draw_header(const char *title,const char *sub){
    setcol(16,18,38); fillrect(0,0,W,48);
    setcol(60,100,255); SDL_RenderDrawLine(ren,0,48,W,48);
    txt(fnt_big,title,28,10,100,160,255);
    if(sub) txtr(fnt_sm,sub,W-16,17,70,80,130);
}
static void draw_footer(const char *hint){
    setcol(16,18,38); fillrect(0,H-26,W,26);
    setcol(40,44,80); SDL_RenderDrawLine(ren,0,H-26,W,H-26);
    txt(fnt_sm,hint,28,H-20,70,75,110);
}
static void draw_bg(void){setcol(8,10,22);SDL_RenderClear(ren);}

/* ── Input ──────────────────────────────────────────────────────────────── */
typedef struct{int up,down,left,right,a,b,start,sel;}Keys;
static Keys poll_keys(void){
    Keys k={0}; SDL_Event ev;
    while(SDL_PollEvent(&ev)){
        if(ev.type==SDL_QUIT) running=0;
        if(ev.type==SDL_KEYDOWN) switch(ev.key.keysym.sym){
            case SDLK_UP:        k.up=1;break;
            case SDLK_DOWN:      k.down=1;break;
            case SDLK_LEFT:      k.left=1;break;
            case SDLK_RIGHT:     k.right=1;break;
            case SDLK_RETURN:    k.a=1;break;
            case SDLK_BACKSPACE: k.b=1;break;
            case SDLK_ESCAPE:    k.sel=1;break;
        }
        if(ev.type==SDL_CONTROLLERBUTTONDOWN) switch(ev.cbutton.button){
            case SDL_CONTROLLER_BUTTON_DPAD_UP:    k.up=1;break;
            case SDL_CONTROLLER_BUTTON_DPAD_DOWN:  k.down=1;break;
            case SDL_CONTROLLER_BUTTON_DPAD_LEFT:  k.left=1;break;
            case SDL_CONTROLLER_BUTTON_DPAD_RIGHT: k.right=1;break;
            case SDL_CONTROLLER_BUTTON_A:          k.a=1;break;
            case SDL_CONTROLLER_BUTTON_B:          k.b=1;break;
            case SDL_CONTROLLER_BUTTON_START:      k.start=1;break;
            case SDL_CONTROLLER_BUTTON_BACK:       k.sel=1;break;
        }
    }
    return k;
}

/* ── App lifecycle ──────────────────────────────────────────────────────── */
static void app_destroy(void);
static void app_init(void);
static void flush_sdl_events(void){SDL_Event ev; while(SDL_PollEvent(&ev));}

static void do_reboot(void){
    app_destroy();
    system("sync");
    system("echo ark | sudo -S /sbin/reboot");
    /* reboot didn't fire — reinit so app stays usable */
    app_init();
    flush_sdl_events();
    for(int i=0;i<SDL_NumJoysticks();i++)
        if(SDL_IsGameController(i)){gc=SDL_GameControllerOpen(i);break;}
    refresh_state();
}

/* ── Generic list submenu ───────────────────────────────────────────────── */
#define MAX_ITEMS 16
typedef struct{char label[64];char desc[96];char tag[32];}LItem;

static int submenu(const char *title,const char *sub,
                   LItem items[],int n,int *sel_inout,
                   const char *hint,int center){
    int sel=*sel_inout;
    int IH=52, PAD=24;
    int header_h=48, footer_h=26;
    int area=H-header_h-footer_h;
    int LY, visible;
    if (center) {
        if (n > 0 && n*IH <= area) {
            /* All items fit: center vertically in the available area. */
            LY = header_h + (area - n*IH)/2;
            visible = n;
        } else {
            /* Scroll needed: center the visible page. */
            visible = area/IH;
            if (visible < 1) visible = 1;
            LY = header_h + (area - visible*IH)/2;
        }
        if (LY < header_h + 4) LY = header_h + 4;
    } else {
        /* Keep the original top-aligned layout (CPU/GPU max freq). */
        LY = 56;
        visible = (H-LY-footer_h)/IH;
        if (visible < 1) visible = 1;
    }
    int scroll=0;
    if(sel>=scroll+visible) scroll=sel-visible+1;

    while(running){
        Keys k=poll_keys();
        if(k.up){sel=(sel-1+n)%n; if(sel<scroll)scroll=sel; if(sel>scroll+visible-1)scroll=sel-visible+1;}
        if(k.down){sel=(sel+1)%n; if(sel>=scroll+visible)scroll=sel-visible+1; if(sel<scroll)scroll=sel;}
        if(k.a){*sel_inout=sel;return sel;}
        if(k.b||k.sel) return -1;

        draw_bg();
        draw_header(title,sub);
        for(int i=scroll;i<n&&i<scroll+visible;i++){
            int iy=LY+(i-scroll)*IH;
            if(i==sel){
                rounded(PAD,iy,W-2*PAD,IH-5,8,30,60,180);
                setcol(80,140,255);fillrect(PAD,iy,4,IH-5);
                txt(fnt_med,items[i].label,PAD+18,iy+6,255,255,255);
                txt(fnt_sm, items[i].desc, PAD+18,iy+28,160,190,255);
                if(items[i].tag[0]) txtr(fnt_sm,items[i].tag,W-PAD-8,iy+18,255,220,80);
            }else{
                rounded(PAD,iy,W-2*PAD,IH-5,8,16,18,34);
                txt(fnt_med,items[i].label,PAD+18,iy+6,180,185,210);
                txt(fnt_sm, items[i].desc, PAD+18,iy+28,80,85,110);
                if(items[i].tag[0]) txtr(fnt_sm,items[i].tag,W-PAD-8,iy+18,140,160,200);
            }
        }
        char def_hint[128];
        snprintf(def_hint,sizeof(def_hint),"[DPAD] %s  [A] %s  [B] %s",
                 S(STR_NAVIGATE),S(STR_APPLY),S(STR_BACK));
        draw_footer(hint?hint:def_hint);
        SDL_RenderPresent(ren);
        SDL_Delay(16);
    }
    return -1;
}

/* ── Governor screen ────────────────────────────────────────────────────── */
static void screen_governor(void){
    char ap[256],cp[256];
    snprintf(ap,sizeof(ap),"%s/scaling_available_governors",CPU_POLICY);
    snprintf(cp,sizeof(cp),"%s/scaling_governor",CPU_POLICY);
    char *cur=read_file(cp); char curgov[32]; strncpy(curgov,cur,sizeof(curgov)-1); curgov[sizeof(curgov)-1]=0;
    char *avail=read_file(ap); char abuf[512]; strncpy(abuf,avail,sizeof(abuf)-1); abuf[sizeof(abuf)-1]=0;

    LItem items[MAX_ITEMS]; int n=0, sel=0;
    char *tok=strtok(abuf," \t\n");
    while(tok&&n<MAX_ITEMS){
        strncpy(items[n].label,tok,sizeof(items[n].label)-1); items[n].label[sizeof(items[n].label)-1]=0;
        StringID did = STR_CUSTOM_DESC;
        if(!strcmp(tok,"performance"))  did = STR_PERFORMANCE_DESC;
        if(!strcmp(tok,"schedutil"))    did = STR_SCHEDUTIL_DESC;
        if(!strcmp(tok,"ondemand"))     did = STR_ONDEMAND_DESC;
        if(!strcmp(tok,"conservative")) did = STR_CONSERVATIVE_DESC;
        if(!strcmp(tok,"powersave"))    did = STR_POWERSAVE_DESC;
        strncpy(items[n].desc,S(did),sizeof(items[n].desc)-1);
        if(!strcmp(tok,curgov)){strncpy(items[n].tag,S(STR_ACTIVE),sizeof(items[n].tag)-1);sel=n;}
        else items[n].tag[0]=0;
        n++; tok=strtok(NULL," \t\n");
    }
    int chosen=submenu(S(STR_CPU_GOVERNOR),S(STR_CORTEX_A35),items,n,&sel,NULL,1);
    if(chosen>=0){
        write_file(cp,items[chosen].label);
        refresh_state();
    }
}

static void show_info(const char *title, const char *msg); /* forward declaration */

/* ── OC reality detection ───────────────────────────────────────────────── */
static long long quick_lcg_bench(Uint32 ms) {
    volatile uint32_t a=1,b=2,c=3,d=4;
    long long iters = 0;
    Uint32 t0 = SDL_GetTicks();
    while ((SDL_GetTicks() - t0) < ms) {
        for (int i = 0; i < 1000000; i++) {
            a = a*1664525u+1013904223u;
            b = b*1664525u+1013904223u;
            c = c*1664525u+1013904223u;
            d = d*1664525u+1013904223u;
        }
        iters += 4000000;
    }
    if ((a^b^c^d)==0) iters++;
    return iters;
}

/* Stock kernel score at any freq > 1296 MHz: silicon stays at 1296 MHz.
   Measured on R36S with quick_lcg_bench() compiled at -O2: 1024M ops/4s.
   Real OC (teacupx kernel) at 1512 MHz yields ~1204M ops/4s (+17.6%).
   Threshold at 10% above stock reference; bad-cooling stock always stays below. */
#define OC_REF_STOCK_M 1024LL  /* M ops in 4s on stock silicon above 1296 MHz */

/* Returns 1=real OC (teacupx kernel), 0=stock (fake above 1296 MHz), -1=error */
static int detect_cpu_oc(int cur_hz) {
    {
        FILE *f = fopen(OC_DETECT_CACHE, "r");
        if (f) {
            int v = -1; fscanf(f, "%d", &v); fclose(f);
            if (v == 0 || v == 1) return v;
        }
    }
    if (cur_hz <= 1296000) return -1;

    /* Single bench at current freq — no freq switching needed */
    long long score = quick_lcg_bench(4000);
    long long score_M = score / 1000000LL;

    /* Scale reference to match actual bench duration (quick_lcg_bench targets ms) */
    long long threshold_M = OC_REF_STOCK_M * 110 / 100; /* +10% above stock */
    int result = (score_M > threshold_M) ? 1 : 0;

    FILE *f = fopen(OC_DETECT_CACHE, "w");
    if (f) { fprintf(f, "%d\n", result); fclose(f); }
    return result;
}

/* ── CPU max freq screen ────────────────────────────────────────────────── */
static void screen_cpu_freq(void){
    char ap[256],mp[256];
    snprintf(ap,sizeof(ap),"%s/scaling_available_frequencies",CPU_POLICY);
    snprintf(mp,sizeof(mp),"%s/scaling_max_freq",CPU_POLICY);
    int cur_hz=read_int(mp);
    char *avail=read_file(ap); char abuf[512]; strncpy(abuf,avail,sizeof(abuf)-1);

    int freqs[MAX_ITEMS]; int nf=0;
    char *tok=strtok(abuf," \t\n");
    while(tok&&nf<MAX_ITEMS){freqs[nf++]=atoi(tok);tok=strtok(NULL," \t\n");}
    for(int i=0;i<nf-1;i++) for(int j=i+1;j<nf;j++)
        if(freqs[j]>freqs[i]){int t=freqs[i];freqs[i]=freqs[j];freqs[j]=t;}

    /* Detect whether high freq is real (teacupx kernel) or software-only (stock).
       Runs a ~4s ratio test on first call; cached in OC_DETECT_CACHE afterwards. */
    int oc_real = -1;
    if (cur_hz > 1296000) {
        FILE *cf = fopen(OC_DETECT_CACHE, "r");
        int cached = 0;
        if (cf) { int v=-1; fscanf(cf,"%d",&v); fclose(cf); cached=(v==0||v==1); }
        if (!cached) show_info(S(STR_CPU_MAX_FREQ), "Detecting CPU OC...  (~4s)");
        oc_real = detect_cpu_oc(cur_hz);
    }

    /* When stock kernel is detected (oc_real==0) and cur_hz > 1296 MHz:
       - configured freq gets tag "SET (fake)" — software value, not silicon reality
       - 1296 MHz gets tag "silicon max" / ACTIVE — where hardware actually runs
       - sel cursor stays on configured freq so user sees it first */
    int stock_fake = (oc_real == 0 && cur_hz > 1296000);

    LItem items[MAX_ITEMS]; int n=0, sel=0;
    for(int i=0;i<nf;i++){
        int mhz=freqs[i]/1000;
        int fake = (mhz > 1296 && oc_real != 1);
        snprintf(items[n].label,sizeof(items[n].label),"%d %s",mhz,S(STR_MHZ));
        if(freqs[i]==cur_hz){
            if (stock_fake) {
                strncpy(items[n].desc,S(STR_CPU_FREQ_FAKE_DESC),sizeof(items[n].desc)-1);
                strncpy(items[n].tag,S(STR_CPU_FREQ_SET_FAKE),sizeof(items[n].tag)-1);
            } else {
                strncpy(items[n].desc,S(STR_CURRENT_MAX_FREQ),sizeof(items[n].desc)-1);
                strncpy(items[n].tag,S(STR_ACTIVE),sizeof(items[n].tag)-1);
            }
            sel=n;
        } else if (stock_fake && mhz == 1296) {
            strncpy(items[n].desc,S(STR_CURRENT_MAX_FREQ),sizeof(items[n].desc)-1);
            strncpy(items[n].tag,S(STR_CPU_FREQ_SILICON_MAX),sizeof(items[n].tag)-1);
        } else if (fake) {
            strncpy(items[n].desc,S(STR_CPU_FREQ_FAKE_DESC),sizeof(items[n].desc)-1);
            strncpy(items[n].tag,S(STR_CPU_FREQ_FAKE_TAG),sizeof(items[n].tag)-1);
        } else {
            snprintf(items[n].desc,sizeof(items[n].desc),S(STR_CPU_MAX_FREQ_DESC),mhz);
            items[n].tag[0]=0;
        }
        n++;
    }
    int chosen=submenu(S(STR_CPU_MAX_FREQ),S(STR_CORTEX_A35),items,n,&sel,NULL,0);
    if(chosen>=0){
        char val[32]; snprintf(val,sizeof(val),"%d",freqs[chosen]);
        write_file(mp,val);
        remove(OC_DETECT_CACHE); /* invalidate cache on freq change */
        refresh_state();
    }
}

/* ── GPU max freq screen ────────────────────────────────────────────────── */
static void screen_gpu_freq(void){
    char ap[256],mp[256];
    snprintf(ap,sizeof(ap),"%s/available_frequencies",GPU_DEVFREQ);
    snprintf(mp,sizeof(mp),"%s/max_freq",GPU_DEVFREQ);
    long long cur_hz=atoll(read_file(mp));
    char *avail=read_file(ap); char abuf[512]; strncpy(abuf,avail,sizeof(abuf)-1);

    long long freqs[MAX_ITEMS]; int nf=0;
    char *tok=strtok(abuf," \t\n");
    while(tok&&nf<MAX_ITEMS){freqs[nf++]=atoll(tok);tok=strtok(NULL," \t\n");}
    for(int i=0;i<nf-1;i++) for(int j=i+1;j<nf;j++)
        if(freqs[j]>freqs[i]){long long t=freqs[i];freqs[i]=freqs[j];freqs[j]=t;}

    LItem items[MAX_ITEMS]; int n=0, sel=0;
    for(int i=0;i<nf;i++){
        int mhz=(int)(freqs[i]/1000000LL);
        snprintf(items[n].label,sizeof(items[n].label),"%d %s",mhz,S(STR_MHZ));
        if(freqs[i]==cur_hz){
            strncpy(items[n].desc,S(STR_CURRENT_MAX_FREQ_GPU),sizeof(items[n].desc)-1);
            strncpy(items[n].tag,S(STR_ACTIVE),sizeof(items[n].tag)-1);
            sel=n;
        }else{
            snprintf(items[n].desc,sizeof(items[n].desc),S(STR_GPU_MAX_FREQ_DESC),mhz);
            items[n].tag[0]=0;
        }
        n++;
    }
    int chosen=submenu(S(STR_GPU_MAX_FREQ),S(STR_MALI_G31),items,n,&sel,NULL,0);
    if(chosen>=0){
        char val[32]; snprintf(val,sizeof(val),"%lld",freqs[chosen]);
        write_file(mp,val);
        refresh_state();
    }
}

/* ═══════════════════════════════════════════════════════════════════════════
   DTB TUNING
   ═══════════════════════════════════════════════════════════════════════════ */

static void popen_into(const char *cmd, char *buf, int bufsz) {
    buf[0] = 0;
    FILE *f = popen(cmd, "r");
    if (!f) return;
    size_t n = fread(buf, 1, bufsz-1, f);
    pclose(f);
    buf[n] = 0;
    while (n > 0 && (buf[n-1]=='\n'||buf[n-1]==' ')) buf[--n] = 0;
}

static const char *dtb_find(void) {
    static char path[256];
    const char *cands[] = {
        "/boot/rk3326-r36s-linux.dtb",
        "/boot/rk3326-r36s.dtb", NULL
    };
    for (int i = 0; cands[i]; i++) {
        if (access(cands[i], F_OK) == 0) {
            strncpy(path, cands[i], 255); return path;
        }
    }
    popen_into("ls /boot/rk3326*.dtb 2>/dev/null | head -1", path, sizeof(path));
    return path;
}

static const char *opp_bin_detect(void) {
    static char prop[64];
    FILE *f = fopen(BIN_CACHE_FILE, "r");
    if (f) {
        char line[32] = {0}; fgets(line, sizeof(line), f); fclose(f);
        for (int i = 0; line[i]; i++) {
            if (line[i]=='L' && line[i+1]>='0' && line[i+1]<='9') {
                snprintf(prop, sizeof(prop), "opp-microvolt-L%c", line[i+1]);
                return prop;
            }
        }
    }
    char r[32];
    popen_into("dmesg 2>/dev/null | grep -E 'opp-binning.*OPP prop name' "
               "| tail -1 | grep -oE 'L[0-9]' | tail -1", r, sizeof(r));
    if (!r[0]) {
        popen_into("dmesg 2>/dev/null | grep -oE 'pvtm-volt-sel=[0-9]' "
                   "| tail -1 | grep -oE '[0-9]$'", r, sizeof(r));
        if (r[0] >= '0' && r[0] <= '9') {
            char lb[4] = {'L', r[0], 0}; strncpy(r, lb, sizeof(r)-1);
        } else r[0] = 0;
    }
    if (r[0]=='L' && r[1]>='0' && r[1]<='9') {
        snprintf(prop, sizeof(prop), "opp-microvolt-%s", r);
        FILE *wf = fopen(BIN_CACHE_FILE, "w");
        if (wf) { fprintf(wf, "%s\n", r); fclose(wf); }
        return prop;
    }
    strncpy(prop, "opp-microvolt", sizeof(prop)-1);
    return prop;
}

/* finds OPP node by trying candidates, returns static buf (copy if needed) */
static const char *dtb_find_opp_node(const char *dtb, const char **cands) {
    static char node[80];
    node[0] = 0;
    char cmd[320], r[8];
    for (int i = 0; cands[i]; i++) {
        snprintf(cmd, sizeof(cmd),
            "fdtget '%s' '%s' compatible 2>/dev/null | head -c 4", dtb, cands[i]);
        popen_into(cmd, r, sizeof(r));
        if (r[0]) { strncpy(node, cands[i], sizeof(node)-1); return node; }
    }
    return node;
}

#define MAX_OPP 20
typedef struct { char node[200]; long long freq_hz; int volt_uv; } OPPEntry;

static int dtb_scan_opp(const char *dtb, const char *opp_base,
                         const char *bin_prop, OPPEntry entries[], int max) {
    char cmd[400];
    snprintf(cmd, sizeof(cmd), "fdtget -l '%s' '%s' 2>/dev/null | sort", dtb, opp_base);
    FILE *lf = popen(cmd, "r");
    if (!lf) return 0;
    char names[MAX_OPP][64]; int nn = 0;
    char line[128];
    while (fgets(line, sizeof(line), lf) && nn < MAX_OPP) {
        int len = strlen(line);
        while (len > 0 && (line[len-1]=='\n'||line[len-1]==' ')) line[--len] = 0;
        if (strncmp(line,"opp@",4)!=0 && strncmp(line,"opp-",4)!=0) continue;
        /* skip property-like names (e.g. opp-microvolt shouldn't appear as node but guard anyway) */
        if (atoll(line+4) == 0) continue;
        strncpy(names[nn++], line, 63);
    }
    pclose(lf);
    int n = 0;
    for (int i = 0; i < nn && n < max; i++) {
        long long freq = atoll(names[i]+4);
        char node_path[256];
        snprintf(node_path, sizeof(node_path), "%s/%s", opp_base, names[i]);
        char vcmd[400], vbuf[64];
        snprintf(vcmd, sizeof(vcmd),
            "fdtget -t u '%s' '%s' '%s' 2>/dev/null | awk '{print $1}'",
            dtb, node_path, bin_prop);
        popen_into(vcmd, vbuf, sizeof(vbuf));
        if (!vbuf[0]) {
            snprintf(vcmd, sizeof(vcmd),
                "fdtget -t u '%s' '%s' opp-microvolt 2>/dev/null | awk '{print $1}'",
                dtb, node_path);
            popen_into(vcmd, vbuf, sizeof(vbuf));
        }
        if (!vbuf[0]) continue;
        entries[n].freq_hz = freq;
        entries[n].volt_uv = atoi(vbuf);
        strncpy(entries[n].node, node_path, sizeof(entries[n].node)-1);
        n++;
    }
    return n;
}

static void fmt_mv(int uv, char *buf, int bufsz) {
    if (uv % 1000 == 500) snprintf(buf, bufsz, "%d.5", uv/1000);
    else                  snprintf(buf, bufsz, "%d",   uv/1000);
}

/* Format a large score with K/M/G suffixes and ~3 significant digits. */
static void fmt_score(long long val, char *buf, int bufsz) {
    if (val < 0) val = 0;
    if (val < 1000) {
        snprintf(buf, bufsz, "%lld", val);
    } else if (val < 1000000) {
        double v = val / 1000.0;
        if (v < 10)       snprintf(buf, bufsz, "%.2fK", v);
        else if (v < 100) snprintf(buf, bufsz, "%.1fK", v);
        else              snprintf(buf, bufsz, "%.0fK", v);
    } else if (val < 1000000000LL) {
        double v = val / 1000000.0;
        if (v < 10)       snprintf(buf, bufsz, "%.2fM", v);
        else if (v < 100) snprintf(buf, bufsz, "%.1fM", v);
        else              snprintf(buf, bufsz, "%.0fM", v);
    } else {
        double v = val / 1000000000.0;
        if (v < 10)       snprintf(buf, bufsz, "%.2fG", v);
        else if (v < 100) snprintf(buf, bufsz, "%.1fG", v);
        else              snprintf(buf, bufsz, "%.0fG", v);
    }
}

static void show_info(const char *title, const char *msg) {
    draw_bg(); draw_header(title, NULL);
    txt(fnt_med, msg, 28, 90, 200, 210, 240);
    SDL_RenderPresent(ren);
}

/* write safety scripts + enable systemd unit via sudo */
static void dtb_setup_safety(void) {
    FILE *f = fopen("/tmp/r36_safety_setup.sh", "w");
    if (!f) return;
    fprintf(f,
        "#!/bin/bash\n"
        "cat > /usr/local/bin/r36-dtb-safety.sh << 'SAFEEOF'\n"
        "#!/bin/bash\n"
        "DTB=/boot/rk3326-r36s-linux.dtb\n"
        "BOOTING=/boot/.r36_dtb_patch_booting\n"
        "PENDING=/boot/.r36_dtb_patch_pending\n"
        "if [ -f \"$BOOTING\" ]; then\n"
        "  [ -f \"$DTB.bak\" ] && cp \"$DTB.bak\" \"$DTB\"\n"
        "  rm -f \"$BOOTING\" \"$PENDING\"\n"
        "  sync\n"
        "  exit 0\n"
        "fi\n"
        "if [ -f \"$PENDING\" ]; then\n"
        "  mv \"$PENDING\" \"$BOOTING\" && sync\n"
        "fi\n"
        "exit 0\n"
        "SAFEEOF\n"
        "chmod +x /usr/local/bin/r36-dtb-safety.sh\n"
        "printf '[Unit]\\nDescription=R36 DTB safety\\n"
            "DefaultDependencies=no\\nAfter=local-fs.target\\nBefore=basic.target\\n\\n"
            "[Service]\\nType=oneshot\\n"
            "ExecStart=/usr/local/bin/r36-dtb-safety.sh\\nRemainAfterExit=yes\\n\\n"
            "[Install]\\nWantedBy=basic.target\\n'"
        " > /etc/systemd/system/r36-dtb-safety.service\n"
        /* late-boot service: clears BOOTING flag after ES starts OK */
        "cat > /usr/local/bin/r36-dtb-ok.sh << 'OKEOF'\n"
        "#!/bin/bash\n"
        "rm -f /boot/.r36_dtb_patch_booting\n"
        "sync\n"
        "OKEOF\n"
        "chmod +x /usr/local/bin/r36-dtb-ok.sh\n"
        "printf '[Unit]\\nDescription=R36 DTB boot OK\\nAfter=emulationstation.service\\n\\n"
            "[Service]\\nType=oneshot\\n"
            "ExecStart=/usr/local/bin/r36-dtb-ok.sh\\nRemainAfterExit=yes\\n\\n"
            "[Install]\\nWantedBy=multi-user.target\\n'"
        " > /etc/systemd/system/r36-dtb-ok.service\n"
        "systemctl daemon-reload 2>/dev/null\n"
        "systemctl enable r36-dtb-safety.service 2>/dev/null\n"
        "systemctl enable r36-dtb-ok.service 2>/dev/null\n"
    );
    fclose(f);
    system("echo ark | sudo -S bash /tmp/r36_safety_setup.sh > /dev/null 2>&1");
}

static void dtb_mark_pending(void) {
    system("echo ark | sudo -S touch " DTB_PENDING_FLAG " 2>/dev/null");
    system("echo ark | sudo -S sync 2>/dev/null");
}

/* ── Confirmation screens (summary + table + warnings + buttons) ──────────── */
#define CONFIRM_TABLE_MAX 24
#define CONFIRM_COL_LEN   56

typedef struct {
    char col1[CONFIRM_COL_LEN];
    char col2[CONFIRM_COL_LEN];
    char col3[CONFIRM_COL_LEN];
} ConfirmRow;

static int confirm_screen(const char *title, const char *summary,
                          const char *hdr1, const char *hdr2, const char *hdr3,
                          ConfirmRow rows[], int n_rows,
                          const char **warnings, int n_warnings,
                          const char **infos, int n_infos,
                          const char *yes_text, const char *no_text) {
    int sel = 0;
    const int PAD = 24;
    const int BTN_H = 46;
    const int BTN_W = (W - 2*PAD - 24) / 2;
    const int LINE_H = 20;
    const int ROW_H = 22;
    const int GAP = 18;
    const int HEADER_H = 48;
    const int FOOTER_H = 26;
    const int AREA = H - HEADER_H - FOOTER_H;
    int table_cols = (hdr1 && hdr2 && hdr3) ? 3 : ((hdr1 && hdr2) ? 2 : 0);

    while (running) {
        Keys k = poll_keys();
        if (k.up || k.down || k.left || k.right) sel ^= 1;
        if (k.a) return sel == 0;
        if (k.b || k.sel) return 0;
        draw_bg(); draw_header(title, NULL);

        int summary_h = summary ? LINE_H : 0;
        int table_h = (table_cols > 0 && n_rows > 0) ? (n_rows + 1) * ROW_H + 14 : 0;
        int warnings_h = n_warnings * LINE_H;
        int infos_h = n_infos * LINE_H;

        int gaps = 0;
        if (summary_h) gaps += GAP;
        if (table_h) gaps += GAP;
        if (warnings_h || infos_h) gaps += GAP;
        gaps += GAP; /* before buttons */

        int content_h = summary_h + table_h + warnings_h + infos_h + BTN_H + gaps;
        int start_y = HEADER_H + (AREA - content_h) / 2;
        if (start_y < HEADER_H + 4) start_y = HEADER_H + 4;

        int y = start_y;

        /* Summary */
        if (summary) {
            txt(fnt_med, summary, PAD, y, 100, 160, 255);
            y += LINE_H + GAP;
        }

        /* Table */
        if (table_h) {
            int table_w = W - 2*PAD;
            int table_top = y;
            int table_h_actual = (n_rows + 1) * ROW_H + 14;
            rounded(PAD, table_top, table_w, table_h_actual, 8, 16, 18, 34);

            int hy = table_top + 8;
            int c1x = PAD + 12;
            int c2x = PAD + 12 + table_w/3;
            int c3x = W - PAD - 12;

            txt(fnt_sm, hdr1, c1x, hy, 100, 160, 255);
            if (table_cols == 3) {
                txt(fnt_sm, hdr2, c2x, hy, 100, 160, 255);
                txtr(fnt_sm, hdr3, c3x, hy, 100, 160, 255);
            } else if (table_cols == 2) {
                txtr(fnt_sm, hdr2, c3x, hy, 100, 160, 255);
            }

            /* separator */
            setcol(40, 44, 80);
            SDL_RenderDrawLine(ren, PAD + 10, hy + ROW_H - 2, W - PAD - 10, hy + ROW_H - 2);

            for (int i = 0; i < n_rows; i++) {
                int ry = hy + (i + 1) * ROW_H;
                txt(fnt_sm, rows[i].col1, c1x, ry, 200, 210, 240);
                if (table_cols == 3) {
                    txt(fnt_sm, rows[i].col2, c2x, ry, 200, 210, 240);
                    txtr(fnt_sm, rows[i].col3, c3x, ry, 200, 210, 240);
                } else if (table_cols == 2) {
                    txtr(fnt_sm, rows[i].col2, c3x, ry, 200, 210, 240);
                }
            }
            y += table_h_actual + GAP;
        }

        /* Warnings */
        for (int i = 0; i < n_warnings; i++) {
            txt(fnt_sm, warnings[i], PAD, y, 255, 180, 80);
            y += LINE_H;
        }
        /* Infos */
        for (int i = 0; i < n_infos; i++) {
            txt(fnt_sm, infos[i], PAD, y, 120, 200, 255);
            y += LINE_H;
        }

        /* Buttons */
        int btn_y = y + GAP;
        if (btn_y + BTN_H > H - FOOTER_H - 8)
            btn_y = H - FOOTER_H - 8 - BTN_H;

        int yes_w = txtw(fnt_med, yes_text);
        int no_w = txtw(fnt_med, no_text);
        int txty = btn_y + BTN_H/2 - 10;

        if (sel==0){rounded(PAD,btn_y,BTN_W,BTN_H,8,30,60,180);txt(fnt_med,yes_text,PAD+BTN_W/2-yes_w/2,txty,255,255,255);}
        else       {rounded(PAD,btn_y,BTN_W,BTN_H,8,16,18,34); txt(fnt_med,yes_text,PAD+BTN_W/2-yes_w/2,txty,130,135,160);}
        int bx2 = PAD+BTN_W+24;
        if (sel==1){rounded(bx2,btn_y,BTN_W,BTN_H,8,30,60,180);txt(fnt_med,no_text,bx2+BTN_W/2-no_w/2,txty,255,255,255);}
        else       {rounded(bx2,btn_y,BTN_W,BTN_H,8,16,18,34); txt(fnt_med,no_text,bx2+BTN_W/2-no_w/2,txty,130,135,160);}

        char foot[128];
        snprintf(foot,sizeof(foot),"[DPAD] %s  [A] %s  [B] %s",
                 S(STR_SELECT),S(STR_APPLY),S(STR_CANCEL));
        draw_footer(foot);
        SDL_RenderPresent(ren); SDL_Delay(16);
    }
    return 0;
}

static int confirm_reboot(const char *title, const char *summary) {
    const char *infos[] = {S(STR_REQUIRES_REBOOT)};
    return confirm_screen(title, summary, NULL, NULL, NULL,
                          NULL, 0, NULL, 0, infos, 1,
                          S(STR_REBOOT), S(STR_LATER));
}

static int confirm_cpu_uv(const char *bin_prop, OPPEntry opp[], int n, int offset_uv) {
    ConfirmRow rows[CONFIRM_TABLE_MAX];
    int nr = 0;
    for (int i = 0; i < n && nr < CONFIRM_TABLE_MAX; i++) {
        int mhz = (int)(opp[i].freq_hz / 1000000LL);
        int new_uv = opp[i].volt_uv + offset_uv;
        if (new_uv < OPP_FLOOR_UV) new_uv = OPP_FLOOR_UV;
        char old[16], nw[16];
        fmt_mv(opp[i].volt_uv, old, sizeof(old));
        fmt_mv(new_uv, nw, sizeof(nw));
        snprintf(rows[nr].col1, CONFIRM_COL_LEN, "%d %s", mhz, S(STR_MHZ));
        snprintf(rows[nr].col2, CONFIRM_COL_LEN, "%s %s", old, S(STR_MILLIVOLTS));
        snprintf(rows[nr].col3, CONFIRM_COL_LEN, "%s %s", nw, S(STR_MILLIVOLTS));
        nr++;
    }

    char summary[128];
    char off_str[16];
    fmt_mv(offset_uv < 0 ? -offset_uv : offset_uv, off_str, sizeof(off_str));
    snprintf(summary, sizeof(summary), "%s %s%s %s %d OPPs", S(STR_APPLY),
             offset_uv < 0 ? "-" : "+", off_str, S(STR_MILLIVOLTS), n);

    const char *warnings[] = {S(STR_REQUIRES_REBOOT)};
    const char *infos[] = {
        S(STR_BACKUP_CREATED),
        S(STR_SAFETY_NET_RESTORE)
    };

    char cpu_uv_title[64]; snprintf(cpu_uv_title,sizeof(cpu_uv_title),"%s — %s",S(STR_CPU_UNDERVOLT),S(STR_CONFIRM));
    return confirm_screen(cpu_uv_title, summary,
                          S(STR_FREQUENCY), S(STR_ACTUAL_COL), S(STR_NEW_COL),
                          rows, nr, warnings, 1, infos, 2,
                          S(STR_APPLY), S(STR_CANCEL));
}

static int confirm_cpu_oc(int volt_uv, int has_node, const char *bin_prop) {
    ConfirmRow rows[4];
    int nr = 0;
    char mv[16]; fmt_mv(volt_uv, mv, sizeof(mv));

    snprintf(rows[nr].col1, CONFIRM_COL_LEN, "%s", S(STR_FREQUENCY));
    snprintf(rows[nr].col2, CONFIRM_COL_LEN, "1512 %s max (teacupx)", S(STR_MHZ)); nr++;
    snprintf(rows[nr].col1, CONFIRM_COL_LEN, "%s", S(STR_VALUE));
    snprintf(rows[nr].col2, CONFIRM_COL_LEN, "%s %s", mv, S(STR_MILLIVOLTS)); nr++;
    snprintf(rows[nr].col1, CONFIRM_COL_LEN, "AVS scale");
    snprintf(rows[nr].col2, CONFIRM_COL_LEN, "%s", S(STR_AVS_UNLOCKED)); nr++;
    snprintf(rows[nr].col1, CONFIRM_COL_LEN, "Bin prop");
    snprintf(rows[nr].col2, CONFIRM_COL_LEN, "%s", bin_prop); nr++;

    char summary[128];
    if (has_node)
        snprintf(summary, sizeof(summary), "%s @ %s %s", S(STR_CPU_OC_1608), mv, S(STR_MILLIVOLTS));
    else
        snprintf(summary, sizeof(summary), "%s @ %s %s", S(STR_CPU_OC_1608), mv, S(STR_MILLIVOLTS));

    const char *warnings[] = {S(STR_REQUIRES_REBOOT)};
    const char *infos[] = {
        S(STR_BACKUP_CREATED),
        S(STR_SAFETY_NET_RESTORE)
    };

    char cpu_oc_title[64]; snprintf(cpu_oc_title,sizeof(cpu_oc_title),"%s — %s",S(STR_CPU_OC_1608),S(STR_CONFIRM));
    return confirm_screen(cpu_oc_title, summary,
                          S(STR_PARAMETER), S(STR_VALUE), NULL,
                          rows, nr, warnings, 1, infos, 2,
                          S(STR_APPLY), S(STR_CANCEL));
}

static int confirm_gpu_oc(int volt_uv, int cur_uv, int has_node, const char *bin_prop) {
    ConfirmRow rows[2];
    int nr = 0;
    char new_mv[16], cur_mv[16];
    fmt_mv(volt_uv, new_mv, sizeof(new_mv));
    if (has_node && cur_uv > 0) fmt_mv(cur_uv, cur_mv, sizeof(cur_mv));
    else snprintf(cur_mv, sizeof(cur_mv), "--");

    snprintf(rows[nr].col1, CONFIRM_COL_LEN, "600 %s", S(STR_MHZ));
    snprintf(rows[nr].col2, CONFIRM_COL_LEN, "%s %s", cur_mv, S(STR_MILLIVOLTS));
    snprintf(rows[nr].col3, CONFIRM_COL_LEN, "%s %s", new_mv, S(STR_MILLIVOLTS)); nr++;

    char summary[128];
    snprintf(summary, sizeof(summary), "GPU 600 %s @ %s %s (%s)",
             S(STR_MHZ), new_mv, S(STR_MILLIVOLTS), S(STR_SHARED_RAIL));

    const char *warnings[] = {S(STR_REQUIRES_REBOOT), S(STR_SHARED_RAIL_WARN)};
    const char *infos[] = {
        S(STR_BACKUP_CREATED),
        S(STR_SAFETY_NET_RESTORE)
    };

    char gpu_oc_title[64]; snprintf(gpu_oc_title,sizeof(gpu_oc_title),"%s — %s",S(STR_GPU_OC_600),S(STR_CONFIRM));
    return confirm_screen(gpu_oc_title, summary,
                          S(STR_FREQUENCY), S(STR_ACTUAL_COL), S(STR_NEW_COL),
                          rows, nr, warnings, 2, infos, 2,
                          S(STR_APPLY), S(STR_CANCEL));
}

static int confirm_ram_oc(int volt_uv, int cur_uv, int has_node, const char *dmc_bin) {
    ConfirmRow rows[2];
    int nr = 0;
    char new_mv[16], cur_mv[16];
    fmt_mv(volt_uv, new_mv, sizeof(new_mv));
    if (has_node && cur_uv > 0) fmt_mv(cur_uv, cur_mv, sizeof(cur_mv));
    else snprintf(cur_mv, sizeof(cur_mv), "--");

    snprintf(rows[nr].col1, CONFIRM_COL_LEN, "928 %s", S(STR_MHZ));
    snprintf(rows[nr].col2, CONFIRM_COL_LEN, "%s %s", cur_mv, S(STR_MILLIVOLTS));
    snprintf(rows[nr].col3, CONFIRM_COL_LEN, "%s %s", new_mv, S(STR_MILLIVOLTS)); nr++;

    char summary[128];
    snprintf(summary, sizeof(summary), "RAM 928 %s @ %s %s (%s)",
             S(STR_MHZ), new_mv, S(STR_MILLIVOLTS), S(STR_VCC_DDR_RAIL));

    const char *warnings[] = {S(STR_REQUIRES_REBOOT), S(STR_SHARED_RAIL_WARN)};
    const char *infos[] = {
        S(STR_BACKUP_CREATED),
        S(STR_SAFETY_NET_RESTORE)
    };

    char ram_oc_title[64]; snprintf(ram_oc_title,sizeof(ram_oc_title),"%s — %s",S(STR_RAM_OC_928),S(STR_CONFIRM));
    return confirm_screen(ram_oc_title, summary,
                          S(STR_FREQUENCY), S(STR_ACTUAL_COL), S(STR_NEW_COL),
                          rows, nr, warnings, 2, infos, 2,
                          S(STR_APPLY), S(STR_CANCEL));
}

static int confirm_restore(void) {
    ConfirmRow rows[2];
    int nr = 0;
    snprintf(rows[nr].col1, CONFIRM_COL_LEN, "%s", S(STR_PARAMETER));
    snprintf(rows[nr].col2, CONFIRM_COL_LEN, "%s", S(STR_DTB_ORIGINAL_RESTORED)); nr++;
    snprintf(rows[nr].col1, CONFIRM_COL_LEN, "Safety net");
    snprintf(rows[nr].col2, CONFIRM_COL_LEN, "%s", S(STR_SAFETY_NET_DISABLED)); nr++;

    const char *warnings[] = {
        S(STR_RESTORE_ORIGINAL_SUMMARY),
        S(STR_REQUIRES_REBOOT)
    };
    const char *infos[] = {S(STR_BACKUP_CREATED)};

    return confirm_screen(S(STR_RESTORE_ORIGINAL), S(STR_RESTORE_ORIGINAL_SUMMARY),
                          S(STR_PARAMETER), S(STR_VALUE), NULL,
                          rows, nr, warnings, 2, infos, 1,
                          S(STR_RESTORE_ORIGINAL), S(STR_CANCEL));
}

/* ── Voltage picker builder ──────────────────────────────────────────────── */
#define VOLT_ITEMS_MAX 36
static int volt_items_build(LItem items[], int min_uv, int max_uv,
                             int *sel_out, int cur_uv) {
    int n = 0; *sel_out = 0;
    for (int v = max_uv; v >= min_uv && n < VOLT_ITEMS_MAX; v -= 12500) {
        char lbl[32]; fmt_mv(v, lbl, sizeof(lbl));
        strncat(lbl, " ", sizeof(lbl)-strlen(lbl)-1);
        strncat(lbl, S(STR_MILLIVOLTS), sizeof(lbl)-strlen(lbl)-1);
        strncpy(items[n].label, lbl, 63);
        items[n].desc[0] = 0; items[n].tag[0] = 0;
        if (cur_uv && abs(v - cur_uv) < 6250) *sel_out = n;
        n++;
    }
    return n;
}
static int volt_from_index(int max_uv, int idx) { return max_uv - idx * 12500; }

/* ── DTB: CPU Fine-Tune (per-OPP voltage) ───────────────────────────────── */
static void screen_dtb_cpu_finetune(const char *dtb, const char *opp_base,
                                    const char *bin_prop) {
    if (strcmp(bin_prop, "opp-microvolt") == 0) {
        show_info(S(STR_CPU_FINETUNE), S(STR_BIN_NOT_DETECTED));
        SDL_Delay(2500); return;
    }
    show_info(S(STR_CPU_FINETUNE), S(STR_READING_OPP));
    OPPEntry opp[MAX_OPP]; int n = dtb_scan_opp(dtb, opp_base, bin_prop, opp, MAX_OPP);
    if (n == 0) {
        show_info(S(STR_CPU_FINETUNE), S(STR_OPP_NOT_FOUND));
        SDL_Delay(2000); return;
    }

    int opp_sel = 0;
    while (running) {
        /* build OPP list highest-first — opp[] is sorted ascending by freq */
        LItem opp_items[MAX_OPP];
        for (int i = 0; i < n; i++) {
            int j = n - 1 - i;
            char mv[16]; fmt_mv(opp[j].volt_uv, mv, sizeof(mv));
            snprintf(opp_items[i].label, 64, "%lld MHz", opp[j].freq_hz / 1000000LL);
            snprintf(opp_items[i].desc,  96, "%s %s", mv, S(STR_MILLIVOLTS));
            opp_items[i].tag[0] = 0;
        }
        char hint[128];
        snprintf(hint, sizeof(hint), "%s  %s", S(STR_DPAD_SELECT), S(STR_A_SELECT_B_BACK));
        int chosen_opp = submenu(S(STR_CPU_FINETUNE), bin_prop, opp_items, n, &opp_sel, hint, 1);
        if (chosen_opp < 0) return;
        int real_opp = n - 1 - chosen_opp; /* map display index back to opp[] */

        /* voltage picker for the selected OPP */
        LItem vitems[VOLT_ITEMS_MAX]; int nvsel = 0;
        int nv = volt_items_build(vitems, OPP_FLOOR_UV, 1350000, &nvsel, opp[real_opp].volt_uv);
        char freq_sub[64];
        snprintf(freq_sub, sizeof(freq_sub), "%lld MHz — %s",
                 opp[real_opp].freq_hz / 1000000LL, bin_prop);
        char volt_hint[128];
        snprintf(volt_hint, sizeof(volt_hint), "%s  %s", S(STR_DPAD_VOLTAGE), S(STR_A_APPLY_B_BACK));
        int chosen_v = submenu(S(STR_CPU_FINETUNE), freq_sub, vitems, nv, &nvsel, volt_hint, 1);
        if (chosen_v < 0) continue;

        int new_uv = volt_from_index(1350000, chosen_v);
        if (new_uv == opp[real_opp].volt_uv) continue;

        /* confirm */
        char old_mv[16], new_mv[16];
        fmt_mv(opp[real_opp].volt_uv, old_mv, sizeof(old_mv));
        fmt_mv(new_uv, new_mv, sizeof(new_mv));
        ConfirmRow rows[1]; int nr = 0;
        snprintf(rows[nr].col1, CONFIRM_COL_LEN, "%lld %s", opp[real_opp].freq_hz / 1000000LL, S(STR_MHZ));
        snprintf(rows[nr].col2, CONFIRM_COL_LEN, "%s %s", old_mv, S(STR_MILLIVOLTS));
        snprintf(rows[nr].col3, CONFIRM_COL_LEN, "%s %s", new_mv, S(STR_MILLIVOLTS));
        nr++;
        char title[64]; snprintf(title, sizeof(title), "%s — %s", S(STR_CPU_FINETUNE), S(STR_CONFIRM));
        if (!confirm_screen(title, NULL,
                            S(STR_FREQUENCY), S(STR_ACTUAL_COL), S(STR_NEW_COL),
                            rows, nr,
                            NULL, 0, NULL, 0, S(STR_APPLY), S(STR_CANCEL)))
            continue;

        /* backup */
        char bak[280], cmd[600];
        snprintf(bak, sizeof(bak), "%s.bak", dtb);
        if (access(bak, F_OK) != 0) {
            snprintf(cmd, sizeof(cmd), "echo ark | sudo -S cp '%s' '%s' 2>/dev/null", dtb, bak);
            if (system(cmd) != 0) { show_info("ERROR", S(STR_BACKUP_FAILED)); SDL_Delay(2000); return; }
        }
        show_info(S(STR_CPU_FINETUNE), S(STR_PATCHING_DTB));

        /* patch single OPP — write 3-tuple (min typ max all same) */
        snprintf(cmd, sizeof(cmd),
            "echo ark | sudo -S fdtput -t u '%s' '%s' '%s' %d %d %d 2>/dev/null",
            dtb, opp[real_opp].node, bin_prop, new_uv, new_uv, new_uv);
        int fail = (system(cmd) != 0);
        if (!fail && strcmp(bin_prop, "opp-microvolt") != 0) {
            snprintf(cmd, sizeof(cmd),
                "echo ark | sudo -S fdtput -t u '%s' '%s' opp-microvolt %d %d %d 2>/dev/null",
                dtb, opp[real_opp].node, new_uv, new_uv, new_uv);
            system(cmd);
        }

        if (!fail) {
            opp[real_opp].volt_uv = new_uv; /* update local state */
            dtb_mark_pending(); dtb_setup_safety();
            char msg[80];
            snprintf(msg, sizeof(msg), "%lld MHz @ %s %s",
                     opp[real_opp].freq_hz / 1000000LL, new_mv, S(STR_MILLIVOLTS));
            if (confirm_reboot(S(STR_DTB_PATCHED), msg)) do_reboot();
            return;
        } else {
            show_info("ERROR", S(STR_PATCH_FAILED_RESTORE));
            SDL_Delay(1500);
            snprintf(cmd, sizeof(cmd), "echo ark | sudo -S cp '%s' '%s' 2>/dev/null", bak, dtb);
            system(cmd);
            return;
        }
    }
}

/* ── DTB: CPU Undervolt (uniform offset) ────────────────────────────────── */
static void screen_dtb_cpu_uv(const char *dtb, const char *opp_base,
                               const char *bin_prop) {
    if (strcmp(bin_prop, "opp-microvolt") == 0) {
        show_info(S(STR_CPU_UNDERVOLT), S(STR_BIN_NOT_DETECTED));
        SDL_Delay(2500); return;
    }
    show_info(S(STR_CPU_UNDERVOLT), S(STR_READING_OPP));
    OPPEntry opp[MAX_OPP]; int n = dtb_scan_opp(dtb, opp_base, bin_prop, opp, MAX_OPP);
    if (n == 0) {
        show_info(S(STR_CPU_UNDERVOLT), S(STR_OPP_NOT_FOUND));
        SDL_Delay(2000); return;
    }

    /* offset picker: +50mV → -200mV in 12.5mV steps = 21 items */
    LItem off_items[22]; int noff = 0;
    for (int uv = 50000; uv >= -200000; uv -= 12500) {
        char lbl[32];
        if (uv == 0) {
            strncpy(lbl, S(STR_NO_CHANGES), sizeof(lbl)-1);
        } else {
            int auv = uv < 0 ? -uv : uv;
            char mv[16]; fmt_mv(auv, mv, sizeof(mv));
            snprintf(lbl, sizeof(lbl), "%s%s %s", uv < 0 ? "-" : "+", mv, S(STR_MILLIVOLTS));
        }
        strncpy(off_items[noff].label, lbl, 63);
        off_items[noff].desc[0] = 0; off_items[noff].tag[0] = 0;
        noff++;
    }
    /* index 4 = 0mV (50, 37.5, 25, 12.5, 0) */
    int sel = 4;
    char sub[64];
    snprintf(sub, sizeof(sub), "%s | OPPs: %d", bin_prop, n);

    char uv_hint[128];
    snprintf(uv_hint,sizeof(uv_hint),"%s  %s",S(STR_DPAD_OFFSET),S(STR_A_SELECT_B_BACK));
    int chosen = submenu(S(STR_CPU_UNDERVOLT), sub, off_items, noff, &sel, uv_hint, 1);
    if (chosen < 0 || chosen == 4) return;
    int offset_uv = 50000 - chosen * 12500;

    /* preview */
    if (!confirm_cpu_uv(bin_prop, opp, n, offset_uv)) return;

    /* backup */
    char bak[280]; snprintf(bak, sizeof(bak), "%s.bak", dtb);
    if (access(bak, F_OK) != 0) {
        char c[600];
        snprintf(c, sizeof(c), "echo ark | sudo -S cp '%s' '%s' 2>/dev/null", dtb, bak);
        if (system(c) != 0) {
            show_info("ERROR", S(STR_BACKUP_FAILED)); SDL_Delay(2000); return;
        }
    }
    show_info(S(STR_CPU_UNDERVOLT), S(STR_PATCHING_DTB));

    int fail = 0;
    char cmd[800];
    for (int i = 0; i < n; i++) {
        char vcmd[400], vraw[256];
        snprintf(vcmd, sizeof(vcmd), "fdtget -t u '%s' '%s' '%s' 2>/dev/null",
                 dtb, opp[i].node, bin_prop);
        popen_into(vcmd, vraw, sizeof(vraw));
        if (!vraw[0]) continue;
        char new_vals[256] = ""; char vr2[256]; strncpy(vr2, vraw, sizeof(vr2)-1);
        char *tok = strtok(vr2, " \t\n");
        while (tok) {
            int uv = atoi(tok); int nu = uv + offset_uv;
            if (nu < OPP_FLOOR_UV) nu = OPP_FLOOR_UV;
            char tmp[32]; snprintf(tmp, sizeof(tmp), "%d ", nu);
            strncat(new_vals, tmp, sizeof(new_vals)-strlen(new_vals)-1);
            tok = strtok(NULL, " \t\n");
        }
        snprintf(cmd, sizeof(cmd),
            "echo ark | sudo -S fdtput -t u '%s' '%s' '%s' %s 2>/dev/null",
            dtb, opp[i].node, bin_prop, new_vals);
        if (system(cmd) != 0) fail = 1;
    }

    if (!fail) {
        dtb_mark_pending(); dtb_setup_safety();
        if (confirm_reboot(S(STR_DTB_PATCHED), S(STR_PATCH_SUCCESS)))
            do_reboot();
    } else {
        show_info("ERROR", S(STR_PATCH_FAILED_RESTORE));
        SDL_Delay(1500);
        snprintf(cmd, sizeof(cmd),
            "echo ark | sudo -S cp '%s' '%s' 2>/dev/null", bak, dtb);
        system(cmd);
    }
}

/* ── DTB: CPU OC 1608 MHz ────────────────────────────────────────────────── */
static void screen_dtb_cpu_oc(const char *dtb, const char *opp_base,
                               const char *bin_prop) {
    if (strcmp(bin_prop, "opp-microvolt") == 0) {
        show_info(S(STR_CPU_OC_1608), S(STR_BIN_NOT_DETECTED));
        SDL_Delay(2500); return;
    }
    char cmd[400], r[32];
    snprintf(cmd, sizeof(cmd),
        "fdtget '%s' '%s/opp-1608000000' opp-hz 2>/dev/null | head -c 4",
        dtb, opp_base);
    popen_into(cmd, r, sizeof(r));
    int has_node = r[0] != 0;

    int cur_uv = 0;
    if (has_node) {
        snprintf(cmd, sizeof(cmd),
            "fdtget -t u '%s' '%s/opp-1608000000' '%s' 2>/dev/null | awk '{print $1}'",
            dtb, opp_base, bin_prop);
        popen_into(cmd, r, sizeof(r)); cur_uv = atoi(r);
    }

    char sub[80];
    if (has_node) {
        char mv[16]; fmt_mv(cur_uv, mv, sizeof(mv));
        snprintf(sub, sizeof(sub), "%s: %s %s", S(STR_NODE_ACTIVE), mv, S(STR_MILLIVOLTS));
    } else {
        snprintf(sub, sizeof(sub), "%s: %s", S(STR_CPU_OC_1608), S(STR_DTB_TUNING_DESC));
    }

    if (!has_node) {
        const char *oc_warnings[] = { S(STR_CPU_OC_STOCK_WARN) };
        const char *oc_infos[]   = { S(STR_CPU_OC_NEEDS_KERNEL), S(STR_CPU_OC_KERNEL_MAX) };
        if (!confirm_screen(S(STR_CPU_OC_1608), NULL,
                            NULL, NULL, NULL, NULL, 0,
                            oc_warnings, 1, oc_infos, 2,
                            S(STR_CONTINUE), S(STR_CANCEL))) return;
    }

    LItem vitems[VOLT_ITEMS_MAX]; int nvsel = 0;
    int nv = volt_items_build(vitems, 950000, 1350000, &nvsel,
                              cur_uv ? cur_uv : 1150000);
    char cpu_oc_hint[128];
    snprintf(cpu_oc_hint,sizeof(cpu_oc_hint),"%s  %s",S(STR_DPAD_VOLTAGE),S(STR_A_APPLY_B_BACK));
    int chosen = submenu(S(STR_CPU_OC_1608), sub, vitems, nv, &nvsel, cpu_oc_hint, 1);
    if (chosen < 0) return;
    int volt_uv = volt_from_index(1350000, chosen);
    char volt_mv[16]; fmt_mv(volt_uv, volt_mv, sizeof(volt_mv));

    if (!confirm_cpu_oc(volt_uv, has_node, bin_prop)) return;

    char bak[280]; snprintf(bak, sizeof(bak), "%s.bak", dtb);
    if (access(bak, F_OK) != 0) {
        snprintf(cmd, sizeof(cmd),
            "echo ark | sudo -S cp '%s' '%s' 2>/dev/null", dtb, bak);
        if (system(cmd) != 0) {
            show_info("ERROR", S(STR_BACKUP_FAILED)); SDL_Delay(2000); return;
        }
    }
    show_info(S(STR_CPU_OC_1608), S(STR_PATCHING_DTB));

    int fail = 0;
    char npath[200]; snprintf(npath, sizeof(npath), "%s/opp-1608000000", opp_base);
    if (!has_node) {
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -c '%s' '%s' 2>/dev/null",dtb,npath);
        if(system(cmd)!=0) fail=1;
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -t u '%s' '%s' opp-hz 0 1608000000 2>/dev/null",dtb,npath);
        if(system(cmd)!=0) fail=1;
        /* disable AVS OPP stripping */
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -t u '%s' '%s' 'rockchip,avs-scale' 0 2>/dev/null",dtb,opp_base);
        system(cmd);
    }
    snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -t u '%s' '%s' '%s' %d %d %d 2>/dev/null",
             dtb,npath,bin_prop,volt_uv,volt_uv,volt_uv);
    if(system(cmd)!=0) fail=1;
    if(strcmp(bin_prop,"opp-microvolt")!=0) {
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -t u '%s' '%s' opp-microvolt %d %d %d 2>/dev/null",
                 dtb,npath,volt_uv,volt_uv,volt_uv);
        system(cmd);
    }

    if (!fail) {
        dtb_mark_pending(); dtb_setup_safety();
        char msg[80]; snprintf(msg,sizeof(msg),"CPU OC @ %s %s aplicado.",volt_mv,S(STR_MILLIVOLTS));
        if (confirm_reboot(S(STR_OC_PATCHED), msg))
            do_reboot();
    } else {
        show_info("ERROR", S(STR_PATCH_FAILED_RESTORE));
        SDL_Delay(1500);
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S cp '%s' '%s' 2>/dev/null",bak,dtb);
        system(cmd);
    }
}

/* ── DTB: GPU OC 600 MHz ─────────────────────────────────────────────────── */
static void screen_dtb_gpu_oc(const char *dtb, const char *bin_prop) {
    const char *gpu_cands[] = {
        "/gpu-opp-table","/gpu_opp_table","/gpu-opp-table-0",NULL
    };
    const char *gpu_opp = dtb_find_opp_node(dtb, gpu_cands);
    if (!gpu_opp[0]) {
        show_info(S(STR_GPU_OC_600), S(STR_TABLE_NOT_FOUND));
        SDL_Delay(2000); return;
    }
    if (strcmp(bin_prop,"opp-microvolt")==0) {
        show_info(S(STR_GPU_OC_600), S(STR_BIN_NOT_DETECTED));
        SDL_Delay(2500); return;
    }
    char cmd[400], r[32];
    snprintf(cmd,sizeof(cmd),"fdtget '%s' '%s/opp-600000000' opp-hz 2>/dev/null | head -c 4",
             dtb,gpu_opp);
    popen_into(cmd,r,sizeof(r));
    int has_node = r[0] != 0;
    int cur_uv = 0;
    if (has_node) {
        snprintf(cmd,sizeof(cmd),"fdtget -t u '%s' '%s/opp-600000000' '%s' 2>/dev/null | awk '{print $1}'",
                 dtb,gpu_opp,bin_prop);
        popen_into(cmd,r,sizeof(r)); cur_uv = atoi(r);
    }
    char sub[80];
    snprintf(sub,sizeof(sub),"%s | %s",has_node?S(STR_NODE_ACTIVE):S(STR_GPU_OC_600),S(STR_SHARED_RAIL));

    LItem vitems[VOLT_ITEMS_MAX]; int nvsel=0;
    int nv = volt_items_build(vitems,950000,1150000,&nvsel,cur_uv?cur_uv:1050000);
    char gpu_oc_hint[128];
    snprintf(gpu_oc_hint,sizeof(gpu_oc_hint),"%s  %s",S(STR_DPAD_VOLTAGE),S(STR_A_APPLY_B_BACK));
    int chosen = submenu(S(STR_GPU_OC_600),S(STR_SHARED_RAIL),vitems,nv,&nvsel,gpu_oc_hint,1);
    if (chosen < 0) return;
    int volt_uv = volt_from_index(1150000,chosen);
    char volt_mv[16]; fmt_mv(volt_uv,volt_mv,sizeof(volt_mv));

    if (!confirm_gpu_oc(volt_uv, cur_uv, has_node, bin_prop)) return;

    char bak[280]; snprintf(bak,sizeof(bak),"%s.bak",dtb);
    if (access(bak,F_OK)!=0) {
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S cp '%s' '%s' 2>/dev/null",dtb,bak);
        if(system(cmd)!=0){show_info("ERROR",S(STR_BACKUP_FAILED));SDL_Delay(2000);return;}
    }
    show_info(S(STR_GPU_OC_600),S(STR_PATCHING_DTB));
    int fail=0;
    char npath[200]; snprintf(npath,sizeof(npath),"%s/opp-600000000",gpu_opp);
    if (!has_node) {
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -c '%s' '%s' 2>/dev/null",dtb,npath);
        if(system(cmd)!=0) fail=1;
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -t u '%s' '%s' opp-hz 0 600000000 2>/dev/null",dtb,npath);
        if(system(cmd)!=0) fail=1;
    }
    snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -t u '%s' '%s' '%s' %d 2>/dev/null",
             dtb,npath,bin_prop,volt_uv);
    if(system(cmd)!=0) fail=1;
    if(strcmp(bin_prop,"opp-microvolt")!=0) {
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -t u '%s' '%s' opp-microvolt %d 2>/dev/null",
                 dtb,npath,volt_uv);
        system(cmd);
    }
    if (!fail) {
        dtb_mark_pending(); dtb_setup_safety();
        char msg[80]; snprintf(msg,sizeof(msg),"600 %s @ %s %s aplicado.",S(STR_MHZ),volt_mv,S(STR_MILLIVOLTS));
        if (confirm_reboot(S(STR_GPU_OC_600), msg))
            do_reboot();
    } else {
        show_info("ERROR",S(STR_PATCH_FAILED_RESTORE));
        SDL_Delay(1500);
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S cp '%s' '%s' 2>/dev/null",bak,dtb);
        system(cmd);
    }
}

/* ── DTB: RAM OC 928 MHz ─────────────────────────────────────────────────── */
static void screen_dtb_ram_oc(const char *dtb, const char *bin_prop) {
    const char *dmc_cands[] = {"/dmc-opp-table","/dmc_opp_table",NULL};
    const char *dmc_opp = dtb_find_opp_node(dtb, dmc_cands);
    if (!dmc_opp[0]) {
        show_info(S(STR_RAM_OC_928), S(STR_TABLE_NOT_FOUND));
        SDL_Delay(2000); return;
    }
    /* try DMC-specific bin first, fall back to CPU bin_prop */
    char dmc_bin[64]; dmc_bin[0] = 0;
    popen_into("dmesg 2>/dev/null | grep -iE 'dmc.*opp-binning' | tail -1 "
               "| grep -oE 'L[0-9]' | tail -1", dmc_bin, sizeof(dmc_bin));
    if (dmc_bin[0]=='L' && dmc_bin[1]>='0') {
        char tmp[64]; snprintf(tmp,sizeof(tmp),"opp-microvolt-%s",dmc_bin);
        strncpy(dmc_bin,tmp,sizeof(dmc_bin)-1);
    } else {
        strncpy(dmc_bin, bin_prop, sizeof(dmc_bin)-1);
    }
    if (strcmp(dmc_bin,"opp-microvolt")==0) {
        show_info(S(STR_RAM_OC_928), S(STR_BIN_NOT_DETECTED));
        SDL_Delay(2500); return;
    }
    char cmd[400], r[32];
    snprintf(cmd,sizeof(cmd),"fdtget '%s' '%s/opp-928000000' opp-hz 2>/dev/null | head -c 4",
             dtb,dmc_opp);
    popen_into(cmd,r,sizeof(r));
    int has_node = r[0]!=0;
    int cur_uv=0;
    if (has_node) {
        snprintf(cmd,sizeof(cmd),"fdtget -t u '%s' '%s/opp-928000000' '%s' 2>/dev/null | awk '{print $1}'",
                 dtb,dmc_opp,dmc_bin);
        popen_into(cmd,r,sizeof(r)); cur_uv=atoi(r);
    }
    /* if 924 MHz already active — show action submenu */
    if (has_node) {
        char r2[32];
        snprintf(cmd,sizeof(cmd),"fdtget '%s' '%s/opp-1040000000' opp-hz 2>/dev/null | head -c 4",
                 dtb,dmc_opp);
        popen_into(cmd,r2,sizeof(r2));
        int has_1032 = r2[0]!=0;

        /* build dynamic menu */
        LItem mopts[4]; int mopt_n=0, msel=0;
        /* 0: tune 924 */
        strncpy(mopts[mopt_n].label,S(STR_TUNE_924_VOLT),63);
        mopts[mopt_n].desc[0]=0; mopts[mopt_n].tag[0]=0; mopt_n++;
        /* 1: add or tune 1032 */
        strncpy(mopts[mopt_n].label,S(STR_RAM_OC_1032),63);
        strncpy(mopts[mopt_n].desc,S(STR_RAM_OC_1032_DESC),95);
        strncpy(mopts[mopt_n].tag,has_1032?S(STR_ACTIVE):"",31); mopt_n++;
        /* 2: remove 1032 (only if active) */
        int idx_remove_1032=-1, idx_remove_all=-1;
        if (has_1032) {
            idx_remove_1032=mopt_n;
            strncpy(mopts[mopt_n].label,S(STR_RAM_OC_1032_REMOVE),63);
            mopts[mopt_n].desc[0]=0; mopts[mopt_n].tag[0]=0; mopt_n++;
        }
        /* last: remove all RAM OC */
        idx_remove_all=mopt_n;
        strncpy(mopts[mopt_n].label,S(STR_RAM_OC_REMOVE),63);
        strncpy(mopts[mopt_n].desc,S(STR_RAM_OC_REMOVE_DESC),95);
        mopts[mopt_n].tag[0]=0; mopt_n++;

        char mhint[128];
        snprintf(mhint,sizeof(mhint),"%s  %s",S(STR_DPAD_SELECT),S(STR_A_SELECT_B_BACK));
        int mc=submenu(S(STR_RAM_OC_928),S(STR_VCC_DDR_RAIL),mopts,mopt_n,&msel,mhint,1);
        if (mc<0) return;

        /* ── Remove 1032 MHz ── */
        if (mc==idx_remove_1032) {
            if (!confirm_screen(S(STR_RAM_OC_1032_REMOVE),NULL,NULL,NULL,NULL,NULL,0,
                                NULL,0,NULL,0,S(STR_APPLY),S(STR_CANCEL))) return;
            char bak[280]; snprintf(bak,sizeof(bak),"%s.bak",dtb);
            if (access(bak,F_OK)!=0){
                snprintf(cmd,sizeof(cmd),"echo ark | sudo -S cp '%s' '%s' 2>/dev/null",dtb,bak);
                if(system(cmd)!=0){show_info("ERROR",S(STR_BACKUP_FAILED));SDL_Delay(2000);return;}
            }
            show_info(S(STR_RAM_OC_1032_REMOVE),S(STR_PATCHING_DTB));
            snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -r '%s' '%s/opp-1040000000' 2>/dev/null",dtb,dmc_opp);
            if(system(cmd)==0){
                dtb_mark_pending(); dtb_setup_safety();
                if(confirm_reboot(S(STR_DTB_PATCHED),"1032 MHz OPP removed")) do_reboot();
            } else {
                show_info("ERROR",S(STR_PATCH_FAILED_RESTORE)); SDL_Delay(1500);
            }
            return;
        }

        /* ── Remove all RAM OC ── */
        if (mc==idx_remove_all) {
            if (!confirm_screen(S(STR_RAM_OC_REMOVE),NULL,NULL,NULL,NULL,NULL,0,
                                NULL,0,NULL,0,S(STR_APPLY),S(STR_CANCEL))) return;
            char bak[280]; snprintf(bak,sizeof(bak),"%s.bak",dtb);
            if (access(bak,F_OK)!=0){
                snprintf(cmd,sizeof(cmd),"echo ark | sudo -S cp '%s' '%s' 2>/dev/null",dtb,bak);
                if(system(cmd)!=0){show_info("ERROR",S(STR_BACKUP_FAILED));SDL_Delay(2000);return;}
            }
            show_info(S(STR_RAM_OC_REMOVE),S(STR_PATCHING_DTB));
            int fail=0;
            if (has_1032) {
                snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -r '%s' '%s/opp-1040000000' 2>/dev/null",dtb,dmc_opp);
                if(system(cmd)!=0) fail=1;
            }
            snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -r '%s' '%s/opp-928000000' 2>/dev/null",dtb,dmc_opp);
            if(system(cmd)!=0) fail=1;
            if(!fail){
                dtb_mark_pending(); dtb_setup_safety();
                if(confirm_reboot(S(STR_DTB_PATCHED),"RAM OC removed — stock 786 MHz")) do_reboot();
            } else {
                show_info("ERROR",S(STR_PATCH_FAILED_RESTORE)); SDL_Delay(1500);
                snprintf(cmd,sizeof(cmd),"echo ark | sudo -S cp '%s' '%s' 2>/dev/null",bak,dtb);
                system(cmd);
            }
            return;
        }

        /* ── Add / tune 1032 MHz ── */
        if (mc==1) {
            int cur_1032=0;
            if (has_1032) {
                snprintf(cmd,sizeof(cmd),"fdtget -t u '%s' '%s/opp-1040000000' '%s' 2>/dev/null | awk '{print $1}'",
                         dtb,dmc_opp,dmc_bin);
                popen_into(cmd,r2,sizeof(r2)); cur_1032=atoi(r2);
            }
            const char *w1032[]={ S(STR_RAM_OC_1032_WARN1), S(STR_RAM_OC_1032_WARN2), S(STR_RAM_OC_1032_WARN3) };
            LItem vitems2[VOLT_ITEMS_MAX]; int nvsel2=0;
            volt_items_build(vitems2,950000,1150000,&nvsel2,cur_1032?cur_1032:1150000);
            int nv2=volt_items_build(vitems2,950000,1150000,&nvsel2,cur_1032?cur_1032:1150000);
            char v1032hint[128];
            snprintf(v1032hint,sizeof(v1032hint),"%s  %s",S(STR_DPAD_VOLTAGE),S(STR_A_APPLY_B_BACK));
            int cv=submenu(S(STR_RAM_OC_1032),S(STR_RAM_OC_1032_DESC),vitems2,nv2,&nvsel2,v1032hint,1);
            if (cv<0) return;
            int volt_1032=volt_from_index(1150000,cv);
            char mv_1032[16]; fmt_mv(volt_1032,mv_1032,sizeof(mv_1032));
            ConfirmRow rows[2]; int nr=0;
            snprintf(rows[nr].col1,CONFIRM_COL_LEN,"DMC"); snprintf(rows[nr].col2,CONFIRM_COL_LEN,"1032 %s",S(STR_MHZ)); rows[nr].col3[0]=0; nr++;
            snprintf(rows[nr].col1,CONFIRM_COL_LEN,"%s",S(STR_VALUE)); snprintf(rows[nr].col2,CONFIRM_COL_LEN,"%s %s",mv_1032,S(STR_MILLIVOLTS)); rows[nr].col3[0]=0; nr++;
            char t1032[64]; snprintf(t1032,sizeof(t1032),"%s — %s",S(STR_RAM_OC_1032),S(STR_CONFIRM));
            if (!confirm_screen(t1032,NULL,NULL,NULL,NULL,rows,nr,w1032,3,NULL,0,S(STR_APPLY),S(STR_CANCEL))) return;
            char bak[280]; snprintf(bak,sizeof(bak),"%s.bak",dtb);
            if (access(bak,F_OK)!=0){
                snprintf(cmd,sizeof(cmd),"echo ark | sudo -S cp '%s' '%s' 2>/dev/null",dtb,bak);
                if(system(cmd)!=0){show_info("ERROR",S(STR_BACKUP_FAILED));SDL_Delay(2000);return;}
            }
            show_info(S(STR_RAM_OC_1032),S(STR_PATCHING_DTB));
            int fail=0;
            char npath1032[200]; snprintf(npath1032,sizeof(npath1032),"%s/opp-1040000000",dmc_opp);
            if (!has_1032){
                snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -c '%s' '%s' 2>/dev/null",dtb,npath1032);
                if(system(cmd)!=0) fail=1;
                snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -t u '%s' '%s' opp-hz 0 1040000000 2>/dev/null",dtb,npath1032);
                if(system(cmd)!=0) fail=1;
            }
            snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -t u '%s' '%s' '%s' %d 2>/dev/null",dtb,npath1032,dmc_bin,volt_1032);
            if(system(cmd)!=0) fail=1;
            if(strcmp(dmc_bin,"opp-microvolt")!=0){
                snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -t u '%s' '%s' opp-microvolt %d 2>/dev/null",dtb,npath1032,volt_1032);
                system(cmd);
            }
            if(!fail){
                dtb_mark_pending(); dtb_setup_safety();
                char msg[80]; snprintf(msg,sizeof(msg),"1032 %s @ %s %s",S(STR_MHZ),mv_1032,S(STR_MILLIVOLTS));
                if(confirm_reboot(S(STR_RAM_OC_1032),msg)) do_reboot();
            } else {
                show_info("ERROR",S(STR_PATCH_FAILED_RESTORE)); SDL_Delay(1500);
                snprintf(cmd,sizeof(cmd),"echo ark | sudo -S cp '%s' '%s' 2>/dev/null",bak,dtb);
                system(cmd);
            }
            return;
        }
        /* mc==0: fall through to tune 924 MHz voltage picker below */
    }

    char sub[80];
    snprintf(sub,sizeof(sub),"%s | %s",has_node?S(STR_NODE_ACTIVE):S(STR_RAM_OC_928),S(STR_VCC_DDR_RAIL));

    LItem vitems[VOLT_ITEMS_MAX]; int nvsel=0;
    int nv=volt_items_build(vitems,950000,1150000,&nvsel,cur_uv?cur_uv:1100000);
    char ram_oc_hint[128];
    snprintf(ram_oc_hint,sizeof(ram_oc_hint),"%s  %s",S(STR_DPAD_VOLTAGE),S(STR_A_APPLY_B_BACK));
    int chosen=submenu(S(STR_RAM_OC_928),S(STR_VCC_DDR_RAIL),vitems,nv,&nvsel,ram_oc_hint,1);
    if (chosen<0) return;
    int volt_uv=volt_from_index(1150000,chosen);
    char volt_mv[16]; fmt_mv(volt_uv,volt_mv,sizeof(volt_mv));

    if (!confirm_ram_oc(volt_uv, cur_uv, has_node, dmc_bin)) return;

    char bak[280]; snprintf(bak,sizeof(bak),"%s.bak",dtb);
    if (access(bak,F_OK)!=0) {
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S cp '%s' '%s' 2>/dev/null",dtb,bak);
        if(system(cmd)!=0){show_info("ERROR",S(STR_BACKUP_FAILED));SDL_Delay(2000);return;}
    }
    show_info(S(STR_RAM_OC_928),S(STR_PATCHING_DTB));
    int fail=0;
    char npath[200]; snprintf(npath,sizeof(npath),"%s/opp-928000000",dmc_opp);
    if (!has_node) {
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -c '%s' '%s' 2>/dev/null",dtb,npath);
        if(system(cmd)!=0) fail=1;
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -t u '%s' '%s' opp-hz 0 928000000 2>/dev/null",dtb,npath);
        if(system(cmd)!=0) fail=1;
    }
    snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -t u '%s' '%s' '%s' %d 2>/dev/null",
             dtb,npath,dmc_bin,volt_uv);
    if(system(cmd)!=0) fail=1;
    if(strcmp(dmc_bin,"opp-microvolt")!=0) {
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S fdtput -t u '%s' '%s' opp-microvolt %d 2>/dev/null",
                 dtb,npath,volt_uv);
        system(cmd);
    }
    if (!fail) {
        dtb_mark_pending(); dtb_setup_safety();
        char msg[80]; snprintf(msg,sizeof(msg),"928 %s @ %s %s aplicado.",S(STR_MHZ),volt_mv,S(STR_MILLIVOLTS));
        if (confirm_reboot(S(STR_RAM_OC_928), msg))
            do_reboot();
    } else {
        show_info("ERROR",S(STR_PATCH_FAILED_RESTORE));
        SDL_Delay(1500);
        snprintf(cmd,sizeof(cmd),"echo ark | sudo -S cp '%s' '%s' 2>/dev/null",bak,dtb);
        system(cmd);
    }
}

/* ── Read-only scrollable list (same rounded style as menus, no cursor) ───── */
#define TEXT_LINES_MAX 64
#define TEXT_LINE_LEN 128
static void screen_text(const char *title, char lines[][TEXT_LINE_LEN], int n_lines) {
    int scroll = 0;
    const int PAD = 24, TOP = 62, IH = 40, GAP = 5;
    const int BOTTOM = H - 30;
    int visible = (BOTTOM - TOP) / IH;
    if (visible < 1) visible = 1;
    if (scroll > n_lines - visible) scroll = n_lines - visible;
    if (scroll < 0) scroll = 0;

    while (running) {
        Keys k = poll_keys();
        if (k.b || k.sel) return;
        if (k.up)   { if (scroll > 0) scroll--; }
        if (k.down) { if (scroll < n_lines - visible) scroll++; }

        draw_bg();
        draw_header(title, NULL);
        for (int i = scroll; i < n_lines && i < scroll + visible; i++) {
            int iy = TOP + (i - scroll) * IH;
            rounded(PAD, iy, W - 2*PAD, IH - GAP, 8, 16, 18, 34);
            txt(fnt_sm, lines[i], PAD + 16, iy + 11, 200, 210, 240);
        }

        /* scroll indicator */
        if (n_lines > visible) {
            int bar_h = (visible * (BOTTOM - TOP)) / n_lines;
            if (bar_h < 20) bar_h = 20;
            int track_h = BOTTOM - TOP;
            int bar_y = TOP + (scroll * (track_h - bar_h)) / (n_lines - visible);
            setcol(40, 44, 80);
            fillrect(W - 10, TOP, 4, track_h);
            setcol(100, 140, 255);
            fillrect(W - 10, bar_y, 4, bar_h);
        }

        char foot[128];
        snprintf(foot,sizeof(foot),"[DPAD] %s  [B] %s",S(STR_NAVIGATE),S(STR_BACK));
        draw_footer(foot);
        SDL_RenderPresent(ren);
        SDL_Delay(16);
    }
}

/* ── Read active OPP voltages from /proc/device-tree ─────────────────────── */
static int kernel_scan_opp(const char *opp_base, const char *bin_prop,
                            OPPEntry entries[], int max) {
    char base_path[256];
    snprintf(base_path, sizeof(base_path), "/proc/device-tree%s", opp_base);
    DIR *d = opendir(base_path);
    if (!d) return 0;

    int n = 0;
    struct dirent *de;
    while ((de = readdir(d)) && n < max) {
        if (strncmp(de->d_name, "opp-", 4) != 0 && strncmp(de->d_name, "opp@", 4) != 0)
            continue;
        long long freq = atoll(de->d_name + 4);
        if (freq == 0) continue;

        char path[512];
        snprintf(path, sizeof(path), "%s/%s/%s", base_path, de->d_name, bin_prop);
        int fd = open(path, O_RDONLY);
        if (fd < 0) {
            snprintf(path, sizeof(path), "%s/%s/opp-microvolt", base_path, de->d_name);
            fd = open(path, O_RDONLY);
        }
        if (fd < 0) continue;

        unsigned char buf[16];
        int len = read(fd, buf, sizeof(buf));
        close(fd);
        if (len < 4) continue;

        int uv = (buf[0] << 24) | (buf[1] << 16) | (buf[2] << 8) | buf[3];
        entries[n].freq_hz = freq;
        entries[n].volt_uv = uv;
        n++;
    }
    closedir(d);
    return n;
}

static int opp_find_freq(OPPEntry entries[], int n, long long freq_hz) {
    for (int i = 0; i < n; i++)
        if (entries[i].freq_hz == freq_hz) return i;
    return -1;
}

/* ── OPP diagnostic: DTB on disk vs kernel active ─────────────────────────── */
static void screen_dtb_diag(const char *dtb, const char *opp_base,
                             const char *bin_prop) {
    show_info(S(STR_DIAG_OPP), S(STR_READING_OPP));
    OPPEntry dtb_opp[MAX_OPP]; int n_dtb = 0;
    OPPEntry ker_opp[MAX_OPP]; int n_ker = 0;
    if (opp_base[0]) {
        n_dtb = dtb_scan_opp(dtb, opp_base, bin_prop, dtb_opp, MAX_OPP);
        n_ker = kernel_scan_opp(opp_base, bin_prop, ker_opp, MAX_OPP);
    }

    int scroll = 0;
    const int PAD = 12;
    const int TOP = 58;
    const int BOTTOM = H - 70;
    const int ROW_H = 28;
    const int HEADER_H = 32;
    int visible = (BOTTOM - TOP - HEADER_H) / ROW_H;
    if (visible < 1) visible = 1;

    int c1x = PAD + 22;
    int c2x = PAD + 180;
    int c3rx = W - PAD - 22;
    int line_x1 = PAD + 8;
    int line_x2 = W - PAD - 8;

    while (running) {
        Keys k = poll_keys();
        if (k.b || k.sel) return;
        if (k.up) { if (scroll > 0) scroll--; }
        if (k.down) { if (scroll < n_dtb - visible) scroll++; }

        draw_bg();
        draw_header(S(STR_DIAG_OPP_TITLE), NULL);

        if (n_dtb == 0) {
            txt(fnt_med, S(STR_OPP_NOT_FOUND), PAD, 120, 255, 180, 80);
        } else {
            int table_h = BOTTOM - TOP;
            rounded(PAD, TOP, W - 2*PAD, table_h, 8, 16, 18, 34);

            int hy = TOP + 8;
            txt(fnt_sm, S(STR_FREQUENCY), c1x, hy, 100, 160, 255);
            txt(fnt_sm, S(STR_DIAG_DTB_COL), c2x, hy, 100, 160, 255);
            txtr(fnt_sm, S(STR_DIAG_KERNEL_COL), c3rx, hy, 100, 160, 255);

            setcol(40, 44, 80);
            SDL_RenderDrawLine(ren, line_x1, hy + 20, line_x2, hy + 20);

            for (int i = scroll; i < n_dtb && i < scroll + visible; i++) {
                int ry = TOP + HEADER_H + 6 + (i - scroll) * ROW_H;
                int mhz = (int)(dtb_opp[i].freq_hz / 1000000LL);
                char mhz_str[32]; snprintf(mhz_str, sizeof(mhz_str), "%d %s", mhz, S(STR_MHZ));

                char dtb_mv[16]; fmt_mv(dtb_opp[i].volt_uv, dtb_mv, sizeof(dtb_mv));
                char dtb_str[32]; snprintf(dtb_str, sizeof(dtb_str), "%s %s", dtb_mv, S(STR_MILLIVOLTS));

                int ki = opp_find_freq(ker_opp, n_ker, dtb_opp[i].freq_hz);
                char ker_str[32] = {0};
                int same = 0;
                if (ki >= 0) {
                    char ker_mv[16]; fmt_mv(ker_opp[ki].volt_uv, ker_mv, sizeof(ker_mv));
                    snprintf(ker_str, sizeof(ker_str), "%s %s", ker_mv, S(STR_MILLIVOLTS));
                    same = (ker_opp[ki].volt_uv == dtb_opp[i].volt_uv);
                } else {
                    strncpy(ker_str, S(STR_DIAG_NO_ACTIVE), sizeof(ker_str)-1);
                }

                Uint8 rr = same ? 220 : 255;
                Uint8 gg = same ? 225 : 210;
                Uint8 bb = same ? 240 : 140;

                txt(fnt_med, mhz_str, c1x, ry, rr, gg, bb);
                txt(fnt_med, dtb_str, c2x, ry, rr, gg, bb);
                txtr(fnt_med, ker_str, c3rx, ry, rr, gg, bb);

                if (i < scroll + visible - 1 && i < n_dtb - 1) {
                    setcol(26, 28, 46);
                    SDL_RenderDrawLine(ren, line_x1 + 10, ry + ROW_H - 4,
                                       line_x2 - 10, ry + ROW_H - 4);
                }
            }

            if (n_dtb > visible) {
                int track_top = TOP + HEADER_H;
                int track_h = table_h - HEADER_H;
                int bar_h = (visible * track_h) / n_dtb;
                if (bar_h < 16) bar_h = 16;
                int bar_y = track_top + (scroll * (track_h - bar_h)) / (n_dtb - visible);
                setcol(30, 34, 60);
                fillrect(W - 10, track_top, 4, track_h);
                setcol(90, 130, 255);
                fillrect(W - 10, bar_y, 4, bar_h);
            }
        }

        /* Explanatory note below the table */
        if (n_dtb > 0) {
            txt(fnt_sm, S(STR_DIAG_OPP_EXPL1), PAD, H - 48, 130, 140, 170);
        }

        char foot[128];
        snprintf(foot,sizeof(foot),"[DPAD] %s  [B] %s",S(STR_NAVIGATE),S(STR_BACK));
        draw_footer(foot);
        SDL_RenderPresent(ren);
        SDL_Delay(16);
    }
}

/* ── DTB: Recuperacion emergencia ────────────────────────────────────────── */
static void screen_dtb_recovery(void) {
    char lines[10][TEXT_LINE_LEN];
    int nl = 0;
    snprintf(lines[nl++], TEXT_LINE_LEN, "%s", S(STR_RECOVERY_STEP1));
    snprintf(lines[nl++], TEXT_LINE_LEN, "%s", S(STR_RECOVERY_STEP2));
    snprintf(lines[nl++], TEXT_LINE_LEN, "%s", S(STR_RECOVERY_STEP3));
    snprintf(lines[nl++], TEXT_LINE_LEN, "%s", S(STR_RECOVERY_STEP4));
    snprintf(lines[nl++], TEXT_LINE_LEN, "%s", S(STR_RECOVERY_STEP5));
    snprintf(lines[nl++], TEXT_LINE_LEN, "%s", S(STR_RECOVERY_STEP6));
    snprintf(lines[nl++], TEXT_LINE_LEN, "%s", S(STR_RECOVERY_STEP7));
    snprintf(lines[nl++], TEXT_LINE_LEN, "%s", "");
    snprintf(lines[nl++], TEXT_LINE_LEN, "%s", S(STR_RECOVERY_SAFETY));
    snprintf(lines[nl++], TEXT_LINE_LEN, "%s", S(STR_RECOVERY_PANIC));
    screen_text(S(STR_RECOVERY), lines, nl);
}

/* ── DTB: Restaurar original ─────────────────────────────────────────────── */
static void screen_dtb_restore(const char *dtb) {
    char bak[280]; snprintf(bak, sizeof(bak), "%s.bak", dtb);
    if (access(bak, F_OK) != 0) {
        show_info(S(STR_RESTORE_ORIGINAL), S(STR_NO_BACKUP));
        SDL_Delay(2000); return;
    }
    if (!confirm_restore()) return;
    char cmd[600];
    snprintf(cmd, sizeof(cmd), "echo ark | sudo -S cp '%s' '%s' 2>/dev/null", bak, dtb);
    show_info(S(STR_RESTORE_ORIGINAL), S(STR_RESTORE_ORIGINAL_SUMMARY));
    if (system(cmd) == 0) {
        system("echo ark | sudo -S sync 2>/dev/null");
        system("echo ark | sudo -S systemctl disable r36-dtb-safety.service 2>/dev/null");
        if (confirm_reboot(S(STR_RESTORED), S(STR_DTB_ORIGINAL_RESTORED)))
            do_reboot();
    } else {
        show_info("ERROR", S(STR_RESTORE_FAILED)); SDL_Delay(2000);
    }
}

/* ── Benchmark helpers ───────────────────────────────────────────────────── */
#define CPU_BENCH_BIN  "/usr/local/bin/r36_cpubench"
#define UI_SCORES_FILE "/home/ark/.r36_tuner_ui_scores.log"

static int check_cpu_bench(void) {
    return access(CPU_BENCH_BIN, X_OK) == 0;
}

typedef struct {
    long long score;
    int done;
    int gcc_ok;
    int temp_min;
    int temp_max;
    int temp_sum;
    int temp_count;
    char prev_gov[32];
    int cpu_mhz;
} BenchState;

static int cpu_bench_thread(void *data) {
    BenchState *st = (BenchState *)data;
    if (!check_cpu_bench()) {
        st->gcc_ok = 0;
        st->done = 1;
        return 0;
    }
    st->gcc_ok = 1;

    write_file(CPU_POLICY "/scaling_governor", "performance");

    char cmd[256];
    snprintf(cmd, sizeof(cmd), "%s 2>/dev/null", CPU_BENCH_BIN);
    FILE *f = popen(cmd, "r");
    if (!f) {
        st->done = 1;
        return 0;
    }

    char line[128];
    long long raw = 0;
    if (fgets(line, sizeof(line), f)) raw = atoll(line);
    pclose(f);
    st->score = raw / 1000000;
    st->done = 1;
    return 0;
}

static int screen_cpu_benchmark_result(BenchState *st) {
    int sel = 0; /* 0 = Run Again, 1 = Back */
    const int PAD = 24;
    const int BTN_H = 46;
    const int BTN_W = (W - 2*PAD - 24) / 2;

    int t_avg = st->temp_count > 0 ? st->temp_sum / st->temp_count : 0;
    char score_str[32];
    fmt_score(st->score, score_str, sizeof(score_str));

    /* Log result to history */
    FILE *hf = fopen(UI_SCORES_FILE, "a");
    if (hf) {
        time_t nowt = time(NULL);
        struct tm *tm = localtime(&nowt);
        char date[32];
        strftime(date, sizeof(date), "%Y-%m-%d %H:%M", tm);
        fprintf(hf, "%s | CPU | %s %s @ %d MHz | %dC -> %dC -> %dC peak\n",
                date, score_str, S(STR_BENCHMARK_CPU_MOPS),
                st->cpu_mhz, st->temp_min, t_avg, st->temp_max);
        fclose(hf);
    }

    while (running) {
        Keys k = poll_keys();
        if (k.left || k.right) sel ^= 1;
        if (k.a) return sel == 0;
        if (k.b || k.sel) return 0;

        draw_bg();
        draw_header(S(STR_BENCHMARK_CPU_TITLE), NULL);

        /* Central panel */
        int panel_w = W - 2*PAD;
        int panel_h = H - 48 - 26 - 40;
        int panel_x = PAD;
        int panel_y = 48 + 10;
        rounded(panel_x, panel_y, panel_w, panel_h, 12, 16, 18, 34);

        int cy = panel_y + 26;

        /* Result label */
        const char *res_lbl = S(STR_BENCHMARK_CPU_RESULT);
        txt(fnt_sm, res_lbl, panel_x + panel_w/2 - txtw(fnt_sm, res_lbl)/2, cy, 120, 130, 160);
        cy += 26;

        /* Big score */
        int score_w = txtw(fnt_big, score_str);
        txt(fnt_big, score_str, panel_x + panel_w/2 - score_w/2, cy, 100, 160, 255);
        cy += 50;

        /* Units + freq */
        char cpu_unit_str[64];
        snprintf(cpu_unit_str, sizeof(cpu_unit_str), "%s @ %d MHz", S(STR_BENCHMARK_CPU_MOPS), st->cpu_mhz);
        int unit_w = txtw(fnt_med, cpu_unit_str);
        txt(fnt_med, cpu_unit_str, panel_x + panel_w/2 - unit_w/2, cy, 150, 160, 190);
        cy += 48;

        /* Separator */
        setcol(40, 44, 80);
        SDL_RenderDrawLine(ren, panel_x + 30, cy, panel_x + panel_w - 30, cy);
        cy += 24;

        /* Temperature row */
        char tstr[32];
        const char *init_lbl = "Initial";
        const char *avg_lbl = "Average";
        const char *peak_lbl = "Peak";

        txt(fnt_sm, init_lbl, panel_x + 50, cy, 100, 110, 140);
        snprintf(tstr, sizeof(tstr), "%dC", st->temp_min);
        txt(fnt_med, tstr, panel_x + 50, cy + 16, 200, 210, 240);

        txt(fnt_sm, avg_lbl, panel_x + panel_w/2 - txtw(fnt_sm, avg_lbl)/2, cy, 100, 110, 140);
        snprintf(tstr, sizeof(tstr), "%dC", t_avg);
        txt(fnt_med, tstr, panel_x + panel_w/2 - txtw(fnt_med, tstr)/2, cy + 16, 200, 210, 240);

        txt(fnt_sm, peak_lbl, panel_x + panel_w - 50 - txtw(fnt_sm, peak_lbl), cy, 100, 110, 140);
        snprintf(tstr, sizeof(tstr), "%dC", st->temp_max);
        int peak_txtr = panel_x + panel_w - 50;
        txtr(fnt_med, tstr, peak_txtr, cy + 16, 255, 180, 80);

        cy += 62;

        /* Buttons */
        int btn_y = panel_y + panel_h - BTN_H - 18;
        if (btn_y < cy + 10) btn_y = cy + 10;
        int txty = btn_y + BTN_H/2 - 10;
        const char *btn1 = S(STR_BENCHMARK_CPU_RUN_AGAIN);
        const char *btn2 = S(STR_BENCHMARK_CPU_BACK);
        int w1 = txtw(fnt_med, btn1);
        int w2 = txtw(fnt_med, btn2);

        if (sel == 0) {
            rounded(PAD, btn_y, BTN_W, BTN_H, 8, 30, 60, 180);
            txt(fnt_med, btn1, PAD + BTN_W/2 - w1/2, txty, 255, 255, 255);
        } else {
            rounded(PAD, btn_y, BTN_W, BTN_H, 8, 16, 18, 34);
            txt(fnt_med, btn1, PAD + BTN_W/2 - w1/2, txty, 130, 135, 160);
        }

        int bx2 = PAD + BTN_W + 24;
        if (sel == 1) {
            rounded(bx2, btn_y, BTN_W, BTN_H, 8, 30, 60, 180);
            txt(fnt_med, btn2, bx2 + BTN_W/2 - w2/2, txty, 255, 255, 255);
        } else {
            rounded(bx2, btn_y, BTN_W, BTN_H, 8, 16, 18, 34);
            txt(fnt_med, btn2, bx2 + BTN_W/2 - w2/2, txty, 130, 135, 160);
        }

        draw_footer("[DPAD] Select  [A] Confirm  [B] Back");
        SDL_RenderPresent(ren);
        SDL_Delay(16);
    }
    return 0;
}

static void screen_cpu_benchmark(void) {
    int run_again = 1;
    while (run_again && running) {
        BenchState st = {0};
        st.temp_min = 999;
        st.gcc_ok = 1;
        snprintf(st.prev_gov, sizeof(st.prev_gov), "%s", read_file(CPU_POLICY "/scaling_governor"));
        st.cpu_mhz = read_int(CPU_POLICY "/scaling_max_freq") / 1000;

        SDL_Thread *thread = SDL_CreateThread(cpu_bench_thread, "cpubench", &st);
        if (!thread) {
            show_info(S(STR_BENCHMARK_CPU_TITLE), "Thread error");
            SDL_Delay(2000);
            return;
        }

        Uint32 start = SDL_GetTicks();
        Uint32 last_sample = 0;
        int cancelled = 0;

        while (running && !st.done) {
            Keys k = poll_keys();
            if (k.b) {
                cancelled = 1;
                system("pkill -x r36_cpubench_sdl 2>/dev/null");
                break;
            }

            Uint32 now = SDL_GetTicks();
            if (now - last_sample >= 2000) {
                int t = read_int(CPU_TEMP);
                if (t > 0) {
                    t /= 1000;
                    if (st.temp_count == 0 || t < st.temp_min) st.temp_min = t;
                    if (t > st.temp_max) st.temp_max = t;
                    st.temp_sum += t;
                    st.temp_count++;
                }
                last_sample = now;
            }

            draw_bg();
            draw_header(S(STR_BENCHMARK_CPU_TITLE), NULL);

            int elapsed = (now - start) / 1000;
            if (elapsed > 30) elapsed = 30;
            txt(fnt_med, S(STR_BENCHMARK_CPU_RUNNING), 40, 120, 200, 210, 240);

            char msg[128];
            snprintf(msg, sizeof(msg), "%s: %ds / 30s", S(STR_BENCHMARK_CPU_PLEASE_WAIT), elapsed);
            txt(fnt_sm, msg, 40, 160, 150, 160, 190);

            int pw = (W - 80) * elapsed / 30;
            if (pw > W - 80) pw = W - 80;
            rounded(40, 200, W - 80, 24, 6, 16, 18, 34);
            rounded(42, 202, pw, 20, 4, 60, 100, 220);

            if (st.temp_count > 0) {
                int cur_t = read_int(CPU_TEMP) / 1000;
                snprintf(msg, sizeof(msg), "%s: %dC (peak %dC)",
                         S(STR_BENCHMARK_CPU_TEMP), cur_t, st.temp_max);
                txt(fnt_sm, msg, 40, 250, 150, 160, 190);
            }

            draw_footer(S(STR_B_BACK));
            SDL_RenderPresent(ren);
            SDL_Delay(16);
        }

        SDL_WaitThread(thread, NULL);

        if (st.prev_gov[0]) {
            write_file(CPU_POLICY "/scaling_governor", st.prev_gov);
        }

        if (cancelled) return;

        if (!st.gcc_ok) {
            show_info(S(STR_BENCHMARK_CPU_TITLE), S(STR_BENCHMARK_CPU_GCC_MISSING));
            SDL_Delay(3000);
            return;
        }

        run_again = screen_cpu_benchmark_result(&st);
    }
}

/* ── DTB: Menu principal ─────────────────────────────────────────────────── */
static void screen_dtb_main(void) {
    char dtb[256]; strncpy(dtb, dtb_find(), 255);
    if (!dtb[0]) {
        show_info(S(STR_DTB_TUNING), S(STR_DTB_NOT_FOUND));
        SDL_Delay(2000); return;
    }
    char bin_prop[64]; strncpy(bin_prop, opp_bin_detect(), 63);
    const char *cpu_cands[] = {
        "/opp-table-0","/cpu0-opp-table","/cpu-opp-table",
        "/opp-table0","/opp-table",NULL
    };
    char opp_base[64];
    strncpy(opp_base, dtb_find_opp_node(dtb, cpu_cands), 63);

    int sel = 0;
    while (running) {
        char r[16];
        popen_into("grep -q 1608000 /sys/devices/system/cpu/cpu0/cpufreq/"
                   "scaling_available_frequencies 2>/dev/null && echo yes", r, sizeof(r));
        int cpu_oc = strcmp(r,"yes")==0;
        popen_into("grep -q 600000000 /sys/class/devfreq/ff400000.gpu/"
                   "available_frequencies 2>/dev/null && echo yes", r, sizeof(r));
        int gpu_oc = strcmp(r,"yes")==0;
        char bak[280]; snprintf(bak,sizeof(bak),"%s.bak",dtb);
        int bak_ok = (access(bak,F_OK)==0);
        int bin_ok = strcmp(bin_prop,"opp-microvolt")!=0;
        char bin_tag[16];
        if (bin_ok) {
            const char *l = strrchr(bin_prop, '-');
            snprintf(bin_tag, sizeof(bin_tag), "%s", (l && l[1]=='L') ? l+1 : "OK");
        } else {
            snprintf(bin_tag, sizeof(bin_tag), "%s", S(STR_BIN_MISSING));
        }

        LItem items[8]; int n=0;
        strncpy(items[n].label,S(STR_CPU_UNDERVOLT),63);
        strncpy(items[n].desc,S(STR_PATCH_OPP_DTDB),95);
        strncpy(items[n].tag,bin_tag,31); n++;

        strncpy(items[n].label,S(STR_CPU_FINETUNE),63);
        strncpy(items[n].desc,S(STR_CPU_FINETUNE_DESC),95);
        strncpy(items[n].tag,bin_tag,31); n++;

        strncpy(items[n].label,S(STR_CPU_OC_1608),63);
        strncpy(items[n].desc,S(STR_UNLOCK_1608_DTB),95);
        strncpy(items[n].tag,cpu_oc?S(STR_ACTIVE):"",31); n++;

        strncpy(items[n].label,S(STR_GPU_OC_600),63);
        strncpy(items[n].desc,S(STR_ADD_OPP_600),95);
        strncpy(items[n].tag,gpu_oc?S(STR_ACTIVE):"",31); n++;

        strncpy(items[n].label,S(STR_RAM_OC_928),63);
        strncpy(items[n].desc,S(STR_ADD_OPP_928),95);
        items[n].tag[0]=0; n++;

        strncpy(items[n].label,S(STR_DIAG_OPP),63);
        strncpy(items[n].desc,S(STR_VIEW_OPP_TABLE),95);
        items[n].tag[0]=0; n++;

        strncpy(items[n].label,S(STR_RECOVERY),63);
        strncpy(items[n].desc,S(STR_IF_DEVICE_WONT_BOOT),95);
        items[n].tag[0]=0; n++;

        strncpy(items[n].label,S(STR_RESTORE_ORIGINAL),63);
        strncpy(items[n].desc,bak_ok?S(STR_REVERT_BACKUP):S(STR_NO_BACKUP),95);
        items[n].tag[0]=0; n++;

        int chosen = submenu(S(STR_DTB_TUNING),S(STR_DTB_TUNING_DESC),items,n,&sel,NULL,1);
        if (chosen < 0) return;

        switch(chosen) {
            case 0:
                if (!opp_base[0]) {
                    show_info(S(STR_CPU_UNDERVOLT),S(STR_TABLE_NOT_FOUND));
                    SDL_Delay(2000);
                } else {
                    screen_dtb_cpu_uv(dtb, opp_base, bin_prop);
                }
                break;
            case 1:
                if (!opp_base[0]) {
                    show_info(S(STR_CPU_FINETUNE),S(STR_TABLE_NOT_FOUND));
                    SDL_Delay(2000);
                } else {
                    screen_dtb_cpu_finetune(dtb, opp_base, bin_prop);
                }
                break;
            case 2:
                if (!opp_base[0]) {
                    show_info(S(STR_CPU_OC_1608),S(STR_TABLE_NOT_FOUND));
                    SDL_Delay(2000);
                } else {
                    screen_dtb_cpu_oc(dtb, opp_base, bin_prop);
                }
                break;
            case 3: screen_dtb_gpu_oc(dtb, bin_prop); break;
            case 4: screen_dtb_ram_oc(dtb, bin_prop); break;
            case 5: screen_dtb_diag(dtb, opp_base, bin_prop); break;
            case 6: screen_dtb_recovery(); break;
            case 7: screen_dtb_restore(dtb); break;
        }
    }
}

/* ═══════════════════════════════════════════════════════════════════════════ */

/* ── Monitor screen ─────────────────────────────────────────────────────── */
static void screen_monitor(void){
    Uint32 last=0;
    char cpu_buf[64],gpu_buf[64],ram_buf[64];
    int cpu_mhz=0,cpu_max=0,gpu_cur=0,gpu_max=0,ram_cur=0;
    float temp=0;
    char gov[32]={0};
    char p[256];

    while(running){
        Keys k=poll_keys();
        if(k.b||k.sel||k.start) return;

        Uint32 now=SDL_GetTicks();
        if(now-last>500||last==0){
            last=now;
            snprintf(p,sizeof(p),"%s/scaling_governor",CPU_POLICY);
            strncpy(gov,read_file(p),sizeof(gov)-1); gov[sizeof(gov)-1]=0;
            snprintf(p,sizeof(p),"%s/scaling_cur_freq",CPU_POLICY);
            cpu_mhz=read_int(p)/1000;
            snprintf(p,sizeof(p),"%s/scaling_max_freq",CPU_POLICY);
            cpu_max=read_int(p)/1000;
            temp=read_int(CPU_TEMP)/1000.0f;
            snprintf(p,sizeof(p),"%s/cur_freq",GPU_DEVFREQ);
            gpu_cur=read_int(p)/1000000;
            snprintf(p,sizeof(p),"%s/max_freq",GPU_DEVFREQ);
            gpu_max=read_int(p)/1000000;
            snprintf(p,sizeof(p),"%s/cur_freq",DMC_DEVFREQ);
            ram_cur=read_int(p)/1000000;

            snprintf(cpu_buf,sizeof(cpu_buf),S(STR_CPU_FMT),
                     cpu_mhz,cpu_max,temp,gov);
            snprintf(gpu_buf,sizeof(gpu_buf),S(STR_GPU_FMT),
                     gpu_cur,gpu_max);
            snprintf(ram_buf,sizeof(ram_buf),S(STR_RAM_FMT),ram_cur);
        }

        draw_bg();
        draw_header(S(STR_MONITOR),S(STR_REALTIME));

        int PAD=28, y=62, ROW=56;

        rounded(PAD,y,W-2*PAD,ROW-4,8,16,18,34);
        txt(fnt_med,S(STR_CPU),PAD+16,y+6,100,160,255);
        txt(fnt_sm,cpu_buf,PAD+90,y+18,200,210,240);
        y+=ROW;

        rounded(PAD,y,W-2*PAD,ROW-4,8,16,18,34);
        txt(fnt_med,S(STR_GPU),PAD+16,y+6,80,220,160);
        txt(fnt_sm,gpu_buf,PAD+90,y+18,200,210,240);
        y+=ROW;

        rounded(PAD,y,W-2*PAD,ROW-4,8,16,18,34);
        txt(fnt_med,S(STR_RAM),PAD+16,y+6,180,100,255);
        txt(fnt_sm,ram_buf,PAD+90,y+18,200,210,240);
        y+=ROW;

        rounded(PAD,y,W-2*PAD,ROW-4,8,16,18,34);
        txt(fnt_med,S(STR_TEMP),PAD+16,y+6,255,140,60);
        int bx=PAD+90, bw=W-2*PAD-130, by=y+16, bh=16;
        setcol(28,30,50); fillrect(bx,by,bw,bh);
        float pct=temp/80.0f; if(pct>1.0f)pct=1.0f;
        int fill=(int)(bw*pct);
        Uint8 tr=(Uint8)(55+pct*200),tg=(Uint8)((1.0f-pct)*180);
        setcol(tr,tg,40); fillrect(bx,by,fill,bh);
        char tbuf[32]; snprintf(tbuf,sizeof(tbuf),S(STR_TEMP_FMT),temp);
        txt(fnt_sm,tbuf,bx+bw+10,by,255,200,120);
        y+=ROW;

        char foot[64];
        snprintf(foot,sizeof(foot),"[B] %s",S(STR_BACK));
        draw_footer(foot);
        SDL_RenderPresent(ren);
        SDL_Delay(16);
    }
}

/* ── Language selector ──────────────────────────────────────────────────── */
static void screen_language(void){
    LItem items[2]; int n=0, sel=0;
    strncpy(items[n].label, S(STR_ENGLISH), 63);
    items[n].desc[0]=0;
    strncpy(items[n].tag, current_lang==LANG_EN?S(STR_ACTIVE):"", 31); n++;
    strncpy(items[n].label, S(STR_SPANISH), 63);
    items[n].desc[0]=0;
    strncpy(items[n].tag, current_lang==LANG_ES?S(STR_ACTIVE):"", 31); n++;

    char lang_hint[128];
    snprintf(lang_hint,sizeof(lang_hint),"%s  %s",S(STR_DPAD_NAVIGATE),S(STR_A_SELECT_B_BACK));
    int chosen = submenu(S(STR_LANGUAGE), S(STR_LANGUAGE_DESC), items, n, &sel, lang_hint, 1);
    if (chosen >= 0 && chosen != current_lang) {
        current_lang = chosen;
        save_language();
    }
}

/* ── RAM benchmark ───────────────────────────────────────────────────────── */
#define RAM_BENCH_BIN "/usr/local/bin/r36_rambench"

typedef struct {
    long long write_mbps;
    long long copy_mbps;
    int done;
    int gcc_ok;
    int temp_min;
    int temp_max;
    int temp_sum;
    int temp_count;
    int ram_mhz;
} RamBenchState;

static int check_ram_bench(void) {
    return access(RAM_BENCH_BIN, X_OK) == 0;
}

static int ram_bench_thread(void *data) {
    RamBenchState *st = (RamBenchState *)data;
    if (!check_ram_bench()) {
        st->gcc_ok = 0;
        st->done = 1;
        return 0;
    }
    st->gcc_ok = 1;

    char cmd[256];
    snprintf(cmd, sizeof(cmd), "%s 2>/dev/null", RAM_BENCH_BIN);
    FILE *f = popen(cmd, "r");
    if (!f) {
        st->done = 1;
        return 0;
    }

    char line[128];
    if (fgets(line, sizeof(line), f)) st->write_mbps = atoll(line);
    if (fgets(line, sizeof(line), f)) st->copy_mbps = atoll(line);
    pclose(f);
    st->done = 1;
    return 0;
}

static int screen_ram_benchmark_result(RamBenchState *st) {
    int sel = 0;
    const int PAD = 24;
    const int BTN_H = 46;
    const int BTN_W = (W - 2*PAD - 24) / 2;

    int t_avg = st->temp_count > 0 ? st->temp_sum / st->temp_count : 0;
    char write_str[32], copy_str[32];
    fmt_score(st->write_mbps, write_str, sizeof(write_str));
    fmt_score(st->copy_mbps, copy_str, sizeof(copy_str));

    /* Log result to history */
    FILE *hf = fopen(UI_SCORES_FILE, "a");
    if (hf) {
        time_t nowt = time(NULL);
        struct tm *tm = localtime(&nowt);
        char date[32];
        strftime(date, sizeof(date), "%Y-%m-%d %H:%M", tm);
        fprintf(hf, "%s | RAM | Write %s %s | Copy %s %s @ %d MHz DDR | %dC -> %dC -> %dC peak\n",
                date, write_str, S(STR_BENCHMARK_RAM_MBPS),
                copy_str, S(STR_BENCHMARK_RAM_MBPS),
                st->ram_mhz, st->temp_min, t_avg, st->temp_max);
        fclose(hf);
    }

    while (running) {
        Keys k = poll_keys();
        if (k.left || k.right) sel ^= 1;
        if (k.a) return sel == 0;
        if (k.b || k.sel) return 0;

        draw_bg();
        draw_header(S(STR_BENCHMARK_RAM_TITLE), NULL);

        int panel_w = W - 2*PAD;
        int panel_h = H - 48 - 26 - 40;
        int panel_x = PAD;
        int panel_y = 48 + 10;
        rounded(panel_x, panel_y, panel_w, panel_h, 12, 16, 18, 34);

        int cy = panel_y + 30;

        /* Write */
        const char *w_lbl = S(STR_BENCHMARK_RAM_WRITE);
        txt(fnt_sm, w_lbl, panel_x + panel_w/2 - txtw(fnt_sm, w_lbl)/2, cy, 100, 110, 140);
        cy += 24;
        int w_w = txtw(fnt_big, write_str);
        txt(fnt_big, write_str, panel_x + panel_w/2 - w_w/2, cy, 100, 160, 255);
        cy += 48;
        int unit_w = txtw(fnt_med, S(STR_BENCHMARK_RAM_MBPS));
        txt(fnt_med, S(STR_BENCHMARK_RAM_MBPS), panel_x + panel_w/2 - unit_w/2, cy, 150, 160, 190);
        cy += 44;

        /* Separator */
        setcol(40, 44, 80);
        SDL_RenderDrawLine(ren, panel_x + 30, cy, panel_x + panel_w - 30, cy);
        cy += 24;

        /* Copy */
        const char *c_lbl = S(STR_BENCHMARK_RAM_COPY);
        txt(fnt_sm, c_lbl, panel_x + panel_w/2 - txtw(fnt_sm, c_lbl)/2, cy, 100, 110, 140);
        cy += 24;
        int c_w = txtw(fnt_big, copy_str);
        txt(fnt_big, copy_str, panel_x + panel_w/2 - c_w/2, cy, 100, 160, 255);
        cy += 48;
        txt(fnt_med, S(STR_BENCHMARK_RAM_MBPS), panel_x + panel_w/2 - unit_w/2, cy, 150, 160, 190);
        cy += 28;

        /* DDR freq */
        char ram_freq_str[32];
        snprintf(ram_freq_str, sizeof(ram_freq_str), "@ %d MHz DDR", st->ram_mhz);
        int rf_w = txtw(fnt_sm, ram_freq_str);
        txt(fnt_sm, ram_freq_str, panel_x + panel_w/2 - rf_w/2, cy, 120, 130, 160);
        cy += 22;

        /* Temperature */
        char tstr[64];
        snprintf(tstr, sizeof(tstr), "%s: %dC -> %dC -> %dC peak",
                 S(STR_BENCHMARK_CPU_TEMP), st->temp_min, t_avg, st->temp_max);
        txt(fnt_sm, tstr, panel_x + panel_w/2 - txtw(fnt_sm, tstr)/2, cy, 150, 160, 190);
        cy += 20;

        /* Buttons — never overlap text */
        int btn_y = panel_y + panel_h - BTN_H - 18;
        if (btn_y < cy + 4) btn_y = cy + 4;
        int txty = btn_y + BTN_H/2 - 10;
        const char *btn1 = S(STR_BENCHMARK_CPU_RUN_AGAIN);
        const char *btn2 = S(STR_BENCHMARK_CPU_BACK);
        int w1 = txtw(fnt_med, btn1);
        int w2 = txtw(fnt_med, btn2);

        if (sel == 0) {
            rounded(PAD, btn_y, BTN_W, BTN_H, 8, 30, 60, 180);
            txt(fnt_med, btn1, PAD + BTN_W/2 - w1/2, txty, 255, 255, 255);
        } else {
            rounded(PAD, btn_y, BTN_W, BTN_H, 8, 16, 18, 34);
            txt(fnt_med, btn1, PAD + BTN_W/2 - w1/2, txty, 130, 135, 160);
        }

        int bx2 = PAD + BTN_W + 24;
        if (sel == 1) {
            rounded(bx2, btn_y, BTN_W, BTN_H, 8, 30, 60, 180);
            txt(fnt_med, btn2, bx2 + BTN_W/2 - w2/2, txty, 255, 255, 255);
        } else {
            rounded(bx2, btn_y, BTN_W, BTN_H, 8, 16, 18, 34);
            txt(fnt_med, btn2, bx2 + BTN_W/2 - w2/2, txty, 130, 135, 160);
        }

        draw_footer("[DPAD] Select  [A] Confirm  [B] Back");
        SDL_RenderPresent(ren);
        SDL_Delay(16);
    }
    return 0;
}

static void screen_ram_benchmark(void) {
    int run_again = 1;
    while (run_again && running) {
        RamBenchState st = {0};
        st.temp_min = 999;
        st.gcc_ok = 1;
        st.ram_mhz = read_int(DMC_DEVFREQ "/max_freq") / 1000000;

        SDL_Thread *thread = SDL_CreateThread(ram_bench_thread, "rambench", &st);
        if (!thread) {
            show_info(S(STR_BENCHMARK_RAM_TITLE), "Thread error");
            SDL_Delay(2000);
            return;
        }

        Uint32 start = SDL_GetTicks();
        Uint32 last_sample = 0;
        int cancelled = 0;

        while (running && !st.done) {
            Keys k = poll_keys();
            if (k.b) {
                cancelled = 1;
                system("pkill -x r36_rambench_sdl 2>/dev/null");
                break;
            }

            Uint32 now = SDL_GetTicks();
            if (now - last_sample >= 2000) {
                int t = read_int(CPU_TEMP);
                if (t > 0) {
                    t /= 1000;
                    if (st.temp_count == 0 || t < st.temp_min) st.temp_min = t;
                    if (t > st.temp_max) st.temp_max = t;
                    st.temp_sum += t;
                    st.temp_count++;
                }
                last_sample = now;
            }

            draw_bg();
            draw_header(S(STR_BENCHMARK_RAM_TITLE), NULL);

            int elapsed = (now - start) / 1000;
            if (elapsed > 30) elapsed = 30;
            txt(fnt_med, S(STR_BENCHMARK_RAM_RUNNING), 40, 120, 200, 210, 240);

            char msg[128];
            snprintf(msg, sizeof(msg), "%s: %ds / 30s", S(STR_BENCHMARK_CPU_PLEASE_WAIT), elapsed);
            txt(fnt_sm, msg, 40, 160, 150, 160, 190);

            int pw = (W - 80) * elapsed / 30;
            if (pw > W - 80) pw = W - 80;
            rounded(40, 200, W - 80, 24, 6, 16, 18, 34);
            rounded(42, 202, pw, 20, 4, 60, 100, 220);

            if (st.temp_count > 0) {
                int cur_t = read_int(CPU_TEMP) / 1000;
                snprintf(msg, sizeof(msg), "%s: %dC (peak %dC)",
                         S(STR_BENCHMARK_CPU_TEMP), cur_t, st.temp_max);
                txt(fnt_sm, msg, 40, 250, 150, 160, 190);
            }

            draw_footer(S(STR_B_BACK));
            SDL_RenderPresent(ren);
            SDL_Delay(16);
        }

        SDL_WaitThread(thread, NULL);

        if (cancelled) return;

        if (!st.gcc_ok) {
            show_info(S(STR_BENCHMARK_RAM_TITLE), S(STR_BENCHMARK_RAM_GCC_MISSING));
            SDL_Delay(3000);
            return;
        }

        run_again = screen_ram_benchmark_result(&st);
    }
}

/* ── Benchmark history ───────────────────────────────────────────────────── */
typedef struct {
    char date[32];
    char type[8];
    char detail[96];
    char temp[64];
} HistoryEntry;

static void history_trim(char *s) {
    size_t n = strlen(s);
    while (n > 0 && (s[n-1] == ' ' || s[n-1] == '\t')) s[--n] = 0;
    char *p = s;
    while (*p == ' ' || *p == '\t') p++;
    if (p != s) memmove(s, p, strlen(p) + 1);
}

static int history_load(HistoryEntry entries[], int max) {
    FILE *f = fopen(UI_SCORES_FILE, "r");
    if (!f) return 0;
    int n = 0;
    char line[256];
    while (fgets(line, sizeof(line), f) && n < max) {
        size_t len = strlen(line);
        while (len > 0 && (line[len-1] == '\n' || line[len-1] == '\r')) line[--len] = 0;
        if (len == 0) continue;

        /* Expected format: "date | type | detail | temp" */
        char *p1 = strchr(line, '|');
        if (!p1) continue;
        *p1 = 0;
        strncpy(entries[n].date, line, sizeof(entries[n].date) - 1);
        entries[n].date[sizeof(entries[n].date) - 1] = 0;

        char *p2 = strchr(p1 + 1, '|');
        if (!p2) continue;
        *p2 = 0;
        strncpy(entries[n].type, p1 + 1, sizeof(entries[n].type) - 1);
        entries[n].type[sizeof(entries[n].type) - 1] = 0;

        char *p3 = strrchr(p2 + 1, '|');
        if (!p3) continue;
        *p3 = 0;
        strncpy(entries[n].detail, p2 + 1, sizeof(entries[n].detail) - 1);
        entries[n].detail[sizeof(entries[n].detail) - 1] = 0;

        strncpy(entries[n].temp, p3 + 1, sizeof(entries[n].temp) - 1);
        entries[n].temp[sizeof(entries[n].temp) - 1] = 0;

        history_trim(entries[n].date);
        history_trim(entries[n].type);
        history_trim(entries[n].detail);
        history_trim(entries[n].temp);
        n++;
    }
    fclose(f);
    return n;
}

static void screen_benchmark_history(void) {
    HistoryEntry entries[64];
    int n = history_load(entries, 64);
    if (n == 0) {
        show_info(S(STR_BENCHMARK_HISTORY_TITLE), S(STR_BENCHMARK_HISTORY_EMPTY));
        SDL_Delay(2000);
        return;
    }

    int scroll = 0;
    const int PAD = 16;
    const int TOP = 58;
    const int BOTTOM = H - 34;
    const int GAP = 8;
    const int visible = 4;
    const int ROW_H = (BOTTOM - TOP - (visible - 1) * GAP) / visible;

    while (running) {
        Keys k = poll_keys();
        if (k.b) return;
        if (k.sel) {
            if (confirm_screen(S(STR_BENCHMARK_HISTORY_TITLE),
                               S(STR_BENCHMARK_HISTORY_CLEAR),
                               NULL, NULL, NULL, NULL, 0, NULL, 0, NULL, 0,
                               S(STR_APPLY), S(STR_CANCEL))) {
                remove(UI_SCORES_FILE);
                n = 0;
            }
        }
        if (k.up && scroll > 0) scroll--;
        if (k.down && scroll < n - visible) scroll++;

        draw_bg();
        draw_header(S(STR_BENCHMARK_HISTORY_TITLE), NULL);

        for (int i = scroll; i < n && i < scroll + visible; i++) {
            int y = TOP + (i - scroll) * (ROW_H + GAP);
            int is_cpu = (strcmp(entries[i].type, "CPU") == 0);
            int is_gpu = (strcmp(entries[i].type, "GPU") == 0);

            rounded(PAD, y, W - 2*PAD, ROW_H, 10, 18, 20, 38);

            /* Type badge — CPU: blue, RAM: purple, GPU: orange */
            const char *type_lbl = is_cpu ? S(STR_BENCHMARK_CPU)
                                 : is_gpu ? S(STR_BENCHMARK_GPU)
                                 :          S(STR_BENCHMARK_RAM);
            Uint8 br = is_cpu ? 40  : is_gpu ? 180 : 100;
            Uint8 bg = is_cpu ? 90  : is_gpu ? 100 : 60;
            Uint8 bb = is_cpu ? 220 : is_gpu ? 30  : 180;
            int badge_w = txtw(fnt_sm, type_lbl) + 18;
            rounded(PAD + 10, y + 8, badge_w, 18, 4, br, bg, bb);
            txt(fnt_sm, type_lbl, PAD + 19, y + 9, 255, 255, 255);

            /* Date */
            txt(fnt_sm, entries[i].date, PAD + 14 + badge_w + 8, y + 9, 120, 130, 160);

            /* Detail */
            txt(fnt_med, entries[i].detail, PAD + 18, y + 31, 210, 220, 240);

            /* Temperature */
            txt(fnt_sm, entries[i].temp, PAD + 18, y + 51, 150, 160, 190);
        }

        /* Scroll indicator */
        if (n > visible) {
            int track_h = BOTTOM - TOP;
            int bar_h = (visible * track_h) / n;
            if (bar_h < 16) bar_h = 16;
            int bar_y = TOP + (scroll * (track_h - bar_h)) / (n - visible);
            setcol(30, 34, 60);
            fillrect(W - 10, TOP, 4, track_h);
            setcol(90, 130, 255);
            fillrect(W - 10, bar_y, 4, bar_h);
        }

        if (n == 0) {
            show_info(S(STR_BENCHMARK_HISTORY_TITLE), S(STR_BENCHMARK_HISTORY_EMPTY));
            return;
        }

        char foot[80];
        snprintf(foot, sizeof(foot), "[DPAD] %s  [Select] %s  [B] %s",
                 S(STR_NAVIGATE), S(STR_BENCHMARK_HISTORY_CLEAR), S(STR_BACK));
        draw_footer(foot);
        SDL_RenderPresent(ren);
        SDL_Delay(16);
    }
}

static void screen_gpu_benchmark(void);

/* ── Benchmark submenu ───────────────────────────────────────────────────── */
static void screen_benchmark(void) {
    LItem items[4];
    int n = 0;
    snprintf(items[n].label, sizeof(items[n].label), "%s", S(STR_BENCHMARK_CPU));
    snprintf(items[n].desc, sizeof(items[n].desc), "Integer ALU — 30s");
    items[n++].tag[0] = 0;
    snprintf(items[n].label, sizeof(items[n].label), "%s", S(STR_BENCHMARK_RAM));
    snprintf(items[n].desc, sizeof(items[n].desc), "128 MB memset/memcpy");
    items[n++].tag[0] = 0;
    snprintf(items[n].label, sizeof(items[n].label), "%s", S(STR_BENCHMARK_GPU));
    snprintf(items[n].desc, sizeof(items[n].desc), "glmark2 terrain");
    items[n++].tag[0] = 0;
    snprintf(items[n].label, sizeof(items[n].label), "%s", S(STR_BENCHMARK_HISTORY));
    snprintf(items[n].desc, sizeof(items[n].desc), "Saved scores");
    items[n++].tag[0] = 0;

    int sel = 0;
    while (running) {
        int r = submenu("R36 TUNER NEXT", S(STR_BENCHMARK), items, n, &sel,
                        "[A] Select  [B] Back", 1);
        if (r < 0) break;
        switch (r) {
            case 0: screen_cpu_benchmark(); break;
            case 1: screen_ram_benchmark(); break;
            case 2: screen_gpu_benchmark(); break;
            case 3: screen_benchmark_history(); break;
            default:
                show_info(S(STR_BENCHMARK), S(STR_BENCHMARK_NOT_IMPLEMENTED));
                SDL_Delay(1500);
                break;
        }
    }
}

/* ── GPU benchmark ───────────────────────────────────────────────────────── */
#define GPU_BENCH_RESULT "/tmp/r36_gpu_bench_result.txt"
#define GPU_BENCH_LOG    "/tmp/r36_gpu_bench_out.txt"

static int install_glmark2_legacy(void) {
    show_info(S(STR_BENCHMARK_GPU_TITLE), S(STR_BENCHMARK_GPU_INSTALLING));
    SDL_RenderPresent(ren);
    SDL_Delay(200);

    const char *legacy_bin = "/usr/local/bin/glmark2-es2-drm-legacy";
    const char *data_dir = "/usr/local/share/glmark2data";

    /* The deploy script uploads the legacy binary; ensure it is executable. */
    if (access(legacy_bin, X_OK) != 0) {
        show_info(S(STR_BENCHMARK_GPU_TITLE), "Legacy binary missing");
        SDL_Delay(3000);
        return 0;
    }

    /* Prepare shader data. glmark2 2023.01 shaders use macros undefined in
       the 2021.02 legacy binary; patch them to real precision qualifiers. */
    if (access("/usr/local/share/glmark2data/shaders", F_OK) != 0) {
        char cmd[512];
        snprintf(cmd, sizeof(cmd),
            "if [ -d /usr/share/glmark2/shaders ]; then "
            "  mkdir -p '%s/shaders' && "
            "  ln -sf /usr/share/glmark2/models '%s/models' && "
            "  ln -sf /usr/share/glmark2/textures '%s/textures' && "
            "  cp /usr/share/glmark2/shaders/* '%s/shaders/' && "
            "  sed -i 's/MEDIUMP_OR_DEFAULT/mediump/g; s/HIGHP_OR_DEFAULT/highp/g' '%s/shaders/'*; "
            "else exit 1; fi",
            data_dir, data_dir, data_dir, data_dir, data_dir);
        int rc = system(cmd);
        if (rc != 0) {
            show_info(S(STR_BENCHMARK_GPU_TITLE), "glmark2 data missing.\nRedeploy: python tools/deployment/deploy_ui.py");
            SDL_Delay(3000);
            return 0;
        }
    }
    return 1;
}

static void check_gpu_bench_pending(void);

static void create_gpu_runner(void) {
    FILE *f = fopen("/tmp/r36_gpu_bench_runner.sh", "w");
    if (!f) return;
    fprintf(f,
        "#!/bin/bash\n"
        "export SDL_VIDEO_EGL_DRIVER=/lib/aarch64-linux-gnu/libEGL.so\n"
        "export XDG_RUNTIME_DIR=/run/user/1000\n"
        "export SDL_GAMECONTROLLERCONFIG_FILE=/opt/inttools/gamecontrollerdb.txt\n"
        "GL_LOG=%s\n"
        "TEMP_LOG=/tmp/r36_gpu_bench_temps.txt\n"
        "GPU_MHZ_LOG=/tmp/r36_gpu_bench_gpu_mhz.txt\n"
        "RESULT=%s\n"
        "THERMAL=/sys/class/thermal/thermal_zone0/temp\n"
        "GPU_FREQ=/sys/class/devfreq/ff400000.gpu/cur_freq\n"
        "get_temp() { awk '{printf \"%%.0f\\n\",$1/1000}' \"$THERMAL\" 2>/dev/null; }\n"
        "get_gpu_mhz() { awk '{printf \"%%d\\n\",$1/1000000}' \"$GPU_FREQ\" 2>/dev/null; }\n"
        "# Pin GPU to configured max_freq so devfreq governor cannot scale down.\n"
        "GPU_DEV=/sys/class/devfreq/ff400000.gpu\n"
        "GPU_MAX=$(cat \"$GPU_DEV/max_freq\" 2>/dev/null || echo 0)\n"
        "GPU_MIN_ORIG=$(cat \"$GPU_DEV/min_freq\" 2>/dev/null || echo 0)\n"
        "[ \"$GPU_MAX\" -gt 0 ] && echo \"$GPU_MAX\" > \"$GPU_DEV/min_freq\" 2>/dev/null || true\n"
        "TEMP_START=$(get_temp)\n"
        "GPU_START=$(get_gpu_mhz)\n"
        "rm -f \"$GL_LOG\" \"$TEMP_LOG\" \"$RESULT\" \"$GPU_MHZ_LOG\"\n"
        "( while true; do\n"
        "    get_temp >> \"$TEMP_LOG\"\n"
        "    get_gpu_mhz >> \"$GPU_MHZ_LOG\"\n"
        "    sleep 2\n"
        "done ) &\n"
        "SAMPLER_PID=$!\n"
        "# Run off-screen — no DRM master needed, ES keeps running.\n"
        "glmark2-es2-drm --off-screen --data-path /usr/share/glmark2 "
        "--size 320x240 "
        "-b build:duration=15 -b texture:duration=15 "
        "-b shading:duration=15 -b terrain:duration=15 > \"$GL_LOG\" 2>&1\n"
        "kill \"$SAMPLER_PID\" 2>/dev/null\n"
        "# Restore GPU min_freq.\n"
        "echo \"$GPU_MIN_ORIG\" > \"$GPU_DEV/min_freq\" 2>/dev/null || true\n"
        "TEMP_MAX=$(sort -n \"$TEMP_LOG\" 2>/dev/null | tail -1)\n"
        "TEMP_AVG=$(awk '{s+=$1;n++} END{if(n>0)printf \"%%.0f\",s/n}' \"$TEMP_LOG\" 2>/dev/null)\n"
        "GPU_MHZ=$(sort -n \"$GPU_MHZ_LOG\" 2>/dev/null | tail -1)\n"
        "[ -z \"$TEMP_MAX\" ] && TEMP_MAX=$(get_temp)\n"
        "[ -z \"$TEMP_AVG\" ] && TEMP_AVG=$TEMP_MAX\n"
        "[ -z \"$GPU_MHZ\" ] && GPU_MHZ=${GPU_START:-0}\n"
        "SCORE=$(grep 'glmark2 Score:' \"$GL_LOG\" | awk '{print $NF}')\n"
        "if [ -n \"$SCORE\" ]; then\n"
        "  echo \"OK $SCORE $GPU_MHZ $TEMP_START $TEMP_AVG $TEMP_MAX\" > \"$RESULT\"\n"
        "  echo \"$(date '+%%Y-%%m-%%d %%H:%%M') | GPU | $SCORE pts @ ${GPU_MHZ}MHz | ${TEMP_START}C -> ${TEMP_AVG}C -> ${TEMP_MAX}C peak\" >> %s\n"
        "else\n"
        "  ERR=$(grep -i 'error\\|failed\\|warning' \"$GL_LOG\" 2>/dev/null | tail -3 | tr '\\n' ' ')\n"
        "  echo \"FAIL $ERR\" > \"$RESULT\"\n"
        "fi\n"
        "chown ark \"$RESULT\" 2>/dev/null\n"
        "chown ark %s 2>/dev/null\n"
        "rm -f \"$TEMP_LOG\" \"$GPU_MHZ_LOG\"\n"
        "systemctl is-active --quiet emulationstation || systemctl start emulationstation 2>/dev/null\n",
        GPU_BENCH_LOG, GPU_BENCH_RESULT, UI_SCORES_FILE, UI_SCORES_FILE);
    fclose(f);
    chmod("/tmp/r36_gpu_bench_runner.sh", 0755);
}

static void screen_gpu_benchmark(void) {
    if (access("/usr/bin/glmark2-es2-drm", X_OK) != 0) {
        show_info(S(STR_BENCHMARK_GPU_TITLE),
                  "glmark2 not found.\nInstall: apt install glmark2-es2-drm");
        SDL_Delay(4000);
        return;
    }

    const char *infos[] = {S(STR_BENCHMARK_GPU_BLACK_SCREEN)};
    if (!confirm_screen(S(STR_BENCHMARK_GPU_TITLE),
                        S(STR_BENCHMARK_GPU_RUNNING),
                        NULL, NULL, NULL,
                        NULL, 0, NULL, 0, infos, 1,
                        S(STR_APPLY), S(STR_CANCEL))) {
        return;
    }

    create_gpu_runner();

    /* Write service file to /tmp (avoids heredoc quoting issues), then install
       and start it via sudo.  Off-screen mode: no DRM master needed, tuner_ui
       stays alive and ES keeps running. */
    FILE *sf = fopen("/tmp/r36-gpu-bench.service", "w");
    if (sf) {
        fprintf(sf,
            "[Unit]\nDescription=R36 GPU Benchmark\n"
            "[Service]\nType=simple\nUser=root\n"
            "StandardInput=null\nStandardOutput=journal\nStandardError=journal\n"
            "ExecStart=/tmp/r36_gpu_bench_runner.sh\n"
            "ExecStopPost=rm -f /etc/systemd/system/r36-gpu-bench.service\n");
        fclose(sf);
    }
    system("echo ark | sudo -S bash -c '"
           "cp /tmp/r36-gpu-bench.service /etc/systemd/system/ && "
           "systemctl daemon-reload && systemctl start r36-gpu-bench'");

    /* Poll the GL log for completed scenes, show live progress. */
    static const char *SCENE_NAMES[4] = {"build","texture","shading","terrain"};
    static const char SPINNER[4] = {'|','/','-','\\'};
    Uint32 bench_start = SDL_GetTicks();
    int spin_i = 0;

    while (running) {
        /* Done? show result and return. */
        if (access(GPU_BENCH_RESULT, F_OK) == 0) {
            check_gpu_bench_pending();
            return;
        }

        /* Count completed scenes from log (each done scene has "FPS:" on its line). */
        int done = 0;
        FILE *gl = fopen(GPU_BENCH_LOG, "r");
        if (gl) {
            char buf[256];
            while (fgets(buf, sizeof(buf), gl))
                if (strstr(buf, "FPS:")) done++;
            fclose(gl);
        }

        int elapsed_s = (int)((SDL_GetTicks() - bench_start) / 1000);
        draw_bg();
        draw_header(S(STR_BENCHMARK_GPU_TITLE), NULL);

        char status[64];
        if (done < 4)
            snprintf(status, sizeof(status), "%c  Scene %d/4: %s",
                     SPINNER[spin_i & 3], done + 1, SCENE_NAMES[done]);
        else
            snprintf(status, sizeof(status), "%c  Scoring...", SPINNER[spin_i & 3]);
        txt(fnt_med, status, 40, 100, 200, 210, 240);

        /* Progress bar */
        int bar_x = 40, bar_y = 148, bar_w = W - 80, bar_h = 8;
        SDL_SetRenderDrawColor(ren, 45, 50, 65, 255);
        SDL_Rect bg_bar = {bar_x, bar_y, bar_w, bar_h};
        SDL_RenderFillRect(ren, &bg_bar);
        int fill = bar_w * done / 4;
        if (fill > 0) {
            SDL_SetRenderDrawColor(ren, 80, 160, 220, 255);
            SDL_Rect fg_bar = {bar_x, bar_y, fill, bar_h};
            SDL_RenderFillRect(ren, &fg_bar);
        }

        char time_str[32];
        snprintf(time_str, sizeof(time_str), "%d:%02d", elapsed_s / 60, elapsed_s % 60);
        txt(fnt_sm, time_str, 40, 168, 120, 130, 155);

        draw_footer("[B] Cancel");
        SDL_RenderPresent(ren);

        Keys k = poll_keys();
        if (k.b) {
            system("pkill -x glmark2-es2-drm 2>/dev/null");
            system("echo ark | sudo -S systemctl stop r36-gpu-bench 2>/dev/null");
            break;
        }
        spin_i++;
        SDL_Delay(500);
    }
}

static void check_gpu_bench_pending(void) {
    FILE *f = fopen(GPU_BENCH_RESULT, "r");
    if (!f) return;
    char line[512];
    if (!fgets(line, sizeof(line), f)) { fclose(f); return; }
    fclose(f);
    remove(GPU_BENCH_RESULT);

    const int PAD   = 24;
    const int BTN_H = 46;
    const int BTN_W = (W - 2*PAD - 24) / 2;

    char score[32] = {0}, gpu_mhz[16] = {0};
    char t_start[16] = {0}, t_avg[16] = {0}, t_max[16] = {0};
    int ok = (sscanf(line, "OK %31s %15s %15s %15s %15s",
                     score, gpu_mhz, t_start, t_avg, t_max) == 5);

    char err_msg[256] = {0};
    if (!ok) {
        char *p = line;
        if (strncmp(p, "FAIL ", 5) == 0) p += 5;
        snprintf(err_msg, sizeof(err_msg), "%s", p);
        /* strip trailing newline */
        char *nl = strchr(err_msg, '\n');
        if (nl) *nl = '\0';
    }

    char mhz_str[32];
    snprintf(mhz_str, sizeof(mhz_str), "%s MHz", gpu_mhz);

    SDL_FlushEvents(SDL_FIRSTEVENT, SDL_LASTEVENT);
    Uint32 shown_at = SDL_GetTicks();

    while (running) {
        Keys k = poll_keys();
        if ((k.a || k.b || k.sel) && SDL_GetTicks() - shown_at >= 2000) break;

        draw_bg();
        draw_header(S(STR_BENCHMARK_GPU_RESULT), NULL);

        int panel_w = W - 2*PAD;
        int panel_h = H - 48 - 26 - 40;
        int panel_x = PAD;
        int panel_y = 48 + 10;
        rounded(panel_x, panel_y, panel_w, panel_h, 12, 16, 18, 34);

        int cy = panel_y + 22;

        if (ok) {
            /* "Result" label */
            const char *res_lbl = S(STR_BENCHMARK_CPU_RESULT);
            txt(fnt_sm, res_lbl, panel_x + panel_w/2 - txtw(fnt_sm, res_lbl)/2,
                cy, 120, 130, 160);
            cy += 24;

            /* Big score */
            int sw = txtw(fnt_big, score);
            txt(fnt_big, score, panel_x + panel_w/2 - sw/2, cy, 100, 160, 255);
            cy += 50;

            /* "pts" unit */
            const char *pts = S(STR_BENCHMARK_GPU_PTS);
            txt(fnt_med, pts, panel_x + panel_w/2 - txtw(fnt_med, pts)/2,
                cy, 150, 160, 190);
            cy += 36;

            /* GPU MHz */
            txt(fnt_sm, "GPU", panel_x + panel_w/2 - txtw(fnt_sm, "GPU")/2,
                cy, 100, 110, 140);
            cy += 20;
            txt(fnt_med, mhz_str, panel_x + panel_w/2 - txtw(fnt_med, mhz_str)/2,
                cy, 200, 210, 240);
            cy += 36;

            /* Separator */
            setcol(40, 44, 80);
            SDL_RenderDrawLine(ren, panel_x + 30, cy, panel_x + panel_w - 30, cy);
            cy += 20;

            /* Temperature 3-column: Initial / Average / Peak */
            const char *init_lbl = "Initial";
            const char *avg_lbl  = "Average";
            const char *peak_lbl = "Peak";
            char ts[16];

            txt(fnt_sm, init_lbl, panel_x + 50, cy, 100, 110, 140);
            txt(fnt_sm, avg_lbl,
                panel_x + panel_w/2 - txtw(fnt_sm, avg_lbl)/2, cy, 100, 110, 140);
            txt(fnt_sm, peak_lbl,
                panel_x + panel_w - 50 - txtw(fnt_sm, peak_lbl), cy, 100, 110, 140);
            cy += 18;

            snprintf(ts, sizeof(ts), "%sC", t_start);
            txt(fnt_med, ts, panel_x + 50, cy, 200, 210, 240);

            snprintf(ts, sizeof(ts), "%sC", t_avg);
            txt(fnt_med, ts, panel_x + panel_w/2 - txtw(fnt_med, ts)/2,
                cy, 200, 210, 240);

            snprintf(ts, sizeof(ts), "%sC", t_max);
            txtr(fnt_med, ts, panel_x + panel_w - 50, cy, 255, 180, 80);
        } else {
            /* Failure */
            cy += 20;
            const char *fail = S(STR_BENCHMARK_GPU_FAILED);
            txt(fnt_med, fail, panel_x + panel_w/2 - txtw(fnt_med, fail)/2,
                cy, 255, 140, 140);
            cy += 44;
            /* word-wrap is not available; truncate to panel width */
            txt(fnt_sm, err_msg, panel_x + 20, cy, 180, 185, 200);
        }

        /* Close button */
        int btn_y = panel_y + panel_h - BTN_H - 18;
        int txty  = btn_y + BTN_H/2 - 10;
        const char *btn_lbl = S(STR_BENCHMARK_CPU_BACK);
        int bx = panel_x + panel_w/2 - BTN_W/2;
        rounded(bx, btn_y, BTN_W, BTN_H, 8, 30, 60, 180);
        txt(fnt_med, btn_lbl, bx + BTN_W/2 - txtw(fnt_med, btn_lbl)/2, txty,
            255, 255, 255);

        char foot[64];
        snprintf(foot, sizeof(foot), "[A/B] %s", S(STR_BENCHMARK_CPU_BACK));
        draw_footer(foot);
        SDL_RenderPresent(ren);
        SDL_Delay(16);
    }
}

/* ── Main menu ──────────────────────────────────────────────────────────── */
static void screen_main(void){
    int sel=0;
    int PAD=24;
    int N=7;
    /* Fit 7 items vertically in the area between header (48) and footer (26). */
    int IH = (H - 48 - 26 - 10) / N; /* 10 px total spacing */
    if (IH > 58) IH = 58;
    if (IH < 48) IH = 48;
    int LY = 48 + ((H - 48 - 26) - (N * IH)) / 2;
    if (LY < 56) LY = 56;
    char gov_desc[80],cpu_desc[80],gpu_desc[80],mon_desc[80];
    Uint32 last_refresh=0;

    while(running){
        Uint32 now=SDL_GetTicks();
        if(now-last_refresh>1000||last_refresh==0){
            last_refresh=now;
            refresh_state();
            snprintf(gov_desc,sizeof(gov_desc),"%s: %s",S(STR_ACTUAL),cur_gov);
            snprintf(cpu_desc,sizeof(cpu_desc),"%s: %d %s",S(STR_ACTUAL),cur_cpu_max_mhz,S(STR_MHZ));
            snprintf(gpu_desc,sizeof(gpu_desc),"%s: %d %s",S(STR_ACTUAL),cur_gpu_mhz,S(STR_MHZ));
            snprintf(mon_desc,sizeof(mon_desc),S(STR_MONITOR_DESC),
                     cur_cpu_temp,cur_gpu_mhz,cur_ram_mhz);
        }

        const char *labels[7]={S(STR_CPU_GOVERNOR),S(STR_CPU_MAX_FREQ),S(STR_GPU_MAX_FREQ),
                                S(STR_DTB_TUNING),S(STR_BENCHMARK),S(STR_MONITOR),S(STR_LANGUAGE)};
        char lang_desc[64];
        snprintf(lang_desc,sizeof(lang_desc),"%s / %s",S(STR_ENGLISH),S(STR_SPANISH));
        const char *descs[7]={gov_desc,cpu_desc,gpu_desc,
                               S(STR_DTB_TUNING_DESC),
                               S(STR_BENCHMARK_DESC),
                               mon_desc,
                               lang_desc};

        Keys k=poll_keys();
        if(k.up)   sel=(sel-1+N)%N;
        if(k.down) sel=(sel+1)%N;
        if(k.b||k.sel){running=0;break;}
        if(k.a){
            switch(sel){
                case 0: screen_governor(); break;
                case 1: screen_cpu_freq(); break;
                case 2: screen_gpu_freq(); break;
                case 3: screen_dtb_main(); break;
                case 4: screen_benchmark(); break;
                case 5: screen_monitor(); break;
                case 6: screen_language(); break;
            }
            last_refresh=0;
        }

        draw_bg();
        draw_header("R36 TUNER NEXT", os_subtitle);

        for(int i=0;i<N;i++){
            int iy=LY+i*IH;
            if(i==sel){
                rounded(PAD,iy,W-2*PAD,IH-5,8,30,60,180);
                setcol(80,140,255); fillrect(PAD,iy,4,IH-5);
                txt(fnt_med,labels[i],PAD+18,iy+8, 255,255,255);
                txt(fnt_sm, descs[i], PAD+18,iy+34,160,190,255);
            }else{
                rounded(PAD,iy,W-2*PAD,IH-5,8,16,18,34);
                txt(fnt_med,labels[i],PAD+18,iy+8, 180,185,210);
                txt(fnt_sm, descs[i], PAD+18,iy+34, 80, 85,110);
            }
        }

        char foot[128];
        snprintf(foot,sizeof(foot),"[DPAD] %s  [A] %s  [B] %s",
                 S(STR_NAVIGATE),S(STR_SELECT),S(STR_EXIT));
        draw_footer(foot);
        SDL_RenderPresent(ren);
        SDL_Delay(16);
    }
}

/* ── App init / destroy ─────────────────────────────────────────────────── */
static void app_destroy(void){
    if(gc)     {SDL_GameControllerClose(gc);gc=NULL;}
    if(fnt_sm) {TTF_CloseFont(fnt_sm);fnt_sm=NULL;}
    if(fnt_med){TTF_CloseFont(fnt_med);fnt_med=NULL;}
    if(fnt_big){TTF_CloseFont(fnt_big);fnt_big=NULL;}
    if(ren)    {
        SDL_SetRenderDrawColor(ren,0,0,0,255);
        SDL_RenderClear(ren);
        SDL_RenderPresent(ren);
        SDL_DestroyRenderer(ren);ren=NULL;
    }
    if(win)    {SDL_DestroyWindow(win);win=NULL;}
    TTF_Quit(); SDL_Quit();
}

static void app_init(void){
    SDL_Init(SDL_INIT_VIDEO|SDL_INIT_GAMECONTROLLER);
    TTF_Init();
    fnt_big=TTF_OpenFont(FONT_BOLD,22);
    fnt_med=TTF_OpenFont(FONT_BOLD,17);
    fnt_sm =TTF_OpenFont(FONT_NORM,13);
    win=SDL_CreateWindow("R36 Tuner Next",
        SDL_WINDOWPOS_CENTERED,SDL_WINDOWPOS_CENTERED,
        640,480,SDL_WINDOW_SHOWN|SDL_WINDOW_FULLSCREEN_DESKTOP);
    ren=SDL_CreateRenderer(win,-1,
        SDL_RENDERER_ACCELERATED|SDL_RENDERER_PRESENTVSYNC);
    SDL_GetWindowSize(win,&W,&H);
}

int main(void){
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    /* clear tty1 before SDL2 takes over — hides ES command echo */
    int _tty = open("/dev/tty1", O_WRONLY);
    if (_tty >= 0) { write(_tty, "\033c", 2); close(_tty); }

    app_init();
    load_language();
    detect_os();
    for(int i=0;i<SDL_NumJoysticks();i++)
        if(SDL_IsGameController(i)){gc=SDL_GameControllerOpen(i);break;}
    refresh_state();
    /* Warm-up: on DRM/KMS the first page-flip initialises the display buffer.
       Without this, the very first SDL_RenderPresent shows a black frame. */
    SDL_SetRenderDrawColor(ren, 10, 12, 20, 255);
    SDL_RenderClear(ren);
    SDL_RenderPresent(ren);
    SDL_Delay(50);
    check_gpu_bench_pending();
    screen_main();
    app_destroy();
    return 0;
}
