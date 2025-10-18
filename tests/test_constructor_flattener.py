import pytest
import yaml
from io import StringIO


def test_custom_flattener_with_compose():
    """
    Test that a custom flattener can use compose to parse embedded YAML.
    """

    def flatten_yaml_string(constructor, node):
        """
        Flattener that parses YAML from a string scalar.
        Used to test that custom flatteners can call compose.
        """
        if isinstance(node, yaml.ScalarNode):
            yaml_string = constructor.construct_scalar(node)
            parsed_node = yaml.compose(StringIO(yaml_string), yaml.SafeLoader)

            if isinstance(parsed_node, yaml.MappingNode):
                constructor.flatten_mapping(parsed_node)
                yield parsed_node.value
        else:
            raise yaml.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "expected a string containing YAML for !yaml_string tag",
                node.start_mark
            )

    class CustomLoader(yaml.SafeLoader):
        pass

    CustomLoader.add_flattener('!yaml_string', flatten_yaml_string)

    test_yaml = """
base:
  x: 1
  y: 2

merged:
  <<: !yaml_string "x: 10\\ny: 20\\nz: 30"
  label: test
"""

    result = yaml.load(test_yaml, CustomLoader)

    assert result['merged']['x'] == 10
    assert result['merged']['y'] == 20
    assert result['merged']['z'] == 30
    assert result['merged']['label'] == 'test'


def test_custom_flattener_with_sequence():
    """
    Test custom flattener with sequence of YAML strings (multiple merges).
    """

    def flatten_yaml_string(constructor, node):
        if isinstance(node, yaml.ScalarNode):
            yaml_string = constructor.construct_scalar(node)
            parsed_node = yaml.compose(StringIO(yaml_string), yaml.SafeLoader)

            if isinstance(parsed_node, yaml.MappingNode):
                constructor.flatten_mapping(parsed_node)
                yield parsed_node.value
        else:
            raise yaml.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "expected a string containing YAML for !yaml_string tag",
                node.start_mark
            )

    class CustomLoader(yaml.SafeLoader):
        pass

    CustomLoader.add_flattener('!yaml_string', flatten_yaml_string)

    test_yaml = """
merged:
  <<: [!yaml_string "x: 1", !yaml_string "y: 2", !yaml_string "z: 3"]
  label: multi
"""

    result = yaml.load(test_yaml, CustomLoader)

    assert result['merged']['x'] == 1
    assert result['merged']['y'] == 2
    assert result['merged']['z'] == 3
    assert result['merged']['label'] == 'multi'


def test_custom_flattener_override():
    """
    Test that later values override earlier ones in merge sequence.

    It also lightly verifies that the original/standard MappingNode
    inside of a sequence functions as expected.
    """

    def flatten_yaml_string(constructor, node):
        if isinstance(node, yaml.ScalarNode):
            yaml_string = constructor.construct_scalar(node)
            parsed_node = yaml.compose(StringIO(yaml_string), yaml.SafeLoader)

            if isinstance(parsed_node, yaml.MappingNode):
                constructor.flatten_mapping(parsed_node)
                yield parsed_node.value
        else:
            raise yaml.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "expected a string containing YAML for !yaml_string tag",
                node.start_mark
            )

    class CustomLoader(yaml.SafeLoader):
        pass

    CustomLoader.add_flattener('!yaml_string', flatten_yaml_string)

    test_yaml = """
merged:
  v: 0
  w: overwritten
  <<: [{w: 1, x: overwritten, y: 3}, !yaml_string "x: 10"]
  x: 2
  z: 4
"""

    result = yaml.load(test_yaml, CustomLoader)

    assert result['merged']['v'] == 0
    assert result['merged']['w'] == 1
    assert result['merged']['x'] == 2
    assert result['merged']['y'] == 3
    assert result['merged']['z'] == 4