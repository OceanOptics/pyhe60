from dataclasses import dataclass, fields, field
import glob
from hashlib import shake_128
import itertools
import os
from typing import Union
import warnings

import numpy as np
import pandas as pd

from .utils import init_he60_output_directories

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, *_, **__):
        return iterable

from .constants import HE60_DATA, HE60_OUTPUT_DIR, HE60_INPUT_DIR


# %% -- Read & Write HydroLight 6.0 Inputs -- %% #

@dataclass
class Hyrolight6Input:
    # Assumptions about the water body and atmospheric conditions
    #   - New Case 1 IOPs (IOPs are obtained from recent bio-optical models for case 1 water)
    #   - Constant chlorophyll concentration with depth
    #   - Semi-empirical sky model (based on RADTRAN-X)
    temperature: float = 20.0  # degrees Celsius
    salinity: float = 35.0  # PSU
    chlorophyll: float = 0.10  # Chlorophyll concentration (mg/m^3)
    uv_particle_absorption: str = 'medium'  # 'low', 'medium', 'high'
    include_bioluminescence: bool = False
    include_chlorophyll_fluorescence: bool = True
    include_cdom_fluorescence: bool = True
    include_raman_scattering_by_water: bool = True
    wavelength_start: float = 310.0  # Start wavelength (nm)
    wavelength_stop: float = 790.0  # End wavelength (nm)
    wavelength_step: float = 1.0  # Spacing between wavelength (nm)
    wind_speed: float = 5.0  # Wind speed (m/s)
    index_of_refraction_seawater: Union[float, str] = 'wavelength_dependent'
        # float: Index of refraction of seawater (e.g. 1.34)
        # str: 'wavelength_dependent':  n varies with wavelength, T, and S
    sun_azimuth_angle_relative_to_downwind_direction: float = 0.0  # Sun azimuth angle relative to downwind direction (degrees, 0 to 180)
    sun_zenith_angle: float = 30.0  # Sun zenith angle (degrees, 0 to 90)
    cloud_cover: float = 0  # Cloud cover (fractional, 0 to 1)
    sea_level_pressure: float = 29.92  # inches Hg
    horizontal_visibility: float = 15.0  # km
    relative_humidity: float = 80.0  # %
    precipitable_water_content: float = 2.5  # cm
    total_ozone_content: Union[float, str] = 300  # int: to3 in Dobson Units or str: 'climatology' to use climatological values (requires lat and lon)
    airmass_type: int = 1  # Airmass type (1 to 10; 1: marine, 10: continental; see Gathman, 1983, for a description of aerosol types)
    day_of_year: Union[int, str] = 'annual_average'  # str: 'annual_average' or int: day of year (1 to 365)
    output_depths: list[float] = field(default_factory=lambda: [0.0, 1.0, 2.0, 5.0, 10.0])
    output_dir: str = os.path.join(HE60_DATA, 'output')

    def hash(self):
        # Can't use __hash__ as __hash__ should return an integer
        buffer = ''
        # Ensure all fields are typed consistently
        for f in fields(Hyrolight6Input):
            value = getattr(self, f.name)
            if f.type == Union[float, str]:
                buffer += value if isinstance(value, str) else str(float(value))
            elif f.type == Union[int, str]:
                buffer += value if isinstance(value, str) else str(int(value))
            elif f.type == list[float]:
                buffer += str([float(v) for v in value])
            elif isinstance(value, f.type):
                buffer += str(value)
            else:
                buffer += str(f.type(value))
        return shake_128(buffer.encode()).hexdigest(10)
        # return shake_128("".join(str(v) for v in self.__dict__.values()).encode()).hexdigest(10)

    def write(self, path_to_file=HE60_INPUT_DIR, prefix='pyhe60'):
        """
        Write HydroLight6 input file

        :param path_to_file: path to write configuration file
        :param prefix: prefix for output file
        :return:
        """
        if len(prefix) > 6:
            raise ValueError('prefix must not exceed 6 characters')
        ref = f'{prefix}-{self.hash()}'
        # Ensure input and output directories exist
        if not os.path.exists(path_to_file):
            os.makedirs(path_to_file)
        init_he60_output_directories(self.output_dir)
        filename = os.path.join(path_to_file, f'I{ref}.txt')
        with open(filename, 'w') as f:
            # Group 1: Default parameters
            par_min, par_max, phi_chl, raman0, raman_xs, idynz, raman_exp = 400, 700, 0.02, 488, 0.00026, 1, 5.3
            f.write(f'"{self.output_dir}", {par_min}, {par_max}, {phi_chl}, {raman0}, {raman_xs}, {idynz}, {raman_exp}\n')
            # Group 2 & 3: Run title and root name
            run_title = ref
            f.write(f'{run_title}\n')  # Max 120 characters
            run_name = ref
            f.write(f'{run_name}\n')  # Max 32 characters, no blanks, no special characters
            # Group 4: Output & Model Options
            iOptPrnt, iOptDigital, iOptExcelS, iOptExcelM, iOptRad = -1, 0, 0, 1, 0
            f.write(f'{iOptPrnt}, {iOptDigital}, {iOptExcelS}, {iOptExcelM}, {iOptRad}\n')
            iIOPmodel, iSkyRadModel, iSkyIrradModel, iChl, iCDOM, iIOPTS = 4, 1, 0, 2, 4, 1
            f.write(f'{iIOPmodel}, {iSkyRadModel}, {iSkyIrradModel}, {iChl}, {iCDOM}, {iIOPTS}\n')
            # Group 5: IOP Specification (NEW CASE 1 IOPs)
            ncomp, nconc = 3, 3
            f.write(f'{ncomp}, {nconc}\n')
            compconc_j, nconc = 0, 0
            f.write(f'{compconc_j}, {self.chlorophyll}, {nconc}\n')  # Constant concentration with depth
            # astar
            for itype, iastropt_i, astarRef_i, astar0_i, asgamma_i in ((0, 0, 440, 1, 0.014), ( 0, 1, 440, 1, 0.014), (0, 1, 440, 1, 0.014)):
                f.write(f'{itype}, {iastropt_i}, {astarRef_i}, {astar0_i}, {asgamma_i}\n')
            for astar_file in ['../data/H2OabsorpTS.txt', 'dummyastar.txt', 'dummyastar.txt']:
                f.write(f'{astar_file}\n')
            #bstar
            for ibstropt_i, bstarRef_i, bstar0_i, coef1, coef2, coef3 in ((0, -999, -999, -999, -999, -999), (1, -999, -999, -999, -999, -999), (0, -999, -999, -999, -999, -999)):
                f.write(f'{ibstropt_i}, {bstarRef_i}, {bstar0_i}, {coef1}, {coef2}, {coef3}\n')
            for bstar_file in ['bstarDummy.txt', 'dummybstar.txt', 'dummybstar.txt']:
                f.write(f'{bstar_file}\n')
            #phase function
            for ibbopt_i, bbfrac_i, BfrefPL_i, Bf0PL_i, BfmPL_i in ((0,0,550,0.01,0), (0,0,550,0.01,0), (0,0,550,0.01,0)):
                f.write(f'{ibbopt_i},{bbfrac_i},{BfrefPL_i},{Bf0PL_i},{BfmPL_i}\n')
            for phase_file in ['dpf_pure_H2O.txt', 'dpf_Morel_Case1_small.txt', 'dpf_Morel_Case1_large.txt']:
                f.write(f'{phase_file}\n')
            # Group 6: Wavelengths
            wavelengths = np.arange(self.wavelength_start - self.wavelength_step / 2,
                           self.wavelength_stop + self.wavelength_step + self.wavelength_step / 2,
                           self.wavelength_step)
            n_wavelengths = len(wavelengths) - 1
            if n_wavelengths > 500: # HydroLight6 limit
                raise ValueError(f"Number of wavelengths ({n_wavelengths}) exceeds HydroLight6 limit (500).")
            f.write(f'{n_wavelengths}\n')
            f.write(','.join(str(wl) for wl in wavelengths) + '\n')
            # Group 7: Inelastic Scattering and Internal Sources
            icompchl = 2
            f.write(f'{int(self.include_bioluminescence)},{int(self.include_chlorophyll_fluorescence)},'
                    f'{int(self.include_cdom_fluorescence)},{int(self.include_raman_scattering_by_water)},{icompchl}\n')
            # Group 8: Sky model
            # the “semi-analytic” sky model is being used, with solar zenith angle being specified
            iflagsky, nsky = 2, 3
            if self.sun_zenith_angle >= 89.5:
                raise ValueError('Sun zenith angle must be less than 85 degrees for the semi-analytic sky model.')
            f.write(f'{iflagsky}, {nsky}, {self.sun_zenith_angle:g}, '
                    f'{self.sun_azimuth_angle_relative_to_downwind_direction:g}, {self.cloud_cover:g}\n')
            if isinstance(self.day_of_year, int) and (1 <= self.day_of_year <= 365):
                jday = self.day_of_year
            elif self.day_of_year == 'annual_average':
                jday = -1
            else:
                raise ValueError('Day of year must be an integer between 1 and 365 or "annual_average".')
            rlat, rlon = 0, 0
            f.write(f'{jday}, {rlat}, {rlon}, {self.sea_level_pressure}, {self.airmass_type:d}, '
                    f'{self.relative_humidity:g}, {self.precipitable_water_content}, '
                    f'{self.horizontal_visibility:g}, {self.wind_speed:g}, {self.total_ozone_content:g}\n')
            # Group 9: Surface Information
            if isinstance(self.index_of_refraction_seawater, float) and self.index_of_refraction_seawater > 0:
                refr = self.index_of_refraction_seawater
            elif self.index_of_refraction_seawater == 'wavelength_dependent':
                refr = -1
            else:
                raise ValueError('Index of refraction of seawater must be a positive float or "wavelength_dependent".')
            iSurfaceModelFlag = 3  # sea surface model azimuthally averaged Cox-Munk surfaces is used
            f.write(f'{self.wind_speed:g}, {refr:g}, {self.temperature:g}, {self.salinity:g}, {iSurfaceModelFlag}\n')
            # Group 10: Bottom Relfectance
            ibotm, rflbot = 0, 0  # the water column is infinitely deep, used only if ibotm = 1
            f.write(f'{ibotm}, {rflbot}\n')
            # Group 11: Depths
            iop = 0  # geometric depths (in meters)
            nznom = len(self.output_depths)
            f.write(f'{iop}, {nznom}, {", ".join([str(d) for d in self.output_depths])}\n')
            # Group 12: Data files
            pure_water_data_file = '../data/H2OabsorpTS.txt'
            n_ac9_files = 1
            if self.uv_particle_absorption == 'low':
                uv_ap_file = 'AE_lowUVabs.txt'
            elif self.uv_particle_absorption == 'medium':
                uv_ap_file = 'AE_midUVabs.txt'
            elif self.uv_particle_absorption == 'high':
                uv_ap_file = 'AE_highUVabs.txt'
            else:
                raise ValueError('uv absorption must be low or medium.')
            data_files = [
                'dummyac9.txt',
                'dummyFilteredAc9.txt',
                'dummyHscat.txt',
                'dummyCHLdata.txt',
                'dummyCDOMdata.txt',
                'dummyR.bot',
                'dummyComp.txt',
                'dummyComp.txt',
                uv_ap_file,
                'DummyIrrad.txt',
                os.path.join(HE60_DATA, 'data', 'examples', 'So_biolum_user_data.txt'),
                'DummyRad.txt',
            ]
            f.write(f'{pure_water_data_file}\n')
            f.write(f'{n_ac9_files}\n')
            for dfile in data_files:
                f.write(f'{dfile}\n')
        return filename

    @classmethod
    def from_input_file(cls, filename):
        """
        Create Hyrolight6Input from existing HydroLight6 input file

        :param filename: path to HydroLight6 input file
        :return: Hyrolight6Input
        """
        with open(filename, 'r') as f:
            lines = f.readlines()
        hei = Hyrolight6Input()
        iop_spec_start, iop_spec_end = -9999, -9999
        n_wavelengths, ref = -1, '-'
        for idx, line in enumerate(lines):
            if idx == 0:
                # Group 1
                hei.output_dir = line.split(',')[0].strip().strip('"')
            elif idx == 1:
                # Group 2: Run title
                ref = line.strip()
            elif idx == 2:
                # Group 3: Run name
                pass
            elif 3 <= idx <= 4:
                # Group 4: Output & Model Options
                pass
            elif idx == 5:
                # Group 5: IOP Specification (NEW CASE 1 IOPs)
                ncomp, nconc = [int(v.strip()) for v in line.split(',')]
                iop_spec_start, iop_spec_end = 7, 7 + nconc * 2 + ncomp * 2 + ncomp * 2 - 1
            elif idx == 6:
                hei.chlorophyll = float(line.split(',')[1].strip())
            elif iop_spec_start <= idx <= iop_spec_end:
                # astar, nstar, phase function
                pass
            elif idx == iop_spec_end + 1:
                # Group 6: Wavelengths
                n_wavelengths = int(line.strip())
            elif idx == iop_spec_end + 2:
                wavelengths = [float(v.strip()) for v in line.split(',')]
                if n_wavelengths < 2:
                    raise ValueError('Wavelength configuration not supported. At least two wavelengths required.')
                step0 = wavelengths[1] - wavelengths[0]
                if np.any([step0 != step for step in np.diff(wavelengths)]):
                    raise ValueError('Wavelength configuration not supported. Only uniform spacing supported.')
                hei.wavelength_start = wavelengths[0] + step0 / 2
                hei.wavelength_stop = wavelengths[-1] - step0 / 2
                hei.wavelength_step = step0
            elif idx == iop_spec_end + 3:
                # Group 7: Inelastic Scattering and Internal Sources
                parts = [v.strip() for v in line.split(',')]
                hei.include_bioluminescence = bool(int(parts[0]))
                hei.include_chlorophyll_fluorescence = bool(int(parts[1]))
                hei.include_cdom_fluorescence = bool(int(parts[2]))
                hei.include_raman_scattering_by_water = bool(int(parts[3]))
            elif idx == iop_spec_end + 4:
                # Group 8: Sky model
                parts = [v.strip() for v in line.split(',')]
                hei.sun_zenith_angle = float(parts[2])
                hei.sun_azimuth_angle_relative_to_downwind_direction = float(parts[3])
                hei.cloud_cover = float(parts[4])
            elif idx == iop_spec_end + 5:
                parts = [v.strip() for v in line.split(',')]
                hei.day_of_year = int(parts[0]) if int(parts[0]) >= 0 else 'annual_average'
                hei.sea_level_pressure = float(parts[3])
                hei.airmass_type = int(parts[4])
                hei.relative_humidity = float(parts[5])
                hei.precipitable_water_content = float(parts[6])
                hei.horizontal_visibility = float(parts[7])
                # hei.wind_speed = float(parts[8])  # Prefer group 9 value
                hei.total_ozone_content = float(parts[9])
            elif idx == iop_spec_end + 6:
                # Group 9: Surface Information
                parts = [v.strip() for v in line.split(',')]
                hei.wind_speed = float(parts[0])  # could also be set from group 8
                hei.index_of_refraction_seawater = float(parts[1]) if float(parts[1]) > 0 else 'wavelength_dependent'
                hei.temperature = float(parts[2])
                hei.salinity = float(parts[3])
            elif idx == iop_spec_end + 7:
                # Group 10: Bottom Relfectance
                pass
            elif idx == iop_spec_end + 8:
                # Group 11: Depths
                parts = [v.strip() for v in line.split(',')]
                nznom = int(parts[1])
                hei.output_depths = [float(d) for d in parts[2:2 + nznom]]
            elif idx == iop_spec_end + 19:
                # Group 12: UV particle absorption
                uv_ap_file = line.strip()
                if uv_ap_file == 'AE_lowUVabs.txt':
                    hei.uv_particle_absorption = 'low'
                elif uv_ap_file == 'AE_midUVabs.txt':
                    hei.uv_particle_absorption = 'medium'
                elif uv_ap_file == 'AE_highUVabs.txt':
                    hei.uv_particle_absorption = 'high'
                else:
                    raise ValueError(f'UV particle absorption file not supported: {uv_ap_file}')
            else:
                # Group 12: More Data files
                pass
        if hei.hash() != ref.split('-')[1]:
            warnings.warn('Hash of parsed HydroLight6 input file does not match reference hash in filename.')
        return hei


