import os

import numpy as np

from pyhe60.constants import HE60_DATA
from pyhe60.lut import make_lut_ray

'''
Build a look up table (LUT) of HydroLight 6.0 output for the parameter space given.
Leverage Ray for distributed processing across multiple CPU cores and/or machines. 
'''


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
    'output_depths': np.arange(0, 0.2, 0.02).tolist() + [0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
}
spectral_variable = 'KLu'

# %% Ray parameters
head_node_ip = os.environ.get("HEAD_NODE_IP", '127.0.0.1')
head_node_client_port = os.environ.get("HEAD_NODE_PORT", '10001')
head_node_address = f"ray://{head_node_ip}:{head_node_client_port}"
ray_init_kwargs = dict(
    runtime_env={
        'pip': [
            "numpy>=2.4.2",
            "openpyxl>=3.1.5",
            "pandas>=3.0.0",
            "netcdf4>=1.7.4",
            "tqdm>=4.67.3",
        ],
        'py_modules': [os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'pyhe60'))],
        'env_vars': {
            'RAY_IGNORE_COMMAND_LINE_VALIDATION': '1',
            # 'RAY_DISABLE_MEMORY_MONITOR': '1'
        },
    },
    # _system_config={"file_system_monitor_enabled": False}
)

# %% Build LUT
path_to_lut = os.path.join(HE60_DATA, f'he60.{spectral_variable.lower()}.lut.r1.nc')
# if os.path.exists(path_to_lut):
#     os.remove(path_to_lut)
make_lut_ray(spectral_variable, parameter_space, constants, path_to_lut,
             resume_run=True, lut_is_contiguous=True,
             max_in_flight=200,
             ray_address=head_node_address, ray_init_kwargs=ray_init_kwargs)
print('LUT built at:', path_to_lut)
