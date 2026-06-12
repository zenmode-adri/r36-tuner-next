/*
 * r36_overlay.c — FPS/temp/freq overlay for SDL2/GLES2 on R36S
 * Hook: SDL_GL_SwapWindow via LD_PRELOAD
 * Compile (WSL):
 *   aarch64-linux-gnu-gcc -shared -fPIC -O2 -o libr36overlay.so r36_overlay.c -ldl -lGLESv2
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <unistd.h>
#include <GLES2/gl2.h>

typedef void SDL_Window;
typedef void (*swap_fn_t)(SDL_Window *);

/* ------------------------------------------------------------------ */
/* 8×8 bitmap font, public domain (derived from linux/lib/fonts)      */
/* ------------------------------------------------------------------ */
static const uint8_t font8x8[96][8] = {
 {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, /* 20 sp */
 {0x18,0x3C,0x3C,0x18,0x18,0x00,0x18,0x00}, /* 21 !  */
 {0x36,0x36,0x00,0x00,0x00,0x00,0x00,0x00}, /* 22 "  */
 {0x36,0x36,0x7F,0x36,0x7F,0x36,0x36,0x00}, /* 23 #  */
 {0x0C,0x3E,0x03,0x1E,0x30,0x1F,0x0C,0x00}, /* 24 $  */
 {0x00,0x63,0x33,0x18,0x0C,0x66,0x63,0x00}, /* 25 %  */
 {0x1C,0x36,0x1C,0x6E,0x3B,0x33,0x6E,0x00}, /* 26 &  */
 {0x06,0x06,0x03,0x00,0x00,0x00,0x00,0x00}, /* 27 '  */
 {0x18,0x0C,0x06,0x06,0x06,0x0C,0x18,0x00}, /* 28 (  */
 {0x06,0x0C,0x18,0x18,0x18,0x0C,0x06,0x00}, /* 29 )  */
 {0x00,0x66,0x3C,0xFF,0x3C,0x66,0x00,0x00}, /* 2A *  */
 {0x00,0x0C,0x0C,0x3F,0x0C,0x0C,0x00,0x00}, /* 2B +  */
 {0x00,0x00,0x00,0x00,0x00,0x0C,0x0C,0x06}, /* 2C ,  */
 {0x00,0x00,0x00,0x3F,0x00,0x00,0x00,0x00}, /* 2D -  */
 {0x00,0x00,0x00,0x00,0x00,0x0C,0x0C,0x00}, /* 2E .  */
 {0x60,0x30,0x18,0x0C,0x06,0x03,0x01,0x00}, /* 2F /  */
 {0x3E,0x63,0x73,0x7B,0x6F,0x67,0x3E,0x00}, /* 30 0  */
 {0x0C,0x0E,0x0C,0x0C,0x0C,0x0C,0x3F,0x00}, /* 31 1  */
 {0x1E,0x33,0x30,0x1C,0x06,0x33,0x3F,0x00}, /* 32 2  */
 {0x1E,0x33,0x30,0x1C,0x30,0x33,0x1E,0x00}, /* 33 3  */
 {0x38,0x3C,0x36,0x33,0x7F,0x30,0x78,0x00}, /* 34 4  */
 {0x3F,0x03,0x1F,0x30,0x30,0x33,0x1E,0x00}, /* 35 5  */
 {0x1C,0x06,0x03,0x1F,0x33,0x33,0x1E,0x00}, /* 36 6  */
 {0x3F,0x33,0x30,0x18,0x0C,0x0C,0x0C,0x00}, /* 37 7  */
 {0x1E,0x33,0x33,0x1E,0x33,0x33,0x1E,0x00}, /* 38 8  */
 {0x1E,0x33,0x33,0x3E,0x30,0x18,0x0E,0x00}, /* 39 9  */
 {0x00,0x0C,0x0C,0x00,0x00,0x0C,0x0C,0x00}, /* 3A :  */
 {0x00,0x0C,0x0C,0x00,0x00,0x0C,0x0C,0x06}, /* 3B ;  */
 {0x18,0x0C,0x06,0x03,0x06,0x0C,0x18,0x00}, /* 3C <  */
 {0x00,0x00,0x3F,0x00,0x00,0x3F,0x00,0x00}, /* 3D =  */
 {0x06,0x0C,0x18,0x30,0x18,0x0C,0x06,0x00}, /* 3E >  */
 {0x1E,0x33,0x30,0x18,0x0C,0x00,0x0C,0x00}, /* 3F ?  */
 {0x3E,0x63,0x7B,0x7B,0x7B,0x03,0x1E,0x00}, /* 40 @  */
 {0x0C,0x1E,0x33,0x33,0x3F,0x33,0x33,0x00}, /* 41 A  */
 {0x3F,0x66,0x66,0x3E,0x66,0x66,0x3F,0x00}, /* 42 B  */
 {0x3C,0x66,0x03,0x03,0x03,0x66,0x3C,0x00}, /* 43 C  */
 {0x1F,0x36,0x66,0x66,0x66,0x36,0x1F,0x00}, /* 44 D  */
 {0x7F,0x46,0x16,0x1E,0x16,0x46,0x7F,0x00}, /* 45 E  */
 {0x7F,0x46,0x16,0x1E,0x16,0x06,0x0F,0x00}, /* 46 F  */
 {0x3C,0x66,0x03,0x03,0x73,0x66,0x7C,0x00}, /* 47 G  */
 {0x33,0x33,0x33,0x3F,0x33,0x33,0x33,0x00}, /* 48 H  */
 {0x1E,0x0C,0x0C,0x0C,0x0C,0x0C,0x1E,0x00}, /* 49 I  */
 {0x78,0x30,0x30,0x30,0x33,0x33,0x1E,0x00}, /* 4A J  */
 {0x67,0x66,0x36,0x1E,0x36,0x66,0x67,0x00}, /* 4B K  */
 {0x0F,0x06,0x06,0x06,0x46,0x66,0x7F,0x00}, /* 4C L  */
 {0x63,0x77,0x7F,0x7F,0x6B,0x63,0x63,0x00}, /* 4D M  */
 {0x63,0x67,0x6F,0x7B,0x73,0x63,0x63,0x00}, /* 4E N  */
 {0x1C,0x36,0x63,0x63,0x63,0x36,0x1C,0x00}, /* 4F O  */
 {0x3F,0x66,0x66,0x3E,0x06,0x06,0x0F,0x00}, /* 50 P  */
 {0x1E,0x33,0x33,0x33,0x3B,0x1E,0x38,0x00}, /* 51 Q  */
 {0x3F,0x66,0x66,0x3E,0x36,0x66,0x67,0x00}, /* 52 R  */
 {0x1E,0x33,0x07,0x0E,0x38,0x33,0x1E,0x00}, /* 53 S  */
 {0x3F,0x2D,0x0C,0x0C,0x0C,0x0C,0x1E,0x00}, /* 54 T  */
 {0x33,0x33,0x33,0x33,0x33,0x33,0x3F,0x00}, /* 55 U  */
 {0x33,0x33,0x33,0x33,0x33,0x1E,0x0C,0x00}, /* 56 V  */
 {0x63,0x63,0x63,0x6B,0x7F,0x77,0x63,0x00}, /* 57 W  */
 {0x63,0x63,0x36,0x1C,0x1C,0x36,0x63,0x00}, /* 58 X  */
 {0x33,0x33,0x33,0x1E,0x0C,0x0C,0x1E,0x00}, /* 59 Y  */
 {0x7F,0x63,0x31,0x18,0x4C,0x66,0x7F,0x00}, /* 5A Z  */
 {0x1E,0x06,0x06,0x06,0x06,0x06,0x1E,0x00}, /* 5B [  */
 {0x03,0x06,0x0C,0x18,0x30,0x60,0x40,0x00}, /* 5C \  */
 {0x1E,0x18,0x18,0x18,0x18,0x18,0x1E,0x00}, /* 5D ]  */
 {0x08,0x1C,0x36,0x63,0x00,0x00,0x00,0x00}, /* 5E ^  */
 {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xFF}, /* 5F _  */
 {0x0C,0x0C,0x18,0x00,0x00,0x00,0x00,0x00}, /* 60 `  */
 {0x00,0x00,0x1E,0x30,0x3E,0x33,0x6E,0x00}, /* 61 a  */
 {0x07,0x06,0x06,0x3E,0x66,0x66,0x3B,0x00}, /* 62 b  */
 {0x00,0x00,0x1E,0x33,0x03,0x33,0x1E,0x00}, /* 63 c  */
 {0x38,0x30,0x30,0x3e,0x33,0x33,0x6E,0x00}, /* 64 d  */
 {0x00,0x00,0x1E,0x33,0x3f,0x03,0x1E,0x00}, /* 65 e  */
 {0x1C,0x36,0x06,0x0f,0x06,0x06,0x0F,0x00}, /* 66 f  */
 {0x00,0x00,0x6E,0x33,0x33,0x3E,0x30,0x1F}, /* 67 g  */
 {0x07,0x06,0x36,0x6E,0x66,0x66,0x67,0x00}, /* 68 h  */
 {0x0C,0x00,0x0E,0x0C,0x0C,0x0C,0x1E,0x00}, /* 69 i  */
 {0x30,0x00,0x30,0x30,0x30,0x33,0x33,0x1E}, /* 6A j  */
 {0x07,0x06,0x66,0x36,0x1E,0x36,0x67,0x00}, /* 6B k  */
 {0x0E,0x0C,0x0C,0x0C,0x0C,0x0C,0x1E,0x00}, /* 6C l  */
 {0x00,0x00,0x33,0x7F,0x7F,0x6B,0x63,0x00}, /* 6D m  */
 {0x00,0x00,0x1F,0x33,0x33,0x33,0x33,0x00}, /* 6E n  */
 {0x00,0x00,0x1E,0x33,0x33,0x33,0x1E,0x00}, /* 6F o  */
 {0x00,0x00,0x3B,0x66,0x66,0x3E,0x06,0x0F}, /* 70 p  */
 {0x00,0x00,0x6E,0x33,0x33,0x3E,0x30,0x78}, /* 71 q  */
 {0x00,0x00,0x3B,0x6E,0x66,0x06,0x0F,0x00}, /* 72 r  */
 {0x00,0x00,0x3E,0x03,0x1E,0x30,0x1F,0x00}, /* 73 s  */
 {0x08,0x0C,0x3E,0x0C,0x0C,0x2C,0x18,0x00}, /* 74 t  */
 {0x00,0x00,0x33,0x33,0x33,0x33,0x6E,0x00}, /* 75 u  */
 {0x00,0x00,0x33,0x33,0x33,0x1E,0x0C,0x00}, /* 76 v  */
 {0x00,0x00,0x63,0x6B,0x7F,0x7F,0x36,0x00}, /* 77 w  */
 {0x00,0x00,0x63,0x36,0x1C,0x36,0x63,0x00}, /* 78 x  */
 {0x00,0x00,0x33,0x33,0x33,0x3E,0x30,0x1F}, /* 79 y  */
 {0x00,0x00,0x3F,0x19,0x0C,0x26,0x3F,0x00}, /* 7A z  */
 {0x38,0x0C,0x0C,0x07,0x0C,0x0C,0x38,0x00}, /* 7B {  */
 {0x18,0x18,0x18,0x00,0x18,0x18,0x18,0x00}, /* 7C |  */
 {0x07,0x0C,0x0C,0x38,0x0C,0x0C,0x07,0x00}, /* 7D }  */
 {0x6E,0x3B,0x00,0x00,0x00,0x00,0x00,0x00}, /* 7E ~  */
 {0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF}, /* 7F DEL*/
};

/* ------------------------------------------------------------------ */
/* Debug log                                                           */
/* ------------------------------------------------------------------ */
#include <fcntl.h>
static int dbgfd  = -1;
static int statsfd = -1;
static int overlay_enabled = 1;
static void log_open(void) {
    if (dbgfd >= 0) return;
    dbgfd = open("/tmp/r36overlay.log", O_WRONLY|O_CREAT|O_APPEND, 0666);
}
static void stats_open(void) {
    if (statsfd >= 0) return;
    char path[64];
    snprintf(path, sizeof(path), "/tmp/r36_stats_%d.csv", (int)getpid());
    statsfd = open(path, O_WRONLY|O_CREAT|O_TRUNC, 0666);
    if (statsfd >= 0) {
        const char *hdr = "time_s,fps,cpu_temp_c,cpu_mhz,gpu_mhz,ram_mhz,ram_pct,vdd_arm_mv,vdd_logic_mv\n";
        write(statsfd, hdr, strlen(hdr));
    }
}
static void log_str(const char *s) {
    log_open();
    if (dbgfd >= 0) { int n=0; while(s[n]) n++; write(dbgfd,s,n); }
}
static void log_hex(const char *pfx, unsigned long v) {
    char buf[64]; int i=0;
    const char *hex="0123456789abcdef";
    for(const char *p=pfx;*p;p++) buf[i++]=*p;
    buf[i++]='0'; buf[i++]='x';
    for(int shift=60;shift>=0;shift-=4) buf[i++]=hex[(v>>shift)&0xf];
    buf[i++]='\n'; write(dbgfd>=0?dbgfd:2,buf,i);
}
#define LOG(s) log_str(s)

/* ------------------------------------------------------------------ */
/* GL function pointers (resolved lazily)                              */
/* ------------------------------------------------------------------ */
static void (*_glUseProgram)(GLuint)                                  = NULL;
static GLuint (*_glCreateShader)(GLenum)                              = NULL;
static void (*_glShaderSource)(GLuint,int,const char**,const int*)    = NULL;
static void (*_glCompileShader)(GLuint)                               = NULL;
static GLuint (*_glCreateProgram)(void)                               = NULL;
static void (*_glAttachShader)(GLuint,GLuint)                         = NULL;
static void (*_glLinkProgram)(GLuint)                                 = NULL;
static void (*_glGenTextures)(int,GLuint*)                            = NULL;
static void (*_glBindTexture)(GLenum,GLuint)                          = NULL;
static void (*_glTexImage2D)(GLenum,int,int,int,int,int,GLenum,GLenum,const void*) = NULL;
static void (*_glTexSubImage2D)(GLenum,int,int,int,int,int,GLenum,GLenum,const void*) = NULL;
static void (*_glTexParameteri)(GLenum,GLenum,int)                   = NULL;
static void (*_glGenBuffers)(int,GLuint*)                             = NULL;
static void (*_glBindBuffer)(GLenum,GLuint)                           = NULL;
static void (*_glBufferData)(GLenum,int,const void*,GLenum)           = NULL;
static GLint (*_glGetAttribLocation)(GLuint,const char*)              = NULL;
static GLint (*_glGetUniformLocation)(GLuint,const char*)             = NULL;
static void (*_glEnableVertexAttribArray)(GLuint)                     = NULL;
static void (*_glVertexAttribPointer)(GLuint,int,GLenum,unsigned char,int,const void*) = NULL;
static void (*_glDrawArrays)(GLenum,int,int)                          = NULL;
static void (*_glUniform1i)(GLint,int)                                = NULL;
static void (*_glEnable)(GLenum)                                      = NULL;
static void (*_glDisable)(GLenum)                                     = NULL;
static void (*_glBlendFunc)(GLenum,GLenum)                            = NULL;
static void (*_glGetIntegerv)(GLenum,int*)                            = NULL;
static void (*_glViewport)(int,int,int,int)                           = NULL;
static void (*_glActiveTexture)(GLenum)                               = NULL;
static void (*_glScissor)(int,int,int,int)                            = NULL;
static void (*_glPixelStorei)(GLenum,int)                             = NULL;
static unsigned char (*_glIsEnabled)(GLenum)                          = NULL;
static void (*_glDisableVertexAttribArray)(GLuint)                    = NULL;

/* Constants not in GLES2/gl2.h */
#ifndef GL_CURRENT_PROGRAM
#define GL_CURRENT_PROGRAM             0x8B8D
#endif

#define LOAD_GL(name) _##name = dlsym(gles, #name)

/* ------------------------------------------------------------------ */
/* Overlay dimensions and buffer                                       */
/* ------------------------------------------------------------------ */
#define OW 160   /* overlay pixel width  */
#define OH  80   /* overlay pixel height */

static uint8_t obuf[OW * OH * 4]; /* RGBA pixels */
static GLuint  otex  = 0;
static GLuint  oprog = 0;
static GLuint  ovbo  = 0;
static int     oinit = 0;
static int     ofail = 0;
static GLint   loc_uTex = -1;
static GLint   loc_aPos = -1;
static GLint   loc_aUV  = -1;
static int     tex_dirty = 0;
static uint64_t frame_serial = 0;

/* ------------------------------------------------------------------ */
/* Stats                                                               */
/* ------------------------------------------------------------------ */
static int     frame_count  = 0;
static double  current_fps  = 0.0;
static int     cpu_temp_c   = 0;
static int     cpu_mhz      = 0;
static int     gpu_mhz      = 0;
static int     ram_mhz      = 0;
static int     ram_pct      = 0;
static int     vdd_arm_mv   = 0;
static int     vdd_logic_mv = 0;
static struct timespec t0   = {0,0};

static int sysfs_int(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) return 0;
    int v = 0; fscanf(f, "%d", &v); fclose(f); return v;
}

