import numpy as np
from plotly.express.colors import sample_colorscale
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from .io import Hyrolight6Input

cp_long_name = {
    'sun_zenith_angle': 'Sun Zenith Angle', 'chlorophyll': 'Chlorophyll Concentration',
    'temperature': 'Water Temperature', 'salinity': 'Salinity',
    'uv_particle_absorption': 'UV Particle Absorption Coefficient',
    'include_raman_scattering_by_water': 'Include Raman Scattering by Water', 'wind_speed': 'Wind Speed',
    'sun_azimuth_angle_relative_to_downwind_direction': 'Sun Azimuth Angle Relative to Downwind Direction',
    'sea_level_pressure': 'Sea Level Pressure','relative_humidity': 'Relative Humidity',
    'total_ozone_content': 'Total Ozone Content',
    'airmass_type': 'Airmass Type','day_of_year': 'Day of Year'
}

cp_short_name = {
    'sun_zenith_angle': 'SZA', 'chlorophyll': 'CHL', 'temperature': 'TEMP', 'salinity': 'SAL',
    'uv_particle_absorption': 'UVABS',
    'include_raman_scattering_by_water': 'wRAMAN', 'wind_speed': 'WIND',
    'sun_azimuth_angle_relative_to_downwind_direction': 'SAARDT',
    'sea_level_pressure': 'ATMPRES','relative_humidity': 'RH','total_ozone_content': 'TO3',
    'airmass_type': 'AIRTYPE','day_of_year': 'DOY'
}
cp_units = {
    'sun_zenith_angle': '°', 'chlorophyll': 'µg L<sup>-1</sup>', 'salinity': 'PSU', 'temperature': '°C',
    'uv_particle_absorption': '',
    'include_raman_scattering_by_water': '', 'wind_speed': 'm/s',
    'sun_azimuth_angle_relative_to_downwind_direction': '°',
    'sea_level_pressure': 'inHg', 'relative_humidity': '%', 'total_ozone_content': 'DU',
    'airmass_type': '', 'day_of_year': ''
}
sv_long_name = {
    'Ed': 'Downwelling Irradiance',
    'Lu': 'Upward Radiance',
    'Rrs': 'Remote Sensing Reflectance',
    'Kd': 'Downwelling Attenuation Coefficient',
    'KLu': 'Upward Attenuation Coefficient'
}
sv_short_name = {
    'Ed': 'E<sub>d</sub>',
    'Lu': 'L<sub>u</sub>',
    'Rrs': 'R<sub>rs</sub>',
    'Kd': 'K<sub>d</sub>',
    'KLu': 'K<sub>Lu</sub>'
}
sv_units = {
    'Ed': f'W m<sup>-2</sup> nm<sup>-1</sup>',
    'Lu': f'W m<sup>-2</sup> sr<sup>-1</sup> nm<sup>-1</sup>',
    'Rrs': f'sr<sup>-1</sup>',
    'Kd': f'm<sup>-1</sup>',
    'KLu': 'm<sup>-1</sup>'
}


defaults = Hyrolight6Input().__dict__
for k in ['wavelength_start', 'wavelength_stop', 'wavelength_step', 'output_depths', 'output_dir']:
    del defaults[k]


def plot_spectrum(df, control_parameter, spectral_variable, colorscale='viridis'):
    """
    Plot spectral variable as function of wavelength for different values of control parameter.

    :param df: dataframe, recommend subsetting varying only with control_parameter (use get_subset)
    :param control_parameter: control parameter name
    :param spectral_variable: spectral variable name
    :param colorscale: colorscale name (default 'viridis')
    :return: plotly figure
    """
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, )
    r0, r0_param_value = 0, None
    for i, r in df.iterrows():
        fig.add_scatter(x=r['wl'], y=r[spectral_variable], name=f'{cp_short_name[control_parameter]}: {r[control_parameter]:g}',
                        mode='lines', line_color=sample_colorscale(colorscale, i / (len(df) - 1))[0],
                        legendgroup=i, row=1, col=1)
        if i == 0:
            r0 = r[spectral_variable]
            r0_param_value = r[control_parameter]
            continue
        fig.add_scatter(x=r['wl'], y=(r[spectral_variable] - r0) / (0.5 * (r0 + r[spectral_variable])),
                        mode='lines', line_color=sample_colorscale(colorscale, i / (len(df) - 1))[0],
                        showlegend=False, legendgroup=i, row=2, col=1)
    fig.update_xaxes(showticklabels=True, showgrid=True, zeroline=True, row=1, col=1)
    fig.update_xaxes(title='Wavelength (nm)', showgrid=True, zeroline=True, row=2, col=1)
    fig.update_yaxes(title=f'{sv_short_name[spectral_variable]} ({sv_units[spectral_variable]})', showgrid=True, zeroline=True, row=1, col=1)
    fig.update_yaxes(title=f'Relative Difference wrt {cp_short_name[control_parameter]}={r0_param_value}', showgrid=True, zeroline=True, row=2,
                     col=1)
    fig.update_layout(title=f"{cp_long_name[control_parameter]}", legend_tracegroupgap=0)
    if len(df) > 24:
        fig.update_layout(legend_orientation='h')
    return fig


