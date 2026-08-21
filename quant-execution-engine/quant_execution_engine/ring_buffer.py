from typing import Optional, Tuple
import numpy as np


class TickRingBuffer:
    """
    A fixed-size, zero-allocation circular buffer for time-series tick data.
    Stores [timestamp, bid_price, bid_qty, ask_price, ask_qty] in a 2D float64 matrix.
    """

    def __init__(self, capacity: int = 10_000) -> None:
        self.capacity: int = capacity
        self._data: np.ndarray = np.zeros((capacity, 5), dtype=np.float64)
        self._head: int = 0
        self._full: bool = False

    def push(self, timestamp: float, bid_price: float, bid_qty: float, ask_price: float, ask_qty: float,) -> None:
        """
        Overwrites memory in-place at the current head index. O(1) performance.
        """

        self._data[self._head] = [timestamp, bid_price, bid_qty, ask_price, ask_qty]
        self._head = (self._head + 1) % self.capacity

        if self._head == 0:
            self._full = True

    def get_latest(self) -> np.ndarray:
        """Returns the single most recent tick [1, 5] without copying arrays."""

        if not self._full and self._head == 0:
            raise ValueError("Buffer is empty.")

        latest_idx = (self._head - 1) % self.capacity

        return self._data[latest_idx]

    def get_window(self, length: int) -> np.ndarray:
        """
        Extracts the last 'length' ticks in chronological order.
        Handles ring-wrapping using zero-copy slicing where possible.
        """

        if length > self.capacity:
            raise ValueError(f"Requested length {length} exceeds capacity {self.capacity}.")

        size = self.capacity if self._full else self._head

        if length > size:
            length = size

        if self._head >= length:
            return self._data[self._head - length : self._head]
        else:
            tail_len = length - self._head

            return np.vstack((self._data[self.capacity - tail_len :], self._data[: self._head]))

    @property
    def is_full(self) -> bool:
        return self._full

    def __len__(self) -> int:
        return self.capacity if self._full else self._head