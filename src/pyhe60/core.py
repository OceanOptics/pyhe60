import os
import subprocess
import warnings

import pandas as pd

from .constants import HE60_OUTPUT_DIR, HE60_WD, HE60_EXE, HE60_DATA
from .io import Hyrolight6Input
from .utils import init_he60_output_directories


def run_he60(input_filename, force=False, verbose=True):
    """
    Run HydroLight 6.0 with the given input file.

    :param input_filename: path to input file
    :param force: force re-run even if output file exists (default: False)
    :param verbose: display output from HydroLight 6.0 (default: True)
    :return: None
    """
    if not force:
        output_filename = f'M{os.path.basename(input_filename).lstrip("I").rstrip(".txt")}.xlsx'
        if os.path.exists(os.path.join(HE60_OUTPUT_DIR, output_filename)):
            if verbose:
                print(f'Skipping, output file already exists: {output_filename}')
            return
    kwargs = {} if verbose else {'stdout': subprocess.DEVNULL}  #, 'stderr': subprocess.DEVNULL}
    with open(input_filename, 'r') as f:
        subprocess.run([HE60_EXE], stdin=f, cwd=HE60_WD, **kwargs)


def run_he60_oneshot(cfg: dict, varname: str, working_dir: str=HE60_DATA, prefix: str= 'pyhe60', flag_cleanup: bool=False):
    """
    Run HydroLight 6.0 with the given config and write output to LUT.

    :param working_dir:
    :param cfg: config dict
    :param varname: variable name to extract from output
    :param prefix: hash prefix for input and output files
    :param flag_cleanup: if True, delete input and output files after reading output (default: True)
    :return: pd.DataFrame with output variable, indexed by wavelength and depth
    """
    # Setup directories
    os.makedirs(os.path.join(working_dir, 'run', 'batch'), exist_ok=True)
    init_he60_output_directories(os.path.join(working_dir, 'output'))

    # Write input file
    input = Hyrolight6Input(**cfg)
    input.output_dir = os.path.join(working_dir, 'output')
    input_filename = input.write(os.path.join(working_dir, 'run', 'batch'), prefix=prefix)

    try:
        # Run HydroLight 6.0
        with open(input_filename, 'r') as f:
            subprocess.run([HE60_EXE], stdin=f, cwd=HE60_WD, stdout=subprocess.DEVNULL)

        # Read output file
        output_filename = os.path.join(working_dir, 'output', 'HydroLight', 'excel', f'M{os.path.basename(input_filename).lstrip("I").rstrip(".txt")}.xlsx')
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            xlsx = pd.ExcelFile(output_filename)
            df = pd.read_excel(xlsx, varname, header=3, index_col=0)
    finally:
        # Clean up input and output files (even if interrupted or error occurs)
        if flag_cleanup:
            output_filename = os.path.join(working_dir, 'output', 'HydroLight', 'excel',
                                           f'M{os.path.basename(input_filename).lstrip("I")}')
            for f in [
                input_filename,
                output_filename,
                output_filename.rstrip('.txt') + '.xlsx',
                os.path.join(working_dir, 'output', 'HydroLight', 'printout',
                             f'P{os.path.basename(input_filename).lstrip("I")}')
            ]:
                try:
                    os.remove(f)
                except FileNotFoundError:
                    pass

    return df
