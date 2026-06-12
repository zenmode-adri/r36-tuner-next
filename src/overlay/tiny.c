#include <unistd.h>
__attribute__((constructor)) static void init(void) { write(2, "TINY\n", 5); }
