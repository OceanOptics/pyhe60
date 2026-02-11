import os
import socket
import sys

import ray
from tqdm import tqdm


# Replace with the actual IP and client port of your head node (or use environment variables)
head_node_ip = os.environ.get("HEAD_NODE_IP", '127.0.0.1')
head_node_client_port = os.environ.get("HEAD_NODE_PORT", '10001')
head_node_address = f"ray://{head_node_ip}:{head_node_client_port}"
print(f"Connecting to Ray cluster at {head_node_address}")

dependencies = [
    "numpy>=2.4.2",
    "openpyxl>=3.1.5",
    "pandas>=3.0.0",
    "netcdf4>=1.7.4",
    "tqdm>=4.67.3",
]

current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, '..', 'src'))
print(f"Targeting src at: {src_path}")

ray.init(
    head_node_address,
    runtime_env={
        'pip': dependencies,
        'py_modules': [os.path.join(src_path, 'pyhe60')],
        'env_vars': {
            # 'PYTHONPATH': 'src:.',  # Tell python to look one level deeper for pyhe60
            'RAY_IGNORE_COMMAND_LINE_VALIDATION': '1'
        },
        # 'py_executable': 'uv run --active',
    },
)


@ray.remote
def check_node():
    """
    Run a single HydroLight run to ensure dependencies are properly imported and HydroLight is installed on the nodes.

    :return:
    """
    # Find prime numbers
    success, error_msg = False, ''
    try:
        import pyhe60 as he
        from pyhe60.utils import init_he60_output_directories

        i = he.Hyrolight6Input(wavelength_step=50)
        input_file = i.write(prefix=ray.get_runtime_context().get_task_id()[:6])
        init_he60_output_directories(i.output_dir)
        he.run_he60(input_file, verbose=True)

        success = True
    except ImportError as e:
        error_msg = str(e)
    # Return message
    msg = {
        'hostname': socket.gethostname(),
        # 'node_id': ray.get_runtime_context().get_node_id(),
        'python_version': sys.version,
        # 'sys_path': sys.path,
        'cwd': os.getcwd(),
        # 'files_in_cwd': os.listdir('.'),
    }
    if success:
        msg['success'] = True
    if error_msg:
        msg['error'] = error_msg
    return msg


# Execute the task across the cluster
futures = [check_node.remote() for _ in range(2)]
results = [ray.get(f) for f in tqdm(futures, desc="Processing Cluster Tasks")]

# Display statistics by node
printed = []
for r in results:
    if r['hostname'] not in printed:
        print(r)
        printed.append(r['hostname'])
