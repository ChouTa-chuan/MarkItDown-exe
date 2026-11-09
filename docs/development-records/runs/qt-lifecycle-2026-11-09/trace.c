#include <execinfo.h>
#include <signal.h>
#include <unistd.h>
static void trace(int sig) {
    void *frames[64];
    int n=backtrace(frames,64);
    backtrace_symbols_fd(frames,n,2);
    signal(sig,SIG_DFL);
    raise(sig);
}
void install_trace(void) { signal(SIGSEGV,trace); }
