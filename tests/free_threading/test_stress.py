import random
import re
import threading

import yaml


class Dice(tuple):
    def __new__(cls, a, b):
        return tuple.__new__(cls, (a, b))

    def __repr__(self):
        return "Dice(%s,%s)" % self


def dice_constructor(loader, node):
    value = loader.construct_scalar(node)
    a, b = map(int, value.split('d'))
    return Dice(a, b)


def dice_representer(dumper, data):
    return dumper.represent_scalar("!dice", "%sd%s" % data)


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

    # Dice without resolver
    ("""\
rolls_no_resolver:
  - 1d6
  - 2d4
  - 3d1
""", {
        "rolls_no_resolver": [
            "1d6",
            "2d4",
            "3d1"
        ]
    }),
]


class MyLoader(yaml.CLoader):
    pass


class MyDumper(yaml.CDumper):
    pass


def test_yaml_load_stress():
    yamlcode, result = random.choice(YAML_LOAD_SAMPLES)
    thread_id = threading.current_thread().name
    randint = random.randint(1, 1000)
    yamlcode += f"\nrandom_value_{thread_id}: {randint}"


    constructor, resolver = False, False
    if yamlcode.startswith("rolls"):
        yaml.add_constructor("!dice", dice_constructor, Loader=MyLoader)
        constructor = True
        if yamlcode.startswith("rolls_resolver"):
            yaml.add_implicit_resolver('!dice', re.compile(r'^\d+d\d+$'),
                                        Loader=MyLoader, Dumper=MyDumper)
            resolver = True

    obj = yaml.load(yamlcode, Loader=MyLoader)
    assert obj == {**result, f"random_value_{thread_id}": randint}
    if constructor:
        del MyLoader.yaml_constructors()["!dice"]
    if resolver:
        del MyLoader.yaml_implicit_resolvers()[None]
