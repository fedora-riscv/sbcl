#include <stdio.h>
#include <sys/personality.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
  if ( argc >= 2 ) {
  long pers = personality(-1);

  /* 0x40000 aka. ADDR_NO_RANDOMIZE */
  if (!(pers & 0x40000)) {
    if (personality(pers | 0x40000) == -1) {
      fprintf(stderr, "WARNING: Couldn't set the proper personality flags.  Trying to continue anyway.\n");
    }
  }
  /* fprintf (stdout, "DEBUG: execing %s with arg %s",argv[1],&argv[1]); */
  execvp(argv[1], &argv[1]); 
  
  }
  exit(0);
}
