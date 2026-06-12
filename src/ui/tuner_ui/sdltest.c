#include <SDL2/SDL.h>
#include <stdio.h>
int main(void) {
    printf("Init...\n"); fflush(stdout);
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        printf("SDL_Init FAIL: %s\n", SDL_GetError()); return 1;
    }
    printf("Driver: %s\n", SDL_GetCurrentVideoDriver()); fflush(stdout);
    SDL_Window *w = SDL_CreateWindow("test",0,0,640,480,SDL_WINDOW_SHOWN);
    if (!w) { printf("Window FAIL: %s\n", SDL_GetError()); return 1; }
    printf("Window OK\n"); fflush(stdout);
    SDL_Delay(3000);
    SDL_DestroyWindow(w);
    SDL_Quit();
    return 0;
}
