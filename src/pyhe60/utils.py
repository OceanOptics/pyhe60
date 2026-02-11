from contextlib import contextmanager
import os
import signal

import numpy as np

from pyhe60.constants import HE60_DATA


@contextmanager
def delay_sigint():
    """
    Context manager to delay KeyboardInterrupt during critical sections.
    The interrupt will be raised after exiting the context.
    """
    signal_received = None

    def handler(sig, frame):
        nonlocal signal_received
        signal_received = (sig, frame)

    old_handler = signal.signal(signal.SIGINT, handler)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, old_handler)
        if signal_received:
            old_handler(*signal_received)


def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Y', suffix)


def get_dtype(value):
    if isinstance(value, (np.ndarray, list)):
        dtype = np.array(value).dtype
        fill_value = np.nan if np.issubdtype(dtype, np.floating) else None
        return dtype, fill_value
    if isinstance(value, bool):
        return 'u1', None
    if isinstance(value, int):
        return 'i4', None
    if isinstance(value, float):
        return 'f4', np.nan
    if isinstance(value, str):
        return str, None
    raise ValueError(f'Unsupported constant type: {type(value)}.')


def init_he60_output_directories(output_dir=os.path.join(HE60_DATA, 'output')):
    for dir in [os.path.join(output_dir, 'HydroLight', 'digital'),
                os.path.join(output_dir, 'HydroLight', 'excel'),
                os.path.join(output_dir, 'HydroLight', 'printout')]:
        os.makedirs(dir, exist_ok=True)