static int read_mem_pct(void) {
    FILE *f = fopen("/proc/meminfo", "r");
    if (!f) return 0;
    long total = 0, available = 0;
    char line[128];
    while (fgets(line, sizeof(line), f)) {
        long v;
        if (sscanf(line, "MemTotal: %ld", &v) == 1) total = v;
        else if (sscanf(line, "MemAvailable: %ld", &v) == 1) available = v;
        if (total && available) break;
    }
    fclose(f);
    return total ? (int)((total - available) * 100L / total) : 0;
}

static void update_stats(void) {
    cpu_temp_c   = sysfs_int("/sys/class/thermal/thermal_zone0/temp") / 1000;
    cpu_mhz      = sysfs_int("/sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq") / 1000;
    gpu_mhz      = sysfs_int("/sys/class/devfreq/ff400000.gpu/cur_freq") / 1000000;
    ram_mhz      = sysfs_int("/sys/class/devfreq/dmc/cur_freq") / 1000000;
    ram_pct      = read_mem_pct();
    vdd_arm_mv   = sysfs_int("/sys/class/regulator/regulator.3/microvolts") / 1000;
    vdd_logic_mv = sysfs_int("/sys/class/regulator/regulator.2/microvolts") / 1000;
}

/* ------------------------------------------------------------------ */
/* Pixel drawing                                                       */
/* ------------------------------------------------------------------ */
static void put_pixel(int x, int y, uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
    if (x < 0 || x >= OW || y < 0 || y >= OH) return;
    uint8_t *p = obuf + (y * OW + x) * 4;
    p[0]=r; p[1]=g; p[2]=b; p[3]=a;
}