def generate_input_files(dimensions: dict, defaults: dict=None, mode='individual',
                         input_dir=HE60_INPUT_DIR, prefix='pyhe60'):
    """
    Generate HydroLight6 input files for combinations of specified dimensions

    :param dimensions: dictionary of dimension name and values to use
    :param defaults: dictionary of default parameters to use, must not overlap with dimensions
    :param mode: 'product': all combinations, needed to build full LUT
                 'individual': vary one dimension at a time, recommended for exploration, default
    :param input_dir: HydroLight6 input file directory
    :param prefix: prefix for HydroLight6 input files
    :return: list of generated input filenames
    """
    if defaults is None:
        defaults = {}
    input_filenames = []
    if mode == 'product':
        combinations = list(itertools.product(*dimensions.values()))
        if len(combinations) > 10000:
            warnings.warn(f'Generating {len(combinations)} HydroLight6 input files. This may clutter your disk. Aborting.')
            return []
        for values in tqdm(combinations, desc='Generating HydroLight6 input files'):
            kwargs = {k: v for k, v in zip(dimensions.keys(), values)}
            i = Hyrolight6Input(**kwargs, **defaults)
            filename = i.write(input_dir, prefix=prefix)
            input_filenames.append(filename)
    elif mode == 'individual':
        for key, values in dimensions.items():
            for value in values:
                i = Hyrolight6Input(
                    # wavelength_start=310, wavelength_stop=790, wavelength_step=20, output_depths=output_depth,
                    **{key: value}, **defaults
                )
                filename = i.write(input_dir, prefix=prefix)
                input_filenames.append(filename)
    else:
        raise ValueError(f'Invalid mode: {mode}. Supported modes are "product" and "individual".')
    return input_filenames


