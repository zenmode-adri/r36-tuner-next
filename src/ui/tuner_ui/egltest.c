#include <dlfcn.h>
#include <stdio.h>
int main(void) {
    void *h = dlopen("libEGL.so.1", RTLD_NOW);
    if (!h) { printf("dlopen libEGL.so.1 FAIL: %s\n", dlerror()); }
    else     { printf("dlopen libEGL.so.1 OK\n"); dlclose(h); }

    h = dlopen("/lib/aarch64-linux-gnu/libEGL.so.1", RTLD_NOW);
    if (!h) { printf("dlopen full path FAIL: %s\n", dlerror()); }
    else     { printf("dlopen full path OK\n"); dlclose(h); }
    return 0;
}
