import os
import numpy as np
import pandas as pd

from ..utils import sizeof_fmt


def estimate_lut_size(dimensions: dict):
    ndims = [d if isinstance(d, int) else len(d) for d in dimensions.values()]
    size_bytes = np.prod(ndims) * 4  # float32
    return sizeof_fmt(size_bytes)


def make_lut_from_runs(df: pd.DataFrame, varname: str = 'KLu'):
    """
    Build n-dimensional lookup table from HydroLight6 output dataframe
    :return:
    """

    # Find dimensions
    wl = np.unique(np.stack(df['wl'].to_list()), axis=0)
    if len(wl) > 1:
        raise ValueError('Multiple wavelength configurations found, cannot build LUT.')
    dims = {'wl': np.squeeze(wl)}
    if 'z' in df.columns:
        z = np.unique(np.stack(df['z'].to_list()), axis=0)
        if len(z) > 1:
            raise ValueError('Multiple depth configurations found, cannot build LUT.')
        dims['z'] = np.squeeze(z)
    ignore_dims = ['ref', varname] + list(dims.keys())
    constants = {}
    for c in df.columns:
        if c in ignore_dims:
            continue
        unique_values = df[c].unique().tolist()
        if len(unique_values) > 1:
            dims[c] = sorted(unique_values)
        else:
            constants[c] = unique_values[0]
    # Initialize LUT (check fits in memory)
    ndims = [len(d) for d in dims.values()]
    lut_size = estimate_lut_size(ndims)
    local_memory_size = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')  # in bytes
    if lut_size > 0.8 * local_memory_size:
        raise MemoryError(f"Lookup table size {sizeof_fmt(lut_size)} exceeds 32 GB limit.")
    lut = np.empty(ndims, dtype=np.float32) * np.nan
    # Fill LUT
    main_idx = [slice(None), slice(None)] if 'z' in dims else [slice(None)]
    for _, row in df.iterrows():
        idx = main_idx + [dim.index(row[key]) for key, dim in dims.items() if key not in ['wl', 'z']]
        lut[tuple(idx)] = row[varname]
    return lut, dims, constants
