from multiprocessing import Pool

import numpy as np

import pyhe60 as he
from pyhe60.plotting import select_subset, plot_property, plot_spectrum

if __name__ == '__main__':  # Needed for multiprocessing
    # %% 1. Write Input Parameter Space
    parameter_space = {
        'chlorophyll': np.arange(0, 1.05, 0.05),  # µg/L
        'sun_zenith_angle': np.arange(0, 85, 10),  # degrees
        'temperature': np.arange(8, 33, 2),  # degrees Celsius
        'wind_speed': np.arange(0, 11), # m/s
        # 'salinity': np.arange(33, 41, 1),  # PSU
        # 'uv_particle_absorption': ['low', 'medium', 'high'],  # UV particle absorption
        # 'include_raman_scattering_by_water': [True, False],  # Inelastic Scattering
        # 'sun_azimuth_angle_relative_to_downwind_direction': np.arange(0, 181, 30),  # degrees
        # 'sea_level_pressure': np.arange(28, 33), # inches Hg
        # 'relative_humidity': np.arange(45, 100, 5),  # %
        # 'total_ozone_content': np.arange(250, 501, 50),  # to3 in Dobson Units
        # 'airmass_type': np.arange(1, 11),  # Airmass type (1 to 10)
        # 'day_of_year': list(range(1, 365, 30)) + ['annual_average'],  # day of year
    }
    constants = {
        'wavelength_start': 320, 'wavelength_stop': 780, 'wavelength_step': 20,
        'output_depths': np.arange(0, 10.5, 0.5)
    }
    input_filenames = he.generate_input_files(parameter_space, constants, prefix='demo')


    # %% 2. Run HydroLight 6.0
    # Run sequentially (easy to debug)
    # for input_filename in input_filenames:
    #     he.run_he60(input_filename)

    # Run in parallel (fast)
    with Pool() as p:
        p.map(he.run_he60, input_filenames)


    # %% 3. Read Results
    spectral_variable = 'KLu'
    target_depth = 0.5  # m
    df, z_ref = he.read_multi_m_xslx(spectral_variable, target_depth, prefix='demo')


    # %% 4. Plot Results
    for cp in parameter_space.keys():
        subset = select_subset(df, cp)
        if len(subset) < 2:
            continue  # Need at least two different values to compare

        fig = plot_spectrum(subset, cp, spectral_variable)
        fig.update_layout(title=f'Effect of {cp} on {spectral_variable} at {target_depth} m')
        fig.show()

        fig2 = plot_property(subset, cp, spectral_variable)
        fig2.update_layout(title=f'Effect of {cp} on {spectral_variable} at {target_depth} m')
        fig2.show()
