"""Tests for issue #907: ConstructorError raises AttributeError when
construct_* methods receive non-Node objects.

The bug: construct_scalar, construct_sequence, construct_mapping, and
construct_pairs all access node.id and node.start_mark on the error path
when the object is not a Node subclass. If a non-Node (e.g. list, dict,
int) is passed, this raises AttributeError instead of ConstructorError.
"""

import pytest
import yaml
from yaml.constructor import ConstructorError


class TestConstructorTypeCheck:
    """construct_* methods should raise ConstructorError (not AttributeError)
    when called with non-Node objects."""

    def test_construct_scalar_non_node(self):
        """construct_scalar with a non-Node should raise ConstructorError."""
        from yaml.nodes import ScalarNode
        loader = yaml.SafeLoader("")
        with pytest.raises(ConstructorError, match="expected a scalar node"):
            loader.construct_scalar([1, 2, 3])

    def test_construct_sequence_non_node(self):
        """construct_sequence with a non-Node should raise ConstructorError."""
        loader = yaml.SafeLoader("")
        with pytest.raises(ConstructorError, match="expected a sequence node"):
            loader.construct_sequence("not a node")

    def test_construct_mapping_non_node(self):
        """construct_mapping with a non-Node should raise ConstructorError."""
        loader = yaml.SafeLoader("")
        with pytest.raises(ConstructorError, match="expected a mapping node"):
            loader.construct_mapping(42)

    def test_construct_pairs_non_node(self):
        """construct_pairs with a non-Node should raise ConstructorError."""
        loader = yaml.SafeLoader("")
        with pytest.raises(ConstructorError, match="expected a mapping node"):
            loader.construct_pairs(None)


class TestSafeLoaderEdgeCases:
    """Ensure safe_load still works correctly with various inputs after
    the constructor type-check fix."""

    def test_safe_load_normal(self):
        result = yaml.safe_load("a: 1\nb: 2")
        assert result == {"a": 1, "b": 2}

    def test_safe_load_list(self):
        result = yaml.safe_load("- 1\n- 2\n- 3")
        assert result == [1, 2, 3]

    def test_safe_load_scalar(self):
        result = yaml.safe_load("hello")
        assert result == "hello"

    def test_safe_load_empty(self):
        result = yaml.safe_load("")
        assert result is None

    def test_safe_load_nested(self):
        result = yaml.safe_load("outer:\n  inner:\n    key: value")
        assert result == {"outer": {"inner": {"key": "value"}}}
