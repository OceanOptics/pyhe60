from hashlib import shake_128
import os
from typing import Optional, Tuple

import ray
try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - optional dependency
    tqdm = None

from .parallel import generate_inputs, skip_computed_chunks
from .io import init_lut, write_chunk_to_lut
from ..core import run_he60_oneshot
from ..constants import get_he60_data_dir


@ray.remote
def _make_lut_chunk_ray(index: Tuple[int], input: dict, constants: dict, varname: str,
                        run_hash: str, node_working_dir: str):
    """
    Generate HydroLight6 input files, run HydroLight6, and append output to lut.

    Erase input and output files from HydroLight6 as it runs.
    if ram disk is available, it's recommended to use it as working directory for speed.

    :param index: tuple of parameter values corresponding to this input
    :param input: dict of HydroLight6 input parameters for this run
    :param constants: Constant environmental parameters, to change defaults from Hyrolight6Input
    :param varname: Variable name to store in LUT (e.g. KLu, Rrs, Lu, Ed, Kd)
    :param run_hash: Hash string for this LUT run
    :param node_working_dir: Path to HydroLight6 working directory (default to HE60_DATA)
    :return:
    """
    if node_working_dir is None:
        node_working_dir = get_he60_data_dir()  # Need dynamic call to get correct path on each node if different os are used
    df = run_he60_oneshot({**input, **constants}, varname, node_working_dir, prefix=run_hash, flag_cleanup=True)
    return df, index


def make_lut_ray(varname: str, dimensions: dict, constants: dict = None,
                 path_to_lut: str = None, resume_run: bool = False, lut_is_contiguous: bool = False,
                 node_working_dir: str = None, max_in_flight: Optional[int] = None,
                 ray_address: Optional[str] = None, ray_init_kwargs: Optional[dict] = None):
    """
    Generate HydroLight6 input files, run HydroLight6, and build n-dimensional lookup table in NetCDF file.
    Erase input and output files from HydroLight6 as it runs.
    If ram disk is available, it's recommended to use it as working directory for speed.

    :param varname: Variable name to store in LUT (e.g. KLu, Rrs, Lu, Ed, Kd)
    :param dimensions: Environmental parameters to vary
    :param constants: Constant environmental parameters, to change defaults from Hyrolight6Input
    :param path_to_lut: Path to output NetCDF LUT file
    :param working_dir: Path to HydroLight6 working directory (default to HE60_DATA)
    :param resume_run: Enable resuming an incomplete LUT run by skipping already computed chunks (default: False)
    :param lut_is_contiguous: If True, assumes incomplete LUT is contiguous (no gaps) and sequentially filled. (default: False)
    :param node_working_dir: Path to HydroLight6 working directory on each Ray node (default to HE60_DATA for None (os dependent))
    :param max_in_flight: Max number of submitted tasks kept in flight (None for unlimited)
    :param ray_address: Ray cluster address (None for local)
    :param ray_init_kwargs: Extra kwargs forwarded to ray.init
    :return:
    """

    # Run UID
    lut_hash = shake_128((str(dimensions) + str(constants)).encode()).hexdigest(3)

    # Generate input
    inputs, indexes = generate_inputs(dimensions, constants)
    if resume_run:
        inputs, indexes = skip_computed_chunks(inputs, indexes, varname, path_to_lut, lut_is_contiguous)
        print('Resuming run, skipping already computed chunks. Remaining chunks:', len(inputs))

    # Initialize LUT
    if not resume_run:
        init_lut(path_to_lut, varname, dimensions, constants, lut_hash)
    elif not os.path.exists(path_to_lut):
        raise ValueError(f'Unable to resume, LUT file not found: {path_to_lut}')

    # Initialize Ray
    started_ray = False
    if not ray.is_initialized():
        print(f"Connecting to Ray cluster at {ray_address}")
        ray.init(address=ray_address, **(ray_init_kwargs or {}))
        started_ray = True

    # Run tasks in parallel, writing completed chunks to LUT as they finish to avoid keeping everything in memory
    pbar = tqdm(total=len(inputs), desc="HE60", unit="runs") if tqdm else None
    try:
        pending = []
        constants_ref = ray.put(constants or {})
        for index, input in zip(indexes, inputs):
            pending.append(_make_lut_chunk_ray.remote(index, input, constants_ref, varname, lut_hash, node_working_dir))
            if max_in_flight and len(pending) >= max_in_flight:
                done, pending = ray.wait(pending, num_returns=1)
                df, index = ray.get(done[0])
                write_chunk_to_lut(df, index, varname, path_to_lut)
                if pbar:
                    pbar.update(1)

        while pending:
            done, pending = ray.wait(pending, num_returns=1)
            df, index = ray.get(done[0])
            write_chunk_to_lut(df, index, varname, path_to_lut)
            if pbar:
                pbar.update(1)
    finally:
        if pbar:
            pbar.close()
        if started_ray:
            ray.shutdown()
