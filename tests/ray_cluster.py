import os
import socket
from time import perf_counter
from statistics import stdev

import ray
from tqdm import tqdm


# Replace with the actual IP and client port of your head node (or use environment variables)
head_node_ip = os.environ.get("HEAD_NODE_IP", '127.0.0.1')
head_node_client_port = os.environ.get("HEAD_NODE_PORT", '10001')
head_node_address = f"ray://{head_node_ip}:{head_node_client_port}"
print(f"Connecting to Ray cluster at {head_node_address}")
ray.init(head_node_address)


@ray.remote
def prime_test(limit=1_000_000, timeout=30):
    """
    Simple CPU-bound task to test Ray cluster performance.
    Calculates prime numbers up to a limit or until timeout.

    :param limit: maximum number to check for primality (default: 1,000,000)
    :param timeout: max run time in seconds (default: 30 seconds)
    :return:
    """
    # Find prime numbers
    start_time = perf_counter()
    primes, x = [], 2
    while x < limit and perf_counter() - start_time < timeout:
        x += 1
        if all(x % i != 0 for i in range(2, int(x ** 0.5) + 1)):
            primes.append(x)
    # Return message
    return {'hostname': socket.gethostname(), 'duration': perf_counter() - start_time}


# Execute the task across the cluster
futures = [prime_test.remote() for _ in range(100)]
results = [ray.get(f) for f in tqdm(futures, desc="Processing Cluster Tasks")]

# Display statistics by node
summary = {}
for r in results:
    if r['hostname'] in summary:
        summary[r['hostname']].append(r['duration'])
    else:
        summary[r['hostname']] = [r['duration']]
for hostname, durations in summary.items():
    avg_duration = sum(durations) / len(durations)
    std_error = stdev(durations) if len(durations) > 1 else 0
    print(f"Node: {hostname}, Tasks: {len(durations)}, Avg Duration: {avg_duration:.2f} ± {std_error:.2f} seconds")
