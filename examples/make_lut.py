import os

import numpy as np

from pyhe60.constants import HE60_DATA
from pyhe60.lut import make_lut_oneshot, estimate_lut_size

'''
Build a look up table (LUT) of HydroLight 6.0 output for the parameter space given.
'''


if __name__ == '__main__':  # Needed for multiprocessing
    # %% Parameter Space
    parameter_space = {
        'chlorophyll': [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.6, 0.8, 1, 2, 4],  # µg/L
        'sun_zenith_angle': [0, 10, 20, 30, 40, 50, 60, 70, 80],  # degrees
        'temperature': [5, 10, 15, 20, 25, 30, 35],  # degrees Celsius (might need higher resolution arround 9degC
        'wind_speed': [0, 1, 2, 3, 5, 10, 15],  # m/s
        'salinity': [32.5, 35, 37.5, 40],  # PSU
    }
    constants = {
        'wavelength_start': 310, 'wavelength_stop': 790, 'wavelength_step': 1,
        'output_depths': np.arange(0, 0.2, 0.02).tolist() + [0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
    }
    spectral_variable = 'KLu'

    # %% Estimate LUT Size
    s = estimate_lut_size(dimensions={
        'wl': np.arange(constants['wavelength_start'], constants['wavelength_stop'], constants['wavelength_step']),
        'z': constants['output_depths'], **parameter_space,
    })
    print(f"Estimated LUT size: {s}")

    # %% Set working directory
    # pyhe60 will write temporary input files and HydroLight 6.0 will write output files to working_dir
    # this creates a lot of I/O, one could use a RAM disk for faster performance (if enough RAM is available)
    # To create a 1 GB RAM disk on macOS
    #   diskutil erasevolume HFS+ RAMDisk $(hdiutil attach -nomount ram://2097152)
    working_dir = '/Volumes/RAMDisk/HE60'
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    # Or use default path
    # working_dir = HE60_DATA

    # %% Build LUT
    path_to_lut = os.path.join(working_dir, f'he60.{spectral_variable.lower()}.lut.r0.nc')
    lut = make_lut_oneshot(spectral_variable, parameter_space, constants, path_to_lut, working_dir)