static void fill_rect(int x, int y, int w, int h,
                      uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
    for (int dy=0; dy<h; dy++)
        for (int dx=0; dx<w; dx++)
            put_pixel(x+dx, y+dy, r, g, b, a);
}

/* draw character at 1× scale (8×8), scale=1 or 2 */
static void draw_char(int cx, int cy, char ch, int scale,
                      uint8_t r, uint8_t g, uint8_t b) {
    if (ch < 0x20 || ch > 0x7F) ch = '?';
    const uint8_t *glyph = font8x8[(uint8_t)ch - 0x20];
    for (int row=0; row<8; row++)
        for (int col=0; col<8; col++)
            if (glyph[row] & (1 << col))
                for (int sy=0; sy<scale; sy++)
                    for (int sx=0; sx<scale; sx++)
                        put_pixel(cx + col*scale + sx,
                                  cy + row*scale + sy,
                                  r, g, b, 0xFF);
}

static void draw_str(int x, int y, const char *s, int scale,
                     uint8_t r, uint8_t g, uint8_t b) {
    for (int i=0; s[i]; i++)
        draw_char(x + i*8*scale, y, s[i], scale, r, g, b);
}

static void render_overlay(void) {
    char buf[32];
    tex_dirty = 1;
    fill_rect(0, 0, OW, OH, 0, 0, 0, 160);

    /* line 0: FPS */
    snprintf(buf, sizeof(buf), "FPS %4.1f", current_fps);
    draw_str(2, 2,  buf, 1, 255, 255, 0);

    /* line 1: CPU */
    snprintf(buf, sizeof(buf), "CPU %dC %dMHz", cpu_temp_c, cpu_mhz);
    draw_str(2, 14, buf, 1, 0, 255, 128);

    /* line 2: GPU */
    snprintf(buf, sizeof(buf), "GPU %dMHz", gpu_mhz);
    draw_str(2, 26, buf, 1, 0, 200, 255);

    /* line 3: RAM freq + usage */
    snprintf(buf, sizeof(buf), "RAM %dMHz %d%%", ram_mhz, ram_pct);
    draw_str(2, 38, buf, 1, 200, 150, 255);

    /* line 4: voltages */
    snprintf(buf, sizeof(buf), "A%dmV L%dmV", vdd_arm_mv, vdd_logic_mv);
    draw_str(2, 52, buf, 1, 255, 180, 80);
}

