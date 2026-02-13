import glob
import os
import re

import numpy as np

from pyhe60.lut import make_lut, generate_inputs, merge_partial_luts

"""
Build look up table (LUT) of HydroLight 6.0 output for the parameter space given, 
by manually splitting the LUT generation into multiple jobs to run in parallel across multiple nodes.
Manual implementation to provide an alternative for users who cannot use Ray.
"""

if __name__ == '__main__':  # Needed for multiprocessing
    # %% Parameter Space
    parameter_space = {
        'chlorophyll': [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.6, 0.8, 1, 2, 4],  # µg/L
        'sun_zenith_angle': [0, 10, 20, 30, 40, 50, 60, 70],  # degrees
        'temperature': [5, 10, 15, 20, 25, 30, 35],  # degrees Celsius
        'wind_speed': [0, 1, 2, 3, 5, 10, 15],  # m/s
        'salinity': [32.5, 35, 37.5, 40],  # PSU
    }
    constants = {
        'wavelength_start': 310, 'wavelength_stop': 790, 'wavelength_step': 1,
        'output_depths': np.arange(0, 0.2, 0.02).tolist() + [0.2, 0.5, 1.0]  #, 2.0, 5.0, 10.0]
    }
    spectral_variables = ['KLu', 'Kd', 'Lu', 'Ed']

    # %% Select one job and run it with make_lut_multiprocessing
    n_jobs = 48
    job_id = 24
    working_dir = '/Volumes/RAMDisk/HE60'

    def generate_inputs_for_job(dimensions, constants):
        global job_id, n_jobs
        # Generate Inputs
        inputs, indexes = generate_inputs(dimensions, constants)
        job_size = len(inputs) // n_jobs + (1 if len(inputs) % n_jobs > 0 else 0)
        # Split inputs and indexes for this job
        job_inputs = inputs[job_id * job_size:(job_id + 1) * job_size]
        job_indexes = indexes[job_id * job_size:(job_id + 1) * job_size]
        # Print info about parameter space covered by this job:
        print(f"Job {job_id}/{n_jobs} - Number of runs: {len(job_inputs)}/{len(inputs)}")
        for dim in dimensions.keys():
            dim_values = sorted(set([input[dim] for input in job_inputs]))
            print(f"  {dim}: {dim_values[0]} to {dim_values[-1]} ({len(dim_values)} values)")
        return job_inputs, job_indexes

    path_to_lut = os.path.join(working_dir, f'he60.lut.r1.j{job_id}-{n_jobs}.nc')
    print(f"Generating LUT for job {job_id} at {path_to_lut} ...")
    make_lut = make_lut(spectral_variables, parameter_space, constants, path_to_lut,
                        resume_run=False, lut_is_contiguous=True, generate_inputs_fn=generate_inputs_for_job,
                        n_processes=12)

    # %% After all jobs are completed, merge the resulting LUT files into one final LUT file
    natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]
    path_to_luts = sorted(glob.glob(os.path.join(working_dir, 'he60.lut.r1.j*.nc')), key=natsort)
    final_lut_path = os.path.join(working_dir, f'he60.lut.r1.merged.nc')
    merge_partial_luts(path_to_luts, final_lut_path)
