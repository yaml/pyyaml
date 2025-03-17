import yaml


class MyDumper(yaml.CDumper):
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


def represent1(representer, native):
    return representer.represent_mapping("!tag1", native.__dict__)


def test_default_representers_registered():
    obj = [("hello", "world")]

    yamlcode = yaml.dump(obj, Dumper=yaml.CDumper)
    assert yamlcode == """\
- !!python/tuple
  - hello
  - world
"""


def test_representer_registration():
    yaml.add_representer(MyTestClass1, represent1, Dumper=MyDumper)

    obj = [MyTestClass1(x=1), MyTestClass1(x=1, y=2, z=3)]

    yamlcode = yaml.dump(obj, Dumper=MyDumper)
    assert yamlcode == """\
- !tag1
  x: 1
  y: 0
  z: 0
- !tag1
  x: 1
  y: 2
  z: 3
"""
    del MyDumper.yaml_representers()[MyTestClass1]