/* ------------------------------------------------------------------ */
/* GL overlay setup                                                    */
/* ------------------------------------------------------------------ */
static const char *vs_src =
    "attribute vec2 aPos;"
    "attribute vec2 aUV;"
    "varying vec2 vUV;"
    "void main(){"
    "  gl_Position=vec4(aPos,0.0,1.0);"
    "  vUV=aUV;"
    "}";

static const char *fs_src =
    "precision mediump float;"
    "varying vec2 vUV;"
    "uniform sampler2D uTex;"
    "void main(){"
    "  gl_FragColor=texture2D(uTex,vUV);"
    "}";

static void init_gl(void *gles) {
    LOAD_GL(glUseProgram);
    LOAD_GL(glCreateShader);
    LOAD_GL(glShaderSource);
    LOAD_GL(glCompileShader);
    LOAD_GL(glCreateProgram);
    LOAD_GL(glAttachShader);
    LOAD_GL(glLinkProgram);
    LOAD_GL(glGenTextures);
    LOAD_GL(glBindTexture);
    LOAD_GL(glTexImage2D);
    LOAD_GL(glTexSubImage2D);
    LOAD_GL(glTexParameteri);
    LOAD_GL(glGenBuffers);
    LOAD_GL(glBindBuffer);
    LOAD_GL(glBufferData);
    LOAD_GL(glGetAttribLocation);
    LOAD_GL(glGetUniformLocation);
    LOAD_GL(glEnableVertexAttribArray);
    LOAD_GL(glVertexAttribPointer);
    LOAD_GL(glDrawArrays);
    LOAD_GL(glUniform1i);
    LOAD_GL(glEnable);
    LOAD_GL(glDisable);
    LOAD_GL(glBlendFunc);
    LOAD_GL(glGetIntegerv);
    LOAD_GL(glIsEnabled);
    LOAD_GL(glViewport);
    LOAD_GL(glActiveTexture);
    LOAD_GL(glScissor);
    LOAD_GL(glPixelStorei);
    LOAD_GL(glDisableVertexAttribArray);

    if (!_glCreateProgram) { ofail=1; LOG("init_gl FAIL: no glCreateProgram\n"); return; }

    GLuint vs = _glCreateShader(GL_VERTEX_SHADER);
    GLuint fs = _glCreateShader(GL_FRAGMENT_SHADER);
    _glShaderSource(vs, 1, &vs_src, NULL);
    _glShaderSource(fs, 1, &fs_src, NULL);
    _glCompileShader(vs);
    _glCompileShader(fs);
    oprog = _glCreateProgram();
    _glAttachShader(oprog, vs);
    _glAttachShader(oprog, fs);
    _glLinkProgram(oprog);

    /* quad: covers top-left OW×OH pixels in NDC, y-flipped for GL */
    /* Assume 480×272 PPSSPP internal (scaled to screen).
       We place overlay at NDC (-1,1) to (-1+2*OW/W, 1-2*OH/H).
       Use conservative estimate 480×272, adjust if needed. */
    float x1 = -1.0f, y1 =  1.0f;
    float x2 = -1.0f + 2.0f*OW/640.0f;
    float y2 =  1.0f - 2.0f*OH/480.0f;
    float verts[] = {
        x1,y1, 0.0f,0.0f,
        x2,y1, 1.0f,0.0f,
        x1,y2, 0.0f,1.0f,
        x2,y1, 1.0f,0.0f,
        x2,y2, 1.0f,1.0f,
        x1,y2, 0.0f,1.0f,
    };
    _glGenBuffers(1, &ovbo);
    _glBindBuffer(GL_ARRAY_BUFFER, ovbo);
    _glBufferData(GL_ARRAY_BUFFER, sizeof(verts), verts, GL_STATIC_DRAW);
    _glBindBuffer(GL_ARRAY_BUFFER, 0);

    _glGenTextures(1, &otex);
    _glBindTexture(GL_TEXTURE_2D, otex);
    _glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    _glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    _glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    _glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    _glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, OW, OH, 0,
                  GL_RGBA, GL_UNSIGNED_BYTE, NULL);
    _glBindTexture(GL_TEXTURE_2D, 0);

    loc_uTex = _glGetUniformLocation(oprog, "uTex");
    loc_aPos = _glGetAttribLocation(oprog, "aPos");
    loc_aUV  = _glGetAttribLocation(oprog, "aUV");

    oinit = 1;
}

