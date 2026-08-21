import pytest
import numpy as np
from quant_execution_engine.ring_buffer import TickRingBuffer


def test_push_and_latest():

    buf = TickRingBuffer(capacity=5)
    buf.push(100.0, 50000.0, 1.5, 50001.0, 2.0)

    latest = buf.get_latest()

    assert latest[0] == 100.0
    assert latest[1] == 50000.0
    assert len(buf) == 1


def test_ring_wrapping_overwrites_oldest():

    buf = TickRingBuffer(capacity=3)

    buf.push(1.0, 10.0, 1.0, 11.0, 1.0)
    buf.push(2.0, 10.0, 1.0, 11.0, 1.0)
    buf.push(3.0, 10.0, 1.0, 11.0, 1.0)

    buf.push(4.0, 10.0, 1.0, 11.0, 1.0)

    window = buf.get_window(3)

    np.testing.assert_array_equal(window[:, 0], np.array([2.0, 3.0, 4.0]))

    assert buf.is_full is True