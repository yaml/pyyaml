import concurrent.futures
import random
import threading

import yaml as yaml

try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader



NUM_FILES = 200
NUM_THREADS = 8
ERROR_RATE = 0.1

barrier = threading.Barrier(NUM_THREADS)


def _generate_random_github_workflow():
    """Generate a random GitHub Actions workflow-like YAML structure."""
    workflow = {
        "name": f"Test Workflow {random.randint(1, 1000)}",
        "on": ["push", "pull_request"],
        "jobs": {
            "build": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {
                        "name": "Checkout",
                        "uses": "actions/checkout@v3"
                    },
                    {
                        "name": "Setup Python",
                        "uses": "actions/setup-python@v4",
                        "with": {
                            "python-version": random.choice(["3.8", "3.9", "3.10", "3.11"])
                        }
                    },
                    {
                        "name": "Run tests",
                        "run": "pytest"
                    }
                ]
            }
        }
    }
    
    # Add some randomness to the structure
    if random.random() > 0.5:
        workflow["jobs"]["deploy"] = {
            "runs-on": "ubuntu-latest",
            "needs": ["build"],
            "steps": [
                {
                    "name": "Deploy step",
                    "run": "echo Deploying..."
                }
            ]
        }
    
    return workflow


def _create_yaml_file(directory, index, valid=True):
    barrier.wait()

    filepath = directory / f"workflow_{index}.yml"
    workflow = _generate_random_github_workflow()
    with open(filepath, 'w') as f:
        if valid:
            yaml.dump(workflow, f, Dumper=Dumper)
        else:
            # Introduce an error in the YAML structure
            f.write("name: Invalid Workflow\non: [push\njobs:")
    return filepath, workflow, valid


def _parse_yaml_file(filepath, original_data, expected_valid):
    barrier.wait()

    try:
        with open(filepath, 'r') as f:
            data = yaml.load(f, Loader=Loader)
        assert expected_valid and data == original_data
    except yaml.YAMLError:
        assert not expected_valid


def test_multithreaded_yaml_parsing(tmp_path):
    # Create test files in threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [
            executor.submit(_create_yaml_file, tmp_path, i, random.random() > ERROR_RATE)
            for i in range(NUM_FILES)
        ]
        
        file_info = []
        for future in concurrent.futures.as_completed(futures):
            filepath, workflow, valid = future.result()
            file_info.append((filepath, workflow, valid))

    # Parse files using thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        future_to_file = [
            executor.submit(_parse_yaml_file, filepath, workflow, valid)
            for filepath, workflow, valid in file_info
        ]
        for future in concurrent.futures.as_completed(future_to_file):
            future.result()  # Asserts that this does not raise any assertion errors