static void draw_overlay(void) {
    /* save state */
    int cur_prog = 0, prev_buf = 0, prev_tex = 0, prev_atex = 0x84C0 /*GL_TEXTURE0*/;
    int vp[4] = {0};
    unsigned char s_blend, s_depth, s_cull, s_scissor;
    _glGetIntegerv(GL_CURRENT_PROGRAM,      &cur_prog);
    _glGetIntegerv(GL_VIEWPORT,             vp);
    _glGetIntegerv(GL_ARRAY_BUFFER_BINDING, &prev_buf);
    _glGetIntegerv(GL_ACTIVE_TEXTURE,       &prev_atex);
    _glGetIntegerv(GL_TEXTURE_BINDING_2D,   &prev_tex);
    s_blend  = _glIsEnabled(GL_BLEND);
    s_depth  = _glIsEnabled(GL_DEPTH_TEST);
    s_cull   = _glIsEnabled(GL_CULL_FACE);
    s_scissor= _glIsEnabled(GL_SCISSOR_TEST);

    /* configure for overlay */
    _glDisable(GL_DEPTH_TEST);
    _glDisable(GL_CULL_FACE);
    _glDisable(GL_SCISSOR_TEST);
    _glEnable(GL_BLEND);
    _glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    _glViewport(0, 0, vp[2], vp[3]);

    /* upload texture only when stats changed (once per second) */
    _glActiveTexture(GL_TEXTURE0);
    _glBindTexture(GL_TEXTURE_2D, otex);
    if (tex_dirty) {
        _glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
        _glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, OW, OH,
                         GL_RGBA, GL_UNSIGNED_BYTE, obuf);
        tex_dirty = 0;
    }

    /* draw */
    _glUseProgram(oprog);
    _glUniform1i(loc_uTex, 0);
    _glBindBuffer(GL_ARRAY_BUFFER, ovbo);
    _glEnableVertexAttribArray(loc_aPos);
    _glVertexAttribPointer(loc_aPos, 2, GL_FLOAT, 0, 4*sizeof(float), (void*)0);
    _glEnableVertexAttribArray(loc_aUV);
    _glVertexAttribPointer(loc_aUV,  2, GL_FLOAT, 0, 4*sizeof(float), (void*)(2*sizeof(float)));
    _glDrawArrays(GL_TRIANGLES, 0, 6);

    /* restore state */
    _glDisableVertexAttribArray(loc_aPos);
    _glDisableVertexAttribArray(loc_aUV);
    _glBindBuffer(GL_ARRAY_BUFFER, prev_buf);
    _glActiveTexture(prev_atex);
    _glBindTexture(GL_TEXTURE_2D, prev_tex);
    _glUseProgram(cur_prog);
    _glViewport(vp[0], vp[1], vp[2], vp[3]);
    if (s_blend)   _glEnable(GL_BLEND);   else _glDisable(GL_BLEND);
    if (s_depth)   _glEnable(GL_DEPTH_TEST); else _glDisable(GL_DEPTH_TEST);
    if (s_cull)    _glEnable(GL_CULL_FACE);  else _glDisable(GL_CULL_FACE);
    if (s_scissor) _glEnable(GL_SCISSOR_TEST); else _glDisable(GL_SCISSOR_TEST);
}

