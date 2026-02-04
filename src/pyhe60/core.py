import os
import subprocess

from .constants import HE60_OUTPUT_DIR, HE60_ROOT, HE60_EXE
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
        subprocess.run([f"./{HE60_EXE}"], stdin=f, cwd=HE60_ROOT, **kwargs)

