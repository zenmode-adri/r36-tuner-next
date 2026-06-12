#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#define SZ (128*1024*1024)
int main(){
    char *a=malloc(SZ),*b=malloc(SZ);
    if(!a||!b){puts("OOM");return 1;}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    long long end=t0.tv_sec+30;
    int runs=0;
    while(1){
        clock_gettime(CLOCK_MONOTONIC,&t1);
        if(t1.tv_sec>=end) break;
        memset(a,0xAB,SZ);
        memcpy(b,a,SZ);
        runs++;
    }
    double mb=(double)runs*SZ*2/1024.0/1024.0;
    double el=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
    char buf[64];
    snprintf(buf,sizeof(buf),"STABLE: %d runs %.0f MB/s",runs,mb/el);
    puts(buf);
    return 0;
}