/* ------------------------------------------------------------------ */
/* Library constructor — confirms .so was loaded                      */
/* ------------------------------------------------------------------ */
__attribute__((constructor))
static void overlay_init(void) {
    char comm[256] = {0};
    FILE *f = fopen("/proc/self/comm", "r");
    if (f) { fgets(comm, sizeof(comm), f); fclose(f); }
    if (strstr(comm, "emulationstat")) { overlay_enabled = 0; return; }

    write(2, "R36OVL:loaded\n", 14);
    dbgfd = open("/tmp/r36overlay.log", O_WRONLY|O_CREAT|O_TRUNC, 0666);
    stats_open();
    write(2, dbgfd>=0 ? "R36OVL:log_ok\n" : "R36OVL:log_fail\n", dbgfd>=0?14:16);
    LOG("r36overlay loaded\n");
}

/* ------------------------------------------------------------------ */
/* SDL_GL_SwapWindow hook                                              */
/* ------------------------------------------------------------------ */
/* shared state for both hooks */
static void *gles_handle = NULL;
static int   hook_ready  = 0;

static void ensure_ready(void) {
    if (hook_ready) return;
    hook_ready = 1;

    const char *gl_libs[] = {
        "libGLESv2.so.2", "libGLESv2.so",
        "libEGL.so.1",    "libEGL.so",
        "libMali.so",     NULL
    };
    for (int i = 0; gl_libs[i] && !gles_handle; i++)
        gles_handle = dlopen(gl_libs[i], RTLD_NOW | RTLD_NOLOAD);
    if (!gles_handle) gles_handle = RTLD_DEFAULT;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    update_stats();
    render_overlay();
    init_gl(gles_handle);
    LOG(oinit ? "GL init OK\n" : "GL init FAIL\n");
}

