import concurrent
import random
import re
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


NUM_THREADS = 8
NUM_ITERATIONS = 200
barrier = threading.Barrier(NUM_THREADS)


class Dice(tuple):
    def __new__(cls, a, b):
        return tuple.__new__(cls, (a, b))

    def __repr__(self):
        return "Dice(%s,%s)" % self


def dice_constructor(loader, node):
    value = loader.construct_scalar(node)
    a, b = map(int, value.split('d'))
    return Dice(a, b)


# Different YAML content types for testing
YAML_LOAD_SAMPLES = [
    # Simple key-value pairs
    ("""\
key1: value1
key2: value2
key3: 123
key4: true
""", {
        "key1": "value1",
        "key2": "value2",
        "key3": 123,
        "key4": True
    }),
    
    # Nested structures
    ("""\
config:
  database:
    host: localhost
    port: 5432
    credentials:
      username: admin
      password: secret
  logging:
    level: INFO
    file: /var/log/app.log
""", {
        "config": {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {
                    "username": "admin",
                    "password": "secret"
                }
            },
            "logging": {
                "level": "INFO",
                "file": "/var/log/app.log"
            }
        }
    }),

    # Lists
    ("""\
fruits:
  - apple
  - banana
  - orange
numbers: [1, 2, 3, 4, 5]
mixed:
  - name: John
    age: 30
  - name: Alice
    age: 25
""", {
        "fruits": ["apple", "banana", "orange"],
        "numbers": [1, 2, 3, 4, 5],
        "mixed": [
            {"name": "John", "age": 30},
            {"name": "Alice", "age": 25}
        ]
    }),
    
    # Complex with references
    ("""\
defaults: &defaults
  adapter: postgresql
  host: localhost

development:
  database: myapp_development
  <<: *defaults

test:
  database: myapp_test
  <<: *defaults
""", {
        "defaults": {
            "adapter": "postgresql",
            "host": "localhost"
        },
        "development": {
            "database": "myapp_development",
            "adapter": "postgresql",
            "host": "localhost"
        },
        "test": {
            "database": "myapp_test",
            "adapter": "postgresql",
            "host": "localhost"
        }
    }),

    # Dice with resolver
    ("""\
rolls_resolver:
  - 1d6
  - 2d4
  - 3d1
""", {
        "rolls_resolver": [
            Dice(1, 6),
            Dice(2, 4),
            Dice(3, 1)
        ]
    }),
]


class MyLoader(Loader):
    pass


class MyDumper(Dumper):
    pass


def yaml_load_stress_thread():
    for _ in range(NUM_ITERATIONS):
        barrier.wait()
        yamlcode, result = random.choice(YAML_LOAD_SAMPLES)
        thread_id = threading.current_thread().name
        randint = random.randint(1, 1000)
        yamlcode += f"\nrandom_value_{thread_id}: {randint}"
        obj = yaml.load(yamlcode, Loader=MyLoader)
        assert obj == {**result, f"random_value_{thread_id}": randint}


def test_yaml_load_stress():
    yaml.add_constructor("!dice", dice_constructor, Loader=MyLoader)
    yaml.add_implicit_resolver('!dice', re.compile(r'^\d+d\d+$'),
                                Loader=MyLoader, Dumper=MyDumper)

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [executor.submit(yaml_load_stress_thread) for _ in range(NUM_THREADS)]
        for future in concurrent.futures.as_completed(futures):
            future.result()
