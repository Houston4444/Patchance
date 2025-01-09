from cffi import FFI
ffibuilder = FFI()

ffibuilder.cdef("int process_cb(unsigned long frames, void *arg);")

ffibuilder.set_source("_process_cb",  # name of the output C extension
"""
    #include "process_cb.h"
""",
    sources=['process_cb.c'],   # includes pi.c as additional sources
    libraries=['m'])    # on Unix, link with the math library

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)