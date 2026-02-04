# pyhe60

A Python package for working with HydroLight EcoLight 6.0 (HE60) radiative transfer model. It provides tools for generating input files, running simulations, reading output (M-files), and generating look-up tables (LUTs).

The only Inherent Optical Property (IOP) model currently supported by `pyhe60` is: __New Case 1 IOPs__ (IOPs are obtained from recent bio-optical models for Case 1 water).


## Installation
This project was developed on macOS and will likely run on Linux and Windows with minor adjustements. Ensure HydroLight EcoLight 6.0 is installed and available on your system. For enhanced performance on Macs with M chips, recompile HydroLight (the version provided runs with Rosetta).

### Using uv (recommended)
Create and sync the environment from the lock file:

    uv venv .venv
    source .venv/bin/activate
    uv sync

For optional dependencies required for plotting (plotly) and look-up table generation (netCDF4), install all extras:

    uv sync --all-extras

Or install specific extras:

    uv sync --extra lut --extra plot

Verify installation

    uv run python -c "import pyhe60; print(f'Path: {pyhe60.__file__}'); print(f'Sub-modules: {pyhe60.__path__}')"

### Using pip
Create a virtual environment and install the package:

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    pip install -e .

For optional dependencies, required for plotting (plotly) and look-up table generation (netCDF4), install all extras:

    pip install -e ".[lut,plot]"

Verify installation

    python -c "import pyhe60; print(pyhe60.__version__)"

## Usage
### Running simulations
This example demonstrates how to run HydroLight simulations with different parameters using pyhe60 and plots the results.
    
    python examples/explore_parameter_space.py

### Generating a look-up table
This example shows how to generate a look-up table by running multiple HydroLight simulations across a parameter space. This leverage all cores available on the machine.
    
    python examples/make_lut.py

