# profiler.pyx
cimport cython

import numpy as np

cimport numpy as cnp

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True) # Bypasses Python's ZeroDivisionError check for raw C division
def calculate_obi_cython(double[:, ::1] window):
    cdef int i
    cdef int n = window.shape[0]
    
    # Allocate output array
    cdef cnp.ndarray[cnp.float64_t, ndim=1] obi = np.zeros(n, dtype=np.float64)
    cdef double bid_qty, ask_qty, total_qty
    
    for i in range(n):
        bid_qty = window[i, 2]
        ask_qty = window[i, 4]
        total_qty = bid_qty + ask_qty
        
        if total_qty != 0:
            obi[i] = (bid_qty - ask_qty) / total_qty
        else:
            obi[i] = 0.0
            
    return obi