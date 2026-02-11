from functools import partial
from hashlib import shake_128
import itertools
from multiprocessing import Pool
import os
from typing import Tuple, List

import numpy as np

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, *_, **__):
        return iterable
try:
    import netCDF4
except ImportError:
    netCDF4 = None

from .io import init_lut, write_chunk_to_lut
from ..core import run_he60_oneshot
from ..constants import HE60_DATA


def make_lut_multiprocessing(varname: str, dimensions: dict, constants: dict = None,
                             path_to_lut: str = None, working_dir: str = HE60_DATA,
                             resume_run: bool=False):
    """
    Generate HydroLight6 input files, run HydroLight6, and build n-dimensional lookup table in NetCDF file.
    Uses multiprocessing for parallelization on a single machine.
    Erase input and output files from HydroLight6 as it runs.
    If ram disk is available, it's recommended to use it as working directory for speed.

    :param varname: Variable name to store in LUT (e.g. KLu, Rrs, Lu, Ed, Kd)
    :param dimensions: Environmental parameters to vary
    :param constants: Constant environmental parameters, to change defaults from Hyrolight6Input
    :param path_to_lut: Path to output NetCDF LUT file
    :param working_dir: Path to HydroLight6 working directory (default to HE60_DATA)
    :param resume_run: Enable resuming an incomplete LUT run by skipping already computed chunks (default: False)
    :return:
    """

    # Run UID
    lut_hash = shake_128((str(dimensions)+str(constants)).encode()).hexdigest(3)

    # Generate input
    inputs, indexes = generate_inputs(dimensions, constants)
    if resume_run:
        inputs, indexes = skip_computed_chunks(inputs, indexes, varname, path_to_lut)
        print('Resuming run, remaining simulations:', len(inputs))

    # Initialize LUT
    if not resume_run:
        init_lut(path_to_lut, varname, dimensions, constants, lut_hash)
    elif not os.path.exists(path_to_lut):
        raise ValueError(f'Unable to resume, LUT file not found: {path_to_lut}')

    # Loop over inputs in parallel
    worker = partial(
        _make_lut_chunk_multiprocessing,
        constants=constants,
        varname=varname,
        run_hash=lut_hash,
        working_dir=working_dir
    )
    with Pool() as pool:  # default to os.process_cpu_count()
        for chunk in tqdm(pool.imap_unordered(worker, zip(inputs, indexes)), total=len(inputs), desc=f'HE60'):
            df, index = chunk
            # Protect critical section from KeyboardInterrupt to prevent data corruption
            write_chunk_to_lut(df, index, varname, path_to_lut)


def generate_inputs(dimensions: dict, constants: dict = None):
    """
    Generate list of HydroLight6 input configurations and corresponding LUT indices from dimensions.

    :param dimensions: Environmental parameters to vary, as dict of parameter name to list of values
    :param constants: Environmental constants, check they are not present in dimensions
    :return: inputs, indexes
    """
    if constants is not None:
        for k in constants.keys():
            if k in dimensions:
                raise ValueError(f'Constants and dimensions overlap on key: {k}')
    inputs, indexes = [], []
    combinations = list(itertools.product(*dimensions.values()))
    for input in tqdm(combinations, desc='Inputs'):
        inputs.append({k: i for k, i in zip(dimensions, input)})
        indexes.append(tuple(v.index(i) for v, i in zip(dimensions.values(), input)))
    return inputs, indexes


def skip_computed_chunks(inputs: List[dict], indexes: List[Tuple[int]], varname: str, path_to_lut: str):
    """
    Remove already computed chunks from inputs and indexes by checking for missing values in LUT file.
    This allows resuming an incomplete LUT run without re-running HydroLight6 for already computed chunks.

    :param inputs: List of input LUT chunks
    :param indexes: List of index tuples
    :param varname: Variable name to store in LUT (e.g. KLu, Rrs, Lu, Ed, Kd)
    :param path_to_lut: Path to output NetCDF LUT file
    :return: filtered_inputs and filtered_indexes
    """
    # if LUT does not exist, return all indexes
    if not os.path.isfile(path_to_lut):
        return inputs, indexes

    # Check if already processed
    filtered_inputs, filtered_indexes = [], []
    with netCDF4.Dataset(path_to_lut, 'r') as d:
        if varname in d.variables:
            var = d.variables[varname]
            for input, index in zip(inputs, indexes):
                if np.ma.getmaskarray(var[(slice(None), slice(None)) + index]).all():
                    # Not computed yet
                    filtered_inputs.append(input)
                    filtered_indexes.append(index)

    return filtered_inputs, filtered_indexes


def _make_lut_chunk_multiprocessing(cfg: tuple, constants: dict, varname: str,
                                    run_hash: str, working_dir: str = HE60_DATA):
    """
    Run HydroLight 6.0 for one input configuration and return output variable as DataFrame with corresponding LUT index.
    Generate required inpout file, and erase input and output files from HydroLight6 when run is completed.

    :param cfg: tuple of (input dict, index tuple)
    :param constants: Constant environmental parameters, to change defaults from Hyrolight6Input
    :param varname: Variable name to store in LUT (e.g. KLu, Rrs, Lu, Ed, Kd)
    :param run_hash: Hash string for this LUT run
    :param working_dir: Path to HydroLight6 working directory (default to HE60_DATA)
    :return:
    """
    # Split config (needed as Pool.imap only supports single argument functions)
    input, index = cfg

    # Run HydroLight 6.0
    df = run_he60_oneshot({**input, **constants}, varname, working_dir, prefix=run_hash, flag_cleanup=True)

    return df, index