static void do_frame(void) {
    frame_serial++;
    frame_count++;
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    double elapsed = (now.tv_sec - t0.tv_sec) +
                     (now.tv_nsec - t0.tv_nsec) * 1e-9;
    if (elapsed >= 1.0) {
        current_fps = frame_count / elapsed;
        frame_count = 0;
        t0 = now;
        update_stats();
        render_overlay();
        if (statsfd >= 0) {
            char sb[96];
            int slen = snprintf(sb, sizeof(sb), "%lu,%.1f,%d,%d,%d,%d,%d,%d,%d\n",
                (unsigned long)now.tv_sec, current_fps,
                cpu_temp_c, cpu_mhz, gpu_mhz, ram_mhz, ram_pct, vdd_arm_mv, vdd_logic_mv);
            write(statsfd, sb, slen);
        }
    }
    if (oinit && !ofail) draw_overlay();
}

/* eglSwapBuffers hook (fallback for apps not using SDL_GL_SwapWindow) */
typedef unsigned int EGLBoolean;
typedef void* EGLDisplay;
typedef void* EGLSurface;
EGLBoolean eglSwapBuffers(EGLDisplay dpy, EGLSurface surface) {
    static EGLBoolean (*real_fn)(EGLDisplay, EGLSurface) = NULL;
    static int first = 1;
    static uint64_t last_serial = (uint64_t)-1;
    if (!real_fn) real_fn = dlsym(RTLD_NEXT, "eglSwapBuffers");
    if (!overlay_enabled) return real_fn ? real_fn(dpy, surface) : 1;
    if (first) { first = 0; LOG("eglSwapBuffers first call\n"); ensure_ready(); }
    if (last_serial != frame_serial) {
        last_serial = frame_serial;
        do_frame();
    }
    return real_fn ? real_fn(dpy, surface) : 1;
}

void SDL_GL_SwapWindow(SDL_Window *window) {
    static swap_fn_t real_fn = NULL;
    if (!real_fn) real_fn = dlsym(RTLD_NEXT, "SDL_GL_SwapWindow");
    if (!overlay_enabled) { if (real_fn) real_fn(window); return; }
    if (!hook_ready) {
        LOG("SDL_GL_SwapWindow first call\n");
        LOG("real SDL_GL_SwapWindow found\n");
        ensure_ready();
    }
    do_frame();
    if (real_fn) real_fn(window);
}
