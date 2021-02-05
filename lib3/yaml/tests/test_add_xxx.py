# coding: utf-8

import re

import pytest  # NOQA
from .roundtrip import dedent


# from PyYAML docs
class Dice(tuple):
    def __new__(cls, a, b):
        return tuple.__new__(cls, [a, b])

    def __repr__(self):
        return 'Dice(%s,%s)' % self


def dice_constructor(loader, node):
    value = loader.construct_scalar(node)
    a, b = map(int, value.split('d'))
    return Dice(a, b)


def dice_representer(dumper, data):
    return dumper.represent_scalar(u'!dice', u'{}d{}'.format(*data))


def test_dice_constructor():
    import yaml  # NOQA

    yaml.add_constructor(u'!dice', dice_constructor)
    data = yaml.load('initial hit points: !dice 8d4', Loader=yaml.Loader)
    assert str(data) == "{'initial hit points': Dice(8,4)}"


def test_dice_constructor_with_loader():
    import yaml  # NOQA

    yaml.add_constructor(u'!dice', dice_constructor, Loader=yaml.Loader)
    data = yaml.load('initial hit points: !dice 8d4', Loader=yaml.Loader)
    assert str(data) == "{'initial hit points': Dice(8,4)}"


def test_dice_representer():
    import yaml  # NOQA

    yaml.add_representer(Dice, dice_representer)
    assert (
        yaml.dump(dict(gold=Dice(10, 6)), default_flow_style=False)
        == 'gold: !dice 10d6\n'
    )


def test_dice_implicit_resolver():
    import yaml  # NOQA

    pattern = re.compile(r'^\d+d\d+$')
    yaml.add_implicit_resolver(u'!dice', pattern)
    assert (
        yaml.dump(dict(treasure=Dice(10, 20)), default_flow_style=False)
        == 'treasure: 10d20\n'
    )
    assert yaml.load('damage: 5d10', Loader=yaml.Loader) == dict(damage=Dice(5, 10))


class Obj1(dict):
    def __init__(self, suffix):
        self._suffix = suffix
        self._node = None

    def add_node(self, n):
        self._node = n

    def __repr__(self):
        return 'Obj1(%s->%s)' % (self._suffix, self.items())

    def dump(self):
        return repr(self._node)


class YAMLObj1:
    yaml_tag = u'!obj:'

    @classmethod
    def from_yaml(cls, loader, suffix, node):
        import yaml  # NOQA

        obj1 = Obj1(suffix)
        if isinstance(node, yaml.MappingNode):
            obj1.add_node(loader.construct_mapping(node))
        else:
            raise NotImplementedError
        return obj1

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag + data._suffix, data.dump())


def test_yaml_obj():
    import yaml  # NOQA

    yaml.add_representer(Obj1, YAMLObj1.to_yaml)
    yaml.add_multi_constructor(YAMLObj1.yaml_tag, YAMLObj1.from_yaml)
    x = yaml.load('!obj:x.2\na: 1', Loader=yaml.Loader)
    print(x)
    assert yaml.dump(x) == """!obj:x.2 "{'a': 1}"\n"""


def test_yaml_obj_with_loader_and_dumper():
    import yaml  # NOQA

    yaml.add_representer(Obj1, YAMLObj1.to_yaml, Dumper=yaml.Dumper)
    yaml.add_multi_constructor(
        YAMLObj1.yaml_tag, YAMLObj1.from_yaml, Loader=yaml.Loader
    )
    x = yaml.load('!obj:x.2\na: 1', Loader=yaml.Loader)
    print(x)
    assert yaml.dump(x) == """!obj:x.2 "{'a': 1}"\n"""

