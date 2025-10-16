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