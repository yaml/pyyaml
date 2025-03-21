import re
import yaml


class Dice(tuple):
    def __new__(cls, a, b):
        return tuple.__new__(cls, (a, b))

    def __repr__(self):
        return "Dice(%s,%s)" % self


def dice_representer(dumper, data):
    return dumper.represent_scalar("!dice", "%sd%s" % data)


def _convert_node(node):
    if isinstance(node, yaml.ScalarNode):
        return (node.tag, node.value)
    elif isinstance(node, yaml.SequenceNode):
        value = []
        for item in node.value:
            value.append(_convert_node(item))
        return (node.tag, value)
    elif isinstance(node, yaml.MappingNode):
        value = []
        for key, item in node.value:
            value.append((_convert_node(key), _convert_node(item)))
        return (node.tag, value)


def test_default_implicit_resolvers_registered():
    yamlcode = """\
- [1, 2, 3]
- 2
"""

    node = yaml.compose(yamlcode, Loader=yaml.CLoader)
    assert isinstance(node, yaml.SequenceNode)
    assert isinstance(node.value[0], yaml.SequenceNode)
    for scalar in node.value[0].value:
        assert isinstance(scalar, yaml.ScalarNode)
        assert scalar.tag == 'tag:yaml.org,2002:int'
    assert isinstance(node.value[1], yaml.ScalarNode)
    assert node.value[1].tag == 'tag:yaml.org,2002:int'


class ImplicitResolverLoader(yaml.CLoader):
    pass


class ImplicitResolverDumper(yaml.CDumper):
    pass


def test_implicit_resolver_registration():
    yaml.add_representer(Dice, dice_representer, Dumper=ImplicitResolverDumper)
    yaml.add_implicit_resolver('!dice', re.compile(r'^\d+d\d+$'), Loader=ImplicitResolverLoader, Dumper=ImplicitResolverDumper)

    yamlcode = """\
- 1d4
- 2d6
- 3d8
"""
    node = yaml.compose(yamlcode, Loader=ImplicitResolverLoader)
    assert isinstance(node, yaml.SequenceNode)
    for scalar in node.value:
        assert isinstance(scalar, yaml.ScalarNode)
        assert scalar.tag == '!dice'


class PathResolverLoader(yaml.CLoader):
    pass


class PathResolverDumper(yaml.CDumper):
    pass


def test_path_resolver_loader():
    yaml.add_path_resolver('!root', [],
            Loader=PathResolverLoader, Dumper=PathResolverDumper)
    yaml.add_path_resolver('!root/scalar', [], str,
            Loader=PathResolverLoader, Dumper=PathResolverDumper)
    yaml.add_path_resolver('!root/key11/key12/*', ['key11', 'key12'],
            Loader=PathResolverLoader, Dumper=PathResolverDumper)

    yamlcode = """\
---
"this scalar should be selected"
---
key11: !foo
    key12:
        is: [selected]
    key22:
        key13: [not, selected]
        key23: [not, selected]
"""

    resolved_yamlcode = """\
--- !root/scalar
"this scalar should be selected"
--- !root
key11: !foo
    key12: !root/key11/key12/*
        is: [selected]
    key22:
        key13: [not, selected]
        key23: [not, selected]
"""

    nodes1 = list(yaml.compose_all(yamlcode, Loader=PathResolverLoader))
    nodes2 = list(yaml.compose_all(resolved_yamlcode, Loader=PathResolverLoader))
    for node1, node2 in zip(nodes1, nodes2):
        data1 = _convert_node(node1)
        data2 = _convert_node(node2)
        assert data1 == data2
