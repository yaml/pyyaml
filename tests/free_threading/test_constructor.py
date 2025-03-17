import io

import yaml


class MyLoader(yaml.CLoader):
    pass


class MyTestClass1:
    def __init__(self, x, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        if isinstance(other, MyTestClass1):
            return self.__class__, self.__dict__ == other.__class__, other.__dict__
        else:
            return False

    def __repr__(self):
        return f"MyTestClass1(x={self.x}, y={self.y}, z={self.z})"


def construct1(constructor, node):
    mapping = constructor.construct_mapping(node)
    return MyTestClass1(**mapping)


def test_default_constructors_registered():
    yamlcode = io.StringIO("""\
- !!python/tuple [hello, world]
""")

    objs = yaml.load(yamlcode, Loader=yaml.CLoader)
    assert objs == [("hello", "world")]


def test_constructor_registration():
    yaml.add_constructor("!tag1", construct1, Loader=MyLoader)

    yamlcode = io.StringIO("""\
- !tag1
  x: 1
- !tag1
  x: 1
  'y': 2
  z: 3
""")

    objs = yaml.load(yamlcode, Loader=MyLoader)
    assert objs == [MyTestClass1(x=1), MyTestClass1(x=1, y=2, z=3)]
    del MyLoader.yaml_constructors()["!tag1"]
