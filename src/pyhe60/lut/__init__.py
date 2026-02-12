from .io import read_lut, write_lut, merge_partial_luts
from .format import make_lut_from_runs, estimate_lut_size
from .parallel import make_lut_multiprocessing, generate_inputs

# Try to import Ray-based distributed LUT generation
__make_lut_ray_available = False
try:
    from .distributed import make_lut_ray
    __make_lut_ray_available = True
except ImportError:
    pass

# Default to multiprocessing for backward compatibility
make_lut = make_lut_multiprocessing

__all__ = ['read_lut', 'write_lut', 'merge_partial_luts',
           'estimate_lut_size', 'make_lut_from_runs',
           'generate_inputs', 'make_lut_multiprocessing', 'make_lut']

if __make_lut_ray_available:
    __all__.append('make_lut_ray')