# %% -- Read HydroLight 6.0 M-Outputs -- %% #

def read_m_xlsx(filename, keys=None):
    """
    Read M*.xlsx files output by HydroLight 6
    :param filename: filenames
    :param keys: sheets to read from Excel file
    :return: pd.DataFrame
    """
    if keys is None:
        keys = ['Rrs', 'Lu', 'Ed', 'Kd', 'KLu']
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        xlsx = pd.ExcelFile(filename)
        out = {}
        for sheet_name in keys:
            df = pd.read_excel(xlsx, sheet_name, header=3, index_col=0)
            out[sheet_name] = df.T
            out[sheet_name].index.name = 'variable' if sheet_name == 'Rrs' else 'depth'
    return out


def read_multi_m_xslx(varname='KLu', z_ref=None, prefix='pyhe60',
                      input_dir=HE60_INPUT_DIR, output_dir=HE60_OUTPUT_DIR):
    """
    Read all output files from HydroLight6 batch run

    :param varname: variable to extract (e.g. KLu, Rrs, Lu, Ed, Kd)
    :param z_ref: depth to extract variable at, if None load entire profile (m)
    :param prefix: prefix of output files
    :param input_dir: directory with HydroLight6 input files
    :param output_dir: directory with HydroLight6 output files
    :return:
    """
    defaults = Hyrolight6Input().__dict__
    for k in ['output_depths', 'output_dir', 'wavelength_start', 'wavelength_stop', 'wavelength_step']:
        del defaults[k]
    foo = ['wl', 'z', varname] if z_ref is None else ['wl', varname]
    z_value = z_ref
    df = {k: [] for k in ['ref'] + list(defaults.keys()) + foo}
    for output_filename in tqdm(sorted(glob.glob(os.path.join(output_dir, f'M{prefix}-*.xlsx'))), desc='Reading HE60'):
        ref = os.path.basename(output_filename).lstrip("M").rstrip(".xlsx")
        # Read input file
        input_filename = os.path.join(input_dir, f'I{ref}.txt')
        cfg = Hyrolight6Input.from_input_file(input_filename)
        df['ref'].append(ref)
        for k in defaults.keys():
            df[k].append(getattr(cfg, k))
        # Read M output file
        m = read_m_xlsx(output_filename)
        df['wl'].append(m[varname].columns.to_numpy(dtype=float))
        z = m[varname].rename(index={'in air': -1111}).index.to_numpy(dtype=float)
        if z_ref is None:
            df['z'].append(z)
            df[varname].append(m[varname].to_numpy(dtype=np.float32))
        else:
            if z_ref == 'in air':
                if 'in air' in m[varname].index:
                    z_idx, z_value = 0, z_ref
                else:
                    raise ValueError(f'{ref}: No "in air" data found for {varname} in HydroLight6 output.')
            else:
                z_idx = np.argmin(np.abs(z - z_ref))
                z_value = z[z_idx]
            df[varname].append(m[varname].iloc[z_idx, :].to_numpy(dtype=np.float32))
    if z_ref is None:
        return pd.DataFrame(df)
    else:
        return pd.DataFrame(df), z_value