def plot_property(df, control_parameter, spectral_variable, target_wavelengths=None):
    """
    Plot spectral variable at target wavelengths as function of control parameter.

    :param df: dataframe, recommend subsetting varying only with control_parameter (use get_subset)
    :param control_parameter: control parameter name
    :param spectral_variable: spectral variable name
    :param target_wavelengths: target wavelengths to plot
    :return: plotly figure
    """
    if target_wavelengths is None:
        target_wavelengths = [412, 443, 490, 555, 640, 670, 750]
    wl0_idx = len(target_wavelengths) // 2
    fig = go.Figure()
    for wl in target_wavelengths:
        wl_idx = np.argmin(np.abs(df['wl'].iloc[0] - wl))
        color = wavelength_to_rgb(wl)
        fig.add_scatter(x=df[control_parameter], y=[r[spectral_variable][wl_idx] for _, r in df.iterrows()],
                        visible=True if wl == target_wavelengths[wl0_idx] else 'legendonly',
                        marker_color=color, mode='lines+markers', name=f'{spectral_variable}({wl}) nm')
    fig.update_xaxes(title=f'{cp_long_name[control_parameter]} ({cp_units[control_parameter]})', showgrid=True, zeroline=True)
    fig.update_yaxes(title=f'{sv_short_name[spectral_variable]} ({sv_units[spectral_variable]})', showgrid=True, zeroline=True)
    fig.update_layout(legend_tracegroupgap=0)
    return fig


def select_subset(df, control_parameter, verbose=False):
    """
    Return a subset of the dataframe varying only with the control_parameter, other variables set to default.

    :param df: pandas dataframe
    :param control_parameter: only variable parameter, others will be kept at default values
    :return: return subset of dataframe
    """
    sel = np.ones(len(df), dtype=bool)
    for k, v in defaults.items():
        if k == control_parameter:
            continue
        sel &= (df[k] == v)
        if verbose:
            print(f'{k}={v} n={np.sum(sel)}')
    return df[sel].sort_values(by=[control_parameter], ascending=True).reset_index()


def wavelength_to_rgb(wavelength, gamma=0.8):
    """
    This converts a given wavelength of light to an
    approximate RGB color value. The wavelength must be given
    in nanometers in the range from 380 nm through 750 nm
    (789 THz through 400 THz).

    Reference: Dan Bruton, http://www.physics.sfasu.edu/astro/color/spectra.html

    :param wavelength: Wavelength in nanometers
    :param gamma: Gamma correction factor
    :return: (R, G, B) tuple with values from 0 to
    """
    wavelength = float(wavelength)
    if 380 <= wavelength <= 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        r = ((-(wavelength - 440) / (440 - 380)) * attenuation) ** gamma
        g = 0.0
        b = (1.0 * attenuation) ** gamma
    elif 440 <= wavelength <= 490:
        r = 0.0
        g = ((wavelength - 440) / (490 - 440)) ** gamma
        b = 1.0
    elif 490 <= wavelength <= 510:
        r = 0.0
        g = 1.0
        b = (-(wavelength - 510) / (510 - 490)) ** gamma
    elif 510 <= wavelength <= 580:
        r = ((wavelength - 510) / (580 - 510)) ** gamma
        g = 1.0
        b = 0.0
    elif 580 <= wavelength <= 645:
        r = 1.0
        g = (-(wavelength - 645) / (645 - 580)) ** gamma
        b = 0.0
    elif 645 <= wavelength <= 750:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        r = (1.0 * attenuation) ** gamma
        g = 0.0
        b = 0.0
    else:
        r = 0.0
        g = 0.0
        b = 0.0
    r *= 255
    g *= 255
    b *= 255
    return f'rgb({r:.0f}, {g:.0f}, {b:.0f})'
