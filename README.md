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

### Advanced: Using Ray for distributed computing
For generating look-up tables across a large parameter space, you can leverage Ray for distributed computing. First, install Ray on your local machine:

    uv pip install 'ray[default]'

Setup cluster (assumes uv is installed), on each node (including head node). 

    # Install HydroLight 6.0 on each node
    scp /Applications/HE60.app/Contents/data user@node:~/he60/
    scp /Applications/HE60.app/Contents/source_code user@node:~/he60/
    sudo apt install gfortran
    cd ~/he60/source_code/HydroLight_code
    chmod 754 make_HydroLight6.sh
    ./make_HydroLight6.sh
    mv ~/he60/source_code/build_linux/HydroLight6 /usr/local/bin/

    # Create a virtual environment for Ray (adjust python version as needed, install pip as uses python from uv and required by ray)
    mkdir ray_worker
    cd ray_worker
    uv venv --python 3.13.11  
    uv pip install pip    
    uv pip install 'ray[default]'
    
    # Adjust firewall settings one every node to allow Ray communication (example for Linux)
    sudo ufw allow from <IP_RANGE> to any port 60000:61000 proto tcp comment "Ray Services"
    sudo ufw allow from <IP_RANGE> to any port 6379 proto tcp comment "Ray Monitoring"

    # Adjust firewall settings on head node to allow Ray Dashboard & Client access (example for Linux)
    sudo ufw allow from <IP_RANGE> to any port 8265 proto tcp comment "Ray Dashboard"
    sudo ufw allow from <IP_RANGE> to any port 10001 proto tcp comment "Ray Client"

    # Start Ray cluster (on head node)
    uv run ray start --head --port=6379 --object-manager-port=60000 --node-manager-port=60001 --min-worker-port=60002 --max-worker-port=61000 --dashboard-host 0.0.0.0
    # Join worker nodes to cluster (on each worker node)
    uv run ray start --address='<HEAD_NODE_IP>:6379' --object-manager-port=60000 --node-manager-port=60001 --min-worker-port=60002 --max-worker-port=61000

Test cluster is working from local computer
    
    export HEAD_NODE_IP=<HEAD_NODE_IP>
    uv run python3 tests/ray_cluster.py
    uv run python3 tests/ray_venv.py

## Usage
### Running simulations
This example demonstrates how to run HydroLight simulations with different parameters using pyhe60 and plots the results.
    
    python examples/explore_parameter_space.py

### Generating a look-up table
This example shows how to generate a look-up table by running multiple HydroLight simulations across a parameter space. This leverage all cores available on the machine.
    
    python examples/make_lut.py

### Generating a look-up table with Ray
This example demonstrates how to generate a look-up table using Ray for distributed computing across multiple nodes. Ensure your Ray cluster is set up and running before executing the commands below. Make sure to adjust the `HEAD_NODE_IP` variable to point to your Ray cluster's head node.

    export HEAD_NODE_IP=<HEAD_NODE_IP>
    python examples/make_lut_distributed_ray.py
