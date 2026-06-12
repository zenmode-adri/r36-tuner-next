#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#define SZ (128*1024*1024)
#define SECS 15

static double bench_write(char *a) {
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long end = t0.tv_sec + SECS;
    int runs = 0;
    while (1) {
        clock_gettime(CLOCK_MONOTONIC, &t1);
        if (t1.tv_sec >= end) break;
        memset(a, 0xAB, SZ);
        __asm__ volatile ("" ::: "memory");
        runs++;
    }
    double el = (t1.tv_sec-t0.tv_sec) + (t1.tv_nsec-t0.tv_nsec)/1e9;
    return (double)runs * SZ / 1024.0 / 1024.0 / el;
}

static double bench_copy(char *a, char *b) {
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    long long end = t0.tv_sec + SECS;
    int runs = 0;
    while (1) {
        clock_gettime(CLOCK_MONOTONIC, &t1);
        if (t1.tv_sec >= end) break;
        memcpy(b, a, SZ);
        __asm__ volatile ("" ::: "memory");
        runs++;
    }
    double el = (t1.tv_sec-t0.tv_sec) + (t1.tv_nsec-t0.tv_nsec)/1e9;
    return (double)runs * SZ / 1024.0 / 1024.0 / el;
}

int main() {
    char *a = malloc(SZ), *b = malloc(SZ);
    if (!a || !b) { puts("OOM"); return 1; }
    memset(a, 0, SZ);
    double w = bench_write(a);
    double c = bench_copy(a, b);
    char buf[64];
    snprintf(buf, sizeof(buf), "Write: %.0f MB/s  Copy: %.0f MB/s", w, c);
    puts(buf);
    return 0;
}
