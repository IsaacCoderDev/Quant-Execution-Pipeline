import numpy as np
cimport numpy as cnp

cdef class TickRingBuffer:
    cdef public int capacity
    cdef public int _head
    cdef public bint _full
    
    # C-contiguous memoryview for ultra-fast pointer access
    cdef double[:, ::1] _data 

    def __init__(self, int capacity=10000):
        self.capacity = capacity
        self._head = 0
        self._full = False

        # Allocate the underlying NumPy array and bind it to the memoryview
        self._data = np.zeros((capacity, 5), dtype=np.float64)

    cdef void push(self, double timestamp, double bid_price, double bid_qty, double ask_price, double ask_qty) nogil:
        """
        nogil drops the Python lock. This execution is now pure C.
        """
        self._data[self._head, 0] = timestamp
        self._data[self._head, 1] = bid_price
        self._data[self._head, 2] = bid_qty
        self._data[self._head, 3] = ask_price
        self._data[self._head, 4] = ask_qty
        
        self._head = (self._head + 1) % self.capacity

        if self._head == 0:
            self._full = True